import contextlib
import html
import json
import os

from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction, QColor, QCursor, QIcon, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import QColorDialog, QToolBar, QToolButton

from .ankiaddonconfig import ConfigManager

def _module_addon_id() -> str:
    # #138 — מזהה התוסף נלקח דרך Anki כשאפשר, כדי שגם ייבוא עם שם מודול פנימי יקרא את אותו config של shortcut-manager.
    try:
        return mw.addonManager.addonFromModule(__name__)
    except Exception:
        return __name__.split(".")[0]


# #138 — קונפיג edit-field-review נקרא לפי מזהה התוסף כדי ש-shortcut-manager יכתוב ו-editbar יקרא מאותו מקום.
MODULE_ADDON = _module_addon_id()
config = mw.addonManager.getConfig(MODULE_ADDON)
icons_dir = os.path.join(os.path.dirname(__file__), 'color_icons')
color_buttons = {}

# #269 — מברשת עיצוב לחזרה: לחיצה ראשונה מעתיקה עיצוב מהבחירה, לחיצה שנייה מדביקה אותו.
_HAF_REVIEW_PAINTER_JS = """
(function() {
    if (typeof window._hafPainterReady === 'undefined') {
        window._hafPainterReady = true;
        window._hafPainterActive = false;
        window._hafPainterStyles = null;
        document.addEventListener('mouseup', function() {
            if (!window._hafPainterActive) return;
            var sel = document.getSelection();
            if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return;
            var s = window._hafPainterStyles;
            if (!s) return;
            window._hafPainterActive = false;
            document.body.style.cursor = '';
            var entries = [];
            if (s.color) entries.push(['color', s.color]);
            if (s.backgroundColor && s.backgroundColor !== 'rgba(0, 0, 0, 0)') entries.push(['background-color', s.backgroundColor]);
            if (s.fontSize) entries.push(['font-size', s.fontSize]);
            if (s.fontWeight) entries.push(['font-weight', s.fontWeight]);
            if (s.fontStyle && s.fontStyle !== 'normal') entries.push(['font-style', s.fontStyle]);
            if (s.textDecoration && s.textDecoration !== 'none') entries.push(['text-decoration', s.textDecoration]);
            if (s.fontFamily) entries.push(['font-family', s.fontFamily]);
            if (!entries.length) return;
            var range = sel.getRangeAt(0);
            var content = range.cloneContents();
            var span = document.createElement('span');
            entries.forEach(function(e) { span.style.setProperty(e[0], e[1], 'important'); });
            span.appendChild(content);
            document.execCommand('insertHTML', false, span.outerHTML);
        });
    }
    if (window._hafPainterActive) {
        window._hafPainterActive = false;
        document.body.style.cursor = '';
        return;
    }
    var sel = document.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) { return; }
    var el = sel.getRangeAt(0).startContainer;
    if (el.nodeType === 3) el = el.parentElement;
    var cs = window.getComputedStyle(el);
    window._hafPainterStyles = {
        color: cs.color,
        backgroundColor: cs.backgroundColor,
        fontSize: cs.fontSize,
        fontWeight: cs.fontWeight,
        fontStyle: cs.fontStyle,
        textDecoration: cs.textDecoration,
        fontFamily: cs.fontFamily
    };
    window._hafPainterActive = true;
    document.body.style.cursor = 'copy';
})();
"""

_EFDRC_APPLY_HINT_JS = """
(function() {
    var sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return;
    var range = sel.getRangeAt(0);
    var content = range.cloneContents();
    var span = document.createElement('span');
    span.className = 'haf-hint';
    span.appendChild(content);
    document.execCommand('insertHTML', false, span.outerHTML);
})();
"""


def get_config(arg, fail=False):
    # #138 — שימוש עקבי במזהה התוסף מונע ניתוק בין עורך קיצורי המקשים לבין כפתורי edit-field-review.
    conf = ConfigManager().copy()
    if conf:
        if arg == "fontcolor":
            return conf["סרגל טעקסט קאליר"]
        elif arg == "fontbgcolor":
            return conf["פיל קאליר"]
        else:
            return conf
    else:
        return fail


