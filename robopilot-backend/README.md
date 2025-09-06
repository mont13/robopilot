# RoboPilot Backend

This is the backend service for the RoboPilot project, built with FastAPI and providing APIs for chat, speech-to-text (STT), text-to-speech (TTS), and robot control functionality.

## Features

- **FastAPI Backend**: RESTful API with automatic documentation
- **Database**: PostgreSQL with Alembic migrations
- **Speech Processing**: 
  - Speech-to-Text using Whisper.cpp
  - Text-to-Speech using Piper TTS
- **AI Agent System**: BeeAI Framework with ReAct pattern for intelligent robot control
- **LLM Integration**: Support for LMStudio, Ollama, OpenAI, and custom endpoints
- **Robot Control**: Universal Robots (UR) integration with intelligent tool calling
- **Authentication**: JWT-based user authentication
- **Docker Support**: Containerized development and deployment

## Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)

## Quick Start

### Using Make Commands

```bash
# Start all services (backend + database)
make start

# Run database migrations
make migrate

# Create admin user
make create-admin

# View logs
make logs

# Stop services
make stop
```

### Using Docker Compose Directly

```bash
# Start services
docker-compose up -d --build

# Run migrations
docker-compose run --rm backend poetry run alembic upgrade head

# Create admin user
docker-compose run --rm backend poetry run python create_admin.py

# Stop services
docker-compose down
```

## Environment Variables

The following environment variables can be configured:

- `POSTGRES_DB_HOST`: Database host (default: postgresql)
- `POSTGRES_DB`: Database name (default: fastapi_db)
- `POSTGRES_USER`: Database user (default: postgres)
- `POSTGRES_PASSWORD`: Database password (default: postgres)
- `APP_RELOAD`: Enable auto-reload in development (default: true)

## AI Agent System

The backend now uses the **BeeAI Framework** for advanced AI agent capabilities:

- **ReAct Pattern**: Structured reasoning and acting for better robot control
- **Intelligent Tool Selection**: Automatically chooses appropriate robot tools based on user input
- **Advanced Memory Management**: Maintains conversation context and learning
- **Multi-Provider Support**: Works with various LLM providers seamlessly

### Key Features:
- 🤖 **Smart Robot Control**: Natural language commands automatically trigger appropriate robot actions
- 🧠 **Contextual Conversations**: Remembers previous interactions and maintains session state
- 🛠️ **Extensible Tool System**: Easy to add new robot capabilities and tools
- 🔄 **Error Recovery**: Built-in retry logic and graceful error handling

## LLM Provider Setup

The backend supports multiple LLM providers through the BeeAI framework. You need to have at least one running to use chat functionality.

### LM Studio (Local LLM)

1. **Download and Install LM Studio:**
   - Visit https://lmstudio.ai/
   - Download for your platform (Windows/macOS/Linux)
   - Install and launch the application

2. **Download a Model:**
   - In LM Studio, go to the "Discover" tab
   - Search for models like "gemma-2-2b-it" or "llama-3.2-3b-instruct"
   - Download your preferred model

3. **Start Local Server:**
   - Go to "Local Server" tab in LM Studio
   - Load your downloaded model
   - Click "Start Server"
   - Server will run on http://localhost:1234

4. **Configure in RoboPilot:**
   - The default LM Studio connection should work automatically
   - Access http://localhost:8009/docs to manage connections
   - Or use the frontend connection settings

### Ollama (Alternative Local LLM)

1. **Install Ollama:**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Or visit https://ollama.ai for other installation methods
   ```

2. **Download and Run a Model:**
   ```bash
   # Pull a model (e.g., Llama 3.2 3B)
   ollama pull llama3.2:3b
   
   # Run the model (starts server automatically)
   ollama run llama3.2:3b
   ```

3. **Configure in RoboPilot:**
   - Ollama runs on http://localhost:11434
   - Use the pre-configured Ollama connection
   - Switch active connection via API or frontend

### OpenAI API

1. **Get API Key:**
   - Visit https://platform.openai.com/
   - Create account and get API key

2. **Create Connection:**
   ```bash
   curl -X POST http://localhost:8009/api/connections/ \
     -H "Content-Type: application/json" \
     -d '{
       "name": "OpenAI GPT-4",
       "provider": "openai",
       "model_name": "gpt-4",
       "base_url": "https://api.openai.com/v1",
       "config": {
         "api_key": "your-api-key-here",
         "temperature": 0.7,
         "max_tokens": 1000
       }
     }'
   ```

### Switching Between Providers

```bash
# List all connections
curl http://localhost:8009/api/connections/

# Activate a specific connection
curl -X POST http://localhost:8009/api/connections/{connection_id}/activate

