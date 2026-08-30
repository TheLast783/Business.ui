"""Multi-source data loader, grain harmonization, validation, and snapshot generator."""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from prototype.engine.contracts.schemas import (
    DataQuality,
    ERPSalesRecord,
    MetricSnapshot,
    SupportJiraRecord,
    UserRole,
    WebSessionRecord,
)
from prototype.engine.contracts.semantic_contract import (
    RBACMaskingEngine,
    SemanticContract,
)
from prototype.engine.data.generator import MultiSourceDataGenerator, ScenarioDataBundle


class MultiSourceDataLoader:
    """Ingests heterogeneous business datasets, harmonizes grains, and builds canonical snapshots."""

    def __init__(self, bundle: Optional[ScenarioDataBundle] = None):
        self.bundle: Optional[ScenarioDataBundle] = bundle
        self._daily_harmonized_df: Optional[pd.DataFrame] = None

    def load_scenario(self, scenario_id: str = "scenario_1", seed: int = 42) -> ScenarioDataBundle:
        """Generates and loads scenario data."""
        generator = MultiSourceDataGenerator(seed=seed)
        self.bundle = generator.generate(scenario_id=scenario_id)
        self._daily_harmonized_df = self._harmonize_grains()
        return self.bundle

    def set_bundle(self, bundle: ScenarioDataBundle) -> None:
        """Sets an existing bundle."""
        self.bundle = bundle
        self._daily_harmonized_df = self._harmonize_grains()

    def get_daily_harmonized_df(self) -> pd.DataFrame:
        """Returns the daily grain harmonized metric dataframe."""
        if self._daily_harmonized_df is None:
            if self.bundle is None:
                self.load_scenario("scenario_1")
            else:
                self._daily_harmonized_df = self._harmonize_grains()
        return self._daily_harmonized_df

    def _harmonize_grains(self) -> pd.DataFrame:
        """Reconciles Daily ERP sales, Hourly Web sessions, and Weekly Jira into a unified daily grain."""
        if self.bundle is None:
            raise ValueError("No scenario bundle loaded.")

        erp_df = self.bundle.erp_df.copy()
        web_df = self.bundle.web_df.copy()

        # 1. Aggregate Hourly Web sessions to Daily grain
        web_df["session_date"] = pd.to_datetime(web_df["session_date"]).dt.date
        web_daily = (
            web_df.groupby("session_date")
            .agg(
                sessions=("sessions", "sum"),
                total_pageviews=("page_views", "sum"),
                cart_adds=("cart_add_events", "sum"),
                checkout_starts=("checkout_start_events", "sum"),
                web_purchases=("purchase_events", "sum"),
            )
            .reset_index()
            .rename(columns={"session_date": "date"})
        )

        # 2. Aggregate Daily ERP transactions
        erp_df["transaction_date"] = pd.to_datetime(erp_df["transaction_date"]).dt.date
        erp_valid = erp_df[erp_df["fulfillment_status"] != "Cancelled"]

        erp_daily = (
            erp_valid.groupby("transaction_date")
            .agg(
                gross_revenue=("gross_revenue", "sum"),
                order_volume=("order_id", "nunique"),
                total_cogs=("unit_cogs", lambda x: float((x * erp_valid.loc[x.index, "quantity"]).sum())),
                total_quantity=("quantity", "sum"),
            )
            .reset_index()
            .rename(columns={"transaction_date": "date"})
        )

        # 3. Join ERP and Web daily aggregates on calendar date
        daily = pd.merge(erp_daily, web_daily, on="date", how="outer").fillna(0)
        daily = daily.sort_values("date").reset_index(drop=True)

        # Ensure realistic orders and sessions alignment for consistency
        daily["gross_revenue"] = daily["gross_revenue"].astype(float)
        daily["order_volume"] = daily["order_volume"].astype(int)
        daily["sessions"] = daily["sessions"].astype(int)

        # Reconcile sessions if 0
        mask_zero_sessions = daily["sessions"] <= daily["order_volume"]
        if mask_zero_sessions.any():
            daily.loc[mask_zero_sessions, "sessions"] = (
                daily.loc[mask_zero_sessions, "order_volume"] * 33
            ).astype(int)

        daily["conversion_rate"] = (daily["order_volume"] / daily["sessions"]).clip(0.0, 1.0)
        daily["aov"] = np.where(
            daily["order_volume"] > 0,
            daily["gross_revenue"] / daily["order_volume"],
            0.0
        )
        daily["gross_margin"] = daily["gross_revenue"] - daily["total_cogs"]
        daily["gross_margin_pct"] = np.where(
            daily["gross_revenue"] > 0,
            (daily["gross_margin"] / daily["gross_revenue"]) * 100.0,
            0.0
        )

        return daily

    def compute_period_snapshot(
        self,
        start_date: date,
        end_date: date,
        period_label: str = "Window",
    ) -> MetricSnapshot:
        """Aggregates metrics for a date range and returns a validated MetricSnapshot."""
        daily = self.get_daily_harmonized_df()
        mask = (daily["date"] >= start_date) & (daily["date"] <= end_date)
        window_df = daily[mask]

        if len(window_df) == 0:
            raise ValueError(f"No data available in window {start_date} to {end_date}")

        total_rev = float(window_df["gross_revenue"].sum())
        total_vol = int(window_df["order_volume"].sum())
        total_sess = int(window_df["sessions"].sum())
        total_cogs = float(window_df["total_cogs"].sum())

        return SemanticContract.compute_kpis_from_aggregates(
            gross_revenue=total_rev,
            order_volume=total_vol,
            sessions=total_sess,
            period_label=period_label,
            start_date=start_date,
            end_date=end_date,
            total_cogs=total_cogs,
        )

    def get_baseline_and_observed_snapshots(self) -> Tuple[MetricSnapshot, MetricSnapshot]:
        """Convenience method to retrieve the baseline snapshot and the evaluation anomaly snapshot."""
        if self.bundle is None:
            self.load_scenario("scenario_1")

        daily = self.get_daily_harmonized_df()
        eval_date = self.bundle.evaluation_date
        baseline_df = daily[daily["date"] < eval_date]
        observed_df = daily[daily["date"] == eval_date]

        if len(baseline_df) == 0:
            baseline_df = daily.iloc[:1]
        if len(observed_df) == 0:
            observed_df = daily.iloc[-1:]

        # Normalize baseline to a daily average representation for 1-to-1 comparison with observed day
        n_base_days = len(baseline_df)
        base_rev = float(baseline_df["gross_revenue"].sum() / n_base_days)
        base_vol = int(round(baseline_df["order_volume"].sum() / n_base_days))
        base_sess = int(round(baseline_df["sessions"].sum() / n_base_days))
        base_cogs = float(baseline_df["total_cogs"].sum() / n_base_days)

        baseline_snapshot = SemanticContract.compute_kpis_from_aggregates(
            gross_revenue=base_rev,
            order_volume=base_vol,
            sessions=base_sess,
            period_label="Baseline (28-Day Avg)",
            start_date=baseline_df["date"].min(),
            end_date=baseline_df["date"].max(),
            total_cogs=base_cogs,
        )

        obs_row = observed_df.iloc[0]
        observed_snapshot = SemanticContract.compute_kpis_from_aggregates(
            gross_revenue=float(obs_row["gross_revenue"]),
            order_volume=int(obs_row["order_volume"]),
            sessions=int(obs_row["sessions"]),
            period_label=f"Observed ({eval_date.strftime('%Y-%m-%d')})",
            start_date=eval_date,
            end_date=eval_date,
            total_cogs=float(obs_row["total_cogs"]),
        )

        return baseline_snapshot, observed_snapshot

    def get_masked_erp_data(self, role: UserRole) -> pd.DataFrame:
        """Returns the raw ERP dataset masked according to the user role."""
        if self.bundle is None:
            self.load_scenario("scenario_1")
        return RBACMaskingEngine.mask_erp_dataframe(self.bundle.erp_df, role)

    def get_masked_jira_data(self, role: UserRole) -> pd.DataFrame:
        """Returns the raw Jira dataset formatted according to the user role."""
        if self.bundle is None:
            self.load_scenario("scenario_1")
        return RBACMaskingEngine.mask_jira_dataframe(self.bundle.jira_df, role)


# Alias for backward and cross-module compatibility
DataLoader = MultiSourceDataLoader

__all__ = [
    "MultiSourceDataLoader",
    "DataLoader",
    "ScenarioDataBundle",
]
