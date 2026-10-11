"""Shared libraries for Anki Torah addon distribution.

This package is deployed as _shared_libs in the addons21 directory.
Addons should import from here instead of bundling their own copies.

Usage from an addon:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "_shared_libs"))
    from pyluach.dates import HebrewDate
"""
