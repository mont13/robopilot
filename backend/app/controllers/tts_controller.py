"""
Controller for TTS (text-to-speech) functionality.
"""

import io
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator

from ..utils.piper_tts import PiperTTS

router = APIRouter(prefix="/tts", tags=["TTS"])

# Initialize the TTS
tts = PiperTTS()


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech synthesis."""

    text: str
    voice_id: Optional[str] = None
    speaker_id: Optional[int] = 0

    @validator("text")
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class VoiceResponse(BaseModel):
    """Response model for voice listing."""

    id: str


@router.get("/voices", response_model=List[VoiceResponse])
async def list_voices():
    """List all available voices."""
    voices = tts.get_available_voices()
    return [{"id": voice} for voice in voices]


@router.post("/synthesize")
async def synthesize_speech(request: TextToSpeechRequest):
    """
    Synthesize speech from text and return audio.

    Returns a WAV audio file.
    """
    try:
        # Validate text content
        if not request.text or not request.text.strip():
            raise ValueError("Text cannot be empty")

        audio_data = tts.text_to_speech(
            text=request.text, voice_id=request.voice_id, speaker_id=request.speaker_id
        )

        # Validate audio data isn't empty
        if not audio_data or len(audio_data) < 100:  # Basic check for valid audio data
            raise ValueError("Generated audio is empty or invalid")

        # Return WAV audio file
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Text-to-speech synthesis failed: {str(e)}"
        )
