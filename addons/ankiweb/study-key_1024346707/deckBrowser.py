
import aqt
import aqt.customstudy
from anki.collection import OpChangesWithId
from anki.decks import DeckCollapseScope, DeckId
from anki.hooks import wrap
from anki.utils import ids2str
from aqt import gui_hooks, mw
from aqt.operations import CollectionOp

##
from aqt.operations.deck import add_deck, set_deck_collapsed
from aqt.operations.scheduling import empty_filtered_deck, rebuild_filtered_deck
from aqt.overview import Overview
from aqt.qt import *
from aqt.utils import getOnlyText, showInfo, tr

#######
DEFERRED_DECK_NAMES = (
    "00 פעקל קארטלעך צו באארבעטן 00",
    "0 פעקל קארטלעך צו באארבעטן 0",
    "00 חפיסת כרטיסים לטיפול 00",
    "0 חפיסת כרטיסים לטיפול 0",
)


##
def _overviewDeck(self, did):
    self.set_current_deck(did)
    # mw.col.decks.select(did)
    # self.mw.moveToState("reviewer")


def _overview(self, did):
    mw.col.decks.select(did)
    self.mw.moveToState("overview")


def _showOptionsadd(self, did: str, _old) -> None:
    deck = aqt.mw.col.decks.get(did)
    m = QMenu(self.mw)
    if deck["name"] not in DEFERRED_DECK_NAMES:
        a = m.addAction(tr.actions_rename())
        qconnect(a.triggered, lambda b, did=did: self._rename(DeckId(int(did))))
        a = m.addAction(tr.actions_options())
        qconnect(a.triggered, lambda b, did=did: self._options(DeckId(int(did))))
    a = m.addAction(tr.actions_export())
    qconnect(a.triggered, lambda b, did=did: self._export(DeckId(int(did))))
    a = m.addAction("מעקט אויס א פעקל")
    if deck["name"] not in DEFERRED_DECK_NAMES:
        a.triggered.connect(lambda b, did=did: open_window(DeckId(int(did))))
    else:
        a.triggered.connect((lambda b, did=did: iscards(self, DeckId(int(did)))))
    m.addSeparator()
    if not deck["dyn"]:
        a = m.addAction("שאפט אן אונטערפעקל")
        a.triggered.connect(lambda b, did=did: _on_create(DeckId(int(did))))
    a = m.addAction("פירט אריבער צו א פעקל...")
    a.triggered.connect(lambda b, did=did: open_subdeck_window(self, DeckId(int(did))))
    m.addSeparator()
    a = m.addAction("הייבט אן חזרן")
    a.triggered.connect(lambda b, did=did: _overviewDeck(self, DeckId(int(did))))
    if not deck["dyn"]:
        a = m.addAction("שרייבט א שאלה")
        a.triggered.connect(lambda b, did=did: AddCard(DeckId(int(did))))
    a = m.addAction('עפנט דעם פעקל אין "דורכבלעטערן"')
    a.triggered.connect(lambda b, did=did: inBrowser(DeckId(int(did))))
    m.addSeparator()
    a = m.addAction('סטאטיסטיק')
    a.triggered.connect(lambda b, did=did: openstats(DeckId(int(did))))
    a = m.addAction("איבערבליק")
    a.triggered.connect(lambda b, did=did: _overview(self, DeckId(int(did))))
    m.addSeparator()
    #     if node.filtered:
    if deck["dyn"]:
        if deck["name"] not in DEFERRED_DECK_NAMES:
            a = m.addAction("בויט איבער")
            a.triggered.connect(lambda b: rebuild_current_filtered_deck(self, DeckId(int(did))))
            a = m.addAction("אויסליידיגן")
            a.triggered.connect(lambda b: empty_current_filtered_deck(self, DeckId(int(did))))
    else:
        a = m.addAction("פילטערט שאלות")
        a.triggered.connect(lambda b, did=did: createfiiltered(DeckId(int(did))))
        a = m.addAction("צוגעפאסט לערנען")
        a.triggered.connect(lambda b, did=did: customstudy1(self, DeckId(int(did))))
    if self.mw.col.sched.have_buried():
        m.addSeparator()
        a = m.addAction("ברענגט צוריק פון באזייטיגן")
        a.triggered.connect(lambda b, did=did: unbury(self, DeckId(int(did))))

    gui_hooks.deck_browser_will_show_options_menu(m, int(did))
    m.exec(QCursor.pos())


aqt.deckbrowser.DeckBrowser._showOptions = wrap(aqt.deckbrowser.DeckBrowser._showOptions, _showOptionsadd, 'around')


