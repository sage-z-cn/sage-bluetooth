import asyncio
import logging

from PyQt6.QtCore import QObject, pyqtSignal

from src.core.adapter_controller import AdapterController
from src.core.device_connector import DeviceConnector
from src.core.device_scanner import DeviceScanner
from src.core.gatt_reader import GattReader
from src.core.paired_device_loader import PairedDeviceLoader, unpair_device_by_address
from src.models.device import BLEDeviceModel, ConnectionState, ScanState
from src.models.device_info import DeviceInfoModel
from src.services.connection_monitor import ConnectionMonitor
from src.services.battery_monitor import BatteryMonitor
from src.utils.logger import get_logger

logger = get_logger("bt_manager")

_instance: "BluetoothManager | None" = None


class BluetoothManager(QObject):
    adapter_state_changed = pyqtSignal(bool)
    scan_started = pyqtSignal()
    scan_finished = pyqtSignal()
    device_discovered = pyqtSignal(BLEDeviceModel)
    device_updated = pyqtSignal(BLEDeviceModel)
    paired_devices_loaded = pyqtSignal(list)
    connection_state_changed = pyqtSignal(str, str)
    device_info_ready = pyqtSignal(DeviceInfoModel)
    battery_level_updated = pyqtSignal(str, int)
    battery_critical = pyqtSignal(str, int)
    reconnection_started = pyqtSignal(str)
    reconnection_succeeded = pyqtSignal(str)
    reconnection_failed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._tasks: set[asyncio.Task] = set()
        self._adapter = AdapterController()
        self._scanner = DeviceScanner()
        self._connector = DeviceConnector()
        self._gatt = GattReader()
        self._paired_loader = PairedDeviceLoader()

        self._conn_monitor = ConnectionMonitor()
        self._conn_monitor.configure(
            connect_func=self._connector.connect_with_retry,
            is_connected_func=lambda: self._connector.is_connected,
        )
        self._conn_monitor.reconnection_started.connect(self.reconnection_started.emit)
        self._conn_monitor.reconnection_succeeded.connect(self._on_reconnected)
        self._conn_monitor.reconnection_failed.connect(self.reconnection_failed.emit)

        self._battery_monitor = BatteryMonitor()
        self._battery_monitor.configure(self._gatt)
        self._battery_monitor.battery_updated.connect(self.battery_level_updated.emit)
        self._battery_monitor.battery_critical.connect(self.battery_critical.emit)

        self._adapter.state_changed.connect(self.adapter_state_changed.emit)
        self._adapter.error_occurred.connect(self.error_occurred.emit)

        self._scanner.device_found.connect(self.device_discovered.emit)
        self._scanner.device_updated.connect(self.device_updated.emit)
        self._scanner.scan_started.connect(self.scan_started.emit)
        self._scanner.scan_finished.connect(self.scan_finished.emit)
        self._scanner.error_occurred.connect(self.error_occurred.emit)

        self._paired_loader.paired_devices_loaded.connect(self.paired_devices_loaded.emit)

        self._connector.connected.connect(self._on_connected)
        self._connector.disconnected.connect(self._on_disconnected)
        self._connector.connection_state_changed.connect(self.connection_state_changed.emit)
        self._connector.connection_failed.connect(self._on_connection_failed)
        self._connector.pairing_result.connect(self._on_pairing_result)

        self._gatt.device_info_ready.connect(self._on_device_info_ready)
        self._gatt.battery_level_updated.connect(self.battery_level_updated.emit)
        self._gatt.error_occurred.connect(self.error_occurred.emit)

    @classmethod
    def instance(cls) -> "BluetoothManager":
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance

    def _run_async(self, coro) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        task.add_done_callback(self._on_task_done)
        return task

    def _on_task_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc and not isinstance(exc, asyncio.CancelledError):
            logger.error("Unhandled async task error: %s", exc)

    def is_adapter_on(self) -> bool:
        return self._adapter.is_adapter_on()

    def turn_on_adapter(self) -> None:
        self._run_async(self._adapter.turn_on())

    def turn_off_adapter(self) -> None:
        self._run_async(self._adapter.turn_off())

    def start_scan(self, timeout: float = 10.0) -> None:
        self._run_async(self._scanner.start_scan(timeout))

    def load_paired_devices(self) -> None:
        self._run_async(self._paired_loader.load_paired_devices())

    def stop_scan(self) -> None:
        self._run_async(self._scanner.stop_scan())

    def connect_device(self, address: str) -> None:
        self._run_async(self._connector.connect(address))

    def disconnect_device(self, address: str) -> None:
        self._conn_monitor.stop_monitoring()
        self._battery_monitor.stop()
        self._run_async(self._connector.disconnect(address))

    def pair_device(self, address: str) -> None:
        async def _connect_and_pair():
            if not self._connector.is_connected or self._connector.connected_address != address:
                ok = await self._connector.connect(address)
                if not ok:
                    return
            await self._connector.pair()

        self._run_async(_connect_and_pair())

    def read_device_info(self, address: str) -> None:
        async def _read():
            client = self.get_connected_client()
            if client and client.is_connected and client.address == address:
                await self._gatt.read_device_info(client)
        self._run_async(_read())

    def get_connected_address(self) -> str | None:
        return self._connector.connected_address

    def get_discovered_device(self, address: str):
        return self._scanner._discovered.get(address)

    def get_device_display_name(self, address: str) -> str:
        device = self._scanner._discovered.get(address)
        return device.display_name if device else address

    def get_connected_client(self):
        return self._connector._client

    def mark_device_paired(self, address: str) -> None:
        discovered = self._scanner._discovered
        if address in discovered:
            discovered[address] = discovered[address].with_updates(is_paired=True)
            self.device_updated.emit(discovered[address])

    def unpair_device(self, address: str) -> None:
        self._run_async(unpair_device_by_address(address))

    async def shutdown(self) -> None:
        self._conn_monitor.stop_monitoring()
        self._battery_monitor.stop()
        for task in list(self._tasks):
            task.cancel()
        self._tasks.clear()
        if self._connector.is_connected:
            await self._connector.disconnect()

    def _on_connected(self, address: str) -> None:
        logger.info("Device connected: %s", address)
        self._conn_monitor.on_connected(address)
        self._run_async(self._start_battery_monitor(address))
        self._run_async(self._auto_read_info(address))

    async def _start_battery_monitor(self, address: str) -> None:
        client = self.get_connected_client()
        if client and client.is_connected:
            self._battery_monitor.start(address, client)

    async def _auto_read_info(self, address: str) -> None:
        await self.read_device_info(address)

    def _on_device_info_ready(self, info: DeviceInfoModel) -> None:
        if info.name and info.name != "Unknown":
            address = info.address
            discovered = self._scanner._discovered
            if address in discovered:
                old = discovered[address]
                if old.name == "Unknown" or old.name != info.name:
                    updated = old.with_updates(name=info.name)
                    discovered[address] = updated
                    self.device_updated.emit(updated)
        self.device_info_ready.emit(info)

    def _on_disconnected(self, address: str) -> None:
        logger.info("Device disconnected: %s", address)
        self._conn_monitor.on_disconnected(address)
        self._battery_monitor.stop()

    def _on_reconnected(self, address: str):
        logger.info("Reconnected to %s", address)
        self.reconnection_succeeded.emit(address)
        self._run_async(self._start_battery_monitor(address))
        self._run_async(self._auto_read_info(address))

    def _on_connection_failed(self, address: str, reason: str) -> None:
        self.error_occurred.emit(reason)

    def _on_pairing_result(self, address: str, success: bool) -> None:
        if success:
            logger.info("Pairing succeeded: %s", address)
            self.mark_device_paired(address)
        else:
            self.error_occurred.emit("配对失败")
