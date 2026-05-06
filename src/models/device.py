from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class ConnectionState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    DISCONNECTING = auto()
    PAIRING = auto()


class ScanState(Enum):
    IDLE = auto()
    SCANNING = auto()


class DeviceType(Enum):
    UNKNOWN = auto()
    HEADPHONE = auto()
    HEADSET = auto()
    SPEAKER = auto()
    KEYBOARD = auto()
    MOUSE = auto()
    GAMEPAD = auto()
    WATCH = auto()
    FITNESS_TRACKER = auto()
    PHONE = auto()
    TABLET = auto()
    COMPUTER = auto()
    THERMOMETER = auto()
    HEART_RATE = auto()
    BLOOD_PRESSURE = auto()
    GLUCOSE = auto()


@dataclass(frozen=True)
class BLEDeviceModel:
    address: str
    name: str = "Unknown"
    rssi: int = -100
    appearance: int = 0
    manufacturer_data: dict = field(default_factory=dict)
    service_uuids: list = field(default_factory=list)
    tx_power: Optional[int] = None
    is_connectable: bool = True
    last_seen: datetime = field(default_factory=datetime.now)
    is_paired: bool = False
    connection_state: ConnectionState = ConnectionState.DISCONNECTED

    @classmethod
    def from_bleak(cls, device, advertisement_data) -> "BLEDeviceModel":
        manufacturer_data = advertisement_data.manufacturer_data
        service_uuids = advertisement_data.service_uuids
        if manufacturer_data is None:
            manufacturer_data = {}
        if service_uuids is None:
            service_uuids = []
        return cls(
            address=device.address,
            name=device.name or advertisement_data.local_name or "Unknown",
            rssi=advertisement_data.rssi or -100,
            appearance=getattr(advertisement_data, "appearance", 0) or 0,
            manufacturer_data=dict(manufacturer_data),
            service_uuids=list(service_uuids),
            tx_power=advertisement_data.tx_power,
            is_connectable=getattr(advertisement_data, "is_connectable", True),
        )

    @property
    def display_name(self) -> str:
        if self.name != "Unknown":
            return self.name
        return "未知设备"

    @property
    def signal_quality(self) -> int:
        return max(0, min(100, 2 * (self.rssi + 100)))

    def with_updates(self, **kwargs) -> "BLEDeviceModel":
        current = {
            "address": self.address,
            "name": self.name,
            "rssi": self.rssi,
            "appearance": self.appearance,
            "manufacturer_data": self.manufacturer_data,
            "service_uuids": self.service_uuids,
            "tx_power": self.tx_power,
            "is_connectable": self.is_connectable,
            "last_seen": self.last_seen,
            "is_paired": self.is_paired,
            "connection_state": self.connection_state,
        }
        current.update(kwargs)
        return BLEDeviceModel(**current)
