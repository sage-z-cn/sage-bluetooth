from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QApplication,
)

from src.config import TITLE_BAR_HEIGHT, STATUS_INDICATOR_COLORS, get_resource_path
from src.models.device import ScanState


class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(STATUS_INDICATOR_COLORS["off"])
        self.setFixedSize(10, 10)

    def set_state(self, state: str):
        self._color = QColor(STATUS_INDICATOR_COLORS.get(state, STATUS_INDICATOR_COLORS["off"]))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, 8, 8)
        painter.end()


class TitleBar(QWidget):
    minimize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(TITLE_BAR_HEIGHT)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(6)

        icon_path = get_resource_path("icons/app.png")
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(20, 20)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background:transparent;")
        px = QPixmap(icon_path)
        if not px.isNull():
            icon_lbl.setPixmap(px.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(icon_lbl)

        title_lbl = QLabel("Sage Bluetooth")
        title_lbl.setObjectName("TitleLabel")
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        title_lbl.setFont(font)
        layout.addWidget(title_lbl)

        self._status = StatusIndicator()
        layout.addWidget(self._status)

        layout.addStretch()

        btn_min = QPushButton("─")
        btn_min.setObjectName("TitleBtn")
        btn_min.setFixedSize(28, 28)
        btn_min.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(btn_min)

        btn_close = QPushButton("✕")
        btn_close.setObjectName("TitleBtn")
        btn_close.setFixedSize(28, 28)
        btn_close.clicked.connect(self.close_clicked.emit)
        layout.addWidget(btn_close)

    def set_status(self, state: str):
        self._status.set_state(state)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
