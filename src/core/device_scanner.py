import asyncio
import logging
from datetime import datetime

from bleak import BleakScanner
from PyQt6.QtCore import QObject, pyqtSignal

from src.models.device import BLEDeviceModel
from src.utils.logger import get_logger

logger = get_logger("scanner")


class DeviceScanner(QObject):
    device_found = pyqtSignal(BLEDeviceModel)
    device_updated = pyqtSignal(BLEDeviceModel)
    scan_started = pyqtSignal()
    scan_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    MAX_DEVICES = 50

    def __init__(self):
        super().__init__()
        self._scanner = None
        self._is_scanning = False
        self._discovered: dict[str, BLEDeviceModel] = {}

    @property
    def is_scanning(self) -> bool:
        return self._is_scanning

    async def start_scan(self, timeout: float = 10.0) -> None:
        if self._is_scanning:
            logger.warning("Scan already in progress")
            return

        self._is_scanning = True
        self._discovered.clear()
        self.scan_started.emit()
        logger.info("Starting scan (timeout=%.1fs)", timeout)

        def detection_callback(device, advertisement_data):
            address = device.address
            try:
                new_model = BLEDeviceModel.from_bleak(device, advertisement_data)
            except Exception as e:
                logger.debug("Failed to parse device %s: %s", address, e)
                return

            if address in self._discovered:
                old = self._discovered[address]
                merged = old.with_updates(
                    rssi=new_model.rssi,
                    last_seen=datetime.now(),
                    manufacturer_data=new_model.manufacturer_data or old.manufacturer_data,
                    service_uuids=new_model.service_uuids or old.service_uuids,
                    tx_power=new_model.tx_power or old.tx_power,
                )
                self._discovered[address] = merged
                self.device_updated.emit(merged)
            else:
                if len(self._discovered) >= self.MAX_DEVICES:
                    oldest_addr = next(iter(self._discovered))
                    del self._discovered[oldest_addr]
                self._discovered[address] = new_model
                self.device_found.emit(new_model)
                logger.info("Found device: %s (%s)", new_model.display_name, address)

        try:
            self._scanner = BleakScanner(detection_callback=detection_callback)
            await self._scanner.start()
            await asyncio.sleep(timeout)
            await self._scanner.stop()
        except Exception as e:
            msg = f"扫描失败: {e}"
            self.error_occurred.emit(msg)
            logger.error(msg)
        finally:
            if self._scanner:
                try:
                    await self._scanner.stop()
                except Exception:
                    pass
            self._is_scanning = False
            self.scan_finished.emit()
            logger.info("Scan finished, found %d devices", len(self._discovered))

    async def stop_scan(self) -> None:
        if self._scanner and self._is_scanning:
            logger.info("Stopping scan manually")
            try:
                await self._scanner.stop()
            except Exception as e:
                logger.error("Error stopping scanner: %s", e)
