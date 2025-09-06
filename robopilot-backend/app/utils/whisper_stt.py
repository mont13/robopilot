"""
Whisper STT utility for Speech-to-Text functionality using Python openai-whisper.
"""

# Set up logging
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import whisper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperSTT:
    """Wrapper class for OpenAI Whisper STT functionality."""

    def __init__(
        self, model_name: str = "turbo", device: str = None, temp_dir: str = None
    ):
        """
        Initialize the WhisperSTT client.

        Args:
            model_name: Whisper model to use. Options: tiny, base, small, medium, large, turbo
                       Default: turbo (fast and accurate)
            device: Device to run inference on ('cpu', 'cuda'). If None, auto-detects
            temp_dir: Directory to use for temporary files. If None, uses system default
        """
        self.model_name = model_name
        self.device = device
        self.temp_dir = temp_dir
        self.model = None

        # Validate model name
        available_models = whisper.available_models()
        if model_name not in available_models:
            raise ValueError(
                f"Model '{model_name}' not available. Available models: {', '.join(available_models)}"
            )

        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 9):
            logger.warning("Whisper works best with Python 3.9 or later")

        # Ensure temp directory exists if specified
        if self.temp_dir and not Path(self.temp_dir).exists():
            try:
                os.makedirs(self.temp_dir, exist_ok=True)
            except OSError:
                logger.warning(f"Could not create temp directory at {self.temp_dir}")
                self.temp_dir = None

        logger.info(f"WhisperSTT initialized with model: {model_name}")

    def _load_model(self):
        """Load the Whisper model if not already loaded."""
        if self.model is None:
            logger.info(f"Loading Whisper model ({self.model_name})...")
            start_time = time.time()

            if self.device:
                # Load with specific device
                self.model = whisper.load_model(self.model_name, device=self.device)
            else:
                # Auto-detect device
                self.model = whisper.load_model(self.model_name)

            end_time = time.time()
            logger.info(
                f"Model loaded successfully in {end_time - start_time:.2f} seconds"
            )
            logger.info(f"Model device: {self.model.device}")

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model."""
        self._load_model()

        models_info = {
            "tiny": {
                "params": "39M",
                "vram": "~1GB",
                "speed": "~10x",
                "notes": "Fastest, lower accuracy",
            },
            "base": {
                "params": "74M",
                "vram": "~1GB",
                "speed": "~7x",
                "notes": "Good for quick transcription",
            },
            "small": {
                "params": "244M",
                "vram": "~2GB",
                "speed": "~4x",
                "notes": "Balanced speed/quality",
            },
            "medium": {
                "params": "769M",
                "vram": "~5GB",
                "speed": "~2x",
                "notes": "Better accuracy",
            },
            "turbo": {
                "params": "809M",
                "vram": "~6GB",
                "speed": "~8x",
                "notes": "Fast + accurate (no translation)",
            },
            "large": {
                "params": "1550M",
                "vram": "~10GB",
                "speed": "1x",
                "notes": "Best accuracy, slowest",
            },
        }

        current_info = models_info.get(self.model_name, {})

        return {
            "model_name": self.model_name,
            "device": str(self.model.device),
            "dimensions": str(self.model.dims),
            "parameters": current_info.get("params", "unknown"),
            "vram_usage": current_info.get("vram", "unknown"),
            "relative_speed": current_info.get("speed", "unknown"),
            "notes": current_info.get("notes", ""),
            "available_models": whisper.available_models(),
        }

    def transcribe(
        self,
        audio_file_path: str,
        language: str = None,
        translate: bool = False,
        verbose: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Transcribe audio file using OpenAI Whisper.

        Args:
            audio_file_path: Path to the audio file to transcribe
            language: Language code for transcription (e.g., 'en', 'cs', 'de').
                     If None, auto-detects language
            translate: Whether to translate to English (default: False)
                      Note: turbo model doesn't support translation
            verbose: Whether to print verbose output (default: False)
            **kwargs: Additional options for whisper.transcribe()

        Returns:
            Dictionary with transcription results including text, segments, and language
        """
        if not Path(audio_file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        self._load_model()

        # Check if translation is requested with turbo model
        if translate and self.model_name == "turbo":
            logger.warning(
                "Turbo model doesn't support translation. Use 'medium' or 'large' for translation."
            )
            translate = False

        try:
            logger.info(f"Transcribing audio file: {audio_file_path}")
            start_time = time.time()

            # Prepare transcription options
            transcribe_options = {"verbose": verbose, **kwargs}

            # Add language if specified
            if language:
                transcribe_options["language"] = language

            # Add translation task if requested
            if translate:
                transcribe_options["task"] = "translate"

            # Perform transcription
            result = self.model.transcribe(audio_file_path, **transcribe_options)

            end_time = time.time()
            transcription_time = end_time - start_time

            logger.info(f"Transcription completed in {transcription_time:.2f} seconds")
            logger.info(f"Detected language: {result.get('language', 'unknown')}")

            if verbose:
                logger.info(f"Transcribed text: '{result['text'].strip()}'")
                if "segments" in result:
                    logger.info(f"Number of segments: {len(result['segments'])}")

            # Format the result
            formatted_result = {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "transcription_time": transcription_time,
                "model_used": self.model_name,
                "device_used": str(self.model.device),
            }

            # Add segments if available
            if "segments" in result:
                formatted_result["segments"] = []
                for segment in result["segments"]:
                    formatted_result["segments"].append(
                        {
                            "start": segment.get("start", 0.0),
                            "end": segment.get("end", 0.0),
                            "text": segment.get("text", "").strip(),
                        }
                    )

            # Add translation flag
            formatted_result["translated"] = translate

            return formatted_result

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise RuntimeError(f"Whisper transcription failed: {str(e)}")

    def transcribe_buffer(
        self, audio_data: bytes, file_format: str = "wav", **kwargs
    ) -> dict[str, Any]:
        """
        Transcribe audio from binary data.

        Args:
            audio_data: Binary audio data
            file_format: Audio format extension without leading dot (default: wav)
            **kwargs: Additional options passed to transcribe()

        Returns:
            Dictionary with transcription results
        """
        if not audio_data:
            raise ValueError("Audio data cannot be empty")

        # Create temporary file
        if self.temp_dir:
            temp_audio_path = os.path.join(
                self.temp_dir,
                f"whisper_audio_input_{os.getpid()}_{int(time.time())}.{file_format}",
            )
            with open(temp_audio_path, "wb") as f:
                f.write(audio_data)
        else:
            with tempfile.NamedTemporaryFile(
                suffix=f".{file_format}", delete=False
            ) as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name

        try:
            logger.info(f"Transcribing audio buffer ({len(audio_data)} bytes)")
            return self.transcribe(temp_audio_path, **kwargs)
        finally:
            # Clean up temporary file
            try:
                if Path(temp_audio_path).exists():
                    os.unlink(temp_audio_path)
                    logger.debug(f"Cleaned up temporary file: {temp_audio_path}")
            except OSError:
                logger.warning(f"Failed to delete temporary file: {temp_audio_path}")

    def detect_language(self, audio_file_path: str) -> dict[str, Any]:
        """
        Detect the language of an audio file.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Dictionary with detected language and confidence scores
        """
        if not Path(audio_file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        self._load_model()

        try:
            logger.info(f"Detecting language for: {audio_file_path}")

            # Load and preprocess audio
            audio = whisper.load_audio(audio_file_path)
            audio = whisper.pad_or_trim(audio)

            # Make log-mel spectrogram and move to device
            mel = whisper.log_mel_spectrogram(audio, n_mels=self.model.dims.n_mels).to(
                self.model.device
            )

            # Detect language
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            confidence = probs[detected_language]

            logger.info(
                f"Detected language: {detected_language} (confidence: {confidence:.3f})"
            )

            # Get top 5 language candidates
            top_languages = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "detected_language": detected_language,
                "confidence": confidence,
                "top_candidates": [
                    {"language": lang, "confidence": conf}
                    for lang, conf in top_languages
                ],
            }

        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            raise RuntimeError(f"Language detection failed: {str(e)}")

    def transcribe_with_translation(
        self, audio_file_path: str, **kwargs
    ) -> dict[str, Any]:
        """
        Transcribe audio and translate to English.

        Note: Translation is not supported by the turbo model.
        Will automatically use medium model if turbo is selected.

        Args:
            audio_file_path: Path to the audio file
            **kwargs: Additional options

        Returns:
            Dictionary with original transcription and English translation
        """
        # Check if current model supports translation
        if self.model_name == "turbo":
            logger.warning(
                "Turbo model doesn't support translation. Consider using 'medium' or 'large' model."
            )
            raise ValueError(
                "Translation not supported by turbo model. Use 'medium' or 'large' model for translation."
            )

        # First transcribe to get original language
        original_result = self.transcribe(audio_file_path, translate=False, **kwargs)

        # Then translate to English
        translated_result = self.transcribe(audio_file_path, translate=True, **kwargs)

        return {
            "original": {
                "text": original_result["text"],
                "language": original_result["language"],
                "segments": original_result.get("segments", []),
            },
            "translated": {
                "text": translated_result["text"],
                "language": "en",
                "segments": translated_result.get("segments", []),
            },
            "transcription_time": original_result["transcription_time"]
            + translated_result["transcription_time"],
            "model_used": self.model_name,
        }
