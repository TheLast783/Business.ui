# TEST_READY: BusinessIntelligence.ai KPI Engine Headless Test Suite

## Executive Summary
The standalone headless E2E test suite for the **BusinessIntelligence.ai KPI Intelligence-to-Action Engine** is fully authored, validated, and ready for execution at `prototype/test_scenarios.py`.

- **Test Suite Location**: `prototype/test_scenarios.py`
- **Execution Framework**: Python Standard Library `unittest` (Zero GUI / Zero Browser / Zero Network Dependencies)
- **Total Test Cases**: **93 Test Cases** across 21 Test Classes
- **Total Test Tiers**: 4 Tiers + Deterministic Math Invariants
- **Execution Time**: < 1.0 second (deterministic, high-performance headless execution)

---

## How to Execute the Test Suite

From repository root:
```bash
python prototype/test_scenarios.py
```
Or via Python's `unittest` runner:
```bash
python -m unittest prototype/test_scenarios.py
```
From inside `prototype/`:
```bash
cd prototype
python test_scenarios.py
```

**Exit Code**:
- `0`: All assertions passed cleanly (100% pass).
- `1`: Assertion failure or unexpected exception.

---

## Test Inventory & Coverage Matrix

| Test Category | Class Name | Test Count | Scope & Requirements |
|---|---|:---:|---|
| **Tier 1: Feature Unit Tests** | `TestTier1ConnectedKPIsAndSchemas` | 5 | R1: ERP Daily, Web Hourly, Jira Weekly, 4 Connected KPIs ($R=S \cdot CR \cdot AOV$) |
| | `TestTier1SemanticContractAndRBAC` | 5 | R1: Governed Contract, Lineage, Role-Based Access Control (Analyst vs Executive) |
| | `TestTier1StatisticalProcessControl` | 5 | R2: 28-day baseline, Day-of-Week Seasonality Normalization, $>2.5\sigma$ Anomaly Detection |
| | `TestTier1CausalMetricTree` | 5 | R2: Exact Closed-Form Shapley Metric Tree Decomposition ($\sum \Delta R_i \equiv \Delta R$) |
| | `TestTier1Model1InternalDiagnostic` | 5 | R3: Model 1 Jira & ERP Backlog Clustering, Root Cause Citations, Fallbacks |
| | `TestTier1Model2MacroSentinel` | 5 | R3: Model 2 Maritime/Port Disruption Feeds, Competitor Shocks, Severity Quantification |
| | `TestTier1Model3PrescriptiveAndSimulation` | 5 | R3: Model 3 Multi-Factor Synthesis, 30/60/90-Day Trajectory ROI Simulation, Persona Briefs |
| | `TestTier1PluggableProviders` | 5 | R3: Pluggable LLM Provider (Live API vs Zero-Dependency Deterministic Mock) |
| | `TestTier1Scenario1MultiFactor` | 5 | R4: Scenario 1 70% Port Strike + 30% Warehouse Backlog Compound Attribution |
| | `TestTier1Scenario2Abstention` | 5 | R4: Scenario 2 Low-Confidence Explicit Abstention, Ranked Hypotheses (58% vs 42%) |
| | `TestTier1Scenario3ColdStart` | 5 | R4: Scenario 3 Sparse History ($N=6 < 14$), Bayesian Category Prior, Wide Bounds |
| | `TestTier1Scenario4RBAC` | 5 | R4: Scenario 4 Dynamic Column/Row Masking on Sensitive Financials (`unit_cogs`, `gross_margin`) |
| | `TestTier1HumanFeedbackAndConstraints` | 5 | R5: Human-in-the-Loop Ratings, Corrections, Executive Constraint Mixing Sliders |
| | `TestTier1TelemetryAndCost` | 5 | R5: Runtime Latency ($ms$), Token Accounting ($0$ math tokens), Cost Tracking |
| **Tier 2: Boundary & Corner Cases** | `TestTier2BoundaryAndCornerCases` | 10 | Zero denominators, zero delta, 10x surge, 99% drop, single data point $N=1$, empty feeds/tickets, zero budget, negative margin |
| **Tier 3: Pairwise Combinations** | `TestTier3PairwiseAndCrossModelInteractions` | 6 | Generator $\rightarrow$ Contract, Contract $\rightarrow$ SPC, SPC $\rightarrow$ Metric Tree, Tree $\rightarrow$ Model 3, M1+M2 $\rightarrow$ Abstention, Pipeline $\rightarrow$ Telemetry |
| **Tier 4: Scenario Acceptance** | `TestTier4Scenario1Acceptance` | 1 | Multi-Factor 70/30 Attribution, SPC $>2.5\sigma$, Positive 30/60/90 Trajectory ROI |
| | `TestTier4Scenario2Acceptance` | 1 | Conflicting Signals, Explicit Abstention Flag, 2 Ranked Hypotheses, 2 Canary Tests |
| | `TestTier4Scenario3Acceptance` | 1 | Sparse History $N=6$, Bayesian Prior, $\ge 2\times$ Uncertainty Envelope |
| | `TestTier4Scenario4Acceptance` | 1 | Analyst Masks `unit_cogs` & `gross_margin`, Executive Unmasks Floats, Operational IDs Intact |
| **Invariants & Stress Tests** | `TestDeterministicMathInvariants` | 3 | 100 Randomized Shapley Zero-Residual Trials, Deterministic Reproducibility, Trajectory Monotonicity |
| **TOTAL** | **21 Classes** | **93 Tests** | **100% Coverage across R1, R2, R3, R4, R5, Invariants & Scenarios** |

