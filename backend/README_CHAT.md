# Chat API Integration

This API provides a comprehensive RESTful interface for AI-powered conversational interactions using Language Learning Models (LLMs). It supports advanced features like function calling for robot control, streaming responses, and persistent conversation history.

## Features

- **Chat Session Management**: Create, read, update, and delete conversation sessions
- **AI-Powered Responses**: Process messages through OpenAI-compatible LLM APIs
- **Function/Tool Calling**: Execute robot control functions through AI requests
- **Streaming Support**: Real-time response streaming for better user experience
- **Persistent History**: Automatic conversation history management with timestamps
- **Multi-Provider Support**: Compatible with OpenAI, LM Studio, Ollama, and other OpenAI-compatible endpoints
- **Error Handling**: Comprehensive error handling and logging throughout
- **Multimodal Ready**: Placeholder support for future image analysis capabilities

## Setup

1. Configure your LLM provider settings in the application configuration
2. Ensure robot control utilities are properly configured
3. Start the API using Docker Compose:
   ```bash
   docker-compose up
   ```

## API Endpoints

### Chat Session Management

#### List All Chat Sessions

```
GET /api/lmstudio/chat/sessions
```

Retrieves all chat sessions with their complete message history.

Response:
```json
{
  "sessions": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Robot Control Chat",
      "messages": [
        {
          "role": "user",
          "content": "Move the robot to home position",
          "created_at": "2025-05-25T10:30:00Z"
        },
        {
          "role": "assistant", 
          "content": "I'll move the robot to its home position for you.",
          "created_at": "2025-05-25T10:30:01Z"
        }
      ],
      "created_at": "2025-05-25T10:25:00Z",
      "updated_at": "2025-05-25T10:30:01Z"
    }
  ]
}
```

#### Create a New Chat Session

```
POST /api/lmstudio/chat/sessions
```

Creates a new chat session with an optional custom name.

Request body:
```json
{
  "name": "My Robot Chat"  // Optional
}
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "My Robot Chat",
  "messages": [],
  "created_at": "2025-05-25T10:25:00Z",
  "updated_at": "2025-05-25T10:25:00Z"
}
```

#### Get Specific Chat Session

```
GET /api/lmstudio/chat/sessions/{session_id}
```

Retrieves a specific chat session with all its messages.

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Robot Control Chat",
  "messages": [
    {
      "role": "system",
      "content": "You are RoboPilot, a helpful robot assistant.",
      "created_at": "2025-05-25T10:25:00Z"
    },
    {
      "role": "user",
      "content": "Move the robot to home position",
      "created_at": "2025-05-25T10:30:00Z"
    }
  ],
  "created_at": "2025-05-25T10:25:00Z",
  "updated_at": "2025-05-25T10:30:01Z"
}
```

#### Delete Chat Session

```
DELETE /api/lmstudio/chat/sessions/{session_id}
```

Permanently deletes a chat session and all associated messages.

Response:
```json
{
  "message": "Chat session 123e4567-e89b-12d3-a456-426614174000 deleted successfully"
}
```

#### Get Active Session

```
GET /api/lmstudio/chat/sessions/active/
```

Retrieves the most recently updated session or creates a new one if none exist.

### Message Processing

#### Process Message with AI Response

```
POST /api/lmstudio/chat/completions
```

Sends a message to the AI and generates a response with optional function calling and streaming.

Request body:
```json
{
  "role": "user",
  "content": "Move the robot to home position and turn on the gripper LED",
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": false
}
```

Parameters:
- `role`: Message role - "user", "system", or "assistant" (required)
- `content`: Message content text (required, 1-100,000 characters)
- `temperature`: Sampling temperature (optional, 0.0-2.0, default: 0.7)
- `max_tokens`: Maximum tokens to generate (optional, 1-8192, default: 512)
- `stream`: Enable streaming response (optional, default: false)

Response (non-streaming):
```json
{
  "text": "I'll move the robot to its home position and turn on the gripper LED for you. Let me execute these commands now."
}
```

Response (streaming):
```
data: {"text": "I'll move the robot to its home position and turn on the gripper LED for you. Let me execute these commands now."}

