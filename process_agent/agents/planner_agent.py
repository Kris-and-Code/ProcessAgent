from __future__ import annotations
from typing import Any, Dict, List

from ..core.schemas import PlanStep, OperationType


class PlannerAgent:
    """Generates a high-level machining process plan from part specs and goals.

    The plan is a structured list of operations with parameters.
    """

    def plan_process(self, part_spec: Dict[str, Any]) -> List[PlanStep]:
        """Return a simple plan based on input.

        Day 2: emits typed PlanStep models.
        """
        material = part_spec.get("material", "aluminum_6061")
        plan: List[PlanStep] = [
            PlanStep(
                operation=OperationType.FACE_MILLING,
                depth_mm=0.2,
                notes=f"Face top surface for {material}",
            )
        ]
        holes = part_spec.get("drill_holes") or []
        for hole in holes:
            plan.append(
                PlanStep(
                    operation=OperationType.DRILLING,
                    diameter_mm=hole.get("diameter_mm", 3.0),
                    depth_mm=hole.get("depth_mm", 5.0),
                    position=hole.get("position", [0.0, 0.0]),
                )
            )
        return plan
