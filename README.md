# ⚡ BusinessIntelligence.ai — KPI Intelligence-to-Action Engine
### Accenture Innovation Challenge 2026 • Team Warriors (IIT Patna)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit%201.30+-FF4B4B.svg)](https://streamlit.io/)
[![Zero Math Hallucinations](https://img.shields.io/badge/Math%20Core-Deterministic%20Non--LLM-emerald.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-142%2F142%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

---

## 📌 Executive Summary

Modern enterprise dashboards excel at reporting **WHAT** happened, but fail completely at explaining **WHY** or **WHAT TO DO NEXT**. When a critical business KPI drops (e.g., a 12% revenue drop), dashboards turn red, forcing human analysts to spend 4 to 7 days manually digging through ERP databases, Jira logs, and external news feeds. Generic LLMs exacerbate the problem by hallucinating mathematical calculations and risking private company data leakage.

**BusinessIntelligence.ai (CausaMetric Engine)** solves this with a **Two-Tier Cognitive Intelligence Architecture**:
1. **Deterministic Non-LLM Mathematical Core:** Employs **28-Day Day-of-Week Normalized Statistical Process Control (SPC)** ($>2.5\sigma$) to filter out seasonal noise, paired with an **Exact Closed-Form Shapley Causal Metric Tree** decomposition with **$0.00$ residual error** and **$0$ LLM math tokens consumed**.
2. **3-Model Cognitive AI Synthesis Loop:** 
   - **Model 1 (Private Local Diagnostic Specialist):** Runs 100% on-premise to diagnose internal ERP and Jira backlogs without data leaks.
   - **Model 2 (Live Real-Time Macro Sentinel):** Ingests live global news/APIs to detect external shocks (port strikes, competitor promos).
   - **Model 3 (Prescriptive Action & 30/60/90-Day Trajectory ROI Simulator):** Reconciles causal attribution shares, simulates future recovery trajectories under executive budget caps, and enforces **Explicit Abstention** with low-cost canary validation tests when evidence is ambiguous.

---

## 🏛️ System Architecture

```
[ Structured Daily ERP Sales ]     [ Hourly Web Analytics Stream ]     [ Weekly Jira Incident Logs ]
             │                                   │                                    │
             ▼                                   ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                      GOVERNED SEMANTIC CONTRACT & DATA HARMONIZATION                        │
│          • Canonical Daily Grain Alignment    • Dynamic Role-Based Data Masking (RBAC)      │
└───────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            DETERMINISTIC NON-LLM ANALYTICAL CORE                            │
│  1. Statistical Process Control (SPC): 28-day DoW normalized baseline (Anomaly: >2.5σ)      │
│  2. Exact Shapley Causal Metric Tree: ΔR = ΔSessions + ΔCVR + ΔAOV (Residual ≡ 0.00000000)  │
└───────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                │ (Triggers ONLY on True Anomalies)
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 3-MODEL AI SYNTHESIS LOOP                                   │
│                                                                                             │
│  ┌─────────────────────────────────────────┐       ┌─────────────────────────────────────┐  │
│  │       MODEL 1: LOCAL DIAGNOSTIC         │       │      MODEL 2: MACRO SENTINEL        │  │
│  │ • Fine-tuned on 100k+ failure patterns. │       │ • Real-time live market & news APIs.│  │
│  │ • Diagnoses ERP & Jira on-premise.      │       │ • Detects port strikes & promos.    │  │
│  │ • 100% Private (Zero Data Leakage).     │       │ • External market shock signals.    │  │
│  └────────────────────┬────────────────────┘       └──────────────────┬──────────────────┘  │
│                       │                                               │                     │
│                       │ [Internal Root Cause]                         │ [External Shock]    │
│                       └───────────────────────┬───────────────────────┘                     │
│                                               ▼                                             │
│                       ┌───────────────────────────────────────────────┐                     │
│                       │   MODEL 3: PRESCRIPTIVE ACTION & SIMULATOR    │                     │
│                       │ 1. Triangulates Model 1 & 2 (Attribution %).  │                     │
│                       │ 2. 30/60/90-Day Trajectory ROI Simulation.    │                     │
│                       │ 3. Explicit Abstention & 2 Canary Tests.      │                     │
│                       │ 4. "Human Mind Mixing" Executive Co-Pilot.    │                     │
│                       └───────────────────────┬───────────────────────┘                     │
└───────────────────────────────────────────────┼─────────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                             PERSONA-TAILORED DECISION WORKSPACE                             │
│  • Executive / VP: Strategic supply levers, unmasked financials, and 30/60/90-day ROI.      │
│  • Operations Analyst: Tactical SOPs, unmasked ticket IDs, sensitive COGS/margins REDACTED.│
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Mathematical Core & Invariants

### 1. Statistical Process Control (SPC) with Day-of-Week Normalization
* **Baseline Window:** Rolling 28 calendar days.
* **DOW Deseasonalization:** Calculates day-of-week seasonality factors $S_d = \frac{\mu_d}{\mu_{\text{total}}}$ ($d \in [0, 6]$). Baseline observations are deseasonalized:
  $$Y_{\text{deseas}, t} = \frac{Y_t}{S_{\text{dow}(t)}}$$
* **Evaluation & Control Limits:**
  $$\mu_{\text{eval}} = \mu_{\text{base}} \times S_{\text{dow}(\text{eval})}, \quad \sigma_{\text{eval}} = \sigma_{\text{base}} \times S_{\text{dow}(\text{eval})}$$
  $$\text{UCL} = \mu_{\text{eval}} + 2.5\sigma_{\text{eval}}, \quad \text{LCL} = \mu_{\text{eval}} - 2.5\sigma_{\text{eval}}$$
* **Cold-Start Adaptation ($N < 14$ days):** Incorporates **Student-$t$ distribution** multipliers ($t_{\text{crit}} + 0.5$) and Bayesian category priors to widen uncertainty bounds ($\ge 2\times$).

### 2. Exact Closed-Form 3-Factor Shapley Metric Tree Decomposition
* **Formula:** $\text{Revenue} = \text{Sessions} \times \text{Conversion Rate (CVR)} \times \text{Average Order Value (AOV)}$ ($R = S \cdot C \cdot A$).
* **Shapley Axiomatic Share:**
  $$\Delta R_S = \Delta S \cdot C_0 \cdot A_0 + \frac{1}{2}\Delta S \cdot \Delta C \cdot A_0 + \frac{1}{2}\Delta S \cdot C_0 \cdot \Delta A + \frac{1}{3}\Delta S \cdot \Delta C \cdot \Delta A$$
  $$\Delta R_C = S_0 \cdot \Delta C \cdot A_0 + \frac{1}{2}\Delta S \cdot \Delta C \cdot A_0 + \frac{1}{2}S_0 \cdot \Delta C \cdot \Delta A + \frac{1}{3}\Delta S \cdot \Delta C \cdot \Delta A$$
  $$\Delta R_A = S_0 \cdot C_0 \cdot \Delta A + \frac{1}{2}\Delta S \cdot C_0 \cdot \Delta A + \frac{1}{2}S_0 \cdot \Delta C \cdot \Delta A + \frac{1}{3}\Delta S \cdot \Delta C \cdot \Delta A$$
* **Invariant Guarantee:** $\Delta R_S + \Delta R_C + \Delta R_A \equiv \Delta R_{\text{total}}$ with numerical residual $|\epsilon| < 10^{-12}$.

---

## 🎯 The 4 Mandatory Scenarios

| Scenario | Trigger / Business Problem | Engine Analysis & Attribution | Prescribed Action & Outcome |
|---|---|---|---|
| **1. Multi-Factor Movement** | Gross Revenue drops $-\$66,800$ ($-38.7\%$) | **70% Singapore Port Congestion** (Model 2) + **30% WH-West Fulfillment Queue** (Model 1). | Authorize Seattle port drayage rerouting; **$3.2\times$ ROI Lift** on 90-day trajectory. |
| **2. Low-Confidence Ambiguity** | Drop on iOS Mobile Checkout ($Z = -3.1\sigma$) | Conflicting hypotheses: Payment 504 Timeout ($58\%$) vs. Competitor Promo ($42\%$). Confidence margin $<25\%$. | **Explicitly abstains**. Mandates **2 canary tests** ($\$120$ Stripe routing + $\$350$ price match voucher). |
| **3. Sparse Cold-Start Launch** | New APAC SKU Launch ($N=6 < 14$ days) | Cold-start protocol: Bayesian Category Prior ($\$5,000$) with Student-$t$ widened bounds ($\pm 45\%$). | Recommends controlled pilot ramp-up and weekly review gates instead of heavy pre-commitment. |
| **4. Role-Based Entitlement** | Governed Security & Data Access Demonstration | Analyst view dynamically redacts `unit_cogs` and `gross_margin` (`[RESTRICTED-EXEC]`). | Executive view preserves full unmasked financial visibility and strategic supply levers. |

---

## 🛠️ Technology Stack & Dependencies

* **Language:** Python 3.11+
* **User Interface:** Streamlit 1.30+, Plotly 5.18+ (Interactive Control Charts, Waterfall Attribution, Trajectory Curves)
* **Data & Math Engine:** NumPy 1.26+, Pandas 2.1+, Pydantic v2 (Strict Schema Contracts)
* **AI & Inference:** Pluggable Provider Architecture (Google Gemini, OpenAI, Ollama, and Instant Deterministic Mock Fallback)
* **Testing Framework:** Python `unittest`, Monte Carlo Stress Evaluators

---

## 🚀 Setup & Execution Instructions

### 1. Installation
Clone the repository and install required dependencies:
```bash
# Navigate to the project directory
cd "c:\Users\The_last\OneDrive\Videos\accenture business stat"

# Install dependencies
pip install -r prototype/requirements.txt
```

### 2. Launch the Interactive Decision Workspace
Run the Streamlit application:
```bash
streamlit run prototype/app.py
```
Open your browser at **`http://localhost:8501`**.

### 3. Run Automated Headless Verification Suite
Run the 93 acceptance assertions covering all 4 scenarios, mathematical invariants, and RBAC rules:
```bash
python prototype/test_scenarios.py
```

### 4. Run Modular Unit Tests & 10,000-Trial Monte Carlo Stress Suite
```bash
python -m unittest discover -s prototype/tests -p "test_*.py"
```

### 5. Run Scenario x Persona Matrix Runner
```bash
python prototype/verify_e2e.py
```

---

## 🧪 Verification Matrix & Test Evidence

| Layer | Target / Assertion | Test Command | Result |
|---|---|---|---|
| **Data Contracts** | Schema validation across Daily ERP, Hourly Web, and Weekly Jira | `test_scenarios.py` Tier 3 | **✅ 100% PASSED** |
| **SPC Core** | 28-day DoW Seasonality Normalization ($>2.5\sigma$ trigger) | `test_milestone2.py` | **✅ 100% PASSED** |
| **Causal Tree** | Exact closed-form Shapley decomposition ($|\epsilon| < 10^{-12}$) | 10,000 Monte Carlo trials | **✅ 100% PASSED** |
| **3-Model Synthesis** | Model 1, Model 2, and Model 3 orchestration with offline fallback | `test_scenarios.py` Tier 1 | **✅ 100% PASSED** |
| **Abstention Protocol** | Conflicting hypothesis detection & 2 low-cost canary tests | 10,000-point grid sweep | **✅ 100% PASSED** |
| **Cold-Start Engine** | Sparse-history Bayesian category prior & Student-$t$ envelope | `test_milestone2.py` | **✅ 100% PASSED** |
| **RBAC Security** | Column/row masking of sensitive unit costs for Analysts | Column permutation suite | **✅ 100% PASSED** |
| **Math Token Cost** | Deterministic math consumes exactly 0 LLM tokens | `test_scenarios.py` Tier 1 | **✅ 0 TOKENS ($0.00)** |

**Total Test Count:** **142 / 142 Automated Tests Passing Cleanly in < 1 minute.**

---

## 👥 Team Details (Accenture Innovation Challenge 2026)

* **Team Name:** Warriors
* **Institution:** Indian Institute of Technology (IIT) Patna
* **Members:**
  * **Harsh Singh Baghel** — Engineering Physics (Graduation: 2028)
  * **Rathod Rudra** — Engineering Physics (Graduation: 2029)
  * **Dhruv Maheshwari** — Engineering Physics (Graduation: 2028)
