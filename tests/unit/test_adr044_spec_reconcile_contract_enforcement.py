from __future__ import annotations

import pytest

from cli.lib.errors import CommandError
from cli.lib.skill_contract_enforcement import enforce_ll_contract_payload


def test_spec_reconcile_contract_rejects_unknown_payload_fields(tmp_path) -> None:
    (tmp_path / "skills" / "l3" / "ll-governance-spec-reconcile").mkdir(parents=True, exist_ok=True)
    (tmp_path / "skills" / "l3" / "ll-governance-spec-reconcile" / "ll.contract.yaml").write_text(
        "\n".join(
            [
                "schema_version: 0.1.0",
                "skill_ref: skill.governance.spec_reconcile",
                "workflow_key: governance.spec-reconcile",
                "inputs: [package_dir_ref]",
                "outputs: [spec_reconcile_report_ref]",
                "input_payload:",
                "  required: [package_dir_ref]",
                "  optional: [decisions]",
                "  forbid_extra: true",
                "  types:",
                "    package_dir_ref: string",
                "    decisions: array",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(CommandError) as excinfo:
        enforce_ll_contract_payload(
            tmp_path,
            skill_dir_ref="skills/l3/ll-governance-spec-reconcile",
            payload={"package_dir_ref": "artifacts/feat-to-tech/run-1", "unknown": 123},
        )
    assert excinfo.value.status_code == "INVALID_REQUEST"
    assert "unexpected payload fields" in excinfo.value.message


def test_spec_reconcile_contract_rejects_missing_required_fields(tmp_path) -> None:
    (tmp_path / "skills" / "l3" / "ll-governance-spec-reconcile").mkdir(parents=True, exist_ok=True)
    (tmp_path / "skills" / "l3" / "ll-governance-spec-reconcile" / "ll.contract.yaml").write_text(
        "\n".join(
            [
                "schema_version: 0.1.0",
                "skill_ref: skill.governance.spec_reconcile",
                "workflow_key: governance.spec-reconcile",
                "inputs: [package_dir_ref]",
                "outputs: [spec_reconcile_report_ref]",
                "input_payload:",
                "  required: [package_dir_ref]",
                "  forbid_extra: true",
                "  types:",
                "    package_dir_ref: string",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(CommandError) as excinfo:
        enforce_ll_contract_payload(
            tmp_path,
            skill_dir_ref="skills/l3/ll-governance-spec-reconcile",
            payload={"decisions": []},
        )
    assert excinfo.value.status_code == "INVALID_REQUEST"
    assert "missing required payload field" in excinfo.value.message


def test_spec_reconcile_contract_rejects_wrong_types(tmp_path) -> None:
    (tmp_path / "skills" / "l3" / "ll-governance-spec-reconcile").mkdir(parents=True, exist_ok=True)
    (tmp_path / "skills" / "l3" / "ll-governance-spec-reconcile" / "ll.contract.yaml").write_text(
        "\n".join(
            [
                "schema_version: 0.1.0",
                "skill_ref: skill.governance.spec_reconcile",
                "workflow_key: governance.spec-reconcile",
                "inputs: [package_dir_ref]",
                "outputs: [spec_reconcile_report_ref]",
                "input_payload:",
                "  required: [package_dir_ref]",
                "  optional: [allow_update, decisions]",
                "  forbid_extra: true",
                "  types:",
                "    package_dir_ref: string",
                "    allow_update: boolean",
                "    decisions: array",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(CommandError) as excinfo:
        enforce_ll_contract_payload(
            tmp_path,
            skill_dir_ref="skills/l3/ll-governance-spec-reconcile",
            payload={"package_dir_ref": "artifacts/x", "allow_update": "yes", "decisions": []},
        )
    assert excinfo.value.status_code == "INVALID_REQUEST"
    assert "payload.allow_update must be boolean" in excinfo.value.message

