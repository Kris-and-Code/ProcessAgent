from __future__ import annotations
from typing import Any, Dict
import logging

from ..agents import PlannerAgent, CodeAgent, ValidatorAgent
from .utils import setup_logger, pretty_print_plan

class Orchestrator:
    """Coordinates planner → (validate) → codegen. Adds shared state, logging, error handling."""
    def __init__(self, logger: logging.Logger = None):
        self.planner = PlannerAgent()
        self.coder = CodeAgent()
        self.validator = ValidatorAgent()
        self.logger = logger or setup_logger()
        
    def run(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        state = {}
        self.logger.info("Planning...")
        plan = self.planner.plan_process(spec)
        state["plan"] = [step.model_dump() if hasattr(step, "model_dump") else step for step in plan]
        self.logger.info("Plan created.\n" + pretty_print_plan(state["plan"]))
        self.logger.info("Validating plan...")
        valid, errors = self.validator.validate(state["plan"], None)
        state["valid"] = valid
        state["errors"] = errors
        if not valid:
            self.logger.error(f"Validation failed: {errors}")
            return {"plan": state["plan"], "gcode": None, "valid": False, "errors": errors}
        self.logger.info("Validation passed. Generating code...")
        gcode = self.coder.generate_pseudo_gcode(state["plan"], material=spec.get("material", "unknown"))
        state["gcode"] = gcode
        # Post-gcode validation
        valid2, errors2 = self.validator.validate(state["plan"], gcode)
        state["valid"] = valid2
        state["errors"] = errors2
        if not valid2:
            self.logger.error(f"Validation (post-codegen) failed: {errors2}")
            return {"plan": state["plan"], "gcode": gcode, "valid": False, "errors": errors2}
        self.logger.info("Done.")
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
