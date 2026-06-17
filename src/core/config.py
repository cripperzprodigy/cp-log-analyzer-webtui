"""
Configuration management using Pydantic for strong typing and validation.
"""

import yaml
from pydantic import BaseModel, Field
from typing import Optional

from src.core.logger import logger
from src.core.exceptions import ConfigurationError


class AIConfig(BaseModel):
    model: str = Field(
        default="",
        description="The LiteLLM routing model string (e.g., 'openai/gpt-4o', 'ollama/llama3')",
    )
    api_base: str = Field(default="", description="The base URL for the API provider")
    api_key: str = Field(default="", description="The API key for the provider")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)


class SearchConfig(BaseModel):
    chunk_size_bytes: int = Field(default=1048576, ge=1024)


class WebConfig(BaseModel):
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000, ge=1, le=65535)


class AppConfig(BaseModel):
    ai: AIConfig = Field(default_factory=AIConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    web: WebConfig = Field(default_factory=WebConfig)


def load_config(path: str = "config.yaml") -> AppConfig:
    """
    Loads and validates the configuration from a YAML file.

    Args:
        path (str): The path to the configuration file.

    Returns:
        AppConfig: The validated configuration object.

    Raises:
        ConfigurationError: If the config file cannot be read or fails validation.
    """
    try:
        with open(path, "r") as f:
            raw_config = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("config_load_failed", path=path, error=str(e))
        raw_config = {}

    try:
        return AppConfig(**raw_config)
    except Exception as e:
        logger.error("config_validation_failed", error=str(e))
        raise ConfigurationError(f"Failed to validate config.yaml: {e}")


# Global configuration instance
config = load_config()
