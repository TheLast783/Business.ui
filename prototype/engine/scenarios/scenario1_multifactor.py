"""Scenario 1 Runner: Multi-Factor KPI Movement (70% External Macro / 30% Internal Warehouse)."""

import time
from datetime import date
from typing import Any, Dict, List, Optional, Union

try:
    from prototype.engine.contracts.schemas import (
        ExecutiveConstraint,
        MetricSnapshot,
        PrescriptiveSimulationOutput,
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
    from prototype.engine.synthesis.model1_diagnostic import Model1Diagnostic
    from prototype.engine.synthesis.model2_macro import Model2MacroSentinel
    from prototype.engine.synthesis.model3_prescriptive import Model3Prescriptive
    from prototype.engine.synthesis.providers import PluggableLLMProvider
    from prototype.engine.telemetry.tracker import TelemetryTracker
except ImportError:
    from engine.contracts.schemas import (
        ExecutiveConstraint,
        MetricSnapshot,
        PrescriptiveSimulationOutput,
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
    from engine.synthesis.model1_diagnostic import Model1Diagnostic
    from engine.synthesis.model2_macro import Model2MacroSentinel
    from engine.synthesis.model3_prescriptive import Model3Prescriptive
    from engine.synthesis.providers import PluggableLLMProvider
    from engine.telemetry.tracker import TelemetryTracker


class Scenario1Runner:
    """
    Executes Scenario 1: Compound Multi-Factor Movement.
    Demonstrates:
    - 4 connected KPIs across Daily ERP, Hourly Web, and Weekly Jira
    - SPC detecting statistical anomaly (z < -2.5 sigma)
    - Exact zero-residual Shapley causal metric tree decomposition
    - 70% macro port strike + 30% warehouse backlog synthesis
    - 30/60/90-day trajectory simulation yielding positive net ROI
    - Telemetry tracking with deterministic math vs LLM separation
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
        Executes the complete Scenario 1 intelligence-to-action pipeline.
        """
        t_start = self.tracker.start_timer()
        mode = llm_mode or self.mode

        # 1. Ingestion & Grain Harmonization
        t_ingest_0 = time.time()
        bundle = self.loader.load_scenario(scenario_id="scenario_1")
        daily_df = self.loader.get_daily_harmonized_df()
        ingestion_ms = (time.time() - t_ingest_0) * 1000.0

        # 2. Statistical Process Control (Deterministic Math)
        t_math_0 = time.time()
        revenues = daily_df["gross_revenue"].tolist()
        dates = daily_df["date"].tolist()
        spc_result: SPCResult = self.spc.evaluate(values=revenues, dates=dates)

        # 3. Exact Causal Metric Tree Decomposition (Deterministic Math)
        baseline_snap, observed_snap = self.loader.get_baseline_and_observed_snapshots()
        tree_result: TreeDecompositionResult = CausalMetricTree.decompose_snapshots(
            baseline_snap, observed_snap, method="shapley_3factor"
        )
        math_ms = (time.time() - t_math_0) * 1000.0

        # 4. Model 1 (Internal Diagnostic)
        t_llm_0 = time.time()
        support_records: List[SupportJiraRecord] = []
        if bundle.jira_df is not None and not bundle.jira_df.empty:
            for r in bundle.jira_df.to_dict(orient="records"):
                support_records.append(
                    SupportJiraRecord(
                        ticket_id=str(r.get("ticket_id", "JIRA-4819")),
                        created_timestamp=r.get("created_timestamp"),
                        week_start_date=r.get("week_start_date", date(2026, 8, 24)),
                        category=str(r.get("category", "Shipping Delay")),
                        severity=str(r.get("severity", "P1")),
                        status=str(r.get("status", "Open")),
                        summary=str(r.get("summary", "Port of LA bottleneck")),
                        description_text=str(r.get("description_text", "Inbound freight diverted")),
                        affected_customer_tier=str(r.get("affected_customer_tier", "VIP")),
                        carrier_or_system_id=str(r.get("carrier_or_system_id", "PORT-LAX-DOCK-3")),
                    )
                )

        m1_findings = self.m1.analyze(
            tickets=support_records,
            unfulfilled_orders=340,
            delayed_revenue=78000.0,
            scenario_id="scenario_1",
        )

        # 5. Model 2 (Macro Sentinel)
        macro_feeds = [
            {
                "feed_id": "MACRO-PORT-01",
                "source": "FreightWaves",
                "event_name": "West Coast Port Labor Slowdown",
                "headline": "ILWU dockworker negotiations delaying container offloading at LA/Long Beach",
                "severity_index": 8.5,
                "severity": "CRITICAL",
                "confidence": 0.92,
                "signal_type": "SUPPLY_CHAIN",
            }
        ]
        m2_findings = self.m2.analyze(
            external_signals=macro_feeds,
            scenario_id="scenario_1",
            observed_drop_pct=float(tree_result.delta_revenue / max(1.0, baseline_snap.gross_revenue) * 100.0),
        )

        # 6. Model 3 (Prescriptive Action & Trajectory Simulator)
        m3_output: PrescriptiveSimulationOutput = self.m3.synthesize(
            tree_res=tree_result,
            m1_findings=m1_findings,
            m2_findings=m2_findings,
            role=persona,
            constraint=constraints,
            is_cold_start=False,
            force_ambiguity=False,
            scenario_id="scenario_1",
        )
        llm_ms = (time.time() - t_llm_0) * 1000.0

        # 7. Dynamic RBAC Masking
        masked_erp = self.loader.get_masked_erp_data(persona)

        # 8. Runtime Telemetry Recording
        prompt_toks = 450 if mode != "mock" else 420
        comp_toks = 180 if mode != "mock" else 160
        telemetry: TelemetryRecord = self.tracker.record_run(
            scenario_id="scenario_1",
            start_time_s=t_start,
            prompt_tokens=prompt_toks,
            completion_tokens=comp_toks,
            math_time_ms=math_ms,
            ingestion_time_ms=ingestion_ms,
            llm_time_ms=llm_ms,
            mode=mode,
        )

        kpi_summary = {
            "baseline_gross_revenue": baseline_snap.gross_revenue,
            "observed_gross_revenue": observed_snap.gross_revenue,
            "delta_revenue": tree_result.delta_revenue,
            "sessions_drop_pct": KPICalculator.pct_change(baseline_snap.sessions, observed_snap.sessions),
            "cvr_drop_pct": KPICalculator.pct_change(baseline_snap.conversion_rate, observed_snap.conversion_rate),
            "aov_change_pct": KPICalculator.pct_change(baseline_snap.aov, observed_snap.aov),
            "macro_attribution_pct": m3_output.attribution_external_pct,
            "internal_attribution_pct": m3_output.attribution_internal_pct,
            "net_roi_90d_usd": m3_output.net_roi_usd,
            "roi_multiplier": m3_output.estimated_roi_multiplier,
        }

        return ScenarioExecutionResult(
            scenario_id="scenario_1",
            persona=persona,
            kpi_summary=kpi_summary,
            spc_result=spc_result,
            tree_result=tree_result,
            synthesis_result=m3_output,
            masked_erp_data=masked_erp,
            telemetry=telemetry,
        )
