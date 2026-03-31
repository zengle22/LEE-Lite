import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.unit.support_feat_to_tech import FeatToTechWorkflowHarness

SCRIPT_ROOT = Path(__file__).resolve().parents[2] / "skills" / "ll-dev-feat-to-tech" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from feat_to_tech_common import derive_semantic_lock
from feat_to_tech_derivation import feature_axis
from feat_to_tech_package_builder import build_defects, build_semantic_drift_check

class FeatToTechWorkflowTests(FeatToTechWorkflowHarness):
    def _json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def _run_feat(self, repo_root: Path, feature: dict[str, object], input_run_id: str, tech_run_id: str):
        bundle = self.make_bundle_json(feature, run_id=input_run_id)
        if isinstance(feature.get("semantic_lock"), dict): bundle["semantic_lock"] = feature["semantic_lock"]
        input_dir = self.make_feat_package(repo_root, input_run_id, bundle)
        result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", str(feature["feat_ref"]), "--repo-root", str(repo_root), "--run-id", tech_run_id)
        return result, repo_root / "artifacts" / "feat-to-tech" / tech_run_id

    def _minimal_onboarding_feature(self, feat_ref: str, **overrides: object) -> dict[str, object]:
        feature: dict[str, object] = {
            "feat_ref": feat_ref,
            "title": "最小建档主链能力",
            "axis_id": "minimal-onboarding-flow",
            "track": "foundation",
            "goal": "把首进链路收敛到最小建档页并在提交后立即放行首页。",
            "scope": ["登录/注册完成后，未完成最小建档的用户进入单页最小建档页。", "最小建档页必须稳定收集 gender、birthdate、height、weight、running_level、recent_injury_status。", "用户提交最小建档后立即允许进入首页，设备连接保持后置，不阻塞首进链路。"],
            "constraints": ["最小建档必须维持单页完成，不拆成多步向导。", "birthdate 是 canonical 年龄相关字段，不能用自由推测字段替代。", "device connection 只能作为 deferred follow-up entry，不能重新变成 blocking prerequisite。"],
            "dependencies": ["Boundary to auth: 登录/注册已经完成。", "Boundary to homepage: 首页内容本身不在本 FEAT 内。"],
            "outputs": ["minimal profile completion", "homepage entry allowance"],
            "acceptance_checks": [{"scenario": "Minimal profile submit allows homepage entry", "given": "required fields valid", "when": "submit minimal profile", "then": "profile_minimal_done and homepage entry allowed"}, {"scenario": "Device connection remains deferred", "given": "minimal profile submit succeeds", "when": "home is entered", "then": "device connection is follow-up only"}, {"scenario": "Invalid required fields stay on the page", "given": "birthdate or required fields invalid", "when": "submit is attempted", "then": "field-level errors are returned and homepage entry stays blocked"}],
            "source_refs": [feat_ref, "EPIC-SRC-001-001", "SRC-001"],
        }
        feature.update(overrides)
        if feature.get("axis_id") is None:
            feature.pop("axis_id", None)
        return feature

    def _adoption_e2e_feature(self, feat_ref: str, **overrides: object) -> dict[str, object]:
        feature: dict[str, object] = {
            "feat_ref": feat_ref,
            "title": "governed skill 接入与 pilot 闭环流",
            "axis_id": "skill-adoption-e2e",
            "goal": "让新 skill 能按 onboarding、pilot、cutover/fallback 的主链接入流程稳定落地。",
            "scope": ["定义 onboarding directive、pilot evidence 与 cutover guard 的业务交付物。", "定义 producer -> gate -> formal -> consumer -> audit 的最小 pilot 闭环。", "定义 compat mode、fallback 与 cutover 的业务边界。"],
            "constraints": ["本 FEAT 不重写 foundation FEAT 的内部实现。", "pilot evidence 必须成为 authoritative rollout input。", "fallback 结果必须显式记录到 receipt。"],
            "dependencies": ["Boundary to formal 发布与下游准入流: pilot 只能消费已发布 formal refs。", "Boundary to 主链候选提交与交接流: producer 提交仍沿 authoritative handoff 进入 gate pending。"],
            "outputs": ["onboarding directive", "pilot evidence submission", "cutover recommendation"],
            "acceptance_checks": [{"scenario": "Pilot chain is complete", "given": "producer to audit", "when": "validated", "then": "闭环证据齐全"}, {"scenario": "Fallback is explicit", "given": "pilot failure", "when": "cutover reviewed", "then": "fallback outcome 被记录"}, {"scenario": "Compat mode is frozen", "given": "legacy skill", "when": "onboarded", "then": "compat mode 明确可追踪"}],
            "source_refs": [feat_ref, "EPIC-SRC-001-001", "SRC-001"],
        }
        feature.update(overrides)
        return feature

    def _first_ai_advice_feature(self, feat_ref: str, **overrides: object) -> dict[str, object]:
        feature: dict[str, object] = {
            "feat_ref": feat_ref,
            "title": "首轮 AI 建议释放能力",
            "axis_id": "first-ai-advice-release",
            "track": "foundation",
            "goal": "在最小建档完成后，基于最低必要输入释放首轮训练建议，并对缺失风险输入 fail closed。",
            "scope": [
                "读取最小建档结果与首轮建议最低输入。",
                "基于 running_level 和 recent_injury_status 执行风险门槛判断。",
                "在首页释放最小可用的首轮建议与补充提示。",
            ],
            "constraints": [
                "缺失 risk gate 关键字段时不得放行正常建议分支。",
                "不要求扩展画像或设备连接先完成。",
                "首页可见性与建议生成必须围绕 canonical 最小输入展开。",
            ],
            "dependencies": [
                "Boundary to 最小建档主链: 只消费 profile_minimal_done 和 canonical minimal profile fields。",
                "Boundary to 扩展画像: 补全任务卡与增量保存不在本 FEAT 内。",
            ],
            "outputs": ["first advice payload", "risk gate decision", "homepage advice visibility"],
            "acceptance_checks": [
                {"scenario": "Advice is released after minimal profile completion", "given": "minimal profile is done and risk inputs are present", "when": "homepage opens", "then": "first advice becomes visible"},
                {"scenario": "Missing risk inputs block normal advice", "given": "running_level or recent_injury_status missing", "when": "advice generation is attempted", "then": "normal advice branch is blocked and a completion prompt is shown"},
                {"scenario": "First advice keeps minimum output contract", "given": "safe minimum inputs", "when": "first advice is generated", "then": "training advice level and first week action are present"},
            ],
            "source_refs": [feat_ref, "EPIC-SRC-001-001", "SRC-001"],
        }
        feature.update(overrides)
        return feature

    def _extended_profile_completion_feature(self, feat_ref: str, **overrides: object) -> dict[str, object]:
        feature: dict[str, object] = {
            "feat_ref": feat_ref,
            "title": "扩展画像渐进补全能力",
            "axis_id": "extended-profile-progressive-completion",
            "track": "foundation",
            "goal": "让用户在首页通过任务卡渐进补全扩展画像，并通过增量保存持续更新完成度。",
            "scope": [
                "在首页渲染扩展画像任务卡与下一步补全项。",
                "支持分步 patch 保存与完成度刷新。",
                "保存失败时保留首页可用与重试入口。",
            ],
            "constraints": [
                "不能把扩展画像补全重新拉回首进阻塞链路。",
                "patch 保存必须是 incremental，而不是整页重提交流程。",
                "保存失败不得撤销 homepage_entered。",
            ],
            "dependencies": [
                "Boundary to 首页 shell: 只依赖首页容器承载任务卡，不定义首页其他内容。",
                "Boundary to 最小建档: 最小建档完成态仍由上游主链负责。",
            ],
            "outputs": ["profile completion tasks", "extended profile patch result", "completion projection"],
            "acceptance_checks": [
                {"scenario": "Task cards guide progressive completion", "given": "homepage entered", "when": "tasks are loaded", "then": "user sees next profile completion tasks"},
                {"scenario": "Incremental save updates completion", "given": "patch fields are valid", "when": "user saves a task", "then": "completion percent and next task cards refresh"},
                {"scenario": "Save failure keeps homepage usable", "given": "patch persistence fails", "when": "save returns", "then": "homepage remains usable and retry entry stays visible"},
            ],
            "source_refs": [feat_ref, "EPIC-SRC-001-001", "SRC-001"],
        }
        feature.update(overrides)
        return feature

    def _device_deferred_entry_feature(self, feat_ref: str, **overrides: object) -> dict[str, object]:
        feature: dict[str, object] = {
            "feat_ref": feat_ref,
            "title": "设备连接后置增强能力",
            "axis_id": "device-connect-deferred-entry",
            "track": "foundation",
            "goal": "把设备连接固定为首页后的增强入口，允许跳过，并保证失败不影响主链可用性。",
            "scope": [
                "在首页暴露后置设备连接入口与跳过动作。",
                "定义 deferred start/finalize 连接流程与结果状态。",
                "把连接结果限制在体验增强分支。",
            ],
            "constraints": [
                "设备连接不可成为首页进入或首轮建议释放前置。",
                "连接失败必须是 non-blocking。",
                "设备数据不得覆盖最小建档 canonical 事实。",
            ],
            "dependencies": [
                "Boundary to 首页主链: 只消费 homepage_entered 前置，不改写主链放行逻辑。",
                "Boundary to 设备厂商接入: 厂商协议细节不在本 FEAT 内。",
            ],
            "outputs": ["deferred device connection status", "enhancement readiness", "retry or skip entry"],
            "acceptance_checks": [
                {"scenario": "Deferred entry stays skippable", "given": "homepage entered", "when": "device entry is shown", "then": "user can skip without losing homepage access"},
                {"scenario": "Connection failure is non-blocking", "given": "device auth or sync fails", "when": "connection finalizes", "then": "homepage and first advice remain available"},
                {"scenario": "Connected data only enhances experience", "given": "device connection succeeds", "when": "data arrives", "then": "enhancement becomes available without rewriting canonical onboarding facts"},
            ],
            "source_refs": [feat_ref, "EPIC-SRC-001-001", "SRC-001"],
        }
        feature.update(overrides)
        return feature

    def _state_profile_boundary_feature(self, feat_ref: str, **overrides: object) -> dict[str, object]:
        feature: dict[str, object] = {
            "feat_ref": feat_ref,
            "title": "状态模型与存储边界统一能力",
            "axis_id": "state-and-profile-boundary-alignment",
            "track": "foundation",
            "goal": "统一 primary_state、capability_flags 和 canonical profile 边界，确保完成态与资格判断只读唯一事实源。",
            "scope": [
                "定义 onboarding primary_state 与 capability_flags 的持久化边界。",
                "定义 user_physical_profile 与 runner_profiles 的 canonical ownership。",
                "定义统一读取层和冲突阻断策略。",
            ],
            "constraints": [
                "身体字段冲突时 user_physical_profile 必须是唯一事实源。",
                "completion 和 eligibility 判断不得依赖 derived age 或旁路 store。",
                "跨边界冲突写入必须 fail closed。",
            ],
            "dependencies": [
                "Boundary to 页面层: 页面局部态不承担业务完成态权威。",
                "Boundary to 下游 runtime: 下游只允许读 unified onboarding state。",
            ],
            "outputs": ["primary state record", "canonical physical profile write", "unified onboarding state"],
            "acceptance_checks": [
                {"scenario": "Primary state and flags are explicit", "given": "onboarding progresses", "when": "state is written", "then": "primary_state and capability_flags remain distinct"},
                {"scenario": "Canonical profile boundary is enforced", "given": "body field writes conflict", "when": "boundary is evaluated", "then": "non-canonical write is blocked"},
                {"scenario": "Unified reader fails closed on conflicts", "given": "unresolved cross-boundary conflict", "when": "state is read", "then": "conflict_blocked is returned and downstream gating stops"},
            ],
            "source_refs": [feat_ref, "EPIC-SRC-001-001", "SRC-001"],
        }
        feature.update(overrides)
        return feature

    def test_run_emits_tech_and_optional_arch_api_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-001",
                "title": "主链协作闭环能力",
                "goal": "让 execution、gate、human loops 在主链中形成稳定协作闭环。",
                "scope": [
                    "定义 execution loop 与 gate loop 的 handoff object。",
                    "定义 proposal 与 decision 的回流条件。",
                    "显式约束 queue、handoff、gate 的协作边界。",
                ],
                "constraints": [
                    "保留双会话双队列闭环。",
                    "保留结构化文件对象协作。",
                    "下游不得重造 handoff 规则。",
                    "loop 协作必须显式说明触发 gate 的对象。",
                ],
                "dependencies": [
                    "Boundary to 对象分层与准入能力：consumer/provider admission 由分层 FEAT 决定。",
                    "Boundary to 正式交接与物化能力：formalization decision 不在本 FEAT 内。",
                ],
                "outputs": [
                    "handoff contract",
                    "proposal object",
                    "decision object",
                ],
                "acceptance_checks": [
                    {"scenario": "Loop responsibility split is explicit", "given": "mainline loop", "when": "reviewed", "then": "明确 queue/handoff/gate 边界"},
                    {"scenario": "Loop re-entry conditions are bounded", "given": "revise", "when": "re-enter", "then": "明确 proposal 与 decision 回流"},
                    {"scenario": "Downstream flows do not redefine collaboration rules", "given": "consumer/provider", "when": "handoff", "then": "不得重造并行 contract"},
                ],
                "source_refs": ["FEAT-SRC-001-001", "EPIC-SRC-001-001", "SRC-001", "ARCH-SRC-001-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-required")
            input_dir = self.make_feat_package(repo_root, "feat-required", bundle)
            artifacts_dir = self.run_tech_flow(repo_root, input_dir, "FEAT-SRC-001-001", "tech-required")
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            gate_ready_package = json.loads((artifacts_dir / "input" / "gate-ready-package.json").read_text(encoding="utf-8"))
            bundle_md = (artifacts_dir / "tech-design-bundle.md").read_text(encoding="utf-8")
            tech_md = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")
            arch_md = (artifacts_dir / "arch-design.md").read_text(encoding="utf-8")
            api_md = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")
            executor_cli = json.loads(
                (artifacts_dir / "_cli" / "tech-design-bundle-executor-commit.response.json").read_text(encoding="utf-8")
            )
            supervisor_cli = json.loads(
                (artifacts_dir / "_cli" / "tech-design-bundle-supervisor-commit.response.json").read_text(encoding="utf-8")
            )
            execution = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))

            self.assertTrue((artifacts_dir / "tech-spec.md").exists())
            self.assertFalse((artifacts_dir / "tech-impl.md").exists())
            self.assertTrue((artifacts_dir / "arch-design.md").exists())
            self.assertTrue((artifacts_dir / "api-contract.md").exists())
            self.assertEqual(design["workflow_key"], "dev.feat-to-tech")
            self.assertTrue(design["arch_required"])
            self.assertTrue(design["api_required"])
            self.assertEqual(design["downstream_handoff"]["target_workflow"], "workflow.dev.tech_to_impl")
            self.assertTrue(design["design_consistency_check"]["passed"])
            self.assertTrue(design["design_consistency_check"]["structural_passed"])
            self.assertTrue(design["design_consistency_check"]["semantic_passed"])
            self.assertTrue(design["design_consistency_check"]["minor_open_items"])
            self.assertIn("### Implementation Unit Mapping", bundle_md)
            self.assertIn("### Implementation Carrier View", bundle_md)
            self.assertIn("### State Model", bundle_md)
            self.assertIn("### Main Sequence", bundle_md)
            self.assertGreaterEqual(bundle_md.count("```text"), 2)
            self.assertNotIn("```mermaid", bundle_md)
            self.assertIn("- arch_ref:", bundle_md)
            self.assertIn("- api_ref:", bundle_md)
            self.assertIn("- minor_open_items:", bundle_md)
            self.assertNotIn("### Boundary Placement", bundle_md)
            self.assertNotIn("### Command Contracts", bundle_md)
            self.assertIn("## Implementation Carrier View", tech_md)
            self.assertIn("## Interface Contracts", tech_md)
            self.assertIn("## Minimal Code Skeleton", tech_md)
            self.assertIn("cli/lib/mainline_runtime.py", tech_md)
            self.assertIn("DecisionReturnEnvelope", tech_md)
            self.assertIn("## System Topology", arch_md)
            self.assertIn("## Dedicated Runtime Placement", arch_md)
            self.assertIn("decision-driven runtime re-entry routing", arch_md)
            self.assertIn("## Contract Scope", api_md)
            self.assertIn("## Response Envelope", api_md)
            self.assertIn("## Command Contracts", api_md)
            self.assertIn("ll gate submit-handoff", api_md)
            self.assertIn("ll gate show-pending", api_md)
            self.assertNotIn("ll gate evaluate", api_md)
            self.assertIn("pending_state ∈ {gate_pending, human_review_pending, reentry_pending, retry_pending}", api_md)
            self.assertIn("gate_pending_ref", api_md)
            self.assertIn("Idempotency key: `producer_ref + proposal_ref + payload_digest`", api_md)
            self.assertIn("arch-design.md", design["downstream_handoff"]["supporting_artifact_refs"])
            self.assertIn("api-contract.md", design["downstream_handoff"]["supporting_artifact_refs"])
            self.assertNotIn("tech-impl.md", design["downstream_handoff"]["supporting_artifact_refs"])
            self.assertEqual(executor_cli["status_code"], "OK")
            self.assertEqual(supervisor_cli["status_code"], "OK")
            self.assertEqual(
                executor_cli["data"]["canonical_path"],
                "artifacts/feat-to-tech/tech-required/tech-design-bundle.md",
            )
            self.assertTrue((repo_root / executor_cli["data"]["receipt_ref"]).exists())
            self.assertTrue((repo_root / executor_cli["data"]["registry_record_ref"]).exists())
            self.assertEqual(
                execution["structural_results"]["cli_executor_commit_ref"],
                str(artifacts_dir / "_cli" / "tech-design-bundle-executor-commit.response.json"),
            )
            self.assertEqual(manifest["cli_executor_commit_ref"], str(artifacts_dir / "_cli" / "tech-design-bundle-executor-commit.response.json"))
            self.assertEqual(manifest["cli_supervisor_commit_ref"], str(artifacts_dir / "_cli" / "tech-design-bundle-supervisor-commit.response.json"))
            self.assertEqual(manifest["tech_spec_ref"], str(artifacts_dir / "tech-spec.md"))
            self.assertNotIn("tech_impl_ref", manifest)
            self.assertEqual(manifest["gate_ready_package_ref"], "artifacts/feat-to-tech/tech-required/input/gate-ready-package.json")
            self.assertTrue(manifest["authoritative_handoff_ref"].startswith("artifacts/active/gates/handoffs/"))
            self.assertTrue(manifest["gate_pending_ref"].startswith("artifacts/active/gates/pending/"))
            self.assertEqual(gate_ready_package["payload"]["candidate_ref"], "feat-to-tech.tech-required.tech-design-bundle")
            self.assertEqual(gate_ready_package["payload"]["machine_ssot_ref"], "artifacts/feat-to-tech/tech-required/tech-design-bundle.json")
            self.assertTrue((repo_root / manifest["authoritative_handoff_ref"]).exists())
            self.assertTrue((repo_root / manifest["gate_pending_ref"]).exists())

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

    def test_run_emits_tech_only_when_no_optional_artifacts_are_needed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-002",
                "title": "配置页文案统一能力",
                "goal": "统一配置页文案，不改变系统边界或接口契约。",
                "scope": [
                    "统一页面标题文案。",
                    "统一帮助提示文案。",
                    "统一成功与失败状态提示文案。",
                ],
                "constraints": [
                    "不改变接口结构。",
                    "不新增跨模块 contract。",
                    "不改变模块边界。",
                    "只做现有页面文案收口。",
                ],
                "dependencies": [],
                "outputs": ["page copy update"],
                "acceptance_checks": [
                    {"scenario": "Title copy is consistent", "given": "配置页", "when": "查看标题", "then": "标题文案统一"},
                    {"scenario": "Help text is consistent", "given": "帮助提示", "when": "查看提示", "then": "帮助文案统一"},
                    {"scenario": "Status copy is consistent", "given": "成功失败提示", "when": "触发状态", "then": "状态文案统一"},
                ],
                "source_refs": ["FEAT-SRC-001-002", "EPIC-SRC-001-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-tech-only")
            input_dir = self.make_feat_package(repo_root, "feat-tech-only", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-002", "--repo-root", str(repo_root), "--run-id", "tech-only")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))

            self.assertTrue((artifacts_dir / "tech-spec.md").exists())
            self.assertFalse((artifacts_dir / "tech-impl.md").exists())
            self.assertFalse((artifacts_dir / "arch-design.md").exists())
            self.assertFalse((artifacts_dir / "api-contract.md").exists())
            self.assertFalse(design["arch_required"])
            self.assertFalse(design["api_required"])
            self.assertIsNone(design["artifact_refs"]["arch_spec"])
            self.assertIsNone(design["artifact_refs"]["api_spec"])
            self.assertEqual(design["artifact_refs"]["tech_spec"], "tech-spec.md")

    def test_revision_request_rerun_persists_revision_context_and_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-REVISION",
                "title": "回流修订感知 TECH 流",
                "goal": "验证 allow-update 复跑时会吸收 revision request 并保留 lineage。",
                "scope": [
                    "将 revision request 物化到 artifacts 目录。",
                    "把 revision summary 吸收到 TECH constraints。",
                    "让 manifest 与 evidence 记录 revision lineage。",
                ],
                "constraints": [
                    "不得重写整份 TECH 设计。",
                    "只能做最小约束补丁。",
                    "必须支持同 run_id allow-update 复跑。",
                ],
                "dependencies": [
                    "上游 feat_freeze_package 已可 freeze。",
                ],
                "outputs": ["revision-aware tech candidate"],
                "acceptance_checks": [
                    {"scenario": "revision request is materialized", "given": "rerun input", "when": "invoke run with revision request", "then": "revision-request.json 会写入 artifacts"},
                    {"scenario": "constraints absorb revision", "given": "revision request", "when": "build tech design", "then": "implementation_rules 会保留 revision summary"},
                    {"scenario": "lineage is visible", "given": "manifest and evidence", "when": "inspect outputs", "then": "revision_request_ref 可追溯"},
                ],
                "source_refs": ["FEAT-SRC-001-REVISION", "EPIC-SRC-001-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-tech-revision-input")
            input_dir = self.make_feat_package(repo_root, "feat-tech-revision-input", bundle)

            initial = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-REVISION", "--repo-root", str(repo_root), "--run-id", "tech-revision")
            self.assertEqual(initial.returncode, 0, initial.stderr)
            artifacts_dir = Path(json.loads(initial.stdout)["artifacts_dir"])

            revision_request = {
                "workflow_key": "dev.feat-to-tech",
                "run_id": "tech-revision",
                "source_run_id": "feat-tech-revision-input",
                "decision_type": "revise",
                "decision_target": "implementation_rules",
                "decision_reason": "Add the minimal recovery guardrail before freeze.",
                "revision_round": 2,
                "source_gate_decision_ref": "artifacts/gate-human-orchestrator/revision-decision.json",
                "source_return_job_ref": "artifacts/jobs/waiting-human/tech-revision-return.json",
                "authoritative_input_ref": "artifacts/epic-to-feat/feat-tech-revision-input/feat-freeze-package.json",
            }
            revision_request_path = repo_root / "revision-request.json"
            revision_request_path.write_text(json.dumps(revision_request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            rerun = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-SRC-001-REVISION",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "tech-revision",
                "--allow-update",
                "--revision-request",
                str(revision_request_path),
            )
            self.assertEqual(rerun.returncode, 0, rerun.stderr)

            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            execution = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            freeze_gate = json.loads((artifacts_dir / "tech-freeze-gate.json").read_text(encoding="utf-8"))
            revision_materialized = json.loads((artifacts_dir / "revision-request.json").read_text(encoding="utf-8"))

            self.assertEqual(revision_materialized["decision_reason"], revision_request["decision_reason"])
            self.assertEqual(design["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertEqual(manifest["revision_request_ref"], "revision-request.json")
            self.assertEqual(execution["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertEqual(supervision["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertEqual(freeze_gate["revision_context"]["revision_request_ref"], "revision-request.json")
            self.assertTrue(
                any("Revision constraint:" in item and revision_request["decision_reason"] in item for item in design["tech_design"]["implementation_rules"])
            )
            self.assertTrue(any("Applied revision context:" in item for item in execution["key_decisions"]))
            self.assertTrue((artifacts_dir / "evidence-report.md").read_text(encoding="utf-8").find("revision_request_ref: revision-request.json") >= 0)

    def test_io_path_governance_feat_emits_api_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-004",
                "title": "主链文件 IO 与路径治理能力",
                "goal": "让主链中的 artifact IO、路径与目录边界稳定接入受治理基础，不扩展为全局文件治理总方案。",
                "scope": [
                    "定义主链 handoff、formal materialization 与 governed skill IO 如何接入受治理 path / mode 能力。",
                    "明确哪些 IO 是受治理主链 IO，哪些属于全局文件治理而必须留在本 FEAT 之外。",
                    "要求所有正式主链写入都遵循统一的路径与覆盖边界，不允许以局部临时目录策略替代。",
                ],
                "constraints": [
                    "ADR-005 是本 FEAT 的前置基础；本 FEAT 只定义主链如何消费其受治理 IO/path 能力，不重新实现底层模块。",
                    "主链 IO/path 规则只覆盖 handoff、formal materialization 与 governed skill IO，不得外扩成全局文件治理。",
                    "任何正式主链写入都必须遵守受治理 path / mode 边界，不允许 silent fallback 到自由写入。",
                ],
                "dependencies": [
                    "Boundary to 对象分层与准入能力: 本 FEAT 定义对象落盘边界，不定义对象层级与消费资格本身。",
                    "Boundary to 正式交接与物化能力: 本 FEAT 约束 formalization 的 IO/path 边界，但 formalization 决策语义仍属于正式交接 FEAT。",
                ],
                "outputs": [
                    "Frozen FEAT definition for FEAT-SRC-001-004",
                    "Traceable handoff metadata for downstream derivation",
                ],
                "acceptance_checks": [
                    {"scenario": "Mainline IO boundary is explicit", "given": "mainline path boundary", "when": "reviewed", "then": "主链 IO 与全局文件治理边界清晰"},
                    {"scenario": "Governed path rules are inherited", "given": "formal write path", "when": "validated", "then": "必须使用受治理 path / mode 边界"},
                    {"scenario": "Global file governance is out of scope", "given": "repository-wide IO change", "when": "proposed", "then": "被留在本 FEAT 外"},
                ],
                "source_refs": ["FEAT-SRC-001-004", "EPIC-SRC-001-001", "SRC-001", "ADR-005"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-io-boundary")
            input_dir = self.make_feat_package(repo_root, "feat-io-boundary", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-004", "--repo-root", str(repo_root), "--run-id", "tech-io-boundary")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            arch_body = (artifacts_dir / "arch-design.md").read_text(encoding="utf-8")
            tech_body = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")
            api_body = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")

            self.assertTrue(design["arch_required"])
            self.assertTrue(design["api_required"])
            self.assertTrue((artifacts_dir / "arch-design.md").exists())
            self.assertTrue((artifacts_dir / "api-contract.md").exists())
            self.assertIn("Path policy owns allow/deny and mode decisions before any governed read/write executes.", arch_body)
            self.assertIn("cli/lib/managed_gateway.py", tech_body)
            self.assertIn("GatewayWriteRequest", tech_body)
            self.assertIn("ll artifact commit", api_body)
            self.assertIn("ll artifact read", api_body)
            self.assertIn("PolicyVerdict", tech_body)
            self.assertIn("Canonical refs:", api_body)

    def test_allow_update_removes_stale_optional_api_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-005",
                "title": "配置页文案统一能力",
                "goal": "统一配置页文案，不改变系统边界或接口契约。",
                "scope": [
                    "统一页面标题文案。",
                    "统一帮助提示文案。",
                    "统一成功与失败状态提示文案。",
                ],
                "constraints": [
                    "不改变接口结构。",
                    "不新增跨模块 contract。",
                    "不改变模块边界。",
                    "允许 update 重跑时清理与当前 need assessment 不一致的旧产物。",
                ],
                "dependencies": [],
                "outputs": ["page copy update"],
                "acceptance_checks": [
                    {"scenario": "Title copy is consistent", "given": "配置页", "when": "查看标题", "then": "标题文案统一"},
                    {"scenario": "Help text is consistent", "given": "帮助提示", "when": "查看提示", "then": "帮助文案统一"},
                    {"scenario": "Stale optional artifacts are removed on rerun", "given": "allow-update rerun", "when": "optional contract output is no longer required", "then": "旧契约产物会被删除"},
                ],
                "source_refs": ["FEAT-SRC-001-005", "EPIC-SRC-001-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-update-clean")
            input_dir = self.make_feat_package(repo_root, "feat-update-clean", bundle)
            stale_dir = repo_root / "artifacts" / "feat-to-tech" / "tech-update-clean"
            stale_dir.mkdir(parents=True, exist_ok=True)
            (stale_dir / "api-contract.md").write_text("stale api\n", encoding="utf-8")

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-SRC-001-005",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "tech-update-clean",
                "--allow-update",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((stale_dir / "api-contract.md").exists())

    def test_feature_axis_specific_impl_content_stays_aligned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-003",
                "title": "对象分层与准入能力",
                "goal": "让 candidate package、formal object 与 downstream consumption 形成稳定分层。",
                "scope": [
                    "定义 candidate package、formal object、downstream consumption object 的分层职责和允许的引用方向。",
                    "定义什么对象有资格成为正式输入，以及哪些 consumer 只能读取 formal layer。",
                    "要求任何下游消费都必须沿 formal refs 与 lineage 进入。",
                ],
                "constraints": [
                    "candidate package 与 formal object 强制分层。",
                    "Consumer 准入必须沿 formal refs 与 lineage 判断。",
                    "不得通过路径猜测获得读取资格。",
                ],
                "dependencies": [
                    "Boundary to 正式交接与物化能力: 本 FEAT 定义哪些对象可以成为正式输入，而不是定义正式升级动作本身。",
                    "Boundary to 主链文件 IO 与路径治理能力: path / mode 规则留给 IO 治理 FEAT。",
                ],
                "outputs": ["Frozen FEAT definition", "Traceable handoff metadata"],
                "acceptance_checks": [
                    {"scenario": "Candidate and formal layers cannot be confused", "given": "candidate object", "when": "reviewed", "then": "必须区分 authoritative layer"},
                    {"scenario": "Consumer admission is formal-ref based", "given": "consumer", "when": "validated", "then": "必须沿 formal refs 与 lineage 放行"},
                    {"scenario": "Path guessing is blocked", "given": "旁路读取", "when": "attempted", "then": "被拒绝"},
                ],
                "source_refs": ["FEAT-SRC-001-003", "EPIC-SRC-001-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-layering")
            input_dir = self.make_feat_package(repo_root, "feat-layering", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-003", "--repo-root", str(repo_root), "--run-id", "tech-layering")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            tech_body = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))

            self.assertIn("cli/lib/lineage.py", tech_body)
            self.assertIn("AdmissionRequest", tech_body)

    def test_product_slice_titles_and_machine_fields_drive_axis_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-010",
                "title": "主链 gate 审核与裁决流",
                "axis_id": "handoff-formalization",
                "track": "foundation",
                "goal": "冻结 gate 如何审核 candidate、形成单一 decision object，并把结果明确返回 execution 或 formal 发布链。",
                "scope": [
                    "定义 gate 如何消费 authoritative handoff 并组织审核上下文。",
                    "定义 approve / revise / retry / handoff / reject 的业务语义与输出物。",
                    "定义 decision object 如何成为 formal 发布 trigger。",
                ],
                "constraints": [
                    "approve / revise / retry / handoff / reject 词表只能在本 FEAT 定义。",
                    "decision object 是唯一 authoritative gate result。",
                    "formal publication 只能由 approve decision 触发。",
                    "本 FEAT 不定义 downstream admission。",
                ],
                "dependencies": [
                    "上游依赖 FEAT-SRC-001-009 提供 authoritative handoff submission。",
                    "下游依赖 FEAT-SRC-001-011 负责 formal publication 与 admission。",
                ],
                "outputs": ["authoritative decision object", "formal publication trigger"],
                "upstream_feat": ["FEAT-SRC-001-009"],
                "downstream_feat": ["FEAT-SRC-001-011"],
                "consumes": ["authoritative handoff submission", "proposal", "evidence"],
                "produces": ["authoritative decision object", "delegation directive", "formal publication trigger"],
                "authoritative_artifact": "authoritative decision object",
                "gate_decision_dependency_feat_refs": [],
                "gate_decision_dependency": "owned by this FEAT",
                "admission_dependency_feat_refs": ["FEAT-SRC-001-011"],
                "admission_dependency": "approve decisions emitted here are the only prerequisite for downstream formal publication and admission",
                "identity_and_scenario": {"product_interface": "审批裁决流", "completed_state": "authoritative decision object 已形成"},
                "business_flow": {"main_flow": ["gate consume handoff", "review and decide", "emit decision object"]},
                "product_objects_and_deliverables": {"authoritative_output": "authoritative decision object"},
                "collaboration_and_timeline": {"business_sequence": "handoff -> gate decision -> formal trigger"},
                "acceptance_and_testability": {"test_dimensions": ["decision vocabulary", "decision return path", "formal trigger path", "reject path"]},
                "frozen_downstream_boundary": {"open_technical_decisions": ["runtime persistence carrier"]},
                "acceptance_checks": [
                    {"scenario": "Gate decision path is single and explicit", "given": "handoff", "when": "reviewed", "then": "输出单一 decision object"},
                    {"scenario": "Decision vocabulary is canonical", "given": "reviewer", "when": "deciding", "then": "只允许 approve/revise/retry/handoff/reject"},
                    {"scenario": "Formal trigger is decision-owned", "given": "approve", "when": "publishing", "then": "formal trigger 只能来自 decision object"},
                ],
                "source_refs": ["FEAT-SRC-001-010", "EPIC-SRC-001-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-product-slice")
            input_dir = self.make_feat_package(repo_root, "feat-product-slice", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-010", "--repo-root", str(repo_root), "--run-id", "tech-product-slice")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            tech_body = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")
            api_body = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")

            self.assertEqual(design["selected_feat"]["axis_id"], "handoff-formalization")
            self.assertEqual(design["selected_feat"]["resolved_axis"], "formalization")
            self.assertEqual(design["selected_feat"]["authoritative_artifact"], "authoritative decision object")
            self.assertEqual(design["selected_feat"]["downstream_feat"], ["FEAT-SRC-001-011"])
            self.assertIn("GateBriefRecord", tech_body)
            self.assertIn("GateDecision", tech_body)
            self.assertIn("ll gate evaluate", api_body)
            self.assertIn("ll gate dispatch", api_body)
            self.assertNotIn("validate-admission", api_body)
            self.assertIn("dispatch_pending", tech_body)
            self.assertNotIn("Onboarding registry", tech_body)
            self.assertTrue(design["api_required"])

    def test_formalization_api_doc_uses_cli_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-002",
                "title": "正式交接与物化能力",
                "goal": "让 candidate package 经由 external gate 形成 formal object 并成为下游正式输入。",
                "scope": [
                    "定义 handoff 到 gate decision 的正式升级链。",
                    "定义 approve / revise / retry / handoff / reject 的决策词表。",
                    "定义 formal object 发布与下游正式消费边界。",
                ],
                "constraints": [
                    "business skill 不直接写 formal object。",
                    "formalization 只发生在 gate 决策之后。",
                    "candidate package 不得直接成为下游正式输入。",
                ],
                "dependencies": [
                    "Boundary to 主链协作闭环能力: handoff runtime 仍负责主链提交与回流。",
                    "Boundary to 对象分层与准入能力: formal refs 与 lineage 需要后续准入消费。",
                ],
                "outputs": ["decision object", "formal publish contract"],
                "acceptance_checks": [
                    {"scenario": "Gate decision vocabulary is explicit", "given": "handoff", "when": "reviewed", "then": "决策词表固定"},
                    {"scenario": "Formal object publish is explicit", "given": "approve", "when": "materialized", "then": "形成 formal refs"},
                    {"scenario": "Candidate does not bypass gate", "given": "candidate package", "when": "consumer reads", "then": "不允许直接消费"},
                ],
                "source_refs": ["FEAT-SRC-001-002", "EPIC-SRC-001-001", "SRC-001", "ADR-006"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-formalization-api")
            input_dir = self.make_feat_package(repo_root, "feat-formalization-api", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-002", "--repo-root", str(repo_root), "--run-id", "tech-formalization-api")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            api_md = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")

            self.assertIn("ll gate evaluate", api_md)
            self.assertIn("ll gate dispatch", api_md)
            self.assertIn("decision_ref", api_md)
            self.assertIn("decision_target", api_md)
            self.assertIn("decision_basis_refs", api_md)
            self.assertIn("dispatch_receipt_ref", api_md)
            self.assertIn("decision_not_dispatchable", api_md)
            self.assertIn("Success envelope", api_md)

    def test_minimal_onboarding_feat_emits_profile_flow_tech(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result, artifacts_dir = self._run_feat(
                Path(temp_dir),
                self._minimal_onboarding_feature("FEAT-SRC-001-012"),
                "feat-minimal-onboarding",
                "tech-minimal-onboarding",
            )
            design = self._json(artifacts_dir / "tech-design-bundle.json")
            drift = self._json(artifacts_dir / "semantic-drift-check.json")
            tech_md = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")
            api_md = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(design["selected_feat"]["resolved_axis"], "minimal_onboarding")
            self.assertEqual(design["semantic_lock"]["domain_type"], "product_onboarding_flow")
            self.assertEqual(drift["verdict"], "pass")
            self.assertTrue(drift["semantic_lock_present"])
            self.assertIn("profile_minimal_done", drift["matched_allowed_capabilities"])
            self.assertIn("SubmitMinimalProfile", tech_md)
            self.assertIn("POST /v1/onboarding/minimal-profile", api_md)
            self.assertNotIn("OnboardingDirective", tech_md)
            self.assertNotIn("cutover", tech_md.lower())

    def test_minimal_onboarding_semantic_lock_blocks_rollout_and_pilot_carriers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            feature = self._minimal_onboarding_feature(
                "FEAT-SRC-001-014",
                scope=[
                    "登录/注册完成后，未完成最小建档的用户进入单页最小建档页。",
                    "最小建档页必须稳定收集 gender、birthdate、height、weight、running_level、recent_injury_status。",
                    "错误方案：还要输出 onboarding directive、pilot evidence 与 cutover recommendation。",
                ],
                constraints=[
                    "最小建档必须维持单页完成，不拆成多步向导。",
                    "ll rollout onboard-skill 与 compat mode 不能变成最小建档主链载体。",
                    "device connection 只能作为 deferred follow-up entry，不能重新变成 blocking prerequisite。",
                ],
                outputs=["minimal profile completion", "homepage entry allowance", "pilot evidence submission"],
                acceptance_checks=[
                    {"scenario": "Minimal profile submit allows homepage entry", "given": "required fields valid", "when": "submit minimal profile", "then": "profile_minimal_done and homepage entry allowed"},
                    {"scenario": "Pilot carrier wrongly appears", "given": "rollout chain", "when": "reviewed", "then": "OnboardingDirective and PilotEvidenceSubmission are emitted"},
                    {"scenario": "Invalid required fields stay on the page", "given": "birthdate or required fields invalid", "when": "submit is attempted", "then": "field-level errors are returned and homepage entry stays blocked"},
                ],
            )
            result, artifacts_dir = self._run_feat(Path(temp_dir), feature, "feat-minimal-onboarding-drift", "tech-minimal-onboarding-drift")
            design = self._json(artifacts_dir / "tech-design-bundle.json")
            drift = self._json(artifacts_dir / "semantic-drift-check.json")
            review = self._json(artifacts_dir / "tech-review-report.json")
            acceptance = self._json(artifacts_dir / "tech-acceptance-report.json")
            defects = self._json(artifacts_dir / "tech-defect-list.json")
            gate = self._json(artifacts_dir / "tech-freeze-gate.json")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("semantic-drift-check.json must preserve semantic_lock", result.stderr)
            self.assertEqual(design["semantic_lock"]["domain_type"], "product_onboarding_flow")
            self.assertEqual(drift["verdict"], "reject")
            self.assertFalse(drift["semantic_lock_preserved"])
            self.assertTrue(any(item in drift["forbidden_axis_detected"] for item in ["ll rollout onboard-skill", "cutover", "compat mode"]))
            self.assertEqual(review["decision"], "revise")
            self.assertEqual(acceptance["decision"], "revise")
            self.assertTrue(any(item["title"] == "semantic_lock drift detected" for item in defects))
            self.assertFalse(gate["freeze_ready"])

    def test_product_flow_axes_emit_feat_specific_tech_instead_of_generic_template(self) -> None:
        cases = [
            (
                self._first_ai_advice_feature("FEAT-SRC-001-002"),
                "first_ai_advice",
                ["GenerateFirstAdvice", "EvaluateFirstAdviceRiskGate", "advice_generated", "training_advice_level"],
                "Keep first-advice output, risk-gate decisions, and fallback-mode evidence traceable in freeze-ready artifacts.",
                None,
            ),
            (
                self._extended_profile_completion_feature("FEAT-SRC-001-003"),
                "extended_profile_completion",
                ["SaveExtendedProfilePatch", "GetProfileCompletionTasks", "profile_extension_in_progress", "profile_completion_percent"],
                "Keep patch-save results, profile-completion-percent updates, and retry-state evidence traceable in freeze-ready artifacts.",
                None,
            ),
            (
                self._device_deferred_entry_feature("FEAT-SRC-001-004"),
                "device_deferred_entry",
                ["StartDeferredDeviceConnection", "FinalizeDeviceConnection", "device_failed_nonblocking", "homepage_access_preserved"],
                "Keep deferred-device-connection outcomes and homepage/first-advice preservation evidence traceable in freeze-ready artifacts.",
                None,
            ),
            (
                self._state_profile_boundary_feature("FEAT-SRC-001-005"),
                "state_profile_boundary",
                ["WritePrimaryState", "WritePhysicalProfileCanonical", "ReadUnifiedOnboardingState", "canonical_profile_boundary"],
                "Keep canonical-ownership decisions, conflict-blocked outcomes, and unified-reader judgments traceable in freeze-ready artifacts.",
                "Projection stores 只能作为只读 projection / read model，不得回写 canonical body facts，也不得覆盖 user_physical_profile 的唯一事实源地位。",
            ),
        ]
        for feature, expected_axis, markers, nfr_marker, rule_marker in cases:
            with self.subTest(axis=expected_axis):
                with tempfile.TemporaryDirectory() as temp_dir:
                    result, artifacts_dir = self._run_feat(
                        Path(temp_dir),
                        feature,
                        f"feat-{expected_axis}",
                        f"tech-{expected_axis}",
                    )
                    design = self._json(artifacts_dir / "tech-design-bundle.json")
                    drift = self._json(artifacts_dir / "semantic-drift-check.json")
                    tech_md = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")
                    api_md = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")

                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(design["selected_feat"]["axis_id"], feature["axis_id"])
                    self.assertEqual(design["selected_feat"]["resolved_axis"], expected_axis)
                    self.assertEqual(drift["verdict"], "pass")
                    self.assertTrue(drift["topic_alignment_ok"])
                    self.assertTrue(drift["lock_gate_ok"])
                    self.assertNotEqual(design["selected_feat"]["resolved_axis"], "generic")
                    for marker in markers:
                        self.assertIn(marker, tech_md + "\n" + api_md)
                    self.assertNotIn("genericRequest", tech_md)
                    self.assertNotIn("[runtime.py] -> [contracts.py] -> [receipts.py]", tech_md)
                    self.assertNotIn("`prepared` -> `executed` -> `recorded`", tech_md)
                    self.assertNotIn("不扩展到 EPIC、FEAT、TASK 或实现设计", tech_md)
                    self.assertNotIn("Keep the package freeze-ready by recording execution evidence and supervision evidence.", tech_md)
                    self.assertIn(nfr_marker, tech_md)
                    if rule_marker:
                        self.assertIn(rule_marker, tech_md)

    def test_implementation_rules_rewrite_legacy_not_expand_sentence_for_product_feat(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            feature = self._first_ai_advice_feature(
                "FEAT-SRC-001-026",
                constraints=[
                    "来源与依赖约束：保持与原始输入同题，不扩展到 EPIC、FEAT、TASK 或实现设计。",
                    "缺失 risk gate 关键字段时不得放行正常建议分支。",
                    "不要求扩展画像或设备连接先完成。",
                ],
            )
            result, artifacts_dir = self._run_feat(
                Path(temp_dir),
                feature,
                "feat-legacy-constraint-rewrite",
                "tech-legacy-constraint-rewrite",
            )
            tech_md = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("不扩展到 EPIC、FEAT、TASK 或实现设计", tech_md)
            self.assertIn("不扩展到相邻 FEAT、TASK 排期细节或超出本 FEAT 边界的实现域", tech_md)

    def test_product_flow_axes_reject_generic_placeholder_tech(self) -> None:
        generic_placeholder = [
            "[runtime.py] -> [contracts.py] -> [receipts.py]",
            "`prepared` -> `executed` -> `recorded`",
            "`genericRequest`",
            "normalize request execute authoritative carrier persist evidence and refs return structured result",
        ]
        cases = [
            (self._first_ai_advice_feature("FEAT-SRC-001-022"), "first_ai_advice"),
            (self._extended_profile_completion_feature("FEAT-SRC-001-023"), "extended_profile_completion"),
            (self._device_deferred_entry_feature("FEAT-SRC-001-024"), "device_deferred_entry"),
            (self._state_profile_boundary_feature("FEAT-SRC-001-025"), "state_profile_boundary"),
        ]
        for feature, expected_axis in cases:
            with self.subTest(axis=expected_axis):
                feature["semantic_lock"] = derive_semantic_lock(feature)
                drift = build_semantic_drift_check(feature, generic_placeholder)
                defects = build_defects([expected_axis], {"passed": True, "issues": []}, drift)

                self.assertEqual(feature_axis(feature), expected_axis)
                self.assertEqual(drift["verdict"], "reject")
                self.assertFalse(drift["topic_alignment_ok"])
                self.assertTrue(any(expected_axis in issue for issue in drift["carrier_topic_issues"]))
                self.assertTrue(any(item["title"] == "semantic_lock drift detected" for item in defects))

    def test_axis_keyword_family_conflicts_fail_semantic_drift_checks(self) -> None:
        cases = [
            (
                self._minimal_onboarding_feature(
                    "FEAT-SRC-001-015",
                    scope=["收集 gender、birthdate、height、weight、running_level、recent_injury_status。", "最小建档完成后允许进入首页。", "设备连接保持后置。"],
                    constraints=["不允许把设备连接重新变成首进阻塞前置。"],
                    identity_and_scenario={"completed_state": "用户提交最小建档后立即允许进入首页，且设备绑定不再阻塞首进链路。"},
                ),
                [
                    "OnboardingDirective ll rollout onboard-skill compat mode migration wave cutover guard pilot chain audit submit-pilot-evidence",
                    "cli/lib/rollout_state.py cli/lib/pilot_chain.py rollout state",
                ],
                "minimal_onboarding",
            ),
            (
                {
                    "feat_ref": "FEAT-SRC-001-016",
                    "title": "governed skill 接入与 pilot 闭环流",
                    "axis_id": "skill-adoption-e2e",
                    "semantic_lock": {
                        "domain_type": "adoption_flow_rule",
                        "one_sentence_truth": "Adoption flow keeps onboarding, pilot, cutover, and fallback semantics on the governed skill path.",
                        "primary_object": "pilot evidence",
                        "lifecycle_stage": "cutover",
                        "allowed_capabilities": ["pilot evidence", "compat mode", "cutover"],
                        "forbidden_capabilities": ["profile_minimal_done"],
                        "inheritance_rule": "Downstream TECH must preserve pilot and cutover semantics.",
                    },
                },
                ["SubmitMinimalProfile profile_minimal_done homepage entry guard POST /v1/onboarding/minimal-profile device_connection_deferred"],
                "adoption_e2e",
            ),
        ]
        for feature, generated_text_parts, expected_axis in cases:
            with self.subTest(axis=expected_axis):
                feature["semantic_lock"] = feature.get("semantic_lock") or derive_semantic_lock(feature)
                drift = build_semantic_drift_check(feature, generated_text_parts)
                defects = build_defects([expected_axis], {"passed": True, "issues": []}, drift)

                self.assertEqual(feature_axis(feature), expected_axis)
                self.assertEqual(drift["verdict"], "reject")
                self.assertTrue(drift["axis_conflicts"])
                self.assertTrue(any(defect["title"] == "Resolved axis conflicts with generated TECH keyword family" for defect in defects))

    def test_product_onboarding_words_do_not_false_positive_adoption_e2e(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            feature = self._minimal_onboarding_feature(
                "FEAT-SRC-001-013",
                axis_id=None,
                title="Minimal onboarding profile page",
                goal="Collect the minimum profile and then let the user enter the homepage immediately.",
                scope=[
                    "Show one minimal onboarding page after registration.",
                    "Collect gender, birthdate, height, weight, running_level, and recent_injury_status.",
                    "Allow homepage entry right after minimal profile submission.",
                ],
                constraints=[
                    "Inherited rollout requirements stay outside this FEAT and must not redefine the product flow.",
                    "Device connection remains deferred after homepage entry.",
                ],
                dependencies=[],
                outputs=["minimal profile state", "homepage entry allowance"],
                acceptance_checks=[
                    {"scenario": "minimum profile completes onboarding", "given": "required fields valid", "when": "submitted", "then": "homepage becomes available"},
                    {"scenario": "required field errors block homepage entry", "given": "required fields missing", "when": "submitted", "then": "homepage stays blocked and field errors are visible"},
                    {"scenario": "device connection is still deferred", "given": "minimal profile completes", "when": "homepage opens", "then": "device connection remains a follow-up path"},
                ],
            )
            result, artifacts_dir = self._run_feat(Path(temp_dir), feature, "feat-onboarding-no-adoption", "tech-onboarding-no-adoption")
            design = self._json(artifacts_dir / "tech-design-bundle.json")
            tech_md = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(design["selected_feat"]["resolved_axis"], "minimal_onboarding")
            self.assertNotIn("OnboardingDirective", tech_md)
            self.assertNotIn("PilotEvidenceSubmission", tech_md)
            self.assertNotIn("rollout_state.py", tech_md)
            self.assertNotIn("cutover", tech_md.lower())

    def test_adoption_e2e_feat_emits_api_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result, artifacts_dir = self._run_feat(
                Path(temp_dir),
                self._adoption_e2e_feature("FEAT-SRC-001-006"),
                "feat-adoption-api",
                "tech-adoption-api",
            )
            design = self._json(artifacts_dir / "tech-design-bundle.json")
            drift = self._json(artifacts_dir / "semantic-drift-check.json")
            api_md = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(design["api_required"])
            self.assertEqual(drift["verdict"], "pass")
            self.assertIn("ll rollout onboard-skill", api_md)
            self.assertIn("ll audit submit-pilot-evidence", api_md)
            self.assertIn("compat_mode", api_md)
            self.assertIn("cutover_recommendation", api_md)

    def test_execution_runner_operator_entry_feat_emits_runner_entry_tech(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-ADR018-002",
                "title": "Runner 用户入口流",
                "axis_id": "runner-operator-entry",
                "goal": "让 Claude/Codex CLI 用户通过独立 runner skill 启动或恢复 Execution Loop Job Runner。",
                "scope": [
                    "定义 runner 独立 skill 入口。",
                    "定义 start / resume 语义。",
                    "定义入口调用如何把运行权交给 runner。",
                ],
                "constraints": [
                    "Execution Loop Job Runner 必须以独立 skill 入口暴露给 Claude/Codex CLI 用户。",
                    "入口必须显式声明 start / resume 语义。",
                    "入口不得退化成手工逐个调用下游 skill。",
                ],
                "dependencies": [
                    "Boundary to ready-job FEAT: 本 FEAT 不负责生成 ready execution job。",
                    "Boundary to runner-control-surface FEAT: 入口启动后，后续控制语义由控制面 FEAT 承担。",
                ],
                "outputs": ["runner skill entry definition", "runner invocation record", "runner start receipt"],
                "acceptance_checks": [
                    {"scenario": "Runner skill entry is explicit", "given": "Claude/Codex CLI operator", "when": "runner is started", "then": "存在一个明确的 runner skill entry"},
                    {"scenario": "Runner entry preserves authoritative context", "given": "resume path", "when": "runner resumes", "then": "保留 authoritative run context"},
                    {"scenario": "Runner entry is not manual relay", "given": "post-approve flow", "when": "reviewed", "then": "不会退化成 manual downstream relay"},
                ],
                "source_refs": ["FEAT-SRC-ADR018-002", "EPIC-ADR018", "SRC-ADR018", "ADR-018"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-runner-entry")
            bundle["source_refs"] = ["product.epic-to-feat::feat-runner-entry", feature["feat_ref"], "EPIC-ADR018", "SRC-ADR018", "ADR-018"]
            input_dir = self.make_feat_package(repo_root, "feat-runner-entry", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                feature["feat_ref"],
                "--repo-root",
                str(repo_root),
                "--run-id",
                "tech-runner-entry",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            tech_md = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")
            arch_md = (artifacts_dir / "arch-design.md").read_text(encoding="utf-8")
            api_md = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")

            self.assertTrue(design["arch_required"])
            self.assertTrue(design["api_required"])
            self.assertIn("cli/lib/runner_entry.py", tech_md)
            self.assertIn("cli/lib/execution_runner.py", tech_md)
            self.assertIn("ExecutionRunnerStartRequest", tech_md)
            self.assertIn("Dedicated runner entry placement", arch_md)
            self.assertIn("ll loop run-execution", api_md)
            self.assertIn("entry_mode ∈ {start, resume}", api_md)
            self.assertNotIn("ll gate submit-handoff", api_md)

    def test_adr007_adoption_e2e_feat_preserves_web_and_cli_skill_family(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-ADR007-005",
                "title": "governed skill 接入与 pilot 验证流",
                "axis_id": "skill-adoption-e2e",
                "track": "adoption_e2e",
                "goal": "让 test execution family 按 onboarding、pilot、cutover/fallback 的主链接入流程稳定落地。",
                "scope": [
                    "定义 onboarding directive、pilot evidence 与 cutover guard 的业务交付物。",
                    "定义 producer -> gate -> formal -> consumer -> audit 的最小 pilot 闭环。",
                    "定义 compat mode、fallback 与 cutover 的业务边界。",
                ],
                "constraints": [
                    "本 FEAT 不重写 foundation FEAT 的内部实现。",
                    "pilot evidence 必须成为 authoritative rollout input。",
                    "fallback 结果必须显式记录到 receipt。",
                ],
                "dependencies": [
                    "Boundary to formal 发布与下游准入流: pilot 只能消费已发布 formal refs。",
                    "Boundary to 主链候选提交与交接流: producer 提交仍沿 authoritative handoff 进入 gate pending。",
                ],
                "outputs": ["onboarding directive", "pilot evidence submission", "cutover recommendation"],
                "acceptance_checks": [
                    {"scenario": "Pilot chain is complete", "given": "producer to audit", "when": "validated", "then": "闭环证据齐全"},
                    {"scenario": "CLI sibling is preserved", "given": "ADR-007 family", "when": "derived", "then": "skill.qa.test_exec_cli 被保留"},
                    {"scenario": "CLI runner sibling is preserved", "given": "ADR-007 family", "when": "derived", "then": "skill.runner.test_cli 被保留"},
                ],
                "source_refs": ["FEAT-SRC-ADR007-005", "EPIC-ADR007", "SRC-ADR007", "ADR-007"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-adr007-adoption")
            input_dir = self.make_feat_package(repo_root, "feat-adr007-adoption", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                feature["feat_ref"],
                "--repo-root",
                str(repo_root),
                "--run-id",
                "tech-adr007-adoption",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            implementation_rules = design["tech_design"]["implementation_rules"]
            joined_rules = "\n".join(implementation_rules)

            self.assertIn("skill.qa.test_exec_web_e2e", joined_rules)
            self.assertIn("skill.qa.test_exec_cli", joined_rules)
            self.assertIn("skill.runner.test_e2e", joined_rules)
            self.assertIn("skill.runner.test_cli", joined_rules)

    def test_ambiguous_collaboration_reentry_boundary_fails_semantic_consistency(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-011",
                "title": "主链候选提交与交接流",
                "goal": "冻结 authoritative handoff submission 与 gate pending intake。",
                "scope": [
                    "定义 candidate package、proposal、evidence 在什么触发场景下被提交。",
                    "定义提交后形成什么 authoritative handoff object。",
                    "定义提交完成后对上游和 gate 分别暴露什么业务结果。",
                ],
                "constraints": [
                    "Loop 协作语义必须显式说明哪类对象触发 gate、哪类 decision 允许回流、哪类状态允许继续推进。",
                    "The FEAT must make clear which authoritative handoff and pending-intake results become visible, while keeping approval and re-entry semantics outside this FEAT.",
                ],
                "dependencies": [
                    "Boundary to 正式交接与物化能力: 本 FEAT 只负责协作责任、状态流转与回流条件，不负责 formalization 语义、升级判定与物化结果。",
                ],
                "outputs": ["authoritative handoff submission", "gate pending visibility result"],
                "acceptance_checks": [
                    {"scenario": "submission completion stays visible", "given": "authoritative handoff", "when": "submitted", "then": "上游能看到 pending intake"},
                    {"scenario": "re-entry semantics stay outside", "given": "returned decision", "when": "reviewed", "then": "re-entry semantics remain outside this FEAT"},
                    {"scenario": "loop responsibility split is explicit", "given": "execution/gate/human loops", "when": "reviewed", "then": "责任边界清晰"},
                ],
                "source_refs": ["FEAT-SRC-001-011", "EPIC-SRC-001-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-ambiguous-reentry")
            input_dir = self.make_feat_package(repo_root, "feat-ambiguous-reentry", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-011", "--repo-root", str(repo_root), "--run-id", "tech-ambiguous-reentry")
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            gate = json.loads((artifacts_dir / "tech-freeze-gate.json").read_text(encoding="utf-8"))

            self.assertTrue(design["design_consistency_check"]["structural_passed"])
            self.assertFalse(design["design_consistency_check"]["semantic_passed"])
            self.assertFalse(design["design_consistency_check"]["passed"])
            self.assertTrue(any("re-entry ownership" in issue for issue in design["design_consistency_check"]["issues"]))
            self.assertTrue(any(error == "cross_artifact_consistency_passed" for error in payload["readiness_errors"]))
            self.assertFalse(gate["freeze_ready"])

    def test_validate_input_rejects_missing_feat_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-003",
                "title": "对象分层能力",
                "goal": "统一对象层级。",
                "scope": ["定义 candidate layer。", "定义 formal layer。", "定义 consumer admission。"],
                "constraints": ["formal refs 必须保留。", "禁止路径猜测。", "不改变外部 API。", "不改变 UI。"],
                "dependencies": [],
                "outputs": ["layering notes"],
                "acceptance_checks": [
                    {"scenario": "Candidate and formal layers are split", "given": "candidate object", "when": "评审", "then": "层级清晰"},
                    {"scenario": "Formal refs are required", "given": "consumer", "when": "读取", "then": "必须沿 formal refs"},
                    {"scenario": "Path guessing is blocked", "given": "旁路读取", "when": "尝试消费", "then": "被阻止"},
                ],
                "source_refs": ["FEAT-SRC-001-003", "EPIC-SRC-001-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-invalid")
            input_dir = self.make_feat_package(repo_root, "feat-invalid", bundle)

            result = self.run_cmd("validate-input", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-404")
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("Selected feat_ref not found" in error for error in payload["errors"]))

    def test_review_projection_feat_preserves_semantic_lock_without_runtime_drift(self) -> None:
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
                "feat_ref": "FEAT-SRC-ADR015-001",
                "title": "Human Review Projection 生成流",
                "goal": "从 Machine SSOT 生成 gate 审核用的人类友好 Projection。",
                "axis_id": "projection-generation",
                "scope": [
                    "渲染 Product Summary、Roles、Main Flow、Key Deliverables。",
                    "注入 derived-only / non-authoritative marker。",
                    "保留 projection 到 SSOT 的 trace refs。",
                ],
                "constraints": [
                    "Projection 不是新的真相源。",
                    "不得引入 handoff orchestration、formal publication、governed IO。",
                    "Projection 只服务 gate review。",
                ],
                "dependencies": ["Machine SSOT 已 freeze-ready。", "Projection template 已发布。"],
                "acceptance_checks": [
                    {"scenario": "Projection blocks derive from Machine SSOT", "given": "freeze-ready SSOT", "when": "render projection", "then": "Product Summary / Roles / Main Flow / Deliverables 全部可 trace 到 SSOT"},
                    {"scenario": "Projection keeps derived-only marker", "given": "rendered projection", "when": "review marker block", "then": "Projection 明确 derived-only / non-authoritative / non-inheritable"},
                    {"scenario": "Projection does not drift into governance runtime", "given": "TECH derivation", "when": "review generated design", "then": "不得出现 handoff runtime、formal publication、governed IO 平台语义"},
                ],
                "semantic_lock": semantic_lock,
                "source_refs": ["FEAT-SRC-ADR015-001", "EPIC-SRC-001-001", "SRC-001", "ADR-015"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-review-projection")
            bundle["semantic_lock"] = semantic_lock
            input_dir = self.make_feat_package(repo_root, "feat-review-projection", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-SRC-ADR015-001",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "tech-review-projection",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            drift = json.loads((artifacts_dir / "semantic-drift-check.json").read_text(encoding="utf-8"))
            tech_md = (artifacts_dir / "tech-spec.md").read_text(encoding="utf-8")

            self.assertFalse(design["arch_required"])
            self.assertFalse(design["api_required"])
            self.assertTrue(drift["semantic_lock_preserved"])
            self.assertEqual(design["semantic_lock"]["domain_type"], "review_projection_rule")
            self.assertIn("Projection renderer", tech_md)
            self.assertIn("Machine SSOT remains the only authority", tech_md)
            self.assertNotIn("cli/lib/mainline_runtime.py", tech_md)
            self.assertNotIn("cli/lib/managed_gateway.py", tech_md)
            self.assertNotIn("ll gate ", tech_md)

    def test_formal_feat_ref_is_admissible_input_for_feat_to_tech(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-201",
                "title": "配置中心协作主链",
                "goal": "验证 formal FEAT 能反查回 bundle package 并驱动 TECH 派生。",
                "scope": ["保留协作边界。", "保留接口约束。", "允许 formal admission 进入 TECH。"],
                "constraints": ["不得跳过 FEAT。", "不得丢失 source refs。", "TECH 仍从 feat_freeze_package 派生。", "admission 必须 fail closed。"],
                "dependencies": ["formal FEAT registry 可解析。"],
                "outputs": ["tech design"],
                "acceptance_checks": [
                    {"scenario": "formal ref resolves package", "given": "formal FEAT", "when": "run feat-to-tech", "then": "source package dir 被正确反查"},
                    {"scenario": "selected feat remains explicit", "given": "formal FEAT", "when": "derive TECH", "then": "feat_ref 与 title 不丢失"},
                    {"scenario": "input mode is formal admission", "given": "formal FEAT", "when": "validate input", "then": "input_mode=formal_admission"},
                ],
                "source_refs": ["FEAT-SRC-001-201", "EPIC-SRC-001-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-formal-tech")
            self.make_feat_package(repo_root, "feat-formal-tech", bundle)
            formal_feat_path = repo_root / "ssot" / "feat" / "FEAT-SRC-001-201__configuration-mainline.md"
            formal_feat_path.parent.mkdir(parents=True, exist_ok=True)
            formal_feat_path.write_text(
                "---\nid: FEAT-SRC-001-201\nssot_type: FEAT\ntitle: 配置中心协作主链\nstatus: frozen\n---\n\n# 配置中心协作主链\n\nFormal FEAT body.\n",
                encoding="utf-8",
            )
            registry_dir = repo_root / "artifacts" / "registry"
            registry_dir.mkdir(parents=True, exist_ok=True)
            (registry_dir / "formal-feat-feat-src-001-201.json").write_text(
                json.dumps(
                    {
                        "artifact_ref": "formal.feat.feat-src-001-201",
                        "managed_artifact_ref": "ssot/feat/FEAT-SRC-001-201__configuration-mainline.md",
                        "status": "materialized",
                        "trace": {"run_ref": "feat-formal-tech", "workflow_key": "product.epic-to-feat"},
                        "metadata": {
                            "layer": "formal",
                            "source_package_ref": "artifacts/epic-to-feat/feat-formal-tech",
                            "assigned_id": "FEAT-SRC-001-201",
                            "feat_ref": "FEAT-SRC-001-201",
                            "ssot_type": "FEAT",
                        },
                        "lineage": ["epic-to-feat.feat-formal-tech.feat-freeze-bundle", "artifacts/active/gates/decisions/gate-decision.json"],
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
                "formal.feat.feat-src-001-201",
                "--feat-ref",
                "FEAT-SRC-001-201",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "tech-from-formal",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["input_mode"], "formal_admission")
            manifest = json.loads((Path(payload["artifacts_dir"]) / "package-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["input_artifacts_dir"],
                str((repo_root / "artifacts" / "epic-to-feat" / "feat-formal-tech").resolve()),
            )

            validate = self.run_cmd(
                "validate-input",
                "--input",
                "formal.feat.feat-src-001-201",
                "--feat-ref",
                "FEAT-SRC-001-201",
                "--repo-root",
                str(repo_root),
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)


if __name__ == "__main__":
    unittest.main()