def getnewcolor(button="", command=""):
    """
    Handles color picking via modal, ensuring JS state (focus/selection)
    is preserved and restored correctly.
    """
    if button == "fontcolor":
        action = color_buttons.get(0)
        current_ = get_config("fontcolor")
        icon = "border_color.png"
    else:
        action = color_buttons.get(1)
        current_ = get_config("fontbgcolor")
        icon = "format_color_fill.png"

    if not action:
        return

    # Notify JS: Stop blur/save events, save current selection
    mw.reviewer.web.eval("EFDRC.prepareForModal();")

    color_window = QColorDialog()
    qcolor = QColor(0, 0, 0)
    if current_:
        qcolor.setNamedColor(current_)

    color = color_window.getColor(qcolor, mw)

    # **Critical Fix**: Force focus back to webview immediately after dialog closes
    # This ensures the browser is ready to receive JS commands
    mw.reviewer.web.setFocus()

    if color.isValid():
        color_name = color.name()
        changebuttoncolor(action, color_name, icon)

        conf = get_config("")
        if button == "fontcolor":
            conf["סרגל טעקסט קאליר"] = color_name
        else:
            conf["פיל קאליר"] = color_name
        # #138 — צבעי סרגל edit-field-review נשמרים באותו קונפיג ש-shortcut-manager מעדכן.
        mw.addonManager.writeConfig(MODULE_ADDON, conf)

        # Notify JS: Restore selection, Ensure Editable, Exec Command, Save
        if command:
            mw.reviewer.web.eval(f'EFDRC.finishModal("{command}", "{color_name}")')
        else:
            mw.reviewer.web.eval('EFDRC.finishModal("", "")')

    else:
        # Cancelled: Just restore state without executing
        mw.reviewer.web.eval('EFDRC.finishModal("", "")')


def changebuttoncolor(action, color, icon):
    if isinstance(icon, str):
        pixmap = QPixmap(20, 20)
        pixmap.load(os.path.join(icons_dir, icon))
    else:
        pixmap = icon
    qcolour = QColor(50, 100, 0)
    qcolour.setNamedColor(color)
    tmp = pixmap.toImage()
    height = 0
    while height < tmp.height():
        width = 0
        while width < tmp.width():
            qcolour.setAlpha(tmp.pixelColor(width, height).alpha())
            tmp.setPixelColor(width, height, qcolour)
            width += 1
        height += 1
    pixmap = QPixmap.fromImage(tmp)
    action.setIcon(QIcon(pixmap))


def execCommand(command, color):
    return f'document.execCommand("{command}", false, "{color}")'


def fnt_clr_btn(reviewer, command, action, arg):
    color = get_config(arg)
    if arg == "fontcolor":
        color_buttons[0] = action
        icon = "border_color.png"
        action.triggered.connect(lambda: reviewer.web.eval(f"{execCommand(command, get_config(arg))}"))
    else:
        color_buttons[1] = action
        icon = "format_color_fill.png"
        action.triggered.connect(lambda: reviewer.web.eval(f"{execCommand(command, get_config(arg))}"))
    changebuttoncolor(action, color, icon)
    return action


special_formatting = {
    "אונטערשטרייכן": {
        "arg": None,
        "command": "underline",
        "icon": "format_underlined.png"
    },
    "שיף": {
        "arg": None,
        "command": "italic",
        "icon": "format_italic.png"
    },
    "דיק": {
        "arg": None,
        "command": "bold",
        "icon": "format_bold.png"
    },
    "Separator6": "",
    "אונטערשריפט": {
        "arg": None,
        "command": "subscript",
        "icon": "subscript.png"
    },
    "אויבערשריפט": {
        "arg": None,
        "command": "superscript",
        "icon": "superscript.png"
    },
    "Separator3": "",
    "הינטערגרונט קאליר פונעם טעקסט": {
        "arg": None,
        "command": "hiliteColor",
        "icon": "fontbgcolor"
    },
    "קלייבט אויס דעם טעקסט הינטערגרונט קאליר": {
        "arg": "func",
        "command": lambda: getnewcolor("fontbgcolor", "hiliteColor"),
        "icon": "arrow_drop_down.png"
    },
    "טעקסט קאליר": {
        "arg": None,
        "command": "foreColor",
        "icon": "fontcolor"
    },
    "קלייבט אויס דעם טעקסט קאליר": {
        "arg": "func",
        "command": lambda: getnewcolor("fontcolor", "foreColor"),
        "icon": "arrow_drop_down.png"
    },
    "Separator2": "",
    "נעם אוועק דעם אויסשטעל": {
        "arg": None,
        "command": "removeFormat",
        "icon": "format_clear.png"
    },
    "Separator4": "",
    "אויסריכטן צו ביידע זייטן": {
        "arg": None,
        "command": "justifyFull",
        "icon": "format_align_justify.png"
    },
    "אויסריכטן רעכטס": {
        "arg": None,
        "command": "justifyRight",
        "icon": "format_align_right.png"
    },
    "אויסריכטן אין מיטן": {
        "arg": None,
        "command": "justifyCenter",
        "icon": "format_align_center.png"
    },
    "אויסריכטן לינקס": {
        "arg": None,
        "command": "justifyLeft",
        "icon": "format_align_left.png"
    },
    "Separator1": "",
    "ליסטע": {
        "arg": None,
        "command": "insertUnorderedList",
        "icon": "format_list_bulleted.png"
    },
    "נומערירטע ליסטע": {
        "arg": None,
        "command": "insertOrderedList",
        "icon": "format_list_numbered.png"
    },
    "רוק מער אריין (נאר אין א ליסטע)": {
        "arg": None,
        "command": "indent",
        "icon": "format_indent_decrease.png"
    },
    "רוק ווייניגער אריין (נאר אין א ליסטע)": {
        "arg": None,
        "command": "outdent",
        "icon": "format_indent_increase.png"
    },
    "Separator5": "",
    "דורכשטרייכן": {
        "arg": None,
        "command": "strikeThrough",
        "icon": "format_strikethrough.png"
    }
}
non_colors_actions = []

