from anki.consts import MODEL_CLOZE, MODEL_STD
from anki.notetypes_pb2 import ImageOcclusionField, StockNotetype
from aqt import mw

from _shared_libs.haf_logging import get_logger

from .config import *
from .packaging import version
from .templates.cloze_template08 import *
from .templates.few_q_sep_cards_template07 import *
from .templates.few_q_template06 import *
from .templates.hidden_source_template03 import *
from .templates.img_cloze_template09 import *
from .templates.multi_template10 import *
from .templates.standard_template01 import *
from .templates.standard_with_extended_template02 import *
from .templates.subject_and_source_template05 import *
from .templates.type_ans_template04 import *
from .yiddish_model_names import LEGACY_MODEL_NAMES

logger = get_logger("torah_cards")


first = False


# #158 — Anki מזהה Image Occlusion לפי תגיות שדה פנימיות, גם כשהשדות מתורגמים לעברית.
IMAGE_OCCLUSION_FIELD_TAGS = {
    "הסתרה": ImageOcclusionField.IMAGE_OCCLUSION_FIELD_OCCLUSIONS,
    "תמונה": ImageOcclusionField.IMAGE_OCCLUSION_FIELD_IMAGE,
    "כותרת": ImageOcclusionField.IMAGE_OCCLUSION_FIELD_HEADER,
    "תוספת לתשובה": ImageOcclusionField.IMAGE_OCCLUSION_FIELD_BACK_EXTRA,
    "הערות": ImageOcclusionField.IMAGE_OCCLUSION_FIELD_COMMENTS,
}


def _apply_image_occlusion_metadata(model, module):
    if module != "09img_cloze":
        return False
    changed = False
    original_kind = StockNotetype.OriginalStockKind.ORIGINAL_STOCK_KIND_IMAGE_OCCLUSION
    if model.get("originalStockKind") != original_kind:
        model["originalStockKind"] = original_kind
        changed = True
    for field in model.get("flds", []):
        tag = IMAGE_OCCLUSION_FIELD_TAGS.get(field.get("name"))
        if tag is None:
            continue
        if field.get("tag") != tag:
            field["tag"] = int(tag)
            changed = True
        should_prevent_deletion = tag != ImageOcclusionField.IMAGE_OCCLUSION_FIELD_COMMENTS
        if field.get("preventDeletion") != should_prevent_deletion:
            field["preventDeletion"] = should_prevent_deletion
            changed = True
    return changed


def _find_model(col, module):
    """Reuse the original note type rather than duplicating translated types."""
    names = (mdls[module]['model'],) + LEGACY_MODEL_NAMES.get(module, ())
    for name in names:
        model = col.models.by_name(name)
        if model is not None:
            return model
    return None


def getOrCreateModels(new_user=False):
    global first
    if not new_user:
        old_notetypes = (
            "00 - תורני כללי",
            "01 - תורני - נושאים",
            "02 - תורני - מקור מוסתר (משמש לבחינה גם על המקורות)",
            "03 - חמשה חומשי תורה",
            "04 - גמרא - מקור בשורה חדשה",
            "05 - גמרא - מקור באותה שורה",
            "07 - טור ושו''ע",
            "08 - שאלות בגמרא עם רמז וקישורים",
            "09 - בסיסי (הקלד את התשובה)",
            "10 - בסיסי (וכרטיס הופכי)",
            "12 - השלם את החסר",
            "13 - בסיסי",
            "14 - שאלות אמריקאיות ",
            "15 - שאלות ותשובות מרובות",
            "17 - שאלות ותשובות מרובות- כל שלב מוצג גם בתור שאלה נפרדת"
            )
        for ont in old_notetypes:
            model = mw.col.models.by_name(ont)
            if model:
                return
    modulesToImport = ('02standard_with_extended',
                       '03hidden_source',
                       '04type_ans',
                       '05subject_and_source',
                       '06few_q',
                       '07few_q_sep_cards',
                       '08cloze',
                       '09img_cloze',
                       '10multi',
                       '01standard' # מוכנס אחרון כדי שיופיע למשתמש כברירת מחדל
                       )
    for m in modulesToImport:
        model = _find_model(mw.col, m)
        if not model:
            if m == "07few_q_sep_cards" and mw.col.models.by_name("07 כמו 06 רק שכל שאלה מוצגת גם בתור המשך לשאלות הקודמות וגם בתור כרטיס נפרד (עד 9 כרטיסים)"):  # מונע ייבוא  לסוג כרטיס שאלות מרובות מחולקות במקרה שהותקנה גרסת אדר א תשפד
                updateTemplate(mw.col, m)
                continue
            # create model
            model = addModel(mw.col, m)
            first = True
            #return model
        if model['name'] != mdls[m]['model']:
            model['name'] = mdls[m]['model']
            mw.col.models.save(model)
            first = True
        if _apply_image_occlusion_metadata(model, m):
            mw.col.models.save(model)
            first = True
        model_version = mw.col.get_config('mc_conf')['version']
        if version.parse(model_version) < version.parse(default_conf_syncd['version']):
            updateTemplate(mw.col, m)
            first = True
    if first:
        mw.auto_make_editable()

        #return model

