from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging
from pathlib import Path

from ..core.schemas import PlanStep
from .llm_planner import LLMPlannerAgent


class PlannerAgent:
    """Generates a high-level machining process plan from part specs and goals.

    Uses LLM-powered planning with automatic fallback to rule-based logic.
    The plan is a structured list of operations with parameters including tools, speeds, and feeds.
    """
    
    def __init__(
        self,
        db_path: str | Path | None = None,
        logger: logging.Logger = None,
        use_llm: Optional[bool] = None
    ):
        """Initialize the planner agent with optional logger and LLM configuration.
        
        Args:
            db_path: Path to machining database JSON file
            logger: Optional logger instance
            use_llm: Override LLM usage (None = auto-detect from config)
        """
        self.logger = logger or logging.getLogger("ProcessAgent.PlannerAgent")
        # Use LLM-powered planner (with fallback)
        self.llm_planner = LLMPlannerAgent(db_path=db_path, logger=self.logger, use_llm=use_llm)

    def plan_process(self, part_spec: Dict[str, Any]) -> List[PlanStep]:
        """Generate a machining plan using LLM with fallback to rule-based logic.
        
        Args:
            part_spec: Part specification dictionary with material and optional drill_holes
            
        Returns:
            List of PlanStep objects with operation, parameters, tools, speeds, and feeds
        """
        material = part_spec.get("material", "aluminum_6061")
        holes = part_spec.get("drill_holes") or []
        
        self.logger.info(f"Planning process for material: {material}, holes: {len(holes)}")
        
        # Delegate to LLM planner (which handles fallback internally)
        plan = self.llm_planner.plan_process(part_spec)
        
        self.logger.info(f"Plan generated with {len(plan)} step(s)")
        return plan
