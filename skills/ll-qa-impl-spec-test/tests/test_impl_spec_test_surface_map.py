from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from impl_spec_test_skill_guard import validate_input  # noqa: E402


def _write_request(path: Path, payload: dict[str, object]) -> Path:
    request = {
        "api_version": "v1",
        "command": "skill.impl-spec-test",
        "request_id": "REQ-001",
        "workspace_root": "E:/ai/LEE-Lite-skill-first",
        "actor_ref": "actor.example",
        "trace": {},
        "payload": payload,
    }
    path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_validate_input_accepts_surface_map_and_related_refs(tmp_path: Path) -> None:
    request_path = _write_request(
        tmp_path / "request.json",
        {
            "impl_ref": "IMPL-001",
            "impl_package_ref": "impl-package-001",
            "feat_ref": "FEAT-001",
            "tech_ref": "TECH-001",
            "surface_map_ref": "SURFACE-MAP-001",
            "prototype_ref": "PROTO-001",
            "resolved_design_refs": {
                "surface_map_ref": "SURFACE-MAP-001",
                "prototype_ref": "PROTO-001",
            },
        },
    )

    assert validate_input(request_path) == 0


def test_validate_input_rejects_surface_map_without_coherence_hint(tmp_path: Path) -> None:
    request_path = _write_request(
        tmp_path / "request.json",
        {
            "impl_ref": "IMPL-001",
            "impl_package_ref": "impl-package-001",
            "feat_ref": "FEAT-001",
            "tech_ref": "TECH-001",
            "surface_map_ref": "SURFACE-MAP-001",
        },
    )

    with pytest.raises(ValueError, match="surface_map_ref requires prototype_ref or resolved_design_refs"):
        validate_input(request_path)
