"""
Anki Add-on: Auto Save in Editor (Multi-Window Support with Diff Check)
Version: 3.2 - Config UI Fix (Focus)
"""

import hashlib
import json
import os
import uuid

import aqt
from anki.hooks import wrap
from anki.notes import Note
from aqt import mw
from aqt.editor import Editor
from aqt.gui_hooks import editor_did_init, profile_did_open, profile_will_close
from aqt.qt import *
from aqt.utils import askUser, showWarning
from aqt.webview import WebContent

mw.addonManager.setWebExports(__name__, r"web/.*\.js")

from _shared_libs.haf_logging import get_logger
from _shared_libs.haf_notifications import show_failure, warn_once

logger = get_logger("auto_save_editor")

# --- Config ---
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
DEFAULT_CONFIG = {'save_interval_seconds': 5}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config_to_disk(new_conf):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_conf, f, indent=4)
    except Exception as e:
        show_failure("די איינשטעלונגען פאר אויטאמאטישע גיבויים זענען נישט אפגעזיכערט געווארן פארן קומענדיגן מאל. קלייבט ווידער אויס די איינשטעלונגען און פרובירט אפצוזיכערן; אויב דער פראבלעם קומט צוריק, שיקט א באריכט דורכן הילף מעניו.", e)

config = load_config()
SAVE_INTERVAL = config.get('save_interval_seconds', 60) * 1000  # ms

# --- Global backup path ---
BACKUP_FILE = None
IS_RESTORING = False
manager = None

def initialize_backup_path():
    global BACKUP_FILE
    folder = mw.pm.profileFolder()
    if folder:
        BACKUP_FILE = os.path.join(folder, 'editor_backup.json')

# --- UI: Settings Dialog ---

class AutoSaveConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("איינשטעלונגען פאר אויטאמאטיש אפזיכערן")
        self.setMinimumWidth(300)

        # Make sure the dialog stays on top of its parent
        self.setWindowModality(Qt.WindowModality.WindowModal)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Interval Setting
        self.layout.addWidget(QLabel("אויטאמאטישער גיבוי יעדע באשטימטע צייט (אין סעקונדעס):"))
        self.spin = QSpinBox()
        self.spin.setRange(1, 6000)  # 1 second to 10 minutes
        self.spin.setValue(config.get('save_interval_seconds', 60))
        self.layout.addWidget(self.spin)

        self.layout.addSpacing(10)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def accept(self):
        global config, SAVE_INTERVAL

        new_interval = self.spin.value()
        config['save_interval_seconds'] = new_interval
        SAVE_INTERVAL = new_interval * 1000

        save_config_to_disk(config)

        if manager:
            manager.update_interval(SAVE_INTERVAL)

        super().accept()

def open_settings_dialog(editor):
    """Callback for the editor button/pycmd"""
    # FIX: Get the actual window containing the editor (AddCards or Browser)
    # instead of letting Qt decide or using parentWindow which might be undefined.
    parent_win = editor.widget.window()

    dlg = AutoSaveConfigDialog(parent_win)
    dlg.exec()

# --- Helpers ---
def any_text(fields_dict):
    return any((v or "").strip() for v in fields_dict.values())

def get_note_type_by_name(name: str):
    try:
        return mw.col.models.by_name(name)
    except Exception:
        try:
            return mw.col.models.byName(name)
        except Exception:
            return None

def set_editor_note_compat(editor, note: Note):
    if hasattr(editor, "set_note"):
        editor.set_note(note)
    elif hasattr(editor, "setNote"):
        editor.setNote(note)
    else:
        editor.note = note
        if hasattr(editor, "loadNote"):
            editor.loadNote()
    if hasattr(editor, "loadNote"):
        editor.loadNote()

def switch_model_if_needed(add_cards, note_type):
    try:
        current = add_cards.editor.note.note_type()
        if current.get("name") != note_type.get("name"):
            if hasattr(add_cards, 'modelChooser') and hasattr(add_cards.modelChooser, 'setModel'):
                add_cards.modelChooser.setModel(note_type)
                new_note = mw.col.new_note(note_type)
                set_editor_note_compat(add_cards.editor, new_note)
            else:
                set_editor_note_compat(add_cards.editor, mw.col.new_note(note_type))
    except Exception as e:
        logger.error(f"switch_model_if_needed error: {e}")
        raise

