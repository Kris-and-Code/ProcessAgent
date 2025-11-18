from __future__ import annotations
import sys
import os
from pathlib import Path

# Add project root to path for Streamlit compatibility
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from process_agent.core import Orchestrator, parse_goal_to_spec
from process_agent.core.utils import pretty_print_plan

st.set_page_config(page_title="ProcessAgent UI", layout="wide", initial_sidebar_state="expanded")

# Sidebar with About section
with st.sidebar:
    st.header("About")
    st.write("**ProcessAgent**")
    st.write("Version: 0.5.0")
    st.write("Author: ProcessAgent Team")
    st.write("---")
    st.write("Autonomous LLM-based system for machining process planning and pseudo-G-code generation.")
    st.write("---")
    st.write("### Workflow")
    st.write("1. **Inputs**: Enter goal and select material")
    st.write("2. **Plan**: Review generated machining plan")
    st.write("3. **G-code**: View generated pseudo-G-code")
    st.write("4. **Validation**: Check validation status")

# Main content
st.title("🧩 ProcessAgent – LLM Process Planner")
st.markdown("---")

# Initialize orchestrator
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

# Material dropdown helper
material_options = {
    "Aluminum 6061": "aluminum_6061",
    "Steel 1018": "steel_1018",
}

# ============================================================================
# SECTION 1: INPUTS
# ============================================================================
st.header("📥 Inputs")
with st.container():
    with st.form("goal_form", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])
        with col1:
            goal = st.text_input(
                "**Machining Goal:**",
                value="Prepare drilling operation for aluminum part",
                placeholder="Enter your machining goal (e.g., 'Prepare drilling operation for aluminum part')",
                help="Describe what you want to machine in natural language",
            )
        with col2:
            material_display = st.selectbox(
                "**Material:**",
                options=list(material_options.keys()),
                index=0,
                help="Select the material to be machined",
            )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("🚀 Generate Plan", type="primary", use_container_width=True)
        with col2:
            clear_btn = st.form_submit_button("🗑️ Clear", use_container_width=True)
    
    # Handle Clear button
    if clear_btn:
        st.session_state.goal = ""
        st.session_state.result = None
        st.session_state.error_message = None
        st.rerun()

st.markdown("---")

# Process form submission
error_message = None
if submitted:
    if not goal or not goal.strip():
        error_message = "⚠️ Please enter a machining goal before generating a plan."
        st.session_state.error_message = error_message
    else:
        material_key = material_options.get(material_display, "aluminum_6061")
        
        # Parse goal and merge with selected material
        try:
            spec = parse_goal_to_spec(goal)
            spec["material"] = material_key  # Override with user selection
            
            # Run orchestrator with progress indicators
            with st.spinner("🔄 Generating plan..."):
                try:
                    result = st.session_state.orchestrator.run(spec)
                    st.session_state.result = result
                    st.session_state.error_message = None
                except Exception as e:
                    error_message = f"❌ Error during plan generation: {str(e)}"
                    st.session_state.error_message = error_message
                    st.session_state.result = None
        except Exception as e:
            error_message = f"❌ Error parsing goal: {str(e)}"
            st.session_state.error_message = error_message
            st.session_state.result = None

# Display error if any
if "error_message" in st.session_state and st.session_state.error_message:
    st.error(st.session_state.error_message)

# ============================================================================
# SECTION 2: PLAN
# ============================================================================
if "result" in st.session_state and st.session_state.result:
    result = st.session_state.result
    
    st.header("📋 Plan")
    with st.container():
        if result.get("plan") and len(result["plan"]) > 0:
            # Display plan in a nice format
            plan_text = pretty_print_plan(result["plan"])
            st.code(plan_text, language=None)
            
            # Show plan summary
            st.info(f"✅ Generated {len(result['plan'])} step(s) in the machining plan")
        else:
            st.warning("⚠️ No plan steps generated")
    
    st.markdown("---")
    
    # ============================================================================
    # SECTION 3: G-CODE OUTPUT
    # ============================================================================
    st.header("⚙️ G-code Output")
    with st.container():
        if result.get("gcode"):
            # Better G-code formatting with line numbers
            gcode_lines = result["gcode"].split("\n")
            formatted_gcode = "\n".join([f"{i+1:3d} | {line}" for i, line in enumerate(gcode_lines)])
            
            st.code(formatted_gcode, language="gcode")
            
            # G-code statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Lines", len(gcode_lines))
            with col2:
                # Extract material from G-code comment or use default
                material_display = "N/A"
                if result.get("gcode"):
                    for line in result["gcode"].split("\n"):
                        if "MATERIAL:" in line:
                            material_display = line.split("MATERIAL:")[-1].strip()
                            break
                st.metric("Material", material_display)
            with col3:
                operations = [step.get("operation", "") for step in result.get("plan", [])]
                st.metric("Operations", len(set(operations)))
        else:
            st.warning("⚠️ No G-code generated")
    
    st.markdown("---")
    
    # ============================================================================
    # SECTION 4: VALIDATION
    # ============================================================================
    st.header("✅ Validation")
    with st.container():
        if result.get("valid"):
            st.success("✅ **Validation Passed** - Plan and G-code are valid")
        else:
            st.error("❌ **Validation Failed**")
            if result.get("errors") and len(result["errors"]) > 0:
                st.write("**Errors found:**")
                for i, error in enumerate(result["errors"], 1):
                    st.error(f"{i}. {error}")
            else:
                st.warning("⚠️ Validation failed but no specific errors reported")
