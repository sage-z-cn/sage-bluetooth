from src.models.device import DeviceType

APPEARANCE_MAP = {
    0x0000: DeviceType.UNKNOWN,
    0x0001: DeviceType.PHONE,
    0x0002: DeviceType.COMPUTER,
    0x0003: DeviceType.WATCH,
    0x0004: DeviceType.WATCH,
    0x0005: DeviceType.UNKNOWN,
    0x0006: DeviceType.UNKNOWN,
    0x0007: DeviceType.UNKNOWN,
    0x0008: DeviceType.UNKNOWN,
    0x0009: DeviceType.UNKNOWN,
    0x000A: DeviceType.UNKNOWN,
    0x000B: DeviceType.UNKNOWN,
    0x000C: DeviceType.UNKNOWN,
    0x000D: DeviceType.THERMOMETER,
    0x000E: DeviceType.THERMOMETER,
    0x000F: DeviceType.HEART_RATE,
    0x0010: DeviceType.HEART_RATE,
    0x0011: DeviceType.BLOOD_PRESSURE,
    0x0012: DeviceType.BLOOD_PRESSURE,
    0x0013: DeviceType.BLOOD_PRESSURE,
    0x0014: DeviceType.UNKNOWN,
    0x0015: DeviceType.KEYBOARD,
    0x0016: DeviceType.MOUSE,
    0x0017: DeviceType.GAMEPAD,
    0x0018: DeviceType.GAMEPAD,
    0x0019: DeviceType.UNKNOWN,
    0x001A: DeviceType.UNKNOWN,
    0x001B: DeviceType.UNKNOWN,
    0x001C: DeviceType.UNKNOWN,
    0x001D: DeviceType.GLUCOSE,
    0x001E: DeviceType.FITNESS_TRACKER,
    0x001F: DeviceType.FITNESS_TRACKER,
    0x0020: DeviceType.FITNESS_TRACKER,
    0x0021: DeviceType.FITNESS_TRACKER,
    0x0022: DeviceType.FITNESS_TRACKER,
    0x0023: DeviceType.FITNESS_TRACKER,
    0x0024: DeviceType.FITNESS_TRACKER,
    0x0025: DeviceType.FITNESS_TRACKER,
    0x0026: DeviceType.FITNESS_TRACKER,
    0x0027: DeviceType.FITNESS_TRACKER,
    0x0080: DeviceType.HEADPHONE,
    0x0081: DeviceType.HEADPHONE,
    0x0082: DeviceType.HEADPHONE,
    0x0083: DeviceType.HEADSET,
    0x0084: DeviceType.HEADPHONE,
    0x0085: DeviceType.SPEAKER,
    0x0086: DeviceType.SPEAKER,
    0x0087: DeviceType.SPEAKER,
    0x0088: DeviceType.SPEAKER,
    0x0089: DeviceType.SPEAKER,
    0x008A: DeviceType.SPEAKER,
    0x008B: DeviceType.SPEAKER,
    0x008C: DeviceType.SPEAKER,
    0x008D: DeviceType.SPEAKER,
    0x008E: DeviceType.SPEAKER,
    0x008F: DeviceType.SPEAKER,
    0x00C0: DeviceType.KEYBOARD,
    0x00C1: DeviceType.KEYBOARD,
    0x00C2: DeviceType.MOUSE,
    0x00C3: DeviceType.GAMEPAD,
    0x00C4: DeviceType.GAMEPAD,
    0x00C5: DeviceType.UNKNOWN,
    0x00C6: DeviceType.UNKNOWN,
    0x00C7: DeviceType.UNKNOWN,
    0x00C8: DeviceType.UNKNOWN,
    0x00C9: DeviceType.KEYBOARD,
    0x00CA: DeviceType.UNKNOWN,
    0x00E0: DeviceType.WATCH,
    0x00E1: DeviceType.HEADPHONE,
    0x00E2: DeviceType.HEADSET,
    0x00E3: DeviceType.HEADPHONE,
    0x00E4: DeviceType.SPEAKER,
    0x0100: DeviceType.SPEAKER,
    0x0101: DeviceType.SPEAKER,
    0x0102: DeviceType.SPEAKER,
    0x0103: DeviceType.SPEAKER,
    0x0104: DeviceType.SPEAKER,
    0x0105: DeviceType.SPEAKER,
    0x0106: DeviceType.SPEAKER,
    0x0107: DeviceType.SPEAKER,
    0x0108: DeviceType.SPEAKER,
    0x0109: DeviceType.SPEAKER,
    0x010A: DeviceType.SPEAKER,
}

