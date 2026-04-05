import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "ll-gate-human-orchestrator" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gate_human_orchestrator_runtime import build_supervision_evidence, validate_package_readiness  # noqa: E402
from gate_human_orchestrator_common import dump_json  # noqa: E402


class GateHumanOrchestratorSemanticTests(unittest.TestCase):
    def _write_gate_artifacts(
        self,
        artifacts_dir: Path,
        *,
        projection_status: str = "review_visible",
        decision_basis_refs: list[str] | None = None,
        machine_ssot_ref: str = "candidate.impl",
        freeze_ready: bool = True,
    ) -> None:
        decision_basis_refs = decision_basis_refs or ["candidate.review", machine_ssot_ref]
        bundle = {
            "workflow_run_id": "gate-run-001",
            "decision_ref": "artifacts/decision.json",
            "decision": "approve",
            "decision_target": "candidate.impl",
            "decision_basis_refs": decision_basis_refs,
            "dispatch_target": "formal_publication_trigger",
            "machine_ssot_ref": machine_ssot_ref,
            "human_projection_ref": "artifacts/projection.json",
            "projection_status": projection_status,
            "projection_markers": {
                "derived_only": True,
                "non_authoritative": True,
                "non_inheritable": True,
            },
            "snapshot_ref": "artifacts/snapshot.json",
            "focus_ref": "artifacts/focus.json",
            "materialized_handoff_ref": "artifacts/handoff.json",
            "materialized_job_ref": "",
            "source_refs": [
                "artifacts/gate-decision-bundle.json",
                "artifacts/decision.json",
                "artifacts/projection.json",
            ],
            "runtime_refs": {
                "brief_record_ref": "artifacts/brief.json",
                "pending_human_decision_ref": "artifacts/pending.json",
                "dispatch_receipt_ref": "artifacts/dispatch.json",
                "human_projection_ref": "artifacts/projection.json",
                "snapshot_ref": "artifacts/snapshot.json",
                "focus_ref": "artifacts/focus.json",
            },
        }
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        dump_json(artifacts_dir / "package-manifest.json", {"status": "drafted"})
        (artifacts_dir / "gate-decision-bundle.md").write_text("# Gate Decision Bundle\n", encoding="utf-8")
        dump_json(artifacts_dir / "gate-decision-bundle.json", bundle)
        dump_json(artifacts_dir / "runtime-artifact-refs.json", bundle["runtime_refs"])
        dump_json(artifacts_dir / "gate-review-report.json", {"decision": "pass"})
        dump_json(artifacts_dir / "gate-acceptance-report.json", {"decision": "approve"})
        dump_json(artifacts_dir / "gate-defect-list.json", [])
        dump_json(artifacts_dir / "gate-freeze-gate.json", {"workflow_key": "governance.gate-human-orchestrator", "decision": "pass", "freeze_ready": freeze_ready})
        dump_json(artifacts_dir / "handoff-to-gate-downstreams.json", {"decision": "approve"})
        dump_json(artifacts_dir / "execution-evidence.json", {"run_id": "gate-run-001", "commands_run": ["gate evaluate"]})
        dump_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass", "semantic_findings": []})

    def test_supervision_flags_machine_ssot_missing_from_basis_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir)
            dump_json(
                artifacts_dir / "gate-decision-bundle.json",
                {
                    "workflow_run_id": "gate-run-001",
                    "decision_target": "candidate.impl",
                    "decision_basis_refs": ["candidate.review"],
                    "decision": "approve",
                    "materialized_handoff_ref": "artifacts/handoff.json",
                    "machine_ssot_ref": "candidate.impl",
                    "human_projection_ref": "artifacts/projection.json",
                    "projection_status": "review_visible",
                    "projection_markers": {
                        "derived_only": True,
                        "non_authoritative": True,
                        "non_inheritable": True,
                    },
                    "snapshot_ref": "artifacts/snapshot.json",
                    "focus_ref": "artifacts/focus.json",
                },
            )
            supervision = build_supervision_evidence(artifacts_dir)
            findings = supervision["semantic_findings"]
            self.assertEqual(supervision["decision"], "revise")
            self.assertTrue(any(item["title"] == "Machine SSOT not cited" for item in findings))

    def test_validate_package_readiness_rejects_missing_machine_ssot_from_basis_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir)
            self._write_gate_artifacts(artifacts_dir, decision_basis_refs=["candidate.review"], machine_ssot_ref="candidate.impl")
            ok, errors = validate_package_readiness(artifacts_dir)
            self.assertFalse(ok)
            self.assertTrue(any("machine_ssot_ref must appear in decision_basis_refs" in item for item in errors))

    def test_validate_package_readiness_rejects_traceability_pending_projection_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir)
            self._write_gate_artifacts(artifacts_dir, projection_status="traceability_pending")
            ok, errors = validate_package_readiness(artifacts_dir)
            self.assertFalse(ok)
            self.assertTrue(any("human projection must be review_visible before freeze" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
