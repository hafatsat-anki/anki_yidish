"""Central logger configuration for the addon distribution.

All addon loggers are children of the 'haf' root logger.
Configuration is loaded from config/logging.json if present,
otherwise sensible defaults are used.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path

_ROOT_LOGGER_NAME = "haf"
_LOG_FILENAME = "haf_addons.log"
_configured = False
_log_file_path: Path | None = None
_recent_messages: deque[str] = deque(maxlen=300)
_MAX_RECENT_MESSAGE_CHARS = 12000


class _RecentHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            if len(message) > _MAX_RECENT_MESSAGE_CHARS:
                message = message[:_MAX_RECENT_MESSAGE_CHARS] + "\n[Recent diagnostics shortened; full record is in the log file when available.]"
            _recent_messages.append(message)
        except Exception:
            _recent_messages.append("Diagnostic record could not be formatted.")


class _ConsoleHandler(logging.StreamHandler):
    def handleError(self, record: logging.LogRecord) -> None:
        # Logging failures must not create Anki's stderr error dialog. The
        # original record remains available in the bounded in-memory log.
        pass


class _FileHandler(RotatingFileHandler):
    def handleError(self, record: logging.LogRecord) -> None:
        # A locked/full log file is a diagnostic failure, not a second crash.
        pass

    def close(self) -> None:
        try:
            super().close()
        except OSError:
            # Closing/reconfiguring a diagnostic file must also stay quiet.
            logging.Handler.close(self)


def _resolve_anki2_dir() -> Path | None:
    aqt = sys.modules.get("aqt")
    profile_manager = getattr(getattr(aqt, "mw", None), "pm", None)
    base = getattr(profile_manager, "base", None)
    if isinstance(base, (str, os.PathLike)) and base:
        return Path(base)
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Anki2"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Anki2"
    else:
        return Path.home() / ".local" / "share" / "Anki2"
    return None


def _resolve_log_path(config_value: str) -> Path | None:
    if config_value == "auto":
        anki2_dir = _resolve_anki2_dir()
        if anki2_dir and anki2_dir.exists():
            return anki2_dir / _LOG_FILENAME
        return None

    return Path(config_value).expanduser()


def _find_config_file() -> Path | None:
    candidates = [
        Path(__file__).resolve().parents[2] / "config" / "logging.json",
        Path(__file__).resolve().parents[3] / "config" / "logging.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _apply_defaults(root_logger: logging.Logger) -> None:
    # Installed addons do not carry the repository's config/logging.json.
    # Keep a persistent diagnostic log in that case as well.
    _apply_config(root_logger, {
        "level": os.environ.get("HAF_LOG_LEVEL", "WARNING"),
        "file": "auto",
        "file_level": "INFO",
    })


def _apply_config(root_logger: logging.Logger, config: dict) -> None:
    global _log_file_path

    _log_file_path = None
    for handler in list(root_logger.handlers):
        if isinstance(handler, (_RecentHandler, _ConsoleHandler, _FileHandler)):
            root_logger.removeHandler(handler)
            handler.close()
        elif isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            if handler.stream in (sys.stderr, sys.__stderr__):
                root_logger.removeHandler(handler)
    # Root handlers belong to Anki/other addons and may write to stderr.
    # Only our own addon diagnostic log is isolated; uncaught exceptions keep
    # Anki's normal error handling and sys.excepthook.
    root_logger.propagate = False

    level_str = str(config.get("level", "WARNING"))
    level = getattr(logging, level_str.upper(), logging.WARNING)
    root_logger.setLevel(level)

    fmt = config.get("format", "[%(name)s] %(levelname)s: %(message)s")

    recent_handler = _RecentHandler()
    recent_handler.setFormatter(logging.Formatter(fmt))
    root_logger.addHandler(recent_handler)
    if sys.stdout is not None:
        handler = _ConsoleHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(fmt))
        root_logger.addHandler(handler)

    log_file_value = config.get("file")
    if log_file_value:
        file_path = _resolve_log_path(log_file_value)
        if file_path:
            max_bytes = config.get("max_bytes", 5 * 1024 * 1024)
            backup_count = config.get("backup_count", 2)
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = _FileHandler(
                    str(file_path),
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
            except OSError:
                root_logger.warning("Diagnostic log file is unavailable; keeping console and recent diagnostics.", exc_info=True)
                return
            file_fmt = config.get("file_format", fmt)
            file_handler.setFormatter(logging.Formatter(file_fmt))
            file_level_str = str(config.get("file_level", level_str))
            file_handler.setLevel(
                getattr(logging, file_level_str.upper(), level)
            )
            root_logger.addHandler(file_handler)
            # Filtering only on the logger would drop INFO/DEBUG records
            # before the file handler can receive them.
            root_logger.setLevel(min(level, file_handler.level))
            _log_file_path = file_path


def configure_logging(config: dict | None = None) -> None:
    """Configure the haf root logger.

    Can be called explicitly with a config dict, or will auto-configure
    from config/logging.json or environment variables on first use.
    """
    global _configured
    root_logger = logging.getLogger(_ROOT_LOGGER_NAME)

    if config is not None:
        _apply_config(root_logger, config)
        _configured = True
        return

    config_file = _find_config_file()
    if config_file:
        try:
            with open(config_file, encoding="utf-8") as f:
                file_config = json.load(f)
            if not isinstance(file_config, dict):
                raise ValueError("Logging settings must be a JSON object")
            _apply_config(root_logger, file_config)
        except (OSError, ValueError, TypeError):
            _apply_defaults(root_logger)
            root_logger.warning("Diagnostic logging settings could not be loaded; using defaults.", exc_info=True)
    else:
        _apply_defaults(root_logger)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named child logger under the haf root.

    Auto-configures on first call if not already configured.
    """
    if not _configured:
        configure_logging()
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")


def get_log_file_path() -> Path | None:
    """Return the path to the active log file, or None if file logging is disabled."""
    if not _configured:
        configure_logging()
    return _log_file_path


def get_recent_log_text() -> str:
    """Bounded diagnostics for an explicitly requested support report."""
    if not _configured:
        configure_logging()
    return "\n".join(tuple(_recent_messages))
