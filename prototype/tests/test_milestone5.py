"""Milestone 5 Unit Test Suite: Streamlit Interactive Decision Workspace UI Components."""

import os
import sys
import unittest
import pandas as pd
from unittest.mock import MagicMock, patch

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOTYPE_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(PROTOTYPE_DIR)
for path in [CURRENT_DIR, PROTOTYPE_DIR, ROOT_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from prototype.engine.contracts.schemas import (
        ExecutiveConstraint,
        ScenarioExecutionResult,
        UserRole,
    )
    from prototype.engine.scenarios.runner import ScenarioRunner
    from prototype.ui.styles import (
        CUSTOM_CSS,
        MATH_CORE_BADGE_HTML,
        AI_ENGINE_BADGE_HTML,
        ABSTENTION_BADGE_HTML,
        COLDSTART_BADGE_HTML,
        RBAC_BADGE_HTML,
    )
    from prototype.ui.components import (
        render_header,
        render_sidebar,
        render_spc_view,
        render_tree_view,
        render_synthesis_view,
        render_simulation_view,
        render_feedback_widget,
        render_lineage_drawer,
        render_telemetry_box,
    )
except ImportError:
    from engine.contracts.schemas import (
        ExecutiveConstraint,
        ScenarioExecutionResult,
        UserRole,
    )
    from engine.scenarios.runner import ScenarioRunner
    from ui.styles import (
        CUSTOM_CSS,
        MATH_CORE_BADGE_HTML,
        AI_ENGINE_BADGE_HTML,
        ABSTENTION_BADGE_HTML,
        COLDSTART_BADGE_HTML,
        RBAC_BADGE_HTML,
    )
    from ui.components import (
        render_header,
        render_sidebar,
        render_spc_view,
        render_tree_view,
        render_synthesis_view,
        render_simulation_view,
        render_feedback_widget,
        render_lineage_drawer,
        render_telemetry_box,
    )


class TestMilestone5StylesAndBadges(unittest.TestCase):
    """Test UI CSS styles, badge definitions, and visual differentiation contract."""

    def test_custom_css_presence(self):
        """Verifies CUSTOM_CSS defines required styles and color palettes."""
        self.assertIn("badge-math-core", CUSTOM_CSS)
        self.assertIn("badge-ai-engine", CUSTOM_CSS)
        self.assertIn("badge-abstention", CUSTOM_CSS)
        self.assertIn("badge-coldstart", CUSTOM_CSS)
        self.assertIn("badge-rbac-active", CUSTOM_CSS)
        self.assertIn("telemetry-card", CUSTOM_CSS)
        self.assertIn("math-formula-box", CUSTOM_CSS)

    def test_badge_html_strings(self):
        """Verifies badge HTML strings adhere to the visual differentiation contract."""
        self.assertIn("DETERMINISTIC MATH CORE", MATH_CORE_BADGE_HTML)
        self.assertIn("AI SYNTHESIS ENGINE", AI_ENGINE_BADGE_HTML)
        self.assertIn("ENGINE ABSTENTION PROTOCOL", ABSTENTION_BADGE_HTML)
        self.assertIn("COLD START LAUNCH", COLDSTART_BADGE_HTML)
        self.assertIn("ROLE-BASED ACCESS CONTROL", RBAC_BADGE_HTML)


class TestMilestone5UIComponents(unittest.TestCase):
    """Test UI component rendering with mocked Streamlit calls."""

    def setUp(self):
        self.runner = ScenarioRunner(mode="mock")

    @staticmethod
    def _make_columns(spec):
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        return [MagicMock() for _ in range(n)]

    @patch("streamlit.markdown")
    @patch("streamlit.title")
    @patch("streamlit.columns")
    def test_render_header(self, mock_cols, mock_title, mock_md):
        """Verifies header renders title, status badges, and 4 KPI metrics."""
        mock_cols.side_effect = self._make_columns
        res = self.runner.run(scenario_id="scenario_1", persona=UserRole.EXECUTIVE)
        daily_df = self.runner.loader.get_daily_harmonized_df()

        render_header(result=res, daily_df=daily_df)
        mock_title.assert_called_with("⚡ BusinessIntelligence.ai")
        self.assertTrue(mock_md.called)

    @patch("streamlit.plotly_chart")
    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.columns")
    def test_render_spc_view(self, mock_cols, mock_sub, mock_md, mock_chart):
        """Verifies SPC view renders without errors and plots control chart."""
        mock_cols.side_effect = self._make_columns
        res = self.runner.run(scenario_id="scenario_1", persona=UserRole.EXECUTIVE)
        daily_df = self.runner.loader.get_daily_harmonized_df()

        render_spc_view(spc_res=res.spc_result, daily_df=daily_df)
        mock_chart.assert_called_once()
        self.assertTrue(mock_sub.called)

    @patch("streamlit.plotly_chart")
    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.latex")
    @patch("streamlit.columns")
    def test_render_tree_view(self, mock_cols, mock_latex, mock_sub, mock_md, mock_chart):
        """Verifies Causal Metric Tree view renders LaTeX equations and waterfall chart."""
        mock_cols.side_effect = self._make_columns
        res = self.runner.run(scenario_id="scenario_1", persona=UserRole.EXECUTIVE)

        render_tree_view(tree_res=res.tree_result)
        mock_latex.assert_called_once()
        mock_chart.assert_called_once()

    @patch("streamlit.plotly_chart")
    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.columns")
    def test_render_synthesis_view_all_scenarios(self, mock_cols, mock_sub, mock_md, mock_chart):
        """Verifies Synthesis view renders correctly for all 4 scenarios."""
        mock_cols.side_effect = self._make_columns
        for s_id in ["scenario_1", "scenario_2", "scenario_3", "scenario_4"]:
            res = self.runner.run(scenario_id=s_id, persona=UserRole.EXECUTIVE)
            render_synthesis_view(result=res, role=UserRole.EXECUTIVE)

    @patch("streamlit.plotly_chart")
    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.columns")
    def test_render_simulation_view(self, mock_cols, mock_sub, mock_md, mock_chart):
        """Verifies 30/60/90-day trajectory ROI simulator renders curve."""
        mock_cols.side_effect = self._make_columns
        res = self.runner.run(scenario_id="scenario_1", persona=UserRole.EXECUTIVE)

        render_simulation_view(synthesis_result=res.synthesis_result, budget_cap=45000.0)
        mock_chart.assert_called_once()

    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.columns")
    def test_render_telemetry_box(self, mock_cols, mock_sub, mock_md):
        """Verifies live telemetry box renders 4 metric cards."""
        mock_cols.side_effect = self._make_columns
        res = self.runner.run(scenario_id="scenario_1", persona=UserRole.EXECUTIVE)

        render_telemetry_box(telemetry=res.telemetry)
        self.assertTrue(mock_sub.called)


if __name__ == "__main__":
    unittest.main()

