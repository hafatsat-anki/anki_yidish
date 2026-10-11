"""Hebrew labels for Qt WebEngine's native touch selection popup."""

from aqt.qt import QApplication, QTranslator


# #404 — TouchSelectionMenuWidget has no Q_OBJECT: its tr() inherits the
# QWidget context, independently of QWebEnginePage actions/context menus.
class TouchSelectionTranslator(QTranslator):
    def isEmpty(self):
        return False

    def translate(self, context, source_text, disambiguation=None, n=-1):
        if context == "QWidget":
            return {"Cut": "שנייד", "Copy": "קאפיר", "Paste": "לייג אריין"}.get(source_text)
        return None


def install():
    # #404 — Keep the translator alive for the application lifetime. Native
    # callbacks, touch handles, focus and day/night palettes remain untouched.
    app = QApplication.instance()
    if app is not None and not hasattr(app, "_haf_touch_selection_translator"):
        translator = TouchSelectionTranslator(app)
        app.installTranslator(translator)
        app._haf_touch_selection_translator = translator
