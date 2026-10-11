import contextlib
import json

from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.gui_hooks import webview_will_set_content
from aqt.qt import *
from aqt.theme import theme_manager
from aqt.utils import showInfo
from PyQt6 import QtCore

# ייבוא רכיבי GUI נדרשים
from PyQt6.QtGui import QAction, QColor, QCursor, QFont, QFontDatabase, QIntValidator, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidgetAction,
)

from _shared_libs.haf_logging import get_logger

logger = get_logger("font_size")

RECENT_FONTS_LIMIT = 14
DARK_SHADE = "rgb(26, 26, 26)"
LIGHT_SHADE = "#d7d7d7"

# #354 — קיצור שנקלט כשהמקלדת במצב עברית נשמר בקונפיג עם אות עברית, אבל בזמן לחיצה
# Qt מדווח (בצירופי Ctrl/Alt) את המקש הלטיני של אותה פריסת מקלדת, ולכן הקיצור מעולם לא
# הופעל — ולחיצה על אות בודדת פשוט הקלידה את האות במקום הטקסט המסומן. הפתרון: רישום
# הקיצור גם בווריאנט הלטיני לפי פריסת המקלדת העברית התקנית, כך ששני המצבים נתפסים.
HEBREW_TO_LATIN_KEY = {
    'א': 'T', 'ב': 'C', 'ג': 'D', 'ד': 'S', 'ה': 'V', 'ו': 'U', 'ז': 'Z',
    'ח': 'J', 'ט': 'Y', 'י': 'H', 'כ': 'F', 'ך': 'L', 'ל': 'K', 'מ': 'N',
    'ם': 'O', 'נ': 'B', 'ן': 'I', 'ס': 'X', 'ע': 'G', 'פ': 'P', 'ף': ';',
    'צ': 'M', 'ץ': '.', 'ק': 'E', 'ר': 'R', 'ש': 'A', 'ת': ',',
}


def key_sequence_variants(key: str) -> list[str]:
    """#354 — ברענגט צוריק דעם אפגעזיכערט קיצור און אויך א ווערסיע וואו די העברעאישע אותיות ווערן געטוישט צו די פאסיגע לאטיינישע קנעפלעך."""
    variants = [key]
    if "++" in key:
        # קיצור שמכיל את התו '+' עצמו (למשל Ctrl++) — לא מפרקים אותו
        return variants
    converted = "+".join(HEBREW_TO_LATIN_KEY.get(part, part) for part in key.split("+"))
    if converted != key:
        variants.append(converted)
    return variants


# #138 — קיצור אות בעורך חייב לכלול Ctrl או Alt. ההגנה המקומית מונעת מקונפיג
# ישן/ערוך ידנית לרשום QShortcut שהופך הקלדה רגילה לפקודת עיצוב.
def _unsafe_editor_letter_shortcut(key: str) -> bool:
    parts = [part.strip() for part in str(key or "").split("+") if part.strip()]
    lowered = {part.lower() for part in parts}
    if "ctrl" in lowered or "control" in lowered or "alt" in lowered:
        return False
    non_modifiers = [
        part for part in parts
        if part.lower() not in {"shift", "meta", "cmd", "command"}
    ]
    return len(non_modifiers) == 1 and len(non_modifiers[0]) == 1 and non_modifiers[0].isalpha()


def get_colors():
    background_color = (
        "#272828!important" if theme_manager.night_mode else "hsla(0, 0%, 98%, .9)"
    )
    foreground_color = LIGHT_SHADE if theme_manager.night_mode else DARK_SHADE
    hover_color = DARK_SHADE
    return (background_color, foreground_color, hover_color)


def get_hebrew_fonts_list():
    """ברענגט צוריק אן אויסגעשטעלטע שריפט ליסטע, מיט העברעאישע שריפטן צום ערשט"""
    hebrew_fonts = QFontDatabase.families(QFontDatabase.WritingSystem.Hebrew)
    if len(hebrew_fonts) < 2:
        hebrew_fonts = QFontDatabase.families()
    return sorted(hebrew_fonts)


menu_stylesheet_template = """\
QMenu {{
    background-color: {background};
    border: solid 2px rgba(0, 0, 0, 1);
    border-radius: 8px;
}}
QMenu::item {{
    background-color: transparent;
    font-size: 12px;
    padding: 3px 15px;
    margin: 5px 10px;
    color: {foreground};
    font-weight: 400;
}}
QMenu::item:selected {{
    background-color: rgb(195, 195, 195);
    color: {hover_color};
    border-radius: 4px;
}}"""

font_label_stylesheet_template = """\
QLabel {{
    color: {foreground_color};
    font-family: {font_name};
    background-color: transparent;
    font-size:16px;
    padding:1px 15px;
    margin:2px 10px;
}}
QLabel:hover {{
    color: {hover_color};
    background-color: rgb(195, 195, 195);
    border-radius: 4px;
}}"""


