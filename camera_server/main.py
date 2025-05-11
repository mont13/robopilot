import sys
print("PYTHON EXECUTABLE:", sys.executable)
print("SITE PACKAGES:", sys.path)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import subprocess
import tempfile
import asyncio
import shutil
from typing import Dict, List, Optional
import datetime
import io
import threading
import time

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
# Store the active streaming sessions
active_streams: Dict[str, Dict] = {}

# Latest chunks for direct access
latest_video_chunk = b''
latest_audio_chunk = b''
# Lock for thread-safe access to latest chunks
chunk_lock = threading.Lock()

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
    
    # Create temp files for processing
    temp_dir = tempfile.gettempdir()
    temp_input = os.path.join(temp_dir, f"input_{client_id}.webm")
    temp_video = os.path.join(temp_dir, f"video_{client_id}.webm")
    temp_audio = os.path.join(temp_dir, f"audio_{client_id}.wav")
    
    # Open recording file
    recording_file = open(file_path, "wb")
    
    active_streams[client_id] = {
        "file": recording_file,
        "temp_input": temp_input,
        "temp_video": temp_video,
        "temp_audio": temp_audio,
        "last_update": time.time()
    }
    
    print(f"Client {client_id} connected. Recording to {file_path}")
    
    try:
        while True:
            data = await websocket.receive_bytes()
            
            # Store the incoming data for recording
            recording_file.write(data)
            recording_file.flush()
            
            # Also write to a temp file for real-time processing
            with open(temp_input, "ab") as temp_file:
                temp_file.write(data)
            
            # Update latest chunks for direct access
            with chunk_lock:
                global latest_video_chunk, latest_audio_chunk
                latest_video_chunk = data  # Simplified - in reality we'd process this
                latest_audio_chunk = data  # Simplified - in reality we'd process this
            
            active_streams[client_id]["last_update"] = time.time()
            print(f"Received {len(data)} bytes from client {client_id}")
            
            # Every few chunks, process the temp file to extract streams
            # (We're doing real-time extraction via direct streaming instead)
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
        del clients[client_id]
    finally:
        # Close recording file
        if client_id in active_streams:
            active_streams[client_id]["file"].close()
            
            # Process the complete recording after session is done
            try:
                split_video_audio(file_path)
                print(f"Split video and audio for {filename}")
            except Exception as e:
                print(f"Error splitting video/audio: {e}")
            
            # Clean up temp files
            for temp_file in [temp_input, temp_video, temp_audio]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
            
            del active_streams[client_id]

@app.get("/stream/video")
async def stream_video():
    """Stream the latest video as a WebM stream."""
    return StreamingResponse(
        generate_video_stream(),
        media_type="video/webm",
        headers={"Cache-Control": "no-cache"}
    )

async def generate_video_stream():
    """Generate a video stream from the latest chunks."""
    while True:
        # Check if there's any active streaming
        if not active_streams:
            # No active streaming, send a small delay frame
            await asyncio.sleep(0.5)
            yield b''
            continue
        
        # Get latest chunk
        with chunk_lock:
            chunk = latest_video_chunk
        
        if chunk:
            yield chunk
        
        await asyncio.sleep(0.05)  # Slight delay to avoid overloading

@app.get("/stream/audio")
async def stream_audio():
    """Stream audio content as raw PCM audio data for real-time access."""
    # Use a more compatible format for audio streaming
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "audio/wav",  # Using WAV as it's more widely supported
    }
    
    return StreamingResponse(
        generate_audio_stream(),
        headers=headers,
    )

async def generate_audio_stream():
    """Generate an audio stream from the latest chunks, converted to WAV format."""
    # Create a process to convert WebM audio to WAV in real-time
    if check_ffmpeg_installed():
        ffmpeg_process = subprocess.Popen(
            [
                "ffmpeg",
                "-f", "webm",      # Input format
                "-i", "pipe:0",    # Read from stdin
                "-vn",             # No video
                "-acodec", "pcm_s16le",  # Convert to PCM audio
                "-f", "wav",       # Output format
                "pipe:1"           # Output to stdout
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0  # Unbuffered
        )

        try:
            # First yield WAV header
            wav_header = get_wav_header()
            if wav_header:
                yield wav_header
            
            while True:
                # Check if there's any active streaming
                if not active_streams:
                    # No active streaming, just wait
                    await asyncio.sleep(0.5)
                    continue
                
                # Get latest chunk
                with chunk_lock:
                    chunk = latest_audio_chunk
                
                if chunk and ffmpeg_process:
                    try:
                        # Feed chunk to FFmpeg
                        ffmpeg_process.stdin.write(chunk)
                        ffmpeg_process.stdin.flush()
                        
                        # Read output from FFmpeg (converted WAV data)
                        output = ffmpeg_process.stdout.read(1024)  # Read a block
                        if output:
                            yield output
                    except BrokenPipeError:
                        print("Broken pipe in audio stream")
                        break
                    except Exception as e:
                        print(f"Error in audio stream: {e}")
                        break
                
                await asyncio.sleep(0.05)  # Slight delay
        finally:
            # Clean up FFmpeg process
            if ffmpeg_process:
                try:
                    ffmpeg_process.stdin.close()
                    ffmpeg_process.terminate()
                except:
                    pass
    else:
        # Fallback if FFmpeg is not available
        yield b'No FFmpeg available for audio streaming'

def get_wav_header():
    """Generate a basic WAV header for proper audio playback."""
    # Simple WAV header for 16-bit PCM stereo at 44.1kHz
    # Format: RIFF header + fmt chunk + data chunk header
    sample_rate = 44100
    channels = 2
    bits_per_sample = 16
    
    header = bytearray()
    # RIFF header
    header.extend(b'RIFF')
    header.extend(b'\xFF\xFF\xFF\xFF')  # File size (unknown, set to max)
    header.extend(b'WAVE')
    
    # Format chunk
    header.extend(b'fmt ')
    header.extend((16).to_bytes(4, byteorder='little'))  # Chunk size
    header.extend((1).to_bytes(2, byteorder='little'))   # Audio format (PCM)
    header.extend(channels.to_bytes(2, byteorder='little'))
    header.extend(sample_rate.to_bytes(4, byteorder='little'))
    bytes_per_sec = sample_rate * channels * bits_per_sample // 8
    header.extend(bytes_per_sec.to_bytes(4, byteorder='little'))
    block_align = channels * bits_per_sample // 8
    header.extend(block_align.to_bytes(2, byteorder='little'))
    header.extend(bits_per_sample.to_bytes(2, byteorder='little'))
    
    # Data chunk header
    header.extend(b'data')
    header.extend(b'\xFF\xFF\xFF\xFF')  # Data size (unknown, set to max)
    
    return bytes(header)

@app.get("/stream/status")
async def stream_status():
    """Return information about active streaming sessions."""
    is_active = len(active_streams) > 0
    return {
        "active": is_active,
        "sessions": len(active_streams),
        "last_update": time.time() if is_active else None
    }

@app.post("/api/upload")
async def upload_chunk(file: UploadFile = File(...)):
    # For HTTP POST fallback (not real-time)
    chunk = await file.read()
    print(f"Received chunk of size {len(chunk)} bytes via POST")
    # TODO: Pass to processor/model
    return {"status": "ok"}

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
