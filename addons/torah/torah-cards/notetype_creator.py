"""
יצירת סוג רשומה חדש בלי ידע ב-HTML
"""
import json as _json

from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from PyQt6.QtCore import pyqtSignal as Signal

# ── CONSTANTS ─────────────────────────────────────────────────────────────────

FONT_OPTIONS = ["livorna", "Arial", "David", "Narkisim", "Times New Roman"]
FONT_SIZE_OPTIONS = ["14", "16", "18", "20", "24", "28"]

BACKGROUND_OPTIONS = {
    "ווייס": "white",
    "ליכטיג גרוי": "lightgray",
    "ליכטיג געל": "lightyellow",
    "ליכטיג בלוי": "lightblue",
    "ליכטיג גרין": "lightgreen",
    "עלפנביין": "#fffff0",
}

BOX_BG_OPTIONS = {
    "דורכזיכטיג": "transparent",
    "ווייס": "white",
    "ליכטיג געל": "lightyellow",
    "ליכטיג גרין": "#d4edda",
    "ליכטיג בלוי": "#cce5ff",
    "ליכטיג אראנזש": "#ffe8cc",
    "ליכטיג ראזע": "#ffd6e7",
    "ליכטיג גרוי": "#f0f0f0",
    "ליכטיג לילא": "#ede0ff",
    "גאלדיג": "#fff8e1",
}

ALIGNMENT_OPTIONS = {
    "רעכטס": "right",
    "צענטער": "center",
    "לינקס": "left",
    "אויסגעגליכן צו ביידע זייטן": "justify",
}

BORDER_RADIUS_OPTIONS = {
    "גלייך": "0px",
    "קליין (5px)": "5px",
    "מיטל (10px)": "10px",
    "רונד (20px)": "20px",
}

BORDER_OPTIONS = {
    "אן": "none",
    "דין גרוי": "1px solid #ccc",
    "דין שווארץ": "1px solid black",
    "דיק טונקל": "2px solid #555",
    "מיט שטראכן": "2px dashed #888",
    "פונקטן": "2px dotted #888",
}

SHADOW_OPTIONS = {
    "אן": "none",
    "גרינג": "0 1px 3px rgba(0,0,0,0.15)",
    "מיטל": "0 3px 6px rgba(0,0,0,0.25)",
    "שטארק": "0 6px 12px rgba(0,0,0,0.35)",
}

PADDING_OPTIONS = {
    "ענג (5px)": "5px",
    "געווענליך (10px)": "10px",
    "ברייט (18px)": "18px",
    "מיט אסאך רווח (25px)": "25px",
}

TEXT_COLOR_OPTIONS = {
    "שווארץ": "black",
    "טונקל בלוי": "#003399",
    "טונקל גרין": "#005500",
    "טונקל רויט": "#990000",
    "בלוי-גרין": "#006666",
    "לילא": "#550055",
}

FIELD_BG_OPTIONS = {
    "נעמט פונעם קעסטל": "inherit",
    "ווייס": "white",
    "ליכטיג געל": "lightyellow",
    "ליכטיג בלוי": "#e8f4ff",
    "ליכטיג גרין": "#efffef",
    "ליכטיג אראנזש": "#fff8e8",
    "ליכטיג ראזע": "#fff0f5",
}

# ── KIND constants ─────────────────────────────────────────────────────────────
KIND_STANDARD  = "standard"
KIND_CLOZE     = "cloze"
KIND_IMG_OCC   = "image_occlusion"
KIND_TYPE_ANS  = "type_answer"


def _default_field_style():
    return {
        "font":      "livorna",
        "font_size": "18",
        "bold":      False,
        "italic":    False,
        "color":     "שווארץ",
        "bg":        "נעמט פונעם קעסטל",
    }


def _default_box_style():
    return {
        "color":         "דורכזיכטיג",
        "border_radius": "קליין (5px)",
        "border":        "אן",
        "shadow":        "אן",
        "padding":       "געווענליך (10px)",
    }


DEFAULT_FIELDS_CONFIG = [
    {
        "name": "שאלה",  "on_front": True,  "on_back": False,
        "group": 1, "editable": True,
        "box_style": {**_default_box_style(), "color": "ווייס"},
        "style": _default_field_style(),
    },
    {
        "name": "תשובה", "on_front": False, "on_back": True,
        "group": 2, "editable": True,
        "box_style": {**_default_box_style(), "color": "ליכטיג געל"},
        "style": _default_field_style(),
    },
    {
        "name": "מקור",  "on_front": True,  "on_back": True,
        "group": 3, "editable": False,
        "box_style": {**_default_box_style(), "color": "ליכטיג גרוי"},
        "style": _default_field_style(),
    },
]


