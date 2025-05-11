"""
Piper TTS utility for Text-to-Speech functionality.
"""

import os
import tempfile
import wave
import logging
from typing import List, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import piper-tts
try:
    from piper.voice import PiperVoice  # type: ignore
except ImportError:
    logger.error(
        "piper-tts package not found. Text-to-speech functionality will be unavailable."
    )
    PiperVoice = None


class PiperTTS:
    """Wrapper class for Piper TTS functionality."""

    def __init__(self, voice_dir: str = None):
        """
        Initialize the PiperTTS client.

        Args:
            voice_dir: Directory containing .onnx and .onnx.json voice files.
                       If None, defaults to 'voices' directory in project root.
        """
        # Check common locations for voice models
        possible_voice_dirs = [
            # From docker-compose mount
            "/home/appuser/voices",
            # Project root voices directory
            os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    )
                ),
                "voices",
            ),
            # Current directory
            os.path.join(os.getcwd(), "voices"),
        ]

        self.voice_dir = voice_dir

        if not self.voice_dir:
            # Try each possible location
            for dir_path in possible_voice_dirs:
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    self.voice_dir = dir_path
                    logger.info(f"Found voice directory at: {self.voice_dir}")
                    break

        if not self.voice_dir or not os.path.exists(self.voice_dir):
            logger.warning(
                f"No valid voice directory found. Checked: {possible_voice_dirs}"
            )
            self.voice_dir = possible_voice_dirs[0]  # Default to the first option

        self.voices = {}
        self._load_available_voices()

    def _load_available_voices(self):
        """Load available voice models."""
        if not os.path.exists(self.voice_dir):
            logger.warning(f"Voice directory not found: {self.voice_dir}")
            return

        logger.info(f"Scanning for voices in: {self.voice_dir}")

        # Get all .onnx files in the voice directory
        try:
            all_files = os.listdir(self.voice_dir)
            logger.info(f"Found {len(all_files)} files in voice directory")
            voice_files = [f for f in all_files if f.endswith(".onnx")]
            logger.info(f"Found {len(voice_files)} .onnx files: {voice_files}")
        except Exception as e:
            logger.error(f"Error listing voice directory: {str(e)}")
            return

        for voice_file in voice_files:
            voice_path = os.path.join(self.voice_dir, voice_file)
            voice_id = voice_file.replace(".onnx", "")

            # Check if config file exists
            config_path = f"{voice_path}.json"
            if not os.path.exists(config_path):
                logger.warning(f"No config file for voice model: {voice_file}")
                continue

            self.voices[voice_id] = {"model": voice_path, "config": config_path}

        logger.info(
            f"Loaded {len(self.voices)} voice models: {list(self.voices.keys())}"
        )

    def get_available_voices(self) -> List[str]:
        """Get a list of available voice IDs."""
        return list(self.voices.keys())

    def text_to_speech(
        self,
        text: str,
        voice_id: str = None,
        output_path: Optional[str] = None,
        speaker_id: int = 0,
    ) -> Union[str, bytes]:
        """
        Convert text to speech.

        Args:
            text: Text to convert to speech.
            voice_id: Voice ID to use (e.g., 'en_US-lessac-medium').
                     If None, uses the first available voice.
            output_path: Path to save audio file. If None, returns audio data in memory.
            speaker_id: Speaker ID for multi-speaker models (default: 0).

        Returns:
            If output_path is provided: Path to the saved audio file.
            If output_path is None: Audio data as bytes.

        Raises:
            ValueError: If PiperVoice is not available or if no voices are available.
        """
        if PiperVoice is None:
            raise ValueError(
                "Piper TTS functionality is not available. Please install piper-tts."
            )

        if not self.voices:
            raise ValueError("No voice models are available.")

        # Validate input text
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        text = text.strip()

        # Use specified voice or default to first available
        if voice_id is None:
            voice_id = next(iter(self.voices.keys()))
        elif voice_id not in self.voices:
            raise ValueError(
                f"Voice '{voice_id}' not found. Available voices: {list(self.voices.keys())}"
            )

        voice_data = self.voices[voice_id]
        print(f"Using voice: {voice_id}, model: {voice_data['model']}")

        # Create temporary file if no output path specified
        temp_file = None
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            output_path = temp_file.name
            print(f"Created temporary file: {output_path}")

        try:
            # Load voice model
            voice = PiperVoice.load(
                voice_data["model"], config_path=voice_data["config"]
            )
            print("Loaded voice model successfully")

            # Check if the model supports multiple speakers
            use_speaker_id = (
                hasattr(voice.config, "num_speakers") and voice.config.num_speakers > 1
            )

            if use_speaker_id:
                print(f"Using speaker_id: {speaker_id}")
            else:
                print("Single speaker model detected, ignoring speaker_id")

            # Generate speech - create a wave file and pass it to synthesize
            with wave.open(output_path, "wb") as wav_file:
                if use_speaker_id:
                    voice.synthesize(text, wav_file, speaker_id=speaker_id)
                else:
                    # Don't pass speaker_id for single-speaker models
                    voice.synthesize(text, wav_file)

            # Verify the file was created and has content
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"Generated audio file size: {file_size} bytes")
                if file_size < 100:  # Basic check for valid audio
                    print("Warning: Generated audio file is very small, might be empty")
            else:
                print("Warning: Output audio file was not created")

            # Return file path or audio data
            if temp_file is not None:
                with open(output_path, "rb") as f:
                    audio_data = f.read()
                print(f"Read {len(audio_data)} bytes from temporary file")
                os.unlink(output_path)
                return audio_data
            else:
                return output_path

        except Exception as e:
            if temp_file is not None and os.path.exists(output_path):
                os.unlink(output_path)
            raise ValueError(f"Text-to-speech synthesis failed: {str(e)}")
