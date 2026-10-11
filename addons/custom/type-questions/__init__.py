"""
Anki Add-on: Answer Input Box
Adds a text input box for writing answers during card review
Activated only by calling mw.reviewer.show_text_box()
"""


from aqt import gui_hooks, mw, theme
from aqt.qt import *
from PyQt6.QtCore import Qt
import unicodedata

# Configuration
CONFIG_KEY = "answer_input_addon_config"
DEFAULT_CONFIG = {
    "position": "bottom",  # "bottom", "left", "right"
    "height": 100,
    "width": 300,
    "enabled": False,  # כברירת מחדל לא פעיל
    "force_rtl": True   # תיבת הקלדה תמיד מימין לשמאל
}


class CustomTextEdit(QTextEdit):
    def __init__(self, force_rtl=False, parent=None):
        super().__init__(parent)
        self._force_rtl = force_rtl
        if force_rtl:
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def _enforce_rtl_block(self):
        """
        באשטימט די פאראגראף ריכטונג לויטן טעקסט אינהאלט:
        - העברעאיש/אראביש → RTL
        - ענגליש → LTR
        - נאר נייטראלע צייכנס (נומערן, פיסוק) → RTL אלס ברירת מחדל
        """
        cursor = self.textCursor()
        text = cursor.block().text()
        rtl = self._detect_direction(text)
        fmt = QTextBlockFormat()
        fmt.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if rtl
            else Qt.LayoutDirection.LeftToRight
        )
        cursor.mergeBlockFormat(fmt)

    @staticmethod
    def _detect_direction(text):
        """דערקענט די ריכטונג לויטן ערשטן שטארקן צייכן: RTL=העברעאיש, LTR=לאטייניש, נישט דא=RTL אלס ברירת מחדל."""
        for ch in text:
            bidi = unicodedata.bidirectional(ch)
            if bidi in ('R', 'AL', 'RLE', 'RLO'):   # עברית/ערבית
                return True
            if bidi in ('L', 'LRE', 'LRO'):          # לטינית
                return False
        return True  # ניטרלים בלבד (מספרים, נקודות) → RTL

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
            if mw.reviewer and mw.reviewer.web:
                mw.reviewer.web.setFocus()
        else:
            super().keyPressEvent(event)
            if self._force_rtl:
                self._enforce_rtl_block()