# #354 — קיצור שנקלט כשהמקלדת במצב עברית נשמר עם אות עברית, אבל בזמן לחיצה Qt מדווח
# (בצירופי Ctrl/Alt) את המקש הלטיני של אותה פריסה — ולכן הקיצור לא הופעל, ולחיצה על אות
# בודדת רק הקלידה אותה. רושמים את הקיצור גם בווריאנט הלטיני לפי פריסת המקלדת העברית התקנית.
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
        return variants
    converted = "+".join(HEBREW_TO_LATIN_KEY.get(part, part) for part in key.split("+"))
    if converted != key:
        variants.append(converted)
    return variants


# #138 — validate at runtime too: old configs bypass the settings dialog.
def _safe_review_preset_shortcut(value):
    key = str(value or "").strip()
    if key.lower() in {"", "none", "<nop>", "<default>"}:
        return ""
    parts = [part.strip().lower() for part in key.split("+") if part.strip()]
    if parts and len(parts[-1]) == 1 and parts[-1].isalpha() and not {"ctrl", "control", "alt"}.intersection(parts):
        return ""
    return key


def _font_size_style_presets():
    for addon_id in ("font-size", "font_size"):
        with contextlib.suppress(Exception):
            config = mw.addonManager.getConfig(addon_id) or {}
            presets = config.get("style_presets", [])
            if presets:
                return presets
    return []


def _apply_style_preset_in_review(reviewer, idx):
    presets = _font_size_style_presets()
    if idx >= len(presets):
        return
    preset_json = json.dumps(presets[idx], ensure_ascii=False)
    reviewer.web.eval(f"""
        (function(preset) {{
            if (typeof applyReviewStylePreset !== "function") return;
            applyReviewStylePreset(preset);
            if (!window.EFDRC || typeof EFDRC.scheduleAutoSave !== "function") return;
            const active = document.activeElement && document.activeElement.closest
                ? document.activeElement.closest("[data-EFDRCfield]")
                : null;
            const field = active || EFDRC.activeEditableField;
            if (field) EFDRC.scheduleAutoSave(field);
        }})({preset_json});
    """)