# ── CSS generator ──────────────────────────────────────────────────────────────

def _generate_css(global_font, global_font_size, bg_color, alignment, fields_config=None):
    lines = [
        ".card {",
        f"  font-family: {global_font};",
        f"  font-size: {global_font_size}pt;",
        f"  background-color: {bg_color};",
        f"  text-align: {alignment};",
        "  direction: rtl;",
        "  unicode-bidi: embed;",
        "}",
        ".nightMode { color: white; }",
    ]
    if fields_config:
        for i, f in enumerate(fields_config):
            st    = f["style"]
            color = TEXT_COLOR_OPTIONS.get(st["color"], "black")
            bg    = FIELD_BG_OPTIONS.get(st["bg"], "inherit")
            lines += [
                f".f{i} {{",
                f"  font-family: {st['font']};",
                f"  font-size: {st['font_size']}pt;",
                f"  color: {color};",
                f"  font-weight: {'bold' if st['bold'] else 'normal'};",
                f"  font-style: {'italic' if st['italic'] else 'normal'};",
                "  display: block;",
            ]
            if bg != "inherit":
                lines.append(f"  background-color: {bg};")
            lines.append("}")
    return "\n".join(lines)


# ── HTML renderers (standard) ──────────────────────────────────────────────────

def _field_tag(field_name, type_answer, is_answer, editable=True):
    if is_answer and type_answer:
        return "{{type:" + field_name + "}}"
    if editable:
        return "{{edit:" + field_name + "}}"
    return "{{" + field_name + "}}"


def _render_box(fields_in_group, box_style_dict, answer_field, type_answer, alignment):
    color   = BOX_BG_OPTIONS.get(box_style_dict.get("color",         "דורכזיכטיג"),      "transparent")
    radius  = BORDER_RADIUS_OPTIONS.get(box_style_dict.get("border_radius", "גלייך"),      "0px")
    border  = BORDER_OPTIONS.get(box_style_dict.get("border",        "אן"),        "none")
    shadow  = SHADOW_OPTIONS.get(box_style_dict.get("shadow",        "אן"),        "none")
    padding = PADDING_OPTIONS.get(box_style_dict.get("padding",      "געווענליך (10px)"), "10px")
    div_style = (
        f"background-color:{color}; border-radius:{radius}; border:{border}; "
        f"box-shadow:{shadow}; padding:{padding}; text-align:{alignment}; "
        f"margin-bottom:6px; width:100%; box-sizing:border-box; direction:rtl;"
    )
    tags = [
        f'<span class="f{idx}">'
        + _field_tag(fname, type_answer, fname == answer_field, editable)
        + "</span>"
        for fname, idx, editable in fields_in_group
    ]
    return f'<div style="{div_style}">\n    ' + "\n    ".join(tags) + "\n</div>"


def _render_side(fields_config, answer_field, type_answer, alignment, is_back):
    from collections import OrderedDict
    side_key = "on_back" if is_back else "on_front"
    side_fields = [
        (f["name"], i, f["group"], f.get("editable", True), f.get("box_style", _default_box_style()))
        for i, f in enumerate(fields_config) if f[side_key]
    ]
    if not side_fields:
        return ""
    groups = OrderedDict()
    for fname, idx, grp, editable, box_style in side_fields:
        if grp not in groups:
            groups[grp] = {"members": [], "box_style": box_style}
        groups[grp]["members"].append((fname, idx, editable))
    return "\n".join(
        _render_box(data["members"], data["box_style"], answer_field, type_answer, alignment)
        for data in groups.values()
    )


# ── Notetype creators ──────────────────────────────────────────────────────────

def _name_exists(name):
    if mw.col.models.by_name(name):
        showInfo(f"א סארט רשומה מיטן נאמען '{name}' עקזיסטירט שוין.")
        return True
    return False


