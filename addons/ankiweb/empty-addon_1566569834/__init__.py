import time

import aqt.preferences
from anki.hooks import wrap
from aqt import gui_hooks, mw
from aqt.qt import QCheckBox, QHBoxLayout, QLabel, QKeySequence, QSpinBox
from aqt.reviewer import Reviewer
from aqt.utils import qconnect, tooltip


def _config() -> dict:
    return mw.addonManager.getConfig(__name__) or {}


def _write_config(key: str, value) -> None:
    config = _config()
    config[key] = value
    mw.addonManager.writeConfig(__name__, config)


def _shortcut() -> str:
    return str(_config().get("shortcut", "") or "").strip()


def _wait_enabled() -> bool:
    return bool(_config().get("mandatory_wait_enabled", False))


def _wait_seconds() -> int:
    try:
        return max(1, min(60, int(_config().get("mandatory_wait_seconds", 2) or 2)))
    except Exception:
        return 2


def _add_hide_answer_entry(reviewer: Reviewer, menu) -> None:
    # #273 — hook מודרני במקום Reviewer.contextMenuEvent הישן כדי שהתוסף יעבוד ב-Anki 25.
    action = menu.addAction("באהאלט די תשובה")
    shortcut = _shortcut()
    if shortcut:
        action.setShortcut(QKeySequence(shortcut))
    qconnect(action.triggered, reviewer._showQuestion)


def _shortcut_keys(self: Reviewer, _old):
    shortcuts = _old(self)
    shortcut = _shortcut()
    if shortcut:
        # #273 — שומרים את קיצור "הסתר תשובה" הקיים בלי להשתמש ב-hook מיושן.
        shortcuts.append((QKeySequence(shortcut), lambda: self._showQuestion()))
    return shortcuts


def _on_question_shown(card) -> None:
    if not _wait_enabled() or not getattr(mw, "reviewer", None):
        return
    seconds = _wait_seconds()
    reviewer = mw.reviewer
    # #273 — זמן המוכנות נשמר ב-Reviewer כדי שגם קיצור מקלדת וגם כפתור ans ייחסמו עד סוף ההמתנה.
    reviewer._haf_answer_ready_at = time.monotonic() + seconds
    reviewer.web.eval(f"""
        (function(seconds) {{
            var btn = document.getElementById("ansbut");
            if (!btn) return;
            var original = btn.getAttribute("data-haf-original-text") || btn.textContent || "ווייזט די תשובה";
            btn.setAttribute("data-haf-original-text", original);
            btn.disabled = true;
            btn.style.pointerEvents = "none";
            btn.style.opacity = "0.55";
            var remaining = seconds;
            function render() {{
                btn.textContent = original + " (" + remaining + ")";
            }}
            render();
            var timer = window.setInterval(function() {{
                remaining -= 1;
                if (remaining <= 0) {{
                    window.clearInterval(timer);
                    btn.disabled = false;
                    btn.style.pointerEvents = "";
                    btn.style.opacity = "";
                    btn.textContent = original;
                    return;
                }}
                render();
            }}, 1000);
        }})({seconds});
    """)


def _show_answer_with_wait(self: Reviewer, _old):
    if _wait_enabled():
        ready_at = float(getattr(self, "_haf_answer_ready_at", 0) or 0)
        remaining = ready_at - time.monotonic()
        if remaining > 0:
            # #273 — חסימת הצגת התשובה נעשית בשכבת Reviewer כדי שגם מקלדת לא תעקוף את הכפתור המושבת.
            tooltip(f"מען קען ווייזן די תשובה אין נאך {int(remaining) + 1} סעקונדעס")
            return None
    return _old(self)


def _on_wait_checkbox_changed(state) -> None:
    _write_config("mandatory_wait_enabled", bool(state))


def _on_wait_seconds_changed(value: int) -> None:
    _write_config("mandatory_wait_seconds", int(value))




def _add_preferences(preferences_dialog: aqt.preferences.Preferences) -> None:
    # #273 — ההפעלה נמצאת בהעדפות Anki וברירת המחדל כבויה כדי לא לשנות התנהגות קיימת ללא בחירה.
    row = QHBoxLayout()
    checkbox = QCheckBox("ווארט צייט איידער מען ווייזט די תשובה")
    checkbox.setChecked(_wait_enabled())
    qconnect(checkbox.stateChanged, _on_wait_checkbox_changed)
    row.addWidget(checkbox)

    row.addWidget(QLabel("סעקונדעס:"))
    seconds = QSpinBox()
    seconds.setRange(1, 60)
    seconds.setValue(_wait_seconds())
    qconnect(seconds.valueChanged, _on_wait_seconds_changed)
    row.addWidget(seconds)
    row.addStretch()

    preferences_dialog.form.verticalLayout_5.addLayout(row)


gui_hooks.reviewer_will_show_context_menu.append(_add_hide_answer_entry)
gui_hooks.reviewer_did_show_question.append(_on_question_shown)
Reviewer._shortcutKeys = wrap(Reviewer._shortcutKeys, _shortcut_keys, "around")
Reviewer._showAnswer = wrap(Reviewer._showAnswer, _show_answer_with_wait, "around")

# #273 — תיבת ההפעלה מתווספת ללשונית החזרה של חלון ההעדפות.
aqt.preferences.Preferences.setup_global = wrap(
    aqt.preferences.Preferences.setup_global,
    _add_preferences,
    "after",
)
