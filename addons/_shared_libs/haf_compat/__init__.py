"""Anki version compatibility checker for the Torah addon distribution.

Reads config/anki_compatibility.json relative to the distribution root
and provides utilities to check addon compatibility at runtime.
"""

from __future__ import annotations

from .version_checker import VersionChecker, check_compatibility

__all__ = ["VersionChecker", "check_compatibility"]