class AnswerInputAddon:
    def __init__(self):
        self.config = None
        self.input_widget = None
        self.container = None
        self.focus_shortcut = None
        self.setup_hooks()
        self.setup_external_trigger()
        self.setup_focus_shortcut()

    def load_config(self):
        """Load configuration from Anki's profile"""
        if not mw.pm or not mw.pm.profile:
            return DEFAULT_CONFIG.copy()

        saved = mw.pm.profile.get(CONFIG_KEY, {})
        if saved is None:
            print("[type-questions] Restoring null profile settings from defaults")
            saved = {}
        if not isinstance(saved, dict):
            raise ValueError("type-questions profile settings must be a dictionary")
        config = {**DEFAULT_CONFIG, **saved}
        for key, default in DEFAULT_CONFIG.items():
            if config[key] is None and default is not None:
                print(f"[type-questions] Restoring null setting: {key}")
                config[key] = default
        mw.pm.profile[CONFIG_KEY] = config
        return config

    def save_config(self):
        """Save configuration to Anki's profile"""
        if mw.pm and mw.pm.profile:
            mw.pm.profile[CONFIG_KEY] = self.config

    def get_config(self):
        """Get current configuration, loading if necessary"""
        if self.config is None:
            self.config = self.load_config()
        return self.config

    def setup_hooks(self):
        """Setup Anki hooks"""
        gui_hooks.reviewer_did_show_question.append(self.on_show_question)
        # gui_hooks.reviewer_did_show_answer.append(self.on_show_answer)
        gui_hooks.reviewer_did_show_question.append(self.on_will_show_question)
        gui_hooks.profile_did_open.append(self.on_profile_opened)
        gui_hooks.deck_browser_did_render.append(lambda a: self.hide_input_widget())
        gui_hooks.theme_did_change.append(self.on_theme_did_change)

    def on_theme_did_change(self):
        """Re-apply styles when the theme changes."""
        if self.input_widget and self.container:
            self.apply_styles()

    def on_profile_opened(self):
        """Called when profile is opened - load config"""
        self.config = self.load_config()

    def setup_external_trigger(self):
        """Setup external trigger function"""

        def toggle_text_box():
            """Function to toggle the text box on/off"""
            config = self.get_config()
            config["enabled"] = not config.get("enabled", False)
            self.config = config
            self.save_config()

            if config["enabled"]:
                # הצג את התיבה אם אנחנו במצב עיון
                if mw.state == "review" and mw.reviewer:
                    self.insert_input_widget()
                    self.return_focus_to_reviewer()
            else:
                # הסתר את התיבה
                self.hide_input_widget()

        # הוסף את הפונקציה ל-reviewer
        if hasattr(mw, 'reviewer') and mw.reviewer:
            mw.reviewer.show_text_box = toggle_text_box
        else:
            # אם reviewer עדיין לא קיים, הוסף אותו כאשר הוא נוצר
            def add_function_to_reviewer():
                if hasattr(mw, 'reviewer') and mw.reviewer:
                    mw.reviewer.show_text_box = toggle_text_box

            gui_hooks.profile_did_open.append(add_function_to_reviewer)

    # #263 — התיבה לא מקבלת פוקוס אוטומטי כדי שקיצורי הסקירה ימשיכו לעבוד; Ctrl+Space ממקד אותה לפי בקשת המשתמש.
    def setup_focus_shortcut(self):
        """Focus the answer input only when the user requests it."""
        if self.focus_shortcut:
            return
        self.focus_shortcut = QShortcut(QKeySequence("Ctrl+Space"), mw)
        self.focus_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.focus_shortcut.activated.connect(self.focus_input_widget)

    def focus_input_widget(self):
        """Focus the input widget while reviewing, if the box is enabled."""
        config = self.get_config()
        if mw.state != "review" or not config.get("enabled", False):
            return
        self.insert_input_widget()
        if self.input_widget:
            self.input_widget.setFocus()

    def return_focus_to_reviewer(self):
        """Keep normal reviewer shortcuts active after creating the text box."""
        if mw.reviewer and mw.reviewer.web:
            QTimer.singleShot(0, mw.reviewer.web.setFocus)

    def hide_input_widget(self):
        """Hide the input widget but keep the enabled state"""
        if self.container and self.container.parent():
            self.container.setParent(None)
            self.container = None
            self.input_widget = None

        # לא משנים את המצב enabled - רק מסתירים את הווידג'ט

    def create_input_widget(self):
        """Create the input text widget"""
        config = self.get_config()

        if not config.get("enabled", False):
            return

        if self.input_widget:
            return

        # Create container widget
        self.container = QWidget()
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create text input
        self.input_widget = CustomTextEdit(force_rtl=config.get("force_rtl", True))
        self.input_widget.setPlaceholderText("דריקט צו פאקוסירן Ctrl+Space")

        # Set size based on configuration
        if config["position"] == "bottom":
            self.input_widget.setFixedHeight(config["height"])
        else:
            self.input_widget.setFixedWidth(config["width"])
            self.input_widget.setMaximumHeight(300)
        layout.addWidget(self.input_widget)

        # Apply theme-aware styles
        self.apply_styles()

    def apply_styles(self):
        """Apply styles based on the current Anki theme (light/dark mode)."""
        if not self.input_widget or not self.container:
            return

        is_night_mode = theme.theme_manager.night_mode

        if is_night_mode:
            # Dark theme colors
            bg_color = "#3a3a3a"
            container_bg_color = "#2a2a2a"
            border_color = "#555"
            focus_border_color = "#00aaff"
            text_color = "#f0f0f0"
            focus_bg_color = "#444444"
        else:
            # Light theme colors (original)
            bg_color = "#f9f9f9"
            container_bg_color = "#f0f0f0"
            border_color = "#ccc"
            focus_border_color = "#4CAF50"
            text_color = "#000000"
            focus_bg_color = "white"

        self.input_widget.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {border_color};
                border-radius: 5px;
                padding: 2px;
                font-size: 14px;
                background-color: {bg_color};
                color: {text_color};
            }}
            QTextEdit:focus {{
                border-color: {focus_border_color};
                background-color: {focus_bg_color};
            }}
        """)

        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: {container_bg_color};
                border-radius: 8px;
                margin: 0;
            }}
        """)

    def insert_input_widget(self):
        """Insert the input widget in the reviewer"""
        config = self.get_config()

        if not config.get("enabled", False):
            return

        if not mw.reviewer or not mw.reviewer.web:
            return

        self.create_input_widget()
        if not self.container:
            return

        reviewer_widget = mw.reviewer.web.parentWidget()
        if not reviewer_widget:
            return

        layout = reviewer_widget.layout()
        if not layout:
            layout = QVBoxLayout(reviewer_widget)
            reviewer_widget.setLayout(layout)

        if self.container.parent():
            self.container.setParent(None)

        position = config.get("position", "bottom")

        if position == "bottom":
            index = max(0, layout.count() - 1)
            layout.insertWidget(index, self.container)
        elif position in ("left", "right"):
            if not isinstance(layout, QHBoxLayout):
                old_layout = layout
                new_layout = QHBoxLayout(reviewer_widget)

                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item.widget():
                        new_layout.addWidget(item.widget())

                reviewer_widget.setLayout(new_layout)
                layout = new_layout

            if position == "left":
                layout.insertWidget(0, self.container)
            else:
                layout.addWidget(self.container)
        else:
            layout.addWidget(self.container)

    def on_show_question(self, card):
        """Called when showing a question - only show if enabled"""
        config = self.get_config()
        if not config.get("enabled", False):
            return

        self.insert_input_widget()
        self.return_focus_to_reviewer()


    def on_will_show_question(self, card):
        """Called before showing next question - clear the input"""
        if self.input_widget:
            self.input_widget.clear()


# Initialize the addon
addon = AnswerInputAddon()
