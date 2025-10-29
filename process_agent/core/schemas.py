from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, conlist, confloat, constr


class OperationType(str, Enum):
    FACE_MILLING = "face_milling"
    DRILLING = "drilling"


class DrillHole(BaseModel):
    diameter_mm: confloat(gt=0) = Field(..., description="Hole diameter in mm")
    depth_mm: confloat(gt=0) = Field(..., description="Hole depth in mm")
    position: conlist(confloat(), min_items=2, max_items=2) = Field(
        ..., description="[x, y] in mm"
    )


class PartSpec(BaseModel):
    material: constr(strip_whitespace=True, min_length=1) = Field(
        default="aluminum_6061"
    )
    drill_holes: Optional[List[DrillHole]] = Field(default=None)


class PlanStep(BaseModel):
    operation: OperationType
    depth_mm: Optional[confloat(gt=0)] = None
    diameter_mm: Optional[confloat(gt=0)] = None
    position: Optional[conlist(confloat(), min_items=2, max_items=2)] = None
    notes: Optional[str] = None


class PlanResult(BaseModel):
    plan: List[PlanStep]
    gcode: str
    valid: bool
    errors: List[str] = []

    def as_response(self) -> dict[str, Any]:
        return self.model_dump()
