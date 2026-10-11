
import aqt
import aqt.customstudy
# #138 — dialogs is a DialogManager instance exported by aqt, not a submodule.
from aqt import dialogs
from anki.collection import OpChangesWithId
from anki.decks import DeckId
from anki.scheduler import UnburyDeck
from aqt import mw
from aqt.deckoptions import DeckOptionsDialog, display_options_for_deck_id
from aqt.operations import CollectionOp, QueryOp
from aqt.operations.deck import add_deck, add_deck_dialog, rename_deck, reparent_decks
from aqt.operations.scheduling import empty_filtered_deck, rebuild_filtered_deck, unbury_deck
from aqt.qt import *
from aqt.utils import askUserDialog, getOnlyText, tr

config = mw.addonManager.getConfig(__name__)




class ExtendedComboBox(QComboBox):
    #lineEdit = LineEdit()
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setEditable(True)


        # add a filter model to filter matching items
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        # connect signals

        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.on_completer_activated)

    def focusInEvent(self, e):
        super().lineEdit().focusInEvent(e)
        QTimer.singleShot(0, self.lineEdit().selectAll)
        # QTimer.singleShot(0, self.showPopup)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            # self.activated[str].emit(self.itemText(index))


    # on model change, update the models of the filter and completer as well
    def setModel(self, model):
        super().setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)


    # on model column change, update the model column of the filter and completer as well
    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super().setModelColumn(column)

###

def _on_create() -> None:
        if op := add_deck_dialog(parent=mw):
            op.run_in_background()

def _rename(did) -> None:
    def prompt(name: str) -> None:
        new_name = getOnlyText(tr.decks_new_deck_name(), default=name)
        if not new_name or new_name == name:
            return
        else:
            rename_deck(
                parent=mw, deck_id=did, new_name=new_name
            ).run_in_background()
    QueryOp(
        parent=mw, op=lambda col: col.decks.name(did), success=prompt
    ).run_in_background()

def _export(did: DeckId) -> None:
    mw.onExport(did=did)

class ask_before_delete(QDialog):
    def __init__(self, parent=mw):
        super().__init__(parent)
        self.setWindowTitle("באשטעטיגן דאס אויסמעקן א פעקל")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self._operator = QComboBox()
        self._explanation = QLabel()
        self._explanation.setWordWrap(True)
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout = QGridLayout()
        layout.addWidget(QLabel('<font color=red>זענט איר זיכער אז איר ווילט אויסמעקן דעם פעקל  ?</font>'), 6, 0, 1, 3)
        layout.addWidget(buttonBox, 8, 0, 7, 9)
        self.setLayout(layout)
        return

def ask_delete(did):
    ask_delete = ask_before_delete()
    if ask_delete.exec():
        aqt.operations.deck.remove_decks(
            parent=mw, deck_ids=[did], deck_name=mw.col.decks.name(did)
        ).run_in_background()


def add_sub_deck_dialog(
        did: int,
        *,
        parent: QWidget,
        default_text: str = "",
) -> CollectionOp[OpChangesWithId] | None:
    deck = aqt.mw.col.decks.get(did)
    deckName = deck['name']
    if name := getOnlyText(
            tr.decks_new_deck_name(), default=default_text, parent=parent
    ).strip():
        return add_deck(parent=parent, name=deckName + "::" + name)
    else:
        return None

def on_create(did: int) -> None:
    if op := add_sub_deck_dialog(did, parent=mw):
        op.run_in_background()


class DlgSubDeck(QDialog):
    def __init__(self, did, parent=mw):
        super().__init__(parent)
        self.setWindowTitle('פיר דעם פעקל אונטער אן אנדערן פעקל')
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self._deck_chooser = ExtendedComboBox()
        self._deck_chooser.setMaximumWidth(390)
        decks = {item["name"]: item["id"] for item in mw.col.decks.all()}
        self._deck_chooser.addItem("פיר אריבער צום הויפט ניוו", None)
        for name in sorted(decks.keys()):
            if decks[name] != did:
                self._deck_chooser.addItem(name, decks[name])
        self._deck_chooser.lineEdit().setText('קלייבט אויס א פעקל')

    ##########################################################################################

        ##########################################################################################

        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QGridLayout()
        layout.addWidget(
                QLabel('קלייבט אויס א פעקל וואס דער יעצטיגער פעקל זאל ווערן זיין אונטערפעקל:'), 0, 0, 1, 0)
        layout.addWidget(self._deck_chooser, 1, 0, 1, 0)
        layout.addWidget(buttonBox, 11, 0, 1, 3)
        self.setLayout(layout)

    ##########################################################################################


