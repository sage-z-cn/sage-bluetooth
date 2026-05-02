# 数据模型设计文档

## 1. 模型概述

数据模型层定义了应用中所有核心数据结构的字段、类型和关系。模型设计遵循以下原则：

- **不可变优先**：模型创建后尽量不变，更新时创建新实例
- **与 Bleak 解耦**：UI 层不直接依赖 Bleak 类型
- **序列化友好**：支持 JSON 序列化，便于配置持久化

---

## 2. BLEDeviceModel (设备模型)

表示扫描发现的一个 BLE 设备。

### 2.1 字段定义

| 字段 | 类型 | 说明 |
|-----|------|------|
| address | `str` | 设备 MAC 地址，唯一标识 |
| name | `str` | 设备广播名称 |
| rssi | `int` | 信号强度 (dBm)，负数，越接近 0 越强 |
| appearance | `int` | Appearance 特征值，用于识别设备类型 |
| manufacturer_data | `dict[int, bytes]` | 厂商特定广播数据 |
| service_uuids | `list[str]` | 广播中声明的服务 UUID 列表 |
| tx_power | `Optional[int]` | 发射功率 (dBm) |
| is_connectable | `bool` | 是否可连接 |
| last_seen | `datetime` | 最后一次发现时间 |

### 2.2 伪代码

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class BLEDeviceModel:
    address: str
    name: str = "Unknown"
    rssi: int = -100
    appearance: int = 0
    manufacturer_data: dict = field(default_factory=dict)
    service_uuids: list[str] = field(default_factory=list)
    tx_power: Optional[int] = None
    is_connectable: bool = True
    last_seen: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_bleak(cls, device, advertisement_data) -> "BLEDeviceModel":
        return cls(
            address=device.address,
            name=device.name or advertisement_data.local_name or "Unknown",
            rssi=advertisement_data.rssi or -100,
            appearance=advertisement_data.appearance or 0,
            manufacturer_data=dict(advertisement_data.manufacturer_data),
            service_uuids=list(advertisement_data.service_uuids),
            tx_power=advertisement_data.tx_power,
            is_connectable=advertisement_data.is_connectable,
        )

    @property
    def display_name(self) -> str:
        """用于 UI 显示的友好名称"""
        return self.name if self.name != "Unknown" else f"Unknown ({self.address[-5:]})"

    @property
    def signal_quality(self) -> int:
        """信号质量 0-100"""
        # RSSI 范围约 -30(极好) 到 -90(极弱)
        return max(0, min(100, 2 * (self.rssi + 100)))
```

---

## 3. DeviceInfoModel (设备信息模型)

表示已连接设备的详细信息，通过 GATT 读取获得。

### 3.1 字段定义

| 字段 | 类型 | 说明 |
|-----|------|------|
| address | `str` | 设备地址 |
| name | `str` | 设备名称 |
| appearance | `int` | Appearance 值 |
| manufacturer | `Optional[str]` | 厂商名称 |
| model_number | `Optional[str]` | 型号 |
| serial_number | `Optional[str]` | 序列号 |
| hardware_revision | `Optional[str]` | 硬件版本 |
| firmware_revision | `Optional[str]` | 固件版本 |
| software_revision | `Optional[str]` | 软件版本 |
| battery_level | `Optional[int]` | 电量百分比 (0-100) |
| services | `list[GattServiceModel]` | 发现的 GATT 服务列表 |

### 3.2 伪代码

```python
@dataclass
class DeviceInfoModel:
    address: str = ""
    name: str = "Unknown"
    appearance: int = 0
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    hardware_revision: Optional[str] = None
    firmware_revision: Optional[str] = None
    software_revision: Optional[str] = None
    battery_level: Optional[int] = None
    services: list = field(default_factory=list)

    @property
    def device_type(self) -> str:
        """根据 appearance 返回设备类型名称"""
        return resolve_device_type(self.appearance)

    @property
    def has_battery_info(self) -> bool:
        return self.battery_level is not None

    @property
    def battery_icon(self) -> str:
        """返回电量对应的图标名称"""
        if self.battery_level is None:
            return "battery_unknown"
        if self.battery_level >= 60:
            return "battery_good"
        if self.battery_level >= 20:
            return "battery_medium"
        return "battery_low"
```

---

## 4. GattServiceModel (GATT 服务模型)

表示设备上的一个 GATT 服务。

### 4.1 字段定义

| 字段 | 类型 | 说明 |
|-----|------|------|
| uuid | `str` | 服务 UUID |
| name | `str` | 服务名称（从 UUID 解析） |
| characteristics | `list[GattCharacteristicModel]` | 该服务下的特征列表 |

### 4.2 伪代码

```python
@dataclass
class GattServiceModel:
    uuid: str
    name: str = "Unknown Service"
    characteristics: list = field(default_factory=list)

    @classmethod
    def from_bleak_service(cls, service) -> "GattServiceModel":
        return cls(
            uuid=service.uuid,
            name=resolve_service_name(service.uuid),
            characteristics=[
                GattCharacteristicModel.from_bleak_char(c)
                for c in service.characteristics
            ]
        )
```

---

## 5. GattCharacteristicModel (GATT 特征模型)

表示服务下的一个 GATT 特征。

### 5.1 字段定义

| 字段 | 类型 | 说明 |
|-----|------|------|
| uuid | `str` | 特征 UUID |
| name | `str` | 特征名称 |
| properties | `list[str]` | 属性列表: read, write, notify, indicate 等 |
| value | `Optional[bytes]` | 读取到的原始值 |

### 5.2 伪代码

```python
@dataclass
class GattCharacteristicModel:
    uuid: str
    name: str = "Unknown Characteristic"
    properties: list[str] = field(default_factory=list)
    value: Optional[bytes] = None

    @property
    def can_read(self) -> bool:
        return "read" in self.properties

    @property
    def can_write(self) -> bool:
        return "write" in self.properties or "write-without-response" in self.properties

    @property
    def can_notify(self) -> bool:
        return "notify" in self.properties
