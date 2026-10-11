"""א סימון קעסטל שפאלט אינעם דורכבלעטערער דורך API דער אפיציעלער שפאלט מערכת פון Anki."""

from __future__ import annotations

# אישיו #455: קבועי הקונפיג מאפשרים לעדכן מצב לא פעיל בלי לשנות את עמודות ה-backend.
from anki.browser import BrowserConfig, BrowserDefaults
from anki.collection import BrowserColumns
from aqt import gui_hooks, mw
from aqt.browser.table import CellRow, ItemId
from aqt.qt import (
    QApplication,
    QByteArray,
    QEvent,
    QHeaderView,
    QItemSelectionModel,
    QModelIndex,
    QObject,
    QPainter,
    QPen,
    QPointF,
    QRect,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionHeader,
    QStyleOptionViewItem,
    Qt,
    QTimer,
    QWidget,
)

_COLUMN_KEY = "haf_browser_checkbox"
_PROFILE_INITIALIZED_KEY = "browser_checkboxes.official_column_initialized_v3"
_CHECKBOX_SIZE = 13
_CHECKBOX_COLUMN_WIDTH = 22
_HEADER_CHECK_LABEL = "☑"


def _save_browser_layout(browser) -> None:
    """זיכערט אפ דעם טאבעלע קעפל מצב אינעם פראפיל, אן ארומצונעמען דאס פארמאכן דעם פענסטער."""
    profile = getattr(browser.mw.pm, "profile", None)
    if not isinstance(profile, dict):
        return
    header = browser.form.tableView.horizontalHeader()
    profile["haf_browser_header_state"] = bytes(header.saveState()).hex()
    browser.mw.pm.save()


# אישיו #401: הגדרת העזר נשמרת לצד ה-hook כדי ששחזור הפריסה לא יגרום NameError.
def _restore_browser_layout(browser) -> None:
    """ברענגט צוריק דעם טאבעלע קעפל, אויב א גילטיגער מצב איז אפגעזיכערט."""
    profile = getattr(browser.mw.pm, "profile", None)
    if not isinstance(profile, dict) or getattr(browser, "_closeEventHasCleanedUp", False):
        return
    state_hex = profile.get("haf_browser_header_state")
    if not isinstance(state_hex, str) or not state_hex:
        return
    try:
        state = bytes.fromhex(state_hex)
    except ValueError:
        # מצב שמור פגום אינו צריך למנוע פתיחת דפדפן.
        return
    browser.form.tableView.horizontalHeader().restoreState(QByteArray(state))


def _add_checkbox_column(columns: dict) -> None:
    """שרייבט איין דעם סימון שפאלט אין דער אפיציעלער שפאלט מערכת פון Anki."""
    columns[_COLUMN_KEY] = BrowserColumns.Column(
        key=_COLUMN_KEY,
        cards_mode_label=_HEADER_CHECK_LABEL,
        notes_mode_label=_HEADER_CHECK_LABEL,
        sorting_cards=BrowserColumns.SORTING_NONE,
        sorting_notes=BrowserColumns.SORTING_NONE,
        uses_cell_font=False,
        alignment=BrowserColumns.ALIGNMENT_CENTER,
    )


def _fill_checkbox_cell(
    _item: ItemId,
    _is_notes_mode: bool,
    row: CellRow,
    active_columns: list[str],
) -> None:
    """לאזט דעם צעל אינהאלט ליידיג; דערdelegate מאלט דעם סימון לויט דער אויסגעקליבענער שורה."""
    # אישיו #455: כשהעמודה כבויה אין תא סימון לעדכן; חוסר סנכרון נבדק בנפרד בהמשך.
    if _COLUMN_KEY not in active_columns:
        return
    # אישיו #455: חוסר התאמה בין מספר העמודות הפעילות למספר תאי ה-backend הוא
    # שגיאת סנכרון אמיתית; לא מסתירים אותה ב-IndexError אלא דורשים את האינווריאנט.
    # אישיו #455: השוואת מספר התאים למספר העמודות הפעילות.
    if len(row.cells) != len(active_columns):
        # אישיו #455: דיווח מפורש על חוסר סנכרון במקום בליעת שגיאה.
        raise RuntimeError(
            # אישיו #455: פירוט אי־התאמה בין תאי ה־backend לעמודות הדפדוף.
            "די דורכבלעטערער שפאלטן זענען נישט סינכראניזירט: "
            # אישיו #455: השוואת מספר התאים למספר העמודות הפעילות.
            f"active={len(active_columns)}, cells={len(row.cells)}"
        # אישיו #455: סיום הגדרת הנתונים או הפרמטרים של הפעולה באישיו.
        )
    # אישיו #455: ניקוי טקסט תא הסימון כדי שהציור יתבצע ב־delegate.
    row.cells[active_columns.index(_COLUMN_KEY)].text = ""


