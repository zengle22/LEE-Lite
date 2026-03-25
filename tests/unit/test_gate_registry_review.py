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


class GateRegistryReviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        (self.workspace / "artifacts").mkdir()
        (self.workspace / "contracts" / "input").mkdir(parents=True)
        payload = self.workspace / ".workflow" / "runs" / "RUN-001" / "generated" / "payload.txt"
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_text("hello world", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def build_request(self, command: str, payload: dict, request_id: str) -> dict:
        return {
            "api_version": "v1",
            "command": command,
            "request_id": request_id,
            "workspace_root": self.workspace.as_posix(),
            "actor_ref": "review-suite",
            "trace": {"run_ref": "RUN-001"},
            "payload": payload,
        }

    def request_path(self, name: str) -> Path:
        return self.workspace / "contracts" / "input" / name

    def response_path(self, name: str) -> Path:
        return self.workspace / "artifacts" / "active" / name

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def test_gate_outputs_are_request_scoped_and_dispatch_needs_approve(self) -> None:
        package_path = self.workspace / "artifacts" / "active" / "gates" / "packages" / "gate-ready-package.json"
        write_json(
            package_path,
            {
                "candidate_ref": "artifacts/active/run-001/candidate.json",
                "acceptance_ref": "artifacts/active/run-001/acceptance.json",
                "evidence_bundle_ref": "artifacts/active/run-001/evidence.json",
                "proposal_ref": "artifacts/active/run-001/proposal.json",
            },
        )
        audit_path = self.workspace / "artifacts" / "active" / "audit" / "finding-bundle.json"
        write_json(audit_path, {"findings": []})
        evaluate_payload = {
            "gate_ready_package_ref": "artifacts/active/gates/packages/gate-ready-package.json",
            "audit_finding_refs": ["artifacts/active/audit/finding-bundle.json"],
            "target_matrix": {"allowed_targets": ["materialized_handoff"]},
        }
        evaluate_one = self.build_request("gate.evaluate", evaluate_payload, "req-gate-evaluate-1")
        evaluate_two = self.build_request("gate.evaluate", evaluate_payload, "req-gate-evaluate-2")
        evaluate_one_req = self.request_path("gate-evaluate-1.json")
        evaluate_two_req = self.request_path("gate-evaluate-2.json")
        evaluate_one_response = self.response_path("gate-evaluate-1.response.json")
        evaluate_two_response = self.response_path("gate-evaluate-2.response.json")
        write_json(evaluate_one_req, evaluate_one)
        write_json(evaluate_two_req, evaluate_two)
        self.assertEqual(
            self.run_cli("gate", "evaluate", "--request", str(evaluate_one_req), "--response-out", str(evaluate_one_response)),
            0,
        )
        self.assertEqual(
            self.run_cli("gate", "evaluate", "--request", str(evaluate_two_req), "--response-out", str(evaluate_two_response)),
            0,
        )
        decision_one = read_json(evaluate_one_response)["data"]["gate_decision_ref"]
        decision_two = read_json(evaluate_two_response)["data"]["gate_decision_ref"]
        self.assertNotEqual(decision_one, decision_two)
        self.assertTrue((self.workspace / decision_one).exists())
        self.assertTrue((self.workspace / decision_two).exists())

        approve_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "approve.json"
        reject_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "reject.json"
        write_json(approve_path, {"decision_type": "approve"})
        write_json(reject_path, {"decision_type": "reject"})
        materialize_payload = {"gate_decision_ref": "artifacts/active/gates/decisions/approve.json"}
        materialize_one = self.build_request("gate.materialize", materialize_payload, "req-gate-materialize-1")
        materialize_two = self.build_request("gate.materialize", materialize_payload, "req-gate-materialize-2")
        materialize_one_req = self.request_path("gate-materialize-1.json")
        materialize_two_req = self.request_path("gate-materialize-2.json")
        materialize_one_response = self.response_path("gate-materialize-1.response.json")
        materialize_two_response = self.response_path("gate-materialize-2.response.json")
        write_json(materialize_one_req, materialize_one)
        write_json(materialize_two_req, materialize_two)
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_one_req), "--response-out", str(materialize_one_response)),
            0,
        )
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_two_req), "--response-out", str(materialize_two_response)),
            0,
        )
        handoff_one = read_json(materialize_one_response)["data"]["materialized_handoff_ref"]
        handoff_two = read_json(materialize_two_response)["data"]["materialized_handoff_ref"]
        self.assertNotEqual(handoff_one, handoff_two)
        self.assertTrue((self.workspace / handoff_one).exists())
        self.assertTrue((self.workspace / handoff_two).exists())

        dispatch_request = self.build_request(
            "gate.dispatch",
            {"gate_decision_ref": "artifacts/active/gates/decisions/reject.json"},
            "req-gate-dispatch-reject",
        )
        dispatch_req = self.request_path("gate-dispatch-reject.json")
        dispatch_response = self.response_path("gate-dispatch-reject.response.json")
        write_json(dispatch_req, dispatch_request)
        self.assertEqual(
            self.run_cli("gate", "dispatch", "--request", str(dispatch_req), "--response-out", str(dispatch_response)),
            4,
        )
        self.assertEqual(read_json(dispatch_response)["status_code"], "PRECONDITION_FAILED")

        close_one = self.build_request("gate.close-run", {"run_ref": "RUN-001"}, "req-gate-close-1")
        close_two = self.build_request("gate.close-run", {"run_ref": "RUN-001"}, "req-gate-close-2")
        close_one_req = self.request_path("gate-close-1.json")
        close_two_req = self.request_path("gate-close-2.json")
        close_one_response = self.response_path("gate-close-1.response.json")
        close_two_response = self.response_path("gate-close-2.response.json")
        write_json(close_one_req, close_one)
        write_json(close_two_req, close_two)
        self.assertEqual(
            self.run_cli("gate", "close-run", "--request", str(close_one_req), "--response-out", str(close_one_response)),
            0,
        )
        self.assertEqual(
            self.run_cli("gate", "close-run", "--request", str(close_two_req), "--response-out", str(close_two_response)),
            0,
        )
        closure_one = read_json(close_one_response)["data"]["run_closure_ref"]
        closure_two = read_json(close_two_response)["data"]["run_closure_ref"]
        self.assertNotEqual(closure_one, closure_two)
        self.assertTrue((self.workspace / closure_one).exists())
        self.assertTrue((self.workspace / closure_two).exists())

    def test_commit_governed_cannot_bypass_formal_resolution(self) -> None:
        commit_request = self.build_request(
            "artifact.commit-governed",
            {
                "artifact_ref": "formal.runtime.review",
                "workspace_path": "artifacts/active/formal/runtime-review.json",
                "content_ref": ".workflow/runs/RUN-001/generated/payload.txt",
                "metadata": {"layer": "formal"},
            },
            "req-artifact-commit-governed-review",
        )
        commit_req = self.request_path("artifact-commit-governed-review.json")
        commit_response = self.response_path("artifact-commit-governed-review.response.json")
        write_json(commit_req, commit_request)
        self.assertEqual(
            self.run_cli("artifact", "commit-governed", "--request", str(commit_req), "--response-out", str(commit_response)),
            0,
        )

        resolve_request = self.build_request(
            "registry.resolve-formal-ref",
            {"artifact_ref": "formal.runtime.review"},
            "req-registry-resolve-formal-review",
        )
        resolve_req = self.request_path("registry-resolve-formal-review.json")
        resolve_response = self.response_path("registry-resolve-formal-review.response.json")
        write_json(resolve_req, resolve_request)
        self.assertEqual(
            self.run_cli("registry", "resolve-formal-ref", "--request", str(resolve_req), "--response-out", str(resolve_response)),
            3,
        )
        self.assertEqual(read_json(resolve_response)["status_code"], "ELIGIBILITY_DENIED")


if __name__ == "__main__":
    unittest.main()
