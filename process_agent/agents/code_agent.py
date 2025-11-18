from __future__ import annotations
from typing import Any, Dict, List, Tuple
from pathlib import Path
import logging

from ..core.utils import load_json_file


class CodeAgent:
    """Translates a machining plan into pseudo–G-code using local rules.

    - Loads material/tool defaults from data/machining_db.json
    - Computes spindle speed (S) and feed (F) from material recommendations
    - Emits simple metric, absolute G-code blocks for supported operations
    """

    def __init__(self, db_path: str | Path | None = None, logger: logging.Logger = None) -> None:
        self.db_path = Path(db_path) if db_path else Path(__file__).parents[2] / "data" / "machining_db.json"
        self.logger = logger or logging.getLogger("ProcessAgent.CodeAgent")
        try:
            self.db: Dict[str, Any] = load_json_file(self.db_path)
            self.logger.info(f"Loaded machining database from {self.db_path}")
        except FileNotFoundError:
            self.logger.error(f"Machining database not found at {self.db_path}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load machining database: {str(e)}")
            raise

    def _pick_tool_for_drilling(self, diameter_mm: float) -> Tuple[str, Dict[str, Any]]:
        tools: Dict[str, Any] = self.db.get("tools", {})
        preferred_key = f"drill_{int(diameter_mm)}mm"
        if preferred_key in tools:
            self.logger.debug(f"Using preferred tool: {preferred_key} for {diameter_mm}mm hole")
            return preferred_key, tools[preferred_key]
        # Fallback: choose the closest diameter drill
        candidates: List[Tuple[str, float]] = []
        for key, meta in tools.items():
            if meta.get("type") == "drill" and isinstance(meta.get("diameter_mm"), (int, float)):
                candidates.append((key, float(meta["diameter_mm"])) )
        if not candidates:
            self.logger.error("No drill tools available in database")
            raise ValueError("No drill tools available in DB")
        closest_key, closest_dia = min(candidates, key=lambda kv: abs(kv[1] - diameter_mm))
        self.logger.warning(f"No exact match for {diameter_mm}mm drill, using closest: {closest_key} ({closest_dia}mm)")
        return closest_key, tools[closest_key]

    def _material_params(self, material_key: str) -> Tuple[int, int]:
        materials: Dict[str, Any] = self.db.get("materials", {})
        if material_key not in materials:
            self.logger.error(f"Material '{material_key}' not found in database. Available: {list(materials.keys())}")
            raise ValueError(f"Unknown material: {material_key}")
        rpm = int(materials[material_key].get("recommended_rpm", 1000))
        feed = int(materials[material_key].get("recommended_feed_mm_per_min", 100))
        self.logger.debug(f"Material '{material_key}': RPM={rpm}, Feed={feed} mm/min")
        return rpm, feed

    def generate_pseudo_gcode(self, plan: List[Dict[str, Any]], *, material: str) -> str:
        """Generate pseudo-G-code from a machining plan.
        
        Uses tool, RPM, and feed_rate from plan steps if available (from LLM planner),
        otherwise falls back to material defaults.
        """
        self.logger.info(f"Generating G-code for {len(plan)} step(s), material: {material}")
        
        # Get default material parameters as fallback
        try:
            default_rpm, default_feed = self._material_params(material)
        except ValueError as e:
            self.logger.warning(f"Failed to get material parameters: {str(e)}, using defaults")
            default_rpm, default_feed = 1000, 100
        
        lines: List[str] = []
        lines.append("; PSEUDO-GCODE GENERATED")
        lines.append(f"; MATERIAL: {material}")
        lines.append("G90 G21")  # absolute, metric
        
        # Use RPM from first step if available, otherwise default
        first_step_rpm = plan[0].get("rpm") if plan else None
        initial_rpm = int(first_step_rpm) if first_step_rpm else default_rpm
        lines.append(f"M03 S{initial_rpm}")  # spindle on

        for idx, step in enumerate(plan):
            op = step.get("operation")
            self.logger.debug(f"Processing step {idx+1}: {op}")
            
            # Get step-specific parameters (from LLM planner) or use defaults
            step_rpm = step.get("rpm")
            step_feed = step.get("feed_rate_mm_per_min")
            rpm = int(step_rpm) if step_rpm else default_rpm
            feed = float(step_feed) if step_feed else default_feed
            tool = step.get("tool", "unknown")
            
            if op == "face_milling":
                depth = float(step.get("depth_mm", 0.2))
                # Simple square sweep placeholder
                lines.extend([
                    f"; -- Face Milling (Tool: {tool}, RPM: {rpm}, Feed: {feed} mm/min) --",
                    "G00 X0 Y0 Z5",
                    f"G01 Z-{depth:.3f} F{feed}",
                    "G01 X50 Y0",
                    "G01 X50 Y50",
                    "G01 X0 Y50",
                    "G01 X0 Y0",
                    "G00 Z5",
                ])
                self.logger.debug(f"Generated face milling G-code (tool: {tool}, depth: {depth}mm, RPM: {rpm}, feed: {feed})")
            elif op == "drilling":
                dia = float(step.get("diameter_mm", 3.0))
                depth = float(step.get("depth_mm", 10.0))
                pos = step.get("position", [0.0, 0.0])
                x, y = float(pos[0]), float(pos[1])
                
                # Use tool from plan if available, otherwise look it up
                if tool and tool != "unknown":
                    tool_key = tool
                    tool_meta = self.db.get("tools", {}).get(tool_key, {})
                else:
                    try:
                        tool_key, tool_meta = self._pick_tool_for_drilling(dia)
                    except ValueError as e:
                        self.logger.error(f"Failed to select tool for drilling: {str(e)}")
                        raise
                
                lines.extend([
                    f"; -- Drilling (Tool: {tool_key} DIA {tool_meta.get('diameter_mm','?')}mm, RPM: {rpm}, Feed: {feed} mm/min) --",
                    f"G00 X{x:.3f} Y{y:.3f} Z5",
                    f"G01 Z-{depth:.3f} F{feed}",
                    "G00 Z5",
                ])
                self.logger.debug(f"Generated drilling G-code (tool: {tool_key}, dia: {dia}mm, depth: {depth}mm, pos: [{x}, {y}], RPM: {rpm}, feed: {feed})")
            else:
                self.logger.warning(f"Unsupported operation in step {idx+1}: {op}")
                lines.append(f"; Unsupported operation: {op}")

        lines.append("M05")
        lines.append("M30")
        
        gcode = "\n".join(lines)
        self.logger.info(f"G-code generation completed ({len(lines)} lines)")
        return gcode
