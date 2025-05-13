"""
PraisonAI agents integration with LM Studio.

This module provides functionality to create and manage PraisonAI agents
that can interact with LM Studio models.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from praisonaiagents import Agent, PraisonAIAgents, Task

from ..lmstudio_tools import PREDEFINED_TOOLS


def format_base_url(base_url: Optional[str]) -> Optional[str]:
    """
    Format a base URL to ensure it has the correct protocol and /v1 path.

    Args:
        base_url (Optional[str]): The base URL to format

    Returns:
        Optional[str]: The formatted base URL or None if input was None
    """
    if not base_url:
        return None

    # Add http:// if no protocol is specified
    if not base_url.startswith(("http://", "https://")):
        base_url = f"http://{base_url}"

    # Add /v1 if it's missing
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1" if not base_url.endswith("/") else f"{base_url}v1"

    return base_url


# Setup logging
logger = logging.getLogger(__name__)


class LLMBackedAgent(Agent):
    """An Agent class that uses a configurable LLM backend"""

    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        llm_config: Dict[str, Any] = None,
        tools: List[Any] = None,
        self_reflect: bool = True,
        max_reflect: int = 3,
    ):
        """
        Initialize an Agent with a configurable LLM backend.

        Args:
            name (str): Name of the agent
            role (str): Role of the agent
            goal (str): Goal the agent aims to achieve
            backstory (str): Background story of the agent
            llm_config (Dict[str, Any], optional): LLM configuration
            tools (List[Any]): Tools available to the agent
            self_reflect (bool): Enable self-reflection capability
            max_reflect (int): Maximum number of self-reflection iterations
        """
        # If no LLM config provided, try to get one
        if llm_config is None:
            try:
                import asyncio

                llm_config = asyncio.run(get_llm_config())
            except Exception as e:
                logger.warning(f"Error getting LLM config for agent: {str(e)}")
                # Use a default configuration
                llm_config = {
                    "model": os.environ.get("OPENAI_MODEL_NAME", "gpt-4o"),
                    "api_key": None,
                    "base_url": format_base_url(
                        os.environ.get("LMSTUDIO_HOST", "host.docker.internal:1234")
                    ),
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "response_format": {"type": "text"},
                }

        # Initialize the agent with the provided configuration
        super().__init__(
            name=name,
            instructions=f"""# Role: {role}
# Goal: {goal}
# Backstory: {backstory}""",
            llm=llm_config,
            tools=tools,
            verbose=False,
        )
        logger.info(f"Created LLM backed agent: {name}")


# Keep for backward compatibility
class LMStudioBackedAgent(LLMBackedAgent):
    """An Agent class that uses LM Studio as the backend"""

    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        tools: List[Any] = None,
        self_reflect: bool = True,
        max_reflect: int = 3,
    ):
        """
        Initialize an Agent with LM Studio as the backend.

        Args:
            name (str): Name of the agent
            role (str): Role of the agent
            goal (str): Goal the agent aims to achieve
            backstory (str): Background story of the agent
            tools (List[Any]): Tools available to the agent
            self_reflect (bool): Enable self-reflection capability
            max_reflect (int): Maximum number of self-reflection iterations
        """
        try:
            # Get the config asynchronously using a synchronous wrapper
            import asyncio

            llm_config = asyncio.run(get_llm_config())
        except Exception as e:
            logger.warning(f"Could not get LLM config from connection: {str(e)}")
            # Fallback to environment variables
            llm_config = {
                "model": os.environ.get("OPENAI_MODEL_NAME", "gpt-4o"),
                "api_key": None,  # No API key needed for LM Studio
                "base_url": os.environ.get(
                    "LMSTUDIO_HOST",
                    os.environ.get("OPENAI_API_BASE", "http://localhost:1234/v1"),
                ),
                "temperature": 0.7,
                "max_tokens": 1000,
                "response_format": {"type": "text"},
            }

            # Format the base URL properly
            llm_config["base_url"] = format_base_url(llm_config["base_url"])

        # Initialize using parent class
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            backstory=backstory,
            llm_config=llm_config,
            tools=tools,
            self_reflect=self_reflect,
            max_reflect=max_reflect,
        )


