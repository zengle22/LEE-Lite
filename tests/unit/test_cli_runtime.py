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
        candidate_path = self.workspace / "artifacts" / "active" / "run-001" / "candidate.json"
        write_json(
            candidate_path,
            {
                "freeze_ready": True,
                "status": "freeze_ready",
                "product_summary": "Gate review projection candidate.",
                "roles": ["reviewer", "ssot owner"],
                "main_flow": ["render projection", "review constraints", "record decision"],
                "deliverables": ["human review projection"],
                "completed_state": "Projection is ready for reviewer consumption.",
                "authoritative_output": "Machine SSOT remains the only authoritative source.",
                "frozen_downstream_boundary": "Projection does not flow into downstream inheritance.",
                "open_technical_decisions": ["Regeneration trigger timing remains explicit."],
            },
        )
        bind_request = self.build_request(
            "registry.bind-record",
            {
                "artifact_ref": "candidate.impl",
                "managed_artifact_ref": "artifacts/active/run-001/candidate.json",
                "status": "candidate",
            },
        )
        bind_req = self.request_path("gate-evaluate-bind-candidate.json")
        write_json(bind_req, bind_request)
        bind_response = self.response_path("gate-evaluate-bind-candidate.response.json")
        self.assertEqual(self.run_cli("registry", "bind-record", "--request", str(bind_req), "--response-out", str(bind_response)), 0)

        package_request = self.build_request(
            "gate.create",
            {
                "candidate_ref": "candidate.impl",
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
        self.assertEqual(payload["data"]["decision"], "approve")
        self.assertEqual(payload["data"]["decision_target"], "candidate.impl")
        self.assertEqual(payload["data"]["dispatch_target"], "formal_publication_trigger")
        self.assertEqual(payload["data"]["brief_record_ref"], "artifacts/active/gates/briefs/gate-brief-record.json")
        self.assertEqual(
            payload["data"]["pending_human_decision_ref"],
            "artifacts/active/gates/pending-human/gate-pending-human-decision.json",
        )
        self.assertEqual(payload["data"]["materialized_handoff_ref"], "artifacts/active/handoffs/materialized-handoff.json")
        decision = read_json(self.workspace / payload["data"]["gate_decision_ref"])
        self.assertEqual(decision["materialization_state"], "materialized")
        self.assertEqual(decision["decision_basis_refs"][0], payload["data"]["brief_record_ref"])
        self.assertTrue((self.workspace / payload["data"]["materialized_handoff_ref"]).exists())
        brief = read_json(self.workspace / payload["data"]["brief_record_ref"])
        self.assertEqual(brief["human_projection"]["status"], "review_visible")
        self.assertTrue(brief["human_projection"]["projection_ref"].endswith(".json"))
        block_ids = [block["id"] for block in brief["human_projection"]["review_blocks"]]
        self.assertIn("authoritative_snapshot", block_ids)
        self.assertIn("review_focus", block_ids)


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

    def test_gate_evaluate_revise_stays_in_decision_stage_and_dispatch_returns_execution_job(self) -> None:
        package_request = self.build_request(
            "gate.create",
            {
                "candidate_ref": "candidate.impl",
                "acceptance_ref": "artifacts/active/run-001/acceptance.json",
                "evidence_bundle_ref": "artifacts/active/run-001/evidence.json",
            },
        )
        package_req = self.request_path("gate-create-revise.json")
        write_json(package_req, package_request)
        package_response = self.response_path("gate-create-revise.response.json")
        self.assertEqual(self.run_cli("gate", "create", "--request", str(package_req), "--response-out", str(package_response)), 0)

        audit_bundle = self.workspace / "artifacts" / "active" / "audit" / "finding-bundle-revise.json"
        write_json(audit_bundle, {"findings": [{"severity": "blocker", "title": "missing evidence"}]})
        evaluate_request = self.build_request(
            "gate.evaluate",
            {
                "gate_ready_package_ref": "artifacts/active/gates/packages/gate-ready-package.json",
                "audit_finding_refs": ["artifacts/active/audit/finding-bundle-revise.json"],
                "target_matrix": {"allowed_targets": ["materialized_job", "run_closure"]},
            },
        )
        evaluate_req = self.request_path("gate-evaluate-revise.json")
        write_json(evaluate_req, evaluate_request)
        evaluate_response = self.response_path("gate-evaluate-revise.response.json")
        self.assertEqual(
            self.run_cli("gate", "evaluate", "--request", str(evaluate_req), "--response-out", str(evaluate_response)), 0
        )
        evaluate_payload = read_json(evaluate_response)
        self.assertEqual(evaluate_payload["data"]["decision"], "revise")
        self.assertEqual(evaluate_payload["data"]["materialized_handoff_ref"], "")

        dispatch_request = self.build_request(
            "gate.dispatch",
            {"gate_decision_ref": evaluate_payload["data"]["gate_decision_ref"]},
        )
        dispatch_req = self.request_path("gate-dispatch-revise.json")
        write_json(dispatch_req, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch-revise.response.json")
        self.assertEqual(
            self.run_cli("gate", "dispatch", "--request", str(dispatch_req), "--response-out", str(dispatch_response)),
            0,
        )
        dispatch_payload = read_json(dispatch_response)
        self.assertEqual(dispatch_payload["data"]["dispatch_status"], "dispatched")
        self.assertTrue(dispatch_payload["data"]["materialized_job_ref"].endswith("gate-decision-return.json"))
        self.assertEqual(dispatch_payload["data"]["materialized_handoff_ref"], "")

    def test_gate_materialize_dispatch_and_close(self) -> None:
        candidate_path = self.workspace / "artifacts" / "active" / "run-001" / "candidate.json"
        write_json(candidate_path, {"candidate": True})
        bind_request = self.build_request(
            "registry.bind-record",
            {
                "artifact_ref": "candidate.impl",
                "managed_artifact_ref": "artifacts/active/run-001/candidate.json",
                "status": "candidate",
            },
        )
        bind_req = self.request_path("registry-bind-candidate.json")
        write_json(bind_req, bind_request)
        bind_response = self.response_path("registry-bind-candidate.response.json")
        self.assertEqual(self.run_cli("registry", "bind-record", "--request", str(bind_req), "--response-out", str(bind_response)), 0)

        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": "candidate.impl"})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "candidate_ref": "candidate.impl",
                "target_formal_kind": "handoff",
            },
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
        dispatch_payload = read_json(dispatch_response)
        self.assertEqual(dispatch_payload["data"]["dispatch_status"], "dispatched")
        self.assertEqual(dispatch_payload["data"]["materialized_handoff_ref"], "artifacts/active/handoffs/materialized-handoff.json")
        self.assertEqual(dispatch_payload["data"]["materialized_job_ref"], "")

        close_request = self.build_request("gate.close-run", {"run_ref": "RUN-001"})
        close_req = self.request_path("gate-close.json")
        write_json(close_req, close_request)
        close_response = self.response_path("gate-close.response.json")
        self.assertEqual(self.run_cli("gate", "close-run", "--request", str(close_req), "--response-out", str(close_response)), 0)
        payload = read_json(close_response)
        self.assertEqual(payload["data"]["run_closure_ref"], "artifacts/active/closures/run-closure.json")

    def test_gate_materialize_raw_to_src_candidate_promotes_formal_src_markdown(self) -> None:
        run_id = "raw-src-run"
        candidate_path = self.workspace / "artifacts" / "raw-to-src" / run_id / "src-candidate.md"
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text("# SRC Candidate\n\nApproved content.\n", encoding="utf-8")
        write_json(
            self.workspace / "artifacts" / "registry" / f"raw-to-src-{run_id}-src-candidate.json",
            {
                "artifact_ref": f"raw-to-src.{run_id}.src-candidate",
                "managed_artifact_ref": f"artifacts/raw-to-src/{run_id}/src-candidate.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "product.raw-to-src"},
                "metadata": {"layer": "formal"},
                "lineage": [],
            },
        )
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": f"raw-to-src.{run_id}.src-candidate"})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "candidate_ref": f"raw-to-src.{run_id}.src-candidate",
            },
        )
        materialize_req = self.request_path("gate-materialize-raw-src.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize-raw-src.response.json")
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )

        payload = read_json(materialize_response)
        self.assertEqual(payload["data"]["formal_ref"], f"formal.src.{run_id}")
        self.assertEqual(payload["data"]["assigned_id"], "SRC-001")
        formal_path = self.workspace / "ssot" / "src" / "SRC-001__src-candidate.md"
        self.assertTrue(formal_path.exists())
        formal_content = formal_path.read_text(encoding="utf-8")
        self.assertIn("id: SRC-001", formal_content)
        self.assertIn("ssot_type: SRC", formal_content)
        self.assertIn("gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json", formal_content)
        self.assertIn("Approved content.", formal_content)

        registry_record = read_json(self.workspace / "artifacts" / "registry" / f"formal-src-{run_id}.json")
        self.assertEqual(registry_record["managed_artifact_ref"], "ssot/src/SRC-001__src-candidate.md")
        self.assertEqual(registry_record["status"], "materialized")
        self.assertEqual(registry_record["metadata"]["assigned_id"], "SRC-001")

        materialized_ssot = read_json(self.workspace / payload["data"]["materialized_ssot_ref"])
        self.assertEqual(materialized_ssot["assigned_id"], "SRC-001")
        self.assertEqual(materialized_ssot["output_path"], "ssot/src/SRC-001__src-candidate.md")
        self.assertEqual(materialized_ssot["gate_decision_ref"], "artifacts/active/gates/decisions/gate-decision.json")

        handoff = read_json(self.workspace / payload["data"]["materialized_handoff_ref"])
        self.assertEqual(handoff["formal_ref"], f"formal.src.{run_id}")
        self.assertEqual(handoff["published_ref"], "ssot/src/SRC-001__src-candidate.md")

    def test_gate_materialize_src_to_epic_candidate_promotes_formal_epic_markdown(self) -> None:
        run_id = "src-epic-run"
        package_dir = self.workspace / "artifacts" / "src-to-epic" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        markdown_text = "\n".join(
            [
                "---",
                "artifact_type: epic_freeze_package",
                "workflow_key: product.src-to-epic",
                f"workflow_run_id: {run_id}",
                "title: Governance Runtime EPIC",
                "status: accepted",
                "epic_freeze_ref: EPIC-SRC-001-GOVERNANCE-RUNTIME",
                "src_root_id: SRC-001",
                "source_refs:",
                "  - SRC-001",
                "  - ADR-005",
                "---",
                "",
                "# Governance Runtime EPIC",
                "",
                "Approved EPIC content.",
            ]
        )
        (package_dir / "epic-freeze.md").write_text(markdown_text + "\n", encoding="utf-8")
        write_json(
            package_dir / "epic-freeze.json",
            {
                "artifact_type": "epic_freeze_package",
                "workflow_key": "product.src-to-epic",
                "workflow_run_id": run_id,
                "title": "Governance Runtime EPIC",
                "status": "accepted",
                "schema_version": "1.0.0",
                "epic_freeze_ref": "EPIC-SRC-001-GOVERNANCE-RUNTIME",
                "src_root_id": "SRC-001",
                "business_goal": "Unify governed runtime admission and downstream delivery.",
                "scope": ["Formal EPIC publication", "Downstream admission"],
                "source_refs": ["SRC-001", "ADR-005"],
                "prerequisite_foundations": ["SRC-001", "ADR-005"],
            },
        )
        write_json(package_dir / "epic-acceptance-report.json", {"summary": "EPIC acceptance is approved."})
        write_json(
            self.workspace / "artifacts" / "registry" / f"src-to-epic-{run_id}-epic-freeze.json",
            {
                "artifact_ref": f"src-to-epic.{run_id}.epic-freeze",
                "managed_artifact_ref": f"artifacts/src-to-epic/{run_id}/epic-freeze.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "product.src-to-epic"},
                "metadata": {"layer": "formal"},
                "lineage": [],
            },
        )
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": f"src-to-epic.{run_id}.epic-freeze"})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "candidate_ref": f"src-to-epic.{run_id}.epic-freeze",
            },
        )
        materialize_req = self.request_path("gate-materialize-src-epic.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize-src-epic.response.json")
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )

        payload = read_json(materialize_response)
        self.assertEqual(payload["data"]["formal_ref"], f"formal.epic.{run_id}")
        self.assertEqual(payload["data"]["assigned_id"], "EPIC-001")
        formal_path = self.workspace / "ssot" / "epic" / "EPIC-001__governance-runtime-epic.md"
        self.assertTrue(formal_path.exists())
        formal_content = formal_path.read_text(encoding="utf-8")
        self.assertIn("id: EPIC-001", formal_content)
        self.assertIn("ssot_type: EPIC", formal_content)
        self.assertIn("src_ref: SRC-001", formal_content)
        self.assertIn("acceptance_summary: EPIC acceptance is approved.", formal_content)
        self.assertIn("Approved EPIC content.", formal_content)

        registry_record = read_json(self.workspace / "artifacts" / "registry" / f"formal-epic-{run_id}.json")
        self.assertEqual(
            registry_record["managed_artifact_ref"],
            "ssot/epic/EPIC-001__governance-runtime-epic.md",
        )
        self.assertEqual(registry_record["status"], "materialized")
        self.assertEqual(registry_record["metadata"]["assigned_id"], "EPIC-001")
        self.assertEqual(registry_record["metadata"]["source_package_ref"], f"artifacts/src-to-epic/{run_id}")

        materialized_epic = read_json(self.workspace / payload["data"]["materialized_ssot_ref"])
        self.assertEqual(materialized_epic["assigned_id"], "EPIC-001")
        self.assertEqual(
            materialized_epic["output_path"],
            "ssot/epic/EPIC-001__governance-runtime-epic.md",
        )
        self.assertEqual(materialized_epic["gate_decision_ref"], "artifacts/active/gates/decisions/gate-decision.json")

        handoff = read_json(self.workspace / payload["data"]["materialized_handoff_ref"])
        self.assertEqual(handoff["formal_ref"], f"formal.epic.{run_id}")
        self.assertEqual(
            handoff["published_ref"],
            "ssot/epic/EPIC-001__governance-runtime-epic.md",
        )

    def test_gate_materialize_src_to_epic_candidate_uses_ascii_slug_for_mixed_language_title(self) -> None:
        run_id = "src-epic-mixed-title-run"
        epic_dir = self.workspace / "ssot" / "epic"
        epic_dir.mkdir(parents=True, exist_ok=True)
        (epic_dir / "EPIC-001__existing-epic.md").write_text("---\nid: EPIC-001\nssot_type: EPIC\n---\n\n# Existing\n", encoding="utf-8")
        package_dir = self.workspace / "artifacts" / "src-to-epic" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        markdown_text = "\n".join(
            [
                "---",
                "artifact_type: epic_freeze_package",
                "workflow_key: product.src-to-epic",
                f"workflow_run_id: {run_id}",
                "title: Gate 审批后自动推进 Execution Runner 统一能力",
                "status: accepted",
                "epic_freeze_ref: EPIC-GATE-EXECUTION-RUNNER",
                "src_root_id: SRC-003",
                "source_refs:",
                "  - SRC-003",
                "  - ADR-018",
                "---",
                "",
                "# Gate 审批后自动推进 Execution Runner 统一能力",
                "",
                "Approved EPIC content.",
            ]
        )
        (package_dir / "epic-freeze.md").write_text(markdown_text + "\n", encoding="utf-8")
        write_json(
            package_dir / "epic-freeze.json",
            {
                "artifact_type": "epic_freeze_package",
                "workflow_key": "product.src-to-epic",
                "workflow_run_id": run_id,
                "title": "Gate 审批后自动推进 Execution Runner 统一能力",
                "status": "accepted",
                "schema_version": "1.0.0",
                "epic_freeze_ref": "EPIC-GATE-EXECUTION-RUNNER",
                "src_root_id": "SRC-003",
                "source_refs": ["SRC-003", "ADR-018"],
            },
        )
        write_json(
            self.workspace / "artifacts" / "registry" / f"src-to-epic-{run_id}-epic-freeze.json",
            {
                "artifact_ref": f"src-to-epic.{run_id}.epic-freeze",
                "managed_artifact_ref": f"artifacts/src-to-epic/{run_id}/epic-freeze.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "product.src-to-epic"},
                "metadata": {"layer": "formal"},
                "lineage": [],
            },
        )
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": f"src-to-epic.{run_id}.epic-freeze"})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "candidate_ref": f"src-to-epic.{run_id}.epic-freeze",
            },
        )
        materialize_req = self.request_path("gate-materialize-src-epic-mixed-title.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize-src-epic-mixed-title.response.json")
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )

        payload = read_json(materialize_response)
        expected_ref = "ssot/epic/EPIC-002__gate-execution-runner.md"
        self.assertEqual(payload["data"]["assigned_id"], "EPIC-002")
        self.assertEqual(payload["data"]["published_ref"], expected_ref)
        formal_path = self.workspace / "ssot" / "epic" / "EPIC-002__gate-execution-runner.md"
        self.assertTrue(formal_path.exists())
        registry_record = read_json(self.workspace / "artifacts" / "registry" / f"formal-epic-{run_id}.json")
        self.assertEqual(registry_record["managed_artifact_ref"], expected_ref)
        self.assertEqual(registry_record["metadata"]["assigned_id"], "EPIC-002")

    def test_gate_materialize_epic_to_feat_candidate_promotes_formal_feat_markdown_and_dispatches_jobs(self) -> None:
        run_id = "epic-feat-run"
        package_dir = self.workspace / "artifacts" / "epic-to-feat" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "feat-freeze-bundle.md").write_text("# FEAT Bundle\n", encoding="utf-8")
        write_json(
            package_dir / "feat-freeze-bundle.json",
            {
                "artifact_type": "feat_freeze_package",
                "workflow_key": "product.epic-to-feat",
                "workflow_run_id": run_id,
                "title": "Governed FEAT Bundle",
                "status": "accepted",
                "schema_version": "1.0.0",
                "epic_freeze_ref": "EPIC-SRC001",
                "src_root_id": "SRC-001",
                "source_refs": ["product.epic-to-feat::epic-feat-run", "EPIC-SRC001", "SRC-001"],
                "features": [
                    {
                        "feat_ref": "FEAT-SRC-001-301",
                        "title": "Mainline Collaboration",
                        "goal": "稳定主链协作界面。",
                        "scope": ["统一协作界面。", "统一回流条件。", "统一交接结果。"],
                        "constraints": ["不得跳过 gate。", "不得重写上游 EPIC。", "不得泄漏 formal 职责。"],
                        "dependencies": ["EPIC-SRC001"],
                        "outputs": ["formal feat"],
                        "acceptance_checks": [
                            {"scenario": "scope is explicit", "given": "formal FEAT", "when": "read scope", "then": "scope 可独立验收"},
                            {"scenario": "constraints are explicit", "given": "formal FEAT", "when": "read constraints", "then": "约束可追溯"},
                            {"scenario": "downstream can inherit", "given": "formal FEAT", "when": "dispatch", "then": "TECH/TESTSET 都可消费"},
                        ],
                        "source_refs": ["FEAT-SRC-001-301", "EPIC-SRC001", "SRC-001"],
                    }
                ],
            },
        )
        write_json(
            self.workspace / "artifacts" / "registry" / f"epic-to-feat-{run_id}-feat-freeze-bundle.json",
            {
                "artifact_ref": f"epic-to-feat.{run_id}.feat-freeze-bundle",
                "managed_artifact_ref": f"artifacts/epic-to-feat/{run_id}/feat-freeze-bundle.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "product.epic-to-feat"},
                "metadata": {"layer": "formal"},
                "lineage": [],
            },
        )
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": f"epic-to-feat.{run_id}.feat-freeze-bundle"})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "candidate_ref": f"epic-to-feat.{run_id}.feat-freeze-bundle",
            },
        )
        materialize_req = self.request_path("gate-materialize-epic-feat.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize-epic-feat.response.json")
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )
        materialize_payload = read_json(materialize_response)
        self.assertEqual(materialize_payload["data"]["formal_ref"], f"formal.feat.{run_id}")
        self.assertEqual(materialize_payload["data"]["materialized_formal_refs"], ["formal.feat.feat-src-001-301"])
        formal_feat_path = self.workspace / "ssot" / "feat" / "FEAT-SRC-001-301__mainline-collaboration.md"
        self.assertTrue(formal_feat_path.exists())
        self.assertIn("ssot_type: FEAT", formal_feat_path.read_text(encoding="utf-8"))

        dispatch_request = self.build_request(
            "gate.dispatch",
            {"gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json"},
        )
        dispatch_req = self.request_path("gate-dispatch-epic-feat.json")
        write_json(dispatch_req, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch-epic-feat.response.json")
        self.assertEqual(self.run_cli("gate", "dispatch", "--request", str(dispatch_req), "--response-out", str(dispatch_response)), 0)
        dispatch_payload = read_json(dispatch_response)
        self.assertEqual(len(dispatch_payload["data"]["materialized_job_refs"]), 2)
        for job_ref in dispatch_payload["data"]["materialized_job_refs"]:
            job = read_json(self.workspace / job_ref)
            self.assertEqual(job["job_type"], "next_skill")
            self.assertEqual(job["feat_ref"], "FEAT-SRC-001-301")
            self.assertTrue(job["target_skill"] in {"workflow.dev.feat_to_tech", "workflow.qa.feat_to_testset"})

    def test_gate_materialize_feat_to_tech_candidate_promotes_formal_tech_and_dispatches_impl_job(self) -> None:
        run_id = "feat-tech-run"
        package_dir = self.workspace / "artifacts" / "feat-to-tech" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "tech-design-bundle.md").write_text("# TECH Bundle\n", encoding="utf-8")
        write_json(
            package_dir / "tech-design-bundle.json",
            {
                "artifact_type": "tech_design_package",
                "workflow_key": "dev.feat-to-tech",
                "workflow_run_id": run_id,
                "title": "Mainline Collaboration Technical Design Package",
                "status": "accepted",
                "feat_ref": "FEAT-SRC-001-301",
                "tech_ref": "TECH-FEAT-SRC-001-301",
                "source_refs": ["FEAT-SRC-001-301", "EPIC-SRC001", "SRC-001"],
            },
        )
        write_json(package_dir / "handoff-to-tech-impl.json", {"target_workflow": "workflow.dev.tech_to_impl"})
        write_json(
            self.workspace / "artifacts" / "registry" / f"feat-to-tech-{run_id}-tech-design-bundle.json",
            {
                "artifact_ref": f"feat-to-tech.{run_id}.tech-design-bundle",
                "managed_artifact_ref": f"artifacts/feat-to-tech/{run_id}/tech-design-bundle.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "dev.feat-to-tech"},
                "metadata": {"layer": "candidate"},
                "lineage": [],
            },
        )
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision-tech.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": f"feat-to-tech.{run_id}.tech-design-bundle"})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-tech.json",
                "candidate_ref": f"feat-to-tech.{run_id}.tech-design-bundle",
            },
        )
        materialize_req = self.request_path("gate-materialize-feat-tech.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize-feat-tech.response.json")
        self.assertEqual(self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)), 0)
        materialize_payload = read_json(materialize_response)
        self.assertEqual(materialize_payload["data"]["formal_ref"], f"formal.tech.{run_id}")
        formal_tech_path = self.workspace / "ssot" / "tech" / "SRC-001" / "TECH-FEAT-SRC-001-301__mainline-collaboration-technical-design-package.md"
        self.assertTrue(formal_tech_path.exists())

        dispatch_request = self.build_request(
            "gate.dispatch",
            {"gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-tech.json"},
        )
        dispatch_req = self.request_path("gate-dispatch-feat-tech.json")
        write_json(dispatch_req, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch-feat-tech.response.json")
        self.assertEqual(self.run_cli("gate", "dispatch", "--request", str(dispatch_req), "--response-out", str(dispatch_response)), 0)
        dispatch_payload = read_json(dispatch_response)
        self.assertEqual(len(dispatch_payload["data"]["materialized_job_refs"]), 1)
        job = read_json(self.workspace / dispatch_payload["data"]["materialized_job_refs"][0])
        self.assertEqual(job["target_skill"], "workflow.dev.tech_to_impl")
        self.assertEqual(job["tech_ref"], "TECH-FEAT-SRC-001-301")

    def test_gate_materialize_feat_to_testset_candidate_promotes_formal_testset_and_dispatches_execution_job(self) -> None:
        run_id = "feat-testset-run"
        package_dir = self.workspace / "artifacts" / "feat-to-testset" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "test-set-bundle.md").write_text("# TESTSET Bundle\n", encoding="utf-8")
        write_json(
            package_dir / "test-set-bundle.json",
            {
                "artifact_type": "test_set_candidate_package",
                "workflow_key": "qa.feat-to-testset",
                "workflow_run_id": run_id,
                "title": "Mainline Collaboration TESTSET Bundle",
                "status": "approval_pending",
                "feat_ref": "FEAT-SRC-001-301",
                "test_set_ref": "TESTSET-FEAT-SRC-001-301",
                "downstream_target": "skill.qa.test_exec_cli",
                "source_refs": ["FEAT-SRC-001-301", "EPIC-SRC001", "SRC-001"],
            },
        )
        (package_dir / "test-set.yaml").write_text(
            "id: TESTSET-FEAT-SRC-001-301\nssot_type: TESTSET\nstatus: approved\nfeat_ref: FEAT-SRC-001-301\n",
            encoding="utf-8",
        )
        write_json(package_dir / "handoff-to-test-execution.json", {"target_skill": "skill.qa.test_exec_cli"})
        write_json(
            self.workspace / "artifacts" / "registry" / f"feat-to-testset-{run_id}-test-set-bundle.json",
            {
                "artifact_ref": f"feat-to-testset.{run_id}.test-set-bundle",
                "managed_artifact_ref": f"artifacts/feat-to-testset/{run_id}/test-set-bundle.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "qa.feat-to-testset"},
                "metadata": {"layer": "candidate"},
                "lineage": [],
            },
        )
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision-testset.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": f"feat-to-testset.{run_id}.test-set-bundle"})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-testset.json",
                "candidate_ref": f"feat-to-testset.{run_id}.test-set-bundle",
            },
        )
        materialize_req = self.request_path("gate-materialize-feat-testset.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize-feat-testset.response.json")
        self.assertEqual(self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)), 0)
        materialize_payload = read_json(materialize_response)
        self.assertEqual(materialize_payload["data"]["formal_ref"], f"formal.testset.{run_id}")
        formal_testset_path = self.workspace / "ssot" / "testset" / "TESTSET-FEAT-SRC-001-301__mainline-collaboration-testset-bundle.yaml"
        self.assertTrue(formal_testset_path.exists())

        dispatch_request = self.build_request(
            "gate.dispatch",
            {"gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-testset.json"},
        )
        dispatch_req = self.request_path("gate-dispatch-feat-testset.json")
        write_json(dispatch_req, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch-feat-testset.response.json")
        self.assertEqual(self.run_cli("gate", "dispatch", "--request", str(dispatch_req), "--response-out", str(dispatch_response)), 0)
        dispatch_payload = read_json(dispatch_response)
        self.assertEqual(len(dispatch_payload["data"]["materialized_job_refs"]), 1)
        job = read_json(self.workspace / dispatch_payload["data"]["materialized_job_refs"][0])
        self.assertEqual(job["target_skill"], "skill.qa.test_exec_cli")
        self.assertEqual(job["test_set_ref"], "TESTSET-FEAT-SRC-001-301")

    def test_gate_materialize_tech_to_impl_candidate_promotes_formal_impl(self) -> None:
        run_id = "tech-impl-run"
        package_dir = self.workspace / "artifacts" / "tech-to-impl" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "impl-bundle.md").write_text("# IMPL Bundle\n", encoding="utf-8")
        write_json(
            package_dir / "impl-bundle.json",
            {
                "artifact_type": "feature_impl_candidate_package",
                "workflow_key": "dev.tech-to-impl",
                "workflow_run_id": run_id,
                "title": "Mainline Collaboration IMPL Bundle",
                "status": "execution_ready",
                "feat_ref": "FEAT-SRC-001-301",
                "tech_ref": "TECH-FEAT-SRC-001-301",
                "impl_ref": "IMPL-FEAT-SRC-001-301",
                "source_refs": ["FEAT-SRC-001-301", "TECH-FEAT-SRC-001-301", "EPIC-SRC001", "SRC-001"],
            },
        )
        write_json(
            self.workspace / "artifacts" / "registry" / f"tech-to-impl-{run_id}-impl-bundle.json",
            {
                "artifact_ref": f"tech-to-impl.{run_id}.impl-bundle",
                "managed_artifact_ref": f"artifacts/tech-to-impl/{run_id}/impl-bundle.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "dev.tech-to-impl"},
                "metadata": {"layer": "candidate"},
                "lineage": [],
            },
        )
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision-impl.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": f"tech-to-impl.{run_id}.impl-bundle"})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-impl.json",
                "candidate_ref": f"tech-to-impl.{run_id}.impl-bundle",
            },
        )
        materialize_req = self.request_path("gate-materialize-tech-impl.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize-tech-impl.response.json")
        self.assertEqual(self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)), 0)
        materialize_payload = read_json(materialize_response)
        self.assertEqual(materialize_payload["data"]["formal_ref"], f"formal.impl.{run_id}")
        formal_impl_path = self.workspace / "ssot" / "impl" / "IMPL-FEAT-SRC-001-301__mainline-collaboration-impl-bundle.md"
        self.assertTrue(formal_impl_path.exists())

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
