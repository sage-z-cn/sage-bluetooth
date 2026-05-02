import asyncio
import logging

from PyQt6.QtCore import QObject, pyqtSignal

from src.utils.logger import get_logger

logger = get_logger("conn_monitor")


class ConnectionMonitor(QObject):
    reconnection_started = pyqtSignal(str)
    reconnection_succeeded = pyqtSignal(str)
    reconnection_failed = pyqtSignal(str)
    connection_lost = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._task: asyncio.Task | None = None
        self._target_address: str | None = None
        self._max_retries = 3
        self._retry_delay = 2.0
        self._monitor_interval = 5.0
        self._connect_func = None
        self._is_connected_func = None
        self._stopped = False

    def configure(self, connect_func, is_connected_func):
        self._connect_func = connect_func
        self._is_connected_func = is_connected_func

    def start_monitoring(self, address: str):
        self.stop_monitoring()
        self._target_address = address
        self._stopped = False
        self._task = asyncio.ensure_future(self._monitor_loop())

    def stop_monitoring(self):
        self._stopped = True
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
        self._target_address = None

    def on_connected(self, address: str):
        self.start_monitoring(address)

    def on_disconnected(self, address: str):
        if self._stopped or address != self._target_address:
            return
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
        target = self._target_address
        self._target_address = None
        self._attempt_reconnect(target)

    async def _monitor_loop(self):
        logger.info("Monitoring started for %s", self._target_address)
        try:
            while not self._stopped:
                await asyncio.sleep(self._monitor_interval)
                if self._stopped:
                    break
                if self._is_connected_func and not self._is_connected_func():
                    logger.warning("Connection lost detected for %s", self._target_address)
                    addr = self._target_address
                    self.stop_monitoring()
                    self.connection_lost.emit(addr)
                    self._attempt_reconnect(addr)
                    return
        except asyncio.CancelledError:
            logger.info("Monitor cancelled for %s", self._target_address)

    def _attempt_reconnect(self, address: str):
        if self._stopped:
            return
        self._task = asyncio.ensure_future(self._reconnect_loop(address))

    async def _reconnect_loop(self, address: str):
        logger.info("Reconnection started for %s", address)
        self.reconnection_started.emit(address)
        for attempt in range(self._max_retries):
            if self._stopped:
                return
            logger.info("Reconnect attempt %d/%d for %s", attempt + 1, self._max_retries, address)
            await asyncio.sleep(self._retry_delay * (attempt + 1))
            if self._stopped:
                return
            if self._connect_func:
                ok = await self._connect_func(address)
                if ok:
                    logger.info("Reconnected to %s", address)
                    self.reconnection_succeeded.emit(address)
                    self.start_monitoring(address)
                    return
        logger.error("All reconnection attempts failed for %s", address)
        self.reconnection_failed.emit(address)
