import aqt.preferences
from anki.decks import DeckId
from anki.hooks import wrap
from aqt import VideoDriver, gui_hooks, mw, toolbar
from aqt.operations.deck import add_deck_dialog
from aqt.reviewer import Reviewer
from anki.errors import NotFoundError
from aqt.toolbar import HideMode
from aqt.utils import *

from .deck_browser import nav  #,DECK_NAME_TODAY
from .utils import AddCard


def top_bar_hide_mode(*args):
    if mw.pm.top_bar_hide_mode() == 1:
        mw.reviewer.web.eval('''
                    (function() {
                        var navbar = document.getElementsByClassName("anki-navbar")[0];
                        if (navbar) navbar.className = navbar.className.replace("fullscreen", " ");
                    })();
                    //document.getElementsByClassName("bar")[0].className = document
                    //	.getElementsByClassName("bar")[0]
                    //	.className.replace("fullscreen", " ");
                    ''')

gui_hooks.reviewer_did_init.append(top_bar_hide_mode)






def _revHtml(self) -> str:
    extra = self.mw.col.conf.get("reviewExtra", "")
    fade = ""
    hide_nav_script = ""
    if mw.pm.top_bar_hide_mode() == 1:
        hide_nav_script = '<script>(function(){var navbar=document.getElementsByClassName("anki-navbar")[0]; if (navbar) navbar.classList.toggle("fullscreen", true); document.body.style.marginTop = "1vw";})();</script>'
    if self.mw.pm.video_driver() == VideoDriver.Software:
        fade = "<script>qFade=0;</script>"
    return nav("reviewer") +f"""
    <div id="_mark" hidden>&#x2605;</div>
    <div id="_flag" hidden>&#x2691;</div>
    {fade}
    <div id="qa"></div>
    {extra}
    {hide_nav_script}
    """

def hide_top_bar():
    mw.reviewer.web.eval('''
                var navbar = document.getElementsByClassName("anki-navbar")[0];
                if (navbar) navbar.classList.toggle("fullscreen", true);
                document.body.style.marginTop = "1vw";
                ''')

def show_top_bar():
    mw.reviewer.web.eval('''
                var navbar = document.getElementsByClassName("anki-navbar")[0];
                if (navbar) navbar.classList.toggle("fullscreen", false);
                document.body.style.marginTop = "unset";
                    ''')


def update_top_bar_hide_mode(self=None, _old=None) -> None:
    if mw.state != "review":
        return
    if mw.pm.hide_top_bar():
        if (
            mw.pm.top_bar_hide_mode() == HideMode.FULLSCREEN
            and not mw.windowState() & Qt.WindowState.WindowFullScreen
        ):
            show_top_bar()
            return
        else:
            hide_top_bar()

        return
    show_top_bar()


toolbar.TopWebView.hide_if_allowed = wrap(toolbar.TopWebView.hide_if_allowed, update_top_bar_hide_mode, "around")
gui_hooks.body_classes_need_update.append(update_top_bar_hide_mode)


def _link_Handler(self, url: str) -> None:
        if ":" in url:
            (cmd, arg) = url.split(":", 1)
        else:
            cmd = url
        if cmd == "menuCol":
            mw.form.menuCol.exec(QCursor.pos())
        elif cmd == "deckBrowser":
            mw.moveToState("deckBrowser")
        elif cmd == "add_deck":
            if op := add_deck_dialog(parent=mw):
                op.run_in_background()
        elif cmd == "FilteredDialog":
            aqt.dialogs.open("FilteredDeckConfigDialog", aqt.mw)
        elif cmd == "AddCard":
            mw.onAddCard()
        elif cmd == "onBrowse":
            aqt.dialogs.open("Browser", mw, card=self.card)
        elif cmd == "Stats":
            mw.onStats()
        elif cmd == "menu_Help":
            mw.form.menuHelp.exec(QCursor.pos())
        elif cmd == "browser_search":
            inBrowser(str(arg))
        elif cmd == "Add_deck_Card":
            AddCard(DeckId(int(arg)))
        else:
            return #_old(self, url)


def _refresh_if_needed(self, _old):
        try:
            return _old(self)
        except NotFoundError:
            # #181 — כרטיס שנמחק בדפדוף בזמן מבחן לא קיים יותר; יוצאים למסך הראשי במקום לרענן cid מת.
            try:
                self.card = None
                mw.moveToState("deckBrowser")
            except Exception:
                pass

def inBrowser(find):
    browser = aqt.dialogs.open("Browser", aqt.mw)
    browser.search_for(f"{find}")
    browser.update_history()


def renderReviewer():
    Reviewer.revHtml = wrap (Reviewer.revHtml , _revHtml)
    Reviewer._linkHandler = wrap (Reviewer._linkHandler , _link_Handler, "before")
    Reviewer.refresh_if_needed = wrap(Reviewer.refresh_if_needed, _refresh_if_needed, "around")
    # Reviewer.nextCard = wrap (Reviewer.nextCard , _nextCard, "around")

################$%^&*&^%$



#הסתרת הסרגל מתצוגה מקדימה בדפדוף ומתוצגת פריסת הכרטיסים

from aqt.sound import AVPlayer

av_player = AVPlayer()

def _setup_preview(self, _old) -> None:
    # #287 — Anki 25 בונה Previewer מורכב; החלפה ידנית של ה-WebView גורמת למסך אפור. מריצים מקור ומסתירים רק navbar מיותרת.
    _old(self)
    try:
        self.preview_web.eval("""
            (function() {
                var navbar = document.querySelector('.anki-navbar');
                if (navbar) navbar.style.display = 'none';
            })();
        """)
    except Exception:
        pass

aqt.clayout.CardLayout.setup_preview = wrap(aqt.clayout.CardLayout.setup_preview, _setup_preview, "around")


def setup_web_view(self, _old) -> None:
    # #287 — תצוגה מקדימה בדפדפן נשארת של Anki; כך לא מאבדים טעינת כרטיס ו-WebView לא נשאר אפור.
    _old(self)
    try:
        self._web.eval("""
            (function() {
                var navbar = document.querySelector('.anki-navbar');
                if (navbar) navbar.style.display = 'none';
            })();
        """)
    except Exception:
        pass

aqt.browser.previewer.Previewer._setup_web_view = wrap(aqt.browser.previewer.Previewer._setup_web_view, setup_web_view, "around")
