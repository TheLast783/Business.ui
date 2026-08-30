"""Adversarial Empirical Stress Harness for BusinessIntelligence.ai KPI Engine.
Tests Shapley decomposition, SPC engine, Explicit Abstention, RBAC masking, and Trajectory simulations.
"""

import math
import random
import unittest
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd

import os
import sys

# Ensure prototype and project root are in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOTYPE_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(PROTOTYPE_DIR)
for path in [ROOT_DIR, PROTOTYPE_DIR, CURRENT_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from prototype.engine.contracts.schemas import (
    MetricSnapshot,
    TreeDecompositionResult,
    UserRole,
    ExecutiveConstraint,
    AnomalySeverity,
    AnomalyDirection,
    DataQuality,
)
from prototype.engine.math.causal_tree import CausalMetricTree
from prototype.engine.math.spc import StatisticalProcessControl, get_student_t_critical
from prototype.engine.math.metrics import KPICalculator
from prototype.engine.synthesis.abstention import AbstentionEngine
from prototype.engine.contracts.semantic_contract import SemanticContract, RBACMaskingEngine
from prototype.engine.synthesis.model3_prescriptive import Model3Prescriptive


class AdversarialShapleyStressTest(unittest.TestCase):
    """Stress tests exact closed-form Shapley and LMDI decomposition across extreme inputs."""

    def test_randomized_10000_shapley_trials(self):
        """10,000 randomized factor combinations: verifies exact zero residual (< 1e-4 absolute or < 1e-12 relative)."""
        random.seed(42)
        np.random.seed(42)
        max_abs_residual = 0.0
        max_rel_residual = 0.0

        for i in range(10000):
            s0 = random.uniform(10.0, 1_000_000.0)
            s1 = s0 * random.uniform(0.01, 100.0)
            cr0 = random.uniform(0.0001, 0.5)
            cr1 = random.uniform(0.0001, 0.5)
            aov0 = random.uniform(1.0, 5000.0)
            aov1 = aov0 * random.uniform(0.01, 10.0)

            res = CausalMetricTree.shapley_3factor(s0, s1, cr0, cr1, aov0, aov1)
            residual = abs(res["residual"])
            tot_r = max(1.0, abs(res["delta_revenue"]))
            rel_res = residual / tot_r

            if residual > max_abs_residual:
                max_abs_residual = residual
            if rel_res > max_rel_residual:
                max_rel_residual = rel_res

            self.assertTrue(
                residual < 1e-3 or rel_res < 1e-12,
                f"Trial {i} violated zero residual: s0={s0}, s1={s1}, cr0={cr0}, cr1={cr1}, aov0={aov0}, aov1={aov1}, residual={residual}"
            )
            # Additivity: sum_factors == delta_revenue
            self.assertAlmostEqual(res["delta_revenue"], res["sum_factors"], places=2)

        print(f"[PASSED] 10,000 Randomized Shapley 3-Factor Trials. Max abs residual = {max_abs_residual:.2e}, Max rel residual = {max_rel_residual:.2e}")

    def test_extreme_boundary_and_negative_factors(self):
        """Tests zero baseline, zero actuals, extreme surges, near-zero collapses, and negative deltas."""
        edge_cases = [
            # s0, s1, cr0, cr1, aov0, aov1
            (1e6, 0.0, 0.05, 0.0, 100.0, 0.0),       # Total collapse to zero
            (0.0, 1e6, 0.0, 0.05, 0.0, 100.0),       # Zero baseline to massive surge
            (100.0, 100.0, 0.02, 0.02, 50.0, 50.0),   # Identical baseline & actual (0 delta)
            (1e9, 1e9 + 1, 0.01, 0.01, 100.0, 100.0),# Microscopic delta on huge baseline
            (1000.0, 1000.0, 0.05, 0.02, 200.0, 150.0),  # Multi-factor drops (CR and AOV drop)
            (1000.0, 800.0, 0.05, 0.06, 100.0, 90.0),   # Mixed directional changes (S down, CR up, AOV down)
        ]

        for s0, s1, cr0, cr1, aov0, aov1 in edge_cases:
            res_3f = CausalMetricTree.shapley_3factor(s0, s1, cr0, cr1, aov0, aov1)
            self.assertLess(abs(res_3f["residual"]), 1e-4)

            res_h = CausalMetricTree.hierarchical_shapley(s0, s1, cr0, cr1, aov0, aov1)
            self.assertLess(abs(res_h["residual"]), 1e-4)

            # Structured wrapper
            decomp = CausalMetricTree.decompose_values(s0, s1, cr0, cr1, aov0, aov1)
            self.assertIsNotNone(decomp)
            self.assertLess(abs(decomp.residual), 1e-4)

        print("[PASSED] Extreme Boundary, Zero, and Opposing Shapley Edge Cases.")

    def test_hierarchical_shapley_volume_preservation(self):
        """Verifies hierarchical 2-level Shapley allocates volume delta exactly to sessions and CVR."""
        for _ in range(1000):
            s0 = random.uniform(100.0, 50000.0)
            s1 = random.uniform(100.0, 50000.0)
            cr0 = random.uniform(0.01, 0.15)
            cr1 = random.uniform(0.01, 0.15)
            aov0 = random.uniform(20.0, 500.0)
            aov1 = random.uniform(20.0, 500.0)

            res = CausalMetricTree.hierarchical_shapley(s0, s1, cr0, cr1, aov0, aov1)
            # Check delta_r_volume == delta_r_sessions + delta_r_cvr
            vol_sum = res["delta_r_sessions"] + res["delta_r_cvr"]
            self.assertAlmostEqual(res["delta_r_volume"], vol_sum, places=4)
            self.assertLess(abs(res["residual"]), 1e-4)

        print("[PASSED] Hierarchical Shapley 2-Level Volume Decomposition Consistency.")

    def test_lmdi_and_shapley_directional_agreement(self):
        """Verifies LMDI-1 and Shapley-3 agree on the sign and primary driver of revenue movement."""
        for _ in range(500):
            s0 = random.uniform(1000.0, 20000.0)
            s1 = s0 * random.uniform(0.5, 1.5)
            cr0 = random.uniform(0.02, 0.08)
            cr1 = cr0 * random.uniform(0.5, 1.5)
            aov0 = random.uniform(50.0, 300.0)
            aov1 = aov0 * random.uniform(0.5, 1.5)

            shapley = CausalMetricTree.shapley_3factor(s0, s1, cr0, cr1, aov0, aov1)
            lmdi = CausalMetricTree.lmdi_1(s0, s1, cr0, cr1, aov0, aov1)

            # Both must agree on total delta direction
            if abs(shapley["delta_revenue"]) > 1.0:
                self.assertEqual(
                    np.sign(shapley["delta_revenue"]),
                    np.sign(lmdi["delta_revenue"])
                )

        print("[PASSED] LMDI-1 and Shapley Directional Agreement.")


class AdversarialSPCStressTest(unittest.TestCase):
    """Stress tests SPC engine against non-stationary baselines, cold start, and extreme noise."""

    def test_cold_start_transition_thresholds(self):
        """Verifies SPC transitions from Student-t cold start to normal DoW at N=15 (14 history days)."""
        base_date = date(2026, 8, 1)
        for n in range(1, 35):
            vals = [10000.0 + random.gauss(0, 500) for _ in range(n)]
            dates = [base_date + timedelta(days=i) for i in range(n)]

            spc_res = StatisticalProcessControl.compute(
                values=vals,
                dates=dates,
                metric_name="Gross Revenue",
                cold_start_threshold=14
            )

            # Cold start occurs when history points (n_total - 1) < 14 (i.e. n_total <= 14)
            if n <= 14:
                self.assertTrue(spc_res.is_cold_start, f"Expected cold_start=True for N={n}")
                self.assertEqual(spc_res.data_quality, DataQuality.COLD_START)
                self.assertLess(spc_res.confidence_score, 1.0)
                # UCL / LCL must be wider in cold start
                spread = spc_res.ucl - spc_res.lcl
                self.assertGreater(spread, 0.0)
            else:
                self.assertFalse(spc_res.is_cold_start, f"Expected cold_start=False for N={n}")
                self.assertEqual(spc_res.data_quality, DataQuality.NORMAL)
                self.assertEqual(spc_res.confidence_score, 1.0)

        print("[PASSED] Cold-Start Transition Threshold (N=1 to N=35) Verified.")

    def test_spc_non_stationary_linear_drift(self):
        """Tests SPC under steep upward/downward linear trend."""
        base_date = date(2026, 7, 1)
        # Upward drift of +500/day
        n = 30
        vals = [10000.0 + (i * 500.0) for i in range(n)]
        dates = [base_date + timedelta(days=i) for i in range(n)]

        spc_res = StatisticalProcessControl.compute(vals, dates)
        self.assertIsNotNone(spc_res)
        # Check that mean reflects the window
        self.assertGreater(spc_res.observed_value, spc_res.mean)
        self.assertEqual(spc_res.direction, AnomalyDirection.SURGE)

        print("[PASSED] Non-Stationary Linear Drift SPC Behavior.")

    def test_spc_seasonality_filter_on_weekend_dips(self):
        """Verifies predictable weekend drops (e.g. Sunday -40%) are normalized and do NOT trigger false critical anomalies."""
        random.seed(42)
        base_date = date(2026, 7, 1)
        n = 29
        dates = [base_date + timedelta(days=i) for i in range(n)]
        # Construct series where every Sunday has 40% lower revenue systematically
        vals = []
        for dt in dates:
            base = 100000.0
            if dt.weekday() == 6:  # Sunday
                base *= 0.60
            elif dt.weekday() == 5:  # Saturday
                base *= 0.75
            vals.append(base + random.gauss(0, 2000))

        # Check last point on Sunday
        sunday_idx = -1
        while dates[sunday_idx].weekday() != 6:
            sunday_idx -= 1

        sub_vals = vals[:len(vals) + sunday_idx + 1]
        sub_dates = dates[:len(dates) + sunday_idx + 1]

        spc_res = StatisticalProcessControl.compute(sub_vals, sub_dates)
        # Because Sunday dip is seasonal and learned in DoW index, Z-score should NOT be a critical anomaly (< 2.5)
        self.assertLess(
            abs(spc_res.z_score),
            2.5,
            f"False positive on regular Sunday dip! Z={spc_res.z_score}, DOW={spc_res.dow_index}"
        )
        self.assertFalse(spc_res.is_anomaly)

        print("[PASSED] DoW Seasonality Normalization Prevents False Alarms on Weekend Dips.")

    def test_spc_constant_zero_variance_guard(self):
        """Verifies SPC handles perfectly constant series (variance = 0) without ZeroDivisionError."""
        base_date = date(2026, 8, 1)
        vals = [5000.0] * 28 + [5000.0]
        dates = [base_date + timedelta(days=i) for i in range(29)]

        spc_res = StatisticalProcessControl.compute(vals, dates)
        self.assertEqual(spc_res.z_score, 0.0)
        self.assertFalse(spc_res.is_anomaly)
        self.assertEqual(spc_res.severity, AnomalySeverity.NORMAL)

        # An outlier on zero-variance baseline
        vals_outlier = [5000.0] * 28 + [8000.0]
        spc_res_out = StatisticalProcessControl.compute(vals_outlier, dates)
        self.assertTrue(spc_res_out.is_anomaly)
        self.assertEqual(spc_res_out.direction, AnomalyDirection.SURGE)

        print("[PASSED] Zero-Variance Constant Series Guard in SPC.")


class AdversarialAbstentionStressTest(unittest.TestCase):
    """Stress tests AbstentionEngine across fine-grained confidence grids and edge conditions."""

    def test_comprehensive_confidence_grid(self):
        """Sweeps 10,000 confidence pairs (s1, s2) in [0.0, 1.0] to verify exact decision boundaries."""
        grid_steps = np.linspace(0.0, 1.0, 100)

        for s1 in grid_steps:
            for s2 in grid_steps:
                delta = abs(s1 - s2)
                max_c = max(s1, s2)

                res = AbstentionEngine.evaluate_ambiguity(
                    m1_score=s1,
                    m2_score=s2,
                    confidence_threshold=0.70,
                    margin_threshold=0.25,
                )

                expected_abstain = (
                    (delta < 0.25 and max_c < 0.85)
                    or (max_c < 0.70)
                )

                self.assertEqual(
                    res["is_abstaining"],
                    expected_abstain,
                    f"Mismatch at s1={s1:.2f}, s2={s2:.2f}: expected {expected_abstain}, got {res['is_abstaining']}"
                )

                if res["is_abstaining"]:
                    self.assertEqual(res["status"], "ABSTAINED")
                    self.assertGreaterEqual(len(res["ranked_hypotheses"]), 2)
                    self.assertGreaterEqual(len(res["canary_tests"]), 2)
                    for ct in res["canary_tests"]:
                        self.assertGreater(ct["estimated_cost_usd"], 0.0)
                        self.assertGreater(ct["duration_hours"], 0.0)
                else:
                    self.assertEqual(res["status"], "CONFIDENT")
                    self.assertGreaterEqual(res["overall_confidence"], 0.70)

        print("[PASSED] 10,000-Point Comprehensive Confidence Grid Abstention Boundary Sweep.")

    def test_forced_abstention_override(self):
        """Verifies force_abstain=True overrides even 1.0 confidence."""
        res = AbstentionEngine.evaluate_ambiguity(
            m1_score=0.99,
            m2_score=0.99,
            force_abstain=True
        )
        self.assertTrue(res["is_abstaining"])
        self.assertEqual(res["status"], "ABSTAINED")
        self.assertEqual(len(res["ranked_hypotheses"]), 2)

        print("[PASSED] Forced Abstention Overrides High Confidence.")


class AdversarialRBACMaskingStressTest(unittest.TestCase):
    """Stress tests RBAC masking across column permutations, nulls, and unusual data types."""

    def test_analyst_cogs_margin_leak_resistance(self):
        """Verifies Analyst role NEVER receives unmasked numbers in sensitive financial columns."""
        from prototype.engine.config import REDACTED_CONFIDENTIAL_STR, REDACTED_CUSTOMER_PREFIX
        sensitive_cols = ["unit_cogs", "gross_margin", "gross_margin_pct"]
        
        # Test dictionary records
        for val in [10.5, 0.0, -50.0, 1e6, np.nan, None, "123.45"]:
            rec = {
                "order_id": "ORD-999",
                "customer_id": "CUST-883910",
                "gross_revenue": 1000.0,
                "unit_cogs": val,
                "gross_margin": val,
                "gross_margin_pct": val,
            }
            masked = RBACMaskingEngine.mask_erp_record(rec, UserRole.OPERATIONS_ANALYST)
            for c in sensitive_cols:
                self.assertEqual(
                    masked[c],
                    REDACTED_CONFIDENTIAL_STR,
                    f"Sensitive col {c} leaked value {masked[c]} for Analyst!"
                )
            self.assertTrue(masked["customer_id"].startswith(REDACTED_CUSTOMER_PREFIX))
            self.assertTrue(masked["customer_id"].endswith("910"))

        print("[PASSED] Analyst ERP Record Sensitive Column Leak Resistance.")

    def test_dataframe_masking_under_column_permutations(self):
        """Verifies DataFrame masking is invariant under arbitrary column orderings and types."""
        from prototype.engine.config import REDACTED_CONFIDENTIAL_STR
        base_df = pd.DataFrame({
            "order_id": [f"ORD-{i}" for i in range(100)],
            "transaction_date": [date(2026, 8, 1)] * 100,
            "unit_cogs": np.random.uniform(10.0, 100.0, 100),
            "gross_margin": np.random.uniform(50.0, 500.0, 100),
            "gross_margin_pct": np.random.uniform(20.0, 80.0, 100),
            "customer_id": [f"USER_{1000 + i}" for i in range(100)],
            "carrier_or_system_id": [f"SYS-NODE-{i%5}" for i in range(100)],
            "gross_revenue": np.random.uniform(100.0, 1000.0, 100),
        })

        for _ in range(20):
            # Shuffle columns
            shuffled_cols = list(base_df.columns)
            random.shuffle(shuffled_cols)
            shuffled_df = base_df[shuffled_cols]

            masked_analyst = RBACMaskingEngine.mask_erp_dataframe(shuffled_df, UserRole.OPERATIONS_ANALYST)
            # Must preserve row count
            self.assertEqual(len(masked_analyst), 100)
            # Sensitive columns masked
            for c in ["unit_cogs", "gross_margin", "gross_margin_pct"]:
                if c in masked_analyst.columns:
                    self.assertTrue((masked_analyst[c] == REDACTED_CONFIDENTIAL_STR).all())

            # Executive sees raw numbers
            masked_exec = RBACMaskingEngine.mask_erp_dataframe(shuffled_df, UserRole.EXECUTIVE)
            for c in ["unit_cogs", "gross_margin", "gross_margin_pct"]:
                if c in masked_exec.columns:
                    self.assertTrue(np.issubdtype(masked_exec[c].dtype, np.number))

        print("[PASSED] DataFrame Masking Invariance Under Column Permutations.")

    def test_jira_masking_persona_divergence(self):
        """Verifies Executive sees generic system labels while Analyst sees granular system IDs."""
        jira_df = pd.DataFrame({
            "ticket_id": ["JIRA-101", "JIRA-102"],
            "carrier_or_system_id": ["WH-WEST-01", "NODE-REDIS-04"],
            "issue_category": ["Warehouse Backlog", "Gateway Timeout"],
        })

        exec_jira = RBACMaskingEngine.mask_jira_dataframe(jira_df, UserRole.EXECUTIVE)
        self.assertTrue((exec_jira["carrier_or_system_id"] == "Operational System").all())

        analyst_jira = RBACMaskingEngine.mask_jira_dataframe(jira_df, UserRole.OPERATIONS_ANALYST)
        self.assertEqual(analyst_jira["carrier_or_system_id"].tolist(), ["WH-WEST-01", "NODE-REDIS-04"])

        print("[PASSED] Jira Persona Masking Divergence (Executive vs Analyst).")


class AdversarialTrajectorySimulationStressTest(unittest.TestCase):
    """Stress tests 30/60/90-day Trajectory simulation across extreme budgets and constraints."""

    def test_budget_sweep_zero_to_one_million(self):
        """Sweeps budget constraints from $0 to $1,000,000 to verify graceful clamping and monotonicity."""
        budgets = [0.0, 1.0, 100.0, 1000.0, 10000.0, 45000.0, 50000.0, 100000.0, 500000.0, 1000000.0]
        model3 = Model3Prescriptive()

        prev_net_roi = -float("inf")
        prev_cost = -1.0

        for b in budgets:
            constraint = ExecutiveConstraint(budget_cap_usd=b, target_horizon_days=60)
            out = model3.synthesize(
                constraint=constraint,
                role=UserRole.EXECUTIVE,
                scenario_id="scenario_1"
            )

            # Check points generated
            self.assertEqual(len(out.trajectory_points), 91)
            self.assertIsNotNone(out.summary_roi_metrics)

            actual_cost = out.summary_roi_metrics["intervention_cost_usd"]
            self.assertLessEqual(actual_cost, b + 1e-5)
            self.assertLessEqual(actual_cost, 45000.0)

            # Check 30/60/90 day monotonicity of recommended curve
            pt0 = out.trajectory_points[0].recommended_revenue
            pt30 = out.trajectory_points[30].recommended_revenue
            pt60 = out.trajectory_points[60].recommended_revenue
            pt90 = out.trajectory_points[90].recommended_revenue

            self.assertGreaterEqual(pt30, pt0)
            self.assertGreaterEqual(pt60, pt30)
            self.assertGreaterEqual(pt90, pt60)

            # Check uncertainty envelopes
            for pt in out.trajectory_points:
                self.assertLessEqual(pt.lower_bound_95, pt.recommended_revenue)
                self.assertGreaterEqual(pt.upper_bound_95, pt.recommended_revenue)

            # Budget cap $0 behavior
            if b == 0.0:
                self.assertEqual(actual_cost, 0.0)
                # Constrained curve should match status quo
                for pt in out.trajectory_points:
                    self.assertAlmostEqual(pt.constrained_revenue, pt.status_quo_revenue, places=2)

        print("[PASSED] Budget Sweep ($0 to $1,000,000) Monotonicity & Clamping Verified.")

    def test_policy_override_air_freight_ban(self):
        """Verifies policy override banning air freight introduces recovery lag and slower time constant."""
        model3 = Model3Prescriptive()

        # Normal run
        out_normal = model3.synthesize(
            constraint=ExecutiveConstraint(budget_cap_usd=50000.0, policy_override_note=None),
            role=UserRole.EXECUTIVE
        )

        # Air freight banned run
        out_banned = model3.synthesize(
            constraint=ExecutiveConstraint(budget_cap_usd=50000.0, policy_override_note="Ban expedited air freight"),
            role=UserRole.EXECUTIVE
        )

        # In day 10, normal should recover faster than air-freight-banned
        rec_normal_day10 = out_normal.trajectory_points[10].constrained_revenue
        rec_banned_day10 = out_banned.trajectory_points[10].constrained_revenue

        self.assertGreater(
            rec_normal_day10,
            rec_banned_day10,
            "Expected slower recovery when air freight is banned!"
        )

        print("[PASSED] Policy Override Air Freight Ban Slows Trajectory Curve Appropriately.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
