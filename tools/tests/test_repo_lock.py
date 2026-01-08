"""
Unit tests for repo_lock module.
"""
import unittest
from unittest.mock import Mock, patch
from tools.repo_lock import RepoLock, RepoLockError


class TestRepoLock(unittest.TestCase):
    
    def setUp(self):
        self.repo = "owner/repo"
        self.api_base = "https://api.github.com"
        self.gh_token = "test_token"
        self.lock_ref = "refs/heads/__factory_lock__/open_pr"
        self.lock = RepoLock(
            repo=self.repo,
            api_base=self.api_base,
            gh_token=self.gh_token,
            lock_ref=self.lock_ref
        )
        
    @patch('tools.repo_lock.requests.post')
    def test_acquire_success_201(self, mock_post):
        """Test successful lock acquisition with 201 status."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        base_sha = "abc123"
        self.lock.acquire(base_sha)
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{self.api_base}/repos/{self.repo}/git/refs")
        self.assertEqual(kwargs['json']['ref'], self.lock_ref)
        self.assertEqual(kwargs['json']['sha'], base_sha)
        self.assertIn('Authorization', kwargs['headers'])
        
    @patch('tools.repo_lock.requests.post')
    def test_acquire_success_200(self, mock_post):
        """Test successful lock acquisition with 200 status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        base_sha = "def456"
        self.lock.acquire(base_sha)
        
        mock_post.assert_called_once()
        
    @patch('tools.repo_lock.requests.post')
    def test_acquire_conflict_422(self, mock_post):
        """Test lock acquisition failure when lock is already held (422)."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_post.return_value = mock_response
        
        base_sha = "ghi789"
        with self.assertRaises(RepoLockError) as context:
            self.lock.acquire(base_sha)
        
        self.assertIn("LOCK_ALREADY_HELD", str(context.exception))
        
    @patch('tools.repo_lock.requests.post')
    def test_acquire_other_error(self, mock_post):
        """Test lock acquisition with other HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status = Mock(side_effect=Exception("Server error"))
        mock_post.return_value = mock_response
        
        base_sha = "jkl012"
        with self.assertRaises(Exception):
            self.lock.acquire(base_sha)
        
    @patch('tools.repo_lock.requests.delete')
    def test_release_success_204(self, mock_delete):
        """Test successful lock release with 204 status."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        self.lock.release()
        
        mock_delete.assert_called_once()
        args, kwargs = mock_delete.call_args
        self.assertIn("__factory_lock__/open_pr", args[0])
        self.assertIn('Authorization', kwargs['headers'])
        
    @patch('tools.repo_lock.requests.delete')
    def test_release_not_found_404(self, mock_delete):
        """Test lock release when ref doesn't exist (404) - should warn but not fail."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_delete.return_value = mock_response
        
        # Should not raise an exception
        self.lock.release()
        
        mock_delete.assert_called_once()
        
    @patch('tools.repo_lock.requests.delete')
    def test_release_other_error(self, mock_delete):
        """Test lock release with other HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status = Mock(side_effect=Exception("Server error"))
        mock_delete.return_value = mock_response
        
        with self.assertRaises(Exception):
            self.lock.release()


if __name__ == '__main__':
    unittest.main()
