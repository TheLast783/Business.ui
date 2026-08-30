"""Statistical Process Control (SPC) with Day-of-Week Seasonality Normalization and Cold Start."""

import math
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from prototype.engine.config import (
    ANOMALY_Z_THRESHOLD,
    SPC_BASELINE_WINDOW_DAYS,
    SPC_COLD_START_THRESHOLD_DAYS,
    WARNING_Z_THRESHOLD,
)
from prototype.engine.contracts.schemas import (
    AnomalyDirection,
    AnomalyRecord,
    AnomalySeverity,
    DataQuality,
    SPCResult,
)


STUDENT_T_CRITICAL_01: Dict[int, float] = {
    1: 63.657,
    2: 9.925,
    3: 5.841,
    4: 4.604,
    5: 4.032,
    6: 3.707,
    7: 3.499,
    8: 3.355,
    9: 3.250,
    10: 3.169,
    11: 3.106,
    12: 3.055,
    13: 3.012,
    14: 2.977,
    15: 2.947,
    20: 2.845,
    25: 2.787,
    30: 2.750,
}

STUDENT_T_CRITICAL_05: Dict[int, float] = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    20: 2.086,
    25: 2.060,
    30: 2.042,
}


def get_student_t_critical(df: int, alpha: float = 0.01) -> float:
    """Return Student-t critical value for degrees of freedom df and two-tailed alpha."""
    df_clamped = max(1, min(30, df))
    table = STUDENT_T_CRITICAL_01 if alpha <= 0.02 else STUDENT_T_CRITICAL_05
    if df_clamped in table:
        return table[df_clamped]
    keys = sorted(table.keys())
    for i in range(len(keys) - 1):
        if keys[i] <= df_clamped <= keys[i+1]:
            k1, k2 = keys[i], keys[i+1]
            t1, t2 = table[k1], table[k2]
            return t1 + (t2 - t1) * (df_clamped - k1) / (k2 - k1)
    return 2.576 if alpha <= 0.02 else 1.960