def _make_preset_icon(label: str, color: str, font_name: str, size_str: str, bold: bool, italic: bool = False, underline: bool = False, bg: str = "") -> "QIcon":
    """שאפט QIcon וואס ווייזט דעם מוסטער נאמען מיט א קאליר, שריפט, הינטערגרונט, שיף און אונטערגעשטרייכן."""
    from PyQt6.QtCore import QRect, Qt
    from PyQt6.QtGui import QFont, QPainter
    # #269 — פיקסמאפ פריסט בגודל הכפתור עצמו, כדי שהדוגמה תמלא את המסגרת ולא תופיע כטקסט קטן עם שוליים גדולים.
    dpr = mw.devicePixelRatio() if hasattr(mw, "devicePixelRatio") else 1.0
    base_w, base_h = 30, 30
    px = QPixmap(int(base_w * dpr), int(base_h * dpr))
    px.setDevicePixelRatio(dpr)
    # #269 — רקע: צבע הפריסט אם מוגדר, אחרת לבן (כך הסגנון תמיד גלוי)
    bg_color = QColor(bg) if bg else QColor(Qt.GlobalColor.white)
    if not bg_color.isValid():
        bg_color = QColor(Qt.GlobalColor.white)
    px.fill(bg_color)
    painter = QPainter(px)
    try:
        # #269 — מסגרת דקה כדי להבדיל כפתור מרקע הסרגל
        painter.setPen(QColor("#bbbbbb"))
        painter.drawRect(0, 0, base_w - 1, base_h - 1)
        size_num = int("".join(filter(str.isdigit, str(size_str))) or "0")

        qfont = QFont()
        if font_name:
            qfont.setFamily(font_name)
        # #269 — גודל הגופן בנקודות; גלוי ומייצג (קודם הוגבל לגודל קטן מדי).
        qfont.setPointSize(max(min(size_num or 15, 22), 12))
        if bold:
            qfont.setBold(True)
        if italic:
            qfont.setItalic(True)
        if underline:
            qfont.setUnderline(True)
        painter.setFont(qfont)
        qcolor = QColor(color) if color else QColor(Qt.GlobalColor.black)
        if not qcolor.isValid():
            qcolor = QColor(Qt.GlobalColor.black)
        painter.setPen(qcolor)
        painter.drawText(QRect(2, 1, base_w - 4, base_h - 2), Qt.AlignmentFlag.AlignCenter, (label or "א")[:5])
    finally:
        if painter.isActive():
            painter.end()
    return QIcon(px)


