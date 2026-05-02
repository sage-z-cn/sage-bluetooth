import PyInstaller.__main__
import os
import shutil
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
BUILD_DIR = os.path.join(PROJECT_DIR, "build")
SPEC_FILE = os.path.join(PROJECT_DIR, "SageBluetooth.spec")

APP_NAME = "SageBluetooth"
VERSION = "1.0.0"

ENTRY_SCRIPT = os.path.join(PROJECT_DIR, "src", "main.py")
ICON_PATH = os.path.join(PROJECT_DIR, "resources", "icons", "app.ico")


def clean_build():
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    if os.path.exists(SPEC_FILE):
        os.remove(SPEC_FILE)


def build():
    clean_build()

    args = [
        ENTRY_SCRIPT,
        f"--name={APP_NAME}",
        "--windowed",
        "--onefile",
        f"--icon={ICON_PATH}",
        f"--add-data=resources;resources",
        "--hidden-import=qasync",
        "--hidden-import=bleak.backends.winrt",
        "--hidden-import=bleak.args",
        "--hidden-import=PyQt6.sip",
        "--clean",
        "--noconfirm",
    ]

    print(f"[*] 开始打包 {APP_NAME} v{VERSION}...")
    PyInstaller.__main__.run(args)
    print(f"[*] 打包完成，输出目录: {DIST_DIR}")

    exe_path = os.path.join(DIST_DIR, f"{APP_NAME}.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"[*] 可执行文件: {exe_path}")
        print(f"[*] 文件大小: {size_mb:.1f} MB")
    else:
        print("[!] 打包失败，未生成可执行文件")
        sys.exit(1)


if __name__ == "__main__":
    build()