async def get_llm_config():
    """
    Get the LLM configuration from the active connection in the database.
    If no active connection exists, use default LM Studio config.

    Returns:
        Dict[str, Any]: LLM configuration dictionary
    """
    try:
        # Import here to avoid circular imports
        from ...repository.llm_connection_repository import LLMConnectionRepository

        # Get repository
        repo = LLMConnectionRepository()

        # # Get active connection
        connection = await repo.get_active_connection()

        # # If no active connection, try to activate default connection
        if not connection:
            connection = await repo.activate_default_connection()

        # If we have a valid connection, convert it to LLM config
        if connection:
            llm_config = repo.connection_to_llm_config(connection)
            config = llm_config.model_dump()

            # Special handling for LMStudio provider - it doesn't need a real API key
            if connection.provider.lower() in ["lmstudio", "local"]:
                config["api_key"] = None
            elif connection.provider.lower() == "openai" and (
                not config["api_key"] or config["api_key"] == "not-needed"
            ):
                # For OpenAI, we need a valid API key, try to get from environment
                config["api_key"] = os.environ.get("OPENAI_API_KEY")

            # Format the base URL properly
            config["base_url"] = format_base_url(config["base_url"])

            return config
        else:
            # Fall back to default LM Studio config
            base_url = os.environ.get(
                "LMSTUDIO_HOST",
                os.environ.get("OPENAI_API_BASE", "http://localhost:1234/v1"),
            )
            # Format the base URL properly
            base_url = format_base_url(base_url)

            return {
                "model": os.environ.get("OPENAI_MODEL_NAME", "gpt-4o"),
                "api_key": None,  # None instead of empty string for LM Studio
                "base_url": base_url,
                "temperature": 0.7,
                "max_tokens": 1000,
                "response_format": {"type": "text"},
            }
    except Exception as e:
        logger.error(f"Error getting LLM config: {str(e)}")
        # Fall back to default LM Studio config
        base_url = os.environ.get(
            "LMSTUDIO_HOST",
            os.environ.get("OPENAI_API_BASE", "http://localhost:1234/v1"),
        )
        # Format the base URL properly
        base_url = format_base_url(base_url)

        return {
            "model": os.environ.get("OPENAI_MODEL_NAME", "gpt-4o"),
            "api_key": None,  # None instead of empty string for LM Studio
            "base_url": base_url,
            "temperature": 0.7,
            "max_tokens": 1000,
            "response_format": {"type": "text"},
        }


async def create_master_agent(llm_config=None) -> Agent:
    """
    Create a master agent for basic communication.

    Args:
        llm_config: Optional LLM configuration to use

    Returns:
        Agent: The configured master agent
    """
    # If no LLM config provided, try to get one
    if llm_config is None:
        llm_config = await get_llm_config()

    return LLMBackedAgent(
        name="MasterAgent",
        role="Communication Coordinator",
        goal="Handle user interactions and coordinate with other agents",
        backstory="""You are the main communication hub for the AI system.
        Your primary responsibility is to interpret user requests, maintain
        conversation context, and delegate specialized tasks to other agents
        when needed. When chat history is available (in the state with key 'chat_history'),
        use it to maintain context, reference previous interactions appropriately,
        and provide coherent responses that build on the existing conversation.
        Avoid repeating information the user already knows from previous interactions.""",
        llm_config=llm_config,
        tools=None,  # No tools for the master agent
        self_reflect=True,
        max_reflect=2,
    )


async def create_tools_agent(llm_config=None) -> Agent:
    """
    Create a tools agent for executing specialized operations.

    Args:
        llm_config: Optional LLM configuration to use

    Returns:
        Agent: The configured tools agent
    """
    # If no LLM config provided, try to get one
    if llm_config is None:
        llm_config = await get_llm_config()

    return LLMBackedAgent(
        name="ToolsAgent",
        role="Tool Specialist",
        goal="Execute specialized tools and operations based on requests",
        backstory="""You are an expert in using various tools to accomplish tasks.
        When the master agent delegates a task to you, you select and use the
        appropriate tool to complete it efficiently. Consider any chat history context
        provided in the state (key: 'chat_history') to avoid repeating tool operations
        that have already been performed earlier in the conversation unless explicitly
        requested by the user.
        
        When available, use the function call history provided in the state 
        (key: 'function_call_history') to understand what tools have been used previously,
        their arguments, and results. This will help you make more informed decisions
        about which tools to use and how to use them in the current context.""",
        llm_config=llm_config,
        tools=PREDEFINED_TOOLS,
        self_reflect=True,
        max_reflect=2,
    )


def create_master_agent_sync(llm_config=None) -> Agent:
    """
    Create a master agent for basic communication (synchronous version).

    Args:
        llm_config: Optional LLM configuration to use

    Returns:
        Agent: The configured master agent
    """
    # For backward compatibility
    return LLMBackedAgent(
        name="MasterAgent",
        role="Communication Coordinator",
        goal="Handle user interactions and coordinate with other agents",
        backstory="""You are the main communication hub for the AI system.
        Your primary responsibility is to interpret user requests, maintain
        conversation context, and delegate specialized tasks to other agents
        when needed. When chat history is available (in the state with key 'chat_history'),
        use it to maintain context, reference previous interactions appropriately,
        and provide coherent responses that build on the existing conversation.
        Avoid repeating information the user already knows from previous interactions.""",
        llm_config=llm_config,
        tools=None,  # No tools for the master agent
        self_reflect=True,
        max_reflect=2,
    )


