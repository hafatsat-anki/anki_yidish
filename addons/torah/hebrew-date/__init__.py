from __future__ import annotations

from collections.abc import Sequence

import aqt.preferences
import aqt.reviewer
from anki.cards import CardId
from anki.hooks import wrap
from anki.lang import FormatTimeSpan
from aqt import gui_hooks, mw
from aqt.browser.card_info import CardInfoDialog
from aqt.browser.table import Cell
from aqt.qt import *
from aqt.utils import tr

from _shared_libs.convertdate import convert_table_to_heb, is_date
from _shared_libs.gimatria_sort import gimatria_sort_key
from _shared_libs.pyluach.dates import GregorianDate

# Make sure this code runs when Anki starts, for example, in __init__.py of your addon


# print(dates.HebrewDate.today().hebrew_date_string())
# anki.stats.CardStats.date = wrap(anki.stats.CardStats.date, hdate, "around")







# תאריך עברי בטבלה במסך דפדוף


def get_cell(self, index: QModelIndex) -> Cell:
    txt: str = self.get_row(index).cells[index.column()].text
    if isinstance(txt, str) and txt is not None:
        cell = txt.split("@")
        if is_date(cell[0][:10]):
            date = cell[0][:10]
            cell[0] = f"{convert_table_to_heb(date)} "
            self.get_row(index).cells[index.column()].text = "@".join(cell)
        # בחפיסות מסוננות אנקי עוטף את תאריך היעד בסוגריים — "(2026-07-23)" — לציון
        # יעד מקורי מושהה. הבדיקה על 10 התווים הראשונים נכשלת בגלל ה-"(", ולכן תאריכי
        # יעד בחפיסות מסוננות נשארו לועזיים. convert_table_to_heb כבר יודע לטפל בצורה
        # הזו ומחזיר את התאריך העברי בסוגריים.
        elif cell[0][:1] == "(" and is_date(cell[0][1:11]):
            cell[0] = f"{convert_table_to_heb(cell[0][:12])} "
            self.get_row(index).cells[index.column()].text = "@".join(cell)
    return self.get_row(index).cells[index.column()]


aqt.browser.table.model.DataModel.get_cell = wrap(aqt.browser.table.model.DataModel.get_cell, get_cell)

# #362 — מיון גימטריא (טו/טז) בשדה מיון שבדפדוף
#
# מיון לפי "שדה מיון" (noteFld) הוא מיון לקסיקוגרפי רגיל שמתבצע ב-backend של אנקי.
# הדרך היחידה כתוסף Python להשפיע על סדר התוצאות היא ב-gui_hooks.browser_did_search,
# שמאפשר לשנות את context.ids (רשימת המזהים שכבר חזרו מהחיפוש) לפני שהיא מוצגת בטבלה.
# פועלים רק כשעמודת המיון הנוכחית היא "noteFld" (שדה מיון) — בכל מיון אחר לא נוגעים בסדר.


def _gimatria_sort_enabled() -> bool:
    # try/except חיוני: אצל משתמשים קיימים meta.json עלול להכיל "config": null
    # (נוצר ע"י מתקינים ישנים), ואז getConfig של אנקי עצמו קורס ב-config.update(None)
    # עם TypeError. במקרה כזה נשארים על ברירת המחדל (מופעל).
    try:
        config = mw.addonManager.getConfig(__name__) or {}
    except Exception:
        return True
    return bool(config.get("gimatria_sort_enabled", True))


def _reorder_by_gimatria_sort_field(context) -> None:
    if not _gimatria_sort_enabled():
        return
    browser = getattr(context, "browser", None)
    ids = getattr(context, "ids", None)
    if not browser or not ids:
        return
    table = getattr(browser, "table", None)
    state = getattr(table, "_state", None) if table else None
    if not state or getattr(state, "sort_column", None) != "noteFld":
        return
    is_notes_mode = state.is_notes_mode() if hasattr(state, "is_notes_mode") else False
    # ל-Note אין מתודת sort_field; שדה המיון שמור בעמודת notes.sfld — קוראים אותו
    # ישירות ב-SQL (קריאה בלבד) כדי לא לטעון כל רשומה בנפרד.
    try:
        ids = list(ids)
        sort_fields: dict[int, str] = {}
        chunk_size = 500
        for start in range(0, len(ids), chunk_size):
            chunk = ids[start:start + chunk_size]
            placeholders = ",".join("?" * len(chunk))
            if is_notes_mode:
                rows = mw.col.db.all(
                    f"select id, sfld from notes where id in ({placeholders})", *chunk
                )
                sort_fields.update({row[0]: str(row[1]) for row in rows})
            else:
                rows = mw.col.db.all(
                    f"select c.id, n.sfld from cards c join notes n on n.id = c.nid"
                    f" where c.id in ({placeholders})", *chunk
                )
                sort_fields.update({row[0]: str(row[1]) for row in rows})
    except Exception:
        return
    keys = {item_id: gimatria_sort_key(sort_fields.get(item_id, "")) for item_id in ids}
    reversed_order = bool(getattr(state, "sort_backwards", False))
    context.ids = sorted(ids, key=lambda item_id: keys[item_id], reverse=reversed_order)


gui_hooks.browser_did_search.append(_reorder_by_gimatria_sort_field)


def _gimatria_sort_toggle_pref(self: aqt.preferences.Preferences) -> None:
    # #362 — הגדרת הפעלה/כיבוי תחת טאב "מראה" בהעדפות, כמבוקש.
    checkbox = QCheckBox("סארטירט דעם סארטיר פעלד אין דורכבלעטערן לויט גימטריא (טו/טז)", self.mw)
    checkbox.setChecked(_gimatria_sort_enabled())

    def _on_toggled(checked: bool) -> None:
        # אותה הגנה מפני meta.json עם "config": null (ראו _gimatria_sort_enabled);
        # הכתיבה עצמה גם מתקנת את meta.json בפועל (writeConfig מחליף את ה-null בערך תקין).
        try:
            config = mw.addonManager.getConfig(__name__) or {}
        except Exception:
            config = {}
        config["gimatria_sort_enabled"] = checked
        mw.addonManager.writeConfig(__name__, config)

    checkbox.toggled.connect(_on_toggled)
    # #362 — verticalLayout_8 הוא הפריסה הראשית של appearanceTab עצמו (טאב "מראה").
    self.form.verticalLayout_8.addWidget(checkbox)


# אין ל-Preferences מתודת setup_appearance ייעודית; setup_collection רץ אחרי setupUi
# (כמו ב-remove-buttons באותו קובץ), ולכן זו נקודת ה-hook הבטוחה להוספת ווידג'ט לטאב.
aqt.preferences.Preferences.setup_collection = wrap(
    aqt.preferences.Preferences.setup_collection, _gimatria_sort_toggle_pref, "after"
)

# תאריך עברי מעל כפתורי התשובה במסך מבחן

from datetime import datetime, timedelta


def _button_Time(self, i: int, v3_labels: Sequence[str] | None = None) -> str:
    if self.mw.col.conf["estTimes"]:
        txt = v3_labels[i - 1] if v3_labels else self.mw.col.sched.nextIvlStr(self.card, i, True) or ""
        today = datetime.today()
        delta = timedelta(seconds=self.mw.col.sched.nextIvl(self.card, i))
        d = today + delta
        y = d.strftime('%Y')
        m = d.strftime('%m')
        d = d.strftime('%d')
        hebdate = GregorianDate(int(y), int(m), int(d)).to_heb().hebrew_date_string()
        ivl_secs = self.mw.col.sched.nextIvl(self.card, i)
        self.mw.col.format_timespan(ivl_secs, FormatTimeSpan.CONTEXT_FIELD_NUMBER)
        # showInfo(str(a))

        # return f"<span class=nobold>{txt}</span><br><span class=hebdate>{hebday}, {hebdate}</span><br>"
        return f"<span class=nobold>{txt}<br><span class=hebdate>{hebdate}</span></span>"
    else:
        return ""


aqt.reviewer.Reviewer._buttonTime = wrap(aqt.reviewer.Reviewer._buttonTime, _button_Time)



