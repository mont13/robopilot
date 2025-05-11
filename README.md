# RoboPilot

A Python-based robot control system with camera and audio streaming capabilities.

## Overview

RoboPilot consists of the following components:

1. **Camera Server**: A FastAPI application that captures and streams video/audio from a camera device
2. **Stream Clients**: Various clients to view and extract the video and audio streams
3. **Robot Control**: Python modules for robotic arm control via ur-rtde library and GripperSocketControl

## Setup

### Requirements

- Python 3.8+
- FFmpeg (for stream playback)
- Web browser with WebRTC support

### Installation

1. Clone the repository
   ```
   git clone <your-repository-url>
   cd robopilot
   ```

2. Install the required packages
   ```
   pip install -r requirements.txt
   ```

3. Install the camera server requirements
   ```
   cd camera_server
   pip install -r requirements.txt
   cd ..
   ```

## Usage

### Camera Server

1. Start the camera server:
   ```
   cd camera_server
   python main.py
   ```

2. Open a web browser and navigate to `http://localhost:8000`
   - Click "Start Streaming" to activate your device's camera and microphone
   - The server will start receiving the audio and video streams

### Accessing the Streams

The camera server provides two separate HTTP endpoints:

1. **Video Stream:** http://localhost:8000/stream/video (WebM format)
2. **Audio Stream:** http://localhost:8000/stream/audio (WAV format)

#### Using Stream Clients

Several stream clients are provided to access and process the streams:

1. **Basic Stream Client**: Access both audio and video streams
   ```
   python stream_client.py
   ```

2. **Stream Extractor**: Save audio and video streams to separate files
   ```
   python stream_extractor.py
   ```
   - Files are saved to the `extracted_streams` directory
   - Play extracted files with: `ffplay extracted_streams/video_stream_*.webm`

3. **WebM Stream Client**: Specialized client for WebM video playback
   ```
   python webm_stream_client.py
   ```

4. **FFplay Stream Client**: Direct playback using FFplay
   ```
   python ffplay_stream.py
   ```

### Robot Control

To control the robot arm:

1. Make sure the robot is in the initial state (see image below)
2. Run the example script:
   ```
   python example.py
   ```

For voice command control:
```
python voice_command_robot.py
```

![Robot initial state](example_robot_initial_state.jpg)

## Troubleshooting

### Video Stream Issues

- If FFplay shows "EBML header parsing failed" error, use the `webm_stream_client.py` script instead
- Ensure your browser supports WebRTC and has camera/microphone permissions

### Audio Stream Issues

- If audio stream stops unexpectedly, try restarting the streaming from the web interface
- Check the camera server terminal for any error messages

## File Structure

- `camera_server/`: FastAPI server for camera streaming
  - `main.py`: Main server application
  - `static/js/`: JavaScript files for the web interface
  - `templates/`: HTML templates
  - `recordings/`: Saved WebM recordings (both audio and video)
  - `audio_only/`: Extracted audio recordings
  - `video_only/`: Extracted video recordings
- `stream_client.py`: Basic audio/video stream client
- `stream_extractor.py`: Extracts and saves streams to files
- `webm_stream_client.py`: Specialized WebM streaming client
- `ffplay_stream.py`: Direct FFplay streaming client
- `robot.py`: Robot control class
- `example.py`: Example robot control script
- `voice_command_robot.py`: Voice-controlled robot implementation

## Development

- Use `extracted_streams/` for development and testing with pre-recorded streams
- The `.gitignore` file is configured to exclude all audio and video recordings
