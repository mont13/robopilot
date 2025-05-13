"""
Controller for LLM connection management.
"""

import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from ..models.config import (
    LLMConnectionCreate,
    LLMConnectionResponse,
    LLMConnectionUpdate,
)
from ..repository.llm_connection_repository import LLMConnectionRepository
from ..utils.praison_integration.agents import get_llm_config

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/connections", tags=["LLM Connections"])


# Helper function to get repository
def get_llm_connection_repo():
    return LLMConnectionRepository()


class DefaultConnectionResponse(BaseModel):
    """Response model for the default connection operation."""

    connection_id: str = Field(..., description="ID of the activated connection")
    name: str = Field(..., description="Name of the activated connection")
    provider: str = Field(..., description="Provider of the activated connection")


class TestConnectionRequest(BaseModel):
    """Request model for testing an LLM connection."""

    provider: str = Field(
        ..., description="Provider type (openai, azure, lmstudio, ollama, etc)"
    )
    model_name: str = Field(..., description="Name of the model to use")
    base_url: Optional[str] = Field(None, description="Base URL for API endpoint")
    api_key: Optional[str] = Field(None, description="API key")
    api_version: Optional[str] = Field(None, description="API version (for Azure)")
    prompt: str = Field("Say hello world", description="Test prompt to send")


class TestConnectionResponse(BaseModel):
    """Response model for a connection test."""

    success: bool = Field(..., description="Whether the test was successful")
    response: Optional[str] = Field(None, description="Response from the model")
    error: Optional[str] = Field(None, description="Error message if test failed")


@router.get("/", response_model=List[LLMConnectionResponse])
async def list_connections(
    repo: LLMConnectionRepository = Depends(get_llm_connection_repo),
):
    """Get all LLM connections."""
    try:
        connections = await repo.get_all_connections()

        # Convert to response models
        return [
            LLMConnectionResponse(
                id=conn.id,
                name=conn.name,
                provider=conn.provider,
                model_name=conn.model_name,
                base_url=conn.base_url,
                api_version=conn.api_version,
                is_active=conn.is_active,
                created_at=conn.created_at.isoformat() if conn.created_at else None,
                updated_at=conn.updated_at.isoformat() if conn.updated_at else None,
                config={},  # We don't return the full config for security reasons
            )
            for conn in connections
        ]
    except Exception as e:
        logger.error(f"Failed to list connections: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list connections: {str(e)}"
        )


@router.post("/", response_model=LLMConnectionResponse)
async def create_connection(
    request: LLMConnectionCreate,
    repo: LLMConnectionRepository = Depends(get_llm_connection_repo),
):
    """Create a new LLM connection."""
    try:
        connection = await repo.create_connection(
            name=request.name,
            provider=request.provider,
            model_name=request.model_name,
            base_url=request.base_url,
            api_key=request.api_key,
            api_version=request.api_version,
            is_active=request.is_active,
            config=request.config,
        )

        return LLMConnectionResponse(
            id=connection.id,
            name=connection.name,
            provider=connection.provider,
            model_name=connection.model_name,
            base_url=connection.base_url,
            api_version=connection.api_version,
            is_active=connection.is_active,
            created_at=connection.created_at.isoformat()
            if connection.created_at
            else None,
            updated_at=connection.updated_at.isoformat()
            if connection.updated_at
            else None,
            config={},  # We don't return the full config for security reasons
        )
    except Exception as e:
        logger.error(f"Failed to create connection: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create connection: {str(e)}"
        )


@router.get("/{connection_id}", response_model=LLMConnectionResponse)
async def get_connection(
    connection_id: str = Path(..., description="The ID of the connection to retrieve"),
    repo: LLMConnectionRepository = Depends(get_llm_connection_repo),
):
    """Get a specific LLM connection by ID."""
    try:
        connection = await repo.get_connection_by_id(connection_id)
        if not connection:
            raise HTTPException(
                status_code=404, detail=f"Connection with ID {connection_id} not found"
            )

        return LLMConnectionResponse(
            id=connection.id,
            name=connection.name,
            provider=connection.provider,
            model_name=connection.model_name,
            base_url=connection.base_url,
            api_version=connection.api_version,
            is_active=connection.is_active,
            created_at=connection.created_at.isoformat()
            if connection.created_at
            else None,
            updated_at=connection.updated_at.isoformat()
            if connection.updated_at
            else None,
            config={},  # We don't return the full config for security reasons
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get connection: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get connection: {str(e)}"
        )


@router.put("/{connection_id}", response_model=LLMConnectionResponse)
async def update_connection(
    request: LLMConnectionUpdate,
    connection_id: str = Path(..., description="The ID of the connection to update"),
    repo: LLMConnectionRepository = Depends(get_llm_connection_repo),
):
    """Update an LLM connection."""
    try:
        # Get all non-None fields from the request
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}

        connection = await repo.update_connection(connection_id, **update_data)
        if not connection:
            raise HTTPException(
                status_code=404, detail=f"Connection with ID {connection_id} not found"
            )

        return LLMConnectionResponse(
            id=connection.id,
            name=connection.name,
            provider=connection.provider,
            model_name=connection.model_name,
            base_url=connection.base_url,
            api_version=connection.api_version,
            is_active=connection.is_active,
            created_at=connection.created_at.isoformat()
            if connection.created_at
            else None,
            updated_at=connection.updated_at.isoformat()
            if connection.updated_at
            else None,
            config={},  # We don't return the full config for security reasons
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update connection: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update connection: {str(e)}"
        )


