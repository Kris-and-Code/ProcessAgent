# Testing Guide for ProcessAgent

This guide shows you how to test the FastAPI and Streamlit interfaces.

## Prerequisites

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Ensure dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

## Testing FastAPI

### Step 1: Start the FastAPI Server

In one terminal:
```bash
cd /home/krish007/LLM/ProcessAgent
source venv/bin/activate
uvicorn process_agent.api.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Run the Test Script

In another terminal:
```bash
cd /home/krish007/LLM/ProcessAgent
source venv/bin/activate
python scripts/test_fastapi.py
```

### Step 3: Test Manually with curl

**Health Check:**
```bash
curl http://127.0.0.1:8000/health
```

**Plan Process (Goal String):**
```bash
curl -X POST http://127.0.0.1:8000/plan_process \
  -H "Content-Type: application/json" \
  -d '{"goal": "Prepare drilling operation for aluminum part"}'
```

**Plan (Structured):**
```bash
curl -X POST http://127.0.0.1:8000/plan \
  -H "Content-Type: application/json" \
  -d '{"material": "aluminum_6061", "drill_holes": [{"diameter_mm": 6, "depth_mm": 10, "position": [0, 0]}]}'
```

### Step 4: Use Swagger UI

Open in browser: `http://127.0.0.1:8000/docs`

You can test all endpoints interactively through the Swagger interface.

## Testing Streamlit

### Step 1: Start Streamlit

```bash
cd /home/krish007/LLM/ProcessAgent
source venv/bin/activate
streamlit run process_agent/ui/app.py
```

Or use the test script:
```bash
./scripts/test_streamlit.sh
```

### Step 2: Test the UI

1. Open the browser (usually `http://localhost:8501`)
2. Enter goal: `Prepare drilling operation for aluminum part`
3. Select material: `Aluminum 6061`
4. Click **Generate Plan**
5. Verify:
   - ✅ Plan section shows steps
   - ✅ G-CODE OUTPUT section shows generated code
   - ✅ Validation status shows "✅ Validation passed"

### Expected Output

**Plan Section:**
```
Step 1: Face Milling — Face top surface for aluminum_6061, depth=0.2mm
Step 2: Drilling, diameter=6.0mm, depth=10.0mm, position=[0.0, 0.0]
```

**G-Code Section:**
```
; PSEUDO-GCODE GENERATED
; MATERIAL: aluminum_6061
G90 ; absolute positioning
...
M30 ; program end
```

## Quick Test Commands

```bash
# FastAPI (in separate terminal)
uvicorn process_agent.api.main:app --reload &

# Run tests
python scripts/test_fastapi.py

# Streamlit
streamlit run process_agent/ui/app.py
```

## Troubleshooting

- **Connection refused**: Make sure FastAPI/Streamlit is running
- **Module not found**: Activate venv and ensure dependencies are installed
- **Port already in use**: Change port with `--port 8001` (FastAPI) or `streamlit run ... --server.port 8502` (Streamlit)

