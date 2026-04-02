import json
import tempfile
from pathlib import Path

from tests.unit.support_tech_to_impl import TechToImplWorkflowHarness


class TechToImplContractProjectionTests(TechToImplWorkflowHarness):
    def _feature(self, feat_ref: str) -> dict[str, object]:
        return {
            "feat_ref": feat_ref,
            "title": "主链实施契约收敛能力",
            "goal": "让实现包成为可执行单入口，但不篡改上游设计与测试真相。",
            "scope": [
                "输出 implementation task package。",
                "输出 integration/evidence/handoff 收敛信息。",
                "把上游 refs 投影成执行期可消费 contract。",
            ],
            "constraints": [
                "IMPL 不是第二层技术设计。",
                "IMPL 不是业务、设计或测试事实的 SSOT。",
                "若 repo 与上游冲突，必须显式做 discrepancy handling。",
            ],
            "dependencies": [
                "depends on frozen TECH package",
                "depends on downstream feature delivery handoff",
            ],
            "acceptance_checks": [
                {"scenario": "canonical package metadata exists", "then": "bundle carries package semantics and selected upstream refs"},
                {"scenario": "impl task separates contract layers", "then": "required/suggested and normative/informative are explicit"},
            ],
        }

    def test_run_emits_adr034_contract_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = self._feature("FEAT-SRC-009-001")
            bundle = self.make_bundle_json(feature, run_id="tech-impl-contract", arch_required=True, api_required=True)
            input_dir = self.make_tech_package(repo_root, "tech-impl-contract", bundle)

            artifacts_dir = self.run_impl_flow(repo_root, input_dir, feature["feat_ref"], bundle["tech_ref"])
            impl_bundle = json.loads((artifacts_dir / "impl-bundle.json").read_text(encoding="utf-8"))
            impl_task = (artifacts_dir / "impl-task.md").read_text(encoding="utf-8")
            bundle_md = (artifacts_dir / "impl-bundle.md").read_text(encoding="utf-8")
            document_test = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))

            self.assertTrue(impl_bundle["package_semantics"]["canonical_package"])
            self.assertTrue(impl_bundle["package_semantics"]["execution_time_single_entrypoint"])
            self.assertFalse(impl_bundle["package_semantics"]["domain_truth_source"])
            self.assertEqual(impl_bundle["selected_upstream_refs"]["feat_ref"], feature["feat_ref"])
            self.assertEqual(impl_bundle["selected_upstream_refs"]["tech_ref"], bundle["tech_ref"])
            self.assertEqual(impl_bundle["conflict_policy"]["repo_discrepancy_policy"], "explicit_discrepancy_handling_required")
            self.assertEqual(impl_bundle["freshness_status"], "fresh_on_generation")
            self.assertTrue(impl_bundle["rederive_triggers"])
            self.assertTrue(impl_bundle["scope_boundary"]["in_scope"])
            self.assertTrue(impl_bundle["scope_boundary"]["out_of_scope"])
            self.assertIn("tech", impl_bundle["upstream_impacts"])
            self.assertTrue(impl_bundle["change_controls"]["touch_set"])
            self.assertTrue(impl_bundle["repo_touch_points"])
            self.assertTrue(impl_bundle["embedded_execution_contract"]["acceptance_checks"])
            self.assertTrue(impl_bundle["implementation_task_breakdown"])
            self.assertTrue(impl_bundle["acceptance_to_task_mapping"])
            self.assertEqual(impl_bundle["self_contained_policy"]["principle"], "strong_self_contained_execution_contract")
            self.assertEqual(impl_bundle["testset_mapping"]["mapping_policy"], "TESTSET_over_IMPL_when_present")
            self.assertTrue(impl_bundle["testset_mapping"]["mappings"])
            self.assertIn("## Package Semantics", bundle_md)
            self.assertIn("## Consumption Boundary", bundle_md)
            self.assertIn("canonical execution package", bundle_md)
            self.assertIn("### Concrete Touch Set", bundle_md)
            self.assertIn("### Repo-Aware Placement", bundle_md)
            self.assertIn("### Embedded Frozen Contracts", bundle_md)
            self.assertIn("### Ordered Task Breakdown", bundle_md)
            self.assertIn("### Acceptance-to-Task Mapping", bundle_md)
            self.assertIn("## 1. 任务标识", impl_task)
            self.assertIn("## 3. 范围与非目标", impl_task)
            self.assertIn("## 4. 上游收敛结果", impl_task)
            self.assertIn("## 6. 实施要求", impl_task)
            self.assertIn("## 8. 验收标准与 TESTSET 映射", impl_task)
            self.assertIn("## 9. 执行顺序建议", impl_task)
            self.assertIn("## 10. 风险与注意事项", impl_task)
            self.assertIn("### In Scope", impl_task)
            self.assertIn("### Out of Scope", impl_task)
            self.assertIn("### TECH Contract Snapshot", impl_task)
            self.assertIn("### ARCH Constraint Snapshot", impl_task)
            self.assertIn("### State Model Snapshot", impl_task)
            self.assertIn("### Main Sequence Snapshot", impl_task)
            self.assertIn("### Integration Points Snapshot", impl_task)
            self.assertIn("### Implementation Unit Mapping Snapshot", impl_task)
            self.assertIn("### API Contract Snapshot", impl_task)
            self.assertIn("### UI Constraint Snapshot", impl_task)
            self.assertIn("### Embedded Execution Contract", impl_task)
            self.assertIn("### Touch Set / Module Plan", impl_task)
            self.assertIn("### Repo Touch Points", impl_task)
            self.assertIn("### Allowed", impl_task)
            self.assertIn("### Forbidden", impl_task)
            self.assertIn("### Execution Boundary", impl_task)
            self.assertIn("### Acceptance Trace", impl_task)
            self.assertIn("### Acceptance-to-Task Mapping", impl_task)
            self.assertIn("normalize candidate/proposal/evidence submission", impl_task)
            self.assertIn("HandoffEnvelope", impl_task)
            self.assertIn("- status: `execution_ready`", impl_task)
            self.assertNotIn("- status: `in_progress`", impl_task)
            self.assertIn("### Required", impl_task)
            self.assertIn("### Suggested", impl_task)
            self.assertIn("### Ordered Task Breakdown", impl_task)
            self.assertIn("### Normative / MUST", impl_task)
            self.assertIn("### Informative / Context Only", impl_task)
            self.assertIn("discrepancy handling", impl_task)
            self.assertIn("canonical_package", document_test["sections"])
            self.assertIn("freshness", document_test["sections"])
            self.assertIn("self_contained_boundary", document_test["sections"])
            self.assertEqual(document_test["sections"]["downstream_readiness"]["downstream_target"], "template.dev.feature_delivery_l2")
            self.assertIn("recommended_actor", document_test["sections"]["fixability"])
            self.assertIn("mechanical_fixable", document_test["sections"]["fixability"])
            self.assertIn(document_test["sections"]["fixability"]["status"], {"mechanical_fixable", "local_semantic_fixable", "rebuild_required", "human_judgement_required"})
            self.assertIn("T", document_test["tested_at"])
            self.assertTrue(document_test["tested_at"].endswith("Z"))

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_run_structures_provisional_refs_and_suggested_steps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = self._feature("FEAT-SRC-009-002")
            feature["ui_ref"] = "UI-SRC-009-002"
            feature["testset_ref"] = "TESTSET-SRC-009-002"
            feature["provisional_refs"] = [
                {
                    "ref": "UI-SRC-009-002",
                    "impact_scope": "ui acceptance wording",
                    "follow_up_action": "freeze_ui_before_execution",
                }
            ]
            bundle = self.make_bundle_json(feature, run_id="tech-impl-provisional", arch_required=True, api_required=False)
            input_dir = self.make_tech_package(repo_root, "tech-impl-provisional", bundle)

            artifacts_dir = self.run_impl_flow(repo_root, input_dir, feature["feat_ref"], bundle["tech_ref"])
            impl_bundle = json.loads((artifacts_dir / "impl-bundle.json").read_text(encoding="utf-8"))
            impl_task = (artifacts_dir / "impl-task.md").read_text(encoding="utf-8")

            self.assertEqual(impl_bundle["selected_upstream_refs"]["ui_ref"], "UI-SRC-009-002")
            self.assertEqual(impl_bundle["selected_upstream_refs"]["testset_ref"], "TESTSET-SRC-009-002")
            self.assertEqual(impl_bundle["provisional_refs"][0]["ref"], "UI-SRC-009-002")
            self.assertEqual(impl_bundle["provisional_refs"][0]["status"], "provisional")
            self.assertEqual(impl_bundle["provisional_refs"][0]["follow_up_action"], "freeze_ui_before_execution")
            self.assertTrue(impl_bundle["suggested_steps"])
            self.assertEqual(impl_bundle["testset_mapping"]["testset_ref"], "TESTSET-SRC-009-002")
            self.assertEqual(impl_bundle["testset_mapping"]["mappings"][0]["mapped_to"], "TESTSET-SRC-009-002")
            self.assertIn("UI-SRC-009-002", impl_task)
            self.assertIn("TESTSET-SRC-009-002", impl_task)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_validate_output_rejects_missing_document_test_and_package_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = self._feature("FEAT-SRC-009-003")
            bundle = self.make_bundle_json(feature, run_id="tech-impl-invalid", arch_required=False, api_required=False)
            input_dir = self.make_tech_package(repo_root, "tech-impl-invalid", bundle)

            artifacts_dir = self.run_impl_flow(repo_root, input_dir, feature["feat_ref"], bundle["tech_ref"])
            impl_bundle_path = artifacts_dir / "impl-bundle.json"
            impl_bundle = json.loads(impl_bundle_path.read_text(encoding="utf-8"))
            impl_bundle.pop("package_semantics", None)
            impl_bundle.pop("scope_boundary", None)
            impl_bundle_path.write_text(json.dumps(impl_bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (artifacts_dir / "document-test-report.json").unlink()

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("document-test-report.json", validate.stdout)

    def test_run_normalizes_source_refs_to_selected_optional_authorities(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = self._feature("FEAT-SRC-009-005")
            feature["ui_ref"] = "UI-SRC-009-005"
            feature["testset_ref"] = "TESTSET-SRC-009-005"
            bundle = self.make_bundle_json(feature, run_id="tech-impl-source-refs", arch_required=True, api_required=True)
            bundle["source_refs"] = list(bundle["source_refs"]) + [
                "ARCH-SRC-999-001",
                "API-SRC-999-001",
                "UI-SRC-999-001",
                "TESTSET-SRC-999-001",
            ]
            input_dir = self.make_tech_package(repo_root, "tech-impl-source-refs", bundle)

            artifacts_dir = self.run_impl_flow(repo_root, input_dir, feature["feat_ref"], bundle["tech_ref"])
            impl_bundle = json.loads((artifacts_dir / "impl-bundle.json").read_text(encoding="utf-8"))

            self.assertIn("ARCH-SRC-009-005", impl_bundle["source_refs"])
            self.assertIn("API-SRC-009-005", impl_bundle["source_refs"])
            self.assertIn("UI-SRC-009-005", impl_bundle["source_refs"])
            self.assertIn("TESTSET-SRC-009-005", impl_bundle["source_refs"])
            self.assertNotIn("ARCH-SRC-999-001", impl_bundle["source_refs"])
            self.assertNotIn("API-SRC-999-001", impl_bundle["source_refs"])
            self.assertNotIn("UI-SRC-999-001", impl_bundle["source_refs"])
            self.assertNotIn("TESTSET-SRC-999-001", impl_bundle["source_refs"])

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_validate_input_rejects_malformed_structured_provisional_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = self._feature("FEAT-SRC-009-004")
            feature["provisional_refs"] = [{"ref": "UI-SRC-009-004"}]
            bundle = self.make_bundle_json(feature, run_id="tech-impl-bad-provisional", arch_required=False, api_required=False)
            input_dir = self.make_tech_package(repo_root, "tech-impl-bad-provisional", bundle)

            result = self.run_cmd(
                "validate-input",
                "--input",
                str(input_dir),
                "--feat-ref",
                feature["feat_ref"],
                "--tech-ref",
                bundle["tech_ref"],
                "--repo-root",
                str(repo_root),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("follow_up_action", result.stdout)
