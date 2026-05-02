import json
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from src.config import CONFIG_PATH


@dataclass
class AppConfig:
    auto_hide_on_blur: bool = True
    scan_timeout: float = 10.0
    battery_poll_interval: int = 60
    show_disconnected_devices: bool = False
    theme: str = "light"
    window_width: int = 400
    window_height: int = 600

    CONFIG_PATH: ClassVar[Path] = CONFIG_PATH

    def save(self) -> None:
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {k: v for k, v in self.__dict__.items()}
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls) -> "AppConfig":
        if not cls.CONFIG_PATH.exists():
            return cls()
        try:
            with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            return cls(**filtered)
        except (json.JSONDecodeError, TypeError):
            return cls()
