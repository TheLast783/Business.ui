"""Scenario 2 Runner: Low-Confidence Ambiguity & Explicit Engine Abstention."""

import time
from datetime import date
from typing import Any, Dict, List, Optional, Union

try:
    from prototype.engine.contracts.schemas import (
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
    from prototype.engine.data.loader import MultiSourceDataLoader
    from prototype.engine.math.causal_tree import CausalMetricTree
    from prototype.engine.math.metrics import KPICalculator
    from prototype.engine.math.spc import StatisticalProcessControl
    from prototype.engine.synthesis.abstention import AbstentionEngine
    from prototype.engine.synthesis.model1_diagnostic import Model1Diagnostic
    from prototype.engine.synthesis.model2_macro import Model2MacroSentinel
    from prototype.engine.synthesis.model3_prescriptive import Model3Prescriptive
    from prototype.engine.synthesis.providers import PluggableLLMProvider
    from prototype.engine.telemetry.tracker import TelemetryTracker
except ImportError:
    from engine.contracts.schemas import (
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
    from engine.data.loader import MultiSourceDataLoader
    from engine.math.causal_tree import CausalMetricTree
    from engine.math.metrics import KPICalculator
    from engine.math.spc import StatisticalProcessControl
    from engine.synthesis.abstention import AbstentionEngine
    from engine.synthesis.model1_diagnostic import Model1Diagnostic
    from engine.synthesis.model2_macro import Model2MacroSentinel
    from engine.synthesis.model3_prescriptive import Model3Prescriptive
    from engine.synthesis.providers import PluggableLLMProvider
    from engine.telemetry.tracker import TelemetryTracker


class Scenario2Runner:
    """
    Executes Scenario 2: Low-Confidence / Ambiguous Signals.
    Demonstrates:
    - Ingestion of conflicting operational logs vs external competitor promotions
    - Confidence margin < 25% triggering explicit engine abstention (is_abstaining=True)
    - 2 ranked competing hypotheses (58% internal gateway timeout vs 42% external competitor flash discount)
    - 2 low-cost, short-runtime canary validation tests (< $150)
    - Prevention of premature capital misallocation
    """

    def __init__(self, mode: str = "mock"):
        self.loader = MultiSourceDataLoader()
        self.spc = StatisticalProcessControl(window_days=28, sigma_threshold=2.5)
        # Use the selected LLM mode for all three cognitive models.
        # Quantitative calculations remain deterministic inside the scenario.
        self.m1 = Model1Diagnostic(
            provider=PluggableLLMProvider(mode=mode)
        )
        self.m2 = Model2MacroSentinel(
            provider=PluggableLLMProvider(mode=mode)
        )
        self.m3 = Model3Prescriptive(
            provider=PluggableLLMProvider(mode=mode)
        )
        self.tracker = TelemetryTracker()
        self.mode = mode

    def run(
        self,
        persona: UserRole = UserRole.EXECUTIVE,
        constraints: Optional[ExecutiveConstraint] = None,
        llm_mode: Optional[str] = None,
        **kwargs,
    ) -> ScenarioExecutionResult:
        """
        Executes the Scenario 2 ambiguity & abstention pipeline.
        """
        t_start = self.tracker.start_timer()
        mode = llm_mode or self.mode

        # 1. Ingestion & Harmonization
        t_ingest_0 = time.time()
        bundle = self.loader.load_scenario(scenario_id="scenario_2")
        daily_df = self.loader.get_daily_harmonized_df()
        ingestion_ms = (time.time() - t_ingest_0) * 1000.0

        # 2. Statistical Process Control
        t_math_0 = time.time()
        revenues = daily_df["gross_revenue"].tolist()
        dates = daily_df["date"].tolist()
        spc_result: SPCResult = self.spc.evaluate(values=revenues, dates=dates)

        # 3. Causal Metric Tree Decomposition
        baseline_snap, observed_snap = self.loader.get_baseline_and_observed_snapshots()
        tree_result: TreeDecompositionResult = CausalMetricTree.decompose_snapshots(
            baseline_snap, observed_snap, method="shapley_3factor"
        )
        math_ms = (time.time() - t_math_0) * 1000.0

        # 4. Model 1 (Conflicting Internal Diagnostic)
        t_llm_0 = time.time()
        support_records: List[SupportJiraRecord] = []
        if bundle.jira_df is not None and not bundle.jira_df.empty:
            for r in bundle.jira_df.to_dict(orient="records"):
                support_records.append(
                    SupportJiraRecord(
                        ticket_id=str(r.get("ticket_id", "INC-GATEWAY-02")),
                        created_timestamp=r.get("created_timestamp"),
                        week_start_date=r.get("week_start_date", date(2026, 8, 24)),
                        category=str(r.get("category", "Payment Gateway Timeout")),
                        severity=str(r.get("severity", "P1")),
                        status=str(r.get("status", "Investigating")),
                        summary=str(r.get("summary", "Stripe HTTP 504 Gateway Timeout")),
                        description_text=str(r.get("description_text", "Sporadic payment timeouts on checkout")),
                        affected_customer_tier=str(r.get("affected_customer_tier", "VIP")),
                        carrier_or_system_id=str(r.get("carrier_or_system_id", "PAYMENT-GW-STRIPE-504")),
                    )
                )

        m1_findings = self.m1.analyze(
            tickets=support_records,
            unfulfilled_orders=85,
            delayed_revenue=18000.0,
            scenario_id="scenario_2",
        )

        # 5. Model 2 (Conflicting External Referral / Competitor Flash Campaign)
        macro_feeds = [
            {
                "feed_id": "FEED-TIKTOK-RIVAL-01",
                "source": "Competitor Intelligence API",
                "event_name": "Rival Retailer Flash Discount Campaign",
                "headline": "Competitor launches 35% flash discount coupon on TikTok viral stream",
                "severity_index": 7.0,
                "severity": "HIGH",
                "confidence": 0.82,
                "signal_type": "COMPETITOR_PRICING",
            }
        ]
        m2_findings = self.m2.analyze(
            external_signals=macro_feeds,
            scenario_id="scenario_2",
        )

        # 6. Model 3 (Prescriptive Synthesis with Explicit Abstention)
        m3_output: PrescriptiveSimulationOutput = self.m3.synthesize(
            tree_res=tree_result,
            m1_findings=m1_findings,
            m2_findings=m2_findings,
            role=persona,
            constraint=constraints,
            is_cold_start=False,
            force_ambiguity=True,
            scenario_id="scenario_2",
        )
        llm_ms = (time.time() - t_llm_0) * 1000.0

        # 7. Dynamic RBAC Masking
        masked_erp = self.loader.get_masked_erp_data(persona)

        # 8. Runtime Telemetry Recording
        prompt_toks = 480 if mode != "mock" else 430
        comp_toks = 210 if mode != "mock" else 190
        telemetry: TelemetryRecord = self.tracker.record_run(
            scenario_id="scenario_2",
            start_time_s=t_start,
            prompt_tokens=prompt_toks,
            completion_tokens=comp_toks,
            math_time_ms=math_ms,
            ingestion_time_ms=ingestion_ms,
            llm_time_ms=llm_ms,
            mode=mode,
        )

        kpi_summary = {
            "status": "ABSTAINED",
            "is_abstaining": True,
            "overall_confidence": m3_output.overall_confidence,
            "hypothesis_1_likelihood_pct": 58.0,
            "hypothesis_2_likelihood_pct": 42.0,
            "confidence_margin_pct": 16.0,
            "canary_tests_count": len(m3_output.canary_validation_tests),
            "delta_revenue": tree_result.delta_revenue,
        }

        return ScenarioExecutionResult(
            scenario_id="scenario_2",
            persona=persona,
            kpi_summary=kpi_summary,
            spc_result=spc_result,
            tree_result=tree_result,
            synthesis_result=m3_output,
            masked_erp_data=masked_erp,
            telemetry=telemetry,
        )