def open_subdeck_window(self, did):
    ease_dialog = DlgSubDeck(did)
    if ease_dialog.exec():
        target_deck_id = ease_dialog._deck_chooser.currentData()
        # Anki's public operation uses deck id 0 for the top level.
        reparent_decks(
            parent=mw,
            deck_ids=[DeckId(int(did))],
            new_parent=DeckId(int(target_deck_id) if target_deck_id is not None else 0),
        ).run_in_background()

def unbury():
    mode = UnburyDeck.Mode.ALL
    if mw.col.sched_ver() != 1:
        info = mw.col.sched.congratulations_info()
        if info.have_sched_buried and info.have_user_buried:
            opts = [
                tr.studying_manually_buried_cards(),
                tr.studying_buried_siblings(),
                tr.studying_all_buried_cards(),
                tr.actions_cancel(),
            ]

            diag = askUserDialog(tr.studying_what_would_you_like_to_unbury(), opts)
            diag.setDefault(0)
            ret = diag.run()
            if ret == opts[0]:
                mode = UnburyDeck.Mode.USER_ONLY
            elif ret == opts[1]:
                mode = UnburyDeck.Mode.SCHED_ONLY
            elif ret == opts[3]:
                return

    unbury_deck(
        parent=mw, deck_id=mw.col.decks.get_current_id(), mode=mode
    ).run_in_background()

def rebuild_current_filtered_deck(did) -> None:
    rebuild_filtered_deck(
        parent=mw, deck_id=did
    ).run_in_background()

def empty_current_filtered_deck(did) -> None:
    empty_filtered_deck(
        parent=mw, deck_id=did
    ).run_in_background()


def onStudyMore() -> None:
        import aqt.customstudy
        aqt.customstudy.CustomStudy.fetch_data_and_show(aqt.mw)


# #138 — Anki מפרש Shift לחוץ כבקשה לחלון אפשרויות החפיסה הישן. ההפצה
# משתמשת רק במסך החדש; חפיסה מסוננת ממשיכה למסך המסונן הייעודי שלה.
def _display_new_options_for_deck(deck) -> None:
    if deck["dyn"]:
        dialogs.open("FilteredDeckConfigDialog", mw, deck_id=deck["id"])
    else:
        DeckOptionsDialog(mw, deck)


# #138 — גם פתיחה דרך המבחן/תפריטי Anki עוברת בפונקציה הזו, ולכן Shift אינו
# יכול עוד להחזיר את ממשק האפשרויות הישן באף אחד ממסלולי הפתיחה.
aqt.deckoptions.display_options_for_deck = _display_new_options_for_deck



_HAF_SHORTCUT_KEYS = [
    'create_deck', 'deck_rename', 'deck_options', 'deck_export', 'deck_delete',
    'deck_create_sub_deck', 'deck_move', 'deck_overview', 'deck_unbury',
    'deck_filter', 'deck_custom', 'deck_empty', 'deck_rebuild_f_deck',
]

shortcut_config = [
(config['create_deck'], lambda :_on_create()),#צור חפיסה
(config['deck_rename'], lambda : _rename(DeckId(int(mw.col.decks.selected())))),#שנה שם
(config['deck_options'], lambda :display_options_for_deck_id(mw.col.decks.selected())),#אפשרויות
(config['deck_export'], lambda : _export(DeckId(int(mw.col.decks.selected())))),#ייצוא
(config['deck_delete'], lambda : ask_delete(DeckId(int(mw.col.decks.selected())))),#מחק חפיסה
(config['deck_create_sub_deck'], lambda : on_create(DeckId(int(mw.col.decks.selected())))),#צור תת חפיסה
(config['deck_move'], lambda : open_subdeck_window(mw, DeckId(int(mw.col.decks.selected())))),#העבר לחפיסה אחרת
(config['deck_overview'], lambda : mw.moveToState("overview")),#סיכום
(config['deck_unbury'], lambda :unbury()),#הוצא מהטמנה
(config['deck_filter'], lambda :mw.onCram()),#סנן שאלות
(config['deck_custom'], lambda :onStudyMore()),#לימוד מותאם
(config['deck_empty'], lambda :empty_current_filtered_deck(DeckId(int(mw.col.decks.selected())))),#רוקן
(config['deck_rebuild_f_deck'], lambda :rebuild_current_filtered_deck(DeckId(int(mw.col.decks.selected())))),#בנה מחדש
]
scuts = mw.applyShortcuts(shortcut_config)


def refresh_haf_shortcuts():
    global config
    config = mw.addonManager.getConfig(__name__)
    for scut, key_name in zip(scuts, _HAF_SHORTCUT_KEYS, strict=False):
        scut.setKey(QKeySequence(config[key_name]))

