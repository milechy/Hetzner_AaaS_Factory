import unittest
from unittest.mock import Mock, patch

from tools.repo_lock import RepoLock, RepoLockError


class TestRepoLock(unittest.TestCase):
    @patch("tools.repo_lock.requests.get")
    @patch("tools.repo_lock.requests.post")
    def test_acquire_403_pat_insufficient_scopes_classified(self, mock_post, mock_get):
        get_resp = Mock()
        get_resp.status_code = 200
        get_resp.json.return_value = []
        mock_get.return_value = get_resp

        resp = Mock()
        resp.status_code = 403
        resp.json.return_value = {
            "message": "Resource not accessible by personal access token",
            "status": "403",
        }
        mock_post.return_value = resp

        with self.assertRaises(RepoLockError) as ctx:
            self.lock.acquire(sha="abc")

        self.assertIn("TOKEN_INSUFFICIENT_FOR_GIT_REFS", str(ctx.exception))
    def setUp(self) -> None:
        self.lock = RepoLock(
            repo="owner/repo",
            api_base="https://api.github.com",
            gh_token="tkn",
            ttl_seconds=3600,
        )

    @patch("tools.repo_lock.requests.get")
    @patch("tools.repo_lock.requests.post")
    def test_acquire_ok_201(self, mock_post, mock_get):
        get_resp = Mock()
        get_resp.status_code = 200
        get_resp.json.return_value = []
        mock_get.return_value = get_resp

        resp = Mock()
        resp.status_code = 201
        mock_post.return_value = resp

        self.lock.acquire(sha="abc")
        self.assertTrue(mock_post.called)
        self.assertIsNotNone(self.lock.lock_ref)

    @patch("tools.repo_lock.requests.get")
    @patch("tools.repo_lock.requests.post")
    def test_acquire_conflict_422(self, mock_post, mock_get):
        get_resp = Mock()
        get_resp.status_code = 200
        get_resp.json.return_value = []
        mock_get.return_value = get_resp

        resp = Mock()
        resp.status_code = 422
        mock_post.return_value = resp

        with self.assertRaises(RepoLockError):
            self.lock.acquire(sha="abc")

    @patch("tools.repo_lock.time.time")
    @patch("tools.repo_lock.requests.delete")
    @patch("tools.repo_lock.requests.post")
    @patch("tools.repo_lock.requests.get")
    def test_acquire_reaps_expired_then_acquires(self, mock_get, mock_post, mock_delete, mock_time):
        self.lock.ttl_seconds = 10
        mock_time.return_value = 2000

        get_resp = Mock()
        get_resp.status_code = 200
        get_resp.json.return_value = [
            {"ref": "refs/heads/__factory_lock__/open_pr/1000"},
        ]
        mock_get.return_value = get_resp

        del_resp = Mock()
        del_resp.status_code = 204
        mock_delete.return_value = del_resp

        post_resp = Mock()
        post_resp.status_code = 201
        mock_post.return_value = post_resp

        self.lock.acquire(sha="abc")
        self.assertTrue(mock_delete.called)
        self.assertTrue(mock_post.called)
        self.assertIsNotNone(self.lock.lock_ref)

    @patch("tools.repo_lock.time.time")
    @patch("tools.repo_lock.requests.post")
    @patch("tools.repo_lock.requests.get")
    def test_acquire_blocks_when_active_lock_exists(self, mock_get, mock_post, mock_time):
        self.lock.ttl_seconds = 3600
        mock_time.return_value = 2000

        get_resp = Mock()
        get_resp.status_code = 200
        get_resp.json.return_value = [
            {"ref": "refs/heads/__factory_lock__/open_pr/1500"},
        ]
        mock_get.return_value = get_resp

        with self.assertRaises(RepoLockError):
            self.lock.acquire(sha="abc")
        self.assertFalse(mock_post.called)

    @patch("tools.repo_lock.time.time")
    @patch("tools.repo_lock.requests.delete")
    @patch("tools.repo_lock.requests.post")
    @patch("tools.repo_lock.requests.get")
    def test_acquire_fails_if_reap_delete_fails(self, mock_get, mock_post, mock_delete, mock_time):
        self.lock.ttl_seconds = 10
        mock_time.return_value = 2000

        get_resp = Mock()
        get_resp.status_code = 200
        get_resp.json.return_value = [
            {"ref": "refs/heads/__factory_lock__/open_pr/1000"},
        ]
        mock_get.return_value = get_resp

        del_resp = Mock()
        del_resp.status_code = 500
        mock_delete.return_value = del_resp

        with self.assertRaises(RepoLockError):
            self.lock.acquire(sha="abc")
        self.assertFalse(mock_post.called)

    @patch("tools.repo_lock.time.time")
    @patch("tools.repo_lock.requests.post")
    @patch("tools.repo_lock.requests.get")
    def test_acquire_retries_on_422_collision(self, mock_get, mock_post, mock_time):
        mock_time.return_value = 2000

        get_resp = Mock()
        get_resp.status_code = 200
        get_resp.json.return_value = []
        mock_get.return_value = get_resp

        r1 = Mock(); r1.status_code = 422
        r2 = Mock(); r2.status_code = 201
        mock_post.side_effect = [r1, r2]

        self.lock.acquire(sha="abc")
        self.assertEqual(mock_post.call_count, 2)

    @patch("tools.repo_lock.requests.delete")
    def test_release_ok_204(self, mock_delete):
        self.lock.lock_ref = "refs/heads/__factory_lock__/open_pr/2000"

        resp = Mock()
        resp.status_code = 204
        mock_delete.return_value = resp

        self.lock.release()
        self.assertTrue(mock_delete.called)

    @patch("tools.repo_lock.requests.delete")
    def test_release_not_found_404(self, mock_delete):
        self.lock.lock_ref = "refs/heads/__factory_lock__/open_pr/2000"

        resp = Mock()
        resp.status_code = 404
        mock_delete.return_value = resp

        self.lock.release()  # should not raise

    @patch("tools.repo_lock.requests.delete")
    def test_release_other_error(self, mock_delete):
        self.lock.lock_ref = "refs/heads/__factory_lock__/open_pr/2000"

        resp = Mock()
        resp.status_code = 500
        mock_delete.return_value = resp

        with self.assertRaises(RepoLockError):
            self.lock.release()


