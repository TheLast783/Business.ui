"""3-Model AI Synthesis View: Diagnostic, Macro, and Prescriptive Briefs with Scenario 2-4 Adapters."""

import plotly.express as px
import streamlit as st

try:
    from prototype.engine.contracts.schemas import (
        PrescriptiveSimulationOutput,
        ScenarioExecutionResult,
        UserRole,
    )
    from prototype.ui.styles import (
        AI_ENGINE_BADGE_HTML,
        ABSTENTION_BADGE_HTML,
        COLDSTART_BADGE_HTML,
        RBAC_BADGE_HTML,
    )
except ImportError:
    from engine.contracts.schemas import (
        PrescriptiveSimulationOutput,
        ScenarioExecutionResult,
        UserRole,
    )
    from ui.styles import (
        AI_ENGINE_BADGE_HTML,
        ABSTENTION_BADGE_HTML,
        COLDSTART_BADGE_HTML,
        RBAC_BADGE_HTML,
    )


def render_synthesis_view(result: ScenarioExecutionResult, role: UserRole, key_prefix: str = "synth") -> None:
    """Renders the clean 3-Model AI Synthesis cards, persona brief, and scenario adapters without emojis."""
    st.markdown(AI_ENGINE_BADGE_HTML, unsafe_allow_html=True)
    st.subheader("Prescriptive Decision Brief & Root Cause Synthesis")
    st.caption("Synthesizes internal warehouse operational data with live global market and shipping feeds.")

    presc: PrescriptiveSimulationOutput = result.synthesis_result
    if not presc:
        st.warning("No synthesis result available for current run.")
        return

    # Scenario 2: Low-Confidence Ambiguity & Explicit Abstention
    if presc.is_abstaining:
        st.markdown(ABSTENTION_BADGE_HTML, unsafe_allow_html=True)
        st.warning(
            "**ABSTENTION PROTOCOL ACTIVATED — CAPITAL ALLOCATION SAFEGUARD**\n\n"
            "The confidence delta between the two leading root-cause hypotheses is below 25% (observed: 16% delta). "
            "To eliminate the risk of misallocating capital based on uncertain AI inference, strategic action is deferred until completion of low-cost canary validation tests."
        )

        st.markdown("#### Competing Root-Cause Hypotheses (Ranked by Evidence Weight)")
        col_hyp1, col_hyp2 = st.columns(2)
        
        hypotheses = presc.ranked_hypotheses
        if len(hypotheses) >= 2:
            h1 = hypotheses[0]
            h2 = hypotheses[1]
            with col_hyp1:
                st.markdown(
                    f'<div class="hypothesis-card hypothesis-card-winner">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
                    f'<h4 style="color:#f59e0b;margin:0;font-size:1.0rem;">Hypothesis 1 (Top Candidate)</h4>'
                    f'<span style="background:rgba(245,158,11,0.15);color:#fbbf24;padding:2px 8px;border-radius:4px;font-weight:600;font-size:0.8rem;">{h1.likelihood_pct:.0f}% Likelihood</span>'
                    f'</div>'
                    f'<p style="font-size:0.98rem;font-weight:600;color:#ffffff;margin-bottom:6px;">{h1.name}</p>'
                    f'<p style="color:#94a3b8;font-size:0.88rem;margin:0;"><b>Evidence:</b> {h1.evidence_basis or "Sporadic Stripe HTTP 504 gateway timeouts on iOS checkout"}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col_hyp2:
                st.markdown(
                    f'<div class="hypothesis-card hypothesis-card-runnerup">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
                    f'<h4 style="color:#94a3b8;margin:0;font-size:1.0rem;">Hypothesis 2 (Secondary Rival)</h4>'
                    f'<span style="background:rgba(148,163,184,0.15);color:#cbd5e1;padding:2px 8px;border-radius:4px;font-weight:600;font-size:0.8rem;">{h2.likelihood_pct:.0f}% Likelihood</span>'
                    f'</div>'
                    f'<p style="font-size:0.98rem;font-weight:600;color:#ffffff;margin-bottom:6px;">{h2.name}</p>'
                    f'<p style="color:#94a3b8;font-size:0.88rem;margin:0;"><b>Evidence:</b> {h2.evidence_basis or "Competitor viral flash discount campaign on TikTok & ASEAN feeds"}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.markdown("#### Prescribed Low-Cost Discovery Tests (Pre-Capital Proof)")
        for test in presc.canary_validation_tests:
            st.markdown(
                f'<div class="canary-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<b style="color:#38bdf8;font-size:0.95rem;">{test.name}</b>'
                f'<div>'
                f'<span style="background:rgba(16,185,129,0.15);color:#6ee7b7;padding:2px 8px;border-radius:4px;font-weight:600;font-size:0.8rem;margin-right:6px;">Cost: ${test.estimated_cost_usd:.0f}</span>'
                f'<span style="background:rgba(56,189,248,0.15);color:#7dd3fc;padding:2px 8px;border-radius:4px;font-weight:600;font-size:0.8rem;">Runtime: {test.duration_hours:.1f}h</span>'
                f'</div>'
                f'</div>'
                f'<p style="margin-top:6px;margin-bottom:0;color:#cbd5e1;font-size:0.88rem;"><b>Objective:</b> {test.objective or test.description}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown("---")

    # Scenario 3: Cold Start Launch
    if result.scenario_id == "scenario_3" or (result.spc_result and result.spc_result.is_cold_start):
        st.markdown(COLDSTART_BADGE_HTML, unsafe_allow_html=True)
        st.info(
            "**Sparse-History Launch Guidance**: With limited operational history (N < 14 days), the engine blends a Bayesian Category Benchmark Prior ($5,000 baseline). "
            "Action playbooks emphasize staged pilot ramp-ups and weekly review gates rather than heavy capital pre-commitment."
        )

    # 3-Model Dual Diagnostic Grid
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(
            f'<div class="bi-panel" style="border-left:4px solid #0284c7;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
            f'<h4 style="color:#38bdf8;margin:0;font-size:1.0rem;">Model 1: Local Internal Diagnostic</h4>'
            f'<span style="background:rgba(56,189,248,0.15);color:#7dd3fc;padding:2px 8px;border-radius:4px;font-weight:600;font-size:0.8rem;">{presc.attribution_internal_pct:.0f}% Share</span>'
            f'</div>'
            f'<p style="margin-bottom:6px;font-size:0.9rem;"><b>Internal Root Cause:</b> Warehouse Staging Queue & ERP Backlog at <code>WH-WEST-01</code></p>'
            f'<div style="background:rgba(0,0,0,0.25);border-radius:6px;padding:6px 10px;color:#94a3b8;font-size:0.82rem;">'
            f'<b>Traceable Evidence:</b> <code>JIRA-4819</code>, <code>WH-WEST-01</code>, <code>ERP-BACKLOG-340</code> (340 unfulfilled orders)'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_m2:
        st.markdown(
            f'<div class="bi-panel" style="border-left:4px solid #f59e0b;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
            f'<h4 style="color:#fbbf24;margin:0;font-size:1.0rem;">Model 2: Live Macro Sentinel</h4>'
            f'<span style="background:rgba(245,158,11,0.15);color:#fcd34d;padding:2px 8px;border-radius:4px;font-weight:600;font-size:0.8rem;">{presc.attribution_external_pct:.0f}% Share</span>'
            f'</div>'
            f'<p style="margin-bottom:6px;font-size:0.9rem;"><b>External Shock:</b> West Coast Maritime Port Labor Slowdown & Congestion</p>'
            f'<div style="background:rgba(0,0,0,0.25);border-radius:6px;padding:6px 10px;color:#94a3b8;font-size:0.82rem;">'
            f'<b>Live Feed:</b> <code>MACRO-PORT-01</code> (FreightWaves Terminal Index: 8.5 Severity)'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Model 3 Executive Decision Hero Card
    st.markdown(
        f'<div class="brief-hero-box">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<h3 style="margin:0;font-size:1.15rem;">Model 3 Executive Decision Brief — {role.value}</h3>'
        f'<span style="background:rgba(2,132,199,0.2);color:#7dd3fc;padding:3px 10px;border-radius:4px;font-weight:600;font-size:0.82rem;">Expected ROI: {presc.estimated_roi_multiplier:.1f}x</span>'
        f'</div>'
        f'<h4 style="color:#38bdf8;margin-bottom:8px;font-size:1.0rem;">{presc.headline}</h4>'
        f'<p style="font-size:0.95rem;line-height:1.65;color:#e2e8f0;margin:0;">{presc.narrative}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Causal Driver Balance & Action Playbook
    col_p1, col_p2 = st.columns([2, 3])
    with col_p1:
        st.subheader("Causal Driver Balance")
        fig_pie = px.pie(
            values=[presc.attribution_internal_pct, presc.attribution_external_pct],
            names=["Internal Operational Backlog", "External Macro Port Shock"],
            color_discrete_sequence=["#0284c7", "#f59e0b"],
            hole=0.55
        )
        fig_pie.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=250,
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_pie, use_container_width=True, key=f"{key_prefix}_pie_chart")

    with col_p2:
        st.subheader(f"Action Playbook: Recommended Interventions ({role.value})")
        if role == UserRole.EXECUTIVE:
            st.markdown(
                """
- **Strategic Action 1 (Logistics):** Authorize rerouting of 35% maritime freight to Pacific Northwest (Seattle/Tacoma) port corridors.
- **Strategic Action 2 (Remediation):** Allocate $45,000 expedited drayage budget to clear high-margin APAC SKU backlogs.
- **Governance & SLAs:** Institute 14-day vendor SLA penalty enforcement for 3PL warehouse fulfillment delays.
                """
            )
        else:
            st.markdown(
                """
- **Tactical SOP 1:** Execute automated inventory re-allocation script across WH-West and WH-East for clusters `SKU-ELEC-409` and `SKU-APPR-102`.
- **Tactical SOP 2:** Triage Jira ticket `JIRA-4819` and expedite container release clearance at Long Beach Berth 4.
- **Operational SOP 3:** Trigger proactive fulfillment ETA adjustment notifications to tier-1 enterprise customers.
                """
            )
        st.markdown(
            f"<div style='background:rgba(16,185,129,0.1);border:1px solid #059669;border-radius:6px;padding:8px 14px;color:#6ee7b7;font-weight:500;display:inline-block;margin-top:6px;font-size:0.88rem;'>"
            f"Projected Financial Recovery: <b>{presc.estimated_roi_multiplier:.1f}x Net Return</b> (+320% Revenue Lift)"
            f"</div>",
            unsafe_allow_html=True
        )
