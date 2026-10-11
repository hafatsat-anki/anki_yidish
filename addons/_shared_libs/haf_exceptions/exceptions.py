"""Exception hierarchy for the Anki Torah addon distribution."""

from __future__ import annotations


class HafBaseError(Exception):
    """Base exception for all haf addon errors."""


class HafConfigError(HafBaseError):
    """Raised when addon configuration is invalid or missing."""


class HafCompatibilityError(HafBaseError):
    """Raised when an Anki version incompatibility is detected."""


class HafImportError(HafBaseError):
    """Raised when CSV/file import operations fail."""


class HafDeployError(HafBaseError):
    """Raised when addon deployment encounters an error."""


class HafMediaError(HafBaseError):
    """Raised when media file operations fail (missing, corrupt, etc.)."""
