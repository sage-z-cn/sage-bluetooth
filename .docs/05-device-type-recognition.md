# 设备类型识别设计文档

## 1. 概述

设备类型识别是本工具的重要功能之一。通过分析 BLE 设备的广播数据和 GATT 特征，将设备归类为耳机、键盘、鼠标等具体类型，并显示对应的图标。

识别信息来源有两个：
1. **Appearance 特征值**（0x2A01）：GAP 服务中的标准特征，设备声明自己的外观类型
2. **广播数据中的 Service UUID**：设备广播自己支持的服务，可推断设备类型

---

## 2. Appearance 特征值映射

Appearance 是 Bluetooth SIG 定义的标准特征值（Characteristic UUID: 0x2A01），16 位无符号整数。高 10 位表示类别（Category），低 6 位表示子类别（Sub-category）。

### 2.1 完整映射表

```python
APPEARANCE_MAP = {
    # Unknown / Generic
    0x0000: DeviceType.UNKNOWN,
    0x0001: DeviceType.UNKNOWN,       # Generic Phone
    0x0002: DeviceType.UNKNOWN,       # Generic Computer
    0x0003: DeviceType.WATCH,         # Generic Watch
    0x0004: DeviceType.WATCH,         # Watch: Sports Watch
    0x0005: DeviceType.UNKNOWN,       # Generic Clock
    0x0006: DeviceType.UNKNOWN,       # Generic Display
    0x0007: DeviceType.UNKNOWN,       # Generic Remote Control
    0x0008: DeviceType.UNKNOWN,       # Generic Eye-glasses
    0x0009: DeviceType.UNKNOWN,       # Generic Tag
    0x000A: DeviceType.UNKNOWN,       # Generic Keyring
    0x000B: DeviceType.UNKNOWN,       # Generic Media Player
    0x000C: DeviceType.UNKNOWN,       # Generic Barcode Scanner
    0x000D: DeviceType.THERMOMETER,   # Generic Thermometer
    0x000E: DeviceType.THERMOMETER,   # Thermometer: Ear
    0x000F: DeviceType.HEART_RATE,    # Generic Heart rate Sensor
    0x0010: DeviceType.HEART_RATE,    # Heart Rate Sensor: Heart Rate Belt
    0x0011: DeviceType.BLOOD_PRESSURE,# Generic Blood Pressure
    0x0012: DeviceType.BLOOD_PRESSURE,# Blood Pressure: Arm
    0x0013: DeviceType.BLOOD_PRESSURE,# Blood Pressure: Wrist
    0x0014: DeviceType.UNKNOWN,       # Generic Human Interface Device
    0x0015: DeviceType.KEYBOARD,      # HID: Keyboard
    0x0016: DeviceType.MOUSE,         # HID: Mouse
    0x0017: DeviceType.UNKNOWN,       # HID: Joystick
    0x0018: DeviceType.GAMEPAD,       # HID: Gamepad
    0x0019: DeviceType.UNKNOWN,       # HID: Digitizer Tablet
    0x001A: DeviceType.UNKNOWN,       # HID: Card Reader
    0x001B: DeviceType.UNKNOWN,       # HID: Digital Pen
    0x001C: DeviceType.UNKNOWN,       # HID: Barcode Scanner
    0x001D: DeviceType.GLUCOSE,       # Generic Glucose Meter
    0x001E: DeviceType.UNKNOWN,       # Generic: Running Walking Sensor
    0x001F: DeviceType.UNKNOWN,       # Running Walking Sensor: In-Shoe
    0x0020: DeviceType.UNKNOWN,       # Running Walking Sensor: On-Shoe
    0x0021: DeviceType.UNKNOWN,       # Running Walking Sensor: On-Hip
    0x0022: DeviceType.UNKNOWN,       # Generic: Cycling
    0x0023: DeviceType.UNKNOWN,       # Cycling: Cycling Computer
    0x0024: DeviceType.UNKNOWN,       # Cycling: Speed Sensor
    0x0025: DeviceType.UNKNOWN,       # Cycling: Cadence Sensor
    0x0026: DeviceType.UNKNOWN,       # Cycling: Power Sensor
    0x0027: DeviceType.UNKNOWN,       # Cycling: Speed and Cadence Sensor

    # Audio / Media (0x40 - 0x4F 范围)
    0x0040: DeviceType.SPEAKER,       # Generic Pulse Oximeter
    0x0041: DeviceType.SPEAKER,       # Pulse Oximeter: Fingertip
    0x0042: DeviceType.SPEAKER,       # Pulse Oximeter: Wrist Worn
    0x0043: DeviceType.UNKNOWN,       # Generic Weight Scale
    0x0044: DeviceType.UNKNOWN,       # Generic Personal Mobility Device
    0x0045: DeviceType.UNKNOWN,       # Personal Mobility Device: Powered Wheelchair
    0x0046: DeviceType.UNKNOWN,       # Personal Mobility Device: Mobility Scooter
    0x0047: DeviceType.UNKNOWN,       # Generic Continuous Glucose Monitor
    0x0048: DeviceType.UNKNOWN,       # Generic Insulin Pump
    0x0049: DeviceType.UNKNOWN,       # Insulin Pump: Durable Pump
    0x004A: DeviceType.UNKNOWN,       # Insulin Pump: Patch Pump
    0x004B: DeviceType.UNKNOWN,       # Insulin Pen
    0x004C: DeviceType.UNKNOWN,       # Generic Medication Delivery
    0x004D: DeviceType.SPEAKER,       # Generic: Outdoor Sports Activity
    0x004E: DeviceType.UNKNOWN,       # Outdoor Sports Activity: Location Display Device
    0x004F: DeviceType.UNKNOWN,       # Outdoor Sports Activity: Location and Navigation Display Device

    # 更多类别...
    0x0080: DeviceType.HEADPHONE,     # Generic Earbud
    0x0081: DeviceType.HEADPHONE,     # Earbud: Headset
    0x0082: DeviceType.HEADPHONE,     # Earbud: Headphones
    0x0083: DeviceType.HEADSET,       # Headset
    0x0084: DeviceType.HEADPHONE,     # Headphones
    0x0085: DeviceType.SPEAKER,       # Video Conference Device
    0x0086: DeviceType.SPEAKER,       # Video Conference Device: Speakerphone
    0x0087: DeviceType.SPEAKER,       # Video Conference Device: Conference Phone
    0x0088: DeviceType.UNKNOWN,       # Video Conference Device: Video Conference Camera
    0x0089: DeviceType.SPEAKER,       # Video Conference Device: Video Conference Monitor
    0x008A: DeviceType.SPEAKER,       # Video Conference Device: Video Conference Monitor Speakerphone
    0x008B: DeviceType.SPEAKER,       # Video Conference Device: Video Conference Set-Top Box
    0x008C: DeviceType.SPEAKER,       # Video Conference Device: Video Conference Media Center
    0x008D: DeviceType.SPEAKER,       # Video Conference Device: Video Conference Collaboration Bar
    0x008E: DeviceType.SPEAKER,       # Video Conference Device: Video Conference Collaboration Speakerphone
    0x008F: DeviceType.SPEAKER,       # Video Conference Device: Video Conference Collaboration Camera

    # HID 相关 (0x00C0 - 0x00DF)
    0x00C0: DeviceType.KEYBOARD,      # Generic HID
    0x00C1: DeviceType.KEYBOARD,      # HID: Keyboard
    0x00C2: DeviceType.MOUSE,         # HID: Mouse
    0x00C3: DeviceType.GAMEPAD,       # HID: Joystick
    0x00C4: DeviceType.GAMEPAD,       # HID: Gamepad
    0x00C5: DeviceType.UNKNOWN,       # HID: Digitizer Tablet
    0x00C6: DeviceType.UNKNOWN,       # HID: Card Reader
    0x00C7: DeviceType.UNKNOWN,       # HID: Digital Pen
    0x00C8: DeviceType.UNKNOWN,       # HID: Barcode Scanner
    0x00C9: DeviceType.KEYBOARD,      # HID: Touchpad
    0x00CA: DeviceType.UNKNOWN,       # HID: Presentation Remote

    # 可穿戴设备 (0x00E0 - 0x00FF)
    0x00E0: DeviceType.WATCH,         # Generic Wearable Audio Device
    0x00E1: DeviceType.HEADPHONE,     # Wearable Audio Device: Earbud
    0x00E2: DeviceType.HEADSET,       # Wearable Audio Device: Headset
    0x00E3: DeviceType.HEADPHONE,     # Wearable Audio Device: Headphones
    0x00E4: DeviceType.SPEAKER,       # Wearable Audio Device: Neckband

    # 其他音频 (0x0100 - 0x010F)
    0x0100: DeviceType.SPEAKER,       # Generic Speaker
    0x0101: DeviceType.SPEAKER,       # Speaker: Front Speaker
    0x0102: DeviceType.SPEAKER,       # Speaker: Rear Speaker
    0x0103: DeviceType.SPEAKER,       # Speaker: Subwoofer
    0x0104: DeviceType.SPEAKER,       # Speaker: Portable Speaker
    0x0105: DeviceType.SPEAKER,       # Speaker: Outdoor Speaker
    0x0106: DeviceType.SPEAKER,       # Speaker: Soundbar
    0x0107: DeviceType.SPEAKER,       # Speaker: Bookshelf Speaker
    0x0108: DeviceType.SPEAKER,       # Speaker: Standmounted Speaker
    0x0109: DeviceType.SPEAKER,       # Speaker: Ceiling Speaker
    0x010A: DeviceType.SPEAKER,       # Speaker: Floorstanding Speaker
}
```

