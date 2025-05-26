import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union

from openai import OpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
)

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    A utility class for working with OpenAI's API, primarily for chat completions
    with function calling support.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key. If None, will use the OPENAI_API_KEY environment variable.
            base_url: Optional base URL for the OpenAI API (for custom deployments or proxies).
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.registered_tools = {}

    def chat_completion(
        self,
        messages: List[ChatCompletionMessageParam],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        temperature: float = 0.7,
        stream: bool = False,
        parallel_tool_calls: bool = False,
    ) -> Union[ChatCompletion, Any]:
        """
        Send a request to the OpenAI Chat Completions API.

        Args:
            messages: List of message objects with role and content
            model: The model to use for completion
            tools: Optional list of tools (functions) the model can call
            tool_choice: Whether the model should use tools ("auto", "none", "required" or specific function)
            temperature: Sampling temperature (0-2, lower is more deterministic)
            stream: Whether to stream the response
            parallel_tool_calls: Whether to allow multiple tool calls in a single response

        Returns:
            The API response object or stream
        """
        try:
            # Build request parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
            }
            
            # Only add tools and tool_choice if tools are provided
            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice
                params["parallel_tool_calls"] = parallel_tool_calls
            
            response = self.client.chat.completions.create(**params)
            return response
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise

    def register_tool(self, function: Callable) -> None:
        """
        Register a function as an available tool for the model.

        Args:
            function: The function to register as a tool
        """
        from .function_calling import register_tool

        self.registered_tools[function.__name__] = register_tool(function)

    def get_registered_tools(self) -> List[Dict[str, Any]]:
        """
        Get all registered tools in the format expected by the OpenAI API.

        Returns:
            List of tool specifications
        """
        return list(self.registered_tools.values())

    def handle_function_calls(
        self,
        message: ChatCompletionMessage,
        available_functions: Optional[Dict[str, Callable]] = None,
    ) -> Dict[str, Any]:
        """
        Process function calls in a chat completion response.

        Args:
            message: The message containing potential tool calls
            available_functions: Dictionary mapping function names to callables

        Returns:
            Dictionary with results from function calls, mapping tool_call_id to result
        """
        from .function_calling import handle_function_calls

        functions = available_functions or {
            name: func
            for name, func in globals().items()
            if callable(func) and name in self.registered_tools
        }

        return handle_function_calls(message, functions)

    def create_conversation_with_function_results(
        self,
        messages: List[ChatCompletionMessageParam],
        model: str,
        functions: Dict[str, Callable],
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Union[str, Any]:
        """
        Complete flow for a conversation with function calling and result incorporation.

        Args:
            messages: Conversation history
            model: Model to use
            functions: Dictionary of available functions
            temperature: Temperature for generation
            stream: Whether to stream the response

        Returns:
            Final assistant response after function calls, or a stream
        """
        # Register all provided functions
        for func in functions.values():
            if func.__name__ not in self.registered_tools:
                self.register_tool(func)

        tools = self.get_registered_tools()

        # First completion to potentially get function calls
        response = self.chat_completion(
            messages=messages,
            model=model,
            tools=tools,
            temperature=temperature,
            stream=stream,
        )

        # If streaming, return the stream directly
        if stream:
            return response

        message = response.choices[0].message

        # Check if there are any tool calls
        if message.tool_calls:
            # Execute functions and get results
            results = self.handle_function_calls(message, functions)

            # Add assistant's message with the function calls
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                }
            )

            # Add tool results to the messages
            for tool_call_id, result in results.items():
                # Ensure result is serializable
                if not isinstance(
                    result, (dict, list, str, int, float, bool, type(None))
                ):
                    result = str(result)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(result),
                    }
                )

            # Final completion with function results incorporated
            final_response = self.chat_completion(
                messages=messages, model=model, tools=tools, temperature=temperature
            )

            return final_response.choices[0].message.content

        # If no functions were called, return the original response
        return message.content
