from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ci.common import ROOT


SKILL_SCRIPT = ROOT / "skills" / "l3" / "ll-execution-loop-job-runner" / "scripts" / "runner_operator_entry.py"
SKILL_ROOT = SKILL_SCRIPT.parents[1]
INSTALL_SCRIPT = ROOT / "skills" / "ll-skill-install" / "scripts" / "install_adapter.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class RunnerSkillEntryBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module(SKILL_SCRIPT, "runner_operator_entry")
        self.install_module = load_module(INSTALL_SCRIPT, "install_adapter")
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

    def build_request(self, payload: dict) -> dict:
        return {
            "api_version": "v1",
            "command": "skill.execution-loop-job-runner",
            "request_id": "req-skill-runner-entry",
            "workspace_root": self.workspace.as_posix(),
            "actor_ref": "test-suite",
            "trace": {"run_ref": "RUN-SKILL-RUNNER-001"},
            "payload": payload,
        }

    def run_skill(self, *argv: str) -> int:
        return self.module.main(list(argv))

    def create_ready_job(self, name: str) -> str:
        job_ref = f"artifacts/jobs/ready/{name}"
        write_json(
            self.workspace / job_ref,
            {
                "job_id": Path(name).stem,
                "job_type": "next_skill",
                "status": "ready",
                "queue_path": job_ref,
                "target_skill": "workflow.dev.feat_to_tech",
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "handoff_ref": "artifacts/active/handoffs/handoff.json",
                "input_refs": ["artifacts/active/gates/decisions/gate-decision.json", "formal.feat.demo"],
                "authoritative_input_ref": "formal.feat.demo",
                "formal_ref": "formal.feat.demo",
                "published_ref": "ssot/feat/FEAT-DEMO.md",
                "source_run_id": "RUN-SKILL-RUNNER-001",
                "retry_count": 0,
                "retry_budget": 1,
                "created_at": "2026-03-27T00:00:00Z",
                "feat_ref": "FEAT-DEMO-001",
            },
        )
        return job_ref

    def test_runner_skill_bundle_start_delegates_to_loop_runtime(self) -> None:
        self.create_ready_job("job-skill-start.json")
        request = self.build_request(
            {
                "entry_mode": "start",
                "runner_scope_ref": "runner.scope.default",
                "consume_all": True,
                "runner_run_id": "runner-start-001",
            }
        )
        request_path = self.request_path("skill-runner-start.json")
        response_path = self.response_path("skill-runner-start.response.json")
        write_json(request_path, request)

        with patch(
            "cli.lib.execution_runner.invoke_target",
            return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True}},
        ):
            self.assertEqual(
                self.run_skill("invoke", "--request", str(request_path), "--response-out", str(response_path)),
                0,
            )

        payload = read_json(response_path)
        data = payload["data"]
        self.assertEqual(payload["message"], "execution runner canonical skill start completed")
        self.assertEqual(payload["command"], "skill.execution-loop-job-runner")
        self.assertEqual(data["skill_ref"], "skill.execution_loop_job_runner")
        self.assertEqual(data["runner_skill_ref"], "skill.runner.execution_loop_job_runner")
        self.assertEqual(data["entry_mode"], "start")
        self.assertEqual(data["runner_scope_ref"], "runner.scope.default")
        self.assertEqual(data["delegated_command_ref"], "ll loop run-execution")
        self.assertEqual(data["processed_count"], 1)
        self.assertTrue(data["runner_run_ref"].endswith("artifacts/active/runner/runs/runner-scope-default.json"))
        self.assertTrue(data["runner_context_ref"].endswith("artifacts/active/runner/contexts/runner-scope-default.json"))
        self.assertTrue(data["entry_receipt_ref"].endswith("artifacts/active/runner/receipts/runner-scope-default-start.json"))

    def test_runner_skill_bundle_resume_requires_context(self) -> None:
        request = self.build_request(
            {
                "entry_mode": "resume",
                "runner_scope_ref": "runner.scope.default",
            }
        )
        request_path = self.request_path("skill-runner-resume-invalid.json")
        response_path = self.response_path("skill-runner-resume-invalid.response.json")
        write_json(request_path, request)

        self.assertEqual(
            self.run_skill("invoke", "--request", str(request_path), "--response-out", str(response_path)),
            4,
        )

        payload = read_json(response_path)
        self.assertEqual(payload["command"], "skill.execution-loop-job-runner")
        self.assertEqual(payload["status_code"], "PRECONDITION_FAILED")
        self.assertEqual(payload["message"], "resume_target_not_found: runner context not found")

    def test_runner_skill_bundle_resume_reuses_loop_runtime(self) -> None:
        self.create_ready_job("job-skill-start-before-resume.json")
        start_request = self.build_request(
            {
                "entry_mode": "start",
                "runner_scope_ref": "runner.scope.default",
                "runner_run_id": "runner-start-ctx-001",
            }
        )
        start_request_path = self.request_path("skill-runner-resume-start.json")
        start_response_path = self.response_path("skill-runner-resume-start.response.json")
        write_json(start_request_path, start_request)
        self.assertEqual(
            self.run_skill("invoke", "--request", str(start_request_path), "--response-out", str(start_response_path)),
            0,
        )

        self.create_ready_job("job-skill-resume.json")
        resume_request = self.build_request(
            {
                "entry_mode": "resume",
                "runner_scope_ref": "runner.scope.default",
                "consume_all": True,
            }
        )
        request_path = self.request_path("skill-runner-resume.json")
        response_path = self.response_path("skill-runner-resume.response.json")
        write_json(request_path, resume_request)

        with patch(
            "cli.lib.execution_runner.invoke_target",
            return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True}},
        ):
            self.assertEqual(
                self.run_skill("invoke", "--request", str(request_path), "--response-out", str(response_path)),
                0,
            )

        payload = read_json(response_path)
        data = payload["data"]
        self.assertEqual(payload["message"], "execution runner canonical skill resume completed")
        self.assertEqual(data["entry_mode"], "resume")
        self.assertEqual(data["delegated_command_ref"], "ll loop resume-execution")
        self.assertEqual(data["runner_run_id"], "runner-start-ctx-001")
        self.assertTrue(data["entry_receipt_ref"].endswith("artifacts/active/runner/receipts/runner-scope-default-resume.json"))

    def test_runner_skill_bundle_validate_input_and_output(self) -> None:
        request = self.build_request(
            {
                "entry_mode": "start",
                "runner_scope_ref": "runner.scope.default",
            }
        )
        request_path = self.request_path("skill-runner-validate.json")
        response_path = self.response_path("skill-runner-validate.response.json")
        write_json(request_path, request)

        with patch(
            "cli.lib.execution_runner.invoke_target",
            return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True}},
        ):
            self.assertEqual(self.run_skill("validate-input", "--request", str(request_path)), 0)
            self.assertEqual(
                self.run_skill("invoke", "--request", str(request_path), "--response-out", str(response_path)),
                0,
            )
            self.assertEqual(self.run_skill("validate-output", "--response", str(response_path)), 0)
            self.assertEqual(self.run_skill("freeze-guard", "--response", str(response_path)), 0)

    def test_runner_skill_bundle_evidence_out_persists_delegated_response(self) -> None:
        self.create_ready_job("job-skill-evidence.json")
        request = self.build_request(
            {
                "entry_mode": "start",
                "runner_scope_ref": "runner.scope.default",
                "consume_all": True,
            }
        )
        request_path = self.request_path("skill-runner-evidence.json")
        response_path = self.response_path("skill-runner-evidence.response.json")
        evidence_path = self.response_path("skill-runner-evidence.evidence.json")
        write_json(request_path, request)

        with patch(
            "cli.lib.execution_runner.invoke_target",
            return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True}},
        ):
            self.assertEqual(
                self.run_skill(
                    "invoke",
                    "--request",
                    str(request_path),
                    "--response-out",
                    str(response_path),
                    "--evidence-out",
                    str(evidence_path),
                ),
                0,
            )

        evidence = read_json(evidence_path)
        delegated_path = self.workspace / evidence["delegated_response_ref"]
        self.assertTrue(delegated_path.exists())
        delegated = read_json(delegated_path)
        self.assertEqual(delegated["command"], "loop.run-execution")

    def test_runner_skill_bundle_invoke_rejects_invalid_skill_request(self) -> None:
        request = self.build_request(
            {
                "entry_mode": "start",
            }
        )
        request["command"] = "loop.run-execution"
        request_path = self.request_path("skill-runner-invalid.json")
        response_path = self.response_path("skill-runner-invalid.response.json")
        write_json(request_path, request)

        self.assertEqual(
            self.run_skill("invoke", "--request", str(request_path), "--response-out", str(response_path)),
            2,
        )

        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "INVALID_REQUEST")
        self.assertEqual(payload["command"], "skill.execution-loop-job-runner")
        self.assertIn("command must be skill.execution-loop-job-runner", payload["diagnostics"])

    def test_runner_skill_bundle_installs_as_adapter_from_layered_path(self) -> None:
        with tempfile.TemporaryDirectory() as dest_dir:
            dest_root = Path(dest_dir)
            installed = self.install_module.install_adapter(
                source_skill_dir=SKILL_ROOT,
                dest_root=dest_root,
                workspace_root=ROOT,
                replace=False,
            )
            self.assertEqual(installed.name, "ll-execution-loop-job-runner")
            skill_md = (installed / "SKILL.md").read_text(encoding="utf-8")
            openai_yaml = (installed / "agents" / "openai.yaml").read_text(encoding="utf-8")
            manifest = read_json(installed / ".codex-adapter-manifest.json")
            launcher_path = installed / "scripts" / "invoke_canonical_cli.py"
            self.assertIn("workspace-bound adapter", skill_md.lower())
            self.assertIn("ll-execution-loop-job-runner", openai_yaml)
            self.assertEqual(manifest["canonical_workspace_root"], str(ROOT.resolve()))
            self.assertEqual(manifest["canonical_skill_root"], str(SKILL_ROOT.resolve()))
            self.assertTrue(launcher_path.exists())
            self.assertIn(str(launcher_path), skill_md)
            installed_module = load_module(installed / "scripts" / "runner_operator_entry.py", "installed_runner_operator_entry")
            request = self.build_request(
                {
                    "entry_mode": "start",
                    "runner_scope_ref": "runner.scope.default",
                }
            )
            request_path = self.request_path("installed-runner-validate.json")
            write_json(request_path, request)
            self.assertEqual(installed_module.main(["validate-input", "--request", str(request_path)]), 0)

    def test_runner_skill_bundle_prefers_canonical_cli_root_over_request_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as dest_dir:
            dest_root = Path(dest_dir)
            installed = self.install_module.install_adapter(
                source_skill_dir=SKILL_ROOT,
                dest_root=dest_root,
                workspace_root=ROOT,
                replace=False,
            )
            installed_module = load_module(installed / "scripts" / "runner_operator_entry.py", "installed_runner_operator_entry_root")
            external_workspace = self.workspace / "external-project"
            (external_workspace / "cli").mkdir(parents=True)
            (external_workspace / "cli" / "ll.py").write_text("raise RuntimeError('wrong cli root')\n", encoding="utf-8")

            resolved = installed_module._resolve_cli_root(external_workspace)
            self.assertEqual(resolved, ROOT.resolve())


if __name__ == "__main__":
    unittest.main()
