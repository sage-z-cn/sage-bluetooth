from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu

from src.config import get_resource_path


class TrayIcon(QSystemTrayIcon):
    toggle_window = pyqtSignal()
    toggle_bluetooth = pyqtSignal(bool)
    refresh_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bt_on = False
        self._bt_action = None

        icon = QIcon(get_resource_path("icons/app.ico"))
        if icon.isNull():
            from PyQt6.QtGui import QPixmap
            icon = QIcon(QPixmap(16, 16))
        self.setIcon(icon)
        self.setToolTip("Sage Bluetooth - 蓝牙已关闭")

        self.activated.connect(self._on_activated)

        self._menu = QMenu()
        title = QAction("Sage Bluetooth", self)
        title.setEnabled(False)
        self._menu.addAction(title)
        self._menu.addSeparator()

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.toggle_window.emit)
        self._menu.addAction(show_action)

        self._bt_action = QAction("开启蓝牙", self)
        self._bt_action.triggered.connect(lambda: self.toggle_bluetooth.emit(not self._bt_on))
        self._menu.addAction(self._bt_action)

        self._menu.addSeparator()

        refresh_action = QAction("刷新设备列表", self)
        refresh_action.triggered.connect(self.refresh_clicked.emit)
        self._menu.addAction(refresh_action)

        self._menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.exit_clicked.emit)
        self._menu.addAction(exit_action)

        self.setContextMenu(self._menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window.emit()

    def set_bluetooth_state(self, on: bool):
        self._bt_on = on
        if self._bt_action:
            self._bt_action.setText("关闭蓝牙" if on else "开启蓝牙")
        self.setToolTip("Sage Bluetooth - 蓝牙已开启" if on else "Sage Bluetooth - 蓝牙已关闭")

    def set_connected(self, device_name: str | None):
        if device_name:
            self.setToolTip(f"Sage Bluetooth - 已连接: {device_name}")
        else:
            self.set_bluetooth_state(self._bt_on)
