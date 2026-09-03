"""
RevFlow FastAPI Application — main entry point.

Implements:
- CORS configuration for frontend at localhost:3000
- Startup assertions (Razorpay test mode)
- /health endpoint per §7.1
- All ten API endpoints per §7 with real implementations
"""
import re
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables from .env
load_dotenv()

from revflow.contracts.config import ALL_CONFIG
from revflow.contracts.schemas import (
    HealthResponse,
    RunBatchRequest,
    RunBatchResponse,
    BatchRunRow,
    RunsResponse,
    MetricsResponse,
    ClassifierMetricsResponse,
    AuditLogQuery,
    AuditLogResponse,
    ExceptionsResponse,
    EventDetailResponse,
    ConfigResponse,
    WebhookRequest,
    WebhookResponse,
)
from revflow.contracts.enums import (
    EventType, Cause, Action, LadderStep, Outcome, RuleFired,
    CauseSource, SimulatedChannel, Locale, PTPStatus, BatchRunStatus
)

# ─── Startup assertions ───────────────────────────────────────────────────────


def assert_test_mode() -> None:
    """
    Mandatory startup assertion: RAZORPAY_KEY_ID must match ^rzp_test_.
    Per §8.3: raises and halts the process unless the key is a test key.
    No override flag and no environment variable disables this check.
    """
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    if not re.match(r"^rzp_test_", key_id):
        raise RuntimeError(
            f"RAZORPAY_KEY_ID must be a Razorpay Test Mode key (match ^rzp_test_). "
            f"Got: {key_id[:20]}... (truncated)"
        )


def get_db_status() -> str:
    """Check database connectivity."""
    try:
        from revflow.db.connection import get_connection
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return "connected"
    except Exception:
        return "disconnected"


# ─── Application lifecycle ────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    assert_test_mode()
    # Verify .env has required keys (don't log secrets)
    required = ["RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "LLM_PROVIDER", "LLM_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")
    yield
    # Shutdown (if needed)


# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="RevFlow API",
    version="0.1.0",
    description="AI-Powered Revenue Recovery Orchestration",
    lifespan=lifespan,
)

# CORS — must allow http://localhost:3000 per §7
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Health endpoint (§7.1) ──────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """
    Liveness check.
    Returns 200 with status, version, db, and razorpay_mode.
    razorpay_mode MUST read "test" — guaranteed by assert_test_mode().
    """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        db=get_db_status(),
        razorpay_mode="test",
    )


# ─── Debug endpoint ─────────────────────────────────────────────────────────────


@app.get("/debug/db-path", tags=["debug"])
async def debug_db_path():
    """Debug endpoint to check database path."""
    from revflow.db.connection import get_db_path, get_connection
    with get_connection() as conn:
        result = conn.execute("PRAGMA database_list").fetchall()
        runs = conn.execute("SELECT run_id, status FROM batch_runs").fetchall()
        return {
            "db_path": get_db_path(),
            "database_list": [dict(r) for r in result],
            "runs": [dict(r) for r in runs],
        }


# ─── Run Batch endpoint (§7.2) ───────────────────────────────────────────────


@app.post("/run-batch", response_model=RunBatchResponse, status_code=202, tags=["batch"])
async def run_batch(request: RunBatchRequest, background_tasks: BackgroundTasks) -> RunBatchResponse:
    """
    Trigger a batch run. Returns 202 Accepted immediately.
    Runs the pipeline in a background task.
    """
    from scripts.run_batch import BatchRunner

    run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    # Check for concurrent run
    from revflow.db.connection import get_connection
    with get_connection() as conn:
        running = conn.execute(
            "SELECT 1 FROM batch_runs WHERE status = 'running' LIMIT 1"
        ).fetchone()
        if running:
            raise HTTPException(status_code=409, detail="A batch run is already in progress")

    # Create batch_run record
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO batch_runs (run_id, started_at, status, event_count, llm_call_count, random_seed, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                datetime.now(timezone.utc).isoformat(),
                "running",
                0,  # Will be updated after loading events
                0,
                42,
                "--no-llm" if not request.use_llm else "",
            ),
        )

    # Start background task
    background_tasks.add_task(
        BatchRunner(run_id, use_llm=request.use_llm, regenerate_dataset=request.regenerate_dataset).run
    )

    return RunBatchResponse(run_id=run_id, status="running", poll="/runs")


# ─── List Runs endpoint (§7.3) ───────────────────────────────────────────────


@app.get("/runs", response_model=RunsResponse, tags=["batch"])
async def list_runs() -> RunsResponse:
    """
    List all batch runs, newest first.
    """
    from revflow.db.connection import get_connection
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM batch_runs ORDER BY started_at DESC"
        ).fetchall()

        runs = [
            BatchRunRow(
                run_id=r["run_id"],
                started_at=r["started_at"],
                completed_at=r["completed_at"],
                status=BatchRunStatus(r["status"]),
                event_count=r["event_count"],
                llm_call_count=r["llm_call_count"],
                random_seed=r["random_seed"],
                notes=r["notes"],
            )
            for r in rows
        ]

    return RunsResponse(runs=runs)


