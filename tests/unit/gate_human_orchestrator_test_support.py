import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-gate-human-orchestrator" / "scripts" / "gate_human_orchestrator.py"


class GateHumanOrchestratorTestSupport(unittest.TestCase):
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
        self.write_json(
            root / "artifacts" / "active" / "run-001" / "candidate.json",
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
        self.write_json(root / "artifacts" / "active" / "run-001" / "acceptance.json", {"accepted": True})
        self.write_json(root / "artifacts" / "active" / "run-001" / "evidence.json", {"evidence": True})
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

    def make_raw_to_src_gate_ready_package(self, root: Path, *, run_id: str = "raw-src-run") -> Path:
        artifacts_dir = root / "artifacts" / "raw-to-src" / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / "src-candidate.md").write_text("# SRC Candidate\n\nApproved content.\n", encoding="utf-8")
        self.write_json(
            artifacts_dir / "src-candidate.json",
            {
                "artifact_type": "src_candidate",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": run_id,
                "title": "SRC Candidate",
                "status": "needs_review",
                "problem_statement": "Need a formal SRC artifact after approval.",
            },
        )
        self.write_json(
            root / "artifacts" / "registry" / f"raw-to-src-{run_id}-src-candidate.json",
            {
                "artifact_ref": f"raw-to-src.{run_id}.src-candidate",
                "managed_artifact_ref": f"artifacts/raw-to-src/{run_id}/src-candidate.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "product.raw-to-src"},
                "metadata": {"layer": "formal"},
                "lineage": [],
            },
        )
        self.write_json(artifacts_dir / "acceptance-report.json", {"decision": "approve"})
        self.write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})
        package_dir = artifacts_dir / "input"
        self.write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": run_id, "workflow_key": "product.raw-to-src"},
                "payload": {
                    "candidate_ref": f"raw-to-src.{run_id}.src-candidate",
                    "machine_ssot_ref": f"artifacts/raw-to-src/{run_id}/src-candidate.json",
                    "acceptance_ref": f"artifacts/raw-to-src/{run_id}/acceptance-report.json",
                    "evidence_bundle_ref": f"artifacts/raw-to-src/{run_id}/supervision-evidence.json",
                },
            },
        )
        return package_dir

    def make_feat_freeze_gate_ready_package(self, root: Path, *, run_id: str = "feat-freeze-run") -> Path:
        artifacts_dir = root / "artifacts" / "epic-to-feat" / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.write_json(
            artifacts_dir / "feat-freeze-bundle.json",
            {
                "artifact_type": "feat_freeze_package",
                "workflow_key": "product.epic-to-feat",
                "workflow_run_id": run_id,
                "title": "Execution Runner FEAT Bundle",
                "status": "accepted",
                "epic_freeze_ref": "EPIC-GATE-EXECUTION-RUNNER",
                "feat_refs": [
                    "FEAT-001",
                    "FEAT-002",
                    "FEAT-003",
                ],
                "downstream_workflows": [
                    "workflow.dev.feat_to_tech",
                    "workflow.qa.feat_to_testset",
                ],
                "bundle_intent": "Split the execution runner epic into user-visible FEAT slices so reviewer can approve user entry, control surface, and observability independently.",
                "bundle_shared_non_goals": [
                    "Do not collapse the FEAT bundle back into abstract runtime only wording.",
                    "Do not drift into TECH or implementation sequencing.",
                ],
                "epic_context": {
                    "business_goal": "Freeze approve -> ready job -> runner claim -> next skill invocation as a user-visible product line.",
                    "product_positioning": "This FEAT bundle sits between the approved EPIC and downstream TECH / TESTSET workflows.",
                    "actors_and_roles": [
                        {
                            "role": "Claude/Codex CLI operator",
                            "responsibility": "Start or resume the runner through the dedicated skill entry.",
                        },
                        {
                            "role": "workflow / orchestration operator",
                            "responsibility": "Observe backlog, running, failed, and waiting-human states.",
                        },
                    ],
                    "epic_success_criteria": [
                        "At least one approve -> ready job -> runner claim -> next skill invocation path is testable.",
                        "Runner entry, control surface, and observability stay explicit and user-facing.",
                    ],
                    "decomposition_rules": [
                        "Split by independently reviewable product behavior slices.",
                        "Do not rewrite approve into formal publication or publish-only state.",
                    ],
                },
                "features": [
                    {
                        "feat_ref": "FEAT-001",
                        "title": "Runner 用户入口流",
                        "goal": "Freeze a dedicated user-invokable runner skill entry.",
                        "track": "foundation",
                    },
                    {
                        "feat_ref": "FEAT-002",
                        "title": "Runner 控制面流",
                        "goal": "Freeze the CLI control surface for claim, run, complete, and fail.",
                        "track": "foundation",
                    },
                    {
                        "feat_ref": "FEAT-003",
                        "title": "Runner 运行监控流",
                        "goal": "Freeze the observability surface for backlog, running, failed, and waiting-human states.",
                        "track": "foundation",
                    },
                ],
                "source_refs": [
                    "ADR-018",
                    "EPIC-GATE-EXECUTION-RUNNER",
                ],
            },
        )
        self.write_json(artifacts_dir / "acceptance-report.json", {"decision": "approve"})
        self.write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})
        package_dir = artifacts_dir / "input"
        self.write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": run_id, "workflow_key": "product.epic-to-feat"},
                "payload": {
                    "candidate_ref": f"epic-to-feat.{run_id}.feat-freeze-bundle",
                    "machine_ssot_ref": f"artifacts/epic-to-feat/{run_id}/feat-freeze-bundle.json",
                    "acceptance_ref": f"artifacts/epic-to-feat/{run_id}/acceptance-report.json",
                    "evidence_bundle_ref": f"artifacts/epic-to-feat/{run_id}/supervision-evidence.json",
                },
            },
        )
        return package_dir

    def make_runtime_pending_item(self, root: Path, *, key: str = "gate-job-001") -> None:
        handoff_ref = f"artifacts/active/gates/handoffs/{key}.json"
        pending_ref = f"artifacts/active/gates/pending/{key}.json"
        self.write_json(root / handoff_ref, {"trace": {"run_ref": "RUN-001"}, "producer_ref": "skill.test", "proposal_ref": key, "payload_ref": "artifacts/active/gates/packages/gate-ready-package.json", "pending_state": "gate_pending"})
        self.write_json(root / pending_ref, {"trace": {"run_ref": "RUN-001"}, "handoff_ref": handoff_ref, "producer_ref": "skill.test", "proposal_ref": key, "pending_state": "gate_pending"})
        index_path = root / "artifacts" / "active" / "gates" / "pending" / "index.json"
        index_payload = {"handoffs": {}}
        if index_path.exists():
            index_payload = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(index_payload.get("handoffs"), dict):
                index_payload["handoffs"] = {}
        index_payload["handoffs"][key] = {
            "handoff_ref": handoff_ref,
            "gate_pending_ref": pending_ref,
            "payload_digest": "digest",
            "trace_ref": "",
            "pending_state": "gate_pending",
            "assigned_gate_queue": "mainline.gate.pending",
        }
        self.write_json(index_path, index_payload)

    def make_legacy_runtime_pending_item(self, root: Path, *, key: str = "legacy-gate-job-001") -> Path:
        candidate_md = root / "artifacts" / "raw-to-src" / "run-legacy" / "src-candidate.md"
        candidate_md.parent.mkdir(parents=True, exist_ok=True)
        candidate_md.write_text("# Legacy candidate\n", encoding="utf-8")
        self.write_json(root / "artifacts" / "registry" / "formal-src-run-legacy.json", {"artifact_ref": "formal.src.run-legacy", "managed_artifact_ref": "artifacts/raw-to-src/run-legacy/src-candidate.md", "status": "materialized", "trace": {"run_ref": "RUN-LEGACY"}, "metadata": {}, "lineage": []})
        proposal_path = root / "artifacts" / "raw-to-src" / "run-legacy" / "handoff-proposal.json"
        self.write_json(proposal_path, {"supporting_artifact_refs": ["artifacts/raw-to-src/run-legacy/acceptance-report.json"], "evidence_bundle_refs": ["artifacts/raw-to-src/run-legacy/execution-evidence.json"]})
        self.write_json(root / "artifacts" / "raw-to-src" / "run-legacy" / "acceptance-report.json", {"decision": "approve"})
        self.write_json(root / "artifacts" / "raw-to-src" / "run-legacy" / "execution-evidence.json", {"ok": True})
        handoff_path = root / "artifacts" / "active" / "handoffs" / f"{key}.json"
        pending_path = root / "artifacts" / "active" / "gates" / "pending" / f"{key}.json"
        self.write_json(
            handoff_path,
            {
                "trace": {"run_ref": "RUN-LEGACY"},
                "producer_ref": "skill.test",
                "proposal_ref": str(proposal_path),
                "payload_ref": str(candidate_md),
                "trace_context_ref": str(root / "artifacts" / "raw-to-src" / "run-legacy" / "execution-evidence.json"),
                "state": "gate_pending",
                "gate_pending_ref": f"artifacts/active/gates/pending/{key}.json",
            },
        )
        self.write_json(pending_path, {"handoff_ref": f"artifacts/active/handoffs/{key}.json", "pending_state": "gate_pending", "assigned_gate_queue": "gate-queue-001"})
        self.write_json(root / "artifacts" / "active" / "gates" / "pending" / "_queue-index.json", {"next_index": 2})
        return pending_path
