# tools/tests/test_work_queue.py
import unittest

from tools.work_queue import (
    BOT_ACTOR,
    BlockedHead,
    HumanOnlyViolation,
    InvariantViolation,
    SchemaError,
    build_enqueue_event,
    derive_queue_state,
    parse_jsonl_lines,
)


class TestWorkQueueCore(unittest.TestCase):
    def test_enqueue_human_only(self) -> None:
        with self.assertRaises(HumanOnlyViolation):
            build_enqueue_event(
                actor=BOT_ACTOR,
                job_kind="open_pr",
                repo="owner/repo",
                base="main",
                payload={"x": 1},
                epoch=1000,
            )

    def test_double_enqueue_same_jobId_is_violation(self) -> None:
        e1 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"x": 1},
            epoch=1000,
            job_id="job_1000_abcd",
        )
        e2 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"x": 2},
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
            payload={"x": 1},
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

    def test_single_running_invariant(self) -> None:
        # Two jobs both started -> invalid
        e1 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"x": 1},
            epoch=1000,
            job_id="job_1000_aaaa",
        )
        e2 = build_enqueue_event(
            actor="milechy",
            job_kind="open_pr",
            repo="owner/repo",
            base="main",
            payload={"x": 2},
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