"""
Chat API Controller for AI-powered conversational interfaces.

This module provides a comprehensive REST API for managing chat sessions and
processing messages through Language Learning Models (LLMs). It supports
advanced features like function calling, streaming responses, and persistent
conversation history.

Features:
- Chat session management (create, read, update, delete)
- AI-powered message processing with OpenAI-compatible APIs
- Function/tool calling for robot control and automation
- Streaming and non-streaming response modes
- Persistent conversation history with message timestamps
- Automatic session management and recovery
- Comprehensive error handling and logging

The API is designed to work with various LLM providers including OpenAI,
LM Studio, Ollama, and other OpenAI-compatible endpoints.
"""

import asyncio
import json
import logging
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..config.settings import get_settings
from ..repository.chat_session_repository import ChatSessionRepository
from ..utils.lmstudio_client import ChatMessage, ChatSession
from ..utils.lmstudio_tools import (
    robot_control_gripper,
    robot_gripper_led_control,
    robot_move_home,
    robot_move_to_specified_position,
    robot_reset_all,
    robot_run_pick_and_place_cycle,
)
from ..utils.openai_utils.config import get_llm_config
from ..utils.openai_utils.function_calling import handle_function_calls
from ..utils.openai_utils.openai_client import OpenAIClient

# Configure logging for this module
logger = logging.getLogger(__name__)

# Load application settings
settings = get_settings()

# Create FastAPI router with comprehensive metadata
router = APIRouter(
    prefix="/lmstudio",
    tags=["Chat API"],
    responses={
        400: {"description": "Bad Request - Invalid input parameters"},
        404: {"description": "Not Found - Resource does not exist"},
        500: {"description": "Internal Server Error - Server-side error occurred"},
    },
)


# ============================================================================
# DEPENDENCY INJECTION FUNCTIONS
# ============================================================================


def get_openai_client(api_key: str, base_url: str) -> OpenAIClient:
    """
    Initialize and configure an OpenAI client with registered robot tools.

    This function creates an OpenAI-compatible client and registers all available
    robot control tools that can be called by the language model during conversations.

    Args:
        api_key (str): API key for authentication with the LLM service
        base_url (str): Base URL of the LLM service endpoint

    Returns:
        OpenAIClient: Configured client instance with registered tools

    Raises:
        HTTPException: If client initialization fails

    Registered Tools:
        - robot_move_home: Move robot to home position
        - robot_control_gripper: Control gripper open/close operations
        - robot_gripper_led_control: Control gripper LED indicators
        - robot_move_to_specified_position: Move robot to specific coordinates
        - robot_reset_all: Reset all robot systems to default state
        - robot_run_pick_and_place_cycle: Execute automated pick and place sequence
    """
    try:
        logger.info(f"Initializing OpenAI client with base_url: {base_url}")

        # Create OpenAI client instance
        openai_client = OpenAIClient(
            api_key=api_key,
            base_url=base_url,
        )

        # Register all available robot control tools
        robot_tools = [
            robot_move_home,
            robot_control_gripper,
            robot_gripper_led_control,
            robot_move_to_specified_position,
            robot_reset_all,
            robot_run_pick_and_place_cycle,
        ]

        for tool in robot_tools:
            openai_client.register_tool(tool)
            logger.debug(f"Registered tool: {tool.__name__}")

        logger.info("OpenAI client initialized successfully with all tools registered")
        return openai_client

    except Exception as e:
        error_msg = f"Failed to initialize OpenAI client: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg,
        )


def get_chat_repository() -> ChatSessionRepository:
    """
    Factory function to create a ChatSessionRepository instance.

    This function provides dependency injection for the chat session repository,
    ensuring consistent database access patterns across all endpoints.

    Returns:
        ChatSessionRepository: Repository instance for chat session operations

    Note:
        This function is used as a FastAPI dependency to inject the repository
        into endpoint handlers, promoting separation of concerns and testability.
    """
    return ChatSessionRepository()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ModelInfo(BaseModel):
    """
    Information about a language model.

    This model represents metadata about available language models,
    including their capabilities and current status.
    """

    id: str = Field(..., description="Unique identifier for the model")
    name: str = Field(..., description="Human-readable name of the model")
    status: str = Field(..., description="Current status (loaded, unloaded, error)")
    context_length: Optional[int] = Field(
        None, description="Maximum context length in tokens", ge=1, le=1000000
    )