### 2.2 类别快速判断（按范围）

```python
def resolve_device_type(appearance: int) -> DeviceType:
    """根据 Appearance 值解析设备类型"""
    if appearance in APPEARANCE_MAP:
        return APPEARANCE_MAP[appearance]

    # 按类别范围判断
    category = (appearance >> 6) & 0x3FF

    CATEGORY_MAP = {
        0x00: DeviceType.UNKNOWN,
        0x01: DeviceType.PHONE,
        0x02: DeviceType.COMPUTER,
        0x03: DeviceType.WATCH,
        0x04: DeviceType.WATCH,
        0x05: DeviceType.UNKNOWN,
        0x06: DeviceType.UNKNOWN,
        0x07: DeviceType.UNKNOWN,
        0x08: DeviceType.UNKNOWN,
        0x09: DeviceType.UNKNOWN,
        0x0A: DeviceType.UNKNOWN,
        0x0B: DeviceType.UNKNOWN,
        0x0C: DeviceType.UNKNOWN,
        0x0D: DeviceType.THERMOMETER,
        0x0E: DeviceType.THERMOMETER,
        0x0F: DeviceType.HEART_RATE,
        0x10: DeviceType.HEART_RATE,
        0x11: DeviceType.BLOOD_PRESSURE,
        0x12: DeviceType.BLOOD_PRESSURE,
        0x13: DeviceType.BLOOD_PRESSURE,
        0x14: DeviceType.UNKNOWN,
        0x15: DeviceType.KEYBOARD,
        0x16: DeviceType.MOUSE,
        0x17: DeviceType.GAMEPAD,
        0x18: DeviceType.GAMEPAD,
        0x19: DeviceType.UNKNOWN,
        0x1A: DeviceType.UNKNOWN,
        0x1B: DeviceType.UNKNOWN,
        0x1C: DeviceType.UNKNOWN,
        0x1D: DeviceType.GLUCOSE,
        0x20: DeviceType.FITNESS_TRACKER,
        0x21: DeviceType.FITNESS_TRACKER,
        0x22: DeviceType.FITNESS_TRACKER,
        0x23: DeviceType.FITNESS_TRACKER,
        0x24: DeviceType.UNKNOWN,
        0x25: DeviceType.UNKNOWN,
        0x26: DeviceType.UNKNOWN,
        0x27: DeviceType.UNKNOWN,
        0x40: DeviceType.SPEAKER,
        0x41: DeviceType.SPEAKER,
        0x42: DeviceType.SPEAKER,
        0x43: DeviceType.UNKNOWN,
        0x80: DeviceType.HEADPHONE,
        0x81: DeviceType.HEADPHONE,
        0x82: DeviceType.HEADPHONE,
        0x83: DeviceType.HEADSET,
        0x84: DeviceType.HEADPHONE,
        0x85: DeviceType.SPEAKER,
        0x86: DeviceType.SPEAKER,
        0x87: DeviceType.SPEAKER,
        0xC0: DeviceType.KEYBOARD,
        0xC1: DeviceType.KEYBOARD,
        0xC2: DeviceType.MOUSE,
        0xC3: DeviceType.GAMEPAD,
        0xC4: DeviceType.GAMEPAD,
        0xE0: DeviceType.WATCH,
        0xE1: DeviceType.HEADPHONE,
        0xE2: DeviceType.HEADSET,
        0xE3: DeviceType.HEADPHONE,
        0xE4: DeviceType.SPEAKER,
        0x100: DeviceType.SPEAKER,
        0x101: DeviceType.SPEAKER,
        0x102: DeviceType.SPEAKER,
        0x103: DeviceType.SPEAKER,
        0x104: DeviceType.SPEAKER,
        0x105: DeviceType.SPEAKER,
        0x106: DeviceType.SPEAKER,
        0x107: DeviceType.SPEAKER,
        0x108: DeviceType.SPEAKER,
        0x109: DeviceType.SPEAKER,
        0x10A: DeviceType.SPEAKER,
    }

    return CATEGORY_MAP.get(category, DeviceType.UNKNOWN)
```

