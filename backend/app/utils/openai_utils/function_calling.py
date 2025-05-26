import inspect
import json
import logging
from functools import wraps
from typing import Dict, Any, Callable, List, Union
from docstring_parser import parse

from openai.types.chat import ChatCompletionMessage

logger = logging.getLogger(__name__)


def register_tool(func: Callable) -> Dict[str, Any]:
    """
    Convert a Python function into an OpenAI tool specification.

    Args:
        func: The function to convert to a tool

    Returns:
        Tool specification dictionary
    """
    # Get function signature
    sig = inspect.signature(func)

    # Parse docstring for description
    docstring = parse(inspect.getdoc(func) or "")

    # Extract parameter info
    params = {}
    required_params = []

    for name, param in sig.parameters.items():
        # Skip self parameter for instance methods
        if name == "self":
            continue

        param_type = param.annotation
        param_desc = ""

        # Get description from docstring if available
        for param_doc in docstring.params:
            if param_doc.arg_name == name:
                param_desc = param_doc.description
                break

        # Determine parameter type
        param_info = {"description": param_desc}

        # Handle different parameter types
        if param_type is str:
            param_info["type"] = "string"
        elif param_type is int:
            param_info["type"] = "integer"
        elif param_type is float:
            param_info["type"] = "number"
        elif param_type is bool:
            param_info["type"] = "boolean"
        elif param_type is list:
            param_info["type"] = "array"
        elif param_type is dict:
            param_info["type"] = "object"
        elif getattr(param_type, "__origin__", None) is Union:
            # Handle Optional types (Union[Type, None])
            types = getattr(param_type, "__args__", [])
            if len(types) == 2 and types[1] is type(None):
                # This is Optional[Type]
                if types[0] is str:
                    param_info["type"] = ["string", "null"]
                elif types[0] is int:
                    param_info["type"] = ["integer", "null"]
                elif types[0] is float:
                    param_info["type"] = ["number", "null"]
                elif types[0] is bool:
                    param_info["type"] = ["boolean", "null"]
                elif types[0] is list:
                    param_info["type"] = ["array", "null"]
                elif types[0] is dict:
                    param_info["type"] = ["object", "null"]
                else:
                    param_info["type"] = ["string", "null"]
            else:
                param_info["type"] = "string"

        # Add parameter to the schema
        params[name] = param_info

        # Add to required parameters if no default value
        if param.default == inspect.Parameter.empty:
            required_params.append(name)

    # Build tool specification
    tool = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": docstring.short_description or "",
            "parameters": {
                "type": "object",
                "properties": params,
                "required": required_params,
                "additionalProperties": False,
            },
        },
    }

    return tool


def handle_function_calls(
    message: ChatCompletionMessage, available_functions: Dict[str, Callable]
) -> Dict[str, Any]:
    """
    Process and execute function calls from a model message.

    Args:
        message: The ChatCompletionMessage containing potential tool calls
        available_functions: Dictionary mapping function names to callable functions

    Returns:
        Dictionary mapping tool_call_id to function results
    """
    results = {}

    # Check if there are tool calls
    if not message.tool_calls:
        return results

    # Process each tool call
    for tool_call in message.tool_calls:
        if tool_call.type != "function":
            continue

        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        tool_call_id = tool_call.id

        # Check if function exists
        if function_name not in available_functions:
            logger.warning(f"Function {function_name} not found")
            results[tool_call_id] = {"error": f"Function {function_name} not available"}
            continue

        # Execute function
        function = available_functions[function_name]
        try:
            function_result = function(**function_args)
            # Convert non-serializable objects to strings if needed
            if not isinstance(
                function_result, (dict, list, str, int, float, bool, type(None))
            ):
                function_result = str(function_result)
            results[tool_call_id] = function_result
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            results[tool_call_id] = {"error": str(e)}

    return results


def tool(func=None):
    """
    Decorator to register a function as a tool and add metadata for OpenAI function calling.

    Usage:
        @tool
        def get_weather(location: str) -> dict:
            '''Get current weather for a location.'''
            # function implementation

    Returns:
        The decorated function
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        # Store the tool specification on the function
        wrapper._tool_spec = register_tool(f)
        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def get_tools_from_functions(functions: List[Callable]) -> List[Dict[str, Any]]:
    """
    Convert a list of functions to OpenAI tool specifications.

    Args:
        functions: List of functions to convert

    Returns:
        List of tool specifications
    """
    tools = []

    for func in functions:
        # If function was decorated with @tool
        if hasattr(func, "_tool_spec"):
            tools.append(func._tool_spec)
        else:
            # Generate tool spec on the fly
            tools.append(register_tool(func))

    return tools
