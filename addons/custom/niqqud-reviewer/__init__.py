"""
ניקוד ביים חזרן
לייגט צו א רעכטן מויז מעניו מיט העברעאישע ניקוד צייכנס ביים חזרן, ווי אינעם געווענליכן רעדאקטירער.
ווייזט זיך נאר ביים חזרן, און נאר ווען א פעלד contenteditable איז אקטיוו (רעדאקטירן דורך edit-field-review).
"""
from aqt import gui_hooks, mw
from aqt.qt import QAction

_is_editing = False  # True רק כשיש contenteditable ממוקד בסוקר

# JS שמוזרק בכל כרטיס — מאזין לפוקוס על contenteditable ומדווח לפייתון
_JS_TRACK = """
(function() {
    document.addEventListener('focusin', function(e) {
        if (e.target && e.target.isContentEditable) {
            pycmd('niqqud:editing_start');
        }
    }, true);
    document.addEventListener('focusout', function(e) {
        if (e.target && e.target.isContentEditable) {
            pycmd('niqqud:editing_end');
        }
    }, true);
})();
"""

# תווי ניקוד עברי: (תו, תצוגה בתפריט)
# הסדר והשמות זהים לתוסף "ניקוד וטעמי המקרא" (unicode-normalize_2065559429) בעורך
NIQQUD = [
    ("\u05B0", "פְ  שוא"),
    ("\u05B1", "פֱ  חטף סגול"),
    ("\u05B2", "פֲ  חטף פתח"),
    ("\u05B3", "פֳ  חטף קמץ"),
    ("\u05B4", "פִ  חיריק"),
    ("\u05B5", "פֵ  צירה"),
    ("\u05B6", "פֶ  סגול"),
    ("\u05B7", "פַ  פּתח"),
    ("\u05B8", "פָ  קמץ (גרויס)"),
    ("\u05B9", "פֹ  חולם (פול)"),
    ("\u05BA", "פֺ  חסר חולם"),
    ("\u05BB", "פֻ  קובוץ"),
    ("\u05BC", "פּ  דגש, מפיק, שורוק"),
    ("\u05C1", "שׁ  רעכטער שין"),
    ("\u05C2", "שׂ  לינקער שין"),
    ("\u05C7", "פׇ  קליינער קמץ"),
]

# טעמי המקרא: (תו, שם) — זהה לתוסף "ניקוד וטעמי המקרא" בעורך
TEAMIM = [
    ("\u0591", "א֑  אתנחתא"),
    ("\u0592", "א֒  סגולתא"),
    ("\u0593", "א֓  שלשלת"),
    ("\u0594", "א֔  קליינער זקף"),
    ("\u0595", "א֕  גרויסער זקף"),
    ("\u0596", "א֖  טיפחא"),
    ("\u0597", "א֗  רביע"),
    ("\u0598", "א֘  צינורית"),
    ("\u0599", "א֙  פשטא"),
    ("\u059A", "א֚  יתיב"),
    ("\u059B", "א֛  תביר"),
    ("\u059C", "א֜  גרש"),
    ("\u059D", "א֝  פריערדיגער גרש"),
    ("\u059E", "א֞  גרשיים"),
    ("\u059F", "א֟  קרני פרה"),
    ("\u05A0", "א֠  גרויסע תלישא"),
    ("\u05A1", "א֡  פזר"),
    ("\u05A2", "א֢  איבערגעקערטער אתנח"),
    ("\u05A3", "א֣  מונח"),
    ("\u05A4", "א֤  מהפך"),
    ("\u05A5", "א֥  מרכא"),
    ("\u05A6", "א֦  דאפלטע מרכא"),
    ("\u05A7", "א֧  דרגא"),
    ("\u05A8", "א֨  קדמא"),
    ("\u05A9", "א֩  קליינע תלישא"),
    ("\u05AA", "א֪  ירח בן יומו"),
    ("\u05AB", "א֫  עולה"),
    ("\u05AC", "א֬  עילוי"),
    ("\u05AD", "א֭  דחי"),
    ("\u05AE", "א֮  זרקא"),
    ("\u05AF", "א֯  רונדער מסורה צייכן"),
    ("\u05BD", "אֽ  מתג"),
    ("\u05C0", "א׀  פסק"),
    ("\u05BE", "א־  מקף"),
    ("\u05C3", "א׃  סוף פסוק"),
]


def _insert_niqqud(char: str) -> None:
    """לייגט אריין א ניקוד צייכן ביים סמן ביים חזרן."""
    code = ord(char)
    mw.reviewer.web.eval(
        f"document.execCommand('insertText', false, String.fromCharCode({code}));"
    )


def _inject_tracking(card) -> None:
    """לייגט אריין JS צו נאכפאלגן דעם פאקוס אויף contenteditable."""
    mw.reviewer.web.eval(_JS_TRACK)


def _handle_js_message(handled: tuple, message: str, context) -> tuple:
    global _is_editing
    if message == "niqqud:editing_start":
        _is_editing = True
        return (True, None)
    if message == "niqqud:editing_end":
        _is_editing = False
        return (True, None)
    return handled


def on_context_menu(webview, menu) -> None:
    """לייגט צו ניקוד און טעמי המקרא אונטערמעניוס צום רעכטן מויז מעניו ביים חזרן."""
    if mw.state != "review" or not mw.reviewer or webview is not mw.reviewer.web:
        return
    if not _is_editing:
        return
    niqqud_menu = menu.addMenu("ניקוד")
    for char, name in NIQQUD:
        action = QAction(name, menu)
        action.triggered.connect(lambda checked=False, c=char: _insert_niqqud(c))
        niqqud_menu.addAction(action)
    teamim_menu = menu.addMenu("טעמי המקרא")
    for char, name in TEAMIM:
        action = QAction(name, menu)
        action.triggered.connect(lambda checked=False, c=char: _insert_niqqud(c))
        teamim_menu.addAction(action)


gui_hooks.reviewer_did_show_question.append(_inject_tracking)
gui_hooks.reviewer_did_show_answer.append(_inject_tracking)
gui_hooks.webview_did_receive_js_message.append(_handle_js_message)
gui_hooks.webview_will_show_context_menu.append(on_context_menu)
