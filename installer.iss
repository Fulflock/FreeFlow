; installer.iss — Inno Setup script for FreeFlow (no admin install)
#define MyAppName      "FreeFlow"
#define MyAppVersion   "0.1.0"
#define MyAppPublisher "Benjamin Mathias"
#define MyAppExeName   "FreeFlow.exe"

[Setup]
AppId={{6F8B2A4B-7C9E-4D3A-9B6A-1FF50E3D0042}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist_installer
OutputBaseFilename=FreeFlow-Setup
SetupIconFile=assets\freeflow.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
; Auto-update support: if FreeFlow is already running, Inno Setup will close
; it cleanly (instead of failing on locked files) and restart it after install.
CloseApplications=force
RestartApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french";  MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon";   Description: "{cm:CreateDesktopIcon}";   GroupDescription: "{cm:AdditionalIcons}"
Name: "startmenuicon"; Description: "Ajouter au menu Demarrer"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\FreeFlow.exe";   DestDir: "{app}"; Flags: ignoreversion
Source: "config.json";         DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "assets\freeflow.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; \
      IconFilename: "{app}\assets\freeflow.ico"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
      IconFilename: "{app}\assets\freeflow.ico"; WorkingDir: "{app}"; Tasks: startmenuicon
Name: "{userprograms}\Desinstaller {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent
; On silent upgrade (triggered by the in-app updater) we still want the app
; to relaunch automatically so the user doesn't have to.
Filename: "{app}\{#MyAppExeName}"; Flags: nowait runasoriginaluser; Check: ShouldRelaunchAfterSilent

[Code]
function ShouldRelaunchAfterSilent: Boolean;
begin
  Result := WizardSilent;
end;