# ======================================================================
#  1. Define the JavaScript code in one place to avoid repetition
# ======================================================================
HEBREW_DATE_CONVERSION_SCRIPT = """
    // --- Start of Hebrew Date Conversion Logic ---
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

    function Convert_date_to_heb(gregorianDateStr) {
        try { const date = new Date(gregorianDateStr + "T00:00:00Z"); return getFullHebrewDate(date); }
        catch (e) { return gregorianDateStr; }
    }

    // ##### THIS FUNCTION IS NOW STATEFUL (HAS MEMORY) #####
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

            // If this is the first label OR a new Hebrew year, add the year string.
            if (!window.lastProcessedHebrewYear || currentHebrewYear > window.lastProcessedHebrewYear) {
                const yearInGematria = _num_to_str(currentHebrewYear, true);
                finalLabel = `${monthPart.value} ${yearInGematria}`;
            }

            // Update the state for the next function call.
            window.lastProcessedHebrewYear = currentHebrewYear;

            return finalLabel;

        } catch (e) { return match; }
    }

    function Convert_tooltip_date_to_heb(match, day, month, year) {
        try { const date = new Date(Date.UTC(year, month - 1, day)); return getFullHebrewDate(date); }
        catch (e) { return match; }
    }

    // #250 — לוח השנה בסטטיסטיקות מציג לפעמים תאריך לועזי עם שמות חודשים בעברית, למשל "יום ראשון, 17 מאי 2026".
    var HAF_GREG_HEB_MONTHS = window.HAF_GREG_HEB_MONTHS || {"ינואר":1,"פברואר":2,"מרץ":3,"אפריל":4,"מאי":5,"יוני":6,"יולי":7,"אוגוסט":8,"ספטמבר":9,"אוקטובר":10,"נובמבר":11,"דצמבר":12};
    window.HAF_GREG_HEB_MONTHS = HAF_GREG_HEB_MONTHS;
    var HAF_GREG_ENG_MONTHS = window.HAF_GREG_ENG_MONTHS || {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,"July":7,"August":8,"September":9,"October":10,"November":11,"December":12};
    window.HAF_GREG_ENG_MONTHS = HAF_GREG_ENG_MONTHS;

    function Convert_english_gregorian_month_date(match, monthName, day, year) {
        try {
            const month = HAF_GREG_ENG_MONTHS[monthName];
            if (!month) return match;
            const date = new Date(Date.UTC(parseInt(year, 10), month - 1, parseInt(day, 10)));
            return getFullHebrewDate(date);
        } catch (e) { return match; }
    }

    function Convert_english_gregorian_month_year(match, monthName, year) {
        try {
            const month = HAF_GREG_ENG_MONTHS[monthName];
            if (!month) return match;
            const date = new Date(Date.UTC(parseInt(year, 10), month - 1, 15));
            const hebrewFormatter = new Intl.DateTimeFormat('he-u-ca-hebrew', { timeZone: 'UTC', year: 'numeric', month: 'long' });
            const parts = hebrewFormatter.formatToParts(date);
            const monthPart = parts.find(p => p.type === 'month');
            const yearPart = parts.find(p => p.type === 'year');
            if (!monthPart || !yearPart) return match;
            return `${monthPart.value} ${_num_to_str(parseInt(yearPart.value), false)}`;
        } catch (e) { return match; }
    }
    function Convert_hebrew_gregorian_month_date(match, prefix, day, monthName, year) {
        try {
            const month = HAF_GREG_HEB_MONTHS[monthName];
            if (!month) return match;
            const date = new Date(Date.UTC(parseInt(year, 10), month - 1, parseInt(day, 10)));
            return (prefix || "") + getFullHebrewDate(date);
        } catch (e) { return match; }
    }

    function Convert_month_to_heb(monthName, inferredYear) {
        try { const date = new Date(`${monthName} 1, ${inferredYear}`); return new Intl.DateTimeFormat('he-u-ca-hebrew', { month: 'long' }).format(date); }
        catch (e) { return monthName; }
    }

    function Convert_short_month_to_heb(monthAbbr, inferredYear) {
        try {
            const date = new Date(`${monthAbbr} 15, ${inferredYear}`);
            if (isNaN(date.getTime())) return monthAbbr;
            const hebrewFormatter = new Intl.DateTimeFormat('he-u-ca-hebrew', { month: 'long' });
            const hebMonth = hebrewFormatter.format(date);

            const yearFormatter = new Intl.DateTimeFormat('he-u-ca-hebrew', { year: 'numeric' });
            const yearParts = yearFormatter.formatToParts(date);
            const yearValue = yearParts.find(p => p.type === 'year');
            const currentHebrewYear = yearValue ? parseInt(yearValue.value) : 0;

            if (!window.lastProcessedHebrewYear || currentHebrewYear > window.lastProcessedHebrewYear) {
                const yearInGematria = _num_to_str(currentHebrewYear, false);
                window.lastProcessedHebrewYear = currentHebrewYear;
                return `${hebMonth} ${yearInGematria}`;
            }
            window.lastProcessedHebrewYear = currentHebrewYear;
            return hebMonth;
        } catch (e) { return monthAbbr; }
    }

    function Convert_year_to_heb(year) {
        try {
            const date = new Date(Date.UTC(parseInt(year, 10), 6, 1));
            const parts = new Intl.DateTimeFormat('he-u-ca-hebrew', { timeZone: 'UTC', year: 'numeric' }).formatToParts(date);
            const yearPart = parts.find(p => p.type === 'year');
            return yearPart ? _num_to_str(parseInt(yearPart.value), false) : year;
        } catch (e) { return year; }
    }

    function Convert_day_of_week_to_heb(match, dayOfWeek, dayOfMonth) {
        try { return _num_to_str(parseInt(dayOfMonth)); }
        catch (e) { return match; }
    }

    // #250 — לוח השנה בסטטיסטיקות: הנתונים מגיעים מהתוסף (Python) דרך pycmd כדי לכסות שנה
    // עברית מלאה (תשרי–אלול) שחוצה שתי שנים לועזיות, ולא רק את השנה הלועזית שהרכיב המקורי מצייר.
    window._hafHebCal = window._hafHebCal || {
        counts: null,          // Map iso -> {count, day, date}
        maxCount: 0,
        minHebYear: 0,
        maxHebYear: 0,
        displayHebYear: 0,
        days: 365,             // טווח הנתונים שנשלף (365 = "12 חודשים", 0 = כל ההיסטוריה)
        key: null,             // search + days שעבורם נשלפו הנתונים
        errorKey: null,
        pending: false,
        version: 0
    };

    function _hafStatsIsoDate(date) {
        return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate())).toISOString().slice(0, 10);
    }

    function _hafStatsAddDays(date, days) {
        const next = new Date(date.getTime());
        next.setUTCDate(next.getUTCDate() + days);
        return next;
    }

    function _hafStatsUtcFromLocal(date) {
        return new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    }

    var _hafStatsHebFormatter = null;
    function _hafStatsHebrewParts(date) {
        if (!_hafStatsHebFormatter) {
            _hafStatsHebFormatter = new Intl.DateTimeFormat('he-u-ca-hebrew', {
                timeZone: 'UTC', year: 'numeric', month: 'long', day: 'numeric'
            });
        }
        const parts = _hafStatsHebFormatter.formatToParts(date);
        const day = parts.find(p => p.type === 'day');
        const month = parts.find(p => p.type === 'month');
        const year = parts.find(p => p.type === 'year');
        if (!day || !month || !year) return null;
        return { day: parseInt(day.value, 10), month: month.value, year: parseInt(year.value, 10) };
    }

    function _hafStatsHebYearOf(dateUtc) {
        const hp = _hafStatsHebrewParts(dateUtc);
        return hp ? hp.year : 0;
    }

    // #250 — א' תשרי של שנה עברית נופל בספטמבר-אוקטובר של השנה הלועזית hebYear-3761
    var _hafTishreiCache = {};
    function _hafStatsTishrei1(hebYear) {
        if (_hafTishreiCache[hebYear]) return _hafTishreiCache[hebYear];
        const gregYear = hebYear - 3761;
        let cursor = new Date(Date.UTC(gregYear, 7, 20));
        const end = new Date(Date.UTC(gregYear, 10, 15));
        for (; cursor <= end; cursor = _hafStatsAddDays(cursor, 1)) {
            const hp = _hafStatsHebrewParts(cursor);
            if (hp && hp.year === hebYear && hp.month === 'תשרי' && hp.day === 1) {
                _hafTishreiCache[hebYear] = cursor;
                return cursor;
            }
        }
        return null;
    }

    // #250 — סולם צבעים תואם ל-interpolateBlues של הרכיב המקורי (טווח 0.2–1, ובמצב לילה 0.2–0.8)
    var _HAF_BLUES = [
        [0, 247, 251, 255], [0.125, 222, 235, 247], [0.25, 198, 219, 239],
        [0.375, 158, 202, 225], [0.5, 107, 174, 214], [0.625, 66, 146, 198],
        [0.75, 33, 113, 181], [0.875, 8, 81, 156], [1, 8, 48, 107]
    ];
    function _hafStatsColour(count, maxCount, nightMode) {
        if (count <= 0) return nightMode ? '#333333' : '#dddddd';
        const hi = nightMode ? 0.8 : 1.0;
        const t = 0.2 + (maxCount ? Math.min(1, count / maxCount) : 0) * (hi - 0.2);
        for (let i = 1; i < _HAF_BLUES.length; i++) {
            const a = _HAF_BLUES[i - 1], b = _HAF_BLUES[i];
            if (t <= b[0]) {
                const f = (t - a[0]) / (b[0] - a[0]);
                const r = Math.round(a[1] + (b[1] - a[1]) * f);
                const g = Math.round(a[2] + (b[2] - a[2]) * f);
                const bl = Math.round(a[3] + (b[3] - a[3]) * f);
                return `rgb(${r}, ${g}, ${bl})`;
            }
        }
        return 'rgb(8, 48, 107)';
    }

    function _hafStatsSearchValue() {
        const el = document.getElementById('statisticsSearchText');
        return el ? el.value : 'deck:current';
    }

    // #250 — כמו במקור: קוראים את בורר הטווח של הדף (12 חודשים = 365, כל ההיסטוריה = 0).
    // ברירת המחדל של אנקי היא 12 חודשים.
    function _hafStatsRangeDays() {
        const box = document.querySelector('.range-box');
        if (box) {
            const radios = Array.from(box.querySelectorAll('input[type="radio"]'));
            // שני הרדיו האחרונים הם בורר הטווח: [12 חודשים, כל ההיסטוריה]
            if (radios.length >= 2 && radios[radios.length - 1].checked) return 0;
        }
        return 365;
    }

    // #366 — משתמשים ב-tooltip ייעודי ולא ב-SVG <title> המערכתי של Windows או באלמנט
    // המשותף של Svelte. אם התא שמתחתיו הועלם באמצע ריחוף — למשל בגלל ציור מחדש של
    // הלוח, גלילה או תזוזה מהירה — האירוע mouseout לא נורה על האלמנט שנמחק, וה-tooltip
    // נשאר גלוי עם התאריך האחרון שרוחף עליו גם כשעולים לשאר החלון. לכן מסמנים "בעלות"
    // על ה-tooltip ומסתירים אותו בכל תזוזת עכבר מחוץ ללוח העברי.
    function _hafStatsInstallTooltipWatcher() {
        if (window._hafStatsTooltipWatcher) return;
        window._hafStatsTooltipWatcher = true;
        const release = function(ev) {
            if (!window._hafStatsTooltipOwned) return;
            const target = ev && ev.target;
            if (target && target.closest && target.closest('g.haf-hebrew-stats-calendar')) return;
            _hafStatsHideTooltip();
        };
        document.addEventListener('mousemove', release, true);
        document.addEventListener('mouseleave', release, true);
        document.addEventListener('wheel', release, true);
        window.addEventListener('blur', function() { _hafStatsHideTooltip(); });
    }

    function _hafStatsTooltipElement() {
        let tt = document.getElementById('haf-hebrew-calendar-tooltip');
        if (!tt) {
            tt = document.createElement('div');
            tt.id = 'haf-hebrew-calendar-tooltip';
            tt.setAttribute('dir', 'rtl');
            tt.style.cssText = 'position:fixed;z-index:2147483647;pointer-events:none;' +
                'max-width:260px;padding:8px 11px;border-radius:9px;' +
                'box-shadow:0 8px 24px rgba(0,0,0,.25);' +
                'font:500 13px/1.45 system-ui,Segoe UI,sans-serif;text-align:right;' +
                'white-space:nowrap;opacity:0;transform:translateY(2px);' +
                'transition:opacity .1s ease,transform .1s ease;';
            document.body.appendChild(tt);
        }
        return tt;
    }

    function _hafStatsShowTooltip(html, ev) {
        const tt = _hafStatsTooltipElement();
        _hafStatsInstallTooltipWatcher();
        window._hafStatsTooltipOwned = true;
        const nightMode = !!(document.body.classList.contains('night-mode') ||
            document.documentElement.classList.contains('night-mode') ||
            document.body.dataset.bsTheme === 'dark');
        tt.style.border = '1px solid ' + (nightMode ? '#596273' : '#d6dbe3');
        tt.style.background = nightMode ? '#262a32' : '#ffffff';
        tt.style.color = nightMode ? '#f3f4f6' : '#20242b';
        tt.innerHTML = html;
        tt.style.opacity = '1';
        tt.style.transform = 'translateY(0)';
        const pad = 12;
        let x = (ev.clientX || 0) + pad;
        let y = (ev.clientY || 0) + pad;
        const width = tt.offsetWidth || 180;
        const height = tt.offsetHeight || 54;
        if (x + width > window.innerWidth - 6) x = Math.max(6, (ev.clientX || 0) - width - pad);
        if (y + height > window.innerHeight - 6) y = Math.max(6, (ev.clientY || 0) - height - pad);
        tt.style.left = x + 'px';
        tt.style.top = y + 'px';
        return true;
    }

    function _hafStatsHideTooltip() {
        window._hafStatsTooltipOwned = false;
        const tt = document.getElementById('haf-hebrew-calendar-tooltip');
        if (tt) {
            tt.style.opacity = '0';
            tt.style.transform = 'translateY(2px)';
        }
    }

    // #250 — מוחזר מ-Python עם ספירת החזרות היומית לטווח המבוקש (offset יום -> כמות)
    window._hafHebCalReceive = function(data) {
        const st = window._hafHebCal;
        st.pending = false;
        if (!data || data.error) {
            st.counts = null;
            st.errorKey = st.key;
            console.warn('hebrew-date: hafHebCal failed:', data && data.error);
            _hafHebCalRestoreNative();
            return;
        }
        st.errorKey = null;
        st.days = Number(data.days) || 0;
        const rollover = Number(data.rolloverHour || 0);
        const counts = new Map();
        let maxCount = 0;
        let minDate = null;
        Object.keys(data.counts || {}).forEach(function(key) {
            const offset = parseInt(key, 10);
            const count = Number(data.counts[key]) || 0;
            if (!count || !Number.isFinite(offset)) return;
            // אותו חישוב יום כמו ברכיב המקורי: היום + offset ימים, פחות שעות ה-rollover
            const local = new Date();
            local.setDate(local.getDate() + offset);
            local.setHours(local.getHours() - rollover);
            const date = _hafStatsUtcFromLocal(local);
            const iso = _hafStatsIsoDate(date);
            const existing = counts.get(iso);
            if (existing) {
                existing.count += count;
                maxCount = Math.max(maxCount, existing.count);
            } else {
                counts.set(iso, { count: count, day: offset, date: date });
                maxCount = Math.max(maxCount, count);
            }
            if (!minDate || date < minDate) minDate = date;
        });
        st.counts = counts;
        st.maxCount = maxCount;
        const todayUtc = _hafStatsUtcFromLocal(new Date());
        st.maxHebYear = _hafStatsHebYearOf(todayUtc);
        // כמו במקור: בטווח "12 חודשים" מותר לדפדף שנה אחת אחורה (חלון של 365 יום נוגע
        // תמיד בשנה העברית הקודמת); ב"כל ההיסטוריה" — עד השנה העברית הראשונה שיש בה נתונים
        st.minHebYear = st.days > 0
            ? st.maxHebYear - 1
            : (minDate ? Math.min(_hafStatsHebYearOf(minDate), st.maxHebYear) : st.maxHebYear);
        if (!st.displayHebYear || st.displayHebYear < st.minHebYear || st.displayHebYear > st.maxHebYear) {
            st.displayHebYear = st.maxHebYear;
        }
        st.version++;
        _hafRenderHebrewStatsCalendar();
    };

    // #250 — מחזירים את הלוח הלועזי המקורי לתצוגה: בשגיאה, או כשאין נתונים בכלל
    // (במקרה כזה הרכיב המקורי מסתיר את הגרף כולו בעצמו — בדיוק כמו במקור).
    function _hafHebCalRestoreNative() {
        _hafStatsHideTooltip();  // #366 — התאים שלנו נעלמים; לא להשאיר tooltip שלנו תלוי באוויר
        document.querySelectorAll('svg').forEach(function(svg) {
            const weekdayGroup = svg.querySelector('g.weekdays');
            const daysGroup = svg.querySelector('g.days');
            if (!weekdayGroup || !daysGroup) return;
            if (weekdayGroup.style.opacity === '0') weekdayGroup.style.opacity = '';
            if (weekdayGroup.style.pointerEvents === 'none') weekdayGroup.style.pointerEvents = '';
            if (daysGroup.style.opacity === '0') daysGroup.style.opacity = '';
            if (daysGroup.style.pointerEvents === 'none') daysGroup.style.pointerEvents = '';
            const overlay = svg.querySelector('g.haf-hebrew-stats-calendar');
            if (overlay) overlay.remove();
            const graphDiv = svg.closest('.graph') || svg.parentElement;
            if (!graphDiv) return;
            const nav = graphDiv.querySelector('.haf-heb-cal-nav');
            if (nav) nav.remove();
            graphDiv.querySelectorAll('[data-haf-hidden-nav]').forEach(function(el) {
                el.style.display = '';
                el.removeAttribute('data-haf-hidden-nav');
            });
        });
    }

    // #250 — מחליפים את ניווט השנים הלועזי (◄ 2026 ►) בניווט בין שנים עבריות
    function _hafStatsSetupHebNav(svg, st) {
        const graphDiv = svg.closest('.graph') || svg.parentElement;
        if (!graphDiv) return;
        const nativeButtons = Array.from(graphDiv.querySelectorAll('button')).filter(function(btn) {
            const t = (btn.textContent || '').trim();
            return (t === '◄' || t === '►') && !btn.hasAttribute('data-haf-heb-nav');
        });
        if (nativeButtons.length) {
            const span = nativeButtons[0].closest('span');
            const box = span ? span.parentElement : null;
            if (box && !box.classList.contains('haf-heb-cal-nav') && !box.hasAttribute('data-haf-hidden-nav')) {
                box.style.display = 'none';
                box.setAttribute('data-haf-hidden-nav', '1');
            }
        }
        let nav = graphDiv.querySelector('.haf-heb-cal-nav');
        if (!nav) {
            nav = document.createElement('div');
            nav.className = 'haf-heb-cal-nav';
            nav.setAttribute('dir', 'rtl');
            nav.style.cssText = 'display:flex;justify-content:center;align-items:center;gap:10px;margin:2px 0 4px;';
            // #250 — בלוח RTL הזמן מתקדם שמאלה, לכן "שנה קודמת" מצביעה ימינה ו"שנה הבאה" שמאלה
            const prevBtn = document.createElement('button');
            prevBtn.textContent = '►';
            prevBtn.setAttribute('data-haf-heb-nav', '-1');
            const yearLabel = document.createElement('strong');
            yearLabel.className = 'haf-heb-cal-year';
            const nextBtn = document.createElement('button');
            nextBtn.textContent = '◄';
            nextBtn.setAttribute('data-haf-heb-nav', '1');
            [prevBtn, nextBtn].forEach(function(btn) {
                // צבע יורש מהדף — תואם גם למצב לילה
                btn.style.cssText = 'background:none;border:none;color:inherit;font-size:100%;padding:0 6px;cursor:pointer;';
                btn.addEventListener('click', function() {
                    const delta = parseInt(btn.getAttribute('data-haf-heb-nav'), 10);
                    const target = st.displayHebYear + delta;
                    if (target < st.minHebYear || target > st.maxHebYear) return;
                    st.displayHebYear = target;
                    _hafRenderHebrewStatsCalendar();
                });
            });
            nav.appendChild(prevBtn);
            nav.appendChild(yearLabel);
            nav.appendChild(nextBtn);
            const hiddenBox = graphDiv.querySelector('[data-haf-hidden-nav]');
            if (hiddenBox && hiddenBox.parentElement) {
                hiddenBox.parentElement.insertBefore(nav, hiddenBox);
            } else if (svg.parentElement) {
                svg.parentElement.insertBefore(nav, svg);
            }
        }
        const label = nav.querySelector('.haf-heb-cal-year');
        if (label) label.textContent = _num_to_str(st.displayHebYear, true);
        nav.querySelectorAll('button[data-haf-heb-nav]').forEach(function(btn) {
            const target = st.displayHebYear + parseInt(btn.getAttribute('data-haf-heb-nav'), 10);
            const enabled = target >= st.minHebYear && target <= st.maxHebYear;
            btn.disabled = !enabled;
            btn.style.opacity = enabled ? '1' : '0.3';
            btn.style.cursor = enabled ? 'pointer' : 'default';
        });
    }

    function _hafRenderHebrewStatsCalendar() {
        if (window._hafHebrewStatsCalendarRendering) return;
        window._hafHebrewStatsCalendarRendering = true;
        try {
            const st = window._hafHebCal;
            document.querySelectorAll('svg').forEach(function(svg) {
                const weekdayGroup = svg.querySelector('g.weekdays');
                const daysGroup = svg.querySelector('g.days');
                if (!weekdayGroup || !daysGroup) return;

                // #250 — מבקשים נתונים מהתוסף כשאין עדיין נתונים, או כשהחיפוש/הטווח בחלון השתנו
                const search = _hafStatsSearchValue();
                const rangeDays = _hafStatsRangeDays();
                const key = rangeDays + '|' + search;
                if (!st.pending && st.errorKey !== key && (st.counts === null || st.key !== key)) {
                    st.key = key;
                    if (typeof pycmd === 'function') {
                        st.pending = true;
                        pycmd('hafHebCal:' + JSON.stringify({ search: search, days: rangeDays }));
                    }
                }
                if (!st.counts) return;

                // כמו במקור: כשאין אף חזרה בנתונים — לא מציגים לוח בכלל (הרכיב המקורי
                // מסתיר את הגרף כולו במצב הזה, ומחזירים לו את השליטה)
                if (st.maxCount === 0) {
                    _hafHebCalRestoreNative();
                    return;
                }

                const hebYear = st.displayHebYear;
                const yearStart = _hafStatsTishrei1(hebYear);
                const nextYearStart = _hafStatsTishrei1(hebYear + 1);
                if (!yearStart || !nextYearStart) return;

                // #250 — מסתירים את לוח השנה הגרגוריאני המקורי ומציירים עליו שנה עברית מלאה
                // מא' תשרי עד כ"ט אלול, בלי לגעת בנתוני Svelte עצמם.
                weekdayGroup.style.opacity = '0';
                weekdayGroup.style.pointerEvents = 'none';
                daysGroup.style.opacity = '0';
                daysGroup.style.pointerEvents = 'none';

                _hafStatsSetupHebNav(svg, st);

                const vb = svg.viewBox && svg.viewBox.baseVal;
                const rectBox = svg.getBoundingClientRect ? svg.getBoundingClientRect() : { width: 0, height: 0 };
                const width = (vb && vb.width) || rectBox.width || 760;
                const height = (vb && vb.height) || rectBox.height || 120;
                const nightMode = !!(document.body.classList.contains('night-mode') || document.documentElement.classList.contains('night-mode') || document.body.dataset.bsTheme === 'dark');

                const weekdayOrder = Array.from(weekdayGroup.querySelectorAll('text'))
                    .map(text => Number(text.__data__))
                    .filter(num => Number.isFinite(num));
                const order = weekdayOrder.length === 7 ? weekdayOrder : [0, 1, 2, 3, 4, 5, 6];
                const rowForWeekday = new Map(order.map((weekday, idx) => [weekday, idx]));

                const signature = `${hebYear}:${st.version}:${order.join('')}:${Math.round(width)}:${Math.round(height)}:${nightMode ? 1 : 0}`;

                let overlay = svg.querySelector('g.haf-hebrew-stats-calendar');
                if (!overlay) {
                    overlay = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                    overlay.setAttribute('class', 'haf-hebrew-stats-calendar');
                    svg.appendChild(overlay);
                }
                if (overlay.getAttribute('data-haf-signature') === signature && overlay.childNodes.length) {
                    return;
                }
                overlay.setAttribute('data-haf-signature', signature);
                // #366 — התאים שמתחת לעכבר עומדים להימחק; mouseout כבר לא ייורה עליהם
                _hafStatsHideTooltip();
                overlay.textContent = '';

                const days = [];
                for (let cursor = yearStart; cursor < nextYearStart; cursor = _hafStatsAddDays(cursor, 1)) {
                    days.push(cursor);
                }
                const todayUtc = _hafStatsUtcFromLocal(new Date());
                // כמו במקור: בטווח "12 חודשים" ימים ללא נתונים מצוירים רק בתוך שנה אחורה
                const yearAgoLocal = new Date();
                yearAgoLocal.setFullYear(yearAgoLocal.getFullYear() - 1);
                const rangeCutoff = st.days > 0 ? _hafStatsUtcFromLocal(yearAgoLocal) : null;
                const startOffset = rowForWeekday.has(yearStart.getUTCDay()) ? rowForWeekday.get(yearStart.getUTCDay()) : yearStart.getUTCDay();
                // #250 — הלוח נפרש מימין לשמאל: תשרי בעמודה הימנית והזמן מתקדם שמאלה,
                // תוויות ימות השבוע בצד ימין של הרשת.
                const weekCount = Math.ceil((days.length + startOffset) / 7);
                const labelMargin = 34;
                const edgeMargin = 18;
                const marginTop = 20;
                const marginBottom = 6;
                const gap = 2;
                const cellW = Math.max(5, (width - labelMargin - edgeMargin) / weekCount - gap);
                const cellH = Math.max(8, (height - marginTop - marginBottom) / 7 - gap);
                const labelColor = (weekdayGroup.querySelector('text') && (weekdayGroup.querySelector('text').getAttribute('fill') || getComputedStyle(weekdayGroup.querySelector('text')).fill)) || (nightMode ? '#dddddd' : '#111111');

                function columnX(column) {
                    return width - labelMargin - (column + 1) * (cellW + gap);
                }

                function svgEl(name, attrs) {
                    const el = document.createElementNS('http://www.w3.org/2000/svg', name);
                    Object.entries(attrs || {}).forEach(([key, value]) => el.setAttribute(key, String(value)));
                    overlay.appendChild(el);
                    return el;
                }

                const weekdayLetters = {0: 'א', 1: 'ב', 2: 'ג', 3: 'ד', 4: 'ה', 5: 'ו', 6: 'ש'};
                order.forEach(function(weekday, row) {
                    const text = svgEl('text', {
                        x: width - labelMargin + 8,
                        y: marginTop + row * (cellH + gap) + cellH / 2,
                        fill: labelColor,
                        'font-size': '10',
                        'font-family': 'monospace',
                        'text-anchor': 'start',
                        'dominant-baseline': 'middle'
                    });
                    text.textContent = weekdayLetters[weekday] || '';
                    // כמו במקור: לחיצה על א/ב/ו/ש קובעת את היום הראשון בשבוע — מעבירים את
                    // הלחיצה לאלמנט המקורי המוסתר כדי שההעדפה תישמר דרך המנגנון של אנקי
                    if (weekday === 0 || weekday === 1 || weekday === 5 || weekday === 6) {
                        text.style.cursor = 'pointer';
                        text.addEventListener('click', function() {
                            const target = Array.from(weekdayGroup.querySelectorAll('text'))
                                .find(t => Number(t.__data__) === weekday);
                            if (target) target.dispatchEvent(new MouseEvent('click', { bubbles: false }));
                        });
                    }
                });

                const hebWeekdayNames = {0: 'יום ראשון', 1: 'יום שני', 2: 'יום שלישי', 3: 'יום רביעי', 4: 'יום חמישי', 5: 'יום שישי', 6: 'שבת'};
                const monthLabelKeys = new Set();
                days.forEach(function(date, idx) {
                    // כמו ברכיב המקורי — לא מציירים ימים עתידיים
                    if (date > todayUtc) return;
                    const iso = _hafStatsIsoDate(date);
                    const entry = st.counts.get(iso);
                    // כמו במקור: יום בלי נתונים מצויר רק בתוך חלון הטווח (שנה אחורה כשנבחר
                    // "12 חודשים"); מחוץ לחלון נשאר ריק
                    if (!entry && rangeCutoff && date <= rangeCutoff) return;
                    const hp = _hafStatsHebrewParts(date);
                    if (!hp) return;
                    const count = entry ? entry.count : 0;
                    const row = rowForWeekday.has(date.getUTCDay()) ? rowForWeekday.get(date.getUTCDay()) : date.getUTCDay();
                    const column = Math.floor((idx + startOffset) / 7);
                    const x = columnX(column);
                    const y = marginTop + row * (cellH + gap);

                    // תווית חודש מעל היום הראשון המוצג של כל חודש
                    const monthKey = `${hp.month}:${hp.year}`;
                    if (!monthLabelKeys.has(monthKey)) {
                        monthLabelKeys.add(monthKey);
                        // התווית נצמדת לקצה הימני של העמודה ונמשכת שמאלה (direction rtl)
                        const monthText = svgEl('text', {
                            x: x + cellW,
                            y: 10,
                            fill: labelColor,
                            'font-size': '8',
                            'font-family': 'sans-serif',
                            'text-anchor': 'start',
                            direction: 'rtl'
                        });
                        monthText.textContent = hp.month === 'תשרי' ? `${hp.month} ${_num_to_str(hp.year, false)}` : hp.month;
                    }

                    // תא חלק בדיוק כמו במקור — צבע בלבד, בלי מסגרת ובלי אותיות על הקוביות
                    const rect = svgEl('rect', {
                        x: x,
                        y: y,
                        width: cellW,
                        height: cellH,
                        fill: _hafStatsColour(count, st.maxCount, nightMode),
                        'data-haf-hebrew-cell': '1',
                        'aria-label': `${_num_to_str(hp.day)} ${hp.month} ${_num_to_str(hp.year, true)}, ${count} חזרות`
                    });
                    // tooltip מרחף כמו במקור: "יום פלוני, תאריך עברי" ומספר חזרות
                    const tipHtml = `${hebWeekdayNames[date.getUTCDay()]}, ${_num_to_str(hp.day)} ${hp.month} ${_num_to_str(hp.year, true)}<br>${count} חזרות`;
                    rect.addEventListener('mousemove', function(ev) { _hafStatsShowTooltip(tipHtml, ev); });
                    rect.addEventListener('mouseout', _hafStatsHideTooltip);
                    if (count > 0 && entry) {
                        rect.setAttribute('class', 'graph-element-clickable');
                        rect.style.cursor = 'pointer';
                        rect.addEventListener('click', function() {
                            if (typeof pycmd === 'function') {
                                pycmd(`browserSearch: "prop:rated=${entry.day}"`);
                            }
                        });
                    }
                });
            });
        } finally {
            window._hafHebrewStatsCalendarRendering = false;
        }
    }

    function convertAttributeValue(val) {
        let newVal = val;
        newVal = newVal.replace(/(\\d{4}-\\d{2}-\\d{2})/g, function(m) { return Convert_date_to_heb(m); });
        newVal = newVal.replace(/(\\d{1,2})\\.(\\d{1,2})\\.(\\d{4})/g, function(m, d, mo, y) { return Convert_tooltip_date_to_heb(m, d, mo, y); });
        newVal = newVal.replace(/(יום\\s+(?:ראשון|שני|שלישי|רביעי|חמישי|שישי|שבת),?\\s*)?(\\d{1,2})\\s+(ינואר|פברואר|מרץ|אפריל|מאי|יוני|יולי|אוגוסט|ספטמבר|אוקטובר|נובמבר|דצמבר)\\s+(\\d{4})/g, function(m, prefix, d, monthName, y) { return Convert_hebrew_gregorian_month_date(m, prefix || "", d, monthName, y); });
        newVal = newVal.replace(/\\b(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),?\\s+(January|February|March|April|May|June|July|August|September|October|November|December)\\s+(\\d{1,2}),?\\s+(\\d{4})\\b/g, function(m, monthName, d, y) { return Convert_english_gregorian_month_date(m, monthName, d, y); });
        newVal = newVal.replace(/\\b(January|February|March|April|May|June|July|August|September|October|November|December)\\s+(\\d{1,2}),?\\s+(\\d{4})\\b/g, function(m, monthName, d, y) { return Convert_english_gregorian_month_date(m, monthName, d, y); });
        return newVal;
    }
    // --- End of Hebrew Date Conversion Logic ---

    // --- START: פונקציה מתוקנת ---
    function convertDatesOnNode(node, inferredYear) {
        if (node.nodeType === Node.TEXT_NODE) {
            let content = node.textContent;
            if (!content || content.trim() === '') return;
            let changed = false;

            if (content.includes("Date Time:") || content.includes("Date:")) {
                content = content.replace(/Date Time:/g, 'דאטום און צייט:').replace(/Date:/g, 'דאטום:');
                changed = true;
            }

            const tableRegex = /(\\d{4}-\\d{2}-\\d{2})/g;
            if (tableRegex.test(content)) { content = content.replace(tableRegex, (match) => Convert_date_to_heb(match)); changed = true; }

            const tooltipRegex = /(\\d{1,2})\\.(\\d{1,2})\\.(\\d{4})/g;
            if (tooltipRegex.test(content)) { content = content.replace(tooltipRegex, (match, day, month, year) => Convert_tooltip_date_to_heb(match, day, month, year)); changed = true; }

            const hebrewGregorianMonthRegex = /(יום\\s+(?:ראשון|שני|שלישי|רביעי|חמישי|שישי|שבת),?\\s*)?(\\d{1,2})\\s+(ינואר|פברואר|מרץ|אפריל|מאי|יוני|יולי|אוגוסט|ספטמבר|אוקטובר|נובמבר|דצמבר)\\s+(\\d{4})/g;
            if (hebrewGregorianMonthRegex.test(content)) { content = content.replace(hebrewGregorianMonthRegex, (match, prefix, day, monthName, year) => Convert_hebrew_gregorian_month_date(match, prefix || "", day, monthName, year)); changed = true; }

            const englishWeekdayDateRegex = /\\b(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),?\\s+(January|February|March|April|May|June|July|August|September|October|November|December)\\s+(\\d{1,2}),?\\s+(\\d{4})\\b/g;
            if (englishWeekdayDateRegex.test(content)) { content = content.replace(englishWeekdayDateRegex, (match, monthName, day, year) => Convert_english_gregorian_month_date(match, monthName, day, year)); changed = true; }

            const englishMonthDateRegex = /\\b(January|February|March|April|May|June|July|August|September|October|November|December)\\s+(\\d{1,2}),?\\s+(\\d{4})\\b/g;
            if (englishMonthDateRegex.test(content)) { content = content.replace(englishMonthDateRegex, (match, monthName, day, year) => Convert_english_gregorian_month_date(match, monthName, day, year)); changed = true; }

            const graphRegex = /\\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s(\\d{1,2})\\b/g;
            if (graphRegex.test(content)) { content = content.replace(graphRegex, (match, month, day) => Convert_graph_date_to_heb(match, month, day, inferredYear)); changed = true; }

            const shortMonthRegex = /^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$/;
            if (shortMonthRegex.test(content.trim())) { content = Convert_short_month_to_heb(content.trim(), inferredYear); changed = true; }

            const monthYearRegex = /^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+(\\d{4})$/;
            const monthYearMatch = content.trim().match(monthYearRegex);
            if (monthYearMatch) { content = Convert_short_month_to_heb(monthYearMatch[1], parseInt(monthYearMatch[2])); changed = true; }

            const fullMonthYearRegex = /^(January|February|March|April|May|June|July|August|September|October|November|December)\\s+(\\d{4})$/;
            const fullMonthYearMatch = content.trim().match(fullMonthYearRegex);
            if (fullMonthYearMatch) { content = Convert_english_gregorian_month_year(content.trim(), fullMonthYearMatch[1], fullMonthYearMatch[2]); changed = true; }

            const fullMonthRegex = /\\b(January|February|March|April|May|June|July|August|September|October|November|December)\\b/g;
            if (fullMonthRegex.test(content)) { content = content.replace(fullMonthRegex, (match) => Convert_month_to_heb(match, inferredYear)); changed = true; }

            const dayOfWeekRegex = /\\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\\s(\\d{1,2})\\b/g;
            if (dayOfWeekRegex.test(content)) { content = content.replace(dayOfWeekRegex, (match, dayOfWeek, dayOfMonth) => Convert_day_of_week_to_heb(match, dayOfWeek, dayOfMonth)); changed = true; }

            const yearRegex = /^(\\d{4})$/g;
            if (yearRegex.test(content.trim())) {
                const parentElement = node.parentElement;
                // בדיקה האם האלמנט הקודם מכיל את הטקסט 'מיקום' כדי למנוע המרה
                if (parentElement && parentElement.previousElementSibling && parentElement.previousElementSibling.textContent.trim() === 'מיקום') {
                    // This is the "מיקום" (location) field, so do not convert the number.
                } else {
                    content = content.replace(yearRegex, (match) => Convert_year_to_heb(match));
                    changed = true;
                }
            }

            if (changed) { node.textContent = content; }

        } else if (node.nodeType === Node.ELEMENT_NODE) {
            // #250 — המרת תאריכים בתכונות title / aria-label (tooltip של SVG וכד.)
            if (typeof node.getAttribute === 'function') {
                ['title', 'data-original-title', 'aria-label'].forEach(function(attr) {
                    const val = node.getAttribute(attr);
                    if (!val) return;
                    let newVal = convertAttributeValue(val);
                    if (newVal !== val) node.setAttribute(attr, newVal);
                });
            }
            for (const child of node.childNodes) {
                convertDatesOnNode(child, inferredYear);
            }
        }
    }
    // --- END: פונקציה מתוקנת ---

    function runConversion() {
        let inferredYear = new Date().getFullYear();
        const yearMatch = document.body.innerText.match(/\\b(\\d{4})-\\d{2}-\\d{2}\\b/);
        if (yearMatch) { inferredYear = parseInt(yearMatch[1]); }

        // ##### RESET THE YEAR TRACKER ON EACH RUN #####
        window.lastProcessedHebrewYear = 0;

        if (window.cardInfoDateObserver) { window.cardInfoDateObserver.disconnect(); }

        convertDatesOnNode(document.body, inferredYear);
        _hafRenderHebrewStatsCalendar();

        const observer = new MutationObserver((mutationsList) => {
            // Reset the tracker before processing mutations to handle dynamic graph updates correctly
            window.lastProcessedHebrewYear = 0;
            for (const mutation of mutationsList) {
                if (mutation.type === 'childList') {
                    for (const node of mutation.addedNodes) {
                        convertDatesOnNode(node, inferredYear);
                    }
                }
                if (mutation.type === 'characterData') {
                    convertDatesOnNode(mutation.target, inferredYear);
                }
                if (mutation.type === 'attributes') {
                    convertDatesOnNode(mutation.target, inferredYear);
                }
            }
            _hafRenderHebrewStatsCalendar();
        });

        observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['title', 'data-original-title', 'aria-label'] });
        window.cardInfoDateObserver = observer;
    }

    // #250 — תוצאות הסטטיסטיקה נטענות באופן אסינכרוני; מריצים כמה פעימות קצרות אחרי ה-render של הגרפים וה-tooltip.
    [0, 250, 800, 1600, 3200].forEach(function(delay) { setTimeout(runConversion, delay); });
"""

