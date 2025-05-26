import os


async def get_llm_config():
    """
    Get the LLM configuration from the active connection in the database.
    This is the central point for obtaining LLM configuration for all providers.

    If no active connection exists, an exception is raised.

    Returns:
        Dict[str, Any]: LLM configuration dictionary with standardized parameters
        that can be used with any supported provider (OpenAI, Gemini, LMStudio, Ollama)

    Raises:
        ValueError: If no active LLM connection is found in the database
    """
    # Import here to avoid circular imports
    from ...repository.llm_connection_repository import LLMConnectionRepository

    # Get repository
    repo = LLMConnectionRepository()

    # Get active connection
    connection = await repo.get_active_connection()

    if connection:
        # Log the provider being used
        os.environ["OPENAI_API_KEY"] = connection.api_key
        os.environ["OPENAI_BASE_URL"] = connection.base_url
        os.environ["OPENAI_MODEL"] = connection.model_name

        llm_config = {
            "model": connection.model_name,  # Model name without provider prefix
            # Core settings
            "temperature": 0.7,  # Controls randomness (like temperature)
            "timeout": 30,  # Timeout in seconds
            "top_p": 0.9,  # Nucleus sampling parameter
            "max_tokens": 4096,  # Max tokens in response
            # API settings (optional)
            "api_key": connection.api_key,
            "api_version": connection.api_version,  # Your API key (or use environment variable)
            "base_url": connection.base_url,  # Custom API endpoint if needed
            # Response formatting
            "response_format": {  # Force specific response format
                "type": "text"  # Options: "text", "json_object"
            },
        }

        return llm_config
    else:
        error_msg = "No active LLM connection found. Please configure an LLM connection and set it as active."
        raise ValueError(error_msg)
