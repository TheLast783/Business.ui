"""Exact closed-form Shapley Causal Metric Tree and Logarithmic Mean Divisia Index (LMDI) decomposition."""
import math
from datetime import date
from typing import Dict, Any, Optional

from prototype.engine.contracts.schemas import TreeDecompositionResult, MetricSnapshot


class CausalMetricTree:
    """
    Exact closed-form 3-factor Shapley decomposition for R = Sessions * CVR * AOV.
    Guarantees sum(delta_R_i) == total_delta_R with residual < 1e-5.
    """

    @staticmethod
    def shapley_3factor(
        s0: float, s1: float,
        cr0: float, cr1: float,
        aov0: float, aov1: float
    ) -> Dict[str, float]:
        """Calculates exact 3-factor Shapley contributions and returns dictionary."""
        s0, s1 = float(s0), float(s1)
        cr0, cr1 = float(cr0), float(cr1)
        aov0, aov1 = float(aov0), float(aov1)

        ds = s1 - s0
        dcr = cr1 - cr0
        daov = aov1 - aov0

        delta_r_s = (
            ds * cr0 * aov0
            + 0.5 * ds * dcr * aov0
            + 0.5 * ds * cr0 * daov
            + (1.0 / 3.0) * ds * dcr * daov
        )
        delta_r_cr = (
            s0 * dcr * aov0
            + 0.5 * ds * dcr * aov0
            + 0.5 * s0 * dcr * daov
            + (1.0 / 3.0) * ds * dcr * daov
        )
        delta_r_aov = (
            s0 * cr0 * daov
            + 0.5 * ds * cr0 * daov
            + 0.5 * s0 * dcr * daov
            + (1.0 / 3.0) * ds * dcr * daov
        )

        r0 = s0 * cr0 * aov0
        r1 = s1 * cr1 * aov1
        total_delta_r = r1 - r0
        sum_factors = delta_r_s + delta_r_cr + delta_r_aov
        residual = total_delta_r - sum_factors

        return {
            "delta_revenue": total_delta_r,
            "delta_r_sessions": delta_r_s,
            "delta_r_cvr": delta_r_cr,
            "delta_r_aov": delta_r_aov,
            "sum_factors": sum_factors,
            "residual": residual
        }

    @staticmethod
    def shapley_2factor(
        v0: float, v1: float,
        aov0: float, aov1: float
    ) -> Dict[str, float]:
        """Exact closed-form 2-factor Shapley attribution for R = V * AOV."""
        v0, v1 = float(v0), float(v1)
        aov0, aov1 = float(aov0), float(aov1)

        dv = v1 - v0
        daov = aov1 - aov0

        delta_r_v = dv * aov0 + 0.5 * dv * daov
        delta_r_aov = v0 * daov + 0.5 * dv * daov

        total_delta_r = (v1 * aov1) - (v0 * aov0)
        sum_factors = delta_r_v + delta_r_aov
        residual = total_delta_r - sum_factors

        return {
            "delta_revenue": total_delta_r,
            "delta_r_volume": delta_r_v,
            "delta_r_aov": delta_r_aov,
            "sum_factors": sum_factors,
            "residual": residual,
        }

    @classmethod
    def hierarchical_shapley(
        cls,
        s0: float, s1: float,
        cr0: float, cr1: float,
        aov0: float, aov1: float
    ) -> Dict[str, float]:
        """
        Hierarchical 2-Level Multiplicative Shapley attribution:
        Level 1: R = V * AOV
        Level 2: V = S * CR -> allocate Delta R_V proportionally to Delta V_S and Delta V_CR.
        """
        s0, s1 = float(s0), float(s1)
        cr0, cr1 = float(cr0), float(cr1)
        aov0, aov1 = float(aov0), float(aov1)

        v0 = s0 * cr0
        v1 = s1 * cr1
        dv = v1 - v0

        res_l1 = cls.shapley_2factor(v0, v1, aov0, aov1)
        delta_r_v = res_l1["delta_r_volume"]
        delta_r_aov = res_l1["delta_r_aov"]

        ds = s1 - s0
        dcr = cr1 - cr0
        delta_v_s = ds * cr0 + 0.5 * ds * dcr
        delta_v_cr = s0 * dcr + 0.5 * ds * dcr

        if abs(dv) > 1e-9:
            delta_r_s = delta_r_v * (delta_v_s / dv)
            delta_r_cr = delta_r_v * (delta_v_cr / dv)
        else:
            res_dir = cls.shapley_3factor(s0, s1, cr0, cr1, aov0, aov1)
            delta_r_s = res_dir["delta_r_sessions"]
            delta_r_cr = res_dir["delta_r_cvr"]

        total_delta_r = (s1 * cr1 * aov1) - (s0 * cr0 * aov0)
        sum_factors = delta_r_s + delta_r_cr + delta_r_aov

        return {
            "delta_revenue": total_delta_r,
            "delta_r_sessions": delta_r_s,
            "delta_r_cvr": delta_r_cr,
            "delta_r_aov": delta_r_aov,
            "delta_r_volume": delta_r_v,
            "sum_factors": sum_factors,
            "residual": total_delta_r - sum_factors,
        }

    @staticmethod
    def lmdi_1(
        s0: float, s1: float,
        cr0: float, cr1: float,
        aov0: float, aov1: float
    ) -> Dict[str, float]:
        """Continuous-path Logarithmic Mean Divisia Index (LMDI-I) decomposition."""
        s0, s1 = float(s0), float(s1)
        cr0, cr1 = float(cr0), float(cr1)
        aov0, aov1 = float(aov0), float(aov1)

        r0 = s0 * cr0 * aov0
        r1 = s1 * cr1 * aov1
        delta_r = r1 - r0

        if abs(r1 - r0) < 1e-9 or r0 <= 0 or r1 <= 0:
            l_val = r0
        else:
            l_val = (r1 - r0) / math.log(r1 / r0)

        d_s = l_val * math.log(s1 / s0) if s0 > 0 and s1 > 0 else 0.0
        d_cr = l_val * math.log(cr1 / cr0) if cr0 > 0 and cr1 > 0 else 0.0
        d_aov = l_val * math.log(aov1 / aov0) if aov0 > 0 and aov1 > 0 else 0.0
        sum_f = d_s + d_cr + d_aov

        return {
            "delta_revenue": delta_r,
            "delta_r_sessions": d_s,
            "delta_r_cvr": d_cr,
            "delta_r_aov": d_aov,
            "sum_factors": sum_f,
            "residual": delta_r - sum_f
        }

    @classmethod
    def decompose_values(
        cls,
        s0: float, s1: float,
        cr0: float, cr1: float,
        aov0: float, aov1: float,
        method: str = "shapley_3factor",
        start_date: date = date(2026, 8, 1),
        eval_date: date = date(2026, 8, 29),
        base_label: str = "Baseline",
        actual_label: str = "Actual"
    ) -> TreeDecompositionResult:
        """Decomposes raw baseline vs actual values into a structured TreeDecompositionResult."""
        if method == "hierarchical":
            res = cls.hierarchical_shapley(s0, s1, cr0, cr1, aov0, aov1)
        else:
            res = cls.shapley_3factor(s0, s1, cr0, cr1, aov0, aov1)

        total_delta_r = res["delta_revenue"]
        delta_r_s = res["delta_r_sessions"]
        delta_r_cr = res["delta_r_cvr"]
        delta_r_aov = res["delta_r_aov"]
        delta_r_vol = res.get("delta_r_volume", delta_r_s + delta_r_cr)
        sum_factors = res["sum_factors"]
        residual = res["residual"]

        if abs(total_delta_r) > 1e-6:
            pct_s = round((delta_r_s / total_delta_r) * 100.0, 4)
            pct_cr = round((delta_r_cr / total_delta_r) * 100.0, 4)
            pct_aov = round(100.0 - pct_s - pct_cr, 4)
        else:
            pct_s, pct_cr, pct_aov = 0.0, 0.0, 0.0

        factors = {"sessions": delta_r_s, "cvr": delta_r_cr, "aov": delta_r_aov, "volume": delta_r_vol}
        factors_pct = {"sessions": pct_s, "cvr": pct_cr, "aov": pct_aov}

        # Adverse driver share normalized
        neg_factors = {k: abs(v) for k, v in {"sessions": delta_r_s, "cvr": delta_r_cr, "aov": delta_r_aov}.items() if v < 0}
        total_neg = sum(neg_factors.values()) if neg_factors else 0.0
        if total_neg > 1e-9:
            adverse_shares = {k: round((v / total_neg * 100.0), 2) for k, v in neg_factors.items()}
        else:
            adverse_shares = {}
        for k in ["sessions", "cvr", "aov"]:
            if k not in adverse_shares:
                adverse_shares[k] = 0.0

        r0 = s0 * cr0 * aov0
        r1 = s1 * cr1 * aov1

        lmdi_res = cls.lmdi_1(s0, s1, cr0, cr1, aov0, aov1)

        return TreeDecompositionResult(
            delta_revenue=round(total_delta_r, 2),
            factor_dollar_contributions={k: round(v, 2) for k, v in factors.items()},
            factor_pct_contributions=factors_pct,
            delta_r_sessions=round(delta_r_s, 2),
            delta_r_cvr=round(delta_r_cr, 2),
            delta_r_aov=round(delta_r_aov, 2),
            delta_r_volume=round(delta_r_vol, 2),
            sum_factors=round(sum_factors, 2),
            residual=round(residual, 6),
            baseline_metrics=MetricSnapshot(
                period_label=base_label,
                start_date=start_date,
                end_date=eval_date,
                gross_revenue=round(r0, 2),
                order_volume=int(s0 * cr0),
                sessions=int(s0),
                conversion_rate=round(cr0, 6),
                aov=round(aov0, 2)
            ),
            actual_metrics=MetricSnapshot(
                period_label=actual_label,
                start_date=eval_date,
                end_date=eval_date,
                gross_revenue=round(r1, 2),
                order_volume=int(s1 * cr1),
                sessions=int(s1),
                conversion_rate=round(cr1, 6),
                aov=round(aov1, 2)
            ),
            method=method,
            adverse_driver_shares=adverse_shares,
            lmdi_verification={
                "sessions": round(lmdi_res["delta_r_sessions"], 2),
                "cvr": round(lmdi_res["delta_r_cvr"], 2),
                "aov": round(lmdi_res["delta_r_aov"], 2),
            }
        )

    @classmethod
    def decompose_3factor(
        cls,
        s0: float, s1: float,
        cr0: float, cr1: float,
        aov0: float, aov1: float
    ) -> TreeDecompositionResult:
        return cls.decompose_values(s0, s1, cr0, cr1, aov0, aov1)

    @classmethod
    def decompose(
        cls,
        base_snap: MetricSnapshot,
        actual_snap: MetricSnapshot,
        method: str = "shapley_3factor"
    ) -> TreeDecompositionResult:
        res = cls.decompose_values(
            s0=float(base_snap.sessions),
            s1=float(actual_snap.sessions),
            cr0=float(base_snap.conversion_rate),
            cr1=float(actual_snap.conversion_rate),
            aov0=float(base_snap.aov),
            aov1=float(actual_snap.aov),
            method=method,
            start_date=base_snap.start_date,
            eval_date=actual_snap.end_date,
            base_label=base_snap.period_label,
            actual_label=actual_snap.period_label
        )
        res.baseline_metrics = base_snap
        res.actual_metrics = actual_snap
        return res

    # Alias for convenience
    decompose_snapshots = decompose

