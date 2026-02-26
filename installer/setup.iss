; Inno Setup Script for SystemAnalyzer
; Build with: ISCC.exe setup.iss /DAppVersion=1.0.0
; Or from GitHub Actions (version passed automatically)

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppName=System Analyzer
AppVersion={#AppVersion}
AppPublisher=YourName
AppPublisherURL=https://github.com/teogames11-sudo/SystemAnalyzer
AppSupportURL=https://github.com/teogames11-sudo/SystemAnalyzer/issues
AppUpdatesURL=https://github.com/teogames11-sudo/SystemAnalyzer/releases
DefaultDirName={autopf}\SystemAnalyzer
DefaultGroupName=System Analyzer
AllowNoIcons=yes
OutputDir=..\dist\installer
OutputBaseFilename=SystemAnalyzer-Setup-{#AppVersion}
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\SystemAnalyzer.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\SystemAnalyzer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\icon.ico";               DestDir: "{app}";  Flags: ignoreversion

[Icons]
Name: "{group}\System Analyzer";        Filename: "{app}\SystemAnalyzer.exe"
Name: "{group}\Удалить System Analyzer"; Filename: "{uninstallexe}"
Name: "{commondesktop}\System Analyzer"; Filename: "{app}\SystemAnalyzer.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SystemAnalyzer.exe"; Description: "Запустить System Analyzer"; Flags: nowait postinstall skipifsilent
