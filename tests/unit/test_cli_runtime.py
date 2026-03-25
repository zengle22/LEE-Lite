from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cli.ll import main


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CliRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        (self.workspace / "artifacts").mkdir()
        (self.workspace / "contracts" / "input").mkdir(parents=True)
        (self.workspace / ".workflow" / "runs" / "RUN-001" / "generated").mkdir(parents=True)
        (self.workspace / ".workflow" / "runs" / "RUN-001" / "generated" / "payload.txt").write_text(
            "hello world", encoding="utf-8"
        )

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

    def test_artifact_write_and_commit_flow(self) -> None:
        content_ref = ".workflow/runs/RUN-001/generated/payload.txt"
        write_request = self.build_request(
            "artifact.write",
            {
                "artifact_ref": "candidate.src",
                "workspace_path": "artifacts/active/run-001/src-candidate.md",
                "requested_mode": "create",
                "content_ref": content_ref,
            },
        )
        write_path = self.request_path("artifact-write.json")
        write_json(write_path, write_request)
        response_path = self.response_path("artifact-write.response.json")

        exit_code = self.run_cli("artifact", "write", "--request", str(write_path), "--response-out", str(response_path))
        self.assertEqual(exit_code, 0)
        response = read_json(response_path)
        self.assertEqual(response["status_code"], "OK")
        self.assertEqual(response["data"]["canonical_path"], "artifacts/active/run-001/src-candidate.md")
        self.assertTrue((self.workspace / "artifacts" / "registry" / "candidate-src.json").exists())

        read_request = self.build_request(
            "artifact.read",
            {
                "artifact_ref": "candidate.src",
                "workspace_path": "artifacts/active/run-001/src-candidate.md",
                "requested_mode": "read",
            },
        )
        read_path = self.request_path("artifact-read-denied.json")
        write_json(read_path, read_request)
        read_response = self.response_path("artifact-read-denied.response.json")
        exit_code = self.run_cli("artifact", "read", "--request", str(read_path), "--response-out", str(read_response))
        self.assertEqual(exit_code, 3)
        denied = read_json(read_response)
        self.assertEqual(denied["status_code"], "ELIGIBILITY_DENIED")

        commit_request = self.build_request(
            "artifact.commit",
            {
                "artifact_ref": "candidate.src",
                "workspace_path": "artifacts/active/run-001/src-candidate.md",
                "requested_mode": "commit",
                "content_ref": content_ref,
            },
        )
        commit_path = self.request_path("artifact-commit.json")
        write_json(commit_path, commit_request)
        commit_response = self.response_path("artifact-commit.response.json")
        self.assertEqual(
            self.run_cli("artifact", "commit", "--request", str(commit_path), "--response-out", str(commit_response)), 0
        )

        read_ok = self.response_path("artifact-read-ok.response.json")
        exit_code = self.run_cli("artifact", "read", "--request", str(read_path), "--response-out", str(read_ok))
        self.assertEqual(exit_code, 0)
        ok = read_json(read_ok)
        self.assertEqual(ok["data"]["content"], "hello world")

    def test_policy_denies_code_root_write(self) -> None:
        request = self.build_request(
            "artifact.write",
            {
                "artifact_ref": "code.bad",
                "workspace_path": "cli/hack.py",
                "requested_mode": "create",
                "content_ref": ".workflow/runs/RUN-001/generated/payload.txt",
            },
        )
        req = self.request_path("artifact-bad.json")
        write_json(req, request)
        response = self.response_path("artifact-bad.response.json")
        exit_code = self.run_cli("artifact", "write", "--request", str(req), "--response-out", str(response))
        self.assertEqual(exit_code, 3)
        payload = read_json(response)
        self.assertEqual(payload["status_code"], "POLICY_DENIED")

    def test_registry_bind_and_verify(self) -> None:
        bind_request = self.build_request(
            "registry.bind-record",
            {
                "artifact_ref": "formal.epic",
                "managed_artifact_ref": "artifacts/active/formal-epic.json",
                "status": "materialized",
                "lineage": ["gate-decision-001"],
            },
        )
        req = self.request_path("registry-bind.json")
        write_json(req, bind_request)
        response = self.response_path("registry-bind.response.json")
        self.assertEqual(self.run_cli("registry", "bind-record", "--request", str(req), "--response-out", str(response)), 0)

        verify_request = self.build_request(
            "registry.verify-eligibility",
            {"artifact_ref": "formal.epic", "admission_context": {"consumer": "test"}, "lineage_expectation": "gate-decision-001"},
        )
        verify = self.request_path("registry-verify.json")
        write_json(verify, verify_request)
        verify_response = self.response_path("registry-verify.response.json")
        self.assertEqual(
            self.run_cli("registry", "verify-eligibility", "--request", str(verify), "--response-out", str(verify_response)),
            0,
        )
        payload = read_json(verify_response)
        self.assertEqual(payload["data"]["eligibility_result"], "eligible")

    def test_audit_emits_bypass_findings(self) -> None:
        request = self.build_request(
            "audit.emit-finding-bundle",
            {
                "workspace_diff_ref": "artifacts/active/diff.json",
                "gateway_receipt_refs": [],
                "registry_refs": [],
                "policy_verdict_refs": [],
                "attempted_unmanaged_reads": ["scratch/untracked.md"],
                "bypass_write_paths": ["scratch/out.md"],
            },
        )
        req = self.request_path("audit.json")
        write_json(req, request)
        response = self.response_path("audit.response.json")
        self.assertEqual(
            self.run_cli("audit", "emit-finding-bundle", "--request", str(req), "--response-out", str(response)), 0
        )
        payload = read_json(response)
        self.assertEqual(payload["data"]["severity_summary"]["blocker"], 2)
        self.assertEqual(payload["data"]["canonical_path"], "artifacts/active/audit/finding-bundle.json")

    def test_gate_package_and_evaluate(self) -> None:
        package_request = self.build_request(
            "gate.create",
            {
                "candidate_ref": "artifacts/active/run-001/candidate.json",
                "acceptance_ref": "artifacts/active/run-001/acceptance.json",
                "evidence_bundle_ref": "artifacts/active/run-001/evidence.json",
            },
        )
        package_req = self.request_path("gate-create.json")
        write_json(package_req, package_request)
        package_response = self.response_path("gate-create.response.json")
        self.assertEqual(self.run_cli("gate", "create", "--request", str(package_req), "--response-out", str(package_response)), 0)

        audit_bundle = self.workspace / "artifacts" / "active" / "audit" / "finding-bundle.json"
        write_json(audit_bundle, {"findings": []})
        evaluate_request = self.build_request(
            "gate.evaluate",
            {
                "gate_ready_package_ref": "artifacts/active/gates/packages/gate-ready-package.json",
                "audit_finding_refs": ["artifacts/active/audit/finding-bundle.json"],
                "target_matrix": {"allowed_targets": ["materialized_handoff", "materialized_job", "run_closure"]},
            },
        )
        evaluate_req = self.request_path("gate-evaluate.json")
        write_json(evaluate_req, evaluate_request)
        evaluate_response = self.response_path("gate-evaluate.response.json")
        self.assertEqual(
            self.run_cli("gate", "evaluate", "--request", str(evaluate_req), "--response-out", str(evaluate_response)), 0
        )
        payload = read_json(evaluate_response)
        self.assertEqual(payload["data"]["gate_decision_ref"], "artifacts/active/gates/decisions/gate-decision.json")

    def test_gate_evaluate_respects_guarded_disable(self) -> None:
        request = self.build_request(
            "gate.evaluate",
            {
                "gate_ready_package_ref": "artifacts/active/gates/packages/gate-ready-package.json",
                "audit_finding_refs": [],
                "target_matrix": {"allowed_targets": ["materialized_handoff"]},
                "guard_required": True,
            },
        )
        req = self.request_path("gate-guarded.json")
        write_json(req, request)
        response = self.response_path("gate-guarded.response.json")
        exit_code = self.run_cli("gate", "evaluate", "--request", str(req), "--response-out", str(response))
        self.assertEqual(exit_code, 4)
        payload = read_json(response)
        self.assertEqual(payload["status_code"], "PROVISIONAL_SLICE_DISABLED")

    def test_gate_materialize_dispatch_and_close(self) -> None:
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json"
        write_json(decision_path, {"decision_type": "approve"})

        materialize_request = self.build_request(
            "gate.materialize", {"gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json"}
        )
        materialize_req = self.request_path("gate-materialize.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize.response.json")
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )

        dispatch_request = self.build_request(
            "gate.dispatch", {"gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json"}
        )
        dispatch_req = self.request_path("gate-dispatch.json")
        write_json(dispatch_req, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch.response.json")
        self.assertEqual(self.run_cli("gate", "dispatch", "--request", str(dispatch_req), "--response-out", str(dispatch_response)), 0)

        close_request = self.build_request("gate.close-run", {"run_ref": "RUN-001"})
        close_req = self.request_path("gate-close.json")
        write_json(close_req, close_request)
        close_response = self.response_path("gate-close.response.json")
        self.assertEqual(self.run_cli("gate", "close-run", "--request", str(close_req), "--response-out", str(close_response)), 0)
        payload = read_json(close_response)
        self.assertEqual(payload["data"]["run_closure_ref"], "artifacts/active/closures/run-closure.json")

    def test_rollout_readiness_core_and_guarded(self) -> None:
        request = self.build_request(
            "rollout.summarize-readiness",
            {
                "integration_matrix_ref": "ssot/impl/integration-matrix.md",
                "migration_wave_ref": "ssot/impl/migration-wave.md",
                "pilot_chain_ref": "ssot/impl/pilot-chain.md",
            },
        )
        req = self.request_path("rollout-core.json")
        write_json(req, request)
        response = self.response_path("rollout-core.response.json")
        self.assertEqual(self.run_cli("rollout", "summarize-readiness", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)
        self.assertEqual(payload["data"]["readiness_label"], "core-ready")

        guarded = self.build_request(
            "rollout.summarize-readiness",
            {
                "integration_matrix_ref": "ssot/impl/integration-matrix.md",
                "migration_wave_ref": "ssot/impl/migration-wave.md",
                "pilot_chain_ref": "ssot/impl/pilot-chain.md",
                "guarded_gate_result_ref": "artifacts/active/gates/guarded.json",
                "guarded_enabled": True,
            },
        )
        guarded_req = self.request_path("rollout-guarded.json")
        write_json(guarded_req, guarded)
        guarded_response = self.response_path("rollout-guarded.response.json")
        self.assertEqual(
            self.run_cli("rollout", "summarize-readiness", "--request", str(guarded_req), "--response-out", str(guarded_response)),
            0,
        )
        guarded_payload = read_json(guarded_response)
        self.assertEqual(guarded_payload["data"]["readiness_label"], "guarded-ready")

    def test_validate_request_command(self) -> None:
        request = self.build_request("validate.request", {"dummy": True})
        req = self.request_path("validate-request.json")
        write_json(req, request)
        response = self.response_path("validate-request.response.json")
        self.assertEqual(self.run_cli("validate", "request", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)
        self.assertEqual(payload["status_code"], "OK")


if __name__ == "__main__":
    unittest.main()

