"""Governed Semantic Contract, Lineage Graph, Invariant Verification, and RBAC Masking."""

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from prototype.engine.config import (
    CR_MAX_VALUE,
    CR_MIN_VALUE,
    RECONCILIATION_TOLERANCE,
    REDACTED_CONFIDENTIAL_STR,
    REDACTED_CUSTOMER_PREFIX,
)
from prototype.engine.contracts.schemas import (
    ERPSalesRecord,
    MetricSnapshot,
    SupportJiraRecord,
    UserRole,
    WebSessionRecord,
)


@dataclass
class LineageNode:
    """Represents a node in the semantic data lineage graph."""
    node_id: str
    name: str
    node_type: str  # "SOURCE_TABLE", "TRANSFORMATION", "CANONICAL_KPI"
    granularity: str  # "Daily", "Hourly", "Weekly", "Aggregated"
    description: str
    upstream_dependencies: List[str] = field(default_factory=list)
    formula: Optional[str] = None
    owner_team: str = "Data Platform & Governance"
    sla_freshness_hours: int = 24


class SemanticLineageGraph:
    """Declarative lineage graph tracking the 4 connected KPIs and 3 heterogeneous sources."""

    def __init__(self):
        self._nodes: Dict[str, LineageNode] = {}
        self._build_default_graph()

    def _build_default_graph(self) -> None:
        nodes = [
            LineageNode(
                node_id="src_erp_sales",
                name="Daily ERP Sales Transactions",
                node_type="SOURCE_TABLE",
                granularity="Daily",
                description="Structured SQL table containing transaction orders, quantities, prices, COGS, and fulfillment statuses.",
                upstream_dependencies=[],
                owner_team="Enterprise ERP Systems",
                sla_freshness_hours=24,
            ),
            LineageNode(
                node_id="src_web_sessions",
                name="Hourly Web Analytics Stream",
                node_type="SOURCE_TABLE",
                granularity="Hourly",
                description="High-frequency event stream capturing visitor sessions, bounce rates, and checkout funnel stages.",
                upstream_dependencies=[],
                owner_team="Digital Analytics Engineering",
                sla_freshness_hours=1,
            ),
            LineageNode(
                node_id="src_support_jira",
                name="Weekly Support & Jira Ticket Logs",
                node_type="SOURCE_TABLE",
                granularity="Weekly",
                description="Semi-structured operational and customer support logs tagged with incident taxonomy.",
                upstream_dependencies=[],
                owner_team="Customer Operations & DevOps",
                sla_freshness_hours=168,
            ),
            LineageNode(
                node_id="kpi_sessions",
                name="Sessions (S)",
                node_type="CANONICAL_KPI",
                granularity="Aggregated",
                description="Total unique web visitor sessions within the evaluation window.",
                upstream_dependencies=["src_web_sessions"],
                formula="COUNT(DISTINCT session_id)",
                owner_team="Growth Analytics",
                sla_freshness_hours=1,
            ),
            LineageNode(
                node_id="kpi_order_volume",
                name="Order Volume (V)",
                node_type="CANONICAL_KPI",
                granularity="Aggregated",
                description="Count of distinct completed, non-cancelled order transactions.",
                upstream_dependencies=["src_erp_sales"],
                formula="COUNT(DISTINCT order_id) WHERE fulfillment_status != 'Cancelled'",
                owner_team="Enterprise ERP Systems",
                sla_freshness_hours=24,
            ),
            LineageNode(
                node_id="kpi_conversion_rate",
                name="Conversion Rate (CR)",
                node_type="CANONICAL_KPI",
                granularity="Aggregated",
                description="Ratio of completed order transactions to total web sessions.",
                upstream_dependencies=["kpi_order_volume", "kpi_sessions"],
                formula="Order Volume (V) / Sessions (S)",
                owner_team="BI Semantic Layer",
                sla_freshness_hours=24,
            ),
            LineageNode(
                node_id="kpi_gross_revenue",
                name="Gross Revenue (R)",
                node_type="CANONICAL_KPI",
                granularity="Aggregated",
                description="Total financial revenue recognized across all valid orders.",
                upstream_dependencies=["src_erp_sales"],
                formula="SUM((quantity * unit_price) - discount_amount)",
                owner_team="Finance Analytics",
                sla_freshness_hours=24,
            ),
            LineageNode(
                node_id="kpi_aov",
                name="Average Order Value (AOV)",
                node_type="CANONICAL_KPI",
                granularity="Aggregated",
                description="Average monetary value per completed order.",
                upstream_dependencies=["kpi_gross_revenue", "kpi_order_volume"],
                formula="Gross Revenue (R) / Order Volume (V)",
                owner_team="BI Semantic Layer",
                sla_freshness_hours=24,
            ),
        ]
        for n in nodes:
            self._nodes[n.node_id] = n

    def get_node(self, node_id: str) -> Optional[LineageNode]:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[LineageNode]:
        return list(self._nodes.values())

    def get_lineage_trace(self, target_kpi_id: str) -> List[str]:
        """Returns ordered upstream lineage path for a target KPI."""
        visited: List[str] = []

        def _dfs(nid: str):
            if nid in self._nodes:
                for up in self._nodes[nid].upstream_dependencies:
                    if up not in visited:
                        _dfs(up)
                if nid not in visited:
                    visited.append(nid)

        _dfs(target_kpi_id)
        return visited