class LoadModelRequest(BaseModel):
    """
    Request to load a specific language model.

    Used for dynamically loading models into memory for inference.
    """

    model_path: str = Field(..., description="File system path to the model")
    model_id: Optional[str] = Field(None, description="Optional custom identifier")
    context_length: Optional[int] = Field(
        None, description="Override default context length", ge=1, le=1000000
    )


class ChatSessionResponse(BaseModel):
    """
    Complete chat session data with messages and metadata.

    This model represents a full chat session including all messages,
    timestamps, and session metadata for API responses.
    """

    id: str = Field(..., description="Unique session identifier")
    name: str = Field(..., description="Session display name")
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Chronologically ordered messages in the session",
    )
    created_at: Optional[str] = Field(None, description="ISO timestamp of creation")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last update")


class ChatSessionListResponse(BaseModel):
    """
    Container for multiple chat sessions.

    Used when returning lists of chat sessions from the API.
    """

    sessions: List[ChatSessionResponse] = Field(
        default_factory=list, description="Array of chat sessions"
    )


class CreateChatSessionRequest(BaseModel):
    """
    Request to create a new chat session.

    Validates session creation parameters and provides defaults.
    """

    name: Optional[str] = Field(
        None,
        description="Optional session name (auto-generated if not provided)",
        min_length=1,
        max_length=100,
    )


class SingleMessageRequest(BaseModel):
    """
    Request to process a single message in a conversation.

    This model handles all types of messages (user, system, assistant)
    and includes parameters for controlling AI response generation.
    """

    role: str = Field(
        ...,
        description="Message role (system, user, assistant)",
        pattern="^(system|user|assistant)$",
    )
    content: str = Field(
        ..., description="Message content text", min_length=1, max_length=100000
    )
    temperature: Optional[float] = Field(
        0.7,
        description="Sampling temperature for response generation (0.0-2.0)",
        ge=0.0,
        le=2.0,
    )
    max_tokens: Optional[int] = Field(
        512, description="Maximum tokens to generate in response", ge=1, le=8192
    )
    stream: bool = Field(False, description="Enable streaming response mode")


class TextResponse(BaseModel):
    """
    Simple text response from the AI.

    Standard response format for non-streaming text generation.
    """

    text: str = Field(..., description="Generated response text")


class ImageAnalysisRequest(BaseModel):
    """
    Request for image analysis with AI.

    Supports multimodal AI capabilities for processing images with text prompts.
    Note: This functionality may require specific model capabilities.
    """

    prompt: str = Field(
        ...,
        description="Text prompt to guide image analysis",
        min_length=1,
        max_length=10000,
    )
    image_path: str = Field(..., description="File system path to the image file")


# ============================================================================
# CHAT SESSION MANAGEMENT ENDPOINTS
# ============================================================================


