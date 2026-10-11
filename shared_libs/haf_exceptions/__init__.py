"""Project-specific exception hierarchy for the addon distribution.

Usage:
    from _shared_libs.haf_exceptions import HafImportError, HafConfigError

    raise HafConfigError("Missing required field 'deck_id'")
"""

from __future__ import annotations

from .exceptions import (
    HafBaseError,
    HafCompatibilityError,
    HafConfigError,
    HafDeployError,
    HafImportError,
    HafMediaError,
)

__all__ = [
    "HafBaseError",
    "HafCompatibilityError",
    "HafConfigError",
    "HafDeployError",
    "HafImportError",
    "HafMediaError",
]
