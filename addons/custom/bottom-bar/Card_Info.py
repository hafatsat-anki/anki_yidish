import html

from aqt import QSize, gui_hooks, mw
from aqt.qt import *
from aqt.webview import AnkiWebView, AnkiWebViewKind

# ======================================================================
#  1. Hebrew Date Conversion Script (Fixed Alignment & Tiny Units)
# ======================================================================
HEBREW_DATE_CONVERSION_SCRIPT = """
    // --- 1. CSS Injection for Sidebar Layout ---
    function injectCustomStyles() {
        if (document.getElementById('anki-sidebar-custom-css')) return;

        const css = `
            /* אלגעמיינער צוריקשטעל */
            body {
                overflow-x: hidden;
                margin: 0 !important;
                padding: 0 !important;
            }
            .container {
                padding: 0 4px !important;
                margin: 0 !important;
                max-width: 100% !important;
                width: 100% !important;
            }

            /* --- אויבערשטע טאבעלע --- */
            .stats-table th, .stats-table td {
                padding: 1px 4px !important;
                font-size: 11px !important;
                line-height: 1.1 !important;
            }

            /* --- געשיכטע טאבעלע (Revlog) --- */
            .revlog-table {
                font-size: 11px !important;
                width: 100% !important;
                display: flex !important;
                flex-direction: row !important;
                overflow-x: auto !important;
                padding-bottom: 10px;
            }

            .revlog-table .column {
                padding: 0 !important;
                min-width: unset !important;
                flex: 1 1 auto !important;
                text-align: center !important;
            }

            .revlog-table .column-head {
                height: 20px !important;
                font-size: 10px !important;
                font-weight: bold;
                white-space: nowrap;
                overflow: hidden;
                margin-bottom: 2px !important;
            }

            /* === דער וויכטיגער פאררעכטונג פון דער שורות אויסריכטונג === */
            /* שטעלט א גלייכע הייך פאר אלע צעלן, כדי די שורות זאלן זיין אויסגעריכט צווישן די שפאלטן */
            .revlog-table .column-content > div {
                height: 32px !important;       /* א פעסטע הייך פאר אלע */
                max-height: 32px !important;
                padding: 0 !important;         /* נעמט אוועק איבעריגע אינערליכע רווחים */
                margin: 0 !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important; /* אויסריכטן אין מיטן פון דער הייך */
                align-items: center !important;     /* אויסריכטן אין מיטן פון דער ברייט */
                border-bottom: 1px solid #f0f0f0;   /* א דינער אפטייל קו */
            }

            /* --- אויסשטעל פונעם דאטום צעל --- */
            .revlog-table .column-content b {
                font-size: 10px !important;
                display: block !important;
                line-height: 1.1 !important;
                font-weight: normal !important;
            }
            /* די שעה (דער שטרודל) */
            .revlog-table .column-content span.time-split {
                display: block !important;
                font-size: 9px !important;
                color: #888 !important;
                line-height: 1 !important;
                margin-top: 0px !important;
            }

            /* --- פארקלענערן צייט איינסן (טעג/מינוטן) --- */
            .tiny-unit {
                font-size: 8px !important;
                opacity: 0.7;
                margin-right: 1px;
                vertical-align: middle;
            }

            /* באזונדערע באהאנדלונג פונעם ציון שפאלט (קנעפלעך) */
            .revlog-table .column-content div {
                /* מאכט זיכער אז אינערליכע רווחים רוקן נישט דעם אינהאלט */
            }
        `;

        const style = document.createElement('style');
        style.id = 'anki-sidebar-custom-css';
        style.textContent = css;
        document.head.appendChild(style);
    }

    // --- 2. Hebrew Helper Functions ---
    var _GEMATRIOS = {
      1: 'א', 2: 'ב', 3: 'ג', 4: 'ד', 5: 'ה', 6: 'ו', 7: 'ז', 8: 'ח', 9: 'ט',
      10: 'י', 20: 'כ', 30: 'ל', 40: 'מ', 50: 'נ', 60: 'ס', 70: 'ע', 80: 'פ', 90: 'צ',
      100: 'ק', 200: 'ר', 300: 'ש', 400: 'ת'
    };
    function Division_without_a_remainder(num, Divide) { return Math.floor(num / Divide); }
    function _stringify_gematria(letters) {
      let len = letters.length;
      if (len > 1) { return `${letters.slice(0, -1)}"${letters.slice(-1)}`; }
      else if (len === 1) { return letters + "'"; }
      else { return ""; }
    }
    function _get_letters(num) {
      let ones = num % 10, tens = num % 100 - ones, hundreds = num % 1000 - tens - ones;
      let four_hundreds = 'ת'.repeat(Division_without_a_remainder(hundreds, 400));
      hundreds = hundreds % 400;
      let letters = four_hundreds + (hundreds ? _GEMATRIOS[hundreds] : '') + (tens ? _GEMATRIOS[tens] : '') + (ones ? _GEMATRIOS[ones] : '');
      return letters.replace(/יה/g, 'טו').replace(/יו/g, 'טז');
    }
    function _num_to_str(num, thousands = false) {
      let letters = _stringify_gematria(_get_letters(num % 1000));
      if (thousands && num >= 1000) {
        let thousand = _get_letters(Division_without_a_remainder(num, 1000)) + "'";
        letters = thousand + letters;
      }
      return letters;
    }
    function getFullHebrewDate(date) {
        const num_heb_dete = new Intl.DateTimeFormat('he-u-ca-hebrew', { timeZone: 'UTC', year: 'numeric', month: 'numeric', day: 'numeric' }).format(date);
        const n_h_d = num_heb_dete.split(/[ .\\/]+/);
        if (n_h_d.length < 3) return num_heb_dete;
        n_h_d[0] = _num_to_str(parseInt(n_h_d[0]));
        const yearPart = n_h_d[n_h_d.length - 1].replace("ה׳", "").trim();
        n_h_d[n_h_d.length - 1] = _num_to_str(parseInt(yearPart), false);
        return n_h_d.join(' ');
    }

    // --- Replacement Logics ---
    function Convert_date_to_heb(gregorianDateStr) {
        try { const date = new Date(gregorianDateStr + "T00:00:00Z"); return getFullHebrewDate(date); }
        catch (e) { return gregorianDateStr; }
    }
    function Convert_graph_date_to_heb(match, monthStr, dayStr, inferredYear) {
        try {
            const date = new Date(`${monthStr} ${dayStr}, ${inferredYear}`);
            const hebrewFormatter = new Intl.DateTimeFormat('he-u-ca-hebrew', { year: 'numeric', month: 'short', day: 'numeric' });
            const parts = hebrewFormatter.formatToParts(date);
            const dayPart = parts.find(p => p.type === 'day');
            const monthPart = parts.find(p => p.type === 'month');
            const yearPart = parts.find(p => p.type === 'year');
            if (!dayPart || !monthPart || !yearPart) return match;
            const dayInGematria = _num_to_str(parseInt(dayPart.value));
            const currentHebrewYear = parseInt(yearPart.value);
            let finalLabel = `${dayInGematria} ${monthPart.value}`;
            if (!window.lastProcessedHebrewYear || currentHebrewYear > window.lastProcessedHebrewYear) {
                const yearInGematria = _num_to_str(currentHebrewYear, true);
                finalLabel = `${monthPart.value} ${yearInGematria}`;
            }
            window.lastProcessedHebrewYear = currentHebrewYear;
            return finalLabel;
        } catch (e) { return match; }
    }
    function Convert_tooltip_date_to_heb(match, day, month, year) {
        try { const date = new Date(Date.UTC(year, month - 1, day)); return getFullHebrewDate(date); }
        catch (e) { return match; }
    }
    function Convert_month_to_heb(monthName, inferredYear) {
        try { const date = new Date(`${monthName} 1, ${inferredYear}`); return new Intl.DateTimeFormat('he-u-ca-hebrew', { month: 'long' }).format(date); }
        catch (e) { return monthName; }
    }
    function Convert_year_to_heb(year) {
        try {
            const date = new Date(year, 0, 1);
            return new Intl.DateTimeFormat('he-u-ca-hebrew', { month: 'long' }).format(date);
        } catch (e) { return year; }
    }
    function Convert_day_of_week_to_heb(match, dayOfWeek, dayOfMonth) {
        try { return _num_to_str(parseInt(dayOfMonth)); }
        catch (e) { return match; }
    }

    // --- 3. DOM Traversal ---
    function convertDatesOnNode(node, inferredYear) {
        if (node.nodeType === Node.TEXT_NODE) {
            let content = node.textContent;
            if (!content || content.trim() === '') return;
            let changed = false;

            // 1. Handle "Date Time:" (Prepare for split)
            if (content.includes("@")) {
                // If it looks like a time separator in the log
                const parent = node.parentElement;
                if(parent && parent.classList.contains('hidden-xs')) {
                     parent.classList.add('time-split');
                     changed = true;
                }
            }

            const tableRegex = /(\\d{4}-\\d{2}-\\d{2})/g;
            if (tableRegex.test(content)) { content = content.replace(tableRegex, (match) => Convert_date_to_heb(match)); changed = true; }

            const tooltipRegex = /(\\d{1,2})\\.(\\d{1,2})\\.(\\d{4})/g;
            if (tooltipRegex.test(content)) { content = content.replace(tooltipRegex, (match, day, month, year) => Convert_tooltip_date_to_heb(match, day, month, year)); changed = true; }

            const graphRegex = /\\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s(\\d{1,2})\\b/g;
            if (graphRegex.test(content)) { content = content.replace(graphRegex, (match, month, day) => Convert_graph_date_to_heb(match, month, day, inferredYear)); changed = true; }

            const fullMonthRegex = /\\b(January|February|March|April|May|June|July|August|September|October|November|December)\\b/g;
            if (fullMonthRegex.test(content)) { content = content.replace(fullMonthRegex, (match) => Convert_month_to_heb(match, inferredYear)); changed = true; }

            const dayOfWeekRegex = /\\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\\s(\\d{1,2})\\b/g;
            if (dayOfWeekRegex.test(content)) { content = content.replace(dayOfWeekRegex, (match, dayOfWeek, dayOfMonth) => Convert_day_of_week_to_heb(match, dayOfWeek, dayOfMonth)); changed = true; }

            const yearRegex = /^(\\d{4})$/g;
            if (yearRegex.test(content.trim())) {
                const parentElement = node.parentElement;
                if (parentElement && parentElement.previousElementSibling && parentElement.previousElementSibling.textContent.trim() === 'פלאץ') {
                } else {
                    content = content.replace(yearRegex, (match) => Convert_year_to_heb(match));
                    changed = true;
                }
            }

            if (changed) { node.textContent = content; }

        } else if (node.nodeType === Node.ELEMENT_NODE) {
            for (const child of node.childNodes) {
                convertDatesOnNode(child, inferredYear);
            }
        }
    }

    // --- 4. Extra Formatting (Tiny Units & Time Split) ---
    function formatTimeCells() {
        // Find all cells in the revlog table
        const cells = document.querySelectorAll('.revlog-table .column-content > div');

        cells.forEach(cell => {
            // A. Shrink time units (מינוטן, טעג etc)
            if (cell.innerHTML.match(/(סעקונדעס|מינוטן|טעג|חדשים|יארן)/)) {
                if (!cell.querySelector('.tiny-unit')) {
                    cell.innerHTML = cell.innerHTML.replace(
                        /(סעקונדעס|מינוטן|טעג|חדשים|יארן)/g,
                        '<span class="tiny-unit">$1</span>'
                    );
                }
            }

            // B. Ensure time split (The @ part)
            // Sometimes the @ is in a span with class 'hidden-xs'. We want to force it to break line.
            const timeSpan = cell.querySelector('span.hidden-xs');
            if (timeSpan && !timeSpan.classList.contains('time-split')) {
                timeSpan.classList.add('time-split');
                // Remove the @ if desired, or keep it. Let's clean it up slightly
                timeSpan.textContent = timeSpan.textContent.replace('@', '').trim();
            }
        });
    }

    // --- 5. Main Execution ---
    function runConversion() {
        injectCustomStyles();

        let inferredYear = new Date().getFullYear();
        const yearMatch = document.body.innerText.match(/\\b(\\d{4})-\\d{2}-\\d{2}\\b/);
        if (yearMatch) { inferredYear = parseInt(yearMatch[1]); }

        window.lastProcessedHebrewYear = 0;

        // Run recursive text node conversion
        convertDatesOnNode(document.body, inferredYear);
        // Run cell formatting (HTML injection)
        formatTimeCells();

        if (window.cardInfoDateObserver) { window.cardInfoDateObserver.disconnect(); }

        const observer = new MutationObserver((mutationsList) => {
            window.lastProcessedHebrewYear = 0;
            injectCustomStyles(); // Ensure CSS stays

            let shouldFormatCells = false;

            for (const mutation of mutationsList) {
                if (mutation.type === 'childList') {
                    for (const node of mutation.addedNodes) {
                        convertDatesOnNode(node, inferredYear);
                    }
                    shouldFormatCells = true;
                }
                if (mutation.type === 'characterData') {
                    convertDatesOnNode(mutation.target, inferredYear);
                    shouldFormatCells = true;
                }
            }

            if (shouldFormatCells) {
                formatTimeCells();
            }
        });

        observer.observe(document.body, { childList: true, subtree: true, characterData: true });
        window.cardInfoDateObserver = observer;
    }

    setTimeout(runConversion, 250);
"""

