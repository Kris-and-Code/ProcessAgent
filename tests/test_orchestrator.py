from process_agent.core import Orchestrator


def test_orchestrator_flow_validates():
    orch = Orchestrator()
    result = orch.run({"material": "aluminum_6061"})
    assert result["valid"] is True
    assert "gcode" in result and isinstance(result["gcode"], str)
    assert isinstance(result["plan"], list)
    assert isinstance(result["plan"][0], dict)
