"""BusinessIntelligence.ai — Clean Enterprise Design System."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #090e17;
  --panel: #0f172a;
  --panel-border: #1e293b;
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --accent-blue: #0284c7;
  --accent-cyan: #38bdf8;
  --accent-green: #10b981;
  --accent-amber: #f59e0b;
}

/* Global App Container */
.stApp {
  background: #090e17;
  color: #f8fafc;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.main .block-container {
  padding-top: 1.5rem;
  padding-bottom: 3.5rem;
  max-width: 1480px;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em !important;
  color: #ffffff !important;
}
h1 { font-size: 1.85rem !important; }
h2 { font-size: 1.35rem !important; margin-top: 0.8rem !important; }
h3 { font-size: 1.1rem !important; }
p, li { color: #cbd5e1; font-size: 0.92rem; line-height: 1.6; }
code, pre { font-family: 'JetBrains Mono', monospace !important; font-size: 0.86rem !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: #0b111e !important;
  border-right: 1px solid #1e293b !important;
}
section[data-testid="stSidebar"] > div {
  padding-top: 1.2rem;
}
section[data-testid="stSidebar"] label {
  color: #94a3b8 !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
}

/* Inputs & Selectboxes */
div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {
  background: #0f172a !important;
  border: 1px solid #334155 !important;
  border-radius: 8px !important;
  color: #f8fafc !important;
  font-size: 0.9rem !important;
}
div[data-baseweb="select"] > div:hover, .stTextInput input:focus, .stTextArea textarea:focus {
  border-color: #0284c7 !important;
}

/* Multiselect Tag Badges - Clean & Un-truncated */
div[data-baseweb="tag"], span[data-baseweb="tag"] {
  background: #1e293b !important;
  color: #f1f5f9 !important;
  border: 1px solid #3b82f6 !important;
  border-radius: 6px !important;
  padding: 4px 10px !important;
  margin: 3px 4px !important;
  display: inline-flex !important;
  white-space: nowrap !important;
  max-width: none !important;
  overflow: visible !important;
}
div[data-baseweb="tag"] span, span[data-baseweb="tag"] span {
  color: #f1f5f9 !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  white-space: nowrap !important;
  overflow: visible !important;
}
div[data-baseweb="tag"] svg, span[data-baseweb="tag"] svg {
  fill: #94a3b8 !important;
}

/* KPI Summary Cards */
div[data-testid="metric-container"] {
  background: #0f172a !important;
  border: 1px solid #1e293b !important;
  border-radius: 12px !important;
  padding: 14px 18px !important;
  min-height: 100px;
}
div[data-testid="metric-container"] label {
  color: #94a3b8 !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  color: #ffffff !important;
  font-size: 1.55rem !important;
  font-weight: 700 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
  font-size: 0.82rem !important;
  font-weight: 500 !important;
}

/* Professional Cards & Panels */
.bi-panel, .brief-hero-box, .telemetry-card, .hypothesis-card, .canary-card, .feedback-ai-box {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 12px;
}
.bi-panel { padding: 18px; margin-bottom: 14px; }
.brief-hero-box {
  border-left: 4px solid #0284c7 !important;
  padding: 20px 24px;
  margin: 12px 0 20px;
}
.feedback-ai-box {
  border-left: 4px solid #38bdf8 !important;
  padding: 18px 22px;
  margin: 12px 0 16px;
  background: #0b1322;
}

/* Telemetry Card - Resilient Layout */
.telemetry-card {
  padding: 14px 16px;
  text-align: center;
  border: 1px solid #334155;
  background: #0f172a;
}
.telemetry-card .metric-val {
  font-size: 1.25rem;
  font-weight: 700;
  color: #38bdf8;
  white-space: nowrap !important;
  letter-spacing: -0.01em;
}
.telemetry-card .metric-lbl {
  font-size: 0.72rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 4px;
  white-space: nowrap !important;
}

/* Status Badges - Text Only */
.badge-math-core, .badge-ai-engine, .badge-abstention, .badge-coldstart, .badge-rbac-active {
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.72rem;
  letter-spacing: 0.03em;
  display: inline-block;
  margin-bottom: 6px;
}
.badge-math-core { color: #38bdf8; background: rgba(56, 189, 248, 0.08); border: 1px solid #0284c7; }
.badge-ai-engine { color: #c084fc; background: rgba(192, 132, 252, 0.08); border: 1px solid #7c3aed; }
.badge-abstention { color: #f59e0b; background: rgba(245, 158, 11, 0.08); border: 1px solid #d97706; }
.badge-coldstart { color: #34d399; background: rgba(52, 211, 153, 0.08); border: 1px solid #059669; }
.badge-rbac-active { color: #94a3b8; background: #0f172a; border: 1px solid #334155; }

/* Tabs */
div[data-baseweb="tab-list"] {
  gap: 6px;
  background: #0b111e;
  padding: 4px 6px;
  border-radius: 10px;
  border: 1px solid #1e293b;
  margin-bottom: 16px;
}
button[data-baseweb="tab"] {
  color: #94a3b8 !important;
  font-weight: 500 !important;
  font-size: 0.88rem !important;
  border-radius: 8px !important;
  padding: 8px 14px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: #ffffff !important;
  background: #1e293b !important;
  font-weight: 600 !important;
}
div[data-baseweb="tab-highlight"] { display: none !important; }

/* Buttons */
.stButton > button {
  background: #0284c7 !important;
  border: 1px solid #0369a1 !important;
  border-radius: 8px !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  font-size: 0.9rem !important;
  padding: 8px 18px !important;
}
.stButton > button:hover {
  background: #0369a1 !important;
  border-color: #38bdf8 !important;
}

/* Hypothesis & Canary Cards */
.hypothesis-card {
  padding: 16px;
  margin-bottom: 12px;
}
.hypothesis-card-winner { border-left: 4px solid #f59e0b; }
.hypothesis-card-runnerup { border-left: 4px solid #64748b; }
.canary-card {
  padding: 14px 18px;
  margin-bottom: 10px;
  border-left: 4px solid #0284c7;
}
</style>
"""

MATH_CORE_BADGE_HTML = '<div class="badge-math-core">DETERMINISTIC MATH CORE · STATISTICAL & CAUSAL LOGIC</div>'
AI_ENGINE_BADGE_HTML = '<div class="badge-ai-engine">AI SYNTHESIS ENGINE · GOVERNED NARRATIVE</div>'
ABSTENTION_BADGE_HTML = '<div class="badge-abstention">ABSTENTION · LOW CONFIDENCE MARGIN</div>'
COLDSTART_BADGE_HTML = '<div class="badge-coldstart">COLD START · BAYESIAN PRIOR ACTIVE</div>'
RBAC_BADGE_HTML = '<div class="badge-rbac-active">RBAC ACTIVE · FIELD-LEVEL MASKING</div>'
