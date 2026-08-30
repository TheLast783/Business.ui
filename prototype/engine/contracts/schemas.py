"""Pydantic schemas and dataclass models for multi-source data records, snapshots, and RBAC."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class UserRole(str, Enum):
    """Role-Based Access Control (RBAC) personas."""
    EXECUTIVE = "EXECUTIVE"
    OPERATIONS_ANALYST = "OPERATIONS_ANALYST"


class DataQuality(str, Enum):
    """Data quality status indicators."""
    NORMAL = "NORMAL"
    COLD_START = "COLD_START"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    CORRUPTED = "CORRUPTED"


class AnomalySeverity(str, Enum):
    """Statistical anomaly severity levels."""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AnomalyDirection(str, Enum):
    """Direction of metric movement."""
    DROP = "DROP"
    SURGE = "SURGE"
    NONE = "NONE"


class ERPSalesRecord(BaseModel):
    """Structured Daily ERP Sales Transaction record."""
    order_id: str = Field(..., description="Unique transaction ID")
    transaction_date: date = Field(..., description="Daily grain date")
    timestamp: datetime = Field(..., description="Exact transaction timestamp")
    customer_id: str = Field(..., description="Customer identifier")
    sku_id: str = Field(..., description="Product SKU ID")
    product_category: str = Field(..., description="Product Category")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    unit_price: float = Field(..., ge=0.0, description="Unit price charged")
    discount_amount: float = Field(default=0.0, ge=0.0, description="Promotional discount")
    gross_revenue: float = Field(..., ge=0.0, description="Gross revenue after discount")
    unit_cogs: Optional[float] = Field(default=None, description="Confidential unit cost of goods sold")
    gross_margin: Optional[float] = Field(default=None, description="Confidential gross margin amount")
    gross_margin_pct: Optional[float] = Field(default=None, description="Confidential gross margin percentage")
    fulfillment_status: str = Field(default="Shipped", description="Status: Shipped, Pending, Cancelled, Returned")
    shipping_location: str = Field(default="WH-West", description="Warehouse or port origin")
    channel: str = Field(default="Direct", description="Sales channel: Direct, Marketplace, B2B, Affiliate")


class WebSessionRecord(BaseModel):
    """Hourly Web Analytics Session stream record."""
    session_id: str = Field(..., description="Unique web session identifier")
    session_timestamp: datetime = Field(..., description="Hourly timestamp")
    session_date: date = Field(..., description="Date for daily rollup joins")
    session_hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    visitor_id: str = Field(..., description="Anonymous visitor cookie identifier")
    traffic_source: str = Field(default="Direct", description="Traffic channel: Direct, Organic, Paid Search, Social")
    device_category: str = Field(default="Desktop", description="Device category: Desktop, Mobile, Tablet")
    sessions: int = Field(default=1, ge=1, description="Number of visitor sessions in bucket")
    page_views: int = Field(default=1, ge=1, description="Number of pageviews")
    cart_add_events: int = Field(default=0, ge=0, description="Cart addition events")
    checkout_start_events: int = Field(default=0, ge=0, description="Checkout initiation events")
    purchase_events: int = Field(default=0, ge=0, description="Completed order purchase events")
    is_converted: bool = Field(default=False, description="Whether session resulted in purchase")
    bounce_flag: bool = Field(default=False, description="Whether visitor bounced immediately")


class SupportJiraRecord(BaseModel):
    """Weekly Unstructured Customer Support & Jira ticket record."""
    ticket_id: str = Field(..., description="Unique ticket identifier")
    created_timestamp: datetime = Field(..., description="Ticket creation timestamp")
    week_start_date: date = Field(..., description="Monday of the week grain")
    category: str = Field(..., description="Incident category")
    severity: str = Field(default="P2", description="Severity: P1, P2, P3")
    status: str = Field(default="Open", description="Ticket status: Open, In Progress, Resolved, Closed")
    summary: str = Field(..., description="Summary headline")
    description_text: str = Field(..., description="Detailed textual complaint / diagnostic logs")
    resolution_time_hrs: Optional[float] = Field(default=None, description="Resolution time in hours")
    affected_customer_tier: str = Field(default="Standard", description="Enterprise, VIP, Standard")
    carrier_or_system_id: Optional[str] = Field(default=None, description="Technical system/carrier ID")


class MetricSnapshot(BaseModel):
    """Reconciled multi-source canonical KPI snapshot for a given time window."""
    period_label: str = Field(..., description="Identifier for period (e.g. 'Baseline', 'Observed', 'Day-29')")
    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")
    gross_revenue: float = Field(..., ge=0.0, description="Total Gross Revenue ($)")
    order_volume: int = Field(..., ge=0, description="Total Count of Non-Cancelled Orders")
    sessions: int = Field(..., ge=0, description="Total Web Sessions")
    conversion_rate: float = Field(..., ge=0.0, le=1.0, description="Order Volume / Sessions")
    aov: float = Field(..., ge=0.0, description="Gross Revenue / Order Volume (Average Order Value)")
    total_cogs: Optional[float] = Field(default=None, description="Confidential total COGS")
    total_gross_margin: Optional[float] = Field(default=None, description="Confidential total gross margin")
    gross_margin_pct: Optional[float] = Field(default=None, description="Confidential gross margin %")

    @field_validator("conversion_rate")
    @classmethod
    def validate_cr_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Conversion rate {v} must be strictly between 0.0 and 1.0")
        return v


class AnomalyRecord(BaseModel):
    """Statistical Process Control (SPC) anomaly detection output."""
    metric_name: str = Field(..., description="Name of KPI evaluated (e.g. Gross Revenue, Conversion Rate)")
    timestamp: datetime = Field(..., description="Timestamp of evaluation")
    observed_value: float = Field(..., description="Actual value observed")
    expected_value: float = Field(..., description="Baseline expected value (DoW seasonality adjusted)")
    z_score: float = Field(..., description="Standardized deviation score")
    severity: AnomalySeverity = Field(..., description="Anomaly severity classification")
    direction: AnomalyDirection = Field(..., description="Direction of anomaly (DROP or SURGE)")
    is_anomaly: bool = Field(..., description="True if |z_score| >= ANOMALY_Z_THRESHOLD")
    dow_index: float = Field(default=1.0, description="Day of week seasonality multiplier applied")
    ucl: float = Field(default=0.0, description="Upper Control Limit (+2.5 sigma)")
    lcl: float = Field(default=0.0, description="Lower Control Limit (-2.5 sigma)")
    data_quality: DataQuality = Field(default=DataQuality.NORMAL, description="Data quality context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual diagnostic payload")


class ExecutiveConstraint(BaseModel):
    """Executive Human-in-the-Loop constraint and mind-mixing inputs."""
    budget_cap_usd: float = Field(default=10000.0, ge=0.0, description="Maximum budget allocated for remediation")
    target_horizon_days: int = Field(default=60, description="Target optimization horizon (30, 60, or 90 days)")
    risk_tolerance: str = Field(default="MODERATE", description="Risk posture: LOW, MODERATE, AGGRESSIVE")
    focus_dimension: str = Field(default="BALANCED", description="Optimization goal: REVENUE, MARGIN, CSAT, BALANCED")
    policy_override_note: Optional[str] = Field(default=None, description="Free-text executive directive or override")


class TelemetryRecord(BaseModel):
    """Runtime performance, token usage, cost accounting, and split metric tracking."""
    scenario_id: str = Field(..., description="Scenario identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Invocation timestamp")
    latency_ms: float = Field(..., ge=0.0, description="Total execution time in milliseconds")
    total_latency_ms: Optional[float] = Field(default=None, description="Alias for latency_ms")
    ingestion_time_ms: float = Field(default=0.0, ge=0.0, description="Time spent in data ingestion / harmonization")
    math_time_ms: float = Field(default=0.0, ge=0.0, description="Time spent in deterministic math (SPC + Trees)")
    llm_time_ms: float = Field(default=0.0, ge=0.0, description="Time spent in AI synthesis engine")
    prompt_tokens: int = Field(default=0, ge=0, description="Number of prompt tokens consumed")
    completion_tokens: int = Field(default=0, ge=0, description="Number of completion tokens generated")
    total_tokens: int = Field(default=0, ge=0, description="Total tokens consumed")
    math_tokens: int = Field(default=0, ge=0, description="Tokens consumed by deterministic math core (strictly 0)")
    llm_tokens: Optional[int] = Field(default=None, description="Alias for total_tokens")
    estimated_cost_usd: float = Field(default=0.0, ge=0.0, description="Estimated LLM API cost in USD")
    cost_usd: Optional[float] = Field(default=None, description="Alias for estimated_cost_usd")
    llm_provider: str = Field(default="mock", description="LLM provider name: mock, gpt-4o, gemini, etc.")
    llm_calls: int = Field(default=0, ge=0, description="Number of external LLM API calls attempted")
    llm_calls_count: Optional[int] = Field(default=None, description="Alias for llm_calls")
    cache_hits: int = Field(default=0, ge=0, description="Number of cached insight generations reused")
    insight_cost_usd: float = Field(default=0.0, ge=0.0, description="Estimated cost attributable to this insight")

    def model_post_init(self, __context: Any) -> None:
        if self.total_latency_ms is None:
            self.total_latency_ms = self.latency_ms
        if self.llm_tokens is None:
            self.llm_tokens = self.total_tokens
        if self.cost_usd is None:
            self.cost_usd = self.estimated_cost_usd
        if self.llm_calls_count is None:
            self.llm_calls_count = self.llm_calls

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)




class SPCResult(BaseModel):
    """Result of Statistical Process Control computation for a time series."""
    metric_name: str = Field(default="Gross Revenue", description="Evaluated KPI name")
    evaluation_date: Optional[date] = Field(default=None, description="Date of evaluated point")
    observed_value: float = Field(..., description="Observed metric value at evaluation point")
    mean: float = Field(..., description="Baseline expected value (seasonality adjusted)")
    std: float = Field(..., description="Standard deviation (seasonality adjusted)")
    ucl: float = Field(..., description="Upper Control Limit")
    lcl: float = Field(..., description="Lower Control Limit")
    z_score: float = Field(..., description="Standardized Z-Score")
    is_anomaly: bool = Field(..., description="True if |z_score| >= sigma_threshold")
    severity: AnomalySeverity = Field(default=AnomalySeverity.NORMAL, description="Anomaly severity level")
    direction: AnomalyDirection = Field(default=AnomalyDirection.NONE, description="Movement direction (DROP/SURGE/NONE)")
    is_cold_start: bool = Field(default=False, description="True if baseline data points < cold start threshold (14)")
    dow_index: float = Field(default=1.0, description="Day of Week seasonality multiplier")
    mad: Optional[float] = Field(default=None, description="Median Absolute Deviation")
    modified_z_score: Optional[float] = Field(default=None, description="MAD-based modified Z-Score")
    data_quality: DataQuality = Field(default=DataQuality.NORMAL, description="Data quality classification")
    baseline_points_count: int = Field(default=0, description="Number of historical points in baseline")
    dow_indices: Dict[int, float] = Field(default_factory=dict, description="Calculated 7-day seasonality indices")
    confidence_score: float = Field(default=1.0, description="Confidence score in baseline (penalized for cold start)")

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like subscripting for backward compatibility with oracle dicts."""
        return getattr(self, item)


class TreeDecompositionResult(BaseModel):
    """Exact closed-form Shapley Causal Metric Tree decomposition result."""
    delta_revenue: float = Field(..., description="Total Gross Revenue change: R1 - R0 ($)")
    factor_dollar_contributions: Dict[str, float] = Field(..., description="Dollar contribution per factor (sessions, cvr, aov)")
    factor_pct_contributions: Dict[str, float] = Field(..., description="Percentage contribution per factor summing to 100%")
    delta_r_sessions: float = Field(..., description="Dollar contribution of Sessions change")
    delta_r_cvr: float = Field(..., description="Dollar contribution of Conversion Rate change")
    delta_r_aov: float = Field(..., description="Dollar contribution of Average Order Value change")
    delta_r_volume: Optional[float] = Field(default=None, description="Combined volume dollar effect (Sessions + CVR)")
    sum_factors: float = Field(..., description="Sum of factor dollar contributions")
    residual: float = Field(default=0.0, description="Mathematical residual error: delta_revenue - sum_factors (guaranteed < 1e-5)")
    baseline_metrics: Optional[MetricSnapshot] = Field(default=None, description="Baseline period metrics")
    actual_metrics: Optional[MetricSnapshot] = Field(default=None, description="Evaluation period metrics")
    method: str = Field(default="shapley_3factor", description="Decomposition method: shapley_3factor, hierarchical_shapley, lmdi_1")
    adverse_driver_shares: Dict[str, float] = Field(default_factory=dict, description="Share of adverse (negative) pressure normalized to 100%")
    lmdi_verification: Optional[Dict[str, float]] = Field(default=None, description="Alternative LMDI-I verification contributions")

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like subscripting for backward compatibility with oracle dicts."""
        return getattr(self, item)


# Semantic Model Aliases for multi-module compatibility
ERPTransaction = ERPSalesRecord
WebAnalyticsSession = WebSessionRecord
SupportTicket = SupportJiraRecord


# ============================================================================
# SYNTHESIS & AI ARCHITECTURE SCHEMAS (MILESTONE 3)
# ============================================================================

class RootCauseFinding(BaseModel):
    """Isolated internal operational failure root cause with grounded citations."""
    cause_id: str = Field(default="RC-INT-001", description="Unique root cause identifier")
    title: str = Field(..., description="Short descriptive headline of failure mode")
    category: str = Field(default="LOGISTICS", description="Operational category (INFRASTRUCTURE, LOGISTICS, PAYMENT, CATALOG)")
    severity: str = Field(default="HIGH", description="Severity classification: CRITICAL, HIGH, MEDIUM, LOW")
    affected_systems: List[str] = Field(default_factory=list, description="List of system/component IDs affected")
    affected_skus: List[str] = Field(default_factory=list, description="SKU IDs impacted by operational bottleneck")
    evidence_citations: List[str] = Field(default_factory=list, description="Grounding citations (e.g. JIRA-4819, WH-WEST-01)")
    citations: List[str] = Field(default_factory=list, description="Alias for evidence_citations")
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Confidence in this root cause (0.0 to 1.0)")
    confidence: Optional[float] = Field(default=None, description="Alias for confidence_score")
    estimated_internal_share_pct: float = Field(default=30.0, ge=0.0, le=100.0, description="Share % of internal attribution")
    share_pct: Optional[float] = Field(default=None, description="Alias for estimated_internal_share_pct")
    description: str = Field(default="", description="Detailed narrative description of operational issue")

    def model_post_init(self, __context: Any) -> None:
        if not self.citations and self.evidence_citations:
            self.citations = list(self.evidence_citations)
        elif not self.evidence_citations and self.citations:
            self.evidence_citations = list(self.citations)
        if self.confidence is None:
            self.confidence = self.confidence_score
        if self.share_pct is None:
            self.share_pct = self.estimated_internal_share_pct

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class InternalDiagnosticInput(BaseModel):
    """Input payload for Model 1 Internal Diagnostic Engine."""
    scenario_id: str = Field(default="scenario_1", description="Scenario identifier")
    kpi_name: str = Field(default="Gross Revenue", description="Evaluated KPI name")
    anomaly_timestamp: Optional[Union[datetime, str]] = Field(default=None, description="Timestamp of detected anomaly")
    tree_attribution: Dict[str, float] = Field(default_factory=dict, description="Causal metric tree factor percentages")
    tickets: List[SupportJiraRecord] = Field(default_factory=list, description="Support & Jira ticket records")
    unfulfilled_orders: int = Field(default=0, ge=0, description="Count of backlogged or delayed orders")
    delayed_revenue: float = Field(default=0.0, ge=0.0, description="Gross revenue delayed in backlogged orders")
    backlog: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed ERP backlog order records")


class InternalDiagnosticOutput(BaseModel):
    """Structured output from Model 1 Internal Diagnostic Engine."""
    model_name: str = Field(default="Model-1-Internal-Diagnostic", description="Model name identifier")
    execution_mode: str = Field(default="DETERMINISTIC_FALLBACK", description="Execution mode: LIVE_LLM or DETERMINISTIC_FALLBACK")
    status: str = Field(default="SUCCESS", description="Diagnostic status: SUCCESS, DEGRADED, NO_INTERNAL_ANOMALY")
    primary_root_causes: List[RootCauseFinding] = Field(default_factory=list, description="Ranked list of operational root causes")
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Backward compatibility findings list")
    diagnostic_summary: str = Field(default="", description="Summary narrative of internal diagnosis")
    summary: Optional[str] = Field(default=None, description="Alias for diagnostic_summary")
    primary_internal_driver: str = Field(default="Operational_Bottleneck", description="Primary failure mode category")
    internal_confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Overall internal diagnostic confidence")
    estimated_internal_share_pct: float = Field(default=30.0, ge=0.0, le=100.0, description="Model 1 estimated internal attribution share %")
    citations: List[str] = Field(default_factory=list, description="All grounded internal citations")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Execution latency in milliseconds")
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

    def model_post_init(self, __context: Any) -> None:
        if self.summary is None:
            self.summary = self.diagnostic_summary
        elif not self.diagnostic_summary:
            self.diagnostic_summary = self.summary

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class MacroSignalFeed(BaseModel):
    """External market, logistics, weather, or competitor signal feed."""
    feed_id: str = Field(..., description="Unique feed/signal identifier")
    source: str = Field(default="MarketIntelligence", description="Signal source name")
    timestamp: Optional[Union[datetime, str]] = Field(default=None, description="Signal observation timestamp")
    event_name: str = Field(default="External Event", description="Name of external shock event")
    headline: str = Field(default="", description="Headline summary of market event")
    region: str = Field(default="GLOBAL", description="Geographic or market region affected")
    signal_type: str = Field(default="SUPPLY_CHAIN", description="Signal category: SUPPLY_CHAIN, COMPETITOR_PRICING, MACRO_ECONOMIC, WEATHER")
    severity_index: float = Field(default=5.0, ge=0.0, le=10.0, description="Severity score on 0-10 scale")
    severity: Optional[str] = Field(default=None, description="Categorical severity: CRITICAL, HIGH, MODERATE, LOW")
    confidence: Optional[float] = Field(default=None, description="Feed source confidence score")
    raw_snippet: Optional[str] = Field(default=None, description="Verbatim quote or excerpt from feed")

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class MacroShockAssessment(BaseModel):
    """Quantified assessment of an external macro shock."""
    shock_id: str = Field(default="SHOCK-EXT-001", description="Unique macro shock identifier")
    event_name: str = Field(..., description="Name of macro shock event")
    impact_mechanism: str = Field(..., description="Causal economic/logistical transmission mechanism")
    severity: str = Field(default="HIGH", description="Macro severity: CRITICAL, HIGH, MODERATE, LOW")
    confidence_score: float = Field(default=0.88, ge=0.0, le=1.0, description="Confidence in macro shock attribution")
    estimated_external_share_pct: float = Field(default=70.0, ge=0.0, le=100.0, description="External attribution share %")
    external_citations: List[str] = Field(default_factory=list, description="External signal feed citations")
    citations: List[str] = Field(default_factory=list, description="Alias for external_citations")

    def model_post_init(self, __context: Any) -> None:
        if not self.citations and self.external_citations:
            self.citations = list(self.external_citations)
        elif not self.external_citations and self.citations:
            self.external_citations = list(self.citations)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class MacroSentinelInput(BaseModel):
    """Input payload for Model 2 Macro Sentinel Engine."""
    scenario_id: str = Field(default="scenario_1", description="Scenario identifier")
    kpi_name: str = Field(default="Gross Revenue", description="Evaluated KPI name")
    anomaly_period: Optional[str] = Field(default=None, description="Timeframe or date of anomaly")
    observed_drop_pct: float = Field(default=0.0, description="Percentage change in primary KPI")
    macro_feeds: List[MacroSignalFeed] = Field(default_factory=list, description="List of external signal feeds")


class MacroSentinelOutput(BaseModel):
    """Structured output from Model 2 Macro Sentinel Engine."""
    model_name: str = Field(default="Model-2-Macro-Sentinel", description="Model identifier")
    execution_mode: str = Field(default="DETERMINISTIC_FALLBACK", description="LIVE_LLM or DETERMINISTIC_FALLBACK")
    status: str = Field(default="EXTERNAL_SHOCK_DETECTED", description="Status: EXTERNAL_SHOCK_DETECTED, NO_MACRO_IMPACT")
    macro_shocks: List[MacroShockAssessment] = Field(default_factory=list, description="List of quantified external shocks")
    macro_signals: List[Dict[str, Any]] = Field(default_factory=list, description="Raw or normalized signal feeds")
    macro_share_pct: float = Field(default=70.0, ge=0.0, le=100.0, description="Estimated external macro share %")
    external_confidence: float = Field(default=0.88, ge=0.0, le=1.0, description="Confidence in external assessment")
    confidence_score: float = Field(default=0.88, ge=0.0, le=1.0, description="Alias for external_confidence")
    top_external_shock: str = Field(default="West Coast Port Labor Slowdown", description="Primary external shock headline")
    external_severity: str = Field(default="HIGH", description="Severity level of top shock")
    market_impact_summary: str = Field(default="", description="Narrative summary of market/macro impact")
    sentinel_summary: Optional[str] = Field(default=None, description="Alias for market_impact_summary")
    citations: List[str] = Field(default_factory=list, description="External citation IDs")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Execution latency in milliseconds")
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

    def model_post_init(self, __context: Any) -> None:
        if self.sentinel_summary is None:
            self.sentinel_summary = self.market_impact_summary
        elif not self.market_impact_summary:
            self.market_impact_summary = self.sentinel_summary

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class RankedHypothesis(BaseModel):
    """Ranked competing hypothesis under ambiguity."""
    rank: int = Field(..., ge=1, description="Hypothesis rank (1 = most likely)")
    name: str = Field(default="", description="Descriptive title of hypothesis")
    hypothesis: Optional[str] = Field(default=None, description="Alias for name")
    likelihood_pct: float = Field(..., ge=0.0, le=100.0, description="Estimated likelihood percentage")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence score")
    evidence_basis: Optional[str] = Field(default=None, description="Key supporting evidence string")
    supporting_evidence: Optional[str] = Field(default=None, description="Detailed supporting evidence")
    counter_evidence: Optional[str] = Field(default=None, description="Counter-evidence or conflicting observation")

    def model_post_init(self, __context: Any) -> None:
        if not self.name and self.hypothesis:
            self.name = self.hypothesis
        elif not self.hypothesis and self.name:
            self.hypothesis = self.name
        if self.confidence_score is None:
            self.confidence_score = self.likelihood_pct / 100.0

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class CanaryValidationTest(BaseModel):
    """Prescribed low-cost, low-risk canary experiment to resolve ambiguity."""
    test_id: str = Field(default="CANARY-01", description="Unique test identifier")
    name: str = Field(default="", description="Title of canary test")
    title: Optional[str] = Field(default=None, description="Alias for name")
    test_name: Optional[str] = Field(default=None, description="Alias for name")
    estimated_cost_usd: float = Field(default=150.0, ge=0.0, description="Estimated execution cost in USD")
    cost_usd: Optional[float] = Field(default=None, description="Alias for estimated_cost_usd")
    duration_hours: float = Field(default=2.0, ge=0.0, description="Execution duration in hours")
    runtime_hours: Optional[float] = Field(default=None, description="Alias for duration_hours")
    objective: Optional[str] = Field(default=None, description="Target validation objective")
    description: Optional[str] = Field(default=None, description="Detailed step-by-step execution guide")
    decision_gate: Optional[str] = Field(default=None, description="Decision criterion gate")

    def model_post_init(self, __context: Any) -> None:
        if not self.name:
            self.name = self.title or self.test_name or "Canary Test"
        if not self.title:
            self.title = self.name
        if not self.test_name:
            self.test_name = self.name
        if self.cost_usd is None:
            self.cost_usd = self.estimated_cost_usd
        if self.runtime_hours is None:
            self.runtime_hours = self.duration_hours

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class AbstentionResult(BaseModel):
    """Output from the Ambiguity & Explicit Abstention Engine."""
    is_abstaining: bool = Field(..., description="True if engine explicitly abstains from definitive attribution")
    status: str = Field(default="ABSTAINED", description="Status: ABSTAINED or CONFIDENT")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Aggregated calibrated confidence score")
    message: Optional[str] = Field(default=None, description="Explanatory message for user")
    abstention_reason: Optional[str] = Field(default=None, description="Detailed rationale for abstention")
    ranked_hypotheses: List[RankedHypothesis] = Field(default_factory=list, description="Ranked competing hypotheses")
    canary_validation_tests: List[CanaryValidationTest] = Field(default_factory=list, description="Prescribed canary validation tests")
    canary_tests: List[CanaryValidationTest] = Field(default_factory=list, description="Alias for canary_validation_tests")

    def model_post_init(self, __context: Any) -> None:
        if not self.canary_tests and self.canary_validation_tests:
            self.canary_tests = list(self.canary_validation_tests)
        elif not self.canary_validation_tests and self.canary_tests:
            self.canary_validation_tests = list(self.canary_tests)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class ActionItem(BaseModel):
    """Actionable prescriptive intervention item."""
    action_id: str = Field(default="ACT-001", description="Unique action identifier")
    title: str = Field(..., description="Action headline")
    owner_role: str = Field(default="Operations Lead", description="Accountable persona / team")
    priority: str = Field(default="P1 - HIGH", description="Priority level (P0 - IMMEDIATE, P1 - HIGH, P2 - MEDIUM)")
    estimated_cost_usd: float = Field(default=0.0, ge=0.0, description="Implementation cost in USD")
    expected_recovery_usd: float = Field(default=0.0, ge=0.0, description="Projected gross revenue recovery")
    net_roi_pct: float = Field(default=0.0, description="Expected net ROI percentage")
    controllable_lever: str = Field(default="Operational capacity", description="Business lever the owner can control")
    expected_impact_usd: float = Field(default=0.0, ge=0.0, description="Expected measurable financial impact")
    confidence_score: float = Field(default=0.75, ge=0.0, le=1.0, description="Confidence in expected action outcome")
    decision_rights: str = Field(default="Owner approval required", description="Decision authority required to execute")
    constraints: List[str] = Field(default_factory=list, description="Budget, risk, policy or timing constraints")
    monitoring_plan: List[str] = Field(default_factory=list, description="Post-action monitoring checks")
    execution_steps: List[str] = Field(default_factory=list, description="Step-by-step playbook actions")

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class TrajectoryPoint(BaseModel):
    """Single day evaluation point along 30/60/90-day trajectory curves."""
    day: int = Field(..., ge=0, le=90, description="Day index (0 to 90)")
    status_quo_revenue: float = Field(..., ge=0.0, description="Daily revenue under do-nothing status quo ($)")
    recommended_revenue: float = Field(..., ge=0.0, description="Daily revenue under recommended strategy ($)")
    constrained_revenue: float = Field(..., ge=0.0, description="Daily revenue under executive constrained strategy ($)")
    status_quo: Optional[float] = Field(default=None, description="Alias for status_quo_revenue")
    prescribed: Optional[float] = Field(default=None, description="Alias for recommended_revenue")
    recommended: Optional[float] = Field(default=None, description="Alias for recommended_revenue")
    constrained: Optional[float] = Field(default=None, description="Alias for constrained_revenue")
    lower_bound_95: Optional[float] = Field(default=None, description="95% confidence lower bound")
    upper_bound_95: Optional[float] = Field(default=None, description="95% confidence upper bound")

    def model_post_init(self, __context: Any) -> None:
        if self.status_quo is None:
            self.status_quo = self.status_quo_revenue
        if self.prescribed is None:
            self.prescribed = self.recommended_revenue
        if self.recommended is None:
            self.recommended = self.recommended_revenue
        if self.constrained is None:
            self.constrained = self.constrained_revenue

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

TrajectoryCurvePoint = TrajectoryPoint


class PrescriptiveSimulationOutput(BaseModel):
    """Comprehensive multi-factor synthesis, trajectory simulation, and persona action brief."""
    model_name: str = Field(default="Model-3-Prescriptive-Action", description="Model name")
    scenario_id: str = Field(default="scenario_1", description="Scenario identifier")
    active_persona: UserRole = Field(default=UserRole.EXECUTIVE, description="Active RBAC persona")
    headline: str = Field(default="", description="Primary narrative headline")
    narrative: str = Field(default="", description="Synthesis narrative paragraph")
    synthesis_headline: Optional[str] = Field(default=None, description="Alias for headline")
    attribution_internal_pct: float = Field(default=30.0, ge=0.0, le=100.0, description="Internal operational attribution %")
    attribution_external_pct: float = Field(default=70.0, ge=0.0, le=100.0, description="External macro attribution %")
    combined_attribution_breakdown: Dict[str, float] = Field(default_factory=dict, description="Detailed driver breakdown")
    is_abstaining: bool = Field(default=False, description="Whether engine abstained due to ambiguity")
    overall_confidence: float = Field(default=0.88, ge=0.0, le=1.0, description="Calibrated confidence score")
    abstention_details: Optional[Dict[str, Any]] = Field(default=None, description="Abstention hypotheses & canary tests")
    ranked_hypotheses: List[RankedHypothesis] = Field(default_factory=list, description="Ranked competing hypotheses")
    canary_validation_tests: List[CanaryValidationTest] = Field(default_factory=list, description="Canary validation tests")
    action_playbook: List[Any] = Field(default_factory=list, description="Persona-tailored action items or steps")
    structured_action_playbook: List[ActionItem] = Field(default_factory=list, description="Governed driver-to-action contract with owner, confidence and monitoring")
    trajectory_points: List[TrajectoryPoint] = Field(default_factory=list, description="91-day daily trajectory points (0 to 90)")
    trajectory: List[Dict[str, Any]] = Field(default_factory=list, description="Milestone keyframe trajectory points (0, 30, 60, 90)")
    summary_roi_metrics: Dict[str, Any] = Field(default_factory=dict, description="Summary ROI metrics across horizons")
    estimated_roi_multiplier: float = Field(default=4.2, ge=0.0, description="Gross recovery / cost ROI multiplier")
    net_roi_usd: float = Field(default=0.0, description="Net ROI dollar amount over 90 days")
    roi_ratio: float = Field(default=0.0, description="Net ROI ratio multiplier")
    trajectory_30: float = Field(default=0.0, description="Projected day-30 daily revenue ($)")
    trajectory_60: float = Field(default=0.0, description="Projected day-60 daily revenue ($)")
    trajectory_90: float = Field(default=0.0, description="Projected day-90 daily revenue ($)")
    payback_period_days: Optional[float] = Field(default=None, description="Days to recover intervention cost")
    user_role: Optional[str] = Field(default=None, description="String representation of persona")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Execution latency in milliseconds")
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

    def model_post_init(self, __context: Any) -> None:
        if self.synthesis_headline is None:
            self.synthesis_headline = self.headline
        elif not self.headline:
            self.headline = self.synthesis_headline
        if self.user_role is None:
            self.user_role = self.active_persona.value if hasattr(self.active_persona, "value") else str(self.active_persona)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class ScenarioExecutionResult(BaseModel):
    """End-to-end execution result for a complete scenario run."""
    scenario_id: str = Field(..., description="Scenario identifier (e.g. scenario_1)")
    persona: UserRole = Field(default=UserRole.EXECUTIVE, description="Persona role used during run")
    user_role: Optional[str] = Field(default=None, description="String representation of active persona")
    kpi_summary: Optional[Dict[str, Any]] = Field(default=None, description="Reconciled KPI summary metrics")
    spc_result: Optional[SPCResult] = Field(default=None, description="SPC anomaly detection result")
    tree_result: Optional[TreeDecompositionResult] = Field(default=None, description="Exact Causal Tree decomposition")
    synthesis_result: Optional[PrescriptiveSimulationOutput] = Field(default=None, description="3-Model AI synthesis & simulation")
    prescriptive_output: Optional[PrescriptiveSimulationOutput] = Field(default=None, description="Alias for synthesis_result")
    masked_erp_data: Optional[Any] = Field(default=None, description="RBAC-masked ERP transactions DataFrame/records")
    telemetry: Optional[TelemetryRecord] = Field(default=None, description="Full end-to-end telemetry record")
    materiality_report: Optional[Dict[str, Any]] = Field(default=None, description="Deterministic KPI materiality and prioritisation report")
    data_health: Optional[List[Dict[str, Any]]] = Field(default=None, description="Source freshness, grain and quality health records")
    learning_summary: Optional[Dict[str, Any]] = Field(default=None, description="Feedback calibration and learning-loop summary")

    def model_post_init(self, __context: Any) -> None:
        if self.prescriptive_output is None:
            self.prescriptive_output = self.synthesis_result
        elif self.synthesis_result is None:
            self.synthesis_result = self.prescriptive_output
        if self.user_role is None:
            self.user_role = self.persona.value if hasattr(self.persona, "value") else str(self.persona)

    def __getitem__(self, item: str) -> Any:
        if item == "prescriptive_output":
            return self.synthesis_result or self.prescriptive_output
        elif item == "user_role":
            return self.user_role or (self.persona.value if hasattr(self.persona, "value") else str(self.persona))
        return getattr(self, item)