class SemanticContract:
    """Governed Semantic Contract defining canonical formulas, invariants, and integrity tests."""

    @staticmethod
    def compute_kpis_from_aggregates(
        gross_revenue: float,
        order_volume: int,
        sessions: int,
        period_label: str = "Window",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        total_cogs: Optional[float] = None,
    ) -> MetricSnapshot:
        """Computes and constructs a strictly validated MetricSnapshot from aggregates."""
        s_date = start_date or date.today()
        e_date = end_date or date.today()

        if sessions <= 0:
            cr = 0.0
        else:
            cr = min(1.0, max(0.0, float(order_volume) / float(sessions)))

        if order_volume <= 0:
            aov = 0.0
        else:
            aov = float(gross_revenue) / float(order_volume)

        gross_margin = None
        gross_margin_pct = None
        if total_cogs is not None and gross_revenue > 0:
            gross_margin = gross_revenue - total_cogs
            gross_margin_pct = (gross_margin / gross_revenue) * 100.0

        snapshot = MetricSnapshot(
            period_label=period_label,
            start_date=s_date,
            end_date=e_date,
            gross_revenue=float(gross_revenue),
            order_volume=int(order_volume),
            sessions=int(sessions),
            conversion_rate=float(cr),
            aov=float(aov),
            total_cogs=float(total_cogs) if total_cogs is not None else None,
            total_gross_margin=float(gross_margin) if gross_margin is not None else None,
            gross_margin_pct=float(gross_margin_pct) if gross_margin_pct is not None else None,
        )

        # Enforce contract invariants
        is_valid, violations = SemanticContract.validate_snapshot_invariants(snapshot)
        if not is_valid:
            raise ValueError(f"Semantic Contract invariant violations: {'; '.join(violations)}")

        return snapshot

    @staticmethod
    def validate_snapshot_invariants(snapshot: MetricSnapshot) -> Tuple[bool, List[str]]:
        """Verifies mathematical consistency and domain invariants for a MetricSnapshot."""
        violations: List[str] = []

        # 1. Non-negativity
        if snapshot.gross_revenue < 0.0:
            violations.append(f"Gross Revenue must be >= 0 (got {snapshot.gross_revenue})")
        if snapshot.order_volume < 0:
            violations.append(f"Order Volume must be >= 0 (got {snapshot.order_volume})")
        if snapshot.sessions < 0:
            violations.append(f"Sessions must be >= 0 (got {snapshot.sessions})")
        if snapshot.aov < 0.0:
            violations.append(f"AOV must be >= 0 (got {snapshot.aov})")

        # 2. Conversion Rate Bounds [0.0, 1.0]
        if not (CR_MIN_VALUE <= snapshot.conversion_rate <= CR_MAX_VALUE):
            violations.append(
                f"Conversion Rate {snapshot.conversion_rate} outside valid range [{CR_MIN_VALUE}, {CR_MAX_VALUE}]"
            )

        # 3. Order Volume vs Sessions Invariant (V <= S)
        if snapshot.order_volume > snapshot.sessions and snapshot.sessions > 0:
            violations.append(
                f"Order Volume ({snapshot.order_volume}) exceeds total Sessions ({snapshot.sessions})"
            )

        # 4. Closed-form Mathematical Reconciliations
        if snapshot.order_volume > 0:
            recomputed_rev = snapshot.order_volume * snapshot.aov
            if abs(recomputed_rev - snapshot.gross_revenue) > 0.01:
                violations.append(
                    f"Revenue identity mismatch: R={snapshot.gross_revenue} vs V*AOV={recomputed_rev:.2f}"
                )

        if snapshot.sessions > 0:
            recomputed_vol = round(snapshot.sessions * snapshot.conversion_rate)
            if abs(recomputed_vol - snapshot.order_volume) > 2:
                violations.append(
                    f"Volume identity mismatch: V={snapshot.order_volume} vs S*CR={recomputed_vol}"
                )

        return (len(violations) == 0, violations)

    @staticmethod
    def reconcile_erp_and_web(
        erp_order_count: int,
        web_purchase_events: int,
        tolerance: float = RECONCILIATION_TOLERANCE,
    ) -> Tuple[bool, float, str]:
        """Validates that daily ERP orders and Web purchase events align within tolerance."""
        if erp_order_count == 0 and web_purchase_events == 0:
            return True, 0.0, "Exact match (0 orders)"

        baseline = max(erp_order_count, web_purchase_events)
        discrepancy = abs(erp_order_count - web_purchase_events) / float(baseline)

        is_reconciled = discrepancy <= tolerance
        msg = (
            f"ERP orders ({erp_order_count}) and Web purchases ({web_purchase_events}) "
            f"discrepancy is {discrepancy * 100:.2f}% (Tolerance: {tolerance * 100:.1f}%)"
        )
        return is_reconciled, discrepancy, msg