def wait_for_editor_ready(add_cards, tries=50, delay_ms=100, on_ready=None):
    count = {"n": 0}
    owner = manager
    def tick():
        if manager is not owner or not owner or owner.halted:
            return
        try:
            if add_cards and getattr(add_cards, "editor", None) and add_cards.editor.note:
                if on_ready:
                    on_ready(add_cards.editor)
                return
        except Exception:
            pass
        count["n"] += 1
        if count["n"] < tries:
            QTimer.singleShot(delay_ms, tick)
        else:
            owner.fail(RuntimeError("דער רעדאקטירער פענסטער איז נישט געווען גרייט צום צוריקברענגען אין דער באשטימטער צייט"))
    QTimer.singleShot(delay_ms, tick)

def build_restored_note(note_type, fields_map, tags_list):
    note = mw.col.new_note(note_type)
    field_names = [f['name'] for f in note_type['flds']]
    for i, fname in enumerate(field_names):
        if fname in fields_map:
            note.fields[i] = fields_map[fname]
    note.tags = tags_list or []
    return note

# --- Manager Logic ---

class AutoSaverManager:
    def __init__(self):
        self.editors = {}
        self.last_written_hash = ""
        self.halted = False
        self.timer = QTimer(mw)
        self.timer.timeout.connect(self.check_and_save)
        self.timer.start(SAVE_INTERVAL)

    def update_interval(self, new_interval_ms):
        self.timer.setInterval(new_interval_ms)

    def fail(self, exc):
        self.halted = True
        self.timer.stop()
        logger.error(f"Autosave stopped: {exc}")
        show_failure("דאס אויטאמאטישע אפזיכערן אדער צוריקברענגען איז אפגעשטעלט געווארן. דער פריערדיגער גיבוי איז געבליבן. זיכערט אליין אפ די רעדאקטירער פענסטער און עפנט דעם פראפיל פון פריש פארן נאכאמאל פרובירן.", exc)

    def register(self, editor):
        # #256 — מזהה פנימי נדרש גם לעורכים עם רשומה קיימת כדי שניקוי זיכרון אחרי הוספה לא ישאיר מצב לא עקבי.
        if not hasattr(editor, 'autosaver_id'):
            editor.autosaver_id = str(uuid.uuid4())
        self.editors[editor.autosaver_id] = editor

    def unregister(self, editor):
        if hasattr(editor, 'autosaver_id') and editor.autosaver_id in self.editors:
            del self.editors[editor.autosaver_id]

    def reset_after_add(self, editor, added_note=None):
        # #256 — לאחר לחיצה על "הוסף" הגיבוי של השאלה הישנה נמחק מיד, כדי שלא תופיע הודעת שחזור שגויה.
        old_id = getattr(editor, 'autosaver_id', None)
        if old_id and old_id in self.editors:
            del self.editors[old_id]
        editor.autosaver_id = str(uuid.uuid4())
        self.editors[editor.autosaver_id] = editor
        self._remove_backup_entries(old_id, getattr(added_note, 'id', None))
        self.last_written_hash = ""

    def _remove_backup_entries(self, window_id=None, note_id=None):
        if self.halted or IS_RESTORING:
            return
        if not BACKUP_FILE or not os.path.exists(BACKUP_FILE):
            return
        try:
            with open(BACKUP_FILE, encoding='utf-8') as f:
                entries = json.load(f)
            if isinstance(entries, dict):
                entries = [entries]
            if not isinstance(entries, list):
                raise ValueError("דער רעדאקטירער גיבוי איז נישט אין א גילטיגן פארמאט")
            filtered = []
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError("די רשומה אינעם רעדאקטירער גיבוי איז נישט גילטיג")
                if window_id and entry.get('window_id') == window_id:
                    continue
                if note_id and entry.get('note_id') == note_id:
                    continue
                filtered.append(entry)
            if filtered:
                with open(BACKUP_FILE + '.tmp', 'w', encoding='utf-8') as f:
                    json.dump(filtered, f, sort_keys=True, ensure_ascii=False)
                os.replace(BACKUP_FILE + '.tmp', BACKUP_FILE)
            else:
                os.remove(BACKUP_FILE)
        except FileNotFoundError:
            return
        except Exception as e:
            logger.error(f"Backup cleanup after add error: {e}")
            self.fail(e)

    def check_and_save(self):
        if self.halted or IS_RESTORING or not BACKUP_FILE:
            return

        current_snapshot = []

        for editor in list(self.editors.values()):
            try:
                if not editor.widget or not editor.note:
                    continue

                # Get Deck Info
                current_deck_id = None
                current_deck_name = None
                try:
                    # #61 — deck_chooser במקום deckChooser (deprecated)
                    if hasattr(editor, 'parentWindow') and hasattr(editor.parentWindow, 'deck_chooser'):
                        current_deck_id = editor.parentWindow.deck_chooser.selectedId()
                        current_deck_name = mw.col.decks.name(current_deck_id)
                    elif mw.col.decks.current():
                        current = mw.col.decks.current()
                        current_deck_id = current.get('id')
                        current_deck_name = current.get('name')
                except (AttributeError, KeyError) as exc:
                    raise RuntimeError("מען קען נישט דערקענען דעם פעקל פונעם רעדאקטירער פענסטער") from exc

                note_type = editor.note.note_type()
                if not note_type:
                    raise ValueError("דער סארט רשומה פונעם רעדאקטירער פענסטער פעלט")
                note_id = editor.note.id if getattr(editor.note, "id", None) else None

                # דלג על כרטיסים קיימים שנצפו בדפדוף — הם כבר שמורים ב-DB (#74)
                if note_id:
                    continue

                data = {
                    'window_id': editor.autosaver_id,
                    'note_id':note_id,
                    'note_type_name': note_type.get('name'),
                    'deck_id': current_deck_id,
                    'deck_name': current_deck_name,
                    'fields': dict(zip(
                        [fld['name'] for fld in note_type['flds']],
                        editor.note.fields, strict=False
                    )),
                    'tags': list(editor.note.tags) if getattr(editor.note, "tags", None) else []
                }

                if any_text(data['fields']):
                    current_snapshot.append(data)

            except Exception as e:
                self.fail(e)
                return

        current_snapshot.sort(key=lambda x: x['window_id'])

        try:
            json_str = json.dumps(current_snapshot, sort_keys=True, ensure_ascii=False)
            current_hash = hashlib.md5(json_str.encode('utf-8')).hexdigest()
        except Exception as exc:
            self.fail(exc)
            return

        if current_hash == self.last_written_hash:
            return

        try:
            if not current_snapshot:
                if os.path.exists(BACKUP_FILE):
                    os.remove(BACKUP_FILE)
            else:
                with open(BACKUP_FILE + '.tmp', 'w', encoding='utf-8') as f:
                    f.write(json_str)
                os.replace(BACKUP_FILE + '.tmp', BACKUP_FILE)

            self.last_written_hash = current_hash

        except Exception as e:
            self.fail(e)

    def cleanup(self):
        self.halted = True
        self.timer.stop()

