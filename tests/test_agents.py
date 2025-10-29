from process_agent.agents import PlannerAgent, CodeAgent, ValidatorAgent
from process_agent.core.schemas import OperationType


def test_planner_returns_steps_with_types():
    planner = PlannerAgent()
    plan = planner.plan_process({"material": "aluminum_6061"})
    assert plan and hasattr(plan[0], "operation")
    assert plan[0].operation == OperationType.FACE_MILLING


def test_code_agent_generates_header():
    coder = CodeAgent()
    gcode = coder.generate_pseudo_gcode([
        {"operation": "face_milling", "depth_mm": 0.2}
    ], material="aluminum_6061")
    assert "PSEUDO-GCODE" in gcode and "M30" in gcode


def test_validator_flags_missing_header():
    validator = ValidatorAgent()
    ok, errors = validator.validate([{"operation": "face_milling", "depth_mm": 0.2}], gcode="")
    assert not ok
    assert errors
