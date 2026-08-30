"""Deterministic Math View 1: Statistical Process Control (SPC) Component."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    from prototype.engine.contracts.schemas import SPCResult
    from prototype.ui.styles import MATH_CORE_BADGE_HTML, COLDSTART_BADGE_HTML
except ImportError:
    from engine.contracts.schemas import SPCResult
    from ui.styles import MATH_CORE_BADGE_HTML, COLDSTART_BADGE_HTML


def render_spc_view(spc_res: SPCResult, daily_df: pd.DataFrame, key: str = "spc_control_chart") -> None:
    """Renders the Statistical Process Control (SPC) interactive chart and statistical breakdown."""
    st.markdown(MATH_CORE_BADGE_HTML, unsafe_allow_html=True)
    st.subheader("1. Statistical Process Control (SPC) Anomaly Detection")
    st.caption(
        "28-day rolling Day-of-Week (DoW) normalized baseline with standardized Z-Score evaluation. "
        "Closed-form calculation with zero LLM hallucination."
    )

    if getattr(spc_res, "is_cold_start", False):
        st.markdown(COLDSTART_BADGE_HTML, unsafe_allow_html=True)
        st.info(
            "❄️ **Cold Start Protocol Engaged**: Sparse historical dataset detected (N < 14 days). "
            "Engine incorporates Bayesian Category Prior Mean ($5,000.00) with widened uncertainty bounds (±45%)."
        )

    # Statistical Summary Metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Baseline Mean (μ)", f"${spc_res.mean:,.0f}", f"DoW index: {spc_res.dow_index:.2f}x")
    col_m2.metric("Control Limits (LCL / UCL)", f"${spc_res.lcl:,.0f} / ${spc_res.ucl:,.0f}", "±2.5σ Threshold")
    col_m3.metric("Observed Point Value", f"${spc_res.observed_value:,.0f}", f"Z-Score: {spc_res.z_score:+.2f}σ")
    
    if spc_res.is_anomaly:
        col_m4.markdown('<div class="anomaly-alert-box" style="padding:10px;text-align:center;"><b>🚨 ANOMALY</b><br>|Z| ≥ 2.5σ</div>', unsafe_allow_html=True)
    else:
        col_m4.markdown('<div style="background:#064e3b;border:1px solid #059669;border-radius:6px;padding:10px;text-align:center;color:#6ee7b7;"><b>✅ IN-CONTROL</b><br>Normal Variance</div>', unsafe_allow_html=True)

    # Plotly SPC Control Chart
    fig_spc = go.Figure()

    # Historical Revenue Line
    dates = daily_df["date"].tolist() if "date" in daily_df.columns else list(range(len(daily_df)))
    revs = daily_df["gross_revenue"].tolist() if "gross_revenue" in daily_df.columns else []

    fig_spc.add_trace(go.Scatter(
        x=dates,
        y=revs,
        mode="lines+markers",
        name="Daily Gross Revenue ($)",
        line=dict(color="#38bdf8", width=2.5),
        marker=dict(size=6, color="#0284c7")
    ))

    # Control Bands
    fig_spc.add_hline(
        y=spc_res.ucl,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"UCL (+2.5σ): ${spc_res.ucl:,.0f}",
        annotation_position="top right"
    )
    fig_spc.add_hline(
        y=spc_res.mean,
        line_dash="dot",
        line_color="#94a3b8",
        annotation_text=f"Seasonality Mean: ${spc_res.mean:,.0f}",
        annotation_position="bottom right"
    )
    fig_spc.add_hline(
        y=spc_res.lcl,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"LCL (-2.5σ): ${spc_res.lcl:,.0f}",
        annotation_position="bottom right"
    )

    # Highlight evaluation point
    if dates and revs:
        eval_date = dates[-1]
        eval_val = revs[-1]
        fig_spc.add_trace(go.Scatter(
            x=[eval_date],
            y=[eval_val],
            mode="markers",
            name="Evaluated Anomaly Point" if spc_res.is_anomaly else "Evaluated Day",
            marker=dict(size=14, color="#ef4444" if spc_res.is_anomaly else "#10b981", symbol="circle-open-dot", line=dict(width=3, color="#ffffff"))
        ))

    fig_spc.update_layout(
        title="<b>Statistical Process Control (SPC) Chart with Seasonality Correction</b>",
        xaxis_title="Calendar Date",
        yaxis_title="Gross Revenue ($)",
        template="plotly_dark",
        height=380,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_spc, use_container_width=True, key=key)
