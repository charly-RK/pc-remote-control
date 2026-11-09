; Inno Setup 6 script for PC Remote Control.
; Build first with: pyinstaller PCRemoteControl.spec  (produces dist\PCRemoteControl.exe)

#define MyAppName "PC Remote Control"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "RISK KEEP"
#define MyAppExeName "PCRemoteControl.exe"
#define RunValueName "PCRemoteControl"

[Setup]
AppId={{8F3C2B7A-5D1E-4C6B-9A42-7E0D1B3F6A58}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\PC Remote Control
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=..\..\dist\installer
OutputBaseFilename=PCRemoteControl-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startwithwindows"; Description: "Start with Windows"; GroupDescription: "Additional options:"

[Files]
Source: "..\..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Registry]
; Same HKCU Run value name used by the application (see WindowsAutoStart).
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#RunValueName}"; ValueData: """{app}\{#MyAppExeName}"" --background"; Flags: uninsdeletevalue; Tasks: startwithwindows

[Run]
; The installer runs elevated, so the firewall rule can be created here.
Filename: "{app}\{#MyAppExeName}"; Parameters: "--configure-firewall"; Flags: runhidden waituntilterminated; StatusMsg: "Configuring Windows Firewall..."
Filename: "{app}\{#MyAppExeName}"; Parameters: "--background"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--remove-firewall"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveFirewallRule"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
