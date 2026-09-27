"""The one v0.1 preference: badge position relative to the cat's lower-left."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class OverlayConfig:
    offset_x: int = 12
    offset_y: int = -62


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
        return ConfigResult(OverlayConfig(x, y))
    except (UnicodeError, ValueError, KeyError) as error:
        # Leave the user's file untouched so they can correct it.
        return ConfigResult(OverlayConfig(), str(error))
