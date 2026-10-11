"""Qt bootstrapping used by this distribution before add-ons are loaded."""

from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from aqt.qt import QTranslator, Qt

_translator: QTranslator | None = None
NATIVE_CATALOG_SHA256 = "411232b61b96088b534016b9f52b00240470b4062e0f4adb8940e66786aca8d9"


class YiddishQtTranslator(QTranslator):
    def __init__(self) -> None:
        super().__init__()
        self.messages = json.loads(Path(__file__).with_name("yiddish_qt.json").read_text(encoding="utf-8"))

    def isEmpty(self) -> bool:
        return False

    def translate(self, context: str, source: str, disambiguation: str | None = None, n: int = -1) -> str | None:
        # The catalog intentionally includes only Qt-owned strings. Never translate
        # arbitrary collection data or an add-on's contractual identifiers.
        if not context.startswith(("Q", "MAC_APPLICATION_MENU")):
            return None
        value = self.messages.get(source)
        if value is None:
            return None
        if n >= 0:
            value = value.replace("%n", str(n))
        return value


def install_qt(app) -> None:
    global _translator
    if _translator is not None:
        return
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    _translator = YiddishQtTranslator()
    if not app.installTranslator(_translator):
        raise RuntimeError("מען האט נישט געקענט איינלאדן די יידישע Qt־תרגומים.")
    app.setProperty("ankiYiddishQtInitializedBeforeAddons", True)


def verify_native(backend) -> None:
    from anki._fluent import LegacyTranslationEnum

    resources = json.loads(backend.i18n_resources(modules=[]))
    if not resources["langs"] or resources["langs"][0] != "yi":
        raise RuntimeError("דער אנקי־מנוע נוצט נישט די יידישע שפראך. ביטע אינסטאלירט די יידישע ווערסיע פונדאסניי.")
    text = resources["resources"][0] if resources["resources"] else ""
    matches = list(re.finditer(r"^(-?[a-zA-Z][\w-]*)\s*=", text, re.MULTILINE))
    entries = {
        m.group(1): text[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)].strip()
        for i, m in enumerate(matches)
    }
    digest = hashlib.sha256(json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if digest != NATIVE_CATALOG_SHA256 or len(entries) != 1733:
        raise RuntimeError("דער יידישער אנקי־מנוע איז נישט פולשטענדיג. ביטע אינסטאלירט די יידישע ווערסיע פונדאסניי.")
    value = backend.translate(*LegacyTranslationEnum.ACTIONS_ADD)
    cancel = backend.translate(*LegacyTranslationEnum.ACTIONS_CANCEL)
    if value != "צולייגן" or cancel != "אפזאגן":
        raise RuntimeError("דער יידישער אנקי־מנוע איז נישט אינסטאלירט ריכטיג. ביטע אינסטאלירט די יידישע ווערסיע פונדאסניי.")