def addModel(col, module):
    """Add add-on note type to collection"""
    models = col.models
    #showInfo(str(module))
    #print(module)
    model = models.new(mdls[module]['model'])
    model['type'] = mdls[module]['type']
    srtfld = 0
    # Add fields:
    fields = mdls[module]['fields']
    for num, i in enumerate(fields):
        fld = models.new_field(fields[i])
        if "מקור" in fld['name'] or "מיקום" in fld['name'] or "מסכת ודף" in fld['name']:
            fld['sticky']=True
            srtfld = num
        fld['font']='Times New Roman'
        fld['size']=24
        fld['rtl']=True
        # #158 — שדות הסתרת תמונה מקבלים tag תואם גם כששם השדה בעברית.
        if module == "09img_cloze" and fields[i] in IMAGE_OCCLUSION_FIELD_TAGS:
            field_tag = IMAGE_OCCLUSION_FIELD_TAGS[fields[i]]
            fld["tag"] = int(field_tag)
            fld["preventDeletion"] = field_tag != ImageOcclusionField.IMAGE_OCCLUSION_FIELD_COMMENTS
        models.addField(model, fld)
    # Add template
    cards = mdls[module]['cards']
    for c in cards:
        template = models.new_template(cards[c]['card_name'])
        template['qfmt'] = cards[c]['card_front']
        template['afmt'] = cards[c]['card_back']
        model['css'] = cards[c]['card_css']
        model['sortf'] = srtfld  # set sortfield to question
        models.addTemplate(model, template)
    _apply_image_occlusion_metadata(model, module)
    models.add(model)
    return model

def updateTemplate(col, module):
    """Update add-on note templates"""
    logger.info(f"Updating {mdls[module]['model']} note template")
    model = _find_model(col, module)
    if model is None:
        return addModel(col, module)
    model['name'] = mdls[module]['model']
    fields = mdls[module]['fields']
    models = col.models
    fild = []
    srtfld = 0
    for num, i in enumerate(fields):
        fld = models.new_field(fields[i])
        if "מקור" in fld['name'] or "מיקום" in fld['name'] or "מסכת ודף" in fld['name'] or "פרשה ופרק" in fld['name'] or "סימן וסעיף" in fld['name']:
            fld['sticky']=True
            srtfld = num
        fld['font']='Times New Roman'
        fld['size']=24
        fld['ord']=num
        fld['rtl']=True
        # #158 — עדכון תבנית משמר גם את תגיות השדות של Image Occlusion.
        if module == "09img_cloze" and fields[i] in IMAGE_OCCLUSION_FIELD_TAGS:
            field_tag = IMAGE_OCCLUSION_FIELD_TAGS[fields[i]]
            fld["tag"] = int(field_tag)
            fld["preventDeletion"] = field_tag != ImageOcclusionField.IMAGE_OCCLUSION_FIELD_COMMENTS
        fild.append(fld)
        model["flds"]= fild
    #showInfo(str(fild))
    template = model['tmpls'][0]
    template['name'] = mdls[module]['cards']["card1"]['card_name']
    template['qfmt'] = mdls[module]['cards']["card1"]['card_front']
    template['afmt'] = mdls[module]['cards']["card1"]['card_back']
    # עדכון רשומה עם יותר מכרטיס 1
    tmpls_count = 1
    while tmpls_count < len(model['tmpls']):
        template = model['tmpls'][tmpls_count]
        tmpls_count += 1
        template['name'] = mdls[module]['cards'][f"card{tmpls_count}"]['card_name']
        template['qfmt'] = mdls[module]['cards'][f"card{tmpls_count}"]['card_front']
        template['afmt'] = mdls[module]['cards'][f"card{tmpls_count}"]['card_back']
        logger.info(f"Template count: {tmpls_count}")
    while len(model['tmpls']) < len(mdls[module]['cards']):
            tmpls_count += 1
            template = models.new_template(mdls[module]['cards'][f"card{tmpls_count}"]['card_name'])
            template['qfmt'] = mdls[module]['cards'][f"card{tmpls_count}"]['card_front']
            template['afmt'] = mdls[module]['cards'][f"card{tmpls_count}"]['card_back']
            models.addTemplate(model, template)

    model['css'] = mdls[module]['cards']["card1"]['card_css']
    model['type'] = mdls[module]['type']
    model['sortf'] = srtfld  # set sortfield to question
    _apply_image_occlusion_metadata(model, module)
    col.models.save(model)
    fild = []
    return model

mdls = {      "01standard": {"model": standard_model,
                    "cards": standard_cards,
                    "fields": standard_fields,
                    "type": MODEL_STD,
                      },
             "02standard_with_extended": {"model": standard_with_extended_model,
                    "cards": standard_with_extended_cards,
                    "fields": standard_with_extended_fields,
                    "type": MODEL_STD,
                      },
             "03hidden_source": {"model": hidden_source_model,
                    "cards": hidden_source_cards,
                    "fields": hidden_source_fields,
                    "type": MODEL_STD,
                       },
             "04type_ans": {"model": type_ans_model,
                    "cards": type_ans_cards,
                    "fields": type_ans_fields,
                    "type": MODEL_STD,
                       },
             "05subject_and_source": {"model": subject_and_source_model,
                    "cards": subject_and_source_cards,
                    "fields": subject_and_source_fields,
                    "type": MODEL_STD,
                        },
             "06few_q": {"model": few_q_model,
                    "cards": few_q_cards,
                    "fields": few_q_fields,
                    "type": MODEL_STD,
                      },
             "07few_q_sep_cards": {"model": few_q_sep_cards_model,
                    "cards": few_q_sep_cards_cards,
                    "fields": few_q_sep_cards_fields,
                    "type": MODEL_STD,
                         },
             "08cloze": {"model": cloze_model,
                    "cards": cloze_cards,
                    "fields": cloze_fields,
                    "type": MODEL_CLOZE  ,
                       },
             "09img_cloze": {"model": img_cloze_model,
                    "cards": img_cloze_cards,
                    "fields": img_cloze_fields,
                    "type": MODEL_CLOZE,
                        },
             "10multi": {"model": multi_model,
                    "cards": multi_cards,
                    "fields": multi_fields,
                    "type": MODEL_STD,
                            }
             }