# --- Restore Queue Logic ---

RESTORE_QUEUE = []

def process_restore_queue():
    global RESTORE_QUEUE, IS_RESTORING

    if manager and manager.halted:
        return

    if not RESTORE_QUEUE:
        IS_RESTORING = False
        if BACKUP_FILE and os.path.exists(BACKUP_FILE):
            try:
                os.remove(BACKUP_FILE)
            except OSError as exc:
                manager.fail(exc)
        return

    entry_data = RESTORE_QUEUE[0]

    try:
        note_type = get_note_type_by_name(entry_data.get('note_type_name', ''))
        if not note_type:
            raise ValueError(f"דער סארט רשומה צום צוריקברענגען פעלט: {entry_data.get('note_type_name', '')}")

        add_cards = aqt.dialogs.open("AddCards", mw)

        def on_window_ready(editor):
            try:
                # #61 — deck_chooser במקום deckChooser (deprecated)
                if entry_data.get('deck_id') and hasattr(add_cards, 'deck_chooser'):
                    add_cards.deck_chooser.selected_deck_id = entry_data['deck_id']

                switch_model_if_needed(add_cards, note_type)
                restored_note = build_restored_note(note_type, entry_data.get('fields', {}), entry_data.get('tags', []))
                set_editor_note_compat(editor, restored_note)

            except Exception as e:
                manager.fail(e)
                return
            RESTORE_QUEUE.pop(0)
            owner = manager
            QTimer.singleShot(400, lambda: process_restore_queue() if manager is owner else None)

        wait_for_editor_ready(add_cards, tries=50, delay_ms=100, on_ready=on_window_ready)

    except Exception as e:
        manager.fail(e)
        IS_RESTORING = False

