"""Data-source health and freshness assessment for heterogeneous KPI inputs."""
from datetime import datetime, date, time
from typing import Any, Dict, List
import pandas as pd


class DataHealthEngine:
    SOURCE_CONFIG = {
        "ERP": {"grain": "Daily", "sla_hours": 24, "owner": "Enterprise ERP Systems", "column": "transaction_date"},
        "Web Analytics": {"grain": "Hourly", "sla_hours": 1, "owner": "Digital Analytics Engineering", "column": "session_timestamp"},
        "Jira / Support": {"grain": "Weekly", "sla_hours": 168, "owner": "Customer Operations & DevOps", "column": "created_timestamp"},
    }

    @classmethod
    def assess(cls, bundle: Any) -> List[Dict[str, Any]]:
        frames = [
            ("ERP", getattr(bundle, "erp_df", None)),
            ("Web Analytics", getattr(bundle, "web_df", None)),
            ("Jira / Support", getattr(bundle, "jira_df", None)),
        ]
        eval_date = getattr(bundle, "evaluation_date", None)
        if eval_date is not None:
            eval_dt = datetime.combine(pd.to_datetime(eval_date).date(), time(23, 59, 59))
        else:
            eval_dt = datetime.utcnow()

        rows = []
        for name, df in frames:
            cfg = cls.SOURCE_CONFIG[name]
            if df is None or df.empty:
                rows.append({
                    "source": name, "status": "MISSING", "rows": 0,
                    "grain": cfg["grain"], "sla_hours": cfg["sla_hours"],
                    "freshness_hours": None, "quality_pct": 0.0,
                    "owner": cfg["owner"], "message": "No records available"
                })
                continue

            col = cfg["column"]
            parsed = pd.to_datetime(df[col], errors="coerce") if col in df.columns else pd.Series(dtype="datetime64[ns]")
            valid = parsed.notna()
            max_ts = parsed[valid].max() if valid.any() else None
            freshness = None
            if max_ts is not None:
                max_dt = max_ts.to_pydatetime()
                if max_dt.tzinfo is not None:
                    max_dt = max_dt.replace(tzinfo=None)
                freshness = max(0.0, (eval_dt - max_dt).total_seconds() / 3600.0)

            quality_pct = float(valid.mean() * 100.0) if len(valid) else 0.0
            status = "FRESH" if freshness is not None and freshness <= cfg["sla_hours"] else "STALE"
            if quality_pct < 95:
                status = "QUALITY_WARNING" if status == "FRESH" else "STALE + QUALITY_WARNING"

            rows.append({
                "source": name, "status": status, "rows": int(len(df)),
                "grain": cfg["grain"], "sla_hours": cfg["sla_hours"],
                "freshness_hours": round(freshness, 1) if freshness is not None else None,
                "quality_pct": round(quality_pct, 1),
                "owner": cfg["owner"],
                "message": f"Observed at {max_dt.isoformat()}" if max_ts is not None else "Timestamp unavailable",
            })
        return rows
