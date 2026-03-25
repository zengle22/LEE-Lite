import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-qa-feat-to-testset" / "scripts" / "feat_to_testset.py"


class FeatToTestSetWorkflowTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def make_bundle_json(self, feature: dict[str, object], run_id: str) -> dict[str, object]:
        feat_ref = str(feature["feat_ref"])
        return {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "workflow_run_id": run_id,
            "title": f"{feature['title']} FEAT Freeze Bundle",
            "status": "accepted",
            "schema_version": "1.0.0",
            "epic_freeze_ref": "EPIC-SRC-001",
            "src_root_id": "SRC-001",
            "feat_refs": [feat_ref],
            "source_refs": [
                f"product.epic-to-feat::{run_id}",
                feat_ref,
                "EPIC-SRC-001",
                "SRC-001",
                "ADR-012",
            ],
            "features": [feature],
        }

    def make_feat_package(self, root: Path, run_id: str, bundle_json: dict[str, object]) -> Path:
        package_dir = root / "artifacts" / "epic-to-feat" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "workflow_run_id": run_id,
            "status": bundle_json["status"],
            "schema_version": bundle_json["schema_version"],
            "epic_freeze_ref": bundle_json["epic_freeze_ref"],
            "src_root_id": bundle_json["src_root_id"],
        }
        markdown = [
            "---",
            *[f"{key}: {value}" for key, value in frontmatter.items()],
            "source_refs:",
            *[f"  - {item}" for item in bundle_json["source_refs"]],
            "---",
            "",
            f"# {bundle_json['title']}",
            "",
            "## FEAT Inventory",
            "",
            *[f"### {feature['feat_ref']} {feature['title']}" for feature in bundle_json["features"]],
        ]
        (package_dir / "feat-freeze-bundle.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
        (package_dir / "feat-freeze-bundle.json").write_text(
            json.dumps(bundle_json, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        payloads = {
            "package-manifest.json": {"status": bundle_json["status"], "run_id": run_id},
            "feat-review-report.json": {"decision": "pass", "summary": "review ok"},
            "feat-acceptance-report.json": {"decision": "approve", "summary": "acceptance ok"},
            "feat-defect-list.json": [],
            "feat-freeze-gate.json": {"workflow_key": "product.epic-to-feat", "freeze_ready": True, "decision": "pass"},
            "handoff-to-feat-downstreams.json": {
                "target_workflows": [{"workflow": "workflow.qa.test_set_production_l3"}],
                "derivable_children": ["TECH", "TASK", "TESTSET"],
            },
            "execution-evidence.json": {"run_id": run_id, "decision": "pass"},
            "supervision-evidence.json": {"run_id": run_id, "decision": "pass"},
        }
        for name, payload in payloads.items():
            (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return package_dir

    def test_run_emits_candidate_package_ready_for_external_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-TESTSET",
                "title": "Governed FEAT to TESTSET",
                "goal": "将 FEAT acceptance 拆成受治理 TESTSET candidate package。",
                "scope": [
                    "将 selected FEAT acceptance checks 映射为 test units。",
                    "输出 analysis、strategy 与 TESTSET 主对象。",
                    "生成 gate subjects 与 test execution handoff。",
                ],
                "constraints": [
                    "只有 test-set.yaml 是正式主对象。",
                    "approval 前不得把 candidate package 物化为 freeze package。",
                    "gate 必须外置且 subject identity 稳定。",
                ],
                "dependencies": [
                    "上游 feat_freeze_package 已 freeze_ready。",
                    "下游 test execution skill 可消费 required_environment_inputs。",
                ],
                "non_goals": [
                    "不直接实现 test runner 细节。",
                    "不扩张为 TECH 或 TASK 设计。",
                ],
                "track": "adoption_e2e",
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "analysis 保持 FEAT 边界",
                        "given": "selected FEAT",
                        "when": "产出 analysis",
                        "then": "scope、constraints、non-goals 均可追溯",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "strategy 覆盖 acceptance",
                        "given": "acceptance checks",
                        "when": "派生 strategy",
                        "then": "每条 acceptance 都至少映射一个 test unit",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "handoff 可执行",
                        "given": "candidate package",
                        "when": "交接到 test execution",
                        "then": "required_environment_inputs 可直接消费",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-TESTSET", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-to-testset-input")
            input_dir = self.make_feat_package(repo_root, "feat-to-testset-input", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-SRC-001-TESTSET",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-to-testset-output",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])

            bundle_json = json.loads((artifacts_dir / "test-set-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            freeze_gate = json.loads((artifacts_dir / "test-set-freeze-gate.json").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            test_set = yaml.safe_load((artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))

            self.assertEqual(bundle_json["artifact_type"], "test_set_candidate_package")
            self.assertEqual(bundle_json["status"], "approval_pending")
            self.assertEqual(manifest["status"], "approval_pending")
            self.assertEqual(test_set["status"], "approved")
            self.assertEqual(freeze_gate["status"], "pending")
            self.assertTrue(freeze_gate["ready_for_external_approval"])
            self.assertEqual(handoff["target_skill"], "skill.qa.test_exec_web_e2e")
            self.assertTrue((artifacts_dir / "analysis-review-subject.json").exists())
            self.assertTrue((artifacts_dir / "strategy-review-subject.json").exists())
            self.assertTrue((artifacts_dir / "test-set-approval-subject.json").exists())
            self.assertGreaterEqual(len(test_set["test_units"]), 3)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

    def test_validate_input_rejects_missing_feat_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-INPUT",
                "title": "Input Validation",
                "goal": "验证输入缺失 feat_ref 时被拒绝。",
                "scope": ["校验 required files。", "校验 feat_ref 存在。", "校验 upstream lineage。"],
                "constraints": ["需要 EPIC 引用。", "需要 SRC 引用。", "需要 acceptance checks。"],
                "acceptance_checks": [
                    {"id": "AC-01", "scenario": "required files present", "given": "input dir", "when": "校验", "then": "全部文件存在"},
                    {"id": "AC-02", "scenario": "feat exists", "given": "feat_ref", "when": "查找", "then": "返回匹配 feature"},
                    {"id": "AC-03", "scenario": "handoff admits TESTSET", "given": "handoff", "when": "检查 derivable children", "then": "包含 TESTSET"},
                ],
                "source_refs": ["FEAT-SRC-001-INPUT", "EPIC-SRC-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-to-testset-invalid")
            input_dir = self.make_feat_package(repo_root, "feat-to-testset-invalid", bundle)

            result = self.run_cmd("validate-input", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-404")
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("Selected feat_ref not found" in error for error in payload["errors"]))


if __name__ == "__main__":
    unittest.main()
