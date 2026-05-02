import sys
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)

from src.services.connection_monitor import ConnectionMonitor
cm = ConnectionMonitor()
print(f"ConnectionMonitor OK")

from src.services.battery_monitor import BatteryMonitor
bm = BatteryMonitor()
print(f"BatteryMonitor OK, threshold={bm.CRITICAL_THRESHOLD}")

from src.services import ConnectionMonitor, BatteryMonitor
print("services/__init__.py OK")

from src.core.bluetooth_manager import BluetoothManager
m = BluetoothManager()
print(f"BluetoothManager OK, has conn_monitor={hasattr(m, '_conn_monitor')}, has battery_monitor={hasattr(m, '_battery_monitor')}")

from src.app import App
print("App OK")

print("STAGE 6 VERIFICATION PASSED")
