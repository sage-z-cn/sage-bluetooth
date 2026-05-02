import logging
from typing import Callable

from bleak import BleakClient
from PyQt6.QtCore import QObject, pyqtSignal

from src.models.device_info import DeviceInfoModel, GattServiceModel
from src.utils.logger import get_logger
from src.utils.uuid_constants import (
    CHAR_APPEARANCE,
    CHAR_BATTERY_LEVEL,
    CHAR_DEVICE_NAME,
    CHAR_FIRMWARE_REVISION,
    CHAR_HARDWARE_REVISION,
    CHAR_MANUFACTURER_NAME,
    CHAR_MODEL_NUMBER,
    CHAR_SERIAL_NUMBER,
    CHAR_SOFTWARE_REVISION,
)

logger = get_logger("gatt_reader")


class GattReader(QObject):
    device_info_ready = pyqtSignal(DeviceInfoModel)
    battery_level_updated = pyqtSignal(str, int)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._poll_task = None

    async def read_device_info(self, client: BleakClient) -> DeviceInfoModel:
        info = DeviceInfoModel(address=client.address)

        info.name = client.name or "Unknown"
        try:
            data = await client.read_gatt_char(CHAR_DEVICE_NAME)
            info.name = data.decode("utf-8", errors="ignore").strip()
        except Exception:
            pass

        try:
            data = await client.read_gatt_char(CHAR_APPEARANCE)
            info.appearance = int.from_bytes(data, "little")
        except Exception:
            pass

        char_map = {
            CHAR_MANUFACTURER_NAME: "manufacturer",
            CHAR_MODEL_NUMBER: "model_number",
            CHAR_SERIAL_NUMBER: "serial_number",
            CHAR_HARDWARE_REVISION: "hardware_revision",
            CHAR_FIRMWARE_REVISION: "firmware_revision",
            CHAR_SOFTWARE_REVISION: "software_revision",
        }
        for char_uuid, field_name in char_map.items():
            try:
                data = await client.read_gatt_char(char_uuid)
                value = data.decode("utf-8", errors="ignore").strip()
                setattr(info, field_name, value)
            except Exception:
                pass

        info.battery_level = await self.read_battery_level(client)

        try:
            services = client.services
            if services:
                info.services = [GattServiceModel.from_bleak_service(s) for s in services]
        except Exception:
            pass

        self.device_info_ready.emit(info)
        logger.info("Device info ready: %s, manufacturer=%s, battery=%s",
                     info.name, info.manufacturer, info.battery_level)
        return info

    async def read_battery_level(self, client: BleakClient) -> int | None:
        try:
            data = await client.read_gatt_char(CHAR_BATTERY_LEVEL)
            return data[0]
        except Exception:
            return None

    async def start_battery_notification(self, client: BleakClient) -> bool:
        try:
            def handler(_, data: bytes):
                if data:
                    level = data[0]
                    self.battery_level_updated.emit(client.address, level)

            await client.start_notify(CHAR_BATTERY_LEVEL, handler)
            logger.info("Battery notification started for %s", client.address)
            return True
        except Exception as e:
            logger.info("Battery notify not supported: %s", e)
            return False

    async def start_battery_polling(self, client: BleakClient, interval: int = 60) -> None:
        if not await self.start_battery_notification(client):
            logger.info("Falling back to polling every %ds", interval)
            while client.is_connected:
                level = await self.read_battery_level(client)
                if level is not None:
                    self.battery_level_updated.emit(client.address, level)
                try:
                    import asyncio
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
