import anki
from anki.hooks import wrap
from anki.models import ModelManager
from aqt import gui_hooks, mw

from .templates.anki_daf import *
from .templates.anki_daf_cloze import *
from .templates.chafetz_chaim import *
from .templates.mishna_berura import *
from .templates.standard_template01 import *

olds = ["תת_לשימוש_המאגר_המוכן_משנב"]
mdls = {
    "תת - שאלה רגילה - (לשימוש המאגר)":
        {"model": standard_model,
         "cards": standard_cards,
         "fields": standard_fields,
         "type": 0,
         },
    "תת_לשימוש_המאגר_המוכן_משנב":
        {"model": mb_model,
         "cards": mb_cards,
         "fields": mb_fields,
         "type": 0,
         },
    "תת_לשימוש_המאגר_המוכן_חפץ_חיים":
        {"model": cc_model,
         "cards": cc_cards,
         "fields": cc_fields,
         "type": 0,
         },
    "AnkiDaf":
        {"model": ad_model,
         "cards": ad_cards,
         "fields": ad_fields,
         "type": 0,
         },
    "Anki-Daf-cloze":
        {"model": "adc_model",
         "cards": adc_cards,
         "fields": adc_fields,
         "type": 1,
         }
}

repo_notetypes_names = mdls.keys()

def on_p_strt(*args):
    for ntn in repo_notetypes_names:
        getOrCreateModels(mw.col, ntn)
gui_hooks.profile_did_open.append(on_p_strt)


def getOrCreateModels(col, model_to_add):
    current_model = mw.col.conf["curModel"]  # לשמור על הרשומה האחרונה שהתווספה כברירת מחדל.
    # model = col.models.by_name(mdls[model_to_add]['model']) # משום מה לא קולט חלק מהרשומות ולכן בדיקה אם קיים נעשתה בצורה אחרת וכדלהלן
    notetype_names = list(col._backend.get_notetype_names())
    all_notetypes = []
    for notetype in notetype_names:
        all_notetypes.append(notetype.name)
    # if not model:
    if model_to_add not in all_notetypes:
        addModel(col, model_to_add)
    mw.col.conf["curModel"] = current_model  # לשמור על הרשומה האחרונה שהתווספה כברירת מחדל.


def addModel(col, module):
    """Add add-on note type to collection"""
    models = col.models
    model = models.new(module)
    model['type'] = mdls[module]['type']
    srtfld = 0
    # Add fields:
    fields = mdls[module]['fields']
    for num, i in enumerate(fields):
        fld = models.new_field(fields[i])
        if fld['name'] in ("מיקום (חלק סימן וסעיף)", "מקור"):
            fld['sticky'] = True
            srtfld = num
        fld['font'] = 'Times New Roman'
        fld['size'] = 24
        fld['rtl'] = True
        models.add_field(model, fld)
    # Add template
    cards = mdls[module]['cards']
    for c in cards:
        template = models.new_template(cards[c]['card_name'])
        template['qfmt'] = cards[c]['card_front']
        template['afmt'] = cards[c]['card_back']
        model['css'] = cards[c]['card_css']
        model['sortf'] = srtfld  # set sortfield to question
        models.add_template(model, template)
    models.add(model)
    return model


def all_names_and_ids_without_repo(self: ModelManager):
    notetype_names = list(self.col._backend.get_notetype_names())
    # הצורך בלעשות את הסינון עם רשימה נפרדת הוא משום שבסינון מהרשימה המקורית חלק מהרשומות לא מזוהות משום מה.
    filtered_notetypes = []
    for notetype_name in notetype_names:
        if notetype_name.name in repo_notetypes_names:
            continue
        filtered_notetypes.append(notetype_name)
    return filtered_notetypes


anki.models.ModelManager.all_names_and_ids = wrap(anki.models.ModelManager.all_names_and_ids,
                                                  all_names_and_ids_without_repo)

