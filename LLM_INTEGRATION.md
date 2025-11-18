# LLM Integration Guide

## Overview

ProcessAgent now includes LLM-powered planning capabilities with automatic fallback to rule-based logic. The system uses structured prompts to generate machining plans with tool selection, speeds, and feeds.

## Features

- **LLM-Powered Planning**: Uses OpenAI GPT models (or compatible APIs) to generate intelligent machining plans
- **Automatic Fallback**: Falls back to rule-based logic if LLM is unavailable or fails
- **Structured Output**: LLM generates plans with tool, RPM, and feed_rate for each step
- **Database Integration**: LLM uses machining database to select appropriate tools and parameters
- **Validation**: Enhanced validator catches missing or incorrect LLM outputs

## Setup

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# Enable/disable LLM (set to false to use rule-based only)
USE_LLM=true

# OpenAI API Key
OPENAI_API_KEY=your_api_key_here

# Model selection (gpt-4o-mini is recommended for cost-effectiveness)
LLM_MODEL=gpt-4o-mini

# LLM Parameters
LLM_TEMPERATURE=0.1  # Low temperature for deterministic output
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=30
```

### 2. Install Dependencies

All required dependencies are already in `requirements.txt`:
- `openai==1.51.0`
- `langchain==0.3.3`
- `langchain-openai==0.2.2`
- `python-dotenv==1.0.1`

## Architecture

### LLM Planner Agent (`process_agent/agents/llm_planner.py`)

The `LLMPlannerAgent` class:
- Loads machining database (materials, tools, operations)
- Creates structured prompts with database context
- Calls LLM with deterministic prompts
- Parses and validates LLM responses
- Falls back to rule-based logic on failure

### Prompt Engineering

The planner uses a carefully crafted prompt that:
1. Provides full context (materials, tools, operations from DB)
2. Specifies exact output format (JSON array)
3. Includes examples of correct output
4. Requests tool, RPM, and feed_rate selection

### Fallback Logic

If LLM fails:
- Catches exceptions gracefully
- Logs warnings
- Automatically uses rule-based planner
- System continues to function normally

## Usage

### Basic Usage

```python
from process_agent.core import Orchestrator

# Auto-detects LLM from environment
orch = Orchestrator()

# Generate plan (uses LLM if available, otherwise rule-based)
spec = {
    "material": "aluminum_6061",
    "drill_holes": [
        {"diameter_mm": 6.0, "depth_mm": 10.0, "position": [0.0, 0.0]}
    ]
}
result = orch.run(spec)
```

### Force Rule-Based Mode

```python
# Disable LLM explicitly
orch = Orchestrator(use_llm=False)
```

### Testing

Run the test script:

```bash
python scripts/test_llm_planner.py
```

## Prompt Variations

The system uses a single, well-tested prompt that:
- Includes all database information
- Provides clear instructions
- Specifies exact JSON format
- Includes examples

For testing different prompts, modify `_create_planning_prompt()` in `llm_planner.py`.

## Validation

The `ValidatorAgent` now checks for:
- Tool identifiers (from LLM)
- RPM values (from LLM)
- Feed rates (from LLM)
- Operation-specific requirements

Missing LLM fields are logged as warnings but don't fail validation (allows rule-based fallback).

## PlanStep Schema Updates

`PlanStep` now includes:
- `tool: Optional[str]` - Tool identifier from database
- `rpm: Optional[int]` - Spindle speed in RPM
- `feed_rate_mm_per_min: Optional[float]` - Feed rate in mm/min

These fields are populated by the LLM planner and used by the CodeAgent.

## CodeAgent Integration

The `CodeAgent` now:
- Uses tool, RPM, and feed_rate from plan steps (if available)
- Falls back to material defaults if not provided
- Logs which values are used

## Troubleshooting

### LLM Not Working

1. Check `.env` file exists and has `OPENAI_API_KEY`
2. Verify API key is valid
3. Check logs for LLM initialization messages
4. System will automatically fall back to rule-based

### LLM Output Issues

1. Check logs for parsing errors
2. Validator will catch missing/invalid fields
3. System validates and fixes LLM output automatically

### Cost Concerns

- Use `gpt-4o-mini` for lower costs
- Set `USE_LLM=false` to disable LLM entirely
- System works perfectly in rule-based mode

## Future Improvements

- Support for multiple LLM providers (Anthropic, etc.)
- Prompt versioning and A/B testing
- Caching of LLM responses
- Fine-tuning on machining domain data



