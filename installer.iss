; installer.iss — Inno Setup script for FreeFlow (no admin, near one-click)
#define MyAppName      "FreeFlow"
#define MyAppVersion   "0.1.1"
#define MyAppPublisher "Benjamin Mathias"
#define MyAppExeName   "FreeFlow.exe"

[Setup]
AppId={{6F8B2A4B-7C9E-4D3A-9B6A-1FF50E3D0042}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist_installer
OutputBaseFilename=FreeFlow-Setup
SetupIconFile=assets\freeflow.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

; ── Near one-click: skip every question ──────────────────────────────────
; No language picker, no welcome page, no install-location page, no
; "additional tasks" page, no "ready to install" confirmation, no finished
; page. The user double-clicks → a progress bar runs → FreeFlow launches.
ShowLanguageDialog=no
DisableWelcomePage=yes
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
DisableFinishedPage=yes

; Auto-update support: if FreeFlow is already running, close it cleanly
; (instead of failing on locked files) and restart it after install.
CloseApplications=force
RestartApplications=yes

[Languages]
; French first so the no-dialog default is French.
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; onedir payload — the whole dist\FreeFlow folder (exe + _internal + bundled
; 145 MB model). recursesubdirs/createallsubdirs copies the nested _internal\.
Source: "dist\FreeFlow\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; A copy of the icon at the app root so shortcuts always resolve it.
Source: "assets\freeflow.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Created unconditionally (no checkbox page) — a friend gets the desktop +
; Start-menu icons automatically.
Name: "{userdesktop}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; \
      IconFilename: "{app}\freeflow.ico"; WorkingDir: "{app}"
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
      IconFilename: "{app}\freeflow.ico"; WorkingDir: "{app}"
Name: "{userprograms}\Desinstaller {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Auto-launch after a normal install (no finished page). Runs automatically
; at the end of the wizard because there is no `postinstall` flag.
Filename: "{app}\{#MyAppExeName}"; Flags: nowait skipifsilent runasoriginaluser
; Silent upgrade (triggered by the in-app updater): relaunch automatically.
Filename: "{app}\{#MyAppExeName}"; Flags: nowait runasoriginaluser; Check: ShouldRelaunchAfterSilent

[Code]
function ShouldRelaunchAfterSilent: Boolean;
begin
  Result := WizardSilent;
end;
