import contextlib
import pathlib
from datetime import datetime

# #189 — דרוש לפתיחת Browser מתוך כפתור החיפוש בחלון ההדפסה.
import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import getSaveFile, showWarning
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import QComboBox, QCompleter

from .lib.pyluach.dates import GregorianDate

a = {}
b = [0,0]


# #189 — בניית שאילתת ההדפסה מרוכזת במקום אחד כדי שכפתור החיפוש וההדפסה ישתמשו באותו סינון בדיוק.
def _build_print_search_query(print_dialog) -> str:
    if print_dialog._deck_chooser.currentText() != 'אלע פעקלעך':
        decks = 'deck:' + '"' + print_dialog._deck_chooser.currentText().replace('"', r'\"') + '"'
    else:
        decks = ""
    if print_dialog._tag_chooser.currentText() != '(אלעס)':
        tag = ' tag:' + print_dialog._tag_chooser.currentText().replace('"', r'\"') + '* '
    else:
        tag = ""
    if print_dialog._from_day.value() != 0 or print_dialog._to_day.value() != 0:
        due_from = "prop:due>" + str(print_dialog._from_day.value()) + " "
        due_to = "prop:due<" + str(print_dialog._to_day.value()) + " "
    else:
        due_from = ""
        due_to = ""
    search_query = print_dialog._search_query.text().strip()
    return " ".join(
        part.strip() for part in (decks, tag, due_from, due_to, search_query)
        if part and part.strip()
    )


def _matching_cards_or_warn(findstr: str) -> list[int] | None:
    # #189 — אותה בדיקת תקינות משמשת גם לפתיחה בדפדוף וגם להדפסה כדי לא להריץ שאילתה שגויה פעמיים בדרכים שונות.
    try:
        return mw.col.find_cards(findstr)
    except Exception as e:
        from _shared_libs.haf_notifications import show_failure
        show_failure("די זוך שאילתה איז אומגילטיג. קוקט די זוך תנאים אינעם דרוק פענסטער און פרובירט נאכאמאל.", e)
        return None


def _show_browser_for_print_search(findstr: str) -> None:
    # #189 — פתיחת Browser בפועל מופרדת מהכפתור כדי שחלון ההדפסה יוכל להישאר פתוח ברקע.
    browser = aqt.dialogs.open("Browser", mw)
    browser.search_for(findstr)
    with contextlib.suppress(Exception):
        browser.update_history()
    with contextlib.suppress(Exception):
        browser.activateWindow()
        browser.raise_()


def _open_browser_for_print_search(findstr: str, print_dialog=None) -> None:
    # #189 — כפתור החיפוש פותח את דפדוף Anki עם אותם כרטיסים שהיו נשלחים להדפסה.
    matching_cards = _matching_cards_or_warn(findstr)
    if matching_cards is None:
        return
    if not matching_cards:
        showWarning("קיין קארטלעך זענען נישט געפונען געווארן לויטן פילטער")
        return
    if print_dialog is not None:
        # #189 — החיפוש לא סוגר את חלון ההדפסה; הוא רק מוריד אותו מאחור ופותח את הדפדוף מעליו.
        with contextlib.suppress(Exception):
            print_dialog.setModal(False)
            print_dialog.setWindowModality(Qt.WindowModality.NonModal)
            print_dialog.lower()
        QTimer.singleShot(0, lambda query=findstr: _show_browser_for_print_search(query))
        return
    _show_browser_for_print_search(findstr)



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


class QHSeparationLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(1)
        self.setFixedHeight(20)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)


