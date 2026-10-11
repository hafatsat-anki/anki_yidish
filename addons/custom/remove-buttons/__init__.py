import contextlib
import pathlib
import re as _re

import aqt.browser.browser
import aqt.fields
from anki.hooks import wrap
from aqt import gui_hooks, mw
from aqt.browser import SidebarTreeView
from aqt.editor import Editor
from aqt.qt import *
from aqt.utils import qconnect, tr
from aqt.webview import AnkiWebViewKind

from .decktorani import alert, testFunction

# #404 — Translate the native WebEngine touch popup in the Hebrew fixes addon.
from .touch_translation import install as _install_touch_translation

_install_touch_translation()

# #418 — Apply field-scoped list spacing in editor shadow roots and cards.
from .list_spacing import install as _install_list_spacing

_install_list_spacing()

# ##remove actions from menus
# mw.form.menuEdit.removeAction(mw.form.actionUndo)
mw.form.menuCol.removeAction(mw.form.actionExit)
mw.form.menuCol.removeAction(mw.form.action_create_backup)
mw.form.menubar.setFixedHeight(0)
edit_menu = mw.form.menuCol
action = mw.form.actionUndo
edit_menu.addAction(action)
action = mw.form.actionRedo
filename = str(pathlib.Path(__file__).parent.resolve())
icon = QIcon(filename + "/redo.png")
mw.form.actionRedo.setIcon(icon)
edit_menu.addAction(action)
sync_action = QAction(mw)
sync_action.setText("סינכראניזירן")
sync_action.setProperty("haf_menu_icon", "sync")
sync_action.setProperty("haf_menu_color", "#947e69")
sync_action.setIcon(QIcon(filename + "/sync.png"))
sync_action.triggered.connect(mw.onSync)
#mw.form.menuCol.addAction(sync_action)
mw.form.menuCol.insertAction(mw.form.menuCol.actions()[1], sync_action)

action_create_backup = mw.form.action_create_backup
mw.form.menuCol.insertAction(mw.form.menuCol.actions()[1], action_create_backup)
action_open_backup =mw.form.action_open_backup
mw.form.menuCol.insertAction(mw.form.menuCol.actions()[2], action_open_backup)

mw.form.menuCol.addAction(mw.form.actionAdd_ons)

icon = QIcon(filename + "/addon.png")
mw.form.actionAdd_ons.setIcon(icon)
mw.form.menuCol.addAction(mw.form.actionPreferences)

# #יצירת תפריט כלי מאגר
mw.addon_col_menu = QMenu(("&זאמלונג כלים"), mw)
icon = QIcon(filename + "/coltool.png")
mw.addon_col_menu.setIcon(icon)
mw.form.menuCol.insertMenu(
    mw.form.menuTools.menuAction(), mw.addon_col_menu)
# יצירת תפריט תצוגה (הגדרות זום ועוד ייכנסו לכאן)
mw.addon_view_menu = QMenu("&אויסשטעל", mw)
mw.addon_view_menu.setIcon(QIcon(filename + "/disp.png"))
mw.addon_view_menu.addMenu(mw.form.menuqt_accel_view)
# לא מוסיפים לתפריט menuCol כאן – reorganize_col_menu יסדר הכל
mw.addon_col_menu.addAction(mw.form.actionFullDatabaseCheck)
mw.addon_col_menu.addAction(mw.form.actionCheckMediaDatabase)
icon = QIcon(filename + "/madiacheck.png")
mw.form.actionCheckMediaDatabase.setIcon(icon)
mw.addon_col_menu.addAction(mw.form.actionEmptyCards)
icon = QIcon(filename + "/empty.png")
mw.form.actionEmptyCards.setIcon(icon)
#הוספת אפשרות לחפיסות תורניות ריקות
action = QAction("לייג צו מסודרדיגע ליידיגע תורה פעקלעך", mw)
qconnect(action.triggered, testFunction)
qconnect(action.triggered, alert)
filename = str(pathlib.Path(__file__).parent.resolve())
icon = QIcon(filename + "/decktorany.png")
action.setIcon(icon)
mw.addon_col_menu.addAction(action)
action = QAction("פיר סארטן רשומה", mw)
qconnect(action.triggered, mw.onNoteTypes)
filename = str(pathlib.Path(__file__).parent.resolve())
icon = QIcon(filename + "/manage.png")
action.setIcon(icon)
mw.addon_col_menu.addAction(action)

