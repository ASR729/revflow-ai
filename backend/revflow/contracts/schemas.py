"""
RevFlow API Schemas — generated from 00_CONTRACTS_RevFlow.md §7.

Pydantic request/response models for all ten endpoints.
"""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

from revflow.contracts.enums import (
    EventType,
    Cause,
    Action,
    LadderStep,
    Outcome,
    RuleFired,
    CauseSource,
    SimulatedChannel,
    Locale,
    PTPStatus,
    BatchRunStatus,
)


# ─── Shared models ────────────────────────────────────────────────────────────


class RunID(BaseModel):
    run_id: str = Field(pattern=r"^RUN-\d{8}T\d{6}$")


class EventID(BaseModel):
    event_id: str = Field(pattern=r"^EVT-\d{4}$")


class CustomerID(BaseModel):
    customer_id: str = Field(pattern=r"^CUST-\d{4}$")


class AmountINR(BaseModel):
    amount_inr: float = Field(ge=0, description="Amount in rupees, 2 decimal places")


# ─── 1. GET /health ───────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    db: Literal["connected"]
    razorpay_mode: Literal["test"]

    model_config = ConfigDict(json_schema_extra={
        "example": {"status": "ok", "version": "0.1.0", "db": "connected", "razorpay_mode": "test"}
    })


# ─── 2. POST /run-batch ───────────────────────────────────────────────────────


class RunBatchRequest(BaseModel):
    use_llm: bool = True
    regenerate_dataset: bool = True


class RunBatchResponse(BaseModel):
    run_id: str = Field(pattern=r"^RUN-\d{8}T\d{6}$")
    status: Literal["running"]
    poll: Literal["/runs"]


# ─── 3. GET /runs ─────────────────────────────────────────────────────────────


class BatchRunRow(BaseModel):
    run_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: BatchRunStatus
    event_count: int
    llm_call_count: int
    random_seed: int
    notes: Optional[str] = None


class RunsResponse(BaseModel):
    runs: list[BatchRunRow]


# ─── 4. GET /metrics ──────────────────────────────────────────────────────────


class AmountsINR(BaseModel):
    at_risk: float
    addressable: float
    realised_recovered: float
    simulated_outreach: float
    deferred: float
    withheld: float
    escalated: float


class Rates(BaseModel):
    recovery_rate_realised: Optional[float] = None
    addressable_coverage: float
    retry_success_rate: Optional[float] = None


class PipelineMetrics(BaseModel):
    event_count: int
    at_risk_inr: float
    addressable_inr: float
    realised_recovered_inr: float
    recovery_rate_realised: Optional[float] = None


class ByPipeline(BaseModel):
    checkout_dropoff: PipelineMetrics
    subscription_failure: PipelineMetrics
    b2b_receivable: PipelineMetrics


class Boundedness(BaseModel):
    withheld_count: int
    escalated_count: int
    deterministic_share: float
    llm_call_count: int
    llm_call_budget: int
    out_of_bounds_action_count: int
    missing_rationale_count: int
    p95_decision_latency_ms: int


class Integrity(BaseModel):
    false_positive_count: int
    false_positive_cost_inr: float
    harassment_incident_count: int
    over_retry_count: int


class ActionBreakdown(BaseModel):
    retry_now: int
    retry_later: int
    nudge: int
    escalate_to_human: int
    stop: int


class OutcomeBreakdown(BaseModel):
    recovered: int
    failed: int
    api_error: int
    simulated: int
    pending: int
    paused: int
    escalated: int
    withheld: int


class MetricsResponse(BaseModel):
    run_id: str
    generated_at: str
    random_seed: int
    llm_mode: Literal["live", "cached", "disabled"]
    event_count: int
    amounts_inr: AmountsINR
    rates: Rates
    by_pipeline: ByPipeline
    boundedness: Boundedness
    integrity: Integrity
    action_breakdown: ActionBreakdown
    outcome_breakdown: OutcomeBreakdown


# ─── 5. GET /classifier-metrics ───────────────────────────────────────────────


class CauseMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    support: int


class OverallMetrics(BaseModel):
    accuracy: float
    macro_precision: float
    macro_recall: float
    support: int


class BySourceMetrics(BaseModel):
    rule: dict[str, float | int]
    llm: dict[str, float | int]


class ConfusionPair(BaseModel):
    true_cause: str
    predicted_cause: str
    count: int


class ClassifierMetricsResponse(BaseModel):
    run_id: str
    generated_at: str
    overall: OverallMetrics
    by_cause: dict[str, CauseMetrics]
    by_source: BySourceMetrics
    confusion_pairs: list[ConfusionPair]


# ─── 6. GET /audit-log ────────────────────────────────────────────────────────


