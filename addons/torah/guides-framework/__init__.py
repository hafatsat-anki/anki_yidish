
import os
import re
import sys
from urllib.parse import unquote, urlsplit

import aqt
from anki.hooks import wrap

# ייבואים של Anki
from aqt import gui_hooks, mw
from aqt.qt import QAction as AnkiQAction
from aqt.utils import qconnect, showInfo, showText, tooltip
from PyQt6.QtCore import QFileInfo, Qt, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings

# ייבוא רכיבי ווב
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow

from _shared_libs.haf_logging import get_logger

logger = get_logger("guides_framework")

# --- הגדרות נתיבים ---
try:
    ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    ADDON_DIR = os.path.dirname(os.path.abspath(sys.argv[0] if sys.argv else '.'))

LOCAL_DOCS_DIR = "docs_ankiweb_net"
LOCAL_MANUAL_DIR = os.path.join(LOCAL_DOCS_DIR, "manual")
LOCAL_FAQ_DIR = os.path.join(LOCAL_DOCS_DIR, "faq")
# --- תוכן HTML קבוע (ללא שינוי, קוצר לצורך נוחות הקריאה) ---
tech_support_html = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            text-align: center;
        }

        .header h1 {
            font-size: 24px;
            margin: 0;
        }

        .content {
            padding: 20px;
        }

        h2 {
            font-size: 20px;
            color: #28406e;
            margin: 10px 0 8px;
            padding-bottom: 5px;
            border-bottom: 2px solid #e1e8f0;
        }

        h3 {
            font-size: 16px;
            margin: 8px 0 6px;
            color: #4a6fa5;
        }

        p {
            margin-bottom: 8px;
            line-height: 1.4;
            font-size: 14px;
        }

        .email-button {
            display: inline-block;
            padding: 8px 16px;
            background-color: #4a6fa5;
            color: white;
            border-radius: 6px;
            margin: 5px auto;
            transition: all 0.3s;
            text-align: center;
            text-decoration: none;
            font-weight: bold;
            font-size: 14px;
        }

        .email-button:hover {
            background-color: #28406e;
            transform: translateY(-2px);
        }

        .email-container {
            text-align: center;
            margin: 8px 0;
        }

        .highlight {
            font-weight: bold;
            color: #1e3355;
        }

        .note {
            background-color: #f8f9fa;
            padding: 10px;
            border-right: 4px solid #4a6fa5;
            margin: 10px 0;
            font-size: 14px;
        }

        .footer {
            background-color: #e1e8f0;
            padding: 12px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }

        .section {
            margin-bottom: 20px;
        }

        .compact-spacing {
            line-height: 1.3;
        }

    </style>
</head>
<body>
    <!-- תמיכה טכנית -->
    <div class="container">
        <div class="header">
            <h1>טעכנישע שטיצע</h1>
        </div>
        <div class="content">
            <div class="section">
                <h3>די ווערסיע פון אנקי ווערט פארשפרייט דורך "הפצת אנקי" פאר די עמלי התורה שליט"א</h3>

                <p>פאר הילף, טעכנישע שטיצע און טעות באריכטן קענט איר שיקן אן אימעיל צו:</p>
                <div class="email-container">
                    <a href="mailto:anki4tora@gmail.com" class="email-button">anki4tora@gmail.com</a>
                </div>

                <p>צו באקומען אונזער נייסטע ווערסיע, קענט איר שיקן אן אימעיל צו:</p>
                <div class="email-container">
                    <a href="mailto:3422973@gmail.com" class="email-button">3422973@gmail.com</a>
                </div>

                <p>צו באקומען א מעלדונג ווען א נייע ווערסיע קומט ארויס בעז"ה, שיקט דאס ווארט "עדכונים" צו:</p>
                <div class="email-container">
                    <a href="mailto:anki4tora@gmail.com?subject=%D7%A2%D7%93%D7%9B%D7%95%D7%A0%D7%99%D7%9D" class="email-button">anki4tora@gmail.com</a>
                </div>

                <div class="note compact-spacing">
                    <span class="highlight">אכטונג! כאטש די שיטה פון דער פראגראם האט זיך שוין באוויזן,</span><br>
                    <span class="highlight">דאך פארבייט די פראגראם נישט חזרן פון דער גמרא, נאר זי העלפט נאך מער מיט ידיעת התורה.</span>
                </div>

                <p class="compact-spacing"><span class="highlight">בברכת התורה.</span><br>
                    "הפצת אנקי."<br>
                    פראגראם ווערסיע: כד תשרי תשפז.
                </p>
            </div>
        </div>
        <div class="footer">
            <h3>© אלע רעכטן אויף די צוגאב פארבעסערונגען און אנדערע אנטוויקלונגען פון "הפצת אנקי" זענען רעזערווירט.</h3>
            לויט די תנאים פונעם AGPL3 לייסענס.
        </div>
    </div>
