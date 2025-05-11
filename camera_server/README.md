# Camera Streaming Server

A FastAPI-based web application for streaming video/audio from a device's camera and microphone, with automatic splitting of recordings into separate video and audio files.

## Features

- Live WebSocket-based streaming from browser to server
- Records video/audio in WebM format
- Automatically splits recordings into separate video-only and audio-only files
- Organized file storage in separate directories

## Directory Structure

```
camera_server/
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
├── recordings/          # Original video+audio recordings
├── video_only/          # Video-only recordings (no audio) 
├── audio_only/          # Audio-only recordings (WAV files)
├── static/              # Static assets
│   └── js/
│       └── stream.js    # Client-side streaming logic
└── templates/
    └── index.html       # Web interface
```

## Requirements

- Python 3.9 or higher
- FFmpeg (external dependency)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/robopilot.git
cd robopilot/camera_server
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

1. Start the server:
```bash
python main.py
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Allow camera and microphone permissions when prompted

4. Click "Start Streaming" to begin recording

5. Click "Stop Streaming" to end the session

6. Recordings will be saved in the following locations:
   - Original: `./recordings/`
   - Video-only: `./video_only/`
   - Audio-only: `./audio_only/`

## Notes

- Make sure your browser supports WebRTC (most modern browsers do)
- For mobile usage, use a secure HTTPS connection or localhost
- Recordings use the format: `received_[client_id]_[timestamp].webm`