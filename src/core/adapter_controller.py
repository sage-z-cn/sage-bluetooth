import asyncio
import ctypes
import logging
import subprocess

from PyQt6.QtCore import QObject, pyqtSignal

from src.config import check_admin_privilege
from src.utils.logger import get_logger

logger = get_logger("adapter")


class AdapterController(QObject):
    state_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def is_adapter_on(self) -> bool:
        try:
            result = subprocess.run(
                [
                    "powershell", "-Command",
                    "(Get-PnpDevice -Class Bluetooth -Status OK -ErrorAction SilentlyContinue).Count -gt 0",
                ],
                capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip().lower() == "true"
        except Exception as e:
            logger.error("Failed to check adapter state: %s", e)
            return False

    async def turn_on(self) -> bool:
        if not check_admin_privilege():
            msg = "开启蓝牙需要管理员权限，请右键以管理员身份运行本程序"
            self.error_occurred.emit(msg)
            return False

        try:
            instance_id = await self._get_bluetooth_instance_id()
            if not instance_id:
                self.error_occurred.emit("未找到蓝牙适配器")
                return False

            await self._run_ps(
                f"Enable-PnpDevice -InstanceId '{instance_id}' -Confirm:$false"
            )
            await asyncio.sleep(1.0)
            if self.is_adapter_on():
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
        if not check_admin_privilege():
            msg = "关闭蓝牙需要管理员权限，请右键以管理员身份运行本程序"
            self.error_occurred.emit(msg)
            return False

        try:
            instance_id = await self._get_bluetooth_instance_id()
            if not instance_id:
                self.error_occurred.emit("未找到蓝牙适配器")
                return False

            await self._run_ps(
                f"Disable-PnpDevice -InstanceId '{instance_id}' -Confirm:$false"
            )
            await asyncio.sleep(1.0)
            if not self.is_adapter_on():
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

    async def _get_bluetooth_instance_id(self) -> str | None:
        cmd = (
            "(Get-PnpDevice -Class Bluetooth -Status OK -ErrorAction SilentlyContinue "
            "| Where-Object { $_.FriendlyName -like '*Bluetooth*' } "
            "| Select-Object -First 1).InstanceId"
        )
        success, output = await self._run_ps(cmd)
        return output.strip() if success and output.strip() else None

    async def _run_ps(self, command: str) -> tuple[bool, str]:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True, text=True, timeout=15,
            ),
        )
        success = result.returncode == 0
        output = result.stdout if success else result.stderr
        return success, output