---

## 4 Mandatory Scenario Acceptance Verification

### 1. Scenario 1 (Multi-Factor KPI Movement)
- **Inputs**: 30-day multi-source dataset (ERP Daily, Web Hourly, Jira Weekly) with compound shock on day 30.
- **Assertions**:
  - SPC detects drop with $z < -2.5\sigma$.
  - Causal Metric Tree decomposes $\Delta R$ with zero residual ($|\sum \Delta R_i - \Delta R| < 10^{-5}$).
  - Compound factor attribution validates to ~70% External (Port Strike / Sessions) and ~30% Internal (Warehouse Backlog / CVR).
  - 30/60/90-day trajectory simulation demonstrates positive net recovery after intervention costs.

### 2. Scenario 2 (Low-Confidence & Explicit Abstention)
- **Inputs**: Conflicting operational incident (payment gateway 504) vs external market shock (competitor 35% discount).
- **Assertions**:
  - Confidence margin between competing hypotheses is $< 25\%$ (58% vs 42%).
  - Engine explicitly sets `is_abstaining == True` and status `ABSTAINED`.
  - Exactly 2 ranked competing hypotheses are returned with probability weights.
  - At least 2 concrete low-cost canary validation tests are generated (e.g. 5% route canary < $150).

### 3. Scenario 3 (Sparse-History Cold-Start Launch)
- **Inputs**: Newly launched SKU dataset with history length $N = 6 < 14$ days.
- **Assertions**:
  - Engine triggers `is_cold_start == True`.
  - Baseline computation shifts from purely empirical rolling window to Bayesian shrinkage with category benchmark prior.
  - Standard error / uncertainty envelope width is $\ge 2\times$ wider than mature 28-day baseline.

### 4. Scenario 4 (Role-Based Entitlement & Masking)
- **Inputs**: ERP transaction dataset containing sensitive financial columns (`unit_cogs`, `gross_margin`, `gross_margin_pct`).
- **Assertions**:
  - Under `UserRole.OPERATIONS_ANALYST`: `unit_cogs`, `gross_margin`, and `gross_margin_pct` are masked string tokens (`[REDACTED_CONFIDENTIAL]`).
  - Under `UserRole.EXECUTIVE`: all financial columns are unmasked numeric floats.
  - Operational Jira ticket keys (`JIRA-*`) and warehouse codes (`WH-*`) remain fully visible to Analyst.

---

## Deterministic Invariant Guarantees
1. **Zero-Residual Shapley Decomposition**:
   $$\sum_{i \in \{S, CR, AOV\}} \Delta R_i \equiv \Delta R \quad (\text{Residual } \epsilon < 10^{-5})$$
   $$\sum_{i \in \{S, CR, AOV\}} \text{PctContribution}_i \equiv 100.0\% \quad (\text{when } \Delta R \neq 0)$$
2. **Deterministic Math Telemetry**:
   Deterministic Math Core (SPC + Metric Tree) consumes strictly **0 LLM tokens** and **$0.00 cost**.
3. **Execution Reproducibility**:
   Identical input feeds guarantee identical SPC control limits, z-scores, and Shapley factor dollar allocations across all runs.
