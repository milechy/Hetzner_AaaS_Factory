import unittest
from unittest.mock import Mock, patch

from tools.repo_lock import RepoLock, RepoLockError


class TestRepoLock(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()