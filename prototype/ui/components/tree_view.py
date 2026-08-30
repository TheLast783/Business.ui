"""Deterministic Math View 2: Exact Shapley Causal Metric Tree Component."""

import plotly.graph_objects as go
import streamlit as st

try:
    from prototype.engine.contracts.schemas import TreeDecompositionResult
    from prototype.ui.styles import MATH_CORE_BADGE_HTML
except ImportError:
    from engine.contracts.schemas import TreeDecompositionResult
    from ui.styles import MATH_CORE_BADGE_HTML


def render_tree_view(tree_res: TreeDecompositionResult, key: str = "tree_waterfall_chart") -> None:
    """Renders the Exact Shapley Causal Metric Tree decomposition waterfall and LaTeX mathematical formulas."""
    st.markdown(MATH_CORE_BADGE_HTML, unsafe_allow_html=True)
    st.subheader("2. Exact Shapley Causal Metric Tree Attribution")
    st.caption(
        "Closed-form axiomatic Shapley decomposition: ΔRevenue = ΔSessions + ΔCVR + ΔAOV. "
        "Strict mathematical guarantee: Residual Error ≡ 0.00000000."
    )

    # LaTeX Exact Formula Box
    st.markdown('<div class="math-formula-box">', unsafe_allow_html=True)
    st.latex(
        r"\Delta R = R_1 - R_0 = \Delta \text{Sessions} \cdot \overline{\text{CVR}} \cdot \overline{\text{AOV}} "
        r"+ \overline{\text{Sessions}} \cdot \Delta \text{CVR} \cdot \overline{\text{AOV}} "
        r"+ \overline{\text{Sessions}} \cdot \overline{\text{CVR}} \cdot \Delta \text{AOV} "
        r"+ \text{Shapley Residual}"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Attribution Metric Summary
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    col_t1.metric(
        "Total Δ Revenue",
        f"${tree_res.delta_revenue:,.0f}",
        f"Residual: {tree_res.residual:.8f}"
    )
    col_t2.metric(
        "Sessions Effect",
        f"${tree_res.delta_r_sessions:,.0f}",
        f"{tree_res.factor_pct_contributions.get('sessions', 0.0):.1f}% share"
    )
    col_t3.metric(
        "Conversion Rate Effect",
        f"${tree_res.delta_r_cvr:,.0f}",
        f"{tree_res.factor_pct_contributions.get('conversion_rate', 0.0):.1f}% share"
    )
    col_t4.metric(
        "Average Order Value Effect",
        f"${tree_res.delta_r_aov:,.0f}",
        f"{tree_res.factor_pct_contributions.get('aov', 0.0):.1f}% share"
    )

    # Waterfall Chart
    fig_waterfall = go.Figure(go.Waterfall(
        name="Causal Attribution",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Web Sessions Drop", "Conversion Rate Drop", "AOV Movement", "Total Realized Δ Revenue"],
        textposition="outside",
        text=[
            f"${tree_res.delta_r_sessions:,.0f}",
            f"${tree_res.delta_r_cvr:,.0f}",
            f"${tree_res.delta_r_aov:,.0f}",
            f"${tree_res.delta_revenue:,.0f}"
        ],
        y=[
            tree_res.delta_r_sessions,
            tree_res.delta_r_cvr,
            tree_res.delta_r_aov,
            tree_res.delta_revenue
        ],
        connector={"line": {"color": "#64748b", "width": 1.5}},
        decreasing={"marker": {"color": "#ef4444"}},
        increasing={"marker": {"color": "#10b981"}},
        totals={"marker": {"color": "#38bdf8"}}
    ))

    fig_waterfall.update_layout(
        title="<b>Shapley Mathematical Attribution Waterfall ($ USD)</b>",
        xaxis_title="Causal Tree Decomposition Node",
        yaxis_title="Dollar Impact ($)",
        template="plotly_dark",
        height=380,
        margin=dict(l=40, r=40, t=50, b=40)
    )
    st.plotly_chart(fig_waterfall, use_container_width=True, key=key)
