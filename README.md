# RoboPilot - AI-Powered Voice Assistant for Robot Control

RoboPilot is a comprehensive AI-powered voice assistant system designed for robot control and interaction. It combines speech-to-text, text-to-speech, and large language model capabilities to provide natural language control of robotic systems through a modern web interface.

## 🚀 Features

### Core Capabilities
- **Voice Control**: Real-time speech recognition with Whisper STT engine
- **AI-Powered Chat**: LLM integration with OpenAI, LM Studio, and Ollama support
- **Text-to-Speech**: High-quality voice synthesis using Piper TTS
- **Robot Control**: Direct robot manipulation through natural language commands
- **Function Calling**: AI can execute robot control functions automatically
- **Session Management**: Persistent conversation history and session management
- **Streaming Responses**: Real-time AI response streaming for better UX

### Robot Functions
- Movement control (home position, specific coordinates)
- Gripper operations (open/close, LED control)
- Automated sequences (pick and place cycles)
- System reset and status monitoring

## 🏗️ Architecture

The project consists of three main components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │    │    Database     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│                 │    │                 │    │                 │
│ • Voice UI      │    │ • STT/TTS APIs  │    │ • Chat Sessions │
│ • Chat Interface│    │ • LLM Integration│   │ • Message History│
│ • Real-time     │    │ • Robot Control │    │ • User Data     │
│   Audio         │    │ • Function Calls│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Backend (FastAPI)
- **REST API**: Comprehensive RESTful endpoints for all operations
- **Speech Processing**: Whisper-based STT and Piper-based TTS
- **LLM Integration**: Support for multiple AI providers
- **Robot Control**: Direct integration with robotic systems
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based user authentication

### Frontend (Next.js)
- **Modern UI**: React-based interface with Tailwind CSS
- **Real-time Audio**: Web Audio API integration for voice capture
- **Streaming Chat**: Server-sent events for real-time responses
- **Connection Management**: Multiple LLM provider support
- **Responsive Design**: Works on desktop and mobile devices

## 🐳 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose
- Make (optional, for convenience commands)

### Setup and Run

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd robopilot
   ```

2. **Start all services**:
   ```bash
   make startd
   ```
   
   Or manually:
   ```bash
   docker-compose up -d --build
   docker-compose run --rm server poetry run alembic upgrade head
   ```

3. **Create an admin user**:
   ```bash
   make create-admin
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8009
   - API Documentation: http://localhost:8009/docs

5. **Stop all services**:
   ```bash
   make stopd
   ```

## 🔧 Development Setup

