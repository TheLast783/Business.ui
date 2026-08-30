"""Milestone 2 Unit Test Suite: Deterministic Non-LLM Mathematical Core."""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOTYPE_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(PROTOTYPE_DIR)
for path in [CURRENT_DIR, PROTOTYPE_DIR, ROOT_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from datetime import date, datetime, timedelta
import math
import random
import unittest
import numpy as np
import pandas as pd

from prototype.engine.contracts.schemas import (
    AnomalyDirection,
    AnomalySeverity,
    DataQuality,
    MetricSnapshot,
    SPCResult,
    TreeDecompositionResult,
)
from prototype.engine.math.causal_tree import CausalMetricTree
from prototype.engine.math.metrics import KPICalculator
from prototype.engine.math.spc import (
    StatisticalProcessControl,
    get_student_t_critical,
)


class TestKPICalculator(unittest.TestCase):
    """Test standard business metric formulas, snapshots, and reconciliation."""

    def test_gross_revenue_calculation(self):
        rev = KPICalculator.gross_revenue(quantity=10, unit_price=50.0, discount_amount=25.0)
        self.assertEqual(rev, 475.0)
        # Clamped to 0
        rev_neg = KPICalculator.gross_revenue(quantity=1, unit_price=10.0, discount_amount=50.0)
        self.assertEqual(rev_neg, 0.0)

    def test_conversion_rate_bounds_and_zero_sessions(self):
        cr = KPICalculator.conversion_rate(order_volume=30, sessions=1000)
        self.assertEqual(cr, 0.03)
        # Zero sessions
        cr_zero = KPICalculator.conversion_rate(order_volume=0, sessions=0)
        self.assertEqual(cr_zero, 0.0)
        # Clamping at 1.0
        cr_high = KPICalculator.conversion_rate(order_volume=120, sessions=100)
        self.assertEqual(cr_high, 1.0)

    def test_average_order_value_and_zero_orders(self):
        aov = KPICalculator.average_order_value(gross_revenue=150000.0, order_volume=3000)
        self.assertEqual(aov, 50.0)
        # Zero orders
        aov_zero = KPICalculator.average_order_value(gross_revenue=0.0, order_volume=0)
        self.assertEqual(aov_zero, 0.0)

    def test_gross_margin_and_margin_pct(self):
        gm = KPICalculator.gross_margin(gross_revenue=100.0, quantity=2, unit_cogs=25.0)
        self.assertEqual(gm, 50.0)
        gm_pct = KPICalculator.gross_margin_pct(gross_margin=50.0, gross_revenue=100.0)
        self.assertEqual(gm_pct, 50.0)
        # Zero revenue
        self.assertEqual(KPICalculator.gross_margin_pct(0.0, 0.0), 0.0)

    def test_pct_change_and_zero_baseline(self):
        pct = KPICalculator.pct_change(100.0, 80.0)
        self.assertEqual(pct, -20.0)
        self.assertEqual(KPICalculator.pct_change(0.0, 0.0), 0.0)
        self.assertEqual(KPICalculator.pct_change(0.0, 50.0), 100.0)

    def test_create_snapshot_validation(self):
        snap = KPICalculator.create_snapshot(
            period_label="Baseline",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 28),
            gross_revenue=150000.0,
            order_volume=3000,
            sessions=100000,
            total_cogs=75000.0,
            total_gross_margin=75000.0,
        )
        self.assertEqual(snap.gross_revenue, 150000.0)
        self.assertEqual(snap.conversion_rate, 0.03)
        self.assertEqual(snap.aov, 50.0)
        self.assertEqual(snap.gross_margin_pct, 50.0)

    def test_reconcile_from_dataframes(self):
        df_erp = pd.DataFrame([
            {"transaction_date": "2026-08-28", "order_id": "O1", "gross_revenue": 100.0, "quantity": 1, "unit_cogs": 40.0, "fulfillment_status": "Shipped"},
            {"transaction_date": "2026-08-28", "order_id": "O2", "gross_revenue": 200.0, "quantity": 2, "unit_cogs": 50.0, "fulfillment_status": "Shipped"},
            {"transaction_date": "2026-08-28", "order_id": "O3", "gross_revenue": 300.0, "quantity": 3, "unit_cogs": 60.0, "fulfillment_status": "Cancelled"},
        ])
        df_web = pd.DataFrame([
            {"session_date": "2026-08-28", "sessions": 100},
        ])
        snap = KPICalculator.reconcile_from_dataframes(df_erp, df_web, period_label="Day-28")
        self.assertEqual(snap.gross_revenue, 300.0)  # O1 + O2
        self.assertEqual(snap.order_volume, 2)
        self.assertEqual(snap.sessions, 100)
        self.assertEqual(snap.conversion_rate, 0.02)
        self.assertEqual(snap.aov, 150.0)
        self.assertEqual(snap.total_cogs, 140.0)  # 1*40 + 2*50


