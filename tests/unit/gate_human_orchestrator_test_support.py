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