### Backend Development

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install Poetry** (if not installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

6. **Start development server**:
   ```bash
   poetry run python -m app.main
   ```

### Frontend Development

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Access development frontend**:
   ```
   http://localhost:3000
   ```

## 📡 API Documentation

### User Management & Authentication
- `GET /api/users` - Get all users (requires authentication)
- `POST /api/users` - Create a new user (requires authentication)
- `GET /api/users/{user_id}` - Get user by ID (requires authentication)
- `POST /api/users/login` - Authenticate user and get tokens
- `POST /api/users/refresh-token` - Refresh access token
- `POST /api/users/register` - Register new user (placeholder)

### Speech-to-Text (STT)
- `POST /api/stt/transcribe` - Transcribe uploaded audio file
  - Supports multiple languages, translation, timestamps, and format options
- `POST /api/stt/transcribe/buffer` - Transcribe raw audio data from request body
  - Query parameters: `language`, `translate`, `format`

### Text-to-Speech (TTS)
- `GET /api/tts/voices` - List all available voice models
- `POST /api/tts/synthesize` - Convert text to speech
  - Returns WAV audio file with voice and speaker options

### Chat & LLM Integration
- `GET /api/lmstudio/chat/sessions` - List all chat sessions with messages
- `POST /api/lmstudio/chat/sessions` - Create new chat session
- `GET /api/lmstudio/chat/sessions/{session_id}` - Get specific session
- `DELETE /api/lmstudio/chat/sessions/{session_id}` - Delete session permanently
- `GET /api/lmstudio/chat/sessions/active/` - Get most recent or create new session
- `POST /api/lmstudio/chat/completions` - Process message with AI response
  - Supports streaming, function calling, temperature control
- `POST /api/lmstudio/analyze-image` - Analyze image with multimodal AI (placeholder)

### LLM Connection Management
- `GET /api/connections/` - List all configured LLM connections
- `POST /api/connections/` - Create new LLM connection
- `GET /api/connections/{connection_id}` - Get specific connection
- `PUT /api/connections/{connection_id}` - Update connection settings
- `DELETE /api/connections/{connection_id}` - Delete connection
- `POST /api/connections/{connection_id}/activate` - Set connection as active
- `GET /api/connections/active/` - Get currently active connection

**Supported LLM Providers**: OpenAI, Gemini, LM Studio, Ollama

For detailed API documentation with request/response schemas, visit http://localhost:8009/docs when running the backend.

## 🎛️ Configuration

### LLM Providers

RoboPilot supports multiple LLM providers:

#### OpenAI
```json
{
  "name": "OpenAI GPT-4",
  "provider": "openai",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4"
}
```

#### LM Studio (Local)
```json
{
  "name": "Local LM Studio",
  "provider": "lmstudio",
  "api_key": "lm-studio",
  "base_url": "http://localhost:1234/v1",
  "model": "local-model"
}
```

#### Ollama (Local)
```json
{
  "name": "Local Ollama",
  "provider": "ollama",
  "api_key": "ollama",
  "base_url": "http://localhost:11434/v1",
  "model": "llama2"
}
```

### Voice Models

The system includes pre-configured voice models:
- **English**: `en_US-lessac-medium`
- **Czech**: `cs_CZ-jirka-medium`

Additional voice models can be added to the `backend/voices/` directory.

## 🤖 Robot Integration

RoboPilot includes built-in robot control functions that can be called by the AI:

- `robot_move_home()` - Move to home position
- `robot_move_to_specified_position(x, y, z)` - Move to coordinates
- `robot_control_gripper(action)` - Control gripper (open/close)
- `robot_gripper_led_control(state)` - Control gripper LEDs
- `robot_run_pick_and_place_cycle()` - Execute pick and place
- `robot_reset_all()` - Reset all systems

These functions are automatically available to the AI and can be triggered through natural language commands.

## 📝 Usage Examples

### Voice Control
1. Click the microphone button in the web interface
2. Speak your command: "Move the robot to position 10, 20, 30"
3. The AI will process your speech and execute the appropriate robot functions

### Chat Interface
1. Type messages in the chat input
2. The AI will respond and can execute robot commands automatically
3. View conversation history in the session panel

### API Usage

```python
import requests

# Transcribe audio
with open("command.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8009/api/stt/transcribe",
        files={"file": f}
    )
    text = response.json()["text"]

# Send to chat
response = requests.post(
    "http://localhost:8009/api/lmstudio/chat/completions",
    json={"role": "user", "content": text}
)
reply = response.json()["text"]

# Convert to speech
response = requests.post(
    "http://localhost:8009/api/tts/synthesize",
    json={"text": reply, "voice_id": "en_US-lessac-medium"}
)
with open("response.wav", "wb") as f:
    f.write(response.content)
```

## 🔍 Troubleshooting

### Common Issues

1. **Docker services won't start**:
   - Check Docker is running
   - Ensure ports 3000, 8009, and 5432 are available
   - Run `docker-compose logs` to check for errors

2. **Voice models not found**:
   - Ensure voice files are in `backend/voices/`
   - Check Docker volume mounts
   - Restart the backend service

3. **LLM connection fails**:
   - Verify API keys and endpoints
   - Check network connectivity
   - Ensure the LLM service is running

4. **Audio not working**:
   - Check browser permissions for microphone
   - Ensure HTTPS for production deployments
   - Verify audio format compatibility

### Logs

Check application logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -m "Add feature"`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Whisper](https://github.com/openai/whisper) for speech-to-text
- [Piper TTS](https://github.com/rhasspy/piper) for text-to-speech
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Next.js](https://nextjs.org/) for the frontend framework
- [LM Studio](https://lmstudio.ai/) for local LLM support

---

For detailed documentation on specific components, see:
- [Chat API Documentation](backend/README_CHAT.md)
- [STT API Documentation](backend/README_STT.md)
- [TTS API Documentation](backend/README_TTS.md)