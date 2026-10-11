import contextlib

from anki.decks import DeckManager
from anki.models import ModelManager
from aqt import mw
from aqt.qt import *
from aqt.utils import getFile, showWarning

from . import import_xaml

a = []
b = [0,0]
# #155 — שומרים handler אחרון כדי למנוע חיבור כפול לפתיחת ייבוא.
_patched_import_handler = None


# #154 — ברירות מחדל מונעות קריסה כאשר meta/config של התוסף ריק או נמחק.
def _addon_config() -> dict:
    config = mw.addonManager.getConfig(__name__) or {}
    config.setdefault("defdeck", "")
    config.setdefault("defmodel", "")
    return config


def _ensure_cached_defaults() -> None:
    # #154 — שומר מקום לשתי ברירות המחדל בזיכרון כדי שפתיחה דרך קובץ לא תיפול על IndexError.
    while len(a) < 2:
        a.append("")


class QHSeparationLine(QFrame):
    '''
    a horizontal separation line\n
    '''
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(1)
        self.setFixedHeight(20)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)


class Dlg_import_xaml(QDialog):
    def __init__(self, parent=mw, preselected_file=None):
        super().__init__(parent)
        self.setWindowTitle('xml אימפארט פון שו"ת אין א טעקע')
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self._xml_chooser = QPushButton(self)
        self._xml_chooser.setMaximumWidth(390)
        if preselected_file:
            self.xml_file = [preselected_file]
            self._xml_chooser.setText(f"אויסגעקליבן: {[preselected_file]}")
        else:
            self._xml_chooser.setText("דריקט דא אויסצוקלייבן א טעקע")
        self._xml_chooser.clicked.connect(lambda: getFile(mw, "אימפארט פוןXML צו אנקי", cb=self.duplicateCards1, filter="אויסגאבע פונעם חזרות פראגראם (*.xml)", multi=True))

        self._deck_chooser = ExtendedComboBox()
        self._deck_chooser.setMaximumWidth(390)
        decks = {item["name"]: item["id"] for item in mw.col.decks.all()}
        for name in sorted(decks.keys()):
            self._deck_chooser.addItem(name, decks[name])
        self._deck_chooser.activated.connect(self._changed)

        self._model_chooser = ExtendedComboBox()
        self._model_chooser.setMaximumWidth(390)

        self.import_style = QCheckBox("אימפארטיר אויך דעם אינהאלט אויסשטעל (א פרואוו פונקציע — ביטע באריכט יעדן אומדערווארטן רעזולטאט)")

        models = {item["name"]: item["id"] for item in mw.col.models.all()}
        for name in sorted(models.keys()):
            self._model_chooser.addItem(name, models[name])
        self._model_chooser.activated.connect(self._changed)


        self._explanation = QLabel()
        self._explanation.setWordWrap(True)
        self._changed()

        self.setdefdeck = QCheckBox("שטעל אלס ברירת מחדל")
        self.setdefmodel = QCheckBox("שטעל אלס ברירת מחדל")

        ##########################################################################################
        #showWarning(str(a))
        try:
            try:
                defdeckconf = a[-2]
                defmodelconf = a[-1]
            except (IndexError, KeyError):
                CONFIG = _addon_config()
                defdeckconf = CONFIG["defdeck"]
                defmodelconf = CONFIG["defmodel"]
        except (KeyError, TypeError):
            defdeckconf = 'קלייבט אויס א פעקל'


        self._deck_chooser.lineEdit().setText(defdeckconf)
        with contextlib.suppress(AttributeError, NameError):
            self._model_chooser.lineEdit().setText(defmodelconf)