def create_standard_notetype(
    name, fields_config, answer_field,
    global_font, global_font_size, bg_color, alignment,
    type_answer, add_reversed,
):
    if _name_exists(name):
        return False
    models = mw.col.models
    model  = models.new(name)
    model["type"] = 0

    srtfld = 0
    for num, f in enumerate(fields_config):
        fld = models.new_field(f["name"])
        if any(k in f["name"] for k in ("מקור", "מיקום", "מסכת", "פרשה", "סימן")):
            fld["sticky"] = True
            srtfld = num
        fld["font"] = f["style"]["font"]
        fld["size"] = int(f["style"]["font_size"])
        fld["rtl"]  = True
        models.addField(model, fld)

    t1 = models.new_template("קארטל 1 – שאלה ← תשובה")
    t1["qfmt"] = _render_side(fields_config, answer_field, type_answer, alignment, is_back=False)
    t1["afmt"] = "{{FrontSide}}\n<hr id=answer>\n" + _render_side(fields_config, answer_field, type_answer, alignment, is_back=True)
    models.addTemplate(model, t1)

    if add_reversed:
        t2 = models.new_template("קארטל 2 – תשובה ← שאלה")
        t2["qfmt"] = _render_side(fields_config, None, False, alignment, is_back=True)
        t2["afmt"] = "{{FrontSide}}\n<hr id=answer>\n" + _render_side(fields_config, None, False, alignment, is_back=False)
        models.addTemplate(model, t2)

    model["css"]   = _generate_css(global_font, global_font_size, bg_color, alignment, fields_config)
    model["sortf"] = srtfld
    models.add(model)
    return True


def create_cloze_notetype(
    name, text_field, extra_field,
    global_font, global_font_size, bg_color, alignment,
):
    if _name_exists(name):
        return False
    models = mw.col.models
    model  = models.new(name)
    model["type"] = 1  # MODEL_CLOZE

    for fname in (text_field, extra_field):
        fld = models.new_field(fname)
        fld["rtl"] = True
        models.addField(model, fld)

    t = models.new_template("פילט אויס דאס אויסגעלאזטע")
    t["qfmt"] = "{{cloze:" + text_field + "}}"
    t["afmt"] = "{{cloze:" + text_field + "}}<br><small>{{" + extra_field + "}}</small>"
    models.addTemplate(model, t)

    model["css"] = _generate_css(global_font, global_font_size, bg_color, alignment)
    models.add(model)
    return True


def create_image_occlusion_notetype(name, global_font, global_font_size, bg_color):
    if _name_exists(name):
        return False
    try:
        from anki.notetypes_pb2 import StockNotetype as _SN
        nt_json = mw.col._backend.get_stock_notetype_legacy(
            _SN.Kind.KIND_IMAGE_OCCLUSION
        )
        model = _json.loads(nt_json)
        model["name"] = name
        model["originalStockKind"] = _SN.OriginalStockKind.ORIGINAL_STOCK_KIND_IMAGE_OCCLUSION
        model["css"] += (
            f"\n.card {{\n"
            f"  font-family: {global_font};\n"
            f"  font-size: {global_font_size}pt;\n"
            f"  background-color: {bg_color};\n"
            f"}}"
        )
        mw.col.models.add(model)
        return True
    except Exception as exc:
        from _shared_libs.haf_notifications import show_failure
        show_failure("דער סארט רשומה 'בילד באהאלטן' איז נישט געשאפן געווארן. עפנט אנקי איבער און פרובירט נאכאמאל; אויב די פראבלעם קומט צוריק, שיקט א באריכט פונעם הילף מעניו.", exc)
        return False


# ── Per-field style dialog ─────────────────────────────────────────────────────

class _FieldStyleDialog(QDialog):
    def __init__(self, field_name, style, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"פעלד פארמאטירונג: {field_name}")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._style = dict(style)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)

        self._font_combo = QComboBox()
        for f in FONT_OPTIONS:
            self._font_combo.addItem(f)
        self._font_combo.setCurrentText(self._style.get("font", "livorna"))
        layout.addRow("שריפט:", self._font_combo)

        self._size_combo = QComboBox()
        for s in FONT_SIZE_OPTIONS:
            self._size_combo.addItem(s + "pt")
        idx = self._size_combo.findText(self._style.get("font_size", "18") + "pt")
        self._size_combo.setCurrentIndex(idx if idx >= 0 else 2)
        layout.addRow("שריפט גרייס:", self._size_combo)

        self._bold_cb = QCheckBox()
        self._bold_cb.setChecked(self._style.get("bold", False))
        layout.addRow("דיקע אותיות:", self._bold_cb)

        self._italic_cb = QCheckBox()
        self._italic_cb.setChecked(self._style.get("italic", False))
        layout.addRow("שיפע אותיות:", self._italic_cb)

        self._color_combo = QComboBox()
        for c in TEXT_COLOR_OPTIONS:
            self._color_combo.addItem(c)
        idx = self._color_combo.findText(self._style.get("color", "שווארץ"))
        self._color_combo.setCurrentIndex(max(0, idx))
        layout.addRow("טעקסט קאליר:", self._color_combo)

        self._bg_combo = QComboBox()
        for b in FIELD_BG_OPTIONS:
            self._bg_combo.addItem(b)
        idx = self._bg_combo.findText(self._style.get("bg", "נעמט פונעם קעסטל"))
        self._bg_combo.setCurrentIndex(max(0, idx))
        layout.addRow("טעקסט הינטערגרונט:", self._bg_combo)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("באשטעטיקן")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("אפזאגן")
        layout.addRow(btn_box)

    def get_style(self):
        return {
            "font":      self._font_combo.currentText(),
            "font_size": self._size_combo.currentText().replace("pt", ""),
            "bold":      self._bold_cb.isChecked(),
            "italic":    self._italic_cb.isChecked(),
            "color":     self._color_combo.currentText(),
            "bg":        self._bg_combo.currentText(),
        }


