#!/usr/bin/env python3
"""
RevFlow Batch Orchestration — run_batch.py.

Per §7.2, BE-12: Orchestrates 300-event batch run end-to-end.
Returns 202 immediately, runs in background.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

# Load environment variables from .env (project root)
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revflow.db.connection import init_db, get_connection, reset_db
from revflow.db.ledger import insert_audit_row
from revflow.ingestion.batch_loader import load_synthetic_events, insert_events
from revflow.ingestion.normaliser import Event
from revflow.classifier.rules import classify_by_rules
from revflow.classifier.llm_fallback import classify_by_llm
from revflow.policy.engine import decide_action_async
from revflow.executor.retry import execute_retry_now
from revflow.executor.simulated_comms import write_simulated_nudge
from revflow.executor.escalation import write_escalation
from revflow.ptp.tracker import detect_ptp, handle_ptp_pause, check_ptp_status
from revflow.ladder.b2b import assign_ladder_step, advance_ladder_step
from revflow.classifier.eval import write_classifier_metrics
from revflow.contracts.enums import (
    EventType, Cause, CauseSource, Action, Outcome, LadderStep, RuleFired
)
from revflow.contracts.config import BATCH_SIZE, RANDOM_SEED, LLM_CALL_BUDGET_PER_RUN
from revflow.adapters.llm import set_offline_mode


class BatchRunner:
    """Orchestrates a full batch run."""

    def __init__(self, run_id: str, use_llm: bool = True, regenerate_dataset: bool = True):
        self.run_id = run_id
        self.use_llm = use_llm
        self.regenerate_dataset = regenerate_dataset
        self.llm_calls_used = 0
        self.events: List[Event] = []
        self.started_at = datetime.now(timezone.utc)

    async def run(self) -> dict:
        """Execute the full batch pipeline."""
        print(f"[{self.run_id}] Starting batch run...")

        # Enable offline mode if LLM is disabled
        if not self.use_llm:
            set_offline_mode(True)
            print("  Offline mode enabled (LLM disabled)")

        try:
            # Step 1: Load/regenerate dataset
            if self.regenerate_dataset:
                from scripts.generate_dataset import main as generate_main
                print("  Generating dataset...")
                generate_main()

            self.events = load_synthetic_events(self.run_id)
            print(f"  Loaded {len(self.events)} events")

            # Step 2: Insert events and batch_run record
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO batch_runs (
                        run_id, started_at, status, event_count, llm_call_count, random_seed, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        self.run_id,
                        self.started_at.isoformat(),
                        "running",
                        len(self.events),
                        0,
                        RANDOM_SEED,
                        "--no-llm" if not self.use_llm else "",
                    ),
                )

            # Assign globally unique event_ids (per run_id)
            run_suffix = self.run_id.replace("RUN-", "").replace("T", "").replace(":", "")[-10:]
            for i, event in enumerate(self.events):
                event.event_id = f"EVT-{run_suffix}-{i+1:04d}"

            insert_events(self.events)
            print("  Events inserted")

            # Step 3: Process each event through the pipeline
            for i, event in enumerate(self.events):
                if i % 50 == 0:
                    print(f"  Processing event {i+1}/{len(self.events)}...")

                await self._process_event(event)

            # Step 4: Finalize run
            completed_at = datetime.now(timezone.utc)
            with get_connection() as conn:
                conn.execute(
                    "UPDATE batch_runs SET completed_at = ?, status = ?, llm_call_count = ? WHERE run_id = ?",
                    (completed_at.isoformat(), "completed", self.llm_calls_used, self.run_id)
                )

            # Step 5: Compute metrics
            write_classifier_metrics(self.run_id)
            self._compute_summary_metrics()

            print(f"[{self.run_id}] Completed successfully!")
            return {"status": "completed", "events_processed": len(self.events)}

        except Exception as e:
            # Mark run as failed
            with get_connection() as conn:
                conn.execute(
                    "UPDATE batch_runs SET status = ?, notes = ? WHERE run_id = ?",
                    ("failed", f"Error: {str(e)[:500]}", self.run_id)
                )
            print(f"[{self.run_id}] FAILED: {e}")
            raise

    async def _process_event(self, event: Event) -> None:
        """Process a single event through classifier → policy → executor."""
        from revflow.contracts.enums import CauseSource, Action, Outcome, RuleFired, LadderStep
        run_date = datetime.now(timezone.utc)

        # ─── PTP Detection (NEW PTPs from customer_reply_text) ──────────────
        # Per §4.4: If customer_reply_text is non-null, run PTP detection
        # This must happen BEFORE policy engine Stage 2b so the pause is registered
        if event.customer_reply_text:
            from revflow.ptp.tracker import detect_ptp, handle_ptp_pause, check_ptp_status
            promised_date, detection_source = await detect_ptp(event)
            if promised_date:
                # Check if promise is already broken at detection time
                from revflow.contracts.config import PTP_GRACE_DAYS
                promised_dt = datetime.fromisoformat(promised_date).replace(tzinfo=timezone.utc)
                grace_end = promised_dt + timedelta(days=PTP_GRACE_DAYS)
                
                if run_date > grace_end:
                    # Promise already broken at detection time - handle as broken promise
                    # Only B2B_RECEIVABLE events have ladder steps; subscription_failure PTPs don't escalate via ladder
                    if event.event_type == EventType.B2B_RECEIVABLE:
                        from revflow.ladder.b2b import advance_ladder_step, assign_ladder_step
                        from revflow.contracts.enums import LadderStep, Action, Outcome, RuleFired
                        
                        # Compute the ladder_step that SHOULD be assigned based on invoice age
                        # This is what the action table would assign for this invoice_overdue event
                        ladder_step_at_pause = assign_ladder_step(event, Cause.INVOICE_OVERDUE, run_date)
                        
                        with get_connection() as conn:
                            conn.execute(
                                """INSERT INTO ptp_commitments (
                                    run_id, event_id, promised_date, detected_from_text,
                                    detection_source, status, ladder_step_at_pause, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (
                                    self.run_id,
                                    event.event_id,
                                    promised_date,
                                    event.customer_reply_text[:500],
                                    detection_source.value,
                                    "broken",
                                    ladder_step_at_pause.value,
                                    datetime.now(timezone.utc).isoformat(),
                                )
                            )
                        
                        # Advance one step above the ladder_step_at_pause (per §4.4)
                        next_step = advance_ladder_step(ladder_step_at_pause, LadderStep.FLAG_FOR_HUMAN)
                        
                        # Write audit log for broken promise
                        insert_audit_row(
                            run_id=self.run_id,
                            event_id=event.event_id,
                            event_type=event.event_type.value,
                            cause="unclassified",
                            cause_source=detection_source.value,
                            rule_fired=RuleFired.PTP_PROMISE_BROKEN_ESCALATED.value,
                            action=Action.ESCALATE_TO_HUMAN.value,
                            ladder_step=next_step.value,
                            rationale=f"PTP broken at detection (promised {promised_date}, grace ended {grace_end.date()}). Escalated one step above {ladder_step_at_pause.value}.",
                            outcome=Outcome.ESCALATED.value,
                            amount_inr=event.amount_inr,
                            is_simulated=0,
                            llm_calls_used=0,
                        )
                        
                        # Update event ladder_step
                        with get_connection() as conn:
                            conn.execute(
                                "UPDATE events SET ladder_step = ? WHERE event_id = ?",
                                (next_step.value, event.event_id)
                            )
                        return  # Broken promise handled, skip normal processing
                    else:
                        # For subscription_failure, just record the broken PTP without ladder escalation
                        with get_connection() as conn:
                            conn.execute(
                                """INSERT INTO ptp_commitments (
                                    run_id, event_id, promised_date, detected_from_text,
                                    detection_source, status, ladder_step_at_pause, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (
                                    self.run_id,
                                    event.event_id,
                                    promised_date,
                                    event.customer_reply_text[:500],
                                    detection_source.value,
                                    "broken",
                                    "none",  # No ladder for subscription
                                    datetime.now(timezone.utc).isoformat(),
                                )
                            )
                        # For subscription, just continue to normal processing (will hit retry ceiling or other guards)
                else:
                    # New PTP detected - handle the pause
                    ptp_decision = handle_ptp_pause(
                        event=event,
                        promised_date=promised_date,
                        detection_source=detection_source,
                        run_id=self.run_id,
                        run_date=run_date,
                    )
                    # PTP pause decision overrides normal processing
                    # handle_ptp_pause already wrote the audit row and updated event
                    return  # PTP pause handled, skip normal processing

        # ─── Classifier ─────────────────────────────────────────────────────
        # Try rules first
        cause = classify_by_rules(event)

        if cause is not None:
            cause_source = CauseSource.RULE
        else:
            # LLM fallback for ambiguous events
            if self.use_llm:
                cause = await classify_by_llm(event)
                cause_source = CauseSource.LLM
                self.llm_calls_used += 1
            else:
                cause = Cause.UNCLASSIFIED
                cause_source = CauseSource.LLM  # Marked as LLM path even if disabled

        # Enforce applicability (should already be done in classify_by_rules)
        from revflow.contracts.enums import validate_cause_applicability
        cause = validate_cause_applicability(cause, event.event_type)

        # ─── Policy Engine ──────────────────────────────────────────────────
        decision = await decide_action_async(
            event=event,
            cause=cause,
            cause_source=cause_source,
            run_id=self.run_id,
            as_of=run_date,
            llm_calls_used=self.llm_calls_used,
            use_llm=self.use_llm,
        )

        # Update llm_calls_used if Stage 4 was used
        if "llm_calls_used" in decision:
            self.llm_calls_used = decision["llm_calls_used"]

        # ─── Executor ────────────────────────────────────────────────────────
        action = decision["action"]
        outcome = decision["outcome"]
        ladder_step = decision["ladder_step"]
        rule_fired = decision["rule_fired"]
        rationale = decision["rationale"]
        cause_source_out = CauseSource(decision.get("cause_source", cause_source.value))

        # Write audit log
        audit_id = insert_audit_row(
            run_id=self.run_id,
            event_id=event.event_id,
            event_type=event.event_type.value,
            cause=cause.value,
            cause_source=cause_source_out.value,
            rule_fired=rule_fired.value,
            action=action.value,
            ladder_step=ladder_step.value,
            rationale=rationale,
            outcome=outcome.value,
            amount_inr=event.amount_inr,
            is_simulated=1 if action == Action.NUDGE else 0,
            llm_calls_used=decision.get("llm_calls_used", 0) - self.llm_calls_used,
        )

        # Execute action
        if action == Action.RETRY_NOW:
            # Real retry via Razorpay Test Mode
            retry_result = await execute_retry_now(event)

            # Update audit_log with actual outcome
            with get_connection() as conn:
                attributed_recovery = event.amount_inr if retry_result.outcome == "recovered" else 0
                final_outcome = retry_result.outcome  # recovered, failed, api_error

                conn.execute(
                    """UPDATE audit_log SET
                        outcome = ?,
                        attributed_recovery_inr = ?,
                        rationale = ?
                        WHERE id = ?""",
                    (
                        final_outcome,
                        attributed_recovery,
                        rationale + f" | Razorpay: {retry_result.message}",
                        audit_id,
                    ),
                )

        elif action == Action.NUDGE:
            # Simulated comms
            await write_simulated_nudge(
                run_id=self.run_id,
                audit_log_id=audit_id,
                event=event,
                cause=cause.value,
                locale=Locale.EN,  # Default, could be enhanced
                channel=SimulatedChannel.SMS,
                tone="neutral",
            )

            # Update event ladder_step if B2B
            if event.event_type == EventType.B2B_RECEIVABLE:
                with get_connection() as conn:
                    conn.execute(
                        "UPDATE events SET ladder_step = ? WHERE event_id = ?",
                        (ladder_step.value, event.event_id),
                    )

        elif action == Action.ESCALATE_TO_HUMAN:
            # Write escalation
            queue = "finance_review" if event.event_type == EventType.B2B_RECEIVABLE else "ops_review"
            write_escalation(
                run_id=self.run_id,
                audit_log_id=audit_id,
                event=event,
                rule_fired=rule_fired.value,
                ladder_step=ladder_step,
                queue=queue,
            )

            # Update event ladder_step if B2B
            if event.event_type == EventType.B2B_RECEIVABLE:
                with get_connection() as conn:
                    conn.execute(
                        "UPDATE events SET ladder_step = ? WHERE event_id = ?",
                        (ladder_step.value, event.event_id),
                    )

        elif action == Action.STOP:
            # Withheld - nothing to execute
            pass

        elif action == Action.RETRY_LATER:
            # Deferred - nothing to execute now
            pass

        # Update event with decision info
        with get_connection() as conn:
            conn.execute(
                """UPDATE events SET
                    ladder_step = ?,
                    paused_until = ?
                    WHERE event_id = ?""",
                (
                    ladder_step.value,
                    decision.get("paused_until"),
                    event.event_id,
                ),
            )

    def _compute_summary_metrics(self) -> None:
        """Compute and write summary_metrics.json per §5.6."""
        from revflow.metrics.summary import compute_summary_metrics
        compute_summary_metrics(self.run_id)


from revflow.contracts.enums import Locale, SimulatedChannel