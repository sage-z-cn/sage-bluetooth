import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.config import WINDOW_WIDTH, WINDOW_HEIGHT
from src.ui.main_window import MainWindow
from src.ui.title_bar import TitleBar
from src.ui.control_panel import ControlPanel, ToggleSwitch
from src.ui.device_list_widget import DeviceListWidget, EmptyState
from src.ui.device_detail_widget import DeviceDetailWidget
from src.models.device import BLEDeviceModel, ConnectionState, DeviceType
from src.models.device_info import DeviceInfoModel


@pytest.fixture
def main_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    return window


@pytest.fixture
def title_bar(qtbot):
    bar = TitleBar()
    qtbot.addWidget(bar)
    return bar


@pytest.fixture
def control_panel(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    return panel


@pytest.fixture
def device_list(qtbot):
    widget = DeviceListWidget()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def detail_widget(qtbot):
    widget = DeviceDetailWidget()
    qtbot.addWidget(widget)
    return widget


class TestMainWindow:
    def test_window_size(self, main_window):
        assert main_window.width() == WINDOW_WIDTH
        assert main_window.height() == WINDOW_HEIGHT

    def test_window_flags(self, main_window):
        flags = main_window.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_fixed_size(self, main_window):
        assert main_window.minimumSize() == main_window.maximumSize()

    def test_has_title_bar(self, main_window):
        assert main_window.get_title_bar() is not None

    def test_has_control_panel(self, main_window):
        assert main_window.get_control_panel() is not None

    def test_has_device_list(self, main_window):
        assert main_window.get_device_list() is not None

    def test_has_detail_panel(self, main_window):
        assert main_window.get_detail_panel() is not None

    def test_detail_panel_hidden_by_default(self, main_window):
        assert not main_window.get_detail_panel().isVisible()

    def test_set_bluetooth_state_on(self, main_window):
        main_window.set_bluetooth_state(True)
        assert main_window.get_control_panel()._switch._checked

    def test_set_bluetooth_state_off_hides_detail(self, main_window):
        main_window.set_bluetooth_state(False)
        assert not main_window.get_detail_panel().isVisible()


class TestTitleBar:
    def test_fixed_height(self, title_bar):
        from src.config import TITLE_BAR_HEIGHT
        assert title_bar.height() == TITLE_BAR_HEIGHT

    def test_status_indicator(self, title_bar):
        title_bar.set_status("on")
        assert title_bar._status._color.name() == "#4caf50"

    def test_status_off(self, title_bar):
        title_bar.set_status("off")
        assert title_bar._status._color.name() == "#f44336"

    def test_status_busy(self, title_bar):
        title_bar.set_status("busy")
        assert title_bar._status._color.name() == "#ffc107"


class TestControlPanel:
    def test_fixed_height(self, control_panel):
        assert control_panel.height() == 52

    def test_toggle_initial_state(self, control_panel):
        assert not control_panel._switch._checked

    def test_set_bluetooth_state_on(self, control_panel):
        control_panel.set_bluetooth_state(True)
        assert control_panel._switch._checked
        assert "ON" in control_panel._label.text()

    def test_set_bluetooth_state_off(self, control_panel):
        control_panel.set_bluetooth_state(True)
        control_panel.set_bluetooth_state(False)
        assert not control_panel._switch._checked
        assert "OFF" in control_panel._label.text()


class TestToggleSwitch:
    def test_initial_unchecked(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        assert not switch.checked

    def test_initial_checked(self, qtbot):
        switch = ToggleSwitch(checked=True)
        qtbot.addWidget(switch)
        assert switch.checked

    def test_toggle_click(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        signals = []
        switch.toggled.connect(signals.append)
        qtbot.mouseClick(switch, Qt.MouseButton.LeftButton)
        assert switch.checked
        assert signals == [True]


class TestDeviceList:
    def test_initial_empty_state(self, device_list):
        assert device_list.device_count == 0

    def test_add_device(self, device_list):
        model = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test Device")
        device_list.add_device(model)
        assert device_list.device_count == 1

    def test_add_duplicate_device(self, device_list):
        model = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        device_list.add_device(model)
        model2 = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Updated")
        device_list.add_device(model2)
        assert device_list.device_count == 1

    def test_remove_device(self, device_list):
        model = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        device_list.add_device(model)
        device_list.remove_device("AA:BB:CC:DD:EE:FF")
        assert device_list.device_count == 0

    def test_clear_devices(self, device_list):
        for i in range(3):
            model = BLEDeviceModel(address=f"AA:BB:CC:DD:EE:{i:02X}", name=f"Device {i}")
            device_list.add_device(model)
        device_list.clear()
        assert device_list.device_count == 0

    def test_update_connection_state(self, device_list):
        model = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        device_list.add_device(model)
        device_list.update_connection_state("AA:BB:CC:DD:EE:FF", ConnectionState.CONNECTED)
        item = device_list._devices["AA:BB:CC:DD:EE:FF"]
        assert item._model.connection_state == ConnectionState.CONNECTED

    def test_deselect(self, device_list):
        model = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        device_list.add_device(model)
        device_list._on_device_selected("AA:BB:CC:DD:EE:FF")
        device_list.deselect()
        assert device_list.selected_address is None


class TestDeviceDetailWidget:
    def test_initial_state(self, detail_widget):
        for label in detail_widget._labels.values():
            assert label.text() == "--"

    def test_show_device_info(self, detail_widget):
        info = DeviceInfoModel(
            address="AA:BB:CC:DD:EE:FF",
            name="Test Device",
            appearance=0x0080,
            manufacturer="Apple",
            battery_level=85,
        )
        detail_widget.show_device(info)
        assert detail_widget._labels["name"].text() == "Test Device"
        assert detail_widget._labels["address"].text() == "AA:BB:CC:DD:EE:FF"
        assert detail_widget._labels["manufacturer"].text() == "Apple"
        assert detail_widget._labels["battery"].text() == "85%"

    def test_update_battery_good(self, detail_widget):
        detail_widget.update_battery(80)
        assert detail_widget._labels["battery"].text() == "80%"
        assert "#4CAF50" in detail_widget._labels["battery"].styleSheet()

    def test_update_battery_medium(self, detail_widget):
        detail_widget.update_battery(40)
        assert detail_widget._labels["battery"].text() == "40%"
        assert "#FF9800" in detail_widget._labels["battery"].styleSheet()

    def test_update_battery_low(self, detail_widget):
        detail_widget.update_battery(10)
        assert detail_widget._labels["battery"].text() == "10%"
        assert "#F44336" in detail_widget._labels["battery"].styleSheet()

    def test_clear_info(self, detail_widget):
        info = DeviceInfoModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        detail_widget.show_device(info)
        detail_widget.clear_info()
        for label in detail_widget._labels.values():
            assert label.text() == "--"