# ── Per-box style dialog ───────────────────────────────────────────────────────

class _BoxStyleDialog(QDialog):
    def __init__(self, group_num, box_style, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"קעסטל איינשטעלונגען – גרופע {group_num}")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._style = dict(box_style)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)

        self._color_combo = QComboBox()
        for label in BOX_BG_OPTIONS:
            self._color_combo.addItem(label)
        idx = self._color_combo.findText(self._style.get("color", "דורכזיכטיג"))
        self._color_combo.setCurrentIndex(max(0, idx))
        layout.addRow("הינטערגרונט קאליר:", self._color_combo)

        self._radius_combo = QComboBox()
        for label in BORDER_RADIUS_OPTIONS:
            self._radius_combo.addItem(label)
        idx = self._radius_combo.findText(self._style.get("border_radius", "קליין (5px)"))
        self._radius_combo.setCurrentIndex(max(0, idx))
        layout.addRow("רונדן עקן:", self._radius_combo)

        self._border_combo = QComboBox()
        for label in BORDER_OPTIONS:
            self._border_combo.addItem(label)
        idx = self._border_combo.findText(self._style.get("border", "אן"))
        self._border_combo.setCurrentIndex(max(0, idx))
        layout.addRow("ראם:", self._border_combo)

        self._shadow_combo = QComboBox()
        for label in SHADOW_OPTIONS:
            self._shadow_combo.addItem(label)
        idx = self._shadow_combo.findText(self._style.get("shadow", "אן"))
        self._shadow_combo.setCurrentIndex(max(0, idx))
        layout.addRow("שאטן:", self._shadow_combo)

        self._padding_combo = QComboBox()
        for label in PADDING_OPTIONS:
            self._padding_combo.addItem(label)
        idx = self._padding_combo.findText(self._style.get("padding", "געווענליך (10px)"))
        self._padding_combo.setCurrentIndex(max(0, idx))
        layout.addRow("אינערליכע רווח:", self._padding_combo)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("באשטעטיקן")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("אפזאגן")
        layout.addRow(btn_box)

    def get_style(self):
        return {
            "color":         self._color_combo.currentText(),
            "border_radius": self._radius_combo.currentText(),
            "border":        self._border_combo.currentText(),
            "shadow":        self._shadow_combo.currentText(),
            "padding":       self._padding_combo.currentText(),
        }


# ── Fields table widget ────────────────────────────────────────────────────────

