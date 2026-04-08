"""Minimal contract enforcement for governed skills (ll.contract.yaml).

Today we only enforce what we can do mechanically at the CLI boundary:
- required input fields
- allowed/optional input fields (when declared)
- basic payload types (when declared)

This is intentionally small and opt-in per command handler, so that we can
incrementally harden contracts without breaking unrelated skills.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import CommandError, ensure


_TYPE_CHECKS: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


def _load_ll_contract(contract_path: Path) -> dict[str, Any]:
    ensure(contract_path.exists(), "PRECONDITION_FAILED", f"ll.contract.yaml missing: {contract_path}")
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    ensure(isinstance(payload, dict), "PRECONDITION_FAILED", f"ll.contract.yaml must be a mapping: {contract_path}")
    return payload


def enforce_ll_contract_payload(
    workspace_root: Path,
    *,
    skill_dir_ref: str,
    payload: dict[str, Any],
) -> None:
    """Validate request payload against ll.contract.yaml if rules are declared.

    Contract format supported:

    - `inputs: [fieldA, fieldB]` (required fields)
    - optional `input_payload`:
        required: [fieldA]
        optional: [fieldB]
        forbid_extra: true|false
        types:
          fieldA: string|boolean|array|object
    """

    contract_path = (workspace_root / skill_dir_ref / "ll.contract.yaml").resolve()
    contract = _load_ll_contract(contract_path)

    if not isinstance(payload, dict):
        raise CommandError("INVALID_REQUEST", "payload must be an object")

    declared_inputs = contract.get("inputs")
    required_fields = [str(item).strip() for item in declared_inputs] if isinstance(declared_inputs, list) else []
    required_fields = [field for field in required_fields if field]

    input_payload = contract.get("input_payload") if isinstance(contract.get("input_payload"), dict) else {}
    if input_payload:
        required_fields = [str(item).strip() for item in (input_payload.get("required") or []) if str(item).strip()]
        optional_fields = [str(item).strip() for item in (input_payload.get("optional") or []) if str(item).strip()]
        forbid_extra = bool(input_payload.get("forbid_extra"))
        types = input_payload.get("types") if isinstance(input_payload.get("types"), dict) else {}
    else:
        optional_fields = []
        forbid_extra = False
        types = {}

    for field in required_fields:
        ensure(field in payload, "INVALID_REQUEST", f"contract violation: missing required payload field: {field}")
        value = payload.get(field)
        if value in (None, ""):
            raise CommandError("INVALID_REQUEST", f"contract violation: payload field must be non-empty: {field}")

    if forbid_extra:
        allowed = set(required_fields) | set(optional_fields)
        extras = sorted([key for key in payload.keys() if key not in allowed])
        ensure(not extras, "INVALID_REQUEST", f"contract violation: unexpected payload fields: {', '.join(extras)}")

    for field, type_name in types.items():
        field_name = str(field).strip()
        if not field_name or field_name not in payload:
            continue
        expected = _TYPE_CHECKS.get(str(type_name).strip())
        if expected is None:
            raise CommandError("PRECONDITION_FAILED", f"ll.contract.yaml declares unknown type for {field_name}: {type_name}")
        value = payload.get(field_name)
        if value is None:
            continue
        ensure(isinstance(value, expected), "INVALID_REQUEST", f"contract violation: payload.{field_name} must be {type_name}")

