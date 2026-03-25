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
            "scope": [
                "主链协作闭环能力：统一 execution、gate、human loop 的交接与回流。",
                "正式交接与物化能力：统一 handoff、gate decision、formal materialization。",
                "对象分层与准入能力：统一 candidate、formal、consumer admission。",
                "主链文件 IO 与路径治理能力：统一 mainline IO/path 边界。",
            ],
            "non_goals": ["不直接下沉到 TASK 或代码实现。"],
            "decomposition_rules": ["capability axes must become independently acceptable FEATs."],
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
            self.assertIn("技能接入与跨 skill 闭环验证能力", adoption_feat["title"])
            self.assertTrue(any("pilot chain" in item or "producer -> consumer -> audit -> gate" in item for item in adoption_feat["scope"]))
            self.assertIn("## FEAT Bundle Intent", markdown)
            self.assertIn("技能接入与跨 skill 闭环验证能力", markdown)

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
            self.assertEqual(handoff["feat_track_map"][-1]["track"], "adoption_e2e")
            self.assertTrue(all(item["track"] == "foundation" for item in handoff["feat_track_map"][:-1]))
            self.assertIn("prerequisite_foundations", markdown)
            self.assertIn("只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力", markdown)

            io_feat = next(feature for feature in bundle["features"] if feature["axis_id"] == "artifact-io-governance")
            self.assertEqual(io_feat["track"], "foundation")
            self.assertTrue(any("ADR-005" in item for item in io_feat["constraints"]))
