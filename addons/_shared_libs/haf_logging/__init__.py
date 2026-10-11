"""Centralized logging for the Anki Torah addon distribution.

Usage from any addon:
    from _shared_libs.haf_logging import get_logger
    logger = get_logger("my_addon")
    logger.info("Started")
    logger.debug("Detail: %s", value)
    logger.error("Failed: %s", err)
"""

from __future__ import annotations

from .logger import configure_logging, get_log_file_path, get_logger, get_recent_log_text

__all__ = ["get_logger", "configure_logging", "get_log_file_path", "get_recent_log_text"]
