"""v1/v2 backward compatibility and format coexistence.

Truth source: design.md §Backward Compatibility & Mixed-Chain Rules.
"""

from __future__ import annotations

from typing import Any

from frz_cli.models import FreezeStatus


def detect_format_version(data: dict[str, Any]) -> str:
    """Detect SSOT format version from raw data.

    Returns "2.0" if format_version field present, "0.x" (v1) otherwise.
    """
    fmt = data.get("format_version")
    if fmt == "2.0":
        return "2.0"
    if fmt is None:
        return "0.x"
    return str(fmt)


def check_mixed_chain(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect mixed v1/v2 references in a chain.

    Returns list of warning dicts.
    """
    versions = [detect_format_version(obj) for obj in objects]
    has_v1 = any(v == "0.x" for v in versions)
    has_v2 = any(v == "2.0" for v in versions)
    warnings: list[dict[str, Any]] = []
    if has_v1 and has_v2:
        warnings.append({
            "warning": "mixed_chain",
            "description": "SSOT chain contains both v1 and v2 format objects",
            "severity": "low",
        })
    return warnings


def adapt_v1_to_v2(v1_data: dict[str, Any]) -> dict[str, Any]:
    """Adapt v1 FRZ package dict to v2-like structure for impl-verify.

    Minimal adaptation: wrap v1 fields into v2 frozen_ssot_chain layout.
    """
    return {
        "format_version": "0.x",
        "frz_ref": v1_data.get("frz_id", "legacy"),
        "version": v1_data.get("version", "1.0"),
        "frozen_ssot_chain": {
            "src_ref": v1_data.get("frz_id", "legacy"),
            "product_boundary": v1_data.get("product_boundary", {}),
            "core_journeys": v1_data.get("core_journeys", []),
            "domain_model": v1_data.get("domain_model", []),
            "state_machine": v1_data.get("state_machine", []),
            "acceptance_contract": v1_data.get("acceptance_contract", {}),
        },
        "freeze_status": FreezeStatus.frozen.value,
    }
