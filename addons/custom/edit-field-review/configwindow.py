import pathlib
import re
from enum import Enum
from typing import TypedDict

from _aqt.hooks import (
    sidebar_should_refresh_notetypes,
)
from anki.models import NoteType
from aqt import gui_hooks, mw
from aqt.qt import *

# #275 — logger נדרש כדי לדווח על סוג רשומה שנכשל בלי להפיל פתיחת פרופיל.
from _shared_libs.haf_logging import get_logger

from .ankiaddonconfig import ConfigManager

conf = ConfigManager()
logger = get_logger("edit_field_review")






class TemplateField(TypedDict):
    name: str
    edit: bool


class Editability(Enum):
    NONE = 0
    PARTIAL = 1
    ALL = 2

    @classmethod
    def from_check_state(cls, check_state: Qt.CheckState) -> "Editability":
        if check_state == Qt.CheckState.Unchecked:
            return cls.NONE
        if check_state == Qt.CheckState.Checked:
            return cls.ALL
        return cls.PARTIAL

    @classmethod
    def to_check_state(cls, val: "Editability") -> Qt.CheckState:
        if val == cls.NONE:
            return Qt.CheckState.Unchecked
        if val == cls.ALL:
            return Qt.CheckState.Checked
        return Qt.CheckState.PartiallyChecked


class FieldIsEditable(TypedDict):
    name: str
    orig_edit: Editability
    edit: Editability


class NoteTypeFields(TypedDict):
    name: str
    fields: list[FieldIsEditable]


def modify_field_editability(
    note_type: "NoteType", field: FieldIsEditable
) -> "NoteType":
    for template in note_type["tmpls"]:
        for side in ["qfmt", "afmt"]:
            if field["edit"] == Editability.ALL:
                template[side] = re.sub(
                    "{{{{((?:(?!edit:)[^#/:}}]+:)*{})}}}}".format(field["name"]),
                    r"{{edit:\1}}",
                    template[side],
                )
            elif field["edit"] == Editability.NONE:
                template[side] = re.sub(
                    "{{{{((?:[^#/:}}]+:)*)edit:((?:[^#/:}}]+:)*{})}}}}".format(field["name"]),
                    r"{{\1\2}}",
                    template[side],
                )
    return note_type


def parse_fields(template: str) -> list[TemplateField]:
    matches = re.findall("{{[^#/}]+?}}", template)  # type: ignore
    fields = []
    for m in matches:
        # strip off mustache
        m = re.sub(r"[{}]", "", m)
        # strip off modifiers
        splitted = m.split(":")
        modifiers = splitted[:-1]
        field_name = splitted[-1]
        has_edit = "edit" in modifiers
        field_info = TemplateField(name=field_name, edit=has_edit)
        fields.append(field_info)
    return fields


def get_fields_in_every_notetype(fields_in_note_type: list[NoteTypeFields]) -> None:
    for _i in fields_in_note_type:
        fields_in_note_type.pop()

    models = mw.col.models
    note_types = models.all()
    for note_type in note_types:
        templates = note_type["tmpls"]
        editable_field_names: set[str] = set()
        uneditable_field_names: set[str] = set()

        for template in templates:
            for side in ["qfmt", "afmt"]:
                for tmpl_field in parse_fields(template[side]):  # type: ignore
                    name = tmpl_field["name"]
                    if tmpl_field["edit"]:
                        editable_field_names.update([name])
                    else:
                        uneditable_field_names.update([name])

        field_names = [fld["name"] for fld in note_type["flds"]]
        fields_list = []
        for fldname in field_names:
            try:
                # if (False, False), skip since the field isn't used in any of the templates.
                editable = {
                    (True, True): Editability.PARTIAL,
                    (True, False): Editability.ALL,
                    (False, True): Editability.NONE,
                }[(fldname in editable_field_names, fldname in uneditable_field_names)]

                field = FieldIsEditable(name=fldname, edit=editable, orig_edit=editable)
                fields_list.append(field)
            except (KeyError, ValueError):
                pass
        nt = NoteTypeFields(name=note_type["name"], fields=fields_list)
        fields_in_note_type.append(nt)








# שינוי אוטומטי של הכרטיסים למצב עריכה
def auto_make_editable():
    current_model = mw.col.conf.get("curModel")
    fields_in_note_type: list[NoteTypeFields] = []
    get_fields_in_every_notetype(fields_in_note_type)
    for _idx, note_type_fields in enumerate(fields_in_note_type):
        # if note_type_fields["name"] == "14 - שאלות אמריקאיות ":
        #     continue
        for field in note_type_fields["fields"]:
            if field["edit"] != Editability.ALL:
                # showInfo(str(field["edit"]))
                field["edit"] = Editability.ALL

    try:
        for note_type_fields in fields_in_note_type:
            modified = False
            try:  # 2.1.45
                note_type = mw.col.models.by_name(note_type_fields["name"])
            except AttributeError:  # 2.1.41-44
                note_type = mw.col.models.byName(  # type: ignore
                    note_type_fields["name"]
                )
            for field in note_type_fields["fields"]:
                if field["edit"] != field["orig_edit"]:
                    modified = True
                    note_type = modify_field_editability(note_type, field)
            if modified:
                try:
                    # #275 — skip_checks עוקף בדיקת תבניות כפולות שקיימת מראש בסוג הרשומה.
                    # אנחנו משנים רק editability של שדות, לא תבניות, אז הבדיקה לא רלוונטית.
                    mw.col.models.update(note_type, skip_checks=True)
                except Exception as exc:
                    logger.warning(f"Failed making note type editable: {note_type_fields['name']}: {exc}")
    finally:
        # #275 — גם אחרי חריגה מחזירים את curModel כדי לא להשאיר את אנקי על סוג רשומה זמני.
        if current_model is not None:
            mw.col.conf["curModel"] = current_model


config = mw.addonManager.getConfig(__name__)

def auto_make_editable_check():
    if config["auto_make_editable"]:
        auto_make_editable()

if config["auto_make_editable"]:
    sidebar_should_refresh_notetypes.append(auto_make_editable)

# clayout.CardLayout.accept = wrap(clayout.CardLayout.accept, show, "after")
# מאפשר גישה מתוספים אחרים
mw.auto_make_editable = auto_make_editable_check
# מאפשר להפעיל מהתפריט
def _add_edit_field_menu_action():
    if not hasattr(mw, "addon_col_menu"):
        return
    action = QAction("ערלויב רעדאקטירן אין אלע פעלדער פון אלע קארטלעך", mw)
    qconnect(action.triggered, auto_make_editable)
    filename = str(pathlib.Path(__file__).parent.resolve())
    icon = QIcon(filename + "/color_icons/edit.png")
    action.setIcon(icon)
    mw.addon_col_menu.addAction(action)


gui_hooks.main_window_did_init.append(_add_edit_field_menu_action)

# #61: consume Configure without opening Anki's JSON editor.
mw.addonManager.setConfigAction(__name__, lambda: True)
