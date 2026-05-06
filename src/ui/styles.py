MAIN_QSS = """
QWidget#TitleBar { background: #2D2D2D; color: #FFFFFF; }
QLabel#TitleLabel { color: #FFFFFF; font-weight: bold; }
QLabel#StatusIndicator { background: transparent; }

QPushButton#TitleBtn { background: transparent; color: #FFFFFF; border: none; padding: 6px; }
QPushButton#TitleBtn:hover { background: #3C3C3C; }

QWidget#ControlPanel { background: #F5F5F5; border-bottom: 1px solid #E0E0E0; }
QLabel#BtStatusLabel { color: #757575; font-size: 13px; }
QLabel#BtStatusLabel[btOn=true] { color: #4CAF50; font-size: 13px; }

QPushButton#Primary { background: #2196F3; color: white; border: 1px solid #1976D2; border-radius: 4px; padding: 6px 10px; }
QPushButton#Primary:hover { background: #1976D2; }
QPushButton#Primary:disabled { background: #BDBDBD; color: #757575; border-color: #BDBDBD; }

QPushButton#Danger { background: #F44336; color: white; border: 1px solid #D32F2F; border-radius: 4px; padding: 6px 10px; }
QPushButton#Danger:hover { background: #D32F2F; }
QPushButton#Danger:disabled { background: #BDBDBD; color: #757575; border-color: #BDBDBD; }

QPushButton#Muted { background: transparent; color: #757575; border: none; padding: 4px; }
QPushButton#Muted:hover { background: #EEEEEE; }

QWidget#DeviceItem { background: #FFFFFF; border-bottom: 1px solid #EEEEEE; }
QWidget#DeviceItem[Selected=true] { background: #E3F2FD; }
QWidget#DeviceItem:hover { background: #F5F5F5; }

QLabel#DeviceName { font-weight: bold; color: #212121; }
QLabel#DeviceMeta { color: #757575; font-size: 11px; }

QWidget#DetailPanel { background: #FFFFFF; border-top: 1px solid #E0E0E0; }
QLabel#DetailLabel { color: #757575; }
QLabel#DetailValue { color: #212121; }
QLabel#DetailHeader { font-weight: bold; font-size: 13px; color: #212121; }
QLabel#BatteryGood { color: #4CAF50; }
QLabel#BatteryMedium { color: #FF9800; }
QLabel#BatteryLow { color: #F44336; }

QWidget#EmptyState { background: #FFFFFF; }
QLabel#EmptyTitle { font-size: 16px; font-weight: bold; color: #616161; }
QLabel#EmptySubtitle { font-size: 12px; color: #9E9E9E; }

QWidget#MainWindow { background: #FAFAFA; border: 1px solid #E0E0E0; border-radius: 8px; }
QScrollArea#DeviceListScroll { background: #FAFAFA; }
QWidget#DeviceListContent { background: #FAFAFA; }
QWidget#DeviceListStack { background: #FAFAFA; }
"""

DARK_QSS = """
QWidget#TitleBar { background: #1A1A1A; color: #E0E0E0; }
QLabel#TitleLabel { color: #E0E0E0; font-weight: bold; }
QLabel#StatusIndicator { background: transparent; }

QPushButton#TitleBtn { background: transparent; color: #E0E0E0; border: none; padding: 6px; }
QPushButton#TitleBtn:hover { background: #383838; }

QWidget#ControlPanel { background: #252525; border-bottom: 1px solid #3C3C3C; }
QLabel#BtStatusLabel { color: #9E9E9E; font-size: 13px; }
QLabel#BtStatusLabel[btOn=true] { color: #4CAF50; font-size: 13px; }

QPushButton#Primary { background: #1976D2; color: white; border: 1px solid #1565C0; border-radius: 4px; padding: 6px 10px; }
QPushButton#Primary:hover { background: #1565C0; }
QPushButton#Primary:disabled { background: #424242; color: #757575; border-color: #424242; }

QPushButton#Danger { background: #D32F2F; color: white; border: 1px solid #C62828; border-radius: 4px; padding: 6px 10px; }
QPushButton#Danger:hover { background: #C62828; }
QPushButton#Danger:disabled { background: #424242; color: #757575; border-color: #424242; }

QPushButton#Muted { background: transparent; color: #9E9E9E; border: none; padding: 4px; }
QPushButton#Muted:hover { background: #383838; }

QWidget#DeviceItem { background: #2D2D2D; border-bottom: 1px solid #3C3C3C; }
QWidget#DeviceItem[Selected=true] { background: #1A3A5C; }
QWidget#DeviceItem:hover { background: #383838; }

QLabel#DeviceName { font-weight: bold; color: #E0E0E0; }
QLabel#DeviceMeta { color: #9E9E9E; font-size: 11px; }

QWidget#DetailPanel { background: #2D2D2D; border-top: 1px solid #3C3C3C; }
QLabel#DetailLabel { color: #9E9E9E; }
QLabel#DetailValue { color: #E0E0E0; }
QLabel#DetailHeader { font-weight: bold; font-size: 13px; color: #E0E0E0; }
QLabel#BatteryGood { color: #4CAF50; }
QLabel#BatteryMedium { color: #FF9800; }
QLabel#BatteryLow { color: #F44336; }

QWidget#EmptyState { background: #1E1E1E; }
QLabel#EmptyTitle { font-size: 16px; font-weight: bold; color: #BDBDBD; }
QLabel#EmptySubtitle { font-size: 12px; color: #757575; }

QWidget#MainWindow { background: #1E1E1E; border: 1px solid #3C3C3C; border-radius: 8px; }
QScrollArea#DeviceListScroll { background: #1E1E1E; }
QWidget#DeviceListContent { background: #1E1E1E; }
QWidget#DeviceListStack { background: #1E1E1E; }
"""


def get_qss(theme: str) -> str:
    return DARK_QSS if theme == "dark" else MAIN_QSS
