from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cli.commands.gate.command import _ensure_proto_to_ui_gate_ready
from cli.lib.errors import CommandError


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def test_gate_blocks_proto_to_ui_when_bundle_markdown_not_expanded(tmp_path: Path) -> None:
    repo_root = tmp_path
    pkg_dir = repo_root / "artifacts" / "proto-to-ui" / "run-1"
    machine_ref = "artifacts/proto-to-ui/run-1/ui-spec-bundle.json"

    _write_text(pkg_dir / "foo.md", "# Foo\n\nbar\n")
    _write_json(
        pkg_dir / "ui-spec-bundle.json",
        {
            "artifact_type": "ui_spec_package",
            "workflow_key": "dev.proto-to-ui",
            "workflow_run_id": "run-1",
            "ui_spec_refs": ["foo.md"],
        },
    )
    _write_text(pkg_dir / "ui-spec-bundle.md", "# UI Spec Bundle\n\n- ui_spec_count: 1\n")
    _write_json(pkg_dir / "ui-spec-completeness-report.json", {"decision": "pass"})
    _write_json(pkg_dir / "ui-spec-freeze-gate.json", {"freeze_ready": True})

    ctx = SimpleNamespace(workspace_root=repo_root)
    with pytest.raises(CommandError) as exc:
        _ensure_proto_to_ui_gate_ready(ctx, candidate_ref="", machine_ssot_ref=machine_ref)
    assert exc.value.status_code == "PRECONDITION_FAILED"


def test_gate_accepts_proto_to_ui_when_bundle_markdown_embeds_refs(tmp_path: Path) -> None:
    repo_root = tmp_path
    pkg_dir = repo_root / "artifacts" / "proto-to-ui" / "run-1"
    machine_ref = "artifacts/proto-to-ui/run-1/ui-spec-bundle.json"

    _write_text(pkg_dir / "foo.md", "# Foo\n\nbar\n")
    _write_json(
        pkg_dir / "ui-spec-bundle.json",
        {
            "artifact_type": "ui_spec_package",
            "workflow_key": "dev.proto-to-ui",
            "workflow_run_id": "run-1",
            "ui_spec_refs": ["foo.md"],
        },
    )
    _write_text(
        pkg_dir / "ui-spec-bundle.md",
        "\n".join(
            [
                "# UI Spec Bundle",
                "",
                "## UI Spec Refs",
                "- foo.md",
                "",
                "## UI Specs (Embedded)",
                "",
                "### foo.md",
                "",
                "bar",
                "",
            ]
        ),
    )
    _write_json(pkg_dir / "ui-spec-completeness-report.json", {"decision": "pass"})
    _write_json(pkg_dir / "ui-spec-freeze-gate.json", {"freeze_ready": True})

    ctx = SimpleNamespace(workspace_root=repo_root)
    _ensure_proto_to_ui_gate_ready(ctx, candidate_ref="", machine_ssot_ref=machine_ref)

