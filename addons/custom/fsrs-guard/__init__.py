"""א וועגווייזער און בדיקה FSRS פאר דער אנקי אויסגאבע."""

from __future__ import annotations

import hashlib
import html
import json
import re
import time
from datetime import date
from pathlib import Path

from aqt import gui_hooks, mw
from aqt.operations import CollectionOp, QueryOp
from aqt.qt import (
    QAction,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    Qt,
    QTimer,
    QVBoxLayout,
)
from aqt.utils import qconnect, showInfo, tooltip

from _shared_libs.haf_logging import get_logger
from _shared_libs.haf_notifications import show_failure, warn_once

logger = get_logger("fsrs_guide")

_PM_KEY_WELCOME = "fsrs_guide.welcome_shown"
_PM_KEY_EVER_ENABLED = "fsrs_guide.ever_enabled"
_PM_KEY_PROFILE_OPENS = "fsrs_guide.profile_open_count"
_PM_KEY_LAST_OPTIMIZE = "fsrs_guide.last_monthly_optimize"
_PM_KEY_UPDATE_CHECK = "fsrs_guide.update_check_schedule"
_PM_KEY_LAST_EVENT_CHECK = "fsrs_guide.last_event_check_signature"
_PM_KEY_LAST_FSRS_SETTINGS_STATE = "fsrs_guide.last_fsrs_settings_state"
_PM_KEY_FUTURE_DUE_PROMPTED = "fsrs_guide.future_due_prompted_date"
_PM_KEY_FUTURE_DUE_APPLIED = "fsrs_guide.future_due_ignore_applied_date"
_PM_KEY_LAST_CARD_COUNT = "fsrs_guide.last_card_count"
_PM_KEY_LAST_MAX_CARD_ID = "fsrs_guide.last_max_card_id"

_FSRS_MONTH_SECS = 30 * 24 * 60 * 60
_FSRS_WEEK_SECS = 7 * 24 * 60 * 60
_LARGE_IMPORT_THRESHOLD = 250
_MAX_PREVIEW_ROWS = 500
_RATIO_LIMIT = 5.0
_MIN_FSRS_DAYS = 365
_FIX_MENU_LABEL = "פאררעכטונג פון די מרווחים פון FSRS"
_monthly_optimize_running = False

_FSRS_TIPS_HTML = """
<div dir='rtl' style='line-height:1.6'>
<h3 style='margin-top:0'>ווי צו נוצן-FSRS ריכטיג</h3>

<p>
FSRS איז אן אלגאריטם וואס רעכנט אויס פאר אייך <b>די גענויעסטע צייט</b> צו חזרן יעדע קארטל —
ווען דער שאנס צו פארגעסן איז פונקט ווי איר האט באשטימט (ברירת מחדל: 10%).
ער לערנט זיך אייער <i>פערזענליכן זכרון מוסטער</i> און ווערט בעסער וואס מער איר נוצט אים.
</p>

<hr/>

<p><b>⚠ דער וויכטיגסטער כלל</b></p>
<p>
דריקט <b>"נאכאמאל"</b> ווען איר פארגעסט — אפילו אויב איר האט נאר פארגעסן א חלק פון דער ענטפער.<br/>
<b>דריקט נישט "שווער" אנשטאט "נאכאמאל"</b> ווען איר האט נישט געוואוסט די ענטפער.
</p>
<p>
ווען איר דריקט "שווער", FSRS מיינט ער אז איר האט געדענקט — אבער מיט א צווייפל.
אויב איר האט געדריקט "שווער" אויף א קארטל וואס איר האט נישט געקענט, וועט דער אלגאריטם פארדרייען אלע
זיינע מרווח חשבונות פאר דעם קארטל — זיי וועלן בלייבן צו גרויס.
</p>

<hr/>

<p><b>📅 ארבעט מיטן צייטפלאן — אויך ווען ער זעט אויס איבערגעטריבן</b></p>
<p>
אויב דער אלגאריטם ווייזט אייך א קארטל נאך 30 טעג, איז דאס נישט קיין טעות.
דאס איז אויסגערעכנט: פונקט ווען דער שאנס צו פארגעסן דערגרייכט אייער באשטימטן שוועל.
</p>
<p>
אויב דאס זעט אייך אויס איבערגעטריבן — <b>איז דאס א גוטער סימן</b>. אייער מח האט שטארק געדענקט,
דערפאר פארגרעסערט דער אלגאריטם דעם מרווח. שטופט נישט דעם קארטל
צו אן פריערדיגער חזרה — דאס שאדט די עפעקטיווקייט.
</p>

<hr/>

<p><b>🔁 אויב איר האט פארגעסן — דריקט "נאכאמאל" אן זיך צו שעמען</b></p>
<p>
פארגעסן איז <b>א חלק פונעם פראצעס</b>, קיין דורכפאל.
א דרוק אויף "נאכאמאל" נישט "באשטראפט" אייך — עס לערנט דעם אלגאריטם
צו פארקלענערן דעם מרווח פאר דעם קארטל, כדי ער זאל פריער צוריקקומען
און פארשטארקן דעם זכרון.
</p>

<hr/>

<p><b>✅ נאך א פאר כללים</b></p>
<ul>
<li>חזרט קארטלעך <b>יעדן טאג</b>, אפילו ווייניג — לאזט נישט די חזרות זיך אנזאמלען.</li>
<li>נוצט"שווער" נאר ווען איר האט געדענקט מיט גרויס שוועריקייט — נישט ווען איר האט נישט געוואוסט.</li>
<li>נוצט"גרינג" נאר ווען דער קארטל איז אייך <i>זייער גרינג</i> — אנדערש "גוט" איז בעסער.</li>
<li>דער אלגאריטם ווערט בעסער מיט דער צייט — גיט אים א פאר וואכן זיך צוצופאסן.</li>
</ul>

</div>
""".strip()