# ─── Metrics endpoint (§7.4) ─────────────────────────────────────────────────


@app.get("/metrics", response_model=MetricsResponse, tags=["metrics"])
async def get_metrics(run_id: str | None = None) -> MetricsResponse:
    """
    Get summary metrics for a run.
    Defaults to most recent completed run.
    """
    from revflow.metrics.summary import compute_summary_metrics
    from revflow.db.connection import get_connection

    # Determine run_id
    if run_id is None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT run_id FROM batch_runs WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 1"
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="no completed runs")
            run_id = row["run_id"]

    # Compute metrics (will also write to file)
    metrics = compute_summary_metrics(run_id, llm_mode="live")
    return MetricsResponse(**metrics)


# ─── Classifier Metrics endpoint (§7.5) ──────────────────────────────────────


@app.get("/classifier-metrics", response_model=ClassifierMetricsResponse, tags=["metrics"])
async def get_classifier_metrics(run_id: str | None = None) -> ClassifierMetricsResponse:
    """
    Get classifier precision/recall metrics for a run.
    """
    from revflow.classifier.eval import evaluate_classifier
    from revflow.db.connection import get_connection

    if run_id is None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT run_id FROM batch_runs WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 1"
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="no classifier metrics available")
            run_id = row["run_id"]

    metrics = evaluate_classifier(run_id)
    return ClassifierMetricsResponse(**metrics)


# ─── Audit Log endpoint (§7.6) ───────────────────────────────────────────────


@app.get("/audit-log", response_model=AuditLogResponse, tags=["audit"])
async def get_audit_log(
    run_id: str | None = None,
    event_type: str | None = None,
    cause: str | None = None,
    action: str | None = None,
    sort: str = "timestamp",
    order: str = "desc",
    limit: int = 100,
    offset: int = 0,
) -> AuditLogResponse:
    """
    Get paginated, filterable audit log.
    """
    from revflow.db.ledger import get_audit_log_rows
    from revflow.db.connection import get_connection

    # Validate enum values if provided
    if event_type and event_type not in [e.value for e in EventType]:
        raise HTTPException(status_code=422, detail=f"Invalid event_type: {event_type}")
    if cause and cause not in [c.value for c in Cause]:
        raise HTTPException(status_code=422, detail=f"Invalid cause: {cause}")
    if action and action not in [a.value for a in Action]:
        raise HTTPException(status_code=422, detail=f"Invalid action: {action}")

    # Default to most recent completed run
    if run_id is None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT run_id FROM batch_runs WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 1"
            ).fetchone()
            if row:
                run_id = row["run_id"]

    rows, total = get_audit_log_rows(
        run_id=run_id,
        event_type=event_type,
        cause=cause,
        action=action,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )

    # Convert to response format
    row_data = []
    for r in rows:
        row_data.append({
            "id": r["id"],
            "run_id": r["run_id"],
            "event_id": r["event_id"],
            "event_type": r["event_type"],
            "cause": r["cause"],
            "cause_source": r["cause_source"],
            "rule_fired": r["rule_fired"],
            "action": r["action"],
            "ladder_step": r["ladder_step"],
            "rationale": r["rationale"],
            "outcome": r["outcome"],
            "amount_inr": round(r["amount_inr"] / 100, 2),
            "attributed_recovery_inr": round(r["attributed_recovery_inr"] / 100, 2),
            "is_simulated": r["is_simulated"],
            "llm_calls_used": r["llm_calls_used"],
            "latency_ms": r["latency_ms"],
            "created_at": r["created_at"],
            "customer_id": r["customer_id"],
            "decline_code": r["decline_code"],
            "simulated_channel": r["simulated_channel"],
        })

    return AuditLogResponse(
        run_id=run_id or "",
        total=total,
        limit=limit,
        offset=offset,
        rows=row_data,
    )


# ─── Exceptions endpoint (§7.7) ──────────────────────────────────────────────


@app.get("/exceptions", response_model=ExceptionsResponse, tags=["audit"])
async def get_exceptions(run_id: str | None = None) -> ExceptionsResponse:
    """
    Get pre-grouped exceptions: withheld_by_policy (action=stop) and needs_a_human (action=escalate_to_human).
    """
    from revflow.db.ledger import get_exceptions
    from revflow.db.connection import get_connection

    if run_id is None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT run_id FROM batch_runs WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 1"
            ).fetchone()
            if row:
                run_id = row["run_id"]

    withheld, needs_human = get_exceptions(run_id)

    def convert_row(r):
        return {
            "id": r["id"],
            "run_id": r["run_id"],
            "event_id": r["event_id"],
            "event_type": r["event_type"],
            "cause": r["cause"],
            "cause_source": r["cause_source"],
            "rule_fired": r["rule_fired"],
            "action": r["action"],
            "ladder_step": r["ladder_step"],
            "rationale": r["rationale"],
            "outcome": r["outcome"],
            "amount_inr": round(r["amount_inr"] / 100, 2),
            "attributed_recovery_inr": round(r["attributed_recovery_inr"] / 100, 2),
            "is_simulated": r["is_simulated"],
            "llm_calls_used": r["llm_calls_used"],
            "latency_ms": r["latency_ms"],
            "created_at": r["created_at"],
            "customer_id": r["customer_id"],
            "decline_code": r["decline_code"],
            "simulated_channel": r["simulated_channel"],
        }

    return ExceptionsResponse(
        run_id=run_id or "",
        withheld_by_policy=[convert_row(r) for r in withheld],
        needs_a_human=[convert_row(r) for r in needs_human],
    )


