"""
צוגאב: צוריקברענגען אויסגעמעקטע רשומות
היט באזונדערע אויסגעמעקטע רשומות און ערלויבט זיי צוריקצוברענגען ביז צוויי טעג נאכן אויסמעקן.
"""
from __future__ import annotations

import json
import time
from functools import wraps
from pathlib import Path

from anki.collection import Collection
from anki.utils import ids2str
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.utils import showWarning, tooltip
from _shared_libs.haf_notifications import show_failure

_DATA_FILE = Path(__file__).parent / "user_files" / "deleted_notes.json"
_EXPIRY_SEC = 2 * 24 * 3600  # יומיים


# ─── Storage ──────────────────────────────────────────────────────────────────

def _current_profile() -> str:
    if not mw.pm.name:
        raise RuntimeError("מען קען נישט דערקענען דעם פראפיל פארן פאפיר קארב")
    return mw.pm.name


def _load_all() -> dict:
    """לאדט אלע דאטן פונעם טעקע (פארמאט: {profile: [entries]})"""
    try:
        if _DATA_FILE.exists():
            data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
            # תמיכה לאחור: קובץ ישן בפורמט רשימה ישירה
            if isinstance(data, list):
                data = {"default": data}
            if not isinstance(data, dict) or any(
                not isinstance(entries, list)
                or any(not isinstance(entry, dict) for entry in entries)
                for entries in data.values()
            ):
                raise ValueError("דער פאפיר קארב איז נישט אין א גילטיגן פארמאט")
            return data
    except Exception as exc:
        raise RuntimeError("מען קען נישט לייענען דעם פאפיר קארב. די פעולה איז אפגעשטעלט כדי צו היטן דעם ביז יעצטיגן גיבוי.") from exc
    return {}


def _load(profile: str | None = None) -> list[dict]:
    profile = profile or _current_profile()
    return _load_all().get(profile, [])


def _save(entries: list[dict], profile: str | None = None) -> None:
    profile = profile or _current_profile()
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    all_data = _load_all()
    all_data[profile] = entries
    temporary = _DATA_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(_DATA_FILE)


def _purge(entries: list[dict]) -> list[dict]:
    cutoff = time.time() - _EXPIRY_SEC
    return [e for e in entries if e.get("deleted_at", 0) >= cutoff]


# ─── Hook: שמירה לפני המחיקה ──────────────────────────────────────────────────

def _on_notes_will_be_deleted(col, note_ids) -> None:
    if not note_ids:
        return
    profile = _current_profile()
    entries = _load(profile)
    now = time.time()
    for nid in note_ids:
        try:
            note = col.get_note(nid)
            notetype = col.models.get(note.mid)
            if not notetype:
                raise ValueError("דער סארט רשומה פעלט")
            cards = note.cards()
            deck_name = "Default"
            if cards:
                deck = col.decks.get(cards[0].did)
                if deck:
                    deck_name = deck["name"]
            entries.append({
                "deleted_at": now,
                "notetype_name": notetype["name"] if notetype else "",
                "field_values": list(note.fields),
                "tags": list(note.tags),
                "deck_name": deck_name,
            })
        except Exception as exc:
            raise RuntimeError(f"דאס אויסמעקן איז אפגעשטעלט: מען קען נישט מאכן א גיבוי פון דער רשומה {nid} אינעם פאפיר קארב.") from exc
    _save(_purge(entries), profile)


# ─── Dialog שחזור ─────────────────────────────────────────────────────────────

