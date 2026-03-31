from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cli.ll import main
from cli.lib.mainline_runtime import submit_handoff


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class GovernedCliRuntimeFlowTest(unittest.TestCase):
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

    def test_gate_submit_show_and_decide_flow(self) -> None:
        payload_path = self.workspace / ".workflow" / "runs" / "RUN-001" / "generated" / "handoff.json"
        write_json(payload_path, {"candidate_ref": "candidate.src"})
        submit_request = self.build_request(
            "gate.submit-handoff",
            {
                "producer_ref": "skill.qa.test_exec_web_e2e",
                "proposal_ref": "proposal-001",
                "payload_ref": ".workflow/runs/RUN-001/generated/handoff.json",
            },
        )
        submit_req = self.request_path("gate-submit.json")
        write_json(submit_req, submit_request)
        submit_response = self.response_path("gate-submit.response.json")
        self.assertEqual(
            self.run_cli("gate", "submit-handoff", "--request", str(submit_req), "--response-out", str(submit_response)),
            0,
        )
        submit_payload = read_json(submit_response)
        handoff_ref = submit_payload["data"]["handoff_ref"]
        self.assertEqual(submit_payload["data"]["pending_state"], "gate_pending")
        self.assertEqual(submit_payload["data"]["assigned_gate_queue"], "mainline.gate.pending")

        self.assertEqual(
            self.run_cli("gate", "submit-handoff", "--request", str(submit_req), "--response-out", str(submit_response)),
            0,
        )
        duplicate_payload = read_json(submit_response)
        self.assertEqual(duplicate_payload["data"]["handoff_ref"], handoff_ref)
        self.assertEqual(duplicate_payload["data"]["idempotent_replay"], "true")

        show_request = self.build_request("gate.show-pending", {})
        show_req = self.request_path("gate-show-pending.json")
        write_json(show_req, show_request)
        show_response = self.response_path("gate-show-pending.response.json")
        self.assertEqual(
            self.run_cli("gate", "show-pending", "--request", str(show_req), "--response-out", str(show_response)),
            0,
        )
        shown = read_json(show_response)
        self.assertEqual(shown["data"]["pending_count"], 1)

        decide_request = self.build_request(
            "gate.decide",
            {
                "handoff_ref": handoff_ref,
                "proposal_ref": "proposal-001",
                "decision": "revise",
            },
        )
        decide_req = self.request_path("gate-decide.json")
        write_json(decide_req, decide_request)
        decide_response = self.response_path("gate-decide.response.json")
        self.assertEqual(
            self.run_cli("gate", "decide", "--request", str(decide_req), "--response-out", str(decide_response)),
            0,
        )
        decision_payload = read_json(decide_response)
        self.assertTrue(decision_payload["data"]["reentry_directive_ref"].endswith("-revise.json"))

    def test_registry_publish_and_validate_admission(self) -> None:
        candidate_path = self.workspace / "artifacts" / "active" / "run-001" / "formal-source.json"
        write_json(candidate_path, {"name": "candidate"})
        bind_request = self.build_request(
            "registry.bind-record",
            {
                "artifact_ref": "candidate.formalizable",
                "managed_artifact_ref": "artifacts/active/run-001/formal-source.json",
                "status": "candidate",
            },
        )
        bind_req = self.request_path("registry-bind-formalizable.json")
        write_json(bind_req, bind_request)
        bind_response = self.response_path("registry-bind-formalizable.response.json")
        self.assertEqual(self.run_cli("registry", "bind-record", "--request", str(bind_req), "--response-out", str(bind_response)), 0)

        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "publish-decision.json"
        write_json(decision_path, {"decision_type": "approve"})
        publish_request = self.build_request(
            "registry.publish-formal",
            {
                "candidate_ref": "candidate.formalizable",
                "decision_ref": "artifacts/active/gates/decisions/publish-decision.json",
                "target_formal_kind": "report",
                "formal_artifact_ref": "formal.report.001",
            },
        )
        publish_req = self.request_path("registry-publish-formal.json")
        write_json(publish_req, publish_request)
        publish_response = self.response_path("registry-publish-formal.response.json")
        self.assertEqual(
            self.run_cli("registry", "publish-formal", "--request", str(publish_req), "--response-out", str(publish_response)),
            0,
        )

        resolve_request = self.build_request("registry.resolve-formal-ref", {"artifact_ref": "formal.report.001"})
        resolve_req = self.request_path("registry-resolve-formal.json")
        write_json(resolve_req, resolve_request)
        resolve_response = self.response_path("registry-resolve-formal.response.json")
        self.assertEqual(
            self.run_cli("registry", "resolve-formal-ref", "--request", str(resolve_req), "--response-out", str(resolve_response)),
            0,
        )

        admission_request = self.build_request(
            "registry.validate-admission",
            {"consumer_ref": "consumer.skill", "requested_ref": "formal.report.001"},
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

        deny_request = self.build_request(
            "registry.validate-admission",
            {"consumer_ref": "consumer.skill", "requested_ref": "candidate.formalizable"},
        )
        deny_req = self.request_path("registry-admission-deny.json")
        write_json(deny_req, deny_request)
        deny_response = self.response_path("registry-admission-deny.response.json")
        self.assertEqual(
            self.run_cli("registry", "validate-admission", "--request", str(deny_req), "--response-out", str(deny_response)),
            3,
        )
        deny_payload = read_json(deny_response)
        self.assertEqual(deny_payload["status_code"], "ELIGIBILITY_DENIED")

    def test_rollout_onboard_cutover_and_pilot_submission(self) -> None:
        onboard_request = self.build_request(
            "rollout.onboard-skill",
            {
                "skill_ref": "skill.qa.test_exec_cli",
                "wave_id": "wave-01",
                "scope": "pilot",
                "compat_mode": True,
                "foundation_ready": True,
            },
        )
        onboard_req = self.request_path("rollout-onboard.json")
        write_json(onboard_req, onboard_request)
        onboard_response = self.response_path("rollout-onboard.response.json")
        self.assertEqual(
            self.run_cli("rollout", "onboard-skill", "--request", str(onboard_req), "--response-out", str(onboard_response)),
            0,
        )

        pilot_request = self.build_request(
            "audit.submit-pilot-evidence",
            {
                "pilot_chain_ref": "pilot-chain-01",
                "producer_ref": "producer",
                "consumer_ref": "consumer",
                "audit_ref": "audit-01",
                "gate_ref": "gate-01",
            },
        )
        pilot_req = self.request_path("audit-pilot.json")
        write_json(pilot_req, pilot_request)
        pilot_response = self.response_path("audit-pilot.response.json")
        self.assertEqual(
            self.run_cli("audit", "submit-pilot-evidence", "--request", str(pilot_req), "--response-out", str(pilot_response)),
            0,
        )
        pilot_payload = read_json(pilot_response)
        self.assertEqual(pilot_payload["data"]["cutover_recommendation"], "cutover_ready")

        cutover_request = self.build_request(
            "rollout.cutover-wave",
            {"wave_id": "wave-01", "pilot_evidence_ref": pilot_payload["data"]["pilot_evidence_ref"]},
        )
        cutover_req = self.request_path("rollout-cutover.json")
        write_json(cutover_req, cutover_request)
        cutover_response = self.response_path("rollout-cutover.response.json")
        self.assertEqual(
            self.run_cli("rollout", "cutover-wave", "--request", str(cutover_req), "--response-out", str(cutover_response)),
            0,
        )
        cutover_payload = read_json(cutover_response)
        self.assertEqual(cutover_payload["data"]["readiness_label"], "cutover_guarded")

        blocked_request = self.build_request("rollout.cutover-wave", {"wave_id": "wave-01"})
        blocked_req = self.request_path("rollout-cutover-blocked.json")
        write_json(blocked_req, blocked_request)
        blocked_response = self.response_path("rollout-cutover-blocked.response.json")
        self.assertEqual(
            self.run_cli("rollout", "cutover-wave", "--request", str(blocked_req), "--response-out", str(blocked_response)),
            4,
        )
        blocked_payload = read_json(blocked_response)
        self.assertEqual(blocked_payload["status_code"], "PRECONDITION_FAILED")

        fallback_request = self.build_request("rollout.fallback-wave", {"wave_id": "wave-01"})
        fallback_req = self.request_path("rollout-fallback.json")
        write_json(fallback_req, fallback_request)
        fallback_response = self.response_path("rollout-fallback.response.json")
        self.assertEqual(
            self.run_cli("rollout", "fallback-wave", "--request", str(fallback_req), "--response-out", str(fallback_response)),
            0,
        )
        fallback_payload = read_json(fallback_response)
        self.assertTrue(fallback_payload["data"]["receipt_ref"].endswith("wave-01-fallback.json"))

    def test_submit_pilot_evidence_accepts_path_like_ref(self) -> None:
        pilot_request = self.build_request(
            "audit.submit-pilot-evidence",
            {
                "pilot_chain_ref": "E:/ai/LEE-Lite-skill-first/artifacts/feat-to-testset/demo/test-set.yaml",
                "producer_ref": "producer",
                "consumer_ref": "consumer",
                "audit_ref": "audit-01",
                "gate_ref": "gate-01",
            },
        )
        pilot_req = self.request_path("audit-pilot-path-like.json")
        write_json(pilot_req, pilot_request)
        pilot_response = self.response_path("audit-pilot-path-like.response.json")
        self.assertEqual(
            self.run_cli("audit", "submit-pilot-evidence", "--request", str(pilot_req), "--response-out", str(pilot_response)),
            0,
        )
        pilot_payload = read_json(pilot_response)
        self.assertIn("pilot-evidence-test-set-", pilot_payload["data"]["pilot_evidence_ref"])
        evidence_path = self.workspace / pilot_payload["data"]["pilot_evidence_ref"]
        self.assertTrue(evidence_path.exists())

    def test_submit_handoff_merges_existing_pending_index_entries(self) -> None:
        payload_path = self.workspace / ".workflow" / "runs" / "RUN-001" / "generated" / "handoff.json"
        write_json(payload_path, {"candidate_ref": "candidate.src"})

        existing_handoff_ref = "artifacts/active/gates/handoffs/existing-handoff.json"
        existing_pending_ref = "artifacts/active/gates/pending/existing-handoff.json"
        write_json(
            self.workspace / existing_handoff_ref,
            {
                "trace": {"run_ref": "RUN-001", "workflow_key": "governance.gate-human-orchestrator"},
                "producer_ref": "skill.existing",
                "proposal_ref": "existing-proposal",
                "payload_ref": "artifacts/active/run-001/existing-payload.json",
                "pending_state": "gate_pending",
                "trace_context_ref": "",
                "payload_digest": "existing-digest",
            },
        )
        write_json(
            self.workspace / existing_pending_ref,
            {
                "trace": {"run_ref": "RUN-001", "workflow_key": "governance.gate-human-orchestrator"},
                "handoff_ref": existing_handoff_ref,
                "producer_ref": "skill.existing",
                "proposal_ref": "existing-proposal",
                "pending_state": "gate_pending",
            },
        )
        write_json(
            self.workspace / "artifacts" / "active" / "gates" / "pending" / "index.json",
            {
                "handoffs": {
                    "existing-handoff": {
                        "handoff_ref": existing_handoff_ref,
                        "gate_pending_ref": existing_pending_ref,
                        "payload_digest": "existing-digest",
                        "trace_ref": "",
                        "pending_state": "gate_pending",
                        "assigned_gate_queue": "mainline.gate.pending",
                    }
                }
            },
        )

        result = submit_handoff(
            self.workspace,
            trace={"run_ref": "RUN-001", "workflow_key": "governance.gate-human-orchestrator"},
            producer_ref="skill.new",
            proposal_ref="proposal-002",
            payload_ref=".workflow/runs/RUN-001/generated/handoff.json",
            trace_context_ref="artifacts/active/run-001/evidence.json",
        )
        self.assertTrue(result["handoff_ref"].endswith("skill-new-proposal-002.json"))

        index_path = self.workspace / "artifacts" / "active" / "gates" / "pending" / "index.json"
        index_payload = read_json(index_path)
        self.assertIn("existing-handoff", index_payload["handoffs"])
        self.assertEqual(len(index_payload["handoffs"]), 2)

        replay = submit_handoff(
            self.workspace,
            trace={"run_ref": "RUN-001", "workflow_key": "governance.gate-human-orchestrator"},
            producer_ref="skill.new",
            proposal_ref="proposal-002",
            payload_ref=".workflow/runs/RUN-001/generated/handoff.json",
            trace_context_ref="artifacts/active/run-001/evidence.json",
        )
        self.assertEqual(replay["idempotent_replay"], "true")
        replay_index_payload = read_json(index_path)
        self.assertEqual(len(replay_index_payload["handoffs"]), 2)


if __name__ == "__main__":
    unittest.main()
