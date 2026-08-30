"""Scenario Runner: Unified pipeline orchestrating Data Loader, SPC, Trees, 3-Model AI, and Telemetry."""

import time
from datetime import date
from typing import Any, Dict, List, Optional, Union
import pandas as pd

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
    from prototype.engine.math.materiality import build_materiality_report
    from prototype.engine.data.health import DataHealthEngine
    from prototype.engine.telemetry.feedback import FeedbackManager
    from prototype.engine.scenarios.scenario1_multifactor import Scenario1Runner
    from prototype.engine.scenarios.scenario2_ambiguous import Scenario2Runner
    from prototype.engine.scenarios.scenario3_coldstart import Scenario3Runner
    from prototype.engine.scenarios.scenario4_rbac import Scenario4Runner
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
    from engine.math.materiality import build_materiality_report
    from engine.data.health import DataHealthEngine
    from engine.telemetry.feedback import FeedbackManager
    from engine.scenarios.scenario1_multifactor import Scenario1Runner
    from engine.scenarios.scenario2_ambiguous import Scenario2Runner
    from engine.scenarios.scenario3_coldstart import Scenario3Runner
    from engine.scenarios.scenario4_rbac import Scenario4Runner
    from engine.synthesis.model1_diagnostic import Model1Diagnostic
    from engine.synthesis.model2_macro import Model2MacroSentinel
    from engine.synthesis.model3_prescriptive import Model3Prescriptive
    from engine.synthesis.providers import PluggableLLMProvider
    from engine.telemetry.tracker import TelemetryTracker


class ScenarioRunner:
    """
    Unified end-to-end orchestration runner for all 4 KPI intelligence scenarios.
    Provides single clean entry points `ScenarioRunner.run(...)` and `ScenarioRunner.run_scenario(...)`.
    """

    def __init__(self, mode: str = "mock"):
        self.mode = mode
        self.loader = MultiSourceDataLoader()
        self.spc = StatisticalProcessControl(window_days=28, sigma_threshold=2.5)
        self.m1 = Model1Diagnostic(provider=PluggableLLMProvider(mode=mode))
        self.m2 = Model2MacroSentinel(provider=PluggableLLMProvider(mode=mode))
        self.m3 = Model3Prescriptive(provider=PluggableLLMProvider(mode=mode))
        self.tracker = TelemetryTracker()
        self.feedback_manager = FeedbackManager()

        # Modular scenario runners
        self.s1_runner = Scenario1Runner(mode=mode)
        self.s2_runner = Scenario2Runner(mode=mode)
        self.s3_runner = Scenario3Runner(mode=mode)
        self.s4_runner = Scenario4Runner(mode=mode)

    def run(
        self,
        scenario_id: str = "scenario_1",
        persona: UserRole = UserRole.EXECUTIVE,
        constraints: Optional[ExecutiveConstraint] = None,
        llm_mode: Optional[str] = None,
        **kwargs,
    ) -> ScenarioExecutionResult:
        """
        Primary interface contract method.
        Executes the specified scenario and returns a typed ScenarioExecutionResult.
        """
        norm_id = str(scenario_id).lower().replace("-", "_")
        mode = llm_mode or self.mode

        if "2" in norm_id or "ambiguous" in norm_id:
            scenario_runner = self.s2_runner
        elif "3" in norm_id or "cold" in norm_id:
            scenario_runner = self.s3_runner
        elif "4" in norm_id or "rbac" in norm_id:
            scenario_runner = self.s4_runner
        else:
            scenario_runner = self.s1_runner

        result = scenario_runner.run(
            persona=persona, constraints=constraints, llm_mode=mode, **kwargs
        )

        # Post-run governance layer shared by every scenario. This is deliberately
        # deterministic and does not invoke an LLM.
        try:
            bundle = scenario_runner.loader.bundle
            daily_df = scenario_runner.loader.get_daily_harmonized_df()
            confidence = (
                float(result.spc_result.confidence_score)
                if result.spc_result is not None else 1.0
            )
            result.materiality_report = build_materiality_report(
                daily_df=daily_df,
                evaluation_date=bundle.evaluation_date,
                confidence=confidence,
            )
            result.data_health = DataHealthEngine.assess(bundle)
            result.learning_summary = self.feedback_manager.get_learning_summary()

            # Surface the governance outputs in the KPI summary for API consumers.
            if result.kpi_summary is None:
                result.kpi_summary = {}
            result.kpi_summary["materiality_score"] = result.materiality_report.get("top_score", 0.0)
            result.kpi_summary["materiality_priority"] = (
                result.materiality_report["kpis"][0]["priority"]
                if result.materiality_report.get("kpis") else "P3 - LOW"
            )
            result.kpi_summary["data_health_status"] = [
                {"source": x["source"], "status": x["status"], "freshness_hours": x["freshness_hours"]}
                for x in (result.data_health or [])
            ]
        except Exception as exc:
            # Governance enrichment must never break the existing scenario pipeline.
            if result.kpi_summary is None:
                result.kpi_summary = {}
            result.kpi_summary["governance_warning"] = str(exc)

        return result

    def run_scenario(
        self,
        scenario_id: str = "scenario_1",
        role: UserRole = UserRole.EXECUTIVE,
        constraint: Optional[ExecutiveConstraint] = None,
        **kwargs,
    ) -> ScenarioExecutionResult:
        """
        Backward-compatible execution method matching legacy interface signatures.
        """
        return self.run(
            scenario_id=scenario_id,
            persona=role,
            constraints=constraint,
            **kwargs,
        )

    def run_all(
        self,
        persona: UserRole = UserRole.EXECUTIVE,
        llm_mode: Optional[str] = None,
    ) -> Dict[str, ScenarioExecutionResult]:
        """
        Executes all 4 scenarios sequentially and returns a mapping of scenario_id -> result.
        """
        results: Dict[str, ScenarioExecutionResult] = {}
        for s_id in ["scenario_1", "scenario_2", "scenario_3", "scenario_4"]:
            results[s_id] = self.run(scenario_id=s_id, persona=persona, llm_mode=llm_mode)
        return results

    def get_telemetry_history(self) -> List[TelemetryRecord]:
        """Returns aggregated telemetry history across runs."""
        records: List[TelemetryRecord] = []
        for runner in [self.s1_runner, self.s2_runner, self.s3_runner, self.s4_runner]:
            records.extend(runner.tracker.get_all_records())
        return records
