;Language: Yiddish (1085)
;By Yaron Shahrabani

!insertmacro LANGFILE "Yiddish" = "יידיש" "Yidish"

!ifdef MUI_WELCOMEPAGE
  ${LangFileString} MUI_TEXT_WELCOME_INFO_TITLE "ברוכים הבאים צום אינסטאלירן פון $(^NameDA)"
  ${LangFileString} MUI_TEXT_WELCOME_INFO_TEXT "דער אשף וועט אייך באגלייטן ביים אינסטאלירן $(^NameDA).$\r$\n$\r$\nמאכט פאר די אינסטאלירונג צו אנדערע פראגראמען וואס קענען נוצן די פיילס.$\r$\n$\r$\n$_CLICK"
!endif

!ifdef MUI_UNWELCOMEPAGE
  ${LangFileString} MUI_UNTEXT_WELCOME_INFO_TITLE "ברוכים הבאים צום אוועקנעמען פון $(^NameDA)"
  ${LangFileString} MUI_UNTEXT_WELCOME_INFO_TEXT "דער אשף וועט אייך באגלייטן ביים אוועקנעמען $(^NameDA).$\r$\n$\r$\nמאכט די פראגראם צו איידער איר גייט ווייטער.$\r$\n$\r$\n$_CLICK"
!endif

!ifdef MUI_LICENSEPAGE
  ${LangFileString} MUI_TEXT_LICENSE_TITLE "דער רישוי-הסכם"
  ${LangFileString} MUI_TEXT_LICENSE_SUBTITLE "ליינט די תנאים איידער איר אינסטאלירט $(^NameDA)."
  ${LangFileString} MUI_INNERTEXT_LICENSE_BOTTOM "אויב איר זענט מסכים צו די תנאים, דרוקט 'איך בין מסכים' כדי צו גיין ווייטער. איר מוזט זיין מסכים צו די תנאים צו אינסטאלירן $(^NameDA)."
  ${LangFileString} MUI_INNERTEXT_LICENSE_BOTTOM_CHECKBOX "אויב איר זענט מסכים צו די תנאים, צייכנט אן דאס קעסטל אונטן. איר מוזט זיין מסכים צו אינסטאלירן $(^NameDA). $_CLICK"
  ${LangFileString} MUI_INNERTEXT_LICENSE_BOTTOM_RADIOBUTTONS "אויב איר זענט מסכים צו די תנאים, קלויבט די ערשטע ברירה אונטן. איר מוזט זיין מסכים צו אינסטאלירן $(^NameDA). $_CLICK"
!endif

!ifdef MUI_UNLICENSEPAGE
  ${LangFileString} MUI_UNTEXT_LICENSE_TITLE "דער רישוי-הסכם"
  ${LangFileString} MUI_UNTEXT_LICENSE_SUBTITLE "ליינט די תנאים איידער איר נעמט אוועק $(^NameDA)."
  ${LangFileString} MUI_UNINNERTEXT_LICENSE_BOTTOM "אויב איר זענט מסכים צו די תנאים, דרוקט 'איך בין מסכים' כדי צו גיין ווייטער. איר מוזט זיין מסכים צו די תנאים צו אוועקנעמען $(^NameDA)."
  ${LangFileString} MUI_UNINNERTEXT_LICENSE_BOTTOM_CHECKBOX "אויב איר זענט מסכים צו די תנאים, צייכנט אן דאס קעסטל אונטן. איר מוזט זיין מסכים צו אוועקנעמען $(^NameDA). $_CLICK"
  ${LangFileString} MUI_UNINNERTEXT_LICENSE_BOTTOM_RADIOBUTTONS "אויב איר זענט מסכים צו די תנאים, קלויבט די ערשטע ברירה אונטן. איר מוזט זיין מסכים צו אוועקנעמען $(^NameDA). $_CLICK"
!endif

!ifdef MUI_LICENSEPAGE | MUI_UNLICENSEPAGE
  ${LangFileString} MUI_INNERTEXT_LICENSE_TOP "דרוקט Page Down צו ליינען דעם ווייטערדיגן טייל פונעם הסכם."
!endif

!ifdef MUI_COMPONENTSPAGE
  ${LangFileString} MUI_TEXT_COMPONENTS_TITLE "אויסקלויבן טיילן"
  ${LangFileString} MUI_TEXT_COMPONENTS_SUBTITLE "קלויבט וועלכע טיילן פון $(^NameDA) צו אינסטאלירן."
