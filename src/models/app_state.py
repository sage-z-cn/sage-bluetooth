from dataclasses import dataclass, field
from typing import Optional

from src.models.device import BLEDeviceModel, ConnectionState, ScanState


@dataclass
class AppState:
    is_adapter_on: bool = False
    scan_state: ScanState = ScanState.IDLE
    connected_device: Optional[str] = None
    selected_device: Optional[str] = None
    discovered_devices: dict = field(default_factory=dict)
    last_error: Optional[str] = None

    @property
    def is_scanning(self) -> bool:
        return self.scan_state == ScanState.SCANNING

    @property
    def is_connected(self) -> bool:
        return self.connected_device is not None

    @property
    def device_count(self) -> int:
        return len(self.discovered_devices)

    def get_device(self, address: str) -> Optional[BLEDeviceModel]:
        return self.discovered_devices.get(address)

    def update_device(self, device: BLEDeviceModel) -> None:
        self.discovered_devices[device.address] = device

    def remove_device(self, address: str) -> None:
        self.discovered_devices.pop(address, None)
        if self.selected_device == address:
            self.selected_device = None
        if self.connected_device == address:
            self.connected_device = None

    def clear_devices(self) -> None:
        self.discovered_devices.clear()
        self.selected_device = None

    def get_connected_device_model(self) -> Optional[BLEDeviceModel]:
        if self.connected_device:
            return self.discovered_devices.get(self.connected_device)
        return None
