import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "l3" / "ll-governance-failure-capture" / "scripts" / "workflow_runtime.py"


class FailureCaptureRuntimeTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_run_records_ref_resolution_and_readiness_rejects_unresolved_edit_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            existing_source = repo_root / "artifacts" / "reports" / "demo-source.json"
            existing_source.parent.mkdir(parents=True, exist_ok=True)
            existing_source.write_text('{"ok": true}\n', encoding="utf-8")
            existing_evidence = repo_root / "artifacts" / "reports" / "demo-evidence.json"
            existing_evidence.write_text('{"ok": true}\n', encoding="utf-8")
            editable_file = repo_root / "skills" / "demo" / "script.py"
            editable_file.parent.mkdir(parents=True, exist_ok=True)
            editable_file.write_text("print('ok')\n", encoding="utf-8")

            request = {
                "artifact_type": "failure_capture_request",
                "schema_version": "0.1.0",
                "status": "open",
                "skill_id": "demo.skill",
                "sku": "demo_sku",
                "run_id": "run-001",
                "artifact_id": "ART-001",
                "failure_scope": "artifact",
                "detected_stage": "human_final_review",
                "detected_by": "reviewer.demo",
                "severity": "high",
                "triage_level": "P1",
                "symptom_summary": "demo symptom",
                "problem_description": "demo problem",
                "failed_artifact_ref": "artifacts/reports/demo-source.json",
                "upstream_refs": ["artifacts/reports/demo-source.json", "artifacts/reports/missing-source.json"],
                "evidence_refs": ["artifacts/reports/demo-evidence.json", "artifacts/reports/missing-evidence.json"],
                "repair_goal": "fix demo issue",
                "suggested_edit_scope": ["skills/demo/script.py:handler", "skills/demo/missing.py:missing_handler"],
            }
            request_path = repo_root / "request.json"
            request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = self.run_cmd("run", "--input", str(request_path), "--repo-root", str(repo_root), "--allow-update")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            package_dir = Path(payload["package_dir"])
            manifest = json.loads((package_dir / "capture_manifest.json").read_text(encoding="utf-8"))

            resolution = manifest["ref_resolution"]
            self.assertEqual(resolution["source_refs"]["missing"], 1)
            self.assertEqual(resolution["evidence_refs"]["missing"], 1)
            self.assertEqual(resolution["allowed_edit_scope"]["missing"], 1)
            self.assertEqual(resolution["allowed_edit_scope"]["resolved"], 1)
            self.assertEqual(manifest["reproducibility_status"], "captured_but_not_reproducible")

            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(package_dir))
            self.assertNotEqual(readiness.returncode, 0)
            self.assertIn("allowed_edit_scope contains unresolved refs", readiness.stdout)
            self.assertIn("source_refs contains unresolved refs", readiness.stdout)
            self.assertIn("evidence_refs contains unresolved refs", readiness.stdout)


if __name__ == "__main__":
    unittest.main()