class _FsrsTipsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("ריכטיג נוצן פון-FSRS")
        self.setMinimumSize(520, 480)
        self.resize(560, 540)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 12)
        root.setSpacing(0)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setReadOnly(True)
        browser.setHtml(_FSRS_TIPS_HTML)
        browser.document().setDocumentMargin(16)
        root.addWidget(browser)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(16, 0, 16, 0)
        btn_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        close_btn = QPushButton("פארמאכן")
        close_btn.setDefault(True)
        close_btn.setFixedWidth(90)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)


def show_fsrs_tips() -> None:
    _FsrsTipsDialog(mw).exec()


def _is_fsrs_enabled() -> bool:
    return mw.col is not None and bool(mw.col.get_config("fsrs", False))


def _schedule_collection_callback(delay: int, callback) -> None:
    """Discard delayed work when its collection has closed or been replaced."""
    collection = mw.col
    if collection is None:
        return

    def run() -> None:
        if mw.col is collection:
            callback()

    QTimer.singleShot(delay, run)


def _fsrs_settings_signature() -> str:
    """ברענגט צוריק א פעסטע חתימה נאר פון די איינשטעלונגען פון FSRS וואס האבן אן השפעה אויפן צייטפלאן."""
    state = mw.col.decks.get_deck_configs_for_update(1)
    parts: list[object] = [bool(state.fsrs)]
    for entry in state.all_config:
        config = entry.config
        inner = config.config
        parts.append(
            (
                int(config.id),
                float(getattr(inner, "desired_retention", 0.0) or 0.0),
                float(getattr(inner, "historical_retention", 0.0) or 0.0),
                str(getattr(inner, "ignore_revlogs_before_date", "") or ""),
                tuple(float(v) for v in (getattr(inner, "fsrs_params_5", []) or [])),
                tuple(float(v) for v in (getattr(inner, "fsrs_params_6", []) or [])),
            )
        )
    raw = repr(tuple(parts)).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _apply_fsrs(enable: bool, show_tips_after: bool = False) -> None:
    collection = mw.col

    def op(col):
        return col.set_config("fsrs", enable)

    def on_success(_) -> None:
        if collection is None or mw.col is not collection:
            return
        if enable:
            try:
                mw.pm.profile[_PM_KEY_EVER_ENABLED] = True
                mw.pm.save()
            except Exception:
                pass
            tooltip('<div dir="rtl">FSRS איז איינגעשאלטן געווארן ✓</div>')
            if show_tips_after:
                show_fsrs_tips()
            if mw.col is not collection:
                return
            # אישיו #411: שינוי מצב FSRS הוא אירוע עצמאי ואינו נחסם בגלל בדיקה יומית קודמת.
            _schedule_collection_callback(
                800,
                lambda: _run_check(
                    manual=False,
                    trigger="fsrs_settings",
                    trigger_token=_fsrs_settings_signature(),
                ),
            )
        else:
            tooltip('<div dir="rtl">FSRS איז אויסגעשאלטן געווארן — צוריק צו-SM-2.</div>')

    CollectionOp(mw, op).success(on_success).run_in_background()


