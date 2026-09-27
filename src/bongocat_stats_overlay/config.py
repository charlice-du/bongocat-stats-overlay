"""Validated badge preferences, compatible with v0.1 position files."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class OverlayConfig:
    offset_x: int = 12
    offset_y: int = -62
    scale: float = 1.0
    count_mouse_clicks: bool = True


@dataclass(frozen=True)
class ConfigResult:
    config: OverlayConfig
    warning: str | None = None


def load_config(path):
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        defaults = OverlayConfig()
        try:
            with path.open("x", encoding="utf-8") as stream:
                json.dump(defaults.__dict__, stream, indent=2)
                stream.write("\n")
        except FileExistsError:
            pass  # Another instance made it; read the resulting file below.
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("config root is not an object")
        x, y = data["offset_x"], data["offset_y"]
        if any(type(value) is not int or not -4000 <= value <= 4000
               for value in (x, y)):
            raise ValueError("offsets must be integers from -4000 to 4000")
        scale = data.get("scale", 1.0)
        if type(scale) not in (int, float) or not 0.75 <= scale <= 2.0:
            raise ValueError("scale must be a number from 0.75 to 2.0")
        count_mouse_clicks = data.get("count_mouse_clicks", True)
        if type(count_mouse_clicks) is not bool:
            raise ValueError("count_mouse_clicks must be true or false")
        return ConfigResult(OverlayConfig(x, y, float(scale),
                                          count_mouse_clicks))
    except (UnicodeError, ValueError, KeyError) as error:
        # Leave the user's file untouched so they can correct it.
        return ConfigResult(OverlayConfig(), str(error))
