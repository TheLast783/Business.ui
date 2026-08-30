# BusinessIntelligence.ai — KPI Intelligence-to-Action Engine

> **Accenture Business Statistics Round 2 Competition Prototype**  
> Production-grade, interactive Decision Workspace connecting multi-source data streams, deterministic closed-form mathematics, governed 3-model AI synthesis, explicit abstention protocols, and role-based access control.

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────────────┐
                               │  Heterogeneous Multi-Source Ingestion  │
                               │  ├── Daily ERP Sales Ledger (Daily)    │
                               │  ├── Hourly Web Clickstream (Hourly)   │
                               │  └── Weekly Jira / Support Logs (Weekly│
                               └──────────────────┬─────────────────────┘
                                                  │
                                                  ▼
                               ┌────────────────────────────────────────┐
                               │    Governed Semantic Data Contract     │
                               │    ├── Calendar Date Harmonization     │
                               │    └── Role-Based Access Control (RBAC)│
                               └──────────────────┬─────────────────────┘
                                                  │
                ┌─────────────────────────────────┴─────────────────────────────────┐
                ▼                                                                   ▼
┌───────────────────────────────────────┐                   ┌───────────────────────────────────────┐
│       📐 DETERMINISTIC MATH CORE      │                   │        🤖 3-MODEL AI SYNTHESIS        │
│   (Zero Hallucination / 0 LLM Tokens) │                   │  (Multi-Model Governed Intelligence)  │
├───────────────────────────────────────┤                   ├───────────────────────────────────────┤
│ • Statistical Process Control (SPC)   │                   │ • Model 1: Local Internal Diagnostic  │
│   - 28-Day Baseline + Seasonality     │                   │ • Model 2: Live Macro Sentinel API    │
│   - 2.5σ Anomaly Detection            │                   │ • Model 3: Prescriptive Story Brief   │
│ • Shapley Causal Metric Tree          │                   │ • Explicit Abstention Protocol        │
│   - ΔRev = ΔSessions + ΔCVR + ΔAOV    │                   │ • 30/60/90-Day Trajectory Simulation  │
│   - Zero-Residual Identity Guaranteed │                   │ • Pluggable Mock / Live LLM Client    │
└───────────────────────────────────────┘                   └───────────────────────────────────────┘
                │                                                                   │
                └─────────────────────────────────┬─────────────────────────────────┘
                                                  │
                                                  ▼
                               ┌────────────────────────────────────────┐
                               │ Streamlit Interactive Decision Portal │
                               │  ├── Scenario Selector (Scenarios 1-4) │
                               │  ├── Persona Switcher (Exec vs Analyst)│
                               │  ├── 30/60/90-Day ROI Trajectory Simulator
                               │  ├── Human-in-the-Loop Feedback Store  │
                               │  └── Real-Time Latency & Cost Telemetry│
                               └────────────────────────────────────────┘
```

---

## 🚀 Key Features & Capabilities

### 1. Visual Distinction Contract
- **Deterministic Math Core** styled with Cobalt Blue (`#1E88E5` / `#00E5FF`) and pill badges confirming closed-form exact calculation and 0 token consumption.
- **AI Synthesis Engine** styled with Amethyst Purple (`#8E24AA` / `#E1BEE7`) and provenance indicators confirming multi-model governed synthesis.

### 2. Four Core Scenarios (R4)
1. **Scenario 1: Multi-Factor Supply Disruption**
   - Compound 70% external macro port strike + 30% internal warehouse backlog attribution.
2. **Scenario 2: Low-Confidence Ambiguity & Explicit Abstention**
   - Triggers when hypothesis confidence margin < 25% (16% observed).
   - Renders Amber/Red Abstention Banner, 2 competing ranked hypotheses (58% Stripe timeout vs 42% TikTok flash campaign), and 2 low-cost canary validation tests (< $150).
3. **Scenario 3: Sparse-History / Cold-Start Launch**
   - Detects N = 6 days (< 14 days mature threshold).
   - Engages Bayesian category prior baseline ($5,000) and displays widened uncertainty envelope (±45%).
4. **Scenario 4: Role-Based Security & Data Entitlement (RBAC)**
   - **Operations Analyst**: Dynamic field redaction on sensitive margins and unit COGS (`[RESTRICTED-EXEC]`), while preserving unmasked Jira keys and container codes.
   - **Executive / VP**: Full numeric transparency, strategic risk levers, and EBITDA recovery horizons.

### 3. Forward Trajectory ROI Simulator (R3)
- Multi-line Plotly curve comparing **Status Quo Decay**, **Recommended Strategy**, and **Executive Constrained Strategy**.
- Dynamic response to budget cap sliders, optimization horizons, and directive overrides.

### 4. Traceable Lineage & Telemetry (R5)
- Data Source Freshness SLA table across ERP, Web, and Jira.
- Live performance telemetry tracking Ingestion latency, Math latency, LLM latency, token counts, and API cost ($0.00 in mock mode).

---

## 📦 Setup & Execution

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### Installation
```bash
pip install -r prototype/requirements.txt
```

### Launch Interactive Streamlit App
```bash
streamlit run prototype/app.py
```
Open `http://localhost:8501` in your browser.

### Run Headless Verification Test Suite
```bash
# Run headless comprehensive acceptance test suite
py -3.11 prototype/test_scenarios.py

# Run modular unit tests
py -3.11 -m unittest discover -s prototype/tests -p "test_*.py"
```

---

## 🧪 Verification Matrix

| Component | Verification Target | Test Command | Status |
| :--- | :--- | :--- | :--- |
| **Data Contracts** | Schema validation across ERP, Web, and Jira | `test_scenarios.py` Tier 3 | ✅ Verified |
| **SPC Core** | Seasonality correction, 2.5σ anomaly trigger | `test_scenarios.py` Tier 1 | ✅ Verified |
| **Causal Tree** | Zero-residual Shapley attribution | `test_scenarios.py` Tier 1 | ✅ Verified |
| **3-Model Synthesis** | Multi-model integration & offline fallback | `test_scenarios.py` Tier 1 | ✅ Verified |
| **Abstention Protocol** | Conflicting hypotheses & canary tests | `test_scenarios.py` Tier 1 | ✅ Verified |
| **Cold-Start Engine** | Bayesian benchmark prior & uncertainty | `test_scenarios.py` Tier 1 | ✅ Verified |
| **RBAC Security** | Persona masking & unmasking | `test_scenarios.py` Tier 1 | ✅ Verified |
| **Interactive UI** | Clean py_compile & Streamlit integration | `py_compile prototype/app.py` | ✅ Verified |

---
*Built with precision for the Accenture Business Statistics Round 2 Competition.*


---

## Round 2 Upgrade Pack — KPI Intelligence-to-Action

This prototype now adds a governed decision layer on top of the existing 4-scenario engine.

### Added capabilities

1. **KPI materiality & prioritisation**
   - Deterministic 0–100 materiality score.
   - Combines statistical severity, business impact, movement magnitude, KPI criticality and confidence.
   - Ranks Gross Revenue, Order Volume, Conversion Rate and AOV.
   - No LLM calls are used to calculate the score.

2. **Source health & freshness**
   - ERP (daily), Web Analytics (hourly), and Jira/Support (weekly) are assessed for freshness SLA, timestamp quality, grain, row count and owner.
   - The UI exposes the reconciliation/health matrix.

3. **Governed action contract**
   - Recommendations now expose: controllable lever, expected impact, owner, confidence, decision rights, constraints and monitoring plan.
   - Existing ROI simulation remains the quantitative source of truth.

4. **Human feedback learning loop**
   - Analyst ratings and explicit driver corrections are persisted to a small JSON learning store.
   - Historical corrections produce driver calibration/accuracy signals.
   - This is a lightweight ranking/calibration loop, **not LLM training**.

5. **Optional live data connectors**
   - Dependency-free REST connector registry for ERP, Web Analytics, Jira and external-event feeds.
   - Configure endpoints through environment variables when real systems are available.
   - Synthetic deterministic feeds remain the default for reproducible judging.

6. **Expanded telemetry**
   - Explicit LLM API-call count, cache-hit count and cost-per-insight fields.
   - Mock mode reports zero external LLM calls and zero API cost.

7. **Governed access/audit preview**
   - Domain entitlements and column-level masking are surfaced in the data workspace.
   - Existing RBAC masking behavior remains unchanged.

### Important architecture boundary

The system intentionally does **not** claim to train an LLM on the business KPI data:

`Data sources → semantic reconciliation → deterministic KPI/SPC/contribution analysis → evidence → confidence/abstention → LLM narrative/recommendation synthesis → human feedback → calibration`

The LLM is therefore not treated as quantitative truth.

### Validation

The original 93-test baseline remains intact, and an additional 8 Round 2 upgrade tests cover materiality, source health, feedback learning, structured actions, telemetry and connector readiness.
