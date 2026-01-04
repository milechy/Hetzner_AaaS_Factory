from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import json
import yaml


class SpecParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedSpec:
    raw: dict[str, Any]
    name: str
    purpose: str
    steps: list[str]  # may be inferred


def _coerce_to_dict(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise SpecParseError("Spec must be a JSON object at top-level.")
    return obj


def parse_spec(*, spec_format: Literal["yaml", "json", "auto"], spec_text: str | None, spec_obj: dict[str, Any] | None) -> dict[str, Any]:
    if spec_obj is not None:
        return _coerce_to_dict(spec_obj)

    if not spec_text:
        raise SpecParseError("specText is empty and specObject is missing.")

    text = spec_text.strip()
    if spec_format == "auto":
        spec_format = "json" if text.startswith("{") else "yaml"

    try:
        if spec_format == "json":
            return _coerce_to_dict(json.loads(text))
        if spec_format == "yaml":
            data = yaml.safe_load(text)
            return _coerce_to_dict(data)
    except Exception as e:
        raise SpecParseError(str(e)) from e

    raise SpecParseError(f"Unsupported specFormat: {spec_format}")


def normalize_spec(spec: dict[str, Any]) -> ParsedSpec:
    name = spec.get("name")
    purpose = spec.get("purpose")
    if not isinstance(name, str) or not name.strip():
        raise SpecParseError("spec.name is required and must be a non-empty string.")
    if not isinstance(purpose, str) or not purpose.strip():
        raise SpecParseError("spec.purpose is required and must be a non-empty string.")

    steps_raw = spec.get("steps")
    steps: list[str] = []
    if isinstance(steps_raw, list) and all(isinstance(x, str) and x.strip() for x in steps_raw):
        steps = [x.strip() for x in steps_raw]

    return ParsedSpec(raw=spec, name=name.strip(), purpose=purpose.strip(), steps=steps)