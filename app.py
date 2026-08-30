"""
BusinessIntelligence.ai — KPI Intelligence-to-Action Engine Prototype
Interactive Streamlit Decision Workspace for Round 2 Demonstration.
"""
import os
import sys

# Ensure root and prototype directories are in sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOTYPE_DIR = os.path.join(ROOT_DIR, "prototype") if os.path.exists(os.path.join(ROOT_DIR, "prototype")) else ROOT_DIR
for p in [ROOT_DIR, PROTOTYPE_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
import pandas as pd

# Setup page configuration - Must be the first Streamlit command
st.set_page_config(
    page_title="BusinessIntelligence.ai | KPI Intelligence-to-Action Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    from engine.contracts.schemas import UserRole, ExecutiveConstraint, ScenarioExecutionResult
    from engine.scenarios.runner import ScenarioRunner
    from engine.contracts.semantic_contract import RBACMaskingEngine, SemanticContractManager
    from engine.data.connectors import DataConnectorRegistry
    from engine.data.loader import MultiSourceDataLoader
    from engine.telemetry.feedback import FeedbackManager
    from ui.styles import CUSTOM_CSS, RBAC_BADGE_HTML
    from ui.components.header import render_header
    from ui.components.sidebar import render_sidebar
    from ui.components.spc_view import render_spc_view
    from ui.components.tree_view import render_tree_view
    from ui.components.synthesis_view import render_synthesis_view
    from ui.components.simulation_view import render_simulation_view
    from ui.components.feedback_widget import render_feedback_widget
    from ui.components.lineage_drawer import render_lineage_drawer
    from ui.components.telemetry_box import render_telemetry_box
except ImportError:
    from prototype.engine.contracts.schemas import UserRole, ExecutiveConstraint, ScenarioExecutionResult
    from prototype.engine.scenarios.runner import ScenarioRunner
    from prototype.engine.contracts.semantic_contract import RBACMaskingEngine, SemanticContractManager
    from prototype.engine.data.connectors import DataConnectorRegistry
    from prototype.engine.data.loader import MultiSourceDataLoader
    from prototype.engine.telemetry.feedback import FeedbackManager
    from prototype.ui.styles import CUSTOM_CSS, RBAC_BADGE_HTML
    from prototype.ui.components.header import render_header
    from prototype.ui.components.sidebar import render_sidebar
    from prototype.ui.components.spc_view import render_spc_view
    from prototype.ui.components.tree_view import render_tree_view
    from prototype.ui.components.synthesis_view import render_synthesis_view
    from prototype.ui.components.simulation_view import render_simulation_view
    from prototype.ui.components.feedback_widget import render_feedback_widget
    from prototype.ui.components.lineage_drawer import render_lineage_drawer
    from prototype.ui.components.telemetry_box import render_telemetry_box

# Inject custom styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Session State
if "runner" not in st.session_state:
    st.session_state.runner = ScenarioRunner(mode="mock")
# Share the same governed feedback/learning store between the UI and orchestrator.
if "feedback_manager" not in st.session_state:
    st.session_state.feedback_manager = st.session_state.runner.feedback_manager

# ==============================================================================
# SIDEBAR: SCENARIO SELECTOR, PERSONA SWITCHER & CONTROLS
# ==============================================================================
scenario_id, active_role, llm_mode, sigma_threshold, exec_constraint = render_sidebar()
st.session_state.runner.mode = llm_mode
if hasattr(st.session_state.runner, "spc"):
    st.session_state.runner.spc.sigma_threshold = sigma_threshold

# ==============================================================================
# EXECUTE RUNNER PIPELINE
# ==============================================================================
runner: ScenarioRunner = st.session_state.runner
result: ScenarioExecutionResult = runner.run(
    scenario_id=scenario_id,
    persona=active_role,
    constraints=exec_constraint,
    llm_mode=llm_mode
)

daily_df = runner.loader.get_daily_harmonized_df()
bundle = runner.loader.bundle

# ==============================================================================
# MAIN VIEW: HEADER & TOP KPI RIBBON
# ==============================================================================
render_header(result=result, daily_df=daily_df)

# ==============================================================================
# KPI PRIORITISATION + DATA HEALTH (deterministic governance layer)
# ==============================================================================
if result.materiality_report:
    with st.expander("KPI Materiality & Prioritisation", expanded=False):
        st.caption("Deterministic prioritisation: statistical severity + business impact + movement magnitude + KPI criticality, scaled by confidence. No LLM math.")
        kpis = result.materiality_report.get("kpis", [])
        if kpis:
            mat_cols = st.columns(min(4, len(kpis)))
            for idx, item in enumerate(kpis[:4]):
                with mat_cols[idx]:
                    st.metric(
                        f"{item['kpi_name']} • {item['priority']}",
                        f"{item['materiality_score']:.0f}/100",
                        f"{item['delta_pct']:+.1f}%",
                    )
            st.dataframe(
                pd.DataFrame([
                    {
                        "KPI": x["kpi_name"],
                        "Priority": x["priority"],
                        "Materiality": x["materiality_score"],
                        "Change": f"{x['delta_pct']:+.2f}%",
                        "Z-score": round(x["z_score"], 2),
                        "Business impact ($)": round(x["business_impact_usd"], 0),
                        "Confidence": f"{x['confidence']*100:.0f}%",
                    } for x in kpis
                ]),
                use_container_width=True,
                hide_index=True,
            )
        if result.data_health:
            st.markdown("#### Source Freshness & Data Health")
            st.dataframe(pd.DataFrame(result.data_health), use_container_width=True, hide_index=True)


# ==============================================================================
# TABBED WORKSPACE
# ==============================================================================
tab_presc, tab_math, tab_ai, tab_sim, tab_data, tab_feedback = st.tabs([
    "1. Decision Brief",
    "2. Statistical Control & Causal Tree",
    "3. Multi-Source Diagnostic Engine",
    "4. Trajectory Simulation & ROI",
    "5. Data Governance & Access Control",
    "6. Analyst Feedback & Telemetry"
])

# ------------------------------------------------------------------------------
# TAB 1: PRESCRIPTIVE STORY & ACTION PLAYBOOK
# ------------------------------------------------------------------------------
with tab_presc:
    render_synthesis_view(result=result, role=active_role, key_prefix="tab1_presc")

# ------------------------------------------------------------------------------
# TAB 2: DETERMINISTIC NON-LLM MATH CORE (SPC + CAUSAL TREE)
# ------------------------------------------------------------------------------
with tab_math:
    col_spc, col_tree = st.columns(2)
    with col_spc:
        if result.spc_result:
            render_spc_view(spc_res=result.spc_result, daily_df=daily_df, key="tab2_spc_chart")
    with col_tree:
        if result.tree_result:
            render_tree_view(tree_res=result.tree_result, key="tab2_tree_waterfall")

# ------------------------------------------------------------------------------
# TAB 3: 3-MODEL COGNITIVE ENGINE & EVIDENCE
# ------------------------------------------------------------------------------
with tab_ai:
    render_synthesis_view(result=result, role=active_role, key_prefix="tab3_ai_engine")

# ------------------------------------------------------------------------------
# TAB 4: 30/60/90-DAY TRAJECTORY ROI SIMULATOR
# ------------------------------------------------------------------------------
with tab_sim:
    if result.synthesis_result:
        render_simulation_view(
            synthesis_result=result.synthesis_result,
            budget_cap=exec_constraint.budget_cap_usd,
            key="tab4_trajectory_chart"
        )

# ------------------------------------------------------------------------------
# TAB 5: MULTI-SOURCE DATA & RBAC MASKING
# ------------------------------------------------------------------------------
with tab_data:
    st.markdown(RBAC_BADGE_HTML, unsafe_allow_html=True)
    st.subheader(f"Role-Based Access Control (Active View: {active_role.value})")
    if active_role == UserRole.OPERATIONS_ANALYST:
        st.info("Sensitive Financial Data Masked: Unit COGS and Gross Margins are redacted (`[RESTRICTED-EXEC]`). Operational ticket IDs and container codes remain visible.")
    else:
        st.success("Executive Access Granted: Full numeric financial transparency with unmasked margins and unit COGS.")

    st.markdown("#### Live Connector Readiness")
    st.caption("Optional REST connectors can replace/supplement synthetic feeds via environment configuration. No API key is hard-coded.")
    st.dataframe(pd.DataFrame(DataConnectorRegistry().status()), use_container_width=True, hide_index=True)

    entitlement = RBACMaskingEngine.entitlement(active_role)
    audit_preview = RBACMaskingEngine.audit_access(
        active_role,
        requested_domain="finance",
        requested_columns=["gross_revenue", "unit_cogs", "gross_margin_pct"],
    )
    st.markdown("#### Governed Entitlements & Audit Preview")
    e1, e2 = st.columns(2)
    with e1:
        st.write("**Accessible domains:** " + ", ".join(entitlement["domains"]))
        st.write("**Financial detail:** " + entitlement["financial_detail"])
    with e2:
        st.write("**Audit decision:** " + audit_preview["decision"])
        st.write("**Masked fields:** " + (", ".join(audit_preview["masked_columns"]) or "None"))

    if bundle is not None:
        masked_erp = result.masked_erp_data if result.masked_erp_data is not None else RBACMaskingEngine.mask_erp_dataframe(bundle.erp_df, active_role)
        st.markdown("#### 1. Daily ERP Sales Transaction Ledger (Daily Grain)")
        st.dataframe(masked_erp.head(15), use_container_width=True)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("#### 2. Hourly Web Analytics Stream (Hourly Grain)")
            if bundle.web_df is not None:
                st.dataframe(bundle.web_df.head(10), use_container_width=True)
        with col_d2:
            st.markdown("#### 3. Weekly Support & Jira Incident Logs (Weekly Grain)")
            if bundle.jira_df is not None:
                st.dataframe(bundle.jira_df.head(10), use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 6: HUMAN-IN-THE-LOOP FEEDBACK, LINEAGE & TELEMETRY
# ------------------------------------------------------------------------------
with tab_feedback:
    render_feedback_widget(
        scenario_id=scenario_id,
        feedback_mgr=st.session_state.feedback_manager,
        llm_mode=llm_mode,
    )
    st.markdown("---")
    if result.telemetry:
        render_telemetry_box(telemetry=result.telemetry)

    st.markdown("---")
    render_lineage_drawer(result=result, bundle=bundle)
