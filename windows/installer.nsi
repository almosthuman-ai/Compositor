Unicode true
RequestExecutionLevel user
ManifestDPIAware true
SetCompressor /SOLID lzma
!include MUI2.nsh
!include LogicLib.nsh
!include x64.nsh
!include WinVer.nsh

Name "Compositor for Windows"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\Compositor\${APP_VERSION}"
BrandingText "Compositor · Legion"
Icon "${APP_ICON}"
UninstallIcon "${APP_ICON}"
VIProductVersion "0.1.0.1"
VIAddVersionKey "ProductName" "Compositor for Windows"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "Compositor Windows Setup"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "Compositor contributors; original Compositor by Robbie Tilton"

!define MUI_ICON "${APP_ICON}"
!define MUI_UNICON "${APP_ICON}"
!define MUI_WELCOMEPAGE_TITLE "Compositor for Windows"
!define MUI_WELCOMEPAGE_TEXT "A layered image editor with pixel-art tools, Glitch Temple effects and ChatGPT collaboration.$\r$\n$\r$\nThe editor works without an account. Sign in to ChatGPT inside the app when you want an AI collaborator.$\r$\n$\r$\nThis installs Compositor for your Windows account."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\Compositor.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Open Compositor"
!insertmacro MUI_PAGE_FINISH
!define MUI_UNCONFIRMPAGE_TEXT_TOP "Remove this Compositor installation? Your saved artwork, settings and ChatGPT sign-in are kept."
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function .onInit
    ${IfNot} ${RunningX64}
        MessageBox MB_OK "Compositor requires 64-bit Windows 10 or later."
        Abort
    ${EndIf}
    ${IfNot} ${AtLeastWin10}
        MessageBox MB_OK "Compositor requires Windows 10 or later."
        Abort
    ${EndIf}
FunctionEnd

Section "Compositor"
    SetShellVarContext current
    SetOutPath "$INSTDIR"
    File /r "${PAYLOAD}\*"
    File /oname=START-HERE.md "${QUICK_START}"
    IfErrors 0 +3
        MessageBox MB_OK "Installation could not finish. Check the destination folder and available disk space, then try again."
        Abort
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    CreateShortcut "$SMPROGRAMS\Compositor.lnk" "$INSTDIR\Compositor.exe" "" "$INSTDIR\Compositor.exe"
    CreateShortcut "$DESKTOP\Compositor.lnk" "$INSTDIR\Compositor.exe" "" "$INSTDIR\Compositor.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "DisplayName" "Compositor for Windows"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "Publisher" "Legion · Compositor contributors"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "DisplayIcon" "$INSTDIR\Compositor.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "URLInfoAbout" "https://github.com/almosthuman-ai/Compositor"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "NoRepair" 1
SectionEnd

Section "Uninstall"
    SetShellVarContext current
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor" "InstallLocation"
    ${If} $0 == $INSTDIR
        Delete "$SMPROGRAMS\Compositor.lnk"
        Delete "$DESKTOP\Compositor.lnk"
        DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Compositor"
    ${EndIf}
    ; Generated from the shipped payload: never recursively remove a user's folder.
    !include "${REMOVE_FILES}"
    Delete "$INSTDIR\START-HERE.md"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
SectionEnd
