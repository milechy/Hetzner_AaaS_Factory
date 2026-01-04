from __future__ import annotations

from dataclasses import dataclass
from typing import Any

HIGH_RISK_DOMAINS = {"infra", "security", "billing", "template"}

HIGH_RISK_KEYWORDS = {
    "infra": ["terraform", "hetzner", "coolify", "caprover", "docker-compose", "k8s", "kubernetes", "firewall"],
    "security": ["secret", "key", "token", "oauth", "sso", "encryption", "branch protection", "codeowners"],
    "billing": ["stripe", "revenuecat", "billing", "invoice", "subscription", "payment"],
    "template": ["factory_templates", "templateagent", "master_", "ssot", "promote template"],
}

HIGH_RISK_PATH_PREFIXES = (
    "infra/",
    "ops/",
    ".github/",
    "templates/",
    "security/",
    "billing/",
)


@dataclass(frozen=True)
class RiskResult:
    high_risk_detected: bool
    notes: list[str]


def detect_high_risk(spec: dict[str, Any]) -> RiskResult:
    haystack = repr(spec).lower()

    notes: list[str] = []
    for domain, words in HIGH_RISK_KEYWORDS.items():
        for w in words:
            if w.lower() in haystack:
                notes.append(f"keyword:{domain}:{w}")

    # explicit flags in spec
    domains = spec.get("domains")
    if isinstance(domains, list):
        for d in domains:
            if isinstance(d, str) and d.lower() in HIGH_RISK_DOMAINS:
                notes.append(f"domain_flag:{d.lower()}")

    return RiskResult(high_risk_detected=len(notes) > 0, notes=notes)


def is_high_risk_path(path: str) -> bool:
    p = path.replace("\\", "/").lstrip("/")
    return any(p.startswith(prefix) for prefix in HIGH_RISK_PATH_PREFIXES)