class TestStatisticalProcessControl(unittest.TestCase):
    """Test 28-day rolling baseline, DoW seasonality, control limits, and cold start."""

    def test_spc_28_day_rolling_baseline(self):
        today = date(2026, 8, 28)
        dates = [today - timedelta(days=i) for i in reversed(range(35))]
        values = [10000.0 * (1.3 if d.weekday() >= 5 else 1.0) + (i % 500) for i, d in enumerate(dates)]

        spc = StatisticalProcessControl.compute(values, dates, window=28, sigma_thresh=2.5)
        self.assertFalse(spc.is_cold_start)
        self.assertGreater(spc.mean, 9000.0)
        self.assertGreater(spc.ucl, spc.mean)
        self.assertLess(spc.lcl, spc.mean)
        self.assertEqual(spc.baseline_points_count, 28)

    def test_spc_dow_seasonality_filters_weekend_cyclicality(self):
        """Verifies weekend natural volume surge is NOT falsely flagged as an anomaly."""
        today = date(2026, 8, 29)  # Saturday
        dates = [today - timedelta(days=i) for i in reversed(range(30))]
        # Pattern: Saturdays have +40% traffic
        values = [10000.0 * (1.4 if d.weekday() == 5 else 1.0) for d in dates]

        spc = StatisticalProcessControl.compute(values, dates, window=28, sigma_thresh=2.5)
        self.assertFalse(spc.is_anomaly, "Natural weekend surge must not trigger false positive anomaly")
        self.assertLess(abs(spc.z_score), 1.5)
        self.assertEqual(spc.severity, AnomalySeverity.NORMAL)

    def test_spc_dow_seasonality_filters_weekend_dip(self):
        """Verifies B2B weekend natural drop is NOT falsely flagged as an anomaly."""
        today = date(2026, 8, 30)  # Sunday
        dates = [today - timedelta(days=i) for i in reversed(range(30))]
        # B2B pattern: Sundays have -50% traffic
        values = [10000.0 * (0.5 if d.weekday() == 6 else 1.0) for d in dates]

        spc = StatisticalProcessControl.compute(values, dates, window=28, sigma_thresh=2.5)
        self.assertFalse(spc.is_anomaly, "Natural Sunday dip must not trigger false positive anomaly")
        self.assertLess(abs(spc.z_score), 1.5)

    def test_spc_critical_anomaly_trigger_above_2_5_sigma(self):
        """Verifies severe drop exceeding 2.5 sigma triggers critical anomaly flag."""
        today = date(2026, 8, 28)
        dates = [today - timedelta(days=i) for i in reversed(range(30))]
        values = [10000.0 + (i % 200) for i in range(29)]
        values.append(4500.0)  # 55% drop

        spc = StatisticalProcessControl.compute(values, dates, window=28, sigma_thresh=2.5)
        self.assertTrue(spc.is_anomaly)
        self.assertLess(spc.z_score, -2.5)
        self.assertLess(values[-1], spc.lcl)
        self.assertEqual(spc.severity, AnomalySeverity.CRITICAL)
        self.assertEqual(spc.direction, AnomalyDirection.DROP)

    def test_spc_warning_anomaly_classification(self):
        """Verifies moderate deviation between 1.5 and 2.5 sigma is classified as WARNING."""
        today = date(2026, 8, 28)
        dates = [today - timedelta(days=i) for i in reversed(range(30))]
        # Baseline with standard deviation ~ 100
        values = [10000.0 + (50 if i % 2 == 0 else -50) for i in range(29)]
        values.append(10000.0 - 1.8 * 50.0)

        spc = StatisticalProcessControl.compute(values, dates, window=28, sigma_thresh=2.5, warning_thresh=1.5)
        self.assertFalse(spc.is_anomaly)
        self.assertEqual(spc.severity, AnomalySeverity.WARNING)

    def test_spc_normal_noise_classification(self):
        today = date(2026, 8, 28)
        dates = [today - timedelta(days=i) for i in reversed(range(30))]
        values = [10000.0 + random.Random(42).uniform(-200, 200) for _ in range(30)]

        spc = StatisticalProcessControl.compute(values, dates, window=28, sigma_thresh=2.5)
        self.assertFalse(spc.is_anomaly)
        self.assertLessEqual(abs(spc.z_score), 1.5)
        self.assertEqual(spc.severity, AnomalySeverity.NORMAL)

    def test_spc_control_limits_symmetry_and_ordering(self):
        values = [1000.0 + (i * 10) for i in range(30)]
        dates = [date(2026, 8, 1) + timedelta(days=i) for i in range(30)]
        spc = StatisticalProcessControl.compute(values, dates, window=28, sigma_thresh=2.5)

        self.assertLess(spc.lcl, spc.mean)
        self.assertGreater(spc.ucl, spc.mean)
        self.assertAlmostEqual(spc.ucl - spc.mean, spc.mean - spc.lcl, places=3)

    def test_spc_cold_start_student_t_limits(self):
        """Verifies cold start mode (N=6 < 14) expands uncertainty envelope with Student-t critical values."""
        dates = [date(2026, 8, 1) + timedelta(days=i) for i in range(6)]
        values = [5000.0, 5200.0, 4800.0, 5100.0, 4900.0, 5050.0]

        spc = StatisticalProcessControl.compute(values, dates, window=28, sigma_thresh=2.5)
        self.assertTrue(spc.is_cold_start)
        self.assertEqual(spc.data_quality, DataQuality.COLD_START)
        self.assertLess(spc.confidence_score, 0.7)
        std_val = spc.std
        spread = (spc.ucl - spc.mean) / std_val if std_val > 0 else 0
        self.assertGreater(spread, 2.5)

    def test_spc_mad_calculation(self):
        values = [10.0, 12.0, 11.0, 13.0, 12.0, 100.0]
        med, mad = StatisticalProcessControl.compute_mad(values)
        self.assertEqual(med, 12.0)
        self.assertEqual(mad, 1.0)

    def test_spc_evaluate_rolling_series(self):
        dates = [date(2026, 8, 1) + timedelta(days=i) for i in range(15)]
        values = [1000.0 + i * 5 for i in range(15)]
        results = StatisticalProcessControl.evaluate_rolling(values, dates, window=28, sigma_thresh=2.5)
        self.assertEqual(len(results), 15)
        self.assertTrue(results[0].is_cold_start)

    def test_spc_dict_subscripting_compatibility(self):
        dates = [date(2026, 8, 1) + timedelta(days=i) for i in range(30)]
        values = [1000.0 for _ in range(30)]
        spc = StatisticalProcessControl.compute(values, dates, window=28)
        self.assertIn("mean", dir(spc))
        self.assertEqual(spc["mean"], spc.mean)
        self.assertEqual(spc["is_anomaly"], spc.is_anomaly)


