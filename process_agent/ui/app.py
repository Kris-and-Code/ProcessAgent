from __future__ import annotations
import json
import streamlit as st

from ..core import Orchestrator

st.set_page_config(page_title="ProcessAgent UI", layout="centered")

st.title("ProcessAgent")
st.caption("Autonomous LLM-based machining process planner (prototype)")

orchestrator = Orchestrator()

with st.form("spec_form"):
    material = st.selectbox("Material", ["aluminum_6061", "steel_1018"], index=0)
    holes_json = st.text_area(
        "Drill holes JSON array",
        value='[{"diameter_mm":3, "depth_mm":5, "position":[10,10]}]',
        height=120,
    )
    submitted = st.form_submit_button("Generate Plan + Pseudo–G-code")

if submitted:
    try:
        drill_holes = json.loads(holes_json) if holes_json.strip() else None
    except Exception as exc:  # noqa: BLE001 - simple UI validation
        st.error(f"Invalid JSON: {exc}")
        drill_holes = None
    spec = {"material": material, "drill_holes": drill_holes}
    result = orchestrator.run(spec)

    st.subheader("Plan")
    st.json(result["plan"])

    st.subheader("Pseudo–G-code")
    st.code(result["gcode"], language="gcode")

    if result.get("valid"):
        st.success("Validation passed")
    else:
        st.error("Validation failed")
        st.write(result.get("errors"))
