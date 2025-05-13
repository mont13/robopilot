"""
Controller for LM Studio API integration.
"""

import json
import logging
import time
from typing import List, Optional, Union

import lmstudio as lms
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..config.settings import get_settings
from ..repository.chat_session_repository import ChatSessionRepository
from ..repository.llm_connection_repository import LLMConnectionRepository
from ..utils.lmstudio_client import ChatMessage, ChatSession, LMStudioClient
from ..utils.lmstudio_tools import PREDEFINED_TOOLS
from ..utils.praison_integration.agents import (
    get_llm_config,
    process_with_multi_agents_async,
)

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
    use_praison: bool = Field(
        False, description="Whether to use PraisonAI agents for processing"
    )


class TextResponse(BaseModel):
    """Response model for text generation."""

    text: str


class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis."""

    prompt: str = Field(..., description="Text prompt to accompany the image")
    image_path: str = Field(..., description="Path to the image file")


class PraisonAgentsRequest(BaseModel):
    """Request model for PraisonAI multi-agent processing."""

    message: str = Field(..., description="User message to process")
    session_id: Optional[str] = Field(None, description="Session ID for chat history")
    async_execution: bool = Field(
        False, description="Whether to execute asynchronously"
    )
    stream: bool = Field(False, description="Whether to stream the response")
    temperature: float = Field(0.7, description="Temperature for generation")
    tools_enabled: bool = Field(True, description="Whether to enable tool usage")
    connection_id: Optional[str] = Field(
        None, description="ID of LLM connection to use"
    )


class PraisonAgentsTestRequest(BaseModel):
    """Test request for PraisonAI integration with comprehensive options."""

    message: str = Field(..., description="User message to process")
    session_id: Optional[str] = Field(None, description="Session ID for chat history")
    session_name: Optional[str] = Field(
        None, description="Name for new session if created"
    )
    stream: bool = Field(False, description="Whether to stream the response")
    temperature: float = Field(0.7, description="Temperature for generation")
    tools_enabled: bool = Field(True, description="Whether to enable tools")
    load_history: bool = Field(True, description="Whether to load chat history")
    save_history: bool = Field(True, description="Whether to save messages to history")
    reflection_enabled: bool = Field(True, description="Enable agent self-reflection")
    reflection_depth: int = Field(2, description="Depth of agent self-reflection")
    include_function_calls: bool = Field(
        True, description="Include function call history"
    )
    connection_id: Optional[str] = Field(
        None, description="ID of LLM connection to use"
    )


@router.post("/praison/chat", response_model=TextResponse)
async def process_with_praison_agents(
    request: PraisonAgentsRequest,
    client: LMStudioClient = Depends(get_lmstudio_client),
):
    """
    Process a message using PraisonAI agents with chat history support.

    This endpoint provides dedicated access to PraisonAI multi-agent processing
    with full chat history integration.
    """
    try:
        # Get repository for chat operations
        repo = ChatSessionRepository()

        # Get specified session or active session or create a new one
        session_id = request.session_id
        if session_id:
            # Check if session exists
            chat_session = await repo.get_session_by_id(session_id)
            if not chat_session:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chat session with ID {session_id} not found",
                )
        else:
            # Get active session or create new one
            active_session = await repo.get_active_session()
            if not active_session:
                active_session = await repo.create_session("New PraisonAI Chat")
            session_id = active_session.id

        logger.info(f"Processing with PraisonAI agents for session {session_id}")

        # Get specific LLM config if connection_id is provided
        llm_config = None
        if request.connection_id:
            # Get connection from repository
            llm_repo = LLMConnectionRepository()
            connection = await llm_repo.get_connection_by_id(request.connection_id)
            if not connection:
                raise HTTPException(
                    status_code=404,
                    detail=f"LLM connection with ID {request.connection_id} not found",
                )
            # Convert to LLM config
            llm_config = llm_repo.connection_to_llm_config(connection).model_dump()
            logger.info(
                f"Using LLM connection: {connection.name} ({connection.provider})"
            )

        # Process with PraisonAI agents
        result = await process_with_multi_agents_async(
            user_input=request.message,
            session_id=session_id,
            chat_repository=repo,
            llm_config=llm_config,
        )

        # Save messages to the database
        messages_to_save = result.get("messages_to_save", [])
        for message in messages_to_save:
            message_id = await repo.add_message(
                session_id=session_id, role=message["role"], content=message["content"]
            )
            logger.debug(f"Saved {message['role']} message to session {session_id}")

            # Log function calls if any were made
            if message["role"] == "assistant" and result.get("tool_calls"):
                for tool_call in result.get("tool_calls", []):
                    try:
                        await repo.log_function_call(
                            session_id=session_id,
                            message_id=message_id.id if message_id else None,
                            function_name=tool_call.get(
                                "function_name", "unknown_function"
                            ),
                            arguments=tool_call.get("arguments", {}),
                            result=tool_call.get("result", None),
                        )
                        logger.info(
                            f"Logged function call {tool_call.get('function_name')} for session {session_id}"
                        )
                    except Exception as func_err:
                        logger.error(f"Error logging function call: {func_err}")

        # Extract response
        response_text = result.get("response", "")
        if not response_text:
            # This should rarely happen now as we handle this in the agent process
            response_text = "No response generated from agents."

        # If streaming is requested, return a streaming response
        if request.stream:

            async def response_generator():
                # Yield the entire response as a single chunk
                yield f"data: {json.dumps({'text': response_text})}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                response_generator(), media_type="text/event-stream"
            )
        else:
            return {"text": response_text}

    except Exception as e:
        logger.error(f"Failed to process with PraisonAI agents: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process with PraisonAI agents: {str(e)}"
        )


@router.post("/praison/test", response_model=TextResponse)
async def test_praison_integration(
    request: PraisonAgentsTestRequest,
    client: LMStudioClient = Depends(get_lmstudio_client),
):
    """
    Test endpoint for PraisonAI integration with comprehensive configuration options.

    This endpoint allows testing various features of the PraisonAI integration:
    - Chat history loading and saving
    - Tool usage and function call logging
    - Agent self-reflection
    - Session management
    - LLM connection selection
    """
    try:
        # Get repository for chat operations
        repo = ChatSessionRepository()

        # Session management
        session_id = request.session_id
        if session_id:
            # Check if session exists
            chat_session = await repo.get_session_by_id(session_id)
            if not chat_session:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chat session with ID {session_id} not found",
                )
        else:
            # Get active session or create new one
            active_session = await repo.get_active_session()
            if not active_session:
                session_name = request.session_name or "PraisonAI Test Session"
                active_session = await repo.create_session(session_name)
            session_id = active_session.id

        logger.info(f"Testing PraisonAI with session {session_id}")

        # Construct the response object for debugging/monitoring
        debug_info = {
            "session_id": session_id,
            "config": {
                "tools_enabled": request.tools_enabled,
                "load_history": request.load_history,
                "save_history": request.save_history,
                "reflection_enabled": request.reflection_enabled,
                "reflection_depth": request.reflection_depth,
                "temperature": request.temperature,
            },
        }

        # Add chat history loading info to debug
        if request.load_history:
            try:
                messages = await repo.get_messages(session_id)
                debug_info["history_loaded"] = len(messages)
            except Exception as e:
                debug_info["history_error"] = str(e)

        # Process with PraisonAI agents with custom configuration
        from praisonaiagents import PraisonAIAgents, Task

        from ..utils.lmstudio_tools import PREDEFINED_TOOLS
        from ..utils.praison_integration.agents import LLMBackedAgent

        # Get LLM config - either from specified connection or default
        llm_config = None
        if request.connection_id:
            # Get connection from repository
            llm_repo = LLMConnectionRepository()
            connection = await llm_repo.get_connection_by_id(request.connection_id)
            if not connection:
                raise HTTPException(
                    status_code=404,
                    detail=f"LLM connection with ID {request.connection_id} not found",
                )
            # Convert to LLM config
            llm_config = llm_repo.connection_to_llm_config(connection).model_dump()
            debug_info["connection"] = {
                "id": connection.id,
                "name": connection.name,
                "provider": connection.provider,
                "model": connection.model_name,
            }
            logger.info(
                f"Using LLM connection: {connection.name} ({connection.provider})"
            )
        else:
            # Use default LM Studio config
            llm_config = {
                "model": "gpt-3.5-turbo",  # This gets mapped to whatever model is loaded in LM Studio
                "api_key": None,  # LM Studio doesn't require a real API key
                "base_url": settings.lmstudio_host,  # Point to LM Studio API
                "temperature": request.temperature,
                "max_tokens": 1000,
                "response_format": {"type": "text"},
            }

        # Create custom agents with the requested configuration
        # We'll create them directly rather than using create_master_agent to have more control
        master_agent = LLMBackedAgent(
            name="TestMasterAgent",
            role="Communication Coordinator",
            goal="Handle user interactions and coordinate with other agents",
            backstory="""You are the main communication hub for the AI system testing.
            Your primary responsibility is to interpret user requests, maintain
            conversation context, and delegate specialized tasks to other agents when needed.
            Use chat history to maintain context and provide coherent responses.""",
            llm_config=llm_config,
            tools=None,
            self_reflect=request.reflection_enabled,
            max_reflect=request.reflection_depth,
        )

        tools_agent = LLMBackedAgent(
            name="TestToolsAgent",
            role="Tool Specialist",
            goal="Execute specialized tools and operations based on requests",
            backstory="""You are an expert at using various tools to accomplish tasks.
            When the master agent delegates a task to you, you select and use the
            appropriate tool to complete it efficiently. Consider chat history context
            to avoid repeating operations unnecessarily.""",
            llm_config=llm_config,
            tools=PREDEFINED_TOOLS if request.tools_enabled else None,
            self_reflect=request.reflection_enabled,
            max_reflect=request.reflection_depth,
        )

        # Define tasks
        master_task = Task(
            name="handle_test_request",
            description="Process the test request and determine if tools are needed",
            expected_output="Processed response or delegation to tools agent",
            agent=master_agent,
        )

        tools_task = Task(
            name="execute_test_tools",
            description="Execute specialized tools based on the test request",
            expected_output="Results from tool execution",
            agent=tools_agent,
            context=[master_task],  # The tools task has context from the master task
        )

        # Create agents system
        agents = PraisonAIAgents(
            agents=[master_agent, tools_agent],
            tasks=[master_task, tools_task],
            process="hierarchical",
            verbose=1,
        )

        # Set user input as state for the agents to access
        agents.set_state("user_input", request.message)

        # For tracking tool calls
        tool_calls_recorder = []

        # Define a tool call callback function
        async def on_tool_call(function_name, arguments, result):
            tool_calls_recorder.append(
                {
                    "function_name": function_name,
                    "arguments": arguments,
                    "result": result,
                }
            )
            logger.info(f"Test tool call recorded: {function_name}")

        # Attach callback to agents
        agents.tool_call_callback = on_tool_call

        # Add chat history if enabled
        if request.load_history:
            try:
                # Get messages from the session
                messages = await repo.get_messages(session_id)

                # Format messages for the agents
                chat_history = []
                for msg in messages:
                    chat_history.append({"role": msg.role, "content": msg.content})

                if chat_history:
                    agents.set_state("chat_history", chat_history)
                    debug_info["chat_history_size"] = len(chat_history)
            except Exception as e:
                logger.error(f"Error loading test chat history: {e}")
                debug_info["history_error"] = str(e)

        # Include function call history if requested
        if request.include_function_calls:
            try:
                function_calls = await repo.get_function_calls(session_id)
                if function_calls:
                    agents.set_state("function_call_history", function_calls)
                    debug_info["function_call_history_size"] = len(function_calls)
            except Exception as e:
                logger.error(f"Error loading function call history: {e}")
                debug_info["function_history_error"] = str(e)

        # Start the multi-agent system asynchronously
        start_time = time.time()
        result = await agents.astart()
        processing_time = time.time() - start_time

        # Add processing time to debug info
        debug_info["processing_time"] = f"{processing_time:.2f}s"

        # Extract response
        response_text = result.get("task_results", {}).get(
            "handle_test_request", "No response generated"
        )
        tool_results = result.get("task_results", {}).get("execute_test_tools", None)

        # If tool results but no response, format a response about the tool execution
        if not response_text and tool_results:
            response_text = f"Tool execution results: {str(tool_results)}"

        # Save messages if requested
        if request.save_history:
            # Messages to save
            messages_to_save = [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": response_text},
            ]

            saved_message_ids = []
            for message in messages_to_save:
                message_id = await repo.add_message(
                    session_id=session_id,
                    role=message["role"],
                    content=message["content"],
                )
                if message_id:
                    saved_message_ids.append(message_id.id)
                logger.debug(
                    f"Saved test {message['role']} message to session {session_id}"
                )

            debug_info["saved_messages"] = len(saved_message_ids)

            # Log function calls if any were made and assistant message was saved
            if tool_calls_recorder and saved_message_ids:
                assistant_message_id = (
                    saved_message_ids[-1] if len(saved_message_ids) > 1 else None
                )
                logged_calls = 0

                for tool_call in tool_calls_recorder:
                    try:
                        await repo.log_function_call(
                            session_id=session_id,
                            message_id=assistant_message_id,
                            function_name=tool_call.get(
                                "function_name", "unknown_function"
                            ),
                            arguments=tool_call.get("arguments", {}),
                            result=tool_call.get("result", None),
                        )
                        logged_calls += 1
                    except Exception as func_err:
                        logger.error(f"Error logging test function call: {func_err}")

                debug_info["logged_function_calls"] = logged_calls

        # Attach debug info to response
        final_response = {"text": response_text, "debug": debug_info}

        # If streaming is requested, return a streaming response
        if request.stream:

            async def response_generator():
                # Yield the entire response as a single chunk
                yield f"data: {json.dumps({'text': response_text, 'debug': debug_info})}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                response_generator(), media_type="text/event-stream"
            )
        else:
            return final_response

    except Exception as e:
        logger.error(f"PraisonAI test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PraisonAI test failed: {str(e)}")


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
            ChatMessage(
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
            )
            for msg in messages
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
    - Using PraisonAI agents if requested
    """
    try:
        # Use PraisonAI agents if requested
        if request.use_praison and request.role == "user":
            # Get active session or create a new one
            repo = ChatSessionRepository()
            active_session = await repo.get_active_session()
            if not active_session:
                active_session = await repo.create_session("New PraisonAI Chat")

            session_id = active_session.id

            # Get LLM config from database
            llm_config = await get_llm_config()

            # Process directly with LM Studio for now until agents are fixed
            logger.info(
                f"Processing user message for session {session_id}"
            )

            # Save user message to session
            await repo.add_message(
                session_id=session_id,
                role="user",
                content=request.content,
            )

            # Get a direct response from the model
            response = client.generate_response(
                prompt=request.content,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False
            )

            # Save assistant message to session
            await repo.add_message(
                session_id=session_id,
                role="assistant",
                content=response,
            )

            logger.info(f"Saved user message to session {session_id}")
            logger.info(f"Saved assistant message to session {session_id}")

            return TextResponse(text=response)


            # Save messages to the database
            messages_to_save = result.get("messages_to_save", [])
            for message in messages_to_save:
                message_id = await repo.add_message(
                    session_id=session_id,
                    role=message["role"],
                    content=message["content"],
                )
                logger.info(f"Saved {message['role']} message to session {session_id}")

                # Log function calls if any were made
                if message["role"] == "assistant" and result.get("tool_calls"):
                    for tool_call in result.get("tool_calls", []):
                        try:
                            await repo.log_function_call(
                                session_id=session_id,
                                message_id=message_id.id if message_id else None,
                                function_name=tool_call.get(
                                    "function_name", "unknown_function"
                                ),
                                arguments=tool_call.get("arguments", {}),
                                result=tool_call.get("result", None),
                            )
                            logger.info(
                                f"Logged function call {tool_call.get('function_name')} for session {session_id}"
                            )
                        except Exception as func_err:
                            logger.error(f"Error logging function call: {func_err}")

            # Extract response from multi-agent processing
            response_text = result.get("response", "")
            if not response_text:
                # This should rarely happen now as we handle this in the agent process
                response_text = "No response generated from agents."

            # If streaming is requested, return a streaming response
            if request.stream:

                async def response_generator():
                    # Yield the entire response as a single chunk
                    yield f"data: {json.dumps({'text': response_text})}\n\n"
                    yield "data: [DONE]\n\n"

                return StreamingResponse(
                    response_generator(), media_type="text/event-stream"
                )
            else:
                return {"text": response_text}

        # Regular LM Studio processing
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