def _active_column_index(browser) -> int | None:
    try:
        return browser.table._model.active_column_index(_COLUMN_KEY)
    except (AttributeError, RuntimeError):
        return None


class _CheckboxDelegate(QStyledItemDelegate):
    """מאלט א לאקאלן סימון קעסטל נאר אינעם שפאלט."""

    def paint(
        self,
        painter: QPainter | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        if painter is None:
            return
        super().paint(painter, option, index)

        # אישיו #413: המלבן מחושב מתוך כל שטח התא ומשאיר שוליים קטנים בלבד.
        # כך Qt מקבל מספיק מקום לציור הוי גם בסקיילינג של Windows.
        cell = option.rect.adjusted(1, 1, -1, -1)
        size = max(10, min(_CHECKBOX_SIZE, cell.width(), cell.height()))
        checkbox = QStyleOptionButton()
        checkbox.rect = QRect(
            cell.left() + (cell.width() - size) // 2,
            cell.top() + (cell.height() - size) // 2,
            size,
            size,
        )
        checkbox.state = QStyle.StateFlag.State_Enabled
        checkbox.state |= (
            QStyle.StateFlag.State_On
            if option.state & QStyle.StateFlag.State_Selected
            else QStyle.StateFlag.State_Off
        )
        QApplication.style().drawControl(
            QStyle.ControlElement.CE_CheckBox,
            checkbox,
            painter,
        )


class _CheckboxHeaderMark(QWidget):
    """מאלט דעם סימון איבערן קעפל, אן זיך צו ווענדן אין דער טעקסט אויסשטעל פונעם סטיל."""

    def __init__(self, browser) -> None:
        header = browser.form.tableView.horizontalHeader()
        super().__init__(header.viewport())
        self.header = header
        self.browser = browser
        self._moving_section = False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.header.sectionResized.connect(self.sync_geometry)
        self.header.sectionMoved.connect(self.sync_geometry)
        self.header.geometriesChanged.connect(self.sync_geometry)
        self.header.viewport().installEventFilter(self)
        self.header.installEventFilter(self)
        browser.form.tableView.horizontalScrollBar().valueChanged.connect(self.sync_geometry)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.LayoutDirectionChange,
        ):
            self.sync_geometry()
        return False

    def sync_geometry(self, *_args) -> None:
        if self._moving_section:
            return
        column = _active_column_index(self.browser)
        if column is None or self.header.isSectionHidden(column):
            self.hide()
            return
        # האינדקס החזותי הראשון נמצא מימין ב-RTL ומשמאל ב-LTR.
        target = (
            0
            if self.header.layoutDirection() == Qt.LayoutDirection.RightToLeft
            else self.header.count() - 1
        )
        current = self.header.visualIndex(column)
        if current != target:
            self._moving_section = True
            try:
                self.header.moveSection(current, target)
            finally:
                self._moving_section = False
        # ב-LTR עמודת הסימון היא האחרונה; מתיחה אוטומטית גוברת על Fixed.
        if target == self.header.count() - 1 and self.header.stretchLastSection():
            self.header.setStretchLastSection(False)
        self.setGeometry(
            self.header.sectionViewportPosition(column),
            0,
            self.header.sectionSize(column),
            self.header.viewport().height(),
        )
        self.show()
        self.raise_()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        column = _active_column_index(self.browser)
        if column is None:
            return
        painter = QPainter(self)
        option = QStyleOptionHeader()
        option.initFrom(self.header)
        option.rect = self.rect()
        option.section = column
        option.orientation = Qt.Orientation.Horizontal
        option.sortIndicator = QStyleOptionHeader.SortIndicator.None_
        # מציירים רקע אטום לפני הכותרת הריקה כדי להסתיר גם את הגליף המקורי.
        painter.fillRect(self.rect(), self.header.palette().button())
        painter.save()
        self.header.style().drawControl(
            QStyle.ControlElement.CE_Header, option, painter, self.header
        )
        painter.restore()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.header.palette().color(self.header.foregroundRole()))
        pen.setWidthF(1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        center = self.rect().center()
        x, y = center.x(), center.y()
        # צ׳קבוקס גאומטרי ממורכז, ללא תלות בגליף או בשולי הטקסט.
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRect(x - 6, y - 6, 12, 12), 2, 2)
        painter.drawLine(QPointF(x - 4, y), QPointF(x - 1, y + 3))
        painter.drawLine(QPointF(x - 1, y + 3), QPointF(x + 4, y - 3))
        painter.end()


