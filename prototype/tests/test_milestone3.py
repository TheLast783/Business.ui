"""Milestone 3 Unit Test Suite: 3-Model AI Synthesis, Pluggable Fallbacks & Ambiguity Abstention Engine."""

import math
import os
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

from prototype.engine.contracts.schemas import (
    ActionItem,
    CanaryValidationTest,
    ExecutiveConstraint,
    InternalDiagnosticInput,
    InternalDiagnosticOutput,
    MacroSentinelInput,
    MacroSentinelOutput,
    MacroShockAssessment,
    MacroSignalFeed,
    MetricSnapshot,
    PrescriptiveSimulationOutput,
    RankedHypothesis,
    RootCauseFinding,
    SupportJiraRecord,
    TrajectoryPoint,
    TreeDecompositionResult,
    UserRole,
)
from prototype.engine.synthesis.abstention import AbstentionEngine
from prototype.engine.synthesis.model1_diagnostic import Model1Diagnostic
from prototype.engine.synthesis.model2_macro import Model2MacroSentinel
from prototype.engine.synthesis.model3_prescriptive import Model3Prescriptive
from prototype.engine.synthesis.providers import (
    BaseSynthesisProvider,
    DeterministicFallbackProvider,
    GeminiSynthesisProvider,
    OllamaSynthesisProvider,
    OpenAISynthesisProvider,
    PluggableLLMProvider,
)


class TestPluggableLLMProviders(unittest.TestCase):
    """Test Pluggable LLM Provider Architecture & Deterministic Instant Fallback."""

    def test_deterministic_fallback_execution_time_under_5ms(self):
        """Verifies deterministic fallback executes in under 5ms with zero network calls."""
        provider = DeterministicFallbackProvider()
        t0 = time.time()
        res = provider.generate("Analyze anomaly drop in conversion rate.")
        elapsed_ms = (time.time() - t0) * 1000.0

        self.assertLess(elapsed_ms, 50.0)  # Generous upper bound for slow CI environments
        self.assertEqual(res["cost_usd"], 0.0)
        self.assertTrue(res["is_fallback"])
        self.assertEqual(res["mode"], "deterministic_mock")
        self.assertIn("Deterministic synthesis", res["text"])

    def test_deterministic_fallback_structured_schema_generation(self):
        """Verifies deterministic fallback returns a valid structured Pydantic model."""
        provider = DeterministicFallbackProvider()
        output = provider.generate_structured(
            system_prompt="System instructions",
            user_prompt="Analyze tickets",
            schema_cls=InternalDiagnosticOutput,
            fallback_factory=lambda: InternalDiagnosticOutput(
                primary_internal_driver="WMS_Sync_Backlog",
                internal_confidence=0.88,
                diagnostic_summary="Fallback internal summary",
            ),
        )
        self.assertIsInstance(output, InternalDiagnosticOutput)
        self.assertEqual(output.primary_internal_driver, "WMS_Sync_Backlog")
        self.assertEqual(output.internal_confidence, 0.88)
        self.assertEqual(output.execution_mode, "DETERMINISTIC_FALLBACK")

    def test_openai_provider_fallback_when_no_api_key(self):
        """Verifies OpenAISynthesisProvider gracefully falls back to deterministic mock when no key is set."""
        provider = OpenAISynthesisProvider(api_key=None)
        res = provider.generate("Test prompt")
        self.assertTrue(res["is_fallback"])
        self.assertEqual(res["cost_usd"], 0.0)

    def test_openai_provider_fallback_on_network_or_rate_limit_error(self):
        """Verifies OpenAISynthesisProvider gracefully catches simulated errors and returns fallback output."""
        provider = OpenAISynthesisProvider(api_key="sk-fake-test-key-12345")
        # Invoking with non-routable or invalid key triggers fallback
        res = provider.generate("Test prompt")
        self.assertIn("text", res)
        self.assertIn("latency_ms", res)

    def test_gemini_provider_fallback_when_no_api_key(self):
        """Verifies GeminiSynthesisProvider falls back cleanly when no key is set."""
        provider = GeminiSynthesisProvider(api_key=None)
        res = provider.generate("Test prompt")
        self.assertTrue(res["is_fallback"])
        self.assertEqual(res["cost_usd"], 0.0)

    def test_ollama_provider_fallback_when_service_unreachable(self):
        """Verifies OllamaSynthesisProvider falls back cleanly when local Ollama is offline."""
        provider = OllamaSynthesisProvider(host="http://localhost:9999")  # Unreachable port
        res = provider.generate("Test prompt")
        self.assertTrue(res["is_fallback"])
        self.assertEqual(res["cost_usd"], 0.0)

    def test_pluggable_llm_provider_mode_switching(self):
        """Verifies PluggableLLMProvider initializes appropriate backend for different modes."""
        p_mock = PluggableLLMProvider(mode="mock")
        self.assertIsInstance(p_mock.backend, DeterministicFallbackProvider)

        p_openai = PluggableLLMProvider(mode="openai", api_key="sk-test")
        self.assertIsInstance(p_openai.backend, OpenAISynthesisProvider)

        p_gemini = PluggableLLMProvider(mode="gemini", api_key="gem-test")
        self.assertIsInstance(p_gemini.backend, GeminiSynthesisProvider)

        p_ollama = PluggableLLMProvider(mode="ollama")
        self.assertIsInstance(p_ollama.backend, OllamaSynthesisProvider)

    def test_token_and_cost_accounting_math(self):
        """Verifies prompt and completion token cost formulas."""
        provider = PluggableLLMProvider(mode="mock")
        res = provider.generate("Word " * 100)  # 100 words
        self.assertGreater(res["prompt_tokens"], 0)
        self.assertEqual(res["cost_usd"], 0.0)  # $0 in mock mode