def create_tools_agent_sync(llm_config=None) -> Agent:
    """
    Create a tools agent for executing specialized operations (synchronous version).

    Args:
        llm_config: Optional LLM configuration to use

    Returns:
        Agent: The configured tools agent
    """
    # For backward compatibility
    return LLMBackedAgent(
        name="ToolsAgent",
        role="Tool Specialist",
        goal="Execute specialized tools and operations based on requests",
        backstory="""You are an expert in using various tools to accomplish tasks.
        When the master agent delegates a task to you, you select and use the 
        appropriate tool to complete it efficiently. Consider any chat history context
        provided in the state (key: 'chat_history') to avoid repeating tool operations
        that have already been performed earlier in the conversation unless explicitly
        requested by the user.

        When available, use the function call history provided in the state 
        (key: 'function_call_history') to understand what tools have been used previously,
        their arguments, and results. This will help you make more informed decisions
        about which tools to use and how to use them in the current context.""",
        llm_config=llm_config,
        tools=PREDEFINED_TOOLS,
        self_reflect=True,
        max_reflect=2,
    )


async def setup_multi_agents(tool_callback=None, llm_config=None) -> PraisonAIAgents:
    """
    Set up the multi-agent system with PraisonAI agents.

    Args:
        tool_callback: Optional callback for tool usage tracking
        llm_config: Optional LLM configuration to use

    Returns:
        PraisonAIAgents: The configured multi-agent system
    """
    # Create agents
    master_agent = await create_master_agent(llm_config)
    tools_agent = await create_tools_agent(llm_config)

    # Create agents system
    agents = PraisonAIAgents(agents=[master_agent, tools_agent])

    # Configure agents
    agents.process = "hierarchical"
    agents.verbose = True

    # Define tasks
    master_task = Task(
        name="handle_user_request",
        description="""Process the user's request considering any chat history,
        and determine if tools are needed. If chat history is available in the
        state (key: 'chat_history'), use it to maintain context, resolve pronouns
        and references to previous messages, and ensure continuity of conversation.
        Pay special attention to follow-up questions that only make sense in the
        context of previous exchanges.""",
        agent=master_agent,
        expected_output="Processed response or delegation to tools agent",
    )

    tools_task = Task(
        name="execute_tools",
        description="""Execute specialized tools based on the request and conversation context.
        If function call history is available in the state (key: 'function_call_history'),
        use it to see what tools have been used previously, how they were used, and their results.
        This helps you avoid redundant operations and build on previous tool executions.""",
        agent=tools_agent,
        expected_output="Results from tool execution with context-aware interpretation",
        context=[master_task],
    )

    # Add tasks
    agents.tasks = [master_task, tools_task]

    # Attach tool callback if provided
    if tool_callback:
        agents.tool_call_callback = tool_callback

    return agents


def setup_multi_agents_sync(tool_callback=None, llm_config=None) -> PraisonAIAgents:
    """
    Set up the multi-agent system with PraisonAI agents (synchronous version).

    Args:
        tool_callback: Optional callback for tool usage tracking
        llm_config: Optional LLM configuration to use

    Returns:
        PraisonAIAgents: The configured multi-agent system
    """
    # Create agents
    master_agent = create_master_agent_sync(llm_config)
    tools_agent = create_tools_agent_sync(llm_config)

    # Create agents system
    agents = PraisonAIAgents(agents=[master_agent, tools_agent])

    # Configure agents
    agents.process = "hierarchical"
    agents.verbose = True

    # Define tasks
    master_task = Task(
        name="handle_user_request",
        description="""Process the user's request considering any chat history,
        and determine if tools are needed. If chat history is available in the
        state (key: 'chat_history'), use it to maintain context, resolve pronouns
        and references to previous messages, and ensure continuity of conversation.
        Pay special attention to follow-up questions that only make sense in the
        context of previous exchanges.""",
        agent=master_agent,
        expected_output="Processed response or delegation to tools agent",
    )

    tools_task = Task(
        name="execute_tools",
        description="""Execute specialized tools based on the request and conversation context.
        If function call history is available in the state (key: 'function_call_history'),
        use it to see what tools have been used previously, how they were used, and their results.
        This helps you avoid redundant operations and build on previous tool executions.""",
        agent=tools_agent,
        expected_output="Results from tool execution with context-aware interpretation",
        context=[master_task],
    )

    # Add tasks
    agents.tasks = [master_task, tools_task]

    # Attach tool callback if provided
    if tool_callback:
        agents.tool_call_callback = tool_callback

    return agents


