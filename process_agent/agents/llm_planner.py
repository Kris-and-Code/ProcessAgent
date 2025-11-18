"""LLM-powered planning agent with structured output and fallback logic."""
from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain_core.exceptions import LangChainException
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    ChatPromptTemplate = None
    PydanticOutputParser = None
    LangChainException = Exception

from ..core.schemas import PlanStep, OperationType
from ..core.llm_config import get_llm_config
from ..core.utils import load_json_file


class LLMPlannerAgent:
    """LLM-powered planner agent with structured output and fallback to rule-based logic."""
    
    def __init__(
        self,
        db_path: str | Path | None = None,
        logger: logging.Logger = None,
        use_llm: Optional[bool] = None
    ):
        """Initialize the LLM planner agent.
        
        Args:
            db_path: Path to machining database JSON file
            logger: Optional logger instance
            use_llm: Override LLM usage (None = auto-detect from config)
        """
        self.logger = logger or logging.getLogger("ProcessAgent.LLMPlannerAgent")
        self.db_path = Path(db_path) if db_path else Path(__file__).parents[2] / "data" / "machining_db.json"
        
        # Load machining database
        try:
            self.db: Dict[str, Any] = load_json_file(self.db_path)
            self.logger.info(f"Loaded machining database from {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to load machining database: {str(e)}")
            self.db = {"materials": {}, "tools": {}, "operations": {}}
        
        # LLM configuration
        self.config = get_llm_config()
        self.use_llm = use_llm if use_llm is not None else self.config.is_available
        
        # Initialize LLM if available
        self.llm = None
        if self.use_llm and LANGCHAIN_AVAILABLE:
            try:
                if self.config.api_key:
                    self.llm = ChatOpenAI(
                        model=self.config.model,
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                        timeout=self.config.timeout,
                        api_key=self.config.api_key
                    )
                    self.logger.info(f"LLM initialized: {self.config.model}")
                else:
                    self.logger.warning("LLM API key not found, falling back to rule-based planning")
                    self.use_llm = False
            except Exception as e:
                self.logger.warning(f"Failed to initialize LLM: {str(e)}, falling back to rule-based planning")
                self.use_llm = False
        elif self.use_llm and not LANGCHAIN_AVAILABLE:
            self.logger.warning("LangChain not available, falling back to rule-based planning")
            self.use_llm = False
    
    def _create_planning_prompt(self, part_spec: Dict[str, Any]) -> str:
        """Create the planning prompt for the LLM."""
        material = part_spec.get("material", "aluminum_6061")
        drill_holes = part_spec.get("drill_holes", [])
        
        # Get available materials, tools, and operations from DB
        materials_info = json.dumps(self.db.get("materials", {}), indent=2)
        tools_info = json.dumps(self.db.get("tools", {}), indent=2)
        operations_info = json.dumps(self.db.get("operations", {}), indent=2)
        
        # Build drill holes description
        holes_desc = ""
        if drill_holes:
            holes_desc = "\nDrill holes to create:\n"
            for i, hole in enumerate(drill_holes, 1):
                holes_desc += f"  {i}. Diameter: {hole.get('diameter_mm')}mm, Depth: {hole.get('depth_mm')}mm, Position: {hole.get('position')}\n"
        else:
            holes_desc = "\nNo specific drill holes specified."
        
        prompt = f"""You are an expert CNC machining process planner. Your task is to generate a structured machining plan based on the given specifications.

**Part Specification:**
- Material: {material}
{holes_desc}

**Available Machining Database:**

Materials:
{materials_info}

Tools:
{tools_info}

Operations:
{operations_info}

**Instructions:**
1. Analyze the part specification and determine the required machining operations.
2. For face milling: Always start with a face milling operation to prepare the surface. Use appropriate tool, RPM, and feed rate from the database based on the material.
3. For drilling: Create drilling operations for each specified hole. Select the appropriate drill tool based on hole diameter, and use material-specific RPM and feed rates.
4. Select tools, RPM, and feed rates from the available database based on the material and operation type.
5. Ensure all operations are in logical sequence (face milling first, then drilling).
6. Provide clear notes explaining each step.

**Output Format:**
Return a JSON array of plan steps. Each step must include:
- operation: "face_milling" or "drilling"
- depth_mm: depth in millimeters (required for face_milling, typically 0.2mm)
- diameter_mm: hole diameter (required for drilling)
- position: [x, y] coordinates (required for drilling)
- tool: tool identifier from database (e.g., "endmill_6mm", "drill_6mm")
- rpm: spindle speed in RPM (from material database)
- feed_rate_mm_per_min: feed rate in mm/min (from material database)
- notes: brief description of the operation

**Example Output:**
[
  {{
    "operation": "face_milling",
    "depth_mm": 0.2,
    "tool": "endmill_6mm",
    "rpm": 12000,
    "feed_rate_mm_per_min": 800,
    "notes": "Face top surface for {material}"
  }},
  {{
    "operation": "drilling",
    "diameter_mm": 6.0,
    "depth_mm": 10.0,
    "position": [0.0, 0.0],
    "tool": "drill_6mm",
    "rpm": 12000,
    "feed_rate_mm_per_min": 800,
    "notes": "Drill 6mm hole at position [0, 0]"
  }}
]

Generate the plan now:"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into plan steps."""
        try:
            # Try to extract JSON from response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse JSON
            plan_data = json.loads(response)
            
            # Ensure it's a list
            if not isinstance(plan_data, list):
                plan_data = [plan_data]
            
            return plan_data
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            self.logger.debug(f"Response content: {response[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
    
    def _validate_and_fix_plan_step(self, step_data: Dict[str, Any], material: str) -> Dict[str, Any]:
        """Validate and fix a plan step, adding defaults from database if needed."""
        # Ensure operation is valid
        op = step_data.get("operation", "").lower()
        if op not in ["face_milling", "drilling"]:
            raise ValueError(f"Invalid operation: {op}")
        
        # Get material parameters
        materials = self.db.get("materials", {})
        material_data = materials.get(material, {})
        default_rpm = material_data.get("recommended_rpm", 1000)
        default_feed = material_data.get("recommended_feed_mm_per_min", 100)
        
        # Fix face_milling
        if op == "face_milling":
            if "depth_mm" not in step_data or step_data["depth_mm"] is None:
                step_data["depth_mm"] = 0.2
            if "tool" not in step_data or not step_data["tool"]:
                step_data["tool"] = "endmill_6mm"  # Default from operations
            if "rpm" not in step_data or step_data["rpm"] is None:
                step_data["rpm"] = default_rpm
            if "feed_rate_mm_per_min" not in step_data or step_data["feed_rate_mm_per_min"] is None:
                step_data["feed_rate_mm_per_min"] = default_feed
        
        # Fix drilling
        elif op == "drilling":
            if "diameter_mm" not in step_data or step_data["diameter_mm"] is None:
                raise ValueError("Drilling operation requires diameter_mm")
            if "depth_mm" not in step_data or step_data["depth_mm"] is None:
                raise ValueError("Drilling operation requires depth_mm")
            if "position" not in step_data or not step_data["position"]:
                raise ValueError("Drilling operation requires position")
            if "tool" not in step_data or not step_data["tool"]:
                # Auto-select tool based on diameter
                dia = step_data["diameter_mm"]
                tools = self.db.get("tools", {})
                preferred_key = f"drill_{int(dia)}mm"
                if preferred_key not in tools:
                    # Find closest match
                    candidates = [(k, v.get("diameter_mm", 0)) for k, v in tools.items() 
                                 if v.get("type") == "drill" and isinstance(v.get("diameter_mm"), (int, float))]
                    if candidates:
                        closest_key, _ = min(candidates, key=lambda kv: abs(kv[1] - dia))
                        step_data["tool"] = closest_key
                    else:
                        step_data["tool"] = "drill_3mm"  # Fallback
                else:
                    step_data["tool"] = preferred_key
            if "rpm" not in step_data or step_data["rpm"] is None:
                step_data["rpm"] = default_rpm
            if "feed_rate_mm_per_min" not in step_data or step_data["feed_rate_mm_per_min"] is None:
                step_data["feed_rate_mm_per_min"] = default_feed
        
        return step_data
    
    def _llm_plan_process(self, part_spec: Dict[str, Any]) -> List[PlanStep]:
        """Generate plan using LLM."""
        if not self.llm:
            raise RuntimeError("LLM not initialized")
        
        self.logger.info("Using LLM to generate machining plan...")
        
        try:
            # Create prompt
            prompt_text = self._create_planning_prompt(part_spec)
            
            # Call LLM
            self.logger.debug("Sending request to LLM...")
            response = self.llm.invoke(prompt_text)
            
            # Extract content
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            self.logger.debug(f"LLM response received ({len(content)} chars)")
            
            # Parse response
            plan_data = self._parse_llm_response(content)
            
            # Validate and fix each step
            material = part_spec.get("material", "aluminum_6061")
            validated_steps = []
            for idx, step_data in enumerate(plan_data):
                try:
                    fixed_step = self._validate_and_fix_plan_step(step_data, material)
                    validated_steps.append(fixed_step)
                except Exception as e:
                    self.logger.warning(f"Step {idx+1} validation failed: {str(e)}, skipping")
            
            # Convert to PlanStep objects
            plan_steps = []
            for step_data in validated_steps:
                try:
                    plan_step = PlanStep(**step_data)
                    plan_steps.append(plan_step)
                except Exception as e:
                    self.logger.warning(f"Failed to create PlanStep: {str(e)}")
            
            if not plan_steps:
                raise ValueError("No valid plan steps generated from LLM")
            
            self.logger.info(f"LLM generated {len(plan_steps)} plan step(s)")
            return plan_steps
            
        except LangChainException as e:
            self.logger.error(f"LangChain error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"LLM planning failed: {str(e)}", exc_info=True)
            raise
    
    def _rule_based_plan_process(self, part_spec: Dict[str, Any]) -> List[PlanStep]:
        """Fallback rule-based planning (original logic)."""
        self.logger.info("Using rule-based planning (fallback)...")
        
        material = part_spec.get("material", "aluminum_6061")
        holes = part_spec.get("drill_holes") or []
        
        # Get material parameters
        materials = self.db.get("materials", {})
        material_data = materials.get(material, {})
        rpm = material_data.get("recommended_rpm", 1000)
        feed = material_data.get("recommended_feed_mm_per_min", 100)
        
        # Get default tools
        operations = self.db.get("operations", {})
        face_mill_tool = operations.get("face_milling", {}).get("default_tool", "endmill_6mm")
        
        plan: List[PlanStep] = [
            PlanStep(
                operation=OperationType.FACE_MILLING,
                depth_mm=0.2,
                tool=face_mill_tool,
                rpm=rpm,
                feed_rate_mm_per_min=feed,
                notes=f"Face top surface for {material}",
            )
        ]
        
        for idx, hole in enumerate(holes):
            diameter = hole.get("diameter_mm", 3.0)
            depth = hole.get("depth_mm", 5.0)
            position = hole.get("position", [0.0, 0.0])
            
            if diameter <= 0 or depth <= 0:
                self.logger.warning(f"Hole {idx+1}: Invalid parameters, using defaults")
                diameter = max(diameter, 3.0)
                depth = max(depth, 5.0)
            
            # Select tool
            tools = self.db.get("tools", {})
            tool_key = f"drill_{int(diameter)}mm"
            if tool_key not in tools:
                # Find closest
                candidates = [(k, v.get("diameter_mm", 0)) for k, v in tools.items() 
                             if v.get("type") == "drill" and isinstance(v.get("diameter_mm"), (int, float))]
                if candidates:
                    tool_key, _ = min(candidates, key=lambda kv: abs(kv[1] - diameter))
                else:
                    tool_key = "drill_3mm"
            
            plan.append(
                PlanStep(
                    operation=OperationType.DRILLING,
                    diameter_mm=diameter,
                    depth_mm=depth,
                    position=position,
                    tool=tool_key,
                    rpm=rpm,
                    feed_rate_mm_per_min=feed,
                )
            )
        
        self.logger.info(f"Rule-based plan generated with {len(plan)} step(s)")
        return plan
    
    def plan_process(self, part_spec: Dict[str, Any]) -> List[PlanStep]:
        """Generate machining plan using LLM with fallback to rule-based logic.
        
        Args:
            part_spec: Part specification dictionary
            
        Returns:
            List of PlanStep objects
        """
        # Try LLM first if enabled
        if self.use_llm and self.llm:
            try:
                return self._llm_plan_process(part_spec)
            except Exception as e:
                self.logger.warning(f"LLM planning failed: {str(e)}, falling back to rule-based logic")
                # Fall through to rule-based
        
        # Fallback to rule-based
        return self._rule_based_plan_process(part_spec)



