"""
Database models for chat sessions.
"""

from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseOrm, BaseSchema


class ChatSession(BaseOrm):
    """Database model for a chat session."""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # Relationship with messages (one-to-many)
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(BaseOrm):
    """Database model for a chat message."""

    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, index=True)
    role = Column(String(20), nullable=False)  # system, user, or assistant
    content = Column(Text, nullable=False)
    session_id = Column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # Relationship with session (many-to-one)
    session: Mapped[ChatSession] = relationship(
        "ChatSession", back_populates="messages"
    )
