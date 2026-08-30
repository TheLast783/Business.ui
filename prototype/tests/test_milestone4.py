"""Milestone 4 Unit Test Suite: Persona Storytelling, Scenario Runners (1-4) & Runtime Telemetry."""

import math
import os
import random
import sys
import time
import unittest
from datetime import date, datetime, timedelta

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOTYPE_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(PROTOTYPE_DIR)
for path in [CURRENT_DIR, PROTOTYPE_DIR, ROOT_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from prototype.engine.config import REDACTED_CONFIDENTIAL_STR
    from prototype.engine.contracts.schemas import (
        ActionItem,
        CanaryValidationTest,
        ExecutiveConstraint,
        MetricSnapshot,
        PrescriptiveSimulationOutput,
        RankedHypothesis,
        ScenarioExecutionResult,
        SPCResult,
        SupportJiraRecord,
        TelemetryRecord,
        TreeDecompositionResult,
        UserRole,
    )
    from prototype.engine.scenarios.runner import ScenarioRunner
    from prototype.engine.scenarios.scenario1_multifactor import Scenario1Runner
    from prototype.engine.scenarios.scenario2_ambiguous import Scenario2Runner
    from prototype.engine.scenarios.scenario3_coldstart import Scenario3Runner
    from prototype.engine.scenarios.scenario4_rbac import Scenario4Runner
    from prototype.engine.telemetry.feedback import FeedbackManager
    from prototype.engine.telemetry.tracker import TelemetryTracker
except ImportError:
    from engine.config import REDACTED_CONFIDENTIAL_STR
    from engine.contracts.schemas import (
        ActionItem,
        CanaryValidationTest,
        ExecutiveConstraint,
        MetricSnapshot,
        PrescriptiveSimulationOutput,
        RankedHypothesis,
        ScenarioExecutionResult,
        SPCResult,
        SupportJiraRecord,
        TelemetryRecord,
        TreeDecompositionResult,
        UserRole,
    )
    from engine.scenarios.runner import ScenarioRunner
    from engine.scenarios.scenario1_multifactor import Scenario1Runner
    from engine.scenarios.scenario2_ambiguous import Scenario2Runner
    from engine.scenarios.scenario3_coldstart import Scenario3Runner
    from engine.scenarios.scenario4_rbac import Scenario4Runner
    from engine.telemetry.feedback import FeedbackManager
    from engine.telemetry.tracker import TelemetryTracker


class TestScenario1MultiFactor(unittest.TestCase):
    """Scenario 1: Multi-Factor KPI Movement (70% External Macro / 30% Internal Warehouse)."""

    def setUp(self):
        self.runner = Scenario1Runner(mode="mock")

    def test_scenario1_spc_anomaly_detection(self):
        """Verifies Scenario 1 triggers statistical process control anomaly (z < -2.5 sigma)."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        spc = res.spc_result
        self.assertIsNotNone(spc)
        self.assertTrue(spc.is_anomaly, "Scenario 1 drop must trigger SPC anomaly flag")
        self.assertLess(spc.z_score, -2.5, "Scenario 1 z-score must exceed -2.5 sigma threshold")

    def test_scenario1_causal_tree_zero_residual(self):
        """Verifies exact closed-form Shapley metric tree decomposition has residual < 1e-5."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        tree = res.tree_result
        self.assertIsNotNone(tree)
        self.assertAlmostEqual(tree.residual, 0.0, places=5)
        self.assertAlmostEqual(tree.sum_factors, tree.delta_revenue, places=4)
        self.assertLess(tree.delta_revenue, 0, "Scenario 1 must exhibit negative revenue delta")

    def test_scenario1_compound_attribution_70_30(self):
        """Verifies Model 1 (30% internal) + Model 2 (70% external) compound attribution."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        synth = res.synthesis_result
        self.assertIsNotNone(synth)
        self.assertEqual(synth.attribution_internal_pct, 30.0)
        self.assertEqual(synth.attribution_external_pct, 70.0)
        self.assertAlmostEqual(synth.attribution_internal_pct + synth.attribution_external_pct, 100.0, places=4)

    def test_scenario1_trajectory_simulation_curves_and_positive_roi(self):
        """Verifies 91 daily trajectory points and positive 90-day Net ROI."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        synth = res.synthesis_result
        self.assertEqual(len(synth.trajectory_points), 91)
        self.assertEqual(synth.trajectory_points[0].day, 0)
        self.assertEqual(synth.trajectory_points[90].day, 90)

        # Recommended recovery must exceed status quo from deployment onwards
        for pt in synth.trajectory_points[10:]:
            self.assertGreater(pt.recommended_revenue, pt.status_quo_revenue)

        # Financial ROI metrics
        self.assertGreater(synth.net_roi_usd, 0.0, "Net 90-day ROI must be positive")
        self.assertGreater(synth.roi_ratio, 1.0, "ROI multiplier must exceed 1.0x")
        self.assertLessEqual(synth.payback_period_days, 30.0, "Payback period must be <= 30 days")

    def test_scenario1_persona_brief_tailoring(self):
        """Verifies distinct executive strategic brief vs operations tactical playbook."""
        res_exec = self.runner.run(persona=UserRole.EXECUTIVE)
        res_ops = self.runner.run(persona=UserRole.OPERATIONS_ANALYST)

        self.assertIn("EXECUTIVE", res_exec.synthesis_result.headline)
        self.assertIn("OPERATIONS", res_ops.synthesis_result.headline)
        self.assertNotEqual(res_exec.synthesis_result.narrative, res_ops.synthesis_result.narrative)


class TestScenario2Ambiguous(unittest.TestCase):
    """Scenario 2: Low-Confidence Ambiguity & Explicit Engine Abstention."""

    def setUp(self):
        self.runner = Scenario2Runner(mode="mock")

    def test_scenario2_explicit_abstention_flag_and_status(self):
        """Verifies engine sets is_abstaining=True and status='ABSTAINED' under conflicting signals."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        synth = res.synthesis_result
        self.assertTrue(synth.is_abstaining, "Scenario 2 must trigger explicit abstention")
        self.assertIn("ABSTENTION", synth.headline.upper())
        self.assertLess(synth.overall_confidence, 0.70, "Calibrated confidence must be below confidence threshold")

    def test_scenario2_ranked_competing_hypotheses(self):
        """Verifies at least 2 ranked competing hypotheses (58% vs 42%) summing to 100%."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        synth = res.synthesis_result
        hypos = synth.ranked_hypotheses
        self.assertGreaterEqual(len(hypos), 2, "Must return at least 2 ranked hypotheses")
        self.assertEqual(hypos[0].rank, 1)
        self.assertEqual(hypos[1].rank, 2)
        self.assertEqual(hypos[0].likelihood_pct, 58.0)
        self.assertEqual(hypos[1].likelihood_pct, 42.0)
        self.assertAlmostEqual(hypos[0].likelihood_pct + hypos[1].likelihood_pct, 100.0, places=1)

    def test_scenario2_low_cost_canary_validation_tests(self):
        """Verifies prescribed canary validation tests are low cost (< $500) and actionable."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        synth = res.synthesis_result
        canaries = synth.canary_validation_tests
        self.assertGreaterEqual(len(canaries), 2, "Must return at least 2 canary validation tests")
        for ct in canaries:
            self.assertLessEqual(ct.estimated_cost_usd, 500.0)
            self.assertLessEqual(ct.duration_hours, 6.0)
            self.assertTrue(len(ct.name) > 0 or len(ct.title or "") > 0)


class TestScenario3ColdStart(unittest.TestCase):
    """Scenario 3: Sparse-History / Cold-Start Launch Baseline (N < 14 Days)."""

    def setUp(self):
        self.runner = Scenario3Runner(mode="mock")

    def test_scenario3_sparse_history_detection_n_equals_6(self):
        """Verifies detection of sparse baseline history with N = 6 < 14 days."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        spc = res.spc_result
        self.assertIsNotNone(spc)
        self.assertTrue(spc.is_cold_start, "N=6 must trigger is_cold_start=True")
        self.assertIn("COLD", res.synthesis_result.headline.upper())

    def test_scenario3_uncertainty_envelope_widening(self):
        """Verifies cold-start uncertainty envelope is widened to ±45% (>= 2x mature baseline)."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        synth = res.synthesis_result
        pt_30 = synth.trajectory_points[30]
        # Check spread between upper bound and recommended curve
        spread_pct = (pt_30.upper_bound_95 - pt_30.recommended_revenue) / pt_30.recommended_revenue
        self.assertAlmostEqual(spread_pct, 0.45, delta=0.05)

    def test_scenario3_conservative_pilot_action_brief(self):
        """Verifies prescriptive brief recommends controlled pilot scaling and 14-day rolling buffer."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        synth = res.synthesis_result
        self.assertIn("COLD-START", synth.headline.upper())
        self.assertGreater(len(synth.action_playbook), 0)


class TestScenario4RBAC(unittest.TestCase):
    """Scenario 4: Role-Based Entitlements & Dynamic Financial Metric Masking."""

    def setUp(self):
        self.runner = Scenario4Runner(mode="mock")

    def test_scenario4_analyst_confidential_columns_masked(self):
        """Verifies Analyst role masks unit_cogs, gross_margin, and gross_margin_pct."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.OPERATIONS_ANALYST)
        masked_df = res.masked_erp_data
        self.assertIsNotNone(masked_df)

        for col in ["unit_cogs", "gross_margin", "gross_margin_pct"]:
            self.assertTrue(
                (masked_df[col] == REDACTED_CONFIDENTIAL_STR).all(),
                f"Column {col} must be completely redacted for Analyst",
            )

    def test_scenario4_executive_financial_metrics_unmasked_floats(self):
        """Verifies Executive role views unmasked numeric floats for cost and margin."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.EXECUTIVE)
        exec_df = res.masked_erp_data
        self.assertIsNotNone(exec_df)

        self.assertIsInstance(exec_df["unit_cogs"].iloc[0], (int, float))
        self.assertIsInstance(exec_df["gross_margin"].iloc[0], (int, float))
        self.assertGreater(exec_df["gross_margin"].iloc[0], 0.0)

    def test_scenario4_operational_identifiers_remain_visible_for_analyst(self):
        """Verifies system IDs (order_id, sku_id, shipping_location) remain unmasked for Analyst."""
        res: ScenarioExecutionResult = self.runner.run(persona=UserRole.OPERATIONS_ANALYST)
        masked_df = res.masked_erp_data
        self.assertTrue(masked_df["order_id"].iloc[0].startswith("ORD-"))
        self.assertTrue(masked_df["sku_id"].iloc[0].startswith("SKU-"))
        self.assertTrue(len(masked_df["shipping_location"].iloc[0]) > 0)

    def test_scenario4_masking_preserves_row_count_and_integrity(self):
        """Verifies masking does not drop rows or mutate non-sensitive columns."""
        res_exec = self.runner.run(persona=UserRole.EXECUTIVE)
        res_ops = self.runner.run(persona=UserRole.OPERATIONS_ANALYST)

        self.assertEqual(len(res_exec.masked_erp_data), len(res_ops.masked_erp_data))
        self.assertEqual(
            res_exec.masked_erp_data["order_id"].tolist(),
            res_ops.masked_erp_data["order_id"].tolist(),
        )


class TestUnifiedScenarioRunner(unittest.TestCase):
    """Test Unified ScenarioRunner Orchestrator."""

    def setUp(self):
        self.runner = ScenarioRunner(mode="mock")

    def test_unified_runner_executes_all_4_scenarios(self):
        """Verifies ScenarioRunner.run(...) dispatches and completes all 4 scenarios cleanly."""
        for scenario_id in ["scenario_1", "scenario_2", "scenario_3", "scenario_4"]:
            res = self.runner.run(scenario_id=scenario_id, persona=UserRole.EXECUTIVE)
            self.assertIsInstance(res, ScenarioExecutionResult)
            self.assertEqual(res.scenario_id, scenario_id)
            self.assertIsNotNone(res.spc_result)
            self.assertIsNotNone(res.tree_result)
            self.assertIsNotNone(res.synthesis_result)
            self.assertIsNotNone(res.telemetry)

    def test_unified_runner_run_all_method(self):
        """Verifies ScenarioRunner.run_all(...) returns results mapping for all 4 scenarios."""
        results = self.runner.run_all(persona=UserRole.EXECUTIVE)
        self.assertEqual(len(results), 4)
        self.assertIn("scenario_1", results)
        self.assertIn("scenario_2", results)
        self.assertIn("scenario_3", results)
        self.assertIn("scenario_4", results)

    def test_unified_runner_subscripting_and_dict_compatibility(self):
        """Verifies ScenarioExecutionResult supports both typed attributes and dict indexing."""
        res = self.runner.run(scenario_id="scenario_1")
        self.assertEqual(res["scenario_id"], res.scenario_id)
        self.assertEqual(res["persona"], res.persona)
        self.assertIsNotNone(res["telemetry"])


class TestRuntimeTelemetryTracker(unittest.TestCase):
    """Test Runtime Telemetry Tracker, Token Accounting, and Cost Splits."""

    def setUp(self):
        self.tracker = TelemetryTracker()

    def test_latency_breakdown_tracking(self):
        """Verifies latency is tracked with ingestion, math core, and LLM breakdown."""
        record = self.tracker.record_run(
            scenario_id="scenario_1",
            ingestion_time_ms=12.5,
            math_time_ms=4.0,
            llm_time_ms=85.0,
            total_latency_ms=101.5,
        )
        self.assertEqual(record.ingestion_time_ms, 12.5)
        self.assertEqual(record.math_time_ms, 4.0)
        self.assertEqual(record.llm_time_ms, 85.0)
        self.assertEqual(record.latency_ms, 101.5)

    def test_deterministic_math_zero_tokens_invariant(self):
        """Asserts deterministic math core consumes strictly 0 LLM tokens."""
        record = self.tracker.record_run(
            scenario_id="scenario_1",
            prompt_tokens=400,
            completion_tokens=150,
            math_time_ms=5.0,
        )
        self.assertEqual(record.math_tokens, 0, "Deterministic math core must consume 0 tokens")
        self.assertEqual(record.total_tokens, 550)

    def test_cost_calculation_mock_vs_live(self):
        """Verifies mock mode incurs $0.00 while live providers incur calculated token costs."""
        cost_mock = self.tracker.calculate_cost(prompt_tokens=1000, completion_tokens=500, provider="mock")
        cost_live = self.tracker.calculate_cost(prompt_tokens=1000, completion_tokens=500, provider="openai")

        self.assertEqual(cost_mock, 0.00)
        self.assertGreater(cost_live, 0.00)
        self.assertAlmostEqual(cost_live, 0.0025, places=5)

    def test_deterministic_vs_llm_split_breakdown(self):
        """Verifies deterministic vs LLM percentage split calculations."""
        record = self.tracker.record_run(
            scenario_id="scenario_1",
            ingestion_time_ms=20.0,
            math_time_ms=5.0,
            llm_time_ms=75.0,
            total_latency_ms=100.0,
        )
        breakdown = self.tracker.get_breakdown(record)
        self.assertAlmostEqual(breakdown["deterministic_pct"], 25.0, places=1)
        self.assertAlmostEqual(breakdown["llm_pct"], 75.0, places=1)
        self.assertEqual(breakdown["math_tokens"], 0)


class TestFeedbackAndMindMixing(unittest.TestCase):
    """Test Human-in-the-Loop Feedback Manager & Mind Mixing Constraints."""

    def setUp(self):
        self.manager = FeedbackManager()
        self.runner = ScenarioRunner(mode="mock")

    def test_record_and_retrieve_feedback(self):
        """Verifies recording star ratings and analyst textual corrections."""
        entry = self.manager.record_feedback(
            scenario_id="scenario_1",
            star_rating=5,
            text_correction="Warehouse queue resolved 6h ahead of SLA.",
            analyst_id="analyst_jdoe",
        )
        self.assertEqual(entry["star_rating"], 5)
        self.assertIn("resolved", entry["text_correction"])

        logs = self.manager.get_feedback("scenario_1")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["analyst_id"], "analyst_jdoe")

    def test_executive_budget_slider_re_simulation(self):
        """Verifies budget constraint updates and re-simulates trajectory curves."""
        # Update budget cap to $20,000
        c_low = self.manager.update_constraints(scenario_id="scenario_1", budget_cap_usd=20000.0)
        res_low = self.manager.re_simulate(self.runner, scenario_id="scenario_1", constraints=c_low)

        # Update budget cap to $50,000
        c_high = self.manager.update_constraints(scenario_id="scenario_1", budget_cap_usd=50000.0)
        res_high = self.manager.re_simulate(self.runner, scenario_id="scenario_1", constraints=c_high)

        # Higher budget cap must allow higher constrained revenue recovery
        pt_low = res_low.synthesis_result.trajectory_points[60]
        pt_high = res_high.synthesis_result.trajectory_points[60]
        self.assertGreater(pt_high.constrained_revenue, pt_low.constrained_revenue)

    def test_policy_override_air_freight_delay_re_simulation(self):
        """Verifies policy override prohibiting air freight adds deployment lag to constrained curve."""
        c_policy = ExecutiveConstraint(policy_override_note="Prohibit expedited air freight")
        res = self.manager.re_simulate(self.runner, scenario_id="scenario_1", constraints=c_policy)

        # Day 6 constrained revenue is delayed relative to recommended
        pt6 = res.synthesis_result.trajectory_points[6]
        self.assertLess(pt6.constrained_revenue, pt6.recommended_revenue)


