#ifndef StageDir
  #error StageDir is required
#endif
#ifndef ReleaseDir
  #define ReleaseDir "."
#endif
#ifndef AppVersion
  #error AppVersion is required
#endif
[Setup]
AppId={{6F4D1BD0-00BE-47F5-9B24-5B9932EC8F20}
AppName=freeAudio Desktop
AppVersion={#AppVersion}
AppVerName=freeAudio Desktop {#AppVersion}
DefaultDirName={localappdata}\Programs\freeAudio Desktop
DefaultGroupName=freeAudio Desktop
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#ReleaseDir}
OutputBaseFilename=freeAudio-Desktop-{#AppVersion}-win64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=classic
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\freeAudioDesktop.exe
CloseApplications=yes
RestartApplications=no
LicenseFile=LICENSE
SetupLogging=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Excludes: "portable.flag,data\*"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\freeAudio Desktop"; Filename: "{app}\freeAudioDesktop.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,freeAudio Desktop}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\freeAudio Desktop"; Filename: "{app}\freeAudioDesktop.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\freeAudioDesktop.exe"; Description: "{cm:LaunchProgram,freeAudio Desktop}"; Flags: nowait postinstall skipifsilent
