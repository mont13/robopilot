"""
Whisper STT utility for Speech-to-Text functionality.
"""

import os
import subprocess
import tempfile
from typing import Any, Dict, List


class WhisperSTT:
    """Wrapper class for Whisper STT functionality."""

    def __init__(
        self, model_path: str = None, whisper_binary: str = None, temp_dir: str = None
    ):
        """
        Initialize the WhisperSTT client.

        Args:
            model_path: Path to the Whisper model file.
                       If None, defaults to /opt/whisper.cpp/models/ggml-base.en.bin
            whisper_binary: Path to the whisper binary.
                          If None, defaults to /opt/whisper.cpp/build/bin/whisper-cli
            temp_dir: Directory to use for temporary files.
                      If None, uses system default temp directory.
        """
        # Default paths
        self.whisper_binary = whisper_binary or "/opt/whisper.cpp/build/bin/whisper-cli"
        self.model_path = model_path or "/opt/whisper.cpp/models/ggml-base.en.bin"
        self.temp_dir = temp_dir

        # Ensure temp directory exists if specified
        if self.temp_dir and not os.path.exists(self.temp_dir):
            try:
                os.makedirs(self.temp_dir, exist_ok=True)
            except OSError:
                print(f"Warning: Could not create temp directory at {self.temp_dir}")
                self.temp_dir = None

        # Check if whisper binary and model exist
        if not os.path.exists(self.whisper_binary):
            print(f"Warning: Whisper binary not found at {self.whisper_binary}")

        if not os.path.exists(self.model_path):
            print(f"Warning: Whisper model not found at {self.model_path}")

    def transcribe(
        self,
        audio_file_path: str,
        language: str = "en",
        translate: bool = False,
        verbose: bool = False,
        options: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using whisper.cpp.

        Args:
            audio_file_path: Path to the audio file to transcribe
            language: Language code for transcription (default: en)
            translate: Whether to translate to English (default: False)
            verbose: Whether to print verbose output (default: False)
            options: Additional command line options for whisper-cli

        Returns:
            Dictionary with transcription results
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # The actual output files will be named based on the input audio file
        # Whisper CLI adds .txt, .vtt, .srt extensions to the input file name
        output_txt_path = f"{audio_file_path}.txt"
        output_vtt_path = f"{audio_file_path}.vtt"
        output_srt_path = f"{audio_file_path}.srt"

        try:
            # Build command
            cmd = [
                self.whisper_binary,
                "-m",
                self.model_path,
                "-f",
                audio_file_path,
                "-l",
                language,
                "--output-txt",
                "--output-vtt",
                "--output-srt",
            ]

            # Add translation if requested
            if translate:
                cmd.append("--translate")

            # Add additional options
            if options:
                for key, value in options.items():
                    if isinstance(value, bool):
                        if value:
                            cmd.append(f"--{key}")
                    else:
                        cmd.extend([f"--{key}", str(value)])

            # Run whisper command
            if verbose:
                print(f"Running command: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            # Check for errors
            if process.returncode != 0:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                raise RuntimeError(f"Whisper transcription failed: {error_msg}")

            if verbose:
                print("Whisper transcription completed successfully.")
                print(
                    f"Output files: {output_txt_path}, {output_vtt_path}, {output_srt_path}"
                )
                print(f"Transcription output: {stdout.decode('utf-8')}")
                print(f"Transcription error: {stderr.decode('utf-8')}")

            # Read results - make sure files exist before reading
            text, vtt, srt = "", "", ""

            if os.path.exists(output_txt_path):
                with open(output_txt_path, "r", encoding="utf-8") as f:
                    text = f.read()
            else:
                print(f"Warning: Output TXT file not found at {output_txt_path}")

            if os.path.exists(output_vtt_path):
                with open(output_vtt_path, "r", encoding="utf-8") as f:
                    vtt = f.read()
            else:
                print(f"Warning: Output VTT file not found at {output_vtt_path}")

            if os.path.exists(output_srt_path):
                with open(output_srt_path, "r", encoding="utf-8") as f:
                    srt = f.read()
            else:
                print(f"Warning: Output SRT file not found at {output_srt_path}")

            # Parse timestamps from VTT or SRT
            segments = self._parse_segments_from_srt(srt) if srt else []

            return {
                "text": text.strip(),
                "segments": segments,
                "vtt": vtt,
                "srt": srt,
                "language": language,
            }
        finally:
            # Clean up temporary files
            for temp_file in [output_txt_path, output_vtt_path, output_srt_path]:
                if os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except OSError:
                        print(f"Warning: Failed to delete temporary file {temp_file}")
                        pass

    def transcribe_buffer(
        self, audio_data: bytes, file_format: str = "wav", **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe audio from binary data.

        Args:
            audio_data: Binary audio data
            file_format: Audio format extension without leading dot (default: wav)

        Returns:
            Dictionary with transcription results
        """
        # Create a temporary file in specified directory if available
        if self.temp_dir:
            temp_audio_path = os.path.join(
                self.temp_dir, f"audio_input_{os.getpid()}.{file_format}"
            )
            with open(temp_audio_path, "wb") as f:
                f.write(audio_data)
        else:
            # Use default tempfile if no temp_dir specified
            temp_audio = tempfile.NamedTemporaryFile(
                suffix=f".{file_format}", delete=False
            )
            temp_audio.write(audio_data)
            temp_audio.close()
            temp_audio_path = temp_audio.name

        try:
            return self.transcribe(temp_audio_path, **kwargs)
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_audio_path)
            except OSError:
                print(f"Warning: Failed to delete temporary file {temp_audio_path}")
                pass

    def _parse_segments_from_srt(self, srt_content: str) -> List[Dict[str, Any]]:
        """
        Parse segments from SRT format.

        Args:
            srt_content: String containing SRT formatted text

        Returns:
            List of segment dictionaries with start time, end time and text
        """
        segments = []
        lines = srt_content.strip().split("\n")

        i = 0
        while i < len(lines):
            # Skip empty lines and segment number
            if not lines[i] or lines[i].isdigit():
                i += 1
                continue

            # Parse timestamp
            if "-->" in lines[i]:
                timestamp_line = lines[i]
                times = timestamp_line.split(" --> ")
                start_time = self._parse_timestamp(times[0])
                end_time = self._parse_timestamp(times[1])

                # Get text (may be multiple lines)
                text_lines = []
                i += 1
                while i < len(lines) and lines[i]:
                    text_lines.append(lines[i])
                    i += 1

                text = " ".join(text_lines)

                segments.append({"start": start_time, "end": end_time, "text": text})
            else:
                i += 1

        return segments

    def _parse_timestamp(self, timestamp: str) -> float:
        """Convert SRT timestamp to seconds."""
        parts = timestamp.strip().split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2].replace(",", "."))

        return hours * 3600 + minutes * 60 + seconds
