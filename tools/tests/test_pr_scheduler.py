"""
Unit tests for pr_scheduler module.
"""
import unittest
from unittest.mock import Mock, patch
from tools.pr_scheduler import assert_no_open_factory_pr, PRScheduleBlocked


class TestPRScheduler(unittest.TestCase):
    
    def setUp(self):
        self.repo = "owner/repo"
        self.base_branch = "main"
        self.api_base = "https://api.github.com"
        self.gh_token = "test_token"
        
    @patch('tools.pr_scheduler.requests.get')
    def test_no_open_prs(self, mock_get):
        """Test when there are no open PRs at all."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        # Should not raise an exception
        assert_no_open_factory_pr(
            repo=self.repo,
            base_branch=self.base_branch,
            api_base=self.api_base,
            gh_token=self.gh_token
        )
        
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn(f"/repos/{self.repo}/pulls", args[0])
        self.assertEqual(kwargs['params']['state'], 'open')
        self.assertEqual(kwargs['params']['per_page'], 100)
        
    @patch('tools.pr_scheduler.requests.get')
    def test_no_matching_factory_prs(self, mock_get):
        """Test when there are open PRs but none are factory PRs on the base branch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "head": {"ref": "feature/normal-branch"},
                "base": {"ref": "main"},
                "html_url": "https://github.com/owner/repo/pull/1"
            },
            {
                "head": {"ref": "proposal/test-123"},
                "base": {"ref": "develop"},  # Different base branch
                "html_url": "https://github.com/owner/repo/pull/2"
            }
        ]
        mock_get.return_value = mock_response
        
        # Should not raise an exception
        assert_no_open_factory_pr(
            repo=self.repo,
            base_branch=self.base_branch,
            api_base=self.api_base,
            gh_token=self.gh_token
        )
        
    @patch('tools.pr_scheduler.requests.get')
    def test_factory_pr_exists_on_same_base(self, mock_get):
        """Test when a factory PR exists on the same base branch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "head": {"ref": "proposal/existing-123"},
                "base": {"ref": "main"},
                "html_url": "https://github.com/owner/repo/pull/100",
                "url": "https://api.github.com/repos/owner/repo/pulls/100"
            }
        ]
        mock_get.return_value = mock_response
        
        with self.assertRaises(PRScheduleBlocked) as context:
            assert_no_open_factory_pr(
                repo=self.repo,
                base_branch=self.base_branch,
                api_base=self.api_base,
                gh_token=self.gh_token
            )
        
        error_msg = str(context.exception)
        self.assertIn("PR_ALREADY_OPEN", error_msg)
        self.assertIn("count=1", error_msg)
        self.assertIn("base=main", error_msg)
        self.assertIn("https://github.com/owner/repo/pull/100", error_msg)
        
    @patch('tools.pr_scheduler.requests.get')
    def test_multiple_factory_prs_on_same_base(self, mock_get):
        """Test when multiple factory PRs exist on the same base branch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "head": {"ref": "proposal/first-123"},
                "base": {"ref": "main"},
                "html_url": "https://github.com/owner/repo/pull/100"
            },
            {
                "head": {"ref": "proposal/second-456"},
                "base": {"ref": "main"},
                "html_url": "https://github.com/owner/repo/pull/101"
            },
            {
                "head": {"ref": "feature/normal"},
                "base": {"ref": "main"},
                "html_url": "https://github.com/owner/repo/pull/102"
            }
        ]
        mock_get.return_value = mock_response
        
        with self.assertRaises(PRScheduleBlocked) as context:
            assert_no_open_factory_pr(
                repo=self.repo,
                base_branch=self.base_branch,
                api_base=self.api_base,
                gh_token=self.gh_token
            )
        
        error_msg = str(context.exception)
        self.assertIn("PR_ALREADY_OPEN", error_msg)
        self.assertIn("count=2", error_msg)
        self.assertIn("base=main", error_msg)
        self.assertIn("https://github.com/owner/repo/pull/100", error_msg)
        
    @patch('tools.pr_scheduler.requests.get')
    def test_api_error_non_200(self, mock_get):
        """Test when GitHub API returns non-200 status (Fail-Safe: should not raise)."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        
        # Should NOT raise - fail-safe behavior
        assert_no_open_factory_pr(
            repo=self.repo,
            base_branch=self.base_branch,
            api_base=self.api_base,
            gh_token=self.gh_token
        )
        
    @patch('tools.pr_scheduler.requests.get')
    def test_api_error_500(self, mock_get):
        """Test when GitHub API returns 500 status (Fail-Safe: should not raise)."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        # Should NOT raise - fail-safe behavior
        assert_no_open_factory_pr(
            repo=self.repo,
            base_branch=self.base_branch,
            api_base=self.api_base,
            gh_token=self.gh_token
        )
        
    @patch('tools.pr_scheduler.requests.get')
    def test_api_exception(self, mock_get):
        """Test when GitHub API request raises exception (Fail-Safe: should not raise)."""
        mock_get.side_effect = Exception("Network error")
        
        # Should NOT raise - fail-safe behavior
        assert_no_open_factory_pr(
            repo=self.repo,
            base_branch=self.base_branch,
            api_base=self.api_base,
            gh_token=self.gh_token
        )


if __name__ == '__main__':
    unittest.main()
