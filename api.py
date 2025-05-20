import fastapi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, __version__ as pydantic_version
from typing import List, Optional
import uvicorn
import threading
import queue
import time
import logging
import socket
import sys
import os
import cv2
import numpy as np
import json # For saving JSON data to file

# DepthAI related imports
import depthai as dai
import blobconverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# --- Configuration Constants ---
MODEL_ZOO_NAME = "mobilenet-ssd"
NN_CONFIDENCE_THRESHOLD = 0.5
NN_INPUT_SIZE = (300, 300) # The frame from nn.passthrough will be this size
CAMERA_FPS = 30
SAVE_PATH = "detection_outputs"

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
detection_queue = queue.Queue(maxsize=1)
is_running = False
camera_thread = None

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

class Resolution(BaseModel): # NEW: Model for resolution
    width: int
    height: int

class DetectionResponse(BaseModel):
    detections: List[Detection]
    timestamp: float
    resolution: Resolution # ADDED: Resolution field
    annotated_image_saved_path: Optional[str] = None
    original_image_saved_path: Optional[str] = None
    json_saved_path: Optional[str] = None

# --- Helper Functions ---
def process_raw_detections(frame, raw_detections):
    if frame is None or not raw_detections:
        return []
    
    frame_height = frame.shape[0]
    frame_width = frame.shape[1]
    
    processed_results = []
    for detection_data in raw_detections:
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

