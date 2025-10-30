from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class OperationType(str, Enum):
    FACE_MILLING = "face_milling"
    DRILLING = "drilling"


class DrillHole(BaseModel):
    diameter_mm: float = Field(..., gt=0, description="Hole diameter in mm")
    depth_mm: float = Field(..., gt=0, description="Hole depth in mm")
    position: list[float] = Field(
        ..., min_length=2, max_length=2, description="[x, y] in mm"
    )


class PartSpec(BaseModel):
    material: str = Field(default="aluminum_6061", min_length=1)
    drill_holes: Optional[list[DrillHole]] = Field(default=None)


class PlanStep(BaseModel):
    operation: OperationType
    depth_mm: Optional[float] = Field(default=None, gt=0)
    diameter_mm: Optional[float] = Field(default=None, gt=0)
    position: Optional[list[float]] = Field(default=None, min_length=2, max_length=2)
    notes: Optional[str] = None


class PlanResult(BaseModel):
    plan: list[PlanStep]
    gcode: str
    valid: bool
    errors: list[str] = []

    def as_response(self) -> dict[str, Any]:
        return self.model_dump()
