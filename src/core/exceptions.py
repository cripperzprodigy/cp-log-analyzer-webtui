"""
Exception hierarchy for the Log Analyzer application.
"""


class LogAnalyzerError(Exception):
    """Base exception for the application."""

    pass


class ConfigurationError(LogAnalyzerError):
    """Raised when there is an issue with the application configuration."""

    pass


class VFSError(LogAnalyzerError):
    """Base exception for Virtual File System errors."""

    pass


class VFSConnectionError(VFSError):
    """Raised when a remote VFS connection cannot be established."""

    pass


class AIError(LogAnalyzerError):
    """Base exception for AI Agent errors."""

    pass


class AIProviderError(AIError):
    """Raised when the AI provider (Litellm/OpenAI/Ollama) returns an error."""

    pass


class AISearchError(AIError):
    """Raised when the AI fails to execute a search properly."""

    pass
