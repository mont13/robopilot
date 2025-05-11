"""
Controller for STT (speech-to-text) functionality.
"""

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from ..utils.whisper_stt import WhisperSTT

router = APIRouter(prefix="/stt", tags=["STT"])

SHARED_TEMP_DIR = "/tmp"

# Ensure the directory exists
os.makedirs(SHARED_TEMP_DIR, exist_ok=True)

# Initialize the STT with shared temp directory
whisper_stt = WhisperSTT(temp_dir=SHARED_TEMP_DIR)


class TranscriptionOptions(BaseModel):
    """Options for transcription."""

    language: Optional[str] = "en"
    translate: Optional[bool] = False
    verbose: Optional[bool] = False
    word_timestamps: Optional[bool] = False
    max_line_width: Optional[int] = None
    max_line_count: Optional[int] = None
    speed_up: Optional[bool] = False
    diarize: Optional[bool] = False


class TranscriptionResponse(BaseModel):
    """Response model for transcription."""

    text: str
    segments: List[Dict[str, Any]]
    vtt: Optional[str] = None
    srt: Optional[str] = None
    language: str


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("en"),
    translate: bool = Form(False),
    verbose: bool = Form(False),
    word_timestamps: bool = Form(False),
    format: str = Form("all"),
):
    """
    Transcribe uploaded audio file.

    Args:
        file: Audio file to transcribe
        language: Language code (default: en)
        translate: Whether to translate to English
        verbose: Verbose output
        word_timestamps: Include word-level timestamps
        format: Output format (txt, vtt, srt, all)

    Returns:
        Transcription result
    """
    try:
        # Save the uploaded file to the shared temp directory
        filename = f"audio_input_{os.getpid()}{os.path.splitext(file.filename)[1]}"
        temp_path = os.path.join(SHARED_TEMP_DIR, filename)

        # Create a backup of the audio in the records directory
        record_path = os.path.join("/home/appuser/records", filename)

        # Write uploaded file content to file in shared temp directory
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Create a backup of the audio in the records directory
        with open(record_path, "wb") as f:
            f.write(content)

        options = {}

        # Add word timestamps if requested
        if word_timestamps:
            options["max-len"] = 1

        # Transcribe the audio
        result = whisper_stt.transcribe(
            temp_path,
            language=language,
            translate=translate,
            verbose=verbose,
            options=options,
        )

        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except OSError:
            print(f"Warning: Failed to delete temporary file {temp_path}")

        # Format the response based on requested format
        if format != "all":
            if format == "txt":
                result = {
                    "text": result["text"],
                    "segments": [],
                    "language": result["language"],
                }
            elif format == "vtt":
                result = {
                    "text": result["text"],
                    "segments": result["segments"],
                    "vtt": result["vtt"],
                    "language": result["language"],
                }
            elif format == "srt":
                result = {
                    "text": result["text"],
                    "segments": result["segments"],
                    "srt": result["srt"],
                    "language": result["language"],
                }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/transcribe/buffer", response_model=TranscriptionResponse)
async def transcribe_audio_buffer(request: Request):
    """
    Transcribe audio from raw binary data in request body.

    Query parameters:
        language: Language code (default: en)
        translate: Whether to translate to English
        format: Audio format (default: wav)

    Body:
        Raw binary audio data

    Returns:
        Transcription result
    """
    try:
        # Get query parameters
        language = request.query_params.get("language", "en")
        translate = request.query_params.get("translate", "false").lower() == "true"
        audio_format = request.query_params.get("format", "wav")

        # Read binary data from request body
        audio_data = await request.body()

        # Transcribe audio
        result = whisper_stt.transcribe_buffer(
            audio_data,
            file_format=audio_format,
            language=language,
            translate=translate,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
