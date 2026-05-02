# 蓝牙核心模块设计文档

## 1. 模块概述

蓝牙核心模块负责所有与 BLE 设备交互的底层操作，基于 `bleak` 库封装，向上层 UI 提供同步风格的信号/槽接口。核心设计目标是：

1. **隔离异步复杂性**：Bleak 的 asyncio API 对 UI 调用方透明
2. **状态集中管理**：所有蓝牙相关状态统一维护
3. **错误优雅处理**：BLE 操作失败时提供清晰的错误信息

---

## 2. 模块结构

```
core/
├── __init__.py
├── bluetooth_manager.py      # 蓝牙管理器 (门面类)
├── adapter_controller.py     # 蓝牙适配器开关控制
├── device_scanner.py         # 设备扫描器
├── device_connector.py       # 设备连接/断开/配对管理
└── gatt_reader.py            # GATT 特征读取器
```

---

## 3. BluetoothManager (门面类)

`BluetoothManager` 是上层 UI 与蓝牙核心交互的唯一入口，采用单例模式管理。

### 3.1 职责

- 协调 Scanner、Connector、AdapterController、GattReader 各子模块
- 维护全局蓝牙状态（适配器状态、扫描状态、连接状态）
- 将异步事件转换为 Qt 信号发射给 UI

### 3.2 伪代码

```python
class BluetoothManager(QObject):
    # ── 信号定义 ──
    adapter_state_changed = Signal(bool)           # 蓝牙适配器开关状态
    scan_started = Signal()
    scan_finished = Signal()
    device_discovered = Signal(BLEDeviceModel)     # 发现新设备
    device_updated = Signal(BLEDeviceModel)        # 设备信息更新
    connection_state_changed = Signal(str, bool)   # (address, is_connected)
    device_info_ready = Signal(DeviceInfoModel)    # 设备信息读取完成
    battery_level_updated = Signal(str, int)       # (address, percentage)
    error_occurred = Signal(str)                   # 错误信息

    # ── 核心方法 ──
    def is_adapter_on(self) -> bool
    def turn_on_adapter(self) -> None
    def turn_off_adapter(self) -> None
    def start_scan(self, timeout: float = 10.0) -> None
    def stop_scan(self) -> None
    def connect_device(self, address: str) -> None
    def disconnect_device(self, address: str) -> None
    def pair_device(self, address: str) -> None
    def read_device_info(self, address: str) -> None
    def get_connected_device(self) -> Optional[BLEDeviceModel]
```

### 3.3 状态机

```
                    ┌─────────────┐
         ┌─────────▶│   IDLE      │◀────────┐
         │          │  (空闲)      │         │
         │          └──────┬──────┘         │
         │                 │ start_scan()   │ scan_finished()
         │                 ▼                │
         │          ┌─────────────┐         │
         │    ┌─────│  SCANNING   │─────┐   │
         │    │     │  (扫描中)    │     │   │
         │    │     └──────┬──────┘     │   │
         │    │            │            │   │
         │ stop_scan()  device_found   timeout
         │    │            │            │   │
         │    │            ▼            │   │
         │    │     ┌─────────────┐     │   │
         │    └────▶│ CONNECTING  │◀────┘   │
         │          │  (连接中)    │         │
         │          └──────┬──────┘         │
         │                 │ connect()      │
         │                 ▼                │
         │          ┌─────────────┐         │
         │    ┌─────│  CONNECTED  │─────┐   │
         │    │     │  (已连接)    │     │   │
         │    │     └──────┬──────┘     │   │
         │    │            │            │   │
         │ disconnect()  read_info   read_battery
         │    │            │            │   │
         │    │            ▼            │   │
         │    │     ┌─────────────┐     │   │
         │    └────▶│DISCONNECTING│─────┘   │
         │          │ (断开中)     │         │
         │          └─────────────┘         │
         │                                  │
         └──────────────────────────────────┘
```

---

## 4. AdapterController (蓝牙适配器控制)

### 4.1 职责

控制 Windows 系统蓝牙适配器的电源状态。

### 4.2 实现方案

