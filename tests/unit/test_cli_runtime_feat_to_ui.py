from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cli.ll import main
from cli.lib.errors import CommandError
from cli.lib.execution_return_registry import invoke_execution_return_job


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CliRuntimeFeatToUiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        (self.workspace / "artifacts").mkdir()
        (self.workspace / "contracts" / "input").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def request_path(self, name: str) -> Path:
        return self.workspace / "contracts" / "input" / name

    def response_path(self, name: str) -> Path:
        return self.workspace / "artifacts" / "active" / name

    def build_request(self, command: str, payload: dict) -> dict:
        return {
            "api_version": "v1",
            "command": command,
            "request_id": f"req-{command.replace('.', '-')}",
            "workspace_root": self.workspace.as_posix(),
            "actor_ref": "test-suite",
            "trace": {"run_ref": "RUN-001"},
            "payload": payload,
        }

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def materialize(self, request_name: str, response_name: str, candidate_ref: str, decision_name: str) -> dict:
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / decision_name
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": candidate_ref})
        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": f"artifacts/active/gates/decisions/{decision_name}",
                "candidate_ref": candidate_ref,
            },
        )
        materialize_req = self.request_path(request_name)
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path(response_name)
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )
        return read_json(materialize_response)

    def test_gate_materialize_feat_to_ui_candidate_promotes_formal_ui_markdown(self) -> None:
        run_dir = "src001-ui-20260331--feat-src-001-001"
        package_dir = self.workspace / "artifacts" / "feat-to-ui" / run_dir
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "ui-spec-bundle.md").write_text("# Homepage Advice Panel\n\nApproved UI content.\n", encoding="utf-8")
        write_json(
            package_dir / "ui-spec-bundle.json",
            {
                "artifact_type": "ui_spec_package",
                "workflow_key": "dev.feat-to-ui",
                "workflow_run_id": "src001-ui-20260331",
                "title": "Homepage Advice Panel",
                "status": "pass",
                "feat_ref": "FEAT-SRC-001-001",
                "source_refs": ["FEAT-SRC-001-001", "EPIC-SRC-001-001", "SRC-001"],
            },
        )
        candidate_ref = f"feat-to-ui.{run_dir}.ui-spec-bundle"
        write_json(
            self.workspace / "artifacts" / "registry" / f"feat-to-ui-{run_dir}-ui-spec-bundle.json",
            {
                "artifact_ref": candidate_ref,
                "managed_artifact_ref": f"artifacts/feat-to-ui/{run_dir}/ui-spec-bundle.md",
                "status": "candidate",
                "trace": {"run_ref": run_dir, "workflow_key": "dev.feat-to-ui"},
                "metadata": {"layer": "candidate", "target_kind": "ui"},
                "lineage": ["FEAT-SRC-001-001"],
            },
        )
        payload = self.materialize(
            "gate-materialize-feat-ui.json",
            "gate-materialize-feat-ui.response.json",
            candidate_ref,
            "gate-decision-ui.json",
        )
        self.assertEqual(payload["data"]["formal_ref"], f"formal.ui.{run_dir}")
        self.assertEqual(payload["data"]["assigned_id"], "UI-FEAT-SRC-001-001")
        formal_path = self.workspace / "ssot" / "ui" / "SRC-001" / "UI-FEAT-SRC-001-001.md"
        self.assertTrue(formal_path.exists())
        formal_content = formal_path.read_text(encoding="utf-8")
        self.assertIn("ssot_type: UI", formal_content)
        self.assertIn("feat_ref: FEAT-SRC-001-001", formal_content)
        self.assertIn("Approved UI content.", formal_content)

        registry_record = read_json(self.workspace / "artifacts" / "registry" / f"formal-ui-{run_dir}.json")
        self.assertEqual(registry_record["managed_artifact_ref"], "ssot/ui/SRC-001/UI-FEAT-SRC-001-001.md")
        self.assertEqual(registry_record["metadata"]["target_kind"], "ui")

    def test_gate_materialize_feat_to_ui_candidate_merges_multiple_feat_slices_by_owner(self) -> None:
        owner_ref = "UI-RUNNER-OPERATOR-SHELL"
        run_specs = [
            ("src001-ui-20260407-r1--feat-src-001-001", "FEAT-SRC-001-001", "Entry Flow", "SURFACE-MAP-FEAT-SRC-001-001"),
            ("src001-ui-20260407-r1--feat-src-001-002", "FEAT-SRC-001-002", "Control Flow", "SURFACE-MAP-FEAT-SRC-001-002"),
            ("src001-ui-20260407-r1--feat-src-999-999", "FEAT-SRC-999-999", "Dirty Flow", "SURFACE-MAP-FEAT-SRC-999-999"),
        ]
        for run_dir, feat_ref, title, surface_map_ref in run_specs:
            package_dir = self.workspace / "artifacts" / "proto-to-ui" / run_dir
            package_dir.mkdir(parents=True, exist_ok=True)
            spec_name = f"[UI-{feat_ref}]__ui_spec.md"
            (package_dir / spec_name).write_text(
                f"# UI Spec {title}\n\n- feat_ref: {feat_ref}\n\n## Page Goal\n{title} goal.\n",
                encoding="utf-8",
            )
            write_json(
                package_dir / "ui-spec-bundle.json",
                {
                    "artifact_type": "ui_spec_package",
                    "workflow_key": "dev.proto-to-ui",
                    "workflow_run_id": run_dir,
                    "title": f"UI Spec Bundle for {feat_ref}",
                    "status": "pass",
                    "feat_ref": feat_ref,
                    "ui_ref": owner_ref,
                    "ui_owner_ref": owner_ref,
                    "ui_action": "update",
                    "ui_spec_refs": [spec_name],
                    "surface_map_ref": surface_map_ref,
                    "source_refs": [feat_ref, "EPIC-SRC-001-001", "SRC-001"] if feat_ref != "FEAT-SRC-999-999" else [feat_ref, "EPIC-SRC-999-001"],
                },
            )
            candidate_ref = f"candidate.ui.{run_dir}"
            write_json(
                self.workspace / "artifacts" / "registry" / f"candidate-ui-{run_dir}.json",
                {
                    "artifact_ref": candidate_ref,
                    "managed_artifact_ref": f"artifacts/proto-to-ui/{run_dir}/ui-spec-bundle.md",
                    "status": "committed",
                    "trace": {"run_ref": run_dir, "workflow_key": "dev.proto-to-ui"},
                    "metadata": {"layer": "candidate", "target_kind": "ui"},
                    "lineage": [feat_ref],
                },
            )
            (package_dir / "ui-spec-bundle.md").write_text(f"# UI Spec Bundle for {feat_ref}\n", encoding="utf-8")

        self.materialize(
            "gate-materialize-merged-ui-seed.json",
            "gate-materialize-merged-ui-seed.response.json",
            "candidate.ui.src001-ui-20260407-r1--feat-src-001-001",
            "gate-decision-ui-merged-seed.json",
        )
        payload = self.materialize(
            "gate-materialize-merged-ui.json",
            "gate-materialize-merged-ui.response.json",
            "candidate.ui.src001-ui-20260407-r1--feat-src-001-002",
            "gate-decision-ui-merged.json",
        )
        self.assertEqual(payload["data"]["assigned_id"], owner_ref)

        formal_path = self.workspace / "ssot" / "ui" / "SRC-001" / f"{owner_ref}.md"
        self.assertTrue(formal_path.exists())
        formal_content = formal_path.read_text(encoding="utf-8")
        self.assertIn("FEAT-SRC-001-001", formal_content)
        self.assertIn("FEAT-SRC-001-002", formal_content)
        self.assertIn("UI Spec Entry Flow", formal_content)
        self.assertIn("UI Spec Control Flow", formal_content)
        self.assertNotIn("FEAT-SRC-999-999", formal_content)

    def test_execution_return_rejects_deprecated_feat_to_ui_route(self) -> None:
        run_dir = "src001-ui-20260331--feat-src-001-001"
        package_dir = self.workspace / "artifacts" / "feat-to-ui" / run_dir
        package_dir.mkdir(parents=True, exist_ok=True)
        write_json(package_dir / "execution-evidence.json", {"input_path": "artifacts/epic-to-feat/src001-input"})
        write_json(package_dir / "package-manifest.json", {"feat_ref": "FEAT-SRC-001-001", "run_id": "src001-ui-20260331"})
        write_json(
            package_dir / "ui-spec-bundle.json",
            {
                "artifact_type": "ui_spec_package",
                "workflow_key": "dev.feat-to-ui",
                "workflow_run_id": "src001-ui-20260331",
                "feat_ref": "FEAT-SRC-001-001",
            },
        )
        decision_ref = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision-ui-revise.json"
        candidate_ref = f"feat-to-ui.{run_dir}.ui-spec-bundle"
        write_json(
            decision_ref,
            {
                "decision_type": "revise",
                "candidate_ref": candidate_ref,
                "decision_target": candidate_ref,
            },
        )
        job = {
            "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-ui-revise.json",
            "candidate_ref": candidate_ref,
            "decision_target": candidate_ref,
            "authoritative_input_ref": candidate_ref,
        }

        with self.assertRaises(CommandError) as ctx:
            invoke_execution_return_job(
                self.workspace,
                trace={"run_ref": "RUN-RETURN", "workflow_key": "governance.gate-human-orchestrator"},
                request_id="req-execution-return-ui",
                job_ref="artifacts/jobs/waiting-human/ui-return.json",
                job=job,
            )
        self.assertEqual(ctx.exception.status_code, "REGISTRY_MISS")
        self.assertIn("feat-to-ui", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
