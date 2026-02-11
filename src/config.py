"""
Application configuration.

All settings are loaded from environment variables (the .env file).
This means the same code works everywhere - only the .env changes:
  - Your laptop: uses your personal API key, debug logging
  - Production server: uses a different key, minimal logging
  - Testing: could use a mock API key
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.

    Each field maps to an environment variable.
    For example, 'openai_api_key' reads from the OPENAI_API_KEY variable.
    Pydantic automatically handles the uppercase/lowercase conversion.
    """

    # Application metadata
    app_name: str = "Meeting Minutes API"
    app_version: str = "1.0.0"
    debug: bool = False

    # OpenAI settings
    openai_api_key: str = ""  # Will be loaded from .env
    openai_model: str = "gpt-4o-mini"  # Good balance of quality and cost
    max_tokens: int = 2000  # Meeting minutes can be long

    # API settings
    max_input_length: int = 50000  # Max characters in meeting notes

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create a single instance - imported everywhere in the app
settings = Settings()