class _TrashDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("צוריקברענגען אויסגעמעקטע רשומות")
        self.setMinimumWidth(700)
        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.addWidget(
            QLabel(
                "באזונדערע אויסגעמעקטע רשומות ווערן געהיט ביז צוויי טעג, און דערנאך אויטאמאטיש אויסגעמעקט.\n"
                "רשומות וואס זענען אויסגעמעקט געווארן ביים אויסמעקן א פעקל קען מען דא נישט צוריקברענגען. מען קען זיי צוריקברענגען דורכן מעניו->בייט פראפיל->ברענג צוריק פון א גיבוי"
            )
        )

        self._tbl = QTableWidget()
        self._tbl.setColumnCount(4)
        self._tbl.setHorizontalHeaderLabels(["סארט רשומה", "ערשטער פעלד", "אויסמעק צייט", ""])
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        hdr = self._tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.resizeSection(3, 72)
        lay.addWidget(self._tbl)

        btns = QHBoxLayout()
        btns.addStretch()
        close_btn = QPushButton("פארמאכן")
        close_btn.clicked.connect(self.accept)
        btns.addWidget(close_btn)
        lay.addLayout(btns)

    def _refresh(self):
        profile = _current_profile()
        entries = _purge(_load(profile))
        _save(entries, profile)
        self._entries = sorted(
            entries, key=lambda e: e.get("deleted_at", 0), reverse=True
        )
        self._tbl.clearSpans()
        self._tbl.setRowCount(0)

        if not self._entries:
            self._tbl.setRowCount(1)
            item = QTableWidgetItem("עס זענען נישט דא קיין אפגעהיטע אויסגעמעקטע רשומות")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._tbl.setItem(0, 0, item)
            self._tbl.setSpan(0, 0, 1, 4)
            return

        self._tbl.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            self._tbl.setItem(row, 0, QTableWidgetItem(entry.get("notetype_name", "")))
            fv = entry.get("field_values") or [""]
            self._tbl.setItem(row, 1, QTableWidgetItem(fv[0][:120]))
            ts = int(entry.get("deleted_at", 0))
            self._tbl.setItem(
                row, 2,
                QTableWidgetItem(
                    QDateTime.fromSecsSinceEpoch(ts).toString("dd/MM HH:mm")
                ),
            )
            btn = QPushButton("ברענג צוריק")
            btn.clicked.connect(lambda _, e=entry: self._restore(e))
            self._tbl.setCellWidget(row, 3, btn)

    def _restore(self, entry: dict) -> None:
        col = mw.col
        notetype = col.models.by_name(entry.get("notetype_name", ""))
        if notetype is None:
            showWarning(
                f"דער סארט רשומה «{entry.get('notetype_name', '')}» איז נישט פאראן.\n"
                "מען דארף אים שאפן אדער אימפארטירן פארן צוריקברענגען."
            )
            return
        try:
            note = col.new_note(notetype)
            for i, val in enumerate(entry.get("field_values", [])):
                if i < len(note.fields):
                    note.fields[i] = val
            note.tags = list(entry.get("tags", []))
            deck_id = col.decks.id(entry.get("deck_name", "Default"))
            col.add_note(note, deck_id)
        except Exception as ex:
            show_failure("דאס צוריקברענגען איז נישט פארענדיגט געווארן. די רשומה איז געבליבן אינעם פאפיר קארב פאר נאך א פרואוו.", ex, parent=self)
            return

        # הסרת הרשומה מהרשימה
        profile = _current_profile()
        ts = entry.get("deleted_at")
        nt = entry.get("notetype_name")
        fv = entry.get("field_values")
        remaining = [
            e for e in _load(profile)
            if not (
                e.get("deleted_at") == ts
                and e.get("notetype_name") == nt
                and e.get("field_values") == fv
            )
        ]
        _save(remaining, profile)
        mw.reset()
        tooltip("די רשומה איז מיט הצלחה צוריקגעברענגט געווארן")
        self._refresh()


# ─── Menu ─────────────────────────────────────────────────────────────────────

def _setup_menu() -> None:
    if not hasattr(mw, "addon_col_menu"):
        return
    root_menu = mw.addon_col_menu

    action = QAction("צוריקברענגען אויסגעמעקטע רשומות", mw)
    action.triggered.connect(lambda: _TrashDialog(mw).exec())
    root_menu.addAction(action)


# ─── Hooks ────────────────────────────────────────────────────────────────────

def _guard_note_deletion(original):
    @wraps(original)
    def remove_notes(col, note_ids, *args, **kwargs):
        note_ids = list(note_ids)
        _on_notes_will_be_deleted(col, note_ids)
        return original(col, note_ids, *args, **kwargs)
    return remove_notes


def _guard_card_deletion(original):
    @wraps(original)
    def remove_notes_by_card(col, card_ids, *args, **kwargs):
        card_ids = list(card_ids)
        note_ids = col.db.list(
            f"select distinct nid from cards where id in {ids2str(card_ids)}"
        ) if card_ids else []
        _on_notes_will_be_deleted(col, note_ids)
        return original(col, card_ids, *args, **kwargs)
    return remove_notes_by_card


# Anki removes failing hooks. Wrap the public entry points so a failed backup
# blocks every subsequent deletion too, until storage is repaired.
Collection.remove_notes = _guard_note_deletion(Collection.remove_notes)
Collection.remove_notes_by_card = _guard_card_deletion(Collection.remove_notes_by_card)
gui_hooks.main_window_did_init.append(_setup_menu)
