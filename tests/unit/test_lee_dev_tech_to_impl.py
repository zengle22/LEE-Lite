import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-dev-tech-to-impl" / "scripts" / "tech_to_impl.py"


class TechToImplWorkflowTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def make_tech_package(self, root: Path, run_id: str, bundle_json: dict[str, object]) -> Path:
        package_dir = root / "artifacts" / "feat-to-tech" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "artifact_type": "tech_design_package",
            "workflow_key": "dev.feat-to-tech",
            "workflow_run_id": run_id,
            "status": bundle_json["status"],
            "schema_version": bundle_json["schema_version"],
            "feat_ref": bundle_json["feat_ref"],
            "tech_ref": bundle_json["tech_ref"],
            "source_refs": bundle_json["source_refs"],
        }
        markdown = [
            "---",
            f"artifact_type: {frontmatter['artifact_type']}",
            f"workflow_key: {frontmatter['workflow_key']}",
            f"workflow_run_id: {frontmatter['workflow_run_id']}",
            f"status: {frontmatter['status']}",
            f"schema_version: {frontmatter['schema_version']}",
            f"feat_ref: {frontmatter['feat_ref']}",
            f"tech_ref: {frontmatter['tech_ref']}",
            "source_refs:",
            *[f"  - {item}" for item in frontmatter["source_refs"]],
            "---",
            "",
            f"# {bundle_json['title']}",
            "",
            "## Selected FEAT",
            "",
            f"- feat_ref: {bundle_json['feat_ref']}",
            f"- tech_ref: {bundle_json['tech_ref']}",
        ]
        (package_dir / "tech-design-bundle.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
        (package_dir / "tech-design-bundle.json").write_text(
            json.dumps(bundle_json, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (package_dir / "tech-spec.md").write_text("# TECH\n\ntech spec\n", encoding="utf-8")
        (package_dir / "tech-impl.md").write_text("# TECH_IMPL\n\ntech impl\n", encoding="utf-8")
        if bundle_json.get("arch_required"):
            (package_dir / "arch-design.md").write_text("# ARCH\n\narch\n", encoding="utf-8")
        if bundle_json.get("api_required"):
            (package_dir / "api-contract.md").write_text("# API\n\napi\n", encoding="utf-8")

        payloads = {
            "package-manifest.json": {"status": bundle_json["status"], "run_id": run_id},
            "tech-review-report.json": {"decision": "pass", "summary": "review ok"},
            "tech-acceptance-report.json": {"decision": "approve", "summary": "acceptance ok"},
            "tech-defect-list.json": [],
            "tech-freeze-gate.json": {"workflow_key": "dev.feat-to-tech", "freeze_ready": True, "decision": "pass"},
            "handoff-to-tech-impl.json": {
                "target_workflow": "workflow.dev.tech_to_impl",
                "feat_ref": bundle_json["feat_ref"],
                "tech_ref": bundle_json["tech_ref"],
                "arch_ref": bundle_json.get("arch_ref"),
                "api_ref": bundle_json.get("api_ref"),
            },
            "execution-evidence.json": {"run_id": run_id, "decision": "pass"},
            "supervision-evidence.json": {"run_id": run_id, "decision": "pass"},
        }
        for name, payload in payloads.items():
            (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return package_dir

    def make_bundle_json(self, feature: dict[str, object], run_id: str, *, arch_required: bool = False, api_required: bool = False) -> dict[str, object]:
        feat_ref = str(feature["feat_ref"])
        tech_ref = f"TECH-{feat_ref}"
        source_refs = [
            f"dev.feat-to-tech::{run_id}",
            feat_ref,
            tech_ref,
            "EPIC-SRC001",
            "SRC-001",
            "ADR-014",
        ]
        arch_ref = f"ARCH-{feat_ref.replace('FEAT-', '', 1)}" if arch_required else None
        api_ref = f"API-{feat_ref.replace('FEAT-', '', 1)}" if api_required else None
        return {
            "artifact_type": "tech_design_package",
            "workflow_key": "dev.feat-to-tech",
            "workflow_run_id": run_id,
            "title": f"{feature['title']} Technical Design Package",
            "status": "accepted",
            "schema_version": "1.0.0",
            "feat_ref": feat_ref,
            "tech_ref": tech_ref,
            "arch_ref": arch_ref,
            "api_ref": api_ref,
            "arch_required": arch_required,
            "api_required": api_required,
            "source_refs": source_refs,
            "selected_feat": feature,
            "tech_design": {
                "design_focus": list(feature["scope"])[:3],
                "implementation_rules": list(feature["constraints"])[:3],
            },
            "design_consistency_check": {"passed": True, "checks": [], "issues": []},
        }

    def test_run_emits_impl_task_package_with_dual_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-201",
                "title": "配置中心页面与发布主链联动能力",
                "goal": "让配置中心页面、接口和发布 gate 在一次实施单内协同落地。",
                "scope": [
                    "新增配置中心页面和交互反馈。",
                    "新增 request/response API contract。",
                    "补充发布 gate 和 handoff 语义。",
                ],
                "constraints": [
                    "不得改写上游 TECH 设计。",
                    "必须保留 smoke gate subject。",
                    "前后端必须共享配置状态语义。",
                ],
                "dependencies": [
                    "consumer/provider coordination with publish workflow",
                    "release gate review dependency",
                ],
                "acceptance_checks": [
                    {"scenario": "页面展示配置项", "then": "配置中心页面可正确渲染"},
                    {"scenario": "接口提交配置变更", "then": "request/response contract 稳定"},
                    {"scenario": "发布 gate 可读实施包", "then": "handoff 和 smoke subject 完整"},
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-dual", arch_required=True, api_required=True)
            input_dir = self.make_tech_package(repo_root, "tech-impl-dual", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                feature["feat_ref"],
                "--tech-ref",
                bundle["tech_ref"],
                "--repo-root",
                str(repo_root),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            impl_bundle = json.loads((artifacts_dir / "impl-bundle.json").read_text(encoding="utf-8"))
            smoke_gate = json.loads((artifacts_dir / "smoke-gate-subject.json").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-feature-delivery.json").read_text(encoding="utf-8"))
            impl_task = (artifacts_dir / "impl-task.md").read_text(encoding="utf-8")

            self.assertTrue((artifacts_dir / "frontend-workstream.md").exists())
            self.assertTrue((artifacts_dir / "backend-workstream.md").exists())
            self.assertTrue((artifacts_dir / "upstream-design-refs.json").exists())
            self.assertEqual(impl_bundle["status"], "execution_ready")
            self.assertTrue(smoke_gate["ready_for_execution"])
            self.assertEqual(handoff["target_template_id"], "template.dev.feature_delivery_l2")
            self.assertIn("## 4. 实施步骤", impl_task)
            self.assertIn("## 7. 验收检查点", impl_task)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

    def test_run_emits_backend_and_migration_when_frontend_not_needed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-202",
                "title": "主链路径迁移与注册表切换能力",
                "goal": "让主链 runtime path、registry 和 cutover 规则稳定进入实施候选包。",
                "scope": [
                    "规范 runtime path 和 registry 落点。",
                    "明确 cutover 和 rollback 约束。",
                    "保持 backend service side 的写入边界。",
                ],
                "constraints": [
                    "不得扩展为 UI 设计问题。",
                    "所有变更必须经过冻结的 TECH 设计。",
                    "迁移阶段必须具备 rollback 方案。",
                ],
                "dependencies": ["registry contract", "workflow gate", "cutover approval"],
                "acceptance_checks": [
                    {"scenario": "path boundary stable", "then": "path 治理进入 backend execution"},
                    {"scenario": "registry traceable", "then": "registry contract 清晰可审计"},
                    {"scenario": "cutover recoverable", "then": "rollback 与 compat mode 可执行"},
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-backend", arch_required=True, api_required=False)
            input_dir = self.make_tech_package(repo_root, "tech-impl-backend", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                feature["feat_ref"],
                "--tech-ref",
                bundle["tech_ref"],
                "--repo-root",
                str(repo_root),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            impl_bundle = json.loads((artifacts_dir / "impl-bundle.json").read_text(encoding="utf-8"))

            self.assertFalse((artifacts_dir / "frontend-workstream.md").exists())
            self.assertTrue((artifacts_dir / "backend-workstream.md").exists())
            self.assertTrue((artifacts_dir / "migration-cutover-plan.md").exists())
            self.assertFalse(impl_bundle["workstream_assessment"]["frontend_required"])
            self.assertTrue(impl_bundle["workstream_assessment"]["backend_required"])
            self.assertTrue(impl_bundle["workstream_assessment"]["migration_required"])

    def test_validate_input_rejects_mismatched_tech_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-203",
                "title": "TECH ref mismatch validation",
                "goal": "验证输入校验会拒绝 tech_ref 不匹配的 TECH 包。",
                "scope": ["保留 tech 输出", "保留 impl task 语义", "不允许 tech_ref 漂移"],
                "constraints": ["输入必须显式选择 tech_ref", "不得猜测 tech_ref", "不得绕过 freeze gate"],
                "dependencies": ["workflow.dev.tech_to_impl"],
                "acceptance_checks": [
                    {"scenario": "input tech_ref visible", "then": "selected TECH 可追溯"},
                    {"scenario": "validation blocks drift", "then": "tech_ref 不匹配会被拒绝"},
                    {"scenario": "freeze gate preserved", "then": "只有 freeze-ready TECH 能进入 IMPL"},
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-invalid", arch_required=False, api_required=False)
            input_dir = self.make_tech_package(repo_root, "tech-impl-invalid", bundle)

            result = self.run_cmd(
                "validate-input",
                "--input",
                str(input_dir),
                "--feat-ref",
                feature["feat_ref"],
                "--tech-ref",
                "TECH-FEAT-SRC-001-404",
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("tech-ref" in error.lower() or "tech_ref" in error.lower() for error in payload["errors"]))


if __name__ == "__main__":
    unittest.main()