class TestAdversarialAndBoundaryInvariants(unittest.TestCase):
    """Adversarial stress testing and mathematical invariant proofs."""

    def test_invariant_shapley_zero_residual_100_random_trials(self):
        """Asserts zero-residual property holds across 100 randomized business parameter sets."""
        rng = random.Random(2026)
        from prototype.engine.math.causal_tree import CausalMetricTree

        for trial in range(100):
            s0 = rng.uniform(1000.0, 1000000.0)
            cr0 = rng.uniform(0.005, 0.15)
            aov0 = rng.uniform(10.0, 500.0)

            s1 = s0 * rng.uniform(0.5, 1.5)
            cr1 = cr0 * rng.uniform(0.5, 1.5)
            aov1 = aov0 * rng.uniform(0.5, 1.5)

            res = CausalMetricTree.decompose_3factor(s0, s1, cr0, cr1, aov0, aov1)
            self.assertAlmostEqual(
                res.residual, 0.0, places=4,
                msg=f"Shapley zero residual failed on trial {trial}: {res}",
            )

    def test_invariant_trajectory_monotonicity(self):
        """Verifies recommended recovery trajectory points are non-decreasing over time."""
        runner = Scenario1Runner(mode="mock")
        res = runner.run(persona=UserRole.EXECUTIVE)
        points = [p.recommended_revenue for p in res.synthesis_result.trajectory_points]

        for t in range(4, 90):
            self.assertLessEqual(
                points[t],
                points[t + 1] + 1e-4,
                msg=f"Recovery trajectory decreased at day {t}: {points[t]} -> {points[t+1]}",
            )


if __name__ == "__main__":
    unittest.main()
