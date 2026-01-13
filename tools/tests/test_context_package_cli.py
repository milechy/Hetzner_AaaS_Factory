# tools/tests/test_context_package_cli.py
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure repository root is on sys.path so `import tools.*` works when running pytest.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import tools.context_package_cli as cli  # noqa: E402


class TestContextPackageCLIHelpers(unittest.TestCase):
    def test_queue_head_job_id(self):
        events = [
            {"type": "__init__"},
            {"type": "enqueue", "jobId": "job_1"},
            {"type": "enqueue", "jobId": "job_2"},
        ]
        self.assertEqual(cli._queue_head_job_id(events), "job_1")

    def test_job_is_blocked(self):
        events = [
            {"type": "enqueue", "jobId": "job_1"},
            {"type": "block", "jobId": "job_1"},
        ]
        self.assertTrue(cli._job_is_blocked(events, "job_1"))

        events2 = [
            {"type": "enqueue", "jobId": "job_1"},
            {"type": "block", "jobId": "job_1"},
            {"type": "unblock", "jobId": "job_1"},
        ]
        self.assertFalse(cli._job_is_blocked(events2, "job_1"))

    def test_find_existing_context_by_job_id(self):
        with tempfile.TemporaryDirectory() as d:
            os.chdir(d)
            base = Path("factory") / "contexts"
            base.mkdir(parents=True, exist_ok=True)
            p = base / "ctx_1_abcd.json"
            p.write_text(
                json.dumps({"contextId": "ctx_1_abcd", "jobId": "job_1"}), encoding="utf-8"
            )
            self.assertEqual(cli._find_existing_context_by_job_id("job_1"), "ctx_1_abcd")
            self.assertEqual(cli._find_existing_context_by_job_id("job_x"), "")


class TestContextPackageCLIMain(unittest.TestCase):
    def test_blocked_head_exits_2(self):
        events = [
            {"type": "enqueue", "jobId": "job_1"},
            {"type": "start", "jobId": "job_1"},
            {"type": "block", "jobId": "job_1"},
        ]

        with patch.object(cli, "_parse_queue_events_from_ssot", return_value=events), \
            patch.object(cli, "derive_queue_state", return_value={}), \
            patch.object(cli, "build_context_package", return_value={}), \
            patch.object(cli, "_switch_to_contexts_branch"), \
            patch.object(cli, "_push_contexts_branch"), \
            patch.object(cli, "_run_check"), \
            patch.object(cli, "RepoLock") as repo_lock_cls, \
            patch.object(cli, "_git_rev_parse", return_value="deadbeef"), \
            patch.object(cli, "_current_branch", return_value="main"), \
            patch.object(cli, "_switch_back"):

            lock = type(
                "L",
                (),
                {"acquire": lambda self, sha: None, "release": lambda self: None},
            )()
            repo_lock_cls.return_value = lock

            with patch.object(cli, "_parse_args") as parse_args:
                parse_args.return_value = type(
                    "Args",
                    (),
                    {
                        "cmd": "materialize-ssot",
                        "actor": "human",
                        "job_id": "job_1",
                        "context_id": "ctx_1_abcd",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo": "owner/repo",
                        "gh_token": "token",
                        "api_base": "https://api.github.com",
                    },
                )()

                with self.assertRaises(SystemExit) as ctx:
                    cli.main()
                self.assertEqual(ctx.exception.code, cli.EXIT_BLOCKED)

    def test_lock_fail_exits_3(self):
        events = [
            {"type": "enqueue", "jobId": "job_1"},
            {"type": "start", "jobId": "job_1"},
        ]

        class _Lock:
            def acquire(self, sha):
                raise cli.RepoLockError("REPO_LOCKED")

            def release(self):
                return None

        with patch.object(cli, "_parse_queue_events_from_ssot", return_value=events), \
            patch.object(cli, "derive_queue_state", return_value={}), \
            patch.object(cli, "_git_rev_parse", return_value="deadbeef"), \
            patch.object(cli, "RepoLock", return_value=_Lock()), \
            patch.object(cli, "_current_branch", return_value="main"), \
            patch.object(cli, "_switch_back"):

            with patch.object(cli, "_parse_args") as parse_args:
                parse_args.return_value = type(
                    "Args",
                    (),
                    {
                        "cmd": "materialize-ssot",
                        "actor": "human",
                        "job_id": "job_1",
                        "context_id": "ctx_1_abcd",
                        "created_at": "2026-01-01T00:00:00Z",
                        "repo": "owner/repo",
                        "gh_token": "token",
                        "api_base": "https://api.github.com",
                    },
                )()

                with self.assertRaises(SystemExit) as ctx:
                    cli.main()
                self.assertEqual(ctx.exception.code, cli.EXIT_LOCK_FAIL)


if __name__ == "__main__":
    unittest.main()