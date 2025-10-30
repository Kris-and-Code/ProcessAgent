import sys
import os
current = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
from process_agent.core.orchestrator import Orchestrator
from process_agent.core.utils import pretty_print_plan, setup_logger

def get_user_spec():
    print("Enter machining operation (example: drilling):", end=" ")
    operation = input().strip().lower() or "drilling"
    print("Select material (aluminum_6061, steel_1018, titanium):", end=" ")
    material = input().strip() or "aluminum_6061"
    print("Enter hole diameter (mm):", end=" ")
    try:
        dia = float(input().strip() or 6)
    except Exception:
        dia = 6.0
    print("Enter hole depth (mm):", end=" ")
    try:
        depth = float(input().strip() or 10)
    except Exception:
        depth = 10.0
    print("Enter position as X Y (e.g., 0 0):", end=" ")
    try:
        pos = list(map(float, input().strip().split()))
        if len(pos) != 2: pos = [0,0]
    except Exception:
        pos = [0, 0]
    spec = {
        "material": material,
        "drill_holes": [{"diameter_mm": dia, "depth_mm": depth, "position": pos}] if operation == "drilling" else [],
    }
    return spec

def run_and_print(orch, label, spec):
    print("\n===", label, "===")
    result = orch.run(spec)
    print("PLAN:")
    print(pretty_print_plan(result["plan"]))
    print("\nG-CODE:")
    print(result["gcode"])
    if not result["valid"]:
        print("\nValidation errors:", result["errors"])

def main():
    logger = setup_logger()
    orch = Orchestrator(logger)
    print("--- ProcessAgent CLI Demo ---")
    userspec = get_user_spec()
    run_and_print(orch, "User Input Run", userspec)
    # Show an error case
    print("\n\nRunning error demo (titanium)...")
    titanium_spec = {"material": "titanium", "drill_holes": [{"diameter_mm": 6, "depth_mm": 10, "position": [0,0]}]}
    run_and_print(orch, "Titanium Error Demo", titanium_spec)

if __name__ == "__main__":
    main()