# ======================================================================
#  2. Create the wrapper functions
# ======================================================================

def setup_ui_and_run_script_on_load(self: CardInfoDialog, card_id: CardId | None, _old) -> None:
    """
    Wraps _setup_ui to run the conversion script after the initial page load.
    """
    # First, run the original setup function
    _old(self, card_id)

    # Define a callback that will execute our JavaScript
    def on_load_finished(ok: bool):
        if ok:
            self.web.eval(HEBREW_DATE_CONVERSION_SCRIPT)

    # Connect our callback to the webview's loadFinished signal
    qconnect(self.web.loadFinished, on_load_finished)


def update_card_and_run_script(self: CardInfoDialog, card_id: CardId | None, _old) -> None:
    """
    Wraps update_card to run the conversion script on every subsequent card change.
    """
    # First, run the original update function
    _old(self, card_id)
    # Then, execute our script again to handle the new content
    self.web.eval(HEBREW_DATE_CONVERSION_SCRIPT)


# ======================================================================
#  3. Apply both wrappers to the CardInfoDialog class
# ======================================================================
CardInfoDialog._setup_ui = wrap(CardInfoDialog._setup_ui, setup_ui_and_run_script_on_load, "around")
CardInfoDialog.update_card = wrap(CardInfoDialog.update_card, update_card_and_run_script, "around")

