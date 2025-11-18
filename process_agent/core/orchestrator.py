from __future__ import annotations
from typing import Any, Dict, Optional
import logging
from pathlib import Path

from ..agents import PlannerAgent, CodeAgent, ValidatorAgent
from .utils import setup_logger, pretty_print_plan

class Orchestrator:
    """Coordinates planner → (validate) → codegen. Adds shared state, logging, error handling."""
    def __init__(
        self,
        logger: logging.Logger = None,
        db_path: str | Path | None = None,
        use_llm: Optional[bool] = None
    ):
        """Initialize orchestrator with optional database path and LLM configuration.
        
        Args:
            logger: Optional logger instance
            db_path: Path to machining database JSON file
            use_llm: Override LLM usage for planner (None = auto-detect from config)
        """
        self.logger = logger or setup_logger()
        # Pass DB path to planner so it can access tools, materials, operations
        self.planner = PlannerAgent(db_path=db_path, logger=self.logger, use_llm=use_llm)
        self.coder = CodeAgent(db_path=db_path, logger=self.logger)
        self.validator = ValidatorAgent(logger=self.logger)
        
    def run(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete planning workflow."""
        state = {}
        material = spec.get("material", "unknown")
        drill_holes_count = len(spec.get("drill_holes", []))
        
        self.logger.info(f"Starting planning workflow for material: {material}, drill_holes: {drill_holes_count}")
        
        # Step 1: Planning
        try:
            self.logger.info("Step 1/4: Planning process...")
            plan = self.planner.plan_process(spec)
            state["plan"] = [step.model_dump() if hasattr(step, "model_dump") else step for step in plan]
            self.logger.info(f"Plan created with {len(state['plan'])} step(s).\n{pretty_print_plan(state['plan'])}")
        except Exception as e:
            self.logger.error(f"Planning failed: {str(e)}", exc_info=True)
            return {"plan": [], "gcode": None, "valid": False, "errors": [f"Planning error: {str(e)}"]}
        
        # Step 2: Pre-codegen validation
        try:
            self.logger.info("Step 2/4: Validating plan structure...")
            valid, errors = self.validator.validate(state["plan"], None)
            state["valid"] = valid
            state["errors"] = errors
            if not valid:
                self.logger.warning(f"Plan validation failed with {len(errors)} error(s): {errors}")
                return {"plan": state["plan"], "gcode": None, "valid": False, "errors": errors}
            self.logger.info("Plan validation passed.")
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}", exc_info=True)
            return {"plan": state["plan"], "gcode": None, "valid": False, "errors": [f"Validation error: {str(e)}"]}
        
        # Step 3: Code generation
        try:
            self.logger.info("Step 3/4: Generating G-code...")
            gcode = self.coder.generate_pseudo_gcode(state["plan"], material=material)
            state["gcode"] = gcode
            gcode_lines = len(gcode.split("\n"))
            self.logger.info(f"G-code generated successfully ({gcode_lines} lines)")
        except ValueError as e:
            self.logger.error(f"G-code generation failed (material/tool error): {str(e)}")
            return {"plan": state["plan"], "gcode": None, "valid": False, "errors": [f"G-code generation error: {str(e)}"]}
        except Exception as e:
            self.logger.error(f"G-code generation failed: {str(e)}", exc_info=True)
            return {"plan": state["plan"], "gcode": None, "valid": False, "errors": [f"G-code generation error: {str(e)}"]}
        
        # Step 4: Post-codegen validation
        try:
            self.logger.info("Step 4/4: Validating generated G-code...")
            valid2, errors2 = self.validator.validate(state["plan"], gcode)
            state["valid"] = valid2
            state["errors"] = errors2
            if not valid2:
                self.logger.warning(f"G-code validation failed with {len(errors2)} error(s): {errors2}")
                return {"plan": state["plan"], "gcode": gcode, "valid": False, "errors": errors2}
            self.logger.info("G-code validation passed. Workflow completed successfully.")
        except Exception as e:
            self.logger.error(f"G-code validation error: {str(e)}", exc_info=True)
            return {"plan": state["plan"], "gcode": gcode, "valid": False, "errors": [f"G-code validation error: {str(e)}"]}
        
        return {
            "plan": state["plan"],
            "gcode": gcode,
            "valid": True,
            "errors": [],
        }

# Optional CLI demo for stand-alone run
if __name__ == "__main__":
    orch = Orchestrator()
    # Example: Drilling aluminum part
    input_spec = {"material": "aluminum_6061", "drill_holes": [{"diameter_mm": 6, "depth_mm": 10, "position": [0,0]}]}
    result = orch.run(input_spec)
    print("PLAN:")
    print(pretty_print_plan(result["plan"]))
    print("\nG-CODE:")
    print(result["gcode"])
    if not result["valid"]:
        print("\nValidation errors:", result["errors"])
