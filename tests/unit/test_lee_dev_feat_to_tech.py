import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-dev-feat-to-tech" / "scripts" / "feat_to_tech.py"


class FeatToTechWorkflowTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def make_feat_package(self, root: Path, run_id: str, bundle_json: dict[str, object]) -> Path:
        package_dir = root / "artifacts" / "epic-to-feat" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "workflow_run_id": run_id,
            "status": bundle_json["status"],
            "schema_version": bundle_json["schema_version"],
            "epic_freeze_ref": bundle_json["epic_freeze_ref"],
            "src_root_id": bundle_json["src_root_id"],
            "feat_refs": bundle_json["feat_refs"],
        }
        markdown = [
            "---",
            *[f"{key}: {value}" for key, value in frontmatter.items() if key != "feat_refs"],
            "feat_refs:",
            *[f"  - {item}" for item in bundle_json["feat_refs"]],
            "source_refs:",
            *[f"  - {item}" for item in bundle_json["source_refs"]],
            "---",
            "",
            f"# {bundle_json['title']}",
            "",
            "## FEAT Bundle Intent",
            "",
            str(bundle_json["bundle_intent"]),
            "",
            "## EPIC Context",
            "",
            f"- epic_freeze_ref: {bundle_json['epic_freeze_ref']}",
            f"- src_root_id: {bundle_json['src_root_id']}",
            "",
            "## Boundary Matrix",
            "",
            *[f"- {item['feat_ref']}: {item['title']}" for item in bundle_json["boundary_matrix"]],
            "",
            "## FEAT Inventory",
            "",
            *[f"### {feature['feat_ref']} {feature['title']}" for feature in bundle_json["features"]],
            "",
            "## Acceptance and Review",
            "",
            "- upstream acceptance: approve",
            "",
            "## Downstream Handoff",
            "",
            "- workflow.product.task.feat_to_delivery_prep",
            "",
            "## Traceability",
            "",
            *[f"- {item}" for item in bundle_json["source_refs"]],
        ]
        (package_dir / "feat-freeze-bundle.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
        (package_dir / "feat-freeze-bundle.json").write_text(
            json.dumps(bundle_json, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        payloads = {
            "package-manifest.json": {"status": bundle_json["status"], "run_id": run_id},
            "feat-review-report.json": {"decision": "pass", "summary": "review ok"},
            "feat-acceptance-report.json": {"decision": "approve", "summary": "acceptance ok"},
            "feat-defect-list.json": [],
            "feat-freeze-gate.json": {"workflow_key": "product.epic-to-feat", "freeze_ready": True, "decision": "pass"},
            "handoff-to-feat-downstreams.json": {
                "target_workflows": [
                    {"workflow": "workflow.product.task.feat_to_delivery_prep"},
                    {"workflow": "workflow.product.feat_to_plan_pipeline"},
                ],
                "derivable_children": ["TECH", "TASK", "TESTSET"],
            },
            "execution-evidence.json": {"run_id": run_id, "decision": "pass"},
            "supervision-evidence.json": {"run_id": run_id, "decision": "pass"},
        }
        for name, payload in payloads.items():
            (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return package_dir

    def make_bundle_json(self, feature: dict[str, object], run_id: str = "feat-src001") -> dict[str, object]:
        feat_ref = str(feature["feat_ref"])
        return {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "workflow_run_id": run_id,
            "title": f"{feature['title']} FEAT Bundle",
            "status": "accepted",
            "schema_version": "1.0.0",
            "epic_freeze_ref": "EPIC-SRC001",
            "src_root_id": "SRC-001",
            "feat_refs": [feat_ref],
            "downstream_workflows": [
                "workflow.product.task.feat_to_delivery_prep",
                "workflow.product.feat_to_plan_pipeline",
            ],
            "source_refs": [
                f"product.epic-to-feat::{run_id}",
                feat_ref,
                "EPIC-SRC001",
                "SRC-001",
                "ADR-009",
            ],
            "bundle_intent": "Derive a governed FEAT bundle for downstream design work.",
            "boundary_matrix": [
                {
                    "feat_ref": feat_ref,
                    "title": feature["title"],
                    "responsible_for": list(feature["scope"])[:2],
                    "not_responsible_for": list(feature.get("non_goals") or [])[:2],
                    "boundary_dependencies": list(feature.get("dependencies") or []),
                }
            ],
            "features": [feature],
        }

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
                "source_refs": ["FEAT-SRC-001-001", "EPIC-SRC001", "SRC-001", "ARCH-SRC-001-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-required")
            input_dir = self.make_feat_package(repo_root, "feat-required", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-001", "--repo-root", str(repo_root), "--run-id", "tech-required")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            executor_cli = json.loads(
                (artifacts_dir / "_cli" / "tech-design-bundle-executor-commit.response.json").read_text(encoding="utf-8")
            )
            supervisor_cli = json.loads(
                (artifacts_dir / "_cli" / "tech-design-bundle-supervisor-commit.response.json").read_text(encoding="utf-8")
            )
            execution = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))

            self.assertTrue((artifacts_dir / "tech-spec.md").exists())
            self.assertTrue((artifacts_dir / "arch-design.md").exists())
            self.assertTrue((artifacts_dir / "api-contract.md").exists())
            self.assertEqual(design["workflow_key"], "dev.feat-to-tech")
            self.assertTrue(design["arch_required"])
            self.assertTrue(design["api_required"])
            self.assertEqual(design["downstream_handoff"]["target_workflow"], "workflow.dev.tech_to_impl")
            self.assertTrue(design["design_consistency_check"]["passed"])
            self.assertIn("arch-design.md", design["downstream_handoff"]["supporting_artifact_refs"])
            self.assertIn("api-contract.md", design["downstream_handoff"]["supporting_artifact_refs"])
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
                "source_refs": ["FEAT-SRC-001-002", "EPIC-SRC001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-tech-only")
            input_dir = self.make_feat_package(repo_root, "feat-tech-only", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-002", "--repo-root", str(repo_root), "--run-id", "tech-only")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))

            self.assertTrue((artifacts_dir / "tech-spec.md").exists())
            self.assertFalse((artifacts_dir / "arch-design.md").exists())
            self.assertFalse((artifacts_dir / "api-contract.md").exists())
            self.assertFalse(design["arch_required"])
            self.assertFalse(design["api_required"])
            self.assertIsNone(design["artifact_refs"]["arch_spec"])
            self.assertIsNone(design["artifact_refs"]["api_spec"])

    def test_io_path_governance_feat_does_not_force_api_contract(self) -> None:
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
                "source_refs": ["FEAT-SRC-001-004", "EPIC-SRC001", "SRC-001", "ADR-005"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-io-boundary")
            input_dir = self.make_feat_package(repo_root, "feat-io-boundary", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-004", "--repo-root", str(repo_root), "--run-id", "tech-io-boundary")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            arch_body = (artifacts_dir / "arch-design.md").read_text(encoding="utf-8")

            self.assertTrue(design["arch_required"])
            self.assertFalse(design["api_required"])
            self.assertTrue((artifacts_dir / "arch-design.md").exists())
            self.assertFalse((artifacts_dir / "api-contract.md").exists())
            self.assertIn("不得外扩成全局文件治理", arch_body)

    def test_allow_update_removes_stale_optional_api_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-005",
                "title": "主链文件 IO 与路径治理能力",
                "goal": "让主链接入受治理 IO/path 基础，不扩展为额外边界契约设计。",
                "scope": [
                    "定义主链 handoff 与 formal materialization 如何接入受治理 path / mode 能力。",
                    "明确哪些 IO 属于主链 handoff / materialization，哪些不属于。",
                    "要求主链写入遵循受治理路径边界。",
                ],
                "constraints": [
                    "本 FEAT 只定义主链如何消费受治理 IO/path 能力。",
                    "不得外扩成全局文件治理或额外边界契约设计。",
                    "允许 update 重跑时清理与当前 need assessment 不一致的旧产物。",
                ],
                "dependencies": [
                    "Boundary to 正式交接与物化能力: formalization 决策语义不在本 FEAT 内。",
                    "Boundary to 对象分层与准入能力: 对象资格与引用方向不在本 FEAT 内。",
                ],
                "outputs": ["Traceable handoff metadata"],
                "acceptance_checks": [
                    {"scenario": "Mainline IO boundary is explicit", "given": "mainline path boundary", "when": "reviewed", "then": "主链 IO 与其他治理边界清晰"},
                    {"scenario": "Governed path rules are inherited", "given": "formal write path", "when": "validated", "then": "必须使用受治理 path / mode 边界"},
                    {"scenario": "Stale optional artifacts are removed on rerun", "given": "allow-update rerun", "when": "optional contract output is no longer required", "then": "旧契约产物会被删除"},
                ],
                "source_refs": ["FEAT-SRC-001-005", "EPIC-SRC001", "SRC-001", "ADR-005"],
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
                "source_refs": ["FEAT-SRC-001-003", "EPIC-SRC001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-invalid")
            input_dir = self.make_feat_package(repo_root, "feat-invalid", bundle)

            result = self.run_cmd("validate-input", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-404")
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("Selected feat_ref not found" in error for error in payload["errors"]))


if __name__ == "__main__":
    unittest.main()
