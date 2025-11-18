#!/usr/bin/env python3
"""Test script for FastAPI endpoints."""
import sys
import os
import httpx
import json

# Add project root to path
current = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

API_BASE = "http://127.0.0.1:8000"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing /health endpoint...")
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print(f"✅ Health check passed: {response.json()}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
    except httpx.ConnectError:
        print(f"❌ Cannot connect to API at {API_BASE}")
        print("   Make sure FastAPI is running: uvicorn process_agent.api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_plan_process():
    """Test /plan_process endpoint with goal string."""
    print("\n🔍 Testing /plan_process endpoint...")
    goal = "Prepare drilling operation for aluminum part"
    payload = {"goal": goal}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{API_BASE}/plan_process",
                json=payload
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Plan generation successful!")
                print(f"\n📋 Plan ({len(result.get('plan', []))} steps):")
                for i, step in enumerate(result.get('plan', []), 1):
                    print(f"   {i}. {step.get('operation', 'N/A')} - {step.get('notes', '')}")
                
                print(f"\n🧠 G-Code (first 5 lines):")
                gcode_lines = result.get('gcode', '').split('\n')[:5]
                for line in gcode_lines:
                    print(f"   {line}")
                
                if result.get('valid'):
                    print("\n✅ Validation: PASSED")
                else:
                    print(f"\n❌ Validation: FAILED")
                    print(f"   Errors: {result.get('errors', [])}")
                
                return True
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except httpx.ConnectError:
        print(f"❌ Cannot connect to API at {API_BASE}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_plan_structured():
    """Test /plan endpoint with structured PartSpec."""
    print("\n🔍 Testing /plan endpoint (structured)...")
    payload = {
        "material": "aluminum_6061",
        "drill_holes": [
            {"diameter_mm": 6, "depth_mm": 10, "position": [0, 0]}
        ]
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{API_BASE}/plan",
                json=payload
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Structured plan generation successful!")
                print(f"   Plan has {len(result.get('plan', []))} steps")
                print(f"   Validation: {'PASSED' if result.get('valid') else 'FAILED'}")
                return True
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except httpx.ConnectError:
        print(f"❌ Cannot connect to API at {API_BASE}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 ProcessAgent FastAPI Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Plan Process (Goal)", test_plan_process()))
    results.append(("Plan (Structured)", test_plan_structured()))
    
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

