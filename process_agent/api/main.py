from __future__ import annotations
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ..core import Orchestrator
from ..core.schemas import PartSpec


app = FastAPI(title="ProcessAgent API", version="0.2.0")
_orchestrator = Orchestrator()


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/plan")
async def plan(spec: PartSpec) -> Dict[str, Any]:
    result = _orchestrator.run(spec)
    return result
