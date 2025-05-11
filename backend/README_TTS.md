# TTS (Text-to-Speech) API Integration

This API provides a RESTful interface for text-to-speech synthesis using the Piper TTS engine. It allows you to convert text to speech with various voices and speaker options.

## Setup

1. Ensure the required voice models are available in the `voices/` directory
2. Start the API using Docker Compose:
   ```
   docker-compose up
   ```

## Available Voice Models

The API comes with the following voice models:
- `cs_CZ-jirka-medium`: Czech voice model
- `en_US-lessac-medium`: English (US) voice model

## API Endpoints

### Health Check

```
GET /api/tts/health
```

Checks if the TTS service is accessible and working.

### Voice Management

#### List Available Voices

```
GET /api/tts/voices
```

Lists all available voice models that can be used for text-to-speech synthesis.

Response:
```json
[
  {"id": "cs_CZ-jirka-medium"},
  {"id": "en_US-lessac-medium"}
]
```

### Text to Speech Synthesis

```
POST /api/tts/synthesize
```

Converts text to speech and returns audio data.

Body:
```json
{
  "text": "Hello, this is a test of the text to speech system.",
  "voice_id": "en_US-lessac-medium",
  "speaker_id": 0
}
```

Parameters:
- `text`: The text to convert to speech (required)
- `voice_id`: The ID of the voice to use (optional, defaults to system default)
- `speaker_id`: The speaker ID when a voice has multiple speaker options (optional, defaults to 0)

Response:
- Returns a WAV audio file with `Content-Type: audio/wav`

## Example Usage

### Python Example

```python
import requests

# Get available voices
response = requests.get("http://localhost:8009/api/tts/voices")
voices = response.json()
print(f"Available voices: {voices}")

# Convert text to speech
response = requests.post(
    "http://localhost:8009/api/tts/synthesize",
    json={
        "text": "Hello, this is a test of the text to speech system.",
        "voice_id": "en_US-lessac-medium"
    }
)

# Save the audio file
if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
    print("Audio saved to output.wav")
else:
    print(f"Error: {response.status_code}, {response.text}")
```

### cURL Example

```bash
# Get available voices
curl -X GET "http://localhost:8009/api/tts/voices"

# Convert text to speech
curl -X POST "http://localhost:8009/api/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test of the text to speech system.", "voice_id": "en_US-lessac-medium"}' \
  --output output.wav
```
