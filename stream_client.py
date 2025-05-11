#!/usr/bin/env python3
"""
Stream Client - Access both audio and video streams from the camera server
Uses specialized WebM handling for video streams
"""

import requests
import threading
import time
import io
import sys
import os
import wave
import pyaudio
import tempfile
import subprocess
from datetime import datetime

# Configuration
SERVER_URL = "http://localhost:8000"
VIDEO_STREAM_URL = f"{SERVER_URL}/stream/video"
AUDIO_STREAM_URL = f"{SERVER_URL}/stream/audio"

# Try to import OpenCV with proper error handling
try:
    import numpy as np
    import cv2
    HAS_OPENCV = True
except ImportError:
    print("Warning: OpenCV not available. Video streaming will be disabled.")
    HAS_OPENCV = False

class WebMStreamProcessor:
    """Process WebM video streams using a temporary file approach"""
    
    def __init__(self, stream_url):
        self.stream_url = stream_url
        self.running = False
        self.temp_dir = None
        self.temp_file = None
    
    def start(self):
        """Start processing the WebM stream"""
        print(f"Starting WebM stream processor for {self.stream_url}")
        
        if not HAS_OPENCV:
            print("Video streaming disabled - OpenCV not available")
            return False
        
        try:
            # Create a temporary directory to store our WebM file
            self.temp_dir = tempfile.mkdtemp(prefix="webm_stream_")
            self.temp_file = os.path.join(self.temp_dir, "stream.webm")
            
            # Start the download thread
            self.running = True
            self.download_thread = threading.Thread(target=self._download_stream)
            self.download_thread.daemon = True
            self.download_thread.start()
            
            # Wait a bit for the download to start
            time.sleep(1)
            
            # Start the playback thread
            self.playback_thread = threading.Thread(target=self._play_stream)
            self.playback_thread.daemon = True
            self.playback_thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting WebM stream processor: {e}")
            self.cleanup()
            return False
    
    def _download_stream(self):
        """Download the WebM stream to a temporary file"""
        print(f"Downloading WebM stream to {self.temp_file}")
        try:
            # Open the stream in binary mode
            response = requests.get(self.stream_url, stream=True, timeout=10)
            
            if response.status_code != 200:
                print(f"Failed to connect to video stream: {response.status_code}")
                self.running = False
                return
            
            print("Connected to video stream. Saving to temporary file...")
            
            # Open the temporary file for writing
            with open(self.temp_file, 'wb') as f:
                # Write chunks as they come in
                for chunk in response.iter_content(chunk_size=8192):
                    if not self.running:
                        break
                    if chunk:
                        f.write(chunk)
                        f.flush()  # Make sure data is written to disk
            
        except Exception as e:
            print(f"Error downloading WebM stream: {e}")
        finally:
            print("WebM download thread stopped")
    
    def _play_stream(self):
        """Play the WebM stream using OpenCV from the temporary file"""
        print("Starting video playback thread")
        last_size = 0
        retry_count = 0
        
        while self.running and retry_count < 30:  # Try for up to 30 seconds
            try:
                if not os.path.exists(self.temp_file):
                    print("Waiting for temporary file to be created...")
                    time.sleep(1)
                    continue
                
                # Check if the file is growing
                current_size = os.path.getsize(self.temp_file)
                if current_size <= last_size and current_size < 1024:  # Less than 1KB
                    print(f"Waiting for more data... Current size: {current_size} bytes")
                    time.sleep(1)
                    retry_count += 1
                    continue
                
                retry_count = 0  # Reset retry count if we're making progress
                last_size = current_size
                
                print(f"Temporary file size: {current_size} bytes. Starting playback...")
                break
                
            except Exception as e:
                print(f"Error checking file: {e}")
                time.sleep(1)
                retry_count += 1
        
        if retry_count >= 30:
            print("Timed out waiting for video data")
            return
        
        # Try using FFplay first (more reliable for WebM streams)
        if self._try_ffplay():
            return
        
        # Fallback to OpenCV if FFplay fails
        self._play_with_opencv()
    
    def _try_ffplay(self):
        """Attempt to play the WebM file using FFplay"""
        try:
            print("Trying to play stream with FFplay...")
            # Check if ffplay is available
            subprocess.run(["ffplay", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            
            # Launch ffplay with appropriate options
            cmd = [
                "ffplay",
                "-fflags", "nobuffer",
                "-flags", "low_delay",
                "-framedrop",
                "-i", self.temp_file,
                "-window_title", "Camera Stream (FFplay)",
                "-loglevel", "warning"
            ]
            
            print("Starting FFplay with command:", " ".join(cmd))
            self.ffplay_process = subprocess.Popen(cmd)
            
            # Monitor the process
            while self.running:
                if self.ffplay_process.poll() is not None:
                    # Process exited
                    print("FFplay process exited with code:", self.ffplay_process.returncode)
                    return False
                time.sleep(0.5)
            
            return True
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"FFplay not available or failed: {e}")
            return False
    
    def _play_with_opencv(self):
        """Play the WebM file using OpenCV as a fallback"""
        print("Using OpenCV for video playback")
        try:
            # Create a window
            cv2.namedWindow("Camera Stream", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Camera Stream", 640, 480)
            
            # Open the temporary file with OpenCV
            cap = cv2.VideoCapture(self.temp_file)
            
            if not cap.isOpened():
                print("Failed to open video file with OpenCV")
                return
            
            print("OpenCV video capture started")
            frame_count = 0
            start_time = time.time()
            
            # Read frames and display them
            while self.running:
                ret, frame = cap.read()
                
                if not ret:
                    print("End of file or error reading frame, reopening...")
                    # Reopen the file - it may have grown
                    cap.release()
                    time.sleep(0.5)  # Wait a bit
                    cap = cv2.VideoCapture(self.temp_file)
                    continue
                
                # Display the frame
                cv2.imshow("Camera Stream", frame)
                frame_count += 1
                
                # Calculate FPS
                elapsed = time.time() - start_time
                if elapsed >= 1.0:
                    fps = frame_count / elapsed
                    print(f"Video FPS: {fps:.2f}")
                    frame_count = 0
                    start_time = time.time()
                
                # Break loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break
            
            # Clean up
            cap.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"Error in OpenCV playback: {e}")
    
    def stop(self):
        """Stop the WebM stream processor"""
        self.running = False
        
        # Terminate ffplay if it's running
        if hasattr(self, 'ffplay_process'):
            try:
                self.ffplay_process.terminate()
                self.ffplay_process.wait(timeout=2)
            except Exception as e:
                print(f"Error terminating FFplay: {e}")
        
        # Wait for threads to finish
        if hasattr(self, 'download_thread'):
            self.download_thread.join(timeout=1.0)
        
        if hasattr(self, 'playback_thread'):
            self.playback_thread.join(timeout=1.0)
        
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files"""
        # Delete the temporary file
        if hasattr(self, 'temp_file') and self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                print(f"Removed temporary file: {self.temp_file}")
            except Exception as e:
                print(f"Error removing temporary file: {e}")
        
        # Delete the temporary directory
        if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
                print(f"Removed temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"Error removing temporary directory: {e}")

def process_audio_stream():
    """Access and play the real-time audio stream"""
    print("Starting audio stream processing...")
    
    try:
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Default audio parameters (will be updated from WAV header)
        sample_rate = 44100
        channels = 2
        sample_width = 2  # 16-bit audio
        
        print(f"Connecting to audio stream at {AUDIO_STREAM_URL}")
        
        # Open a connection to the audio stream
        response = requests.get(AUDIO_STREAM_URL, stream=True, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to connect to audio stream: {response.status_code}")
            return
        
        print("Connected to audio stream successfully!")
        
        # Create a buffer to store incoming audio data
        buffer = b''
        stream = None
        header_processed = False
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                if not header_processed and len(buffer) < 44:  # WAV header is 44 bytes
                    buffer += chunk
                    
                    # Once we have enough data, process the WAV header
                    if len(buffer) >= 44:
                        try:
                            print(f"Processing WAV header. Buffer length: {len(buffer)}")
                            # Use wave module to parse the header
                            wav_file = io.BytesIO(buffer)
                            with wave.open(wav_file, 'rb') as wf:
                                sample_rate = wf.getframerate()
                                channels = wf.getnchannels()
                                sample_width = wf.getsampwidth()
                            
                            # Now we can create the pyaudio stream with correct parameters
                            stream = p.open(format=p.get_format_from_width(sample_width),
                                           channels=channels,
                                           rate=sample_rate,
                                           output=True)
                            
                            header_processed = True
                            print(f"Audio stream opened: {sample_rate}Hz, {channels} channels")
                            print("Playing audio... (Ctrl+C to stop)")
                            
                            # Skip the header for playback
                            audio_data = buffer[44:]
                            if audio_data:
                                stream.write(audio_data)
                            buffer = b''
                        except Exception as e:
                            print(f"Error processing WAV header: {e}")
                            # If header processing fails, print the first bytes for debugging
                            print(f"Header bytes: {buffer[:min(len(buffer), 44)]}")
                            break
                else:
                    # Regular audio data, play it
                    if header_processed and stream:
                        stream.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to audio stream: {e}")
    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down...")
    except Exception as e:
        print(f"Unexpected error in audio processing: {e}")
    finally:
        if 'stream' in locals() and stream:
            stream.stop_stream()
            stream.close()
        if 'p' in locals():
            p.terminate()
        print("Audio stream processing stopped")

def main():
    """Main function to run the stream client"""
    print("Camera Server Stream Client")
    print("==========================")
    print(f"Server URL: {SERVER_URL}")
    print("Checking server connection...")
    
    try:
        # Simple check if server is accessible
        requests.get(SERVER_URL, timeout=3)
        print("Server is accessible!")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        print("Make sure the camera server is running at http://localhost:8000")
        return
    
    print("\nMake sure streaming is active on the web interface before continuing.")
    input("Press Enter when streaming is active...")
    
    print("Starting stream client...")
    
    # Start the video stream in a separate thread using the specialized WebM processor
    video_processor = WebMStreamProcessor(VIDEO_STREAM_URL)
    video_started = video_processor.start()
    if not video_started:
        print("Failed to start video stream, continuing with audio only")
    
    # Start the audio stream in the main thread
    try:
        # Process audio in the main thread
        process_audio_stream()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down...")
    finally:
        # Clean up video processing if it was started
        if video_processor:
            video_processor.stop()
    
    print("Stream client stopped")

if __name__ == "__main__":
    main()