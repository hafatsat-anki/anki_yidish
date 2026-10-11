"""#161: one selection implementation for editor and reviewer WebViews."""
_WEB_PATH = "/_addons/_shared_libs/web/rtl_editing.js"


def inject_rtl_editing(web_content):
    """Load before addon scripts through Anki's CSP-approved addon endpoint."""
    from aqt import mw

    # EDITOR pages reject inline scripts. Registration works for shared_libs
    # even though Anki deliberately does not load it as a standalone addon.
    mw.addonManager.setWebExports("_shared_libs", r"web/rtl_editing\.js")
    marker = 'id="haf-rtl-editing"'
    if marker not in web_content.head:
        web_content.head += f'<script {marker} src="{_WEB_PATH}"></script>'