# ======================================================================
#  2. The Modernized Sidebar Class
# ======================================================================
class StatsSidebar:
    def __init__(self, mw):
        config = mw.addonManager.getConfig(__name__)
        sidebar_autoOpen = True
        if config:
            sidebar_autoOpen = config.get('Card Info sidebar_ Auto Open', True)

        self.mw = mw
        self.shown = None
        self.web = None
        self._page_loaded = False
        self._update_timer = QTimer(self.mw)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._load_pending_card)
        self._pending_card_id = None
        self._load_retry_count = 0
        self._load_in_progress = False

        gui_hooks.reviewer_did_show_question.append(self._update)
        gui_hooks.reviewer_will_end.append(self._cleanup)
        if sidebar_autoOpen:
            gui_hooks.reviewer_did_show_question.append(self.show)

    def _tags_script_for_card(self, card_id):
        config = mw.addonManager.getConfig(__name__) or {}
        if not config.get('Card Info sidebar_ Tags', True):
            return ""
        try:
            card = self.mw.col.get_card(card_id)
            tags = list(card.note().tags)
        except Exception:
            tags = []
        tags_text = ", ".join(html.escape(tag) for tag in tags) or '<span class="haf-card-info-tags-empty">קיין צעטלעך</span>'
        return f"""
        (function() {{
            const existing = document.getElementById('haf-card-info-tags');
            if (existing) existing.remove();
            const root = document.querySelector('.container') || document.body;
            if (!root) return;
            const styleId = 'haf-card-info-tags-style';
            if (!document.getElementById(styleId)) {{
                const style = document.createElement('style');
                style.id = styleId;
                style.textContent = `
                    #haf-card-info-tags {{
                        direction: rtl;
                        font-size: 11px;
                        line-height: 1.4;
                    }}
                    #haf-card-info-tags td {{
                        overflow-wrap: anywhere;
                    }}
                    #haf-card-info-tags .haf-card-info-tags-empty {{
                        color: #777;
                    }}
                `;
                document.head.appendChild(style);
            }}
            function findDetailsTableBody() {{
                const tables = Array.from(document.querySelectorAll('table'));
                for (const table of tables) {{
                    const body = table.tBodies && table.tBodies[0];
                    if (body && body.rows && body.rows.length) return body;
                }}
                return null;
            }}
            function placeTagsRow() {{
                const detailsTable = findDetailsTableBody();
                if (!detailsTable) return false;
                const row = document.createElement('tr');
                row.id = 'haf-card-info-tags';
                row.innerHTML = '<th>צעטלעך</th><td>{tags_text}</td>';
                detailsTable.appendChild(row);
                return true;
            }}
            if (placeTagsRow()) return;
            let attempts = 0;
            const timer = setInterval(() => {{
                attempts += 1;
                if (placeTagsRow() || attempts >= 8) clearInterval(timer);
            }}, 150);
        }})();
        """

    def _addDockable(self, title, w):
        class DockableWithClose(QDockWidget):
            closed = pyqtSignal()

            def closeEvent(self, evt):
                self.closed.emit()
                QDockWidget.closeEvent(self, evt)

        dock = DockableWithClose(title, self.mw)
        dock.setMinimumWidth(300)
        dock.setObjectName(title)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        dock.setWidget(w)

        if self.mw.width() < 600:
            self.mw.resize(QSize(600, self.mw.height()))

        self.mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        return dock

    def _remDockable(self, dock):
        self.mw.removeDockWidget(dock)

    def show(self, card=None):
        if self.shown:
            return

        self.web = AnkiWebView(kind=AnkiWebViewKind.BROWSER_CARD_INFO)
        self.shown = self._addDockable("קארטל אינפארמאציע", self.web)
        self.shown.closed.connect(self._onClosed)
        self._page_loaded = False
        self._current_card_id = None
        self._loading_card_id = None
        self._pending_card_id = None
        self._load_retry_count = 0
        self._load_in_progress = False
        # #69 — דוחים את הטעינה הראשונה כדי שה-AnkiWebView יסיים אתחול ולא תופיע חלונית ריקה בלחיצה הראשונה.
        QTimer.singleShot(350, self._update)

    def hide(self):
        if not self.shown:
            return
        self._remDockable(self.shown)
        if self.web:
            self.web.cleanup()
            self.web = None
        self.shown = None
        self._page_loaded = False
        self._current_card_id = None
        self._loading_card_id = None
        self._pending_card_id = None
        self._load_retry_count = 0
        self._load_in_progress = False
        self._update_timer.stop()
        self._load_hook_connected = False

    def toggle(self):
        if self.shown:
            self.hide()
        else:
            self.show()

    def _onClosed(self):
        # #69 — סגירה דרך QTimer רגיל מונעת timer של progress שנשאר תלוי אחרי סגירת חלונית.
        QTimer.singleShot(100, self.hide)

    def _cleanup(self):
        if self.shown:
            self.web.setHtml("")

    def _update(self, card=None):
        if not self.shown or not self.web:
            return

        card = self.mw.reviewer.card
        if not card:
            return

        self._pending_card_id = card.id
        # #69 — מאחדים קריאות רצופות בזמן מעבר כרטיסים, כדי לא להעמיס טעינות SvelteKit חופפות ולמנוע חלונית תקועה/ריקה.
        self._update_timer.start(50)

    def _load_pending_card(self):
        if not self.shown or not self.web or self._pending_card_id is None:
            return

        card_id = self._pending_card_id
        # סבב 9 — load_sveltekit_page uses fetch internally. Starting another
        # navigation while the first one is active aborts that fetch and makes
        # SvelteKit show "TypeError: Failed to fetch". Keep only the newest
        # pending id and start it after loadFinished.
        if self._load_in_progress:
            return
        if self._loading_card_id != card_id:
            self._load_retry_count = 0

        # מצב נוכחי - אם כבר מציגים את אותו כרטיס, לא לטעון שוב
        if getattr(self, "_current_card_id", None) == card_id and self._page_loaded:
            return

        self._current_card_id = card_id

        # התחבר ל-loadFinished פעם אחת בלבד
        if not getattr(self, "_load_hook_connected", False):
            def on_load(ok=True):
                loaded_id = self._loading_card_id
                if not ok:
                    self._load_in_progress = False
                    QTimer.singleShot(300, self._retry_current_card)
                    return
                if self.web and loaded_id == self._pending_card_id:
                    self.web.eval(HEBREW_DATE_CONVERSION_SCRIPT)
                    # #262 — מידע כרטיס החדש של Anki לא מציג תגיות, לכן מוסיפים אותן בראש הסיידבר.
                    self.web.eval(self._tags_script_for_card(loaded_id))
                    expected_id = loaded_id

                    # #69 / דיווח חדש — loadFinished מסמן רק שמסמך ה-WebView נטען;
                    # SvelteKit ממשיך אחריו fetch פנימי. משאירים את נעילת הניווט
                    # פעילה עד תום חלון ההתייצבות, אחרת מעבר לכרטיס הבא מבטל את
                    # ה-fetch ומציג TypeError: Failed to fetch.
                    def settle_loaded_page():
                        if (
                            self.shown
                            and self.web
                            and expected_id == self._loading_card_id
                            and expected_id == self._pending_card_id
                        ):
                            self._current_card_id = expected_id
                            self._page_loaded = True
                            self._load_retry_count = 0
                        self._load_in_progress = False
                        if (
                            self.shown
                            and self.web
                            and self._pending_card_id is not None
                            and self._pending_card_id != expected_id
                        ):
                            QTimer.singleShot(0, self._load_pending_card)

                    QTimer.singleShot(350, settle_loaded_page)
                elif self.web and self._pending_card_id is not None:
                    # The completed page became stale while it was loading.
                    # Give its SvelteKit fetch the same quiet window before
                    # navigating to the newest pending card.
                    expected_id = loaded_id

                    def settle_stale_page():
                        if expected_id == self._loading_card_id:
                            self._load_in_progress = False
                        if self.shown and self.web and self._pending_card_id is not None:
                            QTimer.singleShot(0, self._load_pending_card)

                    QTimer.singleShot(350, settle_stale_page)

            qconnect(self.web.loadFinished, on_load)
            self._load_hook_connected = True

        self._page_loaded = False
        self._loading_card_id = card_id
        self._load_in_progress = True
        self.web.load_sveltekit_page(f"card-info/{card_id}")
        # #69 — טעינה ראשונה של SvelteKit עלולה להסתיים בלי תוכן; בדיקת fallback אחת מונעת חלונית ריקה.
        QTimer.singleShot(900, self._retry_current_card)

    def _retry_current_card(self):
        if not self.shown or not self.web or self._pending_card_id is None:
            return
        if self._page_loaded and self._current_card_id == self._pending_card_id:
            return
        if self._load_in_progress:
            return
        if self._load_retry_count >= 2:
            return
        self._load_retry_count += 1
        self._page_loaded = False
        self._load_pending_card()


# ======================================================================
#  3. Instantiation and Menu Item Setup
# ======================================================================
_cs = StatsSidebar(mw)

def cardStats(on):
    _cs.toggle()

action = QAction(mw)
action.setText("ווייז אדער באהאלט קארטל אינפארמאציע ביים חזרן")
qconnect(action.triggered, cardStats)
mw.form.menuTools.addAction(action)

def close_card_info_on_deck_browser(state, old_state):
    if state == "deckBrowser" and _cs.shown:
        _cs.hide()

gui_hooks.state_will_change.append(close_card_info_on_deck_browser)


def close_card_info_before_profile_close() -> None:
    # דיווח מעבר פרופיל — destroy the add-on WebView while the old profile is
    # still valid, so none of its timers can reach a closed collection.
    if _cs.shown:
        _cs.hide()


gui_hooks.profile_will_close.append(close_card_info_before_profile_close)
