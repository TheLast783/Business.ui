# E2E Test Infra: BusinessIntelligence.ai KPI Engine

## Test Philosophy
- Opaque-box, requirement-driven, zero GUI/browser dependency for the test runner.
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise Feature Combinations + Realistic Workload Scenarios.
- Direct test execution via: `python test_scenarios.py` from within `prototype/`.

## Feature Inventory & Test Coverage Mapping
| # | Feature | Source (Requirement) | Tier 1 (Unit) | Tier 2 (Boundary) | Tier 3 (Pairwise) | Tier 4 (Scenario E2E) |
|---|---------|---------------------|:-------------:|:-----------------:|:-----------------:|:---------------------:|
| 1 | 4 Connected KPIs & Data Schemas | ORIGINAL_REQUEST § R1 | 5 cases | 5 cases | ✓ | ✓ |
| 2 | Governed Semantic Contract & RBAC | ORIGINAL_REQUEST § R1 | 5 cases | 5 cases | ✓ | ✓ |
| 3 | Seasonality-Normalized SPC (>2.5σ) | ORIGINAL_REQUEST § R2 | 5 cases | 5 cases | ✓ | ✓ |
| 4 | Exact Shapley Metric Tree Math | ORIGINAL_REQUEST § R2 | 5 cases | 5 cases | ✓ | ✓ |
| 5 | Model 1 Internal Diagnostic | ORIGINAL_REQUEST § R3 | 5 cases | 5 cases | ✓ | ✓ |
| 6 | Model 2 Macro Sentinel | ORIGINAL_REQUEST § R3 | 5 cases | 5 cases | ✓ | ✓ |
| 7 | Model 3 Action & 30/60/90 ROI Sim | ORIGINAL_REQUEST § R3 | 5 cases | 5 cases | ✓ | ✓ |
| 8 | Pluggable Fallback Provider | ORIGINAL_REQUEST § R3 | 5 cases | 5 cases | ✓ | ✓ |
| 9 | Scenario 1: Multi-Factor (70/30) | ORIGINAL_REQUEST § R4 | 5 cases | 5 cases | ✓ | ✓ |
| 10| Scenario 2: Ambiguity Abstention | ORIGINAL_REQUEST § R4 | 5 cases | 5 cases | ✓ | ✓ |
| 11| Scenario 3: Cold-Start Sparse Launch | ORIGINAL_REQUEST § R4 | 5 cases | 5 cases | ✓ | ✓ |
| 12| Scenario 4: Role-Based Masking | ORIGINAL_REQUEST § R4 | 5 cases | 5 cases | ✓ | ✓ |
| 13| Human Mind Mixing & Feedback | ORIGINAL_REQUEST § R5 | 5 cases | 5 cases | ✓ | ✓ |
| 14| Telemetry & Cost Accounting | ORIGINAL_REQUEST § R5 | 5 cases | 5 cases | ✓ | ✓ |

## Test Architecture
- Test Runner: Python `unittest` standard library in `prototype/test_scenarios.py`.
- Execution command: `python test_scenarios.py`
- Exit Code: 0 on 100% pass, non-zero on failure.
- Execution speed target: < 3.0 seconds total runtime.

## 4 Mandatory Scenario Acceptance Assertions
1. **Scenario 1 (Multi-Factor Movement)**:
   - Verifies 4 connected KPIs generated across 3 distinct data schemas (ERP, Web, Jira).
   - Verifies SPC detects $z > 2.5\sigma$ anomaly.
   - Verifies exact zero-residual Causal Tree decomposition ($\sum \Delta R_i = \Delta R$).
   - Verifies compound attribution split matches ground truth (70% macro port strike + 30% internal inventory backlog).
   - Verifies 30/60/90-day trajectory ROI projection generates positive net returns.

2. **Scenario 2 (Low-Confidence & Explicit Abstention)**:
   - Ingests conflicting signals (gateway timeout vs viral traffic drop).
   - Asserts `is_abstaining == True` when confidence margin $< 25\%$.
   - Asserts generation of at least 2 ranked competing hypotheses (e.g. 58% vs 42%).
   - Asserts generation of concrete low-cost canary validation tests.

3. **Scenario 3 (Sparse-History Cold-Start)**:
   - Ingests cold-start dataset with $N = 6 < 14$ days history.
   - Asserts engine detects sparse history and applies Bayesian category prior.
   - Asserts uncertainty envelope is at least $2\times$ wider than mature baseline.

4. **Scenario 4 (Role-Based Entitlement & Masking)**:
   - Queries dataset with `UserRole.OPERATIONS_ANALYST` $\rightarrow$ verifies `unit_cogs`, `gross_margin`, and margin % are masked (`[CONFIDENTIAL]`).
   - Queries dataset with `UserRole.EXECUTIVE` $\rightarrow$ verifies sensitive financial metrics are unmasked.
   - Verifies operational ticket IDs remain visible for Analyst.
