from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.editor import Editor
from aqt.qt import (
    QAction,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QIcon,
    QLabel,
    QRadioButton,
    QSpinBox,
    Qt,
    QTimer,
    QVBoxLayout,
    qconnect,
)


def _get_config() -> dict:
    return mw.addonManager.getConfig(__name__) or {}


def _write_config(config: dict) -> None:
    mw.addonManager.writeConfig(__name__, config)


def _apply_zoom(web, factor: float) -> None:
    try:
        web.setZoomFactor(factor)
    except Exception:
        from _shared_libs.haf_notifications import warn_once
        warn_once('addons/custom/zoom-settings/zoom.py:_apply_zoom', 'מען קען נישט אריינשטעלן דעם געבעטן פארגרעסערונג. עפנט דעם פענסטער פון פריש און פרובירט נאכאמאל.')
        pass


def _zoom_factor_main() -> float:
    config = _get_config()
    if config.get("mode", "all") == "all":
        return float(config.get("zoom_all", 1.0))
    return float(config.get("zoom_main", 1.0))


def _zoom_factor_browser() -> float:
    config = _get_config()
    if config.get("mode", "all") == "all":
        return float(config.get("zoom_all", 1.0))
    return float(config.get("zoom_browser", 1.0))


_BASE_FONT_SIZE: float | None = None


def _get_base_font_size() -> float:
    global _BASE_FONT_SIZE
    if _BASE_FONT_SIZE is None:
        _BASE_FONT_SIZE = QApplication.font().pointSizeF()
    return _BASE_FONT_SIZE


def _browser_font_scale() -> float:
    config = _get_config()
    if config.get("mode", "all") == "all":
        return float(config.get("zoom_all", 1.0))
    return float(config.get("browser_font_scale", 1.0))


def _apply_browser_font(browser: Browser) -> None:
    scale = _browser_font_scale()
    if abs(scale - 1.0) < 0.01:
        browser.setStyleSheet("")
        return
    base = _get_base_font_size()
    size_pt = base * scale
    browser.setStyleSheet(f"* {{ font-size: {size_pt:.1f}pt; }}")


def _on_profile_did_open() -> None:
    _apply_zoom(mw.web, _zoom_factor_main())


def _on_editor_did_init(editor: Editor) -> None:
    _apply_zoom(editor.web, _zoom_factor_browser())


def _on_browser_menus_did_init(browser: Browser) -> None:
    # דחייה ע"מ שכל ה-stylesheets של אנקי יוחלו קודם
    QTimer.singleShot(0, lambda: _apply_browser_font(browser))


gui_hooks.profile_did_open.append(_on_profile_did_open)
gui_hooks.editor_did_init.append(_on_editor_did_init)
gui_hooks.browser_menus_did_init.append(_on_browser_menus_did_init)


class ZoomSettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("פארגרעסערונג איינשטעלונגען")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(320)

        config = _get_config()
        vbox = QVBoxLayout(self)

        # --- מצב ---
        mode_group = QGroupBox("פארגרעסערונג מצב")
        mode_vbox = QVBoxLayout(mode_group)
        self.rb_all = QRadioButton("אלע פענסטער — די זעלבע פארגרעסערונג")
        self.rb_per = QRadioButton("לויטן פענסטער — א באזונדערע פארגרעסערונג פאר יעדן פענסטער")
        mode_vbox.addWidget(self.rb_all)
        mode_vbox.addWidget(self.rb_per)
        vbox.addWidget(mode_group)

        current_mode = config.get("mode", "all")
        self.rb_all.setChecked(current_mode == "all")
        self.rb_per.setChecked(current_mode != "all")

        # --- זום אחיד ---
        self.all_group = QGroupBox("פארגרעסערונג גרייס פאר אלע פענסטער")
        all_hbox = QHBoxLayout(self.all_group)
        all_hbox.addWidget(QLabel("פארגרעסערונג:"))
        self.spin_all = QSpinBox()
        self.spin_all.setRange(50, 300)
        self.spin_all.setSuffix("%")
        self.spin_all.setValue(int(float(config.get("zoom_all", 1.0)) * 100))
        all_hbox.addWidget(self.spin_all)
        all_hbox.addStretch()
        vbox.addWidget(self.all_group)

        # --- זום לפי חלון ---
        self.per_group = QGroupBox("פארגרעסערונג לויטן פענסטער")
        per_form = QFormLayout(self.per_group)

        self.spin_main = QSpinBox()
        self.spin_main.setRange(50, 300)
        self.spin_main.setSuffix("%")
        self.spin_main.setValue(int(float(config.get("zoom_main", 1.0)) * 100))

        self.spin_browser = QSpinBox()
        self.spin_browser.setRange(50, 300)
        self.spin_browser.setSuffix("%")
        self.spin_browser.setValue(int(float(config.get("zoom_browser", 1.0)) * 100))

        per_form.addRow("הויפט פענסטער:", self.spin_main)
        per_form.addRow("קארטל רעדאקטירער:", self.spin_browser)
        vbox.addWidget(self.per_group)

        # --- גודל גופן בדפדוף (רק במצב מפוצל) ---
        self.browser_font_group = QGroupBox("טעקסט גרייס אינעם דורכבלעטערער (Qt)")
        bf_hbox = QHBoxLayout(self.browser_font_group)
        bf_hbox.addWidget(QLabel("שריפט גרייס:"))
        self.spin_browser_font = QSpinBox()
        self.spin_browser_font.setRange(50, 300)
        self.spin_browser_font.setSuffix("%")
        self.spin_browser_font.setValue(int(float(config.get("browser_font_scale", 1.0)) * 100))
        bf_hbox.addWidget(self.spin_browser_font)
        bf_hbox.addStretch()
        vbox.addWidget(self.browser_font_group)

        # --- עדכון נראות ---
        qconnect(self.rb_all.toggled, self._update_visibility)
        self._update_visibility()

        # --- כפתורים ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Reset
        )
        qconnect(buttons.accepted, self.accept)
        qconnect(buttons.rejected, self.reject)
        reset_btn = buttons.button(QDialogButtonBox.StandardButton.Reset)
        reset_btn.setText("צוריקשטעלן")
        qconnect(reset_btn.clicked, self._reset)
        vbox.addWidget(buttons)

    def _reset(self) -> None:
        self.rb_all.setChecked(True)
        self.spin_all.setValue(100)
        self.spin_main.setValue(100)
        self.spin_browser.setValue(100)
        self.spin_browser_font.setValue(100)

    def _update_visibility(self) -> None:
        is_all = self.rb_all.isChecked()
        self.all_group.setVisible(is_all)
        self.per_group.setVisible(not is_all)
        self.browser_font_group.setVisible(not is_all)

    def save(self) -> None:
        config = _get_config()
        config["mode"] = "all" if self.rb_all.isChecked() else "per_window"
        config["zoom_all"] = self.spin_all.value() / 100.0
        config["zoom_main"] = self.spin_main.value() / 100.0
        config["zoom_browser"] = self.spin_browser.value() / 100.0
        config["browser_font_scale"] = self.spin_browser_font.value() / 100.0
        _write_config(config)
        _apply_zoom(mw.web, _zoom_factor_main())


def _open_zoom_settings() -> None:
    dialog = ZoomSettingsDialog(mw)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        dialog.save()


# הוסף פריט תפריט להגדרות זום בתוך תת-תפריט תצוגה
import os as _os

_action = QAction("פארגרעסערונג איינשטעלונגען...", mw)
_zoom_icon_path = _os.path.join(mw.addonManager.addonsFolder(), "remove-buttons", "disp.png")
_action.setIcon(QIcon(_zoom_icon_path))
qconnect(_action.triggered, _open_zoom_settings)
# addon_view_menu נוצר ע"י remove-buttons; אם אינו קיים עוד נחזור ל-menuCol
_target_menu = getattr(mw, "addon_view_menu", mw.form.menuCol)
_target_menu.addAction(_action)
