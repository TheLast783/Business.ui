# Project: BusinessIntelligence.ai KPI Intelligence-to-Action Engine Prototype

## Architecture & System Overview
The BusinessIntelligence.ai KPI Intelligence-to-Action Engine prototype reconciles heterogeneous multi-source business data, separates signal from noise with deterministic Statistical Process Control (SPC), decomposes KPI movements down causal metric trees with zero-residual exact math, synthesizes internal operational context and live market shocks across a 3-model AI architecture with pluggable fallbacks, generates persona-tailored actionable briefs, simulates future 30/60/90-day trajectory ROI with dynamic executive constraints, handles ambiguity with explicit abstention, and records live runtime telemetry.

```
+---------------------------------------------------------------------------------------------------+
|                                  USER / STREAMLIT UI (app.py)                                     |
|  - Scenario Selector (1, 2, 3, 4)                                                                 |
|  - Persona Switcher (Executive / VP vs Operations / Category Manager)                             |
|  - Human-in-the-Loop Feedback & Executive Constraint Mixing Sliders                              |
|  - Distinct Visual Badges: 📐 DETERMINISTIC MATH CORE vs 🤖 AI SYNTHESIS ENGINE                  |
|  - Evidence & Lineage Drawer & Live Telemetry Box (ms, tokens, math vs LLM split, cost)          |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                    SCENARIO RUNNER ENGINE                                         |
|  - Scenario 1: Multi-Factor KPI Movement (70% Port Strike + 30% WMS Inventory Backlog)            |
|  - Scenario 2: Low-Confidence / Ambiguous Scenario (Explicit Abstention & 2 Canary Tests)        |
|  - Scenario 3: Sparse-History / Cold-Start Launch (Bayesian Prior, Wide Uncertainty Bands)         |
|  - Scenario 4: Role-Based Entitlements (Dynamic Masking of Sensitive Cost/Margin Columns)         |
+---------------------------------------------------------------------------------------------------+
          |                                                                   |
          v                                                                   v
+------------------------------------+             +------------------------------------------------+
|    HETEROGENEOUS DATA LAYER (R1)   |             |       DETERMINISTIC ANALYTICAL CORE (R2)       |
| - Daily ERP Sales Transactions     |             | - 28-day DoW Normalized SPC (>2.5σ Anomaly)    |
| - Hourly Web Session Stream        |             | - Exact Shapley Causal Metric Tree Math        |
| - Weekly Jira & Support Logs       |             |   (ΔRevenue = ΔSessions + ΔCVR + ΔAOV + Res=0) |
| - Governed Semantic Contract & RBAC|             | - Zero LLM Math, Zero Hallucinations           |
+------------------------------------+             +------------------------------------------------+
                                                                      |
                                                                      v
+---------------------------------------------------------------------------------------------------+
|                        3-MODEL AI SYNTHESIS & PLUGGABLE FALLBACK ENGINE (R3)                      |
| - Model 1 (Internal Diagnostic): Isolates operational bottlenecks from Jira & ERP Backlog         |
| - Model 2 (Macro Sentinel): Quantifies external shocks (Port strikes, competitor price moves)     |
| - Model 3 (Prescriptive Action & Trajectory ROI Simulator):                                       |
|     * Multi-Factor Synthesis & Ambiguity Abstention Filter                                        |
|     * 30/60/90-Day Trajectory Revenue Simulation: R_sq(t), R_rec(t), R_constr(t)                  |
|     * Dynamic Executive Mind-Mixing (Budget cap, time horizon, policy overrides)                  |
| - Pluggable Fallback Provider: Live OpenAI/Gemini/Ollama API + Instant Deterministic Mock Mode    |
+---------------------------------------------------------------------------------------------------+
```

---

## Code Layout
The target prototype code resides exclusively under `prototype/`:

