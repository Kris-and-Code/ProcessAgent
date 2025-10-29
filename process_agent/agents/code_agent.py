from __future__ import annotations
from typing import Any, Dict, List, Tuple
from pathlib import Path

from ..core.utils import load_json_file


class CodeAgent:
    """Translates a machining plan into pseudo–G-code using local rules.

    - Loads material/tool defaults from data/machining_db.json
    - Computes spindle speed (S) and feed (F) from material recommendations
    - Emits simple metric, absolute G-code blocks for supported operations
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else Path(__file__).parents[2] / "data" / "machining_db.json"
        self.db: Dict[str, Any] = load_json_file(self.db_path)

    def _pick_tool_for_drilling(self, diameter_mm: float) -> Tuple[str, Dict[str, Any]]:
        tools: Dict[str, Any] = self.db.get("tools", {})
        preferred_key = f"drill_{int(diameter_mm)}mm"
        if preferred_key in tools:
            return preferred_key, tools[preferred_key]
        # Fallback: choose the closest diameter drill
        candidates: List[Tuple[str, float]] = []
        for key, meta in tools.items():
            if meta.get("type") == "drill" and isinstance(meta.get("diameter_mm"), (int, float)):
                candidates.append((key, float(meta["diameter_mm"])) )
        if not candidates:
            raise ValueError("No drill tools available in DB")
        closest_key, _ = min(candidates, key=lambda kv: abs(kv[1] - diameter_mm))
        return closest_key, tools[closest_key]

    def _material_params(self, material_key: str) -> Tuple[int, int]:
        materials: Dict[str, Any] = self.db.get("materials", {})
        if material_key not in materials:
            raise ValueError(f"Unknown material: {material_key}")
        rpm = int(materials[material_key].get("recommended_rpm", 1000))
        feed = int(materials[material_key].get("recommended_feed_mm_per_min", 100))
        return rpm, feed

    def generate_pseudo_gcode(self, plan: List[Dict[str, Any]], *, material: str) -> str:
        rpm, feed = self._material_params(material)
        lines: List[str] = []
        lines.append("; PSEUDO-GCODE GENERATED")
        lines.append(f"; MATERIAL: {material}")
        lines.append("G90 G21")  # absolute, metric
        lines.append(f"M03 S{rpm}")  # spindle on

        for step in plan:
            op = step.get("operation")
            if op == "face_milling":
                depth = float(step.get("depth_mm", 0.2))
                # Simple square sweep placeholder
                lines.extend([
                    "; -- Face Milling --",
                    "G00 X0 Y0 Z5",
                    f"G01 Z-{depth:.3f} F{feed}",
                    "G01 X50 Y0",
                    "G01 X50 Y50",
                    "G01 X0 Y50",
                    "G01 X0 Y0",
                    "G00 Z5",
                ])
            elif op == "drilling":
                dia = float(step.get("diameter_mm", 3.0))
                depth = float(step.get("depth_mm", 10.0))
                pos = step.get("position", [0.0, 0.0])
                x, y = float(pos[0]), float(pos[1])
                tool_key, tool_meta = self._pick_tool_for_drilling(dia)
                lines.extend([
                    "; -- Drilling --",
                    f"; TOOL {tool_key} DIA {tool_meta.get('diameter_mm','?')}mm",
                    f"G00 X{x:.3f} Y{y:.3f} Z5",
                    f"G01 Z-{depth:.3f} F{feed}",
                    "G00 Z5",
                ])
            else:
                lines.append(f"; Unsupported operation: {op}")

        lines.append("M05")
        lines.append("M30")
        return "\n".join(lines)
