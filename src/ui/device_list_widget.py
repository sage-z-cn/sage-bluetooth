from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QSizePolicy, QStackedWidget, QScrollArea,
)

from src.config import get_resource_path
from src.models.device import BLEDeviceModel, ConnectionState, DeviceType
from src.utils.device_type_resolver import resolve_device_type_comprehensive


def _icon_for_type(device_type: DeviceType) -> QPixmap:
    name_map = {
        DeviceType.HEADPHONE: "device_headphone.png",
        DeviceType.HEADSET: "device_headset.png",
        DeviceType.SPEAKER: "device_speaker.png",
        DeviceType.KEYBOARD: "device_keyboard.png",
        DeviceType.MOUSE: "device_mouse.png",
        DeviceType.GAMEPAD: "device_gamepad.png",
        DeviceType.WATCH: "device_watch.png",
        DeviceType.FITNESS_TRACKER: "device_fitness.png",
        DeviceType.PHONE: "device_phone.png",
        DeviceType.TABLET: "device_tablet.png",
        DeviceType.COMPUTER: "device_computer.png",
        DeviceType.THERMOMETER: "device_thermometer.png",
        DeviceType.HEART_RATE: "device_heart.png",
        DeviceType.BLOOD_PRESSURE: "device_blood_pressure.png",
        DeviceType.GLUCOSE: "device_glucose.png",
    }
    fname = name_map.get(device_type, "device_unknown.png")
    path = get_resource_path(f"icons/{fname}")
    px = QPixmap(path)
    if px.isNull():
        px = QPixmap(get_resource_path("icons/device_unknown.png"))
    return px


