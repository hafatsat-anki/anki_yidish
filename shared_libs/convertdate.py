from datetime import datetime

from .pyluach.dates import GregorianDate


def is_date(date_text: str) -> bool:
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def change_dates_to_heb(text: str) -> str:
    new_str = ''
    temp_str = ''
    i = 0
    while i < len(text) - 10:
        if is_date(text[i:i + 10]):
            new_str += temp_str + GregorianDate(
                int(text[i:i + 4]),
                int(text[i + 5:i + 7]),
                int(text[i + 8:i + 10]),
            ).to_heb().hebrew_date_string()
            temp_str = ''
            i += 10
        else:
            temp_str += text[i]
            i += 1
    return new_str + temp_str + text[-10:]


def convert_table_to_heb(value: str | None) -> str | None:
    if value is None:
        return None
    if is_date(value):
        parts = value.split("-")
        return GregorianDate(
            int(parts[0]), int(parts[1]), int(parts[2])
        ).to_heb().hebrew_date_string()
    if is_date(value[1:-1]):
        parts = value[1:-1].split("-")
        return "(" + GregorianDate(
            int(parts[0]), int(parts[1]), int(parts[2])
        ).to_heb().hebrew_date_string() + ")"
    return value
