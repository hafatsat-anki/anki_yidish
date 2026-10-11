
from aqt import mw
from aqt.main import AnkiQt
from aqt.qt import *


def realOverview(self):
    self.moveToState("overview")

def onOverview(self):
    self.onReview()

def onReview(self):
    # #339: כניסה ישירה למבחן עוקפת את מסך הסקירה שבו אנקי קורא ל-startTimebox().
    # בלי הקריאה, check_timebox נופל על AttributeError: _startTime כשמוגדרת מגבלת זמן.
    self.col.startTimebox()
    self.moveToState("review")

AnkiQt.onOverview = onOverview
AnkiQt.realOverview = realOverview
AnkiQt.onReview = onReview

def onStudyKey(self):
    self.onReview()

AnkiQt.onStudyKey = onStudyKey

for shortcut in mw.findChildren(QShortcut):
    key = shortcut.key().toString()
    if key == "S":
        shortcut.disconnect()
        shortcut.activated.connect(mw.onStudyKey)
        break


m = mw.form
m.actionStudyDeck.triggered.disconnect()
m.actionStudyDeck.triggered.connect(mw.onStudyDeck)