class TestOpenPRCLI(unittest.TestCase):
    """Tests for tools/open_pr_cli.py functionality."""

    def setUp(self):
        self.proposal = {
            "metadata": {
                "repo": "owner/external-repo",
                "baseBranch": "main",
                "proposalId": "test-123",
                "headBranch": "proposal/test-123",
                "title": "Test Proposal",
                "body": "Test body",
            },
            "changes": {
                "files": []
            }
        }

    def test_patch_only_rejected(self):
        """Test that patch-only files are rejected with PATCH_NOT_SUPPORTED."""
        from tools.open_pr_cli import apply_file_changes

        self.proposal["changes"]["files"] = [
            {"path": "test.txt", "patch": "@@ -1,1 +1,1 @@\n-old\n+new\n"}
        ]

        with self.assertRaises(SystemExit) as ctx:
            apply_file_changes(
                self.proposal,
                repo="owner/repo",
                branch_name="test-branch",
                api="https://api.github.com",
                gh_token="test-token",
                dry_run=False
            )
        self.assertEqual(ctx.exception.code, 10)

    @patch('tools.open_pr_cli.requests.put')
    @patch('tools.open_pr_cli.requests.get')
    def test_content_b64_triggers_put(self, mock_get, mock_put):
        """Test that content_b64 triggers PUT with correct URL/branch/path."""
        from tools.open_pr_cli import apply_file_changes

        self.proposal["changes"]["files"] = [
            {"path": "test.txt", "content_b64": "dGVzdCBjb250ZW50"}
        ]

        # Mock GET response (file doesn't exist)
        get_resp = Mock()
        get_resp.status_code = 404
        mock_get.return_value = get_resp

        # Mock PUT response
        put_resp = Mock()
        put_resp.status_code = 201
        put_resp.raise_for_status = Mock()
        mock_put.return_value = put_resp

        apply_file_changes(
            self.proposal,
            repo="owner/external-repo",
            branch_name="proposal/test-123",
            api="https://api.github.com",
            gh_token="test-token",
            dry_run=False
        )

        # Verify PUT was called with correct URL
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        self.assertIn("owner/external-repo", args[0])
        self.assertIn("test.txt", args[0])
        self.assertEqual(kwargs["json"]["branch"], "proposal/test-123")
        self.assertEqual(kwargs["json"]["content"], "dGVzdCBjb250ZW50")

    def test_urls_use_proposal_metadata_repo(self):
        """Test that URLs use proposal.metadata.repo (external repo)."""
        from tools.open_pr_cli import apply_file_changes

        self.proposal["metadata"]["repo"] = "external-org/external-repo"
        self.proposal["changes"]["files"] = [
            {"path": "README.md", "content_b64": "cmVhZG1l"}
        ]

        with patch('tools.open_pr_cli.requests.get') as mock_get, \
             patch('tools.open_pr_cli.requests.put') as mock_put:

            get_resp = Mock()
            get_resp.status_code = 404
            mock_get.return_value = get_resp

            put_resp = Mock()
            put_resp.status_code = 201
            put_resp.raise_for_status = Mock()
            mock_put.return_value = put_resp

            apply_file_changes(
                self.proposal,
                repo="external-org/external-repo",
                branch_name="proposal/test-123",
                api="https://api.github.com",
                gh_token="test-token",
                dry_run=False
            )

            # Verify URLs contain external repo
            args, _ = mock_put.call_args
            self.assertIn("external-org/external-repo", args[0])

    def test_dry_run_no_writes(self):
        """Test that dry-run does zero writes (no POST/PUT/DELETE)."""
        from tools.open_pr_cli import apply_file_changes

        self.proposal["changes"]["files"] = [
            {"path": "test.txt", "content_b64": "dGVzdA=="},
            {"path": "delete.txt", "delete": True},
        ]

        with patch('tools.open_pr_cli.requests.get') as mock_get, \
             patch('tools.open_pr_cli.requests.put') as mock_put, \
             patch('tools.open_pr_cli.requests.delete') as mock_delete:

            apply_file_changes(
                self.proposal,
                repo="owner/repo",
                branch_name="test-branch",
                api="https://api.github.com",
                gh_token="test-token",
                dry_run=True
            )

            # Verify no HTTP operations were performed
            mock_get.assert_not_called()
            mock_put.assert_not_called()
            mock_delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()