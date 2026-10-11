# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

# Built-in columns which are not sortable by default are made sortable here.
#
# Question/Answer columns are too slow so they are not handled.
# Note: the onData function of the columns is None as the data will still
# be fetched from the original source and that function is never reached.

from anki.cards import Card
from anki.consts import *
from anki.hooks import addHook
from aqt.utils import askUser


# #389 — תחליף לכתיבה ישירה לטבלת SQL זמנית: מפתחות/שמות קטנים מספיקים
# להיבנות כביטוי CASE עבור ORDER BY, בלי CREATE/INSERT דרך col.db.
def _case_sort(entries):
    clauses = " ".join(
        f"WHEN {condition} THEN {_sql_text(value)}"
        for condition, value in entries
    )
    return f"(CASE {clauses} ELSE NULL END) COLLATE NOCASE ASC NULLS LAST"


def _sql_text(value):
    return "'" + str(value).replace("'", "''") + "'"


class BasicFields:

    def onAdvBrowserLoad(self, advBrowser):
        """Called when the Advanced Browser add-on has finished
        loading. Create and add all custom columns owned by this
        module."""

        # Store a list of CustomColumns managed by this module. We later
        # use this to build our part of the context menu.
        self.customColumns = []

        def setData(c: Card, value: str):
            n = c.note()
            m = n.note_type()
            if m["type"] == MODEL_CLOZE:
                tmpl = m["tmpls"][0]
                tmpl_name = tmpl["name"]
                if not value.startswith(tmpl_name):
                    return False
                value = value[len(tmpl_name):]
                try:
                    c.ord = int(value)-1
                except ValueError:
                    return False
            else:
                value = value.strip().lower()
                right_tmpl = None
                for tmpl in m["tmpls"]:
                    if tmpl["name"].strip().lower() == value:
                        right_tmpl = tmpl
                        break
                if right_tmpl is None:
                    return False
                c.ord = right_tmpl["ord"]
            c.col.update_card(c)
            return True

        def sort_templates():
            entries = []
            for model in advBrowser.mw.col.models.all():
                templates = model['tmpls']
                for template in templates:
                    ord = template['ord']
                    name = templates[0]['name'] + f" {ord + 1}" if model['type'] == MODEL_CLOZE else template['name']
                    entries.append(
                        (f"n.mid = {int(model['id'])} AND c.ord = {int(ord)}", name)
                    )
            return _case_sort(entries)

        cc = advBrowser.newCustomColumn(
            type="template",
            name="קארטל",
            onData=None,
            onSort=sort_templates,
            setData=setData,
        )
        self.customColumns.append(cc)

        def setData(c: Card, value: str):
            n = c.note()
            n.setTagsFromStr(value)
            c.col.update_note(n)
            advBrowser.editor.loadNote()
            return True

        cc = advBrowser.newCustomColumn(
            type="noteTags",
            name="צעטלעך",
            onData=None,
            onSort=lambda: "(case when trim(n.tags) = '' then null else n.tags end) asc nulls last",
            setData=setData,
        )
        self.customColumns.append(cc)

        def sort_models():
            return _case_sort(
                (f"n.mid = {int(model['id'])}", model['name'])
                for model in advBrowser.mw.col.models.all()
            )

        cc = advBrowser.newCustomColumn(
            type="note",
            name="רשומות",
            onData=None,
            onSort=sort_models,
        )
        self.customColumns.append(cc)

        def sort_decks():
            return _case_sort(
                (f"c.did = {int(deck['id'])}", deck['name'])
                for deck in advBrowser.mw.col.decks.all()
            )
        cc = advBrowser.newCustomColumn(
            type="deck",
            name="פעקל",
            onData=None,
            onSort=sort_decks,
        )
        self.customColumns.append(cc)

        def setData(c: Card, value: str):
            value = value.strip()
            if value.endswith("%"):
                value = value[:-1]
            try:
                f = float(value)
            except ValueError:
                return False
            c.factor = f * 10
            c.col.update_card(c)
            return True

        cc = advBrowser.newCustomColumn(
            type="cardEase",
            name="גרינגקייט",
            onData=None,
            onSort=lambda: f"(case when type = {CARD_TYPE_NEW} then null else factor end) asc nulls last",
            setData=setData,
        )
        self.customColumns.append(cc)

        # fixme: to sort on this column, will need to write to a temp table
        # then sort based on that table, like in Anki's Rust code

        def setData(c: Card, value: str):
            if not c.odid:
                # only accept to change odid if there is already one
                return False
            new_deck = c.col.decks.byName(value)
            if new_deck is None:
                if not askUser(
                        f"{value} does not exists, do you want to create this deck ?", # Translation missing
                        parent=advBrowser,
                        defaultno=True):
                    return False
                new_id = c.col.decks.id(value)
                new_deck = c.col.decks.get(new_id)
            if new_deck["dyn"] == DECK_DYN:
                return False
            c.odid = new_deck["id"]
            c.col.update_card(c)
            return True

        cc = advBrowser.newCustomColumn(
            type="odeck",
            name="אריגינעלער פעקל",
            onData=lambda c, n, t: advBrowser.mw.col.decks.name(c.odid),
            onSort=lambda: _case_sort(
                (f"c.odid = {int(deck['id'])}", deck['name'])
                for deck in advBrowser.mw.col.decks.all()
            ),
            setData=setData,
        )
        self.customColumns.append(cc)

    def onBuildContextMenu(self, contextMenu):
        for cc in self.customColumns:
            contextMenu.addItem(cc)


bf = BasicFields()
addHook("advBrowserLoaded", bf.onAdvBrowserLoad)
addHook("advBrowserBuildContext", bf.onBuildContextMenu)