```

---

## 6. AppState (应用状态模型)

表示应用运行时的全局状态。

### 6.1 字段定义

| 字段 | 类型 | 说明 |
|-----|------|------|
| is_adapter_on | `bool` | 蓝牙适配器是否开启 |
| is_scanning | `bool` | 是否正在扫描 |
| connected_device | `Optional[str]` | 当前连接的设备地址 |
| selected_device | `Optional[str]` | 当前选中的设备地址 |
| discovered_devices | `dict[str, BLEDeviceModel]` | 扫描发现的设备字典 |
| last_error | `Optional[str]` | 最后一次错误信息 |

### 6.2 伪代码

```python
@dataclass
class AppState:
    is_adapter_on: bool = False
    is_scanning: bool = False
    connected_device: Optional[str] = None
    selected_device: Optional[str] = None
    discovered_devices: dict[str, BLEDeviceModel] = field(default_factory=dict)
    last_error: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self.connected_device is not None

    @property
    def device_count(self) -> int:
        return len(self.discovered_devices)

    def get_device(self, address: str) -> Optional[BLEDeviceModel]:
        return self.discovered_devices.get(address)

    def update_device(self, device: BLEDeviceModel):
        self.discovered_devices[device.address] = device

    def clear_devices(self):
        self.discovered_devices.clear()
```

---

## 7. AppConfig (应用配置模型)

表示用户可持久化的配置项。

### 7.1 字段定义

| 字段 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| auto_hide_on_blur | `bool` | True | 失去焦点时自动隐藏窗口 |
| scan_timeout | `float` | 10.0 | 默认扫描超时（秒） |
| battery_poll_interval | `int` | 60 | 电量轮询间隔（秒） |
| show_disconnected_devices | `bool` | False | 是否显示已断开的历史设备 |
| theme | `str` | "light" | UI 主题: light / dark |
| window_width | `int` | 400 | 窗口宽度 |
| window_height | `int` | 600 | 窗口高度 |

### 7.2 伪代码

```python
import json
from pathlib import Path

@dataclass
class AppConfig:
    auto_hide_on_blur: bool = True
    scan_timeout: float = 10.0
    battery_poll_interval: int = 60
    show_disconnected_devices: bool = False
    theme: str = "light"
    window_width: int = 400
    window_height: int = 600

    CONFIG_PATH: ClassVar[Path] = Path.home() / ".sage-bluetooth" / "config.json"

    def save(self):
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls) -> "AppConfig":
        if not cls.CONFIG_PATH.exists():
            return cls()
        with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
```

---

## 8. 模型关系图

```
┌─────────────────────┐
│    AppState         │
├─────────────────────┤
│ discovered_devices  │───▶┌─────────────────────┐
│ connected_device    │────│  BLEDeviceModel     │
│ selected_device     │────├─────────────────────┤
└─────────────────────┘    │ address (PK)        │
                           │ name                │
                           │ rssi                │
                           │ appearance          │
                           │ service_uuids       │
                           └─────────────────────┘
                                    │
                                    │ 连接后读取
                                    ▼
                           ┌─────────────────────┐
                           │  DeviceInfoModel    │
                           ├─────────────────────┤
                           │ address             │
                           │ manufacturer        │
                           │ model_number        │
                           │ battery_level       │
                           │ services            │───▶┌─────────────────────┐
                           └─────────────────────┘    │  GattServiceModel   │
                                                      ├─────────────────────┤
                                                      │ uuid                │
                                                      │ characteristics     │───▶┌─────────────────────────┐
                                                      └─────────────────────┘    │  GattCharacteristicModel│
                                                                                 ├─────────────────────────┤
                                                                                 │ uuid                    │
                                                                                 │ properties              │
                                                                                 │ value                   │
                                                                                 └─────────────────────────┘
```

---

## 9. 枚举定义

### 9.1 ConnectionState (连接状态)

```python
from enum import Enum, auto

class ConnectionState(Enum):
    DISCONNECTED = auto()      # 未连接
    CONNECTING = auto()        # 连接中
    CONNECTED = auto()         # 已连接
    DISCONNECTING = auto()     # 断开中
    PAIRING = auto()           # 配对中
```

### 9.2 ScanState (扫描状态)

```python
class ScanState(Enum):
    IDLE = auto()              # 空闲
    SCANNING = auto()          # 扫描中
```

### 9.3 DeviceType (设备类型)

```python
class DeviceType(Enum):
    UNKNOWN = auto()
    HEADPHONE = auto()         # 耳机
    HEADSET = auto()           # 头戴式耳机
    SPEAKER = auto()           # 音箱
    KEYBOARD = auto()          # 键盘
    MOUSE = auto()             # 鼠标
    GAMEPAD = auto()           # 游戏手柄
    WATCH = auto()             # 手表
    FITNESS_TRACKER = auto()   # 运动手环
    PHONE = auto()             # 手机
    TABLET = auto()            # 平板
    COMPUTER = auto()          # 电脑
    THERMOMETER = auto()       # 温度计
    HEART_RATE = auto()        # 心率计
    BLOOD_PRESSURE = auto()    # 血压计
    GLUCOSE = auto()           # 血糖仪
```