class RBACMaskingEngine:
    """Dynamic domain/column/value-level masking based on UserRole."""

    SENSITIVE_ERP_COLUMNS: List[str] = ["unit_cogs", "gross_margin", "gross_margin_pct"]

    DOMAIN_ENTITLEMENTS: Dict[UserRole, Dict[str, Any]] = {
        UserRole.EXECUTIVE: {
            "domains": ["finance", "sales", "operations", "customer", "macro"],
            "financial_detail": "FULL",
            "audit_action": "ALLOW",
        },
        UserRole.OPERATIONS_ANALYST: {
            "domains": ["sales", "operations", "customer"],
            "financial_detail": "MASKED",
            "audit_action": "MASK_FINANCIAL",
        },
    }

    @classmethod
    def entitlement(cls, role: UserRole) -> Dict[str, Any]:
        """Return governed domain and column entitlements for the active role."""
        return dict(cls.DOMAIN_ENTITLEMENTS.get(role, {
            "domains": [], "financial_detail": "DENY", "audit_action": "DENY"
        }))

    @classmethod
    def audit_access(cls, role: UserRole, requested_domain: str, requested_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create an auditable allow/mask/deny decision without exposing sensitive values."""
        policy = cls.entitlement(role)
        domain = str(requested_domain).lower()
        allowed_domain = domain in [str(x).lower() for x in policy["domains"]]
        requested_columns = requested_columns or []
        masked = [c for c in requested_columns if c in cls.SENSITIVE_ERP_COLUMNS and policy["financial_detail"] != "FULL"]
        action = "DENY" if not allowed_domain else ("MASK" if masked else "ALLOW")
        return {
            "role": role.value if hasattr(role, "value") else str(role),
            "domain": requested_domain,
            "requested_columns": requested_columns,
            "masked_columns": masked,
            "decision": action,
            "reason": policy["audit_action"],
        }

    @classmethod
    def mask_erp_record(cls, record: Union[ERPSalesRecord, Dict[str, Any]], role: UserRole) -> Dict[str, Any]:
        if hasattr(record, "model_dump"):
            data = record.model_dump()
        elif hasattr(record, "dict"):
            data = record.dict()
        else:
            data = dict(record)

        if role == UserRole.OPERATIONS_ANALYST:
            # Redact confidential financial margins
            for col in cls.SENSITIVE_ERP_COLUMNS:
                if col in data:
                    data[col] = REDACTED_CONFIDENTIAL_STR
            # Anonymize customer ID
            if "customer_id" in data and data["customer_id"]:
                raw_id = str(data["customer_id"])
                data["customer_id"] = f"{REDACTED_CUSTOMER_PREFIX}{raw_id[-3:] if len(raw_id) >= 3 else 'XXX'}"
        return data

    @classmethod
    def mask_erp_dataframe(cls, df: pd.DataFrame, role: UserRole) -> pd.DataFrame:
        """Applies dynamic column masking to an entire pandas DataFrame of ERP records."""
        masked_df = df.copy()
        if role == UserRole.OPERATIONS_ANALYST:
            for col in cls.SENSITIVE_ERP_COLUMNS:
                if col in masked_df.columns:
                    masked_df[col] = REDACTED_CONFIDENTIAL_STR
            if "customer_id" in masked_df.columns:
                masked_df["customer_id"] = masked_df["customer_id"].astype(str).apply(
                    lambda cid: f"{REDACTED_CUSTOMER_PREFIX}{cid[-3:] if len(cid) >= 3 else 'XXX'}"
                )
        return masked_df

    @classmethod
    def mask_jira_dataframe(cls, df: pd.DataFrame, role: UserRole) -> pd.DataFrame:
        """Formats Jira records according to persona needs. Analysts see deep system IDs."""
        masked_df = df.copy()
        if role == UserRole.EXECUTIVE:
            # Executive sees high-level aggregated risk summary rather than raw server logs
            if "carrier_or_system_id" in masked_df.columns:
                masked_df["carrier_or_system_id"] = masked_df["carrier_or_system_id"].apply(
                    lambda x: "Operational System" if pd.notna(x) and x != "" else "N/A"
                )
        # Analysts retain full carrier/system ID visibility for deep triage
        return masked_df


SemanticContractManager = SemanticContract

