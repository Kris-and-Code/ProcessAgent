from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class OperationType(str, Enum):
    """Supported machining operations."""
    FACE_MILLING = "face_milling"
    DRILLING = "drilling"


class DrillHole(BaseModel):
    """Specification for a single drill hole."""
    diameter_mm: float = Field(
        ...,
        gt=0,
        description="Hole diameter in millimeters",
        examples=[6.0, 3.0, 8.0],
        json_schema_extra={"minimum": 0.1, "maximum": 100.0}
    )
    depth_mm: float = Field(
        ...,
        gt=0,
        description="Hole depth in millimeters",
        examples=[10.0, 5.0, 20.0],
        json_schema_extra={"minimum": 0.1, "maximum": 500.0}
    )
    position: list[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Hole position as [x, y] coordinates in millimeters",
        examples=[[0.0, 0.0], [10.0, 20.0], [50.0, 30.0]],
        json_schema_extra={"minItems": 2, "maxItems": 2}
    )
    
    @field_validator("position")
    @classmethod
    def validate_position(cls, v: list[float]) -> list[float]:
        """Validate position coordinates."""
        if len(v) != 2:
            raise ValueError("Position must have exactly 2 coordinates [x, y]")
        if not all(isinstance(coord, (int, float)) for coord in v):
            raise ValueError("Position coordinates must be numbers")
        return v


class PartSpec(BaseModel):
    """Input specification for machining process planning."""
    material: str = Field(
        default="aluminum_6061",
        min_length=1,
        max_length=100,
        description="Material identifier (e.g., 'aluminum_6061', 'steel_1018')",
        examples=["aluminum_6061", "steel_1018"],
    )
    drill_holes: Optional[list[DrillHole]] = Field(
        default=None,
        description="Optional list of drill holes to be machined",
        examples=[
            [{"diameter_mm": 6.0, "depth_mm": 10.0, "position": [0.0, 0.0]}],
            [
                {"diameter_mm": 3.0, "depth_mm": 5.0, "position": [10.0, 10.0]},
                {"diameter_mm": 6.0, "depth_mm": 10.0, "position": [20.0, 20.0]}
            ]
        ]
    )
    
    @field_validator("material")
    @classmethod
    def validate_material(cls, v: str) -> str:
        """Validate material identifier."""
        if not v or not v.strip():
            raise ValueError("Material cannot be empty or whitespace only")
        return v.strip()


class PlanStep(BaseModel):
    """A single step in the machining plan."""
    operation: OperationType = Field(
        ...,
        description="Type of machining operation",
        examples=["face_milling", "drilling"]
    )
    depth_mm: Optional[float] = Field(
        default=None,
        gt=0,
        description="Cutting depth in millimeters (required for face_milling, optional for drilling)",
        examples=[0.2, 5.0, 10.0],
        json_schema_extra={"minimum": 0.01, "maximum": 500.0}
    )
    diameter_mm: Optional[float] = Field(
        default=None,
        gt=0,
        description="Hole diameter in millimeters (required for drilling operations)",
        examples=[3.0, 6.0, 8.0],
        json_schema_extra={"minimum": 0.1, "maximum": 100.0}
    )
    position: Optional[list[float]] = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Position coordinates [x, y] in millimeters (required for drilling)",
        examples=[[0.0, 0.0], [10.0, 20.0]],
        json_schema_extra={"minItems": 2, "maxItems": 2}
    )
    tool: Optional[str] = Field(
        default=None,
        description="Tool identifier from machining database (e.g., 'endmill_6mm', 'drill_6mm')",
        examples=["endmill_6mm", "drill_3mm", "drill_6mm"]
    )
    rpm: Optional[int] = Field(
        default=None,
        gt=0,
        description="Spindle speed in RPM (revolutions per minute)",
        examples=[12000, 6000, 8000],
        json_schema_extra={"minimum": 100, "maximum": 50000}
    )
    feed_rate_mm_per_min: Optional[float] = Field(
        default=None,
        gt=0,
        description="Feed rate in millimeters per minute",
        examples=[800.0, 300.0, 500.0],
        json_schema_extra={"minimum": 1.0, "maximum": 10000.0}
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional notes or comments about this step",
        examples=["Face top surface for aluminum_6061", "Drill mounting hole"]
    )
    
    @field_validator("position")
    @classmethod
    def validate_position(cls, v: Optional[list[float]]) -> Optional[list[float]]:
        """Validate position coordinates if provided."""
        if v is None:
            return v
        if len(v) != 2:
            raise ValueError("Position must have exactly 2 coordinates [x, y]")
        if not all(isinstance(coord, (int, float)) for coord in v):
            raise ValueError("Position coordinates must be numbers")
        return v


class PlanResult(BaseModel):
    """Complete result of the planning process."""
    plan: list[PlanStep] = Field(
        ...,
        description="List of machining plan steps",
        min_length=0,
        examples=[
            [
                {
                    "operation": "face_milling",
                    "depth_mm": 0.2,
                    "notes": "Face top surface for aluminum_6061"
                },
                {
                    "operation": "drilling",
                    "diameter_mm": 6.0,
                    "depth_mm": 10.0,
                    "position": [0.0, 0.0]
                }
            ]
        ]
    )
    gcode: str = Field(
        ...,
        description="Generated pseudo-G-code string",
        min_length=0,
        examples=["; PSEUDO-GCODE GENERATED\nG90 G21\nM03 S12000\n..."]
    )
    valid: bool = Field(
        ...,
        description="Whether the plan and G-code passed validation",
        examples=[True, False]
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors (empty if valid=True)",
        examples=[[], ["G-code missing header or terminator"]]
    )
    
    @field_validator("errors")
    @classmethod
    def validate_errors(cls, v: list[str]) -> list[str]:
        """Ensure errors list is empty when valid is True."""
        # Note: This validation would need access to the parent model
        # For now, we'll just ensure it's a list of strings
        if not isinstance(v, list):
            raise ValueError("Errors must be a list")
        if not all(isinstance(e, str) for e in v):
            raise ValueError("All errors must be strings")
        return v

    def as_response(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return self.model_dump()
