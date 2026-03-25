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