@router.get(
    "/chat/sessions",
    response_model=ChatSessionListResponse,
    summary="List all chat sessions",
    description="Retrieve all chat sessions with their messages and metadata",
)
async def list_chat_sessions(
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> ChatSessionListResponse:
    """
    Get all chat sessions with their complete message history.

    This endpoint retrieves all chat sessions from the database, including
    all messages, timestamps, and metadata. Sessions are ordered by most
    recently updated first.

    Args:
        repo: Injected chat session repository

    Returns:
        ChatSessionListResponse: List of all chat sessions with messages

    Raises:
        HTTPException: 500 if database operation fails

    Example:
        ```bash
        curl -X GET "http://localhost:8009/api/lmstudio/chat/sessions"
        ```
    """
    try:
        logger.info("Retrieving all chat sessions")

        # Get all sessions from database
        sessions = await repo.get_all_sessions()
        logger.debug(f"Found {len(sessions)} sessions in database")

        # Build response with messages for each session
        session_responses = []
        for session in sessions:
            try:
                # Get messages for this session
                messages = await repo.get_messages(session.id)

                # Convert to response format
                chat_messages = [
                    ChatMessage(
                        role=msg.role,
                        content=msg.content,
                        created_at=msg.created_at.isoformat()
                        if msg.created_at
                        else None,
                    )
                    for msg in messages
                ]

                # Create session response
                session_response = ChatSessionResponse(
                    id=session.id,
                    name=session.name,
                    messages=chat_messages,
                    created_at=session.created_at.isoformat()
                    if session.created_at
                    else None,
                    updated_at=session.updated_at.isoformat()
                    if session.updated_at
                    else None,
                )
                session_responses.append(session_response)

            except Exception as session_error:
                logger.warning(
                    f"Error processing session {session.id}: {session_error}"
                )
                # Continue with other sessions, don't fail completely
                continue

        logger.info(f"Successfully retrieved {len(session_responses)} chat sessions")
        return ChatSessionListResponse(sessions=session_responses)

    except Exception as e:
        error_msg = f"Failed to list chat sessions: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post(
    "/chat/sessions",
    response_model=ChatSessionResponse,
    status_code=201,
    summary="Create a new chat session",
    description="Create a new chat session with optional custom name",
)
async def create_chat_session(
    request: CreateChatSessionRequest,
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> ChatSessionResponse:
    """
    Create a new chat session for conversations.

    This endpoint creates a new chat session with an optional custom name.
    If no name is provided, a default name will be generated based on the
    current timestamp.

    Args:
        request: Chat session creation parameters
        repo: Injected chat session repository

    Returns:
        ChatSessionResponse: The newly created chat session

    Raises:
        HTTPException: 500 if session creation fails

    Example:
        ```bash
        curl -X POST "http://localhost:8009/api/lmstudio/chat/sessions" \
             -H "Content-Type: application/json" \
             -d '{"name": "My Robot Chat"}'
        ```
    """
    try:
        session_name = request.name or f"Chat {len(await repo.get_all_sessions()) + 1}"
        logger.info(f"Creating new chat session: '{session_name}'")

        # Create the session in database
        session = await repo.create_session(session_name)

        # Verify creation was successful
        db_session = await repo.get_session_by_id(session.id)
        if not db_session:
            raise HTTPException(
                status_code=500,
                detail="Session creation failed: Unable to retrieve created session",
            )

        # Prepare response
        response = ChatSessionResponse(
            id=db_session.id,
            name=db_session.name,
            messages=[],  # New sessions start with no messages
            created_at=db_session.created_at.isoformat()
            if db_session.created_at
            else None,
            updated_at=db_session.updated_at.isoformat()
            if db_session.updated_at
            else None,
        )

        logger.info(f"Successfully created chat session {session.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to create chat session: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/chat/sessions/{session_id}",
    response_model=ChatSession,
    summary="Get a specific chat session",
    description="Retrieve a chat session by ID with all messages",
)
async def get_chat_session(
    session_id: str = Path(..., description="Unique identifier of the chat session"),
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> ChatSession:
    """
    Retrieve a specific chat session with all its messages.

    This endpoint fetches a chat session by its unique ID, including all
    messages in chronological order with their timestamps and metadata.

    Args:
        session_id: Unique identifier of the session to retrieve
        repo: Injected chat session repository

    Returns:
        ChatSession: Complete session data with messages

    Raises:
        HTTPException: 404 if session not found, 500 if retrieval fails

    Example:
        ```bash
        curl -X GET "http://localhost:8009/api/lmstudio/chat/sessions/123e4567-e89b-12d3-a456-426614174000"
        ```
    """
    try:
        logger.info(f"Retrieving chat session: {session_id}")

        # Get session from database
        db_session = await repo.get_session_by_id(session_id)
        if not db_session:
            logger.warning(f"Chat session not found: {session_id}")
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Get all messages for this session
        messages = await repo.get_messages(session_id)
        logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")

        # Convert messages to response format
        chat_messages = [
            ChatMessage(
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat() if msg.created_at else None,
            )
            for msg in messages
        ]

        # Build complete session response
        session_response = ChatSession(
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

        logger.info(f"Successfully retrieved session {session_id}")
        return session_response

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to get chat session {session_id}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.delete(
    "/chat/sessions/{session_id}",
    status_code=200,
    summary="Delete a chat session",
    description="Permanently delete a chat session and all its messages",
)
async def delete_chat_session(
    session_id: str = Path(
        ..., description="Unique identifier of the session to delete"
    ),
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> dict:
    """
    Delete a chat session and all associated messages.

    This endpoint permanently removes a chat session from the database,
    including all messages, function calls, and metadata. This action
    cannot be undone.

    Args:
        session_id: Unique identifier of the session to delete
        repo: Injected chat session repository

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 404 if session not found, 500 if deletion fails

    Example:
        ```bash
        curl -X DELETE "http://localhost:8009/api/lmstudio/chat/sessions/123e4567-e89b-12d3-a456-426614174000"
        ```
    """
    try:
        logger.info(f"Attempting to delete chat session: {session_id}")

        # Attempt to delete the session
        success = await repo.delete_session(session_id)

        if not success:
            logger.warning(f"Chat session not found for deletion: {session_id}")
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        logger.info(f"Successfully deleted chat session: {session_id}")
        return {"message": f"Chat session {session_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to delete chat session {session_id}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/chat/sessions/active/",
    response_model=ChatSessionResponse,
    summary="Get the active chat session",
    description="Retrieve the most recently updated session or create a new one",
)
async def get_active_session(
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> ChatSessionResponse:
    """
    Get the most recently active chat session.

    This endpoint returns the chat session that was most recently updated.
    If no sessions exist, it automatically creates a new default session.
    This is useful for maintaining conversation continuity in single-session
    applications.

    Args:
        repo: Injected chat session repository

    Returns:
        ChatSessionResponse: The active session with all messages

    Raises:
        HTTPException: 500 if session retrieval/creation fails

    Example:
        ```bash
        curl -X GET "http://localhost:8009/api/lmstudio/chat/sessions/active/"
        ```
    """
    try:
        logger.info("Retrieving active chat session")

        # Try to get the most recent session
        active_session = await repo.get_active_session()

        # Create a new session if none exists
        if not active_session:
            logger.info("No active session found, creating new default session")
            active_session = await repo.create_session("New Chat")

        # Get messages for this session
        messages = await repo.get_messages(active_session.id)
        logger.debug(f"Active session {active_session.id} has {len(messages)} messages")

        # Convert messages to response format
        chat_messages = [
            ChatMessage(
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat() if msg.created_at else None,
            )
            for msg in messages
        ]

        # Build response
        response = ChatSessionResponse(
            id=active_session.id,
            name=active_session.name,
            messages=chat_messages,
            created_at=active_session.created_at.isoformat()
            if active_session.created_at
            else None,
            updated_at=active_session.updated_at.isoformat()
            if active_session.updated_at
            else None,
        )

        logger.info(f"Successfully retrieved active session: {active_session.id}")
        return response

    except Exception as e:
        error_msg = f"Failed to get active session: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# ============================================================================
# MESSAGE PROCESSING ENDPOINTS
# ============================================================================


@router.post(
    "/chat/completions",
    response_model=Union[TextResponse, None],
    summary="Process a message and generate AI response",
    description="Send a message to the AI and get a response with optional function calling",
)
async def process_single_message(
    request: SingleMessageRequest,
) -> Union[TextResponse, StreamingResponse]:
    """
    Process a single message and generate an AI response with function calling support.

    This is the main endpoint for interacting with the AI. It supports:
    - User messages with AI response generation
    - System messages for context setting
    - Assistant messages for conversation continuation
    - Function/tool calling for robot control
    - Streaming and non-streaming responses
    - Persistent conversation history

    AI Function Calling Workflow:
    1. Retrieve conversation history from database
    2. Add user message to conversation
    3. Send conversation to AI with available tools
    4. Execute any function calls made by the AI
    5. Send function results back to AI for final response
    6. Save complete interaction to database
    7. Return response to client

    Args:
        request: Message processing parameters

    Returns:
        TextResponse or StreamingResponse: AI-generated response

    Raises:
        HTTPException: 500 if processing fails

    Available Robot Functions:
        - robot_move_home: Move robot to home position
        - robot_control_gripper: Control gripper operations
        - robot_gripper_led_control: Control gripper LED indicators
        - robot_move_to_specified_position: Move to specific coordinates
        - robot_reset_all: Reset all robot systems
        - robot_run_pick_and_place_cycle: Execute pick and place sequence

    Example:
        ```bash
        curl -X POST "http://localhost:8009/api/lmstudio/chat/completions" \
             -H "Content-Type: application/json" \
             -d '{
               "role": "user",
               "content": "Move the robot to home position",
               "temperature": 0.7,
               "stream": false
             }'
        ```
    """
    try:
        # Route processing based on message role
        if request.role == "user":
            return await _process_user_message(request)
        elif request.role in ["system", "assistant"]:
            return await _process_non_user_message(request)
        else:
            logger.warning(f"Unsupported message role: {request.role}")
            return TextResponse(text=f"Unsupported role: {request.role}")

    except Exception as e:
        error_msg = f"Failed to process message: {str(e)}"
        logger.error(
            f"{error_msg} | Role: {request.role} | Content length: {len(request.content)}"
        )
        raise HTTPException(status_code=500, detail=error_msg)


# ============================================================================
# MESSAGE PROCESSING HELPER FUNCTIONS
# ============================================================================


async def _process_user_message(
    request: SingleMessageRequest,
) -> Union[TextResponse, StreamingResponse]:
    """
    Process a user message with AI response generation and function calling.

    This function handles the complete workflow for user messages:
    1. Get/create active session
    2. Save user message to database
    3. Generate AI response with tool support
    4. Execute any function calls
    5. Get final response and save to database

    Args:
        request: User message request with generation parameters

    Returns:
        TextResponse or StreamingResponse: Generated AI response
    """
    # Get the active session from the database
    repo = get_chat_repository()
    active_session = await repo.get_active_session()
    if not active_session:
        active_session = await repo.create_session("New Chat")

    session_id = active_session.id

    # Save user message first
    await repo.add_message(
        session_id=session_id,
        role="user",
        content=request.content,
    )

    # Get LLM configuration and client
    llm_config = await get_llm_config()
    model = llm_config.get("model")
    client = get_openai_client(llm_config.get("api_key"), llm_config.get("base_url"))

    # Prepare conversation history
    formatted_messages = await _prepare_conversation_history(repo, session_id)

    # Log processing information
    logger.info(f"Processing user message for session {session_id}")

    # Determine if robot functions should be enabled based on user message
    user_message_lower = request.content.lower()
    enable_robot_functions = _should_enable_robot_functions(user_message_lower)
    
    # Log tool selection decision
    logger.info(f"Tool selection analysis: message='{request.content}', enable_functions={enable_robot_functions}")
    
    # Get available tools and functions only if needed
    tools = client.get_registered_tools() if enable_robot_functions else []
    available_functions = _get_available_robot_functions() if enable_robot_functions else {}
    
    # Set tool choice based on whether functions are enabled
    tool_choice = "auto" if enable_robot_functions else "none"
    
    logger.info(f"Using tool_choice='{tool_choice}', tools_count={len(tools)}")

    try:
        # Configure generation parameters
        temperature = request.temperature if request.temperature is not None else 0.7

        # Generate AI response with conditional function calls
        completion_kwargs = {
            "messages": formatted_messages,
            "model": model,
            "temperature": temperature,
            "stream": False,
            "parallel_tool_calls": False,
        }
        
        # Only add tools and tool_choice if tools are available
        if tools:
            completion_kwargs["tools"] = tools
            completion_kwargs["tool_choice"] = tool_choice
        
        response = client.chat_completion(**completion_kwargs)

        # Process response and handle any tool calls
        final_response_text = await _handle_ai_response_with_tools(
            response,
            formatted_messages,
            available_functions,
            client,
            model,
            temperature,
            tools,
        )

        # Save assistant response to database
        await repo.add_message(
            session_id=session_id,
            role="assistant",
            content=final_response_text,
        )

        logger.info(f"Successfully processed user message for session {session_id}")

        # Handle streaming vs non-streaming response
        if request.stream:
            return _create_streaming_response(final_response_text)
        else:
            return TextResponse(text=final_response_text)

    except Exception as e:
        error_msg = f"Failed to process user message: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


async def _process_non_user_message(request: SingleMessageRequest) -> TextResponse:
    """
    Process system or assistant messages.

    These messages are typically used for context setting or conversation
    continuation and don't require AI response generation.

    Args:
        request: System or assistant message request

    Returns:
        TextResponse: Confirmation message
    """
    # Get active session
    repo = get_chat_repository()
    active_session = await repo.get_active_session()
    if not active_session:
        active_session = await repo.create_session("New Chat")

    # Save the message to database
    await repo.add_message(
        session_id=active_session.id,
        role=request.role,
        content=request.content,
    )

    logger.info(f"Saved {request.role} message to session {active_session.id}")
    return TextResponse(text=f"{request.role.title()} message saved successfully")


async def _prepare_conversation_history(
    repo: ChatSessionRepository, session_id: str
) -> List[dict]:
    """
    Prepare conversation history for AI model consumption.

    Retrieves messages from database and formats them for OpenAI API,
    ensuring there's a system message for context.

    Args:
        repo: Chat session repository
        session_id: Session identifier

    Returns:
        List[dict]: Formatted messages for AI model
    """
    # Get message history from the repository
    chat_history = await repo.get_messages(session_id)

    # Format messages for OpenAI API
    formatted_messages = []
    for msg in chat_history:
        formatted_messages.append({"role": msg.role, "content": msg.content})

    # Ensure there's a system message for context
    has_system_message = any(m["role"] == "system" for m in formatted_messages)
    if not has_system_message:
        formatted_messages.insert(
            0,
            {
                "role": "system",
                "content": (
                    "You are RoboPilot, a friendly and intelligent robot companion. "
                    
                    "Your main job is having natural conversations. Chat about anything - answer questions, share thoughts, be curious about the user's life. "
                    "Keep responses conversational and natural for speech. Use short, clear sentences. Avoid being overly wordy or repetitive. "
                    
                    "IMPORTANT: Only use robot functions when users ask for specific physical actions like 'move forward', 'pick up object', or 'go home'. "
                    "For everything else - greetings, questions, casual chat - just talk normally without calling any functions. "
                    
                    "Be warm, curious, and engaging. Ask follow-up questions when appropriate. "
                    "Keep things conversational and don't overthink responses."
                ),
            },
        )

    return formatted_messages


def _should_enable_robot_functions(user_message: str) -> bool:
    """
    Determine if robot functions should be enabled based on user message content.
    
    Args:
        user_message: The user's message content in lowercase
        
    Returns:
        bool: True if robot functions should be available, False otherwise
    """
    # First, check if it's clearly a question or conversational request
    question_patterns = [
        "can you", "could you", "would you", "will you", "please",
        "what can", "how can", "what do", "how do", "what is", "how does",
        "tell me", "explain", "describe", "help me understand"
    ]
    
    for pattern in question_patterns:
        if user_message.startswith(pattern):
            return False
    
    # Check for conversational greetings and general questions
    conversation_patterns = [
        "hello", "hi", "hey", "how are you", "what's up", "good morning",
        "good afternoon", "good evening", "thanks", "thank you"
    ]
    
    for pattern in conversation_patterns:
        if pattern in user_message:
            return False
    
    # Direct robot action commands (high priority)
    direct_actions = [
        "move forward", "move backward", "turn left", "turn right", 
        "go forward", "go backward", "go left", "go right", "go home",
        "pick up", "pick it up", "place", "put down", "drop",
        "open gripper", "close gripper", "gripper open", "gripper close",
        "move to", "go to", "navigate to", "execute", "run cycle",
        "reset robot", "robot reset", "start sequence", "perform"
    ]
    
    # Check for direct action commands
    for action in direct_actions:
        if action in user_message:
            return True
    
    # Check for imperative commands that start with action verbs
    imperative_starters = ("move", "go", "turn", "pick", "place", "open", "close", "reset", "stop", "start")
    if user_message.startswith(imperative_starters):
        return True
    
    # Robot control keywords (but only if in clear action context)
    action_keywords = ["move", "turn", "rotate", "pick", "place", "grab", "drop", "home", "position"]
    robot_context = ["robot", "arm", "gripper"]
    
    has_action = any(keyword in user_message for keyword in action_keywords)
    has_robot_context = any(context in user_message for context in robot_context)
    
    # Enable tools only if both action and robot context are present
    if has_action and has_robot_context:
        return True
    
    # Default to conversation mode (no tools)
    return False


def _get_available_robot_functions() -> dict:
    """
    Get mapping of available robot control functions.

    Returns:
        dict: Function name to callable mapping
    """
    return {
        "robot_move_home": robot_move_home,
        "robot_run_pick_and_place_cycle": robot_run_pick_and_place_cycle,
        "robot_control_gripper": robot_control_gripper,
        "robot_gripper_led_control": robot_gripper_led_control,
        "robot_move_to_specified_position": robot_move_to_specified_position,
        "robot_reset_all": robot_reset_all,
    }


async def _handle_ai_response_with_tools(
    response,
    formatted_messages: List[dict],
    available_functions: dict,
    client,
    model: str,
    temperature: float,
    tools: List[dict] = None,
) -> str:
    """
    Handle AI response and execute any tool calls.

    If the AI response includes tool calls, execute them and get a final
    response incorporating the tool results.

    Args:
        response: The initial AI response from OpenAI
        formatted_messages: The conversation history
        available_functions: Dict of available function name -> callable mappings
        client: The OpenAI client instance
        model: Model name to use for follow-up requests
        temperature: Temperature setting for requests
        tools: List of available tools (optional)

    Returns:
        str: Final response text after processing any tool calls
    """
    message = response.choices[0].message

    # Check if the model made any tool calls
    if message.tool_calls and available_functions:
        # Execute the tool calls
        results = handle_function_calls(message, available_functions)

        # Add the assistant's message with tool calls to conversation
        formatted_messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls,
            }
        )

        # Add tool results to conversation
        for tool_call in message.tool_calls:
            tool_call_id = tool_call.id
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            result = results.get(tool_call_id, {"error": "Function execution failed"})

            # Ensure result is serializable
            if not isinstance(result, (dict, list, str, int, float, bool, type(None))):
                result = str(result)

            formatted_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(result),
                }
            )

            logger.info(f"Executed function: {function_name} with args: {arguments}")

        # Get final response after tool execution
        # Generate final response after tool execution
        final_kwargs = {
            "messages": formatted_messages,
            "model": model,
            "temperature": temperature,
        }
        
        # Only add tools and tool_choice if tools are available
        if tools:
            final_kwargs["tools"] = tools
            final_kwargs["tool_choice"] = "auto"
        
        final_response = client.chat_completion(**final_kwargs)

        return final_response.choices[0].message.content
    else:
        # No tool calls, return the original response
        return message.content


def _create_streaming_response(text: str) -> StreamingResponse:
    """
    Create a streaming response for the given text.

    Args:
        text: Text to stream

    Returns:
        StreamingResponse: Streaming HTTP response
    """

    async def generate():
        # Simple streaming implementation - split by words
        words = text.split()
        for i, word in enumerate(words):
            if i > 0:
                yield f" {word}"
            else:
                yield word
            await asyncio.sleep(0.05)  # Small delay for streaming effect

    return StreamingResponse(
        generate(), media_type="text/plain", headers={"Cache-Control": "no-cache"}
    )


# ============================================================================
# IMAGE ANALYSIS ENDPOINTS (PLACEHOLDER)
# ============================================================================


@router.post(
    "/analyze-image",
    response_model=TextResponse,
    summary="Analyze an image with AI",
    description="Send an image to the AI for analysis and description",
)
async def analyze_image(request: ImageAnalysisRequest) -> TextResponse:
    """
    Analyze an image using multimodal AI capabilities.

    This endpoint accepts an image file path and a text prompt, then uses
    the configured AI model to analyze the image and provide a response.
    Note: This feature requires a multimodal-capable AI model.

    Args:
        request: Image analysis request with prompt and image path

    Returns:
        TextResponse: AI analysis of the image

    Raises:
        HTTPException: 501 if not implemented, 500 for processing errors

    Example:
        ```bash
        curl -X POST "http://localhost:8009/api/lmstudio/analyze-image" \
             -H "Content-Type: application/json" \
             -d '{
               "prompt": "What do you see in this image?",
               "image_path": "/path/to/image.jpg"
             }'
        ```
    """
    # Placeholder implementation - this would need to be implemented based on
    # the specific multimodal AI model being used
    logger.warning("Image analysis endpoint called but not fully implemented")

    return TextResponse(
        text="Image analysis functionality is not yet implemented. "
        "This endpoint is a placeholder for future multimodal AI capabilities."
    )
