"""
Repository for LLM connection operations.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.config import LLMConfig, LLMConnection
from app.repository.base_repository import BaseRepository
from app.utils.db_session import get_db_session
from sqlalchemy import select


class LLMConnectionRepository(BaseRepository):
    """
    Repository for LLM connection management operations
    """

    def __init__(self):
        super().__init__(LLMConnection)

    async def get_all_connections(self) -> List[LLMConnection]:
        """
        Get all LLM connections from the database
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(LLMConnection).order_by(LLMConnection.name)
            )
            connections = result.scalars().all()
            return connections

    async def get_connection_by_id(self, connection_id: str) -> Optional[LLMConnection]:
        """
        Get a connection by ID
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(LLMConnection).where(LLMConnection.id == connection_id)
            )
            connection = result.scalars().first()
            return connection

    async def create_connection(
        self,
        name: str,
        provider: str,
        model_name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        is_active: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> LLMConnection:
        """
        Create a new LLM connection
        """
        connection_id = str(uuid.uuid4())

        # If this is set as active, deactivate all other connections
        if is_active:
            await self.deactivate_all_connections()

        # Create the connection object
        connection = LLMConnection(
            id=connection_id,
            name=name,
            provider=provider,
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
            api_version=api_version,
            is_active=is_active,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            config_json=json.dumps(config) if config else None,
        )

        return await self.save(connection)

    async def update_connection(
        self, connection_id: str, **kwargs
    ) -> Optional[LLMConnection]:
        """
        Update an LLM connection by ID
        """
        async with get_db_session() as session:
            connection = await session.get(LLMConnection, connection_id)
            if connection:
                # Update only provided fields
                for key, value in kwargs.items():
                    if key == "config" and value is not None:
                        connection.config_json = json.dumps(value)
                    elif hasattr(connection, key):
                        setattr(connection, key, value)

                # If setting as active, deactivate all other connections
                if kwargs.get("is_active"):
                    await self.deactivate_all_connections(exclude_id=connection_id)

                connection.updated_at = datetime.now()
                await session.commit()
                await session.refresh(connection)
                return connection
            return None

    async def delete_connection(self, connection_id: str) -> bool:
        """
        Delete an LLM connection by ID
        """
        async with get_db_session() as session:
            connection = await session.get(LLMConnection, connection_id)
            if connection:
                # If deleting the active connection, we need to ensure there's another active one
                was_active = connection.is_active

                await session.delete(connection)
                await session.commit()

                # If we deleted the active connection, try to activate another one
                if was_active:
                    await self.activate_default_connection()

                return True
            return False

    async def get_active_connection(self) -> Optional[LLMConnection]:
        """
        Get the currently active LLM connection
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(LLMConnection).where(LLMConnection.is_active == True).limit(1)
            )
            connection = result.scalars().first()
            return connection

    async def deactivate_all_connections(
        self, exclude_id: Optional[str] = None
    ) -> None:
        """
        Set all connections to inactive, optionally excluding one by ID
        """
        async with get_db_session() as session:
            # Get all connections that should be deactivated
            query = select(LLMConnection).where(LLMConnection.is_active == True)
            if exclude_id:
                query = query.where(LLMConnection.id != exclude_id)

            result = await session.execute(query)
            connections = result.scalars().all()

            # Set them all to inactive
            for connection in connections:
                connection.is_active = False
                connection.updated_at = datetime.now()

            await session.commit()

    async def activate_connection(self, connection_id: str) -> bool:
        """
        Set a specific connection as active and deactivate all others
        """
        # First deactivate all
        await self.deactivate_all_connections(exclude_id=connection_id)

        # Then activate the specified one
        async with get_db_session() as session:
            connection = await session.get(LLMConnection, connection_id)
            if connection:
                connection.is_active = True
                connection.updated_at = datetime.now()
                await session.commit()
                return True
            return False

    async def activate_default_connection(self) -> Optional[LLMConnection]:
        """
        Activate the first available connection if none is active
        """
        async with get_db_session() as session:
            # Check if there's already an active connection
            result = await session.execute(
                select(LLMConnection).where(LLMConnection.is_active == True).limit(1)
            )
            active = result.scalars().first()
            if active:
                return active

            # If not, get the first connection and activate it
            result = await session.execute(
                select(LLMConnection).order_by(LLMConnection.created_at).limit(1)
            )
            connection = result.scalars().first()

            if connection:
                connection.is_active = True
                connection.updated_at = datetime.now()
                await session.commit()
                await session.refresh(connection)
                return connection

            return None

    def connection_to_llm_config(self, connection: LLMConnection) -> LLMConfig:
        """
        Convert a connection entity to an LLM configuration that can be used with PraisonAI
        """
        config = {
            "model": connection.model_name,
            "temperature": 0.7,
            "max_tokens": 1000,
            "response_format": {"type": "text"},
        }

        # Add optional fields if they exist
        if connection.base_url:
            config["base_url"] = connection.base_url

        if connection.api_key:
            config["api_key"] = connection.api_key

        if connection.api_version:
            config["api_version"] = connection.api_version

        # Add any additional config from the JSON field
        if connection.config_json:
            try:
                additional_config = json.loads(connection.config_json)
                for key, value in additional_config.items():
                    if key not in [
                        "model",
                        "base_url",
                        "api_key",
                        "api_version",
                    ]:  # Don't override primary fields
                        config[key] = value
            except json.JSONDecodeError:
                pass

        return LLMConfig(**config)
