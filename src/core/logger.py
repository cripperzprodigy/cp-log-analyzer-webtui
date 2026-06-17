"""
Structured logging setup for the application using structlog.
"""

import logging
import sys
import structlog


def setup_logger() -> structlog.BoundLogger:
    """
    Configures and returns a structured logger.

    Returns:
        structlog.BoundLogger: The configured logger instance.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),  # Renders nice colored logs for the terminal
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    return structlog.get_logger()


logger = setup_logger()