def draw_detections_on_frame(frame: np.ndarray, detections_list: List[Detection]) -> np.ndarray:
    display_frame = frame.copy()
    for det in detections_list:
        bbox = det.bbox
        cv2.rectangle(display_frame, (bbox.xmin, bbox.ymin), 
                      (bbox.xmax, bbox.ymax), (0, 255, 0), 2)
        
        label_text = f"{det.label} {det.confidence:.2f}"
        label_y = bbox.ymin - 15 if bbox.ymin - 15 > 15 else bbox.ymin + 25
        cv2.putText(display_frame, label_text, 
                   (bbox.xmin, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return display_frame

def get_pydantic_model_dict(model_instance: BaseModel):
    if pydantic_version.startswith("1."):
        return model_instance.dict()
    else: 
        return model_instance.model_dump()

# --- DepthAI Pipeline Creation ---
def create_depthai_pipeline():
    logger.info("Creating DepthAI pipeline...")
    pipeline_obj = dai.Pipeline()

    cam_rgb = pipeline_obj.create(dai.node.ColorCamera)
    cam_rgb.setPreviewSize(NN_INPUT_SIZE[0], NN_INPUT_SIZE[1])
    cam_rgb.setInterleaved(False)
    cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    cam_rgb.setFps(CAMERA_FPS)

    nn = pipeline_obj.create(dai.node.MobileNetDetectionNetwork)
    try:
        blob_path = blobconverter.from_zoo(name=MODEL_ZOO_NAME, shaves=6, zoo_type="intel")
        nn.setBlobPath(blob_path)
    except Exception as e:
        logger.error(f"Failed to get blob for {MODEL_ZOO_NAME} from zoo: {e}", exc_info=True)
        raise 
        
    nn.setConfidenceThreshold(NN_CONFIDENCE_THRESHOLD)
    nn.setNumInferenceThreads(2) 
    nn.input.setBlocking(False)
    cam_rgb.preview.link(nn.input)

    xout_rgb = pipeline_obj.create(dai.node.XLinkOut)
    xout_rgb.setStreamName("rgb")
    nn.passthrough.link(xout_rgb.input) # Frame from here will be NN_INPUT_SIZE

    xout_nn = pipeline_obj.create(dai.node.XLinkOut)
    xout_nn.setStreamName("nn")
    nn.out.link(xout_nn.input)
    
    logger.info("DepthAI pipeline created successfully.")
    return pipeline_obj

try:
    pipeline = create_depthai_pipeline()
except Exception as e:
    logger.error(f"Fatal error creating DepthAI pipeline during initial setup: {e}. The API's camera features will be unavailable.")
    pipeline = None

# --- FastAPI Application ---
app = FastAPI(title="Object Detection API",
             description="API for real-time object detection. Saves original/annotated images and JSON data on detection.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Camera Worker Thread ---
def camera_worker():
    global is_running, detection_queue, pipeline

    if pipeline is None:
        logger.error("Camera worker: DepthAI pipeline not available.")
        try:
            detection_queue.put_nowait({'error': 'DepthAI pipeline initialization failed. Camera inactive.'})
        except queue.Full: pass
        is_running = False
        return

    try:
        with dai.Device(pipeline) as device:
            logger.info(f"Connected to OAK device: {device.getDeviceInfo().name} (USB: {device.getUsbSpeed().name})")
            
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
                    # Get frame dimensions for resolution
                    frame_height, frame_width, _ = current_frame.shape
                    current_frame_resolution = Resolution(width=frame_width, height=frame_height)
                    
                    detection_models = process_raw_detections(current_frame, current_raw_detections)
                    
                    response_payload = DetectionResponse(
                        detections=detection_models,
                        timestamp=time.time(),
                        resolution=current_frame_resolution # Include resolution
                    )
                    
                    queue_item = {
                        'response_data': response_payload,
                        'frame': current_frame.copy() 
                    }
                    
                    try:
                        detection_queue.put_nowait(queue_item)
                    except queue.Full:
                        try:
                            detection_queue.get_nowait() 
                        except queue.Empty:
                            pass 
                        detection_queue.put_nowait(queue_item)
                
                time.sleep(0.01) 
    
    except RuntimeError as e:
        error_msg = f"OAK Camera Runtime Error: {str(e)}"
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

# --- FastAPI Event Handlers ---
@app.on_event("startup")
async def startup_event():
    global camera_thread, is_running
    if not os.path.exists(SAVE_PATH):
        try:
            os.makedirs(SAVE_PATH)
            logger.info(f"Created output save directory: {SAVE_PATH}")
        except OSError as e:
            logger.error(f"Could not create output save directory {SAVE_PATH}: {e}")

    if pipeline is None:
        logger.warning("Skipping camera thread start: DepthAI pipeline failed.")
        return

    is_running = True
    camera_thread = threading.Thread(target=camera_worker, daemon=True)
    camera_thread.start()
    logger.info("Camera worker thread initiated.")


@app.on_event("shutdown")
async def shutdown_event():
    global is_running
    logger.info("API shutdown. Stopping camera thread...")
    is_running = False 
    if camera_thread and camera_thread.is_alive():
        camera_thread.join(timeout=2.0) 
        if camera_thread.is_alive():
            logger.warning("Camera thread did not stop within timeout.")
        else:
            logger.info("Camera thread stopped.")
    else:
        logger.info("Camera thread was not running or already stopped.")

# --- API Endpoints ---
@app.get("/detections", response_model=DetectionResponse)
async def get_latest_detections():
    if not (camera_thread and camera_thread.is_alive()):
        if not detection_queue.empty():
            try:
                potential_error_item = detection_queue.queue[0]
                if isinstance(potential_error_item, dict) and 'error' in potential_error_item:
                    raise HTTPException(status_code=503, detail=f"Service Unavailable: Camera not running. Error: {potential_error_item['error']}")
            except Exception: pass
        raise HTTPException(status_code=503, detail="Service Unavailable: Camera system is not active.")

    try:
        queued_item = detection_queue.get_nowait()
        
        if isinstance(queued_item, dict) and 'error' in queued_item: 
            raise HTTPException(status_code=503, detail=f"Service Error: {queued_item['error']}")
        
        if not (isinstance(queued_item, dict) and 'response_data' in queued_item and 'frame' in queued_item):
            logger.error(f"Invalid item format in detection_queue: {type(queued_item)}")
            raise HTTPException(status_code=500, detail="Internal server error: Unexpected data format from camera.")

        response_payload: DetectionResponse = queued_item['response_data']
        original_frame: Optional[np.ndarray] = queued_item['frame']
        
        saved_original_path = None
        saved_annotated_path = None
        saved_json_path = None

        if not os.path.exists(SAVE_PATH):
            try:
                os.makedirs(SAVE_PATH, exist_ok=True)
            except OSError as e:
                logger.error(f"Could not create output save directory {SAVE_PATH} on demand: {e}")

        ts_int = int(response_payload.timestamp)
        ts_ms = int((response_payload.timestamp % 1) * 1000)
        filename_base = f"{ts_int}_{ts_ms:03d}"

        if original_frame is not None and os.path.exists(SAVE_PATH):
            try:
                original_filename = f"original_{filename_base}.jpg"
                full_original_save_path = os.path.join(SAVE_PATH, original_filename)
                cv2.imwrite(full_original_save_path, original_frame)
                saved_original_path = full_original_save_path
                logger.info(f"Saved original image to: {full_original_save_path}")

                if response_payload.detections:
                    annotated_frame = draw_detections_on_frame(original_frame, response_payload.detections)
                    annotated_filename = f"annotated_{filename_base}.jpg"
                    full_annotated_save_path = os.path.join(SAVE_PATH, annotated_filename)
                    cv2.imwrite(full_annotated_save_path, annotated_frame)
                    saved_annotated_path = full_annotated_save_path
                    logger.info(f"Saved annotated image to: {full_annotated_save_path}")
                else:
                    logger.info("No detections found, no annotated image saved for this request.")
            except Exception as e:
                logger.error(f"Failed to save detection image(s): {e}", exc_info=True)
        
        response_payload.original_image_saved_path = saved_original_path
        response_payload.annotated_image_saved_path = saved_annotated_path

        if os.path.exists(SAVE_PATH):
            try:
                json_filename = f"data_{filename_base}.json"
                full_json_save_path = os.path.join(SAVE_PATH, json_filename)
                # Update the payload *before* saving, so the saved JSON also contains this path.
                response_payload.json_saved_path = full_json_save_path 

                payload_dict = get_pydantic_model_dict(response_payload)
                
                with open(full_json_save_path, 'w') as f:
                    json.dump(payload_dict, f, indent=4)
                logger.info(f"Saved detection JSON data to: {full_json_save_path}")
            except Exception as e:
                logger.error(f"Failed to save detection JSON data: {e}", exc_info=True)
                response_payload.json_saved_path = None 
        
        return response_payload

    except queue.Empty:
        raise HTTPException(status_code=204, detail="No new detection results available. Try again shortly.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /detections endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching detections.")

@app.get("/health")
async def health_check():
    camera_pipeline_ok = pipeline is not None
    camera_thread_ok = camera_thread is not None and camera_thread.is_alive()
    
    status_detail = "unknown"
    if not camera_pipeline_ok: status_detail = "pipeline_initialization_failed"
    elif camera_thread_ok: status_detail = "running"
    elif camera_thread is None: status_detail = "thread_not_started"
    else: status_detail = "thread_stopped_or_crashed"

    last_error_hint = "N/A"
    if not camera_thread_ok and not detection_queue.empty():
        try:
            item = detection_queue.queue[0] 
            if isinstance(item, dict) and 'error' in item: last_error_hint = item['error']
        except Exception: pass
    
    # The frame resolution passed to the API will be NN_INPUT_SIZE
    # because cam_rgb.preview is linked to nn.input, and nn.passthrough is used.
    expected_output_resolution = {"width": NN_INPUT_SIZE[0], "height": NN_INPUT_SIZE[1]}


    return {
        "status": "healthy" if camera_pipeline_ok and camera_thread_ok else "degraded",
        "timestamp": time.time(),
        "service_name": app.title,
        "pydantic_version": pydantic_version,
        "camera_pipeline_initialized": camera_pipeline_ok,
        "camera_thread_active": camera_thread_ok,
        "camera_status_details": status_detail,
        "last_camera_error_hint": last_error_hint,
        "detection_queue_current_size": detection_queue.qsize(),
        "expected_output_resolution": expected_output_resolution,
        "save_path_exists": os.path.exists(SAVE_PATH),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()) if hasattr(socket, 'gethostbyname') else "N/A"
    }

@app.get("/test")
async def test_endpoint():
    return {
        "message": "API is working!",
        "timestamp": time.time(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()) if hasattr(socket, 'gethostbyname') else "N/A"
    }

# --- Main Execution ---
if __name__ == "__main__":
    logger.info("Starting Object Detection API server...")
    logger.info(f"Using Pydantic version: {pydantic_version}")

    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logger.info(f"Server on all interfaces (0.0.0.0:8000). Access via: http://localhost:8000 or http://{local_ip}:8000")
    except socket.gaierror:
        logger.warning("Could not determine local IP. Server will run on 0.0.0.0:8000.")
        local_ip = "localhost"
    
    logger.info("Endpoints:")
    logger.info(f"  Docs:       http://{local_ip}:8000/docs")
    logger.info(f"  Detections: http://{local_ip}:8000/detections")
    logger.info(f"  Health:     http://{local_ip}:8000/health")
    logger.info(f"  Test:       http://{local_ip}:8000/test")
    logger.info(f"Output (images, JSON) will be saved to: ./{SAVE_PATH}/")
    logger.info("Press Ctrl+C to stop.")
    
    uvicorn.run(
        "__main__:app", # Changed from "api:app" as per user's original code if run directly
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False 
    )