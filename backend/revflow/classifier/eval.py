"""
RevFlow Classifier Evaluation — computes precision/recall vs true_cause.

Per §5.7: Produces classifier_metrics.json with:
- overall accuracy, macro_precision, macro_recall, support
- by_cause: precision, recall, f1, support for each cause with non-zero support
- by_source: rule vs llm accuracy and count
- confusion_pairs: true_cause vs predicted_cause counts

Satisfies FR-4. true_cause is ONLY read here, never by classifier or policy engine.
"""
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any

from revflow.contracts.enums import Cause, EventType
from revflow.ingestion.normaliser import Event
from revflow.db.connection import get_connection
from revflow.db.ledger import get_audit_log_rows

from datetime import datetime, timezone


def _get_project_root() -> Path:
    """Get the project root directory (containing backend/, frontend/, docs/)."""
    current = Path(__file__).resolve().parent
    while current and not (current / "docs" / "00_CONTRACTS_RevFlow.md").exists():
        parent = current.parent
        if parent == current:
            break
        current = parent
    return current


CLASSIFIER_METRICS_PATH = _get_project_root() / "backend" / "data" / "classifier_metrics.json"


def evaluate_classifier(run_id: str) -> Dict[str, Any]:
    """
    Evaluate classifier precision/recall against true_cause for a run.

    Reads events (for true_cause) and audit_log (for predicted cause and source).
    Only evaluates events where true_cause is not None (synthetic data).

    Returns:
        Dict matching §5.7 schema.
    """
    with get_connection() as conn:
        # Get all events with true_cause for this run
        events_rows = conn.execute(
            "SELECT event_id, true_cause, event_type FROM events WHERE run_id = ? AND true_cause IS NOT NULL",
            (run_id,)
        ).fetchall()

        # Get audit_log rows for this run (one per event, the first decision)
        audit_rows = conn.execute(
            """
            SELECT al.event_id, al.cause, al.cause_source
            FROM audit_log al
            JOIN (
                SELECT event_id, MIN(created_at) as first_created
                FROM audit_log
                WHERE run_id = ?
                GROUP BY event_id
            ) first ON al.event_id = first.event_id AND al.created_at = first.first_created
            WHERE al.run_id = ?
            """,
            (run_id, run_id)
        ).fetchall()

    # Build lookup: event_id -> (true_cause, event_type)
    true_causes = {}
    for row in events_rows:
        true_causes[row["event_id"]] = (row["true_cause"], row["event_type"])

    # Build predictions: event_id -> (predicted_cause, cause_source)
    predictions = {}
    for row in audit_rows:
        predictions[row["event_id"]] = (row["cause"], row["cause_source"])

    # Collect evaluation data
    y_true = []
    y_pred = []
    sources = []  # "rule" or "llm"
    event_types = []

    for event_id, (true_cause, event_type) in true_causes.items():
        if event_id in predictions:
            pred_cause, cause_source = predictions[event_id]
            y_true.append(true_cause)
            y_pred.append(pred_cause)
            sources.append(cause_source)
            event_types.append(event_type)

    if not y_true:
        return _empty_metrics(run_id)

    # Compute overall metrics
    from revflow.contracts.enums import Cause
    all_causes = [c.value for c in Cause]

    # Confusion matrix
    confusion = defaultdict(lambda: defaultdict(int))
    for true, pred in zip(y_true, y_pred):
        confusion[true][pred] += 1

    # Per-cause metrics
    by_cause = {}
    for cause in all_causes:
        support = y_true.count(cause)
        if support == 0:
            continue

        tp = confusion[cause].get(cause, 0)
        fp = sum(confusion[other].get(cause, 0) for other in all_causes if other != cause)
        fn = sum(confusion[cause].get(other, 0) for other in all_causes if other != cause)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        by_cause[cause] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }

    # Overall metrics
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / len(y_true)

    # Macro precision/recall (average over causes with support > 0)
    macro_precision = sum(m["precision"] for m in by_cause.values()) / len(by_cause) if by_cause else 0.0
    macro_recall = sum(m["recall"] for m in by_cause.values()) / len(by_cause) if by_cause else 0.0

    # By source
    rule_correct = rule_total = 0
    llm_correct = llm_total = 0
    for true, pred, src in zip(y_true, y_pred, sources):
        if src == "rule":
            rule_total += 1
            if true == pred:
                rule_correct += 1
        elif src == "llm":
            llm_total += 1
            if true == pred:
                llm_correct += 1

    by_source = {
        "rule": {
            "count": rule_total,
            "accuracy": round(rule_correct / rule_total, 4) if rule_total > 0 else 0.0,
        },
        "llm": {
            "count": llm_total,
            "accuracy": round(llm_correct / llm_total, 4) if llm_total > 0 else 0.0,
        },
    }

    # Confusion pairs
    confusion_pairs = []
    for true_cause, pred_dict in confusion.items():
        for pred_cause, count in pred_dict.items():
            confusion_pairs.append({
                "true_cause": true_cause,
                "predicted_cause": pred_cause,
                "count": count,
            })

    # Sort by count descending
    confusion_pairs.sort(key=lambda x: x["count"], reverse=True)

    return {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall": {
            "accuracy": round(accuracy, 4),
            "macro_precision": round(macro_precision, 4),
            "macro_recall": round(macro_recall, 4),
            "support": len(y_true),
        },
        "by_cause": by_cause,
        "by_source": by_source,
        "confusion_pairs": confusion_pairs,
    }


def _empty_metrics(run_id: str) -> Dict[str, Any]:
    """Return empty metrics structure."""
    return {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall": {
            "accuracy": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "support": 0,
        },
        "by_cause": {},
        "by_source": {"rule": {"count": 0, "accuracy": 0.0}, "llm": {"count": 0, "accuracy": 0.0}},
        "confusion_pairs": [],
    }


def write_classifier_metrics(run_id: str) -> None:
    """Evaluate and write classifier_metrics.json."""
    metrics = evaluate_classifier(run_id)
    with open(CLASSIFIER_METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)