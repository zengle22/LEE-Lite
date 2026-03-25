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


class RolloutRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        (self.workspace / "contracts" / "input").mkdir(parents=True)
        (self.workspace / "artifacts" / "active" / "responses").mkdir(parents=True)
        (self.workspace / "artifacts" / "active" / "rollout").mkdir(parents=True)

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
            "trace": {"run_ref": "RUN-ROLLOUT"},
            "payload": payload,
        }

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def test_readiness_blocks_without_matching_pilot_evidence(self) -> None:
        bad_chain = self.workspace / "artifacts" / "active" / "rollout" / "pilot-chain-bad.json"
        write_json(bad_chain, {"chain": ["producer", "gate", "consumer"]})
        request = self.build_request(
            "rollout.summarize-readiness",
            {
                "integration_matrix_ref": "ssot/impl/integration-matrix.md",
                "migration_wave_ref": "ssot/impl/migration-wave.md",
                "pilot_chain_ref": "artifacts/active/rollout/pilot-chain-bad.json",
            },
        )
        req = self.request_path("rollout-readiness-blocked.json")
        write_json(req, request)
        response = self.response_path("rollout-readiness-blocked.response.json")
        self.assertEqual(self.run_cli("rollout", "summarize-readiness", "--request", str(req), "--response-out", str(response)), 4)
        payload = read_json(response)
        self.assertEqual(payload["status_code"], "PRECONDITION_FAILED")

    def test_record_fallback_and_check_scope(self) -> None:
        onboard = self.build_request(
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
        write_json(onboard_req, onboard)
        onboard_response = self.response_path("rollout-onboard.response.json")
        self.assertEqual(self.run_cli("rollout", "onboard-skill", "--request", str(onboard_req), "--response-out", str(onboard_response)), 0)

        fallback = self.build_request(
            "rollout.record-fallback",
            {
                "integration_matrix_ref": "ssot/impl/integration-matrix.md",
                "migration_wave_ref": "ssot/impl/migration-wave.md",
                "pilot_chain_ref": "artifacts/active/rollout/pilot-chain.json",
                "wave_id": "wave-001",
                "compat_mode": "read-only",
                "cutover_guard_ref": "artifacts/active/guards/cutover.json",
                "fallback_reason_code": "pilot_evidence_missing",
            },
        )
        fallback_req = self.request_path("rollout-fallback.json")
        write_json(fallback_req, fallback)
        fallback_response = self.response_path("rollout-fallback.response.json")
        self.assertEqual(self.run_cli("rollout", "record-fallback", "--request", str(fallback_req), "--response-out", str(fallback_response)), 0)
        fallback_payload = read_json(fallback_response)
        wave_state = read_json(self.workspace / fallback_payload["data"]["wave_state_ref"])
        receipt = read_json(self.workspace / fallback_payload["data"]["fallback_receipt_ref"])
        self.assertEqual(wave_state["status"], "fallback_triggered")
        self.assertEqual(receipt["fallback_reason_code"], "pilot_evidence_missing")

        scope = self.build_request(
            "rollout.check-scope",
            {
                "integration_matrix_ref": "ssot/impl/integration-matrix.md",
                "migration_wave_ref": "ssot/impl/migration-wave.md",
                "pilot_chain_ref": "artifacts/active/rollout/pilot-chain.json",
                "proposal_summary": "Fold all file-governance cleanup into a repository-wide rollout.",
                "proposed_scope_actions": ["repository-wide cleanup", "global governance migration"],
            },
        )
        scope_req = self.request_path("rollout-scope.json")
        write_json(scope_req, scope)
        scope_response = self.response_path("rollout-scope.response.json")
        self.assertEqual(self.run_cli("rollout", "check-scope", "--request", str(scope_req), "--response-out", str(scope_response)), 0)
        scope_payload = read_json(scope_response)
        verdict = read_json(self.workspace / scope_payload["data"]["scope_boundary_verdict_ref"])
        self.assertEqual(verdict["scope_boundary_result"], "reject")


if __name__ == "__main__":
    unittest.main()