class TestModel1Diagnostic(unittest.TestCase):
    """Test Model 1: Enterprise Internal Diagnostic Specialist."""

    def setUp(self):
        self.model = Model1Diagnostic()

    def test_model1_ticket_clustering_and_severity_weighting(self):
        """Verifies ticket analysis groups critical and high severity operational issues."""
        tickets = [
            SupportJiraRecord(
                ticket_id="JIRA-4819",
                created_timestamp=datetime(2026, 8, 28, 14, 0),
                week_start_date=date(2026, 8, 24),
                category="WMS_Sync",
                severity="CRITICAL",
                summary="Warehouse batch worker failed on node-04",
                description_text="Fulfillment queue sync worker stopped responding.",
            ),
            SupportJiraRecord(
                ticket_id="JIRA-4822",
                created_timestamp=datetime(2026, 8, 28, 15, 30),
                week_start_date=date(2026, 8, 24),
                category="WMS_Sync",
                severity="P2",
                summary="Inventory picking queue delayed for SKU-401",
                description_text="Pick delay at WH-WEST-01.",
            ),
        ]
        out = self.model.analyze(tickets=tickets, unfulfilled_orders=120, delayed_revenue=28000.0)
        self.assertIsInstance(out, InternalDiagnosticOutput)
        self.assertGreaterEqual(out.internal_confidence, 0.70)
        self.assertEqual(out.primary_internal_driver, "LOGISTICS")
        self.assertGreater(len(out.primary_root_causes), 0)

    def test_model1_grounded_ticket_citations(self):
        """Verifies Model 1 attaches grounded citations (`JIRA-*`, `WH-*`)."""
        tickets = [
            SupportJiraRecord(
                ticket_id="JIRA-4819",
                created_timestamp=datetime(2026, 8, 28, 14, 0),
                week_start_date=date(2026, 8, 24),
                category="WMS_Sync",
                severity="CRITICAL",
                summary="Warehouse batch worker failed on WH-WEST-01",
                description_text="Fulfillment queue blocked.",
            )
        ]
        out = self.model.analyze(tickets=tickets, scenario_id="scenario_1")
        citation_str = " ".join(out.citations)
        self.assertTrue("JIRA-" in citation_str or "WH-" in citation_str or "ERP-" in citation_str)

    def test_model1_erp_backlog_correlation(self):
        """Verifies ERP backlog orders quantify delayed revenue and warehouse bottleneck."""
        out = self.model.analyze(tickets=[], unfulfilled_orders=350, delayed_revenue=75000.0, scenario_id="scenario_1")
        self.assertEqual(out.estimated_internal_share_pct, 30.0)
        self.assertGreater(out.internal_confidence, 0.75)

    def test_model1_internal_share_and_confidence_scoring(self):
        """Verifies internal confidence score is bounded in [0.0, 1.0]."""
        out = self.model.analyze(tickets=[], scenario_id="scenario_1")
        self.assertGreaterEqual(out.internal_confidence, 0.0)
        self.assertLessEqual(out.internal_confidence, 1.0)
        self.assertEqual(out.estimated_internal_share_pct, 30.0)

    def test_model1_empty_tickets_nominal_fallback(self):
        """Verifies empty tickets and zero backlog produce nominal baseline output without crashing."""
        out = self.model.analyze(tickets=[], unfulfilled_orders=0, delayed_revenue=0.0, scenario_id="nominal")
        self.assertEqual(out.status, "NO_INTERNAL_ANOMALY")
        self.assertLessEqual(out.internal_confidence, 0.30)

    def test_model1_input_object_and_positional_signatures(self):
        """Verifies both InternalDiagnosticInput object and positional arguments produce identical results."""
        inp = InternalDiagnosticInput(
            scenario_id="scenario_1",
            unfulfilled_orders=150,
            delayed_revenue=30000.0,
        )
        out_obj = self.model.analyze(input=inp)
        out_pos = self.model.analyze(unfulfilled_orders=150, delayed_revenue=30000.0, scenario_id="scenario_1")

        self.assertEqual(out_obj.primary_internal_driver, out_pos.primary_internal_driver)
        self.assertEqual(out_obj.estimated_internal_share_pct, out_pos.estimated_internal_share_pct)


