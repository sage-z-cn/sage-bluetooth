"""
蓝牙扫描诊断脚本 - 逐步验证扫描和获取设备列表的每个环节

用法:
    .venv/Scripts/python.exe tests/test_scan_diagnostic.py
    .venv/Scripts/python.exe tests/test_scan_diagnostic.py --timeout 15
"""

import asyncio
import sys
import time

sys.path.insert(0, ".")


def header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def result(passed, msg):
    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] {msg}")


async def step1_check_adapter():
    header("Step 1: 检查蓝牙适配器状态")
    try:
        from winsdk.windows.devices.radios import Radio, RadioKind, RadioState

        radios = await Radio.get_radios_async()
        bt_radio = None
        for radio in radios:
            print(f"  发现 Radio: kind={radio.kind}, name={radio.name}, state={radio.state}")
            if radio.kind == RadioKind.BLUETOOTH:
                bt_radio = radio

        if bt_radio is None:
            result(False, "未找到蓝牙 Radio，设备可能不支持蓝牙")
            return False

        is_on = bt_radio.state == RadioState.ON
        result(is_on, f"蓝牙适配器状态: {'ON' if is_on else 'OFF'} (state={bt_radio.state})")
        return is_on
    except Exception as e:
        result(False, f"检查适配器失败: {e}")
        return False


