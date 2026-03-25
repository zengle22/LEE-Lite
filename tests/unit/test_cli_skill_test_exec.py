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


def write_yaml(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestExecSkillRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        (self.workspace / "artifacts").mkdir()
        (self.workspace / "contracts" / "input").mkdir(parents=True)
        self.repo_root = Path(__file__).resolve().parents[2]

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
            "trace": {"run_ref": "RUN-TEST-EXEC"},
            "payload": payload,
        }

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def feat_testset_path(self, feat_id: str) -> str:
        return str(
            self.repo_root
            / "artifacts"
            / "feat-to-testset"
            / f"adr007-qa-test-execution-20260325-rerun1--feat-src-adr007-qa-test-execution-20260325-rerun1-{feat_id}"
            / "test-set.yaml"
        )

    def write_env_spec(self, name: str, content: str) -> str:
        path = self.workspace / "ssot" / "test-env" / name
        write_yaml(path, content)
        return path.as_posix()

    def test_web_skill_emits_candidate_and_handoff_with_real_testset(self) -> None:
        env_ref = self.write_env_spec(
            "web-env.yaml",
            "execution_modality: web_e2e\nbase_url: https://example.test\nbrowser: chromium\nheadless: true\n",
        )
        request = self.build_request(
            "skill.test-exec-web-e2e",
            {
                "test_set_ref": self.feat_testset_path("001"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-web-001",
            },
        )
        req = self.request_path("skill-web.json")
        write_json(req, request)
        response = self.response_path("skill-web.response.json")
        self.assertEqual(
            self.run_cli("skill", "test-exec-web-e2e", "--request", str(req), "--response-out", str(response)),
            0,
        )
        payload = read_json(response)
        self.assertEqual(payload["data"]["skill_ref"], "skill.qa.test_exec_web_e2e")
        self.assertTrue(payload["data"]["candidate_managed_artifact_ref"].startswith("artifacts/active/qa/candidates/"))
        self.assertEqual(payload["data"]["pending_state"], "gate_pending")

    def test_cli_skill_emits_candidate_and_handoff_with_real_testset(self) -> None:
        env_ref = self.write_env_spec(
            "cli-env.yaml",
            "execution_modality: cli\ncommand_entry: python -m sample.runner\nworkdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": self.feat_testset_path("005"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-001",
            },
        )
        req = self.request_path("skill-cli.json")
        write_json(req, request)
        response = self.response_path("skill-cli.response.json")
        self.assertEqual(
            self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)),
            0,
        )
        payload = read_json(response)
        self.assertEqual(payload["data"]["skill_ref"], "skill.qa.test_exec_cli")
        self.assertEqual(payload["data"]["runner_skill_ref"], "skill.runner.test_cli")
        self.assertEqual(payload["data"]["assigned_gate_queue"], "mainline.gate.pending")

    def test_cli_skill_pilot_integration_flow(self) -> None:
        env_ref = self.write_env_spec(
            "cli-pilot-env.yaml",
            "execution_modality: cli\ncommand_entry: python -m sample.runner\nworkdir: .\n",
        )

        onboard_request = self.build_request(
            "rollout.onboard-skill",
            {
                "skill_ref": "skill.qa.test_exec_cli",
                "wave_id": "wave-pilot-01",
                "scope": "pilot",
                "compat_mode": True,
                "foundation_ready": True,
            },
        )
        onboard_req = self.request_path("pilot-onboard.json")
        write_json(onboard_req, onboard_request)
        onboard_response = self.response_path("pilot-onboard.response.json")
        self.assertEqual(
            self.run_cli("rollout", "onboard-skill", "--request", str(onboard_req), "--response-out", str(onboard_response)),
            0,
        )

        skill_request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": self.feat_testset_path("005"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-pilot-005",
            },
        )
        skill_req = self.request_path("pilot-skill.json")
        write_json(skill_req, skill_request)
        skill_response = self.response_path("pilot-skill.response.json")
        self.assertEqual(
            self.run_cli("skill", "test-exec-cli", "--request", str(skill_req), "--response-out", str(skill_response)),
            0,
        )
        skill_payload = read_json(skill_response)["data"]

        decide_request = self.build_request(
            "gate.decide",
            {
                "handoff_ref": skill_payload["handoff_ref"],
                "proposal_ref": "proposal-pilot-005",
                "decision": "approve",
            },
        )
        decide_req = self.request_path("pilot-decide.json")
        write_json(decide_req, decide_request)
        decide_response = self.response_path("pilot-decide.response.json")
        self.assertEqual(
            self.run_cli("gate", "decide", "--request", str(decide_req), "--response-out", str(decide_response)),
            0,
        )
        decision_payload = read_json(decide_response)["data"]

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": decision_payload["gate_decision_ref"],
                "candidate_ref": skill_payload["candidate_artifact_ref"],
                "target_formal_kind": "pilot-report",
            },
        )
        materialize_req = self.request_path("pilot-materialize.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("pilot-materialize.response.json")
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )
        materialize_payload = read_json(materialize_response)["data"]

        admission_request = self.build_request(
            "registry.validate-admission",
            {"consumer_ref": "skill.qa.test_exec_cli.consumer", "requested_ref": materialize_payload["formal_ref"]},
        )
        admission_req = self.request_path("pilot-admission.json")
        write_json(admission_req, admission_request)
        admission_response = self.response_path("pilot-admission.response.json")
        self.assertEqual(
            self.run_cli("registry", "validate-admission", "--request", str(admission_req), "--response-out", str(admission_response)),
            0,
        )

        audit_request = self.build_request(
            "audit.emit-finding-bundle",
            {
                "workspace_diff_ref": "artifacts/active/diff.json",
                "gateway_receipt_refs": [skill_payload["candidate_receipt_ref"]],
                "registry_refs": [skill_payload["candidate_registry_record_ref"]],
                "policy_verdict_refs": [skill_payload["candidate_receipt_ref"]],
                "attempted_unmanaged_reads": [],
                "bypass_write_paths": [],
            },
        )
        audit_req = self.request_path("pilot-audit.json")
        write_json(audit_req, audit_request)
        audit_response = self.response_path("pilot-audit.response.json")
        self.assertEqual(
            self.run_cli("audit", "emit-finding-bundle", "--request", str(audit_req), "--response-out", str(audit_response)),
            0,
        )
        audit_payload = read_json(audit_response)["data"]

        pilot_request = self.build_request(
            "audit.submit-pilot-evidence",
            {
                "pilot_chain_ref": self.feat_testset_path("005"),
                "producer_ref": skill_payload["skill_ref"],
                "consumer_ref": "skill.qa.test_exec_cli.consumer",
                "audit_ref": audit_payload["finding_bundle_ref"],
                "gate_ref": decision_payload["gate_decision_ref"],
            },
        )
        pilot_req = self.request_path("pilot-submit-evidence.json")
        write_json(pilot_req, pilot_request)
        pilot_response = self.response_path("pilot-submit-evidence.response.json")
        self.assertEqual(
            self.run_cli("audit", "submit-pilot-evidence", "--request", str(pilot_req), "--response-out", str(pilot_response)),
            0,
        )
        pilot_payload = read_json(pilot_response)["data"]

        cutover_request = self.build_request(
            "rollout.cutover-wave",
            {"wave_id": "wave-pilot-01", "pilot_evidence_ref": pilot_payload["pilot_evidence_ref"]},
        )
        cutover_req = self.request_path("pilot-cutover.json")
        write_json(cutover_req, cutover_request)
        cutover_response = self.response_path("pilot-cutover.response.json")
        self.assertEqual(
            self.run_cli("rollout", "cutover-wave", "--request", str(cutover_req), "--response-out", str(cutover_response)),
            0,
        )
        cutover_payload = read_json(cutover_response)["data"]
        self.assertEqual(cutover_payload["readiness_label"], "cutover_guarded")


if __name__ == "__main__":
    unittest.main()