由于 Bleak 不提供适配器电源控制 API，采用 **PowerShell PnP 命令** 方案：

```python
class AdapterController:
    def is_adapter_on(self) -> bool:
        """检查蓝牙适配器是否启用"""
        # 通过 PowerShell Get-PnpDevice 查询蓝牙设备状态
        # 返回状态为 "OK" 表示已启用

    def turn_on(self) -> bool:
        """开启蓝牙适配器"""
        # 调用 Enable-PnpDevice
        # 需要管理员权限

    def turn_off(self) -> bool:
        """关闭蓝牙适配器"""
        # 调用 Disable-PnpDevice
        # 需要管理员权限

    def _run_powershell(self, command: str) -> tuple[bool, str]:
        """执行 PowerShell 命令，返回 (success, output)"""
        # 使用 subprocess.run 调用 powershell -Command
```

### 4.3 PowerShell 命令详解

```powershell
# 获取所有蓝牙设备
Get-PnpDevice -Class Bluetooth

# 获取第一个蓝牙设备的 InstanceId
$btDevice = Get-PnpDevice -Class Bluetooth | Where-Object { $_.FriendlyName -like '*Bluetooth*' } | Select-Object -First 1

# 启用蓝牙适配器
Enable-PnpDevice -InstanceId $btDevice.InstanceId -Confirm:$false

# 禁用蓝牙适配器
Disable-PnpDevice -InstanceId $btDevice.InstanceId -Confirm:$false
```

### 4.4 权限处理

```python
def check_admin_privilege() -> bool:
    """检查当前进程是否以管理员权限运行"""
    import ctypes
    return ctypes.windll.shell32.IsUserAnAdmin()

def turn_on(self) -> bool:
    if not check_admin_privilege():
        self.error_occurred.emit("开启蓝牙需要管理员权限，请右键以管理员身份运行本程序")
        return False
    # ... 执行命令
```

---

## 5. DeviceScanner (设备扫描器)

### 5.1 职责

扫描附近 BLE 设备，收集广播数据和 RSSI 信息。

### 5.2 伪代码

```python
class DeviceScanner(QObject):
    device_found = Signal(BLEDeviceModel)
    scan_started = Signal()
    scan_finished = Signal()

    def __init__(self):
        self._scanner: Optional[BleakScanner] = None
        self._is_scanning = False

    async def start_scan(self, timeout: float = 10.0):
        self._is_scanning = True
        self.scan_started.emit()

        def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            model = BLEDeviceModel.from_bleak(device, advertisement_data)
            self.device_found.emit(model)

        self._scanner = BleakScanner(detection_callback=detection_callback)
        await self._scanner.start()
        await asyncio.sleep(timeout)
        await self._scanner.stop()

        self._is_scanning = False
        self.scan_finished.emit()

    async def stop_scan(self):
        if self._scanner and self._is_scanning:
            await self._scanner.stop()
            self._is_scanning = False
```

### 5.3 扫描参数

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| timeout | 10.0 | 单次扫描时长（秒） |
| scanning_mode | "active" | 主动扫描（请求扫描响应） |

### 5.4 设备去重策略

扫描过程中同一设备可能多次上报（信号强度变化、广播数据更新）。采用 **地址去重 + 信息合并** 策略：

```python
# 使用字典按地址去重
_discovered_devices: dict[str, BLEDeviceModel] = {}

def detection_callback(device, advertisement_data):
    address = device.address
    if address in _discovered_devices:
        # 更新 RSSI 和广播数据
        _discovered_devices[address].rssi = device.rssi
        _discovered_devices[address].merge_advertisement(advertisement_data)
    else:
        # 新设备
        model = BLEDeviceModel.from_bleak(device, advertisement_data)
        _discovered_devices[address] = model
        self.device_found.emit(model)
```

---

## 6. DeviceConnector (设备连接管理)

### 6.1 职责

管理 BLE 设备的连接、断开和配对操作。

### 6.2 设计决策：单连接模式