class _CheckboxClickFilter(QObject):
    """א דרוק אינעם קעסטל טוישט די שורה אויסוואל; א דרוק אויפן קעפל צייכנט אן אדער נעמט אוועק דעם סימון פון אלעם."""

    def __init__(self, browser) -> None:
        super().__init__(browser)
        self.browser = browser
        self.view = browser.form.tableView

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 - שם API של Qt
        try:
            # אישיו #401: אירוע הסגירה שומר את הכותרת בלי לעטוף את Browser.closeEvent.
            if watched is self.browser and event.type() == QEvent.Type.Close:
                _save_browser_layout(self.browser)
                return False
            if watched is self.view.viewport():
                if event.type() in (
                    QEvent.Type.MouseButtonPress,
                    QEvent.Type.MouseButtonRelease,
                    QEvent.Type.MouseButtonDblClick,
                ) and event.button() == Qt.MouseButton.LeftButton:
                    return self._handle_cell(event)
            elif watched is self.view.horizontalHeader().viewport():
                if event.type() in (
                    QEvent.Type.MouseButtonPress,
                    QEvent.Type.MouseButtonRelease,
                    QEvent.Type.MouseButtonDblClick,
                ) and event.button() == Qt.MouseButton.LeftButton:
                    return self._handle_header(event)
        except (AttributeError, RuntimeError):
            return False
        return False

    def _handle_cell(self, event) -> bool:
        column = _active_column_index(self.browser)
        index = self.view.indexAt(event.pos())
        if column is None or not index.isValid() or index.column() != column:
            return False
        if event.type() == QEvent.Type.MouseButtonPress:
            self.view.selectionModel().select(
                index,
                QItemSelectionModel.SelectionFlag.Toggle
                | QItemSelectionModel.SelectionFlag.Rows,
            )
        return True

    def _handle_header(self, event) -> bool:
        column = _active_column_index(self.browser)
        if column is None:
            return False
        header = self.view.horizontalHeader()
        if header.logicalIndexAt(event.pos()) != column:
            return False

        # אישיו #413: אזור ידית שינוי הרוחב נשאר בידי Anki ואינו נחשב לחיצה על הסימון.
        x = event.pos().x()
        left = header.sectionViewportPosition(column)
        right = left + header.sectionSize(column)
        grip = max(
            4,
            header.style().pixelMetric(
                QStyle.PixelMetric.PM_HeaderGripMargin,
                None,
                header,
            ),
        )
        if x - left < grip or right - x < grip:
            return False

        if event.type() == QEvent.Type.MouseButtonRelease:
            selection = self.view.selectionModel()
            if len(selection.selectedRows()) < self.view.model().rowCount():
                self.view.selectAll()
            else:
                self.view.clearSelection()
        return True