---

## 3. Service UUID 辅助识别

当 Appearance 值为 0（未知）或缺失时，通过广播数据中的 Service UUID 辅助判断设备类型。

### 3.1 服务 UUID 到设备类型的映射

```python
SERVICE_TYPE_MAP = {
    # 音频类
    "0000180a-0000-1000-8000-00805f9b34fb": None,  # DIS，通用
    "0000180f-0000-1000-8000-00805f9b34fb": None,  # BAS，通用

    # 耳机/音频相关
    "0000110b-0000-1000-8000-00805f9b34fb": DeviceType.HEADPHONE,  # Audio Sink
    "0000110d-0000-1000-8000-00805f9b34fb": DeviceType.HEADPHONE,  # Advanced Audio Distribution
    "0000110e-0000-1000-8000-00805f9b34fb": DeviceType.HEADPHONE,  # AV Remote Control

    # HID 设备
    "00001812-0000-1000-8000-00805f9b34fb": DeviceType.KEYBOARD,   # HID Service

    # 健康设备
    "0000180d-0000-1000-8000-00805f9b34fb": DeviceType.HEART_RATE,  # Heart Rate Service
    "00001810-0000-1000-8000-00805f9b34fb": DeviceType.BLOOD_PRESSURE,  # Blood Pressure Service
    "00001808-0000-1000-8000-00805f9b34fb": DeviceType.GLUCOSE,     # Glucose Service
    "00001809-0000-1000-8000-00805f9b34fb": DeviceType.THERMOMETER,  # Health Thermometer

    # 健身设备
    "00001814-0000-1000-8000-00805f9b34fb": DeviceType.FITNESS_TRACKER,  # Running Speed and Cadence
    "00001816-0000-1000-8000-00805f9b34fb": DeviceType.FITNESS_TRACKER,  # Cycling Speed and Cadence
    "00001818-0000-1000-8000-00805f34fb": DeviceType.FITNESS_TRACKER,   # Cycling Power
}
```

