from __future__ import annotations
from typing import Any, Dict, List, Tuple
import logging


class ValidatorAgent:
    """Validates the plan and generated pseudo–G-code for basic issues."""
    
    def __init__(self, logger: logging.Logger = None):
        """Initialize the validator agent with optional logger."""
        self.logger = logger or logging.getLogger("ProcessAgent.ValidatorAgent")

    def validate(self, plan: List[Dict[str, Any]], gcode: str | None) -> Tuple[bool, List[str]]:
        """Validate plan and optionally G-code, including LLM output validation."""
        errors: List[str] = []
        validation_type = "G-code" if gcode is not None else "Plan"
        self.logger.info(f"Starting {validation_type.lower()} validation...")
        
        # Plan validation
        if not plan:
            error_msg = "Plan is empty"
            errors.append(error_msg)
            self.logger.warning(error_msg)
        else:
            self.logger.debug(f"Validating {len(plan)} plan step(s)")
        
        # G-code validation (only if provided)
        if gcode is not None:
            if not gcode:
                error_msg = "G-code is empty"
                errors.append(error_msg)
                self.logger.warning(error_msg)
            elif "PSEUDO-GCODE" not in gcode:
                error_msg = "G-code missing header (PSEUDO-GCODE marker)"
                errors.append(error_msg)
                self.logger.warning(error_msg)
            elif "M30" not in gcode:
                error_msg = "G-code missing terminator (M30)"
                errors.append(error_msg)
                self.logger.warning(error_msg)
            else:
                self.logger.debug("G-code structure validation passed")

        # Step-by-step validation with LLM output checks
        for idx, step in enumerate(plan):
            op = step.get("operation")
            if op not in {"face_milling", "drilling"}:
                error_msg = f"Step {idx+1}: Unsupported operation '{op}'"
                errors.append(error_msg)
                self.logger.warning(error_msg)
            
            # Validate depth
            depth = step.get("depth_mm")
            if depth is not None and (not isinstance(depth, (int, float)) or depth <= 0):
                error_msg = f"Step {idx+1}: depth_mm must be > 0 (got {depth})"
                errors.append(error_msg)
                self.logger.warning(error_msg)
            
            # Validate tool selection (LLM should provide this, but optional for rule-based)
            tool = step.get("tool")
            if tool is not None and (not isinstance(tool, str) or not tool.strip()):
                error_msg = f"Step {idx+1}: Invalid tool identifier (got {tool})"
                errors.append(error_msg)
                self.logger.warning(error_msg)
            elif tool is None:
                self.logger.debug(f"Step {idx+1}: No tool specified (rule-based fallback mode)")
            
            # Validate RPM (LLM should provide this, but optional for rule-based)
            rpm = step.get("rpm")
            if rpm is not None:
                if not isinstance(rpm, (int, float)) or rpm <= 0:
                    error_msg = f"Step {idx+1}: Invalid RPM value (got {rpm}, must be > 0)"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
            else:
                self.logger.debug(f"Step {idx+1}: No RPM specified (rule-based fallback mode)")
            
            # Validate feed rate (LLM should provide this, but optional for rule-based)
            feed_rate = step.get("feed_rate_mm_per_min")
            if feed_rate is not None:
                if not isinstance(feed_rate, (int, float)) or feed_rate <= 0:
                    error_msg = f"Step {idx+1}: Invalid feed_rate_mm_per_min value (got {feed_rate}, must be > 0)"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
            else:
                self.logger.debug(f"Step {idx+1}: No feed_rate_mm_per_min specified (rule-based fallback mode)")
            
            # Operation-specific validation
            if op == "face_milling":
                if depth is None or depth <= 0:
                    error_msg = f"Step {idx+1}: face_milling requires depth_mm > 0"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
            
            elif op == "drilling":
                dia = step.get("diameter_mm")
                pos = step.get("position")
                if dia is None or not isinstance(dia, (int, float)) or dia <= 0:
                    error_msg = f"Step {idx+1}: drilling requires diameter_mm > 0 (got {dia})"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
                if not (isinstance(pos, list) and len(pos) == 2):
                    error_msg = f"Step {idx+1}: drilling requires position [x, y] (got {pos})"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
                if depth is None or depth <= 0:
                    error_msg = f"Step {idx+1}: drilling requires depth_mm > 0"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
        
        is_valid = len(errors) == 0
        if is_valid:
            self.logger.info(f"{validation_type} validation passed")
        else:
            self.logger.warning(f"{validation_type} validation failed with {len(errors)} error(s)")
        
        return (is_valid, errors)
