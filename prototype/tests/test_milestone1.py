"""Milestone 1 Unit Test Suite: Data Architecture, Governed Semantic Contract, and RBAC."""

import datetime
from datetime import date, timedelta
import unittest
import pandas as pd
import numpy as np

from prototype.engine.config import (
    ANOMALY_Z_THRESHOLD,
    RECONCILIATION_TOLERANCE,
    REDACTED_CONFIDENTIAL_STR,
    REDACTED_CUSTOMER_PREFIX,
    SPC_BASELINE_WINDOW_DAYS,
)
from prototype.engine.contracts.schemas import (
    AnomalyDirection,
    AnomalyRecord,
    AnomalySeverity,
    DataQuality,
    ERPSalesRecord,
    ExecutiveConstraint,
    MetricSnapshot,
    SupportJiraRecord,
    TelemetryRecord,
    UserRole,
    WebSessionRecord,
)
from prototype.engine.contracts.semantic_contract import (
    RBACMaskingEngine,
    SemanticContract,
    SemanticLineageGraph,
)
from prototype.engine.data.generator import (
    MultiSourceDataGenerator,
    ScenarioDataBundle,
)
from prototype.engine.data.loader import MultiSourceDataLoader


class TestM1Schemas(unittest.TestCase):
    """Test strict Pydantic schemas and dataclass models."""

    def test_erp_sales_record_valid(self):
        record = ERPSalesRecord(
            order_id="ORD-20260829-001",
            transaction_date=date(2026, 8, 29),
            timestamp=datetime.datetime(2026, 8, 29, 14, 30, 0),
            customer_id="CUST-9912",
            sku_id="SKU-ELEC-100",
            product_category="Electronics",
            quantity=2,
            unit_price=50.0,
            discount_amount=5.0,
            gross_revenue=95.0,
            unit_cogs=24.50,
            gross_margin=46.0,
            gross_margin_pct=48.42,
            fulfillment_status="Shipped",
            shipping_location="PORT-LAX-WH",
            channel="Direct",
        )
        self.assertEqual(record.order_id, "ORD-20260829-001")
        self.assertEqual(record.gross_revenue, 95.0)

    def test_web_session_record_valid(self):
        web = WebSessionRecord(
            session_id="WEB-20260829-14",
            session_timestamp=datetime.datetime(2026, 8, 29, 14, 0, 0),
            session_date=date(2026, 8, 29),
            session_hour=14,
            visitor_id="VIS-1401",
            traffic_source="Organic",
            device_category="Desktop",
            page_views=5,
            cart_add_events=1,
            checkout_start_events=1,
            purchase_events=1,
            is_converted=True,
            bounce_flag=False,
        )
        self.assertEqual(web.session_hour, 14)
        self.assertTrue(web.is_converted)

    def test_support_jira_record_valid(self):
        ticket = SupportJiraRecord(
            ticket_id="OPS-4821",
            created_timestamp=datetime.datetime(2026, 8, 28, 8, 15, 0),
            week_start_date=date(2026, 8, 24),
            category="Shipping Delay - West Coast Port Congestion",
            severity="P1",
            status="Open",
            summary="Port of LA bottleneck",
            description_text="ILWU dockworker negotiations delaying containers",
            affected_customer_tier="VIP",
            carrier_or_system_id="PORT-LAX-DOCK-3",
        )
        self.assertEqual(ticket.ticket_id, "OPS-4821")
        self.assertEqual(ticket.severity, "P1")

    def test_metric_snapshot_validation(self):
        # Valid snapshot
        snap = MetricSnapshot(
            period_label="Baseline",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 28),
            gross_revenue=150000.0,
            order_volume=3000,
            sessions=100000,
            conversion_rate=0.030,
            aov=50.00,
        )
        self.assertEqual(snap.gross_revenue, 150000.0)

        # Invalid conversion rate (> 1.0) must raise ValueError
        with self.assertRaises(ValueError):
            MetricSnapshot(
                period_label="Corrupted",
                start_date=date(2026, 8, 1),
                end_date=date(2026, 8, 28),
                gross_revenue=100.0,
                order_volume=10,
                sessions=5,
                conversion_rate=2.0,  # Invalid
                aov=10.0,
            )