### 3.2 综合识别逻辑

```python
def resolve_device_type_comprehensive(appearance: int, service_uuids: list[str]) -> DeviceType:
    """综合 Appearance 和 Service UUID 识别设备类型"""

    # 优先使用 Appearance
    if appearance != 0:
        device_type = resolve_device_type(appearance)
        if device_type != DeviceType.UNKNOWN:
            return device_type

    # 辅助使用 Service UUID
    for uuid in service_uuids:
        uuid_lower = uuid.lower()
        if uuid_lower in SERVICE_TYPE_MAP:
            mapped = SERVICE_TYPE_MAP[uuid_lower]
            if mapped is not None:
                return mapped

    # 根据名称关键词推断（兜底策略）
    # 此逻辑在 UI 层根据 device.name 判断

    return DeviceType.UNKNOWN
```

---

## 4. 设备类型到图标的映射

| 设备类型 | 图标文件名 | 图标描述 |
|---------|-----------|---------|
| UNKNOWN | `device_unknown.png` | 通用蓝牙图标 |
| HEADPHONE | `device_headphone.png` | 入耳式耳机 |
| HEADSET | `device_headset.png` | 头戴式耳机 |
| SPEAKER | `device_speaker.png` | 音箱 |
| KEYBOARD | `device_keyboard.png` | 键盘 |
| MOUSE | `device_mouse.png` | 鼠标 |
| GAMEPAD | `device_gamepad.png` | 游戏手柄 |
| WATCH | `device_watch.png` | 智能手表 |
| FITNESS_TRACKER | `device_fitness.png` | 运动手环 |
| PHONE | `device_phone.png` | 手机 |
| TABLET | `device_tablet.png` | 平板 |
| COMPUTER | `device_computer.png` | 电脑 |
| THERMOMETER | `device_thermometer.png` | 温度计 |
| HEART_RATE | `device_heart.png` | 心率计 |
| BLOOD_PRESSURE | `device_blood_pressure.png` | 血压计 |
| GLUCOSE | `device_glucose.png` | 血糖仪 |