# render_deck_node()
def customstudy1(self, did):
    mw.col.decks.select(did)
    import aqt.customstudy
    aqt.customstudy.CustomStudy.fetch_data_and_show(self.mw)

    # aqt.customstudy.CustomStudy(self.mw)


def unbury(self, did):
    mw.col.decks.select(did)
    Overview.on_unbury(self)


def AddCard(did):
    mw.col.decks.select(did)
    mw.onAddCard()


def createfiiltered(did):
    mw.col.decks.select(did)
    mw.onCram()


def openstats(did):
    mw.col.decks.select(did)
    mw.onStats()




def rebuild_current_filtered_deck(self, did) -> None:
    rebuild_filtered_deck(
        parent=mw, deck_id=did
    ).run_in_background()


def empty_current_filtered_deck(self, did) -> None:
    empty_filtered_deck(
        parent=mw, deck_id=did
    ).run_in_background()


def inBrowser(did):
    deck = aqt.mw.col.decks.get(did)
    deckName = deck['name']
    browser = aqt.dialogs.open("Browser", aqt.mw)
    browser.search_for(f"\"deck:{deckName}\"")
    browser.update_history()


class ask_before_delete(QDialog):
    def __init__(self, parent=mw):
        super().__init__(parent)
        self.setWindowTitle("באשטעטיקן אויסמעקן א פעקל")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self._operator = QComboBox()
        self._explanation = QLabel()
        self._explanation.setWordWrap(True)
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout = QGridLayout()
        layout.addWidget(QLabel('<font color=red>זענט איר זיכער אז איר ווילט אויסמעקן דעם פעקל?</font>'), 6, 0, 1, 3)
        layout.addWidget(buttonBox, 8, 0, 7, 9)
        self.setLayout(layout)
        return


def open_window(did):
    ask_delete = ask_before_delete()
    if ask_delete.exec():
        deck_name = mw.col.decks.get(did)["name"]
        aqt.operations.deck.remove_decks(parent=mw, deck_ids=[did], deck_name=deck_name).run_in_background()


def _on_create(did: int) -> None:
    if op := add_sub_deck_dialog(did, parent=mw):
        op.run_in_background()


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
        collapse_deck(did)
        return add_deck(parent=parent, name=deckName + "::" + name)
    else:
        return None


def get_node_and_children_idstr(self, deck_id) -> str:
    return ids2str(
        self.mw.col.decks.deck_and_child_ids(deck_id)
    )


def iscards(self, did):
    total = self.mw.col.db.first(
        f'''
      select
      -- total
      count(id)
      from cards where did in {get_node_and_children_idstr(self, did):s}
    ''')[0]
    if total > 0:
        showInfo(
            "מען קען נישט אויסמעקן דעם פעקל ווען עס האט קארטלעך, ווייל זייער תזמון ווערט געשטערט. <br>כדי אויסצומעקן דעם פעקל, ליידיגט עס קודם אויס דורכן לערנען די קארטלעך דערין.")
    if not total:
        open_window(did)

from aqt.qt import *


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





class DlgSubDeck(QDialog):
    def __init__(self, did, parent=mw):
        super().__init__(parent)
        self.setWindowTitle('פירט א פעקל אריבער אונטער אן אנדערן פעקל')
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self._deck_chooser = ExtendedComboBox()
        self._deck_chooser.setMaximumWidth(390)
        decks = {item["name"]: item["id"] for item in mw.col.decks.all()}
        self._deck_chooser.addItem("פירט אריבער צום הויפט שטאפל", None)
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
        layout.addWidget(QLabel('קלייבט אויס א פעקל אונטער וועלכן דער יעצטיגער פעקל זאל ווערן אן אונטערפעקל:'), 0, 0, 1, 0)
        layout.addWidget(self._deck_chooser, 1, 0, 1, 0)
        layout.addWidget(buttonBox, 11, 0, 1, 3)
        self.setLayout(layout)

        ##########################################################################################

def open_subdeck_window(self, did):
    SubDeck_dialog = DlgSubDeck(did)
    aqt.mw.col.decks.get(did)
    if SubDeck_dialog.exec():
        target_deck_id = SubDeck_dialog._deck_chooser.currentData()
        if SubDeck_dialog._deck_chooser.currentData() is not None:
            self._handle_drag_and_drop(DeckId(int(did)), DeckId(int(target_deck_id)))
        else:
            self._handle_drag_and_drop(DeckId(int(did)), None)
        collapse_deck(target_deck_id)

def collapse_deck(did):
        set_deck_collapsed(
            parent=mw,
            deck_id=did,
            collapsed=False,
            scope=DeckCollapseScope.REVIEWER,
        ).run_in_background()
        mw.moveToState("deckBrowser")
