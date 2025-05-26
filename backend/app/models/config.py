"""
Database models for configuration settings.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Enum as SQLAlchemyEnum, String, Text

from app.models.base import Base


class ProviderType(str, Enum):
    """Enum for supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    LMSTUDIO = "lmstudio"
    OLLAMA = "ollama"


class LLMConnection(Base):
    """Database model for an LLM connection configuration."""

    __tablename__ = "llm_connections"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider = Column(
        SQLAlchemyEnum(ProviderType, native_enum=False),
        nullable=False,
        default=ProviderType.LMSTUDIO
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
    base_url: Optional[str] = Field(None, description="Base URL for API endpoint")
    api_key: Optional[str] = Field(None, description="API key (will be encrypted)")
    api_version: Optional[str] = Field(None, description="API version (for Azure)")
    is_active: bool = Field(False, description="Whether this is the active connection")



class LLMConnectionResponse(BaseModel):
    """Schema for returning an LLM connection."""

    id: str
    name: str
    provider: ProviderType
    model_name: str
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    config: Optional[str] = None


class LLMConnectionUpdate(BaseModel):
    """Schema for updating an LLM connection."""

    name: Optional[str] = None
    provider: Optional[ProviderType] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_version: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class LLMConfig(BaseModel):
    """
    Configuration for an LLM to be used with PraisonAI.
    This is the central configuration model that standardizes
    how we pass LLM settings to the PraisonAI agents.
    """

    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: Optional[int] = 30
    top_p: Optional[float] = 0.9
    response_format: Optional[Dict[str, str]] = Field(
        default_factory=lambda: {"type": "text"}
    )