##########################################################################################

        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QGridLayout()
        layout.addWidget(QLabel('\n● קלייבט אויס די געוואונטשענע טעקע אדער טעקעס און דעם פעקל וואו די פראגעס זאלן אריינגיין:\n\n● דורך דעם פענסטער קען מען אימפארטירן טעקעס XML וואס זענען עקספארטירט פונעם חזרות פראגראם "קלזכור" בלויז.\n צו אימפארטירן אנדערע טעקעס, נוצט די געווענליכע אימפארט אפציע.\n\n● מען קען אויסקלייבן מערערע טעקעס און זיי אימפארטירן אויפאמאל.\n\n● מען קען זוכן דעם געוואונטשענעם פעקל און סארט קארטל.\n\n● מען קען באשטימען א פעקל און סארט קארטל אלס ברירת מחדל, כדי ביים קומענדיגן עפענען דעם פענסטער\n    זאלן זיי שוין זיין אויסגעקליבן. \n\n● דער אימפארט סדר איז פראגע, ענטפער, מקור, רמז, הוספות. אויב מען קלייבט אויס א סארט קארטל\n    מיט ווייניגער ווי 5 פעלדער, וועלן פרטים פעלן לויטן סדר פונעם סוף צום אנהייב.\n    (געווענליך איז הוספות ליידיג, דערפאר זענען 4 פעלדער גענוג).'), 0, 0, 1, 0)
        layout.addWidget(QHSeparationLine(), 2, 0, 1, 3)
        layout.addWidget(self._label('טעקע xml:'), 3, 0)
        layout.addWidget(self._xml_chooser, 3, 1, 1, 2)
        layout.addWidget(self._label('פעקל:'), 4, 0)
        layout.addWidget(self._deck_chooser, 4, 1, 1, 2)
        layout.addWidget(self.setdefdeck, 5, 1)
        layout.addWidget(self._label('סארט קארטל:'), 6, 0)
        layout.addWidget(self._model_chooser, 6, 1, 1, 2)
        layout.addWidget(self.setdefmodel, 7, 1)
        layout.addWidget(self._label('אויסשטעל:'), 8, 0)
        layout.addWidget(self.import_style, 8, 1, 1, 2)
        layout.addWidget(QHSeparationLine(), 9, 0, 1, 3)
        layout.addWidget(self._explanation, 10, 0, 1, 3)
        layout.addWidget(QHSeparationLine(), 11, 0, 1, 3)
        layout.addWidget(buttonBox, 12, 0, 1, 3)
        self.setLayout(layout)

    xml_file = []

    def duplicateCards1(self, a):
        Dlg_import_xaml.updatetitle(self, a)
        self.xml_file = a
        # showWarning(str(self.xml_file))

    def updatetitle(self, a):
        self._xml_chooser.setText(f"אויסגעקליבן: {a})")

    def _label(self, text):
        label = QLabel(text)
        label.setFixedWidth(90)
        return label

    def _changed(self):
        d = f'די פראגעס וועלן אריינגיין אינעם פעקל:{self._deck_chooser.currentText()}.'
        self._explanation.setText(d)



    def checkifinlist(self):
        decks = {item["name"]: item["id"] for item in mw.col.decks.all()}
        models = {item["name"]: item["id"] for item in mw.col.models.all()}
        deck = sorted(decks.keys())
        model = sorted(models.keys())
        if self._model_chooser.currentText() not in model and self._deck_chooser.currentText() not in deck:
           return "dmabnormal"
        elif self._deck_chooser.currentText() not in deck:
           return "dabnormal"
        elif self._model_chooser.currentText() not in model:
           return "mabnormal"
        else:
            return "ok"

def open_window():
    import_xaml_dialog = Dlg_import_xaml()
    if import_xaml_dialog.exec():
        xml_file = import_xaml_dialog.xml_file
        checkifinlist = import_xaml_dialog.checkifinlist()
        deck = DeckManager.id_for_name(mw.col.decks, import_xaml_dialog._deck_chooser.currentText())
        model = ModelManager.id_for_name(mw.col.models, import_xaml_dialog._model_chooser.currentText())
        defdeck = import_xaml_dialog.setdefdeck
        defmodel = import_xaml_dialog.setdefmodel
        import_style = import_xaml_dialog.import_style.isChecked()
        if defdeck.isChecked():
            setdefconf(import_xaml_dialog._deck_chooser.currentText(), "defdeck")
            b[0] = import_xaml_dialog._deck_chooser.currentText()
        if defmodel.isChecked():
            setdefconf(import_xaml_dialog._model_chooser.currentText(), "defmodel")
            b[1] = import_xaml_dialog._model_chooser.currentText()

        a.clear()
        a.append(import_xaml_dialog._deck_chooser.currentText())
        a.append(import_xaml_dialog._model_chooser.currentText())

        if xml_file == [] :
            showWarning("קיין טעקע איז נישט אויסגעקליבן געווארן")
        elif checkifinlist == "dmabnormal" :
            showWarning("אומגילטיגער פעקל און סארט קארטל.")
        elif checkifinlist == "dabnormal" :
            showWarning("אומגילטיגער פעקל נאמען.")
        elif checkifinlist == "mabnormal" :
            showWarning("אומגילטיגער סארט קארטל.")
        elif checkifinlist == "ok" :
            import_xaml.import_xaml(xml_file, deck, model, import_style)
    else:
        a.clear()
        a.append(import_xaml_dialog._deck_chooser.currentText())
        a.append(import_xaml_dialog._model_chooser.currentText())


def setdefconf(state, confVal):
    config = _addon_config()
    config[confVal] = state
    mw.addonManager.writeConfig(__name__, config)


from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import QComboBox, QCompleter


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

def open_window_from_menu():
    CONFIG = _addon_config()
    _ensure_cached_defaults()
    if b[0] == 0:
        with contextlib.suppress(KeyError, TypeError):
            a[0] = CONFIG["defdeck"]
    else:
        a[0] = b[0]
    if b[1] == 0:
        with contextlib.suppress(KeyError, TypeError):
            a[1] = CONFIG["defmodel"]
    else:
        a[1] = b[1]