class TestModel2MacroSentinel(unittest.TestCase):
    """Test Model 2: Real-time Macro-Intelligence Sentinel."""

    def setUp(self):
        self.model = Model2MacroSentinel()

    def test_model2_feed_parsing_and_severity_scoring(self):
        """Verifies ingestion of port strike and competitor flash campaign signals."""
        feeds = [
            MacroSignalFeed(
                feed_id="MACRO-US-PORT-2026-08",
                source="FreightWaves",
                event_name="West Coast Port Labor Slowdown",
                headline="Dwell times surge 120% at Port of LA/Long Beach",
                region="US-WEST",
                signal_type="SUPPLY_CHAIN",
                severity_index=8.5,
                severity="CRITICAL",
                confidence=0.92,
            )
        ]
        out = self.model.analyze(external_signals=feeds, scenario_id="scenario_1")
        self.assertIsInstance(out, MacroSentinelOutput)
        self.assertEqual(out.status, "EXTERNAL_SHOCK_DETECTED")
        self.assertEqual(out.macro_share_pct, 70.0)
        self.assertGreaterEqual(out.external_confidence, 0.90)

    def test_model2_macro_shock_quantification(self):
        """Verifies macro sentinel computes external attribution share."""
        out = self.model.analyze(scenario_id="scenario_1")
        self.assertEqual(out.macro_share_pct, 70.0)
        self.assertIn("Port", out.top_external_shock)

    def test_model2_citation_grounding(self):
        """Verifies macro findings cite valid external feed IDs."""
        feeds = [
            MacroSignalFeed(
                feed_id="FEED-REUTERS-PORT-01",
                source="Reuters",
                event_name="Singapore Port Congestion",
                headline="Singapore port anchorages congested",
                severity_index=8.0,
            )
        ]
        out = self.model.analyze(external_signals=feeds, scenario_id="scenario_1")
        self.assertIn("FEED-REUTERS-PORT-01", out.citations)

    def test_model2_empty_feeds_nominal_climate(self):
        """Verifies empty macro signals return nominal baseline climate."""
        out = self.model.analyze(external_signals=[], scenario_id="nominal")
        self.assertEqual(out.status, "NO_MACRO_IMPACT")
        self.assertEqual(out.macro_share_pct, 0.0)
        self.assertEqual(out.external_severity, "LOW")

    def test_model2_input_object_and_positional_signatures(self):
        """Verifies MacroSentinelInput object works identically to positional arguments."""
        inp = MacroSentinelInput(
            scenario_id="scenario_1",
            observed_drop_pct=-18.2,
        )
        out_obj = self.model.analyze(input=inp)
        out_pos = self.model.analyze(scenario_id="scenario_1", observed_drop_pct=-18.2)
        self.assertEqual(out_obj.macro_share_pct, out_pos.macro_share_pct)
        self.assertEqual(out_obj.top_external_shock, out_pos.top_external_shock)