class DlgPrint(QDialog):
    def __init__(self, parent=mw, initial_deck_name=None):
        super().__init__(parent)
        self._initial_deck_name = initial_deck_name
        self.setWindowTitle('דרוקן')
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self._deck_chooser = ExtendedComboBox()
        self._deck_chooser.setMaximumWidth(390)
        decks = {item["name"]: item["id"] for item in mw.col.decks.all()}
        self._deck_chooser.addItem('אלע פעקלעך', None)
        for name in sorted(decks.keys()):
            self._deck_chooser.addItem(name, decks[name])
        self.setdefdeck = QCheckBox("שטעל אלס ברירת מחדל")

        self.duo_label = self._label("געפלאנטער דאטום (דער דאטום איז צווישן די נומערן, נישט אריינגערעכנט):", False)
        self.duo_label2 = self._label("פאר פראגעס וואס זענען געפלאנט פאר היינט, שרייבט פון טאג \"1-\" ביז טאג \"1\".\nשטעל פון טאג \"0\" ביז טאג \"0\" כדי אריינצונעמען אלע פראגעס.", False)
        self._from_day_label = self._label("פון טאג:", False)
        self._from_day = self._spinbox(0, '\"0\"=היינט. \"1-\"=נעכטן. \"1\"=מארגן.')
        self._to_day_label = self._label("ביז טאג:" ,False)
        self._to_day = self._spinbox(0, '\"0\"=היינט. \"1-\"=נעכטן. \"1\"=מארגן.')
        self._to_day.cleanText()
        duo_holder = QHBoxLayout()
        duo_holder.addSpacing(3)
        duo_holder.setContentsMargins(0,0,0,0)
        widgets = (self.duo_label, self._from_day_label, self._from_day, self._to_day_label, self._to_day)
        for widget in widgets:
            duo_holder.addWidget(widget)
        duo_holder.addStretch()
        duo_holder2 = QHBoxLayout()
        duo_holder2.addSpacing(3)
        duo_holder2.setContentsMargins(0,0,0,0)
        duo_holder2.addWidget(self.duo_label2)
        duo_VBox=QVBoxLayout()
        duo_VBox.addSpacing(3)
        duo_VBox.setContentsMargins(0,0,0,0)
        duo_VBox.addLayout(duo_holder)
        duo_VBox.addLayout(duo_holder2)
        self.duo_box = QGroupBox()
        self.duo_box.setLayout(duo_VBox)

        self._tag_chooser = ExtendedComboBox()
        self._tag_chooser.setMaximumWidth(390)
        self._tag_chooser.addItem('(אלעס)', None)
        for tags in mw.col.tags.all():
            self._tag_chooser.addItem(tags)
        self.setdeftag = QCheckBox("שטעל אלס ברירת מחדל")

        # #189 — שדה חיפוש חופשי מאפשר לבחור שאלות להדפסה לפי כל שאילתת חיפוש של Anki.
        self._search_query = QLineEdit()
        self._search_query.setMaximumWidth(390)
        # #189 — כפתור חיפוש מאפשר לבדוק מיד בדפדוף את אותם כרטיסים שיודפסו.
        self._search_browser_btn = QPushButton("זוך אינעם דורכבלעטערער")
        self._search_browser_btn.clicked.connect(
            lambda: _open_browser_for_print_search(_build_print_search_query(self), self)
        )

        self._sort_chooser = ExtendedComboBox()
        self._sort_chooser.setMaximumWidth(150)
        self.sorts = {"חזרות" : "cardReps",
                        "פעקל" : "deck",
                        "קארטל" : "template",
                        "קארטל געטוישט" : "cardMod",
                        "צייט מרווח" : "cardIvl",
                        "גרינגקייט" : "cardEase",
                        "רשומה" : "note",
                        "רשומה געטוישט" : "noteMod",
                        "פראגע" : "question",
                        "טעותים" : "cardLapses",
                        "סארטיר פעלד" : "noteFld",
                        "געפלאנטער דאטום" : "cardDue",
                        "שאף דאטום" : "noteCrt",
                        "צעטלעך" : "noteTags",
                        "ענטפער" : "answer"
                      }

        for sort in self.sorts:
            self._sort_chooser.addItem(sort)
        self.sort_label = self._label('סארטיר פראגעס לויט:')
        self.reverse_on = self._radio_button("אראפגייענדיגער סדר", 95, True)
        self.reverse_off = self._radio_button("ארויפגייענדיגער סדר", 95)
        reverse_holder = QHBoxLayout()
        reverse_holder.addSpacing(3)
        reverse_holder.setContentsMargins(0,0,0,0)
        widgets = (self.sort_label, self._sort_chooser, self.reverse_on, self.reverse_off)
        for widget in widgets:
            reverse_holder.addWidget(widget)
        reverse_holder.addStretch()
        self.reverse_box = QGroupBox()
        self.reverse_box.setLayout(reverse_holder)
        ##########################################################################################

        self.format_label = self._label("דרוק אויסשטעל:", 76)
        self.format_on = self._radio_button("פולער אויסשטעל", 105, True)
        self.format_off = self._radio_button("נאר אינהאלט", 105)
        self.numer = QCheckBox("לייג צו נומערן")
        self.show_hint = QCheckBox("ווייז באהאלטענע רמזים און מקורות")
        self.add_deck = QCheckBox("דרוק דעם פעקל נאמען")
        format_holder = QGridLayout()
        # format_holder.addSpacing(1)
        QSpacerItem(5,1)
        format_holder.setContentsMargins(0,0,0,0)
        widgets = ((self.format_label,0,1),(self.format_on,0,2),(self.format_off,0,3),(QLabel(""),0,4),(self.numer,1,2),(self.show_hint,1,3),(self.add_deck,1,4))
        for widget, row, col in widgets:
            format_holder.addWidget(widget, row, col)
        # format_holder.addStretch()
        self.format_box = QGroupBox()
        self.format_box.setLayout(format_holder)

        self.ptintorfile_label = self._label("דרוק ציל:", 76)
        self.ptintorfile_on = self._radio_button("נאר דרוקן" ,105, True)
        self.ptintorfile_doc = self._radio_button("זיכער אפ אלס ווארד טעקע", 110)
        self.ptintorfile_off = self._radio_button("זיכער אפ אלס טעקע html", 120)
        self.ptintorpdf = self._radio_button("זיכער אפ אלס טעקע pdf", 110)
        self.ptintorxml = self._radio_button("זיכער אפ אלס טעקע xml (קלזכור)", 160)
        self.ptintorfile_holder = QGridLayout()
        self.ptintorfile_holder.setContentsMargins(0,0,0,0)
        widgets = ((self.ptintorfile_on, 0, 1),(self.ptintorfile_doc, 0, 2),(self.ptintorpdf, 0, 3),(self.ptintorfile_off, 1,1),(self.ptintorxml, 0, 4),(self.ptintorfile_label, 0, 0))
        for widget, row, col in widgets:
            self.ptintorfile_holder.addWidget(widget, row, col)
        self.ptintorfile_box = QGroupBox()
        self.ptintorfile_box.setLayout(self.ptintorfile_holder)

        self._order_chooser = ExtendedComboBox()
        self._order_chooser.setMaximumWidth(390)
        orders = ["די עלטסטע","צופעליג","וואקסנדיגע צייט מרווחים","קלענער ווערנדיגע צייט מרווחים","די מערסטע טעותים","דער צולייג סדר","געפלאנטער דאטום","לעצטנס צוגעלייגט","פארשפעטיגונג אין פארגלייך צום מרווח"]
        for order in orders:
            self._order_chooser.addItem(order, None)

        self.sortqbefore_label = self._label("דרוק סדר:", 76)
        self.sortqbefore_on = self._radio_button("פראגע און ענטפער", 105, True)
        self.sortqbefore_off = self._radio_button("פראגעס באזונדער און ענטפערס באזונדער", 190)
        sortqbefore_holder = QHBoxLayout()
        sortqbefore_holder.addSpacing(3)
        sortqbefore_holder.setContentsMargins(0,0,0,0)
        widgets = (self.sortqbefore_label, self.sortqbefore_on, self.sortqbefore_off)
        for widget in widgets:
            sortqbefore_holder.addWidget(widget)
        sortqbefore_holder.addStretch()
        self.sortqbefore_box = QGroupBox()
        self.sortqbefore_box.setLayout(sortqbefore_holder)

        self.create_filtered_deck = QCheckBox("שאף א געפילטערטן פעקל מיט אלע פראגעס וואס מען וועט דרוקן, אויסגעשטעלט לויטן געפלאנטן דאטום פון שפעט צו פרי (אן אפגעשטעלטע)")

        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout = QGridLayout()
        # #252/#259 — טקסט העזרה מעודכן לייצוא Word העצמאי ולתמונות המוטמעות בתוך docx.
        layout.addWidget(self._label(
'''
   ● מען קען דרוקן לויט נאך פילטערס דורך שאפן א געפילטערטן פעקל און אים דרוקן פון דעם פענסטער.
     ● מען קען עקספארטירן צו א ווארד טעקע אויך ווען ווארד איז נישט אינסטאלירט אויפן קאמפיוטער.
   ● עצה: מען קען אויסקלייבן דעם גאנצן געדרוקטן טעקסט מיט א דרוק דערויף, און דערנאך מיט די קיצור קנעפלעך Ctrl + A.
    ● ביים עקספארטירן פראגעס צו ווארד, אויב מען קלייבט צוויי אדער מער שפאלטן, זענען זיי אויסגעשטעלט פון לינקס צו רעכטס.
      מען קען דאס גרינג פאררעכטן אינעם אויסשטעל טאב ביי נאך שפאלטן.
        ● ביים עקספארטירן פראגעס צו ווארד ווערן די בילדער פון די קארטלעך אפגעזיכערט אינעם טעקע-Word אליין.'''
        , False),0, 0, 1, 0)

        layout.addWidget(QHSeparationLine(), 2, 0, 1, 3)
        layout.addWidget(self._label('פעקל צו דרוקן:'), 7, 0)
        layout.addWidget(self._deck_chooser, 7, 1)
        layout.addWidget(self.setdefdeck, 7, 2)
        layout.addWidget(self._label('צעטל:'),9, 0)
        layout.addWidget(self._tag_chooser, 9, 1)
        layout.addWidget(self.setdeftag, 9, 2)
        # #189 — שורת החיפוש יושבת ליד הסינונים הקיימים ונבנית יחד איתם לשאילתת find_cards אחת.
        layout.addWidget(self._label('זוכעניש:'), 10, 0)
        layout.addWidget(self._search_query, 10, 1)
        layout.addWidget(self._search_browser_btn, 10, 2)
        layout.addWidget(self.duo_box, 11, 0, 1, 3)
        layout.addWidget(self.reverse_box, 12, 0, 1, 3)
        layout.addWidget(self.format_box, 15, 0, 1, 3)
        layout.addWidget(self.sortqbefore_box, 19, 0, 1, 3)
        layout.addWidget(self.ptintorfile_box, 20, 0, 1, 3)
        layout.addWidget(self.create_filtered_deck, 21, 0, 1, 3)
        layout.addWidget(buttonBox, 22, 0, 1, 3)
        self.setLayout(layout)

        self.update_checked()
        if self._initial_deck_name:
            self._select_deck_name(self._initial_deck_name)

        self.ptintorxml.toggled.connect(self.disable_buttons_on_xml)
        self.sortqbefore_checked = None

        if self.ptintorxml.isChecked():
            self.disable_buttons_on_xml(True)

    def disable_buttons_on_xml(self, checked):
        if not checked:
            self.sortqbefore_on.setCheckable(True)
            self.sortqbefore_off.setCheckable(True)
            if self.sortqbefore_checked is not None:
                self.sortqbefore_checked.setChecked(True)
        else:
            self.sortqbefore_checked = self.sortqbefore_on if self.sortqbefore_on.isChecked() else self.sortqbefore_off
            self.sortqbefore_on.setCheckable(False)
            self.sortqbefore_off.setCheckable(False)

