import pytest
import asyncio
from unittest.mock import MagicMock, patch

from src.models.device import BLEDeviceModel, ConnectionState
from src.models.device_info import DeviceInfoModel
from src.models.app_config import AppConfig
from src.models.app_state import AppState


class TestAppConfig:
    def _patch_config_path(self, path):
        return patch.object(AppConfig, "CONFIG_PATH", path)

    def test_save_and_load(self, tmp_path):
        config_path = tmp_path / "config.json"
        with self._patch_config_path(config_path):
            original = AppConfig(auto_hide_on_blur=False, scan_timeout=15.0)
            original.save()

            loaded = AppConfig.load()
            assert loaded.auto_hide_on_blur is False
            assert loaded.scan_timeout == 15.0

    def test_load_defaults_on_missing(self, tmp_path):
        config_path = tmp_path / "nonexistent.json"
        with self._patch_config_path(config_path):
            config = AppConfig.load()
            assert config.auto_hide_on_blur is True
            assert config.scan_timeout == 10.0

    def test_load_defaults_on_corrupt(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text("not json!!!", encoding="utf-8")
        with self._patch_config_path(config_path):
            config = AppConfig.load()
            assert config.auto_hide_on_blur is True

    def test_load_ignores_extra_keys(self, tmp_path):
        config_path = tmp_path / "config.json"
        import json
        data = {"auto_hide_on_blur": False, "unknown_key": "value"}
        config_path.write_text(json.dumps(data), encoding="utf-8")
        with self._patch_config_path(config_path):
            config = AppConfig.load()
            assert config.auto_hide_on_blur is False
            assert not hasattr(config, "unknown_key")


class TestAppState:
    def test_initial_state(self):
        state = AppState()
        assert state.is_adapter_on is False
        assert state.is_scanning is False
        assert state.is_connected is False
        assert state.device_count == 0

    def test_update_device(self):
        state = AppState()
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        state.update_device(device)
        assert state.device_count == 1
        assert state.get_device("AA:BB:CC:DD:EE:FF") is not None

    def test_update_device_overwrites(self):
        state = AppState()
        device1 = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Old")
        device2 = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="New")
        state.update_device(device1)
        state.update_device(device2)
        assert state.device_count == 1
        assert state.get_device("AA:BB:CC:DD:EE:FF").name == "New"

    def test_remove_device(self):
        state = AppState()
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        state.update_device(device)
        state.remove_device("AA:BB:CC:DD:EE:FF")
        assert state.device_count == 0

    def test_remove_device_clears_selected(self):
        state = AppState()
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        state.update_device(device)
        state.selected_device = "AA:BB:CC:DD:EE:FF"
        state.remove_device("AA:BB:CC:DD:EE:FF")
        assert state.selected_device is None

    def test_remove_device_clears_connected(self):
        state = AppState()
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        state.update_device(device)
        state.connected_device = "AA:BB:CC:DD:EE:FF"
        state.remove_device("AA:BB:CC:DD:EE:FF")
        assert state.connected_device is None

    def test_remove_nonexistent(self):
        state = AppState()
        state.remove_device("AA:BB:CC:DD:EE:FF")
        assert state.device_count == 0

    def test_clear_devices(self):
        state = AppState()
        for i in range(3):
            state.update_device(BLEDeviceModel(address=f"AA:BB:CC:DD:EE:{i:02X}"))
        state.selected_device = "AA:BB:CC:DD:EE:00"
        state.clear_devices()
        assert state.device_count == 0
        assert state.selected_device is None

    def test_get_device_not_found(self):
        state = AppState()
        assert state.get_device("AA:BB:CC:DD:EE:FF") is None

    def test_is_connected(self):
        state = AppState()
        assert state.is_connected is False
        state.connected_device = "AA:BB:CC:DD:EE:FF"
        assert state.is_connected is True

    def test_get_connected_device_model(self):
        state = AppState()
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Test")
        state.update_device(device)
        state.connected_device = "AA:BB:CC:DD:EE:FF"
        model = state.get_connected_device_model()
        assert model is not None
        assert model.name == "Test"

    def test_get_connected_device_model_none(self):
        state = AppState()
        assert state.get_connected_device_model() is None


class TestDeviceInfoModel:
    def test_device_type(self):
        info = DeviceInfoModel(address="AA:BB:CC:DD:EE:FF", appearance=0x0080)
        assert info.device_type.name == "HEADPHONE"

    def test_has_battery_info(self):
        info = DeviceInfoModel(address="AA:BB:CC:DD:EE:FF", battery_level=80)
        assert info.has_battery_info is True

    def test_no_battery_info(self):
        info = DeviceInfoModel(address="AA:BB:CC:DD:EE:FF")
        assert info.has_battery_info is False

    def test_battery_icon_good(self):
        info = DeviceInfoModel(address="AA:BB:CC:DD:EE:FF", battery_level=80)
        assert info.battery_icon == "battery_good"

    def test_battery_icon_medium(self):
        info = DeviceInfoModel(address="AA:BB:CC:DD:EE:FF", battery_level=40)
        assert info.battery_icon == "battery_medium"

    def test_battery_icon_low(self):
        info = DeviceInfoModel(address="AA:BB:CC:DD:EE:FF", battery_level=10)
        assert info.battery_icon == "battery_low"

    def test_battery_icon_unknown(self):
        info = DeviceInfoModel(address="AA:BB:CC:DD:EE:FF")
        assert info.battery_icon == "battery_unknown"


class TestGattModels:
    def test_characteristic_can_read(self):
        from src.models.device_info import GattCharacteristicModel
        char = GattCharacteristicModel(uuid="test", properties=["read"])
        assert char.can_read is True
        assert char.can_write is False

    def test_characteristic_can_write(self):
        from src.models.device_info import GattCharacteristicModel
        char = GattCharacteristicModel(uuid="test", properties=["write"])
        assert char.can_write is True

    def test_characteristic_can_write_without_response(self):
        from src.models.device_info import GattCharacteristicModel
        char = GattCharacteristicModel(uuid="test", properties=["write-without-response"])
        assert char.can_write is True

    def test_characteristic_can_notify(self):
        from src.models.device_info import GattCharacteristicModel
        char = GattCharacteristicModel(uuid="test", properties=["notify"])
        assert char.can_notify is True
