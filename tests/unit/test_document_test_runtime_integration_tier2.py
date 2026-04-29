import json
import tempfile
from pathlib import Path

import yaml

from tests.unit.support_feat_to_tech import FeatToTechWorkflowHarness
from tests.unit.support_tech_to_impl import TechToImplWorkflowHarness


class FeatToTechDocumentTestIntegrationTests(FeatToTechWorkflowHarness):
    def test_feat_to_tech_emits_document_test_and_enforces_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-DOC-TECH-001",
                "title": "主链协作闭环能力",
                "goal": "让 execution、gate、human loops 在主链中形成稳定协作闭环。",
                "scope": ["定义 execution loop 与 gate loop 的 handoff object。", "显式约束 queue、handoff、gate 的协作边界。"],
                "constraints": ["保留双会话双队列闭环。", "下游不得重造 handoff 规则。"],
                "dependencies": ["Boundary to 对象分层与准入能力。"],
                "outputs": ["handoff contract"],
                "acceptance_checks": [
                    {"id": "AC-01", "scenario": "Loop responsibility split is explicit", "given": "主链协作闭环场景", "when": "生成 TECH", "then": "明确 queue/handoff/gate 边界"},
                    {"id": "AC-02", "scenario": "Handoff contract remains canonical", "given": "已有上游 FEAT", "when": "产出 handoff contract", "then": "下游不需要重造 handoff 规则"},
                    {"id": "AC-03", "scenario": "Boundary constraints are preserved", "given": "治理约束存在", "when": "进入 gate 前校验", "then": "queue 与 gate 协作边界保持可追溯"},
                ],
                "source_refs": ["FEAT-DOC-TECH-001", "EPIC-SRC-001-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-doc-tech-input")
            input_dir = self.make_feat_package(repo_root, "feat-doc-tech-input", bundle)
            artifacts_dir = self.run_tech_flow(repo_root, input_dir, "FEAT-DOC-TECH-001", "tech-doc-test")

            report = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            gate = json.loads((artifacts_dir / "tech-freeze-gate.json").read_text(encoding="utf-8"))
            evidence = (artifacts_dir / "evidence-report.md").read_text(encoding="utf-8")

            self.assertEqual(manifest["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))
            self.assertEqual(supervision["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))
            self.assertEqual(supervision["document_test_outcome"], report["test_outcome"])
            self.assertTrue(gate["checks"]["document_test_report_present"])
            self.assertTrue(gate["checks"]["document_test_non_blocking"])
            self.assertIn("## Document Test", evidence)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

            report["test_outcome"] = "blocking_defect_found"
            (artifacts_dir / "document-test-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(readiness.returncode, 0)
            self.assertIn("document_test_non_blocking", readiness.stdout)


class TechToImplDocumentTestIntegrationTests(TechToImplWorkflowHarness):
    def test_tech_to_impl_emits_document_test_and_enforces_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-DOC-IMPL-001",
                "title": "配置中心页面与发布主链联动能力",
                "goal": "让配置中心页面、接口和发布 gate 在一次实施单内协同落地。",
                "scope": ["新增配置中心页面和交互反馈。", "新增 request/response API contract。"],
                "constraints": ["必须保留 smoke gate subject。", "前后端必须共享配置状态语义。"],
                "dependencies": ["release gate review dependency"],
                "acceptance_checks": [
                    {"id": "AC-01", "scenario": "页面展示配置项", "given": "已生成配置中心页面", "when": "加载页面", "then": "配置中心页面可正确渲染"},
                    {"id": "AC-02", "scenario": "接口提交配置变更", "given": "request/response contract 已定义", "when": "提交配置变更", "then": "request/response contract 稳定"},
                    {"id": "AC-03", "scenario": "发布链仍受 smoke gate 约束", "given": "impl candidate package", "when": "进入下游执行前", "then": "smoke gate subject 完整保留"},
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="tech-doc-impl-input", arch_required=True, api_required=True)
            input_dir = self.make_tech_package(repo_root, "tech-doc-impl-input", bundle)
            artifacts_dir = self.run_impl_flow(repo_root, input_dir, feature["feat_ref"], bundle["tech_ref"])

            report = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            gate_ready = json.loads((artifacts_dir / "input" / "gate-ready-package.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))
            self.assertEqual(report["test_outcome"], "no_blocking_defect_found")
            self.assertEqual(supervision["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))
            self.assertEqual(supervision["document_test_outcome"], "no_blocking_defect_found")
            self.assertEqual(gate_ready["payload"]["evidence_bundle_ref"], str(Path("artifacts") / "tech-to-impl" / artifacts_dir.name / "supervision-evidence.json").replace("\\", "/"))

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

            report["test_outcome"] = "blocking_defect_found"
            (artifacts_dir / "document-test-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(readiness.returncode, 0)
            self.assertIn("document-test-report.json test_outcome must match", readiness.stdout)