# ======================================================================
#  4. Stats Window Hebrew Calendar - issue #250
# ======================================================================
from aqt import gui_hooks


def _inject_hebrew_in_stats_window(web):
    # #250 — המרת חודשים/שנים לועזיים לעברית בחלון הסטטיסטיקה של אנקי.
    # webview_did_inject_style_into_page נקרא לכל webview; בודקים אם ההורה הוא NewDeckStats.
    try:
        from aqt.stats import NewDeckStats
        parent = web.parentWidget()
        while parent is not None:
            if isinstance(parent, NewDeckStats):
                # מחברים ל-loadFinished פעם אחת בלבד כדי שהסקריפט ירוץ גם אחרי טעינת הגרפים
                if not getattr(web, "_haf_stats_hook_registered", False):
                    web._haf_stats_hook_registered = True
                    web.page().loadFinished.connect(
                        lambda ok, w=web: ok and w.eval(HEBREW_DATE_CONVERSION_SCRIPT)
                    )
                web.eval(HEBREW_DATE_CONVERSION_SCRIPT)
                return
            parent = parent.parentWidget() if callable(getattr(parent, "parentWidget", None)) else None
    except Exception:
        pass


gui_hooks.webview_did_inject_style_into_page.append(_inject_hebrew_in_stats_window)