class TestSemanticContractAndLineage(unittest.TestCase):
    """Test Governed Semantic Contract, Lineage Graph, and Mathematical Invariants."""

    def setUp(self):
        self.contract = SemanticContract()
        self.lineage = SemanticLineageGraph()

    def test_lineage_graph_nodes_and_trace(self):
        nodes = self.lineage.get_all_nodes()
        self.assertGreaterEqual(len(nodes), 7)
        kpi_node = self.lineage.get_node("kpi_gross_revenue")
        self.assertIsNotNone(kpi_node)
        self.assertEqual(kpi_node.node_type, "CANONICAL_KPI")

        trace = self.lineage.get_lineage_trace("kpi_conversion_rate")
        self.assertIn("src_web_sessions", trace)
        self.assertIn("src_erp_sales", trace)
        self.assertIn("kpi_order_volume", trace)
        self.assertIn("kpi_sessions", trace)

    def test_compute_kpis_from_aggregates(self):
        snapshot = self.contract.compute_kpis_from_aggregates(
            gross_revenue=150000.0,
            order_volume=3000,
            sessions=100000,
            period_label="Baseline",
            total_cogs=73500.0,
        )
        self.assertAlmostEqual(snapshot.conversion_rate, 0.030, places=4)
        self.assertAlmostEqual(snapshot.aov, 50.0, places=2)
        self.assertIsNotNone(snapshot.total_gross_margin)
        self.assertAlmostEqual(snapshot.total_gross_margin, 76500.0, places=2)
        self.assertAlmostEqual(snapshot.gross_margin_pct, 51.0, places=2)

    def test_validate_snapshot_invariants(self):
        valid_snap = MetricSnapshot(
            period_label="Valid",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 28),
            gross_revenue=83200.0,
            order_volume=1600,
            sessions=80000,
            conversion_rate=0.020,
            aov=52.00,
        )
        is_valid, violations = self.contract.validate_snapshot_invariants(valid_snap)
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)

    def test_reconcile_erp_and_web(self):
        # Within 2% tolerance
        is_ok, disc, msg = self.contract.reconcile_erp_and_web(1000, 1010, tolerance=0.02)
        self.assertTrue(is_ok)
        self.assertLess(disc, 0.02)

        # Exceeding 2% tolerance
        is_ok2, disc2, msg2 = self.contract.reconcile_erp_and_web(1000, 1100, tolerance=0.02)
        self.assertFalse(is_ok2)
        self.assertGreater(disc2, 0.02)


class TestRBACMasking(unittest.TestCase):
    """Test Role-Based Access Control dynamic masking for Executive vs Analyst."""

    def setUp(self):
        self.sample_df = pd.DataFrame([
            {
                "order_id": "ORD-001",
                "customer_id": "CUST-US-98101",
                "gross_revenue": 100.0,
                "unit_cogs": 45.0,
                "gross_margin": 55.0,
                "gross_margin_pct": 55.0,
                "shipping_location": "PORT-LAX-WH",
            },
            {
                "order_id": "ORD-002",
                "customer_id": "CUST-US-98102",
                "gross_revenue": 200.0,
                "unit_cogs": 90.0,
                "gross_margin": 110.0,
                "gross_margin_pct": 55.0,
                "shipping_location": "WH-OAKLAND",
            },
        ])

        self.jira_df = pd.DataFrame([
            {
                "ticket_id": "OPS-4821",
                "category": "Shipping Delay",
                "carrier_or_system_id": "PORT-LAX-DOCK-3",
                "summary": "Port congestion",
            }
        ])

    def test_analyst_role_masking(self):
        masked_erp = RBACMaskingEngine.mask_erp_dataframe(self.sample_df, UserRole.OPERATIONS_ANALYST)

        # Financial margins and unit COGS must be redacted
        for col in ["unit_cogs", "gross_margin", "gross_margin_pct"]:
            self.assertTrue((masked_erp[col] == REDACTED_CONFIDENTIAL_STR).all())

        # Customer ID must be anonymized
        self.assertTrue(masked_erp["customer_id"].iloc[0].startswith(REDACTED_CUSTOMER_PREFIX))

        # Jira system ID must remain visible for Analyst
        masked_jira = RBACMaskingEngine.mask_jira_dataframe(self.jira_df, UserRole.OPERATIONS_ANALYST)
        self.assertEqual(masked_jira["carrier_or_system_id"].iloc[0], "PORT-LAX-DOCK-3")
        self.assertEqual(masked_jira["ticket_id"].iloc[0], "OPS-4821")

    def test_executive_role_unmasked(self):
        exec_erp = RBACMaskingEngine.mask_erp_dataframe(self.sample_df, UserRole.EXECUTIVE)

        # Financial margins and unit COGS must remain visible floats
        self.assertIsInstance(exec_erp["unit_cogs"].iloc[0], (int, float, np.number))
        self.assertEqual(exec_erp["unit_cogs"].iloc[0], 45.0)
        self.assertEqual(exec_erp["gross_margin"].iloc[0], 55.0)
        self.assertEqual(exec_erp["customer_id"].iloc[0], "CUST-US-98101")


