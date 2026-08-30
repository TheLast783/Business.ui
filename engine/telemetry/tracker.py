"""Runtime Telemetry Tracker: Latency Breakdown, Token Accounting, and Cost Split."""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

try:
    from prototype.engine.contracts.schemas import TelemetryRecord
except ImportError:
    from engine.contracts.schemas import TelemetryRecord


class TelemetryTracker:
    """
    Tracks runtime execution performance, component-level latencies,
    token consumption, cost accounting, and deterministic vs LLM split percentages.
    """

    # Per-token pricing tables (USD per token)
    TOKEN_RATES: Dict[str, Dict[str, float]] = {
        "mock": {"prompt": 0.0, "completion": 0.0},
        "deterministic_mock": {"prompt": 0.0, "completion": 0.0},
        "openai": {"prompt": 0.0015 / 1000.0, "completion": 0.0020 / 1000.0},
        "gpt-4o": {"prompt": 0.0025 / 1000.0, "completion": 0.0100 / 1000.0},
        "gpt-4o-mini": {"prompt": 0.00015 / 1000.0, "completion": 0.0006 / 1000.0},
        "gemini": {"prompt": 0.00125 / 1000.0, "completion": 0.0050 / 1000.0},
        "gemini-1.5-flash": {"prompt": 0.000075 / 1000.0, "completion": 0.0003 / 1000.0},
        "ollama": {"prompt": 0.0, "completion": 0.0},
    }

    def __init__(self):
        self.records: List[TelemetryRecord] = []

    def start_timer(self) -> float:
        """Returns the current high-resolution timestamp."""
        return time.time()

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        provider: str = "mock"
    ) -> float:
        """
        Computes USD cost based on token counts and provider pricing rate.
        Mock and local providers incur exactly $0.00.
        """
        normalized_provider = (provider or "mock").lower()
        rates = self.TOKEN_RATES.get(normalized_provider, self.TOKEN_RATES["openai"])
        cost = (prompt_tokens * rates["prompt"]) + (completion_tokens * rates["completion"])
        return round(float(cost), 6)

    def record_run(
        self,
        scenario_id: str,
        start_time_s: Optional[float] = None,
        prompt_tokens: int = 420,
        completion_tokens: int = 160,
        math_time_ms: float = 4.2,
        ingestion_time_ms: float = 0.0,
        llm_time_ms: Optional[float] = None,
        total_latency_ms: Optional[float] = None,
        mode: str = "mock",
        provider: Optional[str] = None,
    ) -> TelemetryRecord:
        """
        Records an execution run with full latency and token breakdown.
        Guarantees that deterministic math core consumes strictly 0 tokens.
        """
        llm_provider = provider or mode or "mock"

        if total_latency_ms is None:
            if start_time_s is not None:
                elapsed_ms = (time.time() - start_time_s) * 1000.0
                total_latency_ms = max(math_time_ms + ingestion_time_ms + 0.5, elapsed_ms)
            else:
                total_latency_ms = ingestion_time_ms + math_time_ms + (llm_time_ms or 0.0)

        if llm_time_ms is None:
            llm_time_ms = max(0.0, total_latency_ms - math_time_ms - ingestion_time_ms)

        cost_usd = self.calculate_cost(prompt_tokens, completion_tokens, provider=llm_provider)

        record = TelemetryRecord(
            scenario_id=scenario_id,
            timestamp=datetime.utcnow(),
            latency_ms=round(total_latency_ms, 2),
            total_latency_ms=round(total_latency_ms, 2),
            ingestion_time_ms=round(ingestion_time_ms, 2),
            math_time_ms=round(math_time_ms, 2),
            llm_time_ms=round(llm_time_ms, 2),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            math_tokens=0,  # Invariant: 0 tokens for deterministic math
            llm_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=cost_usd,
            cost_usd=cost_usd,
            llm_provider=llm_provider,
            llm_calls=0 if str(mode).lower() in {"mock", "deterministic_mock"} else 3,
            cache_hits=0,
            insight_cost_usd=cost_usd,
        )
        self.records.append(record)
        return record

    def get_breakdown(self, record: Optional[TelemetryRecord] = None) -> Dict[str, Any]:
        """Returns the deterministic vs LLM time and token breakdown."""
        rec = record or self.get_latest_record()
        if not rec:
            return {
                "deterministic_ms": 0.0,
                "llm_ms": 0.0,
                "deterministic_pct": 100.0,
                "llm_pct": 0.0,
                "math_tokens": 0,
                "llm_tokens": 0,
                "cost_usd": 0.0,
            }

        det_ms = rec.ingestion_time_ms + rec.math_time_ms
        llm_ms = rec.llm_time_ms
        tot_ms = max(0.001, rec.latency_ms)

        det_pct = min(100.0, round((det_ms / tot_ms) * 100.0, 2))
        llm_pct = max(0.0, round(100.0 - det_pct, 2))

        return {
            "deterministic_ms": round(det_ms, 2),
            "llm_ms": round(llm_ms, 2),
            "deterministic_pct": det_pct,
            "llm_pct": llm_pct,
            "math_tokens": 0,
            "llm_tokens": rec.total_tokens,
            "cost_usd": rec.estimated_cost_usd,
        }

    def get_latest_record(self) -> Optional[TelemetryRecord]:
        """Returns the most recent telemetry record."""
        return self.records[-1] if self.records else None

    def get_all_records(self) -> List[TelemetryRecord]:
        """Returns all recorded telemetry records."""
        return list(self.records)

    def clear(self) -> None:
        """Clears all stored telemetry history."""
        self.records.clear()
