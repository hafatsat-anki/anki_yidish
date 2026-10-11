from collections.abc import Callable, Iterable
from typing import NewType

import aqt  # noqa: F401
from anki.rsbackend import DeckTreeNode
from aqt import gui_hooks, mw
from aqt.qt import QEvent, QObject, QTimer

DeckId = NewType("DeckId", int)


def get_first(all_decks: Iterable, *_) -> DeckTreeNode | None:
    try:
        return next(iter(all_decks))
    except StopIteration:
        return None


def get_last(all_decks: Iterable, *_) -> DeckTreeNode | None:
    last = None
    for item in all_decks:
        last = item
    return last


def visible(deck_id):
    parents = mw.col.decks.parents(deck_id)
    return all(not parent.get("collapsed") for parent in parents)


def get_next(all_decks: Iterable, current: DeckId, constraint_check: Callable):
    found_current = False
    for deck in all_decks:
        if found_current and constraint_check(deck.id, current) and visible(deck.id):
            return deck
        if deck.id == current:
            found_current = True
    return None


def get_previous(all_decks: Iterable, current: DeckId, constraint_check: Callable):
    last = None
    for deck in all_decks:
        if deck.id == current:
            break
        if constraint_check(deck.id, current) and visible(deck.id):
            last = deck
    return last


def goto(target: DeckId):
    mw.col.decks.select(target)
    # #349: ב-HTML של Modern Theme שורת החפיסה היא [data-deck-id] ו-class הסימון current
    # יושב על .accordion-button שבתוכה — הסלקטורים המקוריים (id / onclick*='open:') לא
    # מוצאים אותה ולכן הניווט בחיצים לא סימן שום חפיסה. מסירים גם את כל סימוני current
    # הקיימים (ולא רק את הראשון) למניעת סימון כפול.
    mw.web.eval(f"""
    (function(){{
        document.querySelectorAll('.current').forEach(function(c) {{
            c.classList.remove('current');
        }});

        var t = document.getElementById('{target}');
        if (!t) {{
            var host = document.querySelector("[data-deck-id='{target}']");
            if (host) t = host.querySelector('.accordion-button') || host;
        }}
        if (!t)
            t = document.querySelector("[onclick*='open:{target}']");

        if (t) {{
            t.classList.add('current');
            t.scrollIntoView({{block:"nearest", inline:"nearest"}});
        }}
    }})();
    """)


def compare_level(A_id, B_id):
    tree = mw.col.decks.deck_tree()
    A = mw.col.decks.find_deck_in_tree(tree, A_id)
    B = mw.col.decks.find_deck_in_tree(tree, B_id)
    if not A or not B:
        return -1
    return A.level - B.level


def check_same_level(A_id, B_id):
    return compare_level(A_id, B_id) == 0


def check_lower_level(A_id, B_id):
    return compare_level(A_id, B_id) < 0


def move(func: Callable, constraint_check: Callable = lambda *_: True):
    if mw.state != "deckBrowser":
        return
    current = mw.col.decks.selected()
    alldecks = mw.col.decks.all_names_and_ids(skip_empty_default=True)
    deck = func(alldecks, current, constraint_check)
    if deck:
        deck_id = deck.id
        parents = mw.col.decks.parents(deck_id)
        while not visible(deck_id) and parents:
            deck_id = parents.pop().get("id")
        goto(deck_id)


def toggle_collapse():
    current = mw.col.decks.selected()
    if not current:
        return

    deck = mw.col.decks.get(current)
    mw.web.eval(f"""
    var p = document.getElementById('{deck['id']}');
    if (p) {{
        var c = p.querySelector(".collapse-icon");
        if (!c)
            c = p.querySelector(".col-5.row .col:not(.p-0) a");
        if (c) c.click();
    }}
    """)


def goto_next_deck_same_lvl(): move(get_next, check_same_level)
def goto_next_deck(): move(get_next)
def goto_previous_deck_same_lvl(): move(get_previous, check_same_level)
def goto_previous_deck(): move(get_previous)
def goto_parent_deck(): move(get_previous, check_lower_level)
def goto_first_deck(): move(get_first)
def goto_last_deck(): move(get_last)
# #339: startTimebox לפני כניסה ישירה למבחן — מונע AttributeError: _startTime במגבלת זמן
def study(): mw.col.startTimebox(); mw.moveToState("review")


str2func = {
    "goto_first_deck": goto_first_deck,
    "goto_last_deck": goto_last_deck,
    "goto_next_deck": goto_next_deck,
    "goto_next_deck_same_lvl": goto_next_deck_same_lvl,
    "goto_parent_deck": goto_parent_deck,
    "goto_previous_deck": goto_previous_deck,
    "goto_previous_deck_same_lvl": goto_previous_deck_same_lvl,
    "open_overview": mw.onOverview,
    "study": study,
    "toggle_collapse": toggle_collapse,
}

config = mw.addonManager.getConfig(__name__)


# ••• Unified Key Combiner •••


class NavigatorAccelerator(QObject):
    def __init__(self, mw, config, func_map):
        super().__init__(mw)
        self.mw = mw

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_tick)

        self.current_func = None

        # הגדרות מהירות (במילישניות)
        self.base_delay = 300  # זמן המתנה ראשוני לפני שהחזרה מתחילה
        self.initial_rate = 150  # מהירות התחלתית
        self.min_rate = 40  # מהירות מקסימלית (מספר נמוך = מהר יותר)
        self.acceleration_factor = 0.85  # כמה לקצץ מהזמן בכל מחזור (האצה)

        self.current_rate = self.initial_rate

        # אנו מתקינים את הפילטר על האפליקציה כולה כדי לתפוס את המקשים
        mw.app.installEventFilter(self)

    def eventFilter(self, obj, event):
        # פועל רק במסך בחירת החפיסות
        if self.mw.state != "deckBrowser":
            return False

        # if event.type() == QEvent.Type.KeyPress:
        if event.type() == QEvent.Type.KeyRelease:
            key = event.key()

            # קביעת הפונקציה לפי קוד המקש
            func_to_run = None
            if key == 16777235:  # חץ למעלה
                func_to_run = goto_previous_deck
            elif key == 16777237:  # חץ למטה
                func_to_run = goto_next_deck

            if func_to_run:
                # אם המערכת מנסה לעשות חזרה אוטומטית סטנדרטית - אנחנו חוסמים אותה
                # כדי להשתמש במנגנון ההאצה שלנו
                # if event.isAutoRepeat():
                #     return True

                # לחיצה ראשונה - הפעלה מיידית
                self.current_func = func_to_run

                self.current_func()

                # אתחול הטיימר לחזרות הבאות
                self.current_rate = self.initial_rate
                # self.timer.start(self.base_delay)
                return True




        return False

    def on_tick(self):
        if self.current_func:
            # הפעלת הפונקציה
            self.current_func()

            # חישוב המהירות החדשה (האצה)
            new_rate = int(self.current_rate * self.acceleration_factor)
            self.current_rate = max(self.min_rate, new_rate)

            # עדכון הטיימר למהירות החדשה
            self.timer.setInterval(self.current_rate)

accelerator = NavigatorAccelerator(mw, config, str2func)


shortcut_config = []
for key, action in config["keys"].items():
    action_func = str2func.get(action)
    if action_func is not None:
        shortcut_config.append((key, action_func))
scuts = mw.applyShortcuts(shortcut_config)


def setup(state, _old):
    enabled = (state == "deckBrowser")
    for s in scuts:
        s.setEnabled(enabled)


gui_hooks.state_did_change.append(setup)
