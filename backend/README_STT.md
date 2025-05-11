# STT (Speech-to-Text) API Integration

This API provides a RESTful interface for speech-to-text transcription using the Whisper STT engine. It allows you to convert audio to text with various options for language, format, and output style.

## Setup

1. Ensure the required Whisper models are available
2. Start the API using Docker Compose:
   ```
   docker-compose up
   ```

## API Endpoints

### Transcribe Audio File

```
POST /api/stt/transcribe
```

Transcribes an uploaded audio file and returns the text.

Form parameters:
- `file`: Audio file to transcribe (required)
- `language`: Language code (optional, defaults to "en")
- `translate`: Whether to translate to English (optional, defaults to false)
- `verbose`: Verbose output (optional, defaults to false)
- `word_timestamps`: Include word-level timestamps (optional, defaults to false)
- `format`: Output format - "txt", "vtt", "srt", or "all" (optional, defaults to "all")

Response:
```json
{
  "text": "This is the transcribed text.",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.5,
      "text": "This is the transcribed"
    },
    {
      "id": 1,
      "start": 2.5,
      "end": 4.0,
      "text": "text."
    }
  ],
  "language": "en",
  "vtt": "WEBVTT\n\n00:00:00.000 --> 00:00:02.500\nThis is the transcribed\n\n00:00:02.500 --> 00:00:04.000\ntext.",
  "srt": "1\n00:00:00,000 --> 00:00:02,500\nThis is the transcribed\n\n2\n00:00:02,500 --> 00:00:04,000\ntext."
}
```

### Transcribe Audio Buffer

```
POST /api/stt/transcribe/buffer
```

Transcribes raw audio data sent in the request body.

Query parameters:
- `language`: Language code (optional, defaults to "en")
- `translate`: Whether to translate to English (optional, defaults to false)
- `format`: Audio format (optional, defaults to "wav")

Body:
- Raw binary audio data

Response:
- Same format as `/api/stt/transcribe`

## Supported Languages

The API supports transcription for multiple languages using Whisper's multilingual capability. Some of the supported language codes include:
- `en`: English
- `cs`: Czech
- `de`: German
- `fr`: French
- `es`: Spanish
- And many more...

## Output Formats

The API supports various output formats:
- Plain text
- VTT (Web Video Text Tracks) format for subtitles
- SRT (SubRip) format for subtitles
- Combined output with all formats

## Example Usage

### Python Example

```python
import requests

# Transcribe an audio file
with open("audio.wav", "rb") as f:
    files = {"file": ("audio.wav", f, "audio/wav")}
    response = requests.post(
        "http://localhost:8009/api/stt/transcribe",
        files=files,
        data={
            "language": "en",
            "translate": False,
            "format": "all"
        }
    )

result = response.json()
print(f"Transcription: {result['text']}")
print(f"Language detected: {result['language']}")
```

### cURL Example

```bash
# Transcribe an audio file
curl -X POST "http://localhost:8009/api/stt/transcribe" \
  -F "file=@audio.wav" \
  -F "language=en" \
  -F "format=all"

# Transcribe raw audio data
curl -X POST "http://localhost:8009/api/stt/transcribe/buffer?language=en&format=wav" \
  --data-binary @audio.wav
```