data: [DONE]
```

### Image Analysis (Placeholder)

#### Analyze Image with AI

```
POST /api/lmstudio/analyze-image
```

Analyzes an image using multimodal AI capabilities (requires compatible model).

Request body:
```json
{
  "prompt": "What do you see in this image?",
  "image_path": "/path/to/image.jpg"
}
```

Response:
```json
{
  "text": "Image analysis functionality is not yet implemented. This endpoint is a placeholder for future multimodal AI capabilities."
}
```

## Available Robot Functions

The AI can call the following robot control functions:

### Movement Functions
- **`robot_move_home`**: Move robot to home position
- **`robot_move_to_specified_position`**: Move robot to specific coordinates (x, y, z)

### Gripper Functions  
- **`robot_control_gripper`**: Open or close the robot gripper
- **`robot_gripper_led_control`**: Control gripper LED indicators (on/off)

### Automation Functions
- **`robot_run_pick_and_place_cycle`**: Execute automated pick and place sequence
- **`robot_reset_all`**: Reset all robot systems to default state

## Message Roles

The API supports three types of message roles:

- **`user`**: Messages from the user that typically require AI responses
- **`system`**: Context-setting messages that guide AI behavior
- **`assistant`**: AI-generated responses or manual assistant messages

## Function Calling Workflow

When the AI determines that a robot function should be executed:

1. **Message Processing**: User message is added to conversation history
2. **AI Analysis**: LLM analyzes the request and available tools
3. **Function Selection**: AI chooses appropriate robot functions to call
4. **Function Execution**: Selected functions are executed with provided parameters
5. **Result Integration**: Function results are sent back to the AI
6. **Final Response**: AI generates a final response incorporating the results
7. **History Update**: Complete interaction is saved to the database

## Streaming Responses

Enable streaming for real-time response delivery:

```bash
curl -X POST "http://localhost:8009/api/lmstudio/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{
       "role": "user",
       "content": "Tell me about the robot status",
       "stream": true
     }'
```

Streaming responses use Server-Sent Events (SSE) format with `text/event-stream` content type.

## Example Usage

### Python Example

```python
import requests
import json

# Create a new chat session
def create_session():
    response = requests.post(
        "http://localhost:8009/api/lmstudio/chat/sessions",
        json={"name": "Robot Control Session"}
    )
    return response.json()["id"]

# Send a message with function calling
def send_message(content, stream=False):
    response = requests.post(
        "http://localhost:8009/api/lmstudio/chat/completions",
        json={
            "role": "user",
            "content": content,
            "temperature": 0.7,
            "stream": stream
        }
    )
    return response.json()

# Example usage
session_id = create_session()
result = send_message("Move the robot to home position")
print(result["text"])
```

### JavaScript Example

```javascript
// Send message with streaming
async function sendStreamingMessage(content) {
    const response = await fetch('/api/lmstudio/chat/completions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            role: 'user',
            content: content,
            stream: true
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ') && !line.includes('[DONE]')) {
                const data = JSON.parse(line.slice(6));
                console.log(data.text);
            }
        }
    }
}

// Usage
sendStreamingMessage("Check robot status and move to position (10, 20, 30)");
```

### cURL Examples

```bash
# Create a new session
curl -X POST "http://localhost:8009/api/lmstudio/chat/sessions" \
     -H "Content-Type: application/json" \
     -d '{"name": "My Robot Chat"}'

# Send a user message
curl -X POST "http://localhost:8009/api/lmstudio/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{
       "role": "user",
       "content": "Move the robot to home position",
       "temperature": 0.7
     }'

# Get all sessions
curl -X GET "http://localhost:8009/api/lmstudio/chat/sessions"

# Delete a session
curl -X DELETE "http://localhost:8009/api/lmstudio/chat/sessions/123e4567-e89b-12d3-a456-426614174000"
```

## Error Responses

The API returns standard HTTP status codes:

- **200**: Success
- **201**: Created (for new sessions)
- **400**: Bad Request - Invalid input parameters
- **404**: Not Found - Resource does not exist
- **500**: Internal Server Error - Server-side error occurred

Error response format:
```json
{
  "detail": "Error description"
}
```

## Configuration

The Chat API can be configured to work with various LLM providers:

### OpenAI
```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4"
}
```

### LM Studio
```json
{
  "provider": "lmstudio", 
  "api_key": "lm-studio",
  "base_url": "http://localhost:1234/v1",
  "model": "local-model"
}
```

### Ollama
```json
{
  "provider": "ollama",
  "api_key": "ollama",
  "base_url": "http://localhost:11434/v1", 
  "model": "llama2"
}
```

## Security Considerations

- Always validate and sanitize user inputs
- Implement proper authentication and authorization
- Monitor function calling for unauthorized robot operations
- Log all interactions for audit purposes
- Set appropriate rate limits for API usage

## Troubleshooting

### Common Issues

1. **"No model configured"**: Ensure LLM configuration is properly set
2. **"Function execution failed"**: Check robot connectivity and permissions
3. **"Session not found"**: Verify session ID exists and is valid
4. **Streaming connection drops**: Check network stability and timeout settings

### Logging

The API provides comprehensive logging at different levels:
- **INFO**: General operation information
- **DEBUG**: Detailed debugging information  
- **WARNING**: Non-critical issues
- **ERROR**: Error conditions and failures

Check application logs for detailed error information and debugging.
