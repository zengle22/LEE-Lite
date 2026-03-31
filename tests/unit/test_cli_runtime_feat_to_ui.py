from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cli.ll import main
from cli.lib.execution_return_registry import invoke_execution_return_job

ROOT = Path(__file__).resolve().parents[2]


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
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision-ui.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": candidate_ref})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-ui.json",
                "candidate_ref": candidate_ref,
            },
        )
        materialize_req = self.request_path("gate-materialize-feat-ui.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize-feat-ui.response.json")
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )

        payload = read_json(materialize_response)
        self.assertEqual(payload["data"]["formal_ref"], f"formal.ui.{run_dir}")
        self.assertEqual(payload["data"]["assigned_id"], "UI-FEAT-SRC-001-001")
        formal_path = self.workspace / "ssot" / "ui" / "SRC-001" / "UI-FEAT-SRC-001-001__homepage-advice-panel.md"
        self.assertTrue(formal_path.exists())
        formal_content = formal_path.read_text(encoding="utf-8")
        self.assertIn("ssot_type: UI", formal_content)
        self.assertIn("feat_ref: FEAT-SRC-001-001", formal_content)
        self.assertIn("Approved UI content.", formal_content)

        registry_record = read_json(self.workspace / "artifacts" / "registry" / f"formal-ui-{run_dir}.json")
        self.assertEqual(registry_record["managed_artifact_ref"], "ssot/ui/SRC-001/UI-FEAT-SRC-001-001__homepage-advice-panel.md")
        self.assertEqual(registry_record["metadata"]["target_kind"], "ui")

    def test_invoke_target_supports_execution_return_for_feat_to_ui(self) -> None:
        run_dir = "src001-ui-20260331--feat-src-001-001"
        package_dir = self.workspace / "artifacts" / "feat-to-ui" / run_dir
        input_dir = self.workspace / "artifacts" / "epic-to-feat" / "src001-input"
        package_dir.mkdir(parents=True, exist_ok=True)
        input_dir.mkdir(parents=True, exist_ok=True)
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

        scripts_dir = str((ROOT / "skills" / "ll-dev-feat-to-ui" / "scripts").resolve())
        inserted = False
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
            inserted = True
        try:
            import feat_to_ui  # type: ignore

            patch_target = patch.object(feat_to_ui, "run_workflow", return_value={"ok": True, "artifacts_dir": str(package_dir)})
            with patch_target as mocked_run:
                result = invoke_execution_return_job(
                    self.workspace,
                    trace={"run_ref": "RUN-RETURN", "workflow_key": "governance.gate-human-orchestrator"},
                    request_id="req-execution-return-ui",
                    job_ref="artifacts/jobs/waiting-human/ui-return.json",
                    job=job,
                )
        finally:
            if inserted:
                sys.path.remove(scripts_dir)

        self.assertTrue(result["ok"])
        kwargs = mocked_run.call_args.kwargs
        self.assertEqual(Path(kwargs["input_path"]), input_dir)
        self.assertEqual(kwargs["feat_ref"], "FEAT-SRC-001-001")
        self.assertEqual(kwargs["run_id"], "src001-ui-20260331")
        self.assertTrue(kwargs["allow_update"])
        self.assertEqual(Path(kwargs["revision_request_path"]), package_dir / "revision-request.json")
        revision_request = read_json(package_dir / "revision-request.json")
        self.assertEqual(revision_request["source_run_id"], run_dir)
        self.assertEqual(revision_request["candidate_ref"], candidate_ref)


if __name__ == "__main__":
    unittest.main()
