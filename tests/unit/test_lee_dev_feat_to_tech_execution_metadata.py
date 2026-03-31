import json
import tempfile
from pathlib import Path

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
