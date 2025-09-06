"""
Piper TTS utility for Text-to-Speech functionality using Python piper-tts.
"""

import logging
import os
import tempfile
import time
import wave
from pathlib import Path
from typing import Any

from piper import PiperVoice
from piper.voice import SynthesisConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PiperTTS:
    """Wrapper class for Piper TTS functionality using Python implementation."""

    def __init__(
        self, voice_dir: str | None = None, default_voice: str = "cs_CZ-jirka-medium"
    ):
        """
        Initialize the PiperTTS client.

        Args:
            voice_dir: Directory containing .onnx and .onnx.json voice files.
                      If None, defaults to 'voices' directory in project root.
            default_voice: Default voice model to use (without .onnx extension)
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
        self.default_voice = default_voice
        self.loaded_voices = {}  # Cache for loaded voice models

        if not self.voice_dir:
            # Try each possible location
            for dir_path in possible_voice_dirs:
                if Path(dir_path).exists() and Path(dir_path).is_dir():
                    self.voice_dir = dir_path
                    logger.info(f"Found voice directory at: {self.voice_dir}")
                    break

        if not self.voice_dir or not Path(self.voice_dir).exists():
            logger.warning(
                f"No valid voice directory found. Checked: {possible_voice_dirs}"
            )
            # Create default voice directory
            self.voice_dir = possible_voice_dirs[0]  # Default to the first option
            Path(self.voice_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created voice directory at: {self.voice_dir}")

        self.voices = {}
        self._load_available_voices()

    def _load_available_voices(self):
        """Discover available voice models in the voice directory."""
        if not Path(self.voice_dir).exists():
            logger.warning(f"Voice directory not found: {self.voice_dir}")
            return

        logger.info(f"Scanning for voices in: {self.voice_dir}")

        try:
            all_files = os.listdir(self.voice_dir)
            logger.info(f"Found {len(all_files)} files in voice directory")
            voice_files = [f for f in all_files if f.endswith(".onnx")]
            logger.info(f"Found {len(voice_files)} .onnx files: {voice_files}")
        except Exception as e:
            logger.error(f"Error listing voice directory: {e}")
            return

        for voice_file in voice_files:
            voice_path = os.path.join(self.voice_dir, voice_file)
            voice_id = voice_file.replace(".onnx", "")

            # Check if config file exists
            config_path = f"{voice_path}.json"
            if not Path(config_path).exists():
                logger.warning(f"No config file for voice model: {voice_file}")
                # Try without .json extension (some models may not need it)
                self.voices[voice_id] = {"model": voice_path, "config": None}
            else:
                self.voices[voice_id] = {"model": voice_path, "config": config_path}

        logger.info(
            f"Discovered {len(self.voices)} voice models: {list(self.voices.keys())}"
        )

    def get_available_voices(self) -> list[str]:
        """Get a list of available voice IDs."""
        return list(self.voices.keys())

    def download_voice_if_needed(self, voice_name: str = None) -> Path:
        """
        Download a voice model if it doesn't exist locally.

        Args:
            voice_name: Name of the voice to download (e.g., 'cs_CZ-jirka-medium')
                       If None, uses default_voice

        Returns:
            Path to the voice model file
        """
        if voice_name is None:
            voice_name = self.default_voice

        voice_path = Path(self.voice_dir) / f"{voice_name}.onnx"

        if voice_path.exists():
            logger.info(f"Voice model already exists: {voice_path}")
            return voice_path

        logger.warning(f"Voice model not found: {voice_path}")
        logger.info("Please download voice models manually from:")
        logger.info("https://github.com/rhasspy/piper/releases")
        logger.info(f"Extract to: {self.voice_dir}")

        return voice_path

    def _load_voice(self, voice_id: str) -> PiperVoice:
        """
        Load a voice model, with caching.

        Args:
            voice_id: Voice ID to load

        Returns:
            Loaded PiperVoice instance
        """
        # Check if voice is already loaded
        if voice_id in self.loaded_voices:
            return self.loaded_voices[voice_id]

        # Check if voice exists
        if voice_id not in self.voices:
            raise ValueError(
                f"Voice '{voice_id}' not found. Available voices: {list(self.voices.keys())}"
            )

        voice_data = self.voices[voice_id]
        logger.info(f"Loading voice: {voice_id} from {voice_data['model']}")

        try:
            start_time = time.time()

            # Load voice with or without config
            if voice_data["config"]:
                voice = PiperVoice.load(
                    voice_data["model"], config_path=voice_data["config"]
                )
            else:
                voice = PiperVoice.load(voice_data["model"])

            end_time = time.time()
            logger.info(
                f"Voice loaded successfully in {end_time - start_time:.2f} seconds"
            )

            # Cache the loaded voice
            self.loaded_voices[voice_id] = voice
            return voice

        except Exception as e:
            logger.error(f"Failed to load voice {voice_id}: {e}")
            raise ValueError(f"Failed to load voice '{voice_id}': {e}")

    def create_synthesis_config(
        self,
        volume: float = 1.0,
        length_scale: float = 1.0,
        noise_scale: float = 0.667,
        noise_w_scale: float = 0.8,
        normalize_audio: bool = True,
    ) -> SynthesisConfig:
        """
        Create a synthesis configuration.

        Args:
            volume: Volume level (0.0 to 1.0)
            length_scale: Speed of speech (1.0 = normal, >1.0 = slower, <1.0 = faster)
            noise_scale: Audio variation (lower = less variation)
            noise_w_scale: Speaking variation (lower = less variation)
            normalize_audio: Whether to normalize audio output

        Returns:
            SynthesisConfig object
        """
        return SynthesisConfig(
            volume=volume,
            length_scale=length_scale,
            noise_scale=noise_scale,
            noise_w_scale=noise_w_scale,
            normalize_audio=normalize_audio,
        )

    def text_to_speech(
        self,
        text: str,
        voice_id: str | None = None,
        output_path: str | None = None,
        synthesis_config: SynthesisConfig | None = None,
    ) -> str | bytes:
        """
        Convert text to speech.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use. If None, uses default_voice or first available
            output_path: Path to save audio file. If None, returns audio data in memory
            synthesis_config: Custom synthesis configuration. If None, uses defaults

        Returns:
            If output_path is provided: Path to the saved audio file
            If output_path is None: Audio data as bytes

        Raises:
            ValueError: If no voices are available or if text is empty
        """
        # Validate input text
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        text = text.strip()

        # Determine voice to use
        if voice_id is None:
            if self.default_voice in self.voices:
                voice_id = self.default_voice
            elif self.voices:
                voice_id = next(iter(self.voices.keys()))
            else:
                raise ValueError("No voice models are available")

        # Load voice
        voice = self._load_voice(voice_id)
        logger.info(f"Using voice: {voice_id}")

        # Create temporary file if no output path specified
        temp_file = None
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            output_path = temp_file.name
            temp_file.close()  # Close the file handle so it can be written to
            logger.debug(f"Created temporary file: {output_path}")

        try:
            logger.info(
                f"Synthesizing text: '{text[:50]}{'...' if len(text) > 50 else ''}'"
            )
            start_time = time.time()

            # Generate speech
            with wave.open(output_path, "wb") as wav_file:
                if synthesis_config:
                    voice.synthesize_wav(text, wav_file, syn_config=synthesis_config)
                else:
                    voice.synthesize_wav(text, wav_file)

            end_time = time.time()
            synthesis_time = end_time - start_time
            logger.info(f"Synthesis completed in {synthesis_time:.2f} seconds")

            # Verify the file was created and has content
            if Path(output_path).exists():
                file_size = os.path.getsize(output_path)
                logger.info(f"Generated audio file size: {file_size} bytes")
                if file_size < 100:  # Basic check for valid audio
                    logger.warning("Generated audio file is very small, might be empty")
            else:
                raise ValueError("Output audio file was not created")

            # Return file path or audio data
            if temp_file is not None:
                with open(output_path, "rb") as f:
                    audio_data = f.read()
                logger.debug(f"Read {len(audio_data)} bytes from temporary file")
                os.unlink(output_path)
                return audio_data
            else:
                return output_path

        except Exception as e:
            if temp_file is not None and Path(output_path).exists():
                os.unlink(output_path)
            logger.error(f"Text-to-speech synthesis failed: {e}")
            raise ValueError(f"Text-to-speech synthesis failed: {e}")

    def text_to_speech_streaming(
        self,
        text: str,
        voice_id: str | None = None,
        synthesis_config: SynthesisConfig | None = None,
    ):
        """
        Convert text to speech with streaming output.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use. If None, uses default_voice or first available
            synthesis_config: Custom synthesis configuration

        Yields:
            Audio chunks with sample rate, width, and channels information
        """
        # Validate input text
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        text = text.strip()

        # Determine voice to use
        if voice_id is None:
            if self.default_voice in self.voices:
                voice_id = self.default_voice
            elif self.voices:
                voice_id = next(iter(self.voices.keys()))
            else:
                raise ValueError("No voice models are available")

        # Load voice
        voice = self._load_voice(voice_id)
        logger.info(f"Starting streaming synthesis with voice: {voice_id}")

        try:
            start_time = time.time()

            # Generate audio chunks
            if synthesis_config:
                chunks = voice.synthesize(text, syn_config=synthesis_config)
            else:
                chunks = voice.synthesize(text)

            chunk_count = 0
            for chunk in chunks:
                chunk_count += 1
                yield {
                    "audio_data": chunk.audio_int16_bytes,
                    "sample_rate": chunk.sample_rate,
                    "sample_width": chunk.sample_width,
                    "channels": chunk.sample_channels,
                }

            end_time = time.time()
            logger.info(
                f"Streaming synthesis completed in {end_time - start_time:.2f} seconds "
                f"({chunk_count} chunks)"
            )

        except Exception as e:
            logger.error(f"Streaming synthesis failed: {e}")
            raise ValueError(f"Streaming synthesis failed: {e}")

    def get_voice_info(self, voice_id: str | None = None) -> dict[str, Any]:
        """
        Get information about a voice model.

        Args:
            voice_id: Voice ID to get info for. If None, uses default voice

        Returns:
            Dictionary with voice information
        """
        if voice_id is None:
            if self.default_voice in self.voices:
                voice_id = self.default_voice
            elif self.voices:
                voice_id = next(iter(self.voices.keys()))
            else:
                raise ValueError("No voice models are available")

        if voice_id not in self.voices:
            raise ValueError(f"Voice '{voice_id}' not found")

        voice_data = self.voices[voice_id]

        # Try to load voice to get additional info
        try:
            voice = self._load_voice(voice_id)
            config_info = {
                "sample_rate": getattr(voice.config, "sample_rate", "unknown"),
                "num_speakers": getattr(voice.config, "num_speakers", 1),
                "language": getattr(voice.config, "language", "unknown"),
            }
        except Exception as e:
            logger.warning(f"Could not load voice for detailed info: {e}")
            config_info = {"error": str(e)}

        return {
            "voice_id": voice_id,
            "model_path": voice_data["model"],
            "config_path": voice_data["config"],
            "config_info": config_info,
            "is_loaded": voice_id in self.loaded_voices,
        }

    def test_synthesis(
        self,
        test_text: str = "Welcome to the world of speech synthesis!",
        voice_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Test synthesis functionality.

        Args:
            test_text: Text to use for testing
            voice_id: Voice ID to test with

        Returns:
            Dictionary with test results
        """
        logger.info("Starting synthesis test")

        try:
            start_time = time.time()

            # Perform basic synthesis test
            audio_data = self.text_to_speech(test_text, voice_id=voice_id)

            end_time = time.time()
            test_time = end_time - start_time

            result = {
                "success": True,
                "test_text": test_text,
                "voice_used": voice_id or "default",
                "audio_size": len(audio_data)
                if isinstance(audio_data, bytes)
                else "file",
                "synthesis_time": test_time,
                "message": "Basic synthesis test completed successfully",
            }

            logger.info(
                f"Synthesis test completed successfully in {test_time:.2f} seconds"
            )
            return result

        except Exception as e:
            logger.error(f"Synthesis test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Synthesis test failed",
            }
