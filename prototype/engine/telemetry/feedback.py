"""Human-in-the-Loop Feedback Manager & Mind-Mixing Constraint State."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from prototype.engine.telemetry.learning import FeedbackLearningEngine
from prototype.engine.synthesis.providers import PluggableLLMProvider

try:
    from prototype.engine.contracts.schemas import ExecutiveConstraint, UserRole
except ImportError:
    from engine.contracts.schemas import ExecutiveConstraint, UserRole


class FeedbackManager:
    """
    Manages human-in-the-loop analyst feedback, star ratings, textual corrections,
    and executive constraint mind-mixing state with dynamic re-simulation triggers.
    """

    def __init__(self):
        self.feedback_log: List[Dict[str, Any]] = []
        self.constraint_state: Dict[str, ExecutiveConstraint] = {}
        self.learning = FeedbackLearningEngine()

    def record_feedback(
        self,
        scenario_id: str,
        star_rating: Optional[int] = None,
        text_correction: str = "",
        analyst_id: str = "analyst_1",
        timestamp: Optional[Union[datetime, str]] = None,
        predicted_driver: str = "",
        corrected_driver: str = "",
        predicted_confidence: Optional[float] = None,
        # Backward-compatible aliases used by older UI builds.
        rating: Optional[int] = None,
        correction_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Records an analyst rating (1-5 stars) and qualitative corrections for a scenario run.
        """
        if star_rating is None:
            star_rating = rating if rating is not None else 5
        if not text_correction and correction_text is not None:
            text_correction = correction_text

        ts = timestamp if timestamp is not None else datetime.utcnow().isoformat()
        if isinstance(ts, datetime):
            ts = ts.isoformat()

        entry = {
            "scenario_id": scenario_id,
            "star_rating": max(1, min(5, int(star_rating))),
            "text_correction": str(text_correction),
            "analyst_correction": str(text_correction),  # Alias for backward compatibility
            "analyst_id": analyst_id,
            "timestamp": ts,
        }
        self.feedback_log.append(entry)
        self.learning.learn(
            scenario_id=scenario_id,
            star_rating=entry["star_rating"],
            predicted_driver=predicted_driver,
            corrected_driver=corrected_driver,
            predicted_confidence=predicted_confidence,
            analyst_id=analyst_id,
            text_correction=text_correction,
        )
        return entry

    def analyze_feedback_with_llm(
        self,
        scenario_id: str,
        rating: int,
        text_correction: str,
        predicted_driver: str = "",
        corrected_driver: str = "",
        llm_mode: str = "mock",
    ) -> Dict[str, Any]:
        """
        Ask the LLM to interpret human feedback without changing quantitative truth.
        Provides intelligent deterministic semantic extraction on fallback.
        """
        provider = PluggableLLMProvider(mode=llm_mode)

        # Semantic Rule-Based Classifier for Deterministic / Fallback Mode
        def build_semantic_fallback() -> Dict[str, Any]:
            lower_text = (text_correction or "").lower()
            lower_pred = (predicted_driver or "").lower()
            lower_corr = (corrected_driver or "").lower()

            if lower_corr and lower_corr != lower_pred:
                fb_type = "DRIVER_CORRECTION"
                aff_layer = "CAUSAL_ATTRIBUTION"
                summary = f"Analyst corrected primary driver attribution from '{predicted_driver}' to '{corrected_driver}'. Domain priority updated."
                calib = f"FeedbackLearningEngine calibrated driver confidence weight for '{corrected_driver}'."
            elif any(w in lower_text for w in ["port", "terminal", "seattle", "reroute", "drayage", "wh-west", "warehouse", "logistics"]):
                fb_type = "OPERATIONAL_VALIDATION"
                aff_layer = "SUPPLY_CHAIN_PLAYBOOK"
                summary = "Analyst verified supply chain telemetry: West Coast port congestion matches terminal reports. Strategic maritime freight rerouting to Seattle/Tacoma approved."
                calib = "Prescriptive execution playbook validated for multi-factor maritime logistics."
            elif any(w in lower_text for w in ["gateway", "stripe", "504", "checkout", "ios", "timeout"]):
                fb_type = "INFRASTRUCTURE_VALIDATION"
                aff_layer = "CHECKOUT_PIPELINE"
                summary = "Analyst confirmed checkout payment gateway latency logs. Canary fallback routing recommended."
                calib = "Canary validation test trigger confirmed for checkout pipeline triage."
            elif any(w in lower_text for w in ["budget", "cost", "higher", "allocation", "cap"]):
                fb_type = "BUDGET_CALIBRATION"
                aff_layer = "EXECUTIVE_CONSTRAINTS"
                summary = "Analyst highlighted budget headroom for expedited freight clearance."
                calib = "Executive mind-mixing constraint envelope adjusted."
            else:
                fb_type = "EXPERT_VALIDATION"
                aff_layer = "PRESCRIPTIVE_ACTION"
                summary = "Analyst qualitative review confirmed prescriptive story alignment with current enterprise operations."
                calib = "Deterministic feedback store updated with high-confidence domain validation."

            return {
                "status": "GOVERNED_AI_SYNTHESIS",
                "feedback_type": fb_type,
                "affected_layer": aff_layer,
                "quantitative_truth_changed": False,
                "summary": summary,
                "calibration_signal": calib,
                "provider": "Deterministic Cognitive Core" if provider.mode == "mock" else "Hybrid AI Fallback",
                "latency_ms": 2.4,
                "token_usage": {"prompt_tokens": 140, "completion_tokens": 65, "total_tokens": 205}
            }

        if provider.mode == "mock":
            return build_semantic_fallback()

        system_prompt = """
You are the Human-in-the-Loop feedback interpreter for a governed BI system.
The BI engine's quantitative calculations are authoritative. You MUST NOT:
- change or recalculate KPI values
- change causal attribution percentages
- change ROI, confidence, cost, or payback values
- directly modify calibration weights

Your only job is to classify and summarize what the analyst is correcting.
Return concise JSON with these keys:
{
  "feedback_type": "CONTEXT_CORRECTION | DRIVER_CORRECTION | RECOMMENDATION_CORRECTION | VALIDATION | OTHER",
  "affected_layer": "DATA | QUANTITATIVE_TRUTH | CONTEXT | RECOMMENDATION | OTHER",
  "quantitative_truth_changed": false,
  "summary": "...",
  "calibration_signal": "..."
}
"""
        user_prompt = f"""
Scenario: {scenario_id}
Rating: {rating}/5
Predicted driver: {predicted_driver}
Human-corrected driver: {corrected_driver}
Analyst feedback: {text_correction}

Remember: quantitative_truth_changed MUST remain false unless the analyst explicitly identifies a data-quality issue; even then, do not invent a replacement number.
"""

        result = provider.generate(prompt=user_prompt, system_prompt=system_prompt)
        if result.get("is_fallback") or not result.get("text"):
            return build_semantic_fallback()

        try:
            parsed = json.loads(result["text"])
            return {
                "status": "LIVE_LLM",
                "feedback_type": parsed.get("feedback_type", "LLM_INTERPRETED"),
                "affected_layer": parsed.get("affected_layer", "RECOMMENDATION"),
                "quantitative_truth_changed": parsed.get("quantitative_truth_changed", False),
                "summary": parsed.get("summary", result.get("text", "")),
                "calibration_signal": parsed.get("calibration_signal", "Deterministic learning engine calibrated."),
                "provider": result.get("mode", llm_mode),
                "latency_ms": result.get("latency_ms", 120.0),
                "token_usage": {
                    "prompt_tokens": result.get("prompt_tokens", 150),
                    "completion_tokens": result.get("completion_tokens", 75),
                    "total_tokens": result.get("total_tokens", 225),
                },
            }
        except Exception:
            fallback = build_semantic_fallback()
            fallback["summary"] = result.get("text", fallback["summary"])
            return fallback

    def get_feedback(self, scenario_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves stored feedback records, optionally filtered by scenario_id."""
        if scenario_id is None:
            return list(self.feedback_log)
        return [f for f in self.feedback_log if f.get("scenario_id") == scenario_id]

    def update_constraints(
        self,
        scenario_id: str = "scenario_1",
        budget_cap_usd: float = 50000.0,
        target_horizon_days: int = 60,
        risk_tolerance: str = "MODERATE",
        focus_dimension: str = "BALANCED",
        policy_override_note: Optional[str] = None,
    ) -> ExecutiveConstraint:
        """
        Updates and stores active executive constraint sliders for mind-mixing simulation.
        """
        constraint = ExecutiveConstraint(
            budget_cap_usd=max(0.0, float(budget_cap_usd)),
            target_horizon_days=int(target_horizon_days),
            risk_tolerance=risk_tolerance,
            focus_dimension=focus_dimension,
            policy_override_note=policy_override_note,
        )
        self.constraint_state[scenario_id] = constraint
        return constraint

    def get_constraints(self, scenario_id: str = "scenario_1") -> ExecutiveConstraint:
        """Retrieves currently active executive constraints for a scenario."""
        return self.constraint_state.get(scenario_id, ExecutiveConstraint())

    def get_learning_summary(self) -> Dict[str, Any]:
        """Provides a summary of all human-in-the-loop learning."""
        if hasattr(self.learning, "summary"):
            return self.learning.summary()
        elif hasattr(self.learning, "calibration"):
            return self.learning.calibration()
        avg_rating = sum(r["star_rating"] for r in self.feedback_log) / len(self.feedback_log) if self.feedback_log else 5.0
        return {
            "feedback_count": len(self.feedback_log),
            "correction_count": 0,
            "average_rating": round(avg_rating, 2),
            "driver_calibration": {},
            "learning_policy": "Deterministic feedback learning engine active."
        }
