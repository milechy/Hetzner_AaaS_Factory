"""Test DELETE operation behavior (404 vs other errors)."""
from __future__ import annotations
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.open_pr_cli import apply_file_changes


@pytest.fixture
def delete_proposal():
    """Proposal with DELETE operation."""
    return {
        "metadata": {
            "repo": "owner/repo",
            "baseBranch": "main",
            "proposalId": "test-delete"
        },
        "changes": {
            "files": [
                {
                    "path": "to_delete.txt",
                    "delete": True
                }
            ]
        }
    }


@pytest.fixture
def mock_requests():
    """Mock requests module."""
    with patch('tools.open_pr_cli.requests') as mock:
        yield mock


def test_delete_404_warning_continue(delete_proposal, mock_requests, capsys):
    """Test DELETE on missing file (404) logs warning and continues."""
    # Mock GET (file not found)
    mock_requests.get.return_value.status_code = 404

    # Should NOT raise (404 = success)
    apply_file_changes(
        delete_proposal,
        repo="owner/repo",
        branch_name="test-branch",
        api="https://api.github.com",
        gh_token="test-token",
        dry_run=False
    )

    # Check warning logged
    captured = capsys.readouterr()
    assert "warn" in captured.out.lower()
    assert "to_delete.txt" in captured.out


def test_delete_403_abort(delete_proposal, mock_requests):
    """Test DELETE with 403 error aborts execution."""
    # Mock GET (permission denied)
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = RuntimeError("403 Forbidden")
    mock_requests.get.return_value = mock_response

    # Should raise (fail-fast)
    with pytest.raises(RuntimeError):
        apply_file_changes(
            delete_proposal,
            repo="owner/repo",
            branch_name="test-branch",
            api="https://api.github.com",
            gh_token="test-token",
            dry_run=False
        )


def test_delete_success(delete_proposal, mock_requests, capsys):
    """Test successful DELETE operation."""
    # Mock GET (file exists)
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.json.return_value = {"sha": "file-sha-123"}
    mock_requests.get.return_value = get_response

    # Mock DELETE (success)
    delete_response = MagicMock()
    delete_response.status_code = 204
    delete_response.raise_for_status = MagicMock()
    mock_requests.delete.return_value = delete_response

    apply_file_changes(
        delete_proposal,
        repo="owner/repo",
        branch_name="test-branch",
        api="https://api.github.com",
        gh_token="test-token",
        dry_run=False
    )

    # Check success logged
    captured = capsys.readouterr()
    assert "deleted" in captured.out.lower()
    assert "to_delete.txt" in captured.out
