"""
Controller for LM Studio API integration.
"""

import logging
from typing import List, Optional, Union

import lmstudio as lms
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..config.settings import get_settings
from ..repository.chat_session_repository import ChatSessionRepository
from ..utils.lmstudio_client import ChatMessage, ChatSession, LMStudioClient
from ..utils.lmstudio_tools import PREDEFINED_TOOLS

# Set up logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create router with prefix and tag
router = APIRouter(prefix="/lmstudio", tags=["LM Studio"])

# Initialize the LM Studio client
lmstudio_client = None


def get_lmstudio_client():
    """Get or initialize the LM Studio client."""
    global lmstudio_client
    if lmstudio_client is None:
        try:
            lmstudio_client = LMStudioClient(host=settings.lmstudio_host)
            logger.info("LM Studio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LM Studio client: {str(e)}")
            error_detail = f"""
Failed to initialize LM Studio: {str(e)}

Troubleshooting:
1. Make sure LM Studio is running on {settings.lmstudio_host}
2. Check if the port 1234 is accessible from the container
3. Try restarting the LM Studio server
"""
            raise HTTPException(status_code=500, detail=error_detail)

    return lmstudio_client


# Add repository dependency
def get_chat_repository():
    """Get chat session repository."""
    return ChatSessionRepository()


# Simplified request and response models
class ModelInfo(BaseModel):
    """Model for LM Studio model information."""

    id: str
    name: Optional[str] = None
    type: Optional[str] = None
    instance_id: Optional[str] = None
    context_length: Optional[int] = None


class LoadModelRequest(BaseModel):
    """Request model for loading a model."""

    model_key: str = Field(..., description="The key/name of the model to load")
    ttl: Optional[int] = Field(
        None, description="Time to live (idle seconds until auto-unload)"
    )


class ChatSessionResponse(BaseModel):
    """Response model for a chat session."""

    id: str
    name: Optional[str] = None
    messages: List[ChatMessage] = []
    created_at: str = None
    updated_at: str = None


class ChatSessionListResponse(BaseModel):
    """Response model for listing chat sessions."""

    sessions: List[ChatSessionResponse]


class CreateChatSessionRequest(BaseModel):
    """Request model for creating a chat session."""

    name: Optional[str] = Field(None, description="Optional name for the chat session")


class SingleMessageRequest(BaseModel):
    """Request model for processing a single message."""

    role: str = Field(..., description="Role of the message (system, user, assistant)")
    content: str = Field(..., description="Message content")
    temperature: float = Field(0.7, description="Temperature for generation")
    max_tokens: int = Field(512, description="Maximum tokens to generate")
    stream: bool = Field(False, description="Whether to stream the response")


class TextResponse(BaseModel):
    """Response model for text generation."""

    text: str


