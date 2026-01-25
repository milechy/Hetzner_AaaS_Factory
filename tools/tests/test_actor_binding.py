"""Test actor binding validation in approval tokens."""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
from unittest.mock import patch

# Add parent directory to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from controlled_git.cli import _require_scope, CGError


@pytest.fixture
def valid_token():
    """Valid approval token with actorId."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=1)

    return {
        "id": "test-uuid",
        "issuedAt": now.isoformat().replace("+00:00", "Z"),
        "issuedBy": "human",
        "scope": {
            "repo": "owner/repo",
            "baseBranch": "main",
            "proposalHash": "sha256:abc123",
            "expiresAt": expires.isoformat().replace("+00:00", "Z"),
            "actions": ["open_pr"],
            "actorId": "milechy"
        },
        "signature": "hmac-sha256:placeholder"
    }


def test_actor_binding_success(valid_token):
    """Test successful actor binding validation."""
    # Mock signature verification to focus on actor binding
    with patch('controlled_git.cli.sign') as mock_sign:
        mock_sign.return_value = valid_token["signature"]

        # Should not raise
        _require_scope(
            valid_token,
            repo="owner/repo",
            base="main",
            action="open_pr",
            actor="milechy"
        )


def test_actor_binding_mismatch(valid_token):
    """Test actor mismatch raises APPROVAL_ACTOR_MISMATCH."""
    with pytest.raises(CGError) as exc_info:
        _require_scope(
            valid_token,
            repo="owner/repo",
            base="main",
            action="open_pr",
            actor="different_user"
        )

    assert exc_info.value.code == "APPROVAL_ACTOR_MISMATCH"
    assert "mismatch" in exc_info.value.message.lower()


def test_actor_binding_missing_in_token(valid_token):
    """Test missing actorId in token scope raises error."""
    valid_token["scope"].pop("actorId")

    with pytest.raises(CGError) as exc_info:
        _require_scope(
            valid_token,
            repo="owner/repo",
            base="main",
            action="open_pr",
            actor="milechy"
        )

    assert exc_info.value.code == "APPROVAL_ACTOR_MISMATCH"
    assert "missing" in exc_info.value.message.lower()


def test_actor_binding_numeric_string_permitted(valid_token):
    """Test numeric-only actorId strings are permitted (v1.3 spec)."""
    valid_token["scope"]["actorId"] = "12345"

    with patch('controlled_git.cli.sign') as mock_sign:
        mock_sign.return_value = valid_token["signature"]

        # Should not raise (numeric strings permitted)
        _require_scope(
            valid_token,
            repo="owner/repo",
            base="main",
            action="open_pr",
            actor="12345"
        )
