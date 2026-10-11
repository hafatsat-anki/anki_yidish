"""Give the inline editor ownership of keys before Qt window shortcuts fire."""
import json

from aqt.qt import QEvent, QObject, QWidget, QKeySequence, Qt


def editing_shortcuts(config):
    if isinstance(config, str):
        config = json.loads(config)
    yield from config.get("shortcuts", {}).values()
    yield from config.get("review_preset_shortcuts", {}).values()
    for row in config.get("special_formatting", {}).values():
        if row.get("command"):
            yield row.get("shortcut", "")


def physical_shortcut(value):
    letters = dict(zip("שנבגקכעיןחלךצמםפ/רדאוה'סטז", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    parts = str(value).replace(" ", "").split("+")
    parts[-1] = letters.get(parts[-1], parts[-1])
    return QKeySequence("+".join(parts)).toString().upper()


class InlineEditingShortcutGuard(QObject):
    def __init__(self, mw, config):
        super().__init__(mw)
        self.mw = mw
        self.editing = False
        self.config = config

    def eventFilter(self, receiver, event):
        if not self.editing or self.mw.state != "review":
            return False
        if event.type() != QEvent.Type.ShortcutOverride:
            return False
        web = getattr(getattr(self.mw, "reviewer", None), "web", None)
        if web is None or not isinstance(receiver, QWidget):
            return False
        if receiver is not web and not web.isAncestorOf(receiver):
            return False
        sequence = physical_shortcut(QKeySequence(event.keyCombination()).toString())
        managed = {physical_shortcut(value) for value in editing_shortcuts(self.config()) if value}
        typing = (bool(event.text()) and not event.modifiers() & (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier))
        if sequence not in managed and not typing:
            return False
        # Accept only the override. The actual key event continues to WebEngine,
        # where formatting, presets, clipboard commands and typing are handled.
        event.accept()
        return True

    def reset(self, *args):
        self.editing = False
