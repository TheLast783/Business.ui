"""Canonical KPI calculations, snapshot aggregation, and multi-source reconciliation."""
import math
from datetime import date
from typing import Optional, Union
import pandas as pd

from prototype.engine.contracts.schemas import MetricSnapshot


class KPICalculator:
    """Standard business KPI calculation helpers and canonical snapshot creators."""

    @staticmethod
    def gross_revenue(quantity: int, unit_price: float, discount_amount: float = 0.0) -> float:
        """Computes Gross Revenue = max(0, Quantity * Unit Price - Discount)."""
        rev = (quantity * unit_price) - discount_amount
        return max(0.0, float(rev))

    @staticmethod
    def conversion_rate(order_volume: int, sessions: int) -> float:
        """Computes Conversion Rate = Order Volume / Sessions, clamped to [0.0, 1.0]."""
        if sessions <= 0:
            return 0.0
        cr = order_volume / sessions
        return min(1.0, max(0.0, float(cr)))

    @staticmethod
    def average_order_value(gross_revenue: float, order_volume: int) -> float:
        """Computes Average Order Value (AOV) = Gross Revenue / Order Volume."""
        if order_volume <= 0:
            return 0.0
        return max(0.0, float(gross_revenue / order_volume))

    @staticmethod
    def gross_margin(gross_revenue: float, quantity: int, unit_cogs: float) -> float:
        """Computes Gross Margin ($) = Gross Revenue - (Quantity * Unit COGS)."""
        return float(gross_revenue - (quantity * unit_cogs))

    @staticmethod
    def gross_margin_pct(gross_margin: float, gross_revenue: float) -> float:
        """Computes Gross Margin (%) = (Gross Margin / Gross Revenue) * 100."""
        if gross_revenue <= 0.0:
            return 0.0
        return float((gross_margin / gross_revenue) * 100.0)

    @staticmethod
    def pct_change(baseline: float, actual: float) -> float:
        """Computes percentage change: ((Actual - Baseline) / Baseline) * 100."""
        if baseline == 0.0:
            return 100.0 if actual > 0.0 else 0.0
        return float(((actual - baseline) / baseline) * 100.0)

    @staticmethod
    def create_snapshot(
        period_label: str,
        start_date: date,
        end_date: date,
        gross_revenue: float,
        order_volume: int,
        sessions: int,
        total_cogs: Optional[float] = None,
        total_gross_margin: Optional[float] = None,
    ) -> MetricSnapshot:
        """Creates a fully validated canonical MetricSnapshot."""
        cvr = KPICalculator.conversion_rate(order_volume, sessions)
        aov = KPICalculator.average_order_value(gross_revenue, order_volume)
        margin_pct = (
            KPICalculator.gross_margin_pct(total_gross_margin, gross_revenue)
            if total_gross_margin is not None and gross_revenue > 0
            else None
        )
        return MetricSnapshot(
            period_label=period_label,
            start_date=start_date,
            end_date=end_date,
            gross_revenue=float(gross_revenue),
            order_volume=int(order_volume),
            sessions=int(sessions),
            conversion_rate=cvr,
            aov=aov,
            total_cogs=float(total_cogs) if total_cogs is not None else None,
            total_gross_margin=float(total_gross_margin) if total_gross_margin is not None else None,
            gross_margin_pct=margin_pct,
        )

    @staticmethod
    def calculate_snapshot(
        sessions: float,
        orders: float,
        gross_revenue: float,
        cost: float = 0.0,
        start_date: date = date(2026, 8, 1),
        end_date: date = date(2026, 8, 28)
    ) -> MetricSnapshot:
        return KPICalculator.create_snapshot(
            period_label="Snapshot",
            start_date=start_date,
            end_date=end_date,
            gross_revenue=gross_revenue,
            order_volume=int(orders),
            sessions=int(sessions),
            total_cogs=cost,
            total_gross_margin=gross_revenue - cost
        )

    @staticmethod
    def reconcile_from_dataframes(
        df_erp: pd.DataFrame,
        df_web: pd.DataFrame,
        period_label: str = "Reconciled",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> MetricSnapshot:
        """Rolls up multi-source DataFrames into a canonical snapshot."""
        erp_valid = df_erp[df_erp["fulfillment_status"] != "Cancelled"]
        gross_rev = float(erp_valid["gross_revenue"].sum()) if not erp_valid.empty else 0.0
        orders = int(erp_valid["order_id"].nunique()) if not erp_valid.empty else 0
        total_cogs = float((erp_valid["unit_cogs"] * erp_valid["quantity"]).sum()) if "unit_cogs" in erp_valid and "quantity" in erp_valid else 0.0
        
        sessions = int(df_web["sessions"].sum()) if not df_web.empty and "sessions" in df_web else max(orders * 30, 1)

        dates_erp = pd.to_datetime(df_erp["transaction_date"]).dt.date if not df_erp.empty else []
        s_date = start_date or (min(dates_erp) if len(dates_erp) > 0 else date(2026, 8, 1))
        e_date = end_date or (max(dates_erp) if len(dates_erp) > 0 else date(2026, 8, 28))

        return KPICalculator.create_snapshot(
            period_label=period_label,
            start_date=s_date,
            end_date=e_date,
            gross_revenue=gross_rev,
            order_volume=orders,
            sessions=sessions,
            total_cogs=total_cogs,
            total_gross_margin=gross_rev - total_cogs
        )
