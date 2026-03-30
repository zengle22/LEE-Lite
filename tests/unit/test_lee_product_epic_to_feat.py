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

    def make_revision_request(self, root: Path, run_id: str, source_run_id: str, reason: str) -> Path:
        revision_request = {
            "workflow_key": "product.epic-to-feat",
            "run_id": run_id,
            "source_run_id": source_run_id,
            "decision_type": "revise",
            "decision_reason": reason,
            "decision_target": f"epic-to-feat.{run_id}.feat-freeze-bundle",
            "basis_refs": ["feat-review-report.json", "feat-acceptance-report.json"],
            "revision_round": 1,
            "source_gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
            "source_return_job_ref": "artifacts/jobs/waiting-human/epic-to-feat-return.json",
            "authoritative_input_ref": f"artifacts/src-to-epic/{source_run_id}",
            "candidate_ref": f"epic-to-feat.{run_id}.feat-freeze-bundle",
            "original_input_path": str(root / "artifacts" / "src-to-epic" / source_run_id),
            "triggered_by_request_id": f"req-{run_id}-revise",
            "trace": {
                "run_ref": run_id,
                "workflow_key": "product.epic-to-feat",
            },
        }
        revision_path = root / "revision-request.json"
        revision_path.write_text(json.dumps(revision_request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return revision_path

    def base_epic_json(self) -> dict[str, object]:
        return {
            "artifact_type": "epic_freeze_package",
            "workflow_key": "product.src-to-epic",
            "workflow_run_id": "epic-src001",
            "title": "Managed Artifact IO Governance Foundation",
            "status": "accepted",
            "schema_version": "1.0.0",
            "epic_freeze_ref": "EPIC-SRC-001-001",
            "src_root_id": "SRC-001",
            "source_refs": ["product.src-to-epic::src001", "EPIC-SRC-001-001", "SRC-001", "ADR-005"],
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
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "feat-freeze-bundle.json").read_text(encoding="utf-8"))
            gate_ready_package = json.loads((artifacts_dir / "input" / "gate-ready-package.json").read_text(encoding="utf-8"))
            package_manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
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
            self.assertTrue((artifacts_dir / "_cli" / "gate-submit-handoff.response.json").exists())
            self.assertTrue((repo_root / "artifacts" / "registry" / "epic-to-feat-feat-basic-feat-freeze-bundle.json").exists())
            self.assertEqual(payload["gate_ready_package_ref"], "artifacts/epic-to-feat/feat-basic/input/gate-ready-package.json")
            self.assertTrue(payload["authoritative_handoff_ref"].startswith("artifacts/active/gates/handoffs/"))
            self.assertTrue(payload["gate_pending_ref"].startswith("artifacts/active/gates/pending/"))
            self.assertEqual(gate_ready_package["payload"]["candidate_ref"], "epic-to-feat.feat-basic.feat-freeze-bundle")
            self.assertEqual(gate_ready_package["payload"]["machine_ssot_ref"], "artifacts/epic-to-feat/feat-basic/feat-freeze-bundle.json")
            self.assertEqual(package_manifest["gate_ready_package_ref"], payload["gate_ready_package_ref"])
            self.assertEqual(package_manifest["gate_pending_ref"], payload["gate_pending_ref"])
            self.assertTrue((repo_root / payload["authoritative_handoff_ref"]).exists())
            self.assertTrue((repo_root / payload["gate_pending_ref"]).exists())

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_revision_request_rerun_materializes_revision_trace_and_updates_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epic = self.base_epic_json()
            input_dir = self.make_epic_package(repo_root, "epic-revise-input", epic)

            first_result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "feat-revise")
            self.assertEqual(first_result.returncode, 0, first_result.stderr)

            revision_request_path = self.make_revision_request(
                repo_root,
                run_id="feat-revise",
                source_run_id="epic-revise-input",
                reason="保留下游 FEAT 边界，但把 revise 上下文显式写入 bundle / evidence / gate。",
            )
            rerun_result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-revise",
                "--allow-update",
                "--revision-request",
                str(revision_request_path),
            )
            self.assertEqual(rerun_result.returncode, 0, rerun_result.stderr)

            payload = json.loads(rerun_result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "feat-freeze-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            execution = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            gate = json.loads((artifacts_dir / "feat-freeze-gate.json").read_text(encoding="utf-8"))
            revision_materialized = json.loads((artifacts_dir / "revision-request.json").read_text(encoding="utf-8"))
            report = (artifacts_dir / "evidence-report.md").read_text(encoding="utf-8")

            self.assertEqual(revision_materialized["revision_round"], 1)
            self.assertEqual(revision_materialized["workflow_key"], "product.epic-to-feat")
            self.assertEqual(bundle["revision_context"]["revision_request_ref"], str(artifacts_dir / "revision-request.json"))
            self.assertIn("Gate revise:", bundle["revision_context"]["summary"])
            self.assertEqual(manifest["revision_request_ref"], str(artifacts_dir / "revision-request.json"))
            self.assertEqual(execution["revision_request_ref"], str(artifacts_dir / "revision-request.json"))
            self.assertEqual(supervision["revision_request_ref"], str(artifacts_dir / "revision-request.json"))
            self.assertEqual(gate["revision_request_ref"], str(artifacts_dir / "revision-request.json"))
            self.assertIn("Revision context absorbed", "\n".join(item["title"] for item in supervision["semantic_findings"]))
            self.assertIn("revision_request_ref", report)

    def test_formal_epic_ref_is_admissible_input_for_epic_to_feat(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epic = self.base_epic_json()
            run_id = "epic-formal-input"
            input_dir = self.make_epic_package(repo_root, run_id, epic)

            formal_epic_path = repo_root / "ssot" / "epic" / "EPIC-SRC-001-001__managed-artifact-io-governance-foundation.md"
            formal_epic_path.parent.mkdir(parents=True, exist_ok=True)
            formal_epic_path.write_text(
                "\n".join(
                    [
                        "---",
                        "id: EPIC-SRC-001-001",
                        "ssot_type: EPIC",
                        "src_ref: SRC-001",
                        "title: Managed Artifact IO Governance Foundation",
                        "goal: 把受治理的 artifact IO 主链收敛成统一底座，并能通过真实 skill 接入验证闭环成立。",
                        "status: frozen",
                        "---",
                        "",
                        "# Managed Artifact IO Governance Foundation",
                        "",
                        "Formal EPIC body.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            registry_dir = repo_root / "artifacts" / "registry"
            registry_dir.mkdir(parents=True, exist_ok=True)
            (registry_dir / "formal-epic-epic-formal-input.json").write_text(
                json.dumps(
                    {
                        "artifact_ref": "formal.epic.epic-formal-input",
                        "managed_artifact_ref": "ssot/epic/EPIC-SRC-001-001__managed-artifact-io-governance-foundation.md",
                        "status": "materialized",
                        "trace": {"run_ref": run_id, "workflow_key": "product.src-to-epic"},
                        "metadata": {
                            "layer": "formal",
                            "source_package_ref": f"artifacts/src-to-epic/{run_id}",
                            "assigned_id": "EPIC-SRC-001-001",
                            "ssot_type": "EPIC",
                        },
                        "lineage": [f"src-to-epic.{run_id}.epic-freeze", "artifacts/active/gates/decisions/gate-decision.json"],
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
                "formal.epic.epic-formal-input",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-from-formal",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["input_mode"], "formal_admission")
            artifacts_dir = Path(payload["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "feat-freeze-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(bundle["epic_freeze_ref"], "EPIC-SRC-001-001")
            self.assertTrue(any(ref == "EPIC-SRC-001-001" for ref in bundle["source_refs"]))
            self.assertEqual(
                manifest["input_artifacts_dir"],
                str((repo_root / "artifacts" / "src-to-epic" / run_id).resolve()),
            )

            validate = self.run_cmd(
                "validate-input",
                "--input",
                "formal.epic.epic-formal-input",
                "--repo-root",
                str(repo_root),
            )
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

    def test_execution_runner_epic_preserves_semantic_lock_in_feat_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epic = {
                "artifact_type": "epic_freeze_package",
                "workflow_key": "product.src-to-epic",
                "workflow_run_id": "epic-adr018",
                "title": "Gate 审批后自动推进 Execution Runner 统一能力",
                "status": "accepted",
                "schema_version": "1.0.0",
                "epic_freeze_ref": "EPIC-ADR018",
                "src_root_id": "SRC-ADR018",
                "source_refs": ["product.raw-to-src::src-adr018", "EPIC-ADR018", "SRC-ADR018", "ADR-018", "ADR-001", "ADR-003", "ADR-005"],
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
                "business_goal": "把 gate approve 后的 ready job、runner 消费、next-skill dispatch 和 execution result 回写冻结成连续的自动推进产品线。",
                "business_value_problem": [
                    "dispatch 已能产出 materialized-job，但系统仍缺少正式 consumer 去自动消费 artifacts/jobs/ready。",
                    "approve 语义被附近的 formal publication 语义覆盖，导致自动推进链丢失。",
                ],
                "product_positioning": "该 EPIC 位于 gate 后自动推进运行时层。",
                "actors_and_roles": [
                    {"role": "gate / reviewer owner", "responsibility": "定义 approve 与非 approve 决策何时产生 ready execution job。"},
                    {"role": "execution runner owner", "responsibility": "负责 ready queue 消费、claim、dispatch 与结果回写。"},
                ],
                "scope": [
                    "统一上位产品能力：形成一条 gate approve 后自动推进到下一 skill 的运行时产品线。",
                    "产品行为切片：批准后 Ready Job 生成流。",
                    "产品行为切片：Runner 用户入口流。",
                    "产品行为切片：Runner 控制面流。",
                    "产品行为切片：Execution Runner 自动取件流。",
                    "产品行为切片：下游 Skill 自动派发流。",
                    "产品行为切片：执行结果回写与重试边界流。",
                    "产品行为切片：Runner 运行监控流。",
                ],
                "upstream_and_downstream": ["Upstream：关于 gate approve 后自动推进缺口的 bridge SRC。", "Downstream：拆成 ready job、runner entry、runner control、runner intake、dispatch、feedback、observability 七个 FEAT。"],
                "epic_success_criteria": [
                    "至少一条 gate approve -> ready execution job -> runner claim -> next skill invocation 的真实链路可被验证。",
                    "approve 后链路不再被改写成 formal publication / admission。",
                ],
                "non_goals": ["本 EPIC 不把 approve 重写成 formal publication。", "本 EPIC 不要求第三会话人工接力作为正常路径。"],
                "decomposition_rules": [
                    "FEAT 的 primary decomposition unit 是 approve 后 ready job 生成、runner 用户入口、runner 控制面、runner intake、next-skill dispatch、execution result feedback 与 runner observability。",
                    "任何 FEAT 都不得把 approve 后链路重写成 formal publication、admission 或人工第三会话接力。",
                ],
                "product_behavior_slices": [
                    {
                        "id": "ready-job-emission",
                        "name": "批准后 Ready Job 生成流",
                        "track": "foundation",
                        "goal": "冻结 gate approve 如何生成 ready execution job。",
                        "scope": ["定义 approve 后必须产出的 ready execution job。", "定义 next skill target 和队列落点。", "定义非 approve 决策与 next-skill queue 的边界。"],
                        "product_surface": "批准后 ready job 生成流：gate approve 生成可被 runner 自动消费的 ready execution job",
                        "completed_state": "批准结果已经物化为 ready execution job，并进入 artifacts/jobs/ready。",
                        "business_deliverable": "给 runner 消费的 ready execution job。",
                        "capability_axes": ["批准后 Ready Job 生成能力"],
                        "acceptance_checks": [
                            {"id": "rj-1", "scenario": "Approve emits ready job", "given": "gate approves", "when": "dispatch ends", "then": "one ready execution job must be emitted.", "trace_hints": ["ready execution job"]},
                            {"id": "rj-2", "scenario": "Approve is not formal publication", "given": "approve path is reviewed", "when": "next step is described", "then": "the path must continue into runner-ready execution.", "trace_hints": ["not formal publication"]},
                            {"id": "rj-3", "scenario": "Non-approve stays out of queue", "given": "gate returns revise/retry/reject/handoff", "when": "dispatch evaluates", "then": "no next-skill ready job may be emitted.", "trace_hints": ["queue boundary"]},
                        ],
                    },
                    {
                        "id": "runner-operator-entry",
                        "name": "Runner 用户入口流",
                        "track": "foundation",
                        "goal": "冻结 Claude/Codex CLI 用户如何通过独立 runner skill 启动或恢复 Execution Loop Job Runner。",
                        "scope": ["定义 runner 独立 skill 入口。", "定义 start / resume 语义。", "定义入口调用如何把运行权交给 runner。"],
                        "product_surface": "Runner 用户入口流：Claude/Codex CLI 用户通过独立 runner skill 启动或恢复自动推进运行时",
                        "completed_state": "用户已经可以通过独立 runner skill 显式启动或恢复 Execution Loop Job Runner，并形成可追踪的 invocation record。",
                        "business_deliverable": "给 operator 使用的 runner skill entry 与启动回执。",
                        "capability_axes": ["Runner 用户入口能力"],
                        "acceptance_checks": [
                            {"id": "re-1", "scenario": "Operator can start runner through skill entry", "given": "operator is in Claude/Codex CLI", "when": "runner skill is invoked", "then": "the system must create one authoritative runner invocation record.", "trace_hints": ["skill entry"]},
                            {"id": "re-2", "scenario": "Operator can resume runner", "given": "a runner context already exists", "when": "resume is requested", "then": "the runner must restore authoritative context instead of starting from guesswork.", "trace_hints": ["resume"]},
                            {"id": "re-3", "scenario": "Skill entry is not manual relay", "given": "post-approve flow is inspected", "when": "runner entry is described", "then": "the entry must not collapse into manual downstream skill relay.", "trace_hints": ["no manual relay"]},
                        ],
                    },
                    {
                        "id": "runner-control-surface",
                        "name": "Runner 控制面流",
                        "track": "foundation",
                        "goal": "冻结 runner 的统一 CLI control surface。",
                        "scope": ["定义 start / claim / run / complete / fail / resume 等控制动作。", "定义控制动作如何校验 run context。", "定义控制记录如何可追踪。"],
                        "product_surface": "Runner 控制面流：operator 通过统一 CLI verbs 控制 Execution Loop Job Runner 的运行动作",
                        "completed_state": "runner 的启动、恢复、控制和收口动作都可以通过统一 CLI control surface 完成，并留下审计记录。",
                        "business_deliverable": "给 operator 使用的 runner CLI control surface 与控制动作记录。",
                        "capability_axes": ["Runner 控制面能力"],
                        "acceptance_checks": [
                            {"id": "rc-1", "scenario": "Control verbs are available", "given": "operator uses the runner CLI surface", "when": "commands are listed", "then": "start, claim, run, complete, fail, and resume verbs must exist.", "trace_hints": ["control verbs"]},
                            {"id": "rc-2", "scenario": "Control action records state change", "given": "operator issues a runner command", "when": "the control action completes", "then": "one authoritative control action record must be written.", "trace_hints": ["control action record"]},
                            {"id": "rc-3", "scenario": "Control surface preserves governance", "given": "runner state is under governance", "when": "a control action runs", "then": "the action must honor authoritative run context and ownership boundaries.", "trace_hints": ["ownership"]},
                        ],
                    },
                    {
                        "id": "execution-runner-intake",
                        "name": "Execution Runner 自动取件流",
                        "track": "foundation",
                        "goal": "冻结 Execution Loop Job Runner 如何自动消费 jobs/ready。",
                        "scope": ["定义 runner 扫描、claim、running 和防重入边界。", "定义 ready -> claimed -> running 的状态转移。", "定义 claim 证据与 ownership 记录。"],
                        "product_surface": "runner 自动取件流：Execution Loop Job Runner claim ready job 并接管执行责任",
                        "completed_state": "ready execution job 已被 runner claim，并进入 running ownership 状态。",
                        "business_deliverable": "claimed execution job / running record。",
                        "capability_axes": ["Execution Runner 取件能力"],
                        "acceptance_checks": [
                            {"id": "ri-1", "scenario": "Ready queue is auto-consumed", "given": "jobs/ready has a job", "when": "runner runs", "then": "runner must claim it.", "trace_hints": ["jobs/ready", "claim"]},
                            {"id": "ri-2", "scenario": "Claim is single-owner", "given": "multiple runner attempts", "when": "claim happens", "then": "only one owner may succeed.", "trace_hints": ["single owner"]},
                            {"id": "ri-3", "scenario": "No manual relay", "given": "next step is reviewed", "when": "runner intake is described", "then": "it must not require manual third-session relay.", "trace_hints": ["no manual relay"]},
                        ],
                    },
                    {
                        "id": "next-skill-dispatch",
                        "name": "下游 Skill 自动派发流",
                        "track": "foundation",
                        "goal": "冻结 claimed execution job 如何自动派发到下一个 governed skill。",
                        "scope": ["定义 next skill target、输入包引用和调用边界。", "定义 authoritative invocation record。", "定义启动失败回写边界。"],
                        "product_surface": "next skill 自动派发流：runner 基于 claimed job 调起下一个 governed skill",
                        "completed_state": "claimed job 已被自动派发到目标 skill，并留下 invocation / execution attempt record。",
                        "business_deliverable": "authoritative invocation / execution attempt record。",
                        "capability_axes": ["下游 Skill 自动派发能力"],
                        "acceptance_checks": [
                            {"id": "nd-1", "scenario": "Dispatch targets declared skill", "given": "runner owns a claimed job", "when": "dispatch starts", "then": "the invocation must target the declared next skill.", "trace_hints": ["next skill"]},
                            {"id": "nd-2", "scenario": "Dispatch preserves lineage", "given": "audit inspects dispatch", "when": "invocation is recorded", "then": "job refs and target-skill lineage must remain visible.", "trace_hints": ["lineage"]},
                            {"id": "nd-3", "scenario": "Dispatch stays automatic", "given": "approve path is reviewed", "when": "the next step is described", "then": "the flow must show automatic runner dispatch.", "trace_hints": ["automatic dispatch"]},
                        ],
                    },
                    {
                        "id": "execution-result-feedback",
                        "name": "执行结果回写与重试边界流",
                        "track": "foundation",
                        "goal": "冻结 runner 执行后的 done / failed / retry-reentry 结果。",
                        "scope": ["定义 execution outcome 和 retry / reentry directive。", "定义 running -> done/failed/retry_return 的边界。", "定义失败证据与上游可见结果。"],
                        "product_surface": "执行结果回写流：runner 把 next-skill execution 结果写回主链状态与后续动作",
                        "completed_state": "执行结果已形成 authoritative outcome；成功、失败和重试回流都具有清晰状态与证据。",
                        "business_deliverable": "execution outcome / retry-reentry directive / failure evidence。",
                        "capability_axes": ["执行结果回写与重试边界能力"],
                        "acceptance_checks": [
                            {"id": "ef-1", "scenario": "Execution outcomes are explicit", "given": "runner finishes", "when": "result is recorded", "then": "done, failed, or retry outcomes must be explicit.", "trace_hints": ["done", "failed", "retry"]},
                            {"id": "ef-2", "scenario": "Retry keeps execution semantics", "given": "another attempt is needed", "when": "the outcome is recorded", "then": "the result must return through retry / reentry semantics.", "trace_hints": ["retry", "reentry"]},
                            {"id": "ef-3", "scenario": "Approve is not terminal", "given": "overall chain is reviewed", "when": "post-approve flow is inspected", "then": "the chain must continue through runner execution and feedback.", "trace_hints": ["approve", "runner", "feedback"]},
                        ],
                    },
                    {
                        "id": "runner-observability-surface",
                        "name": "Runner 运行监控流",
                        "track": "foundation",
                        "goal": "冻结 operator 如何观察 runner backlog、running、failed、deadletters 与 waiting-human。",
                        "scope": ["定义 runner 观测面。", "定义关键状态词表。", "定义 observability snapshot 与 operator 决策边界。"],
                        "product_surface": "Runner 运行监控流：operator 观察 ready backlog、running、failed、deadletters 与 waiting-human 状态",
                        "completed_state": "operator 已可通过统一监控面观察 runner 关键状态，并据此决定恢复、排障或人工介入。",
                        "business_deliverable": "给 operator 使用的 runner observability surface 与状态快照。",
                        "capability_axes": ["Runner 运行监控能力"],
                        "acceptance_checks": [
                            {"id": "ro-1", "scenario": "Ready backlog is visible", "given": "runner has queued jobs", "when": "operator opens the monitor surface", "then": "ready backlog must be visible.", "trace_hints": ["ready backlog"]},
                            {"id": "ro-2", "scenario": "Failure and waiting-human states are visible", "given": "runner has failed or waiting-human work", "when": "monitoring is inspected", "then": "those states must be visible without directory guessing.", "trace_hints": ["failed", "waiting-human"]},
                            {"id": "ro-3", "scenario": "Observability stays traceable", "given": "operator inspects one monitored item", "when": "lineage is followed", "then": "the view must resolve back to authoritative runner records.", "trace_hints": ["lineage"]},
                        ],
                    },
                ],
                "constraints_and_dependencies": [
                    "approve 必须落成 ready execution job。",
                    "runner 必须自动消费 artifacts/jobs/ready。",
                    "不得把 approve 改写成 formal publication。",
                ],
                "capability_axes": [
                    {"id": "ready-job-emission", "name": "批准后 Ready Job 生成能力", "scope": "approve 后生成 ready job", "feat_axis": "approve 后 ready job 生成流"},
                    {"id": "runner-operator-entry", "name": "Runner 用户入口能力", "scope": "通过独立 skill 启动或恢复 runner", "feat_axis": "runner 用户入口流"},
                    {"id": "runner-control-surface", "name": "Runner 控制面能力", "scope": "通过统一 CLI 控制 runner", "feat_axis": "runner 控制面流"},
                    {"id": "execution-runner-intake", "name": "Execution Runner 取件能力", "scope": "runner 自动 claim jobs/ready", "feat_axis": "ready job 自动取件流"},
                    {"id": "next-skill-dispatch", "name": "下游 Skill 自动派发能力", "scope": "runner 派发到下一个 skill", "feat_axis": "next skill 自动派发流"},
                    {"id": "execution-result-feedback", "name": "执行结果回写与重试边界能力", "scope": "runner 记录 done/failed/retry", "feat_axis": "执行结果回写流"},
                    {"id": "runner-observability-surface", "name": "Runner 运行监控能力", "scope": "观察 backlog/running/failed/waiting-human", "feat_axis": "runner 运行监控流"},
                ],
                "rollout_requirement": {"required": False},
                "rollout_plan": {"required_feat_tracks": ["foundation"], "required_feat_families": []},
            }
            input_dir = self.make_epic_package(repo_root, "epic-adr018", epic)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "feat-adr018")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "feat-freeze-bundle.json").read_text(encoding="utf-8"))
            drift = json.loads((artifacts_dir / "semantic-drift-check.json").read_text(encoding="utf-8"))
            axis_ids = [feature["axis_id"] for feature in bundle["features"]]

            self.assertEqual(
                axis_ids,
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
            self.assertEqual(bundle["glossary"][0]["term"], "ready execution job")
            self.assertEqual(bundle["glossary"][0]["must_not_be_confused_with"], "formal publication package")
            self.assertIn("runner skill entry", [item["term"] for item in bundle["glossary"]])
            self.assertIn("runner CLI control surface", [item["term"] for item in bundle["glossary"]])
            self.assertIn("runner observability surface", [item["term"] for item in bundle["glossary"]])
            self.assertEqual(bundle["features"][0]["authoritative_artifact"], "ready execution job")
            self.assertEqual(bundle["features"][1]["authoritative_artifact"], "runner skill entry invocation record")
            self.assertEqual(bundle["features"][2]["authoritative_artifact"], "runner control action record")
            self.assertEqual(bundle["features"][3]["authoritative_artifact"], "claimed execution job")
            self.assertEqual(bundle["features"][4]["authoritative_artifact"], "next-skill invocation record")
            self.assertEqual(bundle["features"][5]["authoritative_artifact"], "execution outcome record")
            self.assertEqual(bundle["features"][6]["authoritative_artifact"], "runner observability snapshot")
