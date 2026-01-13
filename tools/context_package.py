

from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# v1.7.0 ContextPackage SSOT materialization (spec §10A)
# These constants are referenced by CLI/tests.
CONTEXTS_SSOT_BRANCH = "__factory_state__/contexts"
QUEUE_SSOT_BRANCH = "__factory_state__/work_queue"
QUEUE_SSOT_PATH = "factory/work_queue.jsonl"


class ContextSchemaError(ValueError):
    """Raised when input data does not satisfy schema requirements."""


class ContextInvariantViolation(RuntimeError):
    """Raised when an invariant required by the spec is violated."""


def now_rfc3339_utc() -> str:
    """Return current UTC timestamp as RFC3339 string with 'Z'."""
    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


# Accept `ctx_` prefix followed by one or more path-safe segments.
# Keep it permissive enough for existing tests/fixtures (e.g. ctx_1_abcd).
_CTX_ID_RE = re.compile(r"^ctx_[0-9a-zA-Z]+(?:_[0-9a-zA-Z]+)*$")


def validate_context_id(context_id: str) -> None:
    """Validate contextId format (minimal, spec-aligned).

    - Must start with `ctx_`
    - Must be url/path-safe (alnum + underscore)
    """
    cid = (context_id or "").strip()
    if not cid:
        raise ContextSchemaError("context_id_missing")
    if not cid.startswith("ctx_"):
        raise ContextSchemaError("context_id_must_start_with_ctx_")
    if not _CTX_ID_RE.match(cid):
        raise ContextSchemaError("context_id_invalid_format")


def contexts_path_for(context_id: str) -> str:
    """Relative path for a materialized context document."""
    validate_context_id(context_id)
    return str(Path("factory") / "contexts" / f"{context_id}.json")


@dataclass(frozen=True)
class ContextBuildInputs:
    """Inputs used to build a ContextPackage document.

    queue_events: raw queue event objects (parsed JSONL)
    job_id: target jobId
    derived_state: output of tools.work_queue.derive_queue_state
    require_head_only: enforce head-of-queue discipline when True
    """

    queue_events: List[Dict[str, Any]]
    job_id: str
    derived_state: Any
    require_head_only: bool = True


def _ev_type(ev: Dict[str, Any]) -> str:
    return (ev.get("type") or ev.get("eventType") or "").strip()


def _find_first(events: List[Dict[str, Any]], *, t: str, job_id: str) -> Optional[Dict[str, Any]]:
    for ev in events:
        if not isinstance(ev, dict):
            continue
        if (ev.get("jobId") or "").strip() != job_id:
            continue
        if _ev_type(ev) == t:
            return ev
    return None


def _require_head_only(inputs: ContextBuildInputs) -> None:
    if not inputs.require_head_only:
        return

    state = inputs.derived_state

    # Best-effort duck-typing across potential state representations.
    head_job_id = None
    if hasattr(state, "head_job_id"):
        head_job_id = getattr(state, "head_job_id")
    elif isinstance(state, dict):
        head_job_id = state.get("headJobId") or state.get("head_job_id")

    if head_job_id and str(head_job_id).strip() != inputs.job_id:
        raise ContextInvariantViolation("job_is_not_head_of_queue")

    # Blocked check (if available)
    blocked = None
    if hasattr(state, "is_blocked") and callable(getattr(state, "is_blocked")):
        try:
            blocked = bool(state.is_blocked(inputs.job_id))
        except Exception:
            blocked = None
    elif isinstance(state, dict):
        # Common shapes: {"blockedJobIds": [...]} or {"blocked": {...}}
        b1 = state.get("blockedJobIds")
        if isinstance(b1, list):
            blocked = inputs.job_id in b1

    if blocked is True:
        # Spec exit code mapping is handled by CLI; core raises invariant.
        raise ContextInvariantViolation("head_job_is_blocked")


def build_context_package(*, context_id: str, created_at: str, inputs: ContextBuildInputs) -> Dict[str, Any]:
    """Build a ContextPackage document (pure).

    v1.7.0 requires:
    - identity fields: contextId, jobId, createdAt
    - job snapshot from enqueue: kind, repo, base, payload
    - source metadata: queueBranch, queuePath, startEventId (if available)
    """

    job_id = (inputs.job_id or "").strip()
    if not job_id:
        raise ContextSchemaError("job_id_missing")

    validate_context_id(context_id)

    ca = (created_at or "").strip()
    if not ca:
        raise ContextSchemaError("created_at_missing")

    _require_head_only(inputs)

    enqueue = _find_first(inputs.queue_events, t="enqueue", job_id=job_id)
    if not enqueue:
        raise ContextInvariantViolation("enqueue_event_not_found")

    job_snapshot = {
        "kind": enqueue.get("kind"),
        "repo": enqueue.get("repo"),
        "base": enqueue.get("base"),
        "payload": enqueue.get("payload"),
    }

    missing = [k for k in ("kind", "repo", "base", "payload") if job_snapshot.get(k) is None]
    if missing:
        raise ContextSchemaError(f"enqueue_missing_fields:{','.join(missing)}")

    start = _find_first(inputs.queue_events, t="start", job_id=job_id)
    start_event_id = None
    if start and isinstance(start.get("eventId"), str) and start.get("eventId"):
        start_event_id = start["eventId"].strip()

    doc: Dict[str, Any] = {
        "contextId": context_id,
        "jobId": job_id,
        "createdAt": ca,
        "job": job_snapshot,
        "source": {
            "queueBranch": QUEUE_SSOT_BRANCH,
            "queuePath": QUEUE_SSOT_PATH,
        },
    }

    if start_event_id is not None:
        doc["source"]["startEventId"] = start_event_id

    # Defensive: ensure JSON serializable.
    try:
        json.dumps(doc)
    except TypeError as e:
        raise ContextSchemaError(f"context_doc_not_json_serializable:{e}")

    return doc