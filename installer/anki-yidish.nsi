Unicode true
!include "MUI2.nsh"
!include "x64.nsh"
!include "WinVer.nsh"
!include "FileFunc.nsh"
Name "אנקי אויף יידיש"
OutFile "..\artifacts\Anki-Yidish-25.9.2-yi.1-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\Anki Yidish"
RequestExecutionLevel user
SetCompressor /SOLID zlib
VIProductVersion "25.9.2.1"
VIAddVersionKey /LANG=1085 "ProductName" "Anki Yidish"
VIAddVersionKey /LANG=1085 "FileDescription" "Anki Yidish Setup"
VIAddVersionKey /LANG=1085 "FileVersion" "25.9.2.1"
VIAddVersionKey /LANG=1085 "ProductVersion" "25.9.2-yi.1"
VIAddVersionKey /LANG=1085 "LegalCopyright" "Ankitects and addon contributors"
Var TestMode
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH
!insertmacro MUI_LANGUAGEEX "." "Yiddish"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_OK "די אויסגאבע פאדערט Windows 10 אדער 11, 64 ביט."
    Abort
  ${EndIf}
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_OK "די אויסגאבע פאדערט Windows 10 אדער 11, 64 ביט."
    Abort
  ${EndIf}
  SetShellVarContext current
  ${GetParameters} $0
  ClearErrors
  ${GetOptions} $0 "/TEST" $1
  ${IfNot} ${Errors}
    StrCpy $TestMode "yes"
  ${EndIf}
FunctionEnd

Section
  IfFileExists "$INSTDIR\app\anki.exe" 0 +4
  IfFileExists "$INSTDIR\distribution.json" +3 0
  MessageBox MB_OK "קלייבט א באזונדערע תיקיה פאר אנקי אויף יידיש. מען טאר נישט איבערשרייבן אן אנדער אנקי אויסגאבע."
  Abort
  IfFileExists "$INSTDIR\app\anki.exe" 0 core_not_present
  ClearErrors
  FileOpen $0 "$INSTDIR\app\anki.exe" a
  IfErrors core_in_use
  FileClose $0
  Goto core_not_present
  core_in_use:
  MessageBox MB_OK "מאכט צו אנקי אויף יידיש איידער איר דערהייבט די אויסגאבע."
  SetErrorLevel 1
  Abort
  core_not_present:
  ClearErrors
  SetOutPath "$INSTDIR\installer-tools"
  File "install_addons.ps1"
  File "merge_modern_theme_config.ps1"
  File "addon_settings_policy.json"
  File "addons.json"
  SetOutPath "$INSTDIR\app"
  File /r "..\artifacts\payload\app\*"
  SetOutPath "$INSTDIR\payload-addons"
  File /r "..\artifacts\payload\Data\addons21\*"
  IfErrors extraction_failed
  nsExec::ExecToLog '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$INSTDIR\installer-tools\install_addons.ps1" -InstallRoot "$INSTDIR"'
  Pop $0
  ${If} $0 != "0"
    MessageBox MB_OK "די אינסטאלאציע איז נישט פארענדיגט. די איינשטעלונגען זענען געגיבויט. פארמאכט אנקי און פרובירט נאכאמאל; אויב דער פראבלעם בלייבט, ווענדט זיך צו שטיצע."
    SetErrorLevel 1
    Abort
  ${EndIf}
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  ${If} $TestMode != "yes"
    CreateDirectory "$SMPROGRAMS\Anki Yidish"
    CreateShortCut "$SMPROGRAMS\Anki Yidish\Anki Yidish.lnk" "$INSTDIR\app\anki.exe" '-b "$INSTDIR\Data" -l yi' "$INSTDIR\app\anki.exe"
    CreateShortCut "$DESKTOP\Anki Yidish.lnk" "$INSTDIR\app\anki.exe" '-b "$INSTDIR\Data" -l yi' "$INSTDIR\app\anki.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AnkiYidish" "DisplayName" "אנקי אויף יידיש"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AnkiYidish" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AnkiYidish" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AnkiYidish" "DisplayVersion" "25.9.2-yi.1"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AnkiYidish" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AnkiYidish" "NoRepair" 1
  ${EndIf}
  Goto install_finished
  extraction_failed:
  MessageBox MB_OK "מען האט נישט געקענט קאפירן די פראגראם טעקעס. פרובירט נאכאמאל נאך פארמאכן אנקי."
  SetErrorLevel 1
  Abort
  install_finished:
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  RMDir /r "$INSTDIR\app"
  RMDir /r "$INSTDIR\payload-addons"
  RMDir /r "$INSTDIR\installer-tools"
  Delete "$INSTDIR\distribution.json"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$DESKTOP\Anki Yidish.lnk"
  Delete "$SMPROGRAMS\Anki Yidish\Anki Yidish.lnk"
  RMDir "$SMPROGRAMS\Anki Yidish"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AnkiYidish"
  MessageBox MB_OK "דער פראגראם איז אראפגענומען. די Data תיקיה מיט די שאלות, איינשטעלונגען און גיבויים איז געהיטן."
SectionEnd