class _SchedulerDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("שיטה פארן קארטל צייטפלאן")
        self.setMinimumWidth(460)
        self.setMaximumWidth(520)
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)
        title = QLabel("שיטה פארן קארטל צייטפלאן")
        title.setStyleSheet("font-size:13px; font-weight:bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(title)
        explain = QLabel(
            "<div dir='rtl' style='line-height:1.7'>"
            "Anki האט צוויי שיטות אויסצורעכענען די חזרה צייט פאר קארטלעך:<br><br>"
            "<b>SM-2</b> - דער קלאסישער אלגאריטם. ניצט פעסטע פאקטארן. די ברירת מחדל.<br>"
            "<b>FSRS</b> - אן אלגאריטם באזירט אויף פארשונג. לערנט זיך אייער פערזענליכן זכרון מוסטער "
            "און פאסט די מרווחים צו. <span style='color:#1a6b1a'>ראטזאם.</span><br><br>"
            "<span style='color:#555; font-size:10px'>"
            "דער שיטה טויש גייט אן אויף אלע פעקלעך אין דער זאמלונג. מען קען עס טוישן ווען מען וויל."
            "</span>"
            "</div>"
        )
        explain.setWordWrap(True)
        explain.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(explain)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame { color: #cccccc; }")
        root.addWidget(sep)

        is_on = _is_fsrs_enabled()
        state_text = "FSRS איינגעשאלטן" if is_on else "SM-2 איינגעשאלטן (ברירת מחדל)"
        state_lbl = QLabel(f"<div dir='rtl'>יעצטיגער מצב: <b>{state_text}</b></div>")
        state_lbl.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(state_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        if not is_on:
            stay_btn = QPushButton("לאז SM-2")
            qconnect(stay_btn.clicked, self.accept)
            btn_row.addWidget(stay_btn)

            enable_btn = QPushButton("גיי צו-FSRS")
            enable_btn.setDefault(True)
            qconnect(enable_btn.clicked, self._on_enable)
            btn_row.addWidget(enable_btn)
        else:
            disable_btn = QPushButton("גיי צוריק צו-SM-2")
            qconnect(disable_btn.clicked, self._on_disable)
            btn_row.addWidget(disable_btn)

            close_btn = QPushButton("פארמאכן")
            close_btn.setDefault(True)
            qconnect(close_btn.clicked, self.accept)
            btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

        hint_sep = QFrame()
        hint_sep.setFrameShape(QFrame.Shape.HLine)
        hint_sep.setStyleSheet("QFrame { color: #dddddd; margin-top: 4px; }")
        root.addWidget(hint_sep)

        hint_lbl = QLabel(
            "<div dir='rtl' style='color:#777; font-size:10px'>"
            "מען קען עס טוישן ווען מען וויל דורך: <b>זאמלונג כלים — צייטפלאן שיטה</b>"
            "</div>"
        )
        hint_lbl.setTextFormat(Qt.TextFormat.RichText)
        hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(hint_lbl)

    def _on_enable(self) -> None:
        self.accept()
        _apply_fsrs(True, show_tips_after=True)

    def _on_disable(self) -> None:
        self.accept()
        _apply_fsrs(False)


def _show_welcome_if_needed() -> None:
    # אישיו #144: בפרופיל חדש וריק לא פותחים מיד חלון בחירה.
    try:
        if mw.pm.profile.get(_PM_KEY_WELCOME, False):
            return
        opens = int(mw.pm.profile.get(_PM_KEY_PROFILE_OPENS, 0) or 0) + 1
        mw.pm.profile[_PM_KEY_PROFILE_OPENS] = opens
        count = int(mw.col.db.scalar("SELECT count() FROM cards") or 0)
        if opens < 2 and count == 0:
            mw.pm.save()
            return
        mw.pm.profile[_PM_KEY_WELCOME] = True
        mw.pm.save()
    except Exception:
        return
    _SchedulerDialog(mw).exec()


# אישיו #145: סטטוס האופטימיזציה החודשית נשמר לכל קבוצת הגדרות.
def _get_addon_config() -> dict:
    addon_name = mw.addonManager.addonFromModule(__name__)
    conf = mw.addonManager.getConfig(addon_name)
    if not isinstance(conf, dict):
        conf = {}
    conf.setdefault("monthly_optimize_presets", {})
    return conf


def _write_addon_config(conf: dict) -> None:
    addon_name = mw.addonManager.addonFromModule(__name__)
    mw.addonManager.writeConfig(addon_name, conf)


def _set_monthly_optimize_status(conf_id, enabled: bool) -> None:
    conf = _get_addon_config()
    conf["monthly_optimize_presets"][str(conf_id)] = enabled
    _write_addon_config(conf)


def _get_monthly_optimize_status(conf_id) -> bool:
    return bool(_get_addon_config()["monthly_optimize_presets"].get(str(conf_id), True))


def _monthly_optimization_is_due(now: int, last: int) -> bool:
    return last <= 0 or now < last or now - last >= _FSRS_MONTH_SECS


# אישיו #145: אופטימיזציה אוטומטית אינה רצה יותר מפעם בחודש.
def _run_fsrs_parameter_optimization(*, manual: bool = False) -> None:
    global _monthly_optimize_running
    collection = mw.col
    if not _is_fsrs_enabled():
        if manual:
            tooltip("FSRS איז נישט איינגעשאלטן")
        return
    if _monthly_optimize_running:
        if manual:
            tooltip("אפשטימונג פון FSRS לויפט שוין")
        return
    now = int(time.time())
    last = int(mw.pm.profile.get(_PM_KEY_LAST_OPTIMIZE, 0) or 0)
    if not manual and not _monthly_optimization_is_due(now, last):
        return
    disabled = {
        str(conf_id)
        for conf_id, enabled in _get_addon_config()["monthly_optimize_presets"].items()
        if not enabled
    }
    _monthly_optimize_running = True
    count = [0]

    def op(col):
        from anki import deck_config_pb2

        state = col.decks.get_deck_configs_for_update(1)
        configs = [
            entry.config
            for entry in state.all_config
            if manual or str(entry.config.id) not in disabled
        ]
        if not configs:
            return None
        mode = deck_config_pb2.UpdateDeckConfigsMode.Value(
            "UPDATE_DECK_CONFIGS_MODE_COMPUTE_ALL_PARAMS"
        )
        request = deck_config_pb2.UpdateDeckConfigsRequest(
            target_deck_id=1,
            configs=configs,
            removed_config_ids=[],
            mode=mode,
            card_state_customizer=state.card_state_customizer,
            limits=state.current_deck.limits,
            new_cards_ignore_review_limit=state.new_cards_ignore_review_limit,
            fsrs=True,
            apply_all_parent_limits=state.apply_all_parent_limits,
            fsrs_reschedule=False,
            fsrs_health_check=state.fsrs_health_check,
        )
        count[0] = len(configs)
        return col.decks.update_deck_configs(request)

    def success(_) -> None:
        global _monthly_optimize_running
        _monthly_optimize_running = False
        if collection is None or mw.col is not collection:
            return
        mw.pm.profile[_PM_KEY_LAST_OPTIMIZE] = now
        mw.pm.save()
        if manual:
            tooltip(f"פאראמעטערן פון FSRS זענען דערהיינטיגט געווארן אין{count[0]} גרופעס איינשטעלונגען")
        # אישיו #411: אופטימיזציה משנה בפועל פרמטרי FSRS ולכן נבדקת גם אם
        # כבר בוצעה היום בדיקה לאחר עדכון. חתימת ההגדרות מונעת בדיקה כפולה.
        _schedule_collection_callback(
            700,
            lambda: _run_check(
                manual=False,
                trigger="fsrs_settings",
                trigger_token=_fsrs_settings_signature(),
            ),
        )

    def failure(exc: Exception) -> None:
        global _monthly_optimize_running
        _monthly_optimize_running = False
        logger.warning("אפשטימונג פון FSRS איז נישט געלונגען: %s", exc)
        if manual:
            tooltip("אפשטימונג פון FSRS איז נישט פארענדיגט געווארן")

    CollectionOp(parent=mw, op=op).success(success).failure(failure).run_in_background()


def _optimize_fsrs_monthly_if_due() -> None:
    _run_fsrs_parameter_optimization(manual=False)


def _optimize_all_fsrs_presets_now() -> None:
    _run_fsrs_parameter_optimization(manual=True)


def _review_days(state) -> int:
    if state.HasField("normal") and state.normal.HasField("review"):
        return int(state.normal.review.scheduled_days)
    return 0


def _rating_days(states) -> dict[str, int]:
    return {
        "hard": _review_days(states.hard),
        "good": _review_days(states.good),
        "easy": _review_days(states.easy),
    }


def _plain_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _problem_rows(col, min_card_id: int = 0) -> list[dict[str, object]]:
    # אישיו #411: FSRS ו-V3 מחושבים לאותו כרטיס דרך אותו SchedulingStates של Anki.
    if min_card_id > 0:
        cards = col.db.all(
            "SELECT id, nid, ivl FROM cards WHERE queue = 2 AND id > ? ORDER BY ivl DESC",
            int(min_card_id),
        )
    else:
        cards = col.db.all(
            "SELECT id, nid, ivl FROM cards WHERE queue = 2 ORDER BY ivl DESC"
        )
    if not cards:
        return []

    fsrs: dict[int, dict[str, int]] = {}
    for cid, _nid, _ivl in cards:
        fsrs[int(cid)] = _rating_days(col._backend.get_scheduling_states(int(cid)))

    # אישיו #411: מכבים FSRS זמנית רק לצורך חישוב V3 ומחזירים תמיד את המצב המקורי.
    v3: dict[int, dict[str, int]] = {}
    previous_fsrs = bool(col.get_config("fsrs", False))
    col.set_config("fsrs", False)
    try:
        for cid, _nid, _ivl in cards:
            v3[int(cid)] = _rating_days(col._backend.get_scheduling_states(int(cid)))
    finally:
        col.set_config("fsrs", previous_fsrs)

    labels = {"hard": "שווער", "good": "גוט", "easy": "גרינג"}
    result: list[dict[str, object]] = []
    for cid, nid, current_ivl in cards:
        cid = int(cid)
        current_ivl = int(current_ivl or 0)
        reasons: list[tuple[float, str]] = []
        for rating in ("hard", "good", "easy"):
            f_days = int(fsrs[cid][rating] or 0)
            v_days = int(v3[cid][rating] or 0)
            if f_days <= 0:
                continue
            ratio = f_days / max(v_days, 1)
            # אישיו #411: סף פי 5 תופס 42 שנה מול 4–5 שנים, שהסף הישן פי 10 פספס.
            if v_days > 0 and f_days >= _MIN_FSRS_DAYS and ratio >= _RATIO_LIMIT:
                reasons.append(
                    (ratio, f"{labels[rating]}: FSRS {f_days} טעג קעגן V3 {v_days} טעג (פי {ratio:.1f})")
                )
            # אישיו #411: החריגה נקבעת מול V3 בלבד; אין תקרת שנים מלאכותית ואין
            # השוואה למרווח הנוכחי, כדי שמצב שכבר תוקן לא יסומן שוב רק בגלל אורך מוחלט.
        if not reasons:
            continue
        reasons.sort(key=lambda item: item[0], reverse=True)
        question = ""
        note = col.get_note(int(nid))
        if note.fields:
            question = _plain_text(note.fields[0])[:140]
        result.append(
            {
                "cid": cid,
                "question": question,
                "current": current_ivl,
                "fsrs_hard": fsrs[cid]["hard"],
                "v3_hard": v3[cid]["hard"],
                "fsrs_good": fsrs[cid]["good"],
                "v3_good": v3[cid]["good"],
                "reason": reasons[0][1],
            }
        )
        if len(result) >= _MAX_PREVIEW_ROWS:
            break
    return result


class _PreviewDialog(QDialog):
    def __init__(
        self,
        rows: list[dict[str, object]],
        parent=None,
        *,
        allow_return_to_fix: bool = False,
    ):
        super().__init__(parent)
        self.return_to_fix = False
        self.setWindowTitle("קארטלעך מיט א צייטפלאן FSRS אויסערגעווענליך")
        self.resize(1050, 580)
        root = QVBoxLayout(self)

        # אישיו #420: אין בטבלה טקסט פנימי על מספרי אישיו; המשתמש רואה רק את הנתונים עצמם.
        table = QTableWidget(len(rows), 8, self)
        table.setHorizontalHeaderLabels(
            [
                "קארטל", "פראגע", "יעצטיגער מרווח", "FSRS שווער", "V3 שווער",
                "FSRS גוט", "V3 גוט", "סיבה פארן דערקענען",
            ]
        )
        for row_index, row in enumerate(rows):
            values = [
                str(row["cid"]),
                str(row["question"]),
                f"{row['current']} טעג",
                f"{row['fsrs_hard']} טעג" if int(row["fsrs_hard"] or 0) else "—",
                f"{row['v3_hard']} טעג" if int(row["v3_hard"] or 0) else "—",
                f"{row['fsrs_good']} טעג" if int(row["fsrs_good"] or 0) else "—",
                f"{row['v3_good']} טעג" if int(row["v3_good"] or 0) else "—",
                str(row["reason"]),
            ]
            for column, value in enumerate(values):
                table.setItem(row_index, column, QTableWidgetItem(value))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = table.horizontalHeader()
        for column in (0, 2, 3, 4, 5, 6):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        root.addWidget(table)

        buttons = QHBoxLayout()
        buttons.addStretch()
        if allow_return_to_fix:
            back = QPushButton("גיי צוריק צום פאררעכטונג פענסטער")
            back.clicked.connect(self._return_to_fix)
            buttons.addWidget(back)
        close = QPushButton("פארמאכן")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)

    def _return_to_fix(self) -> None:
        # אישיו #420: חוזרים לאותו דיאלוג תיקון בלי לחשב מחדש את הטבלה.
        self.return_to_fix = True
        self.accept()


def _retention_is_low(col) -> bool:
    state = col.decks.get_deck_configs_for_update(1)
    for entry in state.all_config:
        value = float(getattr(entry.config.config, "desired_retention", 0.9) or 0.9)
        if value < 0.90:
            return True
    return False


def _show_problem_prompt(rows: list[dict[str, object]], low_retention: bool) -> None:
    # אישיו #411: לעולם לא מציגים התראת 90% אם אין כרטיס חריג בפועל.
    if not rows:
        return
    today_iso = date.today().isoformat()
    mw.pm.profile[_PM_KEY_FUTURE_DUE_PROMPTED] = today_iso
    mw.pm.save()

    # אישיו #447: ההודעה היא המסך הראשי של הזרימה. הטבלה נפתחת רק מהכפתור,
    # וכל סגירה של הטבלה חוזרת לאותה הודעה במקום לסגור את שתי השכבות יחד.
    while True:
        box = QMessageBox(mw)
        box.setWindowTitle("פאררעכטונג פון די צייטפלאנען פון FSRS")
        box.setIcon(QMessageBox.Icon.Warning)
        text = f"מען האט געפונען {len(rows)} קארטלעך מיט א צייטפלאן FSRS אויסערגעווענליך."
        if low_retention:
            text += " דערצו איז דער געוואונטשענער געדענק פראצענט אונטער90%."
        box.setText(text)
        box.setInformativeText(
            "מען קען זען דעם פארגלייך FSRS/V3 פאר דער פאררעכטונג. די פאררעכטונג שטעלט צוריק דעם אנהייב פון "
            "אויסרעכענען FSRS צו היינט, שטעלט צוריק די פאראמעטערן פון FSRS צו די ברירת מחדל ווערטן, שטעלט דעם "
            "היסטארישן געדענק פראצענט צו 90% און מאכט א נייעם צייטפלאן דורך Anki."
        )
        preview = box.addButton("ווייז טאבעלע", QMessageBox.ButtonRole.ActionRole)
        fix = box.addButton("פאררעכט יעצט", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("נישט יעצט", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is preview:
            _PreviewDialog(rows, mw, allow_return_to_fix=True).exec()
            continue
        if clicked is fix:
            _reset_fsrs_from_today(reset_retention=low_retention)
        return


def _reset_fsrs_from_today(reset_retention: bool = False) -> None:
    today_iso = date.today().isoformat()
    backup_folder = mw.pm.backupFolder()

    def op(col):
        from anki import deck_config_pb2

        # Wait for the backup before any scheduling change, inside the operation.
        col.create_backup(backup_folder=backup_folder, force=True, wait_for_completion=True)
        state = col.decks.get_deck_configs_for_update(1)
        configs = []
        for entry in state.all_config:
            config = entry.config
            # אישיו #411: מאגר 011 הראה ש-95% שימור היסטורי מנפח המרת SM-2 ל-FSRS.
            # באיפוס מהיום מכוונים אותו ל-90%, כך שהיציבות ההתחלתית נשארת קרובה
            # למרווח SM-2 הקיים במקום לקפוץ לשנים רבות מעבר לערך של V3.
            config.config.ignore_revlogs_before_date = today_iso
            config.config.historical_retention = 0.90

            # אישיו #411: מאפסים את שתי משפחות הפרמטרים. ב-011 נשארו משקלי FSRS5
            # מותאמים לצד ברירות המחדל של FSRS6, ולכן איפוס חלקי לא היה דטרמיניסטי.
            for field_name in ("fsrs_params_5", "fsrs_params_6"):
                current = getattr(config.config, field_name, None)
                defaults = getattr(state.defaults.config, field_name, None)
                if current is None or defaults is None:
                    continue
                del current[:]
                current.extend(defaults)

            if reset_retention:
                if float(config.config.desired_retention or 0.9) < 0.90:
                    config.config.desired_retention = 0.90
            configs.append(config)
        mode = deck_config_pb2.UpdateDeckConfigsMode.Value("UPDATE_DECK_CONFIGS_MODE_NORMAL")
        request = deck_config_pb2.UpdateDeckConfigsRequest(
            target_deck_id=1,
            configs=configs,
            removed_config_ids=[],
            mode=mode,
            card_state_customizer=state.card_state_customizer,
            limits=state.current_deck.limits,
            new_cards_ignore_review_limit=state.new_cards_ignore_review_limit,
            fsrs=True,
            apply_all_parent_limits=state.apply_all_parent_limits,
            fsrs_reschedule=True,
            fsrs_health_check=state.fsrs_health_check,
        )
        return col.decks.update_deck_configs(request)

    def success(_) -> None:
        mw.pm.profile[_PM_KEY_FUTURE_DUE_APPLIED] = today_iso
        mw.pm.save()

        # אישיו #411: הצלחת פעולת התיקון אינה נחשבת הצלחה לוגית עד שאותה בדיקת FSRS/V3 עוברת שוב.
        def verified(rows: list[dict[str, object]]) -> None:
            if not rows:
                showInfo(
                    "פאררעכטונג FSRS איז פארענדיגט און באשטעטיגט געווארן מיט דער זעלבער בדיקה פון FSRS/V3: "
                    "קיין קארטלעך זענען נישט געבליבן איבערן בדיקה שוועל."
                )
            else:
                showInfo(
                    f"די פאררעכטונג איז געמאכט געווארן, אבער ביים נאכקוקן זענען געבליבן {len(rows)} אויסערגעווענליכע קארטלעך. "
                    "איך וועל נישט באצייכענען די פאררעכטונג אלס אינגאנצן געלונגען. די טאבעלע וועט יעצט געוויזן ווערן."
                )
                _PreviewDialog(rows, mw).exec()

        QueryOp(parent=mw, op=_problem_rows, success=verified).run_in_background()

    def failure(exc: Exception) -> None:
        logger.warning("צוריקשטעלן FSRS איז נישט געלונגען: %s", exc)
        showInfo("איך האב נישט געקענט פארענדיגן די פאררעכטונג פון FSRS. די פאררעכטונג איז נישט באצייכנט געווארן אלס געלונגען.")

    CollectionOp(parent=mw, op=op).success(success).failure(failure).run_in_background()


def _run_check(
    *,
    manual: bool = False,
    min_card_id: int = 0,
    trigger: str = "after_update",
    trigger_token: str = "",
) -> None:
    try:
        enabled = _is_fsrs_enabled()
    except Exception as exc:
        logger.warning("FSRS availability check failed", exc_info=True)
        if manual:
            show_failure("מען קען נישט קוקן צי FSRS איז איינגעשאלטן. עפנט דעם פראפיל פון פריש און פרובירט די בדיקה נאכאמאל.", exc)
        return
    if not enabled:
        if manual:
            showInfo("FSRS איז נישט איינגעשאלטן, דערפאר איז נישט דא וואס צו קוקן.")
        return
    today_iso = date.today().isoformat()
    marker_key = None
    marker_value = None
    if not manual:
        profile = mw.pm.profile
        if trigger == "after_update":
            # Read the shipped version, not a user's override of addon config.
            try:
                version_path = Path(__file__).resolve().parent.parent / "modern-theme" / "config.json"
                version = str(json.loads(version_path.read_text(encoding="utf-8-sig"))["distribution_version"]).strip()
                if not version:
                    raise ValueError("Missing distribution version")
            except Exception as exc:
                logger.warning("FSRS update version could not be read: %s", exc)
                return
            now = int(time.time())
            previous = profile.get(_PM_KEY_UPDATE_CHECK, {})
            if previous.get("version") != version:
                marker_value = {"version": version, "first_check_at": now, "week_checked": False}
            elif not previous.get("week_checked") and now - int(previous["first_check_at"]) >= _FSRS_WEEK_SECS:
                marker_value = dict(previous, week_checked=True)
            else:
                return
            marker_key = _PM_KEY_UPDATE_CHECK
        else:
            # אישיו #411: ייבוא גדול ושינוי הגדרות מקבלים חתימת אירוע משלהם,
            # ולכן אינם נחסמים בגלל בדיקה לאחר עדכון או בדיקת השבוע.
            event_signature = f"{today_iso}:{trigger}:{trigger_token}"
            if profile.get(_PM_KEY_LAST_EVENT_CHECK) == event_signature:
                return
            marker_key = _PM_KEY_LAST_EVENT_CHECK
            marker_value = event_signature

    def operation(col):
        rows = _problem_rows(col, min_card_id=min_card_id)
        low_retention = _retention_is_low(col)
        return rows, low_retention

    def done(result) -> None:
        rows, low_retention = result
        if marker_key is not None:
            profile[marker_key] = marker_value
            mw.pm.save()
        if manual:
            if rows:
                # אישיו #447: גם בהפעלה ידנית מציגים קודם את ההודעה; הטבלה אינה
                # נפתחת אוטומטית ואפשר להגיע אליה רק דרך הכפתור "הצג טבלה".
                _show_problem_prompt(rows, low_retention)
            else:
                showInfo("מען האט נישט געפונען קארטלעך מיט א צייטפלאן פון FSRS אויסערגעווענליך ✓")
            return
        # אישיו #411: אחוז שימור נמוך לבדו אינו פותח דיאלוג כשהטבלה ריקה.
        if rows:
            _show_problem_prompt(rows, low_retention)

    def failed(exc) -> None:
        logger.error("FSRS diagnostic check failed", exc_info=(type(exc), exc, exc.__traceback__))
        if manual:
            show_failure("מען קען נישט פארענדיגן די בדיקה פון FSRS. מען קען פרובירן נאכאמאל פונעם מעניו נאכן עפענען דעם פראפיל פון פריש.", exc)

    QueryOp(parent=mw, op=operation, success=done).failure(failed).run_in_background()


def _run_automatic_check_if_due() -> None:
    _run_check(manual=False, trigger="after_update")


def _run_manual_extreme_check() -> None:
    _run_check(manual=True)


# אישיו #411: operation_did_execute מבדיל בין בדיקה יומית לבין אירועים שמצדיקים בדיקה נוספת.
def _after_collection_operation(changes, _handler) -> None:
    try:
        profile = mw.pm.profile
        count = int(mw.col.db.scalar("SELECT count() FROM cards") or 0)
        max_id = int(mw.col.db.scalar("SELECT max(id) FROM cards") or 0)
        old_count = int(profile.get(_PM_KEY_LAST_CARD_COUNT, count) or count)
        old_max = int(profile.get(_PM_KEY_LAST_MAX_CARD_ID, max_id) or max_id)
        profile[_PM_KEY_LAST_CARD_COUNT] = count
        profile[_PM_KEY_LAST_MAX_CARD_ID] = max_id

        settings_changed = bool(
            getattr(changes, "config", False) or getattr(changes, "deck_config", False)
        )
        current_settings = ""
        if settings_changed and _is_fsrs_enabled():
            current_settings = _fsrs_settings_signature()
            previous_settings = str(profile.get(_PM_KEY_LAST_FSRS_SETTINGS_STATE, "") or "")
            if current_settings:
                profile[_PM_KEY_LAST_FSRS_SETTINGS_STATE] = current_settings
            if current_settings and current_settings != previous_settings:
                mw.pm.save()
                _run_check(
                    manual=False,
                    trigger="fsrs_settings",
                    trigger_token=current_settings,
                )
                return

        mw.pm.save()
        if count - old_count >= _LARGE_IMPORT_THRESHOLD and max_id > old_max:
            # אישיו #411: ייבוא גדול בודק את הכרטיסים החדשים גם אם הבדיקה היומית כבר רצה.
            _run_check(
                manual=False,
                min_card_id=old_max,
                trigger="large_import",
                trigger_token=f"{old_max}:{max_id}:{count}",
            )
    except Exception:
        logger.warning("FSRS _after_collection_operation failed", exc_info=True)
        warn_once("fsrs-guard:collection-operation", "דער שוץ מאטאר פון FSRS האט נישט געקענט פארענדיגן די פעולה. עפנט דעם פראפיל פון פריש און פרובירט א מאנועלע בדיקה.")
        return


# אישיו #415: נשאר רק המתג החודשי הייחודי לתוסף. אין כאן שדה desired_retention נוסף;
# אחוז השימור המובנה באפשרויות החפיסה הוא המקור היחיד לערך הזה.
def _get_monthly_optimize_toggle_js(initial_status: bool, conf_id) -> str:
    checked = "checked" if initial_status else ""
    return f"""
    (() => {{
        const id = 'fsrs-monthly-opt-wrapper';
        if (document.getElementById(id)) return;
        const install = () => {{
            const headers = Array.from(document.querySelectorAll('h1,h2,h3,.setting-title'));
            const header = headers.find(x => x.textContent.includes('FSRS'));
            const target = header && (header.closest('.container') || header.parentElement);
            if (!target) {{ setTimeout(install, 250); return; }}
            const box = document.createElement('div');
            box.id = id;
            box.style.cssText = 'padding:12px;margin:10px 0;border:1px solid var(--border);border-radius:5px';
            box.innerHTML = `<label style="display:flex;gap:8px;align-items:center"><input id="fsrs-monthly-opt-toggle" type="checkbox" {checked}> <b>דערהיינטיגונג FSRS אויטאמאטיש יעדן חודש</b></label>`;
            target.appendChild(box);
            box.querySelector('input').addEventListener('change', function() {{
                pycmd('save_fsrs_monthly_opt:{conf_id}:' + this.checked);
            }});
        }};
        install();
    }})();
    """


def _on_deck_options_did_load(options_dialog) -> None:
    try:
        if not _is_fsrs_enabled():
            return
        conf_id = options_dialog._deck["conf"]
        options_dialog.web.eval(
            _get_monthly_optimize_toggle_js(_get_monthly_optimize_status(conf_id), conf_id)
        )
    except Exception:
        logger.warning("FSRS _on_deck_options_did_load failed", exc_info=True)
        warn_once("fsrs-guard:deck-options", "דער שוץ מאטאר פון FSRS האט נישט געקענט פארענדיגן די פעולה. עפנט דעם פראפיל פון פריש און פרובירט א מאנועלע בדיקה.")



def _on_js_message(handled, message, context):
    if not isinstance(message, str):
        return handled
    if message.startswith("save_fsrs_monthly_opt:"):
        parts = message.split(":", 2)
        if len(parts) == 3:
            _set_monthly_optimize_status(parts[1], parts[2] == "true")
        return (True, None)
    return handled


_menu_action: QAction | None = None


def _add_to_col_menu() -> None:
    global _menu_action
    if _menu_action is not None or not hasattr(mw, "addon_col_menu"):
        return
    action = QAction("צייטפלאן שיטה (FSRS / SM-2)", mw)
    action.setCheckable(True)
    action.setIcon(mw.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
    qconnect(action.triggered, lambda: _SchedulerDialog(mw).exec())
    mw.addon_col_menu.aboutToShow.connect(lambda: action.setChecked(_is_fsrs_enabled()))
    mw.addon_col_menu.addAction(action)

    fix_action = QAction(_FIX_MENU_LABEL, mw)
    fix_action.setIcon(mw.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
    qconnect(fix_action.triggered, _run_manual_extreme_check)
    mw.addon_col_menu.addAction(fix_action)

    optimize_action = QAction("שטים אפ FSRS פאר אלע גרופעס איינשטעלונגען", mw)
    optimize_action.setIcon(mw.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
    qconnect(optimize_action.triggered, _optimize_all_fsrs_presets_now)
    mw.addon_col_menu.addAction(optimize_action)
    _menu_action = action


def _initialize_card_state() -> None:
    try:
        profile = mw.pm.profile
        profile[_PM_KEY_LAST_CARD_COUNT] = int(mw.col.db.scalar("SELECT count() FROM cards") or 0)
        profile[_PM_KEY_LAST_MAX_CARD_ID] = int(mw.col.db.scalar("SELECT max(id) FROM cards") or 0)
        signature = _fsrs_settings_signature()
        if signature:
            profile[_PM_KEY_LAST_FSRS_SETTINGS_STATE] = signature
        mw.pm.save()
    except Exception:
        logger.warning("FSRS _initialize_card_state failed", exc_info=True)
        warn_once("fsrs-guard:card-state", "דער שוץ מאטאר פון FSRS האט נישט געקענט פארענדיגן די פעולה. עפנט דעם פראפיל פון פריש און פרובירט א מאנועלע בדיקה.")



def _on_profile_did_open() -> None:
    _add_to_col_menu()
    _initialize_card_state()
    _schedule_collection_callback(3000, _optimize_fsrs_monthly_if_due)
    _schedule_collection_callback(1500, _run_automatic_check_if_due)
    _show_welcome_if_needed()


gui_hooks.profile_did_open.append(_on_profile_did_open)
gui_hooks.day_did_change.append(_optimize_fsrs_monthly_if_due)
gui_hooks.day_did_change.append(_run_automatic_check_if_due)
gui_hooks.deck_options_did_load.append(_on_deck_options_did_load)
gui_hooks.webview_did_receive_js_message.append(_on_js_message)
if hasattr(gui_hooks, "operation_did_execute"):
    gui_hooks.operation_did_execute.append(_after_collection_operation)
