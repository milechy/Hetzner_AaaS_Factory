import unittest
from unittest.mock import Mock, patch

from tools.repo_lock import RepoLock, RepoLockError


class TestRepoLock(unittest.TestCase):
    def setUp(self) -> None:
        self.lock = RepoLock(
            repo="owner/repo",
            api_base="https://api.github.com",
            gh_token="tkn",
        )

    @patch("tools.repo_lock.requests.post")
    def test_acquire_ok_201(self, mock_post):
        resp = Mock()
        resp.status_code = 201
        mock_post.return_value = resp

        self.lock.acquire(sha="abc")
        self.assertTrue(mock_post.called)

    @patch("tools.repo_lock.requests.post")
    def test_acquire_conflict_422(self, mock_post):
        resp = Mock()
        resp.status_code = 422
        mock_post.return_value = resp

        with self.assertRaises(RepoLockError):
            self.lock.acquire(sha="abc")

    @patch("tools.repo_lock.requests.delete")
    def test_release_ok_204(self, mock_delete):
        resp = Mock()
        resp.status_code = 204
        mock_delete.return_value = resp

        self.lock.release()
        self.assertTrue(mock_delete.called)

    @patch("tools.repo_lock.requests.delete")
    def test_release_not_found_404(self, mock_delete):
        resp = Mock()
        resp.status_code = 404
        mock_delete.return_value = resp

        self.lock.release()  # should not raise

    @patch("tools.repo_lock.requests.delete")
    def test_release_other_error(self, mock_delete):
        resp = Mock()
        resp.status_code = 500
        mock_delete.return_value = resp

        with self.assertRaises(RepoLockError):
            self.lock.release()


if __name__ == "__main__":
    unittest.main()