#מחיקת תפריטי כלים ועריכה
# mw.form.menuEdit.deleteLater()
# mw.form.menuTools.deleteLater()
################################################################mw.form.menuTools.deleteLater()

#################
####מסך דפדוף####
#################


#מחיקת כפתורים מתפריטי מסך הדפדוף
def setupMenu(browser):
    menu = browser.form.menuEdit
    browser.form.menuEdit.setTitle("טעקע")
    action = browser.form.action_toggle_mode
    menu.removeAction(action)
    menu.addSeparator()
    action = browser.form.actionManage_Note_Types
    menu.addAction(action)
    menu.addSeparator()
    menu = browser.form.menuJump
    browser.form.menuJump.setTitle("גיי צו")
    action = browser.form.actionFind
    menu.removeAction(action)
    action = browser.form.actionSidebarFilter
    menu.removeAction(action)
    action = browser.form.actionSidebar
    menu.removeAction(action)
    action = browser.form.actionNote
    menu.removeAction(action)
    action = browser.form.actionCardList
    menu.removeAction(action)
    #############
    menu = browser.form.menu_Notes
    action = browser.form.actionFindDuplicates
    menu.removeAction(action)
    action = browser.form.actionFindReplace
    menu.removeAction(action)
    action = browser.form.actionManage_Note_Types
    menu.removeAction(action)
    #############
    def getMenu(parent, menuName):
        menubar = parent.form.menubar
        for a in menubar.actions():
            if menuName == a.text():
                return a.parent()
        else:
            return menubar.addMenu(menuName)
    menu=getMenu(browser, "זוכן און איבערבייטן")

    menu.addSeparator()
    action = browser.form.actionFindDuplicates
    menu.addAction(action)
    action = browser.form.actionFindReplace
#    action.setTitle("חיפוש והחלפה")
    menu.addAction(action)
    menu = browser.form.menu_Help

    browser.form.menubar.addMenu(menu)
gui_hooks.browser_menus_did_init.append(setupMenu)

#הגדרת סרגל הצד בדפדוף בצד ימין
def setupSidebarRight(self,_old) -> None:
    dw = self.sidebarDockWidget = QDockWidget(tr.browsing_sidebar(), self)
    dw.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
    dw.setObjectName("Sidebar")
    dock_area = (
        Qt.DockWidgetArea.RightDockWidgetArea
        if self.layoutDirection() == Qt.LayoutDirection.RightToLeft
        else Qt.DockWidgetArea.LeftDockWidgetArea
    )
    dw.setAllowedAreas(dock_area)

    self.sidebar = SidebarTreeView(self)
    self.sidebarTree = self.sidebar  # legacy alias
    dw.setWidget(self.sidebar)
    qconnect(
        self.form.actionSidebarFilter.triggered,
        self.focusSidebarSearchBar,
    )
    grid = QGridLayout()
    grid.addWidget(self.sidebar.searchBar, 0, 0)
    grid.addWidget(self.sidebar.toolbar, 0, 1)
    grid.addWidget(self.sidebar, 1, 0, 1, 2)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setSpacing(0)
    w = QWidget()
    w.setLayout(grid)
    dw.setWidget(w)
    self.sidebarDockWidget.setFloating(False)

    self.sidebarDockWidget.setTitleBarWidget(QWidget())
    self.addDockWidget(dock_area, dw)

    # schedule sidebar to refresh after browser window has loaded, so the
    # UI is more responsive
    self.mw.progress.timer(10, self.sidebar.refresh, False)
    #for stage in SidebarStage:
    #    showInfo(str(SidebarStage))


# aqt.browser.browser.Browser.setupSidebar = wrap(aqt.browser.browser.Browser.setupSidebar, setupSidebarRight, "around")


from anki.scheduler.base import FilteredDeckForUpdate
from aqt.filtered_deck import FilteredDeckConfigDialog

# תרגום  Filtered Deck לחפיסה מסוננת

def load_deck_and_show(self, deck: FilteredDeckForUpdate) -> None:
    deck.name = deck.name.replace("Filtered Deck", "געפילטערטער פעקל")
    self.deck = deck
    self._load_deck()
    self.show()
