"""
LMStudio client utility for interacting with LM Studio API.
"""

import asyncio
from datetime import datetime
import inspect
import json
import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import lmstudio as lms
from lmstudio._sdk_models import ModelInstanceInfo
from pydantic import BaseModel, Field

# Import pydantic models and repository
from app.repository.chat_session_repository import ChatSessionRepository


class ChatMessage(BaseModel):
    """Model for a chat message."""

    role: str
    content: str
    created_at: datetime


class FunctionCallInfo(BaseModel):
    """Model for function call information."""

    function_call: bool = False
    function_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ToolResponseSchema(BaseModel):
    """Schema for tool calling structured response."""

    message: str
    function_call: bool = False
    function_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None


class ChatSession(BaseModel):
    """Model for a chat session."""

    id: str
    name: Optional[str] = None
    messages: List[ChatMessage] = []
    created_at: str = None
    updated_at: str = None


logger = logging.getLogger(__name__)


class LMStudioClient:
    """Client for interacting with LM Studio API."""

    # Class variable to track if client has been initialized
    _instance_created = False

    def __init__(self, host: str = "localhost:1234"):
        """Initialize the LM Studio client.

        Args:
            host: The host:port where LM Studio server is running
        """
        # Store the host for reference
        self.host = host
        self.model = None

        # To store the current message ID for function call logging
        self.current_message_id = None
        self.current_session_id = None

        # Initialize repository
        self.chat_repository = ChatSessionRepository()

        # Reset the module completely if this is the first instance
        if not LMStudioClient._instance_created:
            # Try to reset the module first
            LMStudioClient.reset_module()

        # Try to configure the client
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Try to configure the client
                logger.info(
                    f"Configuring LM Studio client with host: {host} (attempt {attempt + 1}/{max_retries})"
                )
                lms.configure_default_client(host)
                logger.info(
                    f"Successfully configured LM Studio client with host: {host}"
                )
                break
            except RuntimeError as e:
                # If client already exists and this is not our last attempt
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Could not set LM Studio client host: {str(e)}, trying to reset..."
                    )
                    # Try a more aggressive reset
                    try:
                        if hasattr(lms, "_default_client"):
                            lms._default_client = None
                    except Exception:
                        pass
                else:
                    # Last attempt failed, log warning and continue with existing client
                    try:
                        existing_host = lms.get_default_client().host
                        logger.warning(
                            f"Could not set LM Studio client host to {host}, using existing host: {existing_host}"
                        )
                    except Exception:
                        logger.warning(
                            f"Could not set LM Studio client host to {host}, using existing client"
                        )

        # Mark that we've created an instance
        LMStudioClient._instance_created = True
        self._initialize_model()

    @staticmethod
    def reset_module():
        """Reset the LM Studio module internal state."""
        try:
            # This is a hacky way to reset the module state - it's not ideal but might help
            import sys

            if "lmstudio" in sys.modules:
                # Remove the module from sys.modules to force a reload
                del sys.modules["lmstudio"]
                # Re-import the module
                import lmstudio as new_lms

                # Update our local reference
                global lms
                lms = new_lms
                logger.info("Successfully reset LM Studio module.")
                return True
        except Exception as e:
            logger.error(f"Failed to reset LM Studio module: {str(e)}")
        return False

    def _initialize_model(self):
        """Initialize the LM Studio model."""
        try:
            # Get current client info for logging
            try:
                current_host = lms.get_default_client().api_host
                logger.info(f"Initializing LM Studio model with host: {current_host}")
            except Exception:
                logger.info(
                    "Initializing LM Studio model (host information not available)"
                )

            # Create the model
            self.model = lms.llm()
            logger.info("LM Studio model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LM Studio model: {str(e)}")
            raise RuntimeError(f"Failed to initialize LM Studio model: {str(e)}")

    def get_available_models(self) -> List[ModelInstanceInfo]:
        """Get a list of available models from LM Studio.

        Returns:
            List of model names
        """
        try:
            # Use the list_loaded_models function to get models loaded in memory
            models = lms.list_loaded_models()
            return [model.get_info() for model in models]

        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
            raise RuntimeError(f"Failed to get available models: {str(e)}")

    def generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        stream: bool = False,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Generate a response from the LM Studio model.

        Args:
            prompt: The prompt text to send to the model
            temperature: The temperature setting for generation (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response

        Returns:
            Generated text response or a generator if streaming
        """
        try:
            # Create a chat with just the user prompt
            chat = lms.Chat()
            chat.add_user_message(prompt)

            # Generate response
            config = {"temperature": temperature, "maxTokens": max_tokens}

            if stream:
                # Return a generator for streaming response
                return self._stream_response(chat, config)
            else:
                # Return complete response
                result = self.model.respond(chat, config=config)
                return result.content

        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            raise RuntimeError(f"Failed to generate response: {str(e)}")

    async def _stream_response(self, chat, config):
        """Stream response from the model.

        Args:
            chat: The chat object containing the conversation
            config: Configuration parameters for generation

        Returns:
            Async generator yielding response fragments
        """
        try:
            for fragment in self.model.respond_stream(chat, config=config):
                yield fragment.content
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            raise RuntimeError(f"Streaming error: {str(e)}")

    def chat_completion(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 512,
        stream: bool = False,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Generate a chat completion with multiple messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: The temperature setting for generation
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response

        Returns:
            Generated text response or a generator if streaming
        """
        try:
            # Create a chat with the provided messages
            chat = lms.Chat()

            # Add messages to the chat
            for message in messages:
                role = message.role
                content = message.content

                if role == "system":
                    # If this is the first message and it's a system message, set it as the system message
                    if not chat._history:
                        chat = lms.Chat(content)
                    else:
                        # Otherwise, add it as a regular message
                        chat.add_system_prompt(content)
                elif role == "user":
                    chat.add_user_message(
                        content
                    )  # Changed from append to add_user_message
                elif role == "assistant":
                    chat.add_assistant_response(content)

            # Generate response
            config = {"temperature": temperature, "maxTokens": max_tokens}

            if stream:
                # Return a generator for streaming response
                return self._stream_response(chat, config)
            else:
                # Return complete response
                result = self.model.respond(chat, config=config)
                return result.content

        except Exception as e:
            logger.error(f"Failed to generate chat completion: {str(e)}")
            raise RuntimeError(f"Failed to generate chat completion: {str(e)}")

    async def process_with_tool(
        self,
        prompt: str,
        tools: List[Any],
        session_id: Optional[str] = None,
        on_message=None,
        on_prediction_fragment=None,
    ):
        """Process a prompt with tools.

        Args:
            prompt: The prompt to process
            tools: List of tool functions to make available
            session_id: Optional session ID for logging function calls
            on_message: Optional callback for handling messages (e.g. chat.append)
            on_prediction_fragment: Optional callback for handling prediction fragments

        Returns:
            The generated response along with function call information
        """
        try:
            # Store session ID for function call logging
            self.current_session_id = session_id

            # Create a message ID for logging function calls
            self.current_message_id = str(uuid.uuid4())

            # If session ID is provided, add the user prompt to session
            if session_id:
                await self.chat_repository.add_message(
                    session_id=session_id,
                    role="user",
                    content=prompt,
                    # Use current_message_id for tracking
                    message_id=self.current_message_id,
                )

            # Check if any tools should be used for this prompt
            tool_info = await self.check_tool_availability(prompt, tools)
            logger.info(
                f"Tool availability check: {tool_info.function_call}, tool: {tool_info.function_name}"
            )

            # Log the tool availability check
            if session_id:
                tool_check_message = f"Tool check: {tool_info.description}"
                await self.chat_repository.add_message(
                    session_id=session_id, role="system", content=tool_check_message
                )

            # Create a chat with the user prompt
            chat = lms.Chat()
            chat.add_user_message(prompt)

            # Extract tool information for each function
            tool_info = []
            for tool in tools:
                tool_name = tool.__name__
                tool_doc = inspect.getdoc(tool) or "No description available"
                tool_signature = inspect.signature(tool)
                tool_params = {
                    param.name: {
                        "type": str(param.annotation)
                        if param.annotation != inspect.Parameter.empty
                        else "any",
                        "description": "Parameter description not available",
                    }
                    for param in tool_signature.parameters.values()
                }

                tool_info.append(
                    {
                        "name": tool_name,
                        "description": tool_doc,
                        "parameters": tool_params,
                    }
                )

            # Function to log tool calls
            async def log_tool_call(name, args, result):
                if self.current_session_id and self.current_message_id:
                    await self.chat_repository.log_function_call(
                        session_id=self.current_session_id,
                        message_id=self.current_message_id,
                        function_name=name,
                        arguments=args,
                        result=result,
                    )

            # Create a wrapper for each tool to log function calls
            wrapped_tools = []
            for tool in tools:

                async def wrapped_tool(*args, **kwargs):
                    try:
                        # Get original function
                        original_func = tool
                        func_name = original_func.__name__

                        # Call the original function
                        result = original_func(*args, **kwargs)

                        # Log the function call
                        await log_tool_call(func_name, kwargs, result)

                        return result
                    except Exception as e:
                        # Log the error
                        error_result = f"Error: {str(e)}"
                        await log_tool_call(func_name, kwargs, error_result)
                        return error_result

                # Update wrapper metadata
                wrapped_tool.__name__ = tool.__name__
                wrapped_tool.__doc__ = tool.__doc__
                wrapped_tools.append(wrapped_tool)

            # Define the response schema for structured output
            result = await asyncio.to_thread(
                self.model.act,
                chat,
                tools,
                on_message=on_message,
                on_prediction_fragment=on_prediction_fragment,
            )

            # If session ID provided, save the assistant's response
            if session_id:
                await self.chat_repository.add_message(
                    session_id=session_id, role="assistant", content=result.content
                )

            return result.content
        except Exception as e:
            logger.error(f"Failed to process with tools: {str(e)}")
            raise RuntimeError(f"Failed to process with tools: {str(e)}")

    async def process_with_tool_streaming(
        self,
        prompt: str,
        tools: List[Any],
        session_id: Optional[str] = None,
    ):
        """Process a prompt with tools and stream the results.

        Args:
            prompt: The prompt to process
            tools: List of tool functions to make available
            session_id: Optional session ID for logging function calls

        Returns:
            An async generator yielding response fragments
        """
        try:
            # Store session ID for function call logging
            self.current_session_id = session_id

            # Create a message ID for logging function calls
            self.current_message_id = str(uuid.uuid4())

            # If session ID is provided, add the user prompt to session
            if session_id:
                await self.chat_repository.add_message(
                    session_id=session_id,
                    role="user",
                    content=prompt,
                    # Use current_message_id for tracking
                    message_id=self.current_message_id,
                )

            # Check if any tools should be used for this prompt
            tool_info = await self.check_tool_availability(prompt, tools)
            logger.info(
                f"Tool availability (streaming): {tool_info.function_call}, tool: {tool_info.function_name}"
            )

            # Log the tool availability check
            if session_id:
                tool_check_message = f"Tool check: {tool_info.description}"
                await self.chat_repository.add_message(
                    session_id=session_id, role="system", content=tool_check_message
                )

            # Create a chat with the user prompt
            chat = lms.Chat()
            chat.add_user_message(prompt)

            # Function to log tool calls
            async def log_tool_call(name, args, result):
                if self.current_session_id and self.current_message_id:
                    await self.chat_repository.log_function_call(
                        session_id=self.current_session_id,
                        message_id=self.current_message_id,
                        function_name=name,
                        arguments=args,
                        result=result,
                    )

            # Create a wrapper for each tool to log function calls
            wrapped_tools = []
            for tool in tools:

                async def wrapped_tool(*args, **kwargs):
                    try:
                        # Get original function
                        original_func = tool
                        func_name = original_func.__name__

                        # Call the original function
                        result = original_func(*args, **kwargs)

                        # Log the function call
                        await log_tool_call(func_name, kwargs, result)

                        return result
                    except Exception as e:
                        # Log the error
                        error_result = f"Error: {str(e)}"
                        await log_tool_call(func_name, kwargs, error_result)
                        return error_result

                # Update wrapper metadata
                wrapped_tool.__name__ = tool.__name__
                wrapped_tool.__doc__ = tool.__doc__
                wrapped_tools.append(wrapped_tool)

            # We'll use this queue to communicate between the callback and our generator
            queue = asyncio.Queue()
            done = asyncio.Event()

            # Total response for saving to DB at the end
            complete_response = ""

            def fragment_callback(fragment, _=0):
                # Add the fragment to the queue for processing
                asyncio.run_coroutine_threadsafe(
                    queue.put(fragment.content), asyncio.get_event_loop()
                )

            # This will run in a separate thread
            async def run_act():
                try:
                    await asyncio.to_thread(
                        self.model.act,
                        chat,
                        wrapped_tools,
                        on_prediction_fragment=fragment_callback,
                    )
                finally:
                    # Signal that we're done
                    done.set()

            # Start the act process in the background
            task = asyncio.create_task(run_act())

            # Yield fragments as they become available
            try:
                while not done.is_set() or not queue.empty():
                    try:
                        # Get the next fragment with a timeout
                        fragment = await asyncio.wait_for(queue.get(), 0.1)
                        complete_response += fragment
                        yield fragment
                        queue.task_done()
                    except asyncio.TimeoutError:
                        # No fragment available yet, continue waiting if not done
                        if not done.is_set():
                            continue
                        break
            finally:
                # Make sure we clean up the task
                if not task.done():
                    task.cancel()

                # Save the complete response if session ID provided
                if session_id:
                    await self.chat_repository.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=complete_response,
                    )

        except Exception as e:
            logger.error(f"Failed to process with tools streaming: {str(e)}")
            raise RuntimeError(f"Failed to process with tools streaming: {str(e)}")

    def process_with_image(self, prompt: str, image_path: str):
        """Process a prompt with an image.

        Args:
            prompt: The text prompt to process
            image_path: Path to the image file

        Returns:
            The generated response describing the image
        """
        try:
            # Prepare the image
            image_handle = lms.prepare_image(image_path)

            # Create a chat with the user prompt and image
            chat = lms.Chat()
            chat.add_user_message(prompt, images=[image_handle])

            # Generate response
            result = self.model.respond(chat)
            return result.content

        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            raise RuntimeError(f"Failed to process image: {str(e)}")

    def get_loaded_models_info(self, model_type: str = None) -> List[Dict[str, Any]]:
        """Get detailed information about models currently loaded in memory.

        Args:
            model_type: Optional type of models to list ("llm" or "embedding"). If None, lists all models.

        Returns:
            List of dictionaries containing model information
        """
        try:
            # Get loaded models
            loaded_models = lms.list_loaded_models(model_type)
            models_info = []

            for model in loaded_models:
                # Extract basic model info
                info = {
                    "name": model.get_info().display_name,
                    "id": model.get_info().identifier,
                    "type": model.get_info().type,
                    "instance_id": model.get_info().instance_reference,
                }

                # Try to get additional model properties if available
                try:
                    if hasattr(model.get_info(), "context_length"):
                        info["context_length"] = model.get_info().context_length
                except Exception:
                    pass

                models_info.append(info)

            return models_info
        except Exception as e:
            logger.error(f"Failed to get loaded models info: {str(e)}")
            raise RuntimeError(f"Failed to get loaded models info: {str(e)}")

    async def process_message(
        self,
        session_id: str,
        role: str,
        content: str,
        available_tools: List[Any] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        stream: bool = False,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Process a single message based on role and handle tool integration."""
        try:
            # Add message to the session
            await self.chat_repository.add_message(
                session_id=session_id, role=role, content=content
            )

            # If role is system or assistant, just add it to history (no completion needed)
            if role != "user":
                return None

            # For user messages, start the completion flow
            self.current_session_id = session_id
            self.current_message_id = str(uuid.uuid4())

            # Check if we should use tools - only do this if tools are provided
            use_tools = False
            if available_tools:
                tool_info = await self.check_tool_availability(content, available_tools)
                use_tools = tool_info.function_call

                if tool_info.function_call:
                    # Log the tool check result
                    await self.chat_repository.add_message(
                        session_id=session_id,
                        role="system",
                        content=f"Tool availability check: {tool_info.description}",
                    )

            if use_tools:
                # Process with tools (streaming or not)
                if stream:
                    # Return the generator directly without awaiting it
                    return self._process_with_tool_streaming_wrapper(
                        content, available_tools, session_id
                    )
                else:
                    response = await self.process_with_tool(
                        prompt=content, tools=available_tools, session_id=session_id
                    )
                    return response
            else:
                # Regular chat completion (streaming or not)
                # Get all messages for this session and prepare a valid conversation history
                db_messages = await self.chat_repository.get_messages(session_id)

                # Process messages to ensure valid conversation format
                processed_messages = self._process_messages_for_chat(db_messages)

                chat_messages = [
                    ChatMessage(role=msg.role, content=msg.content, created_at=msg.created_at.isoformat())
                    for msg in processed_messages
                ]

                if stream:
                    # Return the generator directly without awaiting it
                    return self._chat_completion_streaming_wrapper(
                        chat_messages, session_id, temperature, max_tokens
                    )
                else:
                    # Non-streaming response
                    chat = self._create_lmstudio_chat(chat_messages)
                    config = {"temperature": temperature, "maxTokens": max_tokens}

                    # Generate the response directly
                    result = self.model.respond(chat, config=config)
                    response = result.content

                    # Save the response
                    await self.chat_repository.add_message(
                        session_id=session_id, role="assistant", content=response
                    )

                    return response

        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            raise RuntimeError(f"Failed to process message: {str(e)}")

    def _process_with_tool_streaming_wrapper(
        self, prompt: str, tools: List[Any], session_id: str
    ) -> AsyncGenerator[str, None]:
        """Wrapper to ensure process_with_tool_streaming returns a proper async generator."""
        # Remove 'async' from the method definition to make it return a generator directly
        return self.process_with_tool_streaming(
            prompt=prompt, tools=tools, session_id=session_id
        )

    def _chat_completion_streaming_wrapper(
        self,
        messages: List[ChatMessage],
        session_id: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Wrapper to ensure chat completion streaming returns a proper async generator."""

        # Create a custom async generator that doesn't need to be awaited
        async def generate():
            # Create chat from messages
            chat = self._create_lmstudio_chat(messages)
            config = {"temperature": temperature, "maxTokens": max_tokens}

            # Generate streaming response
            complete_response = ""
            async for fragment in self._stream_response(chat, config):
                complete_response += fragment
                yield fragment

            # Save the complete response
            await self.chat_repository.add_message(
                session_id=session_id, role="assistant", content=complete_response
            )

        return generate()  # Return the generator directly

    def _process_messages_for_chat(self, messages):
        """Process messages to ensure they form a valid conversation structure.

        This prevents issues like consecutive assistant messages and ensures proper
        alternation between user and assistant messages.
        """
        if not messages:
            return []

        processed = []
        last_role = None

        # Process system messages first
        system_messages = [msg for msg in messages if msg.role == "system"]
        if system_messages:
            # Use only the most recent system message
            processed.append(system_messages[-1])
            last_role = "system"

        # Process user and assistant messages, ensuring proper alternation
        user_assistant_messages = [
            msg for msg in messages if msg.role in ["user", "assistant"]
        ]
        user_assistant_messages.sort(key=lambda msg: msg.created_at)

        for msg in user_assistant_messages:
            # Skip if we have consecutive messages with the same role
            # (except for user messages, which can be consecutive)
            if last_role == msg.role and msg.role == "assistant":
                continue

            processed.append(msg)
            last_role = msg.role

        # Ensure the last message is from the user
        if processed and processed[-1].role != "user":
            # This shouldn't happen in normal operation since we're processing
            # after adding the user message, but just in case
            user_messages = [msg for msg in messages if msg.role == "user"]
            if user_messages:
                processed.append(user_messages[-1])

        return processed

    async def create_chat_session(self, name: Optional[str] = None) -> ChatSession:
        """Create a new chat session.

        Args:
            name: Optional name for the chat session

        Returns:
            The created chat session
        """
        # Use repository to create session
        db_session = await self.chat_repository.create_session(name)

        # Convert to pydantic model
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

    async def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID.

        Args:
            session_id: The ID of the chat session

        Returns:
            The chat session or None if not found
        """
        # Use repository to get session
        db_session = await self.chat_repository.get_session_by_id(session_id)

        if not db_session:
            return None

        # Get all messages for this session
        messages = await self.chat_repository.get_messages(session_id)

        # Convert to pydantic models
        chat_messages = [
            ChatMessage(role=msg.role, content=msg.content, created_at=msg.created_at.isoformat()) for msg in messages
        ]

        # Create and return session model
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

    async def get_all_chat_sessions(self) -> List[ChatSession]:
        """Get all chat sessions.

        Returns:
            List of all chat sessions
        """
        # Use repository to get all sessions
        db_sessions = await self.chat_repository.get_all_sessions()

        # Convert to pydantic models
        return [
            ChatSession(
                id=s.id,
                name=s.name,
                messages=[],  # We don't load messages for list view for performance
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
            for s in db_sessions
        ]

    async def get_active_session(self) -> Optional[ChatSession]:
        """Get the most recently active chat session.

        Returns:
            The most recent chat session or None if no sessions exist
        """
        # Use repository to get the most recently updated session
        db_session = await self.chat_repository.get_active_session()

        if not db_session:
            return None

        # Get all messages for this session
        messages = await self.chat_repository.get_messages(db_session.id)

        # Convert to pydantic models
        chat_messages = [
            ChatMessage(role=msg.role, content=msg.content, created_at=msg.created_at.isoformat()) for msg in messages
        ]

        # Create and return session model
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

    async def add_message_to_session(
        self, session_id: str, message: ChatMessage, message_id: Optional[str] = None
    ) -> Optional[ChatSession]:
        """Add a message to a chat session.

        Args:
            session_id: The ID of the chat session
            message: The message to add

        Returns:
            The updated chat session or None if not found
        """
        # Use repository to add message
        db_message = await self.chat_repository.add_message(
            session_id=session_id,
            role=message.role,
            content=message.content,
            message_id=message_id or str(uuid.uuid4()),
        )

        if not db_message:
            return None

        # Return updated session
        return await self.get_chat_session(session_id)

    async def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session.

        Args:
            session_id: The ID of the chat session

        Returns:
            True if the session was deleted, False if it wasn't found
        """
        # Use repository to delete session
        return await self.chat_repository.delete_session(session_id)

    async def chat_completion_with_session(
        self,
        session_id: str,
        message_content: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        stream: bool = False,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Generate a chat completion and store in the session history.

        Args:
            session_id: The ID of the chat session
            message_content: Content of the user's message
            temperature: The temperature setting for generation
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response

        Returns:
            Generated text response or a generator if streaming
        """
        # Get session
        session = await self.get_chat_session(session_id)
        if not session:
            raise ValueError(f"Chat session with ID {session_id} not found")

        # Add user message to the session
        user_message = ChatMessage(role="user", content=message_content)
        await self.add_message_to_session(session_id, user_message)

        # Get updated session with new message
        updated_session = await self.get_chat_session(session_id)

        # Generate response
        response = self.chat_completion(
            messages=updated_session.messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        # If not streaming, add the assistant's response to the session
        if not stream:
            assistant_message = ChatMessage(role="assistant", content=response)
            await self.add_message_to_session(session_id, assistant_message)

        return response

    def _create_lmstudio_chat(self, messages: List[ChatMessage]):
        """Create an LMStudio Chat object from a list of messages."""
        chat = lms.Chat()

        # Add messages to the chat
        for message in messages:
            role = message.role
            content = message.content

            if role == "system":
                # If this is the first message and it's a system message, set it as the system message
                if not chat._history:
                    chat = lms.Chat(content)
                else:
                    # Otherwise, add it as a regular message
                    chat.add_system_prompt(content)
            elif role == "user":
                chat.add_user_message(
                    content
                )  # Changed from append to add_user_message
            elif role == "assistant":
                chat.add_assistant_response(content)

        return chat

    async def check_tool_availability(
        self, prompt: str, tools: List[Any]
    ) -> FunctionCallInfo:
        """
        Check if any tools are applicable for the given prompt.

        Args:
            prompt: User input to check
            tools: List of available tool functions

        Returns:
            FunctionCallInfo with information about potential function calls
        """
        try:
            # Create tool schema for structured output
            tool_schemas = []
            for tool in tools:
                tool_name = tool.__name__
                tool_doc = inspect.getdoc(tool) or "No description available"
                tool_signature = inspect.signature(tool)
                tool_params = {}

                for param_name, param in tool_signature.parameters.items():
                    param_type = "any"
                    if param.annotation != inspect.Parameter.empty:
                        if hasattr(param.annotation, "__name__"):
                            param_type = param.annotation.__name__
                        else:
                            param_type = str(param.annotation)

                    tool_params[param_name] = {
                        "type": param_type,
                        "description": f"Parameter {param_name} for function {tool_name}",
                    }

                tool_schemas.append(
                    {
                        "name": tool_name,
                        "description": tool_doc,
                        "parameters": tool_params,
                    }
                )

            # Create structured prompt to check if tools should be used
            analysis_prompt = f"""
            Analyze the following user request and determine if any of the available tools should be used.

            User request: "{prompt}"

            Available tools:
            {json.dumps(tool_schemas, indent=2)}

            After your analysis, respond with a JSON object containing these fields:
            - should_use_tool: boolean indicating if a tool should be used
            - tool_name: string name of the tool to use (or null if none)
            - description: string explanation of your decision
            - arguments: object containing arguments for the tool (or null if none)
            """

            # Create a simple chat for analysis
            chat = lms.Chat()
            chat.add_user_message(analysis_prompt)

            # Try with structured output first
            try:
                # Define schema directly as JSON schema rather than using a class
                schema = {
                    "type": "object",
                    "properties": {
                        "should_use_tool": {
                            "type": "boolean",
                            "description": "Whether a tool should be used",
                        },
                        "tool_name": {
                            "type": ["string", "null"],
                            "description": "Name of the tool to use",
                        },
                        "description": {
                            "type": "string",
                            "description": "Explanation of the decision",
                        },
                        "arguments": {
                            "type": ["object", "null"],
                            "description": "Arguments for the tool",
                        },
                    },
                    "required": ["should_use_tool", "description"],
                }

                # Pass the schema directly to the respond method
                result = self.model.respond(chat, response_format=schema)
                analysis = result.parsed

                # Convert to FunctionCallInfo
                return FunctionCallInfo(
                    function_call=analysis.get("should_use_tool", False),
                    function_name=analysis.get("tool_name"),
                    arguments=analysis.get("arguments"),
                    description=analysis.get("description", "No description provided"),
                )

            except Exception as parse_error:
                logger.warning(f"Failed to use structured output: {str(parse_error)}")
                logger.warning("Falling back to regular response parsing")

                # Fallback to regular response and try to parse JSON from it
                result = self.model.respond(chat)
                response_text = result.content

                # Try to extract JSON from the response text
                try:
                    # Find JSON in the response (might be surrounded by text)
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}")

                    if json_start >= 0 and json_end > json_start:
                        json_str = response_text[json_start : json_end + 1]
                        analysis_dict = json.loads(json_str)

                        return FunctionCallInfo(
                            function_call=analysis_dict.get("should_use_tool", False),
                            function_name=analysis_dict.get("tool_name"),
                            arguments=analysis_dict.get("arguments"),
                            description=analysis_dict.get(
                                "description", "No description provided"
                            ),
                        )
                except Exception as json_error:
                    logger.warning(
                        f"Failed to extract JSON from response: {str(json_error)}"
                    )

                # If all else fails, use a simple heuristic based on tool names
                for tool in tools:
                    tool_name = tool.__name__
                    if (
                        tool_name.lower() in response_text.lower()
                        and "should use" in response_text.lower()
                    ):
                        return FunctionCallInfo(
                            function_call=True,
                            function_name=tool_name,
                            arguments=None,
                            description=f"Tool matched in response: {tool_name}",
                        )

                # Default to no tool if we can't determine one
                return FunctionCallInfo(
                    function_call=False,
                    description="Could not determine tool usage from response",
                )

        except Exception as e:
            logger.error(f"Failed to check tool availability: {str(e)}")
            # Return default response indicating no function call
            return FunctionCallInfo(
                function_call=False,
                description=f"Error checking tool availability: {str(e)}",
            )
