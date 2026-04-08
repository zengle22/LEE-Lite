from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.lib.errors import CommandError
from cli.lib.ssot_backport_apply import (
    ParsedSsotUpdate,
    apply_ssot_updates,
    merge_decisions_with_patch_receipts,
    parse_ssot_updates,
    resolve_ssot_update_paths,
)


def test_parse_ssot_updates_requires_blocks() -> None:
    with pytest.raises(CommandError):
        parse_ssot_updates("just some prose")


def test_parse_ssot_updates_extracts_path_and_content() -> None:
    text = """
GAP-104:
说明：补齐错误码语义
path: ssot/api_contract/API-011.yaml
```yaml
error_codes:
  E_FOO: something
```
"""
    updates = parse_ssot_updates(text)
    assert updates == [
        ParsedSsotUpdate(
            finding_id="GAP-104",
            ssot_path="ssot/api_contract/API-011.yaml",
            content="error_codes:\n  E_FOO: something",
            content_format="yaml",
        )
    ]


def test_parse_ssot_updates_allows_missing_path() -> None:
    text = """
GAP-105:
说明：补齐默认语义（path omitted on purpose）
```yaml
hello: world
```
"""
    updates = parse_ssot_updates(text)
    assert updates[0].finding_id == "GAP-105"
    assert updates[0].ssot_path == ""


def test_resolve_ssot_update_paths_uses_single_candidate() -> None:
    updates = [
        ParsedSsotUpdate(
            finding_id="GAP-106",
            ssot_path="",
            content="hello: world\n",
            content_format="yaml",
        )
    ]
    resolved = resolve_ssot_update_paths(updates, target_paths_by_finding_id={"GAP-106": ["ssot/api_contract/API-106.yaml"]})
    assert resolved[0].ssot_path == "ssot/api_contract/API-106.yaml"


def test_apply_ssot_updates_writes_ssot_and_emits_receipt(tmp_path: Path) -> None:
    updates = [
        ParsedSsotUpdate(
            finding_id="GAP-200",
            ssot_path="ssot/module_spec/MOD-1.yaml",
            content="hello: world\n",
            content_format="yaml",
        )
    ]
    receipt_map = apply_ssot_updates(
        tmp_path,
        trace={"workflow_key": "governance.spec-reconcile", "run_ref": "r-1"},
        request_id="req-1",
        decided_by={"role": "ssot_owner", "ref": "alice"},
        updates=updates,
    )
    assert receipt_map["GAP-200"][0].startswith("artifacts/reports/governance/spec-backport/patch-receipts/")
    assert (tmp_path / "ssot" / "module_spec" / "MOD-1.yaml").exists()
    receipt_path = tmp_path / receipt_map["GAP-200"][0]
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "ssot_patch_receipt"
    assert payload["finding_id"] == "GAP-200"


def test_apply_ssot_updates_splits_anchor_in_paths(tmp_path: Path) -> None:
    updates = [
        ParsedSsotUpdate(
            finding_id="GAP-202",
            ssot_path="ssot/module_spec/MOD-2.yaml#section",
            content="hello: anchor\n",
            content_format="yaml",
        )
    ]
    apply_ssot_updates(
        tmp_path,
        trace={"workflow_key": "governance.spec-reconcile", "run_ref": "r-3"},
        request_id="req-3",
        decided_by={"role": "ssot_owner", "ref": "alice"},
        updates=updates,
    )
    assert (tmp_path / "ssot" / "module_spec" / "MOD-2.yaml").exists()


def test_apply_ssot_updates_rejects_paths_outside_ssot(tmp_path: Path) -> None:
    updates = [
        ParsedSsotUpdate(
            finding_id="GAP-201",
            ssot_path="artifacts/not-ssot.txt",
            content="nope",
            content_format="txt",
        )
    ]
    with pytest.raises(CommandError):
        apply_ssot_updates(
            tmp_path,
            trace={"workflow_key": "governance.spec-reconcile", "run_ref": "r-2"},
            request_id="req-2",
            decided_by={"role": "ssot_owner", "ref": "alice"},
            updates=updates,
        )


def test_merge_decisions_with_patch_receipts_marks_backported() -> None:
    decisions = [{"finding_id": "GAP-300", "outcome": "deferred", "owner": "ssot_owner", "next_checkpoint": "x"}]
    merged = merge_decisions_with_patch_receipts(
        decisions,
        receipt_map={"GAP-300": ["artifacts/reports/governance/spec-backport/patch-receipts/r.json"]},
    )
    assert merged[0]["finding_id"] == "GAP-300"
    assert merged[0]["outcome"] == "backported"
    assert merged[0]["ssot_patch_refs"] == ["artifacts/reports/governance/spec-backport/patch-receipts/r.json"]
