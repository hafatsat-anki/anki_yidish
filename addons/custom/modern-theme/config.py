from aqt import gui_hooks, mw
from aqt.qt import QEvent, QObject, QTimer, Qt, sip


_BROWSER_SIDEBAR_WIDTH_KEY = "modern_theme.browser_sidebar_width"


def get_config():
    # #419 — addonManager עשוי להחזיר None בפרופיל חדש; שאר התוסף מצפה תמיד למילון.
    return mw.addonManager.getConfig(__name__) or {}


def write_config():
    return mw.addonManager.writeConfig(__name__, config)


# אישיו #401: שומרים את רוחב סרגל הצד בזמן שינוי הגודל ומשחזרים אותו רק אחרי
# שה-Browser של Anki השלים את שחזור המצב המובנה שלו. אין עטיפה של __init__,
# closeEvent או _closeWindow, ולכן התוסף אינו מתערב במחזור חיי חלון הדפדוף.
class _BrowserSidebarWidthTracker(QObject):
    def __init__(self, browser) -> None:
        super().__init__(browser)
        self.browser = browser
        self.dock = getattr(browser, "sidebarDockWidget", None)
        self._tracking = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(200)
        self._save_timer.timeout.connect(self._save_now)
        if self.dock is not None:
            self.dock.installEventFilter(self)
        QTimer.singleShot(0, self._restore)

    def _profile(self) -> dict | None:
        profile = getattr(mw.pm, "profile", None)
        return profile if isinstance(profile, dict) else None

    def _restore(self) -> None:
        if self.dock is None:
            return
        profile = self._profile()
        if profile is None:
            return
        try:
            width = int(profile.get(_BROWSER_SIDEBAR_WIDTH_KEY, 0) or 0)
        except (TypeError, ValueError):
            width = 0
        if width > 0:
            try:
                self.browser.resizeDocks(
                    [self.dock],
                    [width],
                    Qt.Orientation.Horizontal,
                )
            except RuntimeError:
                return
        QTimer.singleShot(0, self._enable_tracking)

    def _enable_tracking(self) -> None:
        self._tracking = True

    def eventFilter(self, watched, event):  # noqa: N802 - שם API של Qt
        if (
            self._tracking
            and watched is self.dock
            and event.type() == QEvent.Type.Resize
            and self.dock is not None
            and self.dock.isVisible()
        ):
            self._save_timer.start()
        return super().eventFilter(watched, event)

    def _save_now(self) -> None:
        if self.dock is None or sip.isdeleted(self.dock):
            return
        try:
            width = int(self.dock.width())
            profile = self._profile()
            if width <= 0 or profile is None:
                from _shared_libs.haf_notifications import warn_once
                warn_once("sidebar:invalid-state", "די זייט סרגל ברייט איז נישט אפגעזיכערט געווארן, ווייל די ברייט אדער דער פראפיל זענען נישט גרייט.")
                return
            if int(profile.get(_BROWSER_SIDEBAR_WIDTH_KEY, 0) or 0) == width:
                return
            profile[_BROWSER_SIDEBAR_WIDTH_KEY] = width
            mw.pm.save()
        except (RuntimeError, TypeError, ValueError):
            from _shared_libs.haf_notifications import warn_once
            warn_once('addons/custom/modern-theme/config.py:_save_now', 'די זייט סרגל ברייט איז נישט אפגעזיכערט געווארן. ביים קומענדיגן עפענען קען דער פריערדיגער ברייט זיך ווייזן.')
            return


def _install_browser_sidebar_width_persistence(browser) -> None:
    if getattr(browser, "_haf_sidebar_width_tracker", None) is not None:
        return
    browser._haf_sidebar_width_tracker = _BrowserSidebarWidthTracker(browser)


gui_hooks.browser_will_show.append(_install_browser_sidebar_width_persistence)


config = get_config()