def is_kalizcor_xml(path: str) -> bool:
    """Check if a file is a KaliZkor XML export by namespace or known field tags."""
    import xml.etree.ElementTree as ET
    kalizcor_ns = "http://schemas.datacontract.org/2004/07/"
    known_tags = {"שאלה_כמחרוזת", "תשובה_כמחרוזת", "זאמל_שאלה", "זאמל_תשובה"}
    for idx, (_event, elem) in enumerate(ET.iterparse(path, events=("start",))):
        tag = elem.tag
        if tag.startswith("{") and kalizcor_ns in tag:
            return True
        if tag.split("}", 1)[-1] in known_tags:
            return True
        if idx > 200:
            break
    return False


def open_window_with_file(path: str) -> None:
    open_window_from_menu()
    import_xaml_dialog = Dlg_import_xaml(preselected_file=path)
    if import_xaml_dialog.exec():
        xml_file = import_xaml_dialog.xml_file
        checkifinlist = import_xaml_dialog.checkifinlist()
        deck = DeckManager.id_for_name(mw.col.decks, import_xaml_dialog._deck_chooser.currentText())
        model = ModelManager.id_for_name(mw.col.models, import_xaml_dialog._model_chooser.currentText())
        defdeck = import_xaml_dialog.setdefdeck
        defmodel = import_xaml_dialog.setdefmodel
        import_style = import_xaml_dialog.import_style.isChecked()
        if defdeck.isChecked():
            setdefconf(import_xaml_dialog._deck_chooser.currentText(), "defdeck")
            b[0] = import_xaml_dialog._deck_chooser.currentText()
        if defmodel.isChecked():
            setdefconf(import_xaml_dialog._model_chooser.currentText(), "defmodel")
            b[1] = import_xaml_dialog._model_chooser.currentText()
        a.clear()
        a.append(import_xaml_dialog._deck_chooser.currentText())
        a.append(import_xaml_dialog._model_chooser.currentText())
        if xml_file == []:
            showWarning("קיין טעקע איז נישט אויסגעקליבן געווארן")
        elif checkifinlist == "dmabnormal":
            showWarning("אומגילטיגער פעקל און סארט קארטל.")
        elif checkifinlist == "dabnormal":
            showWarning("אומגילטיגער פעקל נאמען.")
        elif checkifinlist == "mabnormal":
            showWarning("אומגילטיגער סארט קארטל.")
        elif checkifinlist == "ok":
            import_xaml.import_xaml(xml_file, deck, model, import_style)
    else:
        a.clear()
        a.append(import_xaml_dialog._deck_chooser.currentText())
        a.append(import_xaml_dialog._model_chooser.currentText())


def _patch_anki_import() -> None:
    """Disconnect Anki's actionImport signal and reconnect to our handler."""
    from aqt.utils import getFile as _getFile
    global _patched_import_handler

    def _our_on_import() -> None:
        # Build file filter: reuse Anki's own endings and add *.xml
        try:
            from aqt.import_export.importing import all_accepted_file_endings
            endings = list(all_accepted_file_endings(mw))
            if ".xml" not in endings:
                endings.append(".xml")
            endings_str = " ".join(f"*{e}" for e in endings)
            filt = f"אלע געשטיצטע פארמאטן ({endings_str});"
        except Exception:
            # fallback for legacy Anki
            try:
                from anki import importing as _anki_importing_mod
                filt = ";;".join(x[0] for x in _anki_importing_mod.importers(mw.col))
            except Exception:
                filt = "אלע טעקעס (*.*)"
            filt += ";;XML - קלזכור (*.xml)"

        path = _getFile(mw, "אימפארטירן א טעקע", None, key="import", filter=filt)
        if not path:
            return
        path = str(path)

        if path.lower().endswith(".xml") and is_kalizcor_xml(path):
            open_window_with_file(path)
        else:
            # Pass the already-selected path directly to Anki's import logic
            try:
                from aqt.import_export.importing import import_file
                import_file(mw, path)
            except ImportError:
                import aqt.importing as _legacy
                _legacy.importFile(mw, path)

    # #155 — מנתקים handler קודם של התוסף כדי שלא תיפתח חלונית בחירת קבצים פעם נוספת.
    if _patched_import_handler is not None:
        with contextlib.suppress(Exception):
            mw.form.actionImport.triggered.disconnect(_patched_import_handler)

    try:
        mw.form.actionImport.triggered.disconnect(mw.onImport)
    except Exception:
        pass
    mw.form.actionImport.triggered.connect(_our_on_import)
    _patched_import_handler = _our_on_import


from anki.hooks import addHook

addHook("profileLoaded", _patch_anki_import)
mw.addonManager.setConfigAction(__name__, lambda: True)