def _add_style_preset_buttons(reviewer, toolbar):
    presets = _font_size_style_presets()
    if not presets:
        return
    for shortcut in getattr(reviewer, "_haf_review_preset_qshortcuts", []):
        with contextlib.suppress(Exception):
            shortcut.setEnabled(False)
            shortcut.deleteLater()
    reviewer._haf_review_preset_qshortcuts = []
    toolbar.addSeparator()

    # --- מברשת עיצוב (#269) ---
    painter_action = QAction("🖌", mw)
    painter_action.setToolTip("אויסשטעל בערשטל — קלייבט אויס דעם מקור טעקסט, דריקט, און קלייבט דערנאך אויס דעם ציל טעקסט")
    painter_action.triggered.connect(lambda: reviewer.web.eval(_HAF_REVIEW_PAINTER_JS))
    non_colors_actions.append(painter_action)
    toolbar.addAction(painter_action)

    # #138 — review bindings have their own explicit configuration.
    _efdrc_cfg = mw.addonManager.getConfig(MODULE_ADDON) or {}
    _review_preset_shortcuts: dict = _efdrc_cfg.get("review_preset_shortcuts") or {}

    for idx, preset in enumerate(presets[:5]):
        # #348: ברירת המחדל לכיתוב על כפתור פריסט היא "א" במקום S1/S2... — אות עברית
        # שמדגימה את עיצוב הפריסט (צבע, גופן, הדגשה) בצורה מוחשית.
        # אצל משתמשים שכבר התקינו את התוסף, config.json שלהם שמור עם הלייבל הישן
        # ("S1".."S5") ולכן bump גרסה בלבד לא מספיק — deploy.py משמר config.json קיים
        # בכוונה (סעיף 8 ב-CLAUDE.md). לכן ממירים כאן במפורש את הלייבל הישן הידוע,
        # בלי לגעת בכל לייבל אחר שמשתמש שינה בעצמו.
        raw_label = str(preset.get("label") or "").strip()
        label = "א" if (not raw_label or raw_label == f"S{idx + 1}") else raw_label
        action = QAction(label, mw)

        # #269 — הכפתור מציג את הלייבל בצבע, גופן, רקע וקו תחתון של הפריסט
        color_val = str(preset.get("color") or ("#ffffff" if theme_manager.night_mode else "#000000"))
        font_name = str(preset.get("font") or "")
        size_str = str(preset.get("size") or "14pt")
        bold = bool(preset.get("bold", False))
        italic = bool(preset.get("italic", False))
        underline = bool(preset.get("underline", False))
        # #269 — המפתח הנכון הוא bgColor (כפי שמוגדר ב-font-size addon)
        bg_val = str(preset.get("bgColor") or preset.get("background") or preset.get("bg") or "")
        # #269 — האייקון מייצג גם נטוי, כדי שהמשתמש יראה את סגנון הפריסט כבר בסרגל.
        action.setIcon(_make_preset_icon(label, color_val, font_name, size_str, bold, italic, underline, bg_val))

        # #269 — tooltip מפורט בעברית על כל מאפייני הסגנון
        import html as _html_mod
        tip_parts = []
        if size_str:
            tip_parts.append(f"גרייס: {_html_mod.escape(size_str)}")
        if font_name:
            tip_parts.append(f"שריפט: {_html_mod.escape(font_name)}")
        if color_val and color_val not in ("#000000", "#ffffff", "black", "white"):
            tip_parts.append(f"קאליר: {_html_mod.escape(color_val)}")
        if bg_val:
            tip_parts.append(f"הינטערגרונט: {_html_mod.escape(bg_val)}")
        if bold:
            tip_parts.append("דיק")
        if italic:
            tip_parts.append("שיף")
        if underline:
            tip_parts.append("אונטערשטרייכן")
        tip_body = "<br>".join(tip_parts)
        action.setToolTip(f"<b>סטיל {idx + 1}: {_html_mod.escape(label)}</b>" + ("<br>" + tip_body if tip_body else ""))

        # #138 — an empty review binding disables it; editor bindings belong
        # to a different window and must not silently become review bindings.
        shortcut_key = _safe_review_preset_shortcut(
            _review_preset_shortcuts.get(f"preset_{idx + 1}", "")
        )
        # אישיו #400: שומרים את טולטיפ הבסיס ומוסיפים לו את הקיצור הפעיל.
        action.setProperty("hafShortcutTooltipBase", action.toolTip())
        if shortcut_key:
            action.setToolTip(
                action.toolTip()
                + f"<br><b>קיצור: {html.escape(shortcut_key)}</b>"
            )
        # #bug-fix — לא מגדירים קיצור על ה-QAction של הפריסט כדי למנוע ambiguous shortcut:
        # QAction (WindowShortcut) + QShortcut (WidgetWithChildrenShortcut) על אותו מקש
        # גורמים ל-Qt לסמן ambiguous → אף אחד לא מופעל. נשתמש רק ב-QShortcut.
        shortcut = QShortcut(QKeySequence(shortcut_key), mw)
        # #354 — רישום גם וריאנט לטיני של אותיות עבריות כדי שהקיצור ייתפס בכל פריסת מקלדת.
        if shortcut_key:
            shortcut.setKeys([QKeySequence(v) for v in key_sequence_variants(shortcut_key)])
        # #138 — do not steal the same key from an open Add/Edit/Browser window.
        shortcut.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)
        shortcut.setEnabled(bool(shortcut_key and shortcut_key.lower() not in ("none", "<nop>")))
        shortcut.activated.connect(lambda i=idx: _apply_style_preset_in_review(reviewer, i))
        reviewer._haf_review_preset_qshortcuts.append(shortcut)

        action.setObjectName(f"review_preset_{idx + 1}")
        action.triggered.connect(lambda checked=False, i=idx: _apply_style_preset_in_review(reviewer, i))
        non_colors_actions.append(action)
        # #269 — משתמשים בכפתור ייעודי לפריסטים כדי שהאייקון המצויר יוצג כמעט בגודל מלא במקום להידחס ל-26px של הסרגל.
        preset_button = QToolButton(toolbar)
        preset_button.setDefaultAction(action)
        toolbar.addWidget(preset_button)

def tb_add_action(reviewer, toolbar, icon, tooltip, command, arg):
    action = QAction(mw)
    if icon == "fontbgcolor" or icon == "fontcolor":
        action = fnt_clr_btn(reviewer, command, action, icon)
        action.setToolTip(tooltip)
        toolbar.addAction(action)
        return
    else:
        non_colors_actions.append(action)
        color = "white" if theme_manager.night_mode else "black"
        changebuttoncolor(action, color, icon)
    action.setToolTip(tooltip)

    if arg == "func":
        action.triggered.connect(command)
    elif arg is not None:
        execCommand = f'document.execCommand("{command}", false, "{arg}")'
        action.triggered.connect(lambda: reviewer.web.eval(f"{execCommand}"))
    else:
        execCommand = f'document.execCommand("{command}", false)'
        action.triggered.connect(lambda: reviewer.web.eval(f"{execCommand}"))
    toolbar.addAction(action)


