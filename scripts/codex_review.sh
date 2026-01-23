#!/usr/bin/env bash
set -euo pipefail

BASE_REF="${1:-origin/main}"
git rev-parse --is-inside-work-tree >/dev/null

DIFF="$(git diff --minimal --patch --unified=3 "$BASE_REF"...HEAD)"
if [[ -z "${DIFF//[[:space:]]/}" ]]; then
  echo "No diff vs ${BASE_REF}...HEAD"
  exit 0
fi

# 低トークン固定フォーマット
PROMPT=$'You are a strict code reviewer.\n'
PROMPT+=$'Scope: review ONLY the provided git diff. Do NOT ask to inspect other files.\n'
PROMPT+=$'Do NOT propose refactors or extra scope. Focus on correctness, security, SSOT/policy compliance, and tests.\n'
PROMPT+=$'Output format (exact):\n'
PROMPT+=$'1) MUST_FIX (bullets)\n2) SHOULD_FIX (bullets)\n3) NICE_TO_HAVE (bullets)\n4) TEST_GAPS (bullets)\n5) POLICY_CHECK (bullets)\n'
PROMPT+=$'\n---BEGIN_DIFF---\n'
PROMPT+="${DIFF}"
PROMPT+=$'\n---END_DIFF---\n'

# レビュー専用
codex exec -s read-only -c 'shell_environment_policy.inherit=all' "$PROMPT"
