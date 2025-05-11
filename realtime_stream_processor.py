#!/usr/bin/env python3
"""
Realtime Stream Processor - Access audio and video streams separately
for real-time processing without saving to disk
"""

import threading
import time
import requests
import io
import wave
import numpy as np
import pyaudio
import cv2

# Stream URLs
SERVER_URL = "http://localhost:8000"
VIDEO_STREAM_URL = f"{SERVER_URL}/stream/video"
AUDIO_STREAM_URL = f"{SERVER_URL}/stream/audio"

class VideoProcessor(threading.Thread):
    """Process video stream in real-time"""
    
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = False
        self.frame_buffer = None
        self.new_frame_event = threading.Event()
        self.lock = threading.Lock()
    
    def run(self):
        """Main processing loop"""
        self.running = True
        print(f"Connecting to video stream at {VIDEO_STREAM_URL}")
        
        try:
            # Open the video stream
            cap = cv2.VideoCapture(VIDEO_STREAM_URL)
            if not cap.isOpened():
                print("Failed to open video stream")
                return
                
            print("Video stream connected!")
            
            # Process frames in a loop
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("Error reading video frame")
                    time.sleep(0.1)
                    continue
                
                # Store the frame in the buffer
                with self.lock:
                    self.frame_buffer = frame.copy()
                    
                # Notify that a new frame is available
                self.new_frame_event.set()
                self.new_frame_event.clear()
            
            cap.release()
            
        except Exception as e:
            print(f"Error in video processing: {e}")
        finally:
            print("Video processor stopped")
    
    def get_current_frame(self):
        """Get the most recent video frame"""
        with self.lock:
            if self.frame_buffer is None:
                return None
            return self.frame_buffer.copy()
    
    def wait_for_frame(self, timeout=1.0):
        """Wait for a new frame to arrive"""
        return self.new_frame_event.wait(timeout)
    
    def stop(self):
        """Stop the video processor"""
        self.running = False