class StatisticalProcessControl:
    """
    Statistical Process Control engine implementing:
    - 28-day rolling baseline window.
    - Day-of-Week (DoW) seasonality index normalization to prevent false alarms on cyclical weekend dips.
    - Standardized Z-Score calculation.
    - Upper and Lower Control Limits (UCL / LCL = mean +- 2.5 sigma).
    - Anomaly classification: Critical (|z| >= 2.5), Warning (1.5 <= |z| < 2.5), Normal (|z| < 1.5).
    - Robust Median Absolute Deviation (MAD) calculation.
    - Cold-start adaptation (Student-t critical value and uncertainty expansion when N < 14).
    """

    def __init__(self, window_days: int = SPC_BASELINE_WINDOW_DAYS, sigma_threshold: float = ANOMALY_Z_THRESHOLD):
        self.window_days = window_days
        self.sigma_threshold = sigma_threshold

    @classmethod
    def compute_dow_indices(
        cls,
        values: List[float],
        dates: List[date]
    ) -> Tuple[Dict[int, float], float]:
        """
        Compute Day-of-Week (DoW) seasonality indices (0=Monday ... 6=Sunday).
        Returns (dow_indices, overall_mean) in full double precision.
        """
        if not values:
            return {d: 1.0 for d in range(7)}, 0.0

        overall_mean = sum(values) / len(values)
        if overall_mean <= 0.0:
            return {d: 1.0 for d in range(7)}, 0.0

        dow_sums = {d: 0.0 for d in range(7)}
        dow_counts = {d: 0 for d in range(7)}

        for val, dt in zip(values, dates):
            d = dt.weekday()
            dow_sums[d] += float(val)
            dow_counts[d] += 1

        dow_indices = {}
        for d in range(7):
            if dow_counts[d] > 0:
                dow_mean = dow_sums[d] / dow_counts[d]
                dow_indices[d] = float(dow_mean / overall_mean)
            else:
                dow_indices[d] = 1.0

        return dow_indices, overall_mean

    @classmethod
    def compute_mad(cls, values: List[float]) -> Tuple[float, float]:
        """
        Compute Median and Median Absolute Deviation (MAD).
        Returns (median, mad).
        """
        if not values:
            return 0.0, 0.0
        med = float(np.median(values))
        abs_devs = [abs(x - med) for x in values]
        mad = float(np.median(abs_devs))
        return round(med, 4), round(mad, 4)

    @classmethod
    def compute(
        cls,
        values: Union[List[float], pd.Series, np.ndarray],
        dates: Union[List[date], List[datetime], pd.Series],
        window: int = SPC_BASELINE_WINDOW_DAYS,
        sigma_thresh: float = ANOMALY_Z_THRESHOLD,
        warning_thresh: float = WARNING_Z_THRESHOLD,
        metric_name: str = "Gross Revenue",
        cold_start_threshold: int = SPC_COLD_START_THRESHOLD_DAYS,
    ) -> SPCResult:
        """
        Compute Seasonality-Normalized SPC baseline and control limits for the evaluation point.
        The evaluation point is the last element (values[-1], dates[-1]).
        The baseline window uses up to `window` preceding observations.
        """
        val_list = [float(v) for v in values]
        date_list = []
        for d in dates:
            if isinstance(d, datetime):
                date_list.append(d.date())
            elif isinstance(d, pd.Timestamp):
                date_list.append(d.date())
            else:
                date_list.append(d)

        n_total = len(val_list)
        if n_total == 0:
            raise ValueError("Cannot compute SPC on empty series")

        eval_val = val_list[-1]
        eval_date = date_list[-1]
        eval_dow = eval_date.weekday()

        is_cold_start = n_total < cold_start_threshold or (n_total - 1) < cold_start_threshold

        if is_cold_start:
            history_vals = val_list[:-1] if n_total > 1 else val_list
            sample_n = len(history_vals)
            mu_val = sum(history_vals) / max(1, sample_n)

            if sample_n > 1:
                var_val = sum((x - mu_val) ** 2 for x in history_vals) / (sample_n - 1)
                std_val = math.sqrt(var_val) if var_val > 0 else 1.0
            else:
                std_val = 1.0

            df = max(1, sample_n - 1)
            t_crit = get_student_t_critical(df, alpha=0.01)
            expansion = math.sqrt(1.0 + (1.0 / max(1, sample_n)))
            eff_multiplier = max(sigma_thresh, t_crit * expansion)

            ucl = round(mu_val + eff_multiplier * std_val, 4)
            lcl = round(mu_val - eff_multiplier * std_val, 4)

            diff = eval_val - mu_val
            if abs(diff) < 1e-5:
                z_score = 0.0
            elif std_val > 1e-6:
                z_score = round(diff / std_val, 4)
            else:
                z_score = 0.0

            med, mad = cls.compute_mad(history_vals)
            mod_z = round((0.6745 * (eval_val - med)) / mad, 4) if mad > 0 else z_score

            is_anomaly = abs(z_score) > sigma_thresh or eval_val < lcl or eval_val > ucl
            confidence = max(0.3, round(sample_n / float(cold_start_threshold), 4))

            severity = AnomalySeverity.NORMAL
            if abs(z_score) >= sigma_thresh or eval_val < lcl or eval_val > ucl:
                severity = AnomalySeverity.CRITICAL
            elif abs(z_score) >= warning_thresh:
                severity = AnomalySeverity.WARNING

            direction = AnomalyDirection.NONE
            if z_score < -0.001:
                direction = AnomalyDirection.DROP
            elif z_score > 0.001:
                direction = AnomalyDirection.SURGE

            return SPCResult(
                metric_name=metric_name,
                evaluation_date=eval_date,
                observed_value=round(eval_val, 4),
                mean=round(mu_val, 4),
                std=round(std_val, 4),
                ucl=ucl,
                lcl=lcl,
                z_score=z_score,
                is_anomaly=is_anomaly,
                severity=severity,
                direction=direction,
                is_cold_start=True,
                dow_index=1.0,
                mad=mad,
                modified_z_score=mod_z,
                data_quality=DataQuality.COLD_START,
                baseline_points_count=sample_n,
                dow_indices={d: 1.0 for d in range(7)},
                confidence_score=confidence,
            )

        # Standard Mature Baseline Path: 28-day Day-of-Week Normalized
        if n_total > window:
            base_values = val_list[-window-1:-1]
            base_dates = date_list[-window-1:-1]
        else:
            base_values = val_list[:-1]
            base_dates = date_list[:-1]

        dow_indices, overall_mean = cls.compute_dow_indices(base_values, base_dates)

        # Deseasonalize baseline
        deseasonalized = [
            val / dow_indices[dt.weekday()] if dow_indices[dt.weekday()] > 0 else val
            for val, dt in zip(base_values, base_dates)
        ]

        mu_base = sum(deseasonalized) / len(deseasonalized)
        var_base = sum((x - mu_base) ** 2 for x in deseasonalized) / max(1, len(deseasonalized) - 1)
        sigma_base = math.sqrt(var_base) if var_base > 0 else 0.0

        s_eval = dow_indices[eval_dow]
        mu_eval = mu_base * s_eval
        sigma_eval = sigma_base * s_eval

        ucl = round(mu_eval + sigma_thresh * sigma_eval, 4)
        lcl = round(mu_eval - sigma_thresh * sigma_eval, 4)

        diff = eval_val - mu_eval
        if abs(diff) < 1e-4:
            z_score = 0.0
        elif sigma_eval > 1e-6:
            z_score = round(diff / sigma_eval, 4)
        else:
            z_score = 0.0 if abs(diff) < 1e-4 else (100.0 if diff > 0 else -100.0)

        med, mad = cls.compute_mad(base_values)
        mod_z = round((0.6745 * (eval_val - med)) / mad, 4) if mad > 0 else z_score

        is_anomaly = abs(z_score) > sigma_thresh

        severity = AnomalySeverity.NORMAL
        if abs(z_score) >= sigma_thresh:
            severity = AnomalySeverity.CRITICAL
        elif abs(z_score) >= warning_thresh:
            severity = AnomalySeverity.WARNING

        direction = AnomalyDirection.NONE
        if z_score < -0.001:
            direction = AnomalyDirection.DROP
        elif z_score > 0.001:
            direction = AnomalyDirection.SURGE

        # Display version of dow_indices rounded cleanly
        dow_indices_display = {d: round(v, 4) for d, v in dow_indices.items()}

        return SPCResult(
            metric_name=metric_name,
            evaluation_date=eval_date,
            observed_value=round(eval_val, 4),
            mean=round(mu_eval, 4),
            std=round(sigma_eval, 4),
            ucl=ucl,
            lcl=lcl,
            z_score=z_score,
            is_anomaly=is_anomaly,
            severity=severity,
            direction=direction,
            is_cold_start=False,
            dow_index=round(s_eval, 4),
            mad=mad,
            modified_z_score=mod_z,
            data_quality=DataQuality.NORMAL,
            baseline_points_count=len(base_values),
            dow_indices=dow_indices_display,
            confidence_score=1.0,
        )

    def evaluate(self, values: List[float], dates: List[date]) -> SPCResult:
        """Instance method wrapper for compute."""
        return self.compute(values, dates, window=self.window_days, sigma_thresh=self.sigma_threshold)

    @classmethod
    def evaluate_rolling(
        cls,
        values: Union[List[float], pd.Series],
        dates: Union[List[date], List[datetime], pd.Series],
        window: int = SPC_BASELINE_WINDOW_DAYS,
        sigma_thresh: float = ANOMALY_Z_THRESHOLD,
        metric_name: str = "Gross Revenue",
    ) -> List[SPCResult]:
        """Evaluate SPC sequentially across each point in the historical series."""
        val_list = [float(v) for v in values]
        date_list = [d.date() if isinstance(d, (datetime, pd.Timestamp)) else d for d in dates]

        results = []
        for i in range(len(val_list)):
            sub_vals = val_list[:i+1]
            sub_dates = date_list[:i+1]
            res = cls.compute(
                sub_vals,
                sub_dates,
                window=window,
                sigma_thresh=sigma_thresh,
                metric_name=metric_name,
            )
            results.append(res)
        return results