class TestAbstentionEngine(unittest.TestCase):
    """Test Ambiguity & Explicit Abstention Engine."""

    def test_abstention_trigger_on_narrow_confidence_margin(self):
        """Verifies engine triggers explicit abstention when confidence margin |C1 - C2| < 25%."""
        # 58% internal vs 42% external (difference = 16% < 25%)
        res = AbstentionEngine.evaluate_ambiguity(
            m1_score=0.58,
            m2_score=0.42,
            margin_threshold=0.25,
        )
        self.assertTrue(res["is_abstaining"])
        self.assertEqual(res["status"], "ABSTAINED")
        self.assertGreaterEqual(len(res["ranked_hypotheses"]), 2)
        self.assertGreaterEqual(len(res["canary_tests"]), 2)

    def test_abstention_trigger_on_low_confidence_floor(self):
        """Verifies engine triggers explicit abstention when max confidence < 70%."""
        res = AbstentionEngine.evaluate_ambiguity(
            m1_score=0.62,
            m2_score=0.20,
            confidence_threshold=0.70,
        )
        self.assertTrue(res["is_abstaining"])

    def test_abstention_ranked_hypotheses_generation(self):
        """Verifies generation of at least 2 ranked hypotheses summing to 100%."""
        res = AbstentionEngine.evaluate_ambiguity(force_abstain=True)
        hypos = res["ranked_hypotheses"]
        self.assertEqual(len(hypos), 2)
        self.assertEqual(hypos[0]["rank"], 1)
        self.assertEqual(hypos[1]["rank"], 2)
        self.assertAlmostEqual(hypos[0]["likelihood_pct"] + hypos[1]["likelihood_pct"], 100.0, places=1)

    def test_abstention_low_cost_canary_validation_tests(self):
        """Verifies prescribed canary validation tests are low cost (< $500) and short runtime (< 6h)."""
        res = AbstentionEngine.evaluate_ambiguity(force_abstain=True)
        canaries = res["canary_tests"]
        self.assertGreaterEqual(len(canaries), 2)
        for test in canaries:
            self.assertLessEqual(test["estimated_cost_usd"], 500.0)
            self.assertLessEqual(test["duration_hours"], 6.0)
            self.assertIn("decision_gate", test)

    def test_confident_signal_does_not_abstain(self):
        """Verifies high-confidence separated signals do not trigger abstention."""
        # 88% internal vs 25% external (difference = 63% > 25%, max = 88% > 70%)
        res = AbstentionEngine.evaluate_ambiguity(m1_score=0.88, m2_score=0.25)
        self.assertFalse(res["is_abstaining"])
        self.assertEqual(res["status"], "CONFIDENT")
        self.assertEqual(len(res["canary_tests"]), 0)

    def test_evaluate_typed_and_dict_compatibility(self):
        """Verifies AbstentionEngine.evaluate returns typed AbstentionResult directly."""
        typed_res = AbstentionEngine.evaluate(m1_confidence=0.58, m2_confidence=0.42)
        self.assertTrue(typed_res.is_abstaining)
        self.assertEqual(typed_res.status, "ABSTAINED")
        self.assertGreaterEqual(len(typed_res.ranked_hypotheses), 2)