class AudioProcessor(threading.Thread):
    """Process audio stream in real-time"""
    
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = False
        self.audio_buffer = None
        self.new_audio_event = threading.Event()
        self.lock = threading.Lock()
        
        # Audio parameters (will be updated from stream)
        self.sample_rate = 44100
        self.channels = 2
        self.sample_width = 2  # 16-bit
        
        # Audio processing initialized flag
        self.audio_initialized = False
    
    def run(self):
        """Main processing loop"""
        self.running = True
        print(f"Connecting to audio stream at {AUDIO_STREAM_URL}")
        
        try:
            # Initialize PyAudio for playback (optional)
            p = pyaudio.PyAudio()
            
            # Open the audio stream
            response = requests.get(AUDIO_STREAM_URL, stream=True, timeout=10)
            if response.status_code != 200:
                print(f"Failed to connect to audio stream: {response.status_code}")
                return
                
            print("Audio stream connected!")
            
            # Buffer for WAV header
            header_buffer = b''
            
            # Process audio chunks
            for chunk in response.iter_content(chunk_size=1024):
                if not self.running:
                    break
                
                if not self.audio_initialized:
                    # Collect data for WAV header (44 bytes)
                    header_buffer += chunk
                    if len(header_buffer) >= 44:
                        try:
                            # Parse WAV header
                            wav_file = io.BytesIO(header_buffer)
                            with wave.open(wav_file, 'rb') as wf:
                                self.sample_rate = wf.getframerate()
                                self.channels = wf.getnchannels()
                                self.sample_width = wf.getsampwidth()
                            
                            print(f"Audio format: {self.sample_rate}Hz, {self.channels} channels")
                            self.audio_initialized = True
                            
                            # Optional: Create audio playback stream
                            self.audio_stream = p.open(
                                format=p.get_format_from_width(self.sample_width),
                                channels=self.channels,
                                rate=self.sample_rate,
                                output=True
                            )
                            
                            # Process remaining audio data
                            audio_data = header_buffer[44:]
                            if audio_data:
                                self._process_audio_chunk(audio_data)
                                # Optional: Play audio
                                self.audio_stream.write(audio_data)
                            
                            header_buffer = b''
                        except Exception as e:
                            print(f"Error parsing WAV header: {e}")
                            return
                else:
                    # Process regular audio chunk
                    self._process_audio_chunk(chunk)
                    # Optional: Play audio
                    if hasattr(self, 'audio_stream'):
                        self.audio_stream.write(chunk)
        
        except Exception as e:
            print(f"Error in audio processing: {e}")
        finally:
            if 'p' in locals():
                if hasattr(self, 'audio_stream'):
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                p.terminate()
            print("Audio processor stopped")
    
    def _process_audio_chunk(self, chunk):
        """Process an audio chunk (implement your real-time audio processing here)"""
        # Convert audio bytes to numpy array for processing
        try:
            if self.sample_width == 2:  # 16-bit audio
                fmt = np.int16
            elif self.sample_width == 4:  # 32-bit audio
                fmt = np.int32
            else:
                fmt = np.uint8
            
            # Convert to numpy array
            audio_array = np.frombuffer(chunk, dtype=fmt)
            
            # For stereo audio, split into channels
            if self.channels == 2:
                left = audio_array[0::2]
                right = audio_array[1::2]
                
                # Example: Compute audio level (RMS)
                if len(left) > 0:
                    rms_left = np.sqrt(np.mean(np.square(left.astype(np.float32))))
                    rms_right = np.sqrt(np.mean(np.square(right.astype(np.float32))))
                    
                    # Normalize to 0-1 range (assuming 16-bit audio)
                    level_left = rms_left / 32768
                    level_right = rms_right / 32768
                    
                    # Store in buffer
                    with self.lock:
                        self.audio_buffer = (level_left, level_right)
                    
                    # Notify that new audio data is available
                    self.new_audio_event.set()
                    self.new_audio_event.clear()
            
        except Exception as e:
            print(f"Error processing audio data: {e}")
    
    def get_audio_levels(self):
        """Get the most recent audio levels"""
        with self.lock:
            return self.audio_buffer
    
    def wait_for_audio(self, timeout=1.0):
        """Wait for new audio data"""
        return self.new_audio_event.wait(timeout)
    
    def stop(self):
        """Stop the audio processor"""
        self.running = False

class StreamProcessor:
    """Main class to process both audio and video streams"""
    
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.audio_processor = AudioProcessor()
    
    def start(self):
        """Start processing both streams"""
        self.video_processor.start()
        self.audio_processor.start()
    
    def stop(self):
        """Stop processing"""
        self.video_processor.stop()
        self.audio_processor.stop()
        self.video_processor.join(timeout=1)
        self.audio_processor.join(timeout=1)

def main():
    """Example usage of the stream processor"""
    print("Real-time Stream Processor")
    print("=========================")
    
    # Create and start the stream processor
    processor = StreamProcessor()
    processor.start()
    
    try:
        print("\nProcessing streams... Press Ctrl+C to stop.")
        print("Opening display window...")
        
        # Main processing loop - access both video and audio in real-time
        while True:
            # Process video frames
            if processor.video_processor.wait_for_frame(timeout=0.1):
                frame = processor.video_processor.get_current_frame()
                if frame is not None:
                    # Display the frame
                    cv2.imshow('Video Stream', frame)
                    
                    # Check for key press
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
            
            # Process audio levels
            audio_levels = processor.audio_processor.get_audio_levels()
            if audio_levels is not None:
                left_level, right_level = audio_levels
                # Create a simple audio level visualizer
                bars = int(left_level * 20)
                print(f"Audio Level: {'█' * bars}{' ' * (20-bars)} {left_level:.2f}", end='\r')
            
            time.sleep(0.01)  # Small sleep to prevent high CPU usage
            
    except KeyboardInterrupt:
        print("\nExiting stream processor...")
    finally:
        processor.stop()
        cv2.destroyAllWindows()
        print("Stream processing stopped.")

if __name__ == "__main__":
    main()