# --- מחלקה חדשה: חלון הגדרות ויזואלי ---
class PresetsConfigDialog(QDialog):
    def __init__(self, parent, current_config):
        super().__init__(parent)
        self.setWindowTitle("איינשטעלן שנעלע אויסשטעל קנעפלעך")
        self.setMinimumWidth(700)
        self.config = current_config
        self.presets_data = self.config.get("style_presets", [])

        # אם אין הגדרות או שהרשימה קצרה מדי, נשלים ל-5
        while len(self.presets_data) < 5:
            self.presets_data.append(
                {"font": "Arial", "size": "20pt", "color": "#000000"})

        self.layout = QVBoxLayout(self)
        self.inputs = []

        # #137 — הסבר אופרציות לאיפוס פרמטרים
        note_label = QLabel("💡 כדי צוריקצושטעלן א פאראמעטער (= אן א טויש), דריקט דערויף מיטן רעכטן מויז קנעפל")
        note_label.setStyleSheet("color: gray; font-size: 11px;")
        self.layout.addWidget(note_label)

        # טעינת רשימת הפונטים פעם אחת לשימוש בכולם
        self.font_list = get_hebrew_fonts_list()

        # יצירת שורה לכל פריסט
        for i in range(5):
            preset = self.presets_data[i]
            group = QGroupBox(f"קנעפל {i + 1}")
            h_layout = QHBoxLayout()

            # --- בחירת גופן (Custom ComboBox כמו בתפריט) ---
            lbl_font = QLabel("שריפט:")
            font_combo = QComboBox()
            font_combo.setMinimumWidth(200)
            font_combo.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

            current_font_name = preset.get("font", "")
            current_index = 0

            # #137 — פריט "ללא שינוי" ראשון (נשמר כ-"")
            font_combo.addItem("— אן א טויש —", "")
            if not current_font_name:
                current_index = 0

            # מילוי ה-ComboBox
            for idx, f_name in enumerate(self.font_list):
                # #276 — שמירת פריסט חייבת userData עם שם הגופן; FontRole לבדו לא מוחזר ב-currentData().
                font_combo.addItem(f_name, f_name)
                font_combo.setItemData(idx + 1, QFont(f_name), QtCore.Qt.ItemDataRole.FontRole)
                if f_name == current_font_name:
                    current_index = idx + 1

            font_combo.setCurrentIndex(current_index)
            # #137 — קליק ימני = איפוס לגופן (ללא שינוי)
            font_combo.customContextMenuRequested.connect(
                lambda _, fc=font_combo: fc.setCurrentIndex(0))

            # גודל
            lbl_size = QLabel("גרייס:")
            spin_size = QSpinBox()
            # #137 — 0 = ללא שינוי (special value text), קליק ימני = איפוס
            spin_size.setRange(0, 200)
            spin_size.setSpecialValueText("אן א טויש")
            spin_size.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            spin_size.customContextMenuRequested.connect(
                lambda _, ss=spin_size: ss.setValue(0))
            # חילוץ המספר מהמחרוזת (למשל "20pt" -> 20)
            try:
                current_size = int(''.join(filter(str.isdigit, str(preset.get("size", "0")))))
            except (ValueError, TypeError):
                current_size = 0
            spin_size.setValue(current_size)

            # צבע
            lbl_preview = QLabel("אויסשטעל/קאליר:")
            btn_preview = QPushButton("א")  # האות להמחשה
            btn_preview.setFixedWidth(60)
            btn_preview.setFixedHeight(40)
            btn_preview.setCursor(QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            # #137 — קליק ימני = ניקוי צבע (ללא שינוי)
            btn_preview.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            current_color = preset.get("color", "")
            btn_preview.setProperty("color_val", current_color)  # שמירת הצבע כמאפיין

            # חיבור אירועים לעדכון התצוגה המקדימה
            font_combo.currentIndexChanged.connect(
                lambda _, b=btn_preview, f=font_combo, s=spin_size: self.update_preview(b, f, s))
            spin_size.valueChanged.connect(
                lambda _, b=btn_preview, f=font_combo, s=spin_size: self.update_preview(b, f, s))
            btn_preview.clicked.connect(lambda _, b=btn_preview, f=font_combo, s=spin_size: self.pick_color(b, f, s))
            # #137 — קליק ימני = ניקוי צבע (ללא שינוי)
            btn_preview.customContextMenuRequested.connect(
                lambda _, b=btn_preview, f=font_combo, s=spin_size: (
                    b.setProperty("color_val", ""),
                    self.update_preview(b, f, s)
                ))

            # אתחול ראשוני של התצוגה
            self.update_preview(btn_preview, font_combo, spin_size)

            # --- עיצוב נוסף: מודגש, נטוי, קו תחתון, כתב עליון/תחתון ---
            chk_bold = QCheckBox("דיק")
            chk_bold.setChecked(preset.get("bold", False))

            chk_italic = QCheckBox("שיף")
            chk_italic.setChecked(preset.get("italic", False))

            chk_underline = QCheckBox("אונטערשטרייכן")
            chk_underline.setChecked(preset.get("underline", False))

            chk_superscript = QCheckBox("x²")
            chk_superscript.setChecked(preset.get("superscript", False))

            chk_subscript = QCheckBox("x₂")
            chk_subscript.setChecked(preset.get("subscript", False))

            # כתב עליון/תחתון — בלעדיים אחד לשני
            chk_superscript.toggled.connect(lambda checked, other=chk_subscript: other.setChecked(False) if checked else None)
            chk_subscript.toggled.connect(lambda checked, other=chk_superscript: other.setChecked(False) if checked else None)

            # --- צבע רקע (קליק שמאלי = בחר, קליק ימני = נקה) ---
            lbl_bg = QLabel("הינטערגרונט:")
            btn_bg = QPushButton("  ")
            btn_bg.setMinimumWidth(78)
            btn_bg.setFixedHeight(28)
            btn_bg.setCursor(QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            btn_bg.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            current_bg = preset.get("bgColor", "")
            btn_bg.setProperty("color_val", current_bg)
            # #269 — התצוגה המקדימה בחלון ההגדרה משקפת גם מודגש/נטוי/קו תחתון/רקע, לא רק צבע וגודל.
            btn_preview.setProperty("bold_val", chk_bold.isChecked())
            btn_preview.setProperty("italic_val", chk_italic.isChecked())
            btn_preview.setProperty("underline_val", chk_underline.isChecked())
            btn_preview.setProperty("bg_val", current_bg)
            self._update_bg_preview(btn_bg)
            btn_bg.clicked.connect(lambda _, b=btn_bg, p=btn_preview, f=font_combo, s=spin_size: (
                self.pick_bg_color(b),
                p.setProperty("bg_val", b.property("color_val") or ""),
                self.update_preview(p, f, s)
            ))
            btn_bg.customContextMenuRequested.connect(lambda _, b=btn_bg, p=btn_preview, f=font_combo, s=spin_size: (
                self._clear_bg(b),
                p.setProperty("bg_val", ""),
                self.update_preview(p, f, s)
            ))
            for chk, prop in ((chk_bold, "bold_val"), (chk_italic, "italic_val"), (chk_underline, "underline_val")):
                chk.toggled.connect(lambda checked, p=btn_preview, f=font_combo, s=spin_size, prop=prop: (
                    p.setProperty(prop, checked),
                    self.update_preview(p, f, s)
                ))
            self.update_preview(btn_preview, font_combo, spin_size)

            # הוספה ללייאוט
            h_layout.addWidget(lbl_font)
            h_layout.addWidget(font_combo)
            h_layout.addWidget(lbl_size)
            h_layout.addWidget(spin_size)
            h_layout.addWidget(lbl_preview)
            h_layout.addWidget(btn_preview)
            h_layout.addWidget(chk_bold)
            h_layout.addWidget(chk_italic)
            h_layout.addWidget(chk_underline)
            h_layout.addWidget(chk_superscript)
            h_layout.addWidget(chk_subscript)
            h_layout.addWidget(lbl_bg)
            h_layout.addWidget(btn_bg)

            group.setLayout(h_layout)
            self.layout.addWidget(group)

            # שמירת הרפרנסים כדי לשלוף נתונים בסוף
            self.inputs.append({
                "font": font_combo,
                "size": spin_size,
                "color_btn": btn_preview,
                "bold": chk_bold,
                "italic": chk_italic,
                "underline": chk_underline,
                "superscript": chk_superscript,
                "subscript": chk_subscript,
                "bg_btn": btn_bg,
            })

        # כפתורי אישור וביטול
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def update_preview(self, btn, font_combo, spin_box):
        """דערהיינטיגט דעם פארויסקוק קנעפל לויט די אויסוואלן"""
        font = font_combo.currentData() or font_combo.currentText()
        size = spin_box.value()
        color = btn.property("color_val") or "#000000"

        # #137 — אם ללא שינוי, הצג ב-gray
        is_no_font = (font_combo.currentIndex() == 0)
        is_no_size = (size == 0)
        display_font = font if not is_no_font else "Arial"
        display_size = min(size if not is_no_size else 16, 24)
        display_color = color
        background_color = btn.property("bg_val") or ('#f0f0f0' if is_no_font and is_no_size else 'white')
        font_weight = "bold" if btn.property("bold_val") else "normal"
        font_style = "italic" if btn.property("italic_val") else "normal"
        text_decoration = "underline" if btn.property("underline_val") else "none"

        style = f"""
            QPushButton {{
                background-color: {background_color};
                color: {display_color};
                font-family: '{display_font}';
                font-size: {display_size}px;
                font-weight: {font_weight};
                font-style: {font_style};
                text-decoration: {text_decoration};
                border: 1px solid grey;
                border-radius: 4px;
            }}
        """
        btn.setStyleSheet(style)
        tip_parts = []
        if not is_no_font:
            tip_parts.append(f"שריפט: {font}")
        if not is_no_size:
            tip_parts.append(f"גרייס: {size}")
        tip_parts.append("רעכטער דרוק צו אויסרייניגן")
        btn.setToolTip('\n'.join(tip_parts))

    def pick_color(self, btn, font_combo, spin_box):
        initial = QColor(btn.property("color_val")) if btn.property("color_val") else QColor("#000000")
        color = QColorDialog.getColor(initial=initial, parent=self)
        if color.isValid():
            hex_color = color.name()
            btn.setProperty("color_val", hex_color)
            self.update_preview(btn, font_combo, spin_box)

    def _update_bg_preview(self, btn):
        color = btn.property("color_val")
        if color:
            btn.setText("")
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid grey; border-radius: 3px;")
            btn.setToolTip(f"דריקט צו טוישן דעם הינטערגרונט קאליר: {color}\nרעכטער דרוק צו אויסרייניגן")
        else:
            # #142 — כשצבע הרקע מאופס, הכפתור מציג במפורש "ללא שינוי" כמו שאר פרמטרי הפריסט.
            btn.setText("אן א טויש")
            btn.setStyleSheet("background-color: transparent; border: 1px solid grey; border-radius: 3px; color: gray;")
            btn.setToolTip("דריקט אויסצוקלייבן א הינטערגרונט קאליר\nרעכטער דרוק צו אויסרייניגן")

    def pick_bg_color(self, btn):
        current = btn.property("color_val")
        initial = QColor(current) if current else QColor("#ffffff")
        color = QColorDialog.getColor(initial=initial, parent=self)
        if color.isValid():
            btn.setProperty("color_val", color.name())
            self._update_bg_preview(btn)

    def _clear_bg(self, btn):
        btn.setProperty("color_val", "")
        self._update_bg_preview(btn)

    def get_new_presets(self):
        new_presets = []
        for inp in self.inputs:
            # #137 — שמירת ערכים ריקים ("") כאשר "ללא שינוי" נבחר
            font_val = inp["font"].currentData()  # None/"" עבור "ללא שינוי", str עבור גופן אמיתי
            if font_val is None:
                font_val = ""
            size_val = inp["size"].value()
            size_str = f"{size_val}pt" if size_val > 0 else ""  # 0 = ללא שינוי
            new_presets.append({
                "label": "א",
                "font": font_val,
                "size": size_str,
                "color": inp["color_btn"].property("color_val") or "",
                "bold": inp["bold"].isChecked(),
                "italic": inp["italic"].isChecked(),
                "underline": inp["underline"].isChecked(),
                "superscript": inp["superscript"].isChecked(),
                "subscript": inp["subscript"].isChecked(),
                "bgColor": inp["bg_btn"].property("color_val"),
            })
        return new_presets


class ExtraEditorCommands:
    # #130 — רשימת כל המופעים הפעילים לצורך עדכון כפתורים בזמן אמת
    _instances: list["ExtraEditorCommands"] = []
    # #194 — hook גלובלי אחד מספיק לכל העורכים; רישום hook לכל פתיחה מצטבר ומאט פתיחת/שימוש בעורך לאורך זמן.
    _js_hook_registered = False

    def __init__(self, editor) -> None:
        self.editor: Editor = editor
        self.config = mw.addonManager.getConfig(__name__) or {}
        # מהדורות קודמות שמרו S1..S5 בתוך הגדרות המשתמש, ולכן שינוי
        # config.json לבדו לא משפיע על התקנה קיימת. ממירים רק את ערכי ברירת
        # המחדל הישנים; כיתוב שהמשתמש בחר בעצמו נשמר.
        presets = self.config.get("style_presets") or []
        migrated = False
        for index, preset in enumerate(presets[:5], start=1):
            if isinstance(preset, dict) and preset.get("label") == f"S{index}":
                preset["label"] = "א"
                migrated = True
        if migrated:
            mw.addonManager.writeConfig(__name__, self.config)
        self.buttons = []
        self.preset_buttons = []  # רשימה נפרדת לכפתורי הפריסטים כדי לעדכן אותם
        self.preset_shortcuts = []
        self.editor_shortcuts = []
        self._pending_editor_shortcuts = []
        self._editor_shortcuts_installed = False
        self.create_buttons()
        self.brush_toggeled = False
        # #194 — רישום ה-handler נעשה פעם אחת ברמת המחלקה, כדי שלא יישארו handlers ישנים אחרי סגירת עורכים.
        self._ensure_js_hook()
        with contextlib.suppress(Exception):
            self.editor.widget.destroyed.connect(self._on_editor_destroyed)
        ExtraEditorCommands._instances.append(self)

    @classmethod
    def _ensure_js_hook(cls) -> None:
        # #194 — מונע הצטברות webview_did_receive_js_message callbacks בכל פתיחת עורך.
        if cls._js_hook_registered:
            return
        gui_hooks.webview_did_receive_js_message.append(cls._dispatch_js_message)
        cls._js_hook_registered = True

    @classmethod
    def _dispatch_js_message(cls, handled, message, context):
        # #194 — dispatch יחיד עובר רק על מופעים חיים ומנקה מופעים שהחלון שלהם נסגר.
        for inst in list(cls._instances):
            try:
                if context is inst.editor:
                    return inst.handle_js_message(handled, message, context)
            except RuntimeError:
                cls._remove_instance(inst)
        return handled

    @classmethod
    def _remove_instance(cls, inst: "ExtraEditorCommands") -> None:
        # #194 — ניקוי קיצורי QShortcut ומופע עורך מת מונע האטה מצטברת אחרי פתיחות רבות.
        if inst in cls._instances:
            cls._instances.remove(inst)
        for shortcut in (
            list(getattr(inst, "preset_shortcuts", []))
            + list(getattr(inst, "editor_shortcuts", []))
        ):
            with contextlib.suppress(Exception):
                shortcut.setEnabled(False)
                shortcut.deleteLater()

    def _on_editor_destroyed(self, *_args) -> None:
        # #194 — כאשר חלון העורך נסגר, מסירים את המופע מרשימת dispatch במקום להשאיר reference מת.
        self._remove_instance(self)

    # #142 — בדיקת WebView פעיל מונעת קריאת eval על עורך שכבר נסגר או עדיין לא נטען.
    def _webview(self):
        return getattr(self.editor, "web", None)

    def _editor_button(self, *args, **kwargs):
        """Build toolbar HTML now, but postpone QShortcut creation until first paint."""
        func = kwargs.get("func")
        key = str(kwargs.pop("keys", "") or "").strip()
        button = self.editor.addButton(*args, keys=None, **kwargs)
        # #138 — אין לרשום אות/Shift+אות כקיצור בתוך שדה טקסט.
        if (
            key
            and key.lower() not in {"none", "<nop>"}
            and not _unsafe_editor_letter_shortcut(key)
            and callable(func)
        ):
            self._pending_editor_shortcuts.append((key, func))
        return button

    def _install_deferred_editor_shortcuts(self) -> None:
        if self._editor_shortcuts_installed:
            return
        self._editor_shortcuts_installed = True
        widget = getattr(self.editor, "widget", None)
        if widget is None:
            return
        for key, func in self._pending_editor_shortcuts:
            shortcut = QShortcut(QKeySequence(key), widget)
            shortcut.setKeys([QKeySequence(v) for v in key_sequence_variants(key)])
            with contextlib.suppress(Exception):
                shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(
                lambda checked=False, fn=func: self.editor.call_after_note_saved(
                    lambda: fn(self.editor), keepFocus=True
                )
            )
            self.editor_shortcuts.append(shortcut)

    def set_style(self, style, val):
        web = self._webview()
        if web is None:
            return
        arg = f'"{str(val)}"' if style == "font-family" else f'{str(val)}'
        web.eval(f"""
            var root = document.querySelectorAll(".rich-text-editable");
            root.forEach((sel) => {{
                const sr = sel && sel.shadowRoot;
                if (!sr || typeof sr.getSelection !== "function") return;
                try {{
                    const selection = sr.getSelection();
                    if (!selection || selection.rangeCount === 0) return;
                    fontsi(selection, "{style}", {arg});
                    gText("e");
                }} catch (e) {{
                    console.log(e);
                }}
            }});
        """)

    def apply_preset(self, preset):
        font = preset.get("font", "")
        size = preset.get("size", "")
        color = preset.get("color", "")
        bold = "true" if preset.get("bold", False) else "false"
        italic = "true" if preset.get("italic", False) else "false"
        underline = "true" if preset.get("underline", False) else "false"
        bg_color = preset.get("bgColor", "")
        superscript = "true" if preset.get("superscript", False) else "false"
        subscript = "true" if preset.get("subscript", False) else "false"
        web = self._webview()
        if web is None:
            return

        js_cmd = f"""
            var root = document.querySelectorAll(".rich-text-editable");
            root.forEach((sel) => {{
                const sr = sel && sel.shadowRoot;
                if (!sr || typeof sr.getSelection !== "function") return;
                const selection = sr.getSelection();
                if (!selection || selection.rangeCount === 0) return;
                applyFullStyle(selection, "{font}", "{size}", "{color}", {bold}, {italic}, {underline}, "{bg_color}", {superscript}, {subscript});
            }});
        """
        web.eval(js_cmd)
        self._show_preset_edit_hint_once()

    def _show_preset_edit_hint_once(self):
        config = mw.addonManager.getConfig(__name__) or {}
        if config.get("style_preset_edit_hint_shown", False):
            return

        config["style_preset_edit_hint_shown"] = True
        mw.addonManager.writeConfig(__name__, config)
        self.config = config

        try:
            parent_window = self.editor.widget.window()
        except RuntimeError:
            parent_window = mw
        showInfo("מען קען מיך רעדאקטירן דורכן צאהן ראד קנעפל, דארט אונטער 'איינשטעלן סטילן'.", parent=parent_window)

    def toggle_brush(self):
        if not self.brush_toggeled:
            self.editor.web.eval("""
var root = document.querySelectorAll(".rich-text-editable");

root.forEach((sel) => {
    // וויכטיגע פאררעכטונג: ניצן-const שאפט א נייעם משתנה ביי יעדן דורכגאנג אין דער לולאה
    const sr = sel.shadowRoot;
    // פארזיכערונג: מאכט זיכער אז עס איז דא shadowRoot פארן צולייגן אן אירוע
    if (sr) {
        sr.addEventListener("mouseup", function () {
            // יעצט sr באציט זיך זיכער צו-ShadowRoot דעם באזונדערן וואס מען האט געדריקט
            let selection = sr.getSelection();
            if (isBrushActive) {
                // ראטזאמע בדיקה: איז טאקע אויסגעקליבן טעקסט? (נישט נאר א בלינקנדיגער סמן)
                // selection.isCollapsed ברענגט צוריק true אויב קיין טעקסט איז נישט אויסגעקליבן
                if (selection.rangeCount > 0) {
                    pasteFormat(selection);
                    document.body.style.cursor = "auto";
                    isBrushActive = false; // מען שאלט אויס דעם בערשטל נאכן איין מאל נוצן
                }
            }
        });
    }
});
             """)
        self.brush_toggeled = True
        self.editor.web.eval("""
            var root = document.querySelectorAll(".rich-text-editable");
            var textWasSelected = false;

            for (let i = 0; i < root.length; i++) {
                let sel = root[i];
                let sr = sel.shadowRoot;
                try {
                    toggleBrush(sr);

                    // קוקט צי טעקסט איז אויסגעקליבן געווארן נאכן אנצינדן toggleBrush
                    if (isBrushActive) {
                        textWasSelected = true;
                        break; // שטעל אפ דעם איבערגאנג
                    }
                } catch (e) {
                    console.log(e);
                }
            }

            // בדיקה צום סוף — אויב אין קיין פעלד איז נישט אויסגעקליבן געווארן טעקסט
            if (!textWasSelected) {
                alert("קיין טעקסט איז נישט אויסגעקליבן געווארן!");
            }
        """)

    # #314 — הדבקה נקייה דרך shadow DOM של שדות העורך (Anki 24+)
    def paste_plain(self):
        text = QApplication.clipboard().text()
        if not text:
            return
        import json
        self.editor.web.eval(f"""
            (() => {{
                const text = {json.dumps(text)};
                const roots = document.querySelectorAll(".rich-text-editable");
                for (const el of roots) {{
                    const sr = el && el.shadowRoot;
                    if (!sr || typeof sr.getSelection !== "function") continue;
                    const sel = sr.getSelection();
                    if (!sel || sel.rangeCount === 0) continue;
                    const range = sel.getRangeAt(0);
                    range.deleteContents();
                    const node = document.createTextNode(text);
                    range.insertNode(node);
                    range.setStartAfter(node);
                    range.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(range);
                    const ce = sr.querySelector("[contenteditable]");
                    if (ce) ce.dispatchEvent(new Event("input", {{bubbles: true}}));
                    return;
                }}
                document.execCommand("insertText", false, text);
            }})();
        """)

    def open_config(self):
        # #136 — גלישת RuntimeError אם ה-widget כבר נמחק (קורה כשחלון עורך נסגר)
        try:
            parent_window = self.editor.widget.window()
        except RuntimeError:
            parent_window = mw

        dlg = PresetsConfigDialog(parent_window, self.config)
        if dlg.exec():
            # אם המשתמש לחץ אישור, נעדכן את הקונפיגורציה
            new_presets = dlg.get_new_presets()
            self.config["style_presets"] = new_presets
            mw.addonManager.writeConfig(__name__, self.config)

            # #130 — עדכון כל מופעי העורך הפעילים בזמן אמת; ניקוי מופעים מתים
            dead = []
            for inst in list(ExtraEditorCommands._instances):
                try:
                    inst.config = mw.addonManager.getConfig(__name__)
                    inst.refresh_shortcuts(inst.config)
                except Exception as e:
                    if inst.editor.widget is None or sip.isdeleted(inst.editor.widget):
                        dead.append(inst)
                        continue
                    logger.warning(f"Font shortcuts were not refreshed in an editor: {e}", exc_info=True)
                    from _shared_libs.haf_notifications import warn_once
                    warn_once("font-size:shortcuts", "מען קען נישט דערהיינטיגן קיצורים אין איינעם פון די רעדאקטירער פענסטער. פארמאכט און עפנט אים פון פריש כדי די איינשטעלונגען זאלן אריינגיין.")
            for inst in dead:
                ExtraEditorCommands._instances.remove(inst)
        self.config = mw.addonManager.getConfig(__name__)

    def update_preset_buttons_style(self):
        """
        דערהיינטיגט די מוסטער קנעפלעך אינעם סרגל מיט JavaScript
        """
        web = self._webview()
        if web is None:
            return
        presets = self.config.get("style_presets", [])
        if not presets:
            return

        # אישיו #400: מעבירים ל-JavaScript גם את הקיצור הפעיל כדי שיופיע בטולטיפ של הכפתור.
        display_presets = []
        for index, preset in enumerate(presets):
            display_preset = dict(preset)
            display_preset["shortcut"] = str(
                self.config.get(f"style_preset_{index + 1}_shortcut", "") or ""
            ).strip()
            display_presets.append(display_preset)
        presets_json = json.dumps(display_presets, ensure_ascii=False)
        # #138 — אם WebEngine מקבל גם את האירוע שכבר הפעיל QShortcut, הוא חייב
        # לחסום את הכנסת אות הקיצור לשדה. מעבירים ל-JS רק קיצורי עיצוב פעילים ובטוחים.
        shortcut_keys = [
            self.config.get("font_Shortcut", ""),
            self.config.get("size_Shortcut", ""),
            self.config.get("brush_shortcut", ""),
            *(self.config.get(f"style_preset_{index}_shortcut", "") for index in range(1, 6)),
        ]
        shortcut_blocklist = [
            variant
            for key in shortcut_keys
            if str(key or "").strip().lower() not in {"", "none", "<nop>"}
            and not _unsafe_editor_letter_shortcut(str(key))
            # #138 — use the same Hebrew/Latin alternatives as the live QShortcut.
            for variant in key_sequence_variants(str(key).strip())
        ]
        shortcut_blocklist_json = json.dumps(shortcut_blocklist, ensure_ascii=False)

        # #173 — לא מריצים בזמן init סינכרוני, אבל כן ממתינים קצרות עד שהכפתורים וה-JS קיימים כדי שהעיצוב יופיע.
        web.eval(f"""
            (function(presets, blockedShortcuts, attempts) {{
                function applyPresetStylesWhenReady() {{
                    if (typeof window.HafFontSizeSetShortcutBlocklist === "function") {{
                        window.HafFontSizeSetShortcutBlocklist(blockedShortcuts);
                    }}
                    if (typeof updatePresetButtonsVisually === "function" && document.getElementById("preset_0")) {{
                        updatePresetButtonsVisually(presets);
                        return;
                    }}
                    if (attempts > 0) {{
                        attempts -= 1;
                        setTimeout(applyPresetStylesWhenReady, 50);
                    }}
                }}
                applyPresetStylesWhenReady();
            }})({presets_json}, {shortcut_blocklist_json}, 40);
        """)

    def schedule_preset_buttons_style_update(self):
        # #173 — בזמן editor_did_init_buttons ה-WebView עדיין לא תמיד מוכן; דוחים את ה-JS עד אחרי טעינת הפתק.
        QtCore.QTimer.singleShot(50, self.update_preset_buttons_style)

    def refresh_shortcuts(self, new_config=None) -> None:
        # #134/#138 — shortcut-manager שומר קיצורי פריסטים בקונפיג; רענון זה מעדכן מופעי עורך חיים ככל שניתן.
        self.config = new_config or mw.addonManager.getConfig(__name__) or {}
        self.update_preset_buttons_style()
        self._install_preset_shortcuts()

    def _install_preset_shortcuts(self) -> None:
        for shortcut in getattr(self, "preset_shortcuts", []):
            with contextlib.suppress(Exception):
                shortcut.setEnabled(False)
                shortcut.deleteLater()
        self.preset_shortcuts = []
        widget = getattr(self.editor, "widget", None)
        if widget is None:
            return
        for idx in range(5):
            key = str(self.config.get(f"style_preset_{idx + 1}_shortcut", "") or "").strip()
            # #138 — קונפיג ישן עם A/Shift+A אינו רשאי לבלוע הקלדה בעורך.
            if not key or key.lower() in {"none", "<nop>"} or _unsafe_editor_letter_shortcut(key):
                continue
            shortcut = QShortcut(QKeySequence(key), widget)
            # #354 — רישום גם וריאנט לטיני של אותיות עבריות כדי שהקיצור ייתפס בכל פריסת מקלדת.
            shortcut.setKeys([QKeySequence(variant) for variant in key_sequence_variants(key)])
            with contextlib.suppress(Exception):
                # #138 / דיווח קיצור סגנון מהיר — the editor WebView can
                # consume child-widget shortcuts. WindowShortcut keeps the
                # preset active whenever this editor window is active.
                shortcut.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(lambda checked=False, i=idx: self.apply_preset_by_index(i))
            self.preset_shortcuts.append(shortcut)

    def set_size(self, size, menu):
        if size != '"unset"' and isinstance(size, int) and size > 1600:
            showInfo("מאקסימום גרייס: 1600")
            return
        self.set_style("font-size", size)
        if menu:
            menu.q_menu.close()

    def set_font(self, font_name):
        self.config["prev_font"] = font_name
        self.set_style("font-family", font_name)

    # פונקציה לבחירה מתוך הרשימה "אחרונים" (סוגרת את התפריט)
    def select_recent_font(self, font_name, menu):
        self.set_font(font_name)
        self.add_recent_font(font_name)
        self.save_font_config()
        menu.q_menu.close()

    # פונקציה המופעלת בעת בחירה מה-ComboBox
    def on_combo_font_selected(self, index, combo, menu):
        # שליפת שם הפונט האמיתי (החבוי ב-User Data)
        font_name = combo.itemData(index)
        if font_name:
            self.set_font(font_name)
            self.add_recent_font(font_name)
            self.save_font_config()
            menu.q_menu.close()

    def disable_action(self, menu, lineedit):
        if lineedit.text() != "":
            menu.lineedited = True

    def show_size_menu(self, editor):
        menu = ExtraMenu()
        custom_size = QLineEdit(menu.q_menu)
        custom_size.setMaximumWidth(60)
        custom_size.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        custom_size.setValidator(QIntValidator(0, 1600))
        custom_size.returnPressed.connect(lambda: self.set_size(int(custom_size.text()), menu))

        custom_size_widget = QWidgetAction(menu.q_menu)
        custom_size_widget.setDefaultWidget(custom_size)
        menu.q_menu.addAction(custom_size_widget)

        for size in [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]:
            menu.add_action(
                f"{size}",
                func=lambda _, sz=size: self.set_size(sz, menu),
                stylesheet=None,
            )
        menu.add_action(
            "שטעל צוריק",
            func=lambda _, sz='"unset"': self.set_size(sz, menu),
            stylesheet=None)

        custom_size.textEdited.connect(lambda: self.disable_action(menu, custom_size))
        custom_size.setFocus()
        menu.show()

    def handle_js_message(self, handled, message, context):
        # #131/#136 — בדיקת context מוודאת שרק המופע של העורך הנוכחי מגיב;
        # מונעת קריסה ממופעים ישנים שה-QWidget שלהם נמחק ופתיחת דיאלוג כפול
        if message == "styles_options" and context is self.editor:
            self.open_config()
            return (True, None)  # מחזיר True כדי לאותת ל-Anki שההודעה טופלה

        # אם זו לא ההודעה שלנו, נחזיר את הערך המקורי (handled)
        return handled

    def show_font_menu(self, _editor):
        menu = ExtraMenu()
        (_, foreground_color, hover_color) = get_colors()

        menu.add_action(
            "שטעל צוריק דעם אויסשטעל",
            func=lambda _, fnt="'none'": self.set_font(fnt),
            stylesheet=None)

        # Recent fonts
        for font_name in self.config["recent_fonts"]:
            menu.add_action(
                "אבגדה - " + font_name,
                lambda _, fnt=font_name: self.select_recent_font(fnt, menu),
                stylesheet=font_label_stylesheet_template.format(
                    foreground_color=foreground_color,
                    font_name=font_name,
                    hover_color=hover_color,
                ),
            )

        menu.q_menu.addSeparator()

        # ComboBox בשימוש עם פונקציית העזר
        hebrew_fonts = get_hebrew_fonts_list()

        # 2. יצירת ה-ComboBox
        font_combo = QComboBox(menu.q_menu)
        font_combo.setMinimumWidth(200)  # רוחב מינימלי כדי שייראה טוב

        # 3. מילוי הנתונים: טקסט לתצוגה + שם פונט אמיתי + הגדרת פונט לפריט
        # נוסיף כותרת ראשונה
        font_combo.addItem("קלייבט אויס נאך א שריפט...", None)

        for font_name in hebrew_fonts:
            display_text = f"אבגדה - {font_name}"
            font_combo.addItem(display_text, font_name)  # font_name נשמר כ-User Data

            # הגדרת הפונט הספציפי לפריט ב-ComboBox
            index = font_combo.count() - 1
            font_combo.setItemData(index, QFont(font_name), QtCore.Qt.ItemDataRole.FontRole)

        # 4. חיבור לאירוע בחירה
        # currentIndexChanged שולח את האינדקס הנבחר
        font_combo.currentIndexChanged.connect(
            lambda index: self.on_combo_font_selected(index, font_combo, menu)
        )

        # 5. הוספה לתפריט
        font_widget = QWidgetAction(menu.q_menu)
        font_widget.setDefaultWidget(font_combo)
        menu.q_menu.addAction(font_widget)

        menu.show()

    def save_font_config(self):
        mw.addonManager.writeConfig(__name__, self.config)

    def add_recent_font(self, font_name):
        recent_fonts = self.config["recent_fonts"]
        if font_name in recent_fonts:
            recent_fonts.remove(font_name)
        recent_fonts.insert(0, font_name)
        while len(recent_fonts) > RECENT_FONTS_LIMIT:
            recent_fonts.pop()

    def create_buttons(self) -> None:
        # Size
        size_btn = self._editor_button(
            icon=None,
            label="גרייס",
            cmd="גרייס",
            func=self.show_size_menu,
            tip=f"שריפט גרייס ({self.config.get('size_Shortcut', '')})",
            keys=self.config.get('size_Shortcut', ''),
            id="size",
        )
        self.buttons.append(size_btn)

        # Font
        font_btn = self._editor_button(
            icon=None,
            label="שריפט",
            cmd="שריפט",
            func=self.show_font_menu,
            tip=f"שריפט ({self.config.get('font_Shortcut', '')})",
            keys=self.config.get('font_Shortcut', ''),
            id="font",
        )
        self.buttons.append(font_btn)

        # Clear
        clean_btn = self._editor_button(
            icon=None,
            label="ריין אויס",
            cmd="ריין אויס",
            func=lambda editor: editor.web.eval("setFormat('removeFormat');"),
            tip="נעם אוועק דעם גאנצן אויסשטעל",
            id="clear",
        )
        self.buttons.append(clean_btn)

        # Brush (Merged Copy/Paste)
        brush_btn = self._editor_button(
            icon=None,
            label="🖌️",
            cmd="בערשטל",
            func=lambda _: self.toggle_brush(),
            tip=f"אויסשטעל בערשטל (קאפירן/אריינלייגן) ({self.config.get('brush_shortcut', 'Alt+B')})",
            keys=self.config.get('brush_shortcut', 'Alt+B'),
            id="brush_fmt"
        )
        self.buttons.append(brush_btn)

        # Paste Plain
        paste_plain_btn = self._editor_button(
            icon=None,
            label="לייג אריין ריין",
            cmd="לייג אריין ריין",
            func=lambda _: self.paste_plain(),
            tip="לייג אריין טעקסט אן קיין אויסשטעל",
            id="paste_plain"
        )
        self.buttons.append(paste_plain_btn)

        # Hint
        hint_btn = self._editor_button(
            icon=None,
            label="רמז",
            cmd="רמז",
            func=lambda _: self.editor.web.eval("applyHint()"),
            tip="לייג צו א רמז צום אויסגעקליבענעם טעקסט (דריקט דערויף ביים חזרן אים צו ווייזן)",
            id="hint_btn",
        )
        self.buttons.append(hint_btn)

        # Preset Buttons (S1-S5)
        presets = self.config.get("style_presets", [])
        # אם אין, מייצרים דמה כדי שיהיו כפתורים
        while len(presets) < 5:
            presets.append({"font": "Arial", "size": "20pt", "color": "black"})

        for i in range(5):
            # הלייבל הראשוני הוא "א", אבל העיצוב יתעדכן ב-update_preset_buttons_style
            label = "א"
            presets[i] if i < len(presets) else {}

            # פונקציה שתמיד מושכת את ההגדרה העדכנית לפי האינדקס
            def on_click(editor, idx=i):
                # קריאה מחדש של הקונפיגורציה כדי לוודא שמשתמשים במידע עדכני
                current_conf = mw.addonManager.getConfig(__name__)
                current_presets = current_conf.get("style_presets", [])
                if idx < len(current_presets):
                    self.apply_preset(current_presets[idx])

            btn = self._editor_button(
                icon=None,
                label=label,
                cmd=f"preset_{i}",
                func=on_click,
                tip="לאדט...",
                keys="",
                id=f"preset_{i}"
            )
            self.buttons.append(btn)
            # שמירה ברשימה נפרדת כדי שנוכל לעדכן אותם ויזואלית
            self.preset_buttons.append(btn)

    def apply_preset_by_index(self, idx):
        # קריאה מחדש של הקונפיגורציה כדי למנוע מצב של מידע ישן
        current_conf = mw.addonManager.getConfig(__name__)
        current_presets = current_conf.get("style_presets", [])
        if idx < len(current_presets):
            self.apply_preset(current_presets[idx])


class ExtraMenu(QMenu):
    def __init__(self, *__args) -> None:
        super().__init__(*__args)
        self.q_menu = self
        self.set_style()

    def set_style(self):
        self.q_menu.setWindowFlags(
            self.q_menu.windowFlags()
            | QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.NoDropShadowWindowHint
        )
        self.q_menu.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.q_menu.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.q_menu.setAutoFillBackground(False)
        (background_color, foreground_color, hover_color) = get_colors()
        stylesheet = menu_stylesheet_template.format(
            background=background_color,
            foreground=foreground_color,
            hover_color=hover_color,
        )
        self.q_menu.setStyleSheet(stylesheet)

    def add_action(self, label, func, stylesheet: str | None):
        if stylesheet:
            label_widget = QLabel(label)
            label_widget.setStyleSheet(stylesheet)
            action = QWidgetAction(self.q_menu)
            action.setDefaultWidget(label_widget)
        else:
            action = QAction(label, self.q_menu)
        action.triggered.connect(func)
        self.q_menu.addAction(action)

    def show(self):
        self.q_menu.exec(QCursor.pos())


def setupEditorButtons(buttons, editor):
    extra_commands = ExtraEditorCommands(editor)
    buttons.extend(extra_commands.buttons)


def _reload_config():
    # #138 — נקודת כניסה ל-shortcut-manager כדי לרענן קונפיג וקיצורי פריסטים בלי לפתוח את Anki מחדש.
    new_config = mw.addonManager.getConfig(__name__) or {}
    dead = []
    for inst in list(ExtraEditorCommands._instances):
        try:
            inst.refresh_shortcuts(new_config)
        except Exception as e:
            if inst.editor.widget is None or sip.isdeleted(inst.editor.widget):
                dead.append(inst)
                continue
            logger.warning(f"Font shortcuts were not refreshed in an editor: {e}", exc_info=True)
            from _shared_libs.haf_notifications import warn_once
            warn_once("font-size:shortcuts", "מען קען נישט דערהיינטיגן קיצורים אין איינעם פון די רעדאקטירער פענסטער. פארמאכט און עפנט אים פון פריש כדי די איינשטעלונגען זאלן אריינגיין.")
    for inst in dead:
        ExtraEditorCommands._instances.remove(inst)


gui_hooks.editor_did_init_buttons.append(setupEditorButtons)

mw.addonManager.setWebExports(__name__, r"js/.+(\.js|)")
ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)


def insert_js(web_content, context):
    if isinstance(context, Editor):
        # #161 — editor and reviewer use the same arrow/selection implementation.
        from _shared_libs.haf_rtl import inject_rtl_editing
        inject_rtl_editing(web_content)
        web_content.js.append(f"/_addons/{ADDON_PACKAGE}/js/editor.js")


webview_will_set_content.append(insert_js)


def on_editor_loaded(editor):
    """
    ווערט אויפגערופן יעדעס מאל ווען א רשומה ווערט געלאדנט אינעם רעדאקטירער via hook.
    דאס איז די זיכערסטע צייט צו דערהיינטיגן די קנעפלעך.
    """
    for inst in list(ExtraEditorCommands._instances):
        if inst.editor is editor:
            inst._install_deferred_editor_shortcuts()
            inst._install_preset_shortcuts()
            inst.schedule_preset_buttons_style_update()
            return


gui_hooks.editor_did_load_note.append(on_editor_loaded)


# =========================================================
# כפתור רמז — הצגה בזמן חזרה
# =========================================================
_REVIEWER_HINT_JS = """
(function() {  /* haf-hint reviewer toggle v2 */
    var isDark = document.body.classList.contains('nightMode') ||
                 document.documentElement.classList.contains('night-mode') ||
                 document.body.getAttribute('data-bs-theme') === 'dark';

    var SHOW_COLOR  = isDark ? '#5aafff' : '#0070c9';
    var SHOWN_BG    = isDark ? 'rgba(90,175,255,0.10)' : 'rgba(0,112,201,0.07)';
    var BRACKET_CLR = isDark ? '#888' : '#aaa';
    var EDIT_BG     = isDark ? 'rgba(90,175,255,0.13)' : 'rgba(0,112,201,0.09)';

    /* -------------------------------------------------------
       CSS ריין פאר פעלדער EFDRC ביים רעדאקטירן
       ווען contenteditable="true": באהאלט toggle buttons,
       ווייזט דעם אריגינעלן טעקסט (visibleWrap) אין א בלויעם אויסשטעל
       !important איז שטערקער inline style — אן א טויש DOM אינעם כלל
       ------------------------------------------------------- */
    if (!document.getElementById('haf-hint-edit-css')) {
        var s = document.createElement('style');
        s.id = 'haf-hint-edit-css';
        s.textContent = (
            'span.haf-hint-x-btn { display: none; }' +
            '[data-EFDRCfield].haf-field-editing span.haf-hint > span.haf-show-btn {' +
            '  display: none !important;' +
            '}' +
            '[data-EFDRCfield].haf-field-editing span.haf-hint > span.haf-visible-wrap {' +
            '  display: inline !important;' +
            '  background: transparent !important;' +
            '  cursor: text !important;' +
            '}' +
            '[data-EFDRCfield].haf-field-editing span.haf-hint > span.haf-hint-x-btn {' +
            '  display: inline !important;' +
            '  cursor: pointer;' +
            '  color: #c00;' +
            '  font-size: 0.8em;' +
            '  font-weight: bold;' +
            '  margin-right: 2px;' +
            '  vertical-align: middle;' +
            '  user-select: none;' +
            '  unicode-bidi: isolate;' +
            '}' +
            '[data-EFDRCfield][contenteditable="true"] span.haf-hint {' +
            '  color: ' + SHOW_COLOR + ' !important;' +
            '  background: ' + EDIT_BG + ' !important;' +
            '  border-bottom: 2px dashed ' + SHOW_COLOR + ' !important;' +
            '  border-radius: 2px;' +
            '  cursor: text;' +
            '  unicode-bidi: isolate;' +
            '}'
        );
        document.head.appendChild(s);
    }

    /* -------------------------------------------------------
       Toggle פאר אלע רמזים
       ------------------------------------------------------- */
    function applyToggle(hint) {
        var savedHTML = hint.getAttribute('data-hint-original') || hint.innerHTML;
        if (!hint.getAttribute('data-hint-original')) {
            hint.setAttribute('data-hint-original', savedHTML);
        }
        hint.setAttribute('data-hint-done', '1');
        hint.setAttribute('contenteditable', 'false');
        // #16 — אפגעזונדערונג BiDi האלט דעם קנעפל-X ו"ווייז רמז" פון זיך צו רוקן ווען דער רמז אנטהאלט נומערן/ענגליש
        hint.style.unicodeBidi = 'isolate';
        hint.innerHTML = '';

        var showBtn = document.createElement('span');
        showBtn.className = 'haf-show-btn';
        showBtn.textContent = '[ ווייז רמז ]';
        showBtn.style.cssText = (
            'cursor:pointer;color:' + SHOW_COLOR + ';' +
            'border:1px solid ' + SHOW_COLOR + ';border-radius:4px;' +
            'padding:1px 6px;font-size:0.85em;font-family:sans-serif;display:inline-block;' +
            'unicode-bidi:isolate;'
        );

        var bracketOpen = document.createElement('span');
        bracketOpen.textContent = '[';
        bracketOpen.style.cssText = 'color:' + BRACKET_CLR + ';font-size:0.9em;margin-left:2px;';

        var textSpan = document.createElement('span');
        textSpan.innerHTML = savedHTML;

        var bracketClose = document.createElement('span');
        bracketClose.textContent = ']';
        bracketClose.style.cssText = 'color:' + BRACKET_CLR + ';font-size:0.9em;margin-right:2px;';

        var visibleWrap = document.createElement('span');
        visibleWrap.className = 'haf-visible-wrap';
        visibleWrap.style.cssText = 'cursor:pointer;background:' + SHOWN_BG + ';border-radius:3px;padding:0 2px;unicode-bidi:isolate;';
        visibleWrap.title = 'דריקט צו באהאלטן';
        visibleWrap.appendChild(bracketOpen);
        visibleWrap.appendChild(textSpan);
        visibleWrap.appendChild(bracketClose);
        visibleWrap.style.display = 'none';

        var xBtn = document.createElement('span');
        xBtn.className = 'haf-hint-x-btn';
        xBtn.textContent = '✕';
        xBtn.title = 'נעמט אוועק דעם רמז — דער טעקסט בלייבט';
        xBtn.onmousedown = function(e) {
            e.preventDefault();
            e.stopPropagation();
        };
        xBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            var h = hint;
            setTimeout(function() {
                if (!h.parentNode) return;
                var orig = h.getAttribute('data-hint-original') || '';
                var tmp = document.createElement('span');
                tmp.innerHTML = orig;
                while (tmp.firstChild) {
                    h.parentNode.insertBefore(tmp.firstChild, h);
                }
                h.parentNode.removeChild(h);
            }, 0);
        };

        showBtn.addEventListener('mousedown', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
        showBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            showBtn.style.display = 'none';
            visibleWrap.style.display = 'inline';
        });
        visibleWrap.addEventListener('mousedown', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
        visibleWrap.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            visibleWrap.style.display = 'none';
            showBtn.style.display = 'inline';
        });

        hint.appendChild(showBtn);
        hint.appendChild(visibleWrap);
        hint.appendChild(xBtn);
    }

    function applyAllToggles() {
        document.querySelectorAll('span.haf-hint:not([data-hint-done])').forEach(applyToggle);
    }

    applyAllToggles();

    /* -------------------------------------------------------
       Observer אלגעמיין פאר נייע רמזים:
       כאפט דעם אויסמאלן/איבערבייטן HTML נאכן לאדענען א קארטל און לייגט ארויף toggle
       אויך ווען-EFDRC ברענגט די פעלדער שפעט
       ------------------------------------------------------- */
    if (!window._hafHintObserver) {
        window._hafHintObserver = new MutationObserver(function(mutations) {
            var shouldApply = false;
            mutations.forEach(function(m) {
                if (m.type !== 'childList') return;
                m.addedNodes.forEach(function(node) {
                    if (shouldApply || !node || node.nodeType !== 1) return;
                    if (
                        (node.matches && node.matches('span.haf-hint:not([data-hint-done])')) ||
                        (node.querySelector && node.querySelector('span.haf-hint:not([data-hint-done])'))
                    ) {
                        shouldApply = true;
                    }
                });
            });
            if (shouldApply) {
                applyAllToggles();
            }
        });
        window._hafHintObserver.observe(document.body, { childList: true, subtree: true });
    }

    /* נאך א קורצער דורכגאנג נאכן לאדענען, כדי צו דעקן שפעטע אריינלייגונגען */
    setTimeout(applyAllToggles, 0);
    setTimeout(applyAllToggles, 150);
    setTimeout(applyAllToggles, 500);

    /* -------------------------------------------------------
       MutationObserver: לייג צו/נעם אוועק haf-field-editing נאר לויט
       contenteditable — נישט לויטן פאקוס, כדי דער-X זאל נישט בלינקען
       ------------------------------------------------------- */
    function setXBtnsVisible(fieldEl, show) {
        fieldEl.querySelectorAll('span.haf-hint > span.haf-hint-x-btn').forEach(function(btn) {
            btn.style.setProperty('display', show ? 'inline' : 'none', 'important');
        });
    }

    function applyToggleAndShowX(fieldEl) {
        /* שאלט אן applyToggle אויף נייע רמזים (אן data-hint-done) */
        fieldEl.querySelectorAll('span.haf-hint:not([data-hint-done])').forEach(applyToggle);
        /* ווייז X אויף אלע רמזים אינעם פעלד */
        setXBtnsVisible(fieldEl, true);
    }

    function watchEditableField(fieldEl) {
        if (fieldEl._hafEditWatching) return;
        fieldEl._hafEditWatching = true;

        fieldEl.addEventListener('focus', function() {
            fieldEl.classList.add('haf-field-editing');
            /* אויך אויב EFDRC וועט איבערבייטן innerHTML נאכדעם וואס focus, דער היטער וועט זיך דערמיט זארגן */
            applyToggleAndShowX(fieldEl);
        });

        /* MutationObserver אויפן פעלד אינהאלט:
           EFDRC טוישט innerHTML ב-showRawField נאכדעם וואס focus —
           ווען דאס פאסירט ביים רעדאקטירן, לויפט מען applyToggle פון פריש */
        new MutationObserver(function(mutations) {
            var isEditing = fieldEl.classList.contains('haf-field-editing');
            var hasChildChanges = mutations.some(function(m) { return m.type === 'childList'; });
            if (isEditing && hasChildChanges) {
                /* setTimeout כדי צו געבן-EFDRC צו פארענדיגן דעם-innerHTML replace */
                setTimeout(function() { applyToggleAndShowX(fieldEl); }, 0);
            }
        }).observe(fieldEl, { childList: true, subtree: false });

        /* נעמט אוועק דעם קלאס ווען דער פעלד פארמאכט זיך צום רעדאקטירן */
        new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                if (m.attributeName !== 'contenteditable') return;
                if (fieldEl.getAttribute('contenteditable') !== 'true') {
                    fieldEl.classList.remove('haf-field-editing');
                    setXBtnsVisible(fieldEl, false);
                }
            });
        }).observe(fieldEl, { attributes: true });
    }
    document.querySelectorAll('[data-EFDRCfield]').forEach(watchEditableField);
    if (!window._hafEditFieldWatcher) {
        window._hafEditFieldWatcher = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                m.addedNodes.forEach(function(node) {
                    if (node.nodeType !== 1) return;
                    if (node.hasAttribute('data-EFDRCfield')) watchEditableField(node);
                    node.querySelectorAll && node.querySelectorAll('[data-EFDRCfield]').forEach(watchEditableField);
                });
            });
        });
        window._hafEditFieldWatcher.observe(document.body, { childList: true, subtree: true });
    }

    /* -------------------------------------------------------
       patch ל-EFDRC.showRawField:
       EFDRC טוישט innerHTML נאכן לאדענען/אויפפרישן א פעלד,
       דערפאר דארף מען עס ווידער צולייגן toggle אויף span.haf-hint נייע
       ------------------------------------------------------- */
    if (!window._hafShowRawFieldPatchTimer) {
        window._hafShowRawFieldPatchTimer = setInterval(function() {
            if (!window.EFDRC || typeof window.EFDRC.showRawField !== 'function') return;
            if (window.EFDRC._hafShowRawFieldPatched) {
                clearInterval(window._hafShowRawFieldPatchTimer);
                window._hafShowRawFieldPatchTimer = null;
                return;
            }

            var _origShowRawField = window.EFDRC.showRawField;
            window.EFDRC.showRawField = function() {
                var ret = _origShowRawField.apply(this, arguments);
                applyAllToggles();

                var active = document.activeElement;
                if (active && active.matches && active.matches('[data-EFDRCfield].haf-field-editing')) {
                    applyToggleAndShowX(active);
                }
                return ret;
            };
            window.EFDRC._hafShowRawFieldPatched = true;
            clearInterval(window._hafShowRawFieldPatchTimer);
            window._hafShowRawFieldPatchTimer = null;
        }, 200);
    }

    /* -------------------------------------------------------
       pycmd patch — ברענגט צוריק HTML ריין צום אפזיכערן
       ------------------------------------------------------- */
    if (!window._hafHintPycmdPatched) {
        window._hafHintPycmdPatched = true;

        function _hafCleanHintHtml(html) {
            var div = document.createElement('div');
            div.innerHTML = html;
            div.querySelectorAll('span.haf-hint').forEach(function(el) {
                var orig = el.getAttribute('data-hint-original') || el.innerHTML;
                el.removeAttribute('data-hint-done');
                el.removeAttribute('data-hint-original');
                el.removeAttribute('contenteditable');
                el.removeAttribute('style');
                el.querySelectorAll('.haf-show-btn, .haf-visible-wrap, .haf-hint-x-btn').forEach(function(c) { c.remove(); });
                el.innerHTML = orig;
            });
            return div.innerHTML;
        }

        function _hafB64Decode(s) {
            return decodeURIComponent(window.atob(s).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
        }
        function _hafB64Encode(s) {
            return window.btoa(encodeURIComponent(s).replace(/%([0-9A-F]{2})/g, function(_m, h) {
                return String.fromCharCode('0x' + h);
            }));
        }

        var _origPycmd = window.pycmd;
        window.pycmd = function(msg) {
            if (typeof msg !== 'string') return _origPycmd(msg);

            if (msg.startsWith('EFDRC!save64#') || msg.startsWith('EFDRC!savefinal64#')) {
                var i1 = msg.indexOf('#');
                var i2 = msg.indexOf('#', i1 + 1);
                var i3 = msg.indexOf('#', i2 + 1);
                if (i3 !== -1) {
                    var encoded = msg.substring(i3 + 1);
                    try {
                        var html = _hafB64Decode(encoded);
                        if (html.indexOf('haf-hint') !== -1) {
                            html = _hafCleanHintHtml(html);
                            msg = msg.substring(0, i3 + 1) + _hafB64Encode(html);
                        }
                    } catch(e) {}
                }
            } else if (msg.startsWith('EFDRC!save#') || msg.startsWith('EFDRC#')) {
                var i1 = msg.indexOf('#');
                var i2 = msg.indexOf('#', i1 + 1);
                var i3 = msg.indexOf('#', i2 + 1);
                if (i3 !== -1) {
                    var html = msg.substring(i3 + 1);
                    if (html.indexOf('haf-hint') !== -1) {
                        html = _hafCleanHintHtml(html);
                        msg = msg.substring(0, i3 + 1) + html;
                    }
                }
            }
            return _origPycmd(msg);
        };
    }
})();
"""


def _setup_reviewer_hint(card):
    mw.reviewer.web.eval(_REVIEWER_HINT_JS)


gui_hooks.reviewer_did_show_question.append(_setup_reviewer_hint)
gui_hooks.reviewer_did_show_answer.append(_setup_reviewer_hint)


