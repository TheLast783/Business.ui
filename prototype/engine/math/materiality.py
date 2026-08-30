"""KPI materiality and prioritisation engine.

Deterministic layer: no LLM calls. Combines statistical severity, business impact,
KPI criticality and data confidence into an auditable 0-100 priority score.
"""
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import math
import pandas as pd


@dataclass
class KPIInsight:
    kpi_name: str
    baseline_value: float
    observed_value: float
    delta_value: float
    delta_pct: float
    z_score: float
    statistical_severity: str
    business_impact_usd: float
    kpi_criticality: float
    confidence: float
    materiality_score: float
    priority: str
    method: str = "SPC + business-impact weighting"
    evidence: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence"] = list(self.evidence or [])
        return d


class MaterialityEngine:
    """Ranks KPI movements using transparent deterministic rules."""

    KPI_CRITICALITY = {
        "Gross Revenue": 1.00,
        "Order Volume": 0.85,
        "Conversion Rate": 0.80,
        "AOV": 0.70,
    }

    def __init__(self, business_impact_scale_usd: float = 250_000.0):
        self.business_impact_scale_usd = max(1.0, float(business_impact_scale_usd))

    @staticmethod
    def _pct(baseline: float, observed: float) -> float:
        if abs(baseline) < 1e-12:
            return 0.0
        return (observed - baseline) / abs(baseline) * 100.0

    @staticmethod
    def _severity(z: float) -> str:
        az = abs(float(z))
        if az >= 3.5:
            return "CRITICAL"
        if az >= 2.5:
            return "HIGH"
        if az >= 1.5:
            return "MEDIUM"
        return "LOW"

    def _business_impacts(self, base: Dict[str, float], obs: Dict[str, float]) -> Dict[str, float]:
        """Convert each KPI movement to an estimated USD exposure without double-counting in the score."""
        aov0 = base["AOV"]
        cvr0 = base["Conversion Rate"]
        sessions0 = base["Sessions"]
        orders1 = obs["Order Volume"]
        impacts = {
            "Gross Revenue": abs(obs["Gross Revenue"] - base["Gross Revenue"]),
            "Order Volume": abs(obs["Order Volume"] - base["Order Volume"]) * max(0.0, aov0),
            "Conversion Rate": abs(obs["Conversion Rate"] - cvr0) * max(0.0, sessions0) * max(0.0, aov0),
            "AOV": abs(obs["AOV"] - aov0) * max(0.0, orders1),
        }
        return impacts

    def rank(self, baseline: Dict[str, float], observed: Dict[str, float],
             z_scores: Optional[Dict[str, float]] = None,
             confidence: float = 1.0,
             evidence_by_kpi: Optional[Dict[str, List[str]]] = None) -> List[Dict[str, Any]]:
        z_scores = z_scores or {}
        evidence_by_kpi = evidence_by_kpi or {}
        impacts = self._business_impacts(baseline, observed)
        results: List[KPIInsight] = []

        for name in self.KPI_CRITICALITY:
            b = float(baseline.get(name, 0.0))
            o = float(observed.get(name, 0.0))
            delta = o - b
            pct = self._pct(b, o)
            z = float(z_scores.get(name, 0.0))
            severity = self._severity(z)

            stat_score = min(100.0, abs(z) / 4.0 * 100.0)
            impact_score = min(100.0, math.log1p(impacts[name]) / math.log1p(self.business_impact_scale_usd) * 100.0)
            movement_score = min(100.0, abs(pct) / 20.0 * 100.0)
            criticality = self.KPI_CRITICALITY[name]

            # Transparent weighting: statistical evidence 35%, economic exposure 40%,
            # movement magnitude 15%, KPI criticality 10%, then confidence scales the result.
            raw = (
                0.35 * stat_score
                + 0.40 * impact_score
                + 0.15 * movement_score
                + 0.10 * (criticality * 100.0)
            )
            score = round(max(0.0, min(100.0, raw * max(0.0, min(1.0, confidence)))), 1)
            priority = "P0 - CRITICAL" if score >= 80 else "P1 - HIGH" if score >= 60 else "P2 - MEDIUM" if score >= 35 else "P3 - LOW"

            results.append(KPIInsight(
                kpi_name=name, baseline_value=b, observed_value=o,
                delta_value=delta, delta_pct=pct, z_score=z,
                statistical_severity=severity, business_impact_usd=impacts[name],
                kpi_criticality=criticality, confidence=confidence,
                materiality_score=score, priority=priority,
                evidence=evidence_by_kpi.get(name, []),
            ))

        return [x.to_dict() for x in sorted(results, key=lambda x: x.materiality_score, reverse=True)]


def build_materiality_report(
    daily_df: pd.DataFrame,
    evaluation_date: Any,
    confidence: float = 1.0,
) -> Dict[str, Any]:
    """Build a report from the harmonized daily dataframe."""
    if daily_df is None or daily_df.empty:
        return {"kpis": [], "top_kpi": None, "method": "No data"}

    df = daily_df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    eval_date = pd.to_datetime(evaluation_date).date()
    base = df[df["date"] < eval_date]
    obs = df[df["date"] == eval_date]
    if base.empty or obs.empty:
        return {"kpis": [], "top_kpi": None, "method": "Insufficient data"}

    b = {
        "Gross Revenue": float(base["gross_revenue"].mean()),
        "Order Volume": float(base["order_volume"].mean()),
        "Sessions": float(base["sessions"].mean()),
        "Conversion Rate": float(base["conversion_rate"].mean()),
        "AOV": float(base["aov"].mean()),
    }
    o = obs.iloc[0]
    observed = {
        "Gross Revenue": float(o["gross_revenue"]),
        "Order Volume": float(o["order_volume"]),
        "Sessions": float(o["sessions"]),
        "Conversion Rate": float(o["conversion_rate"]),
        "AOV": float(o["aov"]),
    }

    # KPI-specific z scores from historical daily variation.
    z = {}
    columns = {
        "Gross Revenue": "gross_revenue", "Order Volume": "order_volume",
        "Sessions": "sessions", "Conversion Rate": "conversion_rate", "AOV": "aov"
    }
    for name, col in columns.items():
        series = pd.to_numeric(base[col], errors="coerce").dropna()
        std = float(series.std(ddof=1)) if len(series) > 1 else 0.0
        z[name] = (observed[name] - b[name]) / std if std > 1e-12 else 0.0

    report = MaterialityEngine().rank(b, observed, z_scores=z, confidence=confidence)
    return {
        "kpis": report,
        "top_kpi": report[0]["kpi_name"] if report else None,
        "top_score": report[0]["materiality_score"] if report else 0.0,
        "method": "Deterministic: statistical severity (35%) + business impact (40%) + movement (15%) + KPI criticality (10%), scaled by confidence",
        "evaluation_date": str(eval_date),
    }
