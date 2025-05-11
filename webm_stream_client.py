#!/usr/bin/env python3
"""
WebM Stream Client - Specialized client to handle WebM video streams
Uses a buffered approach to properly handle the WebM header and streaming format
"""

import os
import sys
import time
import tempfile
import threading
import subprocess
import requests
from datetime import datetime

# Configuration
SERVER_URL = "http://localhost:8000"
VIDEO_STREAM_URL = f"{SERVER_URL}/stream/video"

class WebMStreamClient:
    """Client to handle WebM streams using a buffer-based approach"""
    
    def __init__(self, stream_url):
        self.stream_url = stream_url
        self.running = False
        self.temp_dir = None
        self.temp_file = None
        self.ffplay_process = None
        
    def start(self):
        """Start processing the WebM stream"""
        print(f"WebM Stream Client for {self.stream_url}")
        print("=====================================")
        
        try:
            # Create a temporary directory and file for the stream
            self.temp_dir = tempfile.mkdtemp(prefix="webm_stream_")
            self.temp_file = os.path.join(self.temp_dir, "stream.webm")
            print(f"Using temporary file: {self.temp_file}")
            
            # Check if server is accessible
            try:
                print(f"Checking connection to server...")
                response = requests.head(SERVER_URL, timeout=5)
                print(f"Server is accessible! Status: {response.status_code}")
            except requests.RequestException as e:
                print(f"Error connecting to server: {e}")
                print("Please make sure the camera server is running.")
                return False
            
            # Start the stream download thread
            print("Starting stream download...")
            self.running = True
            self.download_thread = threading.Thread(target=self._download_stream)
            self.download_thread.daemon = True
            self.download_thread.start()
            
            # Wait a bit for initial data download
            print("Waiting for initial data...")
            time.sleep(3)  # Allow some time for initial data to be downloaded
            
            # Check if we have enough data
            if not os.path.exists(self.temp_file) or os.path.getsize(self.temp_file) < 1024:
                print("Not enough data received yet. Please make sure streaming is active.")
                time.sleep(2)
            
            # Start the player
            return self._start_player()
            
        except Exception as e:
            print(f"Error starting WebM stream client: {e}")
            self.cleanup()
            return False
            
    def _download_stream(self):
        """Download the WebM stream to a temporary file"""
        print(f"Connecting to video stream at {self.stream_url}")
        try:
            # Open the stream with no timeout to keep connection open
            response = requests.get(self.stream_url, stream=True, timeout=None)
            
            if response.status_code != 200:
                print(f"Failed to connect to video stream: {response.status_code}")
                self.running = False
                return
                
            print("Connected to video stream successfully! Downloading data...")
            
            # Save stream data to the temporary file
            with open(self.temp_file, 'wb') as f:
                start_time = time.time()
                total_bytes = 0
                
                for chunk in response.iter_content(chunk_size=16384):  # 16KB chunks for efficiency
                    if not self.running:
                        break
                    
                    if chunk:
                        f.write(chunk)
                        f.flush()  # Ensure data is written to disk immediately
                        
                        # Track download progress
                        total_bytes += len(chunk)
                        elapsed = time.time() - start_time
                        if elapsed >= 5:  # Report every 5 seconds
                            rate = total_bytes / elapsed / 1024  # KB/s
                            print(f"Download rate: {rate:.2f} KB/s, Total: {total_bytes/1024:.2f} KB")
            
        except requests.RequestException as e:
            print(f"Error downloading stream: {e}")
        except Exception as e:
            print(f"Unexpected error in download thread: {e}")
        finally:
            print("Download thread stopped")
    
    def _start_player(self):
        """Start playing the WebM stream with FFplay"""
        try:
            print("Starting FFplay for WebM playback...")
            
            # Command with optimized settings for WebM streaming
            cmd = [
                "ffplay",
                "-fflags", "+genpts+discardcorrupt+nobuffer",  # Handle streaming issues
                "-flags", "low_delay",                       # Reduce latency
                "-framedrop",                                # Drop frames if needed to maintain sync
                "-vf", "setpts=0.5*PTS",                     # Speed up slightly if behind
                "-i", self.temp_file,                        # Input file
                "-window_title", "WebM Camera Stream",       # Window title
                "-loglevel", "warning"                       # Reduce log noise
            ]
            
            print("Starting FFplay with command:", " ".join(cmd))
            
            # Start FFplay in a subprocess
            self.ffplay_process = subprocess.Popen(cmd)
            
            # Keep the main thread alive
            try:
                print("\nPlaying video stream... Press Ctrl+C to stop.")
                
                while self.running and self.ffplay_process.poll() is None:
                    time.sleep(0.5)
                    
                if self.ffplay_process.poll() is not None:
                    exit_code = self.ffplay_process.returncode
                    print(f"\nFFplay exited with code: {exit_code}")
                    if exit_code != 0:
                        print("FFplay encountered an error. Please check your stream source.")
                        return False
            
            except KeyboardInterrupt:
                print("\nInterrupted by user. Shutting down...")
                self.stop()
            
            return True
                
        except FileNotFoundError:
            print("Error: FFplay not found. Please install FFmpeg/FFplay.")
            return False
        except Exception as e:
            print(f"Error starting FFplay: {e}")
            return False
    
    def stop(self):
        """Stop the stream client"""
        self.running = False
        
        # Stop FFplay
        if self.ffplay_process:
            try:
                print("Stopping FFplay...")
                self.ffplay_process.terminate()
                self.ffplay_process.wait(timeout=2)
            except Exception as e:
                print(f"Error terminating FFplay: {e}")
        
        # Wait for download thread to stop
        if hasattr(self, 'download_thread') and self.download_thread.is_alive():
            print("Waiting for download thread to stop...")
            self.download_thread.join(timeout=2)
        
        self.cleanup()
        print("Stream client stopped.")
    
    def cleanup(self):
        """Clean up temporary files"""
        # Delete temporary file
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                print(f"Removed temporary file.")
            except Exception as e:
                print(f"Error removing temporary file: {e}")
        
        # Remove temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
                print(f"Removed temporary directory.")
            except Exception as e:
                print(f"Error removing temporary directory: {e}")

def main():
    """Main function to start the WebM stream client"""
    client = WebMStreamClient(VIDEO_STREAM_URL)
    
    try:
        if client.start():
            # Wait for user to stop
            while True:
                time.sleep(1)
        else:
            print("Failed to start stream client.")
    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down...")
    finally:
        client.stop()

if __name__ == "__main__":
    main()