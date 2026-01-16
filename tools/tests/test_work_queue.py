# tools/tests/test_work_queue.py
import unittest

from tools.work_queue import (
    BOT_ACTOR,
    BlockedHead,
    HumanOnlyViolation,
    InvariantViolation,
    SchemaError,
    build_enqueue_event,
    build_transition_event,
    derive_queue_state,
    ensure_head_can_transition,
    parse_jsonl_lines,
    validate_transition_append,
)


class TestWorkQueueCore(unittest.TestCase):
    def test_enqueue_human_only(self) -> None:
        with self.assertRaises(HumanOnlyViolation):
            build_enqueue_event(
                actor=BOT_ACTOR,
                job_kind="open_pr",
                repo="owner/repo",
                base="main",
                payload={"head": "feature/test", "x": 1},
                epoch=1000,
            )

    def test_enqueue_open_pr_requires_head(self) -> None:
        # open_pr enqueue must include payload.head (executor requires it)
        with self.assertRaises(SchemaError):
            build_enqueue_event(
                actor="milechy",
                job_kind="open_pr",
                repo="owner/repo",
                base="main",
                payload={"title": "t", "body": "b"},
                epoch=1000,
            )

    def test_double_enqueue_same_jobId_is_violation(self) -> None:
        e1 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"head": "feature/test", "x": 1},
            epoch=1000,
            job_id="job_1000_abcd",
        )
        e2 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"head": "feature/test", "x": 2},
            epoch=1000,
            job_id="job_1000_abcd",
        )
        with self.assertRaises(InvariantViolation):
            derive_queue_state([{"type": "__init__"}, e1, e2])

    def test_event_before_enqueue_is_violation(self) -> None:
        bad = {
            "eventId": "evt_1000_a1b2",
            "ts": "2026-01-10T06:33:58Z",
            "actor": "github-actions[bot]",
            "type": "start",
            "jobId": "job_1000_c3d4",
        }
        with self.assertRaises(InvariantViolation):
            derive_queue_state([{"type": "__init__"}, bad])

    def test_illegal_transition_block_without_running(self) -> None:
        e1 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"head": "feature/test", "x": 1},
            epoch=1000,
            job_id="job_1000_c3d4",
        )
        block = {
            "eventId": "evt_1001_a1b2",
            "ts": "2026-01-10T06:34:00Z",
            "actor": "github-actions[bot]",
            "type": "block",
            "jobId": "job_1000_c3d4",
            "reason": "review_required",
        }
        with self.assertRaises(InvariantViolation):
            derive_queue_state([{"type": "__init__"}, e1, block])

    def test_bot_blocked_head_allows_cancel_only(self) -> None:
        # bot should be blocked from mutating a blocked head except cancel
        e1 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"head": "feature/test", "x": 1},
            epoch=1000,
            job_id="job_1000_blocked",
        )
        s1 = {
            "eventId": "evt_1001_s1",
            "ts": "2026-01-10T06:35:00Z",
            "actor": BOT_ACTOR,
            "type": "start",
            "jobId": "job_1000_blocked",
        }
        b1 = {
            "eventId": "evt_1002_b1",
            "ts": "2026-01-10T06:35:10Z",
            "actor": BOT_ACTOR,
            "type": "block",
            "jobId": "job_1000_blocked",
            "reason": "review_required",
        }
        state = derive_queue_state([{"type": "__init__"}, e1, s1, b1])

        # bot attempting to complete should be blocked
        with self.assertRaises(BlockedHead):
            ensure_head_can_transition(state, "job_1000_blocked", actor=BOT_ACTOR, event_type="done")

        # bot cancel should be allowed
        ensure_head_can_transition(state, "job_1000_blocked", actor=BOT_ACTOR, event_type="cancel")

    def test_bot_transition_append_blocked_head_cancel_allowed(self) -> None:
        # validate_transition_append should allow bot cancel on blocked head
        e1 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"head": "feature/test", "x": 1},
            epoch=1000,
            job_id="job_1000_blocked2",
        )
        s1 = {
            "eventId": "evt_1001_s2",
            "ts": "2026-01-10T06:35:00Z",
            "actor": BOT_ACTOR,
            "type": "start",
            "jobId": "job_1000_blocked2",
        }
        b1 = {
            "eventId": "evt_1002_b2",
            "ts": "2026-01-10T06:35:10Z",
            "actor": BOT_ACTOR,
            "type": "block",
            "jobId": "job_1000_blocked2",
            "reason": "review_required",
        }
        events = [{"type": "__init__"}, e1, s1, b1]

        cancel_ev = build_transition_event(
            actor=BOT_ACTOR,
            event_type="cancel",
            job_id="job_1000_blocked2",
            reason="auto_cleanup",
            epoch=1003,
        )

        # should not raise
        validate_transition_append(events, cancel_ev)

    def test_single_running_invariant(self) -> None:
        # Two jobs both started -> invalid
        e1 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"head": "feature/test", "x": 1},
            epoch=1000,
            job_id="job_1000_aaaa",
        )
        e2 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"head": "feature/test", "x": 2},
            epoch=1001,
            job_id="job_1001_bbbb",
        )
        s1 = {
            "eventId": "evt_1002_a1b2",
            "ts": "2026-01-10T06:35:00Z",
            "actor": "github-actions[bot]",
            "type": "start",
            "jobId": "job_1000_aaaa",
        }
        s2 = {
            "eventId": "evt_1003_c3d4",
            "ts": "2026-01-10T06:35:10Z",
            "actor": "github-actions[bot]",
            "type": "start",
            "jobId": "job_1001_bbbb",
        }
        with self.assertRaises(InvariantViolation):
            derive_queue_state([{"type": "__init__"}, e1, e2, s1, s2])

    def test_parse_jsonl_rejects_non_object(self) -> None:
        with self.assertRaises(SchemaError):
            parse_jsonl_lines(['"not an object"'])


if __name__ == "__main__":
    unittest.main()