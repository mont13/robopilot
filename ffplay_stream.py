#!/usr/bin/env python3
"""
FFplay Stream Client - Uses FFplay to display streams from the camera server
This script launches FFplay with proper settings for WebM streaming
"""

import subprocess
import sys
import time
import requests
import os
from datetime import datetime

# Configuration
SERVER_URL = "http://localhost:8000"
VIDEO_STREAM_URL = f"{SERVER_URL}/stream/video"
AUDIO_STREAM_URL = f"{SERVER_URL}/stream/audio"

def check_ffplay_installed():
    """Check if FFplay is installed on the system"""
    try:
        subprocess.run(["ffplay", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        print("Error: FFplay is not installed or not in your PATH")
        print("Please install FFmpeg/FFplay to use this script")
        return False

def check_server_running():
    """Check if the camera server is running"""
    try:
        response = requests.get(SERVER_URL, timeout=3)
        return True
    except requests.exceptions.RequestException:
        print(f"Error: Could not connect to camera server at {SERVER_URL}")
        print("Make sure the camera server is running")
        return False

def play_video_stream():
    """Play the video stream using FFplay with specific settings for WebM"""
    # FFplay command with options for WebM streaming and low latency
    cmd = [
        "ffplay",
        "-fflags", "nobuffer",  # Reduce buffering for lower latency
        "-flags", "low_delay",  # Low delay mode
        "-framedrop",          # Drop frames when CPU is too slow
        "-i", VIDEO_STREAM_URL, # Input stream URL
        "-window_title", "Camera Stream - Video",
        "-loglevel", "warning"  # Reduce log output
    ]
    
    try:
        print(f"Starting FFplay for video stream...")
        print(f"Press Q to stop playback")
        
        # Run FFplay
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error running FFplay for video: {e}")

def play_audio_stream():
    """Play the audio stream using FFplay"""
    # FFplay command for audio
    cmd = [
        "ffplay",
        "-i", AUDIO_STREAM_URL,
        "-window_title", "Camera Stream - Audio",
        "-loglevel", "warning"
    ]
    
    try:
        print(f"Starting FFplay for audio stream...")
        print(f"Press Q to stop playback")
        
        # Run FFplay
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error running FFplay for audio: {e}")

def play_combined_stream():
    """Use FFplay to access both streams at once (advanced)"""
    # For combined playback, we'll access a sample file to demo the capability
    # This is a demo of how it could work, but actual implementation depends on server support
    print("Note: Combined playback requires specific server support.")
    print("Using video-only stream for demonstration.")
    
    # Use the same settings as video stream
    play_video_stream()

def display_menu():
    """Display a menu of stream options"""
    print("\nCamera Server Stream Options:")
    print("1. Video Stream")
    print("2. Audio Stream")
    print("3. Both Streams (video with audio)")
    print("q. Quit")
    
    choice = input("\nChoose an option (1/2/3/q): ")
    
    if choice == '1':
        play_video_stream()
        return True
    elif choice == '2':
        play_audio_stream()
        return True
    elif choice == '3':
        play_combined_stream()
        return True
    elif choice.lower() == 'q':
        return False
    else:
        print("Invalid choice. Please try again.")
        return True

def main():
    """Main function to run the FFplay stream client"""
    print("Camera Server FFplay Stream Client")
    print("=================================")
    
    # Check if FFplay is installed
    if not check_ffplay_installed():
        return
    
    # Check if server is running
    if not check_server_running():
        return
    
    print("\nMake sure streaming is active on the web interface before continuing.")
    input("Press Enter when streaming is active...")
    
    # Display menu and get choice
    continue_running = True
    while continue_running:
        continue_running = display_menu()
    
    print("Exiting...")

if __name__ == "__main__":
    main()