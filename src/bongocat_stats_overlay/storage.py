"""Local-only persistent statistics with atomic saves and corrupt-file backup."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4


APP_DIR_NAME = "BongoCatStatsOverlay"


def user_data_dir(environ=None):
    variables = os.environ if environ is None else environ
    base = variables.get("LOCALAPPDATA")
    if not base:
        base = Path.home() / "AppData" / "Local"
    return Path(base) / APP_DIR_NAME


@dataclass(frozen=True)
class LoadResult:
    total: int
    corrupt_backup: Path | None = None


def _backup_name(path):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return path.with_name(
        f"{path.stem}.corrupt-{timestamp}-{uuid4().hex[:8]}{path.suffix}")


def load_total(path):
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("statistics root is not an object")
        total = data.get("total")
        if type(total) is not int or total < 0:
            raise ValueError("statistics total is not a non-negative integer")
        return LoadResult(total)
    except FileNotFoundError:
        return LoadResult(0)
    except (UnicodeError, ValueError):
        backup = _backup_name(path)
        # Do not overwrite a broken file with zero; keep it for recovery.
        os.replace(path, backup)
        return LoadResult(0, backup)


def save_total(total, path):
    """Replace the statistics file atomically on the same filesystem."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"total": max(0, int(total))}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
