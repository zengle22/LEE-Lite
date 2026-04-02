import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "skills" / "ll-dev-tech-to-impl" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tech_to_impl_package_builder import build_semantic_drift_check
from tests.unit.support_tech_to_impl import TechToImplWorkflowHarness


class TechToImplWorkflowTests(TechToImplWorkflowHarness):
    def test_semantic_drift_accepts_allowed_capability_signature_when_primary_anchors_are_absent(self) -> None:
        feature = {
            "title": "扩展画像渐进补全能力",
            "goal": "让扩展画像在首页任务卡中按步补全并独立保存。",
            "semantic_lock": {
                "domain_type": "extended_profile_completion_flow",
                "one_sentence_truth": "用户可在首页按任务卡逐步补充跑步背景与扩展画像，且每次补全都能独立保存。",
                "primary_object": "extended profile task card",
                "lifecycle_stage": "incremental save",
                "allowed_capabilities": [
                    "task card",
                    "profile completion",
                    "extended profile patch",
                ],
                "forbidden_capabilities": [
                    "genericrequest",
                ],
            },
        }
        bundle_json = {
            "title": "扩展画像渐进补全能力 Implementation Task Package",
            "selected_scope": {
                "scope": [
                    "将扩展画像后置到首页任务卡与增量补全过程中，允许分步填写、分步保存。",
                ]
            },
        }
        upstream_design_refs = {
            "frozen_decisions": {
                "implementation_rules": [
                    "扩展画像渐进补全能力 必须围绕 task card、profile completion 和 patch save 语义实现。",
                ],
                "integration_points": [
                    "homepage shell 在用户进入首页后调用任务卡和增量保存 surface。",
                ],
            }
        }

        drift = build_semantic_drift_check(feature, bundle_json, upstream_design_refs)

        self.assertEqual(drift["verdict"], "pass")
        self.assertTrue(drift["semantic_lock_preserved"])
        self.assertIn("allowed_capability_signature", drift["anchor_matches"])

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
            artifacts_dir = self.run_impl_flow(repo_root, input_dir, feature["feat_ref"], bundle["tech_ref"])
            impl_bundle = json.loads((artifacts_dir / "impl-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            gate_ready_package = json.loads((artifacts_dir / "input" / "gate-ready-package.json").read_text(encoding="utf-8"))
            smoke_gate = json.loads((artifacts_dir / "smoke-gate-subject.json").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-feature-delivery.json").read_text(encoding="utf-8"))
            evidence_plan = json.loads((artifacts_dir / "dev-evidence-plan.json").read_text(encoding="utf-8"))
            bundle_markdown = (artifacts_dir / "impl-bundle.md").read_text(encoding="utf-8")
            impl_task = (artifacts_dir / "impl-task.md").read_text(encoding="utf-8")

            self.assertTrue((artifacts_dir / "frontend-workstream.md").exists())
            self.assertTrue((artifacts_dir / "backend-workstream.md").exists())
            self.assertTrue((artifacts_dir / "upstream-design-refs.json").exists())
            self.assertEqual(impl_bundle["status"], "execution_ready")
            self.assertTrue(smoke_gate["ready_for_execution"])
            self.assertEqual(handoff["target_template_id"], "template.dev.feature_delivery_l2")
            self.assertIn("frontend-workstream.md", smoke_gate["required_inputs"])
            self.assertIn("backend-workstream.md", smoke_gate["required_inputs"])
            self.assertIn("impl-bundle.json", handoff["deliverables"])
            self.assertTrue(handoff["acceptance_refs"])
            self.assertTrue(evidence_plan["rows"])
            self.assertEqual(evidence_plan["rows"][0]["acceptance_ref"], "AC-001")
            self.assertIn("See `smoke-gate-subject.json`", bundle_markdown)
            self.assertIn("## Consumption Boundary", bundle_markdown)
            self.assertIn("### Concrete Touch Set", bundle_markdown)
            self.assertIn("### Repo-Aware Placement", bundle_markdown)
            self.assertIn("### Embedded Frozen Contracts", bundle_markdown)
            self.assertIn("### Ordered Task Breakdown", bundle_markdown)
            self.assertIn("### Acceptance-to-Task Mapping", bundle_markdown)
            self.assertEqual(impl_bundle["self_contained_policy"]["principle"], "strong_self_contained_execution_contract")
            self.assertTrue(impl_bundle["repo_touch_points"])
            self.assertTrue(impl_bundle["implementation_task_breakdown"])
            self.assertIn("## 6. 实施要求", impl_task)
            self.assertIn("## 8. 验收标准与 TESTSET 映射", impl_task)
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
            self.assertIn("### Execution Boundary", impl_task)
            self.assertIn("### Acceptance Trace", impl_task)
            self.assertIn("### Acceptance-to-Task Mapping", impl_task)
            self.assertIn("### Ordered Task Breakdown", impl_task)
            self.assertIn("- status: `execution_ready`", impl_task)
            self.assertNotIn("- status: `in_progress`", impl_task)
            self.assertIn("cli/lib/protocol.py", impl_task)
            self.assertIn("cli/lib/mainline_runtime.py", impl_task)
            self.assertIn("handoff_prepared -> handoff_submitted -> gate_pending_visible -> decision_returned", impl_task)
            self.assertIn("HandoffEnvelope", impl_task)
            self.assertNotIn("keeping approval and re-entry semantics outside this FEAT", impl_task)
            self.assertIn("Frozen touch set is implemented without design drift.", impl_task)
            self.assertIn("Frozen contracts and runtime sequence execute through the implementation entry.", impl_task)
            self.assertNotIn("The FEAT must define which loop owns which transition", impl_task)

            upstream_design_refs = json.loads((artifacts_dir / "upstream-design-refs.json").read_text(encoding="utf-8"))
            self.assertNotIn("tech_impl", upstream_design_refs["primary_artifacts"])
            frozen_decisions = upstream_design_refs["frozen_decisions"]
            self.assertIn("state_model", frozen_decisions)
            self.assertIn("implementation_unit_mapping", frozen_decisions)
            self.assertTrue(any("decision-driven revise/retry routing stays in runtime" in item for item in frozen_decisions["implementation_rules"]))
            self.assertFalse(any("keeping approval and re-entry semantics outside this FEAT" in item for item in frozen_decisions["implementation_rules"]))
            self.assertEqual(manifest["gate_ready_package_ref"], f"artifacts/tech-to-impl/{artifacts_dir.name}/input/gate-ready-package.json")
            self.assertTrue(manifest["candidate_registry_ref"].startswith("artifacts/registry/"))
            self.assertTrue(manifest["authoritative_handoff_ref"].startswith("artifacts/active/gates/handoffs/"))
            self.assertTrue(manifest["gate_pending_ref"].startswith("artifacts/active/gates/pending/"))
            self.assertEqual(gate_ready_package["payload"]["candidate_ref"], f"tech-to-impl.{artifacts_dir.name}.impl-bundle")
            self.assertEqual(gate_ready_package["payload"]["machine_ssot_ref"], f"artifacts/tech-to-impl/{artifacts_dir.name}/impl-bundle.json")
            self.assertTrue((repo_root / manifest["authoritative_handoff_ref"]).exists())
            self.assertTrue((repo_root / manifest["gate_pending_ref"]).exists())
            registry_record = json.loads((repo_root / manifest["candidate_registry_ref"]).read_text(encoding="utf-8"))
            self.assertEqual(registry_record["artifact_ref"], f"tech-to-impl.{artifacts_dir.name}.impl-bundle")
            self.assertEqual(registry_record["managed_artifact_ref"], f"artifacts/tech-to-impl/{artifacts_dir.name}/impl-bundle.json")
            self.assertEqual(registry_record["status"], "committed")
            self.assertEqual(registry_record["metadata"]["layer"], "candidate")
            self.assertEqual(registry_record["metadata"]["source_package_ref"], f"artifacts/tech-to-impl/{artifacts_dir.name}")

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

    def test_run_reuses_revision_request_on_allow_update_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-201-R",
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
            bundle = self.make_bundle_json(feature, run_id="tech-impl-revise", arch_required=True, api_required=True)
            input_dir = self.make_tech_package(repo_root, "tech-impl-revise", bundle)

            first_pass = self.run_cmd(
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
            self.assertEqual(first_pass.returncode, 0, first_pass.stderr)
            artifacts_dir = Path(json.loads(first_pass.stdout)["artifacts_dir"])

            revision_request_path = repo_root / "revision-request.json"
            revision_request = {
                "workflow_key": "dev.tech-to-impl",
                "run_id": artifacts_dir.name,
                "source_run_id": "tech-impl-revise",
                "decision_type": "revise",
                "decision_target": "dev.tech-to-impl",
                "decision_reason": "Gate requested execution-side revision before resubmission.",
                "basis_refs": [
                    f"artifacts/tech-to-impl/{artifacts_dir.name}/impl-bundle.json",
                    f"artifacts/tech-to-impl/{artifacts_dir.name}/package-manifest.json",
                ],
                "source_gate_decision_ref": "artifacts/gate-human-orchestrator/fake/gate-decision-bundle.json",
                "source_return_job_ref": "artifacts/jobs/waiting-human/fake-execution-return.json",
                "authoritative_input_ref": f"dev.tech-to-impl.{artifacts_dir.name}.impl-bundle",
                "candidate_ref": f"tech-to-impl.{artifacts_dir.name}.impl-bundle",
                "original_input_path": str(input_dir),
                "triggered_by_request_id": "return-job-001",
                "revision_round": 1,
            }
            revision_request_path.write_text(json.dumps(revision_request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            second_pass = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                feature["feat_ref"],
                "--tech-ref",
                bundle["tech_ref"],
                "--repo-root",
                str(repo_root),
                "--allow-update",
                "--revision-request",
                str(revision_request_path),
            )
            self.assertEqual(second_pass.returncode, 0, second_pass.stderr)
            rerun_payload = json.loads(second_pass.stdout)
            self.assertEqual(rerun_payload["revision_round"], 1)
            self.assertTrue(rerun_payload["revision_request_ref"].endswith("revision-request.json"))

            impl_bundle = json.loads((artifacts_dir / "impl-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            execution_evidence = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))
            supervision_evidence = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            revision_file = json.loads((artifacts_dir / "revision-request.json").read_text(encoding="utf-8"))

            self.assertEqual(revision_file["decision_reason"], revision_request["decision_reason"])
            self.assertEqual(impl_bundle["revision_context"]["decision_reason"], revision_request["decision_reason"])
            self.assertEqual(impl_bundle["revision_context"]["revision_round"], 1)
            self.assertIn("Gate revise:", impl_bundle["selected_scope"]["constraints"][-1])
            self.assertEqual(manifest["revision_request_ref"], execution_evidence["revision_request_ref"])
            self.assertEqual(manifest["revision_request_ref"], supervision_evidence["revision_request_ref"])
            self.assertEqual(manifest["revision_round"], 1)
            self.assertEqual(execution_evidence["revision_summary"], supervision_evidence["revision_summary"])
            self.assertTrue(any(str(path).endswith("revision-request.json") for path in execution_evidence["outputs"]))

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
            self.assertEqual([item["acceptance_ref"] for item in impl_bundle["testset_mapping"]["mappings"]], ["AC-001", "AC-002", "AC-003"])
            self.assertFalse(any(item["mapping_status"] == "package_bound_gap" for item in impl_bundle["testset_mapping"]["mappings"]))

    def test_formal_publication_feature_does_not_false_positive_frontend_or_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-204",
                "title": "formal 发布与下游准入流",
                "axis_id": "object-layering",
                "track": "foundation",
                "goal": "冻结 approved decision 之后如何形成 formal output、formal ref 与 lineage，并让下游只通过正式准入链消费。",
                "scope": [
                    "定义 approved decision 之后的 formal 发布动作和 formal output 完成态。",
                    "定义 formal ref / lineage 如何成为 authoritative downstream input。",
                    "定义 consumer admission 边界，阻止 candidate 或旁路对象被正式消费。",
                ],
                "constraints": [
                    "Epic-level constraints：当 rollout_required 为 true 时，foundation 与 adoption_e2e 必须同时落成。",
                    "Consumer 准入必须沿 formal refs 与 lineage 判断，不得通过路径猜测获得读取资格。",
                ],
                "dependencies": [
                    "Boundary to gate review: 本 FEAT 从 approved decision 之后开始。",
                    "Boundary to IO 治理: path / mode 规则留给 IO 治理 FEAT。",
                ],
                "acceptance_checks": [
                    {"scenario": "formal publication path", "then": "approved decision -> formal publication -> admission chain explicit"},
                    {"scenario": "admission is formal-ref based", "then": "consumer must resolve formal refs and lineage"},
                ],
                "identity_and_scenario": {
                    "product_interface": "formal 发布与准入流",
                    "completed_state": "formal package published and admitted",
                    "user_story": "As a formalization owner, I want approved decisions to become one explicit formal publication package.",
                },
                "collaboration_and_timeline": {
                    "loop_gate_human_involvement": [
                        "Gate only provides approved decision.",
                        "Formalization actor publishes formal output after approval.",
                    ]
                },
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-formalization", arch_required=True, api_required=False)
            input_dir = self.make_tech_package(repo_root, "tech-impl-formalization", bundle)

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
            smoke_gate = json.loads((artifacts_dir / "smoke-gate-subject.json").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-feature-delivery.json").read_text(encoding="utf-8"))

            self.assertFalse(impl_bundle["workstream_assessment"]["frontend_required"])
            self.assertTrue(impl_bundle["workstream_assessment"]["backend_required"])
            self.assertFalse(impl_bundle["workstream_assessment"]["migration_required"])
            self.assertFalse((artifacts_dir / "frontend-workstream.md").exists())
            self.assertFalse((artifacts_dir / "migration-cutover-plan.md").exists())
            self.assertNotIn("frontend-workstream.md", smoke_gate["required_inputs"])
            self.assertNotIn("migration-cutover-plan.md", smoke_gate["required_inputs"])
            self.assertIn("backend-workstream.md", smoke_gate["required_inputs"])
            self.assertTrue(handoff["acceptance_refs"])
            self.assertIn("backend-workstream.md", handoff["deliverables"])

    def test_adoption_e2e_component_local_phrase_does_not_false_positive_frontend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-205",
                "title": "governed skill 接入与 pilot 验证流",
                "axis_id": "skill-adoption-e2e",
                "track": "adoption_e2e",
                "goal": "冻结 governed skill 的 onboarding、pilot、cutover 与 fallback 规则。",
                "scope": [
                    "定义 skill onboarding wave 和 pilot target chain。",
                    "定义 cutover / fallback 决策和 rollout evidence。",
                    "保持 runtime、gate、audit 的真实闭环验证。",
                ],
                "constraints": [
                    "Authoritative inherited constraints：对外暴露一个宽 skill：`skill.qa.test_exec_web_e2e`。",
                    "Authoritative inherited constraints：对外暴露一个宽 skill：`skill.qa.test_exec_cli`。",
                    "Authoritative inherited constraints：内部保留一个窄 runner skill：`skill.runner.test_e2e`。",
                    "Authoritative inherited constraints：内部保留一个窄 runner skill：`skill.runner.test_cli`。",
                ],
                "dependencies": [
                    "pilot evidence routes through gate and audit",
                    "cutover and fallback stay runtime-owned",
                ],
                "acceptance_and_testability": {
                    "acceptance_criteria": [
                        "The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests."
                    ],
                    "observable_outcomes": ["pilot evidence is traceable"],
                },
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-adoption", arch_required=True, api_required=True)
            input_dir = self.make_tech_package(repo_root, "tech-impl-adoption", bundle)

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

            self.assertFalse(impl_bundle["workstream_assessment"]["frontend_required"])
            self.assertTrue(impl_bundle["workstream_assessment"]["backend_required"])
            self.assertTrue(impl_bundle["workstream_assessment"]["migration_required"])
            self.assertFalse((artifacts_dir / "frontend-workstream.md").exists())

    def test_validate_package_readiness_rejects_empty_evidence_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-206",
                "title": "候选提交与交接流",
                "goal": "让候选交接和 gate 输入可进入实施。",
                "scope": ["定义 handoff runtime", "定义 gate input", "定义 evidence input"],
                "constraints": ["不得改写 TECH", "必须保留 smoke gate", "必须保留 acceptance refs"],
                "dependencies": ["gate", "runtime"],
                "acceptance_checks": [
                    {"scenario": "handoff visible", "then": "candidate handoff is traceable"},
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-empty-evidence", arch_required=True, api_required=True)
            input_dir = self.make_tech_package(repo_root, "tech-impl-empty-evidence", bundle)

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
            evidence_path = artifacts_dir / "dev-evidence-plan.json"
            evidence_plan = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence_plan["rows"] = []
            evidence_path.write_text(json.dumps(evidence_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(readiness.returncode, 0)
            payload = json.loads(readiness.stdout)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("evidence" in error.lower() for error in payload["errors"]))

    def test_validate_input_rejects_adr007_adoption_package_without_cli_family(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-ADR007-005",
                "title": "governed skill 接入与 pilot 验证流",
                "axis_id": "skill-adoption-e2e",
                "track": "adoption_e2e",
                "goal": "冻结 skill onboarding 与 pilot 验证规则。",
                "scope": ["定义 onboarding", "定义 pilot chain", "定义 cutover / fallback"],
                "constraints": [
                    "Authoritative inherited constraints：对外暴露一个宽 skill：`skill.qa.test_exec_web_e2e`。",
                    "Authoritative inherited constraints：内部保留一个窄 runner skill：`skill.runner.test_e2e`。",
                ],
                "dependencies": ["gate", "audit"],
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-adr007-family", arch_required=True, api_required=True)
            bundle["source_refs"] = [
                f"dev.feat-to-tech::tech-impl-adr007-family",
                feature["feat_ref"],
                bundle["tech_ref"],
                "EPIC-ADR007",
                "SRC-ADR007",
                "ADR-007",
            ]
            bundle["tech_design"]["implementation_rules"] = list(feature["constraints"])
            input_dir = self.make_tech_package(repo_root, "tech-impl-adr007-family", bundle)

            result = self.run_cmd(
                "validate-input",
                "--input",
                str(input_dir),
                "--feat-ref",
                feature["feat_ref"],
                "--tech-ref",
                bundle["tech_ref"],
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("skill.qa.test_exec_cli" in error or "skill.runner.test_cli" in error for error in payload["errors"]))

    def test_acceptance_fallback_uses_observable_outcomes_not_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-205",
                "title": "governed skill 接入与 pilot 验证流",
                "axis_id": "skill-adoption-e2e",
                "track": "adoption_e2e",
                "goal": "冻结 governed skill 的 onboarding、pilot、cutover 与 fallback 规则。",
                "scope": [
                    "定义 onboarding 范围。",
                    "定义 pilot evidence。",
                    "定义 cutover / fallback 规则。",
                ],
                "constraints": [
                    "不扩大为仓库级治理改造。",
                    "真实 pilot evidence 是必要条件。",
                ],
                "dependencies": ["foundation ready", "gate evidence available"],
                "acceptance_and_testability": {
                    "acceptance_criteria": [
                        "criterion one",
                        "criterion two",
                        "criterion three",
                    ],
                    "observable_outcomes": [
                        "pilot evidence 可追踪。",
                        "cutover / fallback 边界可被外部观察。",
                    ],
                },
                "product_objects_and_deliverables": {
                    "authoritative_output": "pilot evidence + cutover decision"
                },
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-acceptance-fallback", arch_required=True, api_required=True)
            input_dir = self.make_tech_package(repo_root, "tech-impl-acceptance-fallback", bundle)

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
            impl_task = (artifacts_dir / "impl-task.md").read_text(encoding="utf-8")
            self.assertNotIn("Expectation must be confirmed during execution.", impl_task)
            self.assertIn("cutover / fallback 边界可被外部观察。", impl_task)

    def test_execution_runner_entry_impl_stays_backend_only_and_preserves_runner_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            semantic_lock = {
                "domain_type": "execution_runner_rule",
                "one_sentence_truth": "gate approve 后必须生成 ready execution job，并由 Execution Loop Job Runner 自动消费后推进到下一个 skill。",
                "primary_object": "execution_loop_job_runner",
                "lifecycle_stage": "post_gate_auto_progression",
                "allowed_capabilities": [
                    "ready_execution_job_materialization",
                    "runner_skill_entry",
                    "runner_control_surface",
                    "ready_queue_consumption",
                    "next_skill_dispatch",
                    "execution_result_recording",
                    "runner_observability",
                ],
                "forbidden_capabilities": [
                    "formal_publication_substitution",
                    "admission_only_decomposition",
                    "third_session_human_relay",
                ],
                "inheritance_rule": "approve semantics must stay coupled to ready-job emission and runner-driven next-skill progression; downstream may not replace this with formal publication or admission-only flows.",
            }
            feature = {
                "feat_ref": "FEAT-SRC-ADR018-002",
                "title": "Runner 用户入口流",
                "axis_id": "runner-operator-entry",
                "goal": "让 Claude/Codex CLI 用户通过独立 runner skill 启动或恢复 Execution Loop Job Runner。",
                "scope": ["定义 runner 独立 skill 入口。", "定义 start / resume 语义。", "定义入口调用如何把运行权交给 runner。"],
                "constraints": [
                    "Execution Loop Job Runner 必须以独立 skill 入口暴露给 Claude/Codex CLI 用户。",
                    "入口必须显式声明 start / resume 语义。",
                    "入口不得退化成手工逐个调用下游 skill。",
                ],
                "dependencies": [
                    "Boundary to ready-job FEAT: 本 FEAT 不负责生成 ready execution job。",
                    "Boundary to runner-control-surface FEAT: 入口启动后，后续控制语义由控制面 FEAT 承担。",
                ],
                "acceptance_checks": [
                    {"scenario": "Runner skill entry is explicit", "then": "存在一个明确的 runner skill entry"},
                    {"scenario": "Runner entry preserves authoritative context", "then": "保留 authoritative run context"},
                    {"scenario": "Runner entry is not manual relay", "then": "不会退化成 manual downstream relay"},
                ],
                "semantic_lock": semantic_lock,
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-runner-entry", arch_required=True, api_required=True)
            bundle["source_refs"] = [
                "dev.feat-to-tech::tech-impl-runner-entry",
                feature["feat_ref"],
                bundle["tech_ref"],
                "EPIC-ADR018",
                "SRC-ADR018",
                "ADR-018",
            ]
            bundle["selected_feat"]["semantic_lock"] = semantic_lock
            bundle["semantic_lock"] = semantic_lock
            bundle["tech_design"] = {
                "design_focus": list(feature["scope"]),
                "implementation_rules": list(feature["constraints"]),
                "state_model": [
                    "runner_entry_requested -> runner_context_initialized -> runner_entry_published",
                ],
                "implementation_unit_mapping": [
                    "`cli/lib/protocol.py` (`extend`): 定义 `ExecutionRunnerStartRequest`、`ExecutionRunnerRunRef`、`RunnerEntryReceipt` 结构。",
                    "`cli/lib/runner_entry.py` (`new`): 提供 runner skill start/resume 的入口适配层。",
                    "`cli/lib/execution_runner.py` (`new`): 管理 runner context bootstrap 与恢复逻辑。",
                    "`cli/commands/loop/command.py` (`new`): 暴露 `run-execution` 入口。",
                ],
                "interface_contracts": [
                    "`ExecutionRunnerStartRequest`: input=`runner_scope_ref`, `entry_mode`; output=`runner_run_ref`, `runner_context_ref`, `entry_receipt_ref`; errors=`runner_scope_missing`; idempotent=`yes by runner_scope_ref + entry_mode`。",
                ],
                "main_sequence": [
                    "1. accept start/resume request from Claude/Codex CLI",
                    "2. bootstrap or restore runner context",
                    "3. publish runner invocation receipt",
                    "4. hand off to queue consumption lifecycle",
                ],
                "integration_points": [
                    "调用方通过 `cli/commands/loop/command.py` / `cli/lib/runner_entry.py` 启动 runner。",
                    "runner context 交由 `cli/lib/execution_runner.py` 继续驱动后续 lifecycle。",
                ],
                "exception_and_compensation": [
                    "runner context build fail：返回 runner_context_conflict 并阻止进入 queue consumption。",
                ],
            }
            input_dir = self.make_tech_package(repo_root, "tech-impl-runner-entry", bundle)

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
            impl_task = (artifacts_dir / "impl-task.md").read_text(encoding="utf-8")
            backend_workstream = (artifacts_dir / "backend-workstream.md").read_text(encoding="utf-8")

            self.assertFalse(impl_bundle["workstream_assessment"]["frontend_required"])
            self.assertTrue(impl_bundle["workstream_assessment"]["backend_required"])
            self.assertFalse(impl_bundle["workstream_assessment"]["migration_required"])
            self.assertFalse((artifacts_dir / "frontend-workstream.md").exists())
            self.assertIn("cli/lib/runner_entry.py", impl_task)
            self.assertIn("cli/lib/execution_runner.py", impl_task)
            self.assertIn("Execution-runner lifecycle remains boundary-safe", impl_task)
            self.assertNotIn("pending visibility / boundary handoff behavior", impl_task)
            self.assertIn("run-execution", backend_workstream)

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
                "TECH-SRC-001-404",
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("tech-ref" in error.lower() or "tech_ref" in error.lower() for error in payload["errors"]))

    def test_run_shortens_default_run_id_for_long_tech_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-999",
                "title": "Long run id coverage",
                "goal": "验证 tech-to-impl 在长 TECH ref 下仍能稳定生成候选包。",
                "scope": ["保留 impl bundle", "保留 impl task", "避免默认路径过长"],
                "constraints": ["默认 run_id 需要稳定收短", "不得丢失 feat/tech traceability", "freeze-ready TECH 才能进入 IMPL"],
                "dependencies": ["workflow.dev.tech_to_impl"],
                "acceptance_checks": [
                    {"scenario": "default run id compacted", "then": "输出目录长度受控"},
                    {"scenario": "impl package still generated", "then": "impl bundle 与 handoff 都存在"},
                    {"scenario": "traceability preserved", "then": "feat_ref / tech_ref 未丢失"},
                ],
            }
            long_run_id = "adr001-003-006-unified-mainline-20260324-rerun13--feat-src-adr001-003-006-unified-mainline-20260324-rerun5-999"
            bundle = self.make_bundle_json(feature, run_id=long_run_id, arch_required=True, api_required=True)
            input_dir = self.make_tech_package(repo_root, long_run_id, bundle)

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
            self.assertLessEqual(len(payload["run_id"]), 120)
            artifacts_dir = Path(payload["artifacts_dir"])
            self.assertTrue((artifacts_dir / "impl-bundle.json").exists())
            self.assertTrue((artifacts_dir / "handoff-to-feature-delivery.json").exists())

    def test_review_projection_impl_keeps_backend_only_and_updates_subdoc_status(self) -> None:
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
                "feat_ref": "FEAT-SRC-ADR015-003",
                "title": "Projection 批注回写流",
                "goal": "把 reviewer comment 回写到 SSOT revision request，并在 SSOT 更新后重新生成 Projection。",
                "axis_id": "feedback-writeback",
                "scope": ["映射 comment 到 SSOT field", "生成 revision request", "触发 projection regeneration"],
                "constraints": ["不得直接 patch projection", "Projection 不是 authoritative source", "writeback 后必须重新生成 projection"],
                "dependencies": ["Projection comment 已捕获", "SSOT revision channel 可用"],
                "acceptance_checks": [
                    {"scenario": "comment maps to SSOT revision request", "then": "revision request 带有完整 provenance"},
                    {"scenario": "projection is regenerated after SSOT update", "then": "旧 projection 不再作为当前审核视图"},
                    {"scenario": "impl package remains backend-only", "then": "不生成 frontend workstream"},
                ],
                "semantic_lock": semantic_lock,
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-review-projection", arch_required=False, api_required=False)
            bundle["semantic_lock"] = semantic_lock
            bundle["selected_feat"]["semantic_lock"] = semantic_lock
            bundle["tech_design"] = {
                "design_focus": list(feature["scope"]),
                "implementation_rules": list(feature["constraints"]),
                "state_model": [
                    "review_comment_captured -> writeback_mapped -> ssot_revision_requested -> ssot_updated -> projection_regenerated",
                ],
                "implementation_unit_mapping": [
                    "`cli/lib/review_projection/writeback.py` (`new`): map reviewer comments to SSOT field refs and create revision requests。",
                    "`cli/lib/review_projection/regeneration.py` (`new`): regenerate projection after SSOT authoritative update。",
                ],
                "interface_contracts": [
                    "`ProjectionComment`: input=`projection_ref`, `comment_ref`, `comment_text`; output=`revision_request_ref`; errors=`mapping_failed`; idempotent=`yes by comment_ref`。",
                ],
                "main_sequence": [
                    "1. capture reviewer comment",
                    "2. map comment to SSOT-owned field",
                    "3. update Machine SSOT and regenerate Projection",
                ],
                "integration_points": [
                    "Reviewer comment enters writeback mapper after projection review.",
                    "Projection regeneration occurs only after SSOT authoritative update.",
                ],
                "exception_and_compensation": [
                    "mapping_failed -> comment_mapping_pending",
                    "regeneration_failed -> projection_regeneration_pending",
                ],
            }
            input_dir = self.make_tech_package(repo_root, "tech-impl-review-projection", bundle)
            artifacts_dir = self.run_impl_flow(repo_root, input_dir, feature["feat_ref"], bundle["tech_ref"])
            impl_bundle = json.loads((artifacts_dir / "impl-bundle.json").read_text(encoding="utf-8"))
            drift = json.loads((artifacts_dir / "semantic-drift-check.json").read_text(encoding="utf-8"))
            impl_task = (artifacts_dir / "impl-task.md").read_text(encoding="utf-8")
            integration_plan = (artifacts_dir / "integration-plan.md").read_text(encoding="utf-8")

            self.assertFalse(impl_bundle["workstream_assessment"]["frontend_required"])
            self.assertTrue(impl_bundle["workstream_assessment"]["backend_required"])
            self.assertFalse((artifacts_dir / "frontend-workstream.md").exists())
            self.assertTrue(drift["semantic_lock_preserved"])
            self.assertIn("status: execution_ready", impl_task)
            self.assertIn("status: execution_ready", integration_plan)

    def test_formal_tech_ref_is_admissible_input_for_tech_to_impl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-401",
                "title": "配置中心实施主链",
                "goal": "验证 formal TECH 能反查回 tech package 并驱动 IMPL 派生。",
                "scope": ["保留 TECH 边界。", "保留 workstream assessment。", "允许 formal admission 进入 IMPL。"],
                "constraints": ["不得跳过 TECH。", "不得丢失 source refs。", "IMPL 仍从 tech_design_package 派生。"],
                "acceptance_checks": [
                    {"scenario": "formal ref resolves package", "then": "source package dir 被正确反查"},
                    {"scenario": "selected tech remains explicit", "then": "feat_ref / tech_ref 不丢失"},
                    {"scenario": "input mode is formal admission", "then": "input_mode=formal_admission"},
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="tech-formal-impl", arch_required=True, api_required=False)
            self.make_tech_package(repo_root, "tech-formal-impl", bundle)
            formal_tech_path = repo_root / "ssot" / "tech" / "SRC-001" / "TECH-SRC-001-401__configuration-implementation-mainline.md"
            formal_tech_path.parent.mkdir(parents=True, exist_ok=True)
            formal_tech_path.write_text(
                "---\nid: TECH-SRC-001-401\nssot_type: TECH\ntitle: 配置中心实施主链技术设计\nstatus: accepted\n---\n\n# 配置中心实施主链技术设计\n\nFormal TECH body.\n",
                encoding="utf-8",
            )
            registry_dir = repo_root / "artifacts" / "registry"
            registry_dir.mkdir(parents=True, exist_ok=True)
            (registry_dir / "formal-tech-tech-formal-impl.json").write_text(
                json.dumps(
                    {
                        "artifact_ref": "formal.tech.tech-formal-impl",
                        "managed_artifact_ref": "ssot/tech/SRC-001/TECH-SRC-001-401__configuration-implementation-mainline.md",
                        "status": "materialized",
                        "trace": {"run_ref": "tech-formal-impl", "workflow_key": "dev.feat-to-tech"},
                        "metadata": {
                            "layer": "formal",
                            "source_package_ref": "artifacts/feat-to-tech/tech-formal-impl",
                            "assigned_id": "TECH-SRC-001-401",
                            "tech_ref": "TECH-SRC-001-401",
                            "feat_ref": "FEAT-SRC-001-401",
                            "ssot_type": "TECH",
                        },
                        "lineage": ["feat-to-tech.tech-formal-impl.tech-design-bundle", "artifacts/active/gates/decisions/gate-decision.json"],
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
                "formal.tech.tech-formal-impl",
                "--feat-ref",
                "FEAT-SRC-001-401",
                "--tech-ref",
                "TECH-SRC-001-401",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "impl-from-formal",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["input_mode"], "formal_admission")
            manifest = json.loads((Path(payload["artifacts_dir"]) / "package-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["input_artifacts_dir"],
                str((repo_root / "artifacts" / "feat-to-tech" / "tech-formal-impl").resolve()),
            )

            validate = self.run_cmd(
                "validate-input",
                "--input",
                "formal.tech.tech-formal-impl",
                "--feat-ref",
                "FEAT-SRC-001-401",
                "--tech-ref",
                "TECH-SRC-001-401",
                "--repo-root",
                str(repo_root),
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_validate_output_rejects_stale_impl_task_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-402",
                "title": "最小建档主链实施",
                "goal": "验证 stale impl-task 会被 validate-output 拦下。",
                "scope": ["最小建档页面提交", "首页放行"],
                "constraints": ["不得偏离上游 TECH", "必须保留 smoke gate subject"],
                "acceptance_checks": [
                    {"scenario": "impl task remains canonical", "then": "validate-output 只接受未漂移的 impl-task"},
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-stale-validate", arch_required=True, api_required=False)
            input_dir = self.make_tech_package(repo_root, "tech-impl-stale-validate", bundle)
            artifacts_dir = self.run_impl_flow(repo_root, input_dir, feature["feat_ref"], bundle["tech_ref"])

            impl_task = artifacts_dir / "impl-task.md"
            impl_task.write_text(impl_task.read_text(encoding="utf-8").replace("## 2. 本次目标", "## 2. 已被篡改"), encoding="utf-8")

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("canonical upstream projection", validate.stdout)

    def test_supervisor_review_rejects_stale_impl_task_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-403",
                "title": "设备连接后置增强实施",
                "goal": "验证 supervisor-review 会拒绝 stale impl-task。",
                "scope": ["后置连接入口", "非阻塞失败处理"],
                "constraints": ["不得扩展到无关 rollout", "必须保留 execution-ready 门槛"],
                "acceptance_checks": [
                    {"scenario": "stale impl task rejected", "then": "supervisor-review 返回 revise"},
                ],
            }
            bundle = self.make_bundle_json(feature, run_id="tech-impl-stale-review", arch_required=True, api_required=False)
            input_dir = self.make_tech_package(repo_root, "tech-impl-stale-review", bundle)
            artifacts_dir = self.run_impl_flow(repo_root, input_dir, feature["feat_ref"], bundle["tech_ref"])

            impl_task = artifacts_dir / "impl-task.md"
            impl_task.write_text(impl_task.read_text(encoding="utf-8") + "\nUnexpected drift.\n", encoding="utf-8")

            review = self.run_cmd("supervisor-review", "--artifacts-dir", str(artifacts_dir), "--repo-root", str(repo_root))
            self.assertNotEqual(review.returncode, 0)
            review_report = json.loads((artifacts_dir / "impl-review-report.json").read_text(encoding="utf-8"))
            acceptance_report = json.loads((artifacts_dir / "impl-acceptance-report.json").read_text(encoding="utf-8"))
            smoke_gate = json.loads((artifacts_dir / "smoke-gate-subject.json").read_text(encoding="utf-8"))
            self.assertEqual(review_report["decision"], "revise")
            self.assertEqual(acceptance_report["decision"], "revise")
            self.assertFalse(smoke_gate["ready_for_execution"])


if __name__ == "__main__":
    unittest.main()