```
prototype/
├── README.md                           # Comprehensive documentation, setup & execution instructions
├── requirements.txt                     # Dependencies: streamlit, pandas, numpy, plotly, pydantic
├── app.py                              # Main Streamlit web application entry point
├── test_scenarios.py                   # Standalone headless test suite covering all scenarios & tiers
├── verify_e2e.py                       # 8-way persona and scenario matrix verification runner
├── engine/                             # Headless analytics & AI engine
│   ├── __init__.py
│   ├── config.py                       # Global settings, anomaly thresholds, token pricing rates
│   ├── contracts/                      # Governed Semantic Contract & RBAC
│   │   ├── __init__.py
│   │   ├── semantic_contract.py        # Canonical KPI formulas, lineage graph, RBAC masking rules
│   │   └── schemas.py                  # Pydantic/dataclass schemas for records, anomalies, payloads
│   ├── data/                           # Multi-source data generation & ingestion
│   │   ├── __init__.py
│   │   ├── generator.py                # Deterministic synthetic data generator for 4 scenarios
│   │   └── loader.py                   # Ingestion, validation, join and grain normalization
│   ├── math/                           # Deterministic Non-LLM Mathematical Core
│   │   ├── __init__.py
│   │   ├── spc.py                      # Statistical Process Control (28-day rolling baseline, 2.5σ)
│   │   ├── causal_tree.py              # Exact closed-form Shapley metric tree decomposition
│   │   └── metrics.py                  # Standard business KPI calculation utilities
│   ├── synthesis/                      # 3-Model AI Synthesis & Fallback Architecture
│   │   ├── __init__.py
│   │   ├── model1_diagnostic.py        # Model 1: Internal diagnostic analysis
│   │   ├── model2_macro.py             # Model 2: Macro sentinel analysis
│   │   ├── model3_prescriptive.py      # Model 3: Action brief & 30/60/90-day trajectory ROI simulator
│   │   ├── providers.py                # Pluggable LLM client (OpenAI/Gemini/Ollama/Deterministic Mock)
│   │   └── abstention.py               # Confidence scoring, hypothesis ranking, canary test generator
│   ├── scenarios/                      # Scenario orchestration & configurations
│   │   ├── __init__.py
│   │   ├── runner.py                   # Unified scenario execution pipeline
│   │   ├── scenario1_multifactor.py    # Scenario 1 compound attribution setup
│   │   ├── scenario2_ambiguous.py      # Scenario 2 conflicting signals & abstention setup
│   │   ├── scenario3_coldstart.py      # Scenario 3 sparse history & cold-start baseline
│   │   └── scenario4_rbac.py           # Scenario 4 role-based entitlement & masking data
│   └── telemetry/                      # Performance, cost & feedback tracking
│       ├── __init__.py
│       ├── tracker.py                  # Latency (ms), token counter, math vs LLM breakdown, cost calculator
│       └── feedback.py                 # Feedback persistence & executive constraint state manager
├── ui/                                 # Streamlit UI Components & Layout
│   ├── __init__.py
│   ├── styles.py                       # CSS styles, visual badge definitions, container themes
│   └── components/                     # Modular UI components
│       ├── __init__.py
│       ├── header.py                   # Header title, engine status, KPI summary ribbon
│       ├── sidebar.py                  # Scenario selector, persona switcher, engine mode controls
│       ├── spc_view.py                 # Plotly SPC chart rendering with control limits & anomaly points
│       ├── tree_view.py                # Causal metric tree waterfall attribution chart & LaTeX math
│       ├── synthesis_view.py           # 3-Model narrative cards, abstention banner, persona briefs
│       ├── simulation_view.py          # 30/60/90-day trajectory ROI projection chart
│       ├── feedback_widget.py          # Human-in-the-loop ratings, corrections & constraint mixing sliders
│       ├── lineage_drawer.py           # Expandable evidence drawer, data freshness & raw citations
│       └── telemetry_box.py            # Latency, token usage, cost and engine breakdown cards
└── tests/                              # Milestone and Stress Unit Test Suites
    ├── test_milestone1.py              # 19 tests for Data Architecture & Semantic Contract
    ├── test_milestone2.py              # 30 tests for SPC & Shapley Math Core
    ├── test_milestone3.py              # 35 tests for 3-Model AI Synthesis & Fallbacks
    ├── test_milestone4.py              # 27 tests for Scenarios, Persona Storytelling & Telemetry
    ├── test_milestone5.py              # 8 tests for Streamlit UI Components & Badges
    └── test_empirical_stress.py        # 15 adversarial stress tests (10,000 randomized Shapley trials)
```

---

## Feature Inventory
Every feature from the Survey phase is enumerated below with its assigned milestone and status:

