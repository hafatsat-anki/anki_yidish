# Copyright: (C) 2021 Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html


from aqt import mw

import contextlib

from aqt.qt import *



def garbage_collect_on_dialog_finish(dialog: QDialog):
    with contextlib.suppress(AttributeError):
        mw.garbage_collect_on_dialog_finish(dialog)


def disable_help_button(dialog: QDialog):
    try:
        from aqt.utils import disable_help_button as _disable_help_button
        _disable_help_button(dialog)
    except ImportError:
        pass


def tweak_window(dialog: QDialog) -> None:
    garbage_collect_on_dialog_finish(dialog)
    disable_help_button(dialog)






def menu_root_entry() -> QMenu:
    return mw.form.menuCol
    #return mw.form.ajt_root_menu


