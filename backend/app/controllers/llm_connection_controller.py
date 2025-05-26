"""
Controller for LLM connection management.

This controller provides endpoints for managing LLM connections across different providers
(OpenAI, Gemini, LMStudio, Ollama). It serves as the central configuration point for all
LLM interactions in the system, replacing provider-specific configuration.

All other components that need to use LLMs should obtain their configuration through
the active connection managed by this controller.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from ..models.config import (
    LLMConnectionCreate,
    LLMConnectionResponse,
    LLMConnectionUpdate,
)
from ..repository.llm_connection_repository import LLMConnectionRepository

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/connections", tags=["LLM Connections"])


# Helper function to get repository
def get_llm_connection_repo():
    return LLMConnectionRepository()


class DefaultConnectionResponse(BaseModel):
    """Response model for the default connection activation operation."""

    connection_id: str = Field(..., description="ID of the activated connection")
    name: str = Field(..., description="Name of the activated connection")
    provider: str = Field(
        ...,
        description="Provider of the activated connection (openai, gemini, lmstudio, ollama)",
    )


class TestConnectionRequest(BaseModel):
    """Request model for testing an LLM connection configuration before saving it."""

    provider: str = Field(
        "lmstudio", description="Provider type (openai, gemini, lmstudio, ollama)"
    )
    model_name: str = Field(..., description="Name of the model to use")
    base_url: Optional[str] = Field(
        None,
        description="Base URL for API endpoint (provider-specific)",
    )
    api_key: Optional[str] = Field(
        None,
        description="API key (required for OpenAI and Gemini, optional for others)",
    )
    api_version: Optional[str] = Field(
        None, description="API version (used for specific provider versions)"
    )
    prompt: str = Field(
        "Say hello world", description="Test prompt to send to the model"
    )


class TestConnectionResponse(BaseModel):
    """Response model for a connection test."""

    success: bool = Field(..., description="Whether the test was successful")
    response: Optional[str] = Field(None, description="Response from the model")
    error: Optional[str] = Field(None, description="Error message if test failed")


@router.get("/", response_model=List[LLMConnectionResponse])
async def list_connections(
    repo: LLMConnectionRepository = Depends(get_llm_connection_repo),
):
    """Get all configured LLM connections across all providers.

    This endpoint returns all saved connections regardless of their active status.
    The API keys are not returned in the response for security reasons.
    """
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
                config=conn.config_json if conn.config_json else None,
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
    """Create a new LLM connection for any supported provider.

    If the connection is set as active (is_active=true), all other connections
    will be automatically deactivated. Only one connection can be active at a time.
    """
    try:
        connection = await repo.create_connection(
            name=request.name,
            provider=request.provider,
            model_name=request.model_name,
            base_url=request.base_url,
            api_key=request.api_key,
            api_version=request.api_version,
            is_active=request.is_active,
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
    """Set a specific connection as the active one.

    This will deactivate all other connections. The active connection is used
    by all LLM-dependent components throughout the system via get_llm_config().
    """
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
    """Get the currently active LLM connection.

    If no active connection exists, this endpoint will attempt to activate a default
    connection (the first one found). If no connections exist at all, a 404 error
    will be returned.

    All LLM operations in the system use this active connection.
    """
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
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get active connection: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get active connection: {str(e)}"
        )
