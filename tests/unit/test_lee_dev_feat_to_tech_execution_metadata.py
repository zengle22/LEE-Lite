import json
import tempfile
from pathlib import Path

import yaml

from tests.unit.support_feat_to_tech import FeatToTechWorkflowHarness


class FeatToTechExecutionMetadataTests(FeatToTechWorkflowHarness):
    def test_selected_feat_preserves_impl_relevant_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-009-101",
                "title": "实施输入元数据透传能力",
                "goal": "让 TECH 包保留下游 tech-to-impl 所需的 UI、TESTSET 与 provisional refs 元数据。",
                "scope": [
                    "输出技术设计包。",
                    "保留 selected_feat 中的 execution-relevant refs。",
                ],
                "constraints": [
                    "TECH 不得发明新的执行契约。",
                    "仅透传 FEAT 已知的下游相关元数据。",
                ],
                "dependencies": ["depends on frozen FEAT metadata"],
                "acceptance_checks": [
                    {
                        "scenario": "selected feat keeps metadata",
                        "then": "ui_ref, testset_ref, provisional_refs survive into TECH package",
                    },
                    {
                        "scenario": "selected feat keeps ui binding",
                        "then": "ui_ref remains attached to the selected_feat snapshot",
                    },
                    {
                        "scenario": "selected feat keeps test mapping",
                        "then": "testset_ref and provisional follow-up data remain available for tech-to-impl",
                    },
                ],
                "source_refs": ["FEAT-SRC-009-101", "EPIC-SRC-009-001", "SRC-009"],
                "ui_ref": "UI-SRC-009-101",
                "testset_ref": "TESTSET-SRC-009-101",
                "provisional_refs": [
                    {
                        "ref": "UI-SRC-009-101",
                        "impact_scope": "ui copy and acceptance wording",
                        "follow_up_action": "freeze_ui_before_impl",
                    }
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-tech-metadata")
            input_dir = self.make_feat_package(repo_root, "feat-tech-metadata", bundle)

            artifacts_dir = self.run_tech_flow(repo_root, input_dir, feature["feat_ref"], "tech-metadata")
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))

            self.assertEqual(design["selected_feat"]["ui_ref"], "UI-SRC-009-101")
            self.assertEqual(design["selected_feat"]["testset_ref"], "TESTSET-SRC-009-101")
            self.assertEqual(design["selected_feat"]["provisional_refs"][0]["ref"], "UI-SRC-009-101")
            self.assertEqual(design["selected_feat"]["provisional_refs"][0]["follow_up_action"], "freeze_ui_before_impl")

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_selected_feat_discovers_historical_testset_as_provisional_execution_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-101",
                "title": "历史 TESTSET 受控接入能力",
                "goal": "让 TECH 包在缺少当前 QA 包时，仍能显式挂接唯一可引用的历史 TESTSET，并标记为 provisional。",
                "scope": [
                    "输出技术设计包。",
                    "自动发现同 feat 的 TESTSET 物料。",
                ],
                "constraints": [
                    "不得静默丢失 tester 需要的测试对象引用。",
                    "不得把 historical_only TESTSET 伪装成完全冻结真相。",
                ],
                "dependencies": ["depends on frozen FEAT metadata"],
                "acceptance_checks": [
                    {
                        "scenario": "historical testset discovered",
                        "then": "selected_feat keeps the discovered testset_ref",
                    },
                    {
                        "scenario": "historical testset marked provisional",
                        "then": "provisional follow-up survives into TECH package",
                    },
                    {
                        "scenario": "traceability preserved",
                        "then": "discovered testset becomes visible in source refs",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-101", "EPIC-SRC-001-001", "SRC-001"],
            }
            testset_dir = repo_root / "ssot" / "testset"
            testset_dir.mkdir(parents=True, exist_ok=True)
            (testset_dir / "TESTSET-SRC-001-101__historical.yaml").write_text(
                yaml.safe_dump(
                    {
                        "id": "TESTSET-SRC-001-101",
                        "parent_id": "FEAT-SRC-001-101",
                        "status": "active",
                        "lifecycle_state": "historical_only",
                        "higher_order_status": "superseded",
                        "historical_note": "older QA object retained for lineage only",
                        "traceability": {"feature_ids": ["FEAT-SRC-001-101"]},
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            bundle = self.make_bundle_json(feature, run_id="feat-tech-historical-testset")
            input_dir = self.make_feat_package(repo_root, "feat-tech-historical-testset", bundle)

            artifacts_dir = self.run_tech_flow(repo_root, input_dir, feature["feat_ref"], "tech-historical-testset")
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))

            self.assertEqual(design["selected_feat"]["testset_ref"], "TESTSET-SRC-001-101")
            self.assertEqual(design["selected_feat"]["provisional_refs"][0]["ref"], "TESTSET-SRC-001-101")
            self.assertIn("refresh_or_replace_testset_before_final_execution", design["selected_feat"]["provisional_refs"][0]["follow_up_action"])
            self.assertIn("TESTSET-SRC-001-101", design["source_refs"])

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
