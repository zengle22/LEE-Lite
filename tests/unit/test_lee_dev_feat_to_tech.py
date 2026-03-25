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
            self.assertTrue((artifacts_dir / "tech-impl.md").exists())
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
            self.assertIn("lee gate submit-handoff", api_md)
            self.assertIn("lee gate show-pending", api_md)
            self.assertNotIn("lee gate decide", api_md)
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
            self.assertTrue((artifacts_dir / "tech-impl.md").exists())
            self.assertFalse((artifacts_dir / "arch-design.md").exists())
            self.assertFalse((artifacts_dir / "api-contract.md").exists())
            self.assertFalse(design["arch_required"])
            self.assertFalse(design["api_required"])
            self.assertIsNone(design["artifact_refs"]["arch_spec"])
            self.assertIsNone(design["artifact_refs"]["api_spec"])
            self.assertEqual(design["artifact_refs"]["tech_spec"], "tech-spec.md")

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
                "source_refs": ["FEAT-SRC-001-004", "EPIC-SRC001", "SRC-001", "ADR-005"],
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
            self.assertIn("lee artifact commit-governed", api_body)
            self.assertIn("lee artifact read-governed", api_body)
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
                "source_refs": ["FEAT-SRC-001-005", "EPIC-SRC001", "SRC-001"],
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
                "source_refs": ["FEAT-SRC-001-003", "EPIC-SRC001", "SRC-001"],
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
                "source_refs": ["FEAT-SRC-001-010", "EPIC-SRC001", "SRC-001"],
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
            self.assertIn("cli/lib/formalization.py", tech_body)
            self.assertIn("GateDecision", tech_body)
            self.assertIn("lee gate decide", api_body)
            self.assertIn("lee registry publish-formal", api_body)
            self.assertNotIn("validate-admission", api_body)
            self.assertIn("materialization_pending", tech_body)
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
                "source_refs": ["FEAT-SRC-001-002", "EPIC-SRC001", "SRC-001", "ADR-006"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-formalization-api")
            input_dir = self.make_feat_package(repo_root, "feat-formalization-api", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-002", "--repo-root", str(repo_root), "--run-id", "tech-formalization-api")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            api_md = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")

            self.assertIn("lee gate decide", api_md)
            self.assertIn("lee registry publish-formal", api_md)
            self.assertIn("decision_reason", api_md)
            self.assertIn("formal_ref", api_md)
            self.assertIn("decision_not_approvable", api_md)
            self.assertIn("Success envelope", api_md)

    def test_adoption_e2e_feat_emits_api_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-006",
                "title": "governed skill 接入与 pilot 闭环流",
                "axis_id": "skill-adoption-e2e",
                "goal": "让新 skill 能按 onboarding、pilot、cutover/fallback 的主链接入流程稳定落地。",
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
                    {"scenario": "Fallback is explicit", "given": "pilot failure", "when": "cutover reviewed", "then": "fallback outcome 被记录"},
                    {"scenario": "Compat mode is frozen", "given": "legacy skill", "when": "onboarded", "then": "compat mode 明确可追踪"},
                ],
                "source_refs": ["FEAT-SRC-001-006", "EPIC-SRC001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-adoption-api")
            input_dir = self.make_feat_package(repo_root, "feat-adoption-api", bundle)

            result = self.run_cmd("run", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-006", "--repo-root", str(repo_root), "--run-id", "tech-adoption-api")
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            design = json.loads((artifacts_dir / "tech-design-bundle.json").read_text(encoding="utf-8"))
            api_md = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")

            self.assertTrue(design["api_required"])
            self.assertIn("lee rollout onboard-skill", api_md)
            self.assertIn("lee audit submit-pilot-evidence", api_md)
            self.assertIn("compat_mode", api_md)
            self.assertIn("cutover_recommendation", api_md)
            self.assertIn("Canonical refs:", api_md)

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
                "source_refs": ["FEAT-SRC-001-011", "EPIC-SRC001", "SRC-001"],
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
