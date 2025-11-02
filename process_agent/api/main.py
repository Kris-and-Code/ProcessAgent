from __future__ import annotations
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ..core import Orchestrator, parse_goal_to_spec
from ..core.schemas import PartSpec


app = FastAPI(title="ProcessAgent API", version="0.2.0")
_orchestrator = Orchestrator()


class GoalRequest(BaseModel):
    goal: str = Field(..., description="Natural language machining goal")


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/plan")
async def plan(spec: PartSpec) -> Dict[str, Any]:
    """Plan using structured PartSpec."""
    result = _orchestrator.run(spec.model_dump())
    return result


@app.post("/plan_process")
async def plan_process(request: GoalRequest) -> Dict[str, Any]:
    """Plan using natural language goal string.
    
    Example: {"goal": "Prepare drilling operation for aluminum part"}
    """
    spec = parse_goal_to_spec(request.goal)
    result = _orchestrator.run(spec)
    return result
