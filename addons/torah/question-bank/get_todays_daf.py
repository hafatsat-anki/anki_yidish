from datetime import date, datetime, timedelta

from aqt import mw

LETTERS_TO_NUM_GEMATRIOS = {
    'א': 1,
    'ב': 2,
    'ג': 3,
    'ד': 4,
    'ה': 5,
    'ו': 6,
    'ז': 7,
    'ח': 8,
    'ט': 9,
    'י': 10,
    'כ': 20,
    'ל': 30,
    'מ': 40,
    'נ': 50,
    'ס': 60,
    'ע': 70,
    'פ': 80,
    'צ': 90,
    'ק': 100,
    'ר': 200,
    'ש': 300,
    'ת': 400
}

def letters_to_num(letters):
    val = 0
    for letter in letters:
        convreted_letter = LETTERS_TO_NUM_GEMATRIOS.get(letter)
        val += convreted_letter if convreted_letter is not None else 0
    return val

_GEMATRIOS = {
    1: 'א',
    2: 'ב',
    3: 'ג',
    4: 'ד',
    5: 'ה',
    6: 'ו',
    7: 'ז',
    8: 'ח',
    9: 'ט',
    10: 'י',
    20: 'כ',
    30: 'ל',
    40: 'מ',
    50: 'נ',
    60: 'ס',
    70: 'ע',
    80: 'פ',
    90: 'צ',
    100: 'ק',
    200: 'ר',
    300: 'ש',
    400: 'ת'
}

mesekhtot = {
    "ברכות": 63,
    "שבת": 156,
    "עירובין": 104,
    "פסחים": 120,
    "שקלים": 21,
    "יומא": 87,
    "סוכה": 55,
    "ביצה": 39,
    "ראש השנה": 34,
    "תענית": 30,
    "מגילה": 31,
    "מועד קטן": 28,
    "חגיגה": 26,
    "יבמות": 121,
    "כתובות": 111,
    "נדרים": 90,
    "נזיר": 65,
    "סוטה": 48,
    "גיטין": 89,
    "קידושין": 81,
    "בבא קמא": 118,
    "בבא מציעא": 118,
    "בבא בתרא": 175,
    "סנהדרין": 112,
    "מכות": 23,
    "שבועות": 48,
    "עבודה זרה": 75,
    "הוריות": 13,
    "זבחים": 119,
    "מנחות": 109,
    "חולין": 141,
    "בכורות": 60,
    "ערכין": 33,
    "תמורה": 33,
    "כריתות": 27,
    "מעילה": 21,
    "קינים": 4,
    "תמיד": 8,
    "מדות": 3,
    "נדה": 72
}


def _stringify_gematria(letters):
    """Insert geresh or gershayim symbols into gematria."""
    length = len(letters)
    if length > 1:
        # return '{}״{}'.format(letters[:-1], letters[-1])
        return f'{letters[:-1]}{letters[-1]}'
    if length == 1:
        # return '{}׳'.format(letters)
        return f'{letters}'
    return ''


def _get_letters(num):
    """Convert numbers under 1,000 into raw letters."""
    ones = num % 10
    tens = num % 100 - ones
    hundreds = num % 1000 - tens - ones
    four_hundreds = ''.join(['ת' for i in range(hundreds // 400)])
    ones = _GEMATRIOS.get(ones, '')
    tens = _GEMATRIOS.get(tens, '')
    hundreds = _GEMATRIOS.get(hundreds % 400, '')
    letters = f'{four_hundreds}{hundreds}{tens}{ones}'
    letters = letters.replace("יה", "טו") \
                .replace("יו", "טז") \
                .replace("קיה", "קטו") \
                .replace("ריה", "רטו") \
                .replace("שיה", "שטו") \
                .replace("תיה", "תטו") \
                .replace("תקיה", "תקטו") \
                .replace("תריה", "תרטו") \
                .replace("תשיה", "תשטו") \
                .replace("תתיה", "תתטו") \
                .replace("קיו", "קטז") \
                .replace("ריו", "רטז") \
                .replace("שיו", "שטז") \
                .replace("תיו", "תטז") \
                .replace("תקיו", "תקטז") \
                .replace("תריו", "תרטז") \
                .replace("תשיו", "תשטז") \
                .replace("תתיו", "תתטז") \
                .replace("שמד", "שדמ") \
                .replace("רצח", "רחצ") \
                .replace("תרצח", "תרחצ") \
                .replace("רעב", "ערב") \
                .replace("רעה", "ערה") \
                .replace("אאכל המסכת", "כל המסכת") \
                .replace("אאפרק", "פרק")
    if letters.endswith("רע.txt"):
        letters = letters.replace("רע", "ער",)
    return letters


def _num_to_str(num, thousands=False):
    """Return gematria string for number.

    Parameters
    ----------
    num : int
        The number to get the Hebrew letter representation
    thousands : bool, optional
        True if the hebrew returned should include a letter for the
        thousands place ie. 'ה׳' for five thousand.

    Returns
    -------
    str
        The Hebrew representation of the number.
    """
    # letters = _stringify_gematria(_get_letters(num))
    letters = _get_letters(num)
    if thousands:
        thousand = _get_letters(num // 1000) + '׳'
        letters = thousand + letters
    return letters


# currdate = date(2020, 1,5)
# currdate = date.today()
def today_daf(daf_date=None) -> tuple:
    first_cycle = date(1923, 9, 23)
    scheduling = mw.col.conf.get("rollover", 4)
    delta = timedelta(hours=scheduling)
    if daf_date is not None:
        cur = daf_date
    else:
        cur = date.today() - timedelta(days=1) if datetime.today().hour < delta.seconds // 3600 else date.today()
    days_since = cur - first_cycle
    days_since = days_since.days
    total_dapim = sum(mesekhtot.values())
    dapim_in_current_cycle = days_since % total_dapim
    dapim_in_current_cycle += 63
    dapim_in_current_cycle += 12

    for _count, (mesekhta, pages) in enumerate(mesekhtot.items(), start=1):
        # print(count)
        if dapim_in_current_cycle < pages:
            if mesekhta == "קינים":
                dapim_in_current_cycle += 21
            if mesekhta == "תמיד":
                dapim_in_current_cycle += 25
            if mesekhta == "מדות":
                dapim_in_current_cycle += 33
            return (mesekhta, _num_to_str(dapim_in_current_cycle + 2, False))
            # break
        dapim_in_current_cycle = dapim_in_current_cycle - pages
    return ("ברכות", _num_to_str(dapim_in_current_cycle + 2, False))
