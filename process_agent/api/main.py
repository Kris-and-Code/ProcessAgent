from __future__ import annotations
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from ..core import Orchestrator, parse_goal_to_spec
from ..core.schemas import PartSpec, PlanResult


app = FastAPI(
    title="ProcessAgent API",
    version="0.5.0",
    description="""
    **ProcessAgent API** - Autonomous LLM-based system for machining process planning.
    
    This API provides endpoints for generating machining plans and pseudo-G-code from natural language
    goals or structured specifications.
    
    ## Features
    
    - Natural language goal parsing
    - Structured specification support
    - Automatic plan generation
    - G-code generation with material-specific parameters
    - Plan and G-code validation
    
    ## Workflow
    
    1. Submit a goal or structured specification
    2. System generates a machining plan
    3. Plan is validated
    4. G-code is generated from the validated plan
    5. Final validation ensures G-code integrity
    """,
    contact={
        "name": "ProcessAgent Team",
    },
)


_orchestrator = Orchestrator()


class GoalRequest(BaseModel):
    """Request model for natural language goal processing."""
    goal: str = Field(
        ...,
        description="Natural language machining goal",
        examples=[
            "Prepare drilling operation for aluminum part",
            "Face mill steel part with 3 holes",
            "Drill 6mm holes in aluminum workpiece"
        ],
        min_length=1,
        max_length=500
    )
    
    @field_validator("goal")
    @classmethod
    def validate_goal(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Goal cannot be empty or whitespace only")
        return v.strip()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status", examples=["ok"])


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API service is running and healthy.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
async def health() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns the current status of the API service.
    """
    return HealthResponse(status="ok")


@app.post(
    "/plan",
    response_model=PlanResult,
    summary="Generate Plan from Structured Specification",
    description="""
    Generate a machining plan and G-code from a structured PartSpec.
    
    This endpoint accepts a structured specification with material and drill hole parameters.
    The system will:
    1. Generate a machining plan based on the specification
    2. Validate the plan structure
    3. Generate pseudo-G-code
    4. Validate the generated G-code
    
    **Example Request:**
    ```json
    {
        "material": "aluminum_6061",
        "drill_holes": [
            {
                "diameter_mm": 6.0,
                "depth_mm": 10.0,
                "position": [0.0, 0.0]
            }
        ]
    }
    ```
    
    **Example Response:**
    ```json
    {
        "plan": [
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
        ],
        "gcode": "; PSEUDO-GCODE GENERATED\\n...",
        "valid": true,
        "errors": []
    }
    ```
    """,
    responses={
        200: {
            "description": "Plan generated successfully",
        },
        400: {
            "description": "Invalid input specification",
            "content": {
                "application/json": {
                    "example": {"detail": "Validation error: material must be at least 1 character"}
                }
            }
        },
        500: {
            "description": "Internal server error during plan generation",
        }
    }
)
async def plan(spec: PartSpec) -> PlanResult:
    """
    Generate a machining plan from a structured PartSpec.
    
    Args:
        spec: PartSpec containing material and optional drill holes
        
    Returns:
        PlanResult with plan, G-code, validation status, and errors
        
    Raises:
        HTTPException: If plan generation fails
    """
    try:
        result_dict = _orchestrator.run(spec.model_dump())
        return PlanResult(**result_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid specification: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")


@app.post(
    "/plan_process",
    response_model=PlanResult,
    summary="Generate Plan from Natural Language Goal",
    description="""
    Generate a machining plan and G-code from a natural language goal string.
    
    This endpoint parses a natural language description and converts it to a structured
    specification, then generates a plan and G-code.
    
    **Supported Materials:**
    - `aluminum` / `aluminium` → aluminum_6061
    - `steel` → steel_1018
    
    **Supported Operations:**
    - `drill` / `drilling` → generates drilling operations
    
    **Example Request:**
    ```json
    {
        "goal": "Prepare drilling operation for aluminum part"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "plan": [
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
        ],
        "gcode": "; PSEUDO-GCODE GENERATED\\n...",
        "valid": true,
        "errors": []
    }
    ```
    """,
    responses={
        200: {
            "description": "Plan generated successfully from natural language goal",
        },
        400: {
            "description": "Invalid goal string",
            "content": {
                "application/json": {
                    "example": {"detail": "Goal cannot be empty or whitespace only"}
                }
            }
        },
        500: {
            "description": "Internal server error during plan generation",
        }
    }
)
async def plan_process(request: GoalRequest) -> PlanResult:
    """
    Generate a machining plan from a natural language goal.
    
    Args:
        request: GoalRequest containing the natural language goal string
        
    Returns:
        PlanResult with plan, G-code, validation status, and errors
        
    Raises:
        HTTPException: If goal parsing or plan generation fails
    """
    try:
        spec = parse_goal_to_spec(request.goal)
        result_dict = _orchestrator.run(spec)
        return PlanResult(**result_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid goal: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")
