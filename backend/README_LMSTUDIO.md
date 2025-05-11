# LM Studio API Integration

This API provides a RESTful interface for interacting with the LM Studio API. It allows you to generate text completions, chat completions, and use tools with LM Studio.

## Setup

1. Install LM Studio on your host machine from [https://lmstudio.ai](https://lmstudio.ai)
2. Start the LM Studio server (in LM Studio, go to the "Local Inference Server" tab and click "Start Server")
3. Ensure the server is running on port 1234 (default)
4. Start this API using Docker Compose:
   ```
   docker-compose up
   ```

## Environment Variables

- `LMSTUDIO_HOST`: The host and port where the LM Studio server is running (default: `host.docker.internal:1234`)

## API Endpoints

### Health Check

```
GET /api/lmstudio/health
```

Checks if the LM Studio API is accessible and working.

### Model Management

#### List Available Models

```
GET /api/lmstudio/models
```

Lists available models from LM Studio.

#### List Loaded Models in Memory

```
GET /api/lmstudio/models/loaded
```

Lists models currently loaded in memory with detailed information.

Optional query parameters:
- `model_type`: Filter by model type (e.g., "llm" or "embedding")

#### Load a Model

```
POST /api/lmstudio/models/load
```

Loads a specific model into memory.

Body:
```json
{
  "model_key": "llama-3.2-1b-instruct",
  "ttl": 3600  // Optional: time-to-live in seconds
}
```

#### Unload a Model

```
DELETE /api/lmstudio/models/unload/{model_key}
```

Unloads a specific model from memory.

### Text Completion

```
POST /api/lmstudio/completions
```

Body:
```json
{
  "prompt": "Once upon a time",
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": false
}
```

### Chat Completion

```
POST /api/lmstudio/chat/completions
```

Body:
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Tell me a joke"}
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": false
}
```

### Image Analysis (Vision)

```
POST /api/lmstudio/vision
```

Body:
```json
{
  "prompt": "Describe this image",
  "image_path": "/path/to/image.jpg"
}
```

### Tool Usage

```
POST /api/lmstudio/tools
```

Body:
```json
{
  "prompt": "Calculate 5 + 10",
  "tools": [
    {
      "name": "add",
      "description": "Given two numbers a and b, returns the sum of them",
      "parameters": {
        "a": {"type": "number"},
        "b": {"type": "number"}
      }
    }
  ]
}
```

## Example Usage

```python
import requests

# Simple text completion
response = requests.post(
    "http://localhost:8009/api/lmstudio/completions",
    json={
        "prompt": "Once upon a time",
        "temperature": 0.7,
        "max_tokens": 512
    }
)
print(response.json()["text"])
```