# ======================================================================
#  4b. Stats Window Hebrew Calendar data bridge - issue #250
# ======================================================================
import json

from aqt.stats import NewDeckStats


def _stats_bridge_cmd(self, cmd: str, _old) -> bool:
    # #250 — הסקריפט המוזרק מבקש את ספירת החזרות היומית לכל ההיסטוריה כדי לצייר לוח שנה
    # עברי מלא (תשרי–אלול) שחוצה שתי שנים לועזיות — הרכיב המקורי מחזיק ב-DOM רק את השנה
    # הלועזית המוצגת. הנתונים נשלפים מאותו API שהדף עצמו משתמש בו (backend graphs), כך
    # שהמספרים זהים אחד לאחד ללוח המקורי, ומוחזרים ל-JS דרך eval.
    if isinstance(cmd, str) and cmd.startswith("hafHebCal:"):
        web = self.form.web
        if web is None:
            return False
        try:
            payload = json.loads(cmd[len("hafHebCal:"):] or "{}")
            search = payload.get("search") or ""
            # כמו במקור: הטווח מגיע מבורר "12 חודשים / כל ההיסטוריה" של הדף (365 / 0)
            days = payload.get("days")
            days = int(days) if isinstance(days, (int, float)) and days >= 0 else 365
            resp = self.mw.col._backend.graphs(search=search, days=days)
            counts = {}
            for day_offset, reviews in resp.reviews.count.items():
                total = reviews.learn + reviews.relearn + reviews.young + reviews.mature + reviews.filtered
                if total:
                    counts[int(day_offset)] = total
            data = {"counts": counts, "rolloverHour": resp.rollover_hour, "days": days}
        except Exception as exc:
            # חיפוש לא תקין שהמשתמש הקליד וכדומה — מדווחים ל-JS שישחזר את הלוח המקורי
            print(f"hebrew-date: hafHebCal failed: {exc}")
            data = {"error": str(exc)}
        web.eval(
            "window._hafHebCalReceive && window._hafHebCalReceive(%s);"
            % json.dumps(data, ensure_ascii=False)
        )
        return False
    return _old(self, cmd)