FilteredDeckConfigDialog.load_deck_and_show = wrap(FilteredDeckConfigDialog.load_deck_and_show, load_deck_and_show)


def loadField1(self : aqt.fields.FieldDialog, idx: int, _old=None) -> None:
    f = self.form
    f.plainTextByDefault.setVisible(False)

aqt.fields.FieldDialog.loadField = wrap(aqt.fields.FieldDialog.loadField, loadField1, "after")
# aqt.forms.preferences.Ui_Preferences.ignore_accents_in_search
def hide_ignore_accents_in_search(self:aqt.preferences.Preferences):
    # self.form.ignore_accents_in_search.setVisible(False)
    self.form.render_latex.setVisible(False)
    self.form.url_schemes.setVisible(False)
    # self.form.ignore_accents_in_search.setVisible(False)

aqt.preferences.Preferences.setup_collection = wrap(aqt.preferences.Preferences.setup_collection, hide_ignore_accents_in_search)

#מחיקת כרטיסיה שירותי צד שלישי בהגדרות
def delete_Third_Party_Services_tab(self:aqt.preferences.Preferences):
    # מזהה האובייקט tab_31 השתנה בין גרסאות Anki. מסירים לפי כותרת הכרטיסייה
    # כדי ש"שירותי/שיעורי צד שלישי" לא יחזור לאחר עדכון Anki.
    for tabs in self.findChildren(QTabWidget):
        for index in range(tabs.count() - 1, -1, -1):
            title = (tabs.tabText(index) or "").replace("&", "").strip().lower()
            if ("דריטע זייט" in title or "third-party" in title or
                    "third party" in title):
                page = tabs.widget(index)
                tabs.removeTab(index)
                if page is not None:
                    page.deleteLater()

    # תאימות לטפסים ישנים שבהם הכותרת עדיין לא הוצבה בזמן setup_collection.
    legacy_tab = getattr(self.form, "tab_31", None)
    if legacy_tab is not None:
        legacy_tab.deleteLater()

aqt.preferences.Preferences.setup_collection = wrap(aqt.preferences.Preferences.setup_collection, delete_Third_Party_Services_tab)



# -----------------------------------------------------------
# פונקציה לשינוי צבע כפתור הסנכרון
# -----------------------------------------------------------


def update_sync_button_color(*args):
    """
    קוקט דעם סינכראניזיר מצב און דערהיינטיגט דעם אייקאן:
    - געווענליך (אן טוישן): דער אריגינעלער אייקאן
    - געווענליכע טוישן (Database/Media): בלוי
    - טוישן אינעם סטרוקטור (Schema): רויט (פולע סינכראניזירונג)
    """
    if not mw.col:
        return
    def update_color(status):
        color = {2: "#d94b48", 1: "#568dcc"}.get(status, "#947e69")
        sync_action.setProperty("haf_menu_color", color)
        menu_icon = getattr(mw, "_haf_menu_icon", None)
        if menu_icon is not None:
            sync_action.setIcon(menu_icon("sync", color))
            return
        icon_path_std = filename + "/sync.png"
        icon_path_blue = filename + "/sync_blue.png"
        icon_path_red = filename + "/sync_red.png"

        if status==2:
                # שינוי במבנה (Schema) דורש סנכרון מלא -> אדום
                sync_action.setIcon(QIcon(icon_path_red))
                # אופציונלי: שינוי טקסט להמחשה
                # sync_action.setToolTip(u"נדרש סנכרון מלא")

        elif status==1:
                # שינוי רגיל או במדיה -> כחול
                sync_action.setIcon(QIcon(icon_path_blue))
                # sync_action.setToolTip(u"נדרש סנכרון")

        else:
                # לא נדרש סנכרון -> רגיל
                sync_action.setIcon(QIcon(icon_path_std))
                # sync_action.setToolTip(u"סינכרון")

    from aqt.sync import get_sync_status
    get_sync_status(mw, lambda a:update_color(a.required))

# # Hook שרץ לאחר כל שינוי במצב (כגון מענה על כרטיס, הוספת רשומה וכו')
gui_hooks.state_did_reset.append(update_sync_button_color)

# # Hook שרץ מיד לאחר סיום סנכרון (כדי להחזיר את הצבע לרגיל)
gui_hooks.sync_did_finish.append(update_sync_button_color)

# Hook שרץ בהחלפת פרופיל
gui_hooks.profile_did_open.append(update_sync_button_color)

