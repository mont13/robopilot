import fastapi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional # Dict is not explicitly used in models but good for general typing
import uvicorn
import threading
import queue
import time
import logging
import socket
import sys

# DepthAI related imports
import depthai as dai
import blobconverter # For automatically downloading the model blob
# numpy is implicitly used by frame.shape and getCvFrame()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# --- Configuration Constants ---
# Model details (MobileNet-SSD trained on COCO)
MODEL_ZOO_NAME = "mobilenet-ssd" # Pre-trained model available via blobconverter
NN_CONFIDENCE_THRESHOLD = 0.5 # Minimum confidence to consider a detection
NN_INPUT_SIZE = (300, 300) # MobileNet-SSD expects 300x300
CAMERA_FPS = 30

# COCO Labels (MobileNet-SSD is often trained on COCO)
# The first label is often "background" or "unknown"
COCO_LABEL_MAP = [
    "background", "person", "bicycle", "car", "motorcycle", "airplane",
    "bus", "train", "truck", "boat", "traffic light", "fire hydrant",
    "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse",
    "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis",
    "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass",
    "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich",
    "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
    "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
    "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush"
]

# Global variables
detection_queue = queue.Queue(maxsize=1) # Holds the latest detection result
is_running = False # Flag to control the camera worker thread
camera_thread = None # Reference to the camera worker thread

# --- Pydantic Data Models ---
class BoundingBox(BaseModel):
    xmin: int
    ymin: int
    xmax: int
    ymax: int

class Detection(BaseModel):
    label: str
    confidence: float
    bbox: BoundingBox

class DetectionResponse(BaseModel):
    detections: List[Detection]
    timestamp: float

# --- Detection Processing Function ---
def process_raw_detections(frame, raw_detections):
    """
    Converts raw DepthAI detections into a list of Pydantic Detection models.
    Each dictionary contains:
    - label: detected object class
    - confidence: detection confidence score
    - bbox: dictionary with xmin, ymin, xmax, ymax coordinates
    """
    if frame is None or not raw_detections:
        return []
    
    frame_height = frame.shape[0]
    frame_width = frame.shape[1]
    
    processed_results = []
    for detection_data in raw_detections:
        # Convert normalized coordinates to pixel coordinates
        xmin = int(detection_data.xmin * frame_width)
        ymin = int(detection_data.ymin * frame_height)
        xmax = int(detection_data.xmax * frame_width)
        ymax = int(detection_data.ymax * frame_height)
        
        label_index = int(detection_data.label)
        label_text = COCO_LABEL_MAP[label_index] if 0 <= label_index < len(COCO_LABEL_MAP) else f"Label_{label_index}"
        
        processed_results.append(
            Detection(
                label=label_text,
                confidence=float(detection_data.confidence),
                bbox=BoundingBox(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)
            )
        )
    return processed_results

# --- DepthAI Pipeline Creation ---
def create_depthai_pipeline():
    """Creates and configures the DepthAI pipeline."""
    logger.info("Creating DepthAI pipeline...")
    pipeline = dai.Pipeline()

    # 1. Color Camera Node
    cam_rgb = pipeline.create(dai.node.ColorCamera)
    cam_rgb.setPreviewSize(NN_INPUT_SIZE[0], NN_INPUT_SIZE[1])
    cam_rgb.setInterleaved(False)
    cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    cam_rgb.setFps(CAMERA_FPS)

    # 2. Neural Network Node (MobileNetDetectionNetwork)
    nn = pipeline.create(dai.node.MobileNetDetectionNetwork)
    try:
        # Download blob if not already downloaded
        blob_path = blobconverter.from_zoo(
            name=MODEL_ZOO_NAME, 
            shaves=6, 
            zoo_type="intel"
        )
        nn.setBlobPath(blob_path)
    except Exception as e:
        logger.error(f"Failed to get blob for {MODEL_ZOO_NAME} from zoo: {e}", exc_info=True)
        raise # Critical failure, pipeline cannot be created
        
    nn.setConfidenceThreshold(NN_CONFIDENCE_THRESHOLD)
    nn.setNumInferenceThreads(2) 
    nn.input.setBlocking(False)

    # Link camera preview output to neural network input
    cam_rgb.preview.link(nn.input)

    # 3. XLinkOut for RGB frames (passthrough from NN for synchronization)
    xout_rgb = pipeline.create(dai.node.XLinkOut)
    xout_rgb.setStreamName("rgb")
    nn.passthrough.link(xout_rgb.input)

    # 4. XLinkOut for NN detections
    xout_nn = pipeline.create(dai.node.XLinkOut)
    xout_nn.setStreamName("nn")
    nn.out.link(xout_nn.input)
    
    logger.info("DepthAI pipeline created successfully.")
    return pipeline

