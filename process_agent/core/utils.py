from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


def load_json_file(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: str | Path, data: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
