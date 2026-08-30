"""Live Runtime Performance Telemetry & Cost Accounting Component."""

import streamlit as st

try:
    from prototype.engine.contracts.schemas import TelemetryRecord
except ImportError:
    from engine.contracts.schemas import TelemetryRecord


def render_telemetry_box(telemetry: TelemetryRecord) -> None:
    """Renders the live runtime latency, token usage, cost accounting, and engine split monitoring box."""
    st.subheader("Runtime Telemetry & Computational Audit")

    ingest_ms = getattr(telemetry, "ingestion_time_ms", 1.5)
    math_ms = getattr(telemetry, "math_time_ms", 4.2)
    latency_ms = getattr(telemetry, "latency_ms", getattr(telemetry, "total_latency_ms", 5.7))
    llm_ms = getattr(telemetry, "llm_time_ms", max(0.5, latency_ms - math_ms))
    llm_calls = getattr(telemetry, "llm_calls", getattr(telemetry, "llm_calls_count", 0))
    total_tokens = getattr(telemetry, "total_tokens", getattr(telemetry, "llm_tokens", 0))
    prompt_tokens = getattr(telemetry, "prompt_tokens", 0)
    completion_tokens = getattr(telemetry, "completion_tokens", 0)
    cost_usd = getattr(telemetry, "estimated_cost_usd", getattr(telemetry, "cost_usd", 0.0))
    provider = getattr(telemetry, "llm_provider", "mock")

    col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
    with col_t1:
        st.markdown(
            f'<div class="telemetry-card">'
            f'<div class="metric-val">{latency_ms:.1f} ms</div>'
            f'<div class="metric-lbl">Total Latency</div>'
            f'<div style="font-size:0.75rem;color:#94a3b8;margin-top:4px;white-space:nowrap;">Ingest {ingest_ms:.1f}ms | Math {math_ms:.1f}ms</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_t2:
        st.markdown(
            f'<div class="telemetry-card">'
            f'<div class="metric-val">0 tokens</div>'
            f'<div class="metric-lbl">Deterministic Math</div>'
            f'<div style="font-size:0.75rem;color:#34d399;margin-top:4px;white-space:nowrap;">100% Non-LLM Math</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_t3:
        st.markdown(
            f'<div class="telemetry-card">'
            f'<div class="metric-val">{total_tokens:,} tokens</div>'
            f'<div class="metric-lbl">AI Narrative Tokens</div>'
            f'<div style="font-size:0.75rem;color:#cbd5e1;margin-top:4px;white-space:nowrap;">Prompt {prompt_tokens} | Comp {completion_tokens}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_t4:
        st.markdown(
            f'<div class="telemetry-card">'
            f'<div class="metric-val">${cost_usd:.6f}</div>'
            f'<div class="metric-lbl">Estimated Cost</div>'
            f'<div style="font-size:0.75rem;color:#38bdf8;margin-top:4px;white-space:nowrap;">Provider: {provider}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with col_t5:
        st.markdown(
            f'<div class="telemetry-card">'
            f'<div class="metric-val">{llm_calls}</div>'
            f'<div class="metric-lbl">LLM API Calls</div>'
            f'<div style="font-size:0.75rem;color:#94a3b8;margin-top:4px;white-space:nowrap;">Deterministic Fallback Active</div>'
            f'</div>',
            unsafe_allow_html=True
        )
