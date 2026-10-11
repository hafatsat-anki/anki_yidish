# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os.path
from collections.abc import Iterable
from copy import deepcopy
from enum import Enum, auto
from typing import NamedTuple

from anki.models import NoteType
from anki.notes import Note
from anki.utils import join_fields
from aqt import mw
from aqt.qt import *

from .collection_manager import NameId
from .config import config


class ImportResult(Enum):
    success = auto()
    dupe = auto()


class FileInfo(NamedTuple):
    name: str
    path: str


def files_in_note(note: Note) -> Iterable[FileInfo]:
    """
    Returns FileInfo for every file referenced by the note.
    Skips missing files.
    """
    for file_ref in note.col.media.files_in_str(note.mid, join_fields(note.fields)):
        if os.path.exists(file_path := os.path.join(note.col.media.dir(), file_ref)):
            yield FileInfo(file_ref, file_path)


def copy_media_files(new_note: Note, other_note: Note) -> None:
    # check if there are any media files referenced by the note
    for file in files_in_note(other_note):
        # #308
        new_filename = new_note.col.media.add_file(file.path)
        # NOTE: this_col_filename may differ from original filename (name conflict, different contents),
        # in which case we need to update the note.
        if new_filename != file.name:
            new_note.fields = [field.replace(file.name, new_filename) for field in new_note.fields]


# def get_matching_model(model_id: int, reference_model: NoteType) -> NoteType:
def get_matching_model(model_id, reference_model: NoteType) -> NoteType:

    if model_id is not None and model_id != NameId.none_type().id:
        # model_id הוא מספר ה-ID של סוג השאלה הנבחר
        try:
            return mw.col.models.get(int(model_id))
        except (ValueError, TypeError):
            # אם זה מחרוזת שם, חפש לפי שם
            model_by_name = mw.col.models.by_name(str(model_id))
            if model_by_name:
                return model_by_name
    else:
        # find a model in current profile that matches the name of model from other profile
        # create a new note type (clone) only if no model with that name exists.
        ref_name = reference_model.get('name')
        matching_model = mw.col.models.by_name(ref_name)
        if matching_model:
            # Reuse the existing note type even if fields differ.
            # import_note() maps fields by name, so partial overlap is sufficient.
            # This prevents Anki from creating duplicate note types with hex suffixes
            # (e.g. 'Basic-908e4') when models.add() encounters a name collision.
            return matching_model
        # No existing model with this name -> safe to add a clone.
        matching_model = deepcopy(reference_model)
        matching_model['id'] = 0
        mw.col.models.add(matching_model)
        return matching_model


# def import_note(other_note: Note, model_id: int, deck_name: str) -> ImportResult:
def import_note(other_note: Note, model_id: str, deck_name: str) -> tuple[ImportResult, int | None]:
    matching_model = get_matching_model(model_id, other_note.note_type())
    deck_id = mw.col.decks.add_normal_deck_with_name(deck_name).id
    new_note = Note(mw.col, matching_model)
    new_note.note_type()['did'] = deck_id

    # #139 — Anki 25 כבר לא מאפשר איטרציה ישירה על Note כמפתחות שדה; עוברים לפי שמות השדות במודל.
    for field in new_note.note_type().get('flds', []):
        field_name = field.get('name')
        if not field_name:
            continue
        if field_name in other_note:
            new_note[field_name] = str(other_note[field_name])

    # copy field tags into new note object
    if config.get('copy_tags'):
        new_note.tags = [tag for tag in other_note.tags if tag != 'leech']

    if config.get('tag_exported_cards') and (tag := config.get('exported_tag')):
        other_note.add_tag(tag)
        other_note.col.update_note(other_note)

    # check if note is dupe of existing one
    if config.get('skip_duplicates') and new_note.dupeOrEmpty():
        return ImportResult.dupe, None
    else:
        copy_media_files(new_note, other_note)
        mw.col.add_note(new_note, deck_id)
        return ImportResult.success, new_note.id