##########################################################################################
    # xml_file = []

    def _spinbox(self, value, tooltip):
        spinbox = QSpinBox()
        spinbox.setRange(-100, 100)
        spinbox.setValue(value)
        spinbox.setSingleStep(1)
        spinbox.setToolTip(tooltip)
        return spinbox

    def _label(self, text, width=90):
        label = QLabel(text)
        if width:
            label.setFixedWidth(width)
        return label
    def _radio_button(self, text, width, checked = False):
            radio_button = QRadioButton(text)
            radio_button.setFixedWidth(width)
            if checked:
                radio_button.setChecked(checked)
            return radio_button

    def _select_deck_name(self, deck_name):
        # #265 — פתיחה מתפריט חפיסה ממקדת את דיאלוג ההדפסה על החפיסה שנלחצה.
        index = self._deck_chooser.findText(deck_name)
        if index >= 0:
            self._deck_chooser.setCurrentIndex(index)
        else:
            self._deck_chooser.lineEdit().setText(deck_name)

    def checkifinlist(self):
        decks = {item["name"]: item["id"] for item in mw.col.decks.all()}
        deck = sorted(decks.keys())
        tag = []
        for item in mw.col.tags.all():
            tag.append(item)

        if self._deck_chooser.currentText() not in deck and self._deck_chooser.currentText() != 'אלע פעקלעך' and self._tag_chooser.currentText() not in tag and self._tag_chooser.currentText() != '(אלעס)':
            return "dmabnormal"
        elif self._deck_chooser.currentText() not in deck and self._deck_chooser.currentText() != 'אלע פעקלעך':
            return "dabnormal"
        elif self._tag_chooser.currentText() not in tag and self._tag_chooser.currentText() != '(אלעס)':
            #showInfo(str(tag))
            return "mabnormal"
        else:
            return "ok"

    def update_checked(self):
        # showWarning(str(a))
        try:
            try:
                # showInfo(str(a))
                deforder = a["deforder"]
                defdeckconf = a["defdeck"]
                deftagconf = a["deftag"]
                defsortconf = a["defsort"]
                # #189 — תיבת החיפוש מתאפסת בכל פתיחה חדשה של חלון ההדפסה ולא נשמרת בזיכרון החלון הקודם.
                print_search = ""
                # _from_day = a["_from_day"]
                # _to_day = a["_to_day"]
                _from_day = 0
                _to_day = 0
                format_on = a["format_on"]
                format_off = a["format_off"]
                ptintorpdf = a["ptintorpdf"]
                ptintorxml = a["ptintorxml"]
                ptintorfile_on = a["ptintorfile_on"]
                ptintorfile_off = a["ptintorfile_off"]
                ptintorfile_doc = a["ptintorfile_doc"]
                sortqbefore_on = a["sortqbefore_on"]
                sortqbefore_off = a["sortqbefore_off"]
                numer = a["numer"]
                show_hint = a["show_hint"]
                add_deck = a["add_deck"]

                # showWarning("מהמילון")
            except Exception:
                CONFIG = mw.addonManager.getConfig(__name__)
                deforder = CONFIG["deforder"]
                defdeckconf = CONFIG["defdeck"]
                deftagconf = CONFIG["deftag"]
                defsortconf = 'געפלאנטער דאטום'
                print_search = ""
                # _from_day = CONFIG["_from_day"]
                # _to_day = CONFIG["_to_day"]
                _from_day = 0
                _to_day = 0
                format_on = CONFIG["format_on"]
                format_off = CONFIG["format_off"]
                ptintorpdf = CONFIG["ptintorpdf"]
                ptintorxml = CONFIG["ptintorxml"]
                ptintorfile_on = CONFIG["ptintorfile_on"]
                ptintorfile_off = CONFIG["ptintorfile_off"]
                ptintorfile_doc = CONFIG["ptintorfile_doc"]
                sortqbefore_on = CONFIG["sortqbefore_on"]
                sortqbefore_off = CONFIG["sortqbefore_off"]
                numer = CONFIG["numer"]
                show_hint = CONFIG["show_hint"]
                add_deck = CONFIG["add_deck"]
                # showWarning("מהמטא")

        except Exception:
            # showWarning(str(traceback.format_exc()))
            defdeckconf = 'אלע פעקלעך'
            deftagconf = '(אלעס)'
            defsortconf = 'געפלאנטער דאטום'
            print_search = ""
            deforder = 0
            _from_day = 0
            _to_day = 0
            format_on = True
            format_off = False
            ptintorfile_on = True
            ptintorpdf = False
            ptintorxml = False
            ptintorfile_off = False
            ptintorfile_doc = False
            sortqbefore_on = True
            sortqbefore_off = False
            numer = True
            show_hint = True
            add_deck = True

            # showWarning("כלום")

        self._deck_chooser.lineEdit().setText(defdeckconf)
        self._tag_chooser.lineEdit().setText(deftagconf)
        self._sort_chooser.lineEdit().setText(defsortconf)
        self._search_query.setText(print_search)
        self._order_chooser.setCurrentIndex(deforder)
        self._from_day.setValue(_from_day)
        self._to_day.setValue(_to_day)
        self.format_on.setChecked(format_on)
        self.format_off.setChecked(format_off)
        self.ptintorfile_on.setChecked(ptintorfile_on)
        self.ptintorpdf.setChecked(ptintorpdf)
        self.ptintorxml.setChecked(ptintorxml)
        self.ptintorfile_off.setChecked(ptintorfile_off)
        self.ptintorfile_doc.setChecked(ptintorfile_doc)
        self.sortqbefore_on.setChecked(sortqbefore_on)
        self.sortqbefore_off.setChecked(sortqbefore_off)
        self.numer.setChecked(numer)
        self.show_hint.setChecked(show_hint)
        self.add_deck.setChecked(add_deck)

