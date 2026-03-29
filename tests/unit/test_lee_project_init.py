import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-project-init" / "scripts" / "workflow_runtime.py"


class LlProjectInitTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def write_request(self, workdir: Path, target_root: Path, **overrides: object) -> Path:
        payload: dict[str, object] = {
            "artifact_type": "project_init_request",
            "schema_version": "1.0.0",
            "project_name": "Demo LEE Workspace",
            "project_slug": "demo-lee-workspace",
            "target_root": str(target_root),
            "template_profile": "lee-skill-first",
            "default_branch": "main",
            "managed_files_policy": "create_missing",
            "initialize_runtime_shells": True,
            "authoritative_layout_ref": "skill://ll-project-init/resources/project-structure-reference.md",
        }
        payload.update(overrides)
        request_path = workdir / "request.json"
        request_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return request_path

    def test_validate_input_accepts_minimal_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target_root = temp_root / "repo"
            request_path = self.write_request(temp_root, target_root)
            result = self.run_cmd("validate-input", "--input", str(request_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["normalized_request"]["project_slug"], "demo-lee-workspace")

    def test_run_materializes_scaffold_and_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target_root = temp_root / "repo"
            request_path = self.write_request(temp_root, target_root)
            result = self.run_cmd(
                "run",
                "--input",
                str(request_path),
                "--repo-root",
                str(target_root),
                "--run-id",
                "demo-init-001",
                "--allow-update",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertTrue((target_root / ".editorconfig").exists())
            self.assertTrue((target_root / ".lee" / "config.yaml").exists())
            self.assertTrue((target_root / ".project" / "dirs.yaml").exists())
            self.assertTrue((target_root / "docs" / "repository-layout.md").exists())
            self.assertTrue((target_root / "skills").exists())
            self.assertTrue((target_root / "tests" / "unit").exists())
            artifacts_dir = Path(payload["artifacts_dir"])
            self.assertTrue((artifacts_dir / "project-bootstrap-report.md").exists())
            summary = json.loads((artifacts_dir / "result-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "freeze_ready")

    def test_second_run_skips_existing_files_and_validates_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target_root = temp_root / "repo"
            request_path = self.write_request(temp_root, target_root)
            first = self.run_cmd(
                "run",
                "--input",
                str(request_path),
                "--repo-root",
                str(target_root),
                "--run-id",
                "demo-init-001",
                "--allow-update",
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.run_cmd(
                "run",
                "--input",
                str(request_path),
                "--repo-root",
                str(target_root),
                "--run-id",
                "demo-init-002",
                "--allow-update",
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            second_payload = json.loads(second.stdout)
            self.assertIn(".editorconfig", second_payload["skipped_existing_paths"])
            artifacts_dir = Path(second_payload["artifacts_dir"])
            validate_output = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate_output.returncode, 0, validate_output.stderr)
            validate_ready = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate_ready.returncode, 0, validate_ready.stderr)


if __name__ == "__main__":
    unittest.main()
