"""
Anki Add-on: Progress Bar

Shows progress in the Reviewer in terms of passed cards per session.

Copyright:  (c) Unknown author (nest0r/Ja-Dark?) 2017
            (c) SebastienGllmt 2017 <https://github.com/SebastienGllmt/>
            (c) liuzikai 2018-2020 <https://github.com/liuzikai>
            (c) Glutanimate 2017-2018 <https://glutanimate.com/>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

# Do not modify the following lines

import datetime
import re
import time
from datetime import date
from typing import Any

import aqt
from anki.hooks import wrap
from aqt import gui_hooks, mw
from aqt.qt import *

# from aqt.utils import showInfo, tooltip

############## USER CONFIGURATION START ##############

dockAreamethod=1

# CARD TALLY CALCULATION

# Which queues to include in the progress calculation (all True by default)
includeNew = True
includeRev = True
includeLrn = True

# Only include new cards once reviews are exhausted.
includeNewAfterRevs = True

# Calculation weights
#
#   Setting proper weights will make the progress bar goes smoothly and reasonably.
#
#   For example, if all weight are 1, and you set 2 steps for a new card in your desk config, you will convey
#   one 'new' into two 'learning' card if you press 'again' at the first time, which will increase remaining
#   count and cause the bar to move backward.
#
#   In this case, it's probably a good idea to set newWeight to 2, and remaining count will be calculated as
#   new * 2 + learn + review. Now pressing 'again' will just make it stop going forward, but not backward. If
#   you press 'easy' at first, the progress will go twice as fast, which is still reasonable.
#
#   However, if you press 'good' followed by 'again', there will be another two learning card again, and the
#   progress still needs to go backward. It may not be a big deal, but if you want the progress never goes
#   backward strictly, enable forceForward below.
#
#   Weights should be integers. It's their relative sizes that matters, not absolute values.
#
#   Another example that make the progress goes unstably is 'bury related new cards to next day.' If you have
#   three new cards in a note, there will be 3 new cards at the beginning of your review, but another two will
#   disappear instantly after you learn one of them. However, all three cards will be regarded as 'completed,'
#   so your progress may go three times as fast.

newWeight = 2
revWeight = 1
lrnWeight = 1

# If enabled, the progress will freeze if remaining count has to increase to prevent moving backward,
#   and wait until your correct answers 'make up' this additional part.
#   NOTE: This will not stop the progress from moving backward if you add cards or toggle suspended.
forceForward = False

# PROGRESS BAR APPEARANCE

def get_progress_config():
    config = mw.addonManager.getConfig(__name__)
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise ValueError("Progress bar settings must be a dictionary")
    config = dict(config)
    if config.get("filtered_decks_count") is None:
        if "filtered_decks_count" in config:
            print("[progress-bar] Restoring null filtered deck counters")
        config["filtered_decks_count"] = {}
    if not isinstance(config["filtered_decks_count"], dict):
        raise ValueError("Progress bar filtered deck counters must be a dictionary")
    config.setdefault("Today", "")
    return config


def getConfig(arg, default: Any=""):
    config = get_progress_config()
    if config:
        return config.get(arg, default)
    else:
        return default

showPercent = getConfig("showPercent", False)  # Show the progress text percentage or not.
showNumber = getConfig("showNumber", False)  # Show the progress text as a fraction

qtxt = getConfig("textColor", "aliceblue")  # Percentage color, if text visible.
qbg = getConfig("backgroundColor", "rgba(0, 0, 0, 0)")  # Background color of progress bar.
qfg = getConfig("foregroundColor", "#3399cc")  # Foreground color of progress bar.
qbr = getConfig("borderRadius", 0)  # Border radius (> 0 for rounded corners).

# optionally restricts progress bar width
maxWidth = getConfig("maxWidth", "5px")  # (e.g. "5px". default: "")

scrollingBarWhenEditing = True  # Make the progress bar 'scrolling' when waiting to resume.

orientationHV = Qt.Orientation.Horizontal  # Show bar horizontally (side to side). Use with top/bottom dockArea.

dockArea = Qt.DockWidgetArea.BottomDockWidgetArea # Shows bar at the bottom. Use with horizontal orientation.

pbStyle = ""  # Stylesheet used only if blank. Else uses QPalette + theme style.
'''pbStyle options (insert a quoted word above):
    -- "plastique", "windowsxp", "windows", "windowsvista", "motif", "cde", "cleanlooks"
    -- "macintosh", "gtk", or "fusion" might also work
    -- "windowsvista" unfortunately ignores custom colors, due to animation?
    -- Some styles don't reset bar appearance fully on undo. An annoyance.
    -- Themes gallery: http://doc.qt.io/qt-4.8/gallery.html'''

##############  USER CONFIGURATION END  ##############

dock = QDockWidget()
mw.dock = dock


nmStyleApplied = 0
nmUnavailable = 0
progressBar: QProgressBar or None = None

pbdStyle = QStyleFactory.create(f"{pbStyle}")  # Don't touch.

# Defining palette in case needed for custom colors with themes.
palette = QPalette()
palette.setColor(QPalette.ColorRole.Base, QColor(qbg))
palette.setColor(QPalette.ColorRole.Highlight, QColor(qfg))
palette.setColor(QPalette.ColorRole.Button, QColor(qbg))
palette.setColor(QPalette.ColorRole.WindowText, QColor(qtxt))
palette.setColor(QPalette.ColorRole.Window, QColor(qbg))

if maxWidth:
    if orientationHV == Qt.Orientation.Horizontal:
        restrictSize = f"max-height: {maxWidth};"
    else:
        restrictSize = f"max-width: {maxWidth};"
else:
    restrictSize = ""

try:
    # Remove that annoying separator strip if we have Night Mode, avoiding conflicts with this add-on.
    import Night_Mode

    Night_Mode.nm_css_menu \
        += Night_Mode.nm_css_menu \
           + '''
        QMainWindow::separator
    {
        width: 0px;
        height: 0px;
    }
    '''
except ImportError:
    nmUnavailable = 1

# times
start_of_anki_epoche_day = 0
next_anki_day_start = 0
current_epoch = 0
days_from_crt = 0
def get_timezone_offset():
    utc_now = datetime.datetime.utcnow()
    local_now = datetime.datetime.now()
    offset = local_now - utc_now
    offset_seconds = offset.total_seconds()
    return offset_seconds

def get_beginning_of_current_day_epoch():
    current_date = datetime.datetime.now()
    get_timezone_offset()
    if datetime.datetime.now().hour < mw.col.conf.get("rollover", 4):
        current_date -= datetime.timedelta(days=1)
    # Calculate the beginning of the day by replacing the time with 00:00:00
    beginning_of_day = current_date.replace(hour=mw.col.conf.get("rollover", 4), minute=0, second=0, microsecond=0)
    # Convert the datetime object to epoch time (in seconds)
    #epoch_time = int((beginning_of_day - datetime.datetime(1970, 1, 1)).total_seconds() - offset_seconds)
    epoch_time = int((beginning_of_day - datetime.datetime(1970, 1, 1)).total_seconds())
    return epoch_time


def update_times():
    global current_epoch, start_of_anki_epoche_day, next_anki_day_start, days_from_crt
    current_epoch = int(time.time())
    start_of_anki_epoche_day = get_beginning_of_current_day_epoch()
    next_anki_day_start = start_of_anki_epoche_day + 86400
    days_from_crt = (start_of_anki_epoche_day - mw.col.crt) // 86400

def sql_deck_name()  -> str:
    return re.escape(mw.col.decks.current()['name'].replace("'", "''").replace("::", ""))


# #365 — משקל כרטיס חדש נקבע לפי צעדי הלמידה של החפיסה, לא לפי newWeight קבוע.
#   newWeight=2 הניח תמיד ששני שלבי למידה נופלים באותו יום ("1m 10m"), ולכן כל כרטיס
#   חדש נספר ברוחב כפול. בחפיסה שבה הצעד השני כבר נופל למחר (למשל "1m 1d") או שיש בה
#   צעד יחיד, הכרטיס ייענה היום פעם אחת בלבד — והסרגל הציג אותו כפול ללא הצדקה.
#   מספר התשובות הצפויות היום = 1 (התשובה הראשונה) + כל צעד המשך שמרווחו קצר מיממה.
_new_weight_cache: tuple = ()


def _deck_new_weight(conf: dict) -> int:
    delays = (conf.get("new") or {}).get("delays") or []
    return 1 + sum(1 for d in delays[1:] if float(d) < 1440)


def _new_weight_signature() -> tuple:
    # The storage schema has no stable `mod` column. Read the public API in
    # bulk and key the cache by the actual deck-to-weight mapping instead.
    configs = {int(conf["id"]): conf for conf in mw.col.decks.all_config()}
    weights = []
    for deck in mw.col.decks.all():
        if deck.get("dyn"):
            continue
        conf = configs.get(int(deck["conf"])) or configs.get(1)
        if conf is None:
            raise ValueError(f"Missing configuration for deck {deck['id']}")
        weights.append((int(deck["id"]), _deck_new_weight(conf)))
    return tuple(sorted(weights))


def new_weight_sql() -> str:
    """אן SQL אויסדרוק וואס גיט צוריק דעם וואג פונעם נייעם קארטל לויט דעם פעקל וואו עס געהערט."""
    global _new_weight_cache
    try:
        signature = _new_weight_signature()
    except Exception:
        from _shared_libs.haf_notifications import warn_once
        warn_once('addons/ankiweb/progress-bar_1685464019/reviewer_progress_bar.py:new_weight_sql', 'מען קען נישט אויסרעכענען וואגן לויטן פעקל. די פארשריט לייסט נוצט דעם אלגעמיינעם וואג און קען זיין אומגענוי.')
        return str(newWeight)
    if _new_weight_cache and _new_weight_cache[0] == signature:
        return _new_weight_cache[1]

    by_weight: dict[int, list[int]] = {}
    for did, weight in signature:
        by_weight.setdefault(weight, []).append(did)

    if not by_weight:
        return str(newWeight)
    if len(by_weight) == 1:
        expr = str(next(iter(by_weight)))
    else:
        # המשקל הנפוץ ביותר הופך ל-ELSE כדי לקצר את רשימות ה-IN
        default_weight = max(by_weight, key=lambda w: len(by_weight[w]))
        # כרטיס בחפיסה מסוננת שומר את חפיסת המקור ב-odid — הצעדים נלקחים משם
        home_did = "(CASE WHEN c.odid != 0 THEN c.odid ELSE c.did END)"
        branches = "".join(
            f" WHEN {home_did} IN ({','.join(str(d) for d in dids)}) THEN {weight}"
            for weight, dids in by_weight.items()
            if weight != default_weight
        )
        expr = f"(CASE{branches} ELSE {default_weight} END)"

    _new_weight_cache = (signature, expr)
    return expr


def initPB() -> None:
    """Initialize and set parameters for progress bar, adding it to the dock."""
    update_times()
    global progressBar
    if not progressBar:
        # only create the progress bar and dock if it is the first instance
        progressBar = QProgressBar()
        mw.progressBar = progressBar
        mw.progressBar = progressBar
        _dock(progressBar)
    progressBar.setTextVisible(showPercent or showNumber)
    progressBar.setOrientation(orientationHV)
    if pbdStyle is None:
        progressBar.setStyleSheet(
            f'''
                QProgressBar
                {{
                    text-align:center;
                    color:{qtxt};
                    background-color: {qbg};
                    border-radius: {qbr}px;
                    {restrictSize}
                }}
                QProgressBar::chunk
                {{
                    background-color: {qfg};
                    margin: 0px;
                    border-radius: {qbr}px;
                }}
                ''')
    else:
        progressBar.setStyle(pbdStyle)
        progressBar.setPalette(palette)


def _dock(pb: QProgressBar) -> QDockWidget:
    """Dock for the progress bar. Giving it a blank title bar,
        making sure to set focus back to the reviewer."""
    tWidget = QWidget()
    dock.setObjectName("pbDock")
    dock.setWidget(pb)
    dock.setTitleBarWidget(tWidget)

    # Note: if there is another widget already in this dock position, we have to add ourself to the list

    # first check existing widgets
    existing_widgets = [widget for widget in mw.findChildren(QDockWidget) if mw.dockWidgetArea(widget) == dockArea]
    # mwchildes = [widget for widget in mw.findChildren(QWidget)]
    # showInfo(str(len(mwchildes)))
    # then add ourselves
    if dockAreamethod == 1:
        mw.addDockWidget(dockArea, dock)
    else:
        mw.mainLayout.insertWidget(mw.mainLayout.count(), dock)
    # stack with any existing widgets
    if len(existing_widgets) > 0:
        mw.setDockNestingEnabled(True)

        if dockArea == Qt.DockWidgetArea.TopDockWidgetArea or dockArea == Qt.DockWidgetArea.BottomDockWidgetArea:
            stack_method = Qt.Orientation.Vertical
        if dockArea == Qt.DockWidgetArea.LeftDockWidgetArea or dockArea == Qt.DockWidgetArea.RightDockWidgetArea:
            stack_method = Qt.Orientation.Horizontal
        mw.splitDockWidget(existing_widgets[0], dock, stack_method)

    if qbr > 0 or pbdStyle is not None:
    #     # Matches background for round corners.
    #     # Also handles background for themes' percentage text.
        mw.setPalette(palette)
    mw.web.setFocus()
    return dock


def updatePB(currDID=None) -> None:
    """Update progress bar range and value with currDID, totalCount[] and doneCount[]"""
    current_epoch + 1200
    def revlog_count(with_did) -> int:
        sql_query = f"SELECT count(id) FROM revlog where {with_did} id >= {start_of_anki_epoche_day}000 and id <= {next_anki_day_start}000"
        res = mw.col.db.first(sql_query)[0]
        return res

    if currDID:
        revlog_specific_deck_for_sql = f"cid in (select id from cards where did in (select id from decks where name regexp '(?i)^{sql_deck_name()}($|)')) and"
        cards_specific_deck_for_sql = f"where did in (select id from decks where name regexp '(?i)^{sql_deck_name()}($|)')"
    else:
        revlog_specific_deck_for_sql = ""
        cards_specific_deck_for_sql = ""

    if currDID and mw.col.decks.is_filtered(current_filtered_deck := mw.col.decks.current()["id"]):
        CONFIG = get_progress_config()
        if str(current_filtered_deck) in CONFIG["filtered_decks_count"]:
            ans = get_progress_config()["filtered_decks_count"][str(current_filtered_deck)]
        else:
            ans = 0
    else:
        ans = revlog_count(revlog_specific_deck_for_sql)
    calc_sql = f"""
    select
    SUM (CASE WHEN (c.queue IN (2, 3) AND c.due <= {days_from_crt} or
             c.queue IN (1, 4) AND c.due <= {next_anki_day_start})
             AND c.type NOT in (1, 3) THEN {revWeight}
             ELSE 0 END) as rev,
    SUM(CASE WHEN c.type = 0 and not c.queue in (-1,-2,-3) THEN {new_weight_sql()} ELSE 0 END) as new,
    SUM(CASE WHEN c.type in (1, 3) and not c.queue in (-1, -2,-3)   THEN {lrnWeight} ELSE 0 END) as lrn
    FROM cards c {cards_specific_deck_for_sql}
         """
    # showText(calc_sql)
    rev, new, lrn = mw.col.db.first(calc_sql)
    sch = sum(filter(None, [rev, new, lrn, ans]))
    if sch == 0:  # 100%
        progressBar.setRange(0, 1 if ans == 0 else ans)
        progressBar.setValue(1)
    else:
        progressBar.setRange(0, sch)
        progressBar.setValue(ans)

    if showNumber:
        if showPercent:
            percent = 100 if sch == 0 else int(100 * ans / sch)
            progressBar.setFormat(f"{ans} / {sch} ({percent}%)")
        else:
            progressBar.setFormat(f"{ans} / {sch}")
    nmApplyStyle()


def setScrollingPB() -> None:
    """Make progress bar in waiting style if the state is resetRequired (happened after editing cards.)"""
    progressBar.setRange(0, 0)
    if showNumber:
        progressBar.setFormat("Waiting...")
    nmApplyStyle()


def nmApplyStyle() -> None:
    """Checks whether Night_Mode is disabled:
        if so, we remove the separator here."""
    global nmStyleApplied
    if not nmUnavailable:
        nmStyleApplied = Night_Mode.nm_state_on
    if not nmStyleApplied:
        mw.setStyleSheet(
            '''
        QMainWindow::separator
    {
        width: 0px;
        height: 0px;
    }
    ''')


def afterStateChangeCallBack(state: str, oldState: str = "") -> None:
    if state == "resetRequired":
        if scrollingBarWhenEditing:
            setScrollingPB()
        return
    elif state == "review":
        # #167 — הסרגל המבוקש במבחן הוא counts-bar של bottom-bar מעל "הצג תשובה"; הדוק התחתון נשאר מוסתר בזמן review.
        dock.hide()
        return
    elif state == "deckBrowser":
        # initPB() has to be here, since objects are not prepared yet when the add-on is loaded.
        if not progressBar:
            initPB()
        dock.show()
        updatePB()
        return
    elif state == "profileManager":
        # fix crash with multiple profiles
        return
    elif state == "overview":
        dock.show()
        updatePB(mw.col.decks.current()['name'])
    # else:  # "overview" or "review"
        # updatePB(mw.col.decks.current()['id'])

def mw_reset_callback(changes = None, initiator = None):
    afterStateChangeCallBack(mw.state)

def showQuestionCallBack(*args) -> None:
    if mw.col.decks.is_filtered(current_filtered_deck := mw.col.decks.current()["id"]):
        CONFIG = get_progress_config()
        Today = getConfig("Today")
        if Today != str(date.today()):
            CONFIG["Today"] = str(date.today())
            CONFIG["filtered_decks_count"] = {}
        if str(current_filtered_deck) not in CONFIG["filtered_decks_count"]:
            CONFIG["filtered_decks_count"][str(current_filtered_deck)] = 0
            # CONFIG["filtered_decks_count"][str(current_filtered_deck)] = []
        mw.addonManager.writeConfig(__name__, CONFIG)

    updatePB(mw.col.decks.current()['name'])


def answer_card_CallBack(*args) -> None:
    if mw.col.decks.is_filtered(current_filtered_deck := mw.col.decks.current()["id"]):
        CONFIG = get_progress_config()
        # if mw.reviewer.card.id not in CONFIG["filtered_decks_count"][str(current_filtered_deck)]:
        #     CONFIG["filtered_decks_count"][str(current_filtered_deck)].append(mw.reviewer.card.id)
        CONFIG["filtered_decks_count"][str(current_filtered_deck)]+=1
        mw.addonManager.writeConfig(__name__, CONFIG)

mw.init_progress_bar = initPB
## add menu option to disable pb
# on_off_toggle_action = QAction('הצג סרגל התקדמות')

def pref_checkbox_state_changed(state, confVal):
    global dock, progressBar
    if not state:
        if progressBar is not None:
            progressBar.deleteLater()
        dock.deleteLater()
        progressBar = None
        gui_hooks.state_will_change.remove(afterStateChangeCallBack)
        gui_hooks.state_did_reset.remove(mw_reset_callback)
        gui_hooks.reviewer_did_show_question.remove(showQuestionCallBack)
        gui_hooks.reviewer_did_answer_card.remove(answer_card_CallBack)
    else:
        dock = QDockWidget()
        mw.dock = dock
        initPB()
        if mw.state == "review":
            updatePB(mw.col.decks.current()['name'])
        else:
            updatePB()
        gui_hooks.state_will_change.append(afterStateChangeCallBack)
        gui_hooks.state_did_reset.append(mw_reset_callback)
        gui_hooks.reviewer_did_show_question.append(showQuestionCallBack)
        gui_hooks.reviewer_did_answer_card.append(answer_card_CallBack)
    config = mw.addonManager.getConfig(__name__)
    config[confVal] = state
    mw.addonManager.writeConfig(__name__, config)

def progress_bar_toggle_pref(self:aqt.preferences.Preferences):
    self.form.progress_bar_toggle = QCheckBox('ווייזט די פארשריט לייסט', mw)
    self.form.progress_bar_toggle.setChecked(getConfig('toggle_on_off', True))
    self.form.gridLayout_2.addWidget(self.form.progress_bar_toggle, 4, 0, 1, 2)
    qconnect(self.form.progress_bar_toggle.stateChanged, lambda state, confVal = 'toggle_on_off': pref_checkbox_state_changed(state,confVal))

aqt.preferences.Preferences.setup_global = wrap(aqt.preferences.Preferences.setup_global, progress_bar_toggle_pref, "after")

def on_anki_start(*args):
    config = mw.addonManager.getConfig(__name__)
    if config.get('toggle_on_off') == 2:
        # on_off_toggle_action.setChecked(True)
        gui_hooks.state_will_change.append(afterStateChangeCallBack)
        gui_hooks.state_did_reset.append(mw_reset_callback)
        gui_hooks.reviewer_did_show_question.append(showQuestionCallBack)
        gui_hooks.reviewer_did_answer_card.append(answer_card_CallBack)
    else:
        gui_hooks.state_will_change.remove(afterStateChangeCallBack)
        gui_hooks.state_did_reset.remove(mw_reset_callback)
        gui_hooks.reviewer_did_show_question.remove(showQuestionCallBack)
        gui_hooks.reviewer_did_answer_card.remove(answer_card_CallBack)

mw.addonManager.setConfigUpdatedAction(__name__, on_anki_start)

on_anki_start()
