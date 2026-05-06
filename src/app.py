import asyncio

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox

from src.core.bluetooth_manager import BluetoothManager
from src.models.app_config import AppConfig
from src.models.device import ConnectionState
from src.ui.main_window import MainWindow
from src.ui.tray_icon import TrayIcon


class App:
    def __init__(self):
        self._config = AppConfig.load()
        self._bt_mgr = BluetoothManager.instance()
        self._window = MainWindow()
        self._tray = TrayIcon(dark_mode=self._config.theme == "dark")

        self._apply_theme(self._config.theme)
        self._connect_signals()
        self._init_state()

    def _connect_signals(self):
        self._window.connect_signals(self._bt_mgr)
        self._window.get_device_list().device_selected.connect(self._on_device_selected)
        self._window.get_device_list().connect_clicked.connect(self._bt_mgr.connect_device)
        self._window.get_device_list().disconnect_clicked.connect(self._bt_mgr.disconnect_device)
        self._window.get_device_list().pair_clicked.connect(self._bt_mgr.pair_device)
        self._window.get_device_list().delete_clicked.connect(self._on_delete_device)
        self._window.get_detail_panel().close_clicked.connect(self._window.hide_device_detail)

        self._window.get_control_panel().bluetooth_toggled.connect(self._on_bluetooth_toggled)
        self._window.get_control_panel().refresh_clicked.connect(self._on_refresh)

        self._tray.toggle_window.connect(self._window.toggle_visible)
        self._tray.toggle_bluetooth.connect(self._on_bluetooth_toggled)
        self._tray.refresh_clicked.connect(self._on_refresh)
        self._tray.theme_toggled.connect(self._on_theme_toggled)
        self._tray.exit_clicked.connect(self._quit)

        self._bt_mgr.adapter_state_changed.connect(self._on_adapter_state_changed)
        self._bt_mgr.error_occurred.connect(self._on_error)
        self._bt_mgr.connection_state_changed.connect(self._on_connection_state_changed)
        self._bt_mgr.scan_started.connect(self._on_scan_started)
        self._bt_mgr.scan_finished.connect(self._on_scan_finished)
        self._bt_mgr.paired_devices_loaded.connect(self._on_paired_devices_loaded)
        self._bt_mgr.battery_critical.connect(self._on_battery_critical)
        self._bt_mgr.reconnection_started.connect(self._on_reconnection_started)
        self._bt_mgr.reconnection_succeeded.connect(self._on_reconnection_succeeded)
        self._bt_mgr.reconnection_failed.connect(self._on_reconnection_failed)

    def _init_state(self):
        is_on = self._bt_mgr.is_adapter_on()
        self._window.set_bluetooth_state(is_on)
        self._tray.set_bluetooth_state(is_on)
        self._tray.show()
        if is_on:
            QTimer.singleShot(0, self._bt_mgr.load_paired_devices)

    def _on_bluetooth_toggled(self, on: bool):
        if on:
            self._bt_mgr.turn_on_adapter()
            self._bt_mgr.load_paired_devices()
        else:
            self._window.hide_device_detail()
            self._bt_mgr.turn_off_adapter()

    def _on_refresh(self):
        if not self._bt_mgr.is_adapter_on():
            self._on_error("蓝牙适配器未开启，请先打开蓝牙")
            return
        self._window.hide_device_detail()
        self._bt_mgr.stop_scan()
        self._window.get_device_list().clear()
        self._bt_mgr.load_paired_devices()
        self._bt_mgr.start_scan()

    def _on_scan_started(self):
        self._window.set_scanning(True)

    def _on_scan_finished(self):
        self._window.set_scanning(False)

    def _on_adapter_state_changed(self, on: bool):
        self._tray.set_bluetooth_state(on)
        if on:
            self._bt_mgr.load_paired_devices()

    def _on_paired_devices_loaded(self, devices: list):
        for model in devices:
            self._window.get_device_list().add_device(model)

    def _on_device_selected(self, address: str):
        self._bt_mgr.read_device_info(address)

    def _on_delete_device(self, address: str):
        device = self._bt_mgr._scanner._discovered.get(address)
        name = device.display_name if device else address
        reply = QMessageBox.question(
            self._window,
            "删除设备",
            f"确定要删除设备 \"{name}\" 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._window.get_device_list().remove_device(address)

    def _on_connection_state_changed(self, address: str, state_name: str):
        state = ConnectionState[state_name]
        self._window.get_device_list().update_connection_state(address, state)
        if state == ConnectionState.CONNECTED:
            device = self._bt_mgr._scanner._discovered.get(address)
            self._tray.set_connected(device.display_name if device else address)
            self._bt_mgr.read_device_info(address)
        elif state == ConnectionState.DISCONNECTED:
            self._tray.set_connected(None)

    def _on_error(self, msg: str):
        self._tray.showMessage("Sage Bluetooth", msg, QSystemTrayIcon.MessageIcon.Warning, 3000)

    def _on_battery_critical(self, address: str, level: int):
        device = self._bt_mgr._scanner._discovered.get(address)
        name = device.display_name if device else address
        self._tray.showMessage(
            "电量不足",
            f"{name} 电量仅剩 {level}%，请尽快充电",
            QSystemTrayIcon.MessageIcon.Warning,
            5000,
        )

    def _on_reconnection_started(self, address: str):
        self._tray.showMessage(
            "Sage Bluetooth",
            "连接已断开，正在尝试重新连接...",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def _on_reconnection_succeeded(self, address: str):
        self._tray.showMessage(
            "Sage Bluetooth",
            "重新连接成功",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _on_reconnection_failed(self, address: str):
        self._tray.showMessage(
            "Sage Bluetooth",
            "重新连接失败，设备已断开",
            QSystemTrayIcon.MessageIcon.Warning,
            3000,
        )
        self._window.get_device_list().update_connection_state(address, ConnectionState.DISCONNECTED)
        self._tray.set_connected(None)

    def _quit(self):
        async def _shutdown():
            await self._bt_mgr.shutdown()
        asyncio.ensure_future(_shutdown())
        self._tray.hide()
        QApplication.instance().quit()

    def _apply_theme(self, theme: str):
        self._window.apply_theme(theme)

    def _on_theme_toggled(self, dark: bool):
        theme = "dark" if dark else "light"
        self._config.theme = theme
        self._config.save()
        self._apply_theme(theme)
