import aqt
from anki.hooks import addHook, remHook
from aqt import mw

from .internal_fields import iff

singleList = False
userOption = None

def get_Config(key, default=None):
    config = mw.addonManager.getConfig(__name__)
    if not config:
        return default
    return config.get(key, default)


def set_Config(key, value):
    config = mw.addonManager.getConfig(__name__)
    if config is None:
        config = {}
    config[key] = value
    mw.addonManager.writeConfig(__name__, config)



def getUserOption():
    global userOption
    if userOption is None:
        userOption = aqt.mw.addonManager.getConfig(__name__)
    return userOption


def getEachFieldInSingleList():
    return getUserOption().get("Use a single list for fields", False)


def getUseInternalFields():
    return getUserOption().get("Show internal fields", False)


def getNoteModeShortcut():
    return getUserOption().get("Keyboard shortcut for note browser mode", "Ctrl+Alt+N")


def getSelectable():
    return getUserOption().get("Table content", "No interaction")

def getColumnAlignment():
    return getUserOption().get("Column alignment", "Start")

def update(_):
    global userOption
    userOption = None
    processInternal()


def processInternal():
    fn = addHook if getUseInternalFields() else remHook
    fn("advBrowserLoaded", iff.onAdvBrowserLoad)
    fn("advBrowserBuildContext", iff.onBuildContextMenu)


processInternal()

mw.addonManager.setConfigUpdatedAction(__name__, update)
