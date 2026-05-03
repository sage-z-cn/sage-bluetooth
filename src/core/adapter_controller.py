import asyncio

from PyQt6.QtCore import QObject, pyqtSignal
from winsdk.windows.devices.radios import Radio, RadioKind, RadioState

from src.utils.logger import get_logger

logger = get_logger("adapter")


class AdapterController(QObject):
    state_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def is_adapter_on(self) -> bool:
        try:
            bt_radio = self._get_bluetooth_radio_sync()
            if bt_radio is None:
                return False
            return bt_radio.state == RadioState.ON
        except Exception as e:
            logger.error("Failed to check adapter state: %s", e)
            return False

    async def turn_on(self) -> bool:
        try:
            bt_radio = await self._get_bluetooth_radio()
            if bt_radio is None:
                self.error_occurred.emit("未找到蓝牙适配器")
                return False

            if bt_radio.state == RadioState.ON:
                self.state_changed.emit(True)
                return True

            result = await bt_radio.set_state_async(RadioState.ON)
            await asyncio.sleep(0.5)

            if result == RadioState.ON or self.is_adapter_on():
                self.state_changed.emit(True)
                logger.info("Bluetooth adapter turned on")
                return True
            else:
                self.error_occurred.emit("开启蓝牙适配器失败")
                return False
        except Exception as e:
            msg = f"开启蓝牙失败: {e}"
            self.error_occurred.emit(msg)
            logger.error(msg)
            return False

    async def turn_off(self) -> bool:
        try:
            bt_radio = await self._get_bluetooth_radio()
            if bt_radio is None:
                self.error_occurred.emit("未找到蓝牙适配器")
                return False

            if bt_radio.state == RadioState.OFF:
                self.state_changed.emit(False)
                return True

            result = await bt_radio.set_state_async(RadioState.OFF)
            await asyncio.sleep(0.5)

            if result == RadioState.OFF or not self.is_adapter_on():
                self.state_changed.emit(False)
                logger.info("Bluetooth adapter turned off")
                return True
            else:
                self.error_occurred.emit("关闭蓝牙适配器失败")
                return False
        except Exception as e:
            msg = f"关闭蓝牙失败: {e}"
            self.error_occurred.emit(msg)
            logger.error(msg)
            return False

    async def _get_bluetooth_radio(self) -> Radio | None:
        radios = await Radio.get_radios_async()
        for radio in radios:
            if radio.kind == RadioKind.BLUETOOTH:
                return radio
        return None

    def _get_bluetooth_radio_sync(self) -> Radio | None:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.ensure_future(self._get_bluetooth_radio())
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, self._get_bluetooth_radio()).result()
        return asyncio.run(self._get_bluetooth_radio())
