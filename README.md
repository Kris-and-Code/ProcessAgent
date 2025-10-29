ProcessAgent
============

Autonomous LLM-based system for machining process planning that outputs a validated plan and pseudo–G-code.

Project Goals
-------------
- Represent machining knowledge (materials, tools, operations) in a simple JSON DB.
- Orchestrate multi-agent planning: planner-> code generator -> validator.
- Expose an API (FastAPI) and a simple UI (Streamlit) for interactive runs.
- Produce pseudo–G-code suitable for early prototyping and iteration.

Getting Started
---------------
1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Run the API

```bash
uvicorn process_agent.api.main:app --reload
```

4) Run the UI

```bash
streamlit run process_agent/ui/app.py
```

5) Run tests

```bash
pytest -q
```

Repository Structure
--------------------
- `data/`: Sample machining DB and example inputs.
- `process_agent/`: Library code (agents, core orchestrator, API, UI).
- `tests/`: Pytest-based unit tests.
- `diagrams/`: Mermaid diagrams.
- `notebooks/`: Jupyter notebooks for exploration.


