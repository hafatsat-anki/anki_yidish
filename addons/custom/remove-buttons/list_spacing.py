"""Compact list spacing in editable fields and reviewer card content (#418)."""
from aqt import gui_hooks


# #418 — Browser defaults add 1em above/below lists (24px in the reported
# field). Scope the rules to field/card content; retain indentation, line
# height, explicit blank lines and the existing day/night colors.
def _rules(scope):
    return f"""
{scope} ul, {scope} ol {{ margin-block: 0 !important; }}
{scope} li, {scope} li > p {{ margin-block: 0 !important; }}
"""


# #418 — Editor fields live in separate shadow roots. Place the stylesheet
# beside anki-editable, never inside its saved HTML or in the outer document.
EDITOR_JS = """(() => {
    for (const host of document.querySelectorAll('.rich-text-editable')) {
        const root = host.shadowRoot;
        if (!root || root.getElementById('haf-list-spacing')) continue;
        const style = document.createElement('style');
        style.id = 'haf-list-spacing';
        style.textContent = %s;
        root.appendChild(style);
    }
})();""" % repr(_rules("anki-editable"))


def apply_editor(editor):
    editor.web.eval(EDITOR_JS)


def apply_card(html, card, kind):
    # #418 — card_will_show also handles subsequent questions/answers without
    # touching the navbar, stored note HTML or note-type templates.
    return '<style id="haf-card-list-spacing">' + _rules("#qa") + '</style>' + html


_installed = False


def install():
    global _installed
    if _installed:
        return
    gui_hooks.editor_did_load_note.append(apply_editor)
    gui_hooks.card_will_show.append(apply_card)
    _installed = True