NewDeckStats._on_bridge_cmd = wrap(NewDeckStats._on_bridge_cmd, _stats_bridge_cmd, "around")


# #272 — raw string שומר על Regex ה-JS בלי אזהרות escape של Python.
HEBREW_DATE_DECK_OPTIONS_SCRIPT = r"""
(function() {
    if (window._hafHebrewDeckOptionsReady) return;
    window._hafHebrewDeckOptionsReady = true;

    var popup = null;
    var activeInput = null;
    var activeAnchor = null;

    var GEMATRIA = {1:"א",2:"ב",3:"ג",4:"ד",5:"ה",6:"ו",7:"ז",8:"ח",9:"ט",10:"י",20:"כ",30:"ל",40:"מ",50:"נ",60:"ס",70:"ע",80:"פ",90:"צ",100:"ק",200:"ר",300:"ש",400:"ת"};
    function numberToHebrew(num, thousands) {
        var n = parseInt(num, 10) || 0;
        var out = "";
        if (thousands && n >= 1000) {
            out += numberToHebrew(Math.floor(n / 1000), false) + "'";
            n = n % 1000;
        }
        while (n >= 400) { out += "ת"; n -= 400; }
        var hundreds = Math.floor(n / 100) * 100; n -= hundreds;
        var tens = Math.floor(n / 10) * 10; n -= tens;
        if (hundreds) out += GEMATRIA[hundreds] || "";
        if (tens === 10 && n === 5) return out + "טו";
        if (tens === 10 && n === 6) return out + "טז";
        if (tens) out += GEMATRIA[tens] || "";
        if (n) out += GEMATRIA[n] || "";
        return out;
    }

    function parseIso(value) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) return null;
        var parts = value.split("-").map(function(p) { return parseInt(p, 10); });
        var date = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
        return isNaN(date.getTime()) ? null : date;
    }

    function isoFromDate(date) {
        return date.toISOString().slice(0, 10);
    }

    function addDays(date, days) {
        var d = new Date(date.getTime());
        d.setUTCDate(d.getUTCDate() + days);
        return d;
    }

    function hebrewParts(date) {
        var parts = new Intl.DateTimeFormat("he-u-ca-hebrew", {
            timeZone: "UTC",
            year: "numeric",
            month: "long",
            day: "numeric"
        }).formatToParts(date);
        var day = parts.find(function(p) { return p.type === "day"; });
        var month = parts.find(function(p) { return p.type === "month"; });
        var year = parts.find(function(p) { return p.type === "year"; });
        if (!day || !month || !year) return null;
        return { day: parseInt(day.value, 10), month: month.value, year: parseInt(year.value, 10) };
    }

    function toHebrewDate(dateStr) {
        try {
            var date = parseIso(dateStr);
            var parts = date ? hebrewParts(date) : null;
            if (!parts) return "";
            return numberToHebrew(parts.day, false) + " " + parts.month + " " + numberToHebrew(parts.year, true);
        } catch (err) {
            return "";
        }
    }

    function sameHebrewMonth(a, b) {
        return a && b && a.year === b.year && a.month === b.month;
    }

    function monthDates(anchor) {
        var target = hebrewParts(anchor);
        var dates = [];
        for (var offset = -45; offset <= 45; offset++) {
            var d = addDays(anchor, offset);
            if (sameHebrewMonth(hebrewParts(d), target)) dates.push(d);
        }
        dates.sort(function(a, b) { return a - b; });
        return dates;
    }

    function setInputDate(input, iso) {
        input.value = iso || "";
        input.setAttribute("value", iso || "");
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
        annotateInput(input);
    }

    function closePopup() {
        if (popup) popup.remove();
        popup = null;
        activeInput = null;
    }

    function renderPopup(input, anchor) {
        closePopup();
        activeInput = input;
        activeAnchor = anchor || parseIso(input.value) || new Date();
        activeAnchor = new Date(Date.UTC(activeAnchor.getUTCFullYear(), activeAnchor.getUTCMonth(), activeAnchor.getUTCDate()));
        var dates = monthDates(activeAnchor);
        var headerParts = hebrewParts(activeAnchor);
        popup = document.createElement("div");
        popup.className = "haf-hebrew-datepicker";
        popup.dir = "rtl";
        var first = dates[0] || activeAnchor;
        var selectedIso = input.value || "";
        var todayIso = isoFromDate(new Date());
        var firstWeekday = first.getUTCDay();
        var cells = "";
        for (var i = 0; i < firstWeekday; i++) cells += '<span class="haf-hdp-empty"></span>';
        dates.forEach(function(d) {
            var iso = isoFromDate(d);
            var hp = hebrewParts(d);
            var cls = "haf-hdp-day" + (iso === selectedIso ? " is-selected" : "") + (iso === todayIso ? " is-today" : "");
            cells += '<button type="button" class="' + cls + '" data-date="' + iso + '">' + numberToHebrew(hp.day, false) + '</button>';
        });
        popup.innerHTML =
            '<div class="haf-hdp-head">' +
              '<button type="button" data-nav="prev" title="פריערדיגער חודש">‹</button>' +
              '<strong>' + headerParts.month + ' ' + numberToHebrew(headerParts.year, true) + '</strong>' +
              '<button type="button" data-nav="next" title="קומענדיגער חודש">›</button>' +
            '</div>' +
            '<div class="haf-hdp-week"><span>א</span><span>ב</span><span>ג</span><span>ד</span><span>ה</span><span>און</span><span>ש</span></div>' +
            '<div class="haf-hdp-grid">' + cells + '</div>' +
            '<div class="haf-hdp-actions"><button type="button" data-action="clear">אויסליידיגן</button><button type="button" data-action="today">היינט</button></div>';
        document.body.appendChild(popup);
        var rect = input.getBoundingClientRect();
        popup.style.top = Math.min(rect.bottom + 4, window.innerHeight - popup.offsetHeight - 8) + "px";
        popup.style.left = Math.max(8, Math.min(rect.left, window.innerWidth - popup.offsetWidth - 8)) + "px";
    }

    function openPicker(input) {
        annotateInput(input);
        renderPopup(input, parseIso(input.value) || new Date());
    }

    function annotateInput(input) {
        var value = input.value || input.getAttribute("value") || "";
        var hebrew = toHebrewDate(value);
        var parent = input.parentElement;
        var label = parent && parent.querySelector(".haf-hebrew-fsrs-date");
        try { if (input.type === "date") input.type = "text"; } catch (err) {}
        input.setAttribute("autocomplete", "off");
        input.setAttribute("inputmode", "none");
        input.classList.add("haf-hebrew-date-input");
        if (!hebrew) {
            if (label) label.textContent = "";
            return;
        }
        if (!label) {
            label = document.createElement("span");
            label.className = "haf-hebrew-fsrs-date";
            label.style.cssText = "position:absolute;inset-inline-end:32px;top:50%;transform:translateY(-50%);font-size:12px;opacity:.86;direction:rtl;white-space:nowrap;color:inherit;pointer-events:none;max-width:58%;overflow:hidden;text-overflow:ellipsis;";
            if (parent) {
                parent.style.position = parent.style.position || "relative";
                parent.appendChild(label);
            } else {
                input.insertAdjacentElement("afterend", label);
            }
        }
        label.textContent = hebrew;
        input.style.color = "transparent";
        input.style.caretColor = "initial";
        if (hebrew) input.setAttribute("title", value + " / " + hebrew);
    }

    function bindInput(input) {
        if (input._hafHebrewDateBound) return;
        input._hafHebrewDateBound = true;
        input.addEventListener("click", function(event) { event.preventDefault(); openPicker(input); }, true);
        input.addEventListener("focus", function() { openPicker(input); }, true);
        input.addEventListener("keydown", function(event) {
            if (event.key === "Escape") { closePopup(); input.blur(); return; }
            if (event.key === "Backspace" || event.key === "Delete") { event.preventDefault(); setInputDate(input, ""); closePopup(); return; }
            if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openPicker(input); return; }
            event.preventDefault();
        }, true);
    }

    function annotateDates() {
        document.querySelectorAll('input[type="date"], input').forEach(function(input) {
            var value = input.value || input.getAttribute("value") || "";
            if (input.type === "date" || /^\d{4}-\d{2}-\d{2}$/.test(value)) {
                bindInput(input);
                annotateInput(input);
            }
        });
    }

    document.addEventListener("input", function(event) {
        if (event.target && event.target.tagName === "INPUT") annotateInput(event.target);
    }, true);

    document.addEventListener("mousedown", function(event) {
        if (!popup) return;
        if (popup.contains(event.target) || event.target === activeInput) return;
        closePopup();
    }, true);

    document.addEventListener("click", function(event) {
        if (!popup || !activeInput) return;
        var day = event.target.closest && event.target.closest(".haf-hdp-day");
        if (day) {
            setInputDate(activeInput, day.getAttribute("data-date") || "");
            closePopup();
            return;
        }
        var nav = event.target.closest && event.target.closest("[data-nav]");
        if (nav) {
            var dates = monthDates(activeAnchor || new Date());
            var base = dates.length ? dates[0] : activeAnchor;
            var dir = nav.getAttribute("data-nav") === "next" ? 35 : -35;
            renderPopup(activeInput, addDays(base, dir));
            return;
        }
        var action = event.target.closest && event.target.closest("[data-action]");
        if (action && action.getAttribute("data-action") === "clear") { setInputDate(activeInput, ""); closePopup(); return; }
        if (action && action.getAttribute("data-action") === "today") { setInputDate(activeInput, isoFromDate(new Date())); closePopup(); }
    }, true);

    var style = document.createElement("style");
    style.textContent = "\
    .haf-hebrew-date-input{cursor:pointer!important;}\
    .haf-hebrew-datepicker{position:fixed;z-index:2147483647;width:246px;background:#fff;color:#1f2933;border:1px solid #b8c0cc;border-radius:6px;box-shadow:0 10px 24px rgba(0,0,0,.22);padding:8px;font-family:system-ui,Segoe UI,sans-serif;font-size:13px;}\
    .haf-hdp-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;}\
    .haf-hdp-head button,.haf-hdp-actions button{border:0;background:#f3f6fb;border-radius:4px;padding:4px 8px;cursor:pointer;}\
    .haf-hdp-week,.haf-hdp-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:3px;text-align:center;}\
    .haf-hdp-week{color:#5d6673;font-weight:600;margin-bottom:4px;}\
    .haf-hdp-day{height:28px;border:1px solid transparent;background:transparent;border-radius:4px;cursor:pointer;}\
    .haf-hdp-day:hover{background:#eaf2ff;}\
    .haf-hdp-day.is-selected{background:#1769e0;color:#fff;}\
    .haf-hdp-day.is-today{border-color:#1769e0;}\
    .haf-hdp-actions{display:flex;justify-content:space-between;margin-top:8px;}\
    ";
    document.head.appendChild(style);

    annotateDates();
    var observer = new MutationObserver(annotateDates);
    observer.observe(document.body, { childList: true, subtree: true });
})();
"""


def _inject_hebrew_in_deck_options(dialog) -> None:
    # #272 — בשדה FSRS "Ignore reviews before" מציגים תאריך עברי ליד הערך בלי לשנות את הערך הגרגוריאני שנשמר.
    try:
        dialog.web.eval(HEBREW_DATE_DECK_OPTIONS_SCRIPT)
    except Exception:
        pass


gui_hooks.deck_options_did_load.append(_inject_hebrew_in_deck_options)
