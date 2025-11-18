#!/usr/bin/env python3
"""Test script for LLM-powered planner with multiple prompts."""
from __future__ import annotations
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from process_agent.core import Orchestrator
from process_agent.core.utils import setup_logger, pretty_print_plan


def test_llm_planner():
    """Test LLM planner with various scenarios."""
    logger = setup_logger()
    orch = Orchestrator(logger=logger)
    
    print("=" * 80)
    print("Testing LLM-Powered PlannerAgent")
    print("=" * 80)
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Simple Aluminum Drilling",
            "spec": {
                "material": "aluminum_6061",
                "drill_holes": [
                    {"diameter_mm": 6.0, "depth_mm": 10.0, "position": [0.0, 0.0]}
                ]
            }
        },
        {
            "name": "Steel with Multiple Holes",
            "spec": {
                "material": "steel_1018",
                "drill_holes": [
                    {"diameter_mm": 3.0, "depth_mm": 5.0, "position": [10.0, 10.0]},
                    {"diameter_mm": 6.0, "depth_mm": 10.0, "position": [20.0, 20.0]}
                ]
            }
        },
        {
            "name": "Aluminum Face Milling Only",
            "spec": {
                "material": "aluminum_6061",
                "drill_holes": None
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"Input: {test_case['spec']}")
        print()
        
        try:
            result = orch.run(test_case['spec'])
            
            print("Plan:")
            print(pretty_print_plan(result['plan']))
            print()
            
            # Check if LLM was used (plan steps should have tool, rpm, feed_rate)
            if result['plan']:
                first_step = result['plan'][0]
                has_llm_fields = all(key in first_step for key in ['tool', 'rpm', 'feed_rate_mm_per_min'])
                if has_llm_fields:
                    print("✅ LLM fields detected (tool, rpm, feed_rate_mm_per_min)")
                else:
                    print("⚠️  Using rule-based fallback (missing LLM fields)")
            
            print(f"Validation: {'✅ PASSED' if result['valid'] else '❌ FAILED'}")
            if result['errors']:
                print(f"Errors: {result['errors']}")
            
            print(f"\nG-code ({len(result['gcode'].split(chr(10)))} lines):")
            print(result['gcode'][:500] + "..." if len(result['gcode']) > 500 else result['gcode'])
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Testing Complete")
    print("=" * 80)


if __name__ == "__main__":
    test_llm_planner()