class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis."""

    prompt: str = Field(..., description="Text prompt to accompany the image")
    image_path: str = Field(..., description="Path to the image file")


@router.get("/health")
async def check_health(client: LMStudioClient = Depends(get_lmstudio_client)):
    """Check the health status of the LM Studio connection."""
    try:
        # Try to get available models as a connectivity test
        models = client.get_available_models()

        # Get client details for diagnostic info
        client_host = "unknown"
        try:
            client_host = lms.get_default_client().api_host
        except Exception as host_err:
            logger.warning(f"Could not get client host: {str(host_err)}")

        return {
            "status": "healthy",
            "message": "LM Studio connection is working",
            "host": client_host,
            "models": [
                {
                    "id": model.identifier,
                    "name": model.display_name,
                    "type": model.type,
                    "instance_id": model.instance_reference,
                    "context_length": model.context_length,
                }
                for model in models
            ],
        }
    except Exception as e:
        logger.error(f"LM Studio health check failed: {str(e)}")
        raise HTTPException(
            status_code=503, detail="LM Studio connection is not healthy"
        )


@router.get("/models", response_model=List[ModelInfo])
async def list_models(client: LMStudioClient = Depends(get_lmstudio_client)):
    """List all available models."""
    try:
        models = client.get_available_models()
        return [
            {
                "id": model.identifier,
                "name": model.display_name,
                "type": model.type,
                "instance_id": model.instance_reference,
                "context_length": model.context_length,
            }
            for model in models
        ]
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/models/loaded", response_model=List[ModelInfo])
async def list_loaded_models(
    model_type: Optional[str] = Query(
        None, description="Filter by model type (llm or embedding)"
    ),
    client: LMStudioClient = Depends(get_lmstudio_client),
):
    """List all models currently loaded in memory."""
    try:
        models_info = client.get_loaded_models_info(model_type)
        return models_info
    except Exception as e:
        logger.error(f"Failed to list loaded models: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list loaded models: {str(e)}"
        )


@router.post("/models/load", response_model=ModelInfo)
async def load_model(
    request: LoadModelRequest, client: LMStudioClient = Depends(get_lmstudio_client)
):
    """Load a specific model into memory by its key."""
    try:
        model_args = {"ttl": request.ttl} if request.ttl else {}
        model = lms.llm(request.model_key, **model_args)

        return {
            "id": model.get_info().identifier,
            "name": model.get_info().display_name,
            "type": model.get_info().type,
            "instance_id": model.get_info().instance_reference,
            "context_length": model.get_info().context_length,
        }
    except Exception as e:
        logger.error(f"Failed to load model {request.model_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@router.post("/vision", response_model=TextResponse)
async def analyze_image(
    request: ImageAnalysisRequest, client: LMStudioClient = Depends(get_lmstudio_client)
):
    """Analyze an image using vision capabilities."""
    try:
        response = client.process_with_image(request.prompt, request.image_path)
        return {"text": response}
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


# Chat session routes
@router.get("/chat/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    repo: ChatSessionRepository = Depends(get_chat_repository),
):
    """Get all chat sessions."""
    try:
        db_sessions = await repo.get_all_sessions()

        sessions = [
            ChatSession(
                id=s.id,
                name=s.name,
                messages=[],  # Empty list for listing view
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
            for s in db_sessions
        ]

        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Failed to list chat sessions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list chat sessions: {str(e)}"
        )


@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: CreateChatSessionRequest = None,
    repo: ChatSessionRepository = Depends(get_chat_repository),
):
    """Create a new chat session."""
    try:
        name = request.name if request else None
        db_session = await repo.create_session(name)

        return ChatSession(
            id=db_session.id,
            name=db_session.name,
            messages=[],
            created_at=db_session.created_at.isoformat()
            if db_session.created_at
            else None,
            updated_at=db_session.updated_at.isoformat()
            if db_session.updated_at
            else None,
        )
    except Exception as e:
        logger.error(f"Failed to create chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create chat session: {str(e)}"
        )


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str = Path(..., description="The ID of the chat session"),
    repo: ChatSessionRepository = Depends(get_chat_repository),
):
    """Get a chat session by ID."""
    try:
        db_session = await repo.get_session_by_id(session_id)
        if not db_session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        messages = await repo.get_messages(session_id)
        chat_messages = [
            ChatMessage(role=msg.role, content=msg.content, created_at=msg.created_at.isoformat()) for msg in messages
        ]

        return ChatSession(
            id=db_session.id,
            name=db_session.name,
            messages=chat_messages,
            created_at=db_session.created_at.isoformat()
            if db_session.created_at
            else None,
            updated_at=db_session.updated_at.isoformat()
            if db_session.updated_at
            else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat session: {str(e)}"
        )


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str = Path(..., description="The ID of the chat session"),
    repo: ChatSessionRepository = Depends(get_chat_repository),
):
    """Delete a chat session."""
    try:
        success = await repo.delete_session(session_id)
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )
        return {"message": f"Chat session {session_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete chat session: {str(e)}"
        )


@router.get("/chat/sessions/active/", response_model=ChatSessionResponse)
async def get_active_session(client: LMStudioClient = Depends(get_lmstudio_client)):
    """Get the most recently active chat session."""
    try:
        active_session = await client.get_active_session()

        if not active_session:
            active_session = await client.create_chat_session("New Chat")

        return {
            "id": active_session.id,
            "name": active_session.name,
            "messages": active_session.messages,
            "created_at": active_session.created_at,
            "updated_at": active_session.updated_at,
        }
    except Exception as e:
        logger.error(f"Failed to get active session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get active session: {str(e)}"
        )


@router.post("/chat/completions", response_model=Union[TextResponse, None])
async def process_single_message(
    request: SingleMessageRequest,
    client: LMStudioClient = Depends(get_lmstudio_client),
):
    """Process a single message and generate a response based on role.

    This unified endpoint handles:
    - Adding system messages to the active session
    - Adding assistant messages to the active session
    - Processing user messages with automatic tool detection
    - Supporting streaming or non-streaming responses
    """
    try:
        # Get active session
        active_session = await client.get_active_session()
        if not active_session:
            active_session = await client.create_chat_session("New Chat")

        session_id = active_session.id

        # For user messages, we'll check if tools should be used
        tools = None
        if request.role == "user":
            # Automatically provide tools for user messages
            tools = PREDEFINED_TOOLS

        # Use streaming mode if requested
        if request.stream:

            async def response_generator():
                # Get the async generator directly - no await here
                generator = client.process_message(
                    session_id=session_id,
                    role=request.role,
                    content=request.content,
                    available_tools=tools,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=True,
                )

                if generator is not None:  # For user messages only
                    async for fragment in generator:
                        yield f"data: {fragment}\n\n"

                yield "data: [DONE]\n\n"

            return StreamingResponse(
                response_generator(), media_type="text/event-stream"
            )
        else:
            # Non-streaming mode
            response = await client.process_message(
                session_id=session_id,
                role=request.role,
                content=request.content,
                available_tools=tools,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False,
            )

            # For system or assistant messages, there's no response
            if request.role != "user":
                return None

            return {"text": response}

    except Exception as e:
        logger.error(f"Failed to process message: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process message: {str(e)}"
        )
