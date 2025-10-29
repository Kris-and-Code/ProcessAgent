from __future__ import annotations
from typing import Any, Dict, List

from ..agents import PlannerAgent, CodeAgent, ValidatorAgent
from .schemas import PartSpec, PlanStep, PlanResult


class Orchestrator:
    """Coordinates planner → code generator → validator."""

    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.coder = CodeAgent()
        self.validator = ValidatorAgent()

    def run(self, part_spec: Dict[str, Any] | PartSpec) -> Dict[str, Any]:
        spec = part_spec if isinstance(part_spec, PartSpec) else PartSpec.model_validate(part_spec)
        plan_steps: List[PlanStep] = self.planner.plan_process(spec.model_dump())
        gcode = self.coder.generate_pseudo_gcode([s.model_dump() for s in plan_steps], material=spec.material)
        ok, errors = self.validator.validate([s.model_dump() for s in plan_steps], gcode)
        result = PlanResult(plan=plan_steps, gcode=gcode, valid=ok, errors=errors)
        return result.as_response()