BLE_UUID_BASE = "-0000-1000-8000-00805f9b34fb"

SERVICE_TYPE_MAP = {
    f"0000110b{BLE_UUID_BASE}": DeviceType.HEADPHONE,
    f"0000110d{BLE_UUID_BASE}": DeviceType.HEADPHONE,
    f"0000110e{BLE_UUID_BASE}": DeviceType.HEADPHONE,
    f"00001812{BLE_UUID_BASE}": DeviceType.KEYBOARD,
    f"0000180d{BLE_UUID_BASE}": DeviceType.HEART_RATE,
    f"00001810{BLE_UUID_BASE}": DeviceType.BLOOD_PRESSURE,
    f"00001808{BLE_UUID_BASE}": DeviceType.GLUCOSE,
    f"00001809{BLE_UUID_BASE}": DeviceType.THERMOMETER,
    f"00001814{BLE_UUID_BASE}": DeviceType.FITNESS_TRACKER,
    f"00001816{BLE_UUID_BASE}": DeviceType.FITNESS_TRACKER,
}

NAME_KEYWORDS = {
    DeviceType.HEADPHONE: ["airpods", "earbuds", "earphone", "buds", "freebuds", "galaxy buds"],
    DeviceType.HEADSET: ["headset", "headphone", "sony wh", "bose qc"],
    DeviceType.SPEAKER: ["speaker", "sound", "audio", "jbl", "bose"],
    DeviceType.KEYBOARD: ["keyboard", "keychron", "mx keys", "k380"],
    DeviceType.MOUSE: ["mouse", "mx master", "logitech"],
    DeviceType.GAMEPAD: ["gamepad", "controller", "xbox", "playstation", "joy-con"],
    DeviceType.WATCH: ["watch", "apple watch", "galaxy watch", "gt ", "huawei watch"],
    DeviceType.FITNESS_TRACKER: ["band", "mi band", "fitbit", "charge"],
    DeviceType.THERMOMETER: ["thermometer"],
    DeviceType.HEART_RATE: ["heart rate", "hrm", "polar", "chest strap"],
}


def resolve_device_type(appearance: int) -> DeviceType:
    if appearance in APPEARANCE_MAP:
        return APPEARANCE_MAP[appearance]
    return DeviceType.UNKNOWN


def resolve_by_service_uuids(service_uuids: list) -> DeviceType:
    for uuid in service_uuids:
        uuid_lower = uuid.lower()
        if uuid_lower in SERVICE_TYPE_MAP:
            return SERVICE_TYPE_MAP[uuid_lower]
    return DeviceType.UNKNOWN


def resolve_by_name(name: str) -> DeviceType:
    name_lower = name.lower()
    for device_type, keywords in NAME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                return device_type
    return DeviceType.UNKNOWN


def resolve_device_type_comprehensive(
    appearance: int,
    service_uuids: list | None = None,
    name: str = "",
) -> DeviceType:
    if appearance != 0:
        device_type = resolve_device_type(appearance)
        if device_type != DeviceType.UNKNOWN:
            return device_type

    if service_uuids:
        device_type = resolve_by_service_uuids(service_uuids)
        if device_type != DeviceType.UNKNOWN:
            return device_type

    if name:
        device_type = resolve_by_name(name)
        if device_type != DeviceType.UNKNOWN:
            return device_type

    return DeviceType.UNKNOWN