# Global pipeline instance, created once
# This is just the pipeline definition, not the active device connection yet.
try:
    pipeline = create_depthai_pipeline()
except Exception as e:
    logger.error(f"Fatal error creating DepthAI pipeline during initial setup: {e}. The API's camera features will be unavailable.")
    pipeline = None # Indicate pipeline creation failure

# --- FastAPI Application ---
app = FastAPI(title="Object Detection API",
             description="API for real-time object detection using OAK-D camera")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Camera Worker Thread ---
def camera_worker():
    """Thread that runs the camera detection loop."""
    global is_running, detection_queue, pipeline

    if pipeline is None:
        logger.error("Camera worker cannot start: DepthAI pipeline is not available (failed during creation).")
        # Put an error in the queue to indicate persistent failure
        try:
            detection_queue.put_nowait({'error': 'DepthAI pipeline initialization failed. Camera inactive.'})
        except queue.Full: # Should not happen with maxsize=1 unless something else is writing
            pass
        is_running = False # Ensure main loop condition is false
        return

    try:
        with dai.Device(pipeline) as device:
            logger.info(f"Successfully connected to OAK device: {device.getDeviceInfo().name}")
            logger.info(f"USB speed: {device.getUsbSpeed().name}")
            
            q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            q_nn = device.getOutputQueue(name="nn", maxSize=4, blocking=False)

            current_frame = None
            current_raw_detections = [] 

            while is_running:
                in_rgb = q_rgb.tryGet()
                in_nn = q_nn.tryGet()

                if in_rgb is not None:
                    current_frame = in_rgb.getCvFrame()

                if in_nn is not None:
                    current_raw_detections = in_nn.detections

                if current_frame is not None:
                    detection_models = process_raw_detections(current_frame, current_raw_detections)
                    
                    payload = DetectionResponse(
                        detections=detection_models,
                        timestamp=time.time()
                    )
                    
                    try:
                        detection_queue.put_nowait(payload)
                    except queue.Full:
                        try:
                            detection_queue.get_nowait() # Discard oldest
                        except queue.Empty:
                            pass # Should ideally not happen if Full was raised
                        detection_queue.put_nowait(payload) # Add newest
                
                time.sleep(0.01) # Small delay to yield CPU
    
    except RuntimeError as e:
        error_msg = f"OAK Camera Runtime Error (often indicates device issue or already in use): {str(e)}"
        logger.error(error_msg, exc_info=True)
        try:
            detection_queue.put_nowait({'error': error_msg})
        except queue.Full: pass
    except Exception as e:
        error_msg = f"Unhandled error in camera thread: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        try:
            detection_queue.put_nowait({'error': error_msg})
        except queue.Full: pass
    finally:
        logger.info("Camera worker thread has finished.")
        # is_running will be set to False by shutdown_event for graceful stop
        # If thread exits due to error, health check (is_alive) will reflect it.