"""

dict_text = """
        .dictionary-term {
            font-weight: bold;
            color: #28406e;
        }

        .dictionary-item {
            margin-bottom: 8px;
            border-bottom: 1px dashed #e1e8f0;
            padding-bottom: 8px;
            font-size: 14px;
        }

        .dictionary-item:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ווערטערבוך פון אנקי באגריפן</h1>
        </div>
        <div class="content">
            <div class="dictionary-item">
                <span class="dictionary-term">"זאמלונג"</span> - אלע באניצער דאטן פונעם יעצטיגן פראפיל.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"פראפיל"/"באניצער"</span> – טיילט אפ פארשידענע באניצער אין דער פראגראם, כדי יעדער זאל האבן אייגענע איינשטעלונגען, סארטן קארטלעך, פעקלעך און דאטן.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"פעקל" = נושא</span> - יעדע שאלה דארף געהערן צו א נושא. למשל, שאלות אויף מסכת ב"ב וועלן זיין אינעם פעקל "ב"ב".
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">אונטערפעקל:</span> א נושא וואס געהערט אונטער אן אנדערן נושא, למשל פרק השותפין אין ב"ב.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">רשומה:</span> דער אינהאלט פון דער שאלה און תשובה פון וועלכן די קארטלעך ווערן געשאפן.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">סארט רשומה:</span> דער סארט רשומה באשטימט וויאזוי די שאלה ווערט געוויזן. למשל: אויספילן דאס אויסגעלאזטע.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">קארטל:</span> די שאלה וואס ווערט געוויזן ביים לערנען, געשאפן פון א רשומה.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"ברידער":</span> צוויי קארטלעך וואס געהערן צו דער זעלבער רשומה.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"פעלד":</span> א טייל פונעם קארטל, למשל "שאלה", "תשובה", "מקור" אאז"וו.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"תזמון":</span> באשטימען דעם צייט אפשטאנד צווישן דער יעצטיגער חזרה און דער קומענדיגער.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"נאכאמאל":</span> א ציון וואס מיינט "איך ווייס נישט". די פראגראם הייבט דעמאלט אן די חזרות פון דער שאלה פון פריש.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">באזייטיגן ביז מארגן:</span> אפשטופן די שאלה ביז מארגן.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">אפשטעלן:</span> אפשטעלן די שאלה פונעם חזרות סדר ביז איר ברענגט זי צוריק אינעם "דורכבלעטערן" פענצטער.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"געפילטערטער" פעקל:</span> א פעקל אן אייגענע קארטלעך, וואס אנטהאלט קארטלעך פון אנדערע פעקלעך.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"צוגעפאסט לערנען":</span> חזרן אויסער דעם געווענליכן חזרות סדר.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">קארטל צושטאנד "ניי"</span> - א געשריבן קארטל אויף וועלכן מען האט נאך נישט געחזרט
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">קארטל צושטאנד "לערנען"</span> - א קארטל מיטן ציון נאכאמאל אדער א נייעס קארטל וואס האט בלויז איין חזרה.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">קארטל צושטאנד "חזרה"</span> - א קארטל נאך דער "לערנען" שטאפל, וואס געפינט זיך אינעם געווענליכן חזרות סדר.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"יונגער" קארטל</span> - א קארטל מיט א צייט אפשטאנד פון ווייניגער ווי דריי וואכן.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"ערוואקסענער" קארטל</span> - א קארטל מיט א צייט אפשטאנד פון מער ווי דריי וואכן.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">א קארטל וואס האלט צוריק:</span> א קארטל וואס האט עטליכע מאל באקומען דעם ציון "נאכאמאל".
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"צעטל":</span> פארבינדן די שאלה מיט נאך נושאים אויסער דעם נושא פונעם פעקל.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"ציון":</span> די לעצטע חזרה/לערנען וואו איר האט געגעבן א ציון פארן קארטל.
            </div>

            <div class="dictionary-item">
                <span class="dictionary-term">"גרינגקייט":</span> באשטימען ווי שווער די שאלה איז.
            </div>
        </div>
    </div>
