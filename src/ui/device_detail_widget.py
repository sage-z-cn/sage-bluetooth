from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
)

from src.models.device_info import DeviceInfoModel
from src.utils.device_type_resolver import resolve_device_type


class SignalBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rssi = -100
        self.setFixedHeight(12)
        self.setFixedWidth(100)

    def set_rssi(self, rssi: int):
        self._rssi = rssi
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QBrush
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._rssi >= -50:
            bars = 10
        elif self._rssi >= -60:
            bars = 8
        elif self._rssi >= -70:
            bars = 6
        elif self._rssi >= -80:
            bars = 4
        elif self._rssi >= -90:
            bars = 2
        else:
            bars = 1

        bar_w = 6
        gap = 2
        total = bars * bar_w + (bars - 1) * gap
        max_h = self.height()

        for i in range(10):
            bar_h = int(max_h * (i + 1) / 10)
            x = i * (bar_w + gap)
            y = max_h - bar_h
            color = QColor("#4CAF50") if i < bars else QColor("#E0E0E0")
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x, y, bar_w, bar_h, 1, 1)
        p.end()


class DeviceDetailWidget(QWidget):
    close_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailPanel")
        self._info: DeviceInfoModel | None = None

        self._base_height = 0
        self._anim = None
        self._expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header_lbl = QLabel("设备信息")
        header_lbl.setObjectName("DetailHeader")
        header.addWidget(header_lbl)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("Muted")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.close_clicked.emit)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self._grid = QGridLayout()
        self._grid.setSpacing(6)
        self._grid.setColumnStretch(1, 1)
        self._labels: dict[str, QLabel] = {}
        self._rows = []
        self._build_rows()
        layout.addLayout(self._grid)
        layout.addStretch()

    def _build_rows(self):
        fields = [
            ("名称", "name"),
            ("地址", "address"),
            ("类型", "type"),
            ("厂商", "manufacturer"),
            ("型号", "model_number"),
            ("序列号", "serial_number"),
            ("固件版本", "firmware_revision"),
            ("电量", "battery"),
            ("信号强度", "signal"),
        ]
        for i, (label_text, key) in enumerate(fields):
            lbl = QLabel(f"{label_text}:")
            lbl.setObjectName("DetailLabel")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val = QLabel("--")
            val.setObjectName("DetailValue")
            val.setWordWrap(True)
            self._grid.addWidget(lbl, i, 0)
            self._grid.addWidget(val, i, 1)
            self._labels[key] = val
            self._rows.append((lbl, val))

    def show_device(self, info: DeviceInfoModel):
        self._info = info
        self._labels["name"].setText(info.name or "Unknown")
        self._labels["address"].setText(info.address)
        self._labels["type"].setText(resolve_device_type(info.appearance).name)
        self._labels["manufacturer"].setText(info.manufacturer or "--")
        self._labels["model_number"].setText(info.model_number or "--")
        self._labels["serial_number"].setText(info.serial_number or "--")
        self._labels["firmware_revision"].setText(info.firmware_revision or "--")

        if info.battery_level is not None:
            bat = info.battery_level
            txt = f"{bat}%"
            if bat >= 60:
                style = "color:#4CAF50;"
            elif bat >= 20:
                style = "color:#FF9800;"
            else:
                style = "color:#F44336;"
            self._labels["battery"].setText(txt)
            self._labels["battery"].setStyleSheet(style)
        else:
            self._labels["battery"].setText("--")
            self._labels["battery"].setStyleSheet("")

        self._labels["signal"].setText("--")

    def update_signal(self, rssi: int):
        self._labels["signal"].setText(f"{rssi} dBm")

    def update_battery(self, level: int):
        txt = f"{level}%"
        if level >= 60:
            style = "color:#4CAF50;"
        elif level >= 20:
            style = "color:#FF9800;"
        else:
            style = "color:#F44336;"
        self._labels["battery"].setText(txt)
        self._labels["battery"].setStyleSheet(style)

    def clear_info(self):
        self._info = None
        for lbl in self._labels.values():
            lbl.setText("--")
            lbl.setStyleSheet("")

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    def refresh_header_style(self):
        for lbl, val in self._rows:
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)
            val.style().unpolish(val)
            val.style().polish(val)
