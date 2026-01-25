"""Test actor binding validation in approval tokens."""
from __future__ import annotations
import json
import os
import pytest
from unittest.mock import patch
from controlled_git.cli import verify_token, _require_scope, CGError


@pytest.fixture
def valid_token():
    """Valid approval token with actorId."""
    return {
        "id": "test-uuid",
        "issuedAt": "2026-01-25T00:00:00Z",
        "issuedBy": "human",
        "scope": {
            "repo": "owner/repo",
            "baseBranch": "main",
            "proposalHash": "sha256:abc123",
            "expiresAt": "2026-01-26T00:00:00Z",
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
