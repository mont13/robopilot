"""
LMStudio client utility for interacting with LM Studio API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Model for a chat message."""

    role: str
    content: str
    created_at: datetime


class FunctionCallInfo(BaseModel):
    """Model for function call information."""

    function_call: bool = False
    function_name: str | None = None
    arguments: dict[str, Any] | None = None
    description: str | None = None


class ToolResponseSchema(BaseModel):
    """Schema for tool calling structured response."""

    message: str
    function_call: bool = False
    function_name: str | None = None
    arguments: dict[str, Any] | None = None


class ChatSession(BaseModel):
    """Model for a chat session."""

    id: str
    name: str | None = None
    messages: list[ChatMessage] = []
    created_at: str = None
    updated_at: str = None