"""

phone_info_html = """
        .phone-number {
            font-size: 20px;
            font-weight: bold;
            color: #28406e;
            margin: 10px 0;
            display: block;
            text-align: center;
        }

        .secondary-phone {
            font-size: 16px;
            color: #4a6fa5;
            display: block;
            text-align: center;
            margin: 6px 0;
        }

        .note {
            background-color: #f8f9fa;
            padding: 10px;
            border-right: 4px solid #4a6fa5;
            margin: 10px 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
<div class="container">
        <div class="header">
            <h1>די טעלעפאן סיסטעם</h1>
        </div>
        <div class="content">
            <p>לתועלת הרבים איז געגרינדעט געווארן א טעלעפאן ליניע פאר חזרות לויט דער אנקי שיטה, דורכן רעקארדירן שאלות און תשובות אן א קאמפיוטער. די סיסטעם ווערט אויך יעדן טאג דערהיינטיגט מיט שאלות אויפן דף היומי.</p>

            <p>בסייעתא דשמיא זענען שוין הונדערטער בני תורה זוכה צו חזרן זייער לערנען אין יעדן פרייען רגע, אויך "ובלכתך בדרך", ביז די דברי תורה זענען ביי זיי כמונחים בקופסא.</p>

            <div class="phone-number">0799-400-404</div>
            <div class="secondary-phone">נומער אין אמעריקע: 151-832-99-603</div>
            <div class="secondary-phone">נומער אין ענגלאנד: 443-306-130-318</div>

            <div class="note">
                <p>פאר נאך אינפארמאציע, שיקט אן אימעיל צו:</p>
                <div class="email-container">
                    <a href="mailto:ankikol2@gmail.com" class="email-button">ankikol2@gmail.com</a>
                </div>
                <p>און שרייבט אינעם נושא "מידע".</p>
                <p>הערה: עס איז פארהאן א פרייע נומער פאר בעלי מינוטן באגרעניצונג אדער בחורי ישיבה.</p>
            </div>
        </div>
    </div>
"""

donate_info_html = """
        .donate-button {
            display: block;
            width: 200px;
            margin: 15px auto;
            padding: 10px 20px;
            background-color: #28406e;
            color: white;
            text-align: center;
            border-radius: 6px;
            font-size: 16px;
            transition: all 0.3s;
            text-decoration: none;
        }

        .donate-button:hover {
            background-color: #1e3355;
            transform: translateY(-2px);
            color: white;
        }
    </style>
</head>
<body>
<div class="container">
        <div class="header">
            <h1>געבט א נדבה פארן פארשפרייטן די פראגראם</h1>
        </div>
        <div class="content">
            <p>אזוי ווי פילע קענען האבן תועלת פארן געדענקען זייער לערנען מיט דער פראגראם און טעלעפאן סיסטעם, ווילן מיר דאס נאך מער פארשפרייטן.</p>

            <p>מען קען געבן א נדבה פאר רעקלאמע דורכן נדרים פלוס וועבזייטל ביי:</p>

            <a href="https://nedar.im/lGvN" class="donate-button">https://nedar.im/lGvN</a>

            <p>אדער ביי די נדרים פלעצער אין בתי כנסת: זוכט "שמע מינאי" און קלייבט דארט אויס די נדבה פאר רעקלאמע.</p>

            <p>מען קען אויך געבן א נדבה דורכן אנקי קול טעלעפאן סיסטעם: <span class="phone-number">0799-400-404</span> אויסוואל 6.</p>

            <p style="text-align: center; font-size: 16px; font-weight: bold; margin-top: 15px;">תזכו למצוות.</p>
        </div>
    </div>
"""

ease_guide_html = """
        .guide-list {
            margin: 12px 0 0;
            padding-right: 22px;
        }

        .guide-list li {
            margin-bottom: 12px;
            font-size: 15px;
            line-height: 1.7;
        }

        .guide-card {
            background: #f8f9fa;
            border-right: 4px solid #4a6fa5;
            padding: 14px 18px;
            margin: 16px 0;
            border-radius: 6px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>איז אנקי צו שווער? מען דארף טוישן דעם אופן פון ארבעטן!</h1>
        </div>
        <div class="content">
            <p>ווען חזרן מיט אנקי ווערט שווער, ליגט די פראבלעם געווענליך אינעם נוסח פון די קארטלעך און דער צייט ווען מען חזרט, נישט אינעם צאל קארטלעך.</p>

            <div class="guide-card">
                <p><span class="highlight">דער ציל:</span> יעדעס קארטל זאל קאנטראלירן איין נקודה אין א קורצער צייט, ווי נאענט מעגליך צום לערנען.</p>
            </div>

            <ol class="guide-list">
                <li><span class="highlight">שרייבט קורצע שאלות.</span> אויב מען דארף טראכטן פון עטליכע פרטים אינאיינעם, טיילט דאס קארטל אויף אין עטליכע שאלות. א גוטע שאלה זאל גלייך זיין קלאר, אן לייענען א גאנצן פאראגראף ביי יעדער חזרה.</li>
                <li><span class="highlight">חזרט נאענט צום לערנען.</span> ווארט נישט ביז די זאכן ווערן ווייט און אומקלאר. לייגט אריין שאלות נאכן פארשטיין די סוגיא און חזרט ווען דער זכרון איז נאך פריש.</li>
                <li><span class="highlight">יעדעס קארטל זאל נעמען בלויז עטליכע סעקונדעס.</span> אויב א קארטל נעמט לאנג, פארקירצט דעם נוסח, לייגט צו א רמז אדער טיילט עס אויף אין קלענערע שאלות.</li>
                <li><span class="highlight">חזרט נישט אן פארשטיין.</span> Anki שטארקט דעם זכרון, אבער עס פארבייט נישט דעם לערנען. פארשטייט קודם דעם מהלך און מאכט דערנאך שאלות פון די הויפט נקודות.</li>
                <li><span class="highlight">פארריכט קארטלעך וואס בלייבן שטענדיג שווער.</span> א קארטל וואס פאלט שטענדיג דורך קען מען פארבעסערן. עפנט עס, טוישט דעם נוסח, לייגט צו א מקור אדער טיילט עס אויף אין עטליכע קארטלעך.</li>
            </ol>
        </div>
    </div>
"""

class LocalGuidePage(QWebEnginePage):
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        url_string = url.toString()
        if url_string.startswith(("http://", "https://")):
            if copy_allowed_external_url(url_string):
                return False

            translated = translate_ankiweb_url(url_string)
            if translated != url_string:
                self.view().load(QUrl(translated))
            else:
                logger.warning(f"Blocked external internet link: {url_string}")
            return False

        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)

# --- מחלקת מציג ה-PDF המעודכנת ---
class PDFViewerQt(QMainWindow):
    """מציג PDF המשתמש ב-QWebEngineView לטיפול בקישורים"""

    def __init__(self, pdf_path=None, is_html=False, html_content=None, WindowTitle=None, window_size=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.is_html = is_html
        self.html_content = html_content
        self.WindowTitle = WindowTitle

        self.setWindowTitle("מציג מידע")
        if not window_size:
            self.resize(1000, 800)
        else:
            self.resize(window_size[0], window_size[1])

        self.pending_anchor = None
        self.web_view = QWebEngineView(self)
        self.web_view.setPage(LocalGuidePage(self.web_view))
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)

        # חיבור האות (Signal) של סיום הטעינה לפונקציה שלנו
        self.web_view.loadFinished.connect(self.handle_anchor_scroll)

        self.setCentralWidget(self.web_view)

        if pdf_path or self.is_html:
            self.load_pdf(pdf_path)

    def load_pdf(self, file_path):
        """טוען קובץ PDF או קישור URL ל-WebEngineView"""
        if not self.is_html:
            # איפוס עוגן קודם
            self.pending_anchor = None

            # תיקון: תמיכה גם ב-file:/// שכולל סולמית (#)
            if file_path.startswith("http://") or file_path.startswith("https://") or file_path.startswith("file://"):

                # --- החלק החדש: הפרדת העוגן מה-URL ---
                if "#" in file_path:
                    # מפרקים את הכתובת ל-2: הכתובת עצמה, והעוגן
                    parts = file_path.split("#", 1)
                    clean_path = parts[0]
                    self.pending_anchor = parts[1] # שומרים את "כרטיסים חדשים" בצד
                    url = QUrl(clean_path)
                else:
                    url = QUrl(file_path)

                display_name = "אינערליכער בלעטערער"
            else:
                # קובץ מקומי רגיל (נתיב)
                file_info = QFileInfo(file_path)
                if not file_info.exists() or not file_info.isFile():
                    from _shared_libs.haf_notifications import show_failure
                    show_failure("די געזוכטע טעקע איז נישט געפונען געווארן. קאנטראלירט אז זי עקזיסטירט און פרובירט זי נאכאמאל צו עפענען.", file_path, parent=self)
                    self.web_view.setUrl(QUrl(""))
                    self.setWindowTitle("מען קען נישט ווייזן די טעקע")
                    return False

                url = QUrl.fromLocalFile(file_info.absoluteFilePath())
                display_name = file_info.fileName()

            if not url.isValid():
                from _shared_libs.haf_notifications import show_failure
                show_failure("מען קען נישט עפענען דעם לינק. קאנטראלירט דעם אדרעס און פרובירט נאכאמאל.", file_path, parent=self)
                self.setWindowTitle("מען קען נישט עפענען דעם לינק")
                return False

            self.web_view.load(url)
            self.setWindowTitle(f"ווייזט - {display_name}")
            if self.statusBar():
                self.statusBar().showMessage(f"לאדט: {display_name}...", 3000)
        else:
            self.web_view.setHtml(self.html_content)
            self.setWindowTitle(self.WindowTitle)
            if self.statusBar():
                self.statusBar().showMessage(f"לאדט: {self.WindowTitle}...", 3000)
        return True

    def handle_anchor_scroll(self, ok):
        """פונקציה שנקראת אוטומטית כשהדף סיים להיטען כדי לגלול לעוגן"""
        if ok and self.pending_anchor:
            logger.debug(f"Page loaded, scrolling to anchor: {self.pending_anchor}")

            # אנו משתמשים ב-setTimeout כדי לתת לדפדפן זמן לרנדר את הדף לפני הגלילה
            # וגם בודקים אם ה-ID קיים באותיות קטנות (כי Markdown בדרך כלל הופך כותרות לקטנות)
            js_code = f"""
            setTimeout(function() {{
                var target = "{self.pending_anchor}";
                var el = document.getElementById(target);

                // אם לא נמצא, מנסים לחפש באותיות קטנות (נפוץ בהמרות MD ל-HTML)
                if (!el) {{
                    el = document.getElementById(target.toLowerCase());
                }}

                // ניסיון פענוח של תווים מיוחדים
                if (!el) {{
                    try {{
                        el = document.getElementById(decodeURIComponent(target));
                    }} catch(e) {{}}
                }}

                if (el) {{
                    el.scrollIntoView({{behavior: "smooth", block: "start"}});
                    console.log("Scrolled to: " + target);
                }} else {{
                    console.log("Anchor not found even after timeout: " + target);
                }}
            }}, 500); // השהייה של 500 מילישניות
            """
            self.web_view.page().runJavaScript(js_code)
            self.pending_anchor = None

    def show(self):
        super().show()
        self.raise_()
        self.activateWindow()

# --- פונקציות עזר לפתיחת החלון ---

def show_pdf_viewer(pdf_path="", window_size=None, parent=None):
    if parent is None:
        parent = mw.app.activeWindow() or mw

    viewer = PDFViewerQt(pdf_path, window_size=window_size, parent=parent)

    if not hasattr(parent, "active_viewers"):
        parent.active_viewers = []
    parent.active_viewers.append(viewer)

    viewer.show()
    return viewer

def show_html_viewer(html_content=None, WindowTitle=None, window_size=None):
    parent = mw.app.activeWindow() or mw

    full_html_content = """
        <!DOCTYPE html>
        <html dir="rtl" lang="he">
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f5f7fa; padding: 20px; }
                .container { max-width: 1000px; margin: 0 auto; background-color: #fff; border-radius: 12px; box-shadow: 0 5px 15px rgba(0, 0, 50, 0.08); overflow: hidden; margin-bottom: 30px; }
                .header { background: linear-gradient(135deg, #4a6fa5 0%, #28406e 100%); color: white; padding: 20px; text-align: center; border-bottom: 4px solid #1e3355; }
                .content { padding: 30px; }
                h1 { font-size: 28px; margin-bottom: 10px; }
    """ + html_content + """</body></html>"""

    viewer = PDFViewerQt(is_html=True, html_content=full_html_content, WindowTitle=WindowTitle, window_size=window_size, parent=parent)
    if not hasattr(parent, "active_viewers"):
        parent.active_viewers = []
    parent.active_viewers.append(viewer)
    viewer.show()
    return viewer

def open_file(filename, window_size=None, parent=None):
    """פותח קובץ או קישור"""
    if filename.startswith("http://") or filename.startswith("https://"):
        if copy_allowed_external_url(filename):
            return
        translated = translate_ankiweb_url(filename)
        if translated == filename:
            logger.warning(f"Blocked external internet link: {filename}")
            return
        filename = translated

    if filename.startswith("file://"):
        logger.debug(f"Opening URL inside viewer: {filename}")
        show_pdf_viewer(filename, window_size, parent)
        return

    file_path = os.path.join(ADDON_DIR, filename)
    if not os.path.exists(file_path):
        from _shared_libs.haf_notifications import show_failure
        show_failure("דער געזוכטער הילף בלאט פעלט אין דער אינסטאלאציע. אויב די פראבלעם בלייבט נאך אן דערהיינטיגונג, שיקט א באריכט פונעם הילף מעניו.", file_path, parent=parent)
        return
    show_pdf_viewer(file_path, window_size, parent)

# --- פונקציות תפריט ---
def add_help_menu(text, icon, func):
    if not mw or not mw.form or not mw.form.menuHelp:
        return
    action = AnkiQAction(text, mw)
    icon_names = {"info.png": "info", "tutor.ico": "write", "tutor2.ico": "book",
                  "tipim.ico": "tips", "dictionary.png": "dictionary", "ts.ico": "support",
                  "phone.ico": "phone", "ad.png": "advert", "manual": "manual"}
    icon_path = os.path.join(ADDON_DIR, "icons", icon_names.get(icon, "info") + ".svg")
    if os.path.exists(icon_path):
        action.setIcon(QIcon(icon_path))
    action.setIconVisibleInMenu(True)
    section = {"ts.ico": "שטיצע און באריכטן", "phone.ico": "די טעלעפאן סיסטעם",
               "ad.png": "וועגן און פארשפרייטן"}.get(icon, "אנווייזונגען און לערנען")
    action.setProperty("haf_help_section", section)
    qconnect(action.triggered, lambda checked=False, f=func: f())
    mw.form.menuHelp.addAction(action)


def _refresh_help_sections():
    """Group late-added actions too, and restore icons after theme add-ons load."""
    menu = mw.form.menuHelp
    about = getattr(mw.form, "actionAbout", None)
    bug = getattr(mw, "_haf_beta_help_bug_action", None)
    for action, icon, section in ((about, "info", "וועגן און פארשפרייטן"), (bug, "bug", "שטיצע און באריכטן")):
        if action is not None:
            action.setIcon(QIcon(os.path.join(ADDON_DIR, "icons", icon + ".svg")))
            action.setIconVisibleInMenu(True)
            action.setProperty("haf_help_section", section)
    actions = [action for action in menu.actions()
               if not action.isSeparator() and not action.property("haf_help_heading")]
    groups = {title: [] for title in ("אנווייזונגען און לערנען", "שטיצע און באריכטן", "די טעלעפאן סיסטעם", "וועגן און פארשפרייטן")}
    for action in actions:
        section = action.property("haf_help_section") or "שטיצע און באריכטן"
        groups.setdefault(section, []).append(action)
    # Remove/reinsert without clearing: clear() can delete actions owned by QMenu.
    for action in menu.actions():
        menu.removeAction(action)
    separators = getattr(mw, "_haf_help_separators", {})
    first_group = True
    for title, items in groups.items():
        if not items:
            continue
        if not first_group:
            if title not in separators:
                separator = AnkiQAction(mw)
                separator.setSeparator(True)
                separators[title] = separator
            menu.addAction(separators[title])
        first_group = False
        for action in items:
            menu.addAction(action)
    mw._haf_help_separators = separators

def technical_support(): show_html_viewer(tech_support_html,"טעכנישע שטיצע", [850,700])
def dictionary(): show_html_viewer(dict_text,"ווערטערבוך פון אנקי באגריפן", [700,700])
def phone_info(): show_html_viewer(phone_info_html,"אינפארמאציע וועגן דער טעלעפאן סיסטעם", [700, 700])
def donate_info(): show_html_viewer(donate_info_html,"געבט א נדבה פארן פארשפרייטן די פראגראם", [700,600])
def ease_guide(): show_html_viewer(ease_guide_html,"איז אנקי צו שווער? מען דארף טוישן דעם אופן פון ארבעטן!", [780,680])

def setup_menu():
    if not mw or not mw.form or not mw.form.menuHelp:
        return
    actions_to_remove = ['actionDocumentation', 'actionAbout', 'actionDonate']
    for action_name in actions_to_remove:
        action = getattr(mw.form, action_name, None)
        if action:
            mw.form.menuHelp.removeAction(action)

    add_help_menu("אלגעמיינע ערקלערונג פון דער אנקי חזרות שיטה", "info.png", lambda: open_file("explanation.pdf"))
    add_help_menu("קורצע אנווייזונגען - שרייבן שאלות", "tutor.ico", lambda: open_file("tutor1write.pdf"))
    add_help_menu("באניצער אנווייזונגען", "tutor2.ico", lambda: open_file("tutor3long.pdf"))
    add_help_menu("די אפיציעלע אנקי אנווייזונגען", "manual", lambda: open_file(os.path.join(LOCAL_MANUAL_DIR, "intro.html"), [1080, 800]))
    add_help_menu("וויכטיגע עצות", "tipim.ico", lambda: open_file("tipim.pdf"))
    add_help_menu("איז אנקי צו שווער? מען דארף טוישן דעם אופן פון ארבעטן!", "tipim.ico", ease_guide)
    add_help_menu("ווערטערבוך פון באגריפן", "dictionary.png", dictionary)
    add_help_menu("טעכנישע שטיצע", "ts.ico", technical_support)
    add_help_menu("אינפארמאציע וועגן דער טעלעפאן סיסטעם", "phone.ico", phone_info)
    add_help_menu("אנקיקול אנווייזונגען", "phone.ico", lambda: open_file("ankikol.pdf"))
    mw.form.menuHelp.addSeparator()
    add_help_menu("זכה את הרבים - קליקט דא צו דרוקן א רעקלאמע פאר דער פראגראם", "ad.png", lambda: open_file("advert.pdf"))
    # mw.donate_info = donate_info
    # add_help_menu("תרום לפרסום התוכנה", "handshake.png", donate_info)
    # אישיו #406: לא מוסיפים לתפריט העזרה את האפשרות לתרום לפרסום התוכנה.
    about_action = getattr(mw.form, 'actionAbout', None)
    if about_action:
        about_action.setIcon(QIcon(os.path.join(ADDON_DIR, "icons", "info.svg")))
        mw.form.menuHelp.addAction(about_action)
    if not getattr(mw, "_haf_help_sections_connected", False):
        mw.form.menuHelp.aboutToShow.connect(_refresh_help_sections)
        mw._haf_help_sections_connected = True
    _refresh_help_sections()

# ==========================================
# קוד יירוט וטיפול בקישורים (Link Interceptor)
# ==========================================
ANCHOR_MAPPINGS = {
    # deck-options.html
    "presets": "קבוצת-הגדרות",
    "sub-decks": "תת-חפיסות",
    "daily-limits": "מגבלות-יומיות",
    "new-cardsday": "כרטיסים-חדשיםיום",
    "maximum-reviewsday": "חזרות-מרביותיום",
    "per-deck-daily-limits": "מגבלות-יומיות-לפי-חפיסה",
    "new-cards-ignore-review-limit": "התעלם-ממגבלת-החזרות-עבור-כרטיסים-חדשים",
    "limits-start-from-top": "חישוב-מגבלות-מחפיסת-האב-העליונה",
    "new-cards": "כרטיסים-חדשים",
    "learning-steps": "שלבי-למידה",
    "day-boundaries": "גבולות-יום",
    "graduating-interval": "מרווח-סיום-למידה",
    "easy-interval": "מרווח-קל",
    "insertion-order": "סדר-הוספה",
    "lapses": "שגיאות",
    "relearning-steps": "שלבי-למידה-מחדש",
    "minimum-interval": "מרווח-מינימלי",
    "leeches": "עלוקות",
    "display-order": "סדר-חזרה",
    "new-card-gather-order": "סדר-איסוף-כרטיסים-חדשים",
    "new-card-sort-order": "סדר-חזרה-של-כרטיסים-חדשים",
    "newreview-order": "סדר-חדשחזרה",
    "interday-learningreview-order": "סדר-למידה-בין-יומיתחזרות",
    "review-sort-order": "סדר-מיון-חזרות",
    "burying": "הטמנה",
    "audio": "שמע",
    "timer": "timer",
    "timers": "timer",
    "auto-advance": "התקדמות-אוטומטית",
    "easy-days": "ימים-קלים",
    "fsrs": "fsrs",
    "desired-retention": "שימור-רצוי",
    "fsrs-parameters": "פרמטרי-fsrs",
    "reschedule-cards-on-change": "תזמן-מחדש-כרטיסים-בעת-שינוי",
    "compute-minimum-recommended-retention": "הסימולטור",
    "the-simulator": "הסימולטור",
    "advanced": "מתקדם",
    "maximum-interval": "מרווח-מרבי",
    "historical-retention": "שימור-היסטורי",
    "ignore-reviews-before": "התעלם-מחזרות-לפני",
    "starting-ease": "רמת-קלות-התחלתית",
    "easy-bonus": "בונוס-קל",
    "interval-modifier": "מכפיל-מרווח",
    "hard-interval": "מרווח-קשה",
    "new-interval": "מרווח-חדש",
    "custom-scheduling": "תזמון-מותאם-אישית",

    # help links from Anki's rust/python/ts code
    "note-types": "סוגי-רשומות",
    "find-and-replace": "מצא-והחלף",
    "notes": "רשומות",
    "keyboard-shortcuts": "קיצורי-מקלדת",
    "adding-cards-and-notes": "הוספת-כרטיסים-ורשומות",
    "adding-a-note-type": "הוספת-כרטיסים-ורשומות",
    "latex": "מתמטיקה-וסמלים",
    "customizing-fields": "התאמה-אישית-של-שדות",
    "editing-features": "תכונות-עריכה",
    "full-screen": "מסך-מלא",
    "template-syntax-error": "בדיקות-ושגיאות",
    "front-of-card-is-blank": "בדיקות-ושגיאות",
    "identical-front-sides": "בדיקות-ושגיאות",
    "no-field-replacement-on-front-side": "בדיקות-ושגיאות",
    "no-cloze-filter-on-cloze-notetype": "בדיקות-ושגיאות",
    "no-cloze-filter-on-cloze-note-type": "בדיקות-ושגיאות",
    "siblings-and-burying": "אחים-והטמנה",
    "waiting": "הפרעה",
    "updating": "עדכון",
    "scheduling": "תזמון",
    "duplicates-and-updating": "כפילויות-ועדכון",
    "html": "html",
    "add-ons-and-custom-scheduling": "המתזמן-v3-של-anki",
}

def mdbook_anchor_slug(value):
    decoded = unquote(value or "").strip().lower()
    decoded = re.sub(r"[`*_~]", "", decoded)
    decoded = re.sub(r"<[^>]+>", "", decoded)
    decoded = re.sub(r"[^\w\s\-\u0590-\u05ff]", "", decoded, flags=re.UNICODE)
    return re.sub(r"\s+", "-", decoded)

def html_has_anchor(html_path, anchor):
    if not anchor:
        return False
    try:
        with open(html_path, "r", encoding="utf-8") as handle:
            html = handle.read()
    except OSError:
        return False
    return f'id="{anchor}"' in html or f"id='{anchor}'" in html or f'name="{anchor}"' in html

def resolve_local_anchor(html_path, anchor):
    if not anchor:
        return ""

    decoded = unquote(anchor).strip()
    mapped = ANCHOR_MAPPINGS.get(decoded, decoded)
    candidates = [decoded, mapped, mdbook_anchor_slug(mapped), mdbook_anchor_slug(decoded)]

    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if html_has_anchor(html_path, candidate):
            return candidate

    logger.warning(f"Local help anchor not found: {anchor} in {html_path}")
    return ""


JS_INTERCEPT_EXTERNAL = r"""
(function() {
    if (window.hasAnkiLinkInterceptor) return;
    window.hasAnkiLinkInterceptor = true;

    document.addEventListener("click", function(e) {
        let el = e.target;
        while (el && el.tagName !== "A") {
            el = el.parentElement;
        }
        if (!el) return;

        const url = el.getAttribute("href");
        if (!url) return;

        if (url.startsWith("http://") || url.startsWith("https://")) {
            e.preventDefault();
            e.stopPropagation();
            pycmd("open_external:" + url);
        }
    }, true);
})();
"""

def inject_link_interceptor(web_content, *args):
    web_content.eval(JS_INTERCEPT_EXTERNAL)

def is_allowed_external_url(url):
    parsed = urlsplit(url)
    return (
        parsed.scheme == "https"
        and (parsed.netloc or "").lower() == "nedar.im"
        and (parsed.path or "").rstrip("/") == "/lGvN"
    )

def copy_allowed_external_url(url):
    if not is_allowed_external_url(url):
        return False
    # #246 — קישור תרומה חיצוני לא נפתח בדפדפן; מעתיקים אותו ידנית ללוח ומציגים tooltip (ללא חלון מודאלי).
    QApplication.clipboard().setText(url)
    tooltip("דער לינק איז קאפירט צום קלעמברעט")
    return True

def translate_ankiweb_url(url):
    """
    מקבל קישור לאתר AnkiWeb, בודק אם יש לנו עותק מקומי,
    מתרגם את העוגן (הסולמית) לעברית, ומחזיר קישור מקומי.
    """
    url_without_anchor, anchor = (url.split("#", 1) + [""])[:2] if "#" in url else (url, "")
    parsed = urlsplit(url_without_anchor)
    host = (parsed.netloc or "").lower()
    path = unquote(parsed.path or "").lstrip("/")
    local_root = LOCAL_MANUAL_DIR

    if host == "docs.ankiweb.net":
        if not path or path == "index.html":
            path = "intro.html"
        local_root = LOCAL_MANUAL_DIR
    elif host == "faqs.ankiweb.net":
        if not path or path == "index.html":
            path = "index.html"
        local_root = LOCAL_FAQ_DIR
    elif not url_without_anchor.startswith(("http://", "https://", "file://")):
        path = unquote(url_without_anchor).lstrip("/") or "intro.html"
        local_root = LOCAL_MANUAL_DIR
    else:
        return url

    # #143 — הקישורים מ-card preferences מגיעים בפורמט
    #         "deck-options.html@highlight=FSRS#fsrs" או עם query string ?highlight=...
    #         ולכן filename לא תאם קובץ מקומי. מנקים את הסיומות הללו.
    for sep in ('@', '?'):
        if sep in path:
            path = path.split(sep, 1)[0]
            logger.debug(f"#143 cleaned filename for local lookup: {path}")

    if path.endswith(".md"):
        path = path[:-3] + ".html"

    local_rel_path = os.path.join(local_root, *path.split("/"))
    local_full_path = os.path.join(ADDON_DIR, local_rel_path)
    logger.debug(f"Looking for local translation: {local_rel_path}")
    # בדיקה האם הקובץ קיים אצלנו
    if os.path.exists(local_full_path):
        logger.debug(f"Found local translation for: {path}")

        # יצירת URL מקומי תקין
        local_url = QUrl.fromLocalFile(local_full_path).toString()

        if anchor:
            translated_anchor = resolve_local_anchor(local_full_path, anchor)
            if translated_anchor:
                local_url += "#" + translated_anchor

        return local_url

    # אם אין לנו קובץ מקומי, מחזיר את הקישור המקורי לאינטרנט
    return url

# שינוי ארגומנטים: (handled, message, context)
def on_bridge_cmd(handled, msg, context):
    # אם תוסף אחר כבר טיפל בזה, אנחנו לא מתערבים
    already_handled = handled[0] if isinstance(handled, tuple) else handled
    if already_handled:
        return handled

    if msg.startswith("open_external:"):
        url = msg[len("open_external:"):]
        logger.debug(f"Opening external: {url}")

        if copy_allowed_external_url(url):
            return (True, None)

        final_url = translate_ankiweb_url(url)
        logger.debug(f"Opening: {final_url}")

        if final_url.startswith(("http://", "https://")):
            logger.warning(f"Blocked external internet link: {url}")
            return (True, None)

        open_file(final_url)
        return (True, None)

    # אם לא טיפלנו, מחזירים את המצב המקורי
    return handled

gui_hooks.webview_did_inject_style_into_page.append(inject_link_interceptor)
gui_hooks.webview_did_receive_js_message.append(on_bridge_cmd)

# --- איתחול ---
setup_menu()




#gui_hooks.profile_did_open.append(_show_first_run_ad_after_profile_open)
mw.open_pdf_file = open_file


def open_help_link(link, _old=None):
    if copy_allowed_external_url(link):
        return None

    final_url = translate_ankiweb_url(link)
    logger.debug(f"Opening: {final_url}")

    if final_url.startswith(("http://", "https://")):
        logger.warning(f"Blocked external internet link: {link}")
        return None

    if final_url != link or final_url.startswith("file://"):
        open_file(final_url)
        return None

    return _old(link) if _old else None



aqt.utils.openLink = wrap(aqt.utils.openLink, open_help_link, "around")

# aqt.preferences.Preferences.setup_global
