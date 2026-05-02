from dataclasses import dataclass, field
from typing import Optional

from src.models.device import DeviceType
from src.utils.device_type_resolver import resolve_device_type


@dataclass
class GattCharacteristicModel:
    uuid: str
    name: str = "Unknown Characteristic"
    properties: list = field(default_factory=list)
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

    @classmethod
    def from_bleak_char(cls, char) -> "GattCharacteristicModel":
        return cls(
            uuid=char.uuid,
            name=char.description or "Unknown Characteristic",
            properties=list(char.properties),
        )


@dataclass
class GattServiceModel:
    uuid: str
    name: str = "Unknown Service"
    characteristics: list = field(default_factory=list)

    @classmethod
    def from_bleak_service(cls, service) -> "GattServiceModel":
        from src.utils.uuid_constants import resolve_service_name
        return cls(
            uuid=service.uuid,
            name=resolve_service_name(service.uuid),
            characteristics=[
                GattCharacteristicModel.from_bleak_char(c)
                for c in service.characteristics
            ],
        )


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
    def device_type(self) -> DeviceType:
        return resolve_device_type(self.appearance)

    @property
    def has_battery_info(self) -> bool:
        return self.battery_level is not None

    @property
    def battery_icon(self) -> str:
        if self.battery_level is None:
            return "battery_unknown"
        if self.battery_level >= 60:
            return "battery_good"
        if self.battery_level >= 20:
            return "battery_medium"
        return "battery_low"
