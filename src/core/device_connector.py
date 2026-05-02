import asyncio

from bleak import BleakClient
from PyQt6.QtCore import QObject, pyqtSignal

from src.models.device import ConnectionState
from src.utils.logger import get_logger

logger = get_logger("connector")


class DeviceConnector(QObject):
    connection_state_changed = pyqtSignal(str, str)
    connected = pyqtSignal(str)
    disconnected = pyqtSignal(str)
    connection_failed = pyqtSignal(str, str)
    pairing_result = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self._client: BleakClient | None = None
        self._address: str | None = None

    @property
    def connected_address(self) -> str | None:
        return self._address

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    async def connect(self, address: str, timeout: float = 15.0) -> bool:
        if self.is_connected:
            await self.disconnect(self._address)

        self.connection_state_changed.emit(address, ConnectionState.CONNECTING.name)
        logger.info("Connecting to %s", address)

        def on_disconnect(client):
            addr = client.address
            logger.info("Disconnected callback: %s", addr)
            self._client = None
            self._address = None
            self.connection_state_changed.emit(addr, ConnectionState.DISCONNECTED.name)
            self.disconnected.emit(addr)

        try:
            self._client = BleakClient(
                address,
                disconnected_callback=on_disconnect,
                timeout=timeout,
            )
            await self._client.connect()
            self._address = address
            self.connection_state_changed.emit(address, ConnectionState.CONNECTED.name)
            self.connected.emit(address)
            logger.info("Connected to %s", address)
            return True
        except Exception as e:
            msg = f"连接失败: {e}"
            self._client = None
            self._address = None
            self.connection_state_changed.emit(address, ConnectionState.DISCONNECTED.name)
            self.connection_failed.emit(address, msg)
            logger.error(msg)
            return False

    async def disconnect(self, address: str | None = None) -> bool:
        if not self.is_connected:
            return True
        addr = address or self._address
        if addr and self._address != addr:
            return False

        self.connection_state_changed.emit(addr, ConnectionState.DISCONNECTING.name)
        logger.info("Disconnecting from %s", addr)
        try:
            await self._client.disconnect()
            return True
        except Exception as e:
            msg = f"断开连接失败: {e}"
            logger.error(msg)
            return False

    async def pair(self) -> bool:
        if not self.is_connected or not self._address:
            self.pairing_result.emit("", False)
            return False
        try:
            await self._client.pair()
            self.pairing_result.emit(self._address, True)
            return True
        except Exception as e:
            logger.error("Pairing failed: %s", e)
            self.pairing_result.emit(self._address, False)
            return False

    async def connect_with_retry(self, address: str, max_retries: int = 3) -> bool:
        for attempt in range(max_retries):
            ok = await self.connect(address)
            if ok:
                return True
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0)
        return False
