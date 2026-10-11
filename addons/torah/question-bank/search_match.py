import re


_TOKEN_RE = re.compile(r"[\w\u0590-\u05ff]+", re.UNICODE)

# #193 v2 — Hebrew gematria letter set. A "gematria term" is a 1–3 letter
# Hebrew string built from these letters that corresponds to a typical perek
# or daf numbering (e.g. "א", "ב", "טו", "כא", "קיג"). When the user types
# such a term we treat it as a *number*, not as an abbreviation, and require
# an EXACT token match — so "שבת ק" will not be satisfied by the letter ק
# appearing inside another word, and to find "במה מדליקין" the user types
# the abbreviation "במ" which is NOT a valid gematria term (no tens letter).
_GEMATRIA_LETTERS = set("אבגדהוזחטיכךלמםנןסעפףצץקרשת")

_TENS_LETTERS = ["י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
_UNITS_LETTERS = ["א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
_HUNDREDS_LETTERS = ["ק", "ר", "ש", "ת"]
# Special spellings (avoid spelling the divine name): 15 = טו, 16 = טז.
_SPECIAL_TWO = {"טו", "טז"}


def _build_valid_gematria_terms() -> set[str]:
    valid: set[str] = set()
    # Single letters: all 22 Hebrew letters are valid (1–400 range).
    for letter in _GEMATRIA_LETTERS:
        valid.add(letter)
    # Two-letter combinations.
    valid.update(_SPECIAL_TWO)
    for tens in _TENS_LETTERS:
        for unit in _UNITS_LETTERS:
            combo = tens + unit
            if combo in {"יה", "יו"}:
                # 15 and 16 are spelled with the special forms above.
                continue
            valid.add(combo)
    for hundreds in _HUNDREDS_LETTERS:
        for unit in _UNITS_LETTERS:
            valid.add(hundreds + unit)
        for tens in _TENS_LETTERS:
            valid.add(hundreds + tens)
    # Three-letter combinations: hundred + tens + unit (e.g. קיג, קכד, רטו).
    for hundreds in _HUNDREDS_LETTERS:
        for tens in _TENS_LETTERS:
            for unit in _UNITS_LETTERS:
                combo = hundreds + tens + unit
                if tens == "י" and unit in {"ה", "ו"}:
                    continue
                valid.add(combo)
        for special in _SPECIAL_TWO:
            valid.add(hundreds + special)
    return valid


_VALID_GEMATRIA_TERMS = _build_valid_gematria_terms()


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text or "")]


def _is_ordered_subsequence(needle: str, haystack: str) -> bool:
    position = 0
    for character in needle:
        position = haystack.find(character, position)
        if position == -1:
            return False
        position += 1
    return True


def _is_gematria_term(term: str) -> bool:
    """Return True if *term* is a 1–3 Hebrew letter string that looks like a
    perek/daf number (e.g. "א", "טו", "קיג"). Such terms must match a token
    exactly rather than as an abbreviation."""
    if not term or len(term) > 3:
        return False
    if not all(ch in _GEMATRIA_LETTERS for ch in term):
        return False
    return term in _VALID_GEMATRIA_TERMS


def ordered_terms_match(search_text: str, filter_terms: list[str]) -> bool:
    """#193 v5 — match ordered terms with a gematria exception scoped to the
    *second-to-last* segment of the path only.

    The search text is typically a path like
    ``תורה::ש"ס::שבת::ק::שאלה כלשהי`` where the second-to-last
    ``::``-separated segment is the chapter (perek/daf) number. The gematria
    rule (chapter-token prefix match required) is applied ONLY to tokens in that
    segment; tokens in the last segment (the note title) and all earlier
    segments are treated with the normal ordered-subsequence rule.

        Examples (path ``ש"ס::שבת::ק::ב. מה מדליקין``):
            * ``["שבת", "ק"]`` matches ``...::ק::...``, ``...::קא::...`` and
                ``...::קב::...`` — ``ק`` is a gematria prefix in the chapter segment.
            * ``["שבת", "ק"]`` against ``ש"ס::שבת::ב::נקודות`` does NOT match —
                there is no ``ק`` prefix in the second-to-last segment.

    Non-gematria terms keep the original cross-token ordered subsequence
    behavior so quick abbreviations like ``במ`` → ``במה מדליקין`` still work.
    """
    terms = [term.lower() for term in filter_terms if term]
    if not terms:
        return True

    # #193 v5 — מפצלים את הנתיב לפי ``::`` כדי לזהות את מקטע מספר הפרק
    # (השני מהסוף). תוקף מיוחד לכלל הגימטריא חל רק על אסימונים במקטע זה.
    text = search_text or ""
    segments = text.split("::") if "::" in text else [text]
    # אוסף אסימונים עם תיוג: האם הם שייכים למקטע השני מהסוף (מספר הפרק).
    tagged_tokens: list[tuple[str, bool]] = []
    last_index = len(segments) - 1
    chapter_index = last_index - 1  # השני מהסוף — שם מספר הפרק
    for seg_index, segment in enumerate(segments):
        is_chapter = seg_index == chapter_index
        for token in _tokens(segment):
            tagged_tokens.append((token, is_chapter))

    token_index = 0
    has_chapter_segment = any(in_chapter for _token, in_chapter in tagged_tokens)
    for term_index, term in enumerate(terms):
        # במאגר השאלות חיפוש כמו "שב ק" צריך להשאיר את "שב" כקיצור של
        # "שבת", ורק את מונח הגימטריא המסיים ("ק") להצמיד למקטע הדף/פרק.
        is_chapter_gematria_lookup = (
            has_chapter_segment
            and len(terms) > 1
            and term_index == len(terms) - 1
            and _is_gematria_term(term)
        )
        matched = False
        while token_index < len(tagged_tokens):
            token, in_chapter = tagged_tokens[token_index]
            # כלל הגימטריא חל רק במקטע מספר הפרק/דף, ובו הוא התאמת תחילית:
            # "ק" מוצא גם "ק", "קא", "קב" וכו', בלי להיתפס למילים אחרות.
            if is_chapter_gematria_lookup:
                if in_chapter and token.startswith(term):
                    matched = True
                    token_index += 1
                    break
            else:
                if _is_ordered_subsequence(term, token):
                    matched = True
                    token_index += 1
                    break
            token_index += 1
        if not matched:
            return False
    return True