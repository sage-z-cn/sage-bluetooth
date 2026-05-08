import traceback
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal
from winsdk.windows.devices.bluetooth import BluetoothDevice
from winsdk.windows.devices.enumeration import DeviceInformation

from src.models.device import BLEDeviceModel
from src.utils.logger import get_logger

logger = get_logger("paired_loader")


async def _find_paired_device_infos() -> list[tuple[DeviceInformation, BluetoothDevice]]:
    all_devices = await DeviceInformation.find_all_async()
    results: list[tuple[DeviceInformation, BluetoothDevice]] = []
    for i in range(all_devices.size):
        info = all_devices.get_at(i)
        if "Bluetooth" not in info.id:
            continue
        try:
            bt = await BluetoothDevice.from_id_async(info.id)
            if bt is not None:
                results.append((info, bt))
        except Exception:
            pass
    return results


class PairedDeviceLoader(QObject):
    paired_devices_loaded = pyqtSignal(list)

    async def load_paired_devices(self) -> list[BLEDeviceModel]:
        devices: list[BLEDeviceModel] = []
        try:
            paired_list = await _find_paired_device_infos()
            for info, bt_device in paired_list:
                try:
                    address = _format_address(bt_device.bluetooth_address)
                    name = info.name or "Unknown"
                    model = BLEDeviceModel(
                        address=address,
                        name=name,
                        rssi=-100,
                        is_paired=True,
                        last_seen=datetime.now(),
                    )
                    devices.append(model)
                    logger.info("Paired device: %s (%s)", name, address)
                except Exception as e:
                    logger.debug("Failed to read paired device %s: %s", info.name, e)
            logger.info("Loaded %d paired devices", len(devices))
        except Exception as e:
            logger.error("Failed to load paired devices: %s\n%s", e, traceback.format_exc())
        self.paired_devices_loaded.emit(devices)
        return devices


async def unpair_device_by_address(address: str) -> bool:
    """通过蓝牙地址解除系统级设备配对。"""
    all_devices = await DeviceInformation.find_all_async()
    for i in range(all_devices.size):
        info = all_devices.get_at(i)
        if "Bluetooth" not in info.id:
            continue
        try:
            bt = await BluetoothDevice.from_id_async(info.id)
            if bt is not None:
                formatted = _format_address(bt.bluetooth_address)
                if formatted == address:
                    result = await info.pairing.unpair_async()
                    logger.info("System unpaired: %s (%s)", info.name or "Unknown", address)
                    return True
        except Exception as e:
            logger.debug("Unpair check failed for %s: %s", info.name if 'info' in dir() else "?", e)
            continue
    logger.warning("Device not found for system unpair: %s", address)
    return False


def _format_address(raw) -> str:
    try:
        addr = int(raw)
    except (TypeError, ValueError):
        if isinstance(raw, str):
            cleaned = raw.strip().replace(":", "").replace("-", "")
            addr = int(cleaned, 16) if cleaned else 0
        else:
            addr = 0
    bytes_list = [(addr >> (8 * i)) & 0xFF for i in range(5, -1, -1)]
    return ":".join(f"{b:02X}" for b in bytes_list)