Bleak 在 Windows 上的并发连接支持有限，且本工具为轻量级管理工具，设计为 **同时只能连接一个设备**。连接新设备时自动断开旧设备。

### 6.3 伪代码

```python
class DeviceConnector(QObject):
    connected = Signal(str)          # address
    disconnected = Signal(str)       # address
    connection_failed = Signal(str, str)  # address, reason
    pairing_result = Signal(str, bool)    # address, success

    def __init__(self):
        self._client: Optional[BleakClient] = None
        self._connected_address: Optional[str] = None

    async def connect(self, address: str, pair: bool = False):
        # 如果已有连接，先断开
        if self._client and self._client.is_connected:
            await self.disconnect(self._connected_address)

        # 创建客户端，设置断开回调
        def on_disconnect(client):
            self.disconnected.emit(client.address)
            self._client = None
            self._connected_address = None

        self._client = BleakClient(address, disconnected_callback=on_disconnect)

        try:
            await self._client.connect()
            if pair:
                await self._client.pair()
            self._connected_address = address
            self.connected.emit(address)
        except Exception as e:
            self.connection_failed.emit(address, str(e))

    async def disconnect(self, address: str):
        if self._client and self._client.is_connected:
            await self._client.disconnect()

    async def pair(self, address: str):
        if self._client and self._client.is_connected:
            try:
                await self._client.pair()
                self.pairing_result.emit(address, True)
            except Exception as e:
                self.pairing_result.emit(address, False)
```

### 6.4 连接超时处理

Bleak 默认连接超时约 10 秒。建议在 UI 层显示连接进度，超时后给出友好提示。

---

## 7. GattReader (GATT 特征读取)

### 7.1 职责

连接建立后，读取设备的 GATT 服务和特征值，获取设备信息。

### 7.2 读取的数据项

| 数据项 | GATT Service | Characteristic UUID | 说明 |
|-------|-------------|---------------------|------|
| 设备名称 | 0x1800 (GAP) | 0x2A00 | 设备广播名称 |
| Appearance | 0x1800 (GAP) | 0x2A01 | 设备外观类型 |
| 厂商名称 | 0x180A (DIS) | 0x2A29 | Manufacturer Name |
| 型号 | 0x180A (DIS) | 0x2A24 | Model Number |
| 序列号 | 0x180A (DIS) | 0x2A25 | Serial Number |
| 硬件版本 | 0x180A (DIS) | 0x2A27 | Hardware Revision |
| 固件版本 | 0x180A (DIS) | 0x2A26 | Firmware Revision |
| 软件版本 | 0x180A (DIS) | 0x2A28 | Software Revision |
| 电量 | 0x180F (BAS) | 0x2A19 | Battery Level (0-100%) |

### 7.3 伪代码

```python
class GattReader:
    # UUID 常量
    SERVICE_GAP = "00001800-0000-1000-8000-00805f9b34fb"
    SERVICE_DIS = "0000180a-0000-1000-8000-00805f9b34fb"
    SERVICE_BAS = "0000180f-0000-1000-8000-00805f9b34fb"

    CHAR_DEVICE_NAME = "00002a00-0000-1000-8000-00805f9b34fb"
    CHAR_APPEARANCE = "00002a01-0000-1000-8000-00805f9b34fb"
    CHAR_MANUFACTURER = "00002a29-0000-1000-8000-00805f9b34fb"
    CHAR_MODEL_NUMBER = "00002a24-0000-1000-8000-00805f9b34fb"
    CHAR_SERIAL_NUMBER = "00002a25-0000-1000-8000-00805f9b34fb"
    CHAR_FIRMWARE_REV = "00002a26-0000-1000-8000-00805f9b34fb"
    CHAR_BATTERY_LEVEL = "00002a19-0000-1000-8000-00805f9b34fb"

    async def read_device_info(self, client: BleakClient) -> DeviceInfoModel:
        info = DeviceInfoModel()
        info.address = client.address

        # 读取 GAP 信息
        try:
            data = await client.read_gatt_char(self.CHAR_DEVICE_NAME)
            info.name = data.decode("utf-8", errors="ignore")
        except:
            info.name = client.name or "Unknown"

        try:
            data = await client.read_gatt_char(self.CHAR_APPEARANCE)
            info.appearance = int.from_bytes(data, "little")
        except:
            info.appearance = 0

        # 读取 DIS 信息
        for char_uuid, field in [
            (self.CHAR_MANUFACTURER, "manufacturer"),
            (self.CHAR_MODEL_NUMBER, "model_number"),
            (self.CHAR_SERIAL_NUMBER, "serial_number"),
            (self.CHAR_FIRMWARE_REV, "firmware_revision"),
        ]:
            try:
                data = await client.read_gatt_char(char_uuid)
                setattr(info, field, data.decode("utf-8", errors="ignore"))
            except:
                pass

        # 读取电量
        try:
            data = await client.read_gatt_char(self.CHAR_BATTERY_LEVEL)
            info.battery_level = data[0]
        except:
            info.battery_level = None

        return info

    async def start_battery_notification(self, client: BleakClient, callback):
        """订阅电量变化通知"""
        try:
            await client.start_notify(self.CHAR_BATTERY_LEVEL, callback)
        except:
            pass
```

