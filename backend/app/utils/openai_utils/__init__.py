"""
OpenAI utilities for the robopilot API.

This package provides utilities for working with OpenAI API, particularly 
for function calling capabilities used with LLMs.
"""

from .openai_client import OpenAIClient
from .function_calling import handle_function_calls, register_tool, get_tools_from_functions, tool

__all__ = ["OpenAIClient", "handle_function_calls", "register_tool", "get_tools_from_functions", "tool"]