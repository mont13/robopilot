"""
Repository for chat session operations
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.chat_session import ChatMessage as DbChatMessage
from app.models.chat_session import ChatSession as DbChatSession
from app.repository.base_repository import BaseRepository
from app.utils.db_session import get_db_session
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, select
from sqlalchemy.ext.declarative import declarative_base

# Define new model for function calls
Base = declarative_base()


class FunctionCall(Base):
    """Model for storing function calls."""

    __tablename__ = "function_calls"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    message_id = Column(String, ForeignKey("chat_messages.id", ondelete="CASCADE"))
    function_name = Column(String, nullable=False)
    arguments = Column(Text)  # JSON serialized arguments
    result = Column(Text)  # JSON serialized result
    created_at = Column(DateTime, default=datetime.now)


class ChatSessionRepository(BaseRepository):
    """
    Repository for chat session management operations
    """

    def __init__(self):
        super().__init__(DbChatSession)

    async def get_all_sessions(self) -> List[DbChatSession]:
        """
        Get all chat sessions from the database
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(DbChatSession).order_by(DbChatSession.updated_at.desc())
            )
            sessions = result.scalars().all()
            return sessions

    async def get_session_by_id(self, session_id: str) -> Optional[DbChatSession]:
        """
        Get a chat session by ID
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(DbChatSession).where(DbChatSession.id == session_id)
            )
            chat_session = result.scalars().first()
            return chat_session

    async def create_session(self, name: Optional[str] = None) -> DbChatSession:
        """
        Create a new chat session
        """
        session_id = str(uuid.uuid4())
        session_name = name or f"Chat {session_id[:8]}"

        chat_session = DbChatSession(
            id=session_id,
            name=session_name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        return await self.save(chat_session)

    async def update_session_name(
        self, session_id: str, name: str
    ) -> Optional[DbChatSession]:
        """
        Update the name of a chat session
        """
        async with get_db_session() as session:
            chat_session = await session.get(DbChatSession, session_id)
            if chat_session:
                chat_session.name = name
                chat_session.updated_at = datetime.now()
                await session.commit()
                await session.refresh(chat_session)
                return chat_session
            return None

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session by ID
        """
        async with get_db_session() as session:
            chat_session = await session.get(DbChatSession, session_id)
            if chat_session:
                await session.delete(chat_session)
                await session.commit()
                return True
            return False

    async def add_message(
        self, session_id: str, role: str, content: str, message_id: str = None
    ) -> Optional[DbChatMessage]:
        """
        Add a new message to a chat session

        Args:
            session_id: The ID of the chat session
            role: The role of the message sender (system, user, assistant)
            content: The content of the message
            message_id: Optional ID for the message, will generate one if not provided

        Returns:
            The created message or None if session not found
        """
        # Create message object first
        message_id = message_id or str(uuid.uuid4())
        message = DbChatMessage(
            id=message_id,
            role=role,
            content=content,
            session_id=session_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        async with get_db_session() as session:
            # Check if chat session exists
            chat_session = await session.get(DbChatSession, session_id)
            if not chat_session:
                return None

            # Update session timestamp
            chat_session.updated_at = datetime.now()

            # Add message to session
            session.add(message)
            await session.commit()

            # No refresh needed as we return the object we created
            return message

    async def get_messages(self, session_id: str) -> List[DbChatMessage]:
        """
        Get all messages for a chat session ordered by creation time
        """
        async with get_db_session() as session:
            # Modified to explicitly select only the columns that exist
            stmt = (
                select(DbChatMessage)
                .where(DbChatMessage.session_id == session_id)
                .order_by(DbChatMessage.created_at)
            )
            result = await session.execute(stmt)
            messages = result.scalars().all()
            return messages

    async def get_active_session(self) -> Optional[DbChatSession]:
        """
        Get the most recently updated chat session

        Returns:
            The most recently updated chat session or None if no sessions exist
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(DbChatSession).order_by(DbChatSession.updated_at.desc()).limit(1)
            )
            active_session = result.scalars().first()
            return active_session

    async def delete_message(self, message_id: str) -> bool:
        """
        Delete a message by ID
        """
        async with get_db_session() as session:
            message = await session.get(DbChatMessage, message_id)
            if message:
                # Update session timestamp
                chat_session = await session.get(DbChatSession, message.session_id)
                if chat_session:
                    chat_session.updated_at = datetime.now()

                await session.delete(message)
                await session.commit()
                return True
            return False

    async def log_function_call(
        self,
        session_id: str,
        message_id: str,
        function_name: str,
        arguments: Dict[str, Any],
        result: Any,
    ) -> str:
        """
        Log a function call to the database

        Args:
            session_id: The ID of the chat session
            message_id: The ID of the message that triggered the function call
            function_name: Name of the function that was called
            arguments: Dictionary of arguments passed to the function
            result: Result returned by the function

        Returns:
            The ID of the created function call record
        """
        # Create function call object
        function_call_id = str(uuid.uuid4())

        # Serialize arguments and result to JSON
        serialized_args = json.dumps(arguments)
        serialized_result = json.dumps(result)

        async with get_db_session() as session:
            # Create function call record
            function_call = FunctionCall(
                id=function_call_id,
                session_id=session_id,
                message_id=message_id,
                function_name=function_name,
                arguments=serialized_args,
                result=serialized_result,
                created_at=datetime.now(),
            )

            session.add(function_call)
            await session.commit()

            return function_call_id

    async def get_function_calls(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all function calls for a chat session

        Args:
            session_id: The ID of the chat session

        Returns:
            List of function calls with deserialized arguments and results
        """
        async with get_db_session() as session:
            stmt = (
                select(FunctionCall)
                .where(FunctionCall.session_id == session_id)
                .order_by(FunctionCall.created_at)
            )
            result = await session.execute(stmt)
            function_calls = result.scalars().all()

            # Deserialize arguments and results
            return [
                {
                    "id": fc.id,
                    "session_id": fc.session_id,
                    "message_id": fc.message_id,
                    "function_name": fc.function_name,
                    "arguments": json.loads(fc.arguments) if fc.arguments else {},
                    "result": json.loads(fc.result) if fc.result else None,
                    "created_at": fc.created_at.isoformat() if fc.created_at else None,
                }
                for fc in function_calls
            ]
