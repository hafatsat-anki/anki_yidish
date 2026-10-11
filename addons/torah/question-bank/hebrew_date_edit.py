"""Hebrew date selection; Gregorian QDate values are internal only."""
from aqt.qt import QComboBox, QDate, QHBoxLayout, QPushButton, QWidget, pyqtSignal

try:
    from _shared_libs.pyluach.dates import GregorianDate, HebrewDate
    from _shared_libs.pyluach.hebrewcal import Month, Year
except ModuleNotFoundError as error:
    if error.name != "_shared_libs":
        raise
    # Source-tree tools and isolated development fixtures (not deployed Anki).
    from shared_libs.pyluach.dates import GregorianDate, HebrewDate
    from shared_libs.pyluach.hebrewcal import Month, Year


def hebrew_date(value):
    if isinstance(value, str):
        value = QDate.fromString(value, "yyyy-MM-dd")
    return GregorianDate(value.year(), value.month(), value.day()).to_heb()


def date_label(value):
    return hebrew_date(value).hebrew_date_string(True)


class HebrewDateEdit(QWidget):
    dateChanged = pyqtSignal(QDate)

    def __init__(self, value, parent=None):
        super().__init__(parent)
        self._date = value
        self._today = value
        self._minimum = QDate(1900, 1, 1)
        self._maximum = QDate(2100, 12, 31)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.day_combo, self.month_combo, self.year_combo = (QComboBox() for _ in range(3))
        for combo, name in ((self.day_combo, "טאג"), (self.month_combo, "חודש"), (self.year_combo, "יאר")):
            combo.setAccessibleName(name)
            combo.setToolTip(name)
            layout.addWidget(combo)
            combo.currentIndexChanged.connect(self._selected)
        today = QPushButton("היינט")
        today.clicked.connect(lambda: self.setDate(self._today))
        layout.addWidget(today)
        self._refresh()

    def date(self):
        return self._date

    def minimumDate(self):
        return self._minimum

    def maximumDate(self):
        return self._maximum

    def setDateRange(self, minimum, maximum):
        if not minimum.isValid() or not maximum.isValid() or minimum > maximum:
            raise ValueError("אומגילטיגער דאטום פארנעם")
        self._minimum, self._maximum = minimum, maximum
        self.setDate(self._date)

    def setDate(self, value):
        if not value.isValid():
            return
        value = max(self._minimum, min(self._maximum, value))
        changed = value != self._date
        self._date = value
        self._refresh()
        if changed:
            self.dateChanged.emit(value)

    def _refresh(self):
        current = hebrew_date(self._date)
        for combo in (self.day_combo, self.month_combo, self.year_combo):
            combo.blockSignals(True)
            combo.clear()
        for year in range(hebrew_date(self._minimum).year, hebrew_date(self._maximum).year + 1):
            self.year_combo.addItem(HebrewDate(year, 7, 1).hebrew_year(True), year)
        self.year_combo.setCurrentIndex(self.year_combo.findData(current.year))
        for month in Year(current.year):
            self.month_combo.addItem(Month(current.year, month).month_name(True), month)
        self.month_combo.setCurrentIndex(self.month_combo.findData(current.month))
        for day in range(1, len(Month(current.year, current.month)) + 1):
            self.day_combo.addItem(HebrewDate(current.year, current.month, day).hebrew_day(), day)
        self.day_combo.setCurrentIndex(self.day_combo.findData(current.day))
        for combo in (self.day_combo, self.month_combo, self.year_combo):
            combo.blockSignals(False)

    def _selected(self, *_):
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        day = self.day_combo.currentData()
        if None in (year, month, day):
            return
        if month == 13 and not Year(year).leap:
            month = 12
        day = min(day, len(Month(year, month)))
        gregorian = HebrewDate(year, month, day).to_greg()
        self.setDate(QDate(gregorian.year, gregorian.month, gregorian.day))
