-- RevFlow Database Schema — generated from 00_CONTRACTS_RevFlow.md §3
-- SQLite. Seven tables, complete and closed.
-- All monetary columns are INTEGER paise (1 rupee = 100 paise).
-- Foreign keys must be enforced: PRAGMA foreign_keys = ON

-- ─── 3.1 batch_runs ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS batch_runs (
    run_id          TEXT PRIMARY KEY,                    -- RUN-YYYYMMDDTHHMMSS
    started_at      TEXT NOT NULL,                       -- ISO 8601 UTC
    completed_at    TEXT,                                -- ISO 8601 UTC, null while running
    status          TEXT NOT NULL,                       -- batch_run_status enum
    event_count     INTEGER NOT NULL DEFAULT 0,
    llm_call_count  INTEGER NOT NULL DEFAULT 0,
    random_seed     INTEGER NOT NULL,
    notes           TEXT
);

-- ─── 3.2 events ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    event_id                TEXT PRIMARY KEY,            -- EVT-0001...EVT-0300 per run
    run_id                  TEXT NOT NULL REFERENCES batch_runs(run_id),
    event_type              TEXT NOT NULL,               -- event_type enum
    amount_inr              INTEGER NOT NULL,            -- Paise
    currency                TEXT NOT NULL DEFAULT 'INR',
    customer_id             TEXT NOT NULL,               -- CUST-XXXX
    decline_code            TEXT,                        -- Null for b2b_receivable, user_abandoned
    decline_message         TEXT,
    true_cause              TEXT,                        -- Ground truth, synthetic only
    retry_count             INTEGER NOT NULL DEFAULT 0,
    last_attempt_at         TEXT,                        -- ISO 8601 UTC
    paused_until            TEXT,                        -- ISO 8601 date
    ladder_step             TEXT NOT NULL DEFAULT 'none', -- ladder_step enum
    invoice_issued_at       TEXT,                        -- ISO 8601 date, b2b only
    invoice_due_date        TEXT,                        -- ISO 8601 date, b2b only
    session_started_at      TEXT,                        -- ISO 8601 UTC, checkout only
    checkout_resume_token   TEXT,                        -- Opaque token
    customer_reply_text     TEXT,                        -- Simulated inbound reply
    dispute_raised          INTEGER NOT NULL DEFAULT 0,  -- Explicit dispute signal for B2B invoices
    created_at              TEXT NOT NULL                -- ISO 8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id);
CREATE INDEX IF NOT EXISTS idx_events_customer_id ON events(customer_id);
CREATE INDEX IF NOT EXISTS idx_events_paused_until ON events(paused_until);

-- ─── 3.3 audit_log ───────────────────────────────────────────────────────────
-- Append-only. No UPDATE or DELETE permitted.
CREATE TABLE IF NOT EXISTS audit_log (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                   TEXT NOT NULL REFERENCES batch_runs(run_id),
    event_id                 TEXT NOT NULL REFERENCES events(event_id),
    event_type               TEXT NOT NULL,               -- Denormalised for metrics
    cause                    TEXT NOT NULL,               -- cause enum
    cause_source             TEXT NOT NULL,               -- cause_source enum
    rule_fired               TEXT NOT NULL,               -- rule_fired enum
    action                   TEXT NOT NULL,               -- action enum
    ladder_step              TEXT NOT NULL DEFAULT 'none', -- ladder_step enum
    rationale                TEXT NOT NULL,               -- Length >= 10 enforced in code
    outcome                  TEXT NOT NULL,               -- outcome enum
    amount_inr               INTEGER NOT NULL,            -- Paise, copied from event
    attributed_recovery_inr  INTEGER NOT NULL DEFAULT 0,  -- Paise, non-zero only when outcome='recovered'
    is_simulated             INTEGER NOT NULL DEFAULT 0,  -- 1 when action='nudge', else 0
    llm_calls_used           INTEGER NOT NULL DEFAULT 0,  -- 0, 1, or 2
    latency_ms               INTEGER NOT NULL,            -- Decision-to-audit-write latency
    created_at               TEXT NOT NULL                -- ISO 8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_audit_log_run_id ON audit_log(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_event_id ON audit_log(event_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_cause ON audit_log(cause);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- ─── 3.4 simulated_actions ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS simulated_actions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_log_id    INTEGER NOT NULL REFERENCES audit_log(id),
    channel         TEXT NOT NULL,                       -- simulated_channel enum
    locale          TEXT NOT NULL,                       -- locale enum
    body_text       TEXT NOT NULL,                       -- Generated copy or voice script
    tts_audio_path  TEXT,                                -- Relative path to sample clip
    status          TEXT NOT NULL DEFAULT 'simulated',   -- Only ever 'simulated'
    created_at      TEXT NOT NULL                        -- ISO 8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_simulated_actions_audit_log_id ON simulated_actions(audit_log_id);

-- ─── 3.5 escalations ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS escalations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_log_id    INTEGER NOT NULL REFERENCES audit_log(id),
    reason          TEXT NOT NULL,                       -- Mirrors rule_fired
    ladder_step     TEXT NOT NULL DEFAULT 'none',        -- flag_for_human for B2B exhaustion
    queue           TEXT NOT NULL,                       -- ops_review or finance_review
    created_at      TEXT NOT NULL                        -- ISO 8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_escalations_audit_log_id ON escalations(audit_log_id);

-- ─── 3.6 contact_log ─────────────────────────────────────────────────────────
-- Keyed by (customer_id, contact_date) — NOT run-scoped per §3.6
-- Unique index on (run_id, customer_id, contact_date, audit_log_id)
CREATE TABLE IF NOT EXISTS contact_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL REFERENCES batch_runs(run_id),
    customer_id     TEXT NOT NULL,
    contact_date    TEXT NOT NULL,                       -- ISO 8601 date only (not datetime)
    audit_log_id    INTEGER NOT NULL REFERENCES audit_log(id)
);

-- The cap check uses: SELECT COUNT(*) WHERE run_id=? AND customer_id=? AND contact_date=?
-- Per §3.6: unique index on (run_id, customer_id, contact_date, audit_log_id)
CREATE UNIQUE INDEX IF NOT EXISTS uq_contact_log_cap
    ON contact_log(run_id, customer_id, contact_date, audit_log_id);

CREATE INDEX IF NOT EXISTS idx_contact_log_customer_date ON contact_log(customer_id, contact_date);
CREATE INDEX IF NOT EXISTS idx_contact_log_run_id ON contact_log(run_id);

-- ─── 3.7 ptp_commitments ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ptp_commitments (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                  TEXT NOT NULL REFERENCES batch_runs(run_id),
    event_id                TEXT NOT NULL REFERENCES events(event_id),
    promised_date           TEXT NOT NULL,               -- ISO 8601 date
    detected_from_text      TEXT NOT NULL,               -- Reply substring for auditability
    detection_source        TEXT NOT NULL,               -- cause_source enum: rule or llm
    status                  TEXT NOT NULL,               -- ptp_status enum
    ladder_step_at_pause    TEXT NOT NULL,               -- Step to resume above if broken
    created_at              TEXT NOT NULL                -- ISO 8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_ptp_commitments_run_id ON ptp_commitments(run_id);
CREATE INDEX IF NOT EXISTS idx_ptp_commitments_event_id ON ptp_commitments(event_id);
CREATE INDEX IF NOT EXISTS idx_ptp_commitments_status ON ptp_commitments(status);