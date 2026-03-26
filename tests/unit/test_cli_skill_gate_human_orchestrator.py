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


class GateHumanOrchestratorSkillCliTest(unittest.TestCase):
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
            "trace": {"run_ref": "RUN-GATE-SKILL"},
            "payload": payload,
        }

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def make_gate_ready_package(self) -> str:
        candidate = self.workspace / "artifacts" / "active" / "run-001" / "candidate.json"
        write_json(
            candidate,
            {
                "freeze_ready": True,
                "status": "freeze_ready",
                "product_summary": "CLI skill should orchestrate gate review projection.",
                "roles": ["reviewer", "ssot owner"],
                "main_flow": ["render", "review", "dispatch"],
                "deliverables": ["gate package"],
                "completed_state": "ready",
                "authoritative_output": "Machine SSOT",
                "frozen_downstream_boundary": "Projection remains review-only.",
                "open_technical_decisions": ["Confirm rollout note."],
            },
        )
        write_json(
            self.workspace / "artifacts" / "registry" / "candidate-impl.json",
            {
                "artifact_ref": "candidate.impl",
                "managed_artifact_ref": "artifacts/active/run-001/candidate.json",
                "status": "candidate",
                "trace": {"run_ref": "RUN-GATE-SKILL"},
                "metadata": {},
                "lineage": [],
            },
        )
        write_json(self.workspace / "artifacts" / "active" / "run-001" / "acceptance.json", {"accepted": True})
        write_json(self.workspace / "artifacts" / "active" / "run-001" / "evidence.json", {"evidence": True})
        package_path = self.workspace / "artifacts" / "active" / "gates" / "packages" / "gate-ready-package.json"
        write_json(
            package_path,
            {
                "trace": {"run_ref": "RUN-GATE-SKILL"},
                "payload": {
                    "candidate_ref": "candidate.impl",
                    "machine_ssot_ref": "candidate.impl",
                    "acceptance_ref": "artifacts/active/run-001/acceptance.json",
                    "evidence_bundle_ref": "artifacts/active/run-001/evidence.json",
                },
            },
        )
        return "artifacts/active/gates/packages/gate-ready-package.json"

    def make_runtime_pending_item(self, *, key: str = "gate-job-001") -> None:
        handoff_ref = f"artifacts/active/gates/handoffs/{key}.json"
        pending_ref = f"artifacts/active/gates/pending/{key}.json"
        write_json(
            self.workspace / handoff_ref,
            {
                "trace": {"run_ref": "RUN-GATE-SKILL"},
                "producer_ref": "skill.test",
                "proposal_ref": key,
                "payload_ref": "artifacts/active/gates/packages/gate-ready-package.json",
                "pending_state": "gate_pending",
            },
        )
        write_json(
            self.workspace / pending_ref,
            {
                "trace": {"run_ref": "RUN-GATE-SKILL"},
                "handoff_ref": handoff_ref,
                "producer_ref": "skill.test",
                "proposal_ref": key,
                "pending_state": "gate_pending",
            },
        )
        write_json(
            self.workspace / "artifacts" / "active" / "gates" / "pending" / "index.json",
            {
                "handoffs": {
                    key: {
                        "handoff_ref": handoff_ref,
                        "gate_pending_ref": pending_ref,
                        "payload_digest": "digest",
                        "trace_ref": "",
                        "pending_state": "gate_pending",
                        "assigned_gate_queue": "mainline.gate.pending",
                    }
                }
            },
        )

    def test_cli_skill_runs_gate_human_orchestrator(self) -> None:
        input_ref = self.make_gate_ready_package()
        request = self.build_request(
            "skill.gate-human-orchestrator",
            {"input_ref": input_ref, "decision": "approve"},
        )
        req = self.request_path("skill-gate-human.json")
        write_json(req, request)
        response = self.response_path("skill-gate-human.response.json")

        self.assertEqual(
            self.run_cli("skill", "gate-human-orchestrator", "--request", str(req), "--response-out", str(response)),
            0,
        )
        payload = read_json(response)["data"]
        self.assertEqual(payload["skill_ref"], "skill.gate.human_orchestrator")
        self.assertEqual(payload["decision"], "approve")
        self.assertEqual(payload["projection_status"], "review_visible")
        self.assertTrue(payload["human_projection_ref"].endswith(".json"))
        bundle = read_json(Path(payload["bundle_ref"]))
        self.assertEqual(bundle["machine_ssot_ref"], "candidate.impl")
        self.assertEqual(bundle["projection_status"], "review_visible")

    def test_cli_skill_claim_next_returns_human_brief(self) -> None:
        self.make_gate_ready_package()
        self.make_runtime_pending_item(key="queue-item-001")
        request = self.build_request(
            "skill.gate-human-orchestrator",
            {"operation": "claim-next"},
        )
        req = self.request_path("skill-gate-human-claim.json")
        write_json(req, request)
        response = self.response_path("skill-gate-human-claim.response.json")

        self.assertEqual(
            self.run_cli("skill", "gate-human-orchestrator", "--request", str(req), "--response-out", str(response)),
            0,
        )
        response_payload = read_json(response)
        payload = response_payload["data"]
        self.assertEqual(response_payload["message"], "governed gate human orchestrator prepared a pending human brief")
        self.assertEqual(payload["operation"], "claim-next")
        self.assertEqual(payload["status"], "claimed")
        self.assertEqual(payload["decision_target"], "candidate.impl")
        self.assertTrue(payload["canonical_path"].endswith("human-decision-request.json"))
        self.assertIn("## 需要你做的决定", payload["human_brief_markdown"])
        self.assertIn("## Machine SSOT 摘要", payload["human_brief_markdown"])
        self.assertIn("## Machine SSOT 人类友好全文", payload["human_brief_markdown"])
        self.assertIn("## Machine SSOT 文件骨架", payload["human_brief_markdown"])
        self.assertIn("## 关键待审阅点", payload["human_brief_markdown"])
        self.assertTrue(payload["review_summary"]["ssot_excerpt"])
        self.assertTrue(payload["review_summary"]["ssot_fulltext_markdown"])
        self.assertTrue(payload["review_summary"]["ssot_outline"])
        self.assertTrue(payload["review_summary"]["review_checkpoints"])
        self.assertEqual(payload["review_summary"]["status"], "pending_human_reply")
        self.assertTrue(any(ref.endswith("queue-item-001.json") for ref in response_payload["evidence_refs"]))


if __name__ == "__main__":
    unittest.main()