class _FieldsTableWidget(QWidget):
    """
    עמודות: שם שדה | קדמי | אחורי | קבוצה | עריכה בסקירה | הגדרות תיבה | עיצוב שדה

    • עריכה בסקירה — שדה מסומן = {{edit:...}} (EFRDC), לא מסומן = {{FieldName}}.
    • שדות עם אותו מספר קבוצה מוצגים יחד בתיבה אחת.
    • שינוי הגדרות תיבה → מסנכרן אוטומטית לכל שדות הקבוצה.
    """
    fields_changed = Signal()
    _HEADERS = ["פעלד נאמען", "פארנט", "הינטן", "גרופע", "רעדאקטירן ביים חזרן", "קעסטל איינשטעלונגען", "פעלד פארמאטירונג"]
    _COL_NAME, _COL_FRONT, _COL_BACK, _COL_GROUP, _COL_EDITABLE, _COL_BOX_STYLE, _COL_FIELD_STYLE = range(7)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        hint = QLabel(
            "גרופע: פעלדער מיטן זעלבן נומער ווערן געוויזן אינאיינעם אין איין קעסטל. "
            "רעדאקטירן ביים חזרן: אן אנגעצייכנט פעלד קען מען דירעקט רעדאקטירן בשעת א חזרה."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(self._HEADERS)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(self._COL_NAME,        QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(self._COL_FRONT,       QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(self._COL_BACK,        QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(self._COL_GROUP,       QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(self._COL_EDITABLE,    QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(self._COL_BOX_STYLE,   QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(self._COL_FIELD_STYLE, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        self._add_btn    = QPushButton("+ לייגט צו א פעלד")
        self._remove_btn = QPushButton("− נעמט אראפ א פעלד")
        self._up_btn     = QPushButton("↑")
        self._down_btn   = QPushButton("↓")
        for b in (self._add_btn, self._remove_btn, self._up_btn, self._down_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self._add_btn.clicked.connect(self._on_add)
        self._remove_btn.clicked.connect(self._on_remove)
        self._up_btn.clicked.connect(self._on_up)
        self._down_btn.clicked.connect(self._on_down)

        self._styles     = []
        self._box_styles = []
        for cfg in DEFAULT_FIELDS_CONFIG:
            self._add_row(
                cfg["name"], cfg["on_front"], cfg["on_back"],
                cfg["group"], cfg.get("editable", True),
                dict(cfg.get("box_style", _default_box_style())),
                dict(cfg["style"]),
            )

    # ── helpers ──

    def _make_cb_widget(self, checked):
        cb = QCheckBox()
        cb.setChecked(checked)
        cb.stateChanged.connect(lambda *_: self.fields_changed.emit())
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.addWidget(cb)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setContentsMargins(0, 0, 0, 0)
        return w

    def _make_group_widget(self, group_num):
        sb = QSpinBox()
        sb.setRange(1, 9)
        sb.setValue(group_num)
        sb.setFixedWidth(48)
        sb.valueChanged.connect(lambda val, s=sb: self._on_group_changed(s))
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.addWidget(sb)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setContentsMargins(0, 0, 0, 0)
        return w

    def _on_group_changed(self, changed_sb):
        changed_row = -1
        for r in range(self._table.rowCount()):
            w = self._table.cellWidget(r, self._COL_GROUP)
            if w and w.findChild(QSpinBox) is changed_sb:
                changed_row = r
                break
        if changed_row == -1:
            self.fields_changed.emit()
            return
        new_group = changed_sb.value()
        for r in range(self._table.rowCount()):
            if r != changed_row and self._get_spinbox(r).value() == new_group:
                self._box_styles[changed_row] = dict(self._box_styles[r])
                break
        self.fields_changed.emit()

    def _get_cb(self, row, col):
        return self._table.cellWidget(row, col).findChild(QCheckBox)

    def _get_spinbox(self, row):
        return self._table.cellWidget(row, self._COL_GROUP).findChild(QSpinBox)

    def _find_row_by_btn(self, btn, col):
        for row in range(self._table.rowCount()):
            if self._table.cellWidget(row, col) is btn:
                return row
        return -1

    def _add_row(self, name, on_front, on_back, group=None,
                 editable=True, box_style=None, field_style=None):
        if group is None:
            used = [self._get_spinbox(r).value() for r in range(self._table.rowCount())]
            group = max(used, default=0) + 1
        row = self._table.rowCount()
        self._styles.append(field_style or _default_field_style())
        self._box_styles.append(box_style or _default_box_style())
        self._table.insertRow(row)

        item = QTableWidgetItem(name)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(row, self._COL_NAME, item)
        self._table.setCellWidget(row, self._COL_FRONT,    self._make_cb_widget(on_front))
        self._table.setCellWidget(row, self._COL_BACK,     self._make_cb_widget(on_back))
        self._table.setCellWidget(row, self._COL_GROUP,    self._make_group_widget(group))
        self._table.setCellWidget(row, self._COL_EDITABLE, self._make_cb_widget(editable))

        box_btn = QPushButton("קעסטל...")
        box_btn.clicked.connect(lambda _, b=box_btn: self._on_box_style_btn(b))
        self._table.setCellWidget(row, self._COL_BOX_STYLE, box_btn)

        fld_btn = QPushButton("פעלד...")
        fld_btn.clicked.connect(lambda _, b=fld_btn: self._on_field_style_btn(b))
        self._table.setCellWidget(row, self._COL_FIELD_STYLE, fld_btn)

        self.fields_changed.emit()

    def _on_box_style_btn(self, btn):
        row = self._find_row_by_btn(btn, self._COL_BOX_STYLE)
        if row == -1:
            return
        group = self._get_spinbox(row).value()
        dlg = _BoxStyleDialog(group, self._box_styles[row], self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_style = dlg.get_style()
            for r in range(self._table.rowCount()):
                if self._get_spinbox(r).value() == group:
                    self._box_styles[r] = dict(new_style)
            self.fields_changed.emit()

    def _on_field_style_btn(self, btn):
        row = self._find_row_by_btn(btn, self._COL_FIELD_STYLE)
        if row == -1:
            return
        name = self._table.item(row, self._COL_NAME).text()
        dlg = _FieldStyleDialog(name, self._styles[row], self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._styles[row] = dlg.get_style()

    def _swap_rows(self, r1, r2):
        t1 = self._table.item(r1, self._COL_NAME).text()
        t2 = self._table.item(r2, self._COL_NAME).text()
        self._table.item(r1, self._COL_NAME).setText(t2)
        self._table.item(r2, self._COL_NAME).setText(t1)
        for col in (self._COL_FRONT, self._COL_BACK, self._COL_EDITABLE):
            v1 = self._get_cb(r1, col).isChecked()
            v2 = self._get_cb(r2, col).isChecked()
            self._get_cb(r1, col).setChecked(v2)
            self._get_cb(r2, col).setChecked(v1)
        g1 = self._get_spinbox(r1).value()
        g2 = self._get_spinbox(r2).value()
        self._get_spinbox(r1).setValue(g2)
        self._get_spinbox(r2).setValue(g1)
        self._styles[r1],     self._styles[r2]     = self._styles[r2],     self._styles[r1]
        self._box_styles[r1], self._box_styles[r2] = self._box_styles[r2], self._box_styles[r1]

    def _on_add(self):
        name, ok = QInputDialog.getText(self, "נייער פעלד", "פעלד נאמען:")
        if ok and name.strip():
            name = name.strip()
            existing = [self._table.item(i, self._COL_NAME).text()
                        for i in range(self._table.rowCount())]
            if name not in existing:
                self._add_row(name, True, True)

    def _on_remove(self):
        rows = sorted({i.row() for i in self._table.selectedItems()}, reverse=True)
        for r in rows:
            self._table.removeRow(r)
            self._styles.pop(r)
            self._box_styles.pop(r)
        self.fields_changed.emit()

    def _on_up(self):
        row = self._table.currentRow()
        if row > 0:
            self._swap_rows(row, row - 1)
            self._table.selectRow(row - 1)

    def _on_down(self):
        row = self._table.currentRow()
        if 0 <= row < self._table.rowCount() - 1:
            self._swap_rows(row, row + 1)
            self._table.selectRow(row + 1)

    def get_fields_config(self):
        return [
            {
                "name":      self._table.item(i, self._COL_NAME).text(),
                "on_front":  self._get_cb(i, self._COL_FRONT).isChecked(),
                "on_back":   self._get_cb(i, self._COL_BACK).isChecked(),
                "group":     self._get_spinbox(i).value(),
                "editable":  self._get_cb(i, self._COL_EDITABLE).isChecked(),
                "box_style": dict(self._box_styles[i]),
                "style":     dict(self._styles[i]),
            }
            for i in range(self._table.rowCount())
        ]

    def get_all_field_names(self):
        return [self._table.item(i, self._COL_NAME).text()
                for i in range(self._table.rowCount())]


# ── Style section (shared across kinds) ───────────────────────────────────────

class _StyleSection(QGroupBox):
    """אלגעמיינע פארמאטירונג: שריפט, גרייס, אויסגלייכונג, הינטערגרונט קאליר."""

    def __init__(self, parent=None):
        super().__init__("אלגעמיינע פארמאטירונג", parent)
        form = QFormLayout(self)

        self._font_combo = QComboBox()
        for f in FONT_OPTIONS:
            self._font_combo.addItem(f)
        form.addRow("פעליקע שריפט:", self._font_combo)

        self._size_combo = QComboBox()
        for s in FONT_SIZE_OPTIONS:
            self._size_combo.addItem(s + "pt")
        self._size_combo.setCurrentIndex(2)
        form.addRow("שריפט גרייס:", self._size_combo)

        self._align_combo = QComboBox()
        for label in ALIGNMENT_OPTIONS:
            self._align_combo.addItem(label)
        self._align_combo.setCurrentIndex(0)  # ימין
        form.addRow("טעקסט אויסגלייכונג:", self._align_combo)

        self._bg_combo = QComboBox()
        for label in BACKGROUND_OPTIONS:
            self._bg_combo.addItem(label)
        form.addRow("קארטל הינטערגרונט קאליר:", self._bg_combo)

    @property
    def font(self):        return self._font_combo.currentText()
    @property
    def font_size(self):   return FONT_SIZE_OPTIONS[self._size_combo.currentIndex()]
    @property
    def alignment(self):   return ALIGNMENT_OPTIONS[self._align_combo.currentText()]
    @property
    def bg_color(self):    return BACKGROUND_OPTIONS[self._bg_combo.currentText()]


# ── Main dialog ────────────────────────────────────────────────────────────────

class NotetypeCreatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("שאפט א נייעם סארט רשומה")
        self.setMinimumWidth(720)
        self.setMinimumHeight(500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._setup_ui()
        self._refresh_answer_combo()

    def _setup_ui(self):
        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner_widget = QWidget()
        layout = QVBoxLayout(inner_widget)
        scroll.setWidget(inner_widget)
        outer.addWidget(scroll)

        # ── שם ──────────────────────────────────────────────────────────────
        name_form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("למשל: 11 - חידוש שאלות")
        name_form.addRow("נאמען פונעם סארט רשומה:", self._name_edit)
        layout.addLayout(name_form)

        # ── סוג הרשומה ──────────────────────────────────────────────────────
        kind_group = QGroupBox("סארט רשומה")
        kind_layout = QVBoxLayout(kind_group)
        self._kind_standard  = QRadioButton("געווענליך  –  שאלה ↔ תשובה")
        self._kind_type_ans = QRadioButton("שרייבט אריין די תשובה  –  {{type:...}}")
        self._kind_cloze    = QRadioButton("פילט אויס דאס אויסגעלאזטע  –  {{cloze:...}}")
        self._kind_img_occ  = QRadioButton("בילד באהאלטן  –  Image Occlusion")
        self._kind_standard.setChecked(True)
        for rb in (self._kind_standard, self._kind_type_ans, self._kind_cloze, self._kind_img_occ):
            kind_layout.addWidget(rb)
        layout.addWidget(kind_group)
        self._kind_standard.toggled.connect(self._on_kind_changed)
        self._kind_type_ans.toggled.connect(self._on_kind_changed)
        self._kind_cloze.toggled.connect(self._on_kind_changed)
        self._kind_img_occ.toggled.connect(self._on_kind_changed)

        # ── סקשן: רגיל ──────────────────────────────────────────────────────
        self._standard_section = QWidget()
        std_layout = QVBoxLayout(self._standard_section)
        std_layout.setContentsMargins(0, 0, 0, 0)

        self._fields_table = _FieldsTableWidget()
        self._fields_table.fields_changed.connect(self._refresh_answer_combo)
        std_layout.addWidget(self._fields_table)

        answer_row = QHBoxLayout()
        answer_row.addWidget(QLabel("תשובה פעלד:"))
        self._answer_combo = QComboBox()
        answer_row.addWidget(self._answer_combo)
        std_layout.addLayout(answer_row)

        cards_group = QGroupBox("קארטל אפציעס")
        cards_form = QFormLayout(cards_group)
        self._reversed_cb = QCheckBox("לייגט צו אן איבערגעקערטן קארטל")
        cards_form.addRow(self._reversed_cb)
        std_layout.addWidget(cards_group)

        layout.addWidget(self._standard_section)

        # ── סקשן: השלם את החסר ──────────────────────────────────────────────
        self._cloze_section = QGroupBox("איינשטעלונגען פאר אויספילן דאס אויסגעלאזטע")
        cloze_form = QFormLayout(self._cloze_section)
        self._cloze_text_field  = QLineEdit("טעקסט")
        self._cloze_extra_field = QLineEdit("נאך")
        cloze_form.addRow("נאמען פונעם טעקסט פעלד:", self._cloze_text_field)
        cloze_form.addRow("נאמען פון נאך א פעלד:", self._cloze_extra_field)
        cloze_lbl = QLabel(
            "דער מוסטער ווערט אויטאמאטיש געשאפן מיט:\n"
            "  שאלה: {{cloze:טעקסט}}\n"
            "  תשובה: {{cloze:טעקסט}}  +  {{נאך}}"
        )
        cloze_lbl.setStyleSheet("color: #555; font-size: 10px;")
        cloze_form.addRow(cloze_lbl)
        self._cloze_section.setVisible(False)
        layout.addWidget(self._cloze_section)

        # ── סקשן: הסתרת תמונה ───────────────────────────────────────────────
        self._img_occ_section = QGroupBox("בילד באהאלטן")
        img_layout = QVBoxLayout(self._img_occ_section)
        img_lbl = QLabel(
            "די פעלדער פונעם סארט 'בילד באהאלטן' ווערן אויטאמאטיש באשטימט דורך Anki.\n"
            "לייגט צו א בילד צו דער רשומה אינעם צולייגן קארטלעך פענצטער ווי געווענליך.\n\n"
            "פעלדער וואס ווערן געשאפן: Occlusion, Image, Header, Back Extra, Comments"
        )
        img_lbl.setWordWrap(True)
        img_layout.addWidget(img_lbl)
        self._img_occ_section.setVisible(False)
        layout.addWidget(self._img_occ_section)

        # ── עיצוב גלובלי (תמיד נראה) ────────────────────────────────────────
        self._style_section = _StyleSection()
        layout.addWidget(self._style_section)

        # ── כפתורים (מחוץ לגלילה) ───────────────────────────────────────────
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("שאפן")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("אפזאגן")
        outer.addWidget(btn_box)

    def _current_kind(self):
        if self._kind_type_ans.isChecked():
            return KIND_TYPE_ANS
        if self._kind_cloze.isChecked():
            return KIND_CLOZE
        if self._kind_img_occ.isChecked():
            return KIND_IMG_OCC
        return KIND_STANDARD

    def _on_kind_changed(self):
        kind = self._current_kind()
        self._standard_section.setVisible(kind in (KIND_STANDARD, KIND_TYPE_ANS))
        self._cloze_section.setVisible(kind == KIND_CLOZE)
        self._img_occ_section.setVisible(kind == KIND_IMG_OCC)

    def _refresh_answer_combo(self):
        previous = self._answer_combo.currentText()
        self._answer_combo.clear()
        for f in self._fields_table.get_all_field_names():
            self._answer_combo.addItem(f)
        idx = self._answer_combo.findText(previous)
        if idx >= 0:
            self._answer_combo.setCurrentIndex(idx)
        else:
            idx = self._answer_combo.findText("תשובה")
            if idx >= 0:
                self._answer_combo.setCurrentIndex(idx)

    def _on_accept(self):
        name = self._name_edit.text().strip()
        if not name:
            showInfo("לייגט אריין א נאמען פארן סארט רשומה.")
            return

        kind       = self._current_kind()
        font       = self._style_section.font
        font_size  = self._style_section.font_size
        bg_color   = self._style_section.bg_color
        alignment  = self._style_section.alignment

        if kind in (KIND_STANDARD, KIND_TYPE_ANS):
            fields_config = self._fields_table.get_fields_config()
            if not fields_config:
                showInfo("לייגט צו כאטש איין פעלד.")
                return
            success = create_standard_notetype(
                name, fields_config,
                answer_field=self._answer_combo.currentText(),
                global_font=font, global_font_size=font_size,
                bg_color=bg_color, alignment=alignment,
                type_answer=(kind == KIND_TYPE_ANS),
                add_reversed=self._reversed_cb.isChecked(),
            )
            n_cards = 2 if self._reversed_cb.isChecked() else 1

        elif kind == KIND_CLOZE:
            text_f  = self._cloze_text_field.text().strip()  or "טעקסט"
            extra_f = self._cloze_extra_field.text().strip() or "נאך"
            success = create_cloze_notetype(
                name, text_f, extra_f,
                global_font=font, global_font_size=font_size,
                bg_color=bg_color, alignment=alignment,
            )
            n_cards = 1

        else:  # KIND_IMG_OCC
            success = create_image_occlusion_notetype(
                name,
                global_font=font, global_font_size=font_size,
                bg_color=bg_color,
            )
            n_cards = 1

        if success:
            showInfo(
                f"דער סארט רשומה '{name}' איז מיט הצלחה געשאפן!\n"
                f"({n_cards} {'קארטלעך' if n_cards > 1 else 'קארטל'})"
            )
            self.accept()


def show_notetype_creator():
    dialog = NotetypeCreatorDialog()
    dialog.exec()
