import json
import tempfile
from pathlib import Path

from tests.unit.support_feat_to_ui import FeatToUiWorkflowHarness


class FeatToUiWorkflowTests(FeatToUiWorkflowHarness):
    def test_run_emits_conditional_pass_only_for_noncritical_open_questions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-UI-001",
                "title": "新用户建档",
                "goal": "让新用户完成首次基本资料录入并进入后续配置步骤。",
                "scope": ["基本信息录入", "引导进入下一步"],
                "constraints": ["必须保留失败重试", "必须给出字段级校验反馈"],
                "acceptance_checks": [{"scenario": "用户完成建档", "then": "用户可进入下一步"}],
                "source_refs": ["FEAT-UI-001", "EPIC-SRC-009-001", "SRC-009"],
                "ui_units": [
                    {
                        "slug": "profile-entry",
                        "page_name": "基本信息录入",
                        "page_type": "multi-step form",
                        "entry_condition": "用户点击开始建档。",
                        "exit_condition": "用户提交合法信息后进入下一步。",
                        "branch_paths": [
                            {"title": "Branch A", "steps": ["点击下一步", "校验失败", "修正字段", "重新提交"]},
                            {"title": "Branch B", "steps": ["提交保存", "接口失败", "展示错误", "重试"]},
                        ],
                        "input_fields": [
                            {"field": "name", "type": "string", "required": True},
                            {"field": "age", "type": "integer", "required": True},
                        ],
                        "required_fields": ["name", "age"],
                        "user_actions": ["填写字段", "点击下一步"],
                        "system_actions": ["初始化页面", "执行校验", "提交保存"],
                        "frontend_validation_rules": ["name 必填", "age 必须为正整数"],
                        "data_dependencies": ["当前草稿"],
                        "api_touchpoints": ["GET /profile/draft", "POST /profile/basic-info"],
                        "error_feedback": "提交失败时展示明确错误并保留当前输入。",
                        "retry_behavior": "用户可修正后再次提交。",
                        "validation_feedback": "字段级错误提示优先。",
                        "open_questions": ["欢迎文案措辞待定。"],
                    }
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-ui-conditional")
            input_dir = self.make_feat_package(repo_root, "feat-ui-conditional", bundle)

            artifacts_dir = self.run_ui_flow(repo_root, input_dir, "FEAT-UI-001", "ui-conditional")
            bundle_json = json.loads((artifacts_dir / "ui-spec-bundle.json").read_text(encoding="utf-8"))
            completeness = json.loads((artifacts_dir / "ui-spec-completeness-report.json").read_text(encoding="utf-8"))
            spec_path = artifacts_dir / "[UI-FEAT-UI-001-profile-entry]__ui_spec.md"

            self.assertTrue(spec_path.exists())
            self.assertEqual(bundle_json["workflow_key"], "dev.feat-to-ui")
            self.assertEqual(bundle_json["ui_spec_count"], 1)
            self.assertEqual(bundle_json["completeness_result"], "conditional_pass")
            self.assertEqual(completeness["decision"], "conditional_pass")
            self.assertTrue(bundle_json["open_questions"])
            self.assertTrue((artifacts_dir / "ui-flow-map.md").exists())
            self.assertIn("## 8. ASCII Wireframe", spec_path.read_text(encoding="utf-8"))

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

    def test_run_fails_when_open_questions_hide_key_path_or_touchpoint_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-UI-003",
                "title": "用户目标设置",
                "goal": "让用户配置训练目标。",
                "scope": ["目标设置"],
                "constraints": ["必须有明确失败反馈"],
                "acceptance_checks": [{"scenario": "用户设置目标", "then": "成功进入下一步"}],
                "source_refs": ["FEAT-UI-003", "EPIC-SRC-009-001", "SRC-009"],
                "ui_units": [
                    {
                        "slug": "goal-selection",
                        "page_name": "目标设置",
                        "entry_condition": "用户进入目标设置页。",
                        "exit_condition": "用户确认目标后进入下一步。",
                        "branch_paths": [
                            {"title": "Branch A", "steps": ["未选择目标", "点击下一步", "显示校验提示", "重新选择"]},
                            {"title": "Branch B", "steps": ["提交失败", "展示错误", "允许重试"]},
                        ],
                        "input_fields": [{"field": "goal_id", "type": "enum", "required": True}],
                        "required_fields": ["goal_id"],
                        "user_actions": ["选择目标", "点击下一步"],
                        "system_actions": ["加载页面", "保存目标"],
                        "frontend_validation_rules": ["goal_id 必选"],
                        "data_dependencies": ["目标选项列表"],
                        "api_touchpoints": ["POST /profile/goal"],
                        "error_feedback": "失败时展示明确错误。",
                        "retry_behavior": "允许再次提交。",
                        "validation_feedback": "未选择目标时显示校验提示。",
                        "open_questions": ["提交后跳转到哪里还未确定。"],
                    }
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-ui-fail")
            input_dir = self.make_feat_package(repo_root, "feat-ui-fail", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-UI-003",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "ui-fail",
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["completeness_result"], "fail")

    def test_run_supports_multiple_ui_units_and_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-UI-002",
                "title": "新用户建档与目标设置",
                "goal": "让新用户完成建档并配置训练目标。",
                "scope": ["基础信息录入", "目标设置", "确认进入计划"],
                "constraints": ["必须支持多步骤返回", "必须支持草稿恢复"],
                "acceptance_checks": [{"scenario": "用户完成多步骤建档", "then": "成功进入计划页"}],
                "source_refs": ["FEAT-UI-002", "EPIC-SRC-009-001", "SRC-009"],
                "ui_units": [
                    {
                        "slug": "profile-entry",
                        "page_name": "基本信息录入",
                        "page_type": "multi-step form",
                        "entry_condition": "用户点击开始建档。",
                        "exit_condition": "用户提交合法信息后进入下一步。",
                        "branch_paths": [
                            {"title": "Branch A", "steps": ["点击下一步", "校验失败", "修正字段", "重新提交"]},
                            {"title": "Branch B", "steps": ["点击下一步", "保存失败", "显示错误", "重试"]},
                        ],
                        "input_fields": [
                            {"field": "name", "type": "string", "required": True},
                            {"field": "age", "type": "integer", "required": True},
                        ],
                        "user_actions": ["填写字段", "点击下一步"],
                        "system_actions": ["初始化草稿", "执行校验", "提交保存"],
                        "frontend_validation_rules": ["name 必填", "age 必须为正整数"],
                        "data_dependencies": ["当前草稿"],
                        "api_touchpoints": ["GET /profile/draft", "POST /profile/basic-info"],
                    },
                    {
                        "slug": "goal-selection",
                        "page_name": "目标设置",
                        "page_type": "selection step",
                        "entry_condition": "用户完成基本信息录入。",
                        "exit_condition": "用户确认目标后进入确认页。",
                        "branch_paths": [
                            {"title": "Branch A", "steps": ["未选择目标", "点击下一步", "显示校验提示", "重新选择"]},
                            {"title": "Branch B", "steps": ["提交失败", "保留当前选择", "允许重试"]},
                        ],
                        "input_fields": [{"field": "goal_id", "type": "enum", "required": True}],
                        "user_actions": ["选择目标", "点击下一步"],
                        "system_actions": ["拉取目标选项", "保存选择"],
                        "frontend_validation_rules": ["goal_id 必选"],
                        "data_dependencies": ["目标选项列表"],
                        "api_touchpoints": ["GET /goal/options", "POST /profile/goal"],
                    },
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-ui-pass")
            input_dir = self.make_feat_package(repo_root, "feat-ui-pass", bundle)

            artifacts_dir = self.run_ui_flow(repo_root, input_dir, "FEAT-UI-002", "ui-pass")
            bundle_json = json.loads((artifacts_dir / "ui-spec-bundle.json").read_text(encoding="utf-8"))
            gate = json.loads((artifacts_dir / "ui-spec-freeze-gate.json").read_text(encoding="utf-8"))

            self.assertEqual(bundle_json["ui_spec_count"], 2)
            self.assertEqual(bundle_json["completeness_result"], "pass")
            self.assertEqual(gate["decision"], "pass")
            self.assertTrue((artifacts_dir / "[UI-FEAT-UI-002-profile-entry]__ui_spec.md").exists())
            self.assertTrue((artifacts_dir / "[UI-FEAT-UI-002-goal-selection]__ui_spec.md").exists())
            self.assertTrue((artifacts_dir / "ui-flow-map.md").exists())
