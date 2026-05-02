[Setup]
AppName=Sage Bluetooth
AppVersion=1.0.0
AppPublisher=Sage
DefaultDirName={autopf}\Sage Bluetooth
DefaultGroupName=Sage Bluetooth
OutputDir=installer
OutputBaseFilename=SageBluetooth-Setup-1.0.0
SetupIconFile=resources\icons\app.ico
UninstallDisplayIcon={app}\SageBluetooth.exe
PrivilegesRequired=admin
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\SageBluetooth.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Sage Bluetooth"; Filename: "{app}\SageBluetooth.exe"
Name: "{autodesktop}\Sage Bluetooth"; Filename: "{app}\SageBluetooth.exe"
Name: "{autostartup}\Sage Bluetooth"; Filename: "{app}\SageBluetooth.exe"; Tasks: startup

[Tasks]
Name: "startup"; Description: "开机自动启动"; GroupDescription: "附加选项:"

[Run]
Filename: "{app}\SageBluetooth.exe"; Description: "立即运行 Sage Bluetooth"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /F /IM SageBluetooth.exe"; Flags: runhidden

[Registry]
Root: HKCU; Subkey: "Software\Sage Bluetooth"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Sage Bluetooth"; ValueType: string; ValueName: "Version"; ValueData: "1.0.0"; Flags: uninsdeletekey
