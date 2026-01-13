# tools/context_package.py
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from tools.work_queue import DerivedQueueState, InvariantViolation, SchemaError, derive_queue_state


# -----------------------------
# Constants (Spec v1.7.0 preview)
# -----------------------------

QUEUE_SSOT_BRANCH = "__factory_state__/work_queue"
QUEUE_SSOT_PATH = "factory/work_queue.jsonl"
CONTEXTS_SSOT_BRANCH = "__factory_state__/contexts"
CONTEXTS_SSOT_DIR = "factory/contexts"


# -----------------------------
# Errors
# -----------------------------

class ContextPackageError(Exception):
    """Base error for ContextPackage operations."""


class ContextSchemaError(ContextPackageError):
    """ContextPackage schema/format is invalid."""


class ContextInvariantViolation(ContextPackageError):
    """ContextPackage hard invariant violated."""


# -----------------------------
# Types
# -----------------------------

ContextPackage = Dict[str, Any]


@dataclass(frozen=True)
class ContextBuildInputs:
    """Inputs required to build a ContextPackage document (pure, no I/O)."""

    queue_events: List[Dict[str, Any]]
    job_id: str

    # Optional: pass derived queue state to avoid re-folding
    derived_state: Optional[DerivedQueueState] = None

    # Required for head-only enforcement in v1.7.0 materialization boundary
    require_head_only: bool = True

    # Optional override: head jobId (if already known)
    head_job_id: Optional[str] = None

    # Optional: existing contexts index for uniqueness enforcement
    existing_contexts_by_job_id: Optional[Dict[str, str]] = None


# -----------------------------
# Helpers
# -----------------------------

_CTX_ID_RE = re.compile(r"^ctx_(\d+)_([0-9a-f]{4})$")


def now_rfc3339_utc() -> str:
    dt = datetime.now(timezone.utc).replace(microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def validate_context_id(context_id: str) -> Tuple[int, str]:
    """Validate ctx_<unix>_<rand4> format. Returns (unix, rand4)."""
    if not isinstance(context_id, str) or not context_id:
        raise ContextSchemaError("contextId_missing_or_invalid")
    m = _CTX_ID_RE.match(context_id)
    if not m:
        raise ContextSchemaError(f"contextId_invalid_format contextId={context_id}")
    unix_s, rand4 = m.group(1), m.group(2)
    try:
        unix = int(unix_s)
    except ValueError as e:
        raise ContextSchemaError(f"contextId_invalid_unix contextId={context_id}") from e
    if unix <= 0:
        raise ContextSchemaError(f"contextId_invalid_unix contextId={context_id}")
    return unix, rand4


def validate_created_at(created_at: str) -> None:
    """Validate RFC3339 UTC (seconds precision) ending with 'Z'."""
    if not isinstance(created_at, str) or not created_at:
        raise ContextSchemaError("createdAt_missing_or_invalid")
    if not created_at.endswith("Z"):
        raise ContextSchemaError(f"createdAt_must_be_utc_z createdAt={created_at}")
    # Minimal parse (avoid strict dependency). Accept ISO form like 2026-01-11T06:00:00Z
    try:
        datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as e:
        raise ContextSchemaError(f"createdAt_invalid_rfc3339 createdAt={created_at}") from e


def _find_enqueue_event(queue_events: List[Dict[str, Any]], job_id: str) -> Dict[str, Any]:
    for ev in queue_events:
        if ev.get("type") == "enqueue" and ev.get("jobId") == job_id:
            return ev
    raise ContextInvariantViolation(f"unknown_jobId jobId={job_id}")


def _find_start_event_id(queue_events: List[Dict[str, Any]], job_id: str) -> Optional[str]:
    # The queue may contain multiple events; pick the first start for this jobId.
    for ev in queue_events:
        if ev.get("type") == "start" and ev.get("jobId") == job_id:
            eid = ev.get("eventId")
            if isinstance(eid, str) and eid:
                return eid
            return None
    return None


def _sanitize_job_snapshot(job: Dict[str, Any]) -> Dict[str, Any]:
    """Return the minimal stable snapshot required by spec."""
    return {
        "kind": job.get("kind"),
        "repo": job.get("repo"),
        "base": job.get("base"),
        "payload": job.get("payload"),
    }


def ensure_no_secrets(obj: Any) -> None:
    """Best-effort guard: reject obvious secret-like keys anywhere in the document."""
    secret_keys = {"token", "gh_token", "github_token", "password", "secret", "api_key", "apikey"}

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(k, str) and k.lower() in secret_keys:
                    raise ContextSchemaError(f"secrets_forbidden key={k}")
                walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)

    walk(obj)


# -----------------------------
# Core builder (pure)
# -----------------------------

def build_context_package(
    *,
    context_id: str,
    created_at: str,
    inputs: ContextBuildInputs,
) -> ContextPackage:
    """Build an immutable ContextPackage document per v1.7.0 minimal materialization boundary.

    This function is pure: it performs no I/O and does not mutate inputs.

    Hard guarantees:
    - Validates contextId / createdAt formats
    - Enforces head-only mutation (default)
    - Enforces: jobId exists and is started (start event present)
    - Enforces uniqueness when existing_contexts_by_job_id is provided
    """

    validate_context_id(context_id)
    validate_created_at(created_at)

    if not isinstance(inputs.job_id, str) or not inputs.job_id:
        raise ContextSchemaError("jobId_missing_or_invalid")

    # Derive state if not provided
    state = inputs.derived_state or derive_queue_state(inputs.queue_events)

    head = inputs.head_job_id
    if inputs.require_head_only and not head:
        head = state.head_non_terminal_job()

    if inputs.require_head_only and head and inputs.job_id != head:
        raise ContextInvariantViolation(f"non_head_job_mutation head={head} jobId={inputs.job_id}")

    # Must exist as a job (enqueue)
    enqueue_ev = _find_enqueue_event(inputs.queue_events, inputs.job_id)
    job = enqueue_ev.get("job")
    if not isinstance(job, dict):
        raise SchemaError("enqueue_job_missing_or_invalid")

    # Must have started (creation timing after start)
    start_event_id = _find_start_event_id(inputs.queue_events, inputs.job_id)
    if not start_event_id:
        raise ContextInvariantViolation(f"job_not_started jobId={inputs.job_id}")

    # Uniqueness: jobId -> exactly one contextId
    existing = inputs.existing_contexts_by_job_id or {}
    if inputs.job_id in existing:
        raise ContextInvariantViolation(
            f"duplicate_context_for_job jobId={inputs.job_id} existingContextId={existing[inputs.job_id]}"
        )

    doc: ContextPackage = {
        "contextId": context_id,
        "jobId": inputs.job_id,
        "createdAt": created_at,
        "job": _sanitize_job_snapshot(job),
        "source": {
            "queueBranch": QUEUE_SSOT_BRANCH,
            "queuePath": QUEUE_SSOT_PATH,
            "startEventId": start_event_id,
        },
    }

    ensure_no_secrets(doc)
    return doc


def contexts_path_for(context_id: str) -> str:
    """Return the SSOT relative path for a context document."""
    validate_context_id(context_id)
    return f"{CONTEXTS_SSOT_DIR}/{context_id}.json"
