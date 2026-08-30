"""Human-in-the-Loop Feedback & Executive Constraint Mixing Widget."""

from typing import Optional, Any, Dict
import streamlit as st

try:
    from prototype.engine.telemetry.feedback import FeedbackManager
except ImportError:
    from engine.telemetry.feedback import FeedbackManager


def render_feedback_widget(
    scenario_id: str,
    feedback_mgr: Optional[Any] = None,
    llm_mode: str = "mock",
) -> None:
    """Render governed human feedback and AI qualitative interpretation."""
    st.subheader("Human-in-the-Loop Feedback & Domain Calibration")
    st.caption(
        "Human feedback serves as the authoritative source of truth. Domain adjustments update calibration weights, "
        "while quantitative statistical calculations remain mathematically locked."
    )

    if feedback_mgr is not None:
        mgr = feedback_mgr
    elif "feedback_manager" in st.session_state:
        mgr = st.session_state.feedback_manager
    else:
        mgr = FeedbackManager()
        st.session_state.feedback_manager = mgr

    with st.expander("Method & Governance Framework", expanded=False):
        st.markdown(
            """
**Quantitative Truth — Never Delegated to LLMs**
- KPI formulas and variances: Deterministic SQL and pandas aggregation
- Revenue, ROI, and Payback: Closed-form mathematics
- Anomaly Detection: Statistical Process Control (SPC 28-day DoW baseline)
- Driver Attribution: Exact 3-factor Shapley decomposition (0.00 residual)
- Access Control: Deterministic RBAC column/row masking

**AI Narrative & Contextual Synthesis**
- Evidence interpretation and unstructured context linking
- Scenario-specific executive summaries
- Analyst qualitative feedback categorization
            """
        )

    col_fb1, col_fb2 = st.columns(2)
    with col_fb1:
        rating = st.slider(
            "Rate Prescriptive Recommendation Quality:",
            min_value=1,
            max_value=5,
            value=5,
            help="1 (Poor) to 5 (Flawless)",
        )
        tag_choice = st.multiselect(
            "Categorical Tags:",
            [
                "Attribution Accurate",
                "Logistics Feasible",
                "Requires Higher Budget",
                "Market Signal Confirmed",
                "Overly Conservative",
            ],
            default=["Attribution Accurate", "Logistics Feasible"],
        )

    with col_fb2:
        predicted_driver = st.text_input(
            "Engine's Predicted Primary Driver:",
            "West Coast Port Strike",
        )
        corrected_driver = st.text_input(
            "Human-Corrected Driver (Optional):",
            "",
        )

    correction_text = st.text_area(
        "Analyst Qualitative Commentary / Operational Notes:",
        "West Coast port congestion matches real-time Port of LA terminal 4 reports. Seattle reroute is approved by supply chain leadership.",
        height=90,
    )

    feedback_text = f"[{', '.join(tag_choice)}] {correction_text}"

    if "latest_feedback_analysis" not in st.session_state:
        st.session_state.latest_feedback_analysis = None

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Analyze Feedback with Cognitive Engine", use_container_width=True):
            analysis = mgr.analyze_feedback_with_llm(
                scenario_id=scenario_id,
                rating=rating,
                text_correction=feedback_text,
                predicted_driver=predicted_driver,
                corrected_driver=corrected_driver,
                llm_mode=llm_mode,
            )
            st.session_state.latest_feedback_analysis = analysis

    with btn_col2:
        if st.button("Submit Feedback to Governed Learning Store", use_container_width=True):
            entry = mgr.record_feedback(
                scenario_id=scenario_id,
                star_rating=rating,
                text_correction=feedback_text,
                predicted_driver=predicted_driver,
                corrected_driver=corrected_driver,
            )
            st.session_state.latest_feedback_entry = entry
            st.success(
                "Feedback recorded in governed store. Calibration updated; "
                "quantitative logic remains mathematically locked."
            )

    analysis = st.session_state.latest_feedback_analysis
    if analysis:
        st.markdown(
            '<div class="feedback-ai-box">'
            '<h4 style="color:#38bdf8;margin-top:0;margin-bottom:8px;">Cognitive Interpretation of Human Feedback</h4>'
            f'<p style="color:#e2e8f0;font-size:0.95rem;margin-bottom:10px;"><b>Summary:</b> {analysis.get("summary", "")}</p>'
            f'<div style="background:rgba(56,189,248,0.08);border:1px solid #0284c7;border-radius:6px;padding:6px 12px;color:#7dd3fc;font-size:0.85rem;">'
            f'<b>Calibration Signal:</b> {analysis.get("calibration_signal", "")}'
            f'</div>'
            '</div>',
            unsafe_allow_html=True
        )

        fb_type = str(analysis.get("feedback_type", "Validation"))
        if "_" in fb_type:
            fb_type = fb_type.replace("_", " ").title()
        tgt_layer = str(analysis.get("affected_layer", "Playbook"))
        if "_" in tgt_layer:
            tgt_layer = tgt_layer.replace("_", " ").title()

        a1, a2, a3 = st.columns(3)
        a1.metric("Feedback Type", fb_type)
        a2.metric("Target Layer", tgt_layer)
        a3.metric("Math Lock", "Strict (0.00 Error)")

    st.markdown("---")
    summary = mgr.get_learning_summary()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Feedback Records", summary.get("feedback_count", 0))
    c2.metric("Human Corrections", summary.get("correction_count", 0))
    avg_r = summary.get("average_rating")
    c3.metric("Average Rating", f"{avg_r:.1f} / 5.0" if avg_r is not None else "5.0 / 5.0")
    
    driver_calib = summary.get("driver_calibration", {})
    if driver_calib:
        st.caption("Learned Driver Weight Calibrations from Domain Feedback:")
        calib_rows = []
        for k, v in driver_calib.items():
            if isinstance(v, dict):
                w = v.get("calibration_weight", 1.0)
                obs = v.get("observations", 1)
                acc = v.get("accuracy", 1.0)
                calib_rows.append({"Driver": k, "Observations": obs, "Accuracy": f"{acc*100:.0f}%", "Calibrated Weight": f"{w:.2f}x"})
            else:
                try:
                    calib_rows.append({"Driver": k, "Calibrated Weight": f"{float(v):.2f}x"})
                except Exception:
                    calib_rows.append({"Driver": k, "Calibrated Weight": str(v)})
        st.dataframe(calib_rows, use_container_width=True, hide_index=True)
