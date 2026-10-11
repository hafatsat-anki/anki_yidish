# Copyright: (c) 2019 Hikaru Y. <hkrysg@gmail.com>
# Copyright: (c) 2023 mizmu addons https://github.com/hafatsat-anki

import logging
from inspect import stack

import aqt
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom
from PyQt6 import QtWidgets, sip

logger = logging.getLogger(__name__)

ADDON = 'AnkiWebView Inspector'
CONTEXT_MENU_ITEM_NAME = 'Inspect'
FONT_SIZE = 12
QDOCKWIDGET_STYLE = '''
    QDockWidget::title {
        padding-top: 0;
        padding-bottom: 0;
    }
'''


class Inspector(QDockWidget):
    """
    Dockable panel with Qt WebEngine Developer Tools
    """

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setObjectName(ADDON)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea|Qt.DockWidgetArea.RightDockWidgetArea|Qt.DockWidgetArea.BottomDockWidgetArea)
        self.toggleViewAction().setText('Toggle Inspector')
        # make the title bar thinner
        self.setStyleSheet(QDOCKWIDGET_STYLE)
        self.web = None
        self.setup_hooks()

    def setup_hooks(self):
        # メインウィンドウ起動時にはパネルを閉じておく
        gui_hooks.profile_did_open.append(self.hide)
        # プロファイル切り替え時にwebをdelete
        gui_hooks.profile_will_close.append(self.delete_web)
        gui_hooks.webview_will_show_context_menu.append(self.on_context_menu_event)
        gui_hooks.editor_will_show_context_menu.append(self.on_context_menu_event)
        gui_hooks.state_will_change.append(self.on_anki_state_change)

    def on_context_menu_event(self, web, menu):
        menu.addAction(CONTEXT_MENU_ITEM_NAME, lambda: self.setup_web(web.page()))



    def setup_web(self, page):
        if self.web:
            self.web.deleteLater()
        self.web = QWebEngineView(mw)
        self.web.setMinimumWidth(240)

        # font size
        ws = self.web.settings()
        ws.setFontSize(QWebEngineSettings.FontSize.MinimumFontSize, FONT_SIZE)
        ws.setFontSize(QWebEngineSettings.FontSize.MinimumLogicalFontSize, FONT_SIZE)
        ws.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, FONT_SIZE)

        # "Uncaught ReferenceError: qt is not defined"を防ぐために
        # AnkiWebViewと同じwebChannelを使う
        channel = mw.web.page().webChannel()
        self.web.page().setWebChannel(channel)

        self.web.page().setInspectedPage(page)
        self.setWidget(self.web)
        # make sure the panel is docked to main window when displaying
        self.setFloating(False)
        self.show()

        page.toHtml(lambda html: logger.debug(html))

    def on_anki_state_change(self, *_):
        """
        パネルを閉じた状態でAnkiのstateが変わったらwebをdelete
        """
        if self.isHidden():
            self.delete_web()

    def delete_web(self):
        if self.web:
            self.web.deleteLater()
            self.web = None




def main():
    # if not check_qt_version():
    #     return
    inspector = Inspector('', mw)
    mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, inspector)


main()

# (❁´◡`❁) inspector in new window (●'◡'●)

class inspector:
    def setupUi(self, Dialog, page):
        self.centralwidget = QWidget(Dialog)
        Dialog.setWindowTitle("inspect")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.web = QWebEngineView(parent=Dialog)
        channel = mw.web.page().webChannel()
        self.web.page().setWebChannel(channel)
        self.web.page().setInspectedPage(page)
        self.verticalLayout.addWidget(self.web)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2.addLayout(self.verticalLayout)

        Dialog.setCentralWidget(self.centralwidget)


class Newinspector(QMainWindow):
    def __init__(self, page=None) -> None:
        super().__init__(mw.app.activeWindow() or mw, Qt.WindowType.Window)

        self.name = "inspector"
        self.form = inspector()
        # self.setMinimumWidth(700)
        # self.setMinimumHeight(800)
        f = self.form
        f.setupUi(self, page)
        self.show()
        restoreGeom(self, "inspector")
        self.activateWindow()

    def closeWithCallback(self, onsuccess: Callable) -> None:
        saveGeom(self, "inspector")
        aqt.dialogs.markClosed("inspector")
        mw.deferred_delete_and_garbage_collect(self)
        self.close()
        onsuccess()


def on_context_menu_event(web, menu):
    menu.addAction("inspector in new window", lambda: aqt.dialogs.openManyinspector("inspector", page=web.page()))
    # a = menu.addAction("copy page", lambda: copy_page(web.page()))
    #mw.applyShortcuts((("F12", a)))
aqt.DialogManager._dialogs["inspector"] = [Newinspector, None]
gui_hooks.webview_will_show_context_menu.append(on_context_menu_event)
gui_hooks.editor_will_show_context_menu.append(on_context_menu_event)


# next code from Add-on number 354407385 https://ankiweb.net/shared/info/354407385 to open multiple inspectors

aqt.DialogManager._openDialogs = list()

# openMany
def openManyinspector(self, name, *args, **kwargs):
    """Open a new window whose kind is name.

    keyword arguments:
    args -- values passed to the opener.
    name -- the name of the window to open
    """
    (creator, _) = self._dialogs[name]
    instance = creator(*args, **kwargs)
    self._openDialogs.append(instance)
    return instance
aqt.DialogManager.openManyinspector = openManyinspector

# markClosedMultiple
def markClosedMultiple(self):
    caller = stack()[2].frame.f_locals['self']
    if caller in self._openDialogs:
        self._openDialogs.remove(caller)

aqt.DialogManager.markClosedMultiple = markClosedMultiple


# markClosed
def markClosedinspector(self):
    self.markClosedMultiple()
    # self._dialogs["inspector"] = [self._dialogs["inspector"][0], None]
aqt.DialogManager.markClosedinspector = markClosedinspector

# allClosed
old_allClosed = aqt.DialogManager.allClosed
def allClosed(self):
    """
    Whether all windows (except the main window) are marked as
    closed.
    """
    return self._openDialogs == [] and old_allClosed(self)
aqt.DialogManager.allClosed = allClosed

# closeAll
old_closeAll = aqt.DialogManager.closeAll
def closeAll(self, onsuccess):
    """Close all windows (except the main one). Call onsuccess when it's done.

    Return True if some window needed closing.
    None otherwise

    Keyword arguments:
    onsuccess -- the function to call when the last window is closed.
    """
    def callback():
        """Call onsuccess if all window (except main) are closed."""
        if self.allClosed():
            onsuccess()
        else:
            # still waiting for others to close
            pass

    if self.allClosed():
        onsuccess()
        return

    for instance in self._openDialogs:
        # It should be useless. I prefer to keep it to avoid erros
        if not sip.isdeleted(instance):
            if getattr(instance, "silentlyClose", False):
                instance.close()
                callback()
            else:
                instance.closeWithCallback(callback)

    return old_closeAll(self, onsuccess)
aqt.DialogManager.closeAll = closeAll


