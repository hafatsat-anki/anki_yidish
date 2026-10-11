# License: AGPLv3

from aqt import mw
from aqt.qt import (
    QDialog,
    QEvent,
    QKeySequence,
    QPushButton,
    QShortcut,
    QSize,
    Qt,
    qtmajor,
)
from aqt.utils import restoreGeom, saveGeom

from _shared_libs.haf_logging import get_logger

from .config import gc
from .lib.pyluach.dates import HebrewDate

logger = get_logger("rescheduler")

if qtmajor == 5:
    from .forms5 import reschedule  # type: ignore  # noqa
else:
    from .forms6 import reschedule  # type: ignore  # noqa


dialogtitle = "alternative_dialog_for_rememorize"


class MultiPrompt(QDialog):
    def __init__(self):
        self.parent = mw.app.activeWindow()
        QDialog.__init__(self, self.parent)
        modality = Qt.WindowModality.WindowModal if qtmajor == 6 else Qt.WindowModal
        self.setWindowModality(modality)
        f = self.form = reschedule.Ui_Dialog()
        f.setupUi(self)
        self.setupHotkeys()

        f.lineEdit.textChanged.connect(self.checkText)  # stackoverflow.com/q/22520747
        f.lineEdit.installEventFilter(self)  # stackoverflow.com/questions/47960368
        tiptext = "לייג צו \"-\" פארן נומער צו טוישן נאר דעם יעצטיגן צייטפלאן. אנדערש טוישט זיך אויך דער חשבון פון די שפעטערדיגע צייטפלאנען"
        f.lineEdit.setToolTip(tiptext)

        up_arrow = Qt.ArrowType.UpArrow if qtmajor == 6 else Qt.UpArrow
        f.tb_up.setArrowType(up_arrow)
        f.tb_up.clicked.connect(lambda _: self.on_arrows(1))
        cut = gc('one_more_day')
        if cut:
            f.tb_up.setToolTip(str(cut))

        down_arrow = Qt.ArrowType.DownArrow if qtmajor == 6 else Qt.DownArrow
        f.tb_down.setArrowType(down_arrow)
        f.tb_down.clicked.connect(lambda _: self.on_arrows(-1))
        cut = gc('one_less_day')
        if cut:
            f.tb_down.setToolTip(str(cut))

        f.pbc_clear.clicked.connect(lambda: f.lineEdit.setText(""))
        f.pbc_enter.clicked.connect(self.accept_read_lineedit)

        if not gc('add_num_area_to_dialog'):
            # hide calculator like input
            # for some reason it doesn't suffice to hide f.vL_calc.setParent(None)
            # if I just run this I will see one remaing button on the upper left of the window
            f.pbc0.setParent(None)
            f.pbc1.setParent(None)
            f.pbc2.setParent(None)
            f.pbc3.setParent(None)
            f.pbc4.setParent(None)
            f.pbc5.setParent(None)
            f.pbc6.setParent(None)
            f.pbc7.setParent(None)
            f.pbc8.setParent(None)
            f.pbc9.setParent(None)
            f.pbc_enter.setParent(None)
            f.pbc_clear.setParent(None)
            f.vL_calc.setParent(None)

        f.pbc0.clicked.connect(lambda: self.add_to_display(0))
        f.pbc1.clicked.connect(lambda: self.add_to_display(1))
        f.pbc2.clicked.connect(lambda: self.add_to_display(2))
        f.pbc3.clicked.connect(lambda: self.add_to_display(3))
        f.pbc4.clicked.connect(lambda: self.add_to_display(4))
        f.pbc5.clicked.connect(lambda: self.add_to_display(5))
        f.pbc6.clicked.connect(lambda: self.add_to_display(6))
        f.pbc7.clicked.connect(lambda: self.add_to_display(7))
        f.pbc8.clicked.connect(lambda: self.add_to_display(8))
        f.pbc9.clicked.connect(lambda: self.add_to_display(9))

        f.pb_clear.clicked.connect(lambda: f.lineEdit.setText(""))
        f.pb_ok_due.clicked.connect(lambda: self.accept_read_lineedit(ivl_and_due=False))
        f.pb_ok_due_and_ivl.clicked.connect(lambda: self.accept_read_lineedit(ivl_and_due=False))
        if gc("default accept is ivl and due", True):
            f.pb_ok_due_and_ivl.setDefault(True)
        else:
            f.pb_ok_due.setDefault(True)
        f.pb_cancel.clicked.connect(self.close)

        f.lineEdit.setFocus()

        f.gb_pos.setTitle("צייטפלאן מיט גרינגקייט פון פריש אויסרעכענען ")
        f.gb_neg.setTitle("נאר דער צייטפלאן")
        f.gb_pos.setToolTip("האט אן השפעה אויך אויף די שפעטערדיגע צייטפלאנען")
        f.gb_neg.setToolTip("האט אן השפעה נאר אויפן יעצטיגן צייטפלאן")


        for v in gc('quick_buttons__left__change_due_and_interval'):
            k = QPushButton()
            today = HebrewDate.today() + v['ivl']
            hebdate = today.hebrew_date_string()
            k.setMinimumSize(QSize(0, 53))  # 53 is the height of the buttons in the top row
            k.setText(v['label']+ "\n(" + hebdate + ")")
            k.setShortcut(v['key'])
            k.setToolTip(v['key'])
            policy = Qt.ContextMenuPolicy.CustomContextMenu if qtmajor == 6 else Qt.CustomContextMenu
            k.setContextMenuPolicy(policy)
            k.clicked.connect(lambda _, a=v['ivl']: self.set_and_accept(days=a, ivl_and_due=True))
            f.vL_pos.addWidget(k)

        for v in gc('quick_buttons__right__change_due_only'):
            k = QPushButton()
            today = HebrewDate.today() + v['ivl']
            hebdate = today.hebrew_date_string()
            k.setMinimumSize(QSize(0, 53))  # 53 is the height of the buttons in the top row
            k.setText(v['label']+ "\n(" + hebdate + ")")
            k.setShortcut(v['key'])
            k.setToolTip(v['key'])
            policy = Qt.ContextMenuPolicy.CustomContextMenu if qtmajor == 6 else Qt.CustomContextMenu
            k.setContextMenuPolicy(policy)
            k.clicked.connect(lambda _, a=v['ivl']: self.set_and_accept(days=a, ivl_and_due=False))
            f.vL_neg.addWidget(k)

        f.pb_forget.setMinimumSize(QSize(0, 53))   # 53 is the height of the buttons in the top row
        f.pb_forget.setText('פארגעס')
        cut = gc('relearn_key')
        if cut:
            f.pb_forget.setToolTip(str(cut))
        f.pb_forget.clicked.connect(lambda: self.set_and_accept(0))
        restoreGeom(self, dialogtitle)

    def checkText(self, arg):
        if arg == "":
            return
        try:
            int(arg)
        except ValueError:
            if not (arg == "+" or arg == "-"):
                self.form.lineEdit.setText(self.form.lineEdit.text()[:-1])
        else:
            return

    def check_key(self, event, confval):
        if qtmajor == 5:
            if (confval and event.key() == eval('Qt.Key_' + str(confval).title())):
                return True
        else:
            if (confval and event.key() == eval('Qt.Key.Key_' + str(confval).title())):
                return True

    def eventFilter(self, source, event):
        type = QEvent.Type.KeyPress if qtmajor == 6 else QEvent.KeyPress
        if (event.type() == type and source is self.form.lineEdit):
            # if (event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_E):
            if (self.form.lineEdit.text() and
                    (self.check_key(event, gc('secondary_accept_1')) or self.check_key(event, gc('secondary_accept_2'))
                    )
                ):
                ivl_and_due = gc("default accept is ivl and due", True)
                if mw.app.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
                    ivl_and_due^=True
                    logger.debug(f"inverted ivl_and_due because of Ctrl to {ivl_and_due}")
                self.accept_read_lineedit(ivl_and_due=ivl_and_due)
                return True
            if self.check_key(event, gc('one_more_day')):
                self.change_value_of_display(1)
                return True
            if self.check_key(event, gc('one_less_day')):
                self.change_value_of_display(-1)
                return True
            if self.check_key(event, gc('relearn_key')):
                self.set_and_accept(0)
                return True
            if gc('quick_buttons__left__change_due_and_interval'):
                for v in gc('quick_buttons__left__change_due_and_interval'):
                    qt_prefix = 'Qt.Key.Key_' if qtmajor == 6 else 'Qt.Key_'
                    if event.key() == eval(qt_prefix + str(v['key'].title())):
                        self.set_and_accept(days=v['ivl'], ivl_and_due=True)
                        return True
            if gc('quick_buttons__right__change_due_only'):
                for v in gc('quick_buttons__right__change_due_only'):
                    qt_prefix = 'Qt.Key.Key_' if qtmajor == 6 else 'Qt.Key_'
                    if event.key() == eval(qt_prefix + str(v['key'].title())):
                        self.set_and_accept(days=v['ivl'], ivl_and_due=False)
                        return True
        return False

    def accept_read_lineedit(self, ivl_and_due=False):
        if len(self.form.lineEdit.text()) == 0:
            return
        days = int(self.form.lineEdit.text())
        self.set_and_accept(days, ivl_and_due)

    def set_and_accept(self, days, ivl_and_due):
        if not ivl_and_due:
            logger.debug("changing due only")
            days = days * -1
        self.days = days
        self.accept()

    def accept(self):
        saveGeom(self, dialogtitle)
        QDialog.accept(self)

    def reject(self):
        saveGeom(self, dialogtitle)
        QDialog.reject(self)

    def change_value_of_display(self, num):
        val = 0 if self.form.lineEdit.text() == "" else int(self.form.lineEdit.text())
        new_val = val + num
        new_val = 0 if new_val < 0 else new_val
        self.form.lineEdit.setText(str(new_val))

    def add_to_display(self, num):
        if (self.form.lineEdit.text() == "" and num == 0):
            pass
        else:
            newstring = self.form.lineEdit.text() + str(num)
            self.form.lineEdit.setText(newstring)

    def on_arrows(self, num):
        if self.form.lineEdit.text() == "":
            self.form.lineEdit.setText(str(0))
        new_val = int(self.form.lineEdit.text()) + num
        new_val = 0 if new_val < 0 else new_val
        self.form.lineEdit.setText(str(new_val))
        today = HebrewDate.today() + new_val
        hebdate = today.hebrew_date_string()
        self.form.datelabel.setText("געפלאנטער דאטום: " + hebdate)

    def setupHotkeys(self):
        keys = [
            [gc('relearn_key'),        lambda: self.set_and_accept(0)],
            [gc('focus_lineedit'),     lambda: self.form.lineEdit.setFocus()],
            [gc('one_more_day'),       lambda: self.change_value_of_display(1)],
            [gc('one_less_day'),       lambda: self.change_value_of_display(-1)],
            [gc('secondary_accept_1'), lambda: self.accept_read_lineedit(ivl_and_due=gc("default accept is ivl and due", True))],
            [gc('secondary_accept_2'), lambda: self.accept_read_lineedit(ivl_and_due=gc("default accept is ivl and due", True))],
        ]
        for cut, func in keys:
                if cut:
                    QShortcut(QKeySequence(str(cut)), self, activated=func)
