#!/usr/bin/env python3
"""
Stream Extractor - Extract both audio and video streams from the camera server
Saves audio as WAV and video as WebM files for easy playback
"""

import os
import time
import requests
import threading
from datetime import datetime

# Configuration
SERVER_URL = "http://localhost:8000"
VIDEO_STREAM_URL = f"{SERVER_URL}/stream/video"
AUDIO_STREAM_URL = f"{SERVER_URL}/stream/audio"
OUTPUT_DIR = "extracted_streams"

def ensure_directory(directory):
    """Ensure that the output directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def extract_video_stream():
    """Extract the video stream and save it as WebM file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = os.path.join(OUTPUT_DIR, f"video_stream_{timestamp}.webm")
    
    print(f"Connecting to video stream at {VIDEO_STREAM_URL}")
    try:
        response = requests.get(VIDEO_STREAM_URL, stream=True, timeout=None)
        
        if response.status_code != 200:
            print(f"Failed to connect to video stream: {response.status_code}")
            return
            
        print(f"Connected to video stream! Saving to {video_filename}")
        
        with open(video_filename, 'wb') as f:
            start_time = time.time()
            bytes_received = 0
            
            for chunk in response.iter_content(chunk_size=16384):  # 16KB chunks
                f.write(chunk)
                bytes_received += len(chunk)
                
                # Print progress every 5 seconds
                elapsed = time.time() - start_time
                if elapsed >= 5:
                    rate = bytes_received / elapsed / 1024  # KB/s
                    print(f"Video: Received {bytes_received/1024:.2f} KB at {rate:.2f} KB/s")
                    start_time = time.time()
                    bytes_received = 0
    except Exception as e:
        print(f"Error extracting video stream: {e}")
    finally:
        print("Video stream extraction stopped")

def extract_audio_stream():
    """Extract the audio stream and save it as WAV file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = os.path.join(OUTPUT_DIR, f"audio_stream_{timestamp}.wav")
    
    print(f"Connecting to audio stream at {AUDIO_STREAM_URL}")
    try:
        response = requests.get(AUDIO_STREAM_URL, stream=True, timeout=None)
        
        if response.status_code != 200:
            print(f"Failed to connect to audio stream: {response.status_code}")
            return
            
        print(f"Connected to audio stream! Saving to {audio_filename}")
        
        with open(audio_filename, 'wb') as f:
            start_time = time.time()
            bytes_received = 0
            
            for chunk in response.iter_content(chunk_size=8192):  # 8KB chunks
                f.write(chunk)
                bytes_received += len(chunk)
                
                # Print progress every 5 seconds
                elapsed = time.time() - start_time
                if elapsed >= 5:
                    rate = bytes_received / elapsed / 1024  # KB/s
                    print(f"Audio: Received {bytes_received/1024:.2f} KB at {rate:.2f} KB/s")
                    start_time = time.time()
                    bytes_received = 0
    except Exception as e:
        print(f"Error extracting audio stream: {e}")
    finally:
        print("Audio stream extraction stopped")

def main():
    """Main function to extract audio and video streams"""
    print("Camera Server Stream Extractor")
    print("=============================")
    print(f"Server URL: {SERVER_URL}")
    
    # Check server connection
    try:
        print("Checking server connection...")
        response = requests.get(SERVER_URL, timeout=5)
        print(f"Server is accessible! Status: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error connecting to server: {e}")
        print("Make sure the camera server is running at http://localhost:8000")
        return
    
    # Create output directory
    ensure_directory(OUTPUT_DIR)
    
    print("\nMake sure streaming is active on the web interface before continuing.")
    input("Press Enter when streaming is active...")
    
    # Start extraction threads
    video_thread = threading.Thread(target=extract_video_stream)
    audio_thread = threading.Thread(target=extract_audio_stream)
    
    video_thread.daemon = True
    audio_thread.daemon = True
    
    print("Starting stream extraction...")
    video_thread.start()
    audio_thread.start()
    
    try:
        print("\nExtracting streams... Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting stream extractor...")
    
    print("Stream extraction complete. Files are saved in the 'extracted_streams' directory.")
    print(f"You can play the files with: ffplay {OUTPUT_DIR}/video_stream_*.webm")
    print(f"Or: ffplay {OUTPUT_DIR}/audio_stream_*.wav")

if __name__ == "__main__":
    main()