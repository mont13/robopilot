"""
LLM Configuration utility for BeeAI integration.

This module provides utilities for obtaining LLM configuration from the database
using the proper config.py models. Supports only Ollama and OpenAI providers.
No environment variables are used - all configuration comes from the database.
"""

from typing import Any

from ..models.config import LLMConfig, ProviderType


async def get_llm_config() -> dict[str, Any]:
    """
    Get the LLM configuration from the active connection in the database.
    Uses the proper config.py models and supports only Ollama and OpenAI providers.
    Does not read any environment variables.

    Returns:
        Dict[str, Any]: LLM configuration dictionary for Ollama or OpenAI

    Raises:
        ValueError: If no active LLM connection is found in the database
        ValueError: If provider is not supported (only Ollama and OpenAI)
    """
    import logging

    logger = logging.getLogger(__name__)

    # Import here to avoid circular imports
    from ..repository.llm_connection_repository import LLMConnectionRepository

    # Get repository
    repo = LLMConnectionRepository()

    # Get active connection
    connection = await repo.get_active_connection()

    if not connection:
        logger.error("No active LLM connection found in database")
        raise ValueError(
            "No active LLM connection found. Please configure an LLM connection and set it as active."
        )

    # Log connection details for debugging
    logger.info(f"Active LLM connection found: {connection.name}")
    logger.info(f"Provider: {connection.provider.value}")
    logger.info(f"Model: {connection.model_name}")
    logger.info(f"Base URL: {connection.base_url}")

    # Only support Ollama and OpenAI providers
    if connection.provider not in [ProviderType.OLLAMA, ProviderType.OPENAI]:
        logger.error(f"Unsupported provider: {connection.provider}")
        raise ValueError(
            f"Unsupported provider: {connection.provider}. Only 'ollama' and 'openai' are supported."
        )

    # Use full model name as-is for BeeAI adapters
    model_name = connection.model_name
    logger.info(f"Using model name: {model_name}")

    # Build configuration dictionary
    llm_config = {
        "model": model_name,
        "provider": connection.provider.value,
        "temperature": 0.7,
        "max_tokens": 4096,
        "timeout": 30,
    }

    # Add provider-specific configuration
    if connection.provider == ProviderType.OLLAMA:
        # Ollama configuration
        base_url = connection.base_url or "http://localhost:11434"
        llm_config["base_url"] = base_url
        logger.info(f"Ollama config - Model: {model_name}, Base URL: {base_url}")
    elif connection.provider == ProviderType.OPENAI:
        # OpenAI configuration
        if connection.api_key:
            llm_config["api_key"] = connection.api_key
            logger.info(
                f"OpenAI config - Model: {model_name}, API key present: {bool(connection.api_key)}"
            )
        if connection.base_url:
            llm_config["base_url"] = connection.base_url
            logger.info(f"OpenAI config - Custom base URL: {connection.base_url}")
        if connection.api_version:
            llm_config["api_version"] = connection.api_version
            logger.info(f"OpenAI config - API version: {connection.api_version}")

    logger.info(
        f"Final LLM config created successfully for {connection.provider.value}"
    )
    return llm_config


def connection_to_beeai_config(connection) -> LLMConfig:
    """
    Convert a database LLMConnection to a BeeAI-compatible LLMConfig.

    Args:
        connection: LLMConnection database model instance

    Returns:
        LLMConfig: Pydantic model for BeeAI framework usage

    Raises:
        ValueError: If provider is not supported
    """
    if connection.provider not in [ProviderType.OLLAMA, ProviderType.OPENAI]:
        raise ValueError(
            f"Unsupported provider: {connection.provider}. Only 'ollama' and 'openai' are supported."
        )

    # Use full model name as-is for BeeAI adapters
    model_name = connection.model_name

    # Build LLMConfig
    config_data = {
        "model": model_name,
        "temperature": 0.7,
        "max_tokens": 4096,
        "timeout": 30,
    }

    # Add provider-specific fields
    if connection.api_key:
        config_data["api_key"] = connection.api_key
    if connection.base_url:
        config_data["base_url"] = connection.base_url
    if connection.api_version:
        config_data["api_version"] = connection.api_version

    return LLMConfig(**config_data)
