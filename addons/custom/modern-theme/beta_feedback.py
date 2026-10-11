"""
א באזונדערער מאדול פאר דער פרואוו ווערסיע (beta) — גרינג צו אוועקנעמען.
אינהאלט:
    1. באנער "פרואוו ווערסיע" + קנעפל "שיקט א באג / פארשלאג" אויפן הויפט עקראן (DeckBrowser).
    2. ארומנעמען showWarning / showCritical / showText צו צולייגן א קנעפל "שיקט מיר א באריכט".
    3. א פענסטער צו זאמלען די טריט וואס ברענגען צום פראבלעם מיט:
        - קאפירן אינעם קאפיר ברעט (א באקוועמער פארמאט פארן געהילף AI)
        - אפזיכערן אין א טעקע
        - עפענען אין אימעיל
צו אוועקנעמען אינגאנצן: מעקט אויס דעם טעקע און די שורות וואס אימפארטירן אים אין-__init__.py.
"""

from __future__ import annotations

import base64
import ctypes
import datetime as _dt
import getpass
import hashlib
import html
import inspect
import os
import json
import platform
import re
import sys
import traceback
import time
from collections import deque
from collections.abc import Callable
from typing import Any

import anki
from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QApplication,
    QCheckBox,
    QDesktopServices,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QGuiApplication,
    QHBoxLayout,
    QEvent,
    QKeySequence,
    QLabel,
    QComboBox,
    QBuffer,  # #390 — קידוד PNG מפורש בתוך MIME כדי שהצילום לא ייעלם בהדבקה.
    QIODevice,
    QMimeData,  # #390 — לוח משולב של טקסט הדיווח וצילום המסך.
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSize,
    QSizePolicy,
    QStyle,
    Qt,
    QTimer,
    QToolButton,
    QUrl,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import showInfo, tooltip
from _shared_libs.haf_logging import get_logger, get_recent_log_text
from _shared_libs.haf_notifications import show_failure

_logger = get_logger("modern_theme.feedback")

# -------------------------------------------------------------- הגדרות
_DEFAULT_EMAIL = "anki4tora@gmail.com"
_BETA_VERSION_LABEL = "פרואוו ווערסיע (Beta)"
_ADDON_MODULE_NAME = __name__.rsplit(".", 1)[0]  # "modern-theme" או דומה

# נשמור הפניות לפונקציות המקוריות כדי לאפשר עטיפה חד-פעמית ובטוחה.
_orig_showWarning: Callable | None = None
_orig_showCritical: Callable | None = None
_orig_showText: Callable | None = None
_orig_showInfo: Callable | None = None
_orig_init_message_box: Callable | None = None
_orig_addons_showText: Callable | None = None
_console_tail: deque[str] = deque(maxlen=300)

# דגל סגירת באנר עד להפעלה הבאה (session-only)
_banner_dismissed: bool = False

# מנע כפל הצגת דיאלוג הדיווח כששני מסלולים מפעילים אותו בוזמנית
_error_dialog_active: bool = False
_last_error_fingerprint = ""
_last_error_time = 0.0

# טעינת תוספים עלולה ליצור חלון נפרד (loadAddons) שלא עובר דרך showWarning/showCritical.
# נשמור דגל כדי לא לפתוח אוטומטית יותר מפעם אחת בכל סשן.
_addon_load_report_auto_opened: bool = False


def _install_console_capture() -> None:
    # אישיו #408/#410/#412/#445: אין החלפה של sys.stdout/sys.stderr.
    return


