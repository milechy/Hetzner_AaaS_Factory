"""Test approval_request hash verification."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

# Add parent directory to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.open_pr_cli import main as open_pr_main


@pytest.fixture
def proposal_file(tmp_path):
    """Create temporary proposal file."""
    proposal = {
        "metadata": {
            "repo": "owner/repo",
            "baseBranch": "main",
            "proposalId": "test-123"
        },
        "changes": {
            "files": [
                {"path": "test.txt", "content_b64": "dGVzdA=="}
            ]
        }
    }
    file_path = tmp_path / "proposal.json"
    file_path.write_text(json.dumps(proposal))
    return str(file_path)


@pytest.fixture
def approval_token_file(tmp_path):
    """Create temporary approval token file."""
    token = {
        "id": "token-uuid",
        "scope": {
            "repo": "owner/repo",
            "baseBranch": "main",
            "proposalHash": "sha256:correct_hash",
            "expiresAt": "2026-12-31T23:59:59Z",
            "actorId": "milechy"
        },
        "signature": "hmac-sha256:test"
    }
    file_path = tmp_path / "token.json"
    file_path.write_text(json.dumps(token))
    return str(file_path)


def test_approval_hash_mismatch_exits_11(proposal_file, approval_token_file, tmp_path):
    """Test hash mismatch between approval_request and proposal exits with code 11."""
    # Create approval_request with WRONG hash
    approval_req = {
        "repo": "owner/repo",
        "baseBranch": "main",
        "normalizedProposalHash": "sha256:WRONG_HASH"
    }
    approval_req_file = tmp_path / "approval_req.json"
    approval_req_file.write_text(json.dumps(approval_req))

    with patch('sys.argv', [
        'open_pr_cli.py',
        '--proposal', proposal_file,
        '--approval-token', str(approval_token_file),
        '--approval-request', str(approval_req_file),
        '--actor', 'milechy'
    ]):
        with pytest.raises(SystemExit) as exc_info:
            open_pr_main()

        # Exit code 11 for hash mismatch
        assert exc_info.value.code == 11


def test_approval_hash_match_proceeds(proposal_file, approval_token_file, tmp_path, monkeypatch):
    """Test matching hash allows execution to proceed past hash check."""
    # Mock canonical_proposal_hash to return known value
    with patch('tools.open_pr_cli.canonical_proposal_hash') as mock_hash:
        mock_hash.return_value = "sha256:matching_hash"

        approval_req = {
            "repo": "owner/repo",
            "baseBranch": "main",
            "normalizedProposalHash": "sha256:matching_hash"
        }
        approval_req_file = tmp_path / "approval_req.json"
        approval_req_file.write_text(json.dumps(approval_req))

        # Mock environment
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("APPROVAL_HMAC_SECRET", "test-secret")

        # Mock ALL GitHub API calls
        with patch('tools.open_pr_cli.requests') as mock_requests:
            # Mock verify_approval to avoid actual token validation
            with patch('tools.open_pr_cli.verify_approval'):
                with patch('tools.open_pr_cli.assert_no_open_factory_pr'):
                    # Hash check should pass, then fail on GitHub API
                    with pytest.raises(SystemExit) as exc_info:
                        with patch('sys.argv', [
                            'open_pr_cli.py',
                            '--proposal', proposal_file,
                            '--approval-token', str(approval_token_file),
                            '--approval-request', str(approval_req_file),
                            '--actor', 'milechy'
                        ]):
                            open_pr_main()

                    # Should NOT be exit code 11 (hash mismatch)
                    # Will be different error (GitHub API mock)
                    assert exc_info.value.code != 11
