!include "MUI2.nsh"

; Application info
Name "MantıPDF"
OutFile "MantiPDF-Setup.exe"
InstallDir "$PROGRAMFILES\MantiPDF"
InstallDirRegKey HKLM "Software\MantiPDF" "Install_Dir"

; Request admin privileges
RequestExecutionLevel admin

; Modern UI settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\..\resources\icon.ico"
!define MUI_UNICON "..\..\resources\icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "Turkish"
!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "MantıPDF" SecMain
    SetOutPath $INSTDIR
    
    ; Copy files from PyInstaller output
    File /r "..\..\dist\MantiPDF\*.*"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\MantıPDF"
    CreateShortcut "$SMPROGRAMS\MantıPDF\MantıPDF.lnk" "$INSTDIR\MantiPDF.exe"
    CreateShortcut "$SMPROGRAMS\MantıPDF\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortcut "$DESKTOP\MantıPDF.lnk" "$INSTDIR\MantiPDF.exe"
    
    ; Write registry keys
    WriteRegStr HKLM "Software\MantiPDF" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MantiPDF" "DisplayName" "MantıPDF"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MantiPDF" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MantiPDF" "DisplayIcon" "$INSTDIR\MantiPDF.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MantiPDF" "Publisher" "Mehmet Emin Korkusuz"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MantiPDF" "DisplayVersion" "1.0.0"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MantiPDF" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MantiPDF" "NoRepair" 1
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\MantıPDF\*.*"
    RMDir "$SMPROGRAMS\MantıPDF"
    Delete "$DESKTOP\MantıPDF.lnk"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MantiPDF"
    DeleteRegKey HKLM "Software\MantiPDF"
SectionEnd