def _windows_console_tail(max_lines: int = 80) -> str:
    # אישיו #429: קורא את שורות הפלט האחרונות מה-console buffer הקיים ב-Windows.
    if os.name != "nt":
        return ""
    try:
        class _Coord(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

        class _SmallRect(ctypes.Structure):
            _fields_ = [
                ("Left", ctypes.c_short),
                ("Top", ctypes.c_short),
                ("Right", ctypes.c_short),
                ("Bottom", ctypes.c_short),
            ]

        class _Csbi(ctypes.Structure):
            _fields_ = [
                ("dwSize", _Coord),
                ("dwCursorPosition", _Coord),
                ("wAttributes", ctypes.c_ushort),
                ("srWindow", _SmallRect),
                ("dwMaximumWindowSize", _Coord),
            ]

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        info = _Csbi()
        if not handle or not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
            return ""
        width = max(1, int(info.dwSize.X))
        last_row = max(0, int(info.dwCursorPosition.Y))
        first_row = max(0, last_row - max_lines + 1)
        count = (last_row - first_row + 1) * width
        if count <= 0:
            return ""
        buffer = ctypes.create_unicode_buffer(count + 1)
        chars_read = ctypes.c_ulong(0)
        start = _Coord(0, first_row)
        if not kernel32.ReadConsoleOutputCharacterW(
            handle, buffer, count, start, ctypes.byref(chars_read)
        ):
            return ""
        raw = buffer[: int(chars_read.value)]
        lines = [raw[i : i + width].rstrip() for i in range(0, len(raw), width)]
        return "\n".join(line for line in lines if line).strip()
    except Exception:
        return ""


def _unique_diagnostics(error_text: str = "") -> str:
    """Keep each traceback once across the error handler and console sources."""
    sources = [error_text, *_console_tail, get_recent_log_text(), _windows_console_tail()]
    seen_traces: set[str] = set()
    seen_sections: set[str] = set()
    sections = []
    pattern = re.compile(
        r"Traceback \(most recent call last\):\n(?:[ \t].*\n|\n)*[^ \t\n][^\n]*(?:\n|$)"
    )

    def unique_trace(match):
        key = re.sub(r"\s+", " ", match.group()).strip()
        if key in seen_traces:
            return ""
        seen_traces.add(key)
        return match.group()

    for source in sources:
        source = str(source or "").replace("\r\n", "\n")
        section = pattern.sub(unique_trace, source).strip()
        key = re.sub(r"\s+", " ", section)
        if section and key not in seen_sections:
            seen_sections.add(key)
            sections.append(section)
    return "\n\n".join(sections)




def _get_email() -> str:
    """ברענגט צוריק אן אימעיל אדרעס פונעם-config (ניצט-default אויב עס איז נישט דא)."""
    try:
        cfg = mw.addonManager.getConfig(_ADDON_MODULE_NAME) or {}
        beta = cfg.get("beta", {}) or {}
        return beta.get("feedback_email") or _DEFAULT_EMAIL
    except Exception:
        return _DEFAULT_EMAIL


def _is_beta_enabled() -> bool:
    try:
        cfg = mw.addonManager.getConfig(_ADDON_MODULE_NAME) or {}
        beta = cfg.get("beta", {}) or {}
        return bool(beta.get("enabled", True))
    except Exception:
        return True


# -------------------------------------------------------------- דיאלוג דיווח
class _FeedbackDialog(QDialog):
    """א פענסטער פאר מערערע צוועקן: באג / פארשלאג / טעות באריכט."""

    def __init__(
        self,
        parent=None,
        *,
        kind: str = "bug",
        error_text: str = "",
    ) -> None:
        # #390 — activeWindow() אחרי פתיחת הדיאלוג הוא הדיאלוג עצמו. שומרים את
        # החלון שהיה פעיל לפניו ומציגים גם רשימת חלונות פתוחים לבחירה מפורשת.
        source_window = QApplication.activeWindow()
        super().__init__(parent or mw)
        self._source_window = source_window
        self._kind = kind  # "bug" | "suggestion" | "error"
        self._error_text = error_text or ""
        self._screenshots: list[tuple[Any, QWidget]] = []

        title_map = {
            "bug": "באג באריכט",
            "suggestion": "שיקן א פארשלאג צו פארבעסערן",
            "error": "הילף און באריכט איבער א פראבלעם",
        }
        self.setWindowTitle(title_map.get(kind, "באריכט"))
        self.setMinimumSize(QSize(640, 520))

        # A report is an invitation to get help, not a critical-error alarm.
        if kind == "error":
            self.setWindowIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
            )

        layout = QVBoxLayout(self)

        # שורה עליונה: אייקון אדום + טקסט הקדמה
        top_row = QHBoxLayout()
        if kind == "error":
            icon_label = QLabel()
            icon_label.setPixmap(
                self.style()
                .standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
                .pixmap(QSize(36, 36))
            )
            icon_label.setFixedSize(QSize(44, 44))
            top_row.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        intro_text = {
            "bug": "באשרייבט בקיצור וואס איר האט פרובירט צו טון, וואס איז טאקע געשען און וואס איר האט ערווארטעט.\n"
                   "לייגט צו די גענויע טריט וואס איר האט געטון פארן פראבלעם.",
            "suggestion": "באשרייבט קלאר דעם פארשלאג. וואס וואלט איר געוואלט קענען טון?\n"
                          "אויב נויטיג, לייגט צו א ביישפיל.",
            "error": "אנקי האט נישט געקענט פארענדיגן א פעולה.\n"
                     "מען קען פארמאכן דעם באריכט פענסטער. אויב דער פראבלעם קומט צוריק, איז ראטזאם צו שיקן א באריכט.\n"
                     "באשרייבט בקיצור וואס איר האט געטון פארן פענסטער האט זיך געעפנט; די אבחון פרטים וועלן מיטגעשיקט ווערן אינעם באריכט.",
        }
        intro = QLabel(intro_text.get(kind, ""))
        intro.setWordWrap(True)
        top_row.addWidget(intro, 1)
        layout.addLayout(top_row)

        self._steps_edit = QPlainTextEdit(self)
        self._steps_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        _opt = self._steps_edit.document().defaultTextOption()
        _opt.setTextDirection(Qt.LayoutDirection.RightToLeft)
        _opt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._steps_edit.document().setDefaultTextOption(_opt)
        self._steps_edit.setPlaceholderText(
            "1. איך האב געעפנט אנקי\n2. איך האב געדריקט אויף ...\n3. איך האב געזען א טעות: ..."
        )
        # #150 — Ctrl+C מתוך תיבת הכתיבה צריך להעתיק את הדוח המלא, לא רק את הטקסט המסומן בתיבה.
        self._steps_edit.installEventFilter(self)
        layout.addWidget(self._steps_edit, 1)

        # #390 — אפשר לצלם את חלון Anki הראשי או חלון פתוח שנבחר במפורש.
        capture_row = QHBoxLayout()
        capture_app_btn = QPushButton("📷 נעם א בילד פון Anki")
        self._capture_window_combo = QComboBox()
        # שם החלון הוא הרכיב היחיד שמותר לכווץ כשאין מקום בשורה.
        self._capture_window_combo.setMinimumWidth(0)
        self._capture_window_combo.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Fixed,
        )
        self._capture_window_combo.setToolTip("קלייבט אויס אן אפענעם פענסטער פאר א בילד")
        self._refresh_capture_windows()
        capture_window_btn = QPushButton("📷 נעם א בילד פון דעם אויסגעקליבענעם פענסטער")
        self._capture_status = QLabel("קיין בילד איז נישט צוגעשטעלט")
        self._capture_status.setWordWrap(False)
        capture_app_btn.clicked.connect(lambda: self._capture_window(mw))
        capture_window_btn.clicked.connect(self._capture_selected_window)
        capture_row.addWidget(capture_app_btn)
        capture_row.addWidget(self._capture_window_combo, 1)
        capture_row.addWidget(capture_window_btn)
        capture_row.addWidget(self._capture_status)
        layout.addLayout(capture_row)

        # כל צילום מוצג כתמונה ממוזערת עם ביטול עצמאי.
        self._attachments_scroll = QScrollArea(self)
        self._attachments_scroll.setWidgetResizable(True)
        self._attachments_scroll.setMaximumHeight(112)
        self._attachments_scroll.setVisible(False)
        self._attachments_widget = QWidget(self._attachments_scroll)
        self._attachments_row = QHBoxLayout(self._attachments_widget)
        self._attachments_row.setContentsMargins(4, 4, 4, 4)
        self._attachments_row.setSpacing(6)
        self._attachments_row.addStretch()
        self._attachments_scroll.setWidget(self._attachments_widget)
        layout.addWidget(self._attachments_scroll)

        if error_text:
            details_button = QPushButton("ווייז אבחון פרטים (ווערן צוגעשטעלט צום באריכט)")
            details_button.setCheckable(True)
            layout.addWidget(details_button)
            self._error_view = QPlainTextEdit(self)
            self._error_view.setPlainText(error_text)
            self._error_view.setReadOnly(True)
            self._error_view.setMaximumHeight(140)
            self._error_view.installEventFilter(self)
            self._error_view.setVisible(False)
            details_button.toggled.connect(self._error_view.setVisible)
            layout.addWidget(self._error_view)

        # שורת מייל — כתובת בולטת + כפתור העתקה
        email_label_text = {
            "bug": "פאר א באג באריכט, שיקט צו:",
            "suggestion": "פאר א פארשלאג, שיקט צו:",
            "error": "פאר א טעות באריכט, שיקט צו:",
        }.get(kind, "פארבינדט זיך:")
        email_row = QHBoxLayout()
        email_desc = QLabel(email_label_text)
        email_addr = QLabel("<b>anki4tora@gmail.com</b>")
        email_addr.setStyleSheet("font-size: 14px;")
        copy_email_btn = QPushButton("📋 קאפיר די אדרעס")
        copy_email_btn.setFixedWidth(200)
        # #192 — callback מושהה לא נוגע בכפתור שכבר נמחק אחרי סגירת דיאלוג הדיווח.
        def reset_copy_email_button() -> None:
            try:
                copy_email_btn.setText("📋 קאפיר די אדרעס")
            except RuntimeError:
                return

        def copy_feedback_email() -> None:
            QApplication.clipboard().setText("anki4tora@gmail.com")
            copy_email_btn.setText("✓ קאפירט!")
            QTimer.singleShot(2000, reset_copy_email_button)

        copy_email_btn.clicked.connect(copy_feedback_email)
        email_row.addWidget(email_desc)
        email_row.addWidget(email_addr)
        email_row.addStretch()
        email_row.addWidget(copy_email_btn)
        layout.addLayout(email_row)

        # הערה על שליחה במייל
        mail_note = QLabel(
            "⚠️ דער 'שיקט מיט אימעיל' קנעפל ארבעט נישט אלעמאל — אויב קיין אימעיל עפנט זיך נישט, קאפירט אינעם קאפיר ברעט און לייגט עס אליין אריין אין אן אימעיל."
        )
        mail_note.setWordWrap(True)
        mail_note.setStyleSheet("color: #b71c1c; font-size: 11px;")
        layout.addWidget(mail_note)

        # כפתורי פעולה
        btn_row = QHBoxLayout()
        copy_btn = QPushButton("קאפיר אינעם קאפיר ברעט")
        save_btn = QPushButton("זיכער אפ אין א טעקע…")
        mail_btn = QPushButton("שיק מיט אימעיל")
        copy_btn.clicked.connect(self._on_copy)
        save_btn.clicked.connect(self._on_save)
        mail_btn.clicked.connect(self._on_mail)
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(mail_btn)
        layout.addLayout(btn_row)

        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bbox.rejected.connect(self.reject)
        bbox.accepted.connect(self.accept)
        layout.addWidget(bbox)

    def _refresh_capture_windows(self) -> None:
        """פילט אן די פענסטער Qt וואס זענען אפן, אן דעם באריכט פענסטער אליין."""
        self._capture_window_combo.clear()
        windows = []
        if self._source_window is not None and self._source_window is not self:
            if self._source_window.isVisible():
                windows.append(self._source_window)
        for window in QApplication.topLevelWidgets():
            if window is self or not window.isVisible() or window.isMinimized():
                continue
            if window not in windows:
                windows.append(window)
        for window in windows:
            title = window.windowTitle().strip() or type(window).__name__
            self._capture_window_combo.addItem(title, window)

    def _capture_selected_window(self) -> None:
        window = self._capture_window_combo.currentData()
        if window is None:
            showInfo("מען האט נישט געפונען אן אפענעם פענסטער פאר א בילד.")
            return
        self._capture_window(window)

    def _capture_window(self, window) -> None:
        # #390 — grab() מצלם רק את חלון התוכנה המבוקש, לא את כל שולחן העבודה.
        if window is None:
            showInfo("מען האט נישט געפונען אן אקטיוון פענסטער פאר א בילד.")
            return
        pixmap = window.grab()
        if pixmap.isNull():
            showInfo("מען האט נישט געקענט נעמען א בילד פונעם פענסטער.")
            return
        thumbnail = QWidget(self._attachments_widget)
        thumbnail.setFixedSize(QSize(132, 94))
        thumbnail_layout = QVBoxLayout(thumbnail)
        thumbnail_layout.setContentsMargins(2, 2, 2, 2)
        thumbnail_layout.setSpacing(1)
        remove_row = QHBoxLayout()
        remove_row.addStretch()
        # #390 — X אדום ופשוט להסרת צילום. לא משתמשים באייקון הסגירה
        # המערכתי, שבחלק מערכות הנושא מצויר כריבוע שחור ומוזר.
        remove_btn = QToolButton(thumbnail)
        remove_btn.setText("×")
        remove_btn.setStyleSheet(
            "QToolButton { color: #d32f2f; border: none; background: transparent; "
            "font-size: 22px; font-weight: 700; padding: 0; }"
            "QToolButton:hover { color: #ffffff; background: #d32f2f; "
            "border-radius: 4px; }"
            "QToolButton:pressed { background: #b71c1c; }"
        )
        remove_btn.setAutoRaise(True)
        remove_btn.setToolTip("נעם אוועק דעם בילד פונעם באריכט")
        remove_btn.setAccessibleName("נעם אוועק בילד")
        remove_btn.setFixedSize(QSize(24, 24))
        remove_row.addWidget(remove_btn)
        preview = QLabel(thumbnail)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setPixmap(
            pixmap.scaled(
                QSize(124, 64),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        thumbnail_layout.addLayout(remove_row)
        thumbnail_layout.addWidget(preview, 1)
        self._screenshots.append((pixmap, thumbnail))
        self._attachments_row.insertWidget(self._attachments_row.count() - 1, thumbnail)
        remove_btn.clicked.connect(
            lambda _checked=False, card=thumbnail: self._remove_screenshot(card)
        )
        self._attachments_scroll.setVisible(True)
        self._update_capture_status()

    def _remove_screenshot(self, thumbnail: QWidget) -> None:
        self._screenshots = [item for item in self._screenshots if item[1] is not thumbnail]
        self._attachments_row.removeWidget(thumbnail)
        thumbnail.deleteLater()
        self._attachments_scroll.setVisible(bool(self._screenshots))
        self._update_capture_status()

    def _update_capture_status(self) -> None:
        count = len(self._screenshots)
        self._capture_status.setText(
            "קיין בילד איז נישט צוגעשטעלט" if not count else f"צוגעשטעלט {count} בילדער"
        )

    def _build_report(self) -> str:
        """בויט א באריכט אין א באקוועמען פארמאט צו שיקן מיט אימעיל."""
        steps = self._steps_edit.toPlainText().strip() or "(קיין טריט זענען נישט אויסגעפילט געווארן)"
        kind_he = {"bug": "באג", "suggestion": "פארשלאג", "error": "טעות"}.get(
            self._kind, "באריכט"
        )
        env = _collect_environment()
        lines = [
            f"באריכט {kind_he} —", "=" * 50, "",
            f"דאטום: {_dt.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", "",
            "--- טריט וואס האבן געברענגט צום פראבלעם ---", "", steps, "",
            "--- סביבה פרטים ---", "",
        ]
        for k, v in env.items():
            lines.append(f"  {k}: {v}")
        diagnostics = _unique_diagnostics(self._error_text)
        if diagnostics:
            lines += ["", "--- טעות פרטים און קאנסאל אויסגאבע ---", "", diagnostics]
        # אישיו #429: שומרים את הרשימה המקורית השנייה של Anki; מוסיפים רשימה רק כשאין כזו.
        if "===Add-ons (active)===" not in diagnostics:
            # אישיו #429: הוספת רשימת התוספים החסרה לסוף פרטי האבחון.
            lines += ["", "--- ליסטע פון צוגאבן ---", "", _collect_addons()]
        lines += ["", "=" * 50]
        return "\n".join(lines)

    def _copy_report_to_clipboard(self) -> str:
        """קאפירט טעקסט און-PNG אינעם זעלבן MIME, כדי אויך Word/אימעיל פראגראמען זאלן באקומען דעם בילד."""
        report = self._build_report()
        mime = QMimeData()
        mime.setText(report)
        if self._screenshots:
            image = self._screenshots[0][0].toImage()
            mime.setImageData(image)
            # #390 — setImageData לבדו לא מספיק בכל יישומי Windows; מוסיפים
            # גם payload תקני image/png לצד הטקסט באותו אובייקט QMimeData.
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            if image.save(buffer, "PNG"):
                png_bytes = bytes(buffer.data())
                mime.setData("image/png", png_bytes)
                # #390 — HTML מאחד את הדיווח והתמונה למסמך אחד שניתן להדביק יחד.
                escaped_report = html.escape(report)
                image_tags = []
                for index, (pixmap, _thumbnail) in enumerate(self._screenshots, 1):
                    image_buffer = QBuffer()
                    image_buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    if pixmap.toImage().save(image_buffer, "PNG"):
                        encoded_png = base64.b64encode(bytes(image_buffer.data())).decode("ascii")
                        image_tags.append(
                            f'<p><img alt="עקראן בילד {index} פון Anki" '
                            f'style="max-width:100%;height:auto" '
                            f'src="data:image/png;base64,{encoded_png}"></p>'
                        )
                    image_buffer.close()
                mime.setHtml(
                    '<div dir="rtl" style="white-space:pre-wrap">'
                    f"<pre>{escaped_report}</pre>" + "".join(image_tags) + "</div>"
                )
            buffer.close()
        QApplication.clipboard().setMimeData(mime)
        return report

    def _on_copy(self) -> None:
        try:
            self._copy_report_to_clipboard()
            tooltip("דער באריכט איז קאפירט געווארן אינעם קאפיר ברעט")
        except Exception:
            QGuiApplication.clipboard().setText(self._build_report())
            tooltip("דער באריכט איז קאפירט געווארן אינעם קאפיר ברעט")

    # אישיו #408: Ctrl+C מעתיק את הדוח בלבד; הדוח המלא אינו נכתב לקונסול Anki.
    def _on_copy_with_log(self) -> None:
        try:
            self._copy_report_to_clipboard()
        except Exception:
            QGuiApplication.clipboard().setText(self._build_report())
        tooltip("דער באריכט איז קאפירט געווארן אינעם קאפיר ברעט (Ctrl+C)")

    def eventFilter(self, obj, event):
        # #150 — QPlainTextEdit בולע Ctrl+C לפני הדיאלוג; לכן לוכדים אותו כאן.
        if event.type() == QEvent.Type.KeyPress and event.matches(QKeySequence.StandardKey.Copy):
            if obj in (getattr(self, "_steps_edit", None), getattr(self, "_error_view", None)):
                self._on_copy_with_log()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        # #150 — גם כשהפוקוס אינו בתיבת טקסט, Ctrl+C מעתיק את הדוח המלא.
        if event.matches(QKeySequence.StandardKey.Copy):
            self._on_copy_with_log()
            return
        super().keyPressEvent(event)

    def _on_save(self) -> None:
        default_name = "anki_bug_report_{}.md".format(
            _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "אפזיכערן א באריכט", default_name,
            "Markdown (*.md);;Text (*.txt);;All Files (*)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._build_report())
            tooltip(f"אפגעזיכערט: {path}")
        except Exception as exc:
            show_failure("דער באריכט איז נישט אפגעזיכערט געווארן. קלייבט אויס אן אנדערן פאלדער אדער קאפירט אים אינעם קאפיר ברעט.", exc, parent=self)

    def _on_mail(self) -> None:
        report = self._build_report()
        subject = "[Anki Modern Beta] " + {
            "bug": "באג באריכט", "suggestion": "פארבעסערונג פארשלאג", "error": "טעות באריכט",
        }.get(self._kind, "באריכט")
        try:
            report = self._copy_report_to_clipboard()
        except Exception:
            QGuiApplication.clipboard().setText(report)
        url = QUrl("mailto:" + _get_email())
        from urllib.parse import quote
        body_short = report if len(report) < 1500 else (
            report[:1400] + "\n\n[...איז פארקורצט געווארן. דער פולער באריכט איז שוין אין אייער קאפיר ברעט — לייגט אים דא אריין.]"
        )
        url.setQuery(f"subject={quote(subject)}&body={quote(body_short)}")
        QDesktopServices.openUrl(url)
        tooltip("איז געעפנט געווארן אין אימעיל. דער פולער באריכט איז אויך קאפירט געווארן אלס גיבוי.")


# -------------------------------------------------------------- איסוף סביבה
def _collect_environment() -> dict[str, Any]:
    info: dict[str, Any] = {}
    try:
        info["anki_version"] = anki.version  # type: ignore[attr-defined]
    except Exception:
        info["anki_version"] = "?"
    try:
        info["python"] = sys.version.split()[0]
    except Exception:
        info["python"] = "?"
    try:
        info["platform"] = platform.platform()
    except Exception:
        info["platform"] = "?"
    try:
        info["profile"] = mw.pm.name if mw and mw.pm else "?"
    except Exception:
        info["profile"] = "?"
    try:
        info["user"] = getpass.getuser()
    except Exception:
        info["user"] = "?"
    try:
        info["addon_version"] = _get_addon_version()
    except Exception:
        info["addon_version"] = "?"
    try:
        info["distribution_version"] = _get_distribution_version()
    except Exception:
        info["distribution_version"] = "?"
    return info


def _collect_addons() -> str:
    try:
        manager = mw.addonManager
        addons = sorted(manager.allAddons())
    except Exception as exc:
        return f"מען קען נישט לייענען די צוגאבן ליסטע: {exc}"
    lines = []
    for addon_id in addons:
        try:
            meta = manager.addon_meta(addon_id)
            status = "איינגעשאלטן" if meta.enabled else "אפגעשטעלט"
            lines.append(
                f"{manager.addonName(addon_id)} | {addon_id} | {status} | "
                f"ווערסיע: {meta.human_version or '?'}"
            )
        except Exception as exc:
            lines.append(f"{addon_id} | מען קען נישט לייענען די פרטים: {exc}")
    return "\n".join(lines) or "עס זענען נישט דא קיין אינסטאלירטע צוגאבן"


def _get_addon_version() -> str:
    try:
        import os
        meta_path = os.path.join(os.path.dirname(__file__), "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            return str(meta.get("human_version") or meta.get("mod") or "?")
    except Exception:
        pass
    return "?"


def _get_distribution_version() -> str:
    try:
        addon_id = mw.addonManager.addonFromModule(__name__)
        cfg = mw.addonManager.getConfig(addon_id) or {}
        value = str(cfg.get("distribution_version") or "").strip()
        if value:
            return value
    except Exception:
        pass
    try:
        # אישיו #414: fallback מוקדם ל-config.json המקומי בלבד; אין fallback לקובץ txt הישן.
        from pathlib import Path
        cfg = json.loads(Path(__file__).with_name("config.json").read_text(encoding="utf-8-sig"))
        value = str(cfg.get("distribution_version") or "").strip()
        if value:
            return value
    except Exception:
        pass
    return "?"

# אישיו #408/#410/#412: נקודת הכניסה של כפתור דיווח באג חייבת להיות מוגדרת במפורש.
def open_bug_dialog() -> None:
    _FeedbackDialog(mw, kind="bug").exec()


def open_suggestion_dialog() -> None:
    _FeedbackDialog(mw, kind="suggestion").exec()


def open_error_dialog(error_text: str) -> None:
    _FeedbackDialog(mw, kind="error", error_text=error_text).exec()


def _install_help_menu_bug_action() -> None:
    # אישיו #449: תפריט עזרה מפעיל את אותה נקודת כניסה של כפתור הבאג בסרגל הבטא.
    menu = getattr(getattr(mw, "form", None), "menuHelp", None)
    if menu is None or getattr(mw, "_haf_beta_help_bug_action", None) is not None:
        return
    action = QAction("באג באריכט", mw)
    from .menu_icons import menu_icon
    action.setIcon(menu_icon("bug"))
    action.setIconVisibleInMenu(True)
    action.setProperty("haf_help_section", "הילף און באריכטן")
    action.triggered.connect(open_bug_dialog)
    menu.addAction(action)
    mw._haf_beta_help_bug_action = action


# -------------------------------------------------------------- שיתוף חפיסות במייל
_SHARE_EMAIL = "anki4tora@gmail.com"


class _ShareDecksDialog(QDialog):
    """א פענסטער אויסצוקלייבן פעקלעך צו עקספארטירן און שיקן מיט אימעיל."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("טיילט פראגעס דורך אימעיל")
        self.setMinimumSize(QSize(480, 520))
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        intro = QLabel("קלייבט אויס פעקלעך צו עקספארטירן און שיקן מיט אימעיל:")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self._decks_layout = QVBoxLayout(scroll_widget)
        self._decks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)
        self._checkboxes: list[tuple[QCheckBox, int, str]] = []
        self._populate_decks()
        sel_row = QHBoxLayout()
        select_all_btn = QPushButton("קלייב אלעס אויס")
        deselect_all_btn = QPushButton("נעם אוועק די גאנצע אויסוואל")
        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn.clicked.connect(self._deselect_all)
        sel_row.addWidget(select_all_btn)
        sel_row.addWidget(deselect_all_btn)
        sel_row.addStretch()
        layout.addLayout(sel_row)
        self._media_cb = QCheckBox("נעם מיט מעדיע (בילדער, אוידיא)")
        self._media_cb.setChecked(True)
        layout.addWidget(self._media_cb)
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)
        self._status_label = QLabel("")
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)
        btn_row = QHBoxLayout()
        self._export_mail_btn = QPushButton("📧 עקספארטיר און שיק מיט אימעיל")
        self._export_mail_btn.clicked.connect(lambda: self._on_export(open_mail=True))
        btn_row.addWidget(self._export_mail_btn)
        self._export_copy_btn = QPushButton("📋 עקספארטיר און קאפיר די אימעיל אדרעס")
        self._export_copy_btn.clicked.connect(lambda: self._on_export(open_mail=False))
        btn_row.addWidget(self._export_copy_btn)
        layout.addLayout(btn_row)
        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def _populate_decks(self) -> None:
        try:
            decks = mw.col.decks.all_names_and_ids()
        except Exception:
            return
        for deck in decks:
            if deck.name == "Default" and not mw.col.find_cards(f'"deck:{deck.name}"'):
                continue
            cb = QCheckBox(deck.name)
            self._decks_layout.addWidget(cb)
            self._checkboxes.append((cb, deck.id, deck.name))

    def _select_all(self) -> None:
        for cb, _, _ in self._checkboxes:
            cb.setChecked(True)

    def _deselect_all(self) -> None:
        for cb, _, _ in self._checkboxes:
            cb.setChecked(False)

    def _on_export(self, *, open_mail: bool) -> None:
        selected = [(did, name) for cb, did, name in self._checkboxes if cb.isChecked()]
        if not selected:
            showInfo("קיין פעקלעך זענען נישט אויסגעקליבן געווארן צום עקספארטירן.")
            return
        import os
        import tempfile
        export_dir = os.path.join(tempfile.gettempdir(), "anki_share_decks")
        os.makedirs(export_dir, exist_ok=True)
        for f in os.listdir(export_dir):
            if f.endswith(".apkg"):
                try:
                    os.remove(os.path.join(export_dir, f))
                except Exception:
                    pass
        from anki.collection import DeckIdLimit
        from anki.import_export_pb2 import ExportAnkiPackageOptions
        with_media = self._media_cb.isChecked()
        options = ExportAnkiPackageOptions(
            with_scheduling=False, with_deck_configs=True, with_media=with_media, legacy=True,
        )
        self._progress.setVisible(True)
        self._status_label.setVisible(True)
        self._progress.setMaximum(len(selected))
        self._export_mail_btn.setEnabled(False)
        self._export_copy_btn.setEnabled(False)
        exported_files: list[str] = []
        for i, (did, name) in enumerate(selected):
            safe_name = name.replace("::", "_").replace("/", "_").replace("\\", "_")
            out_path = os.path.join(export_dir, f"{safe_name}.apkg")
            self._status_label.setText(f"מען עקספארטירט: {name}...")
            self._progress.setValue(i)
            QApplication.processEvents()
            try:
                mw.col.export_anki_package(
                    out_path=out_path, options=options, limit=DeckIdLimit(deck_id=did),
                )
                exported_files.append(out_path)
            except Exception as exc:
                show_failure(f"דער פעקל '{name}' איז נישט עקספארטירט געווארן. פרובירט אים צו עקספארטירן באזונדער דורכן טעקע מעניו.", exc, parent=self)
        self._progress.setValue(len(selected))
        self._status_label.setText(f"עקספארטירט {len(exported_files)} פעקלעך מיט הצלחה!")
        self._export_mail_btn.setEnabled(True)
        self._export_copy_btn.setEnabled(True)
        if not exported_files:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(export_dir))
        if open_mail:
            from urllib.parse import quote
            deck_names = ", ".join(name for _, name in selected)
            subject = quote(f"טיילן אנקי פעקלעך: {deck_names[:80]}")
            body = quote(
                f"צוגעשטעלט {len(exported_files)} אנקי פעקלעך:\n"
                + "\n".join(f"• {name}" for _, name in selected)
                + "\n\n(שטעלט צו די טעקעס פונעם פאלדער וואס האט זיך געעפנט)"
            )
            url = QUrl(f"mailto:{_SHARE_EMAIL}?subject={subject}&body={body}")
            QDesktopServices.openUrl(url)
            tooltip(
                f"עקספארטירט {len(exported_files)} פעקלעך.\n"
                "דער טעקעס פאלדער און אן אימעיל פענסטער האבן זיך געעפנט — שלעפט די טעקעס אינעם אימעיל."
            )
        else:
            try:
                QApplication.clipboard().setText(_SHARE_EMAIL)
            except Exception:
                QGuiApplication.clipboard().setText(_SHARE_EMAIL)
            tooltip(
                f"עקספארטירט {len(exported_files)} פעקלעך.\n"
                f"די אימעיל אדרעס {_SHARE_EMAIL} איז קאפירט געווארן אינעם קאפיר ברעט.\n"
                "דער טעקעס פאלדער האט זיך געעפנט — שיקט זיי מיט אימעיל."
            )


def open_share_dialog() -> None:
    _ShareDecksDialog(mw).exec()


# -------------------------------------------------------------- באנר ב-DeckBrowser
_BANNER_HTML = """
<div id="beta-feedback-banner" dir="rtl" style="
    position: fixed; top: 0; left: 0; right: 0;
    z-index: 99999;
    box-sizing: border-box;
    padding: 3px 14px;
    background: linear-gradient(90deg,#fff8e1,#ffe0b2);
    border-bottom: 1px solid #ffb74d;
    color: #5d4037;
    font-family: inherit;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    line-height: 1.4;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
  <span>⚠️</span>
  <strong>__LABEL__</strong>
  <span style="flex:1;">דאס איז א פרואוו ווערסיע — באריכטן איבער פראבלעמען און פארבעסערונגען העלפן דעם אנטוויקלען. א דאנק! <small style="font-size:10px;color:#c62828;font-weight:700;">(מען קען אויסשאלטן דעם באנער אין די פרעפערענצן)</small></span>
  <button onclick='pycmd("beta_feedback:share_decks")' style="background:#43a047;color:#fff;border:none;border-radius:5px;padding:2px 10px;cursor:pointer;font-size:12px;">📦 טיילט פראגעס</button>
  <button onclick='pycmd("beta_feedback:bug")' style="background:#e53935;color:#fff;border:none;border-radius:5px;padding:2px 10px;cursor:pointer;font-size:12px;">🐞 באריכט א באג</button>
  <button onclick='pycmd("beta_feedback:suggestion")' style="background:#1e88e5;color:#fff;border:none;border-radius:5px;padding:2px 10px;cursor:pointer;font-size:12px;">💡 שיק א פארשלאג</button>
  <button title="פארמאך ביזן קומענדיגן אנהייבן" onclick='pycmd("beta_feedback:dismiss")' style="background:transparent;color:#5d4037;border:none;padding:0 6px;cursor:pointer;font-size:16px;line-height:1;font-weight:bold;">×</button>
</div>
<script>
(function(){
  var existing = document.getElementById('beta-feedback-banner-host');
  if (existing) return;
  var host = document.createElement('div');
  host.id = 'beta-feedback-banner-host';
  document.body.appendChild(host);
  var src = document.getElementById('beta-feedback-banner');
  if (src) host.appendChild(src);
  if (!src) { host.remove(); return; }
  // #280: wrapping changes the banner height when the window or fonts change.
  // A one-time measurement leaves either a gap or an overlap above the navbar.
  var body = document.body;
  if (window.__hafBetaBannerCleanup) window.__hafBetaBannerCleanup();
  var previousPadding = body.style.paddingTop;
  var observer = null;
  function updatePadding() {
    if (!src.isConnected) { cleanup(); return; }
    var padding = (Math.ceil(src.getBoundingClientRect().height) + 4) + 'px';
    if (body.style.paddingTop !== padding) body.style.paddingTop = padding;
  }
  function cleanup() {
    if (observer) observer.disconnect();
    window.removeEventListener('resize', updatePadding);
    body.style.paddingTop = previousPadding;
    if (window.__hafBetaBannerCleanup === cleanup) {
      delete window.__hafBetaBannerCleanup;
    }
  }
  window.__hafBetaBannerCleanup = cleanup;
  window.addEventListener('resize', updatePadding);
  if (window.ResizeObserver) {
    observer = new ResizeObserver(updatePadding);
    observer.observe(src);
  }
  updatePadding();
})();
</script>
"""


def _on_deck_browser_will_render_content(deck_browser, content) -> None:
    if not _is_beta_enabled() or _banner_dismissed:
        return
    try:
        # העדפת הבאנר נפרדת מהפעלת כלי הדיווח של גירסת הבטא.
        cfg = mw.addonManager.getConfig(_ADDON_MODULE_NAME) or {}
        if not cfg.get("show_beta_banner", True):
            return
        banner = _BANNER_HTML.replace("__LABEL__", html.escape(_BETA_VERSION_LABEL))
        content.tree = banner + (content.tree or "")
    except Exception:
        pass


def refresh_banner_preference() -> None:
    """ערלויבט ווידער צו ווייזן דעם באנער פון די פרעפערענצן, אויך נאך צייטווייליג פארמאכן אין×."""
    global _banner_dismissed
    _banner_dismissed = False
    if mw.state == "deckBrowser":
        mw.reset()


def _on_pycmd(handled: tuple[bool, Any], message: str, context: Any):
    if not isinstance(message, str):
        return handled
    if message == "beta_feedback:share_decks":
        open_share_dialog()
        return (True, None)
    if message == "beta_feedback:bug":
        open_bug_dialog()
        return (True, None)
    if message == "beta_feedback:suggestion":
        open_suggestion_dialog()
        return (True, None)
    if message == "beta_feedback:dismiss":
        global _banner_dismissed
        _banner_dismissed = True
        try:
            mw.web.eval(
                "(function(){"
                "if(window.__hafBetaBannerCleanup)window.__hafBetaBannerCleanup();"
                "else document.body.style.paddingTop='';"
                "var b=document.getElementById('beta-feedback-banner-host');"
                "if(b)b.remove();})();"
            )
        except Exception:
            pass
        return (True, None)
    return handled


# -------------------------------------------------------------- עטיפת showWarning / showCritical / showText
def _wrap_show_funcs() -> None:
    global _orig_showWarning, _orig_showCritical, _orig_showText, _orig_showInfo
    from aqt import utils as _au
    if _orig_showWarning is None:
        _orig_showWarning = _au.showWarning
    if _orig_showCritical is None:
        _orig_showCritical = _au.showCritical
    if _orig_showText is None:
        _orig_showText = _au.showText
    if _orig_showInfo is None:
        _orig_showInfo = _au.showInfo

    def _report_without_touching_console(text: str) -> None:
        # אישיו #408: שומרים עותק לדוח בלבד; stdout/stderr נשארים בשליטת Anki.
        _console_tail.append(str(text))
        _maybe_offer_report(str(text))

    def showWarning_wrapped(text, *args, **kwargs):
        if "Traceback" in str(text) and _is_beta_enabled():
            _report_without_touching_console(str(text))
            return
        return _orig_showWarning(text, *args, **kwargs)

    def showCritical_wrapped(text, *args, **kwargs):
        if "Traceback" in str(text) and _is_beta_enabled():
            _report_without_touching_console(str(text))
            return
        return _orig_showCritical(text, *args, **kwargs)

    def showText_wrapped(txt, *args, **kwargs):
        if "Traceback" in str(txt) and _is_beta_enabled():
            _report_without_touching_console(str(txt))
            return
        return _orig_showText(txt, *args, **kwargs)

    def showInfo_wrapped(txt, *args, **kwargs):
        if "Traceback" in str(txt) and _is_beta_enabled():
            _report_without_touching_console(str(txt))
            return
        return _orig_showInfo(txt, *args, **kwargs)

    _au.showWarning = showWarning_wrapped
    _au.showCritical = showCritical_wrapped
    _au.showText = showText_wrapped
    _au.showInfo = showInfo_wrapped


def _wrap_init_message_box() -> None:
    global _orig_init_message_box
    try:
        import aqt.errors
    except ImportError:
        return
    if _orig_init_message_box is None:
        if not hasattr(aqt.errors, "_init_message_box"):
            return
        _orig_init_message_box = aqt.errors._init_message_box

    def _init_message_box_wrapped(*args, **kwargs):
        if not _is_beta_enabled():
            return _orig_init_message_box(*args, **kwargs)
        debug_text = ""
        if len(args) > 1:
            debug_text = str(args[1])
        elif "debug_text" in kwargs:
            debug_text = str(kwargs["debug_text"])
        if debug_text:
            # אישיו #408: ErrorHandler מצורף לדוח בלי כתיבה נוספת לקונסול.
            _console_tail.append(debug_text)

        class DummyBox:
            def exec(self):
                _maybe_offer_report(debug_text, force=True)
            def show(self):
                _maybe_offer_report(debug_text, force=True)
            def addButton(self, *a, **k):
                class DummyBtn:
                    def setShortcut(self, *a, **k):
                        pass
                return DummyBtn()
        return DummyBox()

    aqt.errors._init_message_box = _init_message_box_wrapped


def _addon_load_context() -> tuple[bool, str]:
    """דערקענט צי showText ווערט אויפגערופן פון AddonManager.loadAddons און נעמט ארויס error_text לאקאל."""
    frame = inspect.currentframe()
    try:
        caller = frame.f_back if frame else None
        while caller is not None:
            code = caller.f_code
            if code.co_name == "loadAddons":
                fname = (code.co_filename or "").replace("\\", "/")
                if fname.endswith("aqt/addons.py"):
                    err = caller.f_locals.get("error_text", "")
                    return True, str(err or "")
            caller = caller.f_back
    except Exception:
        return False, ""
    finally:
        del frame
    return False, ""


def _wrap_addons_show_text() -> None:
    global _orig_addons_showText
    try:
        import aqt.addons as _addons
    except Exception:
        return
    if _orig_addons_showText is None:
        if not hasattr(_addons, "showText"):
            return
        _orig_addons_showText = _addons.showText

    def showText_addons_wrapped(*args, **kwargs):
        in_addon_load, addon_error_text = _addon_load_context()
        if not _is_beta_enabled() or not in_addon_load:
            return _orig_addons_showText(*args, **kwargs)
        report_text = addon_error_text.strip()
        if not report_text:
            report_text = str(args[0] if args else kwargs.get("txt", kwargs.get("text", "")))
        report_text = "Add-on startup failed:\n\n" + report_text
        # אישיו #408: שגיאת טעינת תוסף מצורפת לדוח בלי לשנות את פלט הקונסול המקורי.
        _console_tail.append(report_text)
        # #162 — הדיאלוג שלנו נפתח אחרי שה-loader משתחרר.
        QTimer.singleShot(0, lambda text=report_text: _maybe_offer_report(text, force=True))

        class _NoopSignal:
            def connect(self, *args, **kwargs):
                return None
        class _NoopButton:
            def __init__(self) -> None:
                self.clicked = _NoopSignal()
        class _NoopButtonBox:
            def addButton(self, *args, **kwargs):
                return _NoopButton()
        class _NoopDialog:
            def show(self):
                return None
            def exec(self):
                return None
            def close(self):
                return None
            def hide(self):
                return None
        return _NoopDialog(), _NoopButtonBox()

    _addons.showText = showText_addons_wrapped
    try:
        _addons.AddonManager.loadAddons.__globals__["showText"] = showText_addons_wrapped
    except Exception:
        pass


def _is_diagnostic_only(text: str) -> bool:
    """Recognize only standalone haf log records, never mixed/unhandled errors."""
    if "Traceback" in text:
        return False
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lines = [line for line in lines if not re.match(r"^(Anki \d|Python \d|Platform:)", line)]
    return bool(lines) and all(re.match(
        r"^(?:\[haf(?:\.[^\]]+)?\] (?:DEBUG|INFO|WARNING|ERROR|CRITICAL):|"
        r"(?:DEBUG|INFO|WARNING|ERROR|CRITICAL):haf(?:\.[^:]+)?:)", line
    ) for line in lines)


def _maybe_offer_report(text: str, force: bool = False) -> None:
    """ווייזט נאר איין באריכט פענסטער (פארמיידט א דאפלטן דורך א דגל)."""
    global _error_dialog_active, _last_error_fingerprint, _last_error_time
    if _error_dialog_active or not _is_beta_enabled():
        return
    if _is_diagnostic_only(text):
        _logger.info("Diagnostic output received by Anki error handler: %s", text)
        return
    if not force and "Traceback" not in text:
        return
    tracebacks = re.findall(
        r"Traceback \(most recent call last\):\n(?:[ \t].*\n|\n)*[^ \t\n][^\n]*(?:\n|$)",
        text.replace("\r\n", "\n"),
    )
    identity = "\n".join(dict.fromkeys(tracebacks)) if tracebacks else text
    fingerprint = hashlib.sha256(identity.encode("utf-8", errors="replace")).hexdigest()
    now = time.monotonic()
    if fingerprint == _last_error_fingerprint and now - _last_error_time < 5:
        return
    _last_error_fingerprint, _last_error_time = fingerprint, now
    _error_dialog_active = True
    try:
        open_error_dialog(text)
    except Exception:
        pass
    finally:
        _error_dialog_active = False


# -------------------------------------------------------------- excepthook
_orig_excepthook = None


def _install_excepthook() -> None:
    global _orig_excepthook
    if sys.excepthook.__name__ == "hook":
        return
    _orig_excepthook = sys.excepthook

    def hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        # אישיו #412: ה-hook המקורי של Anki נקרא תמיד; דיווח הבטא הוא עותק נוסף ולא תחליף.
        if _orig_excepthook:
            _orig_excepthook(exc_type, exc, tb)
        if not _is_beta_enabled():
            return
        try:
            _console_tail.append(text)
            _maybe_offer_report(text)
        except Exception:
            pass

    sys.excepthook = hook


# -------------------------------------------------------------- ErrorHandler.onTimeout wrapping
def _wrap_error_handler_on_timeout() -> None:
    """נעמט ארום ErrorHandler.onTimeout אלס שוץ — יעדער טעות וואס קומט דורך stderr וועט אויפגעכאפט ווערן."""
    try:
        import aqt.errors as _errs
    except ImportError:
        return
    _EH = getattr(_errs, "ErrorHandler", None)
    if _EH is None or not hasattr(_EH, "onTimeout"):
        return
    _orig = _EH.onTimeout

    def _on_timeout_wrapped(self):
        if not _is_beta_enabled():
            return _orig(self)
        _wrap_init_message_box()
        return _orig(self)
    _EH.onTimeout = _on_timeout_wrapped


# -------------------------------------------------------------- setup
_setup_done = False


def setup() -> None:
    global _setup_done
    if _setup_done:
        return
    _setup_done = True
    try:
        gui_hooks.deck_browser_will_render_content.append(_on_deck_browser_will_render_content)
    except Exception:
        pass
    try:
        gui_hooks.webview_did_receive_js_message.append(_on_pycmd)
    except Exception:
        pass
    for _fn in (
        _install_console_capture,
        _install_help_menu_bug_action,
        _wrap_show_funcs,
        _wrap_init_message_box,
        _wrap_addons_show_text,
        _wrap_error_handler_on_timeout,
        _install_excepthook,
    ):
        try:
            _fn()
        except Exception:
            _logger.exception("Feedback setup failed for %s", _fn.__name__)
    try:
        gui_hooks.profile_did_open.append(_install_excepthook)
    except Exception:
        pass