### 7.4 电量监控策略

| 策略 | 说明 |
|-----|------|
| 初始读取 | 连接成功后立即读取一次电量 |
| 通知订阅 | 如果设备支持 Battery Level 的 Notify，订阅实时更新 |
| 定时轮询 | 如果不支持 Notify，每 60 秒主动读取一次 |

---

## 8. 错误处理策略

### 8.1 常见错误及处理

| 错误场景 | 异常类型 | UI 提示 |
|---------|---------|---------|
| 蓝牙未开启 | `BleakBluetoothNotAvailableError` | "请开启系统蓝牙后重试" |
| 设备未找到 | `BleakDeviceNotFoundError` | "未找到指定设备，请确认设备在附近且可发现" |
| 连接被拒绝 | `BleakError` (权限相关) | "连接被拒绝，请尝试先配对设备" |
| 连接超时 | `asyncio.TimeoutError` | "连接超时，请检查设备是否可连接" |
| 特征未找到 | `BleakCharacteristicNotFoundError` | "设备不支持此功能" |
| 配对失败 | `BleakError` | "配对失败，请确认配对码或重试" |
| 无管理员权限 | `subprocess.CalledProcessError` | "操作需要管理员权限" |

### 8.2 重连机制

```python
async def connect_with_retry(self, address: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            await self.connect(address)
            return
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0)
            else:
                raise
```

---

## 9. asyncio 与 Qt 整合

### 9.1 方案：qasync

使用 `qasync` 库将 asyncio 事件循环嵌入 Qt 事件循环。

```python
import sys
from PyQt5.QtWidgets import QApplication
import qasync
import asyncio

app = QApplication(sys.argv)
loop = qasync.QEventLoop(app)
asyncio.set_event_loop(loop)

# 现在可以在 Qt 槽函数中使用 async def
async def run_scan():
    await scanner.start_scan()

# 通过 asyncio.create_task 启动异步任务
task = asyncio.create_task(run_scan())

with loop:
    loop.run_forever()
```

### 9.2 异步任务管理

```python
class BluetoothManager(QObject):
    def __init__(self):
        self._tasks: set[asyncio.Task] = set()

    def _run_async(self, coro):
        """启动异步任务并跟踪，防止任务被 GC"""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def start_scan(self, timeout: float = 10.0):
        self._run_async(self._scanner.start_scan(timeout))

    def connect_device(self, address: str):
        self._run_async(self._connector.connect(address))
```

---

## 10. 性能考量

| 场景 | 策略 |
|-----|------|
| 扫描频率 | 用户手动触发，避免后台持续扫描 |
| 连接保持 | 连接后保持，用户主动断开或程序退出时断开 |
| 电量轮询 | 优先使用 Notify，退化为 60 秒轮询 |
| 内存管理 | 扫描结果限制最近 50 个设备，防止内存无限增长 |
| 并发限制 | 单连接模式，避免并发 BLE 操作 |