# הרצה ראשונית בעת טעינת התוסף
update_sync_button_color()



#להזיז את יום ראשון להתחלה באפשרויות חפיסה

from aqt import gui_hooks


def get_sunday_reorder_js():
    return """
(function() {




    // CSS-only approach — מען רירט נישט אן-DOM, מען לייגט נאר צו style וואס טוישט דעם זעבארן סדר.
    // Svelte קען אויסמאלן וויפיל ער וויל — דער-style בלייבט.
    // .easy-days-settings ער CSS Grid.
    // children 1-4 (CSS) = headers, last 2 = זונטאג + input.
    // order נידעריגער = ווערט פריער געוויזן אין-grid auto-placement.
    if (document.getElementById('sunday-reorder-css')) return;
    const style = document.createElement('style');
    style.id = 'sunday-reorder-css';
    style.textContent = `
        .easy-days-settings > :nth-child(-n+4) { order: -10 !important; }
        .easy-days-settings > :nth-last-child(-n+2) { order: -5 !important; }
    `;
    document.head.appendChild(style);
})();
    """


def get_deck_options_translation_js():
    # #159 — מחליף את הניסוח באפשרויות חפיסה לנוסח המדויק שבוקש, גם אחרי רינדור חוזר של Svelte.
    return r"""
(function() {
    const replacements = [
        ['שטימט אפ אלע פאראויס באשטימטע איינשטעלונגען', 'שטים אפ אלע גרופעס איינשטעלונגען'],
        ['שטים אפ אלע פאראויס באשטימטע איינשטעלונגען', 'שטים אפ אלע גרופעס איינשטעלונגען'],
        ['אלע גרופעס איינשטעלונגען', 'שטים אפ אלע גרופעס איינשטעלונגען']
    ];
    function replaceText(node) {
        if (!node || !node.nodeValue) return;
        const parent = node.parentElement;
        if (parent && parent.closest && parent.closest('#custom-auto-advance-wrapper, script, style')) return;
        let text = node.nodeValue;
        for (const [from, to] of replacements) {
            text = text.split(from).join(to);
        }
        if (text !== node.nodeValue) node.nodeValue = text;
    }
    function scan(root) {
        if (!root) return;
        if (root.nodeType === Node.TEXT_NODE) {
            replaceText(root);
            return;
        }
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let node;
        while ((node = walker.nextNode())) replaceText(node);
    }
    let observer = window.__hafDeckOptionsTranslationObserver || null;
    let scheduled = false;
    function observe() {
        if (observer) observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    }
    function runScan() {
        scheduled = false;
        if (observer) observer.disconnect();
        scan(document.body);
        observe();
    }
    function scheduleScan() {
        if (scheduled) return;
        scheduled = true;
        (window.requestAnimationFrame || window.setTimeout)(runScan, 16);
    }
    if (!observer) {
        observer = new MutationObserver(scheduleScan);
        window.__hafDeckOptionsTranslationObserver = observer;
    }
    runScan();
})();
    """

def on_options_load(options_dialog):
    # #159 — מזריק גם את תיקון התרגום יחד עם סידור ימי השבוע.
    with contextlib.suppress(Exception):
        options_dialog.web.eval(get_sunday_reorder_js())
    with contextlib.suppress(Exception):
        options_dialog.web.eval(get_deck_options_translation_js())

# רישום ל-Hook הנכון (כמו בקוד הדוגמה שלך)
gui_hooks.deck_options_did_load.append(on_options_load)


#####################################
####כיווץ סרגל צד בפתיחה ראשונה####
#####################################

def _collapse_sidebar_first_time(browser) -> None:
    """מאכט צו אלע זייט סרגל קאטאגאריעס נאר איינמאל פאר א נייעם באניצער."""
    _KEY = "sidebar_collapsed_once"
    if mw.pm.profile.get(_KEY):
        return
    mw.pm.profile[_KEY] = True

    def do_collapse() -> None:
        try:
            browser.sidebar.collapseAll()
        except Exception:
            pass

    mw.progress.timer(300, do_collapse, False)


gui_hooks.browser_will_show.append(_collapse_sidebar_first_time)



