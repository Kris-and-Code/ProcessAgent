# ProcessAgent - Comprehensive Project Overview

## 📋 Table of Contents
1. [Executive Summary](#executive-summary)
2. [Project Vision & Goals](#project-vision--goals)
3. [System Architecture](#system-architecture)
4. [Implementation Timeline](#implementation-timeline)
5. [Core Components](#core-components)
6. [Technical Stack](#technical-stack)
7. [Data Model & Knowledge Base](#data-model--knowledge-base)
8. [Workflow & Process Flow](#workflow--process-flow)
9. [API Endpoints](#api-endpoints)
10. [User Interface](#user-interface)
11. [Current Capabilities](#current-capabilities)
12. [Testing & Quality Assurance](#testing--quality-assurance)
13. [Project Structure](#project-structure)
14. [Future Roadmap](#future-roadmap)

---

## 🎯 Executive Summary

**ProcessAgent** is an autonomous, multi-agent LLM-based system designed to automate machining process planning and generate pseudo-G-code for CNC machining operations. The project was developed over 4 days with a focus on modularity, extensibility, and user-friendliness.

**Key Achievement**: A fully functional system that accepts natural language goals (e.g., "Prepare drilling operation for aluminum part") and produces validated machining plans with corresponding pseudo-G-code, accessible through both REST API and interactive web UI.

---

## 🎯 Project Vision & Goals

### Primary Objectives
1. **Automate Process Planning**: Transform high-level machining goals into detailed, structured process plans
2. **Generate Pseudo-G-code**: Produce machine-readable (but not machine-ready) G-code for prototyping and iteration
3. **Multi-Agent Architecture**: Implement a modular system where specialized agents handle different aspects of the planning process
4. **Knowledge Representation**: Store machining knowledge (materials, tools, operations) in an accessible JSON database
5. **Dual Interface**: Provide both programmatic (API) and interactive (UI) access to the system

### Design Principles
- **Modularity**: Each agent operates independently and can be replaced/upgraded
- **Extensibility**: Easy to add new materials, tools, operations, and validation rules
- **Rule-Based Foundation**: Current implementation uses rule-based logic, designed to be upgraded with LLM integration later
- **Type Safety**: Uses Pydantic v2 for data validation and type checking
- **Production-Ready Structure**: Logging, error handling, and structured responses

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   User Input    │
│  (Goal/Spec)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      Orchestrator               │
│  (Coordinates Workflow)         │
└────────┬───────────────────────┘
         │
         ├───► PlannerAgent ───► Plan Steps
         │
         ├───► ValidatorAgent ──► Validation
         │
         └───► CodeAgent ──────► G-Code
         │
         ▼
┌─────────────────┐
│  Machining DB   │
│  (Knowledge)    │
└─────────────────┘
```

### Agent Responsibilities

1. **PlannerAgent**: 
   - Analyzes input specifications
   - Generates structured plan steps
   - Maps operations to tools and parameters

2. **CodeAgent**:
   - Translates plan steps into G-code
   - Consults machining database for speeds/feeds
   - Generates tool paths and commands

3. **ValidatorAgent**:
   - Validates plan structure and parameters
   - Checks G-code syntax and completeness
   - Ensures safety constraints

4. **Orchestrator**:
   - Coordinates agent execution
   - Manages shared state
   - Handles error propagation
   - Provides logging and monitoring

---

## 📅 Implementation Timeline

### **Day 1: Project Foundation**
**Objective**: Set up project structure and scaffolding

**Deliverables**:
- Created complete folder structure (`process_agent/`, `agents/`, `core/`, `api/`, `ui/`)
- Implemented placeholder agents with stub logic
- Created sample `machining_db.json` with materials, tools, and operations
- Set up FastAPI and Streamlit placeholders
- Added basic pytest test suite
- Created architecture diagram (Mermaid)

**Key Files Created**:
- `process_agent/agents/planner_agent.py`
- `process_agent/agents/code_agent.py`
- `process_agent/agents/validator_agent.py`
- `process_agent/core/orchestrator.py`
- `process_agent/api/main.py`
- `process_agent/ui/app.py`
- `tests/test_agents.py`, `tests/test_orchestrator.py`

---

### **Day 2: Core Logic Implementation**
**Objective**: Implement structured planning with Pydantic models

**Deliverables**:
- Introduced Pydantic v2 schemas for type safety (`PartSpec`, `PlanStep`, `PlanResult`)
- Enhanced `PlannerAgent` to generate structured `PlanStep` objects
- Improved `CodeAgent` to use machining database values
- Enhanced `ValidatorAgent` with comprehensive checks (operations, parameters, positions)
- Updated `Orchestrator` to use typed models
- Migrated from Pydantic v1 to v2 (fixed `conlist`/`confloat` syntax)

**Key Improvements**:
- Type-safe data structures throughout
- Validation at multiple levels
- Better error messages
- Structured plan output

---

### **Day 3: Multi-Agent Workflow Integration**
**Objective**: Connect agents into coordinated workflow with logging

**Deliverables**:
- Enhanced orchestrator with shared state management
- Implemented logging system (console + file: `logs/run.log`)
- Created `parse_goal_to_spec()` utility for natural language parsing
- Built interactive CLI demo (`scripts/run_demo.py`)
- Added pretty-printing for plans
- Implemented pre- and post-codegen validation

**Key Features Added**:
- Structured logging with timestamps
- Progress tracking ("Planning → Validation → Code Generation → Done")
- Error handling and graceful failures
- Shared state dictionary for agent communication

---

### **Day 4: API & UI Interfaces**
**Objective**: Build production-ready FastAPI and Streamlit interfaces

**Deliverables**:
- **FastAPI**:
  - Added `/plan_process` endpoint accepting goal strings
  - Enhanced `/plan` endpoint for structured specs
  - Health check endpoint
  - Swagger/OpenAPI documentation
  
- **Streamlit UI**:
  - Clean, modern interface with goal input
  - Material dropdown selector
  - Expandable Plan and G-Code sections
  - Real-time validation status
  - Sidebar with About section
  - Clear button for form reset

- **Testing Infrastructure**:
  - Created `scripts/test_fastapi.py` for automated API testing
  - Created `scripts/test_streamlit.sh` for UI testing
  - Comprehensive testing guide (`TESTING.md`)

**Key Features**:
- Natural language goal parsing
- Interactive web interface
- Real-time plan generation
- Formatted output display

---

## 🔧 Core Components

### 1. **PlannerAgent** (`process_agent/agents/planner_agent.py`)

**Purpose**: Converts part specifications into structured machining plans

**Current Logic**:
- Analyzes input for material and operations
- Always starts with face milling (0.2mm depth)
- Adds drilling steps for each hole in `drill_holes`
- Returns list of `PlanStep` objects

**Input**:
```python
{
    "material": "aluminum_6061",
    "drill_holes": [
        {"diameter_mm": 6, "depth_mm": 10, "position": [0, 0]}
    ]
}
```

**Output**: List of `PlanStep` objects with operation, depth, diameter, position, notes

---

### 2. **CodeAgent** (`process_agent/agents/code_agent.py`)

**Purpose**: Generates pseudo-G-code from plan steps

**Current Logic**:
- Loads machining database
- Maps materials to RPM and feed rates
- Generates G-code for each operation:
  - Face milling: G1 moves with retraction
  - Drilling: G0 positioning, G1 plunge, retraction
- Includes comments and program structure

**Features**:
- Material-specific parameters from DB
- Tool diameter considerations
- Safe Z-height management
- Program header and footer (M30)

**Example Output**:
```gcode
; PSEUDO-GCODE GENERATED
; MATERIAL: aluminum_6061
G90 ; absolute positioning
; -- Face Milling --
G1 Z-0.200 F200 ; plunge
G1 X0 Y0 F800 ; sweep start
...
M30 ; program end
```

---

### 3. **ValidatorAgent** (`process_agent/agents/validator_agent.py`)

**Purpose**: Validates plans and generated G-code

**Validation Checks**:
1. **Plan Validation** (pre-codegen):
   - Plan is non-empty
   - Operations are supported (`face_milling`, `drilling`)
   - Depth values are positive numbers
   - Drilling operations have diameter and position

2. **G-Code Validation** (post-codegen):
   - G-code contains header (`PSEUDO-GCODE`)
   - G-code contains terminator (`M30`)
   - G-code is non-empty

**Returns**: `(is_valid: bool, errors: List[str])`

---

### 4. **Orchestrator** (`process_agent/core/orchestrator.py`)

**Purpose**: Coordinates the entire workflow

**Workflow**:
1. Accepts part specification
2. Calls PlannerAgent → generates plan
3. Validates plan (pre-codegen)
4. If valid: Calls CodeAgent → generates G-code
5. Validates G-code (post-codegen)
6. Returns comprehensive result

**Shared State**:
- Maintains dictionary with plan, gcode, validation status
- Passed between agents
- Logged at each step

**Error Handling**:
- Stops early on validation failure
- Returns partial results with error messages
- Logs all errors for debugging

---

### 5. **Utilities** (`process_agent/core/utils.py`)

**Key Functions**:
- `parse_goal_to_spec(goal: str)`: Converts natural language to spec dict
- `pretty_print_plan(plan)`: Formats plan for human reading
- `setup_logger(logfile)`: Configures logging (console + file)
- `load_json_file(path)`: Loads JSON files safely
- `utc_timestamp()`: Generates ISO timestamps

---

## 🛠️ Technical Stack

### Core Dependencies

**Web Framework**:
- `fastapi==0.115.0` - Modern async web framework
- `uvicorn[standard]==0.30.6` - ASGI server

**Data Validation**:
- `pydantic==2.9.1` - Data validation and settings management

**UI Framework**:
- `streamlit==1.39.0` - Rapid web app development

**HTTP Client**:
- `httpx==0.27.2` - Modern HTTP client (for testing)

**Development Tools**:
- `pytest==8.3.3` - Testing framework
- `jupyter==1.1.1` - Notebook support

**LLM Support** (Prepared for future):
- `openai==1.51.0`
- `langchain==0.3.3`
- `langchain-openai==0.2.2`
- `litellm==1.48.1`

---

## 📊 Data Model & Knowledge Base

### Machining Database Structure (`data/machining_db.json`)

**Materials**:
```json
{
  "aluminum_6061": {
    "recommended_rpm": 12000,
    "recommended_feed_mm_per_min": 800,
    "notes": "General purpose aluminum, good machinability"
  },
  "steel_1018": {
    "recommended_rpm": 6000,
    "recommended_feed_mm_per_min": 300,
    "notes": "Low carbon steel"
  }
}
```

**Tools**:
```json
{
  "endmill_6mm": {
    "type": "endmill",
    "diameter_mm": 6,
    "flutes": 4,
    "material": "carbide"
  },
  "drill_6mm": {
    "type": "drill",
    "diameter_mm": 6,
    "flutes": 2,
    "material": "HSS"
  }
}
```

**Operations**:
```json
{
  "face_milling": {
    "description": "Face the top surface to achieve flatness",
    "default_tool": "endmill_6mm"
  },
  "drilling": {
    "description": "Drill a through hole",
    "default_tool": "drill_3mm"
  }
}
```

### Pydantic Schemas

**PartSpec**: Input specification
- `material: str` - Material identifier
- `drill_holes: Optional[List[DrillHole]]` - Optional holes to drill

**DrillHole**: Hole specification
- `diameter_mm: float > 0`
- `depth_mm: float > 0`
- `position: List[float]` (length 2) - [x, y] coordinates

**PlanStep**: Individual operation step
- `operation: OperationType` - Enum (FACE_MILLING, DRILLING)
- `depth_mm: Optional[float]`
- `diameter_mm: Optional[float]`
- `position: Optional[List[float]]`
- `notes: Optional[str]`

**PlanResult**: Final output
- `plan: List[PlanStep]`
- `gcode: str`
- `valid: bool`
- `errors: List[str]`

---

## 🔄 Workflow & Process Flow

### Complete Execution Flow

```
1. User Input (Natural Language or Structured)
   ↓
2. parse_goal_to_spec() - Convert goal to spec dict
   ↓
3. Orchestrator.run(spec)
   │
   ├─► PlannerAgent.plan_process(spec)
   │   └─► Returns: List[PlanStep]
   │
   ├─► ValidatorAgent.validate(plan, None)  [Pre-codegen]
   │   └─► Returns: (valid: bool, errors: List)
   │
   ├─► CodeAgent.generate_pseudo_gcode(plan, material)
   │   ├─► Loads machining_db.json
   │   ├─► Gets RPM/feed for material
   │   └─► Returns: G-code string
   │
   └─► ValidatorAgent.validate(plan, gcode)  [Post-codegen]
       └─► Returns: (valid: bool, errors: List)
   ↓
4. Return PlanResult (plan, gcode, valid, errors)
```

### State Management

The orchestrator maintains a shared state dictionary:
```python
state = {
    "plan": [...],      # Plan steps
    "gcode": "...",     # Generated G-code
    "valid": True,      # Validation status
    "errors": []        # Error list
}
```

This state is:
- Passed between agents
- Logged at each stage
- Returned as final result

---

## 🌐 API Endpoints

### FastAPI Server (`process_agent/api/main.py`)

**Base URL**: `http://127.0.0.1:8000`

#### 1. `GET /health`
**Purpose**: Health check endpoint

**Response**:
```json
{
  "status": "ok"
}
```

#### 2. `POST /plan_process`
**Purpose**: Plan using natural language goal

**Request**:
```json
{
  "goal": "Prepare drilling operation for aluminum part"
}
```

**Response**:
```json
{
  "plan": [
    {
      "operation": "face_milling",
      "depth_mm": 0.2,
      "notes": "Face top surface for aluminum_6061"
    },
    {
      "operation": "drilling",
      "diameter_mm": 6.0,
      "depth_mm": 10.0,
      "position": [0.0, 0.0]
    }
  ],
  "gcode": "; PSEUDO-GCODE GENERATED\n...",
  "valid": true,
  "errors": []
}
```

#### 3. `POST /plan`
**Purpose**: Plan using structured PartSpec

**Request**:
```json
{
  "material": "aluminum_6061",
  "drill_holes": [
    {
      "diameter_mm": 6,
      "depth_mm": 10,
      "position": [0, 0]
    }
  ]
}
```

**Response**: Same as `/plan_process`

#### Swagger Documentation
Visit `http://127.0.0.1:8000/docs` for interactive API documentation

---

## 🖥️ User Interface

### Streamlit App (`process_agent/ui/app.py`)

**Features**:
- **Goal Input**: Text box for natural language goals
- **Material Selector**: Dropdown (Aluminum 6061, Steel 1018)
- **Generate Plan Button**: Primary action button
- **Clear Button**: Resets form
- **Expandable Sections**:
  - 📋 PLAN: Shows formatted plan steps
  - 🧠 G-CODE OUTPUT: Shows generated G-code with syntax highlighting
- **Validation Status**: Green checkmark or red error messages
- **Sidebar**: About section with version and author info

**Usage Flow**:
1. User enters goal: "Prepare drilling operation for aluminum part"
2. Selects material from dropdown
3. Clicks "Generate Plan"
4. Plan and G-code appear in expandable sections
5. Validation status displayed at bottom

**Technical Details**:
- Uses session state for orchestrator persistence
- Path resolution for Streamlit compatibility
- Error handling with user-friendly messages
- Spinner during processing

---

## ✅ Current Capabilities

### What Works Today

1. **Natural Language Processing**:
   - ✅ Parses goal strings ("Prepare drilling for aluminum")
   - ✅ Extracts material and operation keywords
   - ✅ Converts to structured specifications

2. **Process Planning**:
   - ✅ Generates face milling steps
   - ✅ Generates drilling steps with parameters
   - ✅ Structures plans as typed objects

3. **G-Code Generation**:
   - ✅ Generates pseudo-G-code for face milling
   - ✅ Generates pseudo-G-code for drilling
   - ✅ Uses material-specific speeds/feeds from database
   - ✅ Includes proper structure (G90, M30, etc.)

4. **Validation**:
   - ✅ Validates plan structure before code generation
   - ✅ Validates G-code after generation
   - ✅ Checks operation types, parameters, positions
   - ✅ Provides detailed error messages

5. **Interfaces**:
   - ✅ FastAPI REST API with 3 endpoints
   - ✅ Streamlit web UI with full functionality
   - ✅ Swagger/OpenAPI documentation
   - ✅ Health check endpoint

6. **Infrastructure**:
   - ✅ Logging (console + file)
   - ✅ Error handling
   - ✅ Type safety (Pydantic)
   - ✅ Testing framework
   - ✅ Project documentation

### Limitations

1. **Rule-Based Logic**: Currently uses keyword matching, not true LLM reasoning
2. **Limited Operations**: Only supports face milling and drilling
3. **Fixed Patterns**: G-code templates are hardcoded
4. **No Tool Changes**: Doesn't handle tool change sequences
5. **No Collision Detection**: Doesn't validate tool paths for collisions
6. **Pseudo-G-code Only**: Not machine-ready, needs manual review

---

## 🧪 Testing & Quality Assurance

### Test Suite Structure

**Unit Tests** (`tests/`):
- `test_agents.py`: Tests for PlannerAgent, CodeAgent, ValidatorAgent
- `test_orchestrator.py`: Tests for end-to-end workflow

**Integration Tests** (`scripts/`):
- `test_fastapi.py`: Automated API endpoint testing
- `test_streamlit.sh`: Streamlit UI launcher

### Running Tests

```bash
# Unit tests
pytest -q

# API tests (requires running server)
python scripts/test_fastapi.py

# Manual UI testing
streamlit run process_agent/ui/app.py
```

### Test Coverage

- ✅ Agent initialization
- ✅ Plan generation
- ✅ G-code header validation
- ✅ End-to-end orchestrator flow
- ✅ API endpoints (health, plan_process, plan)
- ✅ Error handling

---

## 📁 Project Structure

```
ProcessAgent/
├── README.md                 # Project overview
├── TESTING.md                # Testing guide
├── PROJECT_OVERVIEW.md       # This document
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
│
├── data/                    # Data and knowledge base
│   ├── machining_db.json   # Materials, tools, operations
│   └── examples/          # Example inputs
│
├── process_agent/          # Main package
│   ├── __init__.py
│   │
│   ├── agents/            # Agent implementations
│   │   ├── __init__.py
│   │   ├── planner_agent.py    # Process planning
│   │   ├── code_agent.py       # G-code generation
│   │   └── validator_agent.py # Validation
│   │
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Workflow coordination
│   │   ├── schemas.py          # Pydantic models
│   │   └── utils.py            # Utility functions
│   │
│   ├── api/               # FastAPI application
│   │   ├── __init__.py
│   │   └── main.py             # API endpoints
│   │
│   └── ui/                # Streamlit application
│       ├── __init__.py
│       └── app.py               # UI interface
│
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_agents.py
│   └── test_orchestrator.py
│
├── scripts/              # Utility scripts
│   ├── run_demo.py       # Interactive CLI demo
│   ├── test_fastapi.py   # API testing
│   └── test_streamlit.sh # UI launcher
│
├── notebooks/            # Jupyter notebooks
│   └── day1_setup.ipynb
│
├── diagrams/             # Architecture diagrams
│   └── architecture.mmd
│
├── logs/                 # Log files (gitignored)
│   └── run.log
│
└── venv/                # Virtual environment (gitignored)
```

---

## 🚀 Future Roadmap

### Day 5 (Planned)
- ✅ Polish API/UI interfaces
- ✅ Add more comprehensive tests
- ✅ Create example gallery
- ✅ Improve documentation
- ⏳ Add error recovery mechanisms

### Beyond Day 5

**LLM Integration**:
- Replace rule-based parsing with LLM reasoning
- Use LLM for plan optimization
- Generate more sophisticated G-code

**Enhanced Operations**:
- Add turning operations
- Add threading
- Add pocketing
- Add contouring

**Advanced Features**:
- Tool change sequences
- Collision detection
- Stock material simulation
- Fixture planning
- Tolerance checking

**Production Features**:
- Database backend (PostgreSQL)
- Authentication/authorization
- Rate limiting
- Caching
- Metrics and monitoring
- Docker containerization

---

## 📝 Summary

ProcessAgent is a **fully functional, production-structured** system for automated machining process planning. Over 4 days, it evolved from a scaffolded prototype to a working application with:

- ✅ **3 specialized agents** working in coordination
- ✅ **Type-safe data models** (Pydantic v2)
- ✅ **REST API** (FastAPI) with Swagger docs
- ✅ **Interactive UI** (Streamlit)
- ✅ **Comprehensive logging** and error handling
- ✅ **Testing infrastructure**
- ✅ **Complete documentation**

The system is **extensible**, **maintainable**, and **ready for LLM integration** when needed. The modular architecture allows easy upgrades to individual components without affecting others.

**Current Status**: ✅ Day 4 Complete - Both interfaces tested and working

---

*Last Updated: After Day 4 Implementation*
*Version: 0.4.0*

