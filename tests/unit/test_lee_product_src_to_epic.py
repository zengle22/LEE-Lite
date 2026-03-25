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
            self.assertFalse(epic["rollout_requirement"]["required"])
            self.assertEqual(epic["rollout_plan"]["required_feat_tracks"], ["foundation"])
            self.assertTrue(epic["business_value_problem"])
            self.assertTrue(epic["actors_and_roles"])
            self.assertTrue(epic["upstream_and_downstream"])
            self.assertTrue(epic["epic_success_criteria"])
            self.assertTrue(epic["product_behavior_slices"])
            self.assertFalse((artifacts_dir / "companion-epic-proposals.json").exists())
            self.assertTrue((artifacts_dir / "_cli" / "epic-freeze-executor-commit.response.json").exists())
            self.assertTrue((repo_root / "artifacts" / "registry" / "src-to-epic-epic-basic-epic-freeze.json").exists())

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

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
            self.assertTrue(handoff["prerequisite_foundations"])
            self.assertIn("ADR-005 作为主链文件 IO / 路径治理前置基础", markdown)
            self.assertIn("本 EPIC 不重新实现 ADR-005 的 Gateway / Path Policy / Registry 模块，只消费其已交付能力。", epic["non_goals"])
            self.assertEqual(sum(1 for item in epic["non_goals"] if "ADR-005" in item), 1)
            self.assertTrue(any(item["name"] == "formal 发布与下游准入流" for item in epic["product_behavior_slices"]))
            self.assertTrue(epic["business_value_problem"])
            self.assertTrue(epic["actors_and_roles"])
            self.assertTrue(epic["upstream_and_downstream"])

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


if __name__ == "__main__":
    unittest.main()
