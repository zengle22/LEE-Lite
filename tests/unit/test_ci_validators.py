from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ci import common
from tools.ci.checks_code import check_code_size_governance
from tools.ci.checks_repo import check_repo_hygiene, check_ssot_governance
from tools.ci.checks_runtime import build_cli_surface, check_cli_governance, check_cross_domain_compat, check_skill_governance


ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = ROOT / "tools" / "ci" / "manifests"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CiValidatorTests(unittest.TestCase):
    @staticmethod
    def init_git_repo(repo_root: Path) -> None:
        subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "ci@example.com"], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "CI Test"], cwd=repo_root, check=True, capture_output=True)

    def test_repo_hygiene_flags_generated_runtime_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write(repo_root / "pkg" / "__pycache__" / "cached.pyc", "x")
            output_dir = repo_root / "out"
            with patch.object(common, "ROOT", repo_root), patch("tools.ci.checks_repo.ROOT", repo_root):
                exit_code = check_repo_hygiene(["pkg/__pycache__/cached.pyc"], output_dir)
            self.assertEqual(exit_code, 1)
            report = json.loads((output_dir / "repo-hygiene-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["violations"][0]["code"], "forbidden_generated_file")

    def test_ssot_governance_accepts_valid_adr_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write(
                repo_root / "ssot" / "adr" / "ADR-001-Test.MD",
                "# ADR-001：Base\n\n* 状态：Accepted\n* 日期：2026-03-25\n* 相关 ADR：ADR-001\n",
            )
            write(
                repo_root / "ssot" / "adr" / "ADR-002-Test.MD",
                "# ADR-002：Next\n\n* 状态：Draft\n* 日期：2026-03-25\n* 相关 ADR：ADR-001\n\nSee ADR-001.\n",
            )
            output_dir = repo_root / "out"
            with patch.object(common, "ROOT", repo_root), patch("tools.ci.checks_repo.ROOT", repo_root):
                exit_code = check_ssot_governance(
                    ["ssot/adr/ADR-002-Test.MD"],
                    output_dir,
                    MANIFESTS / "ssot_object_registry.json",
                )
            self.assertEqual(exit_code, 0)
            report = json.loads((output_dir / "ssot-governance-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "passed")

    def test_skill_governance_accepts_minimal_bundle_without_provider_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            skill_root = repo_root / "skills" / "demo-skill"
            write(
                skill_root / "SKILL.md",
                "---\nname: demo-skill\ndescription: demo\n---\n\nworkflow.demo\nraw-input\noutput-package\n",
            )
            write(
                skill_root / "ll.contract.yaml",
                "\n".join(
                    [
                        "workflow_key: workflow.demo",
                        "runtime:",
                        "  command: python scripts/run.py --input <path>",
                        "input:",
                        "  artifact_type: raw-input",
                        "  contract_file: input/contract.yaml",
                        "  schema_file: input/schema.json",
                        "output:",
                        "  artifact_type: output-package",
                        "  contract_file: output/contract.yaml",
                        "  schema_file: output/schema.json",
                        "  template_file: output/template.md",
                        "evidence:",
                        "  execution_schema: evidence/execution-evidence.schema.json",
                        "  supervision_schema: evidence/supervision-evidence.schema.json",
                    ]
                ),
            )
            write(skill_root / "ll.lifecycle.yaml", "states:\n  - drafted\n")
            write(skill_root / "input" / "contract.yaml", "name: input\n")
            write(skill_root / "input" / "schema.json", "{}\n")
            write(skill_root / "output" / "contract.yaml", "name: output\n")
            write(skill_root / "output" / "schema.json", "{}\n")
            write(skill_root / "output" / "template.md", "# Output\n")
            write(skill_root / "evidence" / "execution-evidence.schema.json", "{}\n")
            write(skill_root / "evidence" / "supervision-evidence.schema.json", "{}\n")
            write(skill_root / "scripts" / "run.py", "print('ok')\n")
            output_dir = repo_root / "out"
            changed = ["skills/demo-skill/SKILL.md"]
            with patch.object(common, "ROOT", repo_root), patch("tools.ci.checks_runtime.ROOT", repo_root):
                exit_code = check_skill_governance(changed, output_dir, False, MANIFESTS / "test_manifests.json")
            self.assertEqual(exit_code, 0)
            report = json.loads((output_dir / "skill-governance-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "passed")

    def test_cli_governance_matches_committed_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            snapshot_path = output_dir / "snapshot.json"
            snapshot_path.write_text(json.dumps(build_cli_surface(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            exit_code = check_cli_governance(
                ["cli/ll.py"],
                output_dir,
                snapshot_path,
                False,
                MANIFESTS / "test_manifests.json",
            )
            self.assertEqual(exit_code, 0)
            report = json.loads((output_dir / "cli-governance-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "passed")

    def test_cross_domain_compat_maps_known_skill_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            exit_code = check_cross_domain_compat(
                ["skills/ll-product-raw-to-src/SKILL.md"],
                output_dir,
                MANIFESTS / "dependency_rules.json",
                False,
            )
            self.assertEqual(exit_code, 0)
            payload = json.loads((output_dir / "impacted-dependency-chain.json").read_text(encoding="utf-8"))
            self.assertIn("tests/unit/test_lee_product_raw_to_src.py", payload["impacted_tests"])

    def test_cross_domain_compat_fails_closed_for_unmapped_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            exit_code = check_cross_domain_compat(
                ["skills/ll-skill-install/SKILL.md"],
                output_dir,
                MANIFESTS / "dependency_rules.json",
                False,
            )
            self.assertEqual(exit_code, 1)
            report = json.loads((output_dir / "cross-domain-compat-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["violations"][0]["code"], "dependency_mapping_resolution_error")

    def test_code_size_governance_rejects_new_oversized_function(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            write(repo_root / "module.py", "\n".join(["def ok():", "    return 1", ""]))
            subprocess.run(["git", "add", "module.py"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True)
            long_body = "\n".join(f"    x{i} = {i}" for i in range(81))
            write(repo_root / "module.py", f"def ok():\n{long_body}\n    return 1\n")
            output_dir = repo_root / "out"
            with patch.object(common, "ROOT", repo_root), patch("tools.ci.checks_code.ROOT", repo_root):
                exit_code = check_code_size_governance(["module.py"], output_dir, "HEAD")
            self.assertEqual(exit_code, 1)
            report = json.loads((output_dir / "code-size-governance-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["violations"][0]["code"], "function_grew_past_limit")

    def test_code_size_governance_requires_oversized_legacy_file_to_shrink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            large_lines = "\n".join(f"print({i})" for i in range(501))
            write(repo_root / "legacy.py", large_lines + "\n")
            subprocess.run(["git", "add", "legacy.py"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True)
            write(repo_root / "legacy.py", large_lines + "\nprint('more')\n")
            output_dir = repo_root / "out"
            with patch.object(common, "ROOT", repo_root), patch("tools.ci.checks_code.ROOT", repo_root):
                exit_code = check_code_size_governance(["legacy.py"], output_dir, "HEAD")
            self.assertEqual(exit_code, 1)
            report = json.loads((output_dir / "code-size-governance-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["violations"][0]["code"], "oversized_file_not_reduced")


if __name__ == "__main__":
    unittest.main()