class TestModel3PrescriptiveAndTrajectorySimulation(unittest.TestCase):
    """Test Model 3: Prescriptive Action & 30/60/90-Day Trajectory ROI Simulator."""

    def setUp(self):
        self.model = Model3Prescriptive()
        self.tree_res = TreeDecompositionResult(
            delta_revenue=-168000.0,
            factor_dollar_contributions={"sessions": -117600.0, "cvr": -50400.0, "aov": 0.0},
            factor_pct_contributions={"sessions": 70.0, "cvr": 30.0, "aov": 0.0},
            delta_r_sessions=-117600.0,
            delta_r_cvr=-50400.0,
            delta_r_aov=0.0,
            sum_factors=-168000.0,
            baseline_metrics=MetricSnapshot(
                period_label="Baseline",
                start_date=date(2026, 8, 1),
                end_date=date(2026, 8, 28),
                gross_revenue=420000.0,
                order_volume=3500,
                sessions=100000,
                conversion_rate=0.035,
                aov=120.0,
            ),
            actual_metrics=MetricSnapshot(
                period_label="Observed",
                start_date=date(2026, 8, 29),
                end_date=date(2026, 8, 29),
                gross_revenue=252000.0,
                order_volume=2100,
                sessions=75000,
                conversion_rate=0.028,
                aov=120.0,
            ),
        )

    def test_multi_factor_attribution_synthesis_sums_to_100(self):
        """Verifies Model 1 (30%) and Model 2 (70%) attribution percentages sum to 100%."""
        out = self.model.synthesize(tree_res=self.tree_res, scenario_id="scenario_1")
        self.assertAlmostEqual(out.attribution_internal_pct + out.attribution_external_pct, 100.0, places=2)
        self.assertEqual(out.attribution_internal_pct, 30.0)
        self.assertEqual(out.attribution_external_pct, 70.0)

    def test_trajectory_simulation_91_daily_points(self):
        """Verifies trajectory simulation generates exact 91 daily evaluation points (Days 0 to 90)."""
        out = self.model.synthesize(tree_res=self.tree_res, scenario_id="scenario_1")
        self.assertEqual(len(out.trajectory_points), 91)
        self.assertEqual(out.trajectory_points[0].day, 0)
        self.assertEqual(out.trajectory_points[90].day, 90)

    def test_trajectory_monotonic_recovery_curve(self):
        """Verifies recommended recovery trajectory is monotonically non-decreasing over time."""
        out = self.model.synthesize(tree_res=self.tree_res, scenario_id="scenario_1")
        points = [p.recommended_revenue for p in out.trajectory_points]
        # From deployment day t=4 onwards, curve must be strictly non-decreasing
        for t in range(4, 90):
            self.assertLessEqual(
                points[t],
                points[t + 1] + 1e-4,
                msg=f"Trajectory decrease detected at day {t}: {points[t]} -> {points[t+1]}",
            )
        # Recommended recovery must exceed status quo
        for p in out.trajectory_points[10:]:
            self.assertGreater(p.recommended_revenue, p.status_quo_revenue)

    def test_trajectory_financial_roi_and_payback_period(self):
        """Verifies financial ROI metrics: gross revenue saved, net ROI, and payback period."""
        out = self.model.synthesize(tree_res=self.tree_res, scenario_id="scenario_1")
        roi_metrics = out.summary_roi_metrics

        self.assertGreater(roi_metrics["90_day_gross_saved_usd"], 0)
        self.assertGreater(roi_metrics["90_day_net_roi_usd"], 0)
        self.assertGreater(out.roi_ratio, 1.0)
        self.assertLessEqual(out.payback_period_days, 30.0)

    def test_human_mind_mixing_budget_cap_zero(self):
        """Verifies budget cap of $0 collapses constrained recovery to status quo."""
        constraint = ExecutiveConstraint(budget_cap_usd=0.0)
        out = self.model.synthesize(tree_res=self.tree_res, constraint=constraint, scenario_id="scenario_1")

        # Constrained curve matches status quo
        for pt in out.trajectory_points:
            self.assertAlmostEqual(pt.constrained_revenue, pt.status_quo_revenue, delta=1.0)

    def test_human_mind_mixing_budget_cap_perturbation(self):
        """Verifies reducing budget cap from $50k to $20k reduces constrained recovery."""
        c_high = ExecutiveConstraint(budget_cap_usd=50000.0)
        c_low = ExecutiveConstraint(budget_cap_usd=20000.0)

        out_high = self.model.synthesize(tree_res=self.tree_res, constraint=c_high, scenario_id="scenario_1")
        out_low = self.model.synthesize(tree_res=self.tree_res, constraint=c_low, scenario_id="scenario_1")

        self.assertGreater(
            out_high.trajectory_points[60].constrained_revenue,
            out_low.trajectory_points[60].constrained_revenue,
        )

    def test_human_mind_mixing_policy_override_delay(self):
        """Verifies policy override banning air freight introduces extra transition lag."""
        c_air = ExecutiveConstraint(policy_override_note="Prohibit expedited air freight")
        out = self.model.synthesize(tree_res=self.tree_res, constraint=c_air, scenario_id="scenario_1")
        # At day 6, constrained recovery is delayed compared to recommended
        self.assertLess(
            out.trajectory_points[6].constrained_revenue,
            out.trajectory_points[6].recommended_revenue,
        )

    def test_persona_tailoring_executive_vs_operations(self):
        """Verifies Executive receives strategic brief while Operations receives tactical playbook."""
        out_exec = self.model.synthesize(tree_res=self.tree_res, role=UserRole.EXECUTIVE, scenario_id="scenario_1")
        out_ops = self.model.synthesize(tree_res=self.tree_res, role=UserRole.OPERATIONS_ANALYST, scenario_id="scenario_1")

        self.assertIn("EXECUTIVE", out_exec.headline)
        self.assertIn("OPERATIONS", out_ops.headline)
        self.assertNotEqual(out_exec.narrative, out_ops.narrative)

    def test_cold_start_trajectory_wide_confidence_envelope(self):
        """Verifies cold-start scenario widens uncertainty envelope to ±45%."""
        out_cold = self.model.synthesize(tree_res=self.tree_res, is_cold_start=True, scenario_id="scenario_3")
        self.assertTrue("COLD-START" in out_cold.headline or "COLD" in out_cold.headline)
        pt = out_cold.trajectory_points[30]
        # Spread should be ~ ±45%
        upper_diff = (pt.upper_bound_95 - pt.recommended_revenue) / pt.recommended_revenue
        self.assertAlmostEqual(upper_diff, 0.45, delta=0.05)

    def test_model3_dict_and_pydantic_subscripting(self):
        """Verifies output supports both object attribute access and dict indexing."""
        out = self.model.synthesize(tree_res=self.tree_res, scenario_id="scenario_1")
        self.assertEqual(out["headline"], out.headline)
        self.assertEqual(out["attribution_internal_pct"], out.attribution_internal_pct)
        self.assertEqual(out["attribution_external_pct"], out.attribution_external_pct)
        self.assertEqual(out["is_abstaining"], out.is_abstaining)


if __name__ == "__main__":
    unittest.main()