_active_print_dialogs = set()


# #189 — עיבוד תוצאת דיאלוג ההדפסה מופרד מהפתיחה כדי שהדיאלוג יוכל להיות modeless בזמן חיפוש בדפדוף.
def _finish_print_dialog(print_dialog: DlgPrint, result_code) -> None:
    _active_print_dialogs.discard(print_dialog)
    if result_code:
        checkifinlist = print_dialog.checkifinlist()

        if print_dialog._deck_chooser.currentText() != 'אלע פעקלעך':
            decks = 'deck:' + '"' + print_dialog._deck_chooser.currentText().replace('"', r'\"') + '"'
        else:
            decks = ""
        if print_dialog._tag_chooser.currentText() != '(אלעס)':
            tag = ' tag:' + print_dialog._tag_chooser.currentText().replace('"', r'\"') + '* '
        else:
            tag = ""
        # #189 — הטקסט החופשי יצורף לסינונים הקיימים במקום להחליף אותם.
        search_query = print_dialog._search_query.text().strip()

        defdeck = print_dialog.setdefdeck
        deftag = print_dialog.setdeftag

        if defdeck.isChecked():
            setdefconf(print_dialog._deck_chooser.currentText(), "defdeck")
            b[0] = print_dialog._deck_chooser.currentText()
        if deftag.isChecked():
            setdefconf(print_dialog._tag_chooser.currentText(), "deftag")
            b[1] = print_dialog._tag_chooser.currentText()

        a.clear()
        a["deforder"] = print_dialog._order_chooser.currentIndex()
        a["defdeck"] = print_dialog._deck_chooser.currentText()
        a["deftag"] = print_dialog._tag_chooser.currentText()
        a["defsort"] = print_dialog._sort_chooser.currentText()
        # #189 — לא שומרים את החיפוש החופשי אחרי סגירת חלון ההדפסה.
        a["print_search"] = ""
        a["_from_day"] = print_dialog._from_day.value()
        a["_to_day"] = print_dialog._to_day.value()
        a["format_on"] = print_dialog.format_on.isChecked()
        a["format_off"] = print_dialog.format_off.isChecked()
        a["ptintorfile_on"] = print_dialog.ptintorfile_on.isChecked()
        a["ptintorfile_off"] = print_dialog.ptintorfile_off.isChecked()
        a["ptintorfile_doc"] = print_dialog.ptintorfile_doc.isChecked()
        a["ptintorpdf"] = print_dialog.ptintorpdf.isChecked()
        a["ptintorxml"] = print_dialog.ptintorxml.isChecked()
        a["sortqbefore_on"] = print_dialog.sortqbefore_on.isChecked()
        a["sortqbefore_off"] = print_dialog.sortqbefore_off.isChecked()
        a["numer"] = print_dialog.numer.isChecked()
        a["show_hint"] = print_dialog.show_hint.isChecked()
        a["add_deck"] = print_dialog.add_deck.isChecked()
        setdefconf(print_dialog._order_chooser.currentIndex(), "deforder")
        setdefconf(print_dialog.format_on.isChecked(), "format_on")
        setdefconf(print_dialog.format_off.isChecked(), "format_off")
        setdefconf(print_dialog.ptintorfile_on.isChecked(), "ptintorfile_on")
        setdefconf(print_dialog.ptintorfile_off.isChecked(), "ptintorfile_off")
        setdefconf(print_dialog.ptintorxml.isChecked(), "ptintorxml")
        setdefconf(print_dialog.ptintorfile_doc.isChecked(), "ptintorfile_doc")
        setdefconf(print_dialog.sortqbefore_on.isChecked(), "sortqbefore_on")
        setdefconf(print_dialog.sortqbefore_off.isChecked(), "sortqbefore_off")
        setdefconf(print_dialog.numer.isChecked(), "numer")
        setdefconf(print_dialog.show_hint.isChecked(), "show_hint")
        setdefconf(print_dialog.add_deck.isChecked(), "add_deck")



        if checkifinlist == "dmabnormal":
            showWarning("אומגילטיגער פעקל און צעטל.")
            open_window()
        elif checkifinlist == "dabnormal":
            showWarning("אומגילטיגער פעקל נאמען.")
            open_window()
        elif checkifinlist == "mabnormal":
            showWarning("אומגילטיגע צעטל.")
            open_window()
        elif checkifinlist == "ok":
            # #189 — ההדפסה משתמשת באותה שאילתה מרוכזת של כפתור החיפוש בדפדוף.
            findstr = _build_print_search_query(print_dialog)
            # showInfo(findstr)
            matching_cards = _matching_cards_or_warn(findstr)
            if matching_cards is None:
                open_window()
                return
            if len(matching_cards) == 0:
                showWarning("קיין קארטלעך זענען נישט געפונען געווארן לויטן פילטער")
                open_window()
            else:
                if print_dialog.ptintorfile_on.isChecked():
                    filename = str(pathlib.Path(__file__).parent.resolve())
                    file = filename + r'\dshfd578242.html'
                    #showInfo(str(file))
                else:
                    type=""
                    fileappend = ""
                    if print_dialog.ptintorfile_off.isChecked():
                        type="html"
                        fileappend= " צו דרוקן.html"
                    elif print_dialog.ptintorfile_doc.isChecked():
                        type="docx"
                        fileappend= " צו דרוקן.docx"
                    elif print_dialog.ptintorpdf.isChecked():
                        type="pdf"
                        fileappend= " צו דרוקן.pdf"
                    elif print_dialog.ptintorxml.isChecked():
                        type="xml"
                        fileappend= " צו דרוקן.xml"

                    file = getSaveFile(
                        DlgPrint(),
                        "קלייבט אויס א פלאץ",
                        "export",
                        type,
                        fileappend,
                        fname=print_dialog._deck_chooser.currentText().replace("::", "."),
                    )
                    if print_dialog.ptintorfile_doc.isChecked():
                        file = file.replace(".docx", ".html")
                    elif print_dialog.ptintorpdf.isChecked():
                        file = file.replace(".pdf", ".html")
                    elif print_dialog.ptintorxml.isChecked():
                        file = file

                if not file:
                    showWarning("קיין פלאץ איז נישט אויסגעקליבן געווארן.")
                    open_window()
                else:
                    formating = print_dialog.format_on.isChecked()#עם עיצוב או ללא עיצוב
                    ptintorfile = ""
                    if print_dialog.ptintorfile_on.isChecked():
                        ptintorfile = "printonly"#קובץ או הדפסה
                    elif print_dialog.ptintorfile_off.isChecked():
                        ptintorfile = "file"#קובץ או הדפסה
                    elif print_dialog.ptintorfile_doc.isChecked():
                        ptintorfile = "doc"#קובץ או הדפסה
                    elif print_dialog.ptintorpdf.isChecked():
                        ptintorfile = "pdf"#קובץ או הדפסה
                    elif print_dialog.ptintorxml.isChecked():
                        ptintorfile = "xml"#קובץ או הדפסה

                    deckname = print_dialog._deck_chooser.currentText()
                    sortqbefore = print_dialog.sortqbefore_on.isChecked() #סדר שאלות
                    numer = print_dialog.numer.isChecked()#מספור
                    show_hint = print_dialog.show_hint.isChecked()#מספור
                    add_deck = print_dialog.add_deck.isChecked()#מספור
                    order = print_dialog.sorts.get(print_dialog._sort_chooser.currentText())
                    ascending = print_dialog.reverse_on.isChecked()
                    create_filtered_deck = False
                    if print_dialog.create_filtered_deck.isChecked():
                        create_filtered_deck = True
                    from .printer import onPrint
                    onPrint(print_dialog, file, findstr, formating, ptintorfile, sortqbefore, numer, show_hint, add_deck, deckname, order, ascending, create_filtered_deck)

    else:
        a.clear()
        a["deforder"] = print_dialog._order_chooser.currentIndex()
        a["defdeck"] = print_dialog._deck_chooser.currentText()
        a["deftag"] = print_dialog._tag_chooser.currentText()
        a["defsort"] = print_dialog._sort_chooser.currentText()
        # #189 — גם בביטול לא שומרים את החיפוש החופשי; כל סגירה מאפסת את התיבה.
        a["print_search"] = ""
        a["_from_day"] = print_dialog._from_day.value()
        a["_to_day"] = print_dialog._to_day.value()
        a["format_on"] = print_dialog.format_on.isChecked()
        a["format_off"] = print_dialog.format_off.isChecked()
        a["ptintorfile_on"] = print_dialog.ptintorfile_on.isChecked()
        a["ptintorfile_off"] = print_dialog.ptintorfile_off.isChecked()
        a["ptintorfile_doc"] = print_dialog.ptintorfile_doc.isChecked()
        a["ptintorpdf"] = print_dialog.ptintorpdf.isChecked()
        a["ptintorxml"] = print_dialog.ptintorxml.isChecked()
        a["sortqbefore_on"] = print_dialog.sortqbefore_on.isChecked()
        a["sortqbefore_off"] = print_dialog.sortqbefore_off.isChecked()
        a["numer"] = print_dialog.numer.isChecked()
        a["show_hint"] = print_dialog.show_hint.isChecked()
        setdefconf(print_dialog._order_chooser.currentIndex(), "deforder")
        setdefconf(print_dialog.format_on.isChecked(), "format_on")
        setdefconf(print_dialog.format_off.isChecked(), "format_off")
        setdefconf(print_dialog.ptintorfile_on.isChecked(), "ptintorfile_on")
        setdefconf(print_dialog.ptintorfile_off.isChecked(), "ptintorfile_off")
        setdefconf(print_dialog.ptintorfile_doc.isChecked(), "ptintorfile_doc")
        setdefconf(print_dialog.ptintorpdf.isChecked(), "ptintorpdf")
        setdefconf(print_dialog.ptintorxml.isChecked(), "ptintorxml")
        setdefconf(print_dialog.sortqbefore_on.isChecked(), "sortqbefore_on")
        setdefconf(print_dialog.sortqbefore_off.isChecked(), "sortqbefore_off")
        setdefconf(print_dialog.numer.isChecked(), "numer")
        setdefconf(print_dialog.show_hint.isChecked(), "show_hint")


