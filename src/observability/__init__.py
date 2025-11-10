"""Observability package for structured logging and metrics."""

from .logging_config import get_logger, setup_logging

__all__ = ["setup_logging", "get_logger"]