def start_restore_process(backup_list):
    global RESTORE_QUEUE, IS_RESTORING
    IS_RESTORING = True
    RESTORE_QUEUE = backup_list
    process_restore_queue()

# --- Profile Hooks ---

def on_profile_open():
    global manager, IS_RESTORING
    IS_RESTORING = False
    initialize_backup_path()

    manager = AutoSaverManager()

    if not BACKUP_FILE or not os.path.exists(BACKUP_FILE):
        return

    try:
        with open(BACKUP_FILE, encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            return
        if isinstance(data, dict):
            data = [data]

        valid_backups = [b for b in data if any_text(b.get('fields', {}))]
        if not valid_backups:
            os.remove(BACKUP_FILE)
            return

        count = len(valid_backups)
        if askUser(f"עס איז געפונען געווארן א גיבוי פון {count} רעדאקטירער פענסטער וואס זענען נישט אפגעזיכערט געווארן.\nזאל מען זיי יעצט צוריקברענגען?", title="אויטאמאטיש צוריקברענגען"):
            start_restore_process(valid_backups)
        else:
            os.remove(BACKUP_FILE)

    except FileNotFoundError:
        # קובץ הגיבוי נמחק בין בדיקת הקיום לפתיחתו — מצב תקין, אין צורך בדיווח שגיאה
        return
    except Exception as e:
        manager.fail(e)

def on_profile_close():
    global manager
    if manager:
        manager.cleanup()
        manager = None

# --- Editor Hooks ---

def on_editor_init(editor):
    if manager:
        manager.register(editor)


def editor_cleanup_wrapper(self):
    if manager:
        manager.unregister(self)


def _addcards_load_new_note_wrapper(self, sticky_fields_from=None, _old=None):
    _old(self, sticky_fields_from=sticky_fields_from)
    if sticky_fields_from is not None and manager:
        manager.reset_after_add(self.editor, sticky_fields_from)


try:
    from aqt.addcards import AddCards
    AddCards._load_new_note = wrap(AddCards._load_new_note, _addcards_load_new_note_wrapper, "around")
except Exception as e:
    logger.error(f"auto-save #256 AddCards hook install failed: {e}")
    warn_once("auto-save-editor:add-hook", "מען קען נישט דערהיינטיגן דעם אויטאמאטישן גיבוי נאכן צולייגן א רשומה. זיכערט אליין אפ די רעדאקטירער פענסטער; אויב דער פראבלעם קומט צוריק נאכן ווידער עפענען, שיקט א באריכט דורכן הילף מעניו.")

Editor.cleanup = wrap(Editor.cleanup, editor_cleanup_wrapper, "before")

profile_did_open.append(on_profile_open)
profile_will_close.append(on_profile_close)
editor_did_init.append(on_editor_init)

from aqt import gui_hooks


def handle_js_message(handled, message, context):
    # בדיקה האם ההודעה היא זו שחיכינו לה
    if message == "autosave_options":
        open_settings_dialog(context)
        return (True, None)  # מחזיר True כדי לאותת ל-Anki שההודעה טופלה

    # --- מספור שדות (#14) ---
    if message.startswith("haf_num_set:"):
        _handle_set_counter(message)
        return (True, None)

    # אם זו לא ההודעה שלנו, נחזיר את הערך המקורי (handled)
    return handled

gui_hooks.webview_did_receive_js_message.append(handle_js_message)


# ============================================================
# מספור אוטומטי לכתיבת שאלות (#14)
# ============================================================

import re as _re

from aqt import gui_hooks as _gui_hooks

_field_counter = 1
_last_add_cards_id: int | None = None




def _append_numbering_js(webcontent: WebContent, context) -> None:
    """לייגט צו דעם numbering.js אינעם פראגע רעדאקטירער."""
    from aqt.editor import Editor as _Editor
    if isinstance(context, _Editor):
        pkg = mw.addonManager.addonFromModule(__name__)
        webcontent.js.append(f"/_addons/{pkg}/web/numbering.js")


def _inject_numbering_buttons(editor) -> None:
    """רופט אן-HafNumbering.inject דורכן-webview פונעם רעדאקטירער."""
    global _field_counter, _last_add_cards_id
    try:
        from aqt.addcards import AddCards
    except ImportError:
        return
    if not isinstance(editor.parentWindow, AddCards):
        return
    if not editor.note:
        return
    note_type = editor.note.note_type()
    if not note_type:
        return
    all_indices = list(range(len(note_type["flds"])))
    if not all_indices:
        return
    # אם נפתח חלון הוספה חדש, אפס את המונה
    win_id = id(editor.parentWindow)
    if win_id != _last_add_cards_id:
        _last_add_cards_id = win_id
        _field_counter = 1
        editor.web.eval(
            "if(typeof HafNumbering!=='undefined') {"
            "HafNumbering._isActive=false;"
            "HafNumbering._activeField=null;"
            "HafNumbering._currentN=1;}"
        )
    editor.web.eval(
        f"if(typeof HafNumbering!=='undefined') HafNumbering.inject("
        f"{json.dumps(all_indices)}, {_field_counter});"
    )


def _handle_set_counter(message: str) -> None:
    """דערהיינטיגט דעם ציילער לויטן באניצער בקשה (טוישן דעם נומער אויפן קנעפל)."""
    global _field_counter
    try:
        new_val = int(message.split(":")[1])
        if new_val >= 0:
            _field_counter = new_val
    except (ValueError, IndexError):
        pass


def _on_note_added_increment(note) -> None:
    """העכערט דעם ציילער נאכן צולייגן א פראגע — editor_did_load_note וועט זיך זארגן פארן נאכאמאל אריינשטעלן."""
    global _field_counter
    _field_counter += 1


_gui_hooks.webview_will_set_content.append(_append_numbering_js)
_gui_hooks.editor_did_load_note.append(_inject_numbering_buttons)
_gui_hooks.add_cards_did_add_note.append(_on_note_added_increment)


# --- fieldsAreBlank: שדה שמכיל רק מספור (כמו "5. ") לא יחשב כשינוי ---
_HTML_TAGS_RE = _re.compile(r"<[^>]+>")
_NUM_ONLY_RE = _re.compile(r"^\d+\.\s*$")


def _strip_html(s: str) -> str:
    s = s.replace("&nbsp;", " ").replace("<br>", " ").replace("<br/>", " ")
    return _HTML_TAGS_RE.sub("", s).strip()


def _fieldsAreBlank_wrap(self, previousNote=None, _old=None):
    if not self.note:
        return True
    m = self.note_type()
    for c, f in enumerate(self.note.fields):
        clean = _strip_html(f)
        if clean == "" or _NUM_ONLY_RE.match(clean):
            continue
        notChangedvalues = {""}
        if previousNote and m["flds"][c]["sticky"]:
            notChangedvalues.add(_strip_html(previousNote.fields[c]))
        if clean not in notChangedvalues:
            return False
    return True


Editor.fieldsAreBlank = wrap(Editor.fieldsAreBlank, _fieldsAreBlank_wrap, "around")


# Keep expensive editor webviews warm and speed Browser row changes on Anki 25.09.
from . import performance as _editor_performance  # noqa: E402,F401

# סבב 12 — חימום WebEngine נעשה במודול נפרד כדי לא להכביד על טעינת התוסף עצמו.
from . import webengine_prewarm as webengine_prewarm
