import contextlib

import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import (
    add_close_shortcut,
    openLink,
    restoreGeom,
    showInfo,
)
from PyQt6.QtCore import QEventLoop, Qt, QUrl
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QDialog

config = mw.addonManager.getConfig(__name__)


class DlgWebPrinter(QDialog):
    def __init__(self, mw: aqt.main.AnkiQt, tsavepath:str , savepath:str , printto:str) -> None:
        super().__init__()
        QDialog.__init__(self, mw, Qt.WindowType.Window)
        mw.garbage_collect_on_dialog_finish(self)
        self.mw = mw
        self.name = "deckStats"
        self.period = 0
        self.progressbar = QProgressDialog(self)
        self.progressbar.findChild(QProgressBar)
        self.progressbar.setLabelText("מען גרייט צו קארטלעך צו דרוקן. ביטע ווארט.......<br>אכטונג! אויב איר האט אויסגעקליבן אסאך פראגעס, קען די פעולה נעמען א פאר מינוט.")
        self.progressbar.setRange(0, 0)
        self.progressbar.show()
        self.printto = printto
        if self.printto == "pdf":
            self.form = printpdf(tsavepath, "test.pdf", savepath, self.progressbar, self)
        elif self.printto == "printonly":
            self.form = printonly(tsavepath, "test.pdf", savepath, self.progressbar, self)

        restoreGeom(self, self.name)
        add_close_shortcut(self)

        def reject(self) -> None:
            self.form.web.cleanup()
            self.form.web = None
            QDialog.reject(self)






class printonly(QWebEngineView):
    def __init__(self, url, filename, savepath, progressbar, Dialog):
        super().__init__()
        self.url = QUrl.fromUserInput(url)
        self.filename = filename
        self.Dialog = Dialog
        self.m_waitForResult = QEventLoop()
        self.progressbar = progressbar
        self.loadFinished.connect(self.load_finished)
        progressbar.canceled.connect(self.print_canceled)
        self.m_printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.printFinished.connect(self.print_finished)
        self.start()

    def start(self):
        self.load(self.url)

    def load_finished(self, ok):
        if ok:
            self.QPrintPreviewDialog = QPrintPreviewDialog(self.m_printer, parent = aqt.mw.app.activeWindow() or aqt.mw)
            self.QPrintPreviewDialog.paintRequested.connect(self.printDocument)
            self.QPrintPreviewDialog.exec()
            with contextlib.suppress(AttributeError, RuntimeError):
                self.progressbar.close()

        else:
            with contextlib.suppress(AttributeError, RuntimeError):
                self.progressbar.close()

            showInfo("דאס לאדענען איז נישט געלונגען. ביטע באריכט דעם פראבלעם צום הילף צענטער.")

    def printDocument(self, printer):
        self.print(printer)
        self.m_waitForResult.exec()

    def print_finished(self):
        self.m_waitForResult.quit()

    def print_canceled(self):
        self.m_waitForResult.quit()
        self.Dialog.reject()
        del self



class printpdf(QWebEngineView):
    def __init__(self, url, filename, savepath, progressbar, Dialog):
        super().__init__()
        self.url = QUrl.fromUserInput(url)
        self.filename = filename
        self.Dialog = Dialog
        self.progressbar = progressbar
        progressbar.canceled.connect(self.print_canceled)
        self.savepath = savepath
        self.loadFinished.connect(self.load_finished)
        self.pdfPrintingFinished.connect(self.print_finished)
        self.start()

    def start(self):
        self.load(self.url)

    def load_finished(self, ok):
        if ok:
            self.page().printToPdf(self.savepath)
        else:
            self.progressbar.close()
            showInfo("דאס לאדענען איז נישט געלונגען. ביטע באריכט דעם פראבלעם צום הילף צענטער.")

    def print_finished(self):
        self.progressbar.close()
        openLink(QUrl.fromLocalFile(self.savepath).toString())

    def print_canceled(self):
        self.Dialog.reject()
        del self
