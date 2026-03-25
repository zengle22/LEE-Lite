import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-gate-human-orchestrator" / "scripts" / "gate_human_orchestrator.py"


class GateHumanOrchestratorWorkflowTests(unittest.TestCase):
    def run_cmd(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def make_gate_ready_package(self, root: Path, *, candidate_ref: str = "candidate.impl") -> Path:
        candidate_path = root / "artifacts" / "active" / "run-001" / "candidate.json"
        self.write_json(
            candidate_path,
            {
                "freeze_ready": True,
                "status": "freeze_ready",
                "product_summary": "Gate skill renders a reviewer-facing projection from Machine SSOT.",
                "roles": ["reviewer", "ssot owner"],
                "main_flow": ["render projection", "review constraints", "dispatch decision"],
                "deliverables": ["gate decision package"],
                "completed_state": "Projection ready for gate review.",
                "authoritative_output": "Machine SSOT remains authoritative.",
                "frozen_downstream_boundary": "Projection is not inheritable downstream.",
                "open_technical_decisions": ["Confirm reviewer wording."],
            },
        )
        self.write_json(
            root / "artifacts" / "registry" / "candidate-impl.json",
            {
                "artifact_ref": candidate_ref,
                "managed_artifact_ref": "artifacts/active/run-001/candidate.json",
                "status": "candidate",
                "trace": {"run_ref": "RUN-001"},
                "metadata": {},
                "lineage": [],
            },
        )
        acceptance_path = root / "artifacts" / "active" / "run-001" / "acceptance.json"
        evidence_path = root / "artifacts" / "active" / "run-001" / "evidence.json"
        self.write_json(acceptance_path, {"accepted": True})
        self.write_json(evidence_path, {"evidence": True})
        package_dir = root / "artifacts" / "active" / "gates" / "packages"
        self.write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": "RUN-001"},
                "payload": {
                    "candidate_ref": candidate_ref,
                    "machine_ssot_ref": candidate_ref,
                    "acceptance_ref": "artifacts/active/run-001/acceptance.json",
                    "evidence_bundle_ref": "artifacts/active/run-001/evidence.json",
                },
            },
        )
        return package_dir

    def make_runtime_pending_item(self, root: Path, *, key: str = "gate-job-001") -> None:
        handoff_ref = f"artifacts/active/gates/handoffs/{key}.json"
        pending_ref = f"artifacts/active/gates/pending/{key}.json"
        self.write_json(
            root / handoff_ref,
            {
                "trace": {"run_ref": "RUN-001"},
                "producer_ref": "skill.test",
                "proposal_ref": key,
                "payload_ref": "artifacts/active/gates/packages/gate-ready-package.json",
                "pending_state": "gate_pending",
            },
        )
        self.write_json(
            root / pending_ref,
            {
                "trace": {"run_ref": "RUN-001"},
                "handoff_ref": handoff_ref,
                "producer_ref": "skill.test",
                "proposal_ref": key,
                "pending_state": "gate_pending",
            },
        )
        self.write_json(
            root / "artifacts" / "active" / "gates" / "pending" / "index.json",
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

    def test_run_approve_auto_materializes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_gate_ready_package(repo_root)

            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "gate-approve", cwd=ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "gate-decision-bundle.json").read_text(encoding="utf-8"))
            runtime_refs = json.loads((artifacts_dir / "runtime-artifact-refs.json").read_text(encoding="utf-8"))
            freeze_gate = json.loads((artifacts_dir / "gate-freeze-gate.json").read_text(encoding="utf-8"))

            self.assertEqual(bundle["decision"], "approve")
            self.assertEqual(bundle["dispatch_target"], "formal_publication_trigger")
            self.assertEqual(bundle["machine_ssot_ref"], "candidate.impl")
            self.assertEqual(bundle["projection_status"], "review_visible")
            self.assertTrue(bundle["human_projection_ref"].endswith(".json"))
            self.assertEqual(bundle["materialized_job_ref"], "")
            self.assertTrue(bundle["materialized_handoff_ref"].endswith("materialized-handoff.json"))
            self.assertTrue(runtime_refs["dispatch_receipt_ref"].endswith("gate-dispatch-receipt.json"))
            self.assertTrue(freeze_gate["freeze_ready"])

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir), cwd=ROOT)
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir), cwd=ROOT)
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

    def test_run_revise_dispatches_execution_return(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_gate_ready_package(repo_root)
            self.write_json(
                repo_root / "artifacts" / "active" / "audit" / "finding-bundle.json",
                {"findings": [{"severity": "blocker", "title": "missing basis"}]},
            )

            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "gate-revise", cwd=ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "gate-decision-bundle.json").read_text(encoding="utf-8"))
            freeze_gate = json.loads((artifacts_dir / "gate-freeze-gate.json").read_text(encoding="utf-8"))

            self.assertEqual(bundle["decision"], "revise")
            self.assertEqual(bundle["dispatch_target"], "execution_return")
            self.assertEqual(bundle["projection_status"], "review_visible")
            self.assertEqual(bundle["materialized_handoff_ref"], "")
            self.assertTrue(bundle["materialized_job_ref"].endswith("gate-decision-return.json"))
            self.assertTrue(freeze_gate["freeze_ready"])

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir), cwd=ROOT)
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_prepare_round_show_pending_and_capture_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_gate_ready_package(repo_root)

            prepare = self.run_cmd(
                "prepare-round",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "gate-round",
                cwd=ROOT,
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            prepare_payload = json.loads(prepare.stdout)
            artifacts_dir = Path(prepare_payload["artifacts_dir"])
            self.assertTrue((artifacts_dir / "human-decision-request.json").exists())
            self.assertTrue((artifacts_dir / "human-decision-request.md").exists())
            self.assertTrue((artifacts_dir / "round-state.json").exists())

            pending = self.run_cmd("show-pending", "--repo-root", str(repo_root), cwd=ROOT)
            self.assertEqual(pending.returncode, 0, pending.stderr)
            pending_payload = json.loads(pending.stdout)
            self.assertEqual(pending_payload["pending_count"], 1)
            self.assertEqual(pending_payload["items"][0]["run_id"], "gate-round")

            capture = self.run_cmd(
                "capture-decision",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--reply",
                "revise: Please tighten the evidence and target wording.",
                "--approver",
                "human/reviewer-001",
                cwd=ROOT,
            )
            self.assertEqual(capture.returncode, 0, capture.stderr)
            capture_payload = json.loads(capture.stdout)
            submission = json.loads((artifacts_dir / "human-decision-submission.json").read_text(encoding="utf-8"))
            bundle = json.loads((artifacts_dir / "gate-decision-bundle.json").read_text(encoding="utf-8"))
            state = json.loads((artifacts_dir / "round-state.json").read_text(encoding="utf-8"))

            self.assertEqual(submission["decision"], "revise")
            self.assertEqual(bundle["decision"], "revise")
            self.assertTrue(any(item.endswith("human-decision-request.json") for item in bundle["source_refs"]))
            self.assertTrue(any(item.endswith("human-decision-submission.json") for item in bundle["source_refs"]))
            self.assertEqual(state["status"], "decision_recorded")
            self.assertEqual(capture_payload["decision"], "revise")

    def test_claim_next_pulls_from_runtime_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_gate_ready_package(repo_root)
            self.make_runtime_pending_item(repo_root, key="queue-item-001")

            claim = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "queue-round",
                cwd=ROOT,
            )
            self.assertEqual(claim.returncode, 0, claim.stderr)
            claim_payload = json.loads(claim.stdout)
            artifacts_dir = Path(claim_payload["artifacts_dir"])
            pending = json.loads((repo_root / "artifacts" / "active" / "gates" / "pending" / "queue-item-001.json").read_text(encoding="utf-8"))
            state = json.loads((artifacts_dir / "round-state.json").read_text(encoding="utf-8"))

            self.assertEqual(pending["claim_status"], "active")
            self.assertEqual(pending["claimed_run_id"], "queue-round")
            self.assertEqual(state["handoff_ref"], "artifacts/active/gates/handoffs/queue-item-001.json")
            self.assertTrue((artifacts_dir / "queue-claim.json").exists())
            self.assertTrue((artifacts_dir / "human-decision-request.json").exists())

    def test_capture_comment_and_regenerate_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_gate_ready_package(repo_root)

            run_result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "gate-comment", cwd=ROOT)
            self.assertEqual(run_result.returncode, 0, run_result.stderr)
            artifacts_dir = Path(json.loads(run_result.stdout)["artifacts_dir"])

            comment_result = self.run_cmd(
                "capture-comment",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--comment-ref",
                "comment-001",
                "--comment-text",
                "Please tighten the product summary wording.",
                "--comment-author",
                "reviewer-A",
                "--target-block",
                "product_summary",
                cwd=ROOT,
            )
            self.assertEqual(comment_result.returncode, 0, comment_result.stderr)
            comment_payload = json.loads(comment_result.stdout)
            self.assertTrue(comment_payload["revision_request_ref"].endswith("comment-001.json"))

            updated_ssot = repo_root / "artifacts" / "active" / "run-001" / "candidate-updated.json"
            current = json.loads((repo_root / "artifacts" / "active" / "run-001" / "candidate.json").read_text(encoding="utf-8"))
            current["product_summary"] = "Updated summary after gate reviewer feedback."
            self.write_json(updated_ssot, current)

            regenerate_result = self.run_cmd(
                "regenerate-projection",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--updated-ssot-ref",
                "artifacts/active/run-001/candidate-updated.json",
                cwd=ROOT,
            )
            self.assertEqual(regenerate_result.returncode, 0, regenerate_result.stderr)
            bundle = json.loads((artifacts_dir / "gate-decision-bundle.json").read_text(encoding="utf-8"))
            self.assertEqual(bundle["machine_ssot_ref"], "artifacts/active/run-001/candidate-updated.json")
            summary_block = next(block for block in bundle["human_projection"]["review_blocks"] if block["id"] == "product_summary")
            self.assertIn("Updated summary after gate reviewer feedback.", summary_block["content"][0])


if __name__ == "__main__":
    unittest.main()
