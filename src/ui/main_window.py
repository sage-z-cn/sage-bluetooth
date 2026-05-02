from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QApplication

from src.config import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE_BAR_HEIGHT, CONTROL_PANEL_HEIGHT
from src.ui.title_bar import TitleBar
from src.ui.control_panel import ControlPanel
from src.ui.device_list_widget import DeviceListWidget
from src.ui.device_detail_widget import DeviceDetailWidget
from src.ui.styles import MAIN_QSS


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(MAIN_QSS)
        self._auto_hide = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._title_bar = TitleBar()
        layout.addWidget(self._title_bar)

        self._control_panel = ControlPanel()
        layout.addWidget(self._control_panel)

        self._device_list = DeviceListWidget()
        layout.addWidget(self._device_list, 1)

        self._detail_panel = DeviceDetailWidget()
        self._detail_panel.setVisible(False)
        layout.addWidget(self._detail_panel)

        self._title_bar.minimize_clicked.connect(self._hide_window)
        self._title_bar.close_clicked.connect(self._hide_window)

    def _hide_window(self):
        self.hide()

    def toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self._move_to_bottom_right()
            self.show()
            self.raise_()
            self.activateWindow()

    def _move_to_bottom_right(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        x = geo.right() - self.width() - 8
        y = geo.bottom() - self.height() - 8
        self.move(x, y)

    def show_device_detail(self, info):
        self._detail_panel.show_device(info)
        if not self._detail_panel.isVisible():
            self._detail_panel.setVisible(True)

    def hide_device_detail(self):
        self._detail_panel.setVisible(False)
        self._detail_panel.clear_info()
        self._device_list.deselect()

    def set_bluetooth_state(self, on: bool):
        self._control_panel.set_bluetooth_state(on)
        self._title_bar.set_status("on" if on else "off")
        if not on:
            self.hide_device_detail()

    def set_scanning(self, scanning: bool):
        self._control_panel.set_refreshing(scanning)
        self._title_bar.set_status("busy" if scanning else "on")

    def set_auto_hide(self, enabled: bool):
        self._auto_hide = enabled

    def eventFilter(self, obj, event):
        if self._auto_hide and event.type() == QEvent.Type.WindowDeactivate:
            QTimer.singleShot(100, self._check_and_hide)
        return super().eventFilter(obj, event)

    def _check_and_hide(self):
        if not self.isActiveWindow() and self.isVisible():
            self.hide()

    def connect_signals(self, bt_mgr):
        bt_mgr.adapter_state_changed.connect(self.set_bluetooth_state)
        bt_mgr.scan_started.connect(lambda: self.set_scanning(True))
        bt_mgr.scan_finished.connect(lambda: self.set_scanning(False))
        bt_mgr.device_discovered.connect(self._device_list.add_device)
        bt_mgr.device_updated.connect(self._device_list.update_device)
        bt_mgr.device_info_ready.connect(self.show_device_detail)
        bt_mgr.battery_level_updated.connect(self._detail_panel.update_battery)

    def get_title_bar(self) -> TitleBar:
        return self._title_bar

    def get_control_panel(self) -> ControlPanel:
        return self._control_panel

    def get_device_list(self) -> DeviceListWidget:
        return self._device_list

    def get_detail_panel(self) -> DeviceDetailWidget:
        return self._detail_panel
