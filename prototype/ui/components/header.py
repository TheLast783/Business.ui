"""Header component: Title, status badges, and 4 connected KPI summary ribbon."""

import pandas as pd
import streamlit as st

try:
    from prototype.engine.contracts.schemas import ScenarioExecutionResult
    from prototype.ui.styles import MATH_CORE_BADGE_HTML, AI_ENGINE_BADGE_HTML, ABSTENTION_BADGE_HTML, COLDSTART_BADGE_HTML
except ImportError:
    from engine.contracts.schemas import ScenarioExecutionResult
    from ui.styles import MATH_CORE_BADGE_HTML, AI_ENGINE_BADGE_HTML, ABSTENTION_BADGE_HTML, COLDSTART_BADGE_HTML


def render_header(result: ScenarioExecutionResult, daily_df: pd.DataFrame) -> None:
    """Renders the clean enterprise header, status badges, and 4 connected KPIs ribbon."""
    
    is_abstaining = False
    if result.synthesis_result:
        is_abstaining = getattr(result.synthesis_result, "is_abstaining", False)
    
    is_cold_start = False
    if result.spc_result:
        is_cold_start = getattr(result.spc_result, "is_cold_start", False)
        
    is_anomaly = False
    if result.spc_result:
        is_anomaly = getattr(result.spc_result, "is_anomaly", False)

    col_h1, col_h2 = st.columns([3, 2])
    with col_h1:
        st.markdown(
            """
            <div>
                <h1 style="margin:0;font-size:1.85rem !important;">Business Intelligence Platform</h1>
                <div style="color:#94a3b8;font-size:0.9rem;">KPI Root Cause Diagnosis & Prescriptive Action Engine</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col_h2:
        st.markdown("<div style='text-align:right;padding-top:4px;'>", unsafe_allow_html=True)
        if is_abstaining:
            st.markdown('<span class="badge-abstention">ABSTENTION ACTIVE (LOW CONFIDENCE)</span>', unsafe_allow_html=True)
        elif is_cold_start:
            st.markdown('<span class="badge-coldstart">COLD START PRIOR ACTIVE</span>', unsafe_allow_html=True)
        elif is_anomaly:
            st.markdown('<span class="badge-math-core">STATISTICAL ANOMALY DETECTED</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-math-core">NORMAL BASELINE VARIANCE</span>', unsafe_allow_html=True)
            
        st.markdown('<span class="badge-ai-engine">3-MODEL AI SYNTHESIS</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    # 4 Connected KPIs Summary Ribbon
    if daily_df is not None and not daily_df.empty:
        eval_row = daily_df.iloc[-1]
        base_row = daily_df.iloc[:-1].mean(numeric_only=True) if len(daily_df) > 1 else eval_row

        gross_rev_act = float(eval_row.get("gross_revenue", 0.0))
        gross_rev_base = float(base_row.get("gross_revenue", gross_rev_act))
        delta_rev_pct = ((gross_rev_act - gross_rev_base) / max(1.0, gross_rev_base)) * 100.0

        sess_act = int(eval_row.get("sessions", 0))
        sess_base = float(base_row.get("sessions", sess_act))
        delta_sess_pct = ((sess_act - sess_base) / max(1.0, sess_base)) * 100.0

        ord_act = int(eval_row.get("order_volume", 0))
        ord_base = float(base_row.get("order_volume", ord_act))
        delta_ord_pct = ((ord_act - ord_base) / max(1.0, ord_base)) * 100.0

        cvr_act = (ord_act / max(1, sess_act)) * 100.0
        cvr_base = (ord_base / max(1.0, sess_base)) * 100.0
        delta_cvr_pct = cvr_act - cvr_base

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric(
            "Gross Revenue ($)",
            f"${gross_rev_act:,.0f}",
            f"{delta_rev_pct:+.1f}% vs Base",
            delta_color="inverse" if delta_rev_pct < 0 else "normal",
            help="Total realized revenue post discounts and returns across all channels"
        )
        kpi2.metric(
            "Web Traffic",
            f"{sess_act:,}",
            f"{delta_sess_pct:+.1f}% vs Base",
            delta_color="inverse" if delta_sess_pct < 0 else "normal",
            help="Hourly normalized web and mobile visitor sessions"
        )
        kpi3.metric(
            "Order Volume",
            f"{ord_act:,}",
            f"{delta_ord_pct:+.1f}% vs Base",
            delta_color="inverse" if delta_ord_pct < 0 else "normal",
            help="Total completed transactions in ERP ledger"
        )
        kpi4.metric(
            "Conversion Rate",
            f"{cvr_act:.2f}%",
            f"{delta_cvr_pct:+.2f}% pts",
            delta_color="inverse" if delta_cvr_pct < 0 else "normal",
            help="Order Volume / Web Sessions ratio"
        )
    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)
