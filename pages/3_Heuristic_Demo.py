"""
Heuristic Verification Matrix Demo Page
Test hardware stress scenarios against expected AI responses
"""

import streamlit as st
import sys
sys.path.insert(0, '..')

from apexvitals import HEURISTIC_VERIFICATION_MATRIX, get_ai_diagnosis

st.set_page_config(page_title="Heuristic Demo", page_icon="🔬", layout="wide")

st.title("Heuristic Verification Matrix")
st.markdown("### Validate AI diagnosis against reference standards")

# Scenario selector
scenario_keys = list(HEURISTIC_VERIFICATION_MATRIX.keys())
selected = st.sidebar.selectbox("Select Scenario", scenario_keys)

# Display selected scenario
scenario = HEURISTIC_VERIFICATION_MATRIX[selected]

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Input Vector (Simulated)")
    for k, v in scenario["input_vector"].items():
        st.metric(k.replace('_', ' ').title(), v)

    st.info("**Expected Root Cause:** " + scenario["expected_root_cause"])
    st.warning("**Expected Risk:** " + scenario["expected_risk_category"])

with col2:
    st.subheader("Verification Logic")
    st.write(scenario["verification_logic"])

    if st.button("Run AI Diagnosis Test", type="primary"):
        with st.spinner("Querying Gemini AI..."):
            # Build mock telemetry from input vector
            iv = scenario["input_vector"]
            mock_telemetry = {
                "cpu_usage": iv.get("cpu_usage", 50),
                "ram_usage": 45,
                "gpu_temp": iv.get("gpu_temperature", 60),
                "gpu_load": iv.get("gpu_load", 50),
                "gpu_power": iv.get("gpu_power", 100),
                "disk_usage": 50,
                "power_plan": iv.get("power_plan", "Balanced")
            }

            result = get_ai_diagnosis(mock_telemetry)

            st.markdown("#### AI Output")
            st.json(result)

            # Comparison
            st.divider()
            st.markdown("#### Validation")

            expected = scenario["expected_root_cause"]
            actual = result.get("root_cause", "N/A")

            if expected.lower() in actual.lower() or actual.lower() in expected.lower():
                st.success("Root cause MATCHED")
            else:
                st.warning("Root cause differs (expected vs actual):")
                st.write(f"Expected: {expected}")
                st.write(f"Actual: {actual}")

            expected_risk = scenario["expected_risk_category"]
            actual_risk = result.get("risk_category", "N/A")

            if expected_risk == actual_risk:
                st.success(f"Risk category MATCHED: {expected_risk}")
            else:
                st.error(f"Risk mismatch: Expected {expected_risk}, Got {actual_risk}")

st.divider()
st.markdown("### All Scenarios Overview")

for key, data in HEURISTIC_VERIFICATION_MATRIX.items():
    with st.expander(f"{key.replace('_', ' ').title()}"):
        st.write("**Input:**", data["input_vector"])
        st.write("**Expected:**", data["expected_root_cause"])
        st.write("**Risk:**", data["expected_risk_category"])
        st.write("**Why:**", data["verification_logic"])
