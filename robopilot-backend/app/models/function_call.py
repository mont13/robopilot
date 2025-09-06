"""
Database models for function calls.
"""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import Column, ForeignKey, String, Text

from app.models.base import BaseOrm


class FunctionCall(BaseOrm):
    """Database model for storing function calls made during chat sessions."""

    __tablename__ = "function_calls"

    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    message_id = Column(
        String(36), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False
    )
    function_name = Column(String(255), nullable=False)
    arguments = Column(Text, nullable=True)  # JSON serialized arguments
    result = Column(Text, nullable=True)  # JSON serialized result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FunctionCall":
        """Create a FunctionCall instance from a dictionary."""
        return cls(
            id=data.get("id"),
            session_id=data.get("session_id"),
            message_id=data.get("message_id"),
            function_name=data.get("function_name"),
            arguments=json.dumps(data.get("arguments"))
            if data.get("arguments")
            else None,
            result=json.dumps(data.get("result"))
            if data.get("result") is not None
            else None,
            created_at=data.get("created_at") or datetime.now(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert FunctionCall to a dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "function_name": self.function_name,
            "arguments": json.loads(self.arguments) if self.arguments else {},
            "result": json.loads(self.result) if self.result else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
