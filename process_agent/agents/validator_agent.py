from __future__ import annotations
from typing import Any, Dict, List, Tuple


class ValidatorAgent:
    """Validates the plan and generated pseudo–G-code for basic issues."""

    def validate(self, plan: List[Dict[str, Any]], gcode: str) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not plan:
            errors.append("Plan is empty")
        if not gcode or "PSEUDO-GCODE" not in gcode or "M30" not in gcode:
            errors.append("G-code missing header or terminator")

        for idx, step in enumerate(plan):
            op = step.get("operation")
            if op not in {"face_milling", "drilling"}:
                errors.append(f"Step {idx}: Unsupported operation '{op}'")
            depth = step.get("depth_mm")
            if depth is not None and (not isinstance(depth, (int, float)) or depth <= 0):
                errors.append(f"Step {idx}: depth_mm must be > 0")
            if op == "drilling":
                dia = step.get("diameter_mm")
                pos = step.get("position")
                if dia is None or not isinstance(dia, (int, float)) or dia <= 0:
                    errors.append(f"Step {idx}: drilling requires diameter_mm > 0")
                if not (isinstance(pos, list) and len(pos) == 2):
                    errors.append(f"Step {idx}: drilling requires position [x, y]")
        return (len(errors) == 0, errors)