class AuditLogQuery(BaseModel):
    run_id: Optional[str] = None
    event_type: Optional[EventType] = None
    cause: Optional[Cause] = None
    action: Optional[Action] = None
    sort: Literal["amount", "cause", "timestamp"] = "timestamp"
    order: Literal["asc", "desc"] = "desc"
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class AuditLogRow(BaseModel):
    id: int
    run_id: str
    event_id: str
    event_type: EventType
    cause: Cause
    cause_source: CauseSource
    rule_fired: RuleFired
    action: Action
    ladder_step: LadderStep
    rationale: str
    outcome: Outcome
    amount_inr: float
    attributed_recovery_inr: float
    is_simulated: int
    llm_calls_used: int
    latency_ms: int
    created_at: str
    customer_id: str
    decline_code: Optional[str] = None
    simulated_channel: Optional[SimulatedChannel] = None


class AuditLogResponse(BaseModel):
    run_id: str
    total: int
    limit: int
    offset: int
    rows: list[AuditLogRow]


# ─── 7. GET /exceptions ───────────────────────────────────────────────────────


class ExceptionRow(BaseModel):
    id: int
    run_id: str
    event_id: str
    event_type: EventType
    cause: Cause
    cause_source: CauseSource
    rule_fired: RuleFired
    action: Action
    ladder_step: LadderStep
    rationale: str
    outcome: Outcome
    amount_inr: float
    attributed_recovery_inr: float
    is_simulated: int
    llm_calls_used: int
    latency_ms: int
    created_at: str
    customer_id: str
    decline_code: Optional[str] = None
    simulated_channel: Optional[SimulatedChannel] = None


class ExceptionsResponse(BaseModel):
    run_id: str
    withheld_by_policy: list[ExceptionRow]
    needs_a_human: list[ExceptionRow]


# ─── 8. GET /events/{event_id} ────────────────────────────────────────────────


class EventRow(BaseModel):
    event_id: str
    run_id: str
    event_type: EventType
    amount_inr: int
    currency: str
    customer_id: str
    decline_code: Optional[str] = None
    decline_message: Optional[str] = None
    true_cause: Optional[str] = None  # Only in synthetic data, omitted from API response
    retry_count: int
    last_attempt_at: Optional[str] = None
    paused_until: Optional[str] = None
    ladder_step: LadderStep
    invoice_issued_at: Optional[str] = None
    invoice_due_date: Optional[str] = None
    session_started_at: Optional[str] = None
    checkout_resume_token: Optional[str] = None
    customer_reply_text: Optional[str] = None
    created_at: str


class SimulatedActionRow(BaseModel):
    id: int
    audit_log_id: int
    channel: SimulatedChannel
    locale: Locale
    body_text: str
    tts_audio_path: Optional[str] = None
    status: Literal["simulated"]
    created_at: str


class EscalationRow(BaseModel):
    id: int
    audit_log_id: int
    reason: str
    ladder_step: LadderStep
    queue: Literal["ops_review", "finance_review"]
    created_at: str


class PTPCommitmentRow(BaseModel):
    id: int
    run_id: str
    event_id: str
    promised_date: str
    detected_from_text: str
    detection_source: CauseSource
    status: PTPStatus
    ladder_step_at_pause: LadderStep
    created_at: str


class EventDetailResponse(BaseModel):
    event: EventRow
    timeline: list[AuditLogRow]
    simulated_actions: list[SimulatedActionRow]
    escalations: list[EscalationRow]
    ptp_commitments: list[PTPCommitmentRow]


# ─── 9. GET /config ───────────────────────────────────────────────────────────


class ConfigResponse(BaseModel):
    MAX_RETRIES: int
    COOLDOWN_HOURS: int
    RETRY_BACKOFF_HOURS: list[int]
    CHECKOUT_SESSION_WINDOW_MINUTES: int
    MAX_CONTACTS_PER_CUSTOMER_PER_DAY: int
    STOP_IF_CAUSE_IN: list[str]
    LADDER_GENTLE_AFTER_DAYS: int
    LADDER_FIRM_AFTER_DAYS: int
    LADDER_FLAG_AFTER_DAYS: int
    PTP_GRACE_DAYS: int
    LLM_CALL_BUDGET_PER_RUN: int
    LLM_MAX_ATTEMPTS: int
    LLM_TIMEOUT_SECONDS: int
    BATCH_SIZE: int
    RANDOM_SEED: int
    DECISION_LATENCY_BUDGET_MS: int
    editable: bool = False
    note: str = "Global ceiling, not per-merchant in Phase 0"


# ─── 10. POST /webhook ────────────────────────────────────────────────────────


class WebhookRequest(BaseModel):
    # Razorpay webhook payload shape - flexible to accept test mode events
    event: str
    payload: dict


class WebhookResponse(BaseModel):
    event_id: str = Field(pattern=r"^EVT-\d{4}$")
    run_id: str = Field(pattern=r"^RUN-WEBHOOK-\d{8}$")
    accepted: bool = True