import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-product-epic-to-feat" / "scripts" / "epic_to_feat.py"


class EpicToFeatWorkflowTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def make_epic_package(self, root: Path, run_id: str, epic_json: dict[str, object]) -> Path:
        package_dir = root / "artifacts" / "src-to-epic" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "artifact_type": "epic_freeze_package",
            "workflow_key": "product.src-to-epic",
            "workflow_run_id": run_id,
            "title": epic_json["title"],
            "status": epic_json["status"],
            "epic_freeze_ref": epic_json["epic_freeze_ref"],
            "src_root_id": epic_json["src_root_id"],
        }
        markdown = [
            "---",
            *[f"{key}: {value}" for key, value in frontmatter.items()],
            "source_refs:",
            *[f"  - {item}" for item in epic_json["source_refs"]],
            "---",
            "",
            f"# {epic_json['title']}",
            "",
            "## Epic Intent",
            "",
            str(epic_json["business_goal"]),
            "",
            "## Business Goal",
            "",
            str(epic_json["business_goal"]),
            "",
            "## Scope",
            "",
            *[f"- {item}" for item in epic_json["scope"]],
            "",
            "## Non-Goals",
            "",
            *[f"- {item}" for item in epic_json["non_goals"]],
            "",
            "## Decomposition Rules",
            "",
            *[f"- {item}" for item in epic_json["decomposition_rules"]],
            "",
            "## Constraints and Dependencies",
            "",
            *[f"- {item}" for item in epic_json["constraints_and_dependencies"]],
            "",
            "## Downstream Handoff",
            "",
            "- workflow.product.epic-to-feat",
            "",
            "## Traceability",
            "",
            *[f"- {item}" for item in epic_json["source_refs"]],
        ]
        (package_dir / "epic-freeze.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
        (package_dir / "epic-freeze.json").write_text(json.dumps(epic_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payloads = {
            "package-manifest.json": {"status": epic_json["status"], "run_id": run_id},
            "epic-review-report.json": {"decision": "pass", "summary": "review ok"},
            "epic-acceptance-report.json": {"decision": "approve", "summary": "acceptance ok"},
            "epic-defect-list.json": [],
            "epic-freeze-gate.json": {"workflow_key": "product.src-to-epic", "freeze_ready": True, "decision": "pass"},
            "handoff-to-epic-to-feat.json": {"to_skill": "product.epic-to-feat"},
            "execution-evidence.json": {"run_id": run_id, "decision": "pass"},
            "supervision-evidence.json": {"run_id": run_id, "decision": "pass"},
        }
        for name, payload in payloads.items():
            (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return package_dir

    def base_epic_json(self) -> dict[str, object]:
        return {
            "artifact_type": "epic_freeze_package",
            "workflow_key": "product.src-to-epic",
            "workflow_run_id": "epic-src001",
            "title": "Managed Artifact IO Governance Foundation",
            "status": "accepted",
            "schema_version": "1.0.0",
            "epic_freeze_ref": "EPIC-SRC001",
            "src_root_id": "SRC-001",
            "source_refs": ["product.src-to-epic::src001", "EPIC-SRC001", "SRC-001", "ADR-005"],
            "business_goal": "把受治理的 artifact IO 主链收敛成统一底座，并能通过真实 skill 接入验证闭环成立。",
            "business_value_problem": [
                "现有多个 governed skill 仍在自由读写文件，正式 consumer 也会靠目录扫描消费上下游产物。",
                "需要把主链治理能力收口成一个可继续拆分和验证的统一产品能力块。",
            ],
            "product_positioning": "该 EPIC 位于主链治理产品层，负责把候选提交、gate 裁决、formal 输出、受治理 IO 和 skill 接入验证收束为统一能力块。",
            "actors_and_roles": [
                {"role": "workflow 设计者", "responsibility": "定义主链能力边界和下游 FEAT 分解方式。"},
                {"role": "governed skill 作者", "responsibility": "让业务 skill 通过统一主链提交与消费治理对象。"},
            ],
            "scope": [
                "主链协作闭环能力：统一 execution、gate、human loop 的交接与回流。",
                "正式交接与物化能力：统一 handoff、gate decision、formal materialization。",
                "对象分层与准入能力：统一 candidate、formal、consumer admission。",
                "主链文件 IO 与路径治理能力：统一 mainline IO/path 边界。",
            ],
            "upstream_and_downstream": [
                "Upstream：承接 freeze-ready 的 SRC 包。",
                "Downstream：拆成多个可独立验收的 FEAT，并交接给 delivery-prep / plan / TECH / TESTSET。",
            ],
            "epic_success_criteria": [
                "下游 FEAT 可以独立描述主链业务流和交付物。",
                "真实 producer -> consumer -> audit -> gate pilot 可被验证。",
            ],
            "non_goals": ["不直接下沉到 TASK 或代码实现。"],
            "decomposition_rules": [
                "按独立验收的产品行为切片拆分 FEAT，不按实现顺序、能力轴名称或单一任务切分。",
                "FEAT 的 primary decomposition unit 是产品行为切片；capability axes 只作为 cross-cutting constraints 保留，不直接等同于 FEAT。",
            ],
            "product_behavior_slices": [
                {
                    "id": "collaboration-loop",
                    "name": "主链候选提交与交接流",
                    "track": "foundation",
                    "goal": "冻结 governed skill 如何提交 authoritative handoff。",
                    "scope": [
                        "定义 candidate package、proposal、evidence 在什么触发场景下被提交。",
                        "定义提交后形成什么 authoritative handoff object。",
                        "定义提交完成后哪些业务结果对上游和 gate 可见。",
                    ],
                    "product_surface": "候选提交与交接产品界面",
                    "completed_state": "authoritative handoff object 已建立并进入 gate 消费链。",
                    "business_deliverable": "可被 gate 正式消费的 authoritative handoff submission",
                    "capability_axes": ["主链协作闭环能力"],
                },
                {
                    "id": "handoff-formalization",
                    "name": "主链 gate 审核与裁决流",
                    "track": "foundation",
                    "goal": "冻结 gate 审核与裁决以及 formal 发布 trigger。",
                    "scope": [
                        "定义 gate 如何审核 candidate handoff。",
                        "定义 approve / revise / retry / handoff / reject 的业务结果。",
                        "定义 decision object 如何成为 formal 发布 trigger。",
                    ],
                    "product_surface": "gate 审核与裁决产品界面",
                    "completed_state": "authoritative decision object 已形成。",
                    "business_deliverable": "可被 execution 或 formal 发布链消费的 authoritative decision result",
                    "capability_axes": ["正式交接与物化能力", "主链协作闭环能力"],
                },
                {
                    "id": "object-layering",
                    "name": "formal 发布与下游准入流",
                    "track": "foundation",
                    "goal": "冻结 formal 发布与下游准入。",
                    "scope": [
                        "定义 approved decision 之后何时形成 formal output。",
                        "定义 formal ref / lineage 如何成为 downstream authoritative input。",
                        "定义 consumer admission 的业务前置条件。",
                    ],
                    "product_surface": "formal 发布与准入产品界面",
                    "completed_state": "formal publication package 已形成且可被 admission 消费。",
                    "business_deliverable": "可被 downstream consumer 正式消费的 formal publication package",
                    "capability_axes": ["对象分层与准入能力", "正式交接与物化能力"],
                },
                {
                    "id": "artifact-io-governance",
                    "name": "主链受治理 IO 落盘与读取流",
                    "track": "foundation",
                    "goal": "冻结主链 governed write/read 边界。",
                    "scope": [
                        "定义哪些业务动作必须 governed write/read。",
                        "定义业务发起方在什么节点进行正式读写。",
                        "定义 authoritative receipt / managed ref 的业务结果。",
                    ],
                    "product_surface": "受治理 IO 产品界面",
                    "completed_state": "正式主链读写都形成 authoritative receipt / managed ref。",
                    "business_deliverable": "可审计、可追踪、可复用的 governed write/read result",
                    "capability_axes": ["主链文件 IO 与路径治理能力"],
                },
            ],
            "constraints_and_dependencies": [
                "所有正式写入必须经由 Gateway。",
                "managed read 必须经由 Gateway -> Registry guard。",
                "Path Policy 是唯一政策源。",
                "治理主链成立不能只靠组件内自测。",
            ],
            "capability_axes": [
                {"id": "collaboration-loop", "name": "主链协作闭环能力", "scope": "统一协作 loop 边界。", "feat_axis": "loop collaboration"},
                {"id": "handoff-formalization", "name": "正式交接与物化能力", "scope": "统一 handoff 与 formalization。", "feat_axis": "formalization"},
                {"id": "object-layering", "name": "对象分层与准入能力", "scope": "统一对象分层与准入。", "feat_axis": "object layering"},
                {"id": "artifact-io-governance", "name": "主链文件 IO 与路径治理能力", "scope": "统一 mainline IO/path 边界。", "feat_axis": "artifact io governance"},
            ],
            "rollout_requirement": {"required": False},
            "rollout_plan": {"required_feat_tracks": ["foundation"], "required_feat_families": []},
        }

    def test_standard_epic_keeps_foundation_feats_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epic = self.base_epic_json()
            input_dir = self.make_epic_package(repo_root, "epic-basic", epic)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "feat-basic")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "feat-freeze-bundle.json").read_text(encoding="utf-8"))
            axis_ids = {feature["axis_id"] for feature in bundle["features"]}

            self.assertEqual(len(bundle["feat_refs"]), 4)
            self.assertTrue(all(ref.startswith("FEAT-SRC-001-") for ref in bundle["feat_refs"]))
            self.assertNotIn("skill-adoption-e2e", axis_ids)
            first_feat = bundle["features"][0]
            self.assertEqual(first_feat["title"], "主链候选提交与交接流")
            self.assertIn("identity_and_scenario", first_feat)
            self.assertIn("business_flow", first_feat)
            self.assertIn("product_objects_and_deliverables", first_feat)
            self.assertIn("collaboration_and_timeline", first_feat)
            self.assertIn("frozen_downstream_boundary", first_feat)
            self.assertIn("glossary", bundle)
            self.assertIn("prohibited_inference_rules", bundle)
            self.assertTrue(bundle["glossary"])
            self.assertTrue(bundle["prohibited_inference_rules"])
            self.assertIn("upstream_feat", first_feat)
            self.assertIn("downstream_feat", first_feat)
            self.assertIn("consumes", first_feat)
            self.assertIn("produces", first_feat)
            self.assertIn("authoritative_artifact", first_feat)
            self.assertIn("gate_decision_dependency_feat_refs", first_feat)
            self.assertIn("gate_decision_dependency", first_feat)
            self.assertIn("admission_dependency_feat_refs", first_feat)
            self.assertIn("admission_dependency", first_feat)
            self.assertIn("dependency_kinds", first_feat)
            self.assertTrue(first_feat["identity_and_scenario"]["product_interface"])
            self.assertTrue(first_feat["identity_and_scenario"]["completed_state"])
            self.assertTrue(first_feat["product_objects_and_deliverables"]["business_deliverable"])
            self.assertNotIn("re-entry command", first_feat["product_objects_and_deliverables"]["output_objects"])
            self.assertIn("submission accepted marker", first_feat["product_objects_and_deliverables"]["output_objects"])
            self.assertIn("authoritative handoff submission", first_feat["product_objects_and_deliverables"]["required_deliverables"])
            self.assertIn("authoritative handoff object -> gate pending state", first_feat["collaboration_and_timeline"]["handoff_points"])
            self.assertIn("gate pending visibility", first_feat["acceptance_and_testability"]["test_dimensions"])
            self.assertNotIn("retry path", first_feat["acceptance_and_testability"]["test_dimensions"])
            self.assertNotIn("adoption/E2E landing work", bundle["bundle_intent"])
            self.assertTrue((artifacts_dir / "_cli" / "feat-freeze-executor-commit.response.json").exists())
            self.assertTrue((repo_root / "artifacts" / "registry" / "epic-to-feat-feat-basic-feat-freeze-bundle.json").exists())

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_rollout_required_epic_generates_adoption_e2e_feat(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epic = self.base_epic_json()
            epic["rollout_requirement"] = {"required": True}
            epic["rollout_plan"] = {
                "required_feat_tracks": ["foundation", "adoption_e2e"],
                "required_feat_families": [
                    {"family": "skill_onboarding"},
                    {"family": "migration_cutover"},
                    {"family": "cross_skill_e2e_validation"},
                ],
            }
            epic["source_refs"].append("ARCH-SRC-001-001")
            input_dir = self.make_epic_package(repo_root, "epic-rollout", epic)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "feat-rollout")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "feat-freeze-bundle.json").read_text(encoding="utf-8"))
            markdown = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")
            axis_ids = {feature["axis_id"] for feature in bundle["features"]}
            adoption_feat = next(feature for feature in bundle["features"] if feature["axis_id"] == "skill-adoption-e2e")

            self.assertEqual(len(bundle["feat_refs"]), 5)
            self.assertTrue(all(ref.startswith("FEAT-SRC-001-") for ref in bundle["feat_refs"]))
            self.assertIn("skill-adoption-e2e", axis_ids)
            self.assertIn("adoption/E2E landing work", bundle["bundle_intent"])
            self.assertIn("governed skill 接入与 pilot 验证流", adoption_feat["title"])
            self.assertTrue(any("pilot chain" in item or "producer -> consumer -> audit -> gate" in item for item in adoption_feat["scope"]))
            self.assertIn("pilot evidence 要求", adoption_feat["product_objects_and_deliverables"]["required_deliverables"])
            self.assertIn("## FEAT Bundle Intent", markdown)
            self.assertIn("## Canonical Glossary", markdown)
            self.assertIn("#### Identity and Scenario", markdown)
            self.assertIn("#### Business Flow", markdown)
            self.assertIn("#### Product Objects and Deliverables", markdown)
            self.assertIn("#### Collaboration and Timeline", markdown)
            self.assertIn("#### Frozen Downstream Boundary", markdown)
            self.assertIn("## Prohibited Inference Rules", markdown)
            self.assertIn("governed skill 接入与 pilot 验证流", markdown)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_mainline_rollout_injects_adr005_prereq_and_track_map(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epic = self.base_epic_json()
            epic["title"] = "主链正式交接与治理闭环统一能力"
            epic["source_refs"] = [
                "product.src-to-epic::mainline",
                "EPIC-MAINLINE-001",
                "SRC-MAINLINE-001",
                "ADR-001",
                "ADR-003",
                "ADR-006",
            ]
            epic["rollout_requirement"] = {"required": True}
            epic["rollout_plan"] = {
                "required_feat_tracks": ["foundation", "adoption_e2e"],
                "required_feat_families": [
                    {"family": "skill_onboarding"},
                    {"family": "migration_cutover"},
                    {"family": "cross_skill_e2e_validation"},
                ],
            }
            input_dir = self.make_epic_package(repo_root, "epic-mainline", epic)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "feat-mainline")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "feat-freeze-bundle.json").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-feat-downstreams.json").read_text(encoding="utf-8"))
            markdown = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")

            self.assertIn("ADR-005", bundle["source_refs"])
            self.assertTrue(bundle["epic_context"]["prerequisite_foundations"])
            self.assertTrue(handoff["prerequisite_foundations"])
            self.assertTrue(bundle["glossary"])
            self.assertTrue(bundle["prohibited_inference_rules"])
            self.assertTrue(handoff["glossary"])
            self.assertTrue(handoff["prohibited_inference_rules"])
            self.assertTrue(handoff["authoritative_artifact_map"])
            self.assertTrue(handoff["feature_dependency_map"])
            self.assertEqual(handoff["feat_track_map"][-1]["track"], "adoption_e2e")
            self.assertTrue(all(item["track"] == "foundation" for item in handoff["feat_track_map"][:-1]))
            self.assertIn("prerequisite_foundations", markdown)
            self.assertIn("只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力", markdown)
            self.assertIn("## Canonical Glossary", markdown)
            self.assertIn("## Prohibited Inference Rules", markdown)

            io_feat = next(feature for feature in bundle["features"] if feature["axis_id"] == "artifact-io-governance")
            gate_feat = next(feature for feature in bundle["features"] if feature["axis_id"] == "handoff-formalization")
            formal_feat = next(feature for feature in bundle["features"] if feature["axis_id"] == "object-layering")
            adoption_feat = next(feature for feature in bundle["features"] if feature["axis_id"] == "skill-adoption-e2e")
            self.assertEqual(io_feat["track"], "foundation")
            self.assertTrue(any("ADR-005" in item for item in io_feat["constraints"]))
            self.assertEqual(io_feat["title"], "主链受治理 IO 落盘与读取流")
            self.assertTrue(io_feat["product_objects_and_deliverables"]["authoritative_output"])
            self.assertEqual(formal_feat["identity_and_scenario"]["primary_actor"], "formalization actor / downstream admission owner")
            self.assertIn("decision object -> execution loop / delegated handler / formal publication flow", gate_feat["collaboration_and_timeline"]["handoff_points"])
            self.assertIn("[Delegated Handler]", gate_feat["collaboration_and_timeline"]["business_sequence"])
            self.assertIn("approve -> [Formal Publication Flow]", gate_feat["collaboration_and_timeline"]["business_sequence"])
            self.assertIn("handoff delegation path", gate_feat["acceptance_and_testability"]["test_dimensions"])
            self.assertIn("admission reject path", formal_feat["acceptance_and_testability"]["test_dimensions"])
            self.assertNotIn("retry path", formal_feat["acceptance_and_testability"]["test_dimensions"])
            self.assertIn("idempotent repeat write", io_feat["acceptance_and_testability"]["test_dimensions"])
            self.assertIn("pilot evidence 要求", adoption_feat["product_objects_and_deliverables"]["required_deliverables"])
            self.assertIn("fallback path", adoption_feat["acceptance_and_testability"]["test_dimensions"])
            self.assertEqual(gate_feat["authoritative_artifact"], "authoritative decision object")
            self.assertIn(formal_feat["feat_ref"], gate_feat["downstream_feat"])
            self.assertIn(gate_feat["feat_ref"], formal_feat["upstream_feat"])
            self.assertIn("authoritative decision object", formal_feat["consumes"])
            self.assertEqual(gate_feat["gate_decision_dependency_feat_refs"], [])
            self.assertEqual(formal_feat["gate_decision_dependency_feat_refs"], [gate_feat["feat_ref"]])
            self.assertEqual(formal_feat["admission_dependency_feat_refs"], [])
            self.assertEqual(io_feat["admission_dependency_feat_refs"], [formal_feat["feat_ref"]])

    def test_review_projection_epic_preserves_semantic_lock_in_feat_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epic = {
                "artifact_type": "epic_freeze_package",
                "workflow_key": "product.src-to-epic",
                "workflow_run_id": "epic-adr015",
                "title": "Gate 审核投影视图与 SSOT 回写统一能力",
                "status": "accepted",
                "schema_version": "1.0.0",
                "epic_freeze_ref": "EPIC-ADR015",
                "src_root_id": "SRC-ADR015",
                "source_refs": ["product.raw-to-src::src-adr015", "EPIC-ADR015", "SRC-ADR015", "ADR-015"],
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
                "business_goal": "把 Machine SSOT 在 gate 阶段翻译成稳定的人类审核视图，并保持 Projection 只是 derived-only review artifact。",
                "business_value_problem": ["gate reviewer 需要自己拼装主线和边界，审核成本高。", "Projection 不能成为新的真相源。"],
                "product_positioning": "该 EPIC 位于 gate 审核视图层，服务 reviewer 的快速理解与判断。",
                "actors_and_roles": [
                    {"role": "gate reviewer", "responsibility": "基于 Projection 做审核判断。"},
                    {"role": "SSOT owner", "responsibility": "把审核意见回写到 Machine SSOT。"},
                ],
                "scope": ["统一上位产品能力：在 gate 阶段生成 Human Review Projection，并保持 SSOT 仍是唯一权威源。"],
                "upstream_and_downstream": ["Upstream：Machine SSOT。", "Downstream：FEAT / TECH 继续只继承 SSOT。"],
                "epic_success_criteria": ["reviewer 能直接看到 Projection、Snapshot、Focus/Risk 和 writeback 边界。"],
                "non_goals": ["本 EPIC 不定义 mainline runtime governance。"],
                "decomposition_rules": [
                    "按独立验收的产品行为切片拆分 FEAT。",
                    "FEAT 的 primary decomposition unit 是 Projection 生成、Snapshot 提取、Review Focus/Risk 提示和反馈回写这些审核视图切片。",
                ],
                "product_behavior_slices": [
                    {
                        "id": "projection-generation",
                        "name": "Human Review Projection 生成流",
                        "track": "foundation",
                        "goal": "冻结 gate 审核阶段如何从 Machine SSOT 生成一份人类友好的 Projection，并保持 Projection 只是派生视图。",
                        "scope": [
                            "定义 Projection 在什么 gate 触发点生成，以及输入只允许来自 Machine SSOT。",
                            "定义 Projection 必须包含的固定模板块，避免每次自由发挥。",
                            "定义 Projection 生成后如何标识 derived-only / non-authoritative / non-inheritable。",
                        ],
                        "product_surface": "Projection 生成流：从 Machine SSOT 派生一份 gate 审核可读视图",
                        "completed_state": "审核人能看到一份由最新 SSOT 渲染的 Human Review Projection，且该视图明确不是新的真相源。",
                        "business_deliverable": "给审核人使用的 Human Review Projection。",
                        "user_story": "As a gate reviewer, I want a human-friendly Projection generated from the latest Machine SSOT, so that I can understand the product quickly without treating the view as a new source of truth.",
                        "trigger": "当 Machine SSOT 进入 gate 审核阶段并需要给人类 reviewer 展示时。",
                        "main_flow": ["读取最新 Machine SSOT authoritative 内容。", "按固定模板渲染 Projection。", "显式标记派生属性。", "提供给 reviewer 使用。"],
                        "business_sequence": "Projection render sequence",
                        "loop_gate_human_involvement": ["Gate reviewer 阅读 Projection。"],
                        "test_dimensions": ["happy path", "template completeness", "derived-only marker presence", "source traceability"],
                        "frozen_product_shape": ["冻结 Projection 模板。"],
                        "open_technical_decisions": ["renderer implementation"],
                        "authoritative_output": "Human Review Projection（derived review artifact）",
                        "constraints": ["Projection 输入只能来自 SSOT。", "Projection 必须显式标记非权威。", "Projection 模板必须稳定。", "Projection 不能成为下游输入。"],
                        "acceptance_checks": [
                            {"id": "pg-1", "scenario": "Projection derives from SSOT", "given": "Machine SSOT exists", "when": "Projection renders", "then": "Projection must derive only from SSOT.", "trace_hints": ["Projection", "SSOT"]},
                            {"id": "pg-2", "scenario": "Projection is non-authoritative", "given": "reviewer reads Projection", "when": "artifact markers are inspected", "then": "Projection must be marked non-authoritative.", "trace_hints": ["non-authoritative"]},
                            {"id": "pg-3", "scenario": "Projection template is stable", "given": "same SSOT type", "when": "Projection rerenders", "then": "template must stay stable.", "trace_hints": ["stable template"]},
                        ],
                    },
                    {
                        "id": "authoritative-snapshot",
                        "name": "Authoritative Snapshot 生成流",
                        "track": "foundation",
                        "goal": "冻结 Projection 中的 Authoritative Snapshot 如何从 SSOT 稳定提取。",
                        "scope": ["提取 completed state。", "提取 authoritative output。", "提取 frozen boundary 和 open technical decisions。"],
                        "product_surface": "Authoritative Snapshot 流：从 SSOT 提取审核必看的权威约束短摘要",
                        "completed_state": "审核人能在 Projection 中快速看到 authoritative output、completed state 和 frozen boundary。",
                        "business_deliverable": "给审核人快速校验的 Authoritative Snapshot。",
                        "trigger": "当 Projection 已生成并需要补齐权威约束短摘要时。",
                        "main_flow": ["读取 SSOT authoritative fields。", "提取关键字段。", "写入 Snapshot 区块。"],
                        "business_sequence": "Snapshot sequence",
                        "loop_gate_human_involvement": ["Gate reviewer 阅读 Snapshot。"],
                        "test_dimensions": ["field presence", "snapshot completeness", "authoritative traceability", "no new authority added"],
                        "frozen_product_shape": ["冻结 Snapshot 必含字段集合。"],
                        "open_technical_decisions": ["extractor implementation"],
                        "authoritative_output": "Authoritative Snapshot",
                        "constraints": ["Snapshot 只提取 SSOT 已有字段。", "Snapshot 必须包含关键权威字段。", "Snapshot 不能新增权威定义。", "Snapshot 必须可追溯到 SSOT。"],
                        "acceptance_checks": [
                            {"id": "as-1", "scenario": "Snapshot has hard constraints", "given": "SSOT has authoritative fields", "when": "Snapshot renders", "then": "Snapshot must include them.", "trace_hints": ["Snapshot"]},
                            {"id": "as-2", "scenario": "Reviewer does not reconstruct fields", "given": "reviewer reads Snapshot", "when": "checking constraints", "then": "hard constraints must be visible directly.", "trace_hints": ["reviewer"]},
                            {"id": "as-3", "scenario": "Snapshot stays non-authoritative", "given": "Snapshot is compared with SSOT", "when": "authority is checked", "then": "it must remain a projection.", "trace_hints": ["projection"]},
                        ],
                    },
                    {
                        "id": "review-focus-risk",
                        "name": "Review Focus 与风险提示流",
                        "track": "foundation",
                        "goal": "冻结系统如何从 SSOT 自动整理 review focus、risks 与 ambiguities。",
                        "scope": ["整理 review focus。", "识别风险与歧义。", "写入 Projection。"],
                        "product_surface": "Review Focus 流：自动整理审核重点、风险与歧义点",
                        "completed_state": "审核人能直接看到本轮该盯哪些问题和有哪些风险点。",
                        "business_deliverable": "给审核人聚焦判断的 Review Focus / Risks / Ambiguities 摘要。",
                        "trigger": "当 Projection 已生成并需要补齐审核重点与风险提示时。",
                        "main_flow": ["提取边界和交付物信号。", "整理 Focus。", "归纳 Risk。", "写入 Projection。"],
                        "business_sequence": "Focus risk sequence",
                        "loop_gate_human_involvement": ["Gate reviewer 按重点项判断。"],
                        "test_dimensions": ["focus coverage", "risk coverage", "ambiguity coverage", "no new authority added"],
                        "frozen_product_shape": ["冻结 Focus/Risk 模板位置。"],
                        "open_technical_decisions": ["ambiguity detector"],
                        "authoritative_output": "Review Focus / Risks / Ambiguities 摘要",
                        "constraints": ["Focus 必须覆盖关键判断点。", "Risk 只能基于 SSOT。", "风险提示不能升级成新权威。", "输出必须面向 reviewer 可判断。"],
                        "acceptance_checks": [
                            {"id": "rf-1", "scenario": "Focus covers key points", "given": "reviewer prepares decision", "when": "Focus renders", "then": "it must cover key judgment points.", "trace_hints": ["Focus"]},
                            {"id": "rf-2", "scenario": "Risks surface omissions", "given": "SSOT may have ambiguity", "when": "risk extraction runs", "then": "it must surface them.", "trace_hints": ["Risk"]},
                            {"id": "rf-3", "scenario": "Hints stay non-authoritative", "given": "hints are compared with SSOT", "when": "authority is checked", "then": "they must not become a new truth source.", "trace_hints": ["non-authoritative"]},
                        ],
                    },
                    {
                        "id": "feedback-writeback",
                        "name": "Projection 批注回写流",
                        "track": "foundation",
                        "goal": "冻结 gate 审核意见如何回写到 Machine SSOT，并要求回写后重新生成 Projection。",
                        "scope": ["映射评论到 SSOT。", "回写 authoritative 字段。", "重生成 Projection。"],
                        "product_surface": "反馈回写流：审核意见回写 SSOT 并触发 Projection 重生成",
                        "completed_state": "审核意见已沉淀回 Machine SSOT，Projection 已基于最新 SSOT 重生成。",
                        "business_deliverable": "可追踪的 SSOT 修订请求与重生成后的 Projection。",
                        "trigger": "当 reviewer 在 gate 上对 Projection 提出修订意见时。",
                        "main_flow": ["reviewer 提出意见。", "映射到 SSOT。", "更新 SSOT。", "重生成 Projection。"],
                        "business_sequence": "Writeback sequence",
                        "loop_gate_human_involvement": ["Gate reviewer 提意见。", "SSOT owner 完成回写。"],
                        "test_dimensions": ["writeback traceability", "projection regeneration", "single source of truth preserved", "projection not directly editable"],
                        "frozen_product_shape": ["冻结 writeback 必须回到 Machine SSOT 的规则。"],
                        "open_technical_decisions": ["comment mapping implementation"],
                        "authoritative_output": "SSOT revision request + regenerated Projection",
                        "constraints": ["审核意见不能停留在 Projection。", "修订必须回写 SSOT。", "Projection 必须重生成。", "下游继承仍只认 SSOT。"],
                        "acceptance_checks": [
                            {"id": "fw-1", "scenario": "Comments do not terminate on Projection", "given": "reviewer leaves comment", "when": "revision runs", "then": "comment must map back to SSOT.", "trace_hints": ["writeback"]},
                            {"id": "fw-2", "scenario": "Projection regenerates after SSOT change", "given": "SSOT updated", "when": "Projection requested again", "then": "Projection must regenerate.", "trace_hints": ["regenerate"]},
                            {"id": "fw-3", "scenario": "Downstream still inherits SSOT", "given": "downstream needs authoritative input", "when": "handoff occurs", "then": "downstream must still inherit SSOT only.", "trace_hints": ["SSOT only"]},
                        ],
                    },
                ],
                "constraints_and_dependencies": ["Projection 不能成为新的真相源。", "审核意见必须回写 Machine SSOT。"],
                "capability_axes": [
                    {"id": "projection-generation", "name": "Gate Projection 生成能力", "scope": "从 Machine SSOT 生成 Projection。", "feat_axis": "Human Review Projection 生成流"},
                    {"id": "authoritative-snapshot", "name": "Authoritative Snapshot 摘要能力", "scope": "提取权威约束。", "feat_axis": "Authoritative Snapshot 生成流"},
                    {"id": "review-focus-risk", "name": "Review Focus 与风险提示能力", "scope": "提取重点与风险。", "feat_axis": "Review Focus 与风险提示流"},
                    {"id": "feedback-writeback", "name": "Projection 批注回写能力", "scope": "回写 SSOT 并重生成 Projection。", "feat_axis": "Projection 批注回写流"},
                ],
                "rollout_requirement": {"required": False},
                "rollout_plan": {"required_feat_tracks": ["foundation"], "required_feat_families": []},
            }
            input_dir = self.make_epic_package(repo_root, "epic-adr015", epic)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "feat-adr015")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "feat-freeze-bundle.json").read_text(encoding="utf-8"))
            drift = json.loads((artifacts_dir / "semantic-drift-check.json").read_text(encoding="utf-8"))
            titles = [feature["title"] for feature in bundle["features"]]

            self.assertEqual(bundle["semantic_lock"]["domain_type"], "review_projection_rule")
            self.assertEqual(titles, ["Human Review Projection 生成流", "Authoritative Snapshot 生成流", "Review Focus 与风险提示流", "Projection 批注回写流"])
            self.assertTrue(drift["semantic_lock_preserved"])
            self.assertEqual(drift["verdict"], "pass")
            self.assertFalse(drift["forbidden_axis_detected"])
