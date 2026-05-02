# 打包与部署设计文档

## 1. 依赖管理

### 1.1 requirements.txt

```
PyQt6>=6.5.0
bleak>=3.0.1
qasync>=0.28.0
```

### 1.2 开发依赖

```
pytest>=8.0.0
pytest-qt>=4.2.0
pytest-asyncio>=0.23.0
pyinstaller>=6.0.0
```

---

## 2. PyInstaller 打包配置

### 2.1 打包脚本 (build.py)

```python
import PyInstaller.__main__
import os
import shutil

# 清理旧构建
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

PyInstaller.__main__.run([
    "src/main.py",                          # 入口脚本
    "--name=SageBluetooth",                 # 应用名称
    "--windowed",                           # 无控制台窗口
    "--onefile",                            # 打包为单文件
    "--icon=resources/icons/app.ico",       # 应用图标
    "--add-data=resources;resources",       # 打包资源文件
    "--hidden-import=qasync",               # 隐藏导入
    "--hidden-import=bleak.backends.winrt",
    "--hidden-import=bleak.args",
    "--clean",                              # 清理临时文件
    "--noconfirm",                          # 不确认覆盖
])
```

### 2.2 单文件 vs 单目录模式

| 模式 | 优点 | 缺点 | 推荐 |
|-----|------|------|------|
| `--onefile` | 只有一个 exe，分发方便 | 启动慢（需解压） | **推荐** |
| `--onedir` | 启动快，文件结构清晰 | 多文件，分发麻烦 | 备选 |

### 2.3 资源文件处理

PyInstaller 打包后，资源文件路径需要通过 `sys._MEIPASS` 获取：

```python
import sys
import os

def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径（兼容开发环境和 PyInstaller 打包后）"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
```

---

## 3. 安装程序制作

### 3.1 方案对比

| 方案 | 优点 | 缺点 | 推荐 |
|-----|------|------|------|
| **Inno Setup** | 免费，功能强大，Windows 原生 | 需单独学习脚本 | **推荐** |
| NSIS | 轻量，开源 | 脚本复杂 | 备选 |
| 直接分发 exe | 最简单 | 无安装体验，无法创建快捷方式 | 测试阶段 |

### 3.2 Inno Setup 脚本要点

```pascal
[Setup]
AppName=Sage Bluetooth
AppVersion=1.0.0
DefaultDirName={autopf}\Sage Bluetooth
DefaultGroupName=Sage Bluetooth
OutputDir=installer
OutputBaseFilename=SageBluetooth-Setup-1.0.0
SetupIconFile=resources\icons\app.ico
PrivilegesRequired=admin  ; 需要管理员权限（用于蓝牙开关功能）

[Files]
Source: "dist\SageBluetooth.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Sage Bluetooth"; Filename: "{app}\SageBluetooth.exe"
Name: "{autodesktop}\Sage Bluetooth"; Filename: "{app}\SageBluetooth.exe"
Name: "{autostartup}\Sage Bluetooth"; Filename: "{app}\SageBluetooth.exe"; Tasks: startup

[Tasks]
Name: "startup"; Description: "开机自动启动"; GroupDescription: "附加选项:"

[Run]
Filename: "{app}\SageBluetooth.exe"; Description: "立即运行 Sage Bluetooth"; Flags: nowait postinstall skipifsilent
```

---

## 4. 自动更新设计（可选）

### 4.1 简单版本检查

```python
import urllib.request
import json

CURRENT_VERSION = "1.0.0"
UPDATE_URL = "https://your-server.com/api/version"

def check_update() -> Optional[str]:
    try:
        with urllib.request.urlopen(UPDATE_URL, timeout=5) as response:
            data = json.loads(response.read())
            latest = data["version"]
            if latest > CURRENT_VERSION:
                return latest
    except:
        pass
    return None
```

---

## 5. 日志与调试

### 5.1 日志配置

```python
import logging
from pathlib import Path

def setup_logging():
    log_dir = Path.home() / ".sage-bluetooth" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ]
    )
```

### 5.2 Bleak 调试日志

通过环境变量开启 Bleak 的详细日志：

```python
os.environ["BLEAK_LOGGING"] = "1"
```

---

## 6. 运行环境要求

| 要求 | 说明 |
|-----|------|
| 操作系统 | Windows 10 版本 16299 (Fall Creators Update) 或更高 |
| 运行时 | 无需额外 Python 环境（PyInstaller 已打包） |
| 蓝牙适配器 | 支持 BLE (Bluetooth 4.0+) 的适配器 |
| 权限 | 蓝牙开关功能需要管理员权限 |
| 依赖库 | Visual C++ Redistributable（通常系统已自带） |

---

## 7. 目录结构（打包后）

### 7.1 单文件模式运行时

```
%TEMP%/_MEIxxxxx/           # PyInstaller 解压目录
├── SageBluetooth.exe       # 主程序
├── resources/
│   ├── icons/
│   └── styles/
├── python310.dll
├── PyQt6/
├── bleak/
└── ...
```

### 7.2 用户数据目录

```
%USERPROFILE%/.sage-bluetooth/
├── config.json             # 用户配置
├── logs/
│   └── app.log             # 运行日志
└── cache/
    └── devices.json        # 缓存的设备信息
```

---

## 8. 测试策略

### 8.1 单元测试

```python
# tests/test_device_type_resolver.py
import pytest
from src.utils.device_type_resolver import resolve_device_type
from src.models.device import DeviceType

def test_resolve_headphone():
    assert resolve_device_type(0x0080) == DeviceType.HEADPHONE

def test_resolve_keyboard():
    assert resolve_device_type(0x0015) == DeviceType.KEYBOARD

def test_resolve_unknown():
    assert resolve_device_type(0xFFFF) == DeviceType.UNKNOWN
```

### 8.2 集成测试

```python
# tests/test_bluetooth_manager.py
import pytest
from src.core.bluetooth_manager import BluetoothManager

@pytest.mark.asyncio
async def test_scan_devices():
    manager = BluetoothManager()
    # 注：需要真实蓝牙环境
    devices = await manager.scanner.start_scan(timeout=5.0)
    assert isinstance(devices, list)
```

### 8.3 UI 测试

```python
# tests/test_main_window.py
from pytestqt.qt_compat import qt_api
from src.ui.main_window import MainWindow

def test_window_size(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.width() == 400
    assert window.height() == 600
```

---

## 9. 发布检查清单

- [ ] 版本号更新
- [ ] 更新日志 (CHANGELOG.md)
- [ ] 运行测试套件
- [ ] PyInstaller 打包成功
- [ ] 在干净 Windows 环境测试
- [ ] 蓝牙开关功能测试（管理员权限）
- [ ] 设备扫描功能测试
- [ ] 设备连接/断开测试
- [ ] 电量读取测试
- [ ] 托盘图标功能测试
- [ ] 窗口弹出/隐藏测试
- [ ] 安装程序测试
- [ ] 卸载功能测试
