from __future__ import annotations

from aqt import gui_hooks, mw
from aqt.qt import QTimer, QWebEnginePage


_warm_page = None
_warm_done = False


def _finish_warmup(*_args) -> None:
    """לאזט פריי דעם אויפווארעם בלאט נאכדעם וואס דער מאטאר-Web האט פארענדיגט דאס אנהייבן."""
    global _warm_page, _warm_done
    page = _warm_page
    _warm_page = None
    _warm_done = True
    if page is not None:
        page.deleteLater()


def _warm_webengine() -> None:
    """צינדט אן דעם Chromium נאכן עפענען דעם פראפיל, אן צו שאפן א זעבארן פענסטער."""
    global _warm_page
    if _warm_done or _warm_page is not None:
        return
    try:
        page = QWebEnginePage(mw)
        _warm_page = page
        page.loadFinished.connect(_finish_warmup)
        page.setHtml("<html><body></body></html>")
    except Exception:
        _finish_warmup()


def _schedule_webengine_warmup() -> None:
    # ההשהיה הקצרה נותנת למסך הראשי להצטייר קודם; החימום עצמו אסינכרוני.
    QTimer.singleShot(250, _warm_webengine)


gui_hooks.profile_did_open.append(_schedule_webengine_warmup)
