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
        # Check if activation is requested
        need_activation = False
        if "is_active" in kwargs and kwargs["is_active"]:
            need_activation = True

        # Make a copy of kwargs to avoid modifying the original
        update_data = kwargs.copy()

        # Step 1: Update basic properties
        updated_connection = None
        async with get_db_session() as session:
            try:
                # Get the connection
                connection = await session.get(LLMConnection, connection_id)
                if not connection:
                    return None

                # Update fields except is_active (handle separately)
                for key, value in update_data.items():
                    if key != "is_active":  # Skip is_active, we'll handle it separately
                        if key == "config" and value is not None:
                            connection.config_json = json.dumps(value)
                        elif hasattr(connection, key):
                            setattr(connection, key, value)

                # Always update the timestamp
                connection.updated_at = datetime.now()

                # Store ID for later use
                connection_id = connection.id
            except Exception as e:
                # If anything goes wrong, just re-raise the exception
                # The context manager will handle rollback
                raise e

        # Step 2: Handle activation in a completely separate transaction if needed
        if need_activation:
            try:
                # First deactivate all other connections
                await self.deactivate_all_connections(exclude_id=connection_id)

                # Then activate this one in a new transaction
                async with get_db_session() as session:
                    connection = await session.get(LLMConnection, connection_id)
                    if connection:
                        connection.is_active = True
                        connection.updated_at = datetime.now()
            except Exception as e:
                # Log but don't fail the whole operation
                import logging
                logging.error(f"Failed to set connection as active: {str(e)}")

        # Step 3: Get the final state in a fresh transaction
        async with get_db_session() as session:
            connection = await session.get(LLMConnection, connection_id)
            return connection

    async def delete_connection(self, connection_id: str) -> bool:
        """
        Delete an LLM connection by ID
        """
        # First check if connection exists and get its active status
        connection_to_delete = None
        was_active = False

        async with get_db_session() as session:
            try:
                connection_to_delete = await session.get(LLMConnection, connection_id)
                if not connection_to_delete:
                    return False

                # Store active status before deletion
                was_active = connection_to_delete.is_active

                # Delete the connection
                await session.delete(connection_to_delete)

                # Return immediately if it wasn't active
                if not was_active:
                    return True
            except Exception as e:
                # Let context manager handle rollback
                raise e

        # In a separate transaction, activate another connection if needed
        if was_active:
            try:
                await self.activate_default_connection()
            except Exception as e:
                # Log but don't fail if we can't activate a default
                import logging
                logging.error(f"Failed to activate default connection after deletion: {str(e)}")

        return True

    async def get_active_connection(self) -> Optional[LLMConnection]:
        """
        Get the currently active LLM connection
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(LLMConnection).where(LLMConnection.is_active == True).limit(1)
            )
            connection = result.scalars().first()
            return connection if connection else None

    async def deactivate_all_connections_with_session(
        self, session, exclude_id: Optional[str] = None
    ) -> None:
        """
        Set all connections to inactive using an existing session, optionally excluding one by ID
        """
        try:
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

            # Note: This method doesn't commit the session,
            # as it's expected to be called from within a transaction
            # that will handle the commit
        except Exception as e:
            # Log any errors but don't propagate them
            import logging
            logging.error(f"Error deactivating connections: {str(e)}")

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

    async def activate_connection(self, connection_id: str) -> bool:
        """
        Set a specific connection as active and deactivate all others
        """
        # First deactivate all connections
        try:
            await self.deactivate_all_connections()
        except Exception as e:
            import logging
            logging.error(f"Error deactivating connections: {str(e)}")
            # Continue anyway to try activating the requested connection

        # Then activate the specific connection
        async with get_db_session() as session:
            try:
                # Get the connection to make sure it exists
                connection = await session.get(LLMConnection, connection_id)
                if not connection:
                    return False

                # Activate the specified one
                connection.is_active = True
                connection.updated_at = datetime.now()
                return True
            except Exception as e:
                # Let context manager handle rollback
                raise e

    async def activate_default_connection(self) -> Optional[LLMConnection]:
        """
        Activate the first available connection if none is active
        """
        async with get_db_session() as session:
            try:
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
                    await session.refresh(connection)
                    return connection

                return None
            except Exception as e:
                # Let context manager handle rollback
                raise e

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
