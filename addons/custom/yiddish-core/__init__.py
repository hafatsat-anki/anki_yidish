"""Anki 25.09.2 native Yiddish distribution companion."""

from __future__ import annotations

import aqt
import anki.lang
from _shared_libs.haf_logging import get_logger

logger = get_logger(__name__)


def _verify_yiddish() -> None:
    from aqt.yiddish import install_qt, verify_native

    if anki.lang.current_lang != "yi":
        raise RuntimeError("די ווערסיע דארף געעפנט ווערן מיט דער יידישער שפראך.")
    verify_native(anki.lang.current_i18n)
    install_qt(aqt.mw.app)
    logger.info("Native Yiddish locale initialized successfully")


_verify_yiddish()