# #189 — חלון ההדפסה נפתח כ-modeless, כך שפתיחת Browser מכפתור החיפוש משאירה אותו ממתין ברקע במקום לחסום או להיסגר.
def _deck_name_from_id(deck_id):
    if deck_id is None:
        return None
    with contextlib.suppress(Exception):
        return mw.col.decks.name(deck_id)
    return None


# #189 — חלון ההדפסה נפתח כ-modeless, כך שפתיחת Browser מכפתור החיפוש משאירה אותו ממתין ברקע במקום לחסום או להיסגר.
def open_window(deck_id=None, deck_name=None):
    open_window_from_menu()
    initial_deck_name = deck_name or _deck_name_from_id(deck_id)
    print_dialog = DlgPrint(initial_deck_name=initial_deck_name)
    print_dialog.setModal(False)
    print_dialog.setWindowModality(Qt.WindowModality.NonModal)
    _active_print_dialogs.add(print_dialog)
    print_dialog.finished.connect(
        lambda result_code, dialog=print_dialog: _finish_print_dialog(dialog, result_code)
    )
    print_dialog.show()
    print_dialog.raise_()
    print_dialog.activateWindow()


def create_filtered_deck(_filter_string, order) :
        today_heb = GregorianDate.today().to_heb().hebrew_date_string()
        now = datetime.now().strftime('%H:%M:%S')
        f_deck_name = mw.col.decks.new_filtered("פראגעס געדרוקט אום: " + today_heb + " " + now)
        f_deck = mw.col.decks.current()
        f_deck['resched'] = True
        f_deck['delays'] = None
        f_deck['terms'] = [[_filter_string, 10000, 7]]
        mw.col.decks.save(f_deck)
        mw.col.sched.rebuild_filtered_deck(f_deck_name)
        mw.reset()



def setdefconf(state, confVal):
    config = mw.addonManager.getConfig(__name__)
    config[confVal] = state
    mw.addonManager.writeConfig(__name__, config)


def open_window_from_menu():
    CONFIG = mw.addonManager.getConfig(__name__)
    if b[0] == 0:
        with contextlib.suppress(KeyError, IndexError):
            a[0] = CONFIG["defdeck"]
    else:
        with contextlib.suppress(KeyError, IndexError):
            a[0] = b[0]
    if b[1] == 0:
        with contextlib.suppress(KeyError, IndexError):
             a[1] = CONFIG["deftag"]
    else:
        with contextlib.suppress(KeyError, IndexError):
            a[1] = b[1]
