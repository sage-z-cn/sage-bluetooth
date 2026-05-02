import pytest
from src.utils.device_type_resolver import (
    resolve_device_type,
    resolve_by_service_uuids,
    resolve_by_name,
    resolve_device_type_comprehensive,
)
from src.models.device import DeviceType


class TestResolveDeviceType:
    def test_unknown_appearance_zero(self):
        assert resolve_device_type(0x0000) == DeviceType.UNKNOWN

    def test_phone(self):
        assert resolve_device_type(0x0001) == DeviceType.PHONE

    def test_computer(self):
        assert resolve_device_type(0x0002) == DeviceType.COMPUTER

    def test_watch(self):
        assert resolve_device_type(0x0003) == DeviceType.WATCH

    def test_keyboard(self):
        assert resolve_device_type(0x0015) == DeviceType.KEYBOARD

    def test_mouse(self):
        assert resolve_device_type(0x0016) == DeviceType.MOUSE

    def test_gamepad(self):
        assert resolve_device_type(0x0017) == DeviceType.GAMEPAD

    def test_thermometer(self):
        assert resolve_device_type(0x000D) == DeviceType.THERMOMETER

    def test_heart_rate(self):
        assert resolve_device_type(0x000F) == DeviceType.HEART_RATE

    def test_blood_pressure(self):
        assert resolve_device_type(0x0011) == DeviceType.BLOOD_PRESSURE

    def test_glucose(self):
        assert resolve_device_type(0x001D) == DeviceType.GLUCOSE

    def test_fitness_tracker(self):
        assert resolve_device_type(0x001E) == DeviceType.FITNESS_TRACKER

    def test_headphone(self):
        assert resolve_device_type(0x0080) == DeviceType.HEADPHONE

    def test_headset(self):
        assert resolve_device_type(0x0083) == DeviceType.HEADSET

    def test_speaker(self):
        assert resolve_device_type(0x0085) == DeviceType.SPEAKER

    def test_unknown_out_of_range(self):
        assert resolve_device_type(0xFFFF) == DeviceType.UNKNOWN

    def test_keyboard_c1(self):
        assert resolve_device_type(0x00C1) == DeviceType.KEYBOARD

    def test_mouse_c2(self):
        assert resolve_device_type(0x00C2) == DeviceType.MOUSE

    def test_watch_e0(self):
        assert resolve_device_type(0x00E0) == DeviceType.WATCH


BLE_UUID_BASE = "-0000-1000-8000-00805f9b34fb"


class TestResolveByServiceUUIDs:
    def test_audio_sink(self):
        uuids = [f"0000110b{BLE_UUID_BASE}"]
        assert resolve_by_service_uuids(uuids) == DeviceType.HEADPHONE

    def test_heart_rate(self):
        uuids = [f"0000180d{BLE_UUID_BASE}"]
        assert resolve_by_service_uuids(uuids) == DeviceType.HEART_RATE

    def test_blood_pressure(self):
        uuids = [f"00001810{BLE_UUID_BASE}"]
        assert resolve_by_service_uuids(uuids) == DeviceType.BLOOD_PRESSURE

    def test_human_interface(self):
        uuids = [f"00001812{BLE_UUID_BASE}"]
        assert resolve_by_service_uuids(uuids) == DeviceType.KEYBOARD

    def test_unknown_uuid(self):
        uuids = [f"00009999{BLE_UUID_BASE}"]
        assert resolve_by_service_uuids(uuids) == DeviceType.UNKNOWN

    def test_empty_list(self):
        assert resolve_by_service_uuids([]) == DeviceType.UNKNOWN

    def test_multiple_uuids_first_match(self):
        uuids = [f"00001808{BLE_UUID_BASE}", f"0000180d{BLE_UUID_BASE}"]
        assert resolve_by_service_uuids(uuids) == DeviceType.GLUCOSE


class TestResolveByName:
    def test_airpods(self):
        assert resolve_by_name("AirPods Pro") == DeviceType.HEADPHONE

    def test_keyboard(self):
        assert resolve_by_name("Logitech MX Keys") == DeviceType.KEYBOARD

    def test_speaker(self):
        assert resolve_by_name("JBL Flip 6") == DeviceType.SPEAKER

    def test_watch(self):
        assert resolve_by_name("Apple Watch Series 9") == DeviceType.WATCH

    def test_fitness_tracker(self):
        assert resolve_by_name("Mi Band 7") == DeviceType.FITNESS_TRACKER

    def test_gamepad(self):
        assert resolve_by_name("Xbox Controller") == DeviceType.GAMEPAD

    def test_unknown_name(self):
        assert resolve_by_name("Random Device XYZ") == DeviceType.UNKNOWN

    def test_case_insensitive(self):
        assert resolve_by_name("AIRPODS PRO") == DeviceType.HEADPHONE

    def test_empty_name(self):
        assert resolve_by_name("") == DeviceType.UNKNOWN


class TestResolveComprehensive:
    def test_appearance_takes_priority(self):
        result = resolve_device_type_comprehensive(
            0x0080,
            service_uuids=[f"00001812{BLE_UUID_BASE}"],
            name="Keyboard",
        )
        assert result == DeviceType.HEADPHONE

    def test_service_uuid_fallback(self):
        result = resolve_device_type_comprehensive(
            0x0000,
            service_uuids=[f"0000180d{BLE_UUID_BASE}"],
            name="Some Device",
        )
        assert result == DeviceType.HEART_RATE

    def test_name_fallback(self):
        result = resolve_device_type_comprehensive(
            0x0000,
            service_uuids=[],
            name="AirPods Pro",
        )
        assert result == DeviceType.HEADPHONE

    def test_all_unknown(self):
        result = resolve_device_type_comprehensive(
            0x0000,
            service_uuids=[],
            name="",
        )
        assert result == DeviceType.UNKNOWN

    def test_appearance_unknown_tries_service(self):
        result = resolve_device_type_comprehensive(
            0x0005,
            service_uuids=[f"00001812{BLE_UUID_BASE}"],
            name="",
        )
        assert result == DeviceType.KEYBOARD