| # | Feature | Description | Milestone | Status |
|---|---------|-------------|-----------|--------|
| 1 | 4 Connected KPIs Definition | Canonical formulas for Gross Revenue, Order Volume, Conversion Rate, AOV | M1 | DONE |
| 2 | Multi-Source Heterogeneous Data Generation | Daily ERP SQL table, Hourly Web Analytics stream, Weekly Jira/Support logs | M1 | DONE |
| 3 | Governed Semantic Contract | Declarative contract with formulas, lineage, invariant checks | M1 | DONE |
| 4 | RBAC Policy & Data Masking Engine | Dynamic column/row masking on sensitive cost/margin fields for non-executives | M1 | DONE |
| 5 | Seasonality-Normalized SPC Engine | 28-day rolling baseline, Day-of-Week seasonality index, >2.5σ anomaly trigger | M2 | DONE |
| 6 | Exact Causal Metric Tree Decomposition | Closed-form Shapley / LMDI zero-residual attribution ($R = S \times CR \times AOV$) | M2 | DONE |
| 7 | Model 1 Internal Diagnostic | Isolation of operational root causes from Jira tickets & ERP order backlog | M3 | DONE |
| 8 | Model 2 Macro Sentinel | Ingestion and quantification of external macro/supply chain shock feeds | M3 | DONE |
| 9 | Model 3 Multi-Factor Synthesis | Integration of Model 1 + 2 findings with exact tree attribution percentages | M3 | DONE |
| 10 | Model 3 Trajectory ROI Simulator | Mathematical 30/60/90-day trajectory revenue simulation ($R(t)$, Net ROI, Payback) | M3 | DONE |
| 11 | Ambiguity & Explicit Abstention Engine | Abstention trigger on conflicting evidence, ranked hypotheses (58% vs 42%), canary tests | M3 | DONE |
| 12 | Pluggable LLM Provider & Deterministic Mock | Live OpenAI/Gemini/Ollama support + instant deterministic zero-dependency fallback | M3 | DONE |
| 13 | Persona Storytelling Engine | Executive/VP (strategic levers, macro ROI) vs Operations Manager (playbooks, system IDs) | M4 | DONE |
| 14 | Scenario 1 Runner (Multi-Factor) | Compound attribution: 70% macro port strike + 30% internal inventory backlog | M4 | DONE |
| 15 | Scenario 2 Runner (Abstention) | Conflicting signals, explicit abstention flag, competing hypotheses, validation tests | M4 | DONE |
| 16 | Scenario 3 Runner (Cold Start) | Sparse history ($N=6 < 14$), Bayesian category prior, wide uncertainty bands ($\pm 45\%$) | M4 | DONE |
| 17 | Scenario 4 Runner (RBAC View) | Role-based data masking and differentiated analysis views | M4 | DONE |
| 18 | Runtime Telemetry & Cost Accounting | Latency (ms), token counts, deterministic math vs LLM split, cost ($) tracking | M4 | DONE |
| 19 | Human-in-the-Loop Feedback & Mind Mixing | Star ratings, corrections, and executive constraint mixing sliders | M4 | DONE |
| 20 | Streamlit Main App & Theme Styling | Responsive layout, custom CSS badges (Deterministic Math vs AI Synthesis) | M5 | DONE |
| 21 | Interactive Plotly SPC & Tree Views | Interactive SPC control chart + Metric Tree waterfall attribution chart | M5 | DONE |
| 22 | Synthesis, Simulation & Lineage UI Components | 3-Model cards, 30/60/90 trajectory chart, Lineage drawer, Telemetry footer | M5 | DONE |
| 23 | Headless E2E Test Suite (`test_scenarios.py`) | Comprehensive assertion suite covering all 4 scenarios, math invariants, and RBAC | E2E | DONE |
| 24 | Final E2E Test Pass & Hardening | 100% pass on all headless test assertions + adversarial stress testing | M6 | DONE |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| **E2E** | E2E Headless Test Suite & Harness | `prototype/test_scenarios.py` (93 test cases across Tiers 1-4) | Survey | **DONE** |
| **M1** | Data Architecture & Governed Semantic Contract | `prototype/engine/contracts/`, `prototype/engine/data/` | Survey | **DONE** |
| **M2** | Deterministic Non-LLM Math Core | `prototype/engine/math/` (SPC with DoW Seasonality, Exact Shapley Tree Decomposition) | M1 | **DONE** |
| **M3** | 3-Model AI Synthesis & Pluggable Fallbacks | `prototype/engine/synthesis/` (Models 1, 2, 3, Abstention Engine, Providers) | M2 | **DONE** |
| **M4** | Persona Storytelling, Scenarios & Telemetry | `prototype/engine/scenarios/`, `prototype/engine/telemetry/` | M3 | **DONE** |
| **M5** | Streamlit Interactive Decision Workspace UI | `prototype/ui/`, `prototype/app.py`, `prototype/README.md` | M4 | **DONE** |
| **M6** | Final Milestone: 100% E2E Test Pass & Audit | Full verification, Adversarial stress testing, Forensic Integrity Audit | M5, E2E | **DONE** |
