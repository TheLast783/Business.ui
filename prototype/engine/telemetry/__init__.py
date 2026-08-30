"""Telemetry and runtime performance package."""

try:
    from prototype.engine.telemetry.tracker import TelemetryTracker
    from prototype.engine.telemetry.feedback import FeedbackManager
except ImportError:
    from engine.telemetry.tracker import TelemetryTracker
    from engine.telemetry.feedback import FeedbackManager

__all__ = ["TelemetryTracker", "FeedbackManager"]