class TestCausalMetricTree(unittest.TestCase):
    """Test exact closed-form Shapley Value decomposition, zero residuals, and invariants."""

    def test_shapley_exact_zero_residual_sum(self):
        """Asserts sum of factor dollar contributions equals total delta revenue identically."""
        s0, cr0, aov0 = 100000.0, 0.030, 100.0
        s1, cr1, aov1 = 80000.0, 0.024, 90.0

        res = CausalMetricTree.shapley_3factor(s0, s1, cr0, cr1, aov0, aov1)
        self.assertAlmostEqual(res["residual"], 0.0, places=5)
        self.assertAlmostEqual(res["sum_factors"], res["delta_revenue"], places=5)

    def test_shapley_percentage_contributions_sum_to_100(self):
        """Asserts factor percentage contributions sum to exactly 100%."""
        s0, cr0, aov0 = 50000.0, 0.040, 120.0
        s1, cr1, aov1 = 45000.0, 0.032, 110.0

        res = CausalMetricTree.decompose_values(s0, s1, cr0, cr1, aov0, aov1)
        total_pct = sum(res.factor_pct_contributions.values())
        self.assertAlmostEqual(total_pct, 100.0, places=4)

    def test_isolated_sessions_drop_attribution(self):
        """When ONLY sessions drop, sessions factor captures 100% of delta revenue."""
        s0, cr0, aov0 = 10000.0, 0.05, 100.0
        s1, cr1, aov1 = 7000.0, 0.05, 100.0

        res = CausalMetricTree.decompose_values(s0, s1, cr0, cr1, aov0, aov1)
        self.assertAlmostEqual(res.delta_r_sessions, -15000.0, places=2)
        self.assertAlmostEqual(res.delta_r_cvr, 0.0, places=2)
        self.assertAlmostEqual(res.delta_r_aov, 0.0, places=2)
        self.assertAlmostEqual(res.factor_pct_contributions["sessions"], 100.0, places=4)

    def test_isolated_cvr_drop_attribution(self):
        """When ONLY CVR drops, CVR factor captures 100% of delta revenue."""
        s0, cr0, aov0 = 10000.0, 0.05, 100.0
        s1, cr1, aov1 = 10000.0, 0.03, 100.0

        res = CausalMetricTree.decompose_values(s0, s1, cr0, cr1, aov0, aov1)
        self.assertAlmostEqual(res.delta_r_sessions, 0.0, places=2)
        self.assertAlmostEqual(res.delta_r_cvr, -20000.0, places=2)
        self.assertAlmostEqual(res.delta_r_aov, 0.0, places=2)
        self.assertAlmostEqual(res.factor_pct_contributions["cvr"], 100.0, places=4)

    def test_isolated_aov_drop_attribution(self):
        """When ONLY AOV drops, AOV factor captures 100% of delta revenue."""
        s0, cr0, aov0 = 10000.0, 0.05, 100.0
        s1, cr1, aov1 = 10000.0, 0.05, 80.0

        res = CausalMetricTree.decompose_values(s0, s1, cr0, cr1, aov0, aov1)
        self.assertAlmostEqual(res.delta_r_sessions, 0.0, places=2)
        self.assertAlmostEqual(res.delta_r_cvr, 0.0, places=2)
        self.assertAlmostEqual(res.delta_r_aov, -10000.0, places=2)
        self.assertAlmostEqual(res.factor_pct_contributions["aov"], 100.0, places=4)

    def test_shapley_100_randomized_trials_zero_residuals(self):
        """Stress-tests zero-residual invariant over 100 randomized multi-factor parameter shifts."""
        rng = random.Random(20260829)
        for trial in range(100):
            s0 = rng.uniform(10000.0, 200000.0)
            cr0 = rng.uniform(0.01, 0.08)
            aov0 = rng.uniform(20.0, 500.0)

            # Random shifts between -50% and +50%
            s1 = max(100.0, s0 * rng.uniform(0.5, 1.5))
            cr1 = max(0.001, min(1.0, cr0 * rng.uniform(0.5, 1.5)))
            aov1 = max(1.0, aov0 * rng.uniform(0.5, 1.5))

            res = CausalMetricTree.shapley_3factor(s0, s1, cr0, cr1, aov0, aov1)
            self.assertAlmostEqual(
                res["sum_factors"],
                res["delta_revenue"],
                places=4,
                msg=f"Trial {trial} failed zero-residual check: {res}"
            )
            self.assertLess(
                abs(res["residual"]),
                1e-4,
                msg=f"Trial {trial} residual exceeded 1e-4: {res['residual']}"
            )

    def test_mixed_countervailing_forces_and_adverse_shares(self):
        """Verifies adverse driver shares when sessions drop but AOV surges."""
        s0, cr0, aov0 = 100000.0, 0.03, 50.0   # R0 = $150,000
        s1, cr1, aov1 = 60000.0, 0.03, 60.0    # R1 = $108,000 (Delta R = -$42,000)

        res = CausalMetricTree.decompose_values(s0, s1, cr0, cr1, aov0, aov1)
        self.assertLess(res.delta_r_sessions, 0.0)
        self.assertGreater(res.delta_r_aov, 0.0)
        self.assertAlmostEqual(res.sum_factors, res.delta_revenue, places=2)
        # Adverse driver share should normalize negative component to 100%
        self.assertAlmostEqual(res.adverse_driver_shares["sessions"], 100.0, places=2)
        self.assertEqual(res.adverse_driver_shares["aov"], 0.0)

    def test_zero_differential_boundary(self):
        """When baseline equals actual, all deltas and residuals are identically zero."""
        res = CausalMetricTree.decompose_values(1000.0, 1000.0, 0.05, 0.05, 50.0, 50.0)
        self.assertEqual(res.delta_revenue, 0.0)
        self.assertEqual(res.delta_r_sessions, 0.0)
        self.assertEqual(res.delta_r_cvr, 0.0)
        self.assertEqual(res.delta_r_aov, 0.0)
        self.assertEqual(res.residual, 0.0)

    def test_hierarchical_shapley_decomposition(self):
        """Verifies 2-level hierarchical decomposition R = V * AOV -> V = S * CR."""
        s0, cr0, aov0 = 100000.0, 0.03, 50.0
        s1, cr1, aov1 = 80000.0, 0.02, 52.0

        res = CausalMetricTree.decompose_values(s0, s1, cr0, cr1, aov0, aov1, method="hierarchical")
        self.assertAlmostEqual(res.sum_factors, res.delta_revenue, places=2)
        self.assertAlmostEqual(sum(res.factor_pct_contributions.values()), 100.0, places=4)
        self.assertIsNotNone(res.delta_r_volume)

    def test_lmdi_1_verification(self):
        """Verifies continuous-path LMDI-I decomposition method."""
        s0, cr0, aov0 = 10000.0, 0.05, 100.0
        s1, cr1, aov1 = 8000.0, 0.04, 110.0

        lmdi = CausalMetricTree.lmdi_1(s0, s1, cr0, cr1, aov0, aov1)
        self.assertAlmostEqual(lmdi["sum_factors"], lmdi["delta_revenue"], places=4)

    def test_metric_snapshot_input_decomposition(self):
        snap0 = MetricSnapshot(
            period_label="Baseline",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 28),
            gross_revenue=150000.0,
            order_volume=3000,
            sessions=100000,
            conversion_rate=0.03,
            aov=50.0,
        )
        snap1 = MetricSnapshot(
            period_label="Observed",
            start_date=date(2026, 8, 29),
            end_date=date(2026, 8, 29),
            gross_revenue=83200.0,
            order_volume=1600,
            sessions=80000,
            conversion_rate=0.02,
            aov=52.0,
        )

        res = CausalMetricTree.decompose(snap0, snap1)
        self.assertEqual(res.delta_revenue, -66800.0)
        self.assertAlmostEqual(res.sum_factors, -66800.0, places=2)
        self.assertEqual(res.baseline_metrics.period_label, "Baseline")
        self.assertEqual(res.actual_metrics.period_label, "Observed")

    def test_scenario1_ground_truth_decomposition(self):
        """Verifies Scenario 1 exact attribution figures: Gross Revenue drop $150k -> $83.2k."""
        # Sessions: 100k -> 80k (Delta S = -20k)
        # CR: 3.0% -> 2.0% (Delta CR = -1.0%)
        # AOV: $50 -> $52 (Delta AOV = +$2)
        res = CausalMetricTree.decompose_values(100000.0, 80000.0, 0.03, 0.02, 50.0, 52.0)
        # Net drop = -$66,800
        self.assertEqual(res.delta_revenue, -66800.0)
        self.assertAlmostEqual(res.sum_factors, -66800.0, places=2)
        # Exact closed-form Shapley values:
        self.assertAlmostEqual(res.delta_r_sessions, -25466.67, delta=1.0)
        self.assertAlmostEqual(res.delta_r_cvr, -45866.67, delta=1.0)
        self.assertAlmostEqual(res.delta_r_aov, 4533.33, delta=1.0)


if __name__ == "__main__":
    unittest.main()