@router.delete("/{connection_id}", response_model=dict)
async def delete_connection(
    connection_id: str = Path(..., description="The ID of the connection to delete"),
    repo: LLMConnectionRepository = Depends(get_llm_connection_repo),
):
    """Delete an LLM connection."""
    try:
        success = await repo.delete_connection(connection_id)
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Connection with ID {connection_id} not found"
            )

        return {"message": f"Connection with ID {connection_id} successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete connection: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete connection: {str(e)}"
        )


@router.post("/{connection_id}/activate", response_model=DefaultConnectionResponse)
async def activate_connection(
    connection_id: str = Path(..., description="The ID of the connection to activate"),
    repo: LLMConnectionRepository = Depends(get_llm_connection_repo),
):
    """Set a specific connection as the active one."""
    try:
        success = await repo.activate_connection(connection_id)
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Connection with ID {connection_id} not found"
            )

        # Get the updated connection
        connection = await repo.get_connection_by_id(connection_id)

        return DefaultConnectionResponse(
            connection_id=connection.id,
            name=connection.name,
            provider=connection.provider,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate connection: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to activate connection: {str(e)}"
        )


@router.get("/active/", response_model=LLMConnectionResponse)
async def get_active_connection(
    repo: LLMConnectionRepository = Depends(get_llm_connection_repo),
):
    """Get the currently active LLM connection."""
    try:
        connection = await repo.get_active_connection()
        if not connection:
            # Try to activate a default connection
            connection = await repo.activate_default_connection()

        if not connection:
            raise HTTPException(
                status_code=404,
                detail="No active connection found and no connections available to activate",
            )

        return LLMConnectionResponse(
            id=connection.id,
            name=connection.name,
            provider=connection.provider,
            model_name=connection.model_name,
            base_url=connection.base_url,
            api_version=connection.api_version,
            is_active=connection.is_active,
            created_at=connection.created_at.isoformat()
            if connection.created_at
            else None,
            updated_at=connection.updated_at.isoformat()
            if connection.updated_at
            else None,
            config={},  # We don't return the full config for security reasons
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get active connection: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get active connection: {str(e)}"
        )


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest):
    """
    Test a connection configuration without saving it.

    This endpoint tests if the specified configuration can successfully connect to the model
    and generate a response.
    """
    try:
        from praisonaiagents import Agent

        # Create LLM config
        llm_config = {
            "model": request.model_name,
            "api_key": request.api_key if request.api_key else None,
            "base_url": request.base_url if request.base_url else None,
            "temperature": 0.7,
            "max_tokens": 100,
            "timeout": 10,  # Short timeout for testing
            "response_format": {"type": "text"},
        }

        # Add API version for Azure
        if request.api_version:
            llm_config["api_version"] = request.api_version

        # Create test agent
        agent = Agent(
            name="TestAgent",
            instructions="You are a test agent. Keep responses very brief.",
            llm=llm_config,
            verbose=False,
        )

        # Try to get a response
        response = agent.chat(request.prompt)

        return TestConnectionResponse(success=True, response=response)
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return TestConnectionResponse(success=False, error=str(e))


@router.get("/debug/", response_model=dict)
async def debug_connections(
    repo: LLMConnectionRepository = Depends(get_llm_connection_repo),
):
    """
    Get debug information about the LLM connections.

    This endpoint provides detailed information about all connections,
    the active connection, and environment variables related to the API.
    """
    try:
        # Get all connections
        connections = await repo.get_all_connections()

        # Get active connection
        active_connection = await repo.get_active_connection()

        # Check environment variables
        env_vars = {
            "OPENAI_API_KEY": "NA",
            "OPENAI_MODEL_NAME": "lm_studio/gemma-3-4b-it-qat",
            "OPENAI_API_BASE": "http://localhost:1234/v1",
        }

        # Check if we can build a valid config
        try:
            llm_config = await get_llm_config()
            config_status = "Valid configuration"
        except Exception as config_err:
            llm_config = None
            config_status = f"Configuration error: {str(config_err)}"

        # Build response
        response = {
            "connections_count": len(connections),
            "active_connection_id": active_connection.id if active_connection else None,
            "active_connection_provider": active_connection.provider
            if active_connection
            else None,
            "active_connection_model": active_connection.model_name
            if active_connection
            else None,
            "active_connection_base_url": active_connection.base_url
            if active_connection
            else None,
            "environment_variables": env_vars,
            "current_config_status": config_status,
            "current_config": llm_config,
        }

        # Mask API keys for security
        if llm_config and "api_key" in llm_config and llm_config["api_key"]:
            response["current_config"]["api_key"] = "****"

        return response
    except Exception as e:
        logger.error(f"Failed to get debug information: {str(e)}")
        return {"error": str(e), "status": "Failed to get debug information"}
