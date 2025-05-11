import sys
print("PYTHON EXECUTABLE:", sys.executable)
print("SITE PACKAGES:", sys.path)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import subprocess
from typing import Dict
import datetime

# Create directories for storing recordings if they don't exist
RECORDINGS_DIR = "recordings"
VIDEO_ONLY_DIR = "video_only"
AUDIO_ONLY_DIR = "audio_only" 

for directory in [RECORDINGS_DIR, VIDEO_ONLY_DIR, AUDIO_ONLY_DIR]:
    os.makedirs(directory, exist_ok=True)

app = FastAPI()

# Allow CORS for local development (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session state for connected clients
clients: Dict[str, WebSocket] = {}

# Mount static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    client_id = str(id(websocket))
    clients[client_id] = websocket
    # Create a unique filename for each session
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"received_{client_id}_{timestamp}.webm"
    file_path = os.path.join(RECORDINGS_DIR, filename)
    
    # Ensure the recordings directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    f = open(file_path, "ab")
    try:
        while True:
            data = await websocket.receive_bytes()
            f.write(data)  # Save each chunk to file
            f.flush()
            print(f"Received {len(data)} bytes from client {client_id}, saved to {RECORDINGS_DIR}/{filename}")
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
        del clients[client_id]
    finally:
        f.close()
        # Split the video and audio after recording is done
        try:
            split_video_audio(file_path)
            print(f"Split video and audio for {filename}")
        except Exception as e:
            print(f"Error splitting video/audio: {e}")

@app.post("/api/upload")
async def upload_chunk(file: UploadFile = File(...)):
    # For HTTP POST fallback (not real-time)
    chunk = await file.read()
    print(f"Received chunk of size {len(chunk)} bytes via POST")
    # TODO: Pass to processor/model
    return {"status": "ok"}

# Dummy AI inference and robot control (to be replaced)
def dummy_inference(data):
    # Placeholder for ML model
    return "move_arm"

def dummy_robot_control(command):
    print(f"[Robot] Executing command: {command}")

def check_ffmpeg_installed():
    """Check if FFmpeg is installed and available in the PATH"""
    try:
        # Try to run ffmpeg -version to see if it exists
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def split_video_audio(file_path):
    """
    Splits the input video file into a video-only file and an audio-only file using FFmpeg.
    Output files are saved in separate directories.
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return None, None
    
    # Check if FFmpeg is installed
    if not check_ffmpeg_installed():
        print("Error: FFmpeg is not installed or not in PATH. Please install FFmpeg.")
        print("On macOS, you can install it with: brew install ffmpeg")
        return None, None
    
    # Get just the filename without path
    filename = os.path.basename(file_path)
    base, ext = os.path.splitext(filename)
    
    # Define output paths in their respective directories
    video_out = os.path.join(VIDEO_ONLY_DIR, f"{base}_video_only{ext}")
    audio_out = os.path.join(AUDIO_ONLY_DIR, f"{base}_audio_only.wav")
    
    # Extract video only (no audio)
    video_cmd = [
        "ffmpeg", "-y", "-i", file_path, 
        "-c:v", "copy", "-an", 
        video_out
    ]
    
    # Extract audio only
    audio_cmd = [
        "ffmpeg", "-y", "-i", file_path, 
        "-vn", "-acodec", "pcm_s16le", 
        audio_out
    ]
    
    try:
        print(f"Extracting video to {video_out}")
        subprocess.run(video_cmd, check=True, capture_output=True)
        print(f"Extracting audio to {audio_out}")
        subprocess.run(audio_cmd, check=True, capture_output=True)
        return video_out, audio_out
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return None, None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