def _enable_column_once(browser) -> None:
    """צינדט אן דעם שפאלט איינמאל אלס ברירת מחדל, און דערנאך פאלגט דעם באניצער אויסוואל."""
    if mw.pm.profile.get(_PROFILE_INITIALIZED_KEY):
        return

    col = browser.mw.col
    # אישיו #455: קריאת מצב העמודות שמוצג כעת בדפדוף.
    state = browser.table._state

    # אישיו #455: את המצב הפעיל משנים רק דרך מודל Anki, כדי שה-state וה-backend
    # יתעדכנו יחד. קריאת load של שני המצבים ברצף השאירה בעבר את ה-backend במצב האחר.
    # אישיו #455: בדיקת קיום עמודת הסימון לפני עדכון המצב הפעיל.
    if _COLUMN_KEY not in state.active_columns:
        browser.table._model.toggle_column(_COLUMN_KEY)

    # אישיו #455: את המצב שאינו מוצג מעדכנים ישירות בקונפיג בלבד; כך לא משנים
    # את active_browser_columns של ה-backend בזמן שהטבלה עדיין מציגה את המצב הפעיל.
    # אישיו #455: זיהוי המצב המוצג כדי לבחור את הגדרת המצב האחר.
    if state.is_notes_mode():
        # אישיו #455: בחירת מפתח עמודות הכרטיסים כאשר מוצגות רשומות.
        inactive_key = BrowserConfig.ACTIVE_CARD_COLUMNS_KEY
        # אישיו #455: בחירת ברירות המחדל לעמודות הכרטיסים.
        inactive_default = BrowserDefaults.CARD_COLUMNS
    # אישיו #455: בחירת המסלול החלופי כאשר התנאי הקודם אינו מתקיים.
    else:
        # אישיו #455: בחירת מפתח עמודות הרשומות כאשר מוצגים כרטיסים.
        inactive_key = BrowserConfig.ACTIVE_NOTE_COLUMNS_KEY
        # אישיו #455: בחירת ברירות המחדל לעמודות הרשומות.
        inactive_default = BrowserDefaults.NOTE_COLUMNS
    # אישיו #455: קריאת עמודות המצב האחר מהקונפיג בלי לשנות את ה־backend.
    inactive_columns = list(col.get_config(inactive_key, inactive_default))
    # אישיו #455: הוספת עמודת סימון למצב האחר רק אם היא חסרה.
    if _COLUMN_KEY not in inactive_columns:
        # אישיו #455: צירוף עמודת הסימון לרשימת העמודות של המצב האחר.
        inactive_columns.append(_COLUMN_KEY)
        # אישיו #455: שמירת עמודות המצב האחר דרך API הקונפיג של Anki.
        col.set_config(inactive_key, inactive_columns)

    mw.pm.profile[_PROFILE_INITIALIZED_KEY] = True
    mw.pm.save()


def _install_column_ui(browser) -> None:
    """שטעלט איין delegate און פילטערט דעם דרוק נאר צום סימון שפאלט."""
    column = _active_column_index(browser)
    view = browser.form.tableView
    previous = getattr(browser, "_haf_checkbox_delegate_column", None)
    if previous is not None and previous != column:
        view.setItemDelegateForColumn(previous, None)
    browser._haf_checkbox_delegate_column = column
    if column is None:
        mark = getattr(browser, "_haf_checkbox_header_mark", None)
        if mark is not None:
            mark.hide()
        return

    delegate = getattr(browser, "_haf_checkbox_delegate", None)
    if delegate is None:
        delegate = _CheckboxDelegate(view)
        browser._haf_checkbox_delegate = delegate
    view.setItemDelegateForColumn(column, delegate)

    header = view.horizontalHeader()
    if getattr(browser, "_haf_checkbox_header_mark", None) is None:
        browser._haf_checkbox_header_mark = _CheckboxHeaderMark(browser)
    # אישיו #413: העמודה נשארת צרה; רק העמודה שלנו מקבלת את הרוחב המינימלי שלה.
    if header.minimumSectionSize() > _CHECKBOX_COLUMN_WIDTH:
        header.setMinimumSectionSize(_CHECKBOX_COLUMN_WIDTH)
    header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
    if header.sectionSize(column) != _CHECKBOX_COLUMN_WIDTH:
        header.resizeSection(column, _CHECKBOX_COLUMN_WIDTH)
    browser._haf_checkbox_header_mark.sync_geometry()


def _on_browser_will_show(browser) -> None:
    # אישיו #401: אין lifecycle patch; נשמר רק QHeaderView של הטבלה, בנפרד מסרגל הצד.
    _restore_browser_layout(browser)
    if getattr(browser, "_haf_checkbox_filter", None) is not None:
        QTimer.singleShot(0, lambda: _install_column_ui(browser))
        return

    _enable_column_once(browser)
    click_filter = _CheckboxClickFilter(browser)
    browser._haf_checkbox_filter = click_filter
    # אישיו #401: המסנן על החלון משמש רק לשמירת מצב הכותרת בעת סגירה.
    browser.installEventFilter(click_filter)
    browser.form.tableView.viewport().installEventFilter(click_filter)
    browser.form.tableView.horizontalHeader().viewport().installEventFilter(click_filter)

    browser.form.tableView.model().modelReset.connect(
        lambda: QTimer.singleShot(0, lambda: _install_column_ui(browser))
    )
    QTimer.singleShot(0, lambda: _install_column_ui(browser))


gui_hooks.browser_did_fetch_columns.append(_add_checkbox_column)
gui_hooks.browser_did_fetch_row.append(_fill_checkbox_cell)
gui_hooks.browser_will_show.append(_on_browser_will_show)