class TestDataGeneratorAndLoader(unittest.TestCase):
    """Test deterministic multi-source data generation and grain harmonization."""

    def setUp(self):
        self.generator = MultiSourceDataGenerator(seed=42)
        self.loader = MultiSourceDataLoader()

    def test_scenario_1_generation_and_loader(self):
        bundle = self.generator.generate("scenario_1")
        self.assertEqual(bundle.scenario_id, "scenario_1")
        self.assertEqual(bundle.baseline_days, 28)
        self.assertGreater(len(bundle.erp_df), 0)
        self.assertGreater(len(bundle.web_df), 0)
        self.assertGreater(len(bundle.jira_df), 0)

        # Load into loader
        self.loader.set_bundle(bundle)
        daily_df = self.loader.get_daily_harmonized_df()
        self.assertEqual(len(daily_df), 29)  # 28 days baseline + Day 29 anomaly

        # Check baseline vs observed snapshots
        base_snap, obs_snap = self.loader.get_baseline_and_observed_snapshots()
        self.assertAlmostEqual(obs_snap.gross_revenue, 83200.0, delta=2000.0)
        self.assertAlmostEqual(obs_snap.sessions, 80000, delta=1000)
        self.assertAlmostEqual(obs_snap.conversion_rate, 0.020, delta=0.005)
        self.assertAlmostEqual(obs_snap.aov, 52.0, delta=2.0)

    def test_scenario_2_ambiguous_generation(self):
        bundle = self.generator.generate("scenario_2")
        self.assertEqual(bundle.scenario_id, "scenario_2")
        self.assertTrue(bundle.ground_truth["is_ambiguous"])
        self.assertEqual(bundle.data_quality, DataQuality.INSUFFICIENT_SAMPLE)
        self.assertIn("hypothesis_1", bundle.ground_truth)
        self.assertIn("hypothesis_2", bundle.ground_truth)
        self.assertGreaterEqual(len(bundle.ground_truth["canary_tests"]), 2)

    def test_scenario_3_coldstart_generation(self):
        bundle = self.generator.generate("scenario_3")
        self.assertEqual(bundle.scenario_id, "scenario_3")
        self.assertEqual(bundle.baseline_days, 6)
        self.assertEqual(bundle.data_quality, DataQuality.COLD_START)
        self.assertTrue(bundle.ground_truth["is_cold_start"])

    def test_scenario_4_rbac_generation(self):
        bundle = self.generator.generate("scenario_4")
        self.assertEqual(bundle.scenario_id, "scenario_4")
        self.assertIn("unit_cogs", bundle.ground_truth["rbac_fields_masked_for_analyst"])

    def test_generator_reproducibility(self):
        gen1 = MultiSourceDataGenerator(seed=42)
        gen2 = MultiSourceDataGenerator(seed=42)
        b1 = gen1.generate("scenario_1")
        b2 = gen2.generate("scenario_1")
        pd.testing.assert_frame_equal(b1.erp_df, b2.erp_df)
        pd.testing.assert_frame_equal(b1.web_df, b2.web_df)
        pd.testing.assert_frame_equal(b1.jira_df, b2.jira_df)


class TestBoundaryAndAdversarialInvariants(unittest.TestCase):
    """Adversarial and boundary value tests for semantic contract and math compatibility."""

    def setUp(self):
        self.contract = SemanticContract()

    def test_zero_sessions_and_orders(self):
        snap = self.contract.compute_kpis_from_aggregates(
            gross_revenue=0.0,
            order_volume=0,
            sessions=0,
            period_label="ZeroState",
        )
        self.assertEqual(snap.conversion_rate, 0.0)
        self.assertEqual(snap.aov, 0.0)
        self.assertEqual(snap.gross_revenue, 0.0)

    def test_negative_values_raise_error(self):
        with self.assertRaises(ValueError):
            self.contract.compute_kpis_from_aggregates(
                gross_revenue=-500.0,
                order_volume=10,
                sessions=100,
            )

    def test_reconciliation_zero_boundary(self):
        is_ok, disc, msg = self.contract.reconcile_erp_and_web(0, 0)
        self.assertTrue(is_ok)
        self.assertEqual(disc, 0.0)

    def test_rbac_single_record_masking(self):
        erp_record = ERPSalesRecord(
            order_id="ORD-999",
            transaction_date=date(2026, 8, 29),
            timestamp=datetime.datetime(2026, 8, 29, 12, 0),
            customer_id="CUST-SECRET-007",
            sku_id="SKU-TOP-1",
            product_category="Electronics",
            quantity=1,
            unit_price=100.0,
            gross_revenue=100.0,
            unit_cogs=40.0,
            gross_margin=60.0,
            gross_margin_pct=60.0,
        )
        masked = RBACMaskingEngine.mask_erp_record(erp_record, UserRole.OPERATIONS_ANALYST)
        self.assertEqual(masked["unit_cogs"], REDACTED_CONFIDENTIAL_STR)
        self.assertEqual(masked["gross_margin"], REDACTED_CONFIDENTIAL_STR)
        self.assertTrue(masked["customer_id"].startswith(REDACTED_CUSTOMER_PREFIX))

        unmasked = RBACMaskingEngine.mask_erp_record(erp_record, UserRole.EXECUTIVE)
        self.assertEqual(unmasked["unit_cogs"], 40.0)
        self.assertEqual(unmasked["customer_id"], "CUST-SECRET-007")


if __name__ == "__main__":
    unittest.main()
