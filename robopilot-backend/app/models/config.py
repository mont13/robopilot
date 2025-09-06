"""
Database models for configuration settings.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum

from app.models.base import Base


class ProviderType(str, Enum):
    """Enum for supported LLM providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"


class LLMConnection(Base):
    """Database model for an LLM connection configuration."""

    __tablename__ = "llm_connections"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider = Column(
        SQLAlchemyEnum(ProviderType, native_enum=False),
        nullable=False,
        default=ProviderType.OLLAMA,
    )
    model_name = Column(String(100), nullable=False)
    base_url = Column(String(255), nullable=True)
    api_key = Column(Text, nullable=True)
    api_version = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    # Store additional configuration as JSON
    config_json = Column(Text, nullable=True)  # For storing arbitrary config options


# Pydantic models for API
class LLMConnectionCreate(BaseModel):
    """Schema for creating an LLM connection."""

    name: str = Field(..., description="Display name for this connection")
    provider: ProviderType = Field(
        ..., description="Provider type (openai, gemini, lmstudio, ollama)"
    )
    model_name: str = Field(..., description="Name of the model to use")
    base_url: str | None = Field(None, description="Base URL for API endpoint")
    api_key: str | None = Field(None, description="API key (will be encrypted)")
    api_version: str | None = Field(None, description="API version (for Azure)")
    is_active: bool = Field(False, description="Whether this is the active connection")


class LLMConnectionResponse(BaseModel):
    """Schema for returning an LLM connection."""

    id: str
    name: str
    provider: ProviderType
    model_name: str
    base_url: str | None = None
    api_version: str | None = None
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None
    config: str | None = None


class LLMConnectionUpdate(BaseModel):
    """Schema for updating an LLM connection."""

    name: str | None = None
    provider: ProviderType | None = None
    model_name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    api_version: str | None = None
    is_active: bool | None = None
    config: dict[str, Any] | None = None


class LLMConfig(BaseModel):
    """
    Configuration for an LLM to be used with PraisonAI.
    This is the central configuration model that standardizes
    how we pass LLM settings to the PraisonAI agents.
    """

    model: str
    api_key: str | None = None
    base_url: str | None = None
    api_version: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int | None = 30
    top_p: float | None = 0.9
    response_format: dict[str, str] | None = Field(
        default_factory=lambda: {"type": "text"}
    )