# Check active connection
curl http://localhost:8009/api/connections/active/
```

## API Documentation

Once the service is running, you can access:

- **Swagger UI**: http://localhost:8009/docs
- **ReDoc**: http://localhost:8009/redoc
- **OpenAPI JSON**: http://localhost:8009/openapi.json

## Project Structure

```
├── app/
│   ├── config/           # Configuration files
│   ├── controllers/      # API route handlers
│   ├── middleware/       # Custom middleware
│   ├── models/          # Pydantic models
│   ├── repository/      # Database repository layer
│   ├── services/        # Business logic services
│   └── utils/           # Utility functions
├── migrations/          # Alembic database migrations
├── scripts/            # Helper scripts
├── voices/             # TTS voice models
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── pyproject.toml      # Python dependencies
└── Makefile           # Development commands
```

## Development

### Database Migrations

```bash
# Create a new migration
make create-migration MESSAGE="Add new table"

# Apply migrations
make migrate

# Rollback last migration
make migrate-down

# Reset database completely
make reset-db
```

### Accessing Container

```bash
# Open shell in backend container
make shell

# Or using docker-compose directly
docker-compose exec backend bash
```

### Voice Models

The backend uses Piper TTS for text-to-speech. Voice models are stored in the `voices/` directory and are automatically downloaded if not present.

Available voices:
- `cs_CZ-jirka-medium.onnx` - Czech voice
- `en_US-lessac-medium.onnx` - English voice

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration

### Agent Chat (BeeAI-powered)
- `GET /api/agent/chat/sessions` - List chat sessions
- `POST /api/agent/chat/sessions` - Create new session  
- `GET /api/agent/chat/sessions/{id}` - Get session with messages
- `DELETE /api/agent/chat/sessions/{id}` - Delete session
- `GET /api/agent/chat/sessions/active/` - Get active session
- `POST /api/agent/chat/completions` - Process messages with AI agent

#### Agent Features:
- **Intelligent Tool Selection**: Automatically uses robot tools for physical commands
- **Natural Conversation**: Handles both chat and robot control seamlessly  
- **Memory Persistence**: Maintains conversation context across sessions

### Speech
- `POST /api/stt/transcribe` - Speech-to-text transcription
- `POST /api/tts/synthesize` - Text-to-speech synthesis

### LLM Connections
- `GET /api/llm-connections` - List LLM connections
- `POST /api/llm-connections` - Create new connection
- `PUT /api/llm-connections/{id}` - Update connection
- `DELETE /api/llm-connections/{id}` - Delete connection
- `POST /api/llm-connections/{id}/activate` - Set as active connection

## BeeAI Agent Examples

### Basic Chat Interaction
```bash
curl -X POST "http://localhost:8009/api/agent/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{
       "role": "user",
       "content": "Hello! How are you today?",
       "temperature": 0.7
     }'
```

### Robot Control Commands
```bash
# Move robot to home position
curl -X POST "http://localhost:8009/api/agent/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{
       "role": "user", 
       "content": "Move the robot to home position",
       "temperature": 0.7
     }'

# Control gripper
curl -X POST "http://localhost:8009/api/agent/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{
       "role": "user",
       "content": "Open the gripper",
       "temperature": 0.7
     }'
```

### Available Robot Commands:
- "Move robot home" / "Go to home position"
- "Open gripper" / "Close gripper" 
- "Turn on gripper LED" / "Turn off gripper LED"
- "Move to pickup position" / "Move to dropoff position"
- "Run pick and place cycle"
- "Reset robot systems"

## Production Deployment

For production deployment, use the production target:

```bash
# Build production image
make build-prod

# Or with docker-compose
TARGET=release docker-compose up -d --build
```

## Troubleshooting

### Common Issues

1. **Database connection issues**
   ```bash
   # Check database logs
   make logs-db
   
   # Reset database
   make reset-db
   ```

2. **LLM connection errors**
   ```bash
   # Check if LM Studio is running
   curl http://localhost:1234/v1/models
   
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # View backend logs for connection errors
   make logs
   ```

3. **Voice models not found**
   - Voice models are downloaded automatically on first start
   - Check the `voices/` directory for `.onnx` files

4. **Permission issues**
   ```bash
   # Fix permissions for voice files
   sudo chown -R 1000:1000 voices/
   ```

5. **Bash script errors (voice detection)**
   - If you see "binary operator expected" errors
   - This has been fixed in recent versions
   - Restart the backend service: `make restart`

### Logs

```bash
# Backend logs
make logs

# Database logs
make logs-db

# All logs
docker-compose logs -f
```

## Migration to BeeAI Framework

If you're upgrading from a previous version that used custom OpenAI utilities, see:

- **[BeeAI Agent Documentation](README_BEEAI_AGENT.md)** - Complete guide to the new system
- **[Migration Guide](MIGRATION_GUIDE.md)** - Step-by-step migration instructions
- **[Example Scripts](examples/)** - Usage examples and testing tools

### Key Benefits of BeeAI:
- 🚀 **Enhanced AI Capabilities**: ReAct reasoning pattern for better decision making
- 🛡️ **Improved Reliability**: Built-in error recovery and retry mechanisms  
- 🔧 **Better Developer Experience**: Type-safe tool definitions and event monitoring
- 📈 **Performance**: Optimized tool execution and memory management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (including BeeAI agent functionality)
5. Submit a pull request

## License

This project is licensed under the MIT License.