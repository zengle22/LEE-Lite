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
                "metadata": {"layer": "formal"},
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
        self.assertEqual(payload["data"]["gate_decision_ref"], "artifacts/active/gates/decisions/req-gate-evaluate.json")

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
        self.assertTrue(payload["data"]["run_closure_ref"].startswith("artifacts/active/closures/run-closure-"))

    def test_gate_submit_pending_and_reentry_flow(self) -> None:
        submit_request = self.build_request(
            "gate.submit-handoff",
            {
                "producer_ref": "skill.executor",
                "proposal_ref": "artifacts/active/run-001/proposal.json",
                "payload_ref": "artifacts/active/run-001/payload.json",
                "pending_state": "gate_pending",
            },
        )
        submit_req = self.request_path("gate-submit.json")
        write_json(submit_req, submit_request)
        submit_response = self.response_path("gate-submit.response.json")
        self.assertEqual(
            self.run_cli("gate", "submit-handoff", "--request", str(submit_req), "--response-out", str(submit_response)), 0
        )
        submit_payload = read_json(submit_response)
        handoff_ref = submit_payload["data"]["handoff_ref"]
        pending_request = self.build_request("gate.show-pending", {"handoff_ref": handoff_ref})
        pending_req = self.request_path("gate-pending.json")
        write_json(pending_req, pending_request)
        pending_response = self.response_path("gate-pending.response.json")
        self.assertEqual(
            self.run_cli("gate", "show-pending", "--request", str(pending_req), "--response-out", str(pending_response)), 0
        )
        pending_payload = read_json(pending_response)
        self.assertEqual(pending_payload["data"]["pending_state"], "gate_pending")
        self.assertTrue(pending_payload["data"]["assigned_gate_queue"].startswith("gate-queue-"))
        decide_request = self.build_request(
            "gate.decide",
            {
                "handoff_ref": handoff_ref,
                "proposal_ref": "artifacts/active/run-001/proposal.json",
                "decision": "revise",
                "decision_reason": "need more evidence",
            },
        )
        decide_req = self.request_path("gate-decide.json")
        write_json(decide_req, decide_request)
        decide_response = self.response_path("gate-decide.response.json")
        self.assertEqual(self.run_cli("gate", "decide", "--request", str(decide_req), "--response-out", str(decide_response)), 0)
        decide_payload = read_json(decide_response)
        self.assertTrue(decide_payload["data"]["reentry_ref"].startswith("artifacts/active/reentry/"))
        self.assertTrue((self.workspace / decide_payload["data"]["reentry_ref"]).exists())

    def test_artifact_commit_governed_and_read_governed_flow(self) -> None:
        request = self.build_request(
            "artifact.commit-governed",
            {
                "artifact_ref": "formal.runtime",
                "workspace_path": "artifacts/active/formal/runtime.json",
                "content_ref": ".workflow/runs/RUN-001/generated/payload.txt",
                "metadata": {"layer": "formal"},
            },
        )
        req = self.request_path("artifact-commit-governed.json")
        write_json(req, request)
        response = self.response_path("artifact-commit-governed.response.json")
        self.assertEqual(
            self.run_cli("artifact", "commit-governed", "--request", str(req), "--response-out", str(response)), 0
        )
        payload = read_json(response)
        self.assertEqual(payload["data"]["write_status"], "committed")
        read_request = self.build_request(
            "artifact.read-governed",
            {
                "artifact_ref": "formal.runtime",
                "workspace_path": "artifacts/active/formal/runtime.json",
            },
        )
        read_req = self.request_path("artifact-read-governed.json")
        write_json(read_req, read_request)
        read_response = self.response_path("artifact-read-governed.response.json")
        self.assertEqual(
            self.run_cli("artifact", "read-governed", "--request", str(read_req), "--response-out", str(read_response)), 0
        )
        read_payload = read_json(read_response)
        self.assertEqual(read_payload["data"]["content"], "hello world")

    def test_registry_publish_formal_and_validate_admission(self) -> None:
        publish_request = self.build_request(
            "registry.publish-formal",
            {
                "artifact_ref": "formal.epic.runtime",
                "workspace_path": "artifacts/active/formal/epic-runtime.json",
                "content_ref": ".workflow/runs/RUN-001/generated/payload.txt",
                "lineage": ["gate-decision-001"],
            },
        )
        publish_req = self.request_path("registry-publish-formal.json")
        write_json(publish_req, publish_request)
        publish_response = self.response_path("registry-publish-formal.response.json")
        self.assertEqual(
            self.run_cli("registry", "publish-formal", "--request", str(publish_req), "--response-out", str(publish_response)), 0
        )
        published = read_json(publish_response)
        self.assertEqual(published["data"]["write_status"], "materialized")
        resolve_request = self.build_request(
            "registry.resolve-formal-ref",
            {"artifact_ref": "formal.epic.runtime", "lineage_expectation": "gate-decision-001"},
        )
        resolve_req = self.request_path("registry-resolve-formal.json")
        write_json(resolve_req, resolve_request)
        resolve_response = self.response_path("registry-resolve-formal.response.json")
        self.assertEqual(
            self.run_cli("registry", "resolve-formal-ref", "--request", str(resolve_req), "--response-out", str(resolve_response)),
            0,
        )

        admission_request = self.build_request(
            "registry.validate-admission",
            {
                "artifact_ref": "formal.epic.runtime",
                "consumer_ref": "skill.consumer",
                "lineage_expectation": "gate-decision-001",
            },
        )
        admission_req = self.request_path("registry-admission.json")
        write_json(admission_req, admission_request)
        admission_response = self.response_path("registry-admission.response.json")
        self.assertEqual(
            self.run_cli("registry", "validate-admission", "--request", str(admission_req), "--response-out", str(admission_response)),
            0,
        )
        admission_payload = read_json(admission_response)
        self.assertEqual(admission_payload["data"]["admission_result"], "allow")

    def test_rollout_onboard_validate_pilot_and_submit_evidence(self) -> None:
        pilot_chain_path = self.workspace / "artifacts" / "active" / "rollout" / "pilot-chain.json"
        write_json(pilot_chain_path, {"chain": ["producer", "gate", "formal", "consumer", "audit"]})
        onboard_request = self.build_request(
            "rollout.onboard-skill",
            {
                "integration_matrix_ref": "ssot/impl/integration-matrix.md",
                "migration_wave_ref": "ssot/impl/migration-wave.md",
                "pilot_chain_ref": "artifacts/active/rollout/pilot-chain.json",
                "skill_ref": "skill.sample",
                "wave_id": "wave-001",
                "compat_mode": "read-only",
                "cutover_guard_ref": "artifacts/active/guards/cutover.json",
            },
        )
        onboard_req = self.request_path("rollout-onboard.json")
        write_json(onboard_req, onboard_request)
        onboard_response = self.response_path("rollout-onboard.response.json")
        self.assertEqual(
            self.run_cli("rollout", "onboard-skill", "--request", str(onboard_req), "--response-out", str(onboard_response)), 0
        )

        validate_request = self.build_request(
            "rollout.validate-pilot",
            {
                "integration_matrix_ref": "ssot/impl/integration-matrix.md",
                "migration_wave_ref": "ssot/impl/migration-wave.md",
                "pilot_chain_ref": "artifacts/active/rollout/pilot-chain.json",
            },
        )
        validate_req = self.request_path("rollout-validate-pilot.json")
        write_json(validate_req, validate_request)
        validate_response = self.response_path("rollout-validate-pilot.response.json")
        self.assertEqual(
            self.run_cli("rollout", "validate-pilot", "--request", str(validate_req), "--response-out", str(validate_response)),
            0,
        )
        validate_payload = read_json(validate_response)
        self.assertEqual(validate_payload["data"]["cutover_recommendation"], "proceed")

        evidence_request = self.build_request(
            "audit.submit-pilot-evidence",
            {
                "pilot_chain_ref": "artifacts/active/rollout/pilot-chain.json",
                "producer_ref": "skill.producer",
                "consumer_ref": "skill.consumer",
                "audit_ref": "artifacts/active/audit/report.json",
                "gate_ref": "artifacts/active/gates/decisions/gate-decision.json",
            },
        )
        evidence_req = self.request_path("audit-submit-pilot-evidence.json")
        write_json(evidence_req, evidence_request)
        evidence_response = self.response_path("audit-submit-pilot-evidence.response.json")
        self.assertEqual(
            self.run_cli("audit", "submit-pilot-evidence", "--request", str(evidence_req), "--response-out", str(evidence_response)),
            0,
        )
        evidence_payload = read_json(evidence_response)
        self.assertEqual(evidence_payload["data"]["evidence_status"], "sufficient")

    def test_rollout_readiness_core_and_guarded(self) -> None:
        pilot_chain = self.workspace / "artifacts" / "active" / "rollout" / "pilot-chain.json"
        pilot_chain.parent.mkdir(parents=True, exist_ok=True)
        write_json(pilot_chain, {"chain": ["producer", "gate", "formal", "consumer", "audit"]})
        validate = self.build_request(
            "rollout.validate-pilot",
            {"integration_matrix_ref": "ssot/impl/integration-matrix.md", "migration_wave_ref": "ssot/impl/migration-wave.md", "pilot_chain_ref": "artifacts/active/rollout/pilot-chain.json"},
        )
        validate_req = self.request_path("rollout-readiness-validate.json"); write_json(validate_req, validate)
        validate_response = self.response_path("rollout-readiness-validate.response.json")
        self.assertEqual(self.run_cli("rollout", "validate-pilot", "--request", str(validate_req), "--response-out", str(validate_response)), 0)
        request = self.build_request(
            "rollout.summarize-readiness",
            {
                "integration_matrix_ref": "ssot/impl/integration-matrix.md",
                "migration_wave_ref": "ssot/impl/migration-wave.md",
                "pilot_chain_ref": "artifacts/active/rollout/pilot-chain.json",
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
                "pilot_chain_ref": "artifacts/active/rollout/pilot-chain.json",
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