def get_card_info_hebrew_axis_js():
    # #156 — מתרגם את ציר הזמן של גרף מידע כרטיס לפי התאריך העברי האמיתי ומסמן ראש שנה.
    return r"""
(function() {
    const detectFormatter = new Intl.DateTimeFormat('en-u-ca-hebrew', {
        day: 'numeric', month: 'long', year: 'numeric'
    });
    const hebrewFormatter = new Intl.DateTimeFormat('he-IL-u-ca-hebrew', {
        day: 'numeric', month: 'long', year: 'numeric'
    });

    function part(parts, name) {
        const item = parts.find((entry) => entry.type === name);
        return item ? item.value : '';
    }

    function hebrewParts(date) {
        const detectParts = detectFormatter.formatToParts(date);
        const labelParts = hebrewFormatter.formatToParts(date);
        return {
            detectDay: Number(part(detectParts, 'day')),
            detectMonth: part(detectParts, 'month'),
            day: part(labelParts, 'day'),
            month: part(labelParts, 'month'),
            year: part(labelParts, 'year') || part(labelParts, 'yearName'),
        };
    }

    function hebrewYearLabel(rawYear) {
        const raw = String(rawYear || '').trim();
        const existingHebrew = raw.match(/[\u0590-\u05ff]+/g);
        if (existingHebrew) return existingHebrew.join('').replace(/[׳״']/g, '');
        const year = Number((raw.match(/\d+/g) || []).join(''));
        if (!Number.isFinite(year) || year <= 0) return raw;
        let shortYear = year > 5000 ? year - 5000 : year;
        const values = [
            [400, 'ת'], [300, 'ש'], [200, 'ר'], [100, 'ק'],
            [90, 'צ'], [80, 'פ'], [70, 'ע'], [60, 'ס'], [50, 'נ'],
            [40, 'מ'], [30, 'ל'], [20, 'כ'], [10, 'י'],
            [9, 'ט'], [8, 'ח'], [7, 'ז'], [6, 'ו'], [5, 'ה'],
            [4, 'ד'], [3, 'ג'], [2, 'ב'], [1, 'א'],
        ];
        let label = '';
        for (const [value, letter] of values) {
            while (shortYear >= value) {
                label += letter;
                shortYear -= value;
            }
        }
        return label || raw;
    }

    function formatHebrewDate(date, includeYear) {
        const parts = hebrewParts(date);
        // #156 — אויפן גראף אקס ווייזט מען נאר דעם חודש נאמען; דער טאג נומער האט געשאפן עטיקעטעס ווי "28 שבט" וואס האבן אויסגעזען ווי פארדרייטע נומערן.
        if (includeYear && parts.detectMonth.toLowerCase().startsWith('tish')) {
            return `${parts.month} ${hebrewYearLabel(parts.year)}`.trim();
        }
        return parts.month.trim();
    }

    function tickDate(tick) {
        const raw = tick.__data__ || (tick.parentNode && tick.parentNode.__data__);
        if (raw instanceof Date) return raw;
        if (typeof raw === 'number') return new Date(raw > 1000000000000 ? raw : raw * 1000);
        if (raw && raw.date) return new Date(raw.date);
        return null;
    }

    function isPlausibleAxisDate(date) {
        const year = date && date.getFullYear && date.getFullYear();
        const maxYear = new Date().getFullYear() + 80;
        return Number.isFinite(year) && year >= 2000 && year <= maxYear;
    }

    function tickX(tick) {
        const transform = tick.getAttribute('transform') || '';
        const match = transform.match(/translate\(([-0-9.]+)/);
        return match ? Number(match[1]) : null;
    }

    function xTicks(svg) {
        return Array.from(svg.querySelectorAll('.x-ticks .tick')).map((tick) => ({
            tick,
            date: tickDate(tick),
            x: tickX(tick),
        })).filter((item) => item.date && isPlausibleAxisDate(item.date) && Number.isFinite(item.x));
    }

    function interpolateX(ticks, target) {
        for (let idx = 0; idx < ticks.length - 1; idx++) {
            const left = ticks[idx];
            const right = ticks[idx + 1];
            if (target >= left.date && target <= right.date) {
                const ratio = (target - left.date) / (right.date - left.date || 1);
                return left.x + ratio * (right.x - left.x);
            }
        }
        return null;
    }

    function roshHashanaDates(start, end) {
        // #156 — באגרעניצט די זוכעניש נאר צום ערשטן טאג תשרי; לייגט צו א דאפלט בדיקה לויטן נארמאליזירטן דאטום.
        const seen = new Set();
        const dates = [];
        for (let year = start.getFullYear() - 1; year <= end.getFullYear() + 1; year++) {
            for (let day = new Date(year, 7, 15); day <= new Date(year, 9, 31); day.setDate(day.getDate() + 1)) {
                const parts = hebrewParts(day);
                if (parts.detectDay === 1 && parts.detectMonth.toLowerCase().startsWith('tish')) {
                    const key = `${day.getFullYear()}-${day.getMonth()}-${day.getDate()}`;
                    if (!seen.has(key)) {
                        seen.add(key);
                        dates.push(new Date(day));
                    }
                    break;
                }
            }
        }
        return dates.filter((date) => date >= start && date <= end);
    }

    function markerHeight(svg, axisGroup) {
        const transform = axisGroup.getAttribute('transform') || '';
        const match = transform.match(/translate\([^,]+,\s*([-0-9.]+)/);
        if (match) return Math.max(40, Number(match[1]) - 12);
        const viewBox = (svg.getAttribute('viewBox') || '').split(/\s+/).map(Number);
        return Number.isFinite(viewBox[3]) ? Math.max(40, viewBox[3] - 24) : 120;
    }

    function applyHebrewAxis() {
        for (const svg of document.querySelectorAll('svg')) {
            const ticks = xTicks(svg);
            if (ticks.length < 2) continue;

            const start = ticks[0].date;
            const end = ticks[ticks.length - 1].date;
            const spanDays = (end - start) / 86400000;
            const includeYear = spanDays > 370;
            for (const item of ticks) {
                const text = item.tick.querySelector('text');
                const label = formatHebrewDate(item.date, includeYear);
                if (text && text.textContent !== label) text.textContent = label;
            }

            const axisGroup = svg.querySelector('.x-ticks');
            if (!axisGroup) continue;
            const yearStartDates = roshHashanaDates(start, end);
            const signature = [
                start.getTime(),
                end.getTime(),
                ...ticks.map((item) => `${Math.round(item.x)}:${item.date.getTime()}`),
                ...yearStartDates.map((date) => date.getTime()),
            ].join('|');
            if (axisGroup.getAttribute('data-haf-hebrew-axis') === signature) continue;
            axisGroup.setAttribute('data-haf-hebrew-axis', signature);
            axisGroup.querySelectorAll('.haf-hebrew-year-marker').forEach((node) => node.remove());
            const height = markerHeight(svg, axisGroup);
            const night = document.documentElement.classList.contains('night-mode');
            const color = night ? '#e0b957' : '#9a6700';

            for (const date of yearStartDates) {
                const x = interpolateX(ticks, date);
                if (x === null) continue;
                const marker = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                marker.setAttribute('class', 'haf-hebrew-year-marker');
                marker.setAttribute('transform', `translate(${x},0)`);

                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('y1', '0');
                line.setAttribute('y2', String(-height));
                line.setAttribute('stroke', color);
                line.setAttribute('stroke-width', '1.3');
                line.setAttribute('stroke-dasharray', '3 3');
                marker.appendChild(line);

                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.textContent = 'ראש השנה';
                label.setAttribute('y', String(-height + 12));
                label.setAttribute('text-anchor', 'middle');
                label.setAttribute('font-size', '10');
                label.setAttribute('fill', color);
                marker.appendChild(label);
                axisGroup.appendChild(marker);
            }
        }
    }

    function schedule() {
        requestAnimationFrame(applyHebrewAxis);
    }

    if (!window.__hafHebrewCardInfoAxisObserver && document.body) {
        window.__hafHebrewCardInfoAxisObserver = new MutationObserver(schedule);
        window.__hafHebrewCardInfoAxisObserver.observe(document.body, { childList: true, subtree: true });
    }
    schedule();
    setTimeout(schedule, 300);
    setTimeout(schedule, 1000);
})();
    """


