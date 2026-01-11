# tools/work_queue.py
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


# -----------------------------
# Exceptions (map to exit codes)
# -----------------------------

class WorkQueueError(Exception):
    """Base error for work queue."""


class SchemaError(WorkQueueError):
    """Event schema is invalid."""


class InvariantViolation(WorkQueueError):
    """Hard invariant violated (FIFO, transitions, etc.)."""


class HumanOnlyViolation(WorkQueueError):
    """Human-only operation attempted by bot actor."""


class BlockedHead(WorkQueueError):
    """Head-of-queue is blocked; worker must stop (exit=2)."""


# -----------------------------
# Constants (Spec v1.5.0)
# -----------------------------

BOT_ACTOR = "github-actions[bot]"

EVENT_TYPES = {"enqueue", "start", "block", "unblock", "done", "fail", "cancel"}
JOB_KINDS = {"open_pr", "release", "changelog", "maintenance"}

TERMINAL_TYPES = {"done", "fail", "cancel"}


# -----------------------------
# Data types
# -----------------------------

JobState = str  # queued | running | blocked | done | fail | cancel


@dataclass(frozen=True)
class DerivedQueueState:
    # jobId -> derived state
    job_states: Dict[str, JobState]
    # enqueue order: jobIds in the order they were first enqueued
    enqueue_order: List[str]
    # jobId -> enqueue event (for metadata)
    enqueues: Dict[str, Dict[str, Any]]

    def head_non_terminal_job(self) -> Optional[str]:
        for jid in self.enqueue_order:
            st = self.job_states.get(jid)
            if st is None:
                continue
            if st not in TERMINAL_TYPES:
                return jid
        return None

    def count_running(self) -> int:
        return sum(1 for st in self.job_states.values() if st == "running")


# -----------------------------
# Helpers: IDs / timestamps
# -----------------------------

