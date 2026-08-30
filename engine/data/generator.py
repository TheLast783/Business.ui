"""Deterministic synthetic multi-source data generator supporting all 4 scenarios."""

import datetime
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from prototype.engine.config import DEFAULT_RANDOM_SEED
from prototype.engine.contracts.schemas import (
    DataQuality,
    ERPSalesRecord,
    SupportJiraRecord,
    UserRole,
    WebSessionRecord,
)


@dataclass
class ScenarioDataBundle:
    """Encapsulates the 3 heterogeneous raw datasets and metadata for a scenario."""
    scenario_id: str
    scenario_name: str
    description: str
    erp_df: pd.DataFrame
    web_df: pd.DataFrame
    jira_df: pd.DataFrame
    baseline_days: int
    evaluation_date: date
    data_quality: DataQuality
    ground_truth: Dict[str, Any]


class MultiSourceDataGenerator:
    """Generates deterministic, multi-source business data across ERP, Web, and Jira."""

    # Day-of-week seasonality multipliers (Mon=0, Sun=6) - average = 1.0
    DOW_SEASONALITY = [1.05, 1.08, 1.05, 1.02, 1.10, 0.90, 0.80]

    # Standard Hourly Traffic Distribution (0-23) - sums to 1.000
    HOURLY_WEIGHTS = [
        0.010, 0.008, 0.006, 0.005, 0.006, 0.010,
        0.020, 0.035, 0.055, 0.065, 0.065, 0.060,
        0.055, 0.050, 0.050, 0.055, 0.060, 0.065,
        0.075, 0.080, 0.070, 0.050, 0.030, 0.015
    ]

    def __init__(self, seed: int = DEFAULT_RANDOM_SEED):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate(self, scenario_id: str = "scenario_1") -> ScenarioDataBundle:
        """Main dispatcher to generate data for a specific scenario."""
        normalized_id = scenario_id.lower().replace("-", "_")

        if "scenario_1" in normalized_id or "multifactor" in normalized_id:
            return self._generate_scenario_1_multifactor()
        elif "scenario_2" in normalized_id or "ambiguous" in normalized_id:
            return self._generate_scenario_2_ambiguous()
        elif "scenario_3" in normalized_id or "coldstart" in normalized_id:
            return self._generate_scenario_3_coldstart()
        elif "scenario_4" in normalized_id or "rbac" in normalized_id:
            return self._generate_scenario_4_rbac()
        else:
            return self._generate_scenario_1_multifactor()

    def _generate_scenario_1_multifactor(self) -> ScenarioDataBundle:
        """Scenario 1: Compound multi-factor drop (70% Port Strike Logistics + 30% WMS Stockout)."""
        rng = np.random.default_rng(self.seed + 101)
        start_date = date(2026, 8, 1)
        total_days = 29  # 28 days baseline + Day 29 anomaly
        eval_date = start_date + timedelta(days=28)  # 2026-08-29

        erp_records: List[Dict[str, Any]] = []
        web_records: List[Dict[str, Any]] = []
        jira_records: List[Dict[str, Any]] = []

        # Baseline parameters
        base_sessions = 100000.0
        base_cvr = 0.030
        base_aov = 50.00
        base_cogs_unit = 24.50

        for day_idx in range(total_days):
            current_date = start_date + timedelta(days=day_idx)
            dow = current_date.weekday()
            dow_mult = self.DOW_SEASONALITY[dow]

            if day_idx < 28:
                # Normal baseline day with minor Gaussian noise
                noise_s = rng.normal(1.0, 0.02)
                noise_cvr = rng.normal(1.0, 0.015)
                noise_aov = rng.normal(1.0, 0.01)

                day_sessions = int(base_sessions * dow_mult * noise_s)
                day_cvr = base_cvr * noise_cvr
                day_orders = int(day_sessions * day_cvr)
                day_aov = base_aov * noise_aov
            else:
                # Anomaly Day 29: Sessions drop to ~80k, CVR drops to ~2.0%, AOV rises to $52.00
                day_sessions = 80000
                day_cvr = 0.020
                day_orders = 1600  # 80000 * 0.02
                day_aov = 52.00

            # Generate Hourly Web Stream summing exactly to day_sessions
            hourly_counts = (np.array(self.HOURLY_WEIGHTS) * day_sessions).astype(int)
            diff = day_sessions - int(hourly_counts.sum())
            hourly_counts[-1] += diff

            for hour in range(24):
                h_sessions = max(1, int(hourly_counts[hour]))
                h_purchases = int(round(h_sessions * day_cvr))
                h_cart_adds = int(h_sessions * 0.12)
                h_checkout_starts = int(h_sessions * 0.06)

                ts = datetime.datetime.combine(current_date, datetime.time(hour, rng.integers(0, 59)))
                web_records.append({
                    "session_id": f"WEB-{current_date.strftime('%Y%m%d')}-{hour:02d}",
                    "session_timestamp": ts,
                    "session_date": current_date,
                    "session_hour": hour,
                    "visitor_id": f"VIS-{current_date.strftime('%m%d')}-{hour:02d}",
                    "traffic_source": "Organic" if hour % 3 == 0 else ("Paid Search" if hour % 3 == 1 else "Direct"),
                    "device_category": "Mobile" if hour % 2 == 0 else "Desktop",
                    "sessions": h_sessions,
                    "page_views": h_sessions * 3,
                    "cart_add_events": h_cart_adds,
                    "checkout_start_events": h_checkout_starts,
                    "purchase_events": h_purchases,
                    "is_converted": h_purchases > 0,
                    "bounce_flag": False,
                })

            # Generate Daily ERP Orders matching day_orders exactly
            categories = ["Electronics", "Home & Kitchen", "Apparel", "Beauty"]
            channels = ["Direct", "Marketplace", "B2B"]
            order_ids = [f"ORD-{current_date.strftime('%Y%m%d')}-{i:05d}" for i in range(day_orders)]
            cust_ids = [f"CUST-US-98{rng.integers(100, 999)}" for _ in range(day_orders)]
            cat_sample = rng.choice(categories, size=day_orders)
            chan_sample = rng.choice(channels, size=day_orders)
            sku_sample = [f"SKU-{c[:3].upper()}-{rng.integers(100, 199)}" for c in cat_sample]
            
            # Unit price distribution around day_aov
            raw_prices = rng.normal(day_aov, 4.0, size=day_orders).clip(15.0, 200.0)
            scaled_prices = np.round(raw_prices * (day_aov / np.mean(raw_prices)), 2)
            cogs_vals = np.round(scaled_prices * (base_cogs_unit / base_aov), 2)
            margin_vals = np.round(scaled_prices - cogs_vals, 2)
            margin_pct_vals = np.round((margin_vals / scaled_prices) * 100.0, 2)
            
            # Fulfillment status: mostly Shipped, small pending/cancelled for realism
            statuses = ["Shipped"] * day_orders
            if day_idx == 28:
                for idx in range(0, day_orders, 5):
                    statuses[idx] = "Pending"  # Backlog pending due to stockout

            for idx in range(day_orders):
                erp_records.append({
                    "order_id": order_ids[idx],
                    "transaction_date": current_date,
                    "timestamp": datetime.datetime.combine(current_date, datetime.time(rng.integers(0, 23), rng.integers(0, 59))),
                    "customer_id": cust_ids[idx],
                    "sku_id": sku_sample[idx],
                    "product_category": cat_sample[idx],
                    "quantity": 1,
                    "unit_price": float(scaled_prices[idx]),
                    "discount_amount": 0.0,
                    "gross_revenue": float(scaled_prices[idx]),
                    "unit_cogs": float(cogs_vals[idx]),
                    "gross_margin": float(margin_vals[idx]),
                    "gross_margin_pct": float(margin_pct_vals[idx]),
                    "fulfillment_status": statuses[idx],
                    "shipping_location": "PORT-LAX-WH" if idx % 2 == 0 else "WH-OAKLAND",
                    "channel": chan_sample[idx],
                })

        # Generate Weekly Jira & Support Tickets
        # Normal baseline tickets
        for w in range(4):
            w_date = start_date + timedelta(days=w * 7)
            jira_records.append({
                "ticket_id": f"OPS-100{w}",
                "created_timestamp": datetime.datetime.combine(w_date, datetime.time(9, 30)),
                "week_start_date": w_date,
                "category": "Routine Maintenance",
                "severity": "P3",
                "status": "Closed",
                "summary": f"Routine weekly warehouse batch reconciliations for week {w+1}",
                "description_text": "All SLA targets met. Normal transit times observed across carriers.",
                "resolution_time_hrs": 4.5,
                "affected_customer_tier": "Standard",
                "carrier_or_system_id": "CARRIER-FEDEX-STANDARD",
            })

        # Incident Tickets for Anomaly Period (Port strike + WMS inventory stockouts)
        jira_records.extend([
            {
                "ticket_id": "OPS-4821",
                "created_timestamp": datetime.datetime.combine(eval_date - timedelta(days=1), datetime.time(8, 15)),
                "week_start_date": eval_date - timedelta(days=eval_date.weekday()),
                "category": "Shipping Delay - West Coast Port Congestion",
                "severity": "P1",
                "status": "Open",
                "summary": "Port of Los Angeles container bottleneck halting inbound inventory",
                "description_text": "ILWU dockworker labor negotiations causing 8-day vessel queuing at Berth 400. Inbound freight diverted or held at anchorage. Carrier advisories issued, resulting in website delivery date estimates pushing out to 14+ days.",
                "resolution_time_hrs": None,
                "affected_customer_tier": "VIP",
                "carrier_or_system_id": "PORT-LAX-DOCK-3",
            },
            {
                "ticket_id": "OPS-4822",
                "created_timestamp": datetime.datetime.combine(eval_date, datetime.time(10, 00)),
                "week_start_date": eval_date - timedelta(days=eval_date.weekday()),
                "category": "Inventory Backlog - SKU Stockout",
                "severity": "P1",
                "status": "In Progress",
                "summary": "Regional WMS inventory stockout on top 10 revenue-generating electronics SKUs",
                "description_text": "Primary West Coast distribution center reports zero safety stock on flagship bundles. Customers adding items to cart face 'Out of Stock' wall at checkout, dropping conversion by 33%.",
                "resolution_time_hrs": None,
                "affected_customer_tier": "Enterprise",
                "carrier_or_system_id": "WMS-WEST-LOC-12",
            },
            {
                "ticket_id": "OPS-4825",
                "created_timestamp": datetime.datetime.combine(eval_date, datetime.time(14, 20)),
                "week_start_date": eval_date - timedelta(days=eval_date.weekday()),
                "category": "Customer Support Escalation - Delivery Delays",
                "severity": "P2",
                "status": "Open",
                "summary": "Surge in customer inquiries regarding delayed transit times",
                "description_text": "Over 45 inbound calls per hour expressing frustration over extended shipping SLA promises.",
                "resolution_time_hrs": None,
                "affected_customer_tier": "Standard",
                "carrier_or_system_id": "PORT-LAX-DOCK-3",
            },
        ])

        erp_df = pd.DataFrame(erp_records)
        web_df = pd.DataFrame(web_records)
        jira_df = pd.DataFrame(jira_records)

        ground_truth = {
            "baseline_revenue": 150000.0,
            "anomaly_revenue": 83200.0,
            "delta_revenue": -66800.0,
            "macro_driver": "West Coast Port Strike (ILWU)",
            "macro_impact_share": 0.70,
            "internal_driver": "WMS Regional Inventory Stockout",
            "internal_impact_share": 0.30,
            "sessions_drop_pct": -20.0,
            "cvr_drop_pct": -33.33,
            "aov_gain_pct": 4.0,
        }

        return ScenarioDataBundle(
            scenario_id="scenario_1",
            scenario_name="Scenario 1: Multi-Factor KPI Movement",
            description="Compound attribution: 70% Macro Port Congestion + 30% Internal Warehouse Stockout",
            erp_df=erp_df,
            web_df=web_df,
            jira_df=jira_df,
            baseline_days=28,
            evaluation_date=eval_date,
            data_quality=DataQuality.NORMAL,
            ground_truth=ground_truth,
        )

    def _generate_scenario_2_ambiguous(self) -> ScenarioDataBundle:
        """Scenario 2: Low-confidence / Ambiguous signals requiring explicit engine abstention."""
        rng = np.random.default_rng(self.seed + 202)
        start_date = date(2026, 8, 1)
        total_days = 29
        eval_date = start_date + timedelta(days=28)

        # Baseline similar to scenario 1
        bundle_1 = self._generate_scenario_1_multifactor()
        erp_df = bundle_1.erp_df.copy()
        web_df = bundle_1.web_df.copy()

        # Inject ambiguous conflicting Jira and Web diagnostic logs on Day 29
        jira_records = [
            {
                "ticket_id": "INC-SAFARI-01",
                "created_timestamp": datetime.datetime.combine(eval_date, datetime.time(11, 15)),
                "week_start_date": eval_date - timedelta(days=eval_date.weekday()),
                "category": "Frontend Checkout Error",
                "severity": "P1",
                "status": "Investigating",
                "summary": "Safari iOS 17 WebKit JavaScript syntax error during payment form submit",
                "description_text": "Mobile Safari users encountering unhandled Promise rejection in checkout bundle v4.2.1. Cart drops observed on iOS.",
                "resolution_time_hrs": None,
                "affected_customer_tier": "Standard",
                "carrier_or_system_id": "JS-SAFARI-BUNDLE-42",
            },
            {
                "ticket_id": "INC-GATEWAY-02",
                "created_timestamp": datetime.datetime.combine(eval_date, datetime.time(11, 25)),
                "week_start_date": eval_date - timedelta(days=eval_date.weekday()),
                "category": "Payment Gateway Timeout",
                "severity": "P1",
                "status": "Investigating",
                "summary": "Stripe third-party payment gateway HTTP 504 Gateway Timeout",
                "description_text": "Upstream payment provider experiencing sporadic API latency spikes. 504 Gateway Timeout on credit card authorizations.",
                "resolution_time_hrs": None,
                "affected_customer_tier": "VIP",
                "carrier_or_system_id": "PAYMENT-GW-STRIPE-504",
            },
        ]
        jira_df = pd.DataFrame(jira_records)

        ground_truth = {
            "is_ambiguous": True,
            "confidence_score": 0.58,
            "abstention_expected": True,
            "hypothesis_1": "Payment Gateway Tokenization Latency / 504 Timeout (58% likelihood)",
            "hypothesis_2": "Safari iOS 17 Frontend Checkout JS Exception (42% likelihood)",
            "canary_tests": [
                "Deploy 5% synthetic checkout payment probe to Stripe endpoint (Cost: $50, Time: 15m)",
                "Roll back frontend JS bundle to v4.2.0 on 10% canary traffic slice (Cost: $0, Time: 10m)",
            ],
        }

        return ScenarioDataBundle(
            scenario_id="scenario_2",
            scenario_name="Scenario 2: Low-Confidence & Ambiguous Root Causes",
            description="Conflicting operational evidence (Stripe 504 vs Safari JS Crash) triggering explicit engine abstention",
            erp_df=erp_df,
            web_df=web_df,
            jira_df=jira_df,
            baseline_days=28,
            evaluation_date=eval_date,
            data_quality=DataQuality.INSUFFICIENT_SAMPLE,
            ground_truth=ground_truth,
        )

    def _generate_scenario_3_coldstart(self) -> ScenarioDataBundle:
        """Scenario 3: Sparse-history / cold-start launch baseline (N = 6 days < 14 days)."""
        rng = np.random.default_rng(self.seed + 303)
        start_date = date(2026, 8, 23)
        total_days = 7  # 6 days baseline + Day 7 evaluated
        eval_date = start_date + timedelta(days=6)  # 2026-08-29

        erp_records: List[Dict[str, Any]] = []
        web_records: List[Dict[str, Any]] = []
        jira_records: List[Dict[str, Any]] = []

        base_sessions = 5000.0  # New SKU niche launch
        base_cvr = 0.025
        base_aov = 120.00
        base_cogs = 55.00

        for day_idx in range(total_days):
            current_date = start_date + timedelta(days=day_idx)
            dow = current_date.weekday()
            dow_mult = self.DOW_SEASONALITY[dow]

            # High variance for early launch
            variance = rng.normal(1.0, 0.15)
            day_sessions = max(100, int(base_sessions * dow_mult * variance))
            day_cvr = max(0.005, min(0.1, base_cvr * variance))
            day_orders = max(1, int(day_sessions * day_cvr))
            day_aov = base_aov * rng.normal(1.0, 0.05)

            hourly_counts = (np.array(self.HOURLY_WEIGHTS) * day_sessions).astype(int)
            diff = day_sessions - int(hourly_counts.sum())
            hourly_counts[-1] += diff

            for hour in range(24):
                h_sessions = max(1, int(hourly_counts[hour]))
                h_purchases = int(round(h_sessions * day_cvr))

                ts = datetime.datetime.combine(current_date, datetime.time(hour, 15))
                web_records.append({
                    "session_id": f"WEB-LAUNCH-{current_date.strftime('%Y%m%d')}-{hour:02d}",
                    "session_timestamp": ts,
                    "session_date": current_date,
                    "session_hour": hour,
                    "visitor_id": f"VIS-LAUNCH-{hour:02d}",
                    "traffic_source": "Paid Search",
                    "device_category": "Mobile",
                    "sessions": h_sessions,
                    "page_views": h_sessions * 2,
                    "cart_add_events": int(h_sessions * 0.08),
                    "checkout_start_events": int(h_sessions * 0.04),
                    "purchase_events": h_purchases,
                    "is_converted": h_purchases > 0,
                    "bounce_flag": False,
                })

            for line_idx in range(min(day_orders, 15)):
                qty = 1
                price = day_aov
                cogs = base_cogs
                margin = price - cogs
                erp_records.append({
                    "order_id": f"ORD-LAUNCH-{current_date.strftime('%Y%m%d')}-{line_idx:03d}",
                    "transaction_date": current_date,
                    "timestamp": datetime.datetime.combine(current_date, datetime.time(14, line_idx % 60)),
                    "customer_id": f"CUST-NEW-{line_idx:03d}",
                    "sku_id": "SKU-SMART-HUB-GEN3",
                    "product_category": "Smart Home IoT",
                    "quantity": qty,
                    "unit_price": round(price, 2),
                    "discount_amount": 0.0,
                    "gross_revenue": round(price * qty, 2),
                    "unit_cogs": round(cogs, 2),
                    "gross_margin": round(margin, 2),
                    "gross_margin_pct": round((margin / price) * 100.0, 2),
                    "fulfillment_status": "Shipped",
                    "shipping_location": "WH-CENTRAL-01",
                    "channel": "Direct",
                })

        jira_records.append({
            "ticket_id": "LAUNCH-001",
            "created_timestamp": datetime.datetime.combine(start_date, datetime.time(9, 0)),
            "week_start_date": start_date,
            "category": "New Product Launch",
            "severity": "P3",
            "status": "In Progress",
            "summary": "Smart Home Hub Gen-3 Initial Market Introduction (Day 1-7)",
            "description_text": "Monitoring early funnel engagement. Sparse transaction history requires Bayesian prior integration.",
            "resolution_time_hrs": None,
            "affected_customer_tier": "Standard",
            "carrier_or_system_id": "LAUNCH-CAMPAIGN-01",
        })

        erp_df = pd.DataFrame(erp_records)
        web_df = pd.DataFrame(web_records)
        jira_df = pd.DataFrame(jira_records)

        ground_truth = {
            "sku_name": "Smart Home Hub Gen-3",
            "history_days": 6,
            "is_cold_start": True,
            "uncertainty_multiplier": 1.45,
            "confidence_penalty": 0.57,
            "status_flag": "STATUS_SPARSE_DATA_UNRELIABLE_SPC",
        }

        return ScenarioDataBundle(
            scenario_id="scenario_3",
            scenario_name="Scenario 3: Sparse-History / Cold-Start Launch",
            description="New SKU Launch with 6 days history (N < 14) requiring Bayesian prior and widened uncertainty envelopes",
            erp_df=erp_df,
            web_df=web_df,
            jira_df=jira_df,
            baseline_days=6,
            evaluation_date=eval_date,
            data_quality=DataQuality.COLD_START,
            ground_truth=ground_truth,
        )

    def _generate_scenario_4_rbac(self) -> ScenarioDataBundle:
        """Scenario 4: Role-Based Entitlement & Masking Showcase (built upon Scenario 1 data)."""
        bundle_1 = self._generate_scenario_1_multifactor()
        bundle_1.scenario_id = "scenario_4"
        bundle_1.scenario_name = "Scenario 4: Role-Based Entitlements & Masking"
        bundle_1.description = "Enforcing dynamic column/row masking on sensitive financial metrics for non-executives"
        bundle_1.ground_truth["rbac_fields_masked_for_analyst"] = ["unit_cogs", "gross_margin", "gross_margin_pct"]
        bundle_1.ground_truth["rbac_unmasked_for_executive"] = ["unit_cogs", "gross_margin", "gross_margin_pct"]
        return bundle_1


# Alias for backward and cross-module compatibility
SyntheticDataGenerator = MultiSourceDataGenerator

__all__ = [
    "ScenarioDataBundle",
    "MultiSourceDataGenerator",
    "SyntheticDataGenerator",
]

