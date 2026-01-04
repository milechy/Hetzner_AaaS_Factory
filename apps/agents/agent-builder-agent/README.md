# AgentBuilderAgent v0 (proposal-only)

Spec (YAML/JSON) -> skeleton -> PullRequestProposal(JSON)

## Run
```bash
export LLM_ROUTER_URL="http://your-router"
export LLM_ROUTER_API_KEY="..."
python -m agent_builder_agent.cli < request.json

Notes
	•	Agent is decision-only; execution is via Tool boundaries (v0 generates proposal only).
	•	LLM model selection is not performed here; only routingProfile is forwarded to LLMRouter.
	•	High-risk domains (infra/security/billing/template) are detected. v0 omits high-risk files from proposals.

---

## 14) 最低限のテスト
### `tests/test_parse_and_propose.py`
```python
import pytest

from agent_builder_agent.core.spec_parser import normalize_spec


def test_normalize_requires_name_and_purpose():
    with pytest.raises(Exception):
        normalize_spec({})
    with pytest.raises(Exception):
        normalize_spec({"name": "X"})
    ok = normalize_spec({"name": "X", "purpose": "Y"})
    assert ok.name == "X"
    assert ok.purpose == "Y"

tests/test_high_risk_filtering.py

import pytest

from agent_builder_agent.core.risk_detector import detect_high_risk, is_high_risk_path


def test_detect_high_risk_keyword():
    r = detect_high_risk({"name": "X", "purpose": "Y", "billing": "stripe"})
    assert r.high_risk_detected is True


@pytest.mark.parametrize("p,expected", [
    ("infra/main.tf", True),
    ("ops/monitoring/grafana.yaml", True),
    (".github/workflows/ci.yml", True),
    ("src/app.py", False),
])
def test_is_high_risk_path(p, expected):
    assert is_high_risk_path(p) == expected

実装上の注意（OpenAI Agents SDK との接続）
	•	本実装は Agents SDK の Agent/Runner 構造に組み込み可能な形で、ロジックを分離しています。  ￼
	•	v0 では tool 実行（shell/apply_patch 等）を一切入れていません。tool 呼び出しフロー自体は OpenAI の function/tool calling の標準フローに従います。