from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._offset = 3
        self._circle_r = 10
        self._track_w = 44
        self._track_h = 22
        self.setFixedSize(self._track_w, self._track_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def checked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.update()
        self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color = QColor("#4CAF50") if self._checked else QColor("#BDBDBD")
        p.setBrush(QBrush(track_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self._track_w, self._track_h, 11, 11)

        if self._checked:
            cx = self._track_w - self._circle_r - self._offset
        else:
            cx = self._circle_r + self._offset
        cy = self._track_h // 2
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawEllipse(cx - self._circle_r, cy - self._circle_r, self._circle_r * 2, self._circle_r * 2)
        p.end()


class SpinButton(QPushButton):
    def __init__(self, text="🔄", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

    def start_spinning(self):
        self.setEnabled(False)
        self._timer.start(50)

    def stop_spinning(self):
        self._timer.stop()
        self._angle = 0
        self.setEnabled(True)
        self.update()

    def _rotate(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QTransform
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._timer.isActive():
            p.translate(self.rect().center())
            p.rotate(self._angle)
            p.translate(-self.rect().center())
        QPushButton.paintEvent(self, event)
        p.end()


class ControlPanel(QWidget):
    bluetooth_toggled = pyqtSignal(bool)
    refresh_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ControlPanel")
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        self._switch = ToggleSwitch()
        self._switch.toggled.connect(self.bluetooth_toggled.emit)

        self._label = QLabel("蓝牙 OFF")
        self._label.setStyleSheet("color:#757575;font-size:13px;")

        layout.addWidget(self._switch)
        layout.addWidget(self._label)
        layout.addStretch()

        self._refresh_btn = SpinButton("🔄")
        self._refresh_btn.setObjectName("Primary")
        self._refresh_btn.clicked.connect(self.refresh_clicked.emit)
        layout.addWidget(self._refresh_btn)

    def set_bluetooth_state(self, on: bool):
        self._switch.setChecked(on)
        self._label.setText("蓝牙 ON" if on else "蓝牙 OFF")
        self._label.setStyleSheet(f"color:{'#4CAF50' if on else '#757575'};font-size:13px;")

    def set_refreshing(self, refreshing: bool):
        if refreshing:
            self._refresh_btn.start_spinning()
        else:
            self._refresh_btn.stop_spinning()

    def set_switch_enabled(self, enabled: bool):
        self._switch.setEnabled(enabled)