# --- FastAPI Event Handlers ---
@app.on_event("startup")
async def startup_event():
    """Start the camera thread when the API starts."""
    global camera_thread, is_running
    if pipeline is None:
        logger.warning("Skipping camera thread start: DepthAI pipeline initialization failed earlier.")
        return

    is_running = True
    camera_thread = threading.Thread(target=camera_worker, daemon=True)
    camera_thread.start()
    logger.info("Camera worker thread initiated.")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the camera thread when the API shuts down."""
    global is_running
    logger.info("API shutdown initiated. Attempting to stop camera thread...")
    is_running = False 
    if camera_thread and camera_thread.is_alive():
        camera_thread.join(timeout=2.0) 
        if camera_thread.is_alive():
            logger.warning("Camera thread did not stop within the timeout.")
        else:
            logger.info("Camera thread stopped successfully.")
    else:
        logger.info("Camera thread was not running or already stopped.")

# --- API Endpoints ---
@app.get("/detections", response_model=DetectionResponse)
async def get_latest_detections():
    """Get the latest detection results from the OAK-D camera."""
    # First, check if there's a persistent error in the queue if camera isn't live
    # This helps to immediately inform the client if the camera system is down.
    if not (camera_thread and camera_thread.is_alive()):
        try:
            # Try to peek at the queue without blocking or removing
            # This is a bit of a hack as Queue doesn't have a direct peek.
            # If queue is empty, this will raise queue.Empty.
            # If not empty, it might be an error or old data.
            if not detection_queue.empty():
                potential_error_item = detection_queue.queue[0]
                if isinstance(potential_error_item, dict) and 'error' in potential_error_item:
                    raise HTTPException(status_code=503, detail=f"Service Unavailable: Camera not running. Last error: {potential_error_item['error']}")
            # If no error in queue but camera not running, still unavailable
            raise HTTPException(status_code=503, detail="Service Unavailable: Camera system is not active.")
        except queue.Empty:
             raise HTTPException(status_code=503, detail="Service Unavailable: Camera system is not active and no detections queued.")
        except AttributeError: # If detection_queue.queue is not accessible (e.g. other queue type)
            raise HTTPException(status_code=503, detail="Service Unavailable: Camera system is not active.")


    try:
        # Get the latest item. This item should be a DetectionResponse model instance
        # or an error dict if the worker put one there before exiting.
        result_item = detection_queue.get_nowait() 
        if isinstance(result_item, dict) and 'error' in result_item: 
            # This case should ideally be caught by the check above if camera_thread is not alive.
            # But if thread died and put an error, then restarted, this could happen.
            raise HTTPException(status_code=503, detail=f"Service Error: An error was reported by the camera worker: {result_item['error']}")
        
        # Assuming result_item is a DetectionResponse Pydantic model if no error
        # FastAPI will validate this against response_model=DetectionResponse
        return result_item
    except queue.Empty:
        # Camera is running, but no new detection results are in the queue at this exact moment.
        raise HTTPException(status_code=204, detail="No new detection results available at this moment. Try again shortly.")
    except Exception as e:
        logger.error(f"Unexpected error in /detections endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching detections.")

@app.get("/health")
async def health_check():
    """Health check endpoint for the API and camera status."""
    camera_pipeline_ok = pipeline is not None
    camera_thread_ok = camera_thread is not None and camera_thread.is_alive()
    
    status_detail = "unknown"
    if not camera_pipeline_ok:
        status_detail = "pipeline_initialization_failed"
    elif camera_thread_ok:
        status_detail = "running"
    elif camera_thread is None: # Pipeline OK, but thread not even started (e.g. startup event failed)
        status_detail = "thread_not_started"
    else: # Pipeline OK, thread started but not alive
        status_detail = "thread_stopped_or_crashed"

    last_error_hint = "N/A"
    if not camera_thread_ok and not detection_queue.empty():
        try:
            # Peek at the last item if possible to show error context
            item = detection_queue.queue[0] 
            if isinstance(item, dict) and 'error' in item:
                last_error_hint = item['error']
        except Exception:
            pass # Ignore if peeking fails

    return {
        "status": "healthy" if camera_pipeline_ok and camera_thread_ok else "degraded",
        "timestamp": time.time(),
        "service_name": app.title,
        "camera_pipeline_initialized": camera_pipeline_ok,
        "camera_thread_active": camera_thread_ok,
        "camera_status_details": status_detail,
        "last_camera_error_hint": last_error_hint,
        "detection_queue_current_size": detection_queue.qsize(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()) if hasattr(socket, 'gethostbyname') else "N/A"
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint that doesn't require camera."""
    return {
        "message": "API is working!",
        "timestamp": time.time(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()) if hasattr(socket, 'gethostbyname') else "N/A"
    }

# --- Main Execution ---
if __name__ == "__main__":
    logger.info("Starting Object Detection API server...")
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logger.info(f"Server will be available on all interfaces (0.0.0.0:8000).")
        logger.info(f"Try accessing on this machine via: http://localhost:8000 or http://{local_ip}:8000")
    except socket.gaierror:
        logger.warning("Could not determine local IP address. Server will run on 0.0.0.0:8000.")
        local_ip = "localhost" # Fallback for log messages
    
    logger.info("Available Endpoints:")
    logger.info(f"  API Docs (Swagger UI): http://{local_ip}:8000/docs")
    logger.info(f"  Detections:            http://{local_ip}:8000/detections")
    logger.info(f"  Health Check:          http://{local_ip}:8000/health")
    logger.info(f"  Test Endpoint:         http://{local_ip}:8000/test")
    logger.info("Press Ctrl+C to stop the server.")
    
    uvicorn.run(
        "api:app", 
        host="0.0.0.0",
        port=8000,
        log_level="info" 
    )