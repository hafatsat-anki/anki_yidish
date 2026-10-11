DEFAULT_CONFIGS = {
    'print_open': "Ctrl+Alt+Shift+F11",
    # #138 — ברירות מחדל לעריכה במהלך מבחן זמינות גם לפני שהן נטענות מקונפיג edit-field-review.
    'Qbold': "Ctrl+נ",
    'Qitalic': "Ctrl+ן",
    'Qunderline': "Ctrl+ו",
    # #269 — ברירות מחדל ריקות לקיצורי סגנונות מהירים במבחן; המשתמש מגדיר אותן ב-shortcut-manager.
    'review_style_preset_1_shortcut': "",
    'review_style_preset_2_shortcut': "",
    'review_style_preset_3_shortcut': "",
    'review_style_preset_4_shortcut': "",
    'review_style_preset_5_shortcut': "",
    # #359 — ברירת מחדל לקיצור פתיחת העורך המתקדם (external-editor); Ctrl+Shift+0 כדי
    # לא להתנגש עם "הגדר דגל 0" (Ctrl+0).
    'external_editor_open_advanced': "Ctrl+Shift+0",
    # #264 — ברירות מחדל של כפתורי bottom-bar מוצגות גם כשקונפיג התוסף עדיין לא נטען.
    'Button_Skip_Button': "ל",
    'Button_Info_Button': "מ",
    'Button_Undo_Button': "ח",
    'show_skipped': "ctrl+shift+ד",
    # #138 — ברירות מחדל לכל שבעת הדגלים גם אם config ישן טרם קיבל את המפתחות החדשים.
    'reviewer set flag 5': "Ctrl+5",
    'reviewer set flag 6': "Ctrl+6",
    'reviewer set flag 7': "Ctrl+7",
    'window_browser flag_red': "Ctrl+Shift+1",
    'window_browser flag_orange': "Ctrl+Shift+2",
    'window_browser flag_green': "Ctrl+Shift+3",
    'window_browser flag_blue': "Ctrl+Shift+4",
    'window_browser flag_pink': "Ctrl+5",
    'window_browser flag_turquoise': "Ctrl+6",
    'window_browser flag_purple': "Ctrl+7",
    'Ω enable conflict warning': "Y",
    'Ω enable editor': "Y",
    'Ω enable m_toolbox': "Y",
    'Ω enable main': "Y",
    'Ω enable reviewer': "Y",
    'Ω enable window_browser': "Y"
}


def complete_shortcut_config(config):
    """Supply introduced defaults without replacing saved or disabled shortcuts."""
    if not isinstance(config, dict):
        raise ValueError("shortcut-manager configuration must be a JSON object")
    result = {**DEFAULT_CONFIGS, **config}
    for key, default in DEFAULT_CONFIGS.items():
        if result[key] is None and default is not None:
            print(f"[shortcut-manager] Restoring null setting: {key}")
            result[key] = default
    return result
