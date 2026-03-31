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
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            execution = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            document_test = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))
            gate_ready_package = json.loads((artifacts_dir / "input" / "gate-ready-package.json").read_text(encoding="utf-8"))
            spec_path = artifacts_dir / "[UI-FEAT-UI-001-profile-entry]__ui_spec.md"

            self.assertTrue(spec_path.exists())
            self.assertEqual(bundle_json["workflow_key"], "dev.feat-to-ui")
            self.assertEqual(bundle_json["ui_spec_count"], 1)
            self.assertEqual(bundle_json["completeness_result"], "conditional_pass")
            self.assertEqual(completeness["decision"], "conditional_pass")
            self.assertEqual(document_test["test_outcome"], "no_blocking_defect_found")
            self.assertEqual(manifest["document_test_report_ref"], "artifacts/feat-to-ui/ui-conditional--feat-ui-001/document-test-report.json")
            self.assertEqual(execution["structural_results"]["document_test_outcome"], document_test["test_outcome"])
            self.assertEqual(supervision["document_test_outcome"], document_test["test_outcome"])
            self.assertEqual(manifest["gate_ready_package_ref"], "artifacts/feat-to-ui/ui-conditional--feat-ui-001/input/gate-ready-package.json")
            self.assertTrue(manifest["authoritative_handoff_ref"].startswith("artifacts/active/gates/handoffs/"))
            self.assertTrue(manifest["gate_pending_ref"].startswith("artifacts/active/gates/pending/"))
            self.assertEqual(gate_ready_package["payload"]["candidate_ref"], "feat-to-ui.ui-conditional--feat-ui-001.ui-spec-bundle")
            self.assertEqual(gate_ready_package["payload"]["target_formal_kind"], "ui")
            self.assertEqual(gate_ready_package["payload"]["formal_artifact_ref"], "formal.ui.ui-conditional--feat-ui-001")
            registry_record = json.loads((repo_root / "artifacts" / "registry" / "feat-to-ui-ui-conditional--feat-ui-001-ui-spec-bundle.json").read_text(encoding="utf-8"))
            self.assertEqual(registry_record["artifact_ref"], "feat-to-ui.ui-conditional--feat-ui-001.ui-spec-bundle")
            self.assertEqual(registry_record["managed_artifact_ref"], "artifacts/feat-to-ui/ui-conditional--feat-ui-001/ui-spec-bundle.md")
            self.assertTrue(bundle_json["open_questions"])
            self.assertTrue((artifacts_dir / "ui-flow-map.md").exists())
            self.assertIn("## 8. ASCII Wireframe", spec_path.read_text(encoding="utf-8"))

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)
            review = self.run_cmd("supervisor-review", "--artifacts-dir", str(artifacts_dir), "--repo-root", str(repo_root), "--run-id", "ui-conditional")
            self.assertEqual(review.returncode, 0, review.stderr)
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(supervision["document_test_outcome"], "no_blocking_defect_found")
            self.assertEqual(supervision["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))

            document_test["test_outcome"] = "blocking_defect_found"
            (artifacts_dir / "document-test-report.json").write_text(json.dumps(document_test, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(readiness.returncode, 0)
            self.assertIn("document_test_non_blocking", readiness.stdout)

            malformed = dict(document_test)
            malformed.pop("sections")
            (artifacts_dir / "document-test-report.json").write_text(json.dumps(malformed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("sections", validate.stdout)

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
            artifacts_dir = Path(payload["artifacts_dir"])
            document_test = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))
            self.assertEqual(document_test["test_outcome"], "blocking_defect_found")
            self.assertFalse((artifacts_dir / "handoff-proposal.json").exists())
            self.assertFalse((artifacts_dir / "input" / "gate-ready-package.json").exists())

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
                        "page_type": "multi-step form",
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
            self.assertTrue((artifacts_dir / "document-test-report.json").exists())
            self.assertTrue((artifacts_dir / "handoff-proposal.json").exists())
            self.assertTrue((artifacts_dir / "input" / "gate-ready-package.json").exists())

    def test_revision_request_rerun_persists_revision_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-UI-REVISION",
                "title": "训练目标设置",
                "goal": "让用户完成训练目标设置并进入下一步。",
                "scope": ["目标选择", "失败反馈", "下一步跳转"],
                "constraints": ["必须保留失败重试", "必须显式记录 revise 上下文"],
                "acceptance_checks": [{"scenario": "用户完成目标设置", "then": "进入下一步"}],
                "source_refs": ["FEAT-UI-REVISION", "EPIC-SRC-009-001", "SRC-009"],
                "ui_units": [
                    {
                        "slug": "goal-selection",
                        "page_name": "目标设置",
                        "page_type": "single-page form",
                        "entry_condition": "用户进入目标设置页。",
                        "exit_condition": "用户提交目标后进入下一步。",
                        "branch_paths": [
                            {"title": "Branch A", "steps": ["未选择目标", "点击下一步", "显示校验提示", "重新选择"]},
                            {"title": "Branch B", "steps": ["提交失败", "展示错误", "允许重试", "重新提交"]},
                        ],
                        "input_fields": [{"field": "goal_id", "type": "enum", "required": True}],
                        "required_fields": ["goal_id"],
                        "user_actions": ["选择目标", "点击下一步"],
                        "system_actions": ["加载页面", "保存目标"],
                        "frontend_validation_rules": ["goal_id 必选"],
                        "data_dependencies": ["目标选项列表"],
                        "api_touchpoints": ["GET /goal/options", "POST /profile/goal"],
                        "validation_feedback": "未选择目标时显示校验提示。",
                        "error_feedback": "失败时展示明确错误。",
                        "retry_behavior": "允许修正后再次提交。",
                    }
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-ui-revision-input")
            input_dir = self.make_feat_package(repo_root, "feat-ui-revision-input", bundle)

            initial = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-UI-REVISION", "--repo-root", str(repo_root), "--run-id", "ui-revision")
            self.assertEqual(initial.returncode, 0, initial.stderr)
            artifacts_dir = Path(json.loads(initial.stdout)["artifacts_dir"])

            revision_request = {
                "workflow_key": "dev.feat-to-ui",
                "run_id": "ui-revision",
                "source_run_id": "feat-ui-revision-input",
                "decision_type": "revise",
                "decision_target": "ui_spec_bundle",
                "decision_reason": "补充 revise 上下文并要求页面保留恢复性提示。",
                "revision_round": 1,
                "source_gate_decision_ref": "artifacts/gate-human-orchestrator/revision-decision.json",
                "source_return_job_ref": "artifacts/jobs/waiting-human/ui-revision-return.json",
                "authoritative_input_ref": "artifacts/epic-to-feat/feat-ui-revision-input/feat-freeze-bundle.json",
            }
            revision_request_path = repo_root / "revision-request.json"
            revision_request_path.write_text(json.dumps(revision_request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            rerun = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-UI-REVISION",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "ui-revision",
                "--allow-update",
                "--revision-request",
                str(revision_request_path),
            )
            self.assertEqual(rerun.returncode, 0, rerun.stderr)

            bundle_json = json.loads((artifacts_dir / "ui-spec-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            execution = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            gate = json.loads((artifacts_dir / "ui-spec-freeze-gate.json").read_text(encoding="utf-8"))
            revision_materialized = json.loads((artifacts_dir / "revision-request.json").read_text(encoding="utf-8"))
            report = (artifacts_dir / "evidence-report.md").read_text(encoding="utf-8")

            self.assertEqual(revision_materialized["decision_reason"], revision_request["decision_reason"])
            self.assertEqual(bundle_json["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertEqual(manifest["revision_request_ref"], "revision-request.json")
            self.assertEqual(execution["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertEqual(supervision["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertEqual(gate["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertTrue(any("Applied revision context:" in item for item in execution["key_decisions"]))
            self.assertIn("revision_request_ref: revision-request.json", report)
            self.assertEqual(json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))["revision_request_ref"], "revision-request.json")
            self.assertTrue(json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))["gate_ready_package_ref"].endswith("/input/gate-ready-package.json"))

    def test_allow_update_rerun_clears_stale_gate_artifacts_when_package_becomes_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-UI-RERUN",
                "title": "训练目标确认",
                "goal": "让用户完成目标确认并进入下一步。",
                "scope": ["目标确认", "失败反馈"],
                "constraints": ["必须保留失败重试"],
                "acceptance_checks": [{"scenario": "用户完成确认", "then": "进入下一步"}],
                "source_refs": ["FEAT-UI-RERUN", "EPIC-SRC-009-001", "SRC-009"],
                "ui_units": [
                    {
                        "slug": "goal-confirm",
                        "page_name": "目标确认",
                        "page_type": "single-page form",
                        "entry_condition": "用户进入确认页。",
                        "exit_condition": "用户确认后进入下一步。",
                        "branch_paths": [
                            {"title": "Branch A", "steps": ["点击确认", "校验失败", "修正后重试", "重新提交"]},
                            {"title": "Branch B", "steps": ["提交失败", "展示错误", "允许重试", "重新提交"]},
                        ],
                        "input_fields": [{"field": "goal_id", "type": "enum", "required": True}],
                        "required_fields": ["goal_id"],
                        "user_actions": ["确认目标", "点击下一步"],
                        "system_actions": ["加载页面", "保存目标"],
                        "frontend_validation_rules": ["goal_id 必选"],
                        "data_dependencies": ["目标详情"],
                        "api_touchpoints": ["POST /profile/goal/confirm"],
                        "validation_feedback": "校验失败时高亮字段。",
                        "error_feedback": "失败时展示明确错误。",
                        "retry_behavior": "允许再次提交。",
                    }
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-ui-rerun-input")
            input_dir = self.make_feat_package(repo_root, "feat-ui-rerun-input", bundle)

            first_run = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-UI-RERUN", "--repo-root", str(repo_root), "--run-id", "ui-rerun")
            self.assertEqual(first_run.returncode, 0, first_run.stderr)
            artifacts_dir = Path(json.loads(first_run.stdout)["artifacts_dir"])
            self.assertTrue((artifacts_dir / "handoff-proposal.json").exists())
            self.assertTrue((artifacts_dir / "input" / "gate-ready-package.json").exists())

            bundle["features"][0]["ui_units"][0]["open_questions"] = ["提交后跳转到哪里还未确定。"]
            (input_dir / "feat-freeze-bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            rerun = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-UI-RERUN",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "ui-rerun",
                "--allow-update",
            )
            self.assertNotEqual(rerun.returncode, 0)
            self.assertFalse((artifacts_dir / "handoff-proposal.json").exists())
            self.assertFalse((artifacts_dir / "input" / "gate-ready-package.json").exists())
            self.assertFalse((artifacts_dir / "_cli" / "gate-submit-handoff.request.json").exists())
            self.assertFalse((artifacts_dir / "_cli" / "gate-submit-handoff.response.json").exists())
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("handoff_proposal_ref", manifest)
            self.assertNotIn("gate_ready_package_ref", manifest)
            self.assertNotIn("authoritative_handoff_ref", manifest)
            self.assertEqual(json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))["test_outcome"], "blocking_defect_found")

    def test_allow_update_rerun_replaces_stale_pending_queue_entry_before_resubmit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-UI-QUEUE-REPLAY",
                "title": "首页建议卡",
                "goal": "让用户在首页看到首轮建议卡并可重试。",
                "scope": ["首页建议卡"],
                "constraints": ["失败不阻塞首页"],
                "acceptance_checks": [{"scenario": "首页可见建议卡", "then": "用户可查看建议"}],
                "source_refs": ["FEAT-UI-QUEUE-REPLAY", "EPIC-SRC-009-001", "SRC-009"],
                "ui_units": [
                    {
                        "slug": "advice-card",
                        "page_name": "首页建议卡",
                        "page_type": "panel",
                        "entry_condition": "用户进入首页。",
                        "exit_condition": "用户查看建议或点击重试。",
                        "branch_paths": [
                            {"title": "Branch A", "steps": ["进入首页", "展示建议卡", "查看建议"]},
                            {"title": "Branch B", "steps": ["加载失败", "展示重试", "点击重试", "重新拉取"]},
                        ],
                        "input_fields": [{"field": "advice_ready", "type": "boolean", "required": False}],
                        "user_actions": ["查看建议", "点击重试"],
                        "system_actions": ["加载建议卡", "重试生成建议"],
                        "frontend_validation_rules": ["建议卡状态必须可见"],
                        "data_dependencies": ["homepage advice state"],
                        "api_touchpoints": ["GET /homepage/advice"],
                        "validation_feedback": "加载态和失败态都必须明确。",
                        "error_feedback": "失败时展示可重试提示。",
                        "retry_behavior": "允许再次请求建议数据。",
                    }
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-ui-queue-replay-input")
            input_dir = self.make_feat_package(repo_root, "feat-ui-queue-replay-input", bundle)

            first = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-UI-QUEUE-REPLAY",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "ui-queue-replay",
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            artifacts_dir = Path(json.loads(first.stdout)["artifacts_dir"])
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            index_path = repo_root / "artifacts" / "active" / "gates" / "pending" / "index.json"
            index_payload = json.loads(index_path.read_text(encoding="utf-8"))
            handoff_key = Path(str(manifest["authoritative_handoff_ref"])).stem
            index_payload["handoffs"][handoff_key]["payload_digest"] = "stale-digest"
            index_path.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            rerun = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-UI-QUEUE-REPLAY",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "ui-queue-replay",
                "--allow-update",
            )
            self.assertEqual(rerun.returncode, 0, rerun.stderr)

            rerun_manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            rerun_index = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertIn(handoff_key, rerun_index["handoffs"])
            self.assertEqual(rerun_index["handoffs"][handoff_key]["handoff_ref"], rerun_manifest["authoritative_handoff_ref"])
            self.assertEqual(rerun_index["handoffs"][handoff_key]["gate_pending_ref"], rerun_manifest["gate_pending_ref"])

    def test_validate_output_rejects_stale_ui_spec_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-UI-STALE",
                "title": "最小建档页",
                "goal": "让用户完成最小建档并进入首页。",
                "scope": ["最小建档", "首页放行"],
                "constraints": ["必须保留字段校验", "失败后可重试"],
                "acceptance_checks": [{"scenario": "最小建档完成", "then": "进入首页"}],
                "source_refs": ["FEAT-UI-STALE", "EPIC-SRC-009-001", "SRC-009"],
                "ui_units": [
                    {
                        "slug": "minimal-profile",
                        "page_name": "最小建档",
                        "page_type": "single-page form",
                        "entry_condition": "用户首次登录后进入最小建档页。",
                        "exit_condition": "提交合法字段后进入首页。",
                        "branch_paths": [
                            {"title": "Branch A", "steps": ["填写字段", "提交", "校验失败", "修正后重试"]},
                            {"title": "Branch B", "steps": ["提交保存", "接口失败", "展示错误", "允许再次提交"]},
                        ],
                        "input_fields": [{"field": "gender", "type": "enum", "required": True}],
                        "required_fields": ["gender"],
                        "user_actions": ["填写字段", "点击继续"],
                        "system_actions": ["执行校验", "保存数据", "放行首页"],
                        "frontend_validation_rules": ["gender 必填"],
                        "data_dependencies": ["profile 草稿"],
                        "api_touchpoints": ["POST /onboarding/minimal-profile"],
                        "validation_feedback": "字段级错误必须可见。",
                        "error_feedback": "提交失败时保留用户输入。",
                        "retry_behavior": "允许再次提交。",
                    }
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-ui-stale")
            input_dir = self.make_feat_package(repo_root, "feat-ui-stale", bundle)

            artifacts_dir = self.run_ui_flow(repo_root, input_dir, "FEAT-UI-STALE", "ui-stale")
            spec_path = artifacts_dir / "[UI-FEAT-UI-STALE-minimal-profile]__ui_spec.md"
            spec_path.write_text(spec_path.read_text(encoding="utf-8") + "\nTampered.\n", encoding="utf-8")

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("review_gate", validate.stdout)

    def test_supervisor_review_rejects_stale_ui_spec_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-UI-STALE-REVIEW",
                "title": "首页任务卡",
                "goal": "让用户在首页渐进补全扩展画像。",
                "scope": ["首页任务卡", "补全入口"],
                "constraints": ["失败不阻塞首页", "必须保留重试入口"],
                "acceptance_checks": [{"scenario": "补全入口可见", "then": "用户可继续补全"}],
                "source_refs": ["FEAT-UI-STALE-REVIEW", "EPIC-SRC-009-001", "SRC-009"],
                "ui_units": [
                    {
                        "slug": "task-card",
                        "page_name": "首页任务卡",
                        "page_type": "single-page form",
                        "entry_condition": "用户进入首页。",
                        "exit_condition": "用户进入补全页或暂时跳过。",
                        "branch_paths": [
                            {"title": "Branch A", "steps": ["查看任务卡", "点击去补全", "进入补全页", "返回首页"]},
                            {"title": "Branch B", "steps": ["稍后处理", "保留任务卡", "继续浏览首页", "稍后重试"]},
                        ],
                        "input_fields": [{"field": "completion_percent", "type": "integer", "required": False}],
                        "user_actions": ["查看任务卡", "点击入口"],
                        "system_actions": ["渲染首页卡片", "保持首页可用"],
                        "frontend_validation_rules": ["入口状态必须可见"],
                        "data_dependencies": ["profile completion state"],
                        "api_touchpoints": ["GET /profile/completion"],
                        "validation_feedback": "补全状态必须可读。",
                        "error_feedback": "加载失败时展示重试提示。",
                        "retry_behavior": "允许重新拉取任务卡。",
                    }
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-ui-stale-review")
            input_dir = self.make_feat_package(repo_root, "feat-ui-stale-review", bundle)

            artifacts_dir = self.run_ui_flow(repo_root, input_dir, "FEAT-UI-STALE-REVIEW", "ui-stale-review")
            spec_path = artifacts_dir / "[UI-FEAT-UI-STALE-REVIEW-task-card]__ui_spec.md"
            spec_path.write_text(spec_path.read_text(encoding="utf-8") + "\nTampered.\n", encoding="utf-8")

            review = self.run_cmd("supervisor-review", "--artifacts-dir", str(artifacts_dir), "--repo-root", str(repo_root), "--run-id", "ui-stale-review")
            self.assertNotEqual(review.returncode, 0)
            review_report = json.loads((artifacts_dir / "ui-spec-review-report.json").read_text(encoding="utf-8"))
            freeze_gate = json.loads((artifacts_dir / "ui-spec-freeze-gate.json").read_text(encoding="utf-8"))
            document_test = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))
            self.assertEqual(review_report["decision"], "revise")
            self.assertFalse(freeze_gate["freeze_ready"])
            self.assertEqual(document_test["test_outcome"], "blocking_defect_found")
