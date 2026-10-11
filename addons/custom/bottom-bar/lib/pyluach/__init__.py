"""Redirect to shared pyluach library in _shared_libs."""
import sys
from pathlib import Path

_shared_libs = str(Path(__file__).parents[3] / "_shared_libs")
if _shared_libs not in sys.path:
    sys.path.insert(0, _shared_libs)

from pyluach import *
from pyluach import dates, gematria, hebrewcal, parshios, utils

_pkg = __name__
for _mod_name, _mod in [("dates", dates), ("gematria", gematria),
                         ("hebrewcal", hebrewcal), ("parshios", parshios),
                         ("utils", utils)]:
    sys.modules[f"{_pkg}.{_mod_name}"] = _mod
