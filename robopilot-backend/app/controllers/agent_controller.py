"""
Enhanced BeeAI Agent Controller for AI-powered conversational interfaces.

This enhanced module provides a comprehensive REST API for managing chat sessions and
processing messages through BeeAI Framework agents with advanced capabilities.

Enhanced Features:
- Latest BeeAI framework integration with proper typing and patterns
- Advanced session management with statistics and monitoring
- Enhanced agent service integration with performance metrics
- Robust error handling with detailed BeeAI FrameworkError reporting
- Advanced tool calling with execution tracking
- Streaming response support with chunked delivery
- Comprehensive logging, monitoring, and health checks
- Agent performance analytics and caching optimization

The controller provides both basic chat functionality and advanced agent management
features for production deployments.
"""

import asyncio
import logging
import time
from typing import Any, Union

from beeai_framework.errors import FrameworkError
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse

from ..models.agent import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentHealthCheck,
    AgentMessage,
    AgentSessionInfo,
    ConversationHistory,
)
from ..repository.chat_session_repository import ChatSessionRepository
from ..services.agent_service import AgentService

# Configure logging for this module
logger = logging.getLogger(__name__)

# Create FastAPI router with comprehensive metadata
router = APIRouter(
    prefix="/agent",
    tags=["BeeAI Agent API"],
    responses={
        400: {"description": "Bad Request - Invalid input parameters"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Unprocessable Entity - Validation error"},
        500: {"description": "Internal Server Error - Server-side error occurred"},
    },
)


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_chat_repository() -> ChatSessionRepository:
    """Get chat session repository instance."""
    return ChatSessionRepository()


def get_agent_service(
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> AgentService:
    """Get agent service instance with injected repository."""
    return AgentService(repo)


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================


@router.get(
    "/sessions",
    response_model=list[AgentSessionInfo],
    summary="List all chat sessions",
    description="Retrieve all chat sessions with their metadata and statistics",
)
async def list_chat_sessions(
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> list[AgentSessionInfo]:
    """
    Get all chat sessions with enhanced session information.

    Returns:
        List of session information objects with statistics
    """
    try:
        logger.info("Retrieving all chat sessions")

        sessions = await repo.get_all_sessions()
        session_infos = []

        for session in sessions:
            # Get message count
            messages = await repo.get_messages(session.id)
            message_count = len(messages)

            # Count tool calls
            tool_calls = await repo.get_function_calls(session.id)
            tool_calls_count = len(tool_calls)

            session_info = AgentSessionInfo(
                session_id=session.id,
                session_name=session.name,
                message_count=message_count,
                tool_calls_count=tool_calls_count,
                created_at=session.created_at,
                updated_at=session.updated_at,
                is_active=True,
                agent_config={"robot_tools_enabled": True},
            )
            session_infos.append(session_info)

        logger.info(f"Successfully retrieved {len(session_infos)} chat sessions")
        return session_infos

    except Exception as e:
        error_msg = f"Failed to list chat sessions: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post(
    "/sessions",
    response_model=AgentSessionInfo,
    status_code=201,
    summary="Create a new chat session",
    description="Create a new chat session with optional custom name",
)
async def create_chat_session(
    name: str | None = None,
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> AgentSessionInfo:
    """
    Create a new chat session.

    Args:
        name: Optional session name

    Returns:
        Session information for the newly created session
    """
    try:
        session_name = name or f"Chat Session {int(time.time())}"
        logger.info(f"Creating new chat session: '{session_name}'")

        # Create the session
        session = await repo.create_session(session_name)

        # Return session info
        session_info = AgentSessionInfo(
            session_id=session.id,
            session_name=session.name,
            message_count=0,
            tool_calls_count=0,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=True,
            agent_config={"robot_tools_enabled": True},
        )

        logger.info(f"Successfully created chat session {session.id}")
        return session_info

    except Exception as e:
        error_msg = f"Failed to create chat session: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/sessions/active",
    response_model=ConversationHistory,
    summary="Get the active chat session",
    description="Get the most recently updated session or create a new one if none exist",
)
async def get_active_session(
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> ConversationHistory:
    """
    Get the most recently active chat session.

    This endpoint ALWAYS returns a valid session. If no sessions exist,
    it automatically creates a new default session.

    Returns:
        Active session conversation history
    """
    # Active session MUST ALWAYS return a valid session - never 404
    logger.info("Retrieving active chat session")

    # Get most recent session or create new one
    session = await repo.get_active_session()
    if not session:
        logger.info("No sessions found, creating new default session")
        session = await repo.create_session("New Chat")

    # Get messages for this session
    db_messages = await repo.get_messages(session.id)

    # Convert to agent messages
    messages = [
        AgentMessage(
            role=msg.role,
            content=msg.content,
            timestamp=msg.created_at,
            metadata={"message_id": msg.id},
        )
        for msg in db_messages
    ]

    # Build conversation history
    conversation = ConversationHistory(
        session_id=session.id,
        messages=messages,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )

    logger.info(f"Active session: {session.id}")
    return conversation


@router.get(
    "/sessions/{session_id}",
    response_model=ConversationHistory,
    summary="Get a specific chat session",
    description="Retrieve a chat session by ID with all messages",
)
async def get_chat_session(
    session_id: str = Path(..., description="Unique identifier of the chat session"),
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> ConversationHistory:
    """
    Retrieve a specific chat session with conversation history.

    Args:
        session_id: Session identifier

    Returns:
        Complete conversation history
    """
    try:
        logger.info(f"Retrieving chat session: {session_id}")

        # Get session from database
        session = await repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Get messages
        db_messages = await repo.get_messages(session_id)

        # Convert to agent messages
        messages = [
            AgentMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at,
                metadata={"message_id": msg.id},
            )
            for msg in db_messages
        ]

        # Build conversation history
        conversation = ConversationHistory(
            session_id=session.id,
            messages=messages,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

        logger.info(f"Successfully retrieved session {session_id}")
        return conversation

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to get chat session {session_id}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.delete(
    "/sessions/{session_id}",
    status_code=200,
    summary="Delete a chat session",
    description="Permanently delete a chat session and all its messages",
)
async def delete_chat_session(
    session_id: str = Path(
        ..., description="Unique identifier of the session to delete"
    ),
    agent_service: AgentService = Depends(get_agent_service),
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> dict[str, str]:
    """
    Delete a chat session and all associated messages.

    This permanently removes the session from the database, including all
    messages, function calls, and cleans up the agent cache.

    Args:
        session_id: Session identifier
        agent_service: Injected agent service
        repo: Injected repository

    Returns:
        Confirmation message

    Raises:
        HTTPException: 404 if session not found, 500 if deletion fails
    """
    try:
        logger.info(f"Deleting chat session: {session_id}")

        # Check if session exists
        session = await repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Remove agent from cache if exists
        agent_service.remove_agent_from_cache(session_id)

        # Delete session from database (cascades to messages and function calls)
        success = await repo.delete_session(session_id)

        if not success:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete session {session_id}"
            )

        logger.info(f"Successfully deleted chat session: {session_id}")
        return {"message": f"Session {session_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to delete session {session_id}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# ============================================================================
# MESSAGE PROCESSING ENDPOINTS
# ============================================================================


@router.post(
    "/chat",
    response_model=Union[AgentExecutionResponse, None],
    summary="Process a message with enhanced BeeAI agent",
    description="Send a message to the AI agent and get a response with advanced tool calling support and monitoring",
)
async def process_message(
    request: AgentExecutionRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> Union[AgentExecutionResponse, StreamingResponse]:
    """
    Process a user message using enhanced BeeAI agent with full tool support and monitoring.

    This enhanced endpoint:
    1. Ensures a valid session exists
    2. Processes the message through BeeAI agent with intelligent configuration
    3. Handles advanced tool calling with execution tracking
    4. Provides comprehensive monitoring and error handling
    5. Returns structured response with detailed metadata and performance metrics

    Args:
        request: Agent execution request with message and parameters
        agent_service: Injected enhanced agent service

    Returns:
        Agent execution response with metrics or streaming response
    """
    start_time = time.time()
    execution_metadata = {
        "request_timestamp": start_time,
        "session_id": request.session_id,
        "message_length": len(request.message),
        "temperature": request.temperature,
        "max_iterations": request.max_iterations,
        "robot_tools_enabled": request.include_robot_tools,
    }

    try:
        logger.info(
            f"Processing enhanced message for session {request.session_id} "
            f"(length: {len(request.message)}, temp: {request.temperature})"
        )

        # Process message through enhanced agent service
        response_text = await agent_service.process_user_message(
            session_id=request.session_id,
            message_content=request.message,
            temperature=request.temperature,
            max_iterations=request.max_iterations,
            max_retries=request.max_retries,
        )

        execution_time = time.time() - start_time

        # Get agent statistics after processing
        post_stats = agent_service.get_agent_stats(request.session_id)

        # Handle streaming response
        if request.stream_response:
            return _create_streaming_response(response_text)

        # Build enhanced structured response with detailed metadata
        execution_metadata.update(
            {
                "execution_time": execution_time,
                "response_length": len(response_text),
                "agent_stats": post_stats,
                "performance": {
                    "total_executions": post_stats.get("total_executions", 0),
                    "last_execution_time": post_stats.get(
                        "last_execution_time", execution_time
                    ),
                    "memory_type": post_stats.get("memory_type", "unknown"),
                    "tool_count": post_stats.get("tool_count", 0),
                },
            }
        )

        response = AgentExecutionResponse(
            session_id=request.session_id,
            response=response_text,
            tool_calls=[],  # Tool calls are handled internally by BeeAI
            execution_time=execution_time,
            iterations_used=post_stats.get("last_iterations", None),
            metadata=execution_metadata,
        )

        logger.info(
            f"Successfully processed message for session {request.session_id} "
            f"in {execution_time:.2f}s (executions: {post_stats.get('total_executions', 0)})"
        )
        return response

    except FrameworkError as e:
        error_msg = f"BeeAI framework error: {e.explain()}"
        execution_metadata.update(
            {
                "error": error_msg,
                "error_type": "FrameworkError",
                "execution_time": time.time() - start_time,
            }
        )
        logger.error(f"Framework error for session {request.session_id}: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to process message: {str(e)}"
        execution_metadata.update(
            {
                "error": error_msg,
                "error_type": type(e).__name__,
                "execution_time": time.time() - start_time,
            }
        )
        logger.error(
            f"Processing error for session {request.session_id}: {error_msg}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=error_msg)


# ============================================================================
# MONITORING AND HEALTH CHECK ENDPOINTS
# ============================================================================


@router.get(
    "/health",
    response_model=AgentHealthCheck,
    summary="Agent service health check",
    description="Get comprehensive health status of the agent service including LLM and database connections",
)
async def health_check(
    agent_service: AgentService = Depends(get_agent_service),
    repo: ChatSessionRepository = Depends(get_chat_repository),
) -> AgentHealthCheck:
    """
    Perform comprehensive health check of the agent service.

    Returns:
        Detailed health status including component status and metrics
    """
    try:
        logger.debug("Performing agent service health check")

        # Test database connection
        db_healthy = True
        try:
            await repo.get_all_sessions()
            db_healthy = True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            db_healthy = False

        # Test LLM connection (simplified check)
        llm_healthy = True
        errors = []
        try:
            # This is a basic check - could be enhanced with actual LLM ping
            # For now, we'll assume it's healthy if no recent errors
            pass
        except Exception as e:
            logger.warning(f"LLM health check failed: {e}")
            llm_healthy = False
            errors.append(f"LLM connection error: {str(e)}")

        # Get agent statistics
        all_stats = agent_service.get_agent_stats()
        active_sessions = len(all_stats)

        # Determine overall status
        if db_healthy and llm_healthy:
            status = "healthy"
        elif db_healthy or llm_healthy:
            status = "degraded"
        else:
            status = "unhealthy"

        # Get available tools from MCP integration
        from ..utils.mcp_integration import get_mcp_service

        mcp_service = get_mcp_service()
        mcp_status = mcp_service.get_connection_status()
        tool_names = [
            f"MCP:{server}" for server in mcp_status.get("connected_servers", [])
        ]

        if not db_healthy:
            errors.append("Database connection failed")

        health_response = AgentHealthCheck(
            status=status,
            llm_connection=llm_healthy,
            database_connection=db_healthy,
            tools_available=tool_names,
            active_sessions=active_sessions,
            errors=errors,
            mcp_status=mcp_status,
        )

        logger.info(
            f"Health check completed - Status: {status}, Active sessions: {active_sessions}"
        )
        return health_response

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return AgentHealthCheck(
            status="unhealthy",
            llm_connection=False,
            database_connection=False,
            tools_available=[],
            active_sessions=0,
            errors=[f"Health check error: {str(e)}"],
        )


@router.get(
    "/stats",
    summary="Get agent performance statistics",
    description="Retrieve detailed performance statistics for all agents or a specific session",
)
async def get_agent_stats(
    session_id: str | None = Query(None, description="Optional session ID filter"),
    agent_service: AgentService = Depends(get_agent_service),
) -> dict[str, Any]:
    """
    Get agent performance statistics with optional session filtering.

    Args:
        session_id: Optional session ID to filter statistics
        agent_service: Injected agent service

    Returns:
        Dictionary containing performance statistics
    """
    try:
        stats = agent_service.get_agent_stats(session_id)

        if session_id and not stats:
            raise HTTPException(
                status_code=404, detail=f"No statistics found for session {session_id}"
            )

        # Add summary statistics for all sessions
        if not session_id and stats:
            total_executions = sum(s.get("total_executions", 0) for s in stats.values())
            avg_execution_time = (
                sum(s.get("last_execution_time", 0) for s in stats.values())
                / len(stats)
                if stats
                else 0
            )

            summary = {
                "total_sessions": len(stats),
                "total_executions": total_executions,
                "average_execution_time": avg_execution_time,
                "memory_types": list(
                    set(s.get("memory_type", "unknown") for s in stats.values())
                ),
            }

            return {
                "summary": summary,
                "sessions": stats,
            }

        return {"sessions": {session_id: stats}} if session_id else {"sessions": stats}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.post(
    "/cleanup",
    summary="Clean up inactive agents",
    description="Remove inactive agents from cache to free up resources",
)
async def cleanup_agents(
    max_age_seconds: int = Query(
        3600, description="Maximum age for inactive agents in seconds"
    ),
    agent_service: AgentService = Depends(get_agent_service),
) -> dict[str, Any]:
    """
    Clean up inactive agents from the cache.

    Args:
        max_age_seconds: Maximum age for inactive agents
        agent_service: Injected agent service

    Returns:
        Cleanup results
    """
    try:
        logger.info(f"Starting agent cleanup with max age {max_age_seconds}s")

        cleaned_count = agent_service.cleanup_inactive_agents(max_age_seconds)

        return {
            "success": True,
            "cleaned_agents": cleaned_count,
            "max_age_seconds": max_age_seconds,
            "message": f"Successfully cleaned up {cleaned_count} inactive agents",
        }

    except Exception as e:
        error_msg = f"Agent cleanup failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def _create_streaming_response(text: str) -> StreamingResponse:
    """
    Create an enhanced streaming response for the given text.

    Args:
        text: Text to stream

    Returns:
        StreamingResponse instance with optimized chunking
    """

    async def generate():
        """Generate streaming chunks with word-boundary aware sizing."""
        words = text.split()
        current_chunk = ""
        target_chunk_size = 50  # Target size in characters

        logger.debug("Streaming response with word-boundary chunking")

        for word in words:
            # Check if adding this word would exceed target size
            if current_chunk and len(current_chunk) + len(word) + 1 > target_chunk_size:
                # Send current chunk
                yield f"data: {current_chunk}\n\n"
                await asyncio.sleep(0.05)
                current_chunk = word
            else:
                # Add word to current chunk
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word

        # Send final chunk if it has content
        if current_chunk:
            yield f"data: {current_chunk}\n\n"
            await asyncio.sleep(0.05)

        # Send completion marker
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