class DeviceItemWidget(QWidget):
    connect_clicked = pyqtSignal(str)
    disconnect_clicked = pyqtSignal(str)
    pair_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    selected = pyqtSignal(str)

    def __init__(self, model: BLEDeviceModel, parent=None):
        super().__init__(parent)
        self._model = model
        self._is_selected = False
        self.setObjectName("DeviceItem")
        self.setFixedHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dt = resolve_device_type_comprehensive(model.appearance, model.service_uuids, model.name)
        px = _icon_for_type(dt)
        if not px.isNull():
            icon_lbl.setPixmap(px.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(icon_lbl)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_text = model.display_name
        if model.connection_state == ConnectionState.CONNECTED:
            name_text += "  ✅已连接"
        self._name_lbl = QLabel(name_text)
        self._name_lbl.setObjectName("DeviceName")
        self._name_lbl.setWordWrap(True)
        info_layout.addWidget(self._name_lbl)

        battery_text = "--"
        meta = f"{model.address}  |  类型: {dt.name if dt != DeviceType.UNKNOWN else '未知'}"
        meta_lbl = QLabel(meta)
        meta_lbl.setObjectName("DeviceMeta")
        info_layout.addWidget(meta_lbl)

        layout.addLayout(info_layout, 1)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        is_connected = model.connection_state == ConnectionState.CONNECTED
        is_connecting = model.connection_state == ConnectionState.CONNECTING

        if not is_connected and not is_connecting:
            self._main_btn = QPushButton("连接" if model.is_paired else "配对")
            self._main_btn.setObjectName("Primary")
            self._main_btn.setFixedWidth(64)
            self._main_btn.clicked.connect(self._on_main_btn)
        elif is_connecting:
            self._main_btn = QPushButton("连接中...")
            self._main_btn.setEnabled(False)
            self._main_btn.setFixedWidth(64)
        else:
            self._main_btn = QPushButton("断开")
            self._main_btn.setObjectName("Danger")
            self._main_btn.setFixedWidth(64)
            self._main_btn.clicked.connect(lambda: self.disconnect_clicked.emit(self._model.address))

        btn_layout.addWidget(self._main_btn)

        self._delete_btn = QPushButton("删除")
        self._delete_btn.setObjectName("Muted")
        self._delete_btn.setFixedWidth(64)
        self._delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._model.address))
        btn_layout.addWidget(self._delete_btn)

        layout.addLayout(btn_layout)

    def _on_main_btn(self):
        if self._model.is_paired:
            self.connect_clicked.emit(self._model.address)
        else:
            self.pair_clicked.emit(self._model.address)

    def mousePressEvent(self, event):
        self.selected.emit(self._model.address)

    def update_selection(self, selected: bool):
        self._is_selected = selected
        self.setProperty("Selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def update_model(self, model: BLEDeviceModel):
        self._model = model
        name_text = model.display_name
        if model.connection_state == ConnectionState.CONNECTED:
            name_text += "  ✅已连接"
        self._name_lbl.setText(name_text)

    def update_connection_state(self, state: ConnectionState):
        self._model = self._model.with_updates(connection_state=state)
        name_text = self._model.display_name
        if state == ConnectionState.CONNECTED:
            name_text += "  ✅已连接"
        self._name_lbl.setText(name_text)
        self._rebuild_main_btn(state)

    def _rebuild_main_btn(self, state: ConnectionState):
        try:
            self._main_btn.clicked.disconnect()
        except Exception:
            pass
        if state == ConnectionState.CONNECTED:
            self._main_btn.setText("断开")
            self._main_btn.setObjectName("Danger")
            self._main_btn.setEnabled(True)
            self._main_btn.clicked.connect(lambda: self.disconnect_clicked.emit(self._model.address))
        elif state == ConnectionState.CONNECTING:
            self._main_btn.setText("连接中...")
            self._main_btn.setObjectName("Primary")
            self._main_btn.setEnabled(False)
        elif state == ConnectionState.DISCONNECTED:
            self._main_btn.setText("连接" if self._model.is_paired else "配对")
            self._main_btn.setObjectName("Primary")
            self._main_btn.setEnabled(True)
            self._main_btn.clicked.connect(self._on_main_btn)
        self._main_btn.style().unpolish(self._main_btn)
        self._main_btn.style().polish(self._main_btn)


class EmptyState(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EmptyState")
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addStretch()

        icon_lbl = QLabel("📡")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size:36px;background:transparent;")
        layout.addWidget(icon_lbl)

        title = QLabel("未发现蓝牙设备")
        title.setObjectName("EmptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel('点击"刷新"按钮开始扫描')
        sub.setObjectName("EmptySubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addStretch()


class ScanningState(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._count = 0
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.addStretch()

        self._icon_lbl = QLabel("🔄")
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("font-size:36px;background:transparent;")
        layout.addWidget(self._icon_lbl)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

        title = QLabel("正在扫描附近设备...")
        title.setObjectName("EmptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self._count_lbl = QLabel("已发现 0 个设备")
        self._count_lbl.setObjectName("EmptySubtitle")
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._count_lbl)

        layout.addStretch()

    def _rotate(self):
        self._angle = (self._angle + 15) % 360
        self._icon_lbl.setText("🔄")
        self._icon_lbl.setStyleSheet(f"font-size:36px;background:transparent;")

    def start(self):
        self._count = 0
        self._count_lbl.setText("已发现 0 个设备")
        self._timer.start(100)

    def stop(self):
        self._timer.stop()

    def increment_count(self):
        self._count += 1
        self._count_lbl.setText(f"已发现 {self._count} 个设备")


class DeviceListWidget(QWidget):
    device_selected = pyqtSignal(str)
    connect_clicked = pyqtSignal(str)
    disconnect_clicked = pyqtSignal(str)
    pair_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices: dict[str, DeviceItemWidget] = {}
        self._device_order: list[str] = []
        self._selected_address: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setObjectName("DeviceListStack")
        layout.addWidget(self._stack)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("DeviceListScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.verticalScrollBar().setObjectName("DeviceListVScrollBar")

        self._list_widget = QWidget()
        self._list_widget.setObjectName("DeviceListContent")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)
        self._stack.addWidget(self._scroll)

        self._empty = EmptyState()
        self._stack.addWidget(self._empty)

        self._scanning = ScanningState()
        self._stack.addWidget(self._scanning)

        self._stack.setCurrentWidget(self._empty)

    def _is_unknown(self, address: str) -> bool:
        item = self._devices.get(address)
        if item is None:
            return False
        return item._model.name == "Unknown"

    def add_device(self, model: BLEDeviceModel):
        if model.address in self._devices:
            self.update_device(model)
            return

        item = DeviceItemWidget(model)
        item.connect_clicked.connect(self.connect_clicked.emit)
        item.disconnect_clicked.connect(self.disconnect_clicked.emit)
        item.pair_clicked.connect(self.pair_clicked.emit)
        item.delete_clicked.connect(self.delete_clicked.emit)
        item.selected.connect(self._on_device_selected)

        self._devices[model.address] = item

        is_unknown = model.name == "Unknown"
        insert_index = self._list_layout.count() - 1
        if not is_unknown:
            first_unknown = -1
            for i, addr in enumerate(self._device_order):
                if self._is_unknown(addr):
                    first_unknown = i
                    break
            if first_unknown >= 0:
                insert_index = first_unknown
        self._device_order.insert(
            insert_index if insert_index < len(self._device_order) else len(self._device_order),
            model.address,
        )
        self._list_layout.insertWidget(insert_index, item)

        if self._stack.currentWidget() != self._scroll:
            self._stack.setCurrentWidget(self._scroll)

        if self._scanning._timer.isActive():
            self._scanning.increment_count()

    def update_device(self, model: BLEDeviceModel):
        item = self._devices.get(model.address)
        if item:
            item.update_model(model)

    def remove_device(self, address: str):
        item = self._devices.pop(address, None)
        if address in self._device_order:
            self._device_order.remove(address)
        if item:
            item.deleteLater()
            if not self._devices:
                self._stack.setCurrentWidget(self._empty)
            if self._selected_address == address:
                self._selected_address = None

    def update_connection_state(self, address: str, state: ConnectionState):
        item = self._devices.get(address)
        if item:
            item.update_connection_state(state)

    def clear(self):
        for item in self._devices.values():
            item.deleteLater()
        self._devices.clear()
        self._device_order.clear()
        self._selected_address = None
        self._stack.setCurrentWidget(self._empty)

    def set_scanning(self, scanning: bool):
        if scanning:
            self._scanning.start()
            self._stack.setCurrentWidget(self._scanning)
        else:
            self._scanning.stop()
            if self._devices:
                self._stack.setCurrentWidget(self._scroll)
            else:
                self._stack.setCurrentWidget(self._empty)

    def _on_device_selected(self, address: str):
        if self._selected_address == address:
            return
        old = self._devices.get(self._selected_address)
        if old:
            old.update_selection(False)
        self._selected_address = address
        new = self._devices.get(address)
        if new:
            new.update_selection(True)
        self.device_selected.emit(address)

    def deselect(self):
        old = self._devices.get(self._selected_address)
        if old:
            old.update_selection(False)
        self._selected_address = None

    @property
    def selected_address(self) -> str | None:
        return self._selected_address

    @property
    def device_count(self) -> int:
        return len(self._devices)
