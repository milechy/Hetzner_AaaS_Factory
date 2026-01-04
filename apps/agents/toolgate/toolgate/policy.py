from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from toolgate.models import PolicyDoc


class PolicyLoadError(RuntimeError):
    pass


class PolicyStore:
    def __init__(self, *, policies_dir: Path) -> None:
        self._dir = policies_dir

    def load(self, policy_version: str) -> PolicyDoc:
        # convention: {policy_version}.yaml
        path = self._dir / f"{policy_version}.yaml"
        if not path.exists():
            raise PolicyLoadError(f"Policy not found: {path}")

        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            doc = PolicyDoc.model_validate(data)
            return doc
        except Exception as e:
            raise PolicyLoadError(f"Failed to load policy '{policy_version}': {e}") from e