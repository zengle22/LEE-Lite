import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-product-src-to-epic" / "scripts" / "src_to_epic.py"


class SrcToEpicWorkflowTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def make_src_package(self, root: Path, run_id: str, candidate: dict[str, object]) -> Path:
        package_dir = root / "artifacts" / "raw-to-src" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "artifact_type": "src_candidate",
            "workflow_key": "product.raw-to-src",
            "workflow_run_id": run_id,
            "title": candidate["title"],
            "status": "freeze_ready",
            "source_kind": candidate["source_kind"],
            "source_refs": candidate["source_refs"],
        }
        markdown = [
            "---",
            *[f"{key}: {value}" for key, value in frontmatter.items() if not isinstance(value, list)],
            "source_refs:",
            *[f"  - {item}" for item in frontmatter["source_refs"]],
            "---",
            "",
            f"# {candidate['title']}",
            "",
            "## Problem Statement",
            "",
            str(candidate["problem_statement"]),
            "",
        ]
        (package_dir / "src-candidate.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
        (package_dir / "src-candidate.json").write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        payloads = {
            "package-manifest.json": {"status": "freeze_ready", "run_id": run_id},
            "structural-report.json": {"decision": "pass"},
            "source-semantic-findings.json": {"decision": "pass", "summary": "semantic ok"},
            "acceptance-report.json": {"decision": "approve", "summary": "acceptance ok"},
            "result-summary.json": {
                "workflow_key": "product.raw-to-src",
                "recommended_target_skill": "product.src-to-epic",
                "run_id": run_id,
            },
            "proposed-next-actions.json": {"recommended_action": "next_skill"},
            "execution-evidence.json": {"run_id": run_id, "decision": "pass"},
            "supervision-evidence.json": {"run_id": run_id, "decision": "pass"},
        }
        for name, payload in payloads.items():
            (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return package_dir

    def make_revision_request(self, root: Path, run_id: str, source_run_id: str, original_input_path: Path) -> Path:
        revision_request = {
            "workflow_key": "product.src-to-epic",
            "run_id": run_id,
            "source_run_id": source_run_id,
            "decision_type": "revise",
            "decision_reason": "请把 gate revise 上下文显式落盘到 EPIC 约束层，并保持最小补丁而不是整篇重写。",
            "decision_target": "epic_freeze_package",
            "basis_refs": ["epic-review-report.json", "epic-acceptance-report.json"],
            "revision_round": 2,
            "source_gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
            "source_return_job_ref": "artifacts/jobs/waiting-human/src-to-epic-return.json",
            "authoritative_input_ref": f"artifacts/raw-to-src/{source_run_id}",
            "candidate_ref": f"src-to-epic.{run_id}.epic-freeze",
            "original_input_path": str(original_input_path),
            "triggered_by_request_id": f"req-{run_id}-revise",
            "trace": {
                "run_ref": run_id,
                "workflow_key": "product.src-to-epic",
            },
        }
        revision_path = root / "revision-request.json"
        revision_path.write_text(json.dumps(revision_request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return revision_path

    def test_standard_src_stays_single_epic_without_rollout_feat_track(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            candidate = {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": "src-basic",
                "title": "用户权限看板",
                "status": "freeze_ready",
                "source_kind": "product_src",
                "source_refs": ["SRC-100", "REQ-UX-100"],
                "problem_statement": "现有权限配置反馈效率低，运营人员需要统一视图。",
                "target_users": ["运营人员", "产品经理"],
                "trigger_scenarios": ["配置权限策略时", "排查权限异常时"],
                "business_drivers": ["提升权限配置效率并减少误操作。"],
                "key_constraints": ["保留现有审批链。", "不改变现有账号体系。"],
                "in_scope": ["统一权限看板展示。", "权限变更审批入口整合。"],
                "out_of_scope": ["底层账号系统重构。"],
            }
            input_dir = self.make_src_package(repo_root, "src-basic", candidate)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-basic")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            epic = json.loads((artifacts_dir / "epic-freeze.json").read_text(encoding="utf-8"))
            gate_ready_package = json.loads((artifacts_dir / "input" / "gate-ready-package.json").read_text(encoding="utf-8"))
            package_manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(epic["rollout_requirement"]["required"])
            self.assertEqual(epic["rollout_plan"]["required_feat_tracks"], ["foundation"])
            self.assertTrue(epic["business_value_problem"])
            self.assertTrue(epic["actors_and_roles"])
            self.assertTrue(epic["upstream_and_downstream"])
            self.assertTrue(epic["epic_success_criteria"])
            self.assertTrue(epic["product_behavior_slices"])
            self.assertFalse((artifacts_dir / "companion-epic-proposals.json").exists())
            self.assertTrue((artifacts_dir / "_cli" / "epic-freeze-executor-commit.response.json").exists())
            self.assertTrue((artifacts_dir / "_cli" / "gate-submit-handoff.response.json").exists())
            self.assertTrue((repo_root / "artifacts" / "registry" / "src-to-epic-epic-basic-epic-freeze.json").exists())
            self.assertEqual(payload["gate_ready_package_ref"], "artifacts/src-to-epic/epic-basic/input/gate-ready-package.json")
            self.assertTrue(payload["authoritative_handoff_ref"].startswith("artifacts/active/gates/handoffs/"))
            self.assertTrue(payload["gate_pending_ref"].startswith("artifacts/active/gates/pending/"))
            self.assertEqual(gate_ready_package["payload"]["candidate_ref"], "src-to-epic.epic-basic.epic-freeze")
            self.assertEqual(gate_ready_package["payload"]["machine_ssot_ref"], "artifacts/src-to-epic/epic-basic/epic-freeze.json")
            self.assertEqual(package_manifest["gate_ready_package_ref"], payload["gate_ready_package_ref"])
            self.assertEqual(package_manifest["gate_pending_ref"], payload["gate_pending_ref"])
            self.assertTrue((repo_root / payload["authoritative_handoff_ref"]).exists())
            self.assertTrue((repo_root / payload["gate_pending_ref"]).exists())

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_engineering_baseline_src_anchors_bootstrap_axes_without_semantic_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            candidate = {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": "src-engineering-baseline",
                "title": "SRC-003 工程基线与最小可运行骨架",
                "status": "freeze_ready",
                "source_kind": "product_src",
                "source_refs": ["SRC-003", "ADR-001", "ADR-002", "ADR-003"],
                "problem_statement": "需要先冻结 repo layout、apps/api 壳子、apps/miniapp 壳子、compose/postgres、本地 env、db/migrations、/healthz /readyz 与模块边界。",
                "target_users": ["后端工程师", "前端工程师", "DevOps"],
                "trigger_scenarios": ["初始化新仓库承载面时", "准备进入第一条业务功能链时"],
                "business_drivers": ["先冻结最小可运行工程基线，避免后续业务实现继续沿错误目录和运行时边界扩散。"],
                "key_constraints": [
                    "QA/handoff/gate/formal 等语义必须作为 overlay，不得提升为 EPIC 主切片。",
                    "禁止 legacy/src 继续增量扩展。",
                    "必须提供可启动的 apps/api 与 apps/miniapp 骨架。",
                ],
                "in_scope": [
                    "repo layout baseline（业务只进 apps/，legacy/src 不再增量）",
                    "apps/api shell runnable（最小路由 + 分层约束）",
                    "apps/miniapp shell runnable（最小页面与导航）",
                    "local env baseline（compose/postgres/.env.example）",
                    "db migrations discipline（db/migrations 作为唯一 schema 演进通道）",
                    "/healthz 与 /readyz contract（readiness 至少覆盖 DB 可用性）",
                ],
                "out_of_scope": ["不在本 SRC 中展开 handoff/gate/formal 的实现细节。"],
            }
            input_dir = self.make_src_package(repo_root, "src-engineering-baseline", candidate)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-engineering-baseline")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            epic = json.loads((artifacts_dir / "epic-freeze.json").read_text(encoding="utf-8"))
            axis_ids = [item["id"] for item in epic["capability_axes"]]
            slice_ids = [item["id"] for item in epic["product_behavior_slices"]]
            self.assertIn("repo-layout-baseline", axis_ids)
            self.assertIn("api-shell", axis_ids)
            self.assertIn("health-readiness", axis_ids)
            self.assertNotIn("collaboration-loop", axis_ids)
            self.assertNotIn("handoff-formalization", axis_ids)
            self.assertIn("repo-layout-baseline", slice_ids)
            self.assertIn("api-shell", slice_ids)

    def test_governance_runtime_src_keeps_single_epic_with_adoption_e2e_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            candidate = {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": "src-gov",
                "title": "Artifact IO Gateway 与 Path Policy 统一治理",
                "status": "freeze_ready",
                "source_kind": "governance_bridge_src",
                "source_refs": ["SRC-001", "ADR-005"],
                "problem_statement": "现有多个 governed skill 仍在自由读写文件，正式 consumer 也会靠目录扫描消费上下游产物。",
                "target_users": ["skill 作者", "workflow 设计者"],
                "trigger_scenarios": ["producer skill 写正式产物时", "consumer skill 正式读取上游产物时"],
                "business_drivers": ["把共享治理底座收敛为统一能力，并形成真实链路接入与验证闭环。"],
                "key_constraints": [
                    "所有正式写入必须经由 Gateway。",
                    "managed read 必须经由 Gateway -> Registry guard。",
                    "Path Policy 是唯一政策源，不得重新发明等价规则。",
                ],
                "in_scope": ["统一 Gateway / Policy / Registry / Audit 边界。", "为现有 skill 接入和 cross-skill E2E 提供稳定上游。"],
                "out_of_scope": ["直接展开每个 skill 的实现代码。"],
                "bridge_context": {
                    "governance_objects": ["Artifact IO Gateway", "Path Policy", "Artifact Registry", "Workspace Auditor"],
                    "current_failure_modes": ["现有 workflow / skill 各自维护路径与目录规则。", "consumer 仍可能通过目录扫描绕过 formal reference。"],
                    "downstream_inheritance_requirements": ["下游必须保留统一治理边界。", "现有效果需要通过真实 skill 接入与跨 skill E2E 证明。"],
                    "expected_downstream_objects": ["EPIC", "FEAT", "TASK"],
                    "acceptance_impact": ["不能只做底座自测。"],
                },
            }
            input_dir = self.make_src_package(repo_root, "src-gov", candidate)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-gov")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            epic = json.loads((artifacts_dir / "epic-freeze.json").read_text(encoding="utf-8"))
            markdown = (artifacts_dir / "epic-freeze.md").read_text(encoding="utf-8")

            self.assertTrue(epic["rollout_requirement"]["required"])
            self.assertEqual(len(epic["capability_axes"]), 5)
            self.assertTrue(any(item.startswith("产品行为切片：governed skill 接入与 pilot 验证流") for item in epic["scope"]))
            self.assertTrue(any(item.startswith("Cross-cutting capability constraints：") for item in epic["scope"]))
            self.assertIn("adoption_e2e", epic["rollout_plan"]["required_feat_tracks"])
            self.assertTrue(any(item["name"] == "主链候选提交与交接流" for item in epic["product_behavior_slices"]))
            self.assertTrue(any("产品行为切片" in item for item in epic["decomposition_rules"]))
            families = {item["family"] for item in epic["rollout_plan"]["required_feat_families"]}
            self.assertEqual(families, {"skill_onboarding", "migration_cutover", "cross_skill_e2e_validation"})
            self.assertIn("本 EPIC 不要求一次性完成所有现有 governed skill 的全量迁移或全仓 cutover。", epic["non_goals"])
            self.assertIn("本 EPIC 不要求覆盖所有 producer/consumer 组合场景，只要求在下游 FEAT 中显式定义 onboarding 范围、迁移波次和至少一条真实跨 skill pilot 主链。", epic["non_goals"])
            self.assertTrue(any("integration matrix" in item for item in epic["success_metrics"]))
            self.assertTrue(any("真实 producer / consumer 接入后的 handoff / gate / E2E 证据" in item for item in epic["success_metrics"]))
            self.assertIn("workflow / orchestration 设计者", " ".join(actor["role"] for actor in epic["actors_and_roles"]))
            self.assertIn("## Business Value and Problem", markdown)
            self.assertIn("## Product Positioning", markdown)
            self.assertIn("## Actors and Roles", markdown)
            self.assertIn("## Capability Scope", markdown)
            self.assertIn("## Upstream and Downstream", markdown)
            self.assertIn("## Epic Success Criteria", markdown)
            self.assertIn("## Rollout and Adoption", markdown)
            self.assertIn("rollout_required: `true`", markdown)
            self.assertIn("required_feat_tracks: `foundation, adoption_e2e`", markdown)
            self.assertFalse((artifacts_dir / "companion-epic-proposals.json").exists())

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_mainline_bridge_injects_adr005_prerequisite_foundation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            candidate = {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": "src-mainline",
                "title": "LL skill-first 主链统一继承源",
                "status": "freeze_ready",
                "source_kind": "governance_bridge_src",
                "source_refs": ["SRC-MAINLINE-001", "ADR-001", "ADR-003", "ADR-006"],
                "problem_statement": "当前三份 ADR 分散定义了同一条主链的不同侧面，若下游分别理解，会继续在 loop、handoff、gate 与 IO 边界上各自发明等价规则。",
                "target_users": ["workflow 设计者", "governed skill 作者"],
                "trigger_scenarios": ["当下游对象需要继承主链 loop、handoff、gate 与 materialization 边界时。"],
                "business_drivers": ["需要把主链统一收敛为正式继承源，并在后续 skill 接入中验证闭环成立。"],
                "key_constraints": [
                    "双会话双队列闭环",
                    "文件化 handoff runtime",
                    "external gate 独立裁决与物化",
                    "candidate package 与 formal object 强制分层",
                ],
                "in_scope": [
                    "定义主链中 skill 文件读写、artifact 输入输出边界、路径策略与 handoff、gate、formal materialization 的统一治理边界。",
                    "为后续主链对象提供统一继承源与交接依据，不展开实现设计。",
                ],
                "out_of_scope": ["不展开具体 schema、CLI、目录实现。"],
                "bridge_context": {
                    "governance_objects": ["双会话双队列闭环", "文件化 handoff runtime", "external gate 独立裁决与物化", "candidate package 与 formal object 分层"],
                    "current_failure_modes": ["下游分别理解主链边界，会在 loop / handoff / gate / materialization 上继续重写等价规则。"],
                    "downstream_inheritance_requirements": ["下游需求链必须将双会话双队列闭环、文件化 handoff runtime 与 external gate 统一继承。"],
                    "expected_downstream_objects": ["EPIC", "FEAT", "TASK"],
                    "acceptance_impact": ["审计链应能回答谁推进了 candidate、谁做了 final decision、为什么允许推进、正式物化了什么对象。"],
                },
            }
            input_dir = self.make_src_package(repo_root, "src-mainline", candidate)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-mainline")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            epic = json.loads((artifacts_dir / "epic-freeze.json").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-epic-to-feat.json").read_text(encoding="utf-8"))
            markdown = (artifacts_dir / "epic-freeze.md").read_text(encoding="utf-8")

            self.assertIn("ADR-005", epic["source_refs"])
            self.assertIn("ADR-005 是主链文件 IO / 路径治理前置基础；本 EPIC 只消费其已交付能力，不重新实现 Gateway / Path Policy / Registry 模块。", " ".join(item for group in epic["constraint_groups"] for item in group["items"]))

    def test_review_projection_semantic_lock_prevents_governance_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            candidate = {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": "src-adr015",
                "title": "Machine SSOT + Human Review Projection",
                "status": "freeze_ready",
                "source_kind": "governance_bridge_src",
                "source_refs": ["SRC-ADR015", "ADR-015"],
                "semantic_lock": {
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
                        "formal_publication",
                        "governed_io_platform",
                    ],
                    "inheritance_rule": "Projection is derived-only, non-authoritative, non-inheritable.",
                },
                "problem_statement": "Machine SSOT 本体对 AI 足够稳定，但 gate 审核阶段的人类需要一份固定模板的人类友好 Projection 来快速理解产品和边界。",
                "target_users": ["gate reviewer", "SSOT owner"],
                "trigger_scenarios": ["当 Machine SSOT 进入 gate 审核阶段时。"],
                "business_drivers": ["在不污染 SSOT 本体的前提下提升 gate 审核效率。"],
                "key_constraints": ["Projection 只能解释和重组 SSOT，不得新增 authoritative 定义。", "审核意见必须回写 Machine SSOT。"],
                "in_scope": ["在 gate 阶段生成 Human Review Projection。", "提供 Authoritative Snapshot、Review Focus 和回写边界。"],
                "out_of_scope": ["formal publication runtime", "governed IO runtime"],
                "bridge_context": {
                    "governance_objects": ["Machine SSOT", "Human Review Projection", "Authoritative Snapshot"],
                    "current_failure_modes": ["审核人需要自己拼装主线和边界。"],
                    "downstream_inheritance_requirements": ["Projection 不可继承，SSOT 才可继承。"],
                    "expected_downstream_objects": ["EPIC", "FEAT"],
                    "acceptance_impact": ["审核意见必须回写 SSOT。"],
                },
            }
            input_dir = self.make_src_package(repo_root, "src-adr015", candidate)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-adr015")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            epic = json.loads((artifacts_dir / "epic-freeze.json").read_text(encoding="utf-8"))
            drift = json.loads((artifacts_dir / "semantic-drift-check.json").read_text(encoding="utf-8"))

            self.assertEqual(epic["semantic_lock"]["domain_type"], "review_projection_rule")
            self.assertEqual(epic["title"], "Gate 审核投影视图与 SSOT 回写统一能力")
            self.assertEqual([item["id"] for item in epic["product_behavior_slices"]], ["projection-generation", "authoritative-snapshot", "review-focus-risk", "feedback-writeback"])
            self.assertFalse(epic["rollout_requirement"]["required"])
            self.assertTrue(drift["semantic_lock_preserved"])
            self.assertEqual(drift["verdict"], "pass")
            self.assertFalse(drift["forbidden_axis_detected"])
            self.assertTrue(epic["business_value_problem"])
            self.assertTrue(epic["actors_and_roles"])
            self.assertTrue(epic["upstream_and_downstream"])

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_execution_runner_semantic_lock_prevents_formal_publication_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            candidate = {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": "src-adr018",
                "title": "ADR 018 Execution Loop Job Runner 作为自动推进运行时",
                "status": "freeze_ready",
                "source_kind": "governance_bridge_src",
                "source_refs": ["ADR-018", "ADR-001", "ADR-003", "ADR-005"],
                "semantic_lock": {
                    "domain_type": "execution_runner_rule",
                    "one_sentence_truth": "gate approve 后必须生成 ready execution job，并由 Execution Loop Job Runner 自动消费 artifacts/jobs/ready 后推进到下一个 skill，而不是停在 formal publication 或人工接力。",
                    "primary_object": "execution_loop_job_runner",
                    "lifecycle_stage": "post_gate_auto_progression",
                    "allowed_capabilities": [
                        "ready_execution_job_materialization",
                        "ready_queue_consumption",
                        "next_skill_dispatch",
                        "execution_result_recording",
                        "retry_reentry_return",
                    ],
                    "forbidden_capabilities": [
                        "formal_publication_substitution",
                        "admission_only_decomposition",
                        "third_session_human_relay",
                        "directory_guessing_consumer",
                    ],
                    "inheritance_rule": "approve semantics must stay coupled to ready-job emission and runner-driven next-skill progression; downstream may not replace this with formal publication or admission-only flows.",
                },
                "problem_statement": "当前仍缺少一个正式 consumer 去自动消费 artifacts/jobs/ready/ 中的 job，并把它推进到下游 workflow。",
                "target_users": ["workflow / orchestration 设计者", "execution runner owner"],
                "trigger_scenarios": ["当 gate approve 之后需要自动推进到下一个 governed skill 时。"],
                "business_drivers": ["需要把 gate approve 和下一 skill 自动推进重新绑回同一条运行时链。"],
                "key_constraints": [
                    "approve 必须落成 ready execution job。",
                    "runner 必须自动消费 artifacts/jobs/ready。",
                    "不得把 approve 改写成 formal publication。",
                ],
                "in_scope": ["冻结 approve -> ready job -> runner -> next skill -> outcome 这条自动推进链。"],
                "out_of_scope": ["formal publication / admission 产品线", "第三会话人工接力"],
                "bridge_context": {
                    "governance_objects": ["Execution Loop Job Runner", "ready execution job", "artifacts/jobs/ready"],
                    "current_failure_modes": ["approve 后停在 formal publication trigger。", "缺少自动消费 ready job 的正式 runner。"],
                    "downstream_inheritance_requirements": ["下游不得把 approve 后链路改写成 formal publication。"],
                    "expected_downstream_objects": ["EPIC", "FEAT", "TECH", "IMPL", "TESTSET"],
                    "acceptance_impact": ["至少一条 approve -> ready job -> runner -> next skill 链路可被验证。"],
                    "non_goals": ["formal publication / admission 产品线"],
                },
                "operator_surface_inventory": [
                    {"entry_kind": "skill_entry", "name": "Execution Loop Job Runner", "lifecycle_phase": "start", "user_actor": "workflow / orchestration operator"},
                    {"entry_kind": "cli_control_surface", "name": "ll loop run-execution", "lifecycle_phase": "start", "user_actor": "Claude/Codex CLI operator"},
                    {"entry_kind": "cli_control_surface", "name": "ll job claim", "lifecycle_phase": "init", "user_actor": "Claude/Codex CLI operator"},
                    {"entry_kind": "monitor_surface", "name": "runner observability surface", "lifecycle_phase": "monitor", "user_actor": "workflow / orchestration operator"},
                ],
            }
            input_dir = self.make_src_package(repo_root, "src-adr018", candidate)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-adr018")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            epic = json.loads((artifacts_dir / "epic-freeze.json").read_text(encoding="utf-8"))
            drift = json.loads((artifacts_dir / "semantic-drift-check.json").read_text(encoding="utf-8"))
            markdown = (artifacts_dir / "epic-freeze.md").read_text(encoding="utf-8")

            self.assertEqual(epic["semantic_lock"]["domain_type"], "execution_runner_rule")
            self.assertEqual(epic["title"], "Gate 审批后自动推进 Execution Runner 统一能力")
            self.assertEqual(
                [item["id"] for item in epic["product_behavior_slices"]],
                [
                    "ready-job-emission",
                    "runner-operator-entry",
                    "runner-control-surface",
                    "execution-runner-intake",
                    "next-skill-dispatch",
                    "execution-result-feedback",
                    "runner-observability-surface",
                ],
            )
            self.assertEqual(
                [item["id"] for item in epic["capability_axes"]],
                [
                    "ready-job-emission",
                    "runner-operator-entry",
                    "runner-control-surface",
                    "execution-runner-intake",
                    "next-skill-dispatch",
                    "execution-result-feedback",
                    "runner-observability-surface",
                ],
            )
            self.assertEqual(drift["verdict"], "pass")
            self.assertTrue(drift["semantic_lock_preserved"])
            self.assertNotIn("formal 发布与下游准入流", markdown)
            self.assertIn("批准后 Ready Job 生成流", markdown)
            self.assertIn("Runner 用户入口流", markdown)
            self.assertIn("Runner 控制面流", markdown)
            self.assertIn("Execution Runner 自动取件流", markdown)
            self.assertIn("Runner 运行监控流", markdown)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_architecture_ref_is_added_when_matching_architecture_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "ssot" / "architecture").mkdir(parents=True, exist_ok=True)
            (repo_root / "ssot" / "architecture" / "ARCH-SRC-001-001__managed-artifact-io-governance-architecture-overview.md").write_text(
                "# Architecture\n",
                encoding="utf-8",
            )
            candidate = {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": "src-arch",
                "title": "Artifact IO Gateway 与 Path Policy 统一治理",
                "status": "freeze_ready",
                "source_kind": "governance_bridge_src",
                "source_refs": ["SRC-001", "ADR-005"],
                "problem_statement": "现有多个 governed skill 仍在自由读写文件，正式 consumer 也会靠目录扫描消费上下游产物。",
                "target_users": ["skill 作者", "workflow 设计者"],
                "trigger_scenarios": ["producer skill 写正式产物时", "consumer skill 正式读取上游产物时"],
                "business_drivers": ["把共享治理底座收敛为统一能力，并形成真实链路接入与验证闭环。"],
                "key_constraints": ["所有正式写入必须经由 Gateway。"],
                "in_scope": ["统一 Gateway / Policy / Registry / Audit 边界。", "为现有 skill 接入和 cross-skill E2E 提供稳定上游。"],
                "out_of_scope": ["直接展开每个 skill 的实现代码。"],
                "src_root_id": "SRC-001",
                "bridge_context": {
                    "governance_objects": ["Artifact IO Gateway"],
                    "current_failure_modes": ["consumer 仍可能通过目录扫描绕过 formal reference。"],
                    "downstream_inheritance_requirements": ["现有效果需要通过真实 skill 接入与跨 skill E2E 证明。"],
                    "expected_downstream_objects": ["EPIC", "FEAT", "TASK"],
                    "acceptance_impact": ["不能只做底座自测。"],
                },
            }
            input_dir = self.make_src_package(repo_root, "src-arch", candidate)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-arch")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            epic = json.loads((artifacts_dir / "epic-freeze.json").read_text(encoding="utf-8"))
            self.assertIn("ARCH-SRC-001-001", epic["source_refs"])

    def test_governance_bridge_epic_demotes_qa_object_rules_to_inherited_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            candidate = {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": "src-adr007",
                "title": "ADR-007 QA Test Execution Governed Skill 标准方案",
                "status": "freeze_ready",
                "source_kind": "governance_bridge_src",
                "source_refs": ["SRC-ADR007", "ADR-007"],
                "problem_statement": "当前 test execution 相关治理已形成上游对象模型，但下游 EPIC 容易继续围绕 QA 对象级细节拆分，导致主链治理边界被打平。",
                "target_users": ["workflow 设计者", "skill 作者", "reviewer"],
                "trigger_scenarios": ["把 ADR-007 继续下传到 epic-to-feat 时", "需要在主链层统一 handoff、gate 与 formal materialization 时"],
                "business_drivers": ["把 QA execution 源约束收敛为可复用的主链治理闭环，而不是继续平移源对象。"],
                "key_constraints": [
                    "必须保留 TestEnvironmentSpec contract。",
                    "必须保留 TestCasePack / ScriptPack freeze 与 revision 语义。",
                    "必须保留 skill.qa.test_exec_web_e2e 与 skill.runner.test_e2e 的 authoritative source refs。",
                    "必须保留 invalid_run / acceptance_status 等状态语义。",
                ],
                "in_scope": ["定义 QA test execution governed skill 的对象模型、状态语义、冻结链、证据规则与下游继承边界。"],
                "out_of_scope": ["直接展开 runner 脚本实现。"],
                "bridge_context": {
                    "governance_objects": ["loop / handoff / gate 协作", "candidate -> formal materialization", "对象分层与准入", "主链 IO 与路径边界"],
                    "current_failure_modes": ["EPIC 标题已升维，但约束主体仍停留在 QA execution 对象层。", "能力轴与 rollout families 主次不清。"],
                    "downstream_inheritance_requirements": ["下游 FEAT 不得改写上游对象语义。", "源对象级规则仅能作为 inherited authoritative constraints 保留。"],
                    "expected_downstream_objects": ["EPIC", "FEAT", "TASK"],
                    "acceptance_impact": ["EPIC 必须给出 pilot chain、materialization、adoption/cutover/fallback 完成定义。"],
                },
            }
            input_dir = self.make_src_package(repo_root, "src-adr007", candidate)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-adr007")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            epic = json.loads((artifacts_dir / "epic-freeze.json").read_text(encoding="utf-8"))
            markdown = (artifacts_dir / "epic-freeze.md").read_text(encoding="utf-8")

            self.assertIn("统一上位产品能力：形成一条可被多 skill 共享继承的主链受治理交接闭环。", epic["scope"])
            self.assertTrue(any(item.startswith("产品行为切片：formal 发布与下游准入流") for item in epic["scope"]))
            self.assertTrue(any("产品行为切片" in item for item in epic["decomposition_rules"]))
            self.assertTrue(any("cross-cutting constraints" in item for item in epic["decomposition_rules"]))
            self.assertTrue(any("mandatory overlays" in item for item in epic["decomposition_rules"]))
            self.assertTrue(any("producer -> consumer -> audit -> gate" in item for item in epic["success_metrics"]))
            self.assertTrue(any("formal publish" in item for item in epic["success_metrics"]))
            self.assertTrue(any("adoption / cutover / fallback" in item for item in epic["success_metrics"]))

            group_map = {group["name"]: group["items"] for group in epic["constraint_groups"]}
            self.assertEqual(set(group_map), {"Epic-level constraints", "Authoritative inherited constraints", "Downstream preservation rules"})
            epic_level = " ".join(group_map["Epic-level constraints"])
            inherited = " ".join(group_map["Authoritative inherited constraints"])
            for label in ["QA test execution skill", "TestEnvironmentSpec", "TestCasePack 冻结", "ScriptPack 冻结", "合规与判定分层"]:
                self.assertNotIn(label, group_map["Authoritative inherited constraints"])
            for marker in ["TestEnvironmentSpec", "TestCasePack", "ScriptPack", "skill.qa.test_exec_web_e2e", "skill.runner.test_e2e", "invalid_run", "acceptance_status"]:
                self.assertNotIn(marker, epic_level)
                self.assertIn(marker, inherited)

            self.assertIn("### Epic-level constraints", markdown)
            self.assertIn("### Authoritative inherited constraints", markdown)
            self.assertIn("### Downstream preservation rules", markdown)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_revision_request_rerun_materializes_revision_trace_and_updates_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            candidate = {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": "src-revise",
                "title": "ADR-007 QA Test Execution Governed Skill 标准方案",
                "status": "freeze_ready",
                "source_kind": "governance_bridge_src",
                "source_refs": ["SRC-ADR007", "ADR-007"],
                "problem_statement": "当前 test execution 相关治理已形成上游对象模型，但下游 EPIC 容易继续围绕 QA 对象级细节拆分，导致主链治理边界被打平。",
                "target_users": ["workflow 设计者", "skill 作者", "reviewer"],
                "trigger_scenarios": ["把 ADR-007 继续下传到 epic-to-feat 时", "需要在主链层统一 handoff、gate 与 formal materialization 时"],
                "business_drivers": ["把 QA execution 源约束收敛为可复用的主链治理闭环，而不是继续平移源对象。"],
                "key_constraints": [
                    "必须保留 TestEnvironmentSpec contract。",
                    "必须保留 TestCasePack / ScriptPack freeze 与 revision 语义。",
                    "必须保留 skill.qa.test_exec_web_e2e 与 skill.runner.test_e2e 的 authoritative source refs。",
                    "必须保留 invalid_run / acceptance_status 等状态语义。",
                ],
                "in_scope": ["定义 QA test execution governed skill 的对象模型、状态语义、冻结链、证据规则与下游继承边界。"],
                "out_of_scope": ["直接展开 runner 脚本实现。"],
                "bridge_context": {
                    "governance_objects": ["loop / handoff / gate 协作", "candidate -> formal materialization", "对象分层与准入", "主链 IO 与路径边界"],
                    "current_failure_modes": ["EPIC 标题已升维，但约束主体仍停留在 QA execution 对象层。", "能力轴与 rollout families 主次不清。"],
                    "downstream_inheritance_requirements": ["下游 FEAT 不得改写上游对象语义。", "源对象级规则仅能作为 inherited authoritative constraints 保留。"],
                    "expected_downstream_objects": ["EPIC", "FEAT", "TASK"],
                    "acceptance_impact": ["EPIC 必须给出 pilot chain、materialization、adoption/cutover/fallback 完成定义。"],
                },
            }
            input_dir = self.make_src_package(repo_root, "src-revise", candidate)
            initial = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-revise")
            self.assertEqual(initial.returncode, 0, initial.stderr)
            artifacts_dir = Path(json.loads(initial.stdout)["artifacts_dir"])
            revision_path = self.make_revision_request(repo_root, "epic-revise", "src-revise", input_dir)

            rerun = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "epic-revise",
                "--allow-update",
                "--revision-request",
                str(revision_path),
            )
            self.assertEqual(rerun.returncode, 0, rerun.stderr)

            epic = json.loads((artifacts_dir / "epic-freeze.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            execution = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            gate = json.loads((artifacts_dir / "epic-freeze-gate.json").read_text(encoding="utf-8"))
            markdown = (artifacts_dir / "epic-freeze.md").read_text(encoding="utf-8")
            revision_ref = str(artifacts_dir / "revision-request.json")
            group_map = {group["name"]: group["items"] for group in epic["constraint_groups"]}

            self.assertEqual(epic["revision_request_ref"], revision_ref)
            self.assertEqual(manifest["revision_request_ref"], revision_ref)
            self.assertEqual(execution["revision_request_ref"], revision_ref)
            self.assertEqual(supervision["revision_request_ref"], revision_ref)
            self.assertEqual(gate["revision_request_ref"], revision_ref)
            self.assertTrue(any("Gate revise:" in item for item in group_map["Authoritative inherited constraints"]))
            self.assertIn("Gate revise:", markdown)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)


if __name__ == "__main__":
    unittest.main()