!endif

!ifdef MUI_UNCOMPONENTSPAGE
  ${LangFileString} MUI_UNTEXT_COMPONENTS_TITLE "אויסקלויבן טיילן"
  ${LangFileString} MUI_UNTEXT_COMPONENTS_SUBTITLE "קלויבט וועלכע טיילן פון $(^NameDA) צו אוועקנעמען."
!endif

!ifdef MUI_COMPONENTSPAGE | MUI_UNCOMPONENTSPAGE
  ${LangFileString} MUI_INNERTEXT_COMPONENTS_DESCRIPTION_TITLE "באשרייבונג"
  !ifndef NSIS_CONFIG_COMPONENTPAGE_ALTERNATIVE
    ${LangFileString} MUI_INNERTEXT_COMPONENTS_DESCRIPTION_INFO "קלויבט א טייל, אדער פירט איבער אים דעם מייזל, כדי צו זען זיין באשרייבונג."
  !else
    ${LangFileString} MUI_INNERTEXT_COMPONENTS_DESCRIPTION_INFO "קלויבט א טייל, אדער פירט איבער אים דעם מייזל, כדי צו זען זיין באשרייבונג."
  !endif
!endif

!ifdef MUI_DIRECTORYPAGE
  ${LangFileString} MUI_TEXT_DIRECTORY_TITLE "אויסקלויבן דעם אינסטאלירן-פלאץ"
  ${LangFileString} MUI_TEXT_DIRECTORY_SUBTITLE "קלויבט די תיקיה וואו איר ווילט אינסטאלירן $(^NameDA)."
!endif

!ifdef MUI_UNDIRECTORYPAGE
  ${LangFileString} MUI_UNTEXT_DIRECTORY_TITLE "אויסקלויבן דעם אוועקנעמען-פלאץ"
  ${LangFileString} MUI_UNTEXT_DIRECTORY_SUBTITLE "קלויבט די תיקיה פון וועלכער איר ווילט אוועקנעמען $(^NameDA)."
!endif

!ifdef MUI_INSTFILESPAGE
  ${LangFileString} MUI_TEXT_INSTALLING_TITLE "אינסטאלירט"
  ${LangFileString} MUI_TEXT_INSTALLING_SUBTITLE "ווארט ביז $(^NameDA) ווערט אינסטאלירט."
  ${LangFileString} MUI_TEXT_FINISH_TITLE "די אינסטאלירונג איז פארטיג"
  ${LangFileString} MUI_TEXT_FINISH_SUBTITLE "די גאנצע אינסטאלירונג איז פארטיג."
  ${LangFileString} MUI_TEXT_ABORT_TITLE "די אינסטאלירונג איז אפגעזאגט"
  ${LangFileString} MUI_TEXT_ABORT_SUBTITLE "די אינסטאלירונג איז נישט פארענדיגט געווארן."
!endif

!ifdef MUI_UNINSTFILESPAGE
  ${LangFileString} MUI_UNTEXT_UNINSTALLING_TITLE "נעמט אוועק"
  ${LangFileString} MUI_UNTEXT_UNINSTALLING_SUBTITLE "ווארט ביז $(^NameDA) ווערט אוועקגענומען."
  ${LangFileString} MUI_UNTEXT_FINISH_TITLE "דאס אוועקנעמען איז פארטיג"
  ${LangFileString} MUI_UNTEXT_FINISH_SUBTITLE "דאס גאנצע אוועקנעמען איז פארטיג."
  ${LangFileString} MUI_UNTEXT_ABORT_TITLE "דאס אוועקנעמען איז אפגעזאגט"
  ${LangFileString} MUI_UNTEXT_ABORT_SUBTITLE "דאס אוועקנעמען איז נישט פארענדיגט געווארן."
!endif

!ifdef MUI_FINISHPAGE
  ${LangFileString} MUI_TEXT_FINISH_INFO_TITLE "פארענדיגן דעם אינסטאלירן פון $(^NameDA)"
  ${LangFileString} MUI_TEXT_FINISH_INFO_TEXT "$(^NameDA) איז אינסטאלירט געווארן.$\r$\n$\r$\nדרוקט פארטיג צו פארמאכן דעם אשף."
  ${LangFileString} MUI_TEXT_FINISH_INFO_REBOOT "איר דארפט ווידער אויפמאכן דעם קאמפיוטער כדי צו פארענדיגן די אינסטאלירונג. ווילט איר דאס טון יעצט?"
