"""
Enhanced BeeAI Agent Service for managing conversational AI interactions.

This service provides a comprehensive interface for managing AI agents using the latest BeeAI framework
patterns. It features improved memory management, advanced tool calling, proper event handling,
and robust error recovery mechanisms.

Key Improvements:
- Uses latest BeeAI framework patterns and types
- Enhanced memory management with TokenMemory for production workloads
- Improved tool calling with proper event handling
- Better error handling and recovery mechanisms
- Advanced agent configuration and monitoring
- Proper resource cleanup and lifecycle management
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from beeai_framework.adapters.ollama.backend.chat import OllamaChatModel
from beeai_framework.adapters.openai.backend.chat import OpenAIChatModel
from beeai_framework.agents import AgentExecutionConfig
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend import (
    AssistantMessage,
    SystemMessage,
    UserMessage,
)
from beeai_framework.emitter import EventMeta
from beeai_framework.errors import FrameworkError
from beeai_framework.memory import BaseMemory, TokenMemory, UnconstrainedMemory
from beeai_framework.tools import AnyTool

from ..models.config import ProviderType
from ..repository.chat_session_repository import ChatSessionRepository
from ..repository.llm_connection_repository import LLMConnectionRepository
from ..utils.mcp_integration import get_mcp_tools, initialize_mcp_integration

logger = logging.getLogger(__name__)


class AgentService:
    """
    Enhanced service class for managing BeeAI agents and conversations.

    This service provides:
    - Latest BeeAI framework integration with proper typing
    - Advanced agent creation and configuration with ReActAgent
    - Intelligent memory management (TokenMemory for production, UnconstrainedMemory for dev)
    - Modern tool registration using @tool decorator pattern
    - Enhanced conversation processing with proper event handling
    - Robust error handling and recovery mechanisms
    - Agent performance monitoring and caching
    """

    def __init__(self, chat_repository: ChatSessionRepository):
        self.chat_repository = chat_repository
        self._agent_cache: dict[str, ReActAgent] = {}
        self._agent_stats: dict[str, dict[str, Any]] = {}
        self._memory_type = os.getenv("BEEAI_MEMORY_TYPE", "unconstrained")
        self._max_memory_tokens = int(os.getenv("BEEAI_MAX_MEMORY_TOKENS", "8192"))

        logger.info(f"AgentService initialized with memory type: {self._memory_type}")

    async def create_agent(
        self,
        session_id: str,
        include_robot_tools: bool = True,
        custom_tools: list[AnyTool] | None = None,
        system_prompt: str | None = None,
    ) -> ReActAgent:
        """
        Create and configure a BeeAI ReAct agent for a specific session with enhanced capabilities.

        Args:
            session_id: Unique session identifier
            include_robot_tools: Whether to include robot control tools
            custom_tools: Additional custom tools to register
            system_prompt: Optional system prompt override

        Returns:
            Configured ReActAgent instance with advanced memory management

        Raises:
            ValueError: If LLM configuration is invalid
            FrameworkError: If agent creation fails
        """
        try:
            logger.info(f"Creating enhanced agent for session {session_id}")
            start_time = asyncio.get_event_loop().time()

            # Create ChatModel instance from database configuration
            llm = await self._create_chat_model(session_id)

            # Prepare tools with proper validation
            tools = []
            if include_robot_tools:
                # Initialize MCP integration if needed
                await initialize_mcp_integration()

                # Get tools from MCP servers
                mcp_tools = await get_mcp_tools()
                tools.extend(mcp_tools)
                logger.debug(
                    f"Added {len(mcp_tools)} MCP tools: {[getattr(tool, 'name', str(tool)) for tool in mcp_tools]}"
                )

            if custom_tools:
                tools.extend(custom_tools)
                logger.debug(f"Added {len(custom_tools)} custom tools")

            # Create intelligent memory with conversation history
            memory = await self._create_intelligent_memory(session_id, llm)

            # Add system prompt if provided and memory is empty
            if system_prompt and len(memory.messages) == 0:
                await memory.add(SystemMessage(system_prompt))

            # Create agent with enhanced configuration
            agent = ReActAgent(
                llm=llm,
                tools=tools,
                memory=memory,
            )

            # Cache agent and track statistics
            self._agent_cache[session_id] = agent
            self._agent_stats[session_id] = {
                "created_at": asyncio.get_event_loop().time(),
                "creation_time": asyncio.get_event_loop().time() - start_time,
                "tool_count": len(tools),
                "memory_type": type(memory).__name__,
                "message_count": len(memory.messages),
                "last_used": None,
                "total_executions": 0,
            }

            logger.info(
                f"Successfully created agent for session {session_id} with {len(tools)} tools "
                f"and {type(memory).__name__} memory in {self._agent_stats[session_id]['creation_time']:.2f}s"
            )
            return agent

        except Exception as e:
            error_msg = f"Failed to create agent for session {session_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FrameworkError(error_msg)

    async def get_or_create_agent(
        self,
        session_id: str,
        include_robot_tools: bool = True,
        custom_tools: list[AnyTool] | None = None,
    ) -> ReActAgent:
        """
        Get cached agent or create new one for session.

        Args:
            session_id: Session identifier
            include_robot_tools: Whether to include robot control tools
            custom_tools: Additional custom tools to register

        Returns:
            ReActAgent instance
        """
        if session_id in self._agent_cache:
            return self._agent_cache[session_id]

        return await self.create_agent(
            session_id,
            include_robot_tools=include_robot_tools,
            custom_tools=custom_tools,
        )

    async def process_user_message(
        self,
        session_id: str,
        message_content: str,
        temperature: float | None = None,
        max_iterations: int | None = None,
        max_retries: int | None = None,
    ) -> str:
        """
        Process a user message and generate AI response with enhanced monitoring and error handling.

        Args:
            session_id: Session identifier
            message_content: User message content
            temperature: Optional temperature override
            max_iterations: Optional max iterations override
            max_retries: Optional max retries override

        Returns:
            AI-generated response text with tool call results

        Raises:
            FrameworkError: If message processing fails
        """
        try:
            start_time = asyncio.get_event_loop().time()
            logger.info(
                f"Processing user message for session {session_id} (length: {len(message_content)})"
            )

            # Get session - it should exist (created by controller if needed)
            session = await self.chat_repository.get_session_by_id(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Save user message to database
            await self.chat_repository.add_message(
                session_id=session_id, role="user", content=message_content
            )

            # Get or create agent
            agent = await self.get_or_create_agent(session_id=session_id)

            # Add dynamic system prompt if there's no system message yet
            has_system_message = any(
                isinstance(msg, SystemMessage) for msg in agent.memory.messages
            )
            if not has_system_message:
                system_prompt = self._get_dynamic_system_prompt(message_content)
                await agent.memory.add(SystemMessage(system_prompt))

            # Update temperature if provided
            original_temp = None
            if temperature is not None:
                try:
                    # Try to access LLM through agent's internal structure
                    if hasattr(agent, "_llm") and hasattr(agent._llm, "parameters"):
                        original_temp = agent._llm.parameters.temperature
                        agent._llm.parameters.temperature = temperature
                        logger.debug(f"Temporarily set temperature to {temperature}")
                    else:
                        logger.warning(
                            "Cannot access LLM parameters for temperature adjustment"
                        )
                except Exception as e:
                    logger.warning(f"Failed to set temperature: {e}")

            # Update agent memory with latest user message
            user_message = UserMessage(message_content)
            await agent.memory.add(user_message)

            # Configure execution with intelligent defaults
            execution_config = AgentExecutionConfig(
                max_retries_per_step=max_retries or 3,
                total_max_retries=(max_retries or 3) * 3,
                max_iterations=max_iterations or 20,
            )

            # Track execution statistics
            execution_start = asyncio.get_event_loop().time()

            # Process with agent using enhanced event handling with observe pattern
            def on_events(emitter):
                emitter.on(
                    "error",
                    lambda data, event: self._handle_agent_events(
                        data, event, session_id
                    ),
                )
                emitter.on(
                    "retry",
                    lambda data, event: self._handle_agent_events(
                        data, event, session_id
                    ),
                )
                emitter.on(
                    "update",
                    lambda data, event: self._handle_agent_events(
                        data, event, session_id
                    ),
                )
                emitter.on(
                    "start",
                    lambda data, event: self._handle_agent_events(
                        data, event, session_id
                    ),
                )
                emitter.on(
                    "success",
                    lambda data, event: self._handle_agent_events(
                        data, event, session_id
                    ),
                )
                emitter.on(
                    "finish",
                    lambda data, event: self._handle_agent_events(
                        data, event, session_id
                    ),
                )

            response = await agent.run(
                message_content,
                max_retries_per_step=execution_config.max_retries_per_step,
                total_max_retries=execution_config.total_max_retries,
                max_iterations=execution_config.max_iterations,
            ).observe(on_events)

            execution_time = asyncio.get_event_loop().time() - execution_start
            response_text = response.last_message.text

            # Update statistics
            if session_id in self._agent_stats:
                self._agent_stats[session_id].update(
                    {
                        "last_used": asyncio.get_event_loop().time(),
                        "total_executions": self._agent_stats[session_id].get(
                            "total_executions", 0
                        )
                        + 1,
                        "last_execution_time": execution_time,
                    }
                )

            # Save assistant response to database
            await self.chat_repository.add_message(
                session_id=session_id, role="assistant", content=response_text
            )

            # Restore original temperature if it was changed
            if original_temp is not None:
                try:
                    if hasattr(agent, "_llm") and hasattr(agent._llm, "parameters"):
                        agent._llm.parameters.temperature = original_temp
                        logger.debug(f"Restored original temperature: {original_temp}")
                except Exception as e:
                    logger.warning(f"Failed to restore temperature: {e}")

            total_time = asyncio.get_event_loop().time() - start_time
            logger.info(
                f"Successfully processed message for session {session_id} in {total_time:.2f}s "
                f"(execution: {execution_time:.2f}s, iterations: {getattr(response, 'iterations', 'N/A')})"
            )

            return response_text

        except FrameworkError:
            raise
        except Exception as e:
            error_msg = f"Failed to process message for session {session_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FrameworkError(error_msg)

    async def add_system_message(self, session_id: str, content: str) -> None:
        """
        Add a system message to the conversation.

        Args:
            session_id: Session identifier
            content: System message content
        """
        try:
            # Save to database
            await self.chat_repository.add_message(
                session_id=session_id, role="system", content=content
            )

            # Update agent memory if agent exists
            if session_id in self._agent_cache:
                agent = self._agent_cache[session_id]
                system_message = SystemMessage(content)
                await agent.memory.add(system_message)

            logger.info(f"Added system message to session {session_id}")

        except Exception as e:
            error_msg = (
                f"Failed to add system message to session {session_id}: {str(e)}"
            )
            logger.error(error_msg)
            raise FrameworkError(error_msg)

    async def clear_session_memory(self, session_id: str) -> None:
        """
        Clear agent memory for a session.

        Args:
            session_id: Session identifier
        """
        try:
            if session_id in self._agent_cache:
                agent = self._agent_cache[session_id]
                agent.memory.reset()
                logger.info(f"Cleared memory for session {session_id}")

        except Exception as e:
            logger.error(f"Failed to clear memory for session {session_id}: {str(e)}")

    async def refresh_agent_memory(self, session_id: str) -> None:
        """
        Refresh agent memory from database with improved error handling.

        Args:
            session_id: Session identifier
        """
        try:
            if session_id in self._agent_cache:
                agent = self._agent_cache[session_id]

                # Clear current memory
                agent.memory.reset()

                # Reload from database with intelligent memory selection
                memory = await self._create_intelligent_memory(session_id, agent.llm)

                # Update agent memory reference
                agent._memory = memory

                # Update statistics
                if session_id in self._agent_stats:
                    self._agent_stats[session_id]["memory_refreshed_at"] = (
                        asyncio.get_event_loop().time()
                    )
                    self._agent_stats[session_id]["message_count"] = len(
                        memory.messages
                    )

                logger.info(
                    f"Refreshed memory for session {session_id} with {len(memory.messages)} messages"
                )

        except Exception as e:
            logger.error(
                f"Failed to refresh memory for session {session_id}: {str(e)}",
                exc_info=True,
            )
            raise FrameworkError(f"Memory refresh failed: {str(e)}")

    def remove_agent_from_cache(self, session_id: str) -> None:
        """
        Remove agent from cache with proper cleanup.

        Args:
            session_id: Session identifier
        """
        if session_id in self._agent_cache:
            # Clean up memory if it supports it
            agent = self._agent_cache[session_id]
            try:
                if hasattr(agent.memory, "reset"):
                    agent.memory.reset()
            except Exception as e:
                logger.warning(f"Error resetting memory during cleanup: {e}")

            del self._agent_cache[session_id]
            logger.debug(f"Removed agent for session {session_id} from cache")

        if session_id in self._agent_stats:
            del self._agent_stats[session_id]
            logger.debug(f"Removed agent stats for session {session_id}")

    def get_agent_stats(self, session_id: str = None) -> dict[str, Any]:
        """
        Get agent performance statistics.

        Args:
            session_id: Optional specific session ID

        Returns:
            Agent statistics dictionary
        """
        if session_id:
            return self._agent_stats.get(session_id, {})
        return self._agent_stats.copy()

    def cleanup_inactive_agents(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up inactive agents from cache.

        Args:
            max_age_seconds: Maximum age for inactive agents

        Returns:
            Number of agents cleaned up
        """
        current_time = asyncio.get_event_loop().time()
        inactive_sessions = []

        for session_id, stats in self._agent_stats.items():
            last_used = stats.get("last_used") or stats.get("created_at", 0)
            if current_time - last_used > max_age_seconds:
                inactive_sessions.append(session_id)

        for session_id in inactive_sessions:
            self.remove_agent_from_cache(session_id)

        if inactive_sessions:
            logger.info(f"Cleaned up {len(inactive_sessions)} inactive agents")

        return len(inactive_sessions)

    async def _create_chat_model(self, session_id: str):
        """
        Create ChatModel from database configuration using proper BeeAI adapters.
        Sets appropriate environment variables based on provider type from database.

        Args:
            session_id: Session identifier for logging

        Returns:
            Configured ChatModel instance (OllamaChatModel or OpenAIChatModel)

        Raises:
            FrameworkError: If configuration is invalid or provider unsupported
        """
        try:
            # Get LLM connection from database
            repo = LLMConnectionRepository()
            connection = await repo.get_active_connection()

            if not connection:
                logger.error("No active LLM connection found in database")
                raise ValueError("No active LLM connection found in database")

            # Log connection details for debugging
            logger.info(f"Found active connection: {connection.name}")
            logger.info(f"Provider: {connection.provider.value}")
            logger.info(f"Model: {connection.model_name}")
            logger.info(f"Base URL: {connection.base_url}")

            # Only support Ollama and OpenAI
            if connection.provider not in [ProviderType.OLLAMA, ProviderType.OPENAI]:
                error_msg = f"Unsupported provider: {connection.provider}. Only 'ollama' and 'openai' are supported."
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Use full model name as-is for BeeAI adapters
            model_name = connection.model_name
            logger.info(f"Using model name: {model_name}")

            # Create appropriate model based on provider
            if connection.provider == ProviderType.OLLAMA:
                logger.info(f"Creating Ollama model with name: {model_name}")

                # Validate model name
                if not model_name or model_name.strip() == "":
                    error_msg = f"Invalid Ollama model name: '{model_name}'"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                # Set base URL if provided, normalize for Ollama
                base_url = connection.base_url or "http://localhost:11434"

                # Remove /v1 suffix if present (BeeAI will add it automatically)
                if base_url.endswith("/v1"):
                    base_url = base_url[:-3]
                    logger.info("Removed /v1 suffix from Ollama URL")

                # Ensure no trailing slash
                base_url = base_url.rstrip("/")

                logger.info(f"Using normalized Ollama base URL: {base_url}")

                # Test connection to Ollama before creating model
                await self._test_ollama_connection(base_url, model_name)

                # Set BeeAI required environment variables for Ollama
                import os

                os.environ["OLLAMA_BASE_URL"] = base_url
                os.environ["OLLAMA_CHAT_MODEL"] = model_name
                logger.info(f"Set OLLAMA_BASE_URL to: {base_url}")
                logger.info(f"Set OLLAMA_CHAT_MODEL to: {model_name}")

                # Create Ollama model with explicit base_url parameter
                model = OllamaChatModel(model_name, base_url=base_url)
                model.parameters.temperature = 0.7

                logger.info(f"Successfully created Ollama model: {model_name}")
                return model

            elif connection.provider == ProviderType.OPENAI:
                logger.info(f"Creating OpenAI model with name: {model_name}")

                # Validate model name
                if not model_name or model_name.strip() == "":
                    error_msg = f"Invalid OpenAI model name: '{model_name}'"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                # Validate API key
                if not connection.api_key or connection.api_key.strip() == "":
                    error_msg = "OpenAI provider requires an API key"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                # Set BeeAI required environment variables for OpenAI
                import os

                os.environ["OPENAI_API_KEY"] = connection.api_key
                os.environ["OPENAI_CHAT_MODEL"] = model_name
                logger.info("Set OPENAI_API_KEY environment variable")
                logger.info(f"Set OPENAI_CHAT_MODEL to: {model_name}")

                if connection.base_url:
                    os.environ["OPENAI_API_BASE"] = connection.base_url
                    logger.info(f"Set OPENAI_API_BASE to: {connection.base_url}")

                if connection.api_version:
                    os.environ["OPENAI_API_VERSION"] = connection.api_version
                    logger.info(f"Set OPENAI_API_VERSION to: {connection.api_version}")

                # Create OpenAI model
                model = OpenAIChatModel(model_name)
                model.parameters.temperature = 0.7

                logger.info(f"Successfully created OpenAI model: {model_name}")
                return model

        except Exception as e:
            error_msg = (
                f"Failed to create chat model for session {session_id}: {str(e)}"
            )
            logger.error(error_msg, exc_info=True)

            # Log connection details if available
            try:
                repo = LLMConnectionRepository()
                connection = await repo.get_active_connection()
                if connection:
                    logger.error(
                        f"Connection details - Name: {connection.name}, Provider: {connection.provider.value}, Model: {connection.model_name}, Base URL: {connection.base_url}"
                    )
            except:
                logger.error("Could not retrieve connection details for error logging")

            raise FrameworkError(error_msg)

    async def _test_ollama_connection(self, base_url: str, model_name: str) -> None:
        """
        Test connection to Ollama instance and check if model exists.

        Args:
            base_url: Ollama base URL
            model_name: Model name to check

        Raises:
            ValueError: If connection fails or model doesn't exist
        """
        try:
            logger.info(f"Testing Ollama connection to {base_url}")

            # First test basic connectivity
            async with httpx.AsyncClient(timeout=15.0) as client:
                try:
                    # Try the root endpoint first to check if Ollama is running
                    root_response = await client.get(base_url)
                    if (
                        root_response.status_code == 200
                        and "Ollama is running" in root_response.text
                    ):
                        logger.info("✅ Ollama is running and accessible")
                    else:
                        logger.warning(
                            f"Ollama root endpoint returned: {root_response.status_code}"
                        )

                    # Now test the API endpoint
                    api_response = await client.get(f"{base_url}/api/tags")

                    if api_response.status_code != 200:
                        logger.warning(
                            f"Ollama API not responding properly at {base_url}/api/tags (status: {api_response.status_code})"
                        )
                        # Don't fail immediately - the model might still work
                        logger.info("Continuing anyway - model creation may still work")
                        return

                    # Check if model exists
                    models_data = api_response.json()
                    available_models = [
                        model.get("name", "") for model in models_data.get("models", [])
                    ]

                    logger.info(f"Available Ollama models: {available_models}")

                    # Check if our model is available (exact match or partial match)
                    model_found = False
                    for available_model in available_models:
                        if available_model == model_name or available_model.startswith(
                            model_name.split(":")[0]
                        ):
                            model_found = True
                            logger.info(f"Found matching model: {available_model}")
                            break

                    if not model_found:
                        logger.warning(
                            f"Model '{model_name}' not found in Ollama. Available models: {available_models}"
                        )
                        logger.info(
                            "Attempting to use model anyway - Ollama may pull it automatically"
                        )

                except httpx.ConnectError as e:
                    logger.error(f"Cannot connect to Ollama at {base_url}: {e}")
                    raise ValueError(
                        f"Cannot connect to Ollama at {base_url}. Make sure Ollama is running and accessible from the container."
                    )
                except httpx.TimeoutException:
                    logger.error(f"Timeout connecting to Ollama at {base_url}")
                    raise ValueError(
                        f"Timeout connecting to Ollama at {base_url}. Check if the service is responsive."
                    )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error testing Ollama connection: {e}")
            # Don't fail for unexpected errors - continue with model creation
            logger.info("Continuing with model creation despite connection test error")

    async def _create_intelligent_memory(self, session_id: str, llm: Any) -> BaseMemory:
        """
        Create intelligent memory instance with conversation history and optimal memory strategy.

        Args:
            session_id: Session identifier
            llm: Language model instance for TokenMemory

        Returns:
            Memory instance with loaded history and optimal configuration
        """
        try:
            # Choose memory type based on configuration and model capabilities
            if self._memory_type == "token" and hasattr(llm, "parameters"):
                # Use TokenMemory for production workloads with token management
                memory = TokenMemory(
                    llm=llm,
                    max_tokens=self._max_memory_tokens,
                    capacity_threshold=0.8,  # Trigger cleanup at 80% capacity
                    sync_threshold=0.3,  # Sync token counts when needed
                )
                logger.debug(
                    f"Created TokenMemory with max_tokens={self._max_memory_tokens}"
                )
            else:
                # Use UnconstrainedMemory for development and simple cases
                memory = UnconstrainedMemory()
                logger.debug("Created UnconstrainedMemory")

            # Load conversation history from database
            messages = await self.chat_repository.get_messages(session_id)

            # Convert database messages to BeeAI messages with proper ordering
            beeai_messages = []
            for db_message in messages:
                if db_message.role == "system":
                    message = SystemMessage(db_message.content)
                elif db_message.role == "user":
                    message = UserMessage(db_message.content)
                elif db_message.role == "assistant":
                    message = AssistantMessage(db_message.content)
                else:
                    logger.warning(f"Unknown message role: {db_message.role}")
                    continue

                beeai_messages.append(message)

            # Add messages to memory efficiently
            if beeai_messages:
                await memory.add_many(beeai_messages)

            # Sync token counts if using TokenMemory
            if isinstance(memory, TokenMemory):
                await memory.sync()
                logger.debug(f"TokenMemory synced - tokens used: {memory.tokens_used}")

            logger.info(
                f"Loaded {len(messages)} messages into {type(memory).__name__} for session {session_id}"
            )

            return memory

        except Exception as e:
            logger.error(f"Failed to create memory for session {session_id}: {e}")
            # Fallback to simple UnconstrainedMemory
            return UnconstrainedMemory()

    def _get_dynamic_system_prompt(self, user_message: str) -> str:
        """
        Generate dynamic system prompt based on user message context and intent.

        Args:
            user_message: User's message content

        Returns:
            Context-aware system prompt string
        """
        # Enhanced keyword detection for different contexts
        robot_keywords = [
            "move",
            "go",
            "pick",
            "place",
            "open",
            "close",
            "home",
            "gripper",
            "led",
            "robot",
            "position",
            "reset",
            "cycle",
            "arm",
            "joint",
            "coordinate",
            "stop",
        ]

        technical_keywords = [
            "debug",
            "error",
            "status",
            "connection",
            "network",
            "ip",
            "port",
            "sensor",
            "actuator",
            "calibrate",
            "initialize",
        ]

        safety_keywords = [
            "emergency",
            "stop",
            "danger",
            "safe",
            "collision",
            "limit",
            "warning",
        ]

        user_lower = user_message.lower()

        # Check for safety-related content first
        if any(keyword in user_lower for keyword in safety_keywords):
            return (
                "You are RoboPilot, a safety-focused robot assistant. Safety is your top priority. "
                "When dealing with safety concerns, always err on the side of caution. "
                "Use robot tools carefully and explain safety considerations clearly."
            )

        # Check for technical/diagnostic content
        elif any(keyword in user_lower for keyword in technical_keywords):
            return (
                "You are RoboPilot, a technical robot assistant with diagnostic capabilities. "
                "Provide detailed technical information and use appropriate robot tools for diagnostics. "
                "Explain technical concepts clearly and offer troubleshooting guidance."
            )

        # Check for robot control content
        elif any(keyword in user_lower for keyword in robot_keywords):
            return (
                "You are RoboPilot, a robot control assistant with access to physical manipulation tools. "
                "Execute robot actions safely and efficiently. Always confirm actions before execution "
                "and provide clear status updates. Use the available robot tools as needed."
            )

        # Default conversational mode
        else:
            return (
                "You are RoboPilot, an intelligent and helpful AI assistant. "
                "Engage naturally in conversation and provide informative, accurate responses. "
                "You have access to robot control tools if needed, but use them only when explicitly requested."
            )

    def _handle_agent_events(
        self, data: Any, event: EventMeta, session_id: str = None
    ) -> None:
        """
        Enhanced agent execution event handler with comprehensive logging and monitoring.

        Args:
            data: Event data
            event: Event metadata
            session_id: Optional session identifier for context
        """
        session_prefix = f"[{session_id}] " if session_id else ""

        if event.name == "error":
            error_info = (
                FrameworkError.ensure(data.error) if hasattr(data, "error") else data
            )
            logger.error(
                f"{session_prefix}Agent error: {error_info.explain() if hasattr(error_info, 'explain') else error_info}"
            )

        elif event.name == "retry":
            retry_info = getattr(data, "retry_count", "unknown")
            logger.warning(
                f"{session_prefix}Agent retrying action (attempt: {retry_info})"
            )

        elif event.name == "update":
            if hasattr(data, "update"):
                key = data.update.key
                value = getattr(
                    data.update, "parsed_value", getattr(data.update, "value", "N/A")
                )

                # Log different update types with appropriate levels
                if key == "tool_name":
                    logger.info(f"{session_prefix}🔧 Calling tool: {value}")
                elif key == "tool_input":
                    logger.info(f"{session_prefix}📝 Tool input: {value}")
                elif key == "tool_output" or key == "observation":
                    logger.info(f"{session_prefix}👁️ Tool result: {value}")
                elif key == "thought":
                    logger.debug(f"{session_prefix}💭 Agent thinking: {value}")
                else:
                    logger.debug(f"{session_prefix}Agent update ({key}): {value}")

        elif event.name == "start":
            iteration = getattr(data, "iteration", "unknown")
            logger.info(f"{session_prefix}🚀 Agent starting iteration {iteration}")

        elif event.name == "success":
            logger.info(f"{session_prefix}✅ Agent completed successfully")

        elif event.name == "finish":
            result_info = getattr(data, "result", "N/A")
            logger.info(f"{session_prefix}🎯 Agent finished with result: {result_info}")

        else:
            logger.debug(f"{session_prefix}Agent event '{event.name}': {data}")
