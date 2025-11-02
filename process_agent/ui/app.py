from __future__ import annotations
import streamlit as st

from ..core import Orchestrator, parse_goal_to_spec
from ..core.utils import pretty_print_plan

st.set_page_config(page_title="ProcessAgent UI", layout="centered")

# Sidebar with About section
with st.sidebar:
    st.header("About")
    st.write("**ProcessAgent**")
    st.write("Version: 0.4.0")
    st.write("Author: ProcessAgent Team")
    st.write("---")
    st.write("Autonomous LLM-based system for machining process planning and pseudo-G-code generation.")

# Main content
st.title("🧩 ProcessAgent – LLM Process Planner")

# Initialize orchestrator
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

# Material dropdown helper
material_options = {
    "Aluminum 6061": "aluminum_6061",
    "Steel 1018": "steel_1018",
}

# Input form
with st.form("goal_form"):
    goal = st.text_input(
        "Goal:",
        value="Prepare drilling operation for aluminum part",
        placeholder="Enter your machining goal (e.g., 'Prepare drilling operation for aluminum part')",
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        material_display = st.selectbox(
            "Select Material:",
            options=list(material_options.keys()),
            index=0,
        )
    with col2:
        clear_btn = st.form_submit_button("Clear")
    
    submitted = st.form_submit_button("Generate Plan", type="primary")

# Handle Clear button
if clear_btn:
    st.session_state.goal = ""
    st.session_state.result = None
    st.rerun()

# Process form submission
if submitted and goal:
    material_key = material_options.get(material_display, "aluminum_6061")
    
    # Parse goal and merge with selected material
    spec = parse_goal_to_spec(goal)
    spec["material"] = material_key  # Override with user selection
    
    # Run orchestrator
    with st.spinner("Generating plan..."):
        result = st.session_state.orchestrator.run(spec)
        st.session_state.result = result

# Display results if available
if "result" in st.session_state and st.session_state.result:
    result = st.session_state.result
    
    # Plan section (expandable)
    with st.expander("📋 PLAN", expanded=True):
        plan_text = pretty_print_plan(result["plan"])
        st.text(plan_text)
    
    # G-Code section (expandable)
    with st.expander("🧠 G-CODE OUTPUT", expanded=True):
        if result.get("gcode"):
            st.code(result["gcode"], language="gcode")
        else:
            st.warning("No G-code generated")
    
    # Validation status
    if result.get("valid"):
        st.success("✅ Validation passed")
    else:
        st.error("❌ Validation failed")
        if result.get("errors"):
            for error in result["errors"]:
                st.error(f"• {error}")
