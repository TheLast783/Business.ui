"""Sidebar component: Scenario Selector, Persona Switcher, LLM Provider, and Thresholds."""

from typing import Tuple
import streamlit as st

try:
    from prototype.engine.contracts.schemas import ExecutiveConstraint, UserRole
except ImportError:
    from engine.contracts.schemas import ExecutiveConstraint, UserRole


def render_sidebar() -> Tuple[str, UserRole, str, float, ExecutiveConstraint]:
    """
    Renders the sidebar navigation and parameter controls.
    """
    st.sidebar.title("Control Center")
    st.sidebar.caption("System Configuration & Scenario Engine")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Scenario Selection")
    scenario_choice = st.sidebar.selectbox(
        "Business Scenario:",
        [
            "Scenario 1: Multi-Factor Supply Disruption (70/30 Attribution)",
            "Scenario 2: Low-Confidence Ambiguity (Explicit Abstention)",
            "Scenario 3: Sparse-History / Cold Start Launch",
            "Scenario 4: Role-Based Security & Data Entitlements"
        ],
        index=0,
        help="Select one of the 4 benchmark test scenarios."
    )

    if "1" in scenario_choice:
        scenario_id = "scenario_1"
    elif "2" in scenario_choice:
        scenario_id = "scenario_2"
    elif "3" in scenario_choice:
        scenario_id = "scenario_3"
    else:
        scenario_id = "scenario_4"

    st.sidebar.markdown("---")
    st.sidebar.subheader("User Role & Security")
    persona_choice = st.sidebar.radio(
        "Active Persona:",
        [
            "Executive (Strategic Levers & Financial Margins)",
            "Operations Analyst (Tactical SOPs & Masked Data)"
        ],
        index=0,
        help="Switching personas demonstrates dynamic RBAC masking and customized action narratives."
    )
    active_role = UserRole.EXECUTIVE if "Executive" in persona_choice else UserRole.OPERATIONS_ANALYST

    st.sidebar.markdown("---")
    st.sidebar.subheader("Executive Constraints")
    budget_slider = st.sidebar.slider(
        "Remediation Budget Cap ($):",
        min_value=0,
        max_value=100000,
        value=45000,
        step=5000,
        help="Maximum financial budget authorized for operational remediation."
    )
    horizon_slider = st.sidebar.selectbox(
        "Target Optimization Horizon (Days):",
        [30, 60, 90],
        index=1,
        help="Target recovery timeframe."
    )
    policy_text = st.sidebar.text_input(
        "Policy Directive / Override:",
        "Prioritize high-margin APAC inventory; prohibit air freight surcharge",
        help="Strategic constraint passed into simulation engine."
    )

    exec_constraint = ExecutiveConstraint(
        budget_cap_usd=float(budget_slider),
        target_horizon_days=horizon_slider,
        policy_override_note=policy_override_note if (policy_override_note := policy_text) else None
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Engine Configuration")
    engine_mode_choice = st.sidebar.selectbox(
        "AI Synthesis Mode:",
        [
            "Offline Deterministic Mode (Recommended)",
            "Live API (OpenAI / Gemini / Ollama)"
        ],
        index=0,
        help="Deterministic offline fallback guarantees 0 latency and 0 cost."
    )
    llm_mode = "live" if "Live" in engine_mode_choice else "mock"

    sigma_slider = st.sidebar.slider(
        "SPC Anomaly Threshold (Sigma):",
        min_value=1.5,
        max_value=3.5,
        value=2.5,
        step=0.1,
        help="Standard deviation multiplier for anomaly detection."
    )

    return scenario_id, active_role, llm_mode, sigma_slider, exec_constraint
