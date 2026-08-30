"""Configuration settings and constants for the KPI Intelligence-to-Action Engine."""

from typing import Dict

# Statistical Process Control (SPC) settings
SPC_BASELINE_WINDOW_DAYS: int = 28
SPC_COLD_START_THRESHOLD_DAYS: int = 14
ANOMALY_Z_THRESHOLD: float = 2.5
WARNING_Z_THRESHOLD: float = 1.5

# Reconciled Semantic Contract Settings
RECONCILIATION_TOLERANCE: float = 0.02  # +-2% tolerance between ERP orders and Web purchase events
CR_MIN_VALUE: float = 0.0
CR_MAX_VALUE: float = 1.0

# 3-Model AI Synthesis & Abstention Settings
ABSTENTION_CONFIDENCE_THRESHOLD: float = 0.75  # Abstains if top confidence < 75% or delta < 25%
ABSTENTION_MARGIN_THRESHOLD: float = 0.25

# Trajectory ROI Simulation Horizons
SIMULATION_HORIZONS: list = [30, 60, 90]

# Telemetry and Pricing Constants (per 1,000 tokens in USD)
TOKEN_PRICING: Dict[str, Dict[str, float]] = {
    "mock": {"prompt": 0.0000, "completion": 0.0000},
    "gpt-4o": {"prompt": 0.0025, "completion": 0.0100},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.00060},
    "gemini-1.5-pro": {"prompt": 0.00125, "completion": 0.00500},
    "gemini-1.5-flash": {"prompt": 0.000075, "completion": 0.00030},
    "ollama": {"prompt": 0.0000, "completion": 0.0000},
}

# Deterministic Seed
DEFAULT_RANDOM_SEED: int = 42

# RBAC Redaction Constants
REDACTED_CONFIDENTIAL_STR: str = "[CONFIDENTIAL]"
REDACTED_CUSTOMER_PREFIX: str = "CUST-***"