def add_more_toolbar(web_content, context):
    if isinstance(context, Reviewer):
        try:
            mw.reviewer.more_toolbar = QToolBar()
        except AttributeError:
            return
        toolbar = mw.reviewer.more_toolbar
        toolbar.setObjectName('more_toolbar')
        # #269 — אייקוני פריסטים צריכים מקום גדול מעט יותר כדי להציג גופן/גודל/קו תחתון בצורה קריאה.
        toolbar.setIconSize(QSize(26, 26))
        toolbar.setFloatable(True)
        toolbar.setMovable(True)
        for text in special_formatting:
            if text[:-1] == "Separator":
                toolbar.addSeparator()
            else:
                format = special_formatting[text]["command"]
                icon = special_formatting[text]["icon"]
                arg = special_formatting[text]["arg"]
                tb_add_action(reviewer=context,
                              toolbar=toolbar,
                              icon=icon,
                              tooltip=text,
                              command=format,
                              arg=arg)

        toolbar.addSeparator()
        menus = setupmenusButtons(context)
        for menu in menus:
            toolbar.addAction(menu)

        _add_style_preset_buttons(context, toolbar)

        # --- כפתור רמז ---
        toolbar.addSeparator()
        hint_action = QAction(mw)
        hint_action.setToolTip("רמז — נעמט ארום דעם אויסגעקליבענעם טעקסט מיט א באהאלטענעם רמז")
        non_colors_actions.append(hint_action)
        color = "white" if theme_manager.night_mode else "black"
        changebuttoncolor(hint_action, color, "hint_eye.png")
        hint_action.triggered.connect(
            lambda: context.web.eval(_EFDRC_APPLY_HINT_JS)
        )
        toolbar.addAction(hint_action)

        mw.mainLayout.insertWidget(2, toolbar)
        toolbar.hide()


gui_hooks.webview_will_set_content.append(add_more_toolbar)


# font style menus


from aqt import mw
from aqt.editor import Editor
from aqt.qt import *
from aqt.theme import theme_manager
from aqt.utils import showInfo
from PyQt6 import QtCore
from PyQt6.QtGui import QFont, QFontDatabase

RECENT_FONTS_LIMIT = 14

DARK_SHADE = "rgb(26, 26, 26)"
LIGHT_SHADE = "#d7d7d7"


