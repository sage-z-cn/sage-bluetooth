import os
import sys
import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
DEBOUNCE_SECONDS = 0.5


class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self._process = None
        self._last_restart = 0

    def start(self):
        self._spawn()

    def _spawn(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
        self._process = subprocess.Popen(
            [sys.executable, "-m", "src.main"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

    def on_modified(self, event):
        if not event.src_path.endswith(".py"):
            return
        now = time.time()
        if now - self._last_restart < DEBOUNCE_SECONDS:
            return
        self._last_restart = now
        print(f"\n[dev] {event.src_path} changed — restarting...\n")
        self._spawn()

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()


def main():
    handler = RestartHandler()
    observer = Observer()
    observer.schedule(handler, SRC_DIR, recursive=True)
    observer.start()
    handler.start()

    print(f"[dev] Watching {SRC_DIR} for changes... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(0.5)
            if handler._process and handler._process.poll() is not None:
                code = handler._process.returncode
                if code != 0:
                    print(f"[dev] App exited with code {code}, waiting for file change to restart...")
    except KeyboardInterrupt:
        print("\n[dev] Stopping...")
    finally:
        handler.stop()
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