def _eval_card_info_hebrew_axis(webview) -> None:
    # #156 — eval נדחה מעט כדי לתת ל-Svelte ול-D3 לסיים לצייר את הגרף.
    with contextlib.suppress(Exception):
        webview.eval(get_card_info_hebrew_axis_js())


def _inject_card_info_hebrew_axis(webview) -> None:
    # #156 — ההזרקה מוגבלת ל-WebView של מידע כרטיס בלבד.
    if getattr(webview, "kind", None) != AnkiWebViewKind.BROWSER_CARD_INFO:
        return
    QTimer.singleShot(700, lambda: _eval_card_info_hebrew_axis(webview))


gui_hooks.webview_did_inject_style_into_page.append(_inject_card_info_hebrew_axis)


def reorganize_col_menu():
    """לויפט נאכן אנהייבן דעם הויפט פענסטער — שטעלט אויס דעם menuCol אינעם געוואונטשענעם סדר."""
    col = mw.form.menuCol

    def find_by_text(text):
        for a in col.actions():
            if a.text() == text:
                return a
        return None

    # שמירת רפרנסים לפריטים שנוספו ע"י תוספים אחרים
    external_import_action = find_by_text("אימפארטירן באזונדערע פראגעס פון א טעקע")
    xml_import_action      = find_by_text('אימפארטירן שו"ת פון א טעקע XML (קלזכור)')
    shortcut_mgr_action    = find_by_text("איינשטעלן קיצור קנעפלעך")
    print_action           = find_by_text("דרוקן און עקספארטירן צו ווארד")
    question_bank_action   = find_by_text("פראגע זאמלונג")

    # #149 — שומרים פעולות לא מוכרות כדי שסידור התפריט לא יעלים כפתורים מתוספים אחרים.
    known_actions = [
        mw.form.actionSwitchProfile,
        mw.form.action_create_backup,
        mw.form.action_open_backup,
        sync_action,
        mw.form.actionImport,
        mw.form.actionExport,
        external_import_action,
        xml_import_action,
        shortcut_mgr_action,
        mw.form.actionUndo,
        mw.form.actionRedo,
        mw.form.actionAdd_ons,
        mw.form.actionPreferences,
        mw.addon_col_menu.menuAction(),
        mw.addon_view_menu.menuAction(),
        print_action,
        question_bank_action,
        mw.form.actionExit,
        mw.form.action_create_backup,
    ]
    preserved_actions = []
    for existing_action in col.actions():
        if existing_action.isSeparator() or existing_action in known_actions:
            continue
        if existing_action not in preserved_actions:
            preserved_actions.append(existing_action)

    # ניקוי כל הפריטים הנוכחיים מ-menuCol
    for a in col.actions()[:]:
        col.removeAction(a)

    # בנייה מחדש בסדר הרצוי
    col.addAction(mw.form.actionSwitchProfile)
    col.addAction(mw.form.action_create_backup)
    col.addAction(mw.form.action_open_backup)
    col.addAction(sync_action)
    col.addAction(mw.form.actionImport)
    col.addAction(mw.form.actionExport)
    if external_import_action:
        col.addAction(external_import_action)
    if xml_import_action:
        col.addAction(xml_import_action)
    col.addSeparator()
    if shortcut_mgr_action:
        col.addAction(shortcut_mgr_action)
    col.addAction(mw.form.actionUndo)
    # #157 — Redo נשמר כפקודה רגילה בתוך menuCol אחרי Undo.
    col.addAction(mw.form.actionRedo)
    col.addAction(mw.form.actionAdd_ons)
    col.addAction(mw.form.actionPreferences)
    col.addMenu(mw.addon_col_menu)
    col.addMenu(mw.addon_view_menu)
    col.addSeparator()
    if print_action:
        col.addAction(print_action)
    if question_bank_action:
        col.addAction(question_bank_action)
    for preserved_action in preserved_actions:
        col.addAction(preserved_action)


gui_hooks.main_window_did_init.append(reorganize_col_menu)





def _hebrew_studied_in_minute_message(*, cards: int, minutes: str) -> str:
    # #257 — החלפה ממוקדת של tr.studying_card_studied_in_minute למחרוזת עברית תקינה.
    card_text = "איין קארטל" if cards == 1 else f"{cards} קארטלעך"
    verb = "געלערנט" if cards == 1 else "געלערנט"
    minute_unit = "מינוט" if str(minutes).strip() == "1" else "מינוטן"
    return f"{card_text} {verb} אינעווייניג\n{minutes} {minute_unit}."


tr.studying_card_studied_in_minute = _hebrew_studied_in_minute_message

tr.actions_new = lambda: "ניי"