def get_colors():
    background_color = (
        "#272828!important" if theme_manager.night_mode else "hsla(0, 0%, 98%, .9)"
    )
    foreground_color = LIGHT_SHADE if theme_manager.night_mode else DARK_SHADE
    hover_color = DARK_SHADE
    return (background_color, foreground_color, hover_color)


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
    text-align: center;
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
    font-size:14px;
    padding:1px 15px;
    margin:2px 10px;
}}
QLabel:hover {{
    color: {hover_color};
    background-color: rgb(195, 195, 195);
    border-radius: 4px;
}}"""


class ExtraEditorCommands:
    # #138 — שמירת מופעי סרגל פעילים מאפשרת לעדכן קיצורים קיימים לאחר שמירת shortcut-manager.
    _instances = []

    def __init__(self, editor) -> None:
        self.editor: Editor = editor
        self.create_buttons()
        # #138 — רשימת פונטים אחרונים נטענת מאותו config ראשי ש-shortcut-manager מעדכן.
        _raw_config = mw.addonManager.getConfig(MODULE_ADDON) or {}
        # #138 — שומרים את כל הקונפיג, אחרת שמירת recent_fonts מוחקת את קיצורי edit-field-review מהקובץ.
        self.config = _raw_config
        self.config.setdefault("recent_fonts", [])
        self.config.setdefault("prev_font", "")
        ExtraEditorCommands._instances.append(self)

    def set_style(self, style, val):
        arg = f'"{str(val)}"' if style == "font-family" else f'{str(val)}'
        self.editor.web.eval(f'setstyle("{style}", {arg});')

    def ensure_selection(self):
        # #140 — לא בוחרים את כל השדה כשאין טקסט מסומן; editorfontsize.js יודע להחיל סגנון על הסמן להמשך הקלדה.
        return True

    def set_size(self, size, menu):
        if size != '"unset"' and size > 1600:
            showInfo("מאקסימום גרייס: 1600")
            return
        if self.ensure_selection():
            self.set_style("font-size" ,size)
            menu.close()

    def set_font(self, font_name):
        self.config["prev_font"] = font_name
        if self.ensure_selection():
            self.set_style("font-family" ,font_name)

    def disable_action(self, menu, lineedit):
        if lineedit.text() != "":
            menu.lineedited =True

    def show_size_menu(self, editor):
        menu = ExtraMenu()
        custom_size = QLineEdit(menu.q_menu)
        custom_size.setMaximumWidth(60)
        custom_size.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        custom_size.setValidator(QIntValidator(0,1600))
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
        menu.installEventFilter(menu)
        menu.show()

    def show_font_menu(self, _editor):
        menu = ExtraMenu()
        (_, foreground_color, hover_color) = get_colors()
        for font_name in self.config["recent_fonts"]:
            menu.add_action(
                "אבגדהוזח   " + font_name,
                lambda _, fnt=font_name: self.set_font(fnt),
                stylesheet=font_label_stylesheet_template.format(
                    foreground_color=foreground_color,
                    font_name=font_name,
                    hover_color=hover_color,
                ),
                )
        menu.q_menu.addSeparator()

        hebrew_fonts = QFontDatabase.families(QFontDatabase.WritingSystem.Hebrew)
        if len(hebrew_fonts) < 2:
            hebrew_fonts = QFontDatabase.families()
        hebrew_fonts = sorted(hebrew_fonts)

        font_combo = QComboBox(menu.q_menu)
        font_combo.setMinimumWidth(200)
        font_combo.addItem("קלייבט אויס א שריפט...", None)
        for font_name in hebrew_fonts:
            font_combo.addItem(f"אבגדה - {font_name}", font_name)
            idx = font_combo.count() - 1
            font_combo.setItemData(idx, QFont(font_name), QtCore.Qt.ItemDataRole.FontRole)

        font_combo.currentIndexChanged.connect(
            lambda index: self._on_combo_font_selected(index, font_combo, menu)
        )
        font_widget = QWidgetAction(menu.q_menu)
        font_widget.setDefaultWidget(font_combo)
        menu.q_menu.addAction(font_widget)
        menu.show()

    def _on_combo_font_selected(self, index, combo, menu):
        font_name = combo.itemData(index)
        if font_name:
            self.set_font(font_name)
            self.add_recent_font(font_name)
            self.save_font_config()
            menu.q_menu.close()

    def save_font_config(self):
        # #138 — שמירת פונטים אחרונים לא חוזרת למזהה קשיח שיכול להתנתק מ-MODULE_ADDON.
        mw.addonManager.writeConfig(
            MODULE_ADDON,
            self.config,
        )


    def add_recent_font(self, font_name):
        recent_fonts = self.config["recent_fonts"]
        if font_name not in recent_fonts:
            recent_fonts.append(font_name)
            while len(recent_fonts) > RECENT_FONTS_LIMIT:
                del recent_fonts[0]

    def create_buttons(self) -> None:
        # #138 — קיצורי font/size נטענים מהקונפיג הראשי של התוסף ולא משם המודול editbar.
        self.config = mw.addonManager.getConfig(MODULE_ADDON)
        color = "white" if theme_manager.night_mode else "black"

        size_button = QAction("סארט שריפט",mw)
        size_button.setToolTip("סארט שריפט")
        size_button.setShortcut(self.config["reviewer_font_shortcut"])
        # #138 — קיצור QAction צריך לפעול גם כשהפוקוס נמצא בתוך WebEngine של כרטיס המבחן.
        size_button.setShortcutContext(QtCore.Qt.ShortcutContext.ApplicationShortcut)
        size_button.setIcon(QIcon(os.path.join(icons_dir, "abc.png")))
        size_button.triggered.connect(lambda :self.show_font_menu(""))
        changebuttoncolor(size_button, color, "abc.png")

        font_button = QAction("שריפט גרייס", mw)
        font_button.setToolTip("שריפט גרייס")
        font_button.setShortcut(self.config["reviewer_size_shortcut"])
        # #138 — אותו context נדרש גם לכפתור גודל כתב כדי שהקיצור יעבור דרך עורך הקיצורים ויעבוד במבחן.
        font_button.setShortcutContext(QtCore.Qt.ShortcutContext.ApplicationShortcut)
        font_button.setIcon(QIcon(os.path.join(icons_dir, "text_fields.png")))
        font_button.triggered.connect(lambda :self.show_size_menu(self.editor))
        changebuttoncolor(font_button, color, "text_fields.png")


        self.buttons = [size_button, font_button]
        non_colors_actions.extend(self.buttons)

    # #138 — עדכון QAction קיימים במקום שומר על חלון המבחן פתוח ומחליף רק את קיצורי המקלדת.
    def refresh_shortcuts(self, new_config=None) -> None:
        new_config = new_config or mw.addonManager.getConfig(MODULE_ADDON) or {}
        if len(self.buttons) < 2:
            return
        self.buttons[0].setShortcut(new_config.get("reviewer_font_shortcut", ""))
        self.buttons[1].setShortcut(new_config.get("reviewer_size_shortcut", ""))
        # #269 — עדכון קיצורי דרך לכפתורי סגנון
        _rps: dict = new_config.get("review_preset_shortcuts") or {}
        # #bug-fix — מנקים כל קיצור שנשמר ב-QAction של פריסטים (מצטברים ב-non_colors_actions)
        # כדי למנוע ambiguous shortcut עם ה-QShortcut שמטפל בהפעלה.
        for action in non_colors_actions:
            obj_name = action.objectName() if callable(getattr(action, "objectName", None)) else ""
            if obj_name.startswith("review_preset_"):
                action.setShortcut("")
        # עדכון ה-QShortcut שהוא מנגנון ההפעלה האמיתי.
        reviewer = getattr(mw, "reviewer", None)
        shortcuts = getattr(reviewer, "_haf_review_preset_qshortcuts", []) if reviewer else []
        for idx, shortcut in enumerate(shortcuts[:5], start=1):
            # #138 — initial registration and live refresh share the same validation.
            key = _safe_review_preset_shortcut(_rps.get(f"preset_{idx}", ""))
            # #354 — עדכון עם וריאנט לטיני לאותיות עבריות, כמו ברישום הראשוני.
            shortcut.setKeys([QKeySequence(v) for v in key_sequence_variants(key)] if key else [QKeySequence("")])
            shortcut.setEnabled(bool(key.strip()))
            # אישיו #400: מרעננים גם שינוי קיצור בזמן שאנקי פתוח.
            for action in non_colors_actions:
                obj_name = action.objectName() if callable(getattr(action, "objectName", None)) else ""
                if obj_name == f"review_preset_{idx}":
                    base_tooltip = action.property("hafShortcutTooltipBase") or action.toolTip()
                    action.setProperty("hafShortcutTooltipBase", base_tooltip)
                    suffix = f"<br><b>קיצור: {html.escape(key)}</b>" if key else ""
                    action.setToolTip(str(base_tooltip) + suffix)
                    break

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
        self.q_menu.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        (background_color, foreground_color, hover_color) = get_colors()
        stylesheet = menu_stylesheet_template.format(
            background=background_color,
            foreground=foreground_color,
            hover_color=hover_color,
        )
        self.q_menu.setStyleSheet(stylesheet)

    def add_action(self, label, func, stylesheet: str | None):
        if stylesheet:
            label = QLabel(label)
            label.setStyleSheet(stylesheet)
            action = QWidgetAction(self.q_menu)
            action.setDefaultWidget(label)
        else:
            action = QAction(label, self.q_menu)
        action.triggered.connect(func)
        self.q_menu.addAction(action)

    def show(self):
        self.q_menu.exec(QCursor.pos())


def setupmenusButtons(editor):
    extraEditorCommands = ExtraEditorCommands(editor)
    return extraEditorCommands.buttons


# #138 — נקודת כניסה ש-shortcut-manager קורא לה לאחר שמירת ההגדרות כדי לרענן קיצורי מבחן חיים.
def _reload_config():
    global config
    # #138 — רענון live קורא שוב את קונפיג התוסף שעליו shortcut-manager כתב.
    config = mw.addonManager.getConfig(MODULE_ADDON) or {}
    dead = []
    for inst in list(ExtraEditorCommands._instances):
        try:
            inst.refresh_shortcuts(config)
        except RuntimeError:
            dead.append(inst)
    for inst in dead:
        ExtraEditorCommands._instances.remove(inst)


def on_night_mode():
    color = "white" if theme_manager.night_mode else "black"
    for action in non_colors_actions:
            changebuttoncolor(action, color, action.icon().pixmap(QSize(20, 20)))


gui_hooks.theme_did_change.append(on_night_mode)
