"""Round 2 upgrade tests: materiality, data health, feedback learning, and action contract."""
import os
import tempfile
import unittest
from datetime import date
import pandas as pd

from prototype.engine.math.materiality import MaterialityEngine, build_materiality_report
from prototype.engine.data.generator import MultiSourceDataGenerator
from prototype.engine.data.health import DataHealthEngine
from prototype.engine.telemetry.learning import FeedbackLearningEngine
from prototype.engine.telemetry.feedback import FeedbackManager
from prototype.engine.scenarios.runner import ScenarioRunner
from prototype.engine.contracts.schemas import UserRole


class TestRound2Upgrades(unittest.TestCase):
    def test_materiality_prioritises_revenue(self):
        runner = ScenarioRunner(mode="mock")
        result = runner.run("scenario_1", UserRole.EXECUTIVE)
        self.assertIsNotNone(result.materiality_report)
        self.assertEqual(result.materiality_report["top_kpi"], "Gross Revenue")
        self.assertGreaterEqual(result.materiality_report["top_score"], 80)

    def test_materiality_is_deterministic(self):
        b = {"Gross Revenue": 100000, "Order Volume": 3000, "Sessions": 100000,
             "Conversion Rate": .03, "AOV": 33.33}
        o = {"Gross Revenue": 80000, "Order Volume": 2400, "Sessions": 90000,
             "Conversion Rate": .0267, "AOV": 33.33}
        a = MaterialityEngine().rank(b, o, {"Gross Revenue": -4, "Order Volume": -3, "Sessions": -2, "Conversion Rate": -2, "AOV": 0})
        c = MaterialityEngine().rank(b, o, {"Gross Revenue": -4, "Order Volume": -3, "Sessions": -2, "Conversion Rate": -2, "AOV": 0})
        self.assertEqual(a, c)

    def test_data_health_covers_three_grains(self):
        bundle = MultiSourceDataGenerator(seed=42).generate("scenario_1")
        rows = DataHealthEngine.assess(bundle)
        self.assertEqual({r["source"] for r in rows}, {"ERP", "Web Analytics", "Jira / Support"})
        self.assertEqual({r["grain"] for r in rows}, {"Daily", "Hourly", "Weekly"})

    def test_feedback_learning_updates_calibration(self):
        with tempfile.TemporaryDirectory() as td:
            engine = FeedbackLearningEngine(os.path.join(td, "feedback.json"))
            engine.learn("scenario_1", 5, "Port Strike", "Port Strike")
            engine.learn("scenario_1", 2, "Port Strike", "Warehouse Backlog")
            summary = engine.calibration()
            self.assertEqual(summary["feedback_count"], 2)
            self.assertEqual(summary["correction_count"], 2)
            self.assertIn("Port Strike", summary["driver_calibration"])
            self.assertEqual(summary["driver_calibration"]["Port Strike"]["accuracy"], .5)

    def test_feedback_manager_accepts_correction(self):
        with tempfile.TemporaryDirectory() as td:
            mgr = FeedbackManager()
            mgr.learning = FeedbackLearningEngine(os.path.join(td, "feedback.json"))
            entry = mgr.record_feedback(
                "scenario_2", 4, "Evidence points to gateway", predicted_driver="Competitor",
                corrected_driver="Payment Gateway"
            )
            self.assertEqual(entry["star_rating"], 4)
            self.assertEqual(mgr.get_learning_summary()["correction_count"], 1)

    def test_structured_action_contract_present(self):
        result = ScenarioRunner(mode="mock").run("scenario_1", UserRole.EXECUTIVE)
        actions = result.synthesis_result.structured_action_playbook
        self.assertTrue(actions)
        self.assertTrue(actions[0].controllable_lever)
        self.assertGreaterEqual(actions[0].confidence_score, .5)
        self.assertTrue(actions[0].monitoring_plan)
        self.assertTrue(actions[0].decision_rights)

    def test_telemetry_reports_llm_calls_by_mode(self):
        mock_result = ScenarioRunner(mode="mock").run("scenario_1", UserRole.EXECUTIVE)
        self.assertEqual(mock_result.telemetry.llm_calls, 0)

    def test_connector_registry_has_four_sources(self):
        from prototype.engine.data.connectors import DataConnectorRegistry
        statuses = DataConnectorRegistry().status()
        self.assertEqual(len(statuses), 4)
        self.assertTrue(all(x["mode"] == "SYNTHETIC FALLBACK" for x in statuses))


if __name__ == "__main__":
    unittest.main(verbosity=2)