---

## 5. 图标资源规格

### 5.1 尺寸规格

| 用途 | 尺寸 | 格式 |
|-----|------|------|
| 列表项图标 | 40x40 px | PNG |
| 托盘图标 | 16x16, 32x32 px | ICO (多分辨率) |
| 详情面板大图标 | 64x64 px | PNG |
| 按钮图标 | 16x16 px | PNG |

### 5.2 图标风格

- **风格**：扁平化 (Flat Design)
- **主色**：`#2196F3` (蓝色)
- **背景**：透明
- **描边**：1px `#1976D2`

---

## 6. 名称关键词辅助识别

当 Appearance 和 Service UUID 都无法识别时，通过设备名称中的关键词进行兜底识别：

```python
NAME_KEYWORDS = {
    DeviceType.HEADPHONE: ["airpods", "earbuds", "earphone", "buds", "freebuds", "galaxy buds"],
    DeviceType.HEADSET: ["headset", "headphone", "索尼", "sony wh", "bose qc"],
    DeviceType.SPEAKER: ["speaker", "音箱", "sound", "audio", "jbl", "bose"],
    DeviceType.KEYBOARD: ["keyboard", "键盘", "keychron", "mx keys", "k380"],
    DeviceType.MOUSE: ["mouse", "鼠标", "mx master", "logitech"],
    DeviceType.GAMEPAD: ["gamepad", "controller", "xbox", "playstation", "joy-con"],
    DeviceType.WATCH: ["watch", "手表", "apple watch", "galaxy watch", "gt ", "huawei watch"],
    DeviceType.FITNESS_TRACKER: ["band", "手环", "mi band", "fitbit", "charge"],
    DeviceType.THERMOMETER: ["thermometer", "体温计"],
    DeviceType.HEART_RATE: ["heart rate", "hrm", "polar", "chest strap"],
}

def resolve_by_name(name: str) -> DeviceType:
    name_lower = name.lower()
    for device_type, keywords in NAME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                return device_type
    return DeviceType.UNKNOWN
```

---

## 7. 识别优先级

设备类型识别的完整优先级链：

```
1. Appearance 特征值（精确匹配）
   ↓
2. Appearance 类别范围（范围匹配）
   ↓
3. Service UUID 映射
   ↓
4. 设备名称关键词匹配
   ↓
5. 默认: UNKNOWN
```
