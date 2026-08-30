"""Lightweight feedback learning loop.

This is intentionally not LLM training. It learns calibration signals from analyst
corrections and ratings, then exposes them for future ranking/orchestration.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class FeedbackLearningEngine:
    def __init__(self, store_path: Optional[str] = None):
        self.store_path = store_path or os.path.join(os.path.dirname(__file__), "feedback_learning.json")
        self.records: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.records = data
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.records = []

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self.records[-500:], f, indent=2)
        except OSError:
            pass

    def learn(
        self,
        scenario_id: str,
        star_rating: int,
        predicted_driver: Optional[str] = None,
        corrected_driver: Optional[str] = None,
        predicted_confidence: Optional[float] = None,
        analyst_id: str = "analyst_1",
        text_correction: str = "",
    ) -> Dict[str, Any]:
        corrected = corrected_driver.strip() if corrected_driver else ""
        predicted = predicted_driver.strip() if predicted_driver else ""
        record = {
            "scenario_id": scenario_id,
            "star_rating": max(1, min(5, int(star_rating))),
            "predicted_driver": predicted,
            "corrected_driver": corrected,
            "predicted_confidence": predicted_confidence,
            "was_correct": bool(corrected and predicted and corrected.lower() == predicted.lower()),
            "analyst_id": analyst_id,
            "text_correction": text_correction,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.records.append(record)
        self._save()
        return record

    def calibration(self) -> Dict[str, Any]:
        corrections = [r for r in self.records if r.get("corrected_driver")]
        by_driver: Dict[str, Dict[str, float]] = {}
        for r in corrections:
            d = r["predicted_driver"] or "Unknown"
            x = by_driver.setdefault(d, {"count": 0, "correct": 0})
            x["count"] += 1
            x["correct"] += int(r.get("was_correct", False))

        result = {}
        for driver, x in by_driver.items():
            result[driver] = {
                "observations": int(x["count"]),
                "accuracy": round(x["correct"] / x["count"], 3) if x["count"] else 0.0,
                "calibration_weight": round(0.5 + 0.5 * (x["correct"] / x["count"]), 3) if x["count"] else 0.5,
            }
        avg_rating = sum(r["star_rating"] for r in self.records) / len(self.records) if self.records else 0.0
        return {
            "feedback_count": len(self.records),
            "correction_count": len(corrections),
            "average_rating": round(avg_rating, 2),
            "driver_calibration": result,
            "learning_policy": "Future driver rankings can be reweighted by historical human-correction calibration; feedback does not retrain the LLM.",
        }

    def summary(self) -> Dict[str, Any]:
        """Alias for calibration() returning learning statistics summary."""
        return self.calibration()
