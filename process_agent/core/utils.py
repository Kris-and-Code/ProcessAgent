from __future__ import annotations
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List


def load_json_file(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: str | Path, data: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def pretty_print_plan(plan: List[dict]) -> str:
    out = []
    for i, step in enumerate(plan):
        desc = f"Step {i+1}: {step.get('operation','').replace('_',' ').title()}"
        if 'notes' in step and step['notes']:
            desc += f" — {step['notes']}"
        if step.get('diameter_mm'):
            desc += f", diameter={step['diameter_mm']}mm"
        if step.get('depth_mm'):
            desc += f", depth={step['depth_mm']}mm"
        if step.get('position'):
            desc += f", position={step['position']}"
        out.append(desc)
    return '\n'.join(out)


def setup_logger(logfile: str = "logs/run.log") -> logging.Logger:
    Path(logfile).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ProcessAgent")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    # File handler
    fh = logging.FileHandler(logfile, mode="a")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger
