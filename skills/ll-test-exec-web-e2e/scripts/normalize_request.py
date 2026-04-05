#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


_SEMVER_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
_VMAJOR_RE = re.compile(r"^v(?P<major>\d+)$", re.IGNORECASE)


def _normalize_api_version(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw
    match = _VMAJOR_RE.fullmatch(raw)
    if match:
        return f"v{int(match.group('major'))}"
    match = _SEMVER_RE.fullmatch(raw)
    if match:
        return f"v{int(match.group('major'))}"
    if raw.isdigit():
        return f"v{int(raw)}"
    return raw


def _pick_first_string(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return ""


def normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    request["api_version"] = _normalize_api_version(request.get("api_version"))
    payload = request.get("payload")
    if isinstance(payload, dict):
        if not str(payload.get("test_set_ref") or "").strip() and "test_set_refs" in payload:
            payload["test_set_ref"] = _pick_first_string(payload.get("test_set_refs"))
    return request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to request json.")
    parser.add_argument("--output", required=True, help="Path to write normalized request json.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    request = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(request, dict):
        raise ValueError("request must be a JSON object")
    normalized = normalize_request(request)
    output_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

