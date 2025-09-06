"""
Controller for STT (speech-to-text) functionality.
"""

import os
from typing import Any

import aiofiles
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

    language: str | None = "en"
    translate: bool | None = False
    verbose: bool | None = False
    word_timestamps: bool | None = False
    max_line_width: int | None = None
    max_line_count: int | None = None
    speed_up: bool | None = False
    diarize: bool | None = False


class TranscriptionResponse(BaseModel):
    """Response model for transcription."""

    text: str
    segments: list[dict[str, Any]]
    vtt: str | None = None
    srt: str | None = None
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

        # Write uploaded file content to file in shared temp directory
        content = await file.read()
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(content)

        # Transcribe the audio
        result = whisper_stt.transcribe(
            temp_path,
            language=language,
            translate=translate,
            verbose=verbose,
            word_timestamps=word_timestamps,
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
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e!s}")


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
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e!s}")
