"""
Add Table - צולייגן א טאבעלע אינעם רעדאקטירער
לייגט צו א קנעפל אין דער רעדאקטירער סרגל, וואס עפנט א פענסטער אויסצוקלייבן וויפיל שורות און שפאלטן,
צולייגן א קעפל און אויסריכטן — און לייגט אריין א טאבעלע HTML אינעם פעלד.
"""
import json
import os

from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.qt import (
    Qt,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QKeySequence,
    QShortcut,
    QSpinBox,
    QTimer,
    QVBoxLayout,
)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULT_CONFIG = {
    "rows": 3,
    "cols": 3,
    "header": True,
    "align": "right",
    "shortcut": "Ctrl+0",
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except (OSError, json.JSONDecodeError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


config = load_config()


class TableDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("צולייגן א טאבעלע")
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100)
        self.rows_spin.setValue(int(config.get("rows", 3)))
        form.addRow("שורות:", self.rows_spin)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 50)
        self.cols_spin.setValue(int(config.get("cols", 3)))
        form.addRow("שפאלטן:", self.cols_spin)

        self.header_cb = QCheckBox("קעפל שורה")
        self.header_cb.setChecked(bool(config.get("header", True)))
        form.addRow("", self.header_cb)

        self.align_combo = QComboBox()
        self.align_combo.addItem("רעכטס", "right")
        self.align_combo.addItem("אין מיטן", "center")
        self.align_combo.addItem("לינקס", "left")
        idx = self.align_combo.findData(config.get("align", "right"))
        if idx >= 0:
            self.align_combo.setCurrentIndex(idx)
        form.addRow("אויסריכטונג:", self.align_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {
            "rows": self.rows_spin.value(),
            "cols": self.cols_spin.value(),
            "header": self.header_cb.isChecked(),
            "align": self.align_combo.currentData(),
        }


def build_table_html(rows: int, cols: int, header: bool, align: str) -> str:
    border_style = "border:1px solid #888;padding:4px;"
    table_style = (
        "border-collapse:collapse;"
        f"text-align:{align};"
        "margin:6px 0;"
        "min-width:50%;"
    )
    parts = [f'<table dir="rtl" style="{table_style}"><tbody>']
    if header:
        cells = "".join(
            f'<th style="{border_style}font-weight:bold;background:#f0f0f0;">&nbsp;</th>'
            for _ in range(cols)
        )
        parts.append(f"<tr>{cells}</tr>")
        body_rows = max(0, rows - 1)
    else:
        body_rows = rows
    for _ in range(body_rows):
        cells = "".join(f'<td style="{border_style}">&nbsp;</td>' for _ in range(cols))
        parts.append(f"<tr>{cells}</tr>")
    parts.append("</tbody></table><br>")
    return "".join(parts)


def insert_table(editor) -> None:
    parent = editor.parentWindow if hasattr(editor, "parentWindow") else None
    dlg = TableDialog(parent)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return
    vals = dlg.values()
    config.update(vals)
    save_config(config)
    html = build_table_html(vals["rows"], vals["cols"], vals["header"], vals["align"])
    editor.web.eval(
        f"document.execCommand('insertHTML', false, {json.dumps(html)});"
    )


def _add_button(buttons: list, editor) -> list:
    btn = editor.addButton(
        None,
        "AddTable",
        insert_table,
        tip=f"צולייגן א טאבעלע ({config.get('shortcut', 'Ctrl+0')})",
        label="⊞",
        # #379 — create the toolbar HTML now and the QShortcut only after the
        # editor note has loaded, so it cannot block WebEngine's first paint.
        keys=None,
    )
    buttons.append(btn)
    return buttons


def _install_shortcut_after_load(editor) -> None:
    if getattr(editor, "_add_table_shortcut", None) is not None:
        return
    key = str(config.get("shortcut", "Ctrl+0") or "").strip()
    if not key or key.lower() in {"none", "<nop>"}:
        return
    shortcut = QShortcut(QKeySequence(key), editor.widget)
    shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
    shortcut.activated.connect(lambda: insert_table(editor))
    editor._add_table_shortcut = shortcut


def _queue_shortcut_after_load(editor) -> None:
    QTimer.singleShot(0, lambda: _install_shortcut_after_load(editor))


# Issue #379: let WebEngine load the script as a regular exported resource.
# Reading it and calling eval() during editor_did_init blocked the first paint.
_ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)
mw.addonManager.setWebExports(__name__, r"web/.*\.(js)")


def _append_editor_assets(web_content, context) -> None:
    if isinstance(context, Editor):
        web_content.js.append(
            f"/_addons/{_ADDON_PACKAGE}/web/table_editor.js"
        )


gui_hooks.editor_did_init_buttons.append(_add_button)
gui_hooks.editor_did_load_note.append(_queue_shortcut_after_load)
gui_hooks.webview_will_set_content.append(_append_editor_assets)