def process_with_multi_agents(
    user_input: str,
    session_id: str = None,
    chat_repository=None,
    llm_config=None,
) -> Dict[str, Any]:
    """
    Process user input with the multi-agent system.

    Args:
        user_input (str): User's input message
        session_id (str, optional): Chat session ID for history tracking
        chat_repository: Repository for chat session operations
        llm_config (dict, optional): LLM configuration to use

    Returns:
        Dict[str, Any]: Results from the multi-agent processing including messages to save
    """
    # If no llm_config was provided, use the sync version to get a default config
    if llm_config is None:
        try:
            # Use the synchronous approach to get config
            import asyncio

            llm_config = asyncio.run(get_llm_config())
        except Exception as e:
            logger.warning(f"Failed to get default LLM config: {str(e)}")
            # We'll let the agents use their default config

    # For tracking tool calls
    tool_calls_recorder = []

    # Define a tool call callback function
    def on_tool_call(function_name, arguments, result):
        tool_calls_recorder.append(
            {"function_name": function_name, "arguments": arguments, "result": result}
        )
        logger.info(f"Tool call recorded: {function_name}")

    # Setup agents with the callback
    agents = setup_multi_agents_sync(on_tool_call, llm_config)

    # Set user input as state for the agents to access
    agents.set_state("user_input", user_input)

    # Set session ID in state if available
    if session_id:
        agents.set_state("session_id", session_id)

    # Add chat history if available - for sync version, we can't use async repository methods
    # This is mainly here for API consistency
    if session_id and chat_repository:
        # Note: In sync version, we can't actually use the async repo methods
        # This is just API consistency, but in real usage should use async variant
        agents.set_state("session_id", session_id)

    # Start the multi-agent system
    result = agents.start()

    # Extract response
    response_text = result.get("task_results", {}).get(
        "handle_user_request", "No response generated"
    )
    tool_results = result.get("task_results", {}).get("execute_tools", None)

    # If tool results but no response, format a response about the tool execution
    if not response_text and tool_results:
        response_text = f"Tool execution results: {str(tool_results)}"

    # Ensure tool_calls_recorder is accessible in the return value
    return_data = {
        "response": response_text,
        "tool_results": tool_results,
        "tool_calls": tool_calls_recorder,
        "status": result.get("task_status", {}),
        "messages_to_save": [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response_text},
        ],
    }

    return return_data


async def process_with_multi_agents_async(
    user_input: str,
    session_id: str = None,
    chat_repository=None,
    llm_config=None,
) -> Dict[str, Any]:
    """
    Process user input with the multi-agent system asynchronously.

    Args:
        user_input (str): User's input message
        session_id (str, optional): Chat session ID for history tracking
        chat_repository: Repository for chat session operations
        llm_config (dict, optional): LLM configuration to use

    Returns:
        Dict[str, Any]: Results from the multi-agent processing including messages to save
    """
    # If no llm_config was provided, get one
    if llm_config is None:
        try:
            llm_config = await get_llm_config()
        except Exception as e:
            logger.warning(f"Failed to get default LLM config: {str(e)}")
            # We'll let the agents use their default config

    # For tracking tool calls
    tool_calls_recorder = []

    # Define a tool call callback function
    async def on_tool_call(function_name, arguments, result):
        tool_calls_recorder.append(
            {"function_name": function_name, "arguments": arguments, "result": result}
        )
        logger.info(f"Tool call recorded: {function_name}")

    # Setup agents with the callback
    agents = await setup_multi_agents(on_tool_call, llm_config)

    # Set user input as state for the agents to access
    agents.set_state("user_input", user_input)

    # Set session ID in state if available
    if session_id:
        agents.set_state("session_id", session_id)

    # Add chat history if available
    if session_id and chat_repository:
        try:
            # Get all messages for this session
            messages = await chat_repository.get_messages(session_id)

            # Format messages for state
            chat_history = []
            for msg in messages:
                chat_history.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat()
                        if msg.created_at
                        else None,
                    }
                )

            # Add to state
            agents.set_state("chat_history", chat_history)
        except Exception as e:
            logger.error(f"Failed to add chat history to state: {str(e)}")

    # Start the multi-agent system
    result = agents.start()

    # Extract response
    response_text = result.get("task_results", {}).get(
        "handle_user_request", "No response generated"
    )
    tool_results = result.get("task_results", {}).get("execute_tools", None)

    # If tool results but no response, format a response about the tool execution
    if not response_text and tool_results:
        response_text = f"Tool execution results: {str(tool_results)}"

    # Ensure tool_calls_recorder is accessible in the return value
    return_data = {
        "response": response_text,
        "tool_results": tool_results,
        "tool_calls": tool_calls_recorder,
        "status": result.get("task_status", {}),
        "messages_to_save": [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response_text},
        ],
    }

    return return_data