# ─── Event Detail endpoint (§7.8) ────────────────────────────────────────────


@app.get("/events/{event_id}", response_model=EventDetailResponse, tags=["audit"])
async def get_event_detail(event_id: str) -> EventDetailResponse:
    """
    Get full event detail for the Event Detail Drawer.
    true_cause MUST be omitted from response.
    """
    from revflow.db.ledger import (
        get_event_detail, get_audit_timeline,
        get_simulated_actions, get_escalations, get_ptp_commitments
    )
    from revflow.db.connection import get_connection

    event = get_event_detail(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")

    timeline = get_audit_timeline(event_id)
    sim_actions = []
    escalations = []
    ptp_commitments = []

    for t in timeline:
        sim_actions.extend(get_simulated_actions(t["id"]))
        escalations.extend(get_escalations(t["id"]))
    ptp_commitments = get_ptp_commitments(event_id)

    return EventDetailResponse(
        event={
            "event_id": event["event_id"],
            "run_id": event["run_id"],
            "event_type": event["event_type"],
            "amount_inr": event["amount_inr"],
            "currency": event["currency"],
            "customer_id": event["customer_id"],
            "decline_code": event["decline_code"],
            "decline_message": event["decline_message"],
            "true_cause": None,  # Omitted per §7.8
            "retry_count": event["retry_count"],
            "last_attempt_at": event["last_attempt_at"],
            "paused_until": event["paused_until"],
            "ladder_step": event["ladder_step"],
            "invoice_issued_at": event["invoice_issued_at"],
            "invoice_due_date": event["invoice_due_date"],
            "session_started_at": event["session_started_at"],
            "checkout_resume_token": event["checkout_resume_token"],
            "customer_reply_text": event["customer_reply_text"],
            "created_at": event["created_at"],
        },
        timeline=[dict(t) for t in timeline],
        simulated_actions=[dict(s) for s in sim_actions],
        escalations=[dict(e) for e in escalations],
        ptp_commitments=[dict(p) for p in ptp_commitments],
    )


# ─── Config endpoint (§7.9) ──────────────────────────────────────────────────


@app.get("/config", response_model=ConfigResponse, tags=["config"])
async def get_config() -> ConfigResponse:
    """
    Read-only policy ceiling values.
    Returns all §4.1 constants plus editable=false and note.
    """
    return ConfigResponse(**ALL_CONFIG)


# ─── Webhook endpoint (§7.10) ────────────────────────────────────────────────


@app.post("/webhook", response_model=WebhookResponse, status_code=202, tags=["ingestion"])
async def webhook(request: WebhookRequest) -> WebhookResponse:
    """
    Single-event ingestion from Razorpay webhook.
    """
    from revflow.ingestion.normaliser import normalise_event
    from revflow.db.connection import get_connection

    now = datetime.now(timezone.utc)
    # Use date-only for RUN-WEBHOOK to match pattern ^RUN-WEBHOOK-\d{8}$
    run_id = f"RUN-WEBHOOK-{now.strftime('%Y%m%d')}"
    # Use sequential event ID within the webhook run
    event_id = f"EVT-{datetime.now(timezone.utc).strftime('%H%M')[:4]}"

    # Create batch_runs record for this webhook event (if not exists)
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT 1 FROM batch_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if not existing:
            conn.execute(
                """INSERT INTO batch_runs (run_id, started_at, status, event_count, llm_call_count, random_seed, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    datetime.now(timezone.utc).isoformat(),
                    "completed",
                    1,
                    0,
                    42,
                    "webhook ingestion",
                ),
            )

    # Normalise and insert
    event = normalise_event(request.payload, run_id, event_id)

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO events (
                event_id, run_id, event_type, amount_inr, currency, customer_id,
                decline_code, decline_message, true_cause, retry_count,
                last_attempt_at, paused_until, ladder_step,
                invoice_issued_at, invoice_due_date, session_started_at,
                checkout_resume_token, customer_reply_text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event.event_id, event.run_id, event.event_type.value, event.amount_inr,
                event.currency, event.customer_id, event.decline_code,
                event.decline_message, event.true_cause, event.retry_count,
                event.last_attempt_at, event.paused_until, event.ladder_step.value,
                event.invoice_issued_at, event.invoice_due_date, event.session_started_at,
                event.checkout_resume_token, event.customer_reply_text, event.created_at,
            ),
        )

    return WebhookResponse(event_id=event_id, run_id=run_id, accepted=True)


# ─── Import for validation ────────────────────────────────────────────────────
from revflow.contracts.enums import EventType, Cause, Action