def now_rfc3339_utc() -> str:
    dt = datetime.now(timezone.utc).replace(microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def rand4_hex() -> str:
    # Deterministic is not required, only format is. Keep minimal.
    return f"{(os.urandom(2).hex())[:4]}"


def make_event_id(epoch: Optional[int] = None) -> str:
    e = int(time.time()) if epoch is None else int(epoch)
    return f"evt_{e}_{rand4_hex()}"


def make_job_id(epoch: Optional[int] = None) -> str:
    e = int(time.time()) if epoch is None else int(epoch)
    return f"job_{e}_{rand4_hex()}"


# -----------------------------
# JSONL I/O
# -----------------------------

def parse_jsonl_lines(lines: Iterable[str]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
        except json.JSONDecodeError as e:
            raise SchemaError(f"invalid_jsonl_line: {e}") from e
        if not isinstance(obj, dict):
            raise SchemaError("jsonl_line_must_be_object")
        events.append(obj)
    return events


def read_jsonl_file(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise SchemaError(f"queue_file_not_found path={path}")
    with open(path, "r", encoding="utf-8") as f:
        return parse_jsonl_lines(f.readlines())


def append_jsonl_line(path: str, event: Dict[str, Any]) -> None:
    # Single append; lock is handled outside (RepoLock via worker/cli).
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# -----------------------------
# Schema validation
# -----------------------------

def _require_str(event: Dict[str, Any], key: str) -> str:
    v = event.get(key)
    if not isinstance(v, str) or not v:
        raise SchemaError(f"missing_or_invalid {key}")
    return v


def _require_obj(event: Dict[str, Any], key: str) -> Dict[str, Any]:
    v = event.get(key)
    if not isinstance(v, dict):
        raise SchemaError(f"missing_or_invalid {key}")
    return v


def validate_event_schema(event: Dict[str, Any]) -> None:
    t = _require_str(event, "type")
    if t not in EVENT_TYPES:
        raise SchemaError(f"invalid_type type={t}")

    _require_str(event, "eventId")
    _require_str(event, "ts")
    _require_str(event, "actor")
    _require_str(event, "jobId")

    if t == "enqueue":
        job = _require_obj(event, "job")
        kind = job.get("kind")
        repo = job.get("repo")
        base = job.get("base")
        payload = job.get("payload")
        if kind not in JOB_KINDS:
            raise SchemaError(f"invalid_job_kind kind={kind}")
        if not isinstance(repo, str) or "/" not in repo:
            raise SchemaError("invalid_job_repo")
        if not isinstance(base, str) or not base:
            raise SchemaError("invalid_job_base")
        if not isinstance(payload, dict):
            raise SchemaError("invalid_job_payload")
    else:
        # job MUST NOT be required; allow evidence/reason/meta optionally
        pass


# -----------------------------
# Derived state (fold events)
# -----------------------------

def derive_queue_state(events: List[Dict[str, Any]]) -> DerivedQueueState:
    # validate all schemas first
    for ev in events:
        # allow init placeholder line without required keys
        if ev.get("type") == "__init__":
            continue
        validate_event_schema(ev)

    enqueue_order: List[str] = []
    enqueues: Dict[str, Dict[str, Any]] = {}
    job_states: Dict[str, JobState] = {}

    seen_enqueue: set[str] = set()

    for ev in events:
        if ev.get("type") == "__init__":
            continue

        t = ev["type"]
        jid = ev["jobId"]

        # Handle enqueue ordering
        if t == "enqueue":
            if jid in seen_enqueue:
                raise InvariantViolation(f"double_enqueue jobId={jid}")
            seen_enqueue.add(jid)
            enqueue_order.append(jid)
            enqueues[jid] = ev
            job_states[jid] = "queued"
            continue

        # non-enqueue must reference known jobId (already enqueued)
        if jid not in seen_enqueue:
            raise InvariantViolation(f"event_before_enqueue type={t} jobId={jid}")

        # apply state transitions in file order
        cur = job_states.get(jid)
        if cur is None:
            raise InvariantViolation(f"missing_state jobId={jid}")

        nxt = _next_state(cur, t)
        job_states[jid] = nxt

    # Hard invariant: at most one running
    running_count = sum(1 for s in job_states.values() if s == "running")
    if running_count > 1:
        raise InvariantViolation(f"multiple_running count={running_count}")

    return DerivedQueueState(
        job_states=job_states,
        enqueue_order=enqueue_order,
        enqueues=enqueues,
    )


def _next_state(cur: JobState, event_type: str) -> JobState:
    # Spec 3.3 rules
    if event_type == "start":
        if cur != "queued":
            raise InvariantViolation(f"illegal_transition {cur}->start")
        return "running"

    if event_type == "block":
        if cur != "running":
            raise InvariantViolation(f"illegal_transition {cur}->block")
        return "blocked"

    if event_type == "unblock":
        if cur != "blocked":
            raise InvariantViolation(f"illegal_transition {cur}->unblock")
        return "running"

    if event_type in ("done", "fail"):
        if cur not in ("running", "blocked"):
            raise InvariantViolation(f"illegal_transition {cur}->{event_type}")
        return event_type  # done|fail

    if event_type == "cancel":
        if cur not in ("queued", "blocked"):
            raise InvariantViolation(f"illegal_transition {cur}->cancel")
        return "cancel"

    if event_type == "enqueue":
        raise InvariantViolation("enqueue_handled_elsewhere")

    raise SchemaError(f"unknown_event_type {event_type}")


# -----------------------------
# FIFO / head-of-queue checks
# -----------------------------

def ensure_head_can_transition(state: DerivedQueueState, job_id: str) -> None:
    head = state.head_non_terminal_job()
    if head is None:
        raise InvariantViolation("no_non_terminal_jobs")
    if head != job_id:
        raise InvariantViolation(f"non_head_job_mutation head={head} jobId={job_id}")

    # If head is blocked: worker must stop and do nothing.
    if state.job_states.get(head) == "blocked":
        raise BlockedHead(f"head_blocked jobId={head}")


# -----------------------------
# Enqueue helpers (Human only)
# -----------------------------

def build_enqueue_event(
    *,
    actor: str,
    job_kind: str,
    repo: str,
    base: str,
    payload: Dict[str, Any],
    epoch: Optional[int] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    if actor == BOT_ACTOR:
        raise HumanOnlyViolation("enqueue_actor_must_be_human")

    if job_kind not in JOB_KINDS:
        raise SchemaError(f"invalid_job_kind kind={job_kind}")

    jid = job_id or make_job_id(epoch=epoch)
    return {
        "eventId": make_event_id(epoch=epoch),
        "ts": now_rfc3339_utc(),
        "actor": actor,
        "type": "enqueue",
        "jobId": jid,
        "job": {
            "kind": job_kind,
            "repo": repo,
            "base": base,
            "payload": payload,
        },
    }


def validate_enqueue_append(events: List[Dict[str, Any]], enqueue_event: Dict[str, Any]) -> None:
    validate_event_schema(enqueue_event)
    state = derive_queue_state(events)
    jid = enqueue_event["jobId"]

    # No duplicate jobId (strict)
    if jid in state.job_states:
        raise InvariantViolation(f"jobId_already_exists jobId={jid}")


def enqueue(
    *,
    queue_path: str,
    actor: str,
    job_kind: str,
    repo: str,
    base: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    events = read_jsonl_file(queue_path)
    ev = build_enqueue_event(actor=actor, job_kind=job_kind, repo=repo, base=base, payload=payload)
    validate_enqueue_append(events, ev)
    append_jsonl_line(queue_path, ev)
    return ev