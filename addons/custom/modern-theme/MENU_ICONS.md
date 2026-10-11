# Menu icon sources

The SVG geometry in `menu_icons.py` was created for this project from basic
geometric shapes. No external icon library, stock artwork, or Anki logo was used
as a drawing source. These drawings follow the code license of this add-on.

About uses a neutral information symbol, unrelated to Anki branding. Anki's own
About dialog and bundled logo files are not modified.

The module styles the main menus, browser menus, and browser table/header/sidebar
context menus. It changes only icons, never callbacks, shortcuts, or checked state.
Flag colors and the three synchronization states retain their meanings.
The default bronze (`#a27b50`) and neutral sync brown (`#947e69`) complement the
warm bookshelf colors of the main screen; blue/red sync indicators stay semantic.
Help SVGs are owned by `guides-framework/icons`; their topic groups use separators
without headings. Existing unrelated assets are not relicensed by this document.

Commands use purpose-specific drawings: books with a question mark for the question
bank, a page and pen for a new note, a circular arrow for refresh, paired arrows for
note-type conversion, an infinity loop for removing the daily limit, and a rising
curve for optimization. Specific Hebrew command labels take precedence over broad
keyword matching. Unknown actions retain their existing icons; there is no generic
square-plus fallback. Native commands continue to be identified by object name.

Display order uses descending rows and an arrow; the sidebar uses a narrow side
panel, and the toolbar a strip of controls. Automatic, vertical, and horizontal
layouts each have distinct geometry. Grade Now uses a score sheet with rising
rating marks instead of a checkmark.
