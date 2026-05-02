import asyncio

from PyQt6.QtCore import QObject, pyqtSignal

from src.utils.logger import get_logger

logger = get_logger("battery_monitor")


class BatteryMonitor(QObject):
    battery_updated = pyqtSignal(str, int)
    battery_critical = pyqtSignal(str, int)

    CRITICAL_THRESHOLD = 10

    def __init__(self):
        super().__init__()
        self._task: asyncio.Task | None = None
        self._address: str | None = None
        self._gatt_reader = None
        self._client = None
        self._stopped = False
        self._last_level: int | None = None

    def configure(self, gatt_reader):
        self._gatt_reader = gatt_reader

    def start(self, address: str, client):
        self.stop()
        self._address = address
        self._client = client
        self._stopped = False
        self._last_level = None
        self._task = asyncio.ensure_future(self._monitor())

    def stop(self):
        self._stopped = True
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
        self._address = None
        self._client = None
        self._last_level = None

    def update_level(self, address: str, level: int):
        if address == self._address:
            self._last_level = level
            self.battery_updated.emit(address, level)
            if level <= self.CRITICAL_THRESHOLD:
                self.battery_critical.emit(address, level)

    async def _monitor(self):
        logger.info("Battery monitor started for %s", self._address)
        try:
            ok = await self._gatt_reader.start_battery_notification(self._client)
            if ok:
                logger.info("Battery notify active for %s", self._address)
                self._gatt_reader.battery_level_updated.connect(self.update_level)
                return

            logger.info("Battery notify unavailable, polling every 60s for %s", self._address)
            while not self._stopped and self._client and self._client.is_connected:
                level = await self._gatt_reader.read_battery_level(self._client)
                if level is not None:
                    self.update_level(self._address, level)
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info("Battery monitor cancelled for %s", self._address)
        except Exception as e:
            logger.error("Battery monitor error: %s", e)
        finally:
            self._disconnect_notify()

    def _disconnect_notify(self):
        if self._gatt_reader:
            try:
                self._gatt_reader.battery_level_updated.disconnect(self.update_level)
            except Exception:
                pass
