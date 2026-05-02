import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.models.device import (
    BLEDeviceModel,
    ConnectionState,
    ScanState,
    DeviceType,
)


class TestEnums:
    def test_connection_states(self):
        assert ConnectionState.DISCONNECTED.name == "DISCONNECTED"
        assert ConnectionState.CONNECTING.name == "CONNECTING"
        assert ConnectionState.CONNECTED.name == "CONNECTED"
        assert ConnectionState.DISCONNECTING.name == "DISCONNECTING"
        assert ConnectionState.PAIRING.name == "PAIRING"

    def test_scan_states(self):
        assert ScanState.IDLE.name == "IDLE"
        assert ScanState.SCANNING.name == "SCANNING"

    def test_device_types_count(self):
        assert len(DeviceType) >= 16


class TestBLEDeviceModel:
    def test_create_default(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF")
        assert device.address == "AA:BB:CC:DD:EE:FF"
        assert device.name == "Unknown"
        assert device.rssi == -100
        assert device.appearance == 0
        assert device.connection_state == ConnectionState.DISCONNECTED

    def test_frozen(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF")
        with pytest.raises(AttributeError):
            device.name = "Test"

    def test_display_name_with_name(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="AirPods")
        assert device.display_name == "AirPods"

    def test_display_name_unknown(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF")
        assert "Unknown" in device.display_name
        assert "EE:FF" in device.display_name

    def test_signal_quality_strong(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", rssi=-40)
        assert device.signal_quality == 100

    def test_signal_quality_weak(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", rssi=-90)
        assert device.signal_quality == 20

    def test_signal_quality_very_weak(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", rssi=-110)
        assert device.signal_quality == 0

    def test_signal_quality_excellent(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", rssi=-20)
        assert device.signal_quality == 100

    def test_with_updates(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF", name="Old")
        new_device = device.with_updates(name="New", rssi=-50)
        assert new_device.name == "New"
        assert new_device.rssi == -50
        assert new_device.address == "AA:BB:CC:DD:EE:FF"
        assert device.name == "Old"

    def test_with_updates_preserves_connection_state(self):
        device = BLEDeviceModel(
            address="AA:BB:CC:DD:EE:FF",
            connection_state=ConnectionState.CONNECTED,
        )
        new_device = device.with_updates(rssi=-60)
        assert new_device.connection_state == ConnectionState.CONNECTED

    def test_with_updates_change_state(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF")
        new_device = device.with_updates(connection_state=ConnectionState.CONNECTED)
        assert new_device.connection_state == ConnectionState.CONNECTED

    def test_manufacturer_data_default_empty(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF")
        assert device.manufacturer_data == {}

    def test_service_uuids_default_empty(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF")
        assert device.service_uuids == []

    def test_is_connectable_default(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF")
        assert device.is_connectable is True

    def test_is_paired_default(self):
        device = BLEDeviceModel(address="AA:BB:CC:DD:EE:FF")
        assert device.is_paired is False


class TestFromBleak:
    def test_basic_conversion(self):
        mock_device = type("MockDevice", (), {
            "address": "AA:BB:CC:DD:EE:FF",
            "name": "Test Device",
        })()
        mock_ad = type("MockAD", (), {
            "local_name": None,
            "rssi": -65,
            "appearance": 0x0080,
            "manufacturer_data": {0x004C: b"\x01\x02"},
            "service_uuids": ["0000110b-0000-1000-8000-00805f9b34fb"],
            "tx_power": -12,
            "is_connectable": True,
        })()

        model = BLEDeviceModel.from_bleak(mock_device, mock_ad)
        assert model.address == "AA:BB:CC:DD:EE:FF"
        assert model.name == "Test Device"
        assert model.rssi == -65
        assert model.appearance == 0x0080
        assert 0x004C in model.manufacturer_data
        assert len(model.service_uuids) == 1
        assert model.tx_power == -12
        assert model.is_connectable is True

    def test_fallback_to_ad_local_name(self):
        mock_device = type("MockDevice", (), {
            "address": "AA:BB:CC:DD:EE:FF",
            "name": None,
        })()
        mock_ad = type("MockAD", (), {
            "local_name": "Fallback Name",
            "rssi": None,
            "appearance": None,
            "manufacturer_data": {},
            "service_uuids": [],
            "tx_power": None,
            "is_connectable": False,
        })()

        model = BLEDeviceModel.from_bleak(mock_device, mock_ad)
        assert model.name == "Fallback Name"
        assert model.rssi == -100
        assert model.appearance == 0
        assert model.is_connectable is False

    def test_no_name_at_all(self):
        mock_device = type("MockDevice", (), {
            "address": "AA:BB:CC:DD:EE:FF",
            "name": None,
        })()
        mock_ad = type("MockAD", (), {
            "local_name": None,
            "rssi": -80,
            "appearance": 0,
            "manufacturer_data": {},
            "service_uuids": [],
            "tx_power": None,
            "is_connectable": True,
        })()

        model = BLEDeviceModel.from_bleak(mock_device, mock_ad)
        assert model.name == "Unknown"