async def step2_raw_bleak_scan(timeout):
    header(f"Step 2: 直接使用 BleakScanner 原始扫描 (timeout={timeout}s)")
    try:
        from bleak import BleakScanner

        devices = []

        def on_detect(device, adv_data):
            devices.append((device, adv_data))
            print(f"    [回调] 发现: {device.name or 'N/A'} | {device.address} | RSSI={adv_data.rssi}")

        scanner = BleakScanner(detection_callback=on_detect)
        print(f"  BleakScanner 创建成功")
        print(f"  正在扫描...")
        t0 = time.monotonic()

        await scanner.start()
        await asyncio.sleep(timeout)
        await scanner.stop()

        elapsed = time.monotonic() - t0
        print(f"  扫描完成，耗时 {elapsed:.1f}s")
        result(bool(devices), f"原始 BleakScanner 发现 {len(devices)} 个设备")

        if devices:
            print(f"\n  --- 设备列表 ---")
            for i, (dev, adv) in enumerate(devices, 1):
                name = dev.name or adv.local_name or "Unknown"
                print(f"    {i}. {name}")
                print(f"       地址: {dev.address}  RSSI: {adv.rssi}")
                print(f"       UUIDs: {adv.service_uuids}")
                print(f"       Manufacturer Data: {list(adv.manufacturer_data.keys()) if adv.manufacturer_data else 'None'}")
        else:
            print("  !! 未发现任何设备，可能原因:")
            print("     - 蓝牙适配器未开启")
            print("     - 附近没有 BLE 设备广播")
            print("     - Windows 蓝牙服务异常")
            print("     - 权限不足")

        return len(devices)

    except Exception as e:
        result(False, f"BleakScanner 扫描失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def step3_bleak_discover(timeout):
    header(f"Step 3: 使用 BleakScanner.discover() 扫描 (timeout={timeout}s)")
    try:
        from bleak import BleakScanner

        print(f"  正在扫描...")
        t0 = time.monotonic()
        devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
        elapsed = time.monotonic() - t0

        result(bool(devices), f"discover() 发现 {len(devices)} 个设备 ({elapsed:.1f}s)")

        if devices:
            print(f"\n  --- 设备列表 ---")
            for i, (addr, (dev, adv)) in enumerate(devices.items(), 1):
                name = dev.name or adv.local_name or "Unknown"
                print(f"    {i}. {name}")
                print(f"       地址: {dev.address}  RSSI: {adv.rssi}")

        return len(devices)

    except Exception as e:
        result(False, f"discover() 扫描失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def step4_device_scanner_class(timeout):
    header(f"Step 4: 测试项目 DeviceScanner 类 (timeout={timeout}s)")

    found_devices = []
    updated_devices = []
    errors = []

    try:
        from src.core.device_scanner import DeviceScanner

        scanner = DeviceScanner()

        scanner.device_found.connect(lambda d: found_devices.append(d))
        scanner.device_updated.connect(lambda d: updated_devices.append(d))
        scanner.error_occurred.connect(lambda e: errors.append(e))

        print(f"  初始状态: is_scanning={scanner.is_scanning}")

        t0 = time.monotonic()
        await scanner.start_scan(timeout=timeout)
        elapsed = time.monotonic() - t0

        print(f"  扫描后状态: is_scanning={scanner.is_scanning}")
        result(not scanner.is_scanning, f"扫描后 is_scanning 应为 False (实际={scanner.is_scanning})")
        result(not errors, f"扫描错误: {errors}" if errors else "扫描无错误")
        result(bool(found_devices), f"DeviceScanner 发现 {len(found_devices)} 个设备, 更新 {len(updated_devices)} 次 ({elapsed:.1f}s)")

        if found_devices:
            print(f"\n  --- 设备列表 ---")
            for i, d in enumerate(found_devices, 1):
                print(f"    {i}. {d.display_name}")
                print(f"       地址: {d.address}  RSSI: {d.rssi}  类型: {d.appearance}")

        return len(found_devices)

    except Exception as e:
        result(False, f"DeviceScanner 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def step5_bluetooth_manager(timeout):
    header(f"Step 5: 测试 BluetoothManager 集成 (timeout={timeout}s)")

    discovered = []
    updated = []
    scan_start_count = [0]
    scan_finish_count = [0]
    errors = []

    try:
        from src.core.bluetooth_manager import BluetoothManager

        mgr = BluetoothManager()

        mgr.device_discovered.connect(lambda d: discovered.append(d))
        mgr.device_updated.connect(lambda d: updated.append(d))
        mgr.scan_started.connect(lambda: scan_start_count.__setitem__(0, scan_start_count[0] + 1))
        mgr.scan_finished.connect(lambda: scan_finish_count.__setitem__(0, scan_finish_count[0] + 1))
        mgr.error_occurred.connect(lambda e: errors.append(e))

        is_on = mgr.is_adapter_on()
        result(is_on, f"适配器状态: {'ON' if is_on else 'OFF'}")

        if not is_on:
            print("  !! 适配器未开启，跳过扫描测试")
            return 0

        print(f"  开始扫描...")
        mgr.start_scan(timeout=timeout)

        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout + 2:
            await asyncio.sleep(0.5)
            if scan_finish_count[0] >= 1:
                break

        elapsed = time.monotonic() - t0
        result(scan_start_count[0] >= 1, f"scan_started 信号发射 {scan_start_count[0]} 次")
        result(scan_finish_count[0] >= 1, f"scan_finished 信号发射 {scan_finish_count[0]} 次 ({elapsed:.1f}s)")
        result(not errors, f"错误: {errors}" if errors else "无错误")
        result(bool(discovered), f"BluetoothManager 发现 {len(discovered)} 个设备, 更新 {len(updated)} 次")

        if discovered:
            print(f"\n  --- 设备列表 ---")
            for i, d in enumerate(discovered, 1):
                print(f"    {i}. {d.display_name}")
                print(f"       地址: {d.address}  RSSI: {d.rssi}")

        return len(discovered)

    except Exception as e:
        result(False, f"BluetoothManager 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def step6_refresh_flow(timeout):
    header("Step 6: 测试刷新流程 (stop + clear + start)")

    try:
        from src.core.bluetooth_manager import BluetoothManager

        mgr = BluetoothManager()

        if not mgr.is_adapter_on():
            print("  !! 适配器未开启，跳过")
            return

        discovered1 = []
        discovered2 = []
        errors = []
        scan_finish_count = [0]

        mgr.device_discovered.connect(lambda d: discovered1.append(d))
        mgr.error_occurred.connect(lambda e: errors.append(e))
        mgr.scan_finished.connect(lambda: scan_finish_count.__setitem__(0, scan_finish_count[0] + 1))

        short_timeout = min(timeout, 5.0)
        print(f"  第一次扫描 (timeout={short_timeout}s)...")
        mgr.start_scan(timeout=short_timeout)

        t0 = time.monotonic()
        while time.monotonic() - t0 < short_timeout + 2:
            await asyncio.sleep(0.3)
            if scan_finish_count[0] >= 1:
                break

        count1 = len(discovered1)
        print(f"  第一次扫描完成，发现 {count1} 个设备")

        scan_finish_count[0] = 0
        mgr.device_discovered.disconnect()
        mgr.device_discovered.connect(lambda d: discovered2.append(d))

        print(f"  模拟刷新: stop_scan -> clear -> start_scan...")
        mgr.stop_scan()
        await asyncio.sleep(0.3)

        mgr.start_scan(timeout=short_timeout)

        t0 = time.monotonic()
        while time.monotonic() - t0 < short_timeout + 2:
            await asyncio.sleep(0.3)
            if scan_finish_count[0] >= 1:
                break

        count2 = len(discovered2)
        print(f"  第二次扫描完成，发现 {count2} 个设备")

        result(not errors, f"错误: {errors}" if errors else "刷新流程无错误")
        result(scan_finish_count[0] >= 1, f"刷新后 scan_finished 正常发射")
        result(count2 >= 0, f"刷新后扫描发现 {count2} 个设备")

    except Exception as e:
        result(False, f"刷新流程测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="蓝牙扫描诊断")
    parser.add_argument("--timeout", type=float, default=10.0, help="扫描超时(秒)")
    args = parser.parse_args()

    timeout = args.timeout
    print(f"蓝牙扫描诊断工具 - timeout={timeout}s")
    print(f"Python: {sys.version}")
    try:
        from importlib.metadata import version
        print(f"bleak: {version('bleak')}")
    except Exception:
        pass

    adapter_ok = await step1_check_adapter()
    if not adapter_ok:
        print("\n!! 蓝牙适配器未就绪，后续测试可能失败，继续执行...")

    await step2_raw_bleak_scan(timeout)
    await step3_bleak_discover(timeout)

    if sys.platform == "win32":
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
        except Exception as e:
            print(f"\n  [WARN] 无法创建 QApplication: {e}")

    await step4_device_scanner_class(timeout)
    await step5_bluetooth_manager(timeout)
    await step6_refresh_flow(timeout)

    header("诊断完成")


if __name__ == "__main__":
    asyncio.run(main())
