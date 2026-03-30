import json
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.unit.support_feat_to_testset import FeatToTestSetWorkflowHarness


class FeatToTestSetWorkflowTests(FeatToTestSetWorkflowHarness):
    def test_run_emits_candidate_package_ready_for_external_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-TESTSET",
                "title": "主链候选提交与交接流",
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
            artifacts_dir = self.run_testset_flow(repo_root, input_dir, "FEAT-SRC-001-TESTSET", "feat-to-testset-output")

            bundle_json = json.loads((artifacts_dir / "test-set-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            gate_ready_package = json.loads((artifacts_dir / "input" / "gate-ready-package.json").read_text(encoding="utf-8"))
            freeze_gate = json.loads((artifacts_dir / "test-set-freeze-gate.json").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            test_set = yaml.safe_load((artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))
            bundle_markdown = (artifacts_dir / "test-set-bundle.md").read_text(encoding="utf-8")

            self.assertEqual(bundle_json["artifact_type"], "test_set_candidate_package")
            self.assertEqual(bundle_json["status"], "approval_pending")
            self.assertEqual(manifest["status"], "approval_pending")
            self.assertEqual(test_set["status"], "approved")
            self.assertEqual(freeze_gate["status"], "pending")
            self.assertTrue(freeze_gate["ready_for_external_approval"])
            self.assertNotEqual(test_set["derived_slug"], "unspecified")
            self.assertTrue(all("review" not in unit["trigger_action"].lower() for unit in test_set["test_units"]))
            self.assertTrue(all("inspect" not in unit["trigger_action"].lower() for unit in test_set["test_units"]))
            self.assertEqual(handoff["target_skill"], "skill.qa.test_exec_cli")
            self.assertTrue(
                any("authoritative handoff submission" in item for item in handoff["required_environment_inputs"]["data"])
            )
            self.assertTrue(
                any("pending_state" in item for item in handoff["required_environment_inputs"]["data"])
            )
            self.assertTrue(
                any("handoff service identity" in item or "账号材料" in item for item in handoff["required_environment_inputs"]["access"])
            )
            self.assertTrue(
                any(
                    "cli" in item.lower() or "命令" in item or "integration context" in item.lower()
                    for item in handoff["required_environment_inputs"]["ui_or_integration_context"]
                )
            )
            self.assertTrue((artifacts_dir / "analysis-review-subject.json").exists())
            self.assertTrue((artifacts_dir / "strategy-review-subject.json").exists())
            self.assertTrue((artifacts_dir / "test-set-approval-subject.json").exists())
            self.assertGreaterEqual(len(test_set["test_units"]), 10)
            self.assertTrue(all(unit.get("input_preconditions") for unit in test_set["test_units"]))
            self.assertTrue(all(unit.get("trigger_action") for unit in test_set["test_units"]))
            self.assertTrue(all(unit.get("pass_conditions") for unit in test_set["test_units"]))
            self.assertTrue(all(row.get("acceptance_scenario") for row in test_set["acceptance_traceability"]))
            self.assertTrue(all(row.get("coverage_status") == "covered" for row in test_set["acceptance_traceability"]))
            self.assertTrue(any("pending_state" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("gate_pending_ref" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("assigned_gate_queue" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("payload_digest" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("canonical_payload_path" in item for unit in test_set["test_units"] for item in unit["pass_conditions"]))
            self.assertTrue(any("response envelope" in item for unit in test_set["test_units"] for item in unit["required_evidence"]))
            self.assertFalse(any("error code -> retryable -> idempotent_replay mapping" in item for unit in test_set["test_units"] for item in unit["observation_points"]))
            self.assertIn("acceptance_traceability", bundle_markdown)
            self.assertIn("input_preconditions:", bundle_markdown)
            self.assertIn("required_evidence:", bundle_markdown)
            self.assertEqual(manifest["gate_ready_package_ref"], "artifacts/feat-to-testset/feat-to-testset-output/input/gate-ready-package.json")
            self.assertTrue(manifest["authoritative_handoff_ref"].startswith("artifacts/active/gates/handoffs/"))
            self.assertTrue(manifest["gate_pending_ref"].startswith("artifacts/active/gates/pending/"))
            self.assertEqual(gate_ready_package["payload"]["candidate_ref"], "feat-to-testset.feat-to-testset-output.test-set-bundle")
            self.assertEqual(gate_ready_package["payload"]["machine_ssot_ref"], "artifacts/feat-to-testset/feat-to-testset-output/test-set-bundle.json")
            self.assertTrue((repo_root / manifest["authoritative_handoff_ref"]).exists())
            self.assertTrue((repo_root / manifest["gate_pending_ref"]).exists())

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

    def test_revision_request_rerun_persists_revision_context_and_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-REVISION-TESTSET",
                "title": "回流修订感知 TESTSET 流",
                "goal": "验证 allow-update 复跑时会吸收 revision request 并保留 lineage。",
                "scope": [
                    "将 revision request 物化到 artifacts 目录。",
                    "把 revision summary 吸收到 TESTSET preconditions。",
                    "让 manifest 与 evidence 记录 revision lineage。",
                ],
                "constraints": [
                    "不得重写整份 TESTSET 设计。",
                    "只能做最小约束补丁。",
                    "必须支持同 run_id allow-update 复跑。",
                ],
                "dependencies": [
                    "上游 feat_freeze_package 已可 freeze。",
                ],
                "acceptance_checks": [
                    {"id": "AC-01", "scenario": "revision request is materialized", "given": "rerun input", "when": "invoke run with revision request", "then": "revision-request.json 会写入 artifacts"},
                    {"id": "AC-02", "scenario": "constraints absorb revision", "given": "revision request", "when": "build testset", "then": "preconditions 会保留 revision summary"},
                    {"id": "AC-03", "scenario": "lineage is visible", "given": "manifest and evidence", "when": "inspect outputs", "then": "revision_request_ref 可追溯"},
                ],
                "source_refs": ["FEAT-SRC-001-REVISION-TESTSET", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-testset-revision-input")
            input_dir = self.make_feat_package(repo_root, "feat-testset-revision-input", bundle)

            initial = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-REVISION-TESTSET", "--repo-root", str(repo_root), "--run-id", "testset-revision")
            self.assertEqual(initial.returncode, 0, initial.stderr)
            artifacts_dir = Path(json.loads(initial.stdout)["artifacts_dir"])

            revision_request = {
                "workflow_key": "qa.feat-to-testset",
                "run_id": "testset-revision",
                "source_run_id": "feat-testset-revision-input",
                "decision_type": "revise",
                "decision_target": "preconditions",
                "decision_reason": "Add the smallest recovery guardrail before external approval.",
                "revision_round": 2,
                "source_gate_decision_ref": "artifacts/gate-human-orchestrator/revision-decision.json",
                "source_return_job_ref": "artifacts/jobs/waiting-human/testset-revision-return.json",
                "authoritative_input_ref": "artifacts/epic-to-feat/feat-testset-revision-input/feat-freeze-package.json",
            }
            revision_request_path = repo_root / "revision-request.json"
            revision_request_path.write_text(json.dumps(revision_request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            rerun = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-SRC-001-REVISION-TESTSET",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "testset-revision",
                "--allow-update",
                "--revision-request",
                str(revision_request_path),
            )
            self.assertEqual(rerun.returncode, 0, rerun.stderr)

            bundle_json = json.loads((artifacts_dir / "test-set-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            execution = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            test_set = yaml.safe_load((artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))
            revision_materialized = json.loads((artifacts_dir / "revision-request.json").read_text(encoding="utf-8"))

            self.assertEqual(revision_materialized["decision_reason"], revision_request["decision_reason"])
            self.assertEqual(bundle_json["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertEqual(manifest["revision_request_ref"], "revision-request.json")
            self.assertEqual(execution["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertEqual(supervision["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertTrue(
                any("Revision constraint:" in item and revision_request["decision_reason"] in item for item in test_set["preconditions"])
            )
            self.assertTrue(any("Applied revision context:" in item for item in execution["key_decisions"]))
            self.assertTrue((artifacts_dir / "evidence-report.md").read_text(encoding="utf-8").find("revision_request_ref: revision-request.json") >= 0)

    def test_explicit_web_feat_routes_to_web_test_exec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-WEB",
                "title": "登录页浏览器可用性验证流",
                "goal": "将前端登录页的浏览器路径与页面断言派生成可执行 TESTSET。",
                "scope": [
                    "验证 browser 中的 page load、form fill 与 button click 流程。",
                    "验证 locator、selector 与 expected url 断言。",
                    "输出交给 playwright sibling 的 test execution handoff。",
                ],
                "constraints": [
                    "必须保留 page、locator 与 selector 级别的执行上下文。",
                    "不得把浏览器验证降级成纯 CLI 命令 smoke。",
                ],
                "dependencies": [
                    "frontend codebase 可提供 route 与 data-testid 线索。",
                    "browser automation environment 可访问 base_url。",
                ],
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "page and locator context preserved",
                        "given": "login page",
                        "when": "generate testset",
                        "then": "handoff 保留 browser page / locator / selector 上下文",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "browser route stays executable",
                        "given": "base_url and route",
                        "when": "derive handoff",
                        "then": "required_environment_inputs 能表达 browser automation 运行上下文",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "playwright sibling selected",
                        "given": "frontend page flow",
                        "when": "choose downstream target",
                        "then": "target skill 指向 web e2e sibling",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-WEB", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-to-testset-web")
            input_dir = self.make_feat_package(repo_root, "feat-to-testset-web", bundle)
            artifacts_dir = self.run_testset_flow(repo_root, input_dir, "FEAT-SRC-001-WEB", "feat-to-testset-web-output")

            handoff = json.loads((artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            bundle_json = json.loads((artifacts_dir / "test-set-bundle.json").read_text(encoding="utf-8"))

            self.assertEqual(handoff["target_skill"], "skill.qa.test_exec_web_e2e")
            self.assertEqual(bundle_json["downstream_target"], "skill.qa.test_exec_web_e2e")
            self.assertTrue(
                any(
                    any(token in item.lower() for token in ["browser", "page", "locator", "selector", "ui"])
                    for item in handoff["required_environment_inputs"]["ui_or_integration_context"]
                )
            )
            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

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

    def test_review_projection_feat_generates_projection_focused_testset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            semantic_lock = {
                "domain_type": "review_projection_rule",
                "one_sentence_truth": "仅在 gate 审核阶段，从机器优先 SSOT 派生一份人类友好 Projection，帮助人类决策；冻结与继承仍回到 SSOT。",
                "primary_object": "human_review_projection",
                "lifecycle_stage": "gate_review_only",
                "allowed_capabilities": [
                    "projection_generation",
                    "authoritative_snapshot_rendering",
                    "review_focus_extraction",
                    "risk_ambiguity_extraction",
                    "review_feedback_writeback",
                ],
                "forbidden_capabilities": [
                    "mainline_runtime_governance",
                    "handoff_orchestration",
                    "gate_decision_engine",
                    "formal_publication",
                    "governed_io_platform",
                    "global_skill_onboarding",
                ],
                "inheritance_rule": "Projection is derived-only, non-authoritative, non-inheritable.",
            }
            feature = {
                "feat_ref": "FEAT-SRC-ADR015-002",
                "title": "Review Focus 与风险提示流",
                "goal": "从 SSOT 和 Projection 中提取 reviewer 应关注的风险与歧义。",
                "axis_id": "review-focus-risk",
                "scope": [
                    "提取 reviewer 应优先检查的问题。",
                    "识别术语歧义、边界遗漏、异常流缺失。",
                    "把 risk / ambiguity 结果写入 Projection 的 reviewer block。",
                ],
                "constraints": [
                    "risk signal 必须可回链到 SSOT。",
                    "Projection 只服务 reviewer 决策，不引入新的 authority。",
                    "不得退化成 formal publication / gate decision engine 语义。",
                ],
                "dependencies": ["Projection 已渲染。", "SSOT source refs 可解析。"],
                "acceptance_checks": [
                    {"id": "AC-01", "scenario": "review focus is extracted", "given": "projection context", "when": "run focus extraction", "then": "reviewer 应优先关注的判断点被稳定提取"},
                    {"id": "AC-02", "scenario": "risk signals remain traceable", "given": "risk / ambiguity signal", "when": "attach to projection", "then": "每个 signal 都能回链到 SSOT"},
                    {"id": "AC-03", "scenario": "analysis does not drift into runtime governance", "given": "derived review block", "when": "inspect final TESTSET", "then": "不得出现 formal publication、gate decision engine、governed IO 平台断言"},
                ],
                "semantic_lock": semantic_lock,
                "source_refs": ["FEAT-SRC-ADR015-002", "EPIC-SRC-ADR015", "SRC-ADR015", "ADR-015"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-to-testset-review-projection")
            bundle["semantic_lock"] = semantic_lock
            input_dir = self.make_feat_package(repo_root, "feat-to-testset-review-projection", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-SRC-ADR015-002",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-to-testset-review-projection-out",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            test_set = yaml.safe_load((artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            drift = json.loads((artifacts_dir / "semantic-drift-check.json").read_text(encoding="utf-8"))

            self.assertEqual(test_set["semantic_lock"]["domain_type"], "review_projection_rule")
            self.assertTrue(drift["semantic_lock_preserved"])
            self.assertTrue(any("Projection" in item or "projection" in item for item in test_set["pass_criteria"]))
            self.assertTrue(any("SSOT" in item for item in handoff["required_environment_inputs"]["data"]))
            self.assertFalse(any("formal publication" in item.lower() for item in test_set["pass_criteria"]))
            self.assertFalse(any("decision object" in item.lower() for item in test_set["evidence_required"]))

    def test_collaboration_profile_hardens_pending_visibility_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-COLLAB",
                "title": "主链候选提交与交接流",
                "goal": "冻结 authoritative handoff、pending visibility 与 runtime re-entry routing 的协作边界。",
                "scope": [
                    "定义 candidate package、proposal、evidence 在什么触发场景下被提交。",
                    "定义提交后形成什么 authoritative handoff object。",
                    "定义提交完成后对上游和 gate 分别暴露什么业务结果。",
                ],
                "constraints": [
                    "Loop responsibility split must stay explicit.",
                    "Submission completion is visible without implying approval: The FEAT must make clear which authoritative handoff and pending-intake results become visible, while keeping approval and re-entry semantics outside this FEAT.",
                ],
                "dependencies": [
                    "candidate package 已就绪且准备进入主链 handoff。",
                    "下游 workflow 已接入 authoritative handoff submission 消费链。",
                ],
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "candidate submit-mainline 明确 loop 责任边界",
                        "given": "candidate package 已就绪",
                        "when": "执行 candidate submit-mainline",
                        "then": "execution、gate、human loop 各自拥有明确 transition",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "submission completion visibility stays pending-only",
                        "given": "candidate 提交完成",
                        "when": "读取 authoritative handoff object 与 pending visibility",
                        "then": "submission completion is visible without implying approval: The FEAT must make clear which authoritative handoff and pending-intake results become visible, while keeping approval and re-entry semantics outside this FEAT.",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "downstream inherits the same handoff model",
                        "given": "下游 workflow 消费 authoritative handoff submission",
                        "when": "校验 queue / handoff / gate 语义",
                        "then": "下游继承同一套协作规则而不重建并行 queue / handoff 模型",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-COLLAB", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-to-testset-collab")
            input_dir = self.make_feat_package(repo_root, "feat-to-testset-collab", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-SRC-001-COLLAB",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-to-testset-collab-out",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            test_set = yaml.safe_load((artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))

            self.assertTrue(any("pending_state" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("gate_pending_ref" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("assigned_gate_queue" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("retryable / idempotent_replay field semantics" in item for unit in test_set["test_units"] for item in unit["observation_points"]))
            self.assertTrue(any("payload mismatch" in unit["title"].lower() or "不同 payload" in unit["title"] for unit in test_set["test_units"]))
            self.assertTrue(any("payload_ref" in unit["title"] or "坏路径" in unit["title"] for unit in test_set["test_units"]))
            self.assertTrue(any("pending visibility" in unit["title"].lower() or "空队列" in unit["title"] for unit in test_set["test_units"]))
            self.assertTrue(any("reentry directive" in item.lower() or "reentry_directive" in item.lower() for unit in test_set["test_units"] for item in unit["required_evidence"] + unit["supporting_refs"]))
            self.assertGreaterEqual(len(test_set["test_units"]), 10)
            self.assertTrue(any("尚未冻结完整 error mapping table" in item for unit in test_set["test_units"] for item in unit["pass_conditions"]))
            self.assertEqual(test_set["recommended_coverage_scope_name"], ["mainline collaboration feature"])
            self.assertEqual(
                test_set["feature_owned_code_paths"],
                [
                    "cli/lib/mainline_runtime.py",
                    "cli/lib/reentry.py",
                    "cli/lib/gate_collaboration_actions.py",
                ],
            )
            collaboration_trace = {
                row["acceptance_ref"]: row for row in test_set["acceptance_traceability"]
            }
            self.assertIn("decision-driven revise/retry runtime routing", collaboration_trace["AC-02"]["then"])
            self.assertNotIn("approval and re-entry semantics outside this FEAT", collaboration_trace["AC-02"]["then"])

    def test_profile_specific_units_and_handoff_are_hardened(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            io_feature = {
                "feat_ref": "FEAT-SRC-001-IO",
                "title": "主链受治理 IO 落盘与读取流",
                "goal": "冻结主链受治理 IO 的正式写入、读取与失败边界。",
                "scope": [
                    "定义 handoff、decision、formal output、evidence 的正式读写动作。",
                    "定义业务调用点、正式 receipt / registry record 和 managed ref。",
                    "定义被拒绝读写时对业务方可见的失败表现。",
                ],
                "constraints": [
                    "正式写入必须受 Gateway / Policy / Registry 治理。",
                    "不得 fallback 到自由写入。",
                    "不得扩张成全仓文件治理。",
                ],
                "dependencies": [
                    "Gateway / Path Policy / Registry 已接入主链。",
                    "managed write/read preflight 可输出 verdict。",
                ],
                "non_goals": [
                    "不覆盖仓库级全局治理。",
                    "不重写 ADR-005 模块实现。",
                ],
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "正式写入返回 managed refs",
                        "given": "Gateway / Path Policy / Registry 已连通",
                        "when": "执行主链正式 write/read",
                        "then": "成功路径返回 receipt_ref、registry_record_ref、managed_artifact_ref",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "主链 IO 不能扩张为全局文件治理",
                        "given": "请求包含超出主链边界的目录动作",
                        "when": "执行 policy scope check",
                        "then": "超出范围的仓库级治理请求被拒绝",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "失败路径保持可追溯且不得 fallback",
                        "given": "preflight 或 registry / receipt build 可失败",
                        "when": "触发 policy_deny、registry_prerequisite_failed、receipt_pending",
                        "then": "失败路径被记录且不发生 free write fallback",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-IO", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            pilot_feature = {
                "feat_ref": "FEAT-SRC-001-PILOT",
                "title": "governed skill 接入与 pilot 验证流",
                "goal": "冻结 governed skill 的 onboarding、pilot、cutover 与 fallback 规则。",
                "scope": [
                    "定义哪些 governed skill 先接入以及 scope 外对象如何处理。",
                    "定义 pilot 主链如何选定、扩围和形成真实 evidence。",
                    "定义 cutover / fallback 如何判断，以及 adoption 成立需要交付哪些真实 evidence。",
                ],
                "constraints": [
                    "至少保留一条真实 pilot 主链。",
                    "evidence 不足时必须 fail closed。",
                    "不得扩张成仓库级全局治理。",
                ],
                "dependencies": [
                    "foundation FEAT 对应主链已可执行。",
                    "至少一个真实 pilot scope 已被选定。",
                ],
                "non_goals": [
                    "不要求一次性迁移所有 governed skill。",
                    "不替代 release orchestration。",
                ],
                "track": "adoption_e2e",
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "Onboarding scope and migration waves are explicit",
                        "given": "EPIC requires real governed skill landing",
                        "when": "The onboarding package is prepared",
                        "then": "onboarding scope, waves, cutover and fallback rules are machine-readable",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "At least one real pilot chain is required",
                        "given": "Foundation FEATs are implemented in isolation",
                        "when": "Adoption readiness is evaluated",
                        "then": "At least one producer -> consumer -> audit -> gate pilot chain is required",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "Adoption scope does not expand into repository-wide governance",
                        "given": "A team proposes folding all file-governance cleanup into this FEAT",
                        "when": "The proposal is checked against FEAT boundaries",
                        "then": "The FEAT rejects repository-wide governance expansion",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-PILOT", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }

            io_bundle = self.make_bundle_json(io_feature, run_id="feat-to-testset-io")
            io_input_dir = self.make_feat_package(repo_root, "feat-to-testset-io", io_bundle)
            io_artifacts_dir = self.run_testset_flow(repo_root, io_input_dir, "FEAT-SRC-001-IO", "feat-to-testset-io-out")
            io_handoff = json.loads((io_artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            io_access = io_handoff["required_environment_inputs"]["access"]
            self.assertTrue(any("credential" in item.lower() or "token" in item.lower() or "账号" in item for item in io_access))

            pilot_bundle = self.make_bundle_json(pilot_feature, run_id="feat-to-testset-pilot")
            pilot_input_dir = self.make_feat_package(repo_root, "feat-to-testset-pilot", pilot_bundle)
            pilot_artifacts_dir = self.run_testset_flow(repo_root, pilot_input_dir, "FEAT-SRC-001-PILOT", "feat-to-testset-pilot-out")
            pilot_handoff = json.loads((pilot_artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            pilot_test_set = yaml.safe_load((pilot_artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))
            pilot_access = pilot_handoff["required_environment_inputs"]["access"]
            self.assertTrue(any("credential" in item.lower() or "token" in item.lower() or "账号" in item for item in pilot_access))
            self.assertEqual(len(pilot_test_set["test_units"]), 5)
            self.assertIn(
                "fallback 结果必须记录到 receipt / wave state",
                [unit["title"] for unit in pilot_test_set["test_units"]],
            )
            self.assertIn(
                "adoption scope 不得扩张为仓库级全局治理改造",
                [unit["title"] for unit in pilot_test_set["test_units"]],
            )
            self.assertTrue(
                any(unit["trigger_action"] == "生成 onboarding matrix，并把 wave_id、compat_mode、cutover_guard_ref 写回 rollout state。"
                    for unit in pilot_test_set["test_units"])
            )
            fallback_unit = next(unit for unit in pilot_test_set["test_units"] if unit["title"] == "fallback 结果必须记录到 receipt / wave state")
            self.assertFalse(fallback_unit.get("acceptance_ref"))
            self.assertTrue(fallback_unit.get("derivation_basis"))
            self.assertFalse(any("file-governance cleanup" in item for item in fallback_unit["input_preconditions"]))
            pilot_trace = {
                row["acceptance_ref"]: row for row in pilot_test_set["acceptance_traceability"]
            }
            self.assertEqual(
                pilot_trace["AC-02"]["when"] if "AC-02" in pilot_trace else pilot_trace["FEAT-SRC-001-PILOT-AC-02"]["when"],
                "执行 pilot chain verifier 并评估 adoption readiness",
            )
            self.assertIn(
                "producer -> gate -> formal -> consumer -> audit",
                pilot_trace["AC-02"]["then"] if "AC-02" in pilot_trace else pilot_trace["FEAT-SRC-001-PILOT-AC-02"]["then"],
            )
            mapped_units = pilot_trace["AC-03"]["unit_refs"] if "AC-03" in pilot_trace else pilot_trace["FEAT-SRC-001-PILOT-AC-03"]["unit_refs"]
            self.assertEqual(len(mapped_units), 1)

    def test_execution_runner_operator_entry_feat_emits_runner_specific_testset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            semantic_lock = {
                "domain_type": "execution_runner_rule",
                "one_sentence_truth": "gate approve 后写入 ready execution job，由 runner 自动消费并推进到下一 skill，同时保留显式的 operator entry / control / monitor surface。",
                "primary_object": "execution_loop_job_runner",
                "lifecycle_stage": "governed_runtime",
                "allowed_capabilities": [
                    "ready_job_emission",
                    "runner_operator_entry",
                    "runner_control_surface",
                    "ready_queue_consumption",
                    "next_skill_dispatch",
                    "execution_result_feedback",
                    "runner_observability",
                ],
                "forbidden_capabilities": [
                    "formal_publication_only",
                    "manual_downstream_relay",
                    "directory_guessing_monitor",
                ],
                "inheritance_rule": "Preserve runner operator surfaces and authoritative queue lineage across downstream derivation.",
            }
            feature = {
                "feat_ref": "FEAT-SRC-ADR018-ENTRY-002",
                "title": "Execution Runner 用户入口流",
                "goal": "为 Claude/Codex CLI 提供显式的 runner skill 入口，用于启动、恢复与观察 execution loop。", 
                "axis_id": "runner-operator-entry",
                "scope": [
                    "定义独立 runner skill entry 与 CLI control surface 的入口名。",
                    "定义 start / resume 所需的 run context 与 receipt。",
                    "明确入口职责只负责启动或恢复 runner，而不是人工 relay 下游 skill。",
                ],
                "constraints": [
                    "必须是显式的 Claude/Codex CLI 用户入口。",
                    "start / resume 必须保留 authoritative runner context。",
                    "不得把入口逻辑退化成 manual relay。",
                ],
                "dependencies": [
                    "operator_surface_inventory 已声明 skill_entry 与 cli_control_surface。",
                    "runner context bootstrapper 可创建或恢复 run context。",
                ],
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "runner skill entry is explicit",
                        "given": "operator surface inventory includes a runner skill entry",
                        "when": "derive the TESTSET",
                        "then": "the testset preserves the named runner skill entry and CLI surface",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "start and resume preserve authoritative context",
                        "given": "runner start or resume request is issued",
                        "when": "the runner entry is executed",
                        "then": "runner_run_ref and runner context remain authoritative and traceable",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "manual relay is not required",
                        "given": "runner entry is available",
                        "when": "the operator starts the runner",
                        "then": "normal flow does not require manually relaying the next skill invocation",
                    },
                ],
                "semantic_lock": semantic_lock,
                "source_refs": ["FEAT-SRC-ADR018-ENTRY-002", "EPIC-SRC-ADR018", "SRC-ADR018", "ADR-018"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-to-testset-runner-entry")
            bundle["semantic_lock"] = semantic_lock
            input_dir = self.make_feat_package(repo_root, "feat-to-testset-runner-entry", bundle)

            artifacts_dir = self.run_testset_flow(
                repo_root,
                input_dir,
                "FEAT-SRC-ADR018-ENTRY-002",
                "feat-to-testset-runner-entry-out",
            )
            test_set = yaml.safe_load((artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))

            self.assertEqual(test_set["recommended_coverage_scope_name"], ["execution runner operator-entry feature"])
            self.assertEqual(
                test_set["feature_owned_code_paths"],
                [
                    "cli/lib/runner_entry.py",
                    "cli/lib/execution_runner.py",
                    "cli/commands/loop/command.py",
                ],
            )
            self.assertEqual(handoff["target_skill"], "skill.qa.test_exec_cli")
            self.assertTrue(
                any("runner scope fixture" in item for item in handoff["required_environment_inputs"]["data"])
            )
            self.assertTrue(
                any("runner skill entry" in item.lower() or "run-execution" in item.lower() for item in handoff["required_environment_inputs"]["services"] + handoff["required_environment_inputs"]["ui_or_integration_context"])
            )
            self.assertTrue(
                any("runner invocation receipt" in item.lower() or "runner context ref" in item.lower() for unit in test_set["test_units"] for item in unit["required_evidence"] + unit["supporting_refs"])
            )
            self.assertIn(
                "runner skill 入口作为显式 Claude/Codex CLI 用户入口存在",
                [unit["title"] for unit in test_set["test_units"]],
            )
            self.assertIn(
                "start 与 resume 保留 authoritative runner context",
                [unit["title"] for unit in test_set["test_units"]],
            )
            trace = {row["acceptance_ref"]: row for row in test_set["acceptance_traceability"]}
            self.assertIn("人工 relay", trace["AC-03"]["then"])
            self.assertTrue(all(row["coverage_status"] == "covered" for row in test_set["acceptance_traceability"]))

    def test_gate_handoff_requires_machine_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            gate_feature = {
                "feat_ref": "FEAT-SRC-001-GATE",
                "title": "主链 gate 审核与裁决流",
                "goal": "冻结 gate decision 的单一路径与 decision object 语义。",
                "scope": [
                    "定义 approve / revise / retry / handoff / reject 的业务语义和输出物。",
                    "定义每种裁决的返回去向和对上游的业务结果。",
                    "定义 decision object 如何成为后续 formal 发布的唯一触发来源。",
                ],
                "constraints": [
                    "decision path 必须唯一。",
                    "decision object 不得并行分叉。",
                    "formal trigger 只来自 approve。",
                ],
                "dependencies": [
                    "candidate package 已形成 authoritative handoff submission。",
                    "formal publish control layer 可消费 approve decision object。",
                ],
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "Gate decision path is single and explicit",
                        "given": "candidate package awaiting approval",
                        "when": "handoff enters gate evaluation",
                        "then": "only one authoritative decision object is formed",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "Candidate cannot bypass gate",
                        "given": "candidate exists but approval has not occurred",
                        "when": "a downstream consumer requests formal input",
                        "then": "candidate is not treated as formal source",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "Formal publication is only triggered by the decision object",
                        "given": "approve decision object exists",
                        "when": "formal publication is requested",
                        "then": "only approve decision object can trigger formal publish",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-GATE", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            gate_bundle = self.make_bundle_json(gate_feature, run_id="feat-to-testset-gate")
            gate_input_dir = self.make_feat_package(repo_root, "feat-to-testset-gate", gate_bundle)
            gate_result = self.run_cmd(
                "run",
                "--input",
                str(gate_input_dir),
                "--feat-ref",
                "FEAT-SRC-001-GATE",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-to-testset-gate-out",
            )
            self.assertEqual(gate_result.returncode, 0, gate_result.stderr)
            gate_artifacts_dir = Path(json.loads(gate_result.stdout)["artifacts_dir"])
            gate_handoff = json.loads((gate_artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            gate_access = gate_handoff["required_environment_inputs"]["access"]
            self.assertTrue(any("service account" in item.lower() or "token" in item.lower() or "credential" in item.lower() for item in gate_access))

    def test_formal_feat_ref_is_admissible_input_for_feat_to_testset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-202",
                "title": "配置中心测试集主链",
                "goal": "验证 formal FEAT 能反查回 bundle package 并驱动 TESTSET 派生。",
                "scope": ["保留 acceptance 边界。", "保留测试执行 handoff。", "允许 formal admission 进入 TESTSET。"],
                "constraints": ["不得跳过 FEAT。", "不得丢失 source refs。", "TESTSET 仍从 feat_freeze_package 派生。"],
                "acceptance_checks": [
                    {"id": "AC-01", "scenario": "formal ref resolves package", "given": "formal FEAT", "when": "run feat-to-testset", "then": "source package dir 被正确反查"},
                    {"id": "AC-02", "scenario": "selected feat remains explicit", "given": "formal FEAT", "when": "derive TESTSET", "then": "feat_ref 与 title 不丢失"},
                    {"id": "AC-03", "scenario": "input mode is formal admission", "given": "formal FEAT", "when": "validate input", "then": "input_mode=formal_admission"},
                ],
                "source_refs": ["FEAT-SRC-001-202", "EPIC-SRC-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-formal-testset")
            self.make_feat_package(repo_root, "feat-formal-testset", bundle)
            formal_feat_path = repo_root / "ssot" / "feat" / "FEAT-SRC-001-202__configuration-testset-mainline.md"
            formal_feat_path.parent.mkdir(parents=True, exist_ok=True)
            formal_feat_path.write_text(
                "---\nid: FEAT-SRC-001-202\nssot_type: FEAT\ntitle: 配置中心测试集主链\nstatus: frozen\n---\n\n# 配置中心测试集主链\n\nFormal FEAT body.\n",
                encoding="utf-8",
            )
            registry_dir = repo_root / "artifacts" / "registry"
            registry_dir.mkdir(parents=True, exist_ok=True)
            (registry_dir / "formal-feat-feat-src-001-202.json").write_text(
                json.dumps(
                    {
                        "artifact_ref": "formal.feat.feat-src-001-202",
                        "managed_artifact_ref": "ssot/feat/FEAT-SRC-001-202__configuration-testset-mainline.md",
                        "status": "materialized",
                        "trace": {"run_ref": "feat-formal-testset", "workflow_key": "product.epic-to-feat"},
                        "metadata": {
                            "layer": "formal",
                            "source_package_ref": "artifacts/epic-to-feat/feat-formal-testset",
                            "assigned_id": "FEAT-SRC-001-202",
                            "feat_ref": "FEAT-SRC-001-202",
                            "ssot_type": "FEAT",
                        },
                        "lineage": ["epic-to-feat.feat-formal-testset.feat-freeze-bundle", "artifacts/active/gates/decisions/gate-decision.json"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_cmd(
                "run",
                "--input",
                "formal.feat.feat-src-001-202",
                "--feat-ref",
                "FEAT-SRC-001-202",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "testset-from-formal",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["input_mode"], "formal_admission")
            manifest = json.loads((Path(payload["artifacts_dir"]) / "package-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["input_artifacts_dir"],
                str((repo_root / "artifacts" / "epic-to-feat" / "feat-formal-testset").resolve()),
            )

            validate = self.run_cmd(
                "validate-input",
                "--input",
                "formal.feat.feat-src-001-202",
                "--feat-ref",
                "FEAT-SRC-001-202",
                "--repo-root",
                str(repo_root),
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)


if __name__ == "__main__":
    unittest.main()
