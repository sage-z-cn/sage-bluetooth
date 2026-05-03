import asyncio
import subprocess

from PyQt6.QtCore import QObject, pyqtSignal

from src.utils.logger import get_logger

logger = get_logger("adapter")

_PS_GET_RADIO = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Devices.Radios.Radio, Windows.Devices.Radios, ContentType=WindowsRuntime]
$null = [Windows.Foundation.IAsyncOperation`1, Windows.Foundation, ContentType=WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1).MakeGenericMethod([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$task = $asTask.Invoke($null, @([Windows.Devices.Radios.Radio]::GetRadiosAsync()))
$radios = $task.GetAwaiter().GetResult()
$btRadio = $radios | Where-Object { $_.Kind -eq [Windows.Devices.Radios.RadioKind]::Bluetooth } | Select-Object -First 1
$btRadio
"""

_PS_RADIO_STATE = _PS_GET_RADIO + """
if ($btRadio) {
    $btRadio.State -eq [Windows.Devices.Radios.RadioState]::On
} else {
    Write-Output "false"
}
"""

_PS_RADIO_ON = _PS_GET_RADIO + """
if ($btRadio) {
    $btRadio.SetStateAsync([Windows.Devices.Radios.RadioState]::On) | Out-Null
} else {
    throw "No Bluetooth radio found"
}
"""

_PS_RADIO_OFF = _PS_GET_RADIO + """
if ($btRadio) {
    $btRadio.SetStateAsync([Windows.Devices.Radios.RadioState]::Off) | Out-Null
} else {
    throw "No Bluetooth radio found"
}
"""


class AdapterController(QObject):
    state_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def is_adapter_on(self) -> bool:
        try:
            result = subprocess.run(
                ["powershell", "-Command", _PS_RADIO_STATE],
                capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip().lower() == "true"
        except Exception as e:
            logger.error("Failed to check adapter state: %s", e)
            return False

    async def turn_on(self) -> bool:
        try:
            await self._run_ps(_PS_RADIO_ON)
            await asyncio.sleep(0.5)
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
        try:
            await self._run_ps(_PS_RADIO_OFF)
            await asyncio.sleep(0.5)
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