!endif

!ifdef MUI_UNFINISHPAGE
  ${LangFileString} MUI_UNTEXT_FINISH_INFO_TITLE "פארענדיגן דאס אוועקנעמען פון $(^NameDA)"
  ${LangFileString} MUI_UNTEXT_FINISH_INFO_TEXT "$(^NameDA) איז אוועקגענומען געווארן.$\r$\n$\r$\nדרוקט פארטיג צו פארמאכן דעם אשף."
  ${LangFileString} MUI_UNTEXT_FINISH_INFO_REBOOT "איר דארפט ווידער אויפמאכן דעם קאמפיוטער כדי צו פארענדיגן דאס אוועקנעמען. ווילט איר דאס טון יעצט?"
!endif

!ifdef MUI_FINISHPAGE | MUI_UNFINISHPAGE
  ${LangFileString} MUI_TEXT_FINISH_REBOOTNOW "ווידער אויפמאכן יעצט"
  ${LangFileString} MUI_TEXT_FINISH_REBOOTLATER "איך וועל שפעטער אליין ווידער אויפמאכן"
  ${LangFileString} MUI_TEXT_FINISH_RUN "&אויפמאכן $(^NameDA)"
  ${LangFileString} MUI_TEXT_FINISH_SHOWREADME "&ווייזן דעם הסבר-פייל"
  ${LangFileString} MUI_BUTTONTEXT_FINISH "&פארטיג"  
!endif

!ifdef MUI_STARTMENUPAGE
  ${LangFileString} MUI_TEXT_STARTMENU_TITLE "אויסקלויבן א תיקיה אינעם אנהייב-מעניו"
  ${LangFileString} MUI_TEXT_STARTMENU_SUBTITLE "קלויבט וואו צו שאפן די פראגראם-קיצורים."
  ${LangFileString} MUI_INNERTEXT_STARTMENU_TOP "קלויבט אן אנהייב-מעניו-תיקיה פאר די פראגראם-קיצורים. איר קענט אויך אריינשרייבן א נאמען צו שאפן א נייע תיקיה."
  ${LangFileString} MUI_INNERTEXT_STARTMENU_CHECKBOX "נישט שאפן קיצורים"
!endif

!ifdef MUI_UNCONFIRMPAGE
  ${LangFileString} MUI_UNTEXT_CONFIRM_TITLE "אוועקנעמען $(^NameDA)"
  ${LangFileString} MUI_UNTEXT_CONFIRM_SUBTITLE "אוועקנעמען $(^NameDA) פונעם קאמפיוטער."
!endif

!ifdef MUI_ABORTWARNING
  ${LangFileString} MUI_TEXT_ABORTWARNING "זענט איר זיכער אז איר ווילט אפזאגן דאס אינסטאלירן פון $(^Name)?"
!endif

!ifdef MUI_UNABORTWARNING
  ${LangFileString} MUI_UNTEXT_ABORTWARNING "זענט איר זיכער אז איר ווילט אפזאגן דאס אוועקנעמען פון $(^Name)?"
!endif

!ifdef MULTIUSER_INSTALLMODEPAGE
  ${LangFileString} MULTIUSER_TEXT_INSTALLMODE_TITLE "אויסקלויבן באנוצער"
  ${LangFileString} MULTIUSER_TEXT_INSTALLMODE_SUBTITLE "קלויבט פאר וועלכע באנוצער צו אינסטאלירן $(^NameDA)."
  ${LangFileString} MULTIUSER_INNERTEXT_INSTALLMODE_TOP "קלויבט צי צו אינסטאלירן $(^NameDA) נאר פאר אייך אדער פאר אלע באנוצער. $(^ClickNext)"
  ${LangFileString} MULTIUSER_INNERTEXT_INSTALLMODE_ALLUSERS "אינסטאלירן פאר אלע באנוצער"
  ${LangFileString} MULTIUSER_INNERTEXT_INSTALLMODE_CURRENTUSER "אינסטאלירן נאר פאר מיין באנוצער"
!endif
