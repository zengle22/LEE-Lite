import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-qa-feat-to-testset" / "scripts" / "feat_to_testset.py"


class FeatToTestSetWorkflowTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def make_bundle_json(self, feature: dict[str, object], run_id: str) -> dict[str, object]:
        feat_ref = str(feature["feat_ref"])
        return {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "workflow_run_id": run_id,
            "title": f"{feature['title']} FEAT Freeze Bundle",
            "status": "accepted",
            "schema_version": "1.0.0",
            "epic_freeze_ref": "EPIC-SRC-001",
            "src_root_id": "SRC-001",
            "feat_refs": [feat_ref],
            "source_refs": [
                f"product.epic-to-feat::{run_id}",
                feat_ref,
                "EPIC-SRC-001",
                "SRC-001",
                "ADR-012",
            ],
            "features": [feature],
        }

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
        }
        markdown = [
            "---",
            *[f"{key}: {value}" for key, value in frontmatter.items()],
            "source_refs:",
            *[f"  - {item}" for item in bundle_json["source_refs"]],
            "---",
            "",
            f"# {bundle_json['title']}",
            "",
            "## FEAT Inventory",
            "",
            *[f"### {feature['feat_ref']} {feature['title']}" for feature in bundle_json["features"]],
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
                "target_workflows": [{"workflow": "workflow.qa.test_set_production_l3"}],
                "derivable_children": ["TECH", "TASK", "TESTSET"],
            },
            "execution-evidence.json": {"run_id": run_id, "decision": "pass"},
            "supervision-evidence.json": {"run_id": run_id, "decision": "pass"},
        }
        for name, payload in payloads.items():
            (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return package_dir

    def test_run_emits_candidate_package_ready_for_external_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-TESTSET",
                "title": "主链候选提交与交接流",
                "goal": "将 FEAT acceptance 拆成受治理 TESTSET candidate package。",
                "scope": [
                    "将 selected FEAT acceptance checks 映射为 test units。",
                    "输出 analysis、strategy 与 TESTSET 主对象。",
                    "生成 gate subjects 与 test execution handoff。",
                ],
                "constraints": [
                    "只有 test-set.yaml 是正式主对象。",
                    "approval 前不得把 candidate package 物化为 freeze package。",
                    "gate 必须外置且 subject identity 稳定。",
                ],
                "dependencies": [
                    "上游 feat_freeze_package 已 freeze_ready。",
                    "下游 test execution skill 可消费 required_environment_inputs。",
                ],
                "non_goals": [
                    "不直接实现 test runner 细节。",
                    "不扩张为 TECH 或 TASK 设计。",
                ],
                "track": "adoption_e2e",
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "analysis 保持 FEAT 边界",
                        "given": "selected FEAT",
                        "when": "产出 analysis",
                        "then": "scope、constraints、non-goals 均可追溯",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "strategy 覆盖 acceptance",
                        "given": "acceptance checks",
                        "when": "派生 strategy",
                        "then": "每条 acceptance 都至少映射一个 test unit",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "handoff 可执行",
                        "given": "candidate package",
                        "when": "交接到 test execution",
                        "then": "required_environment_inputs 可直接消费",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-TESTSET", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-to-testset-input")
            input_dir = self.make_feat_package(repo_root, "feat-to-testset-input", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-SRC-001-TESTSET",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-to-testset-output",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])

            bundle_json = json.loads((artifacts_dir / "test-set-bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            freeze_gate = json.loads((artifacts_dir / "test-set-freeze-gate.json").read_text(encoding="utf-8"))
            handoff = json.loads((artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            test_set = yaml.safe_load((artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))
            bundle_markdown = (artifacts_dir / "test-set-bundle.md").read_text(encoding="utf-8")

            self.assertEqual(bundle_json["artifact_type"], "test_set_candidate_package")
            self.assertEqual(bundle_json["status"], "approval_pending")
            self.assertEqual(manifest["status"], "approval_pending")
            self.assertEqual(test_set["status"], "approved")
            self.assertEqual(freeze_gate["status"], "pending")
            self.assertTrue(freeze_gate["ready_for_external_approval"])
            self.assertNotEqual(test_set["derived_slug"], "unspecified")
            self.assertTrue(all("review" not in unit["trigger_action"].lower() for unit in test_set["test_units"]))
            self.assertTrue(all("inspect" not in unit["trigger_action"].lower() for unit in test_set["test_units"]))
            self.assertEqual(handoff["target_skill"], "skill.qa.test_exec_web_e2e")
            self.assertTrue(
                any("authoritative handoff submission" in item for item in handoff["required_environment_inputs"]["data"])
            )
            self.assertTrue(
                any("pending_state" in item for item in handoff["required_environment_inputs"]["data"])
            )
            self.assertTrue(
                any("handoff service identity" in item or "账号材料" in item for item in handoff["required_environment_inputs"]["access"])
            )
            self.assertTrue((artifacts_dir / "analysis-review-subject.json").exists())
            self.assertTrue((artifacts_dir / "strategy-review-subject.json").exists())
            self.assertTrue((artifacts_dir / "test-set-approval-subject.json").exists())
            self.assertGreaterEqual(len(test_set["test_units"]), 3)
            self.assertTrue(all(unit.get("input_preconditions") for unit in test_set["test_units"]))
            self.assertTrue(all(unit.get("trigger_action") for unit in test_set["test_units"]))
            self.assertTrue(all(unit.get("pass_conditions") for unit in test_set["test_units"]))
            self.assertTrue(all(row.get("acceptance_scenario") for row in test_set["acceptance_traceability"]))
            self.assertTrue(all(row.get("coverage_status") == "covered" for row in test_set["acceptance_traceability"]))
            self.assertTrue(any("pending_state" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("gate_pending_ref" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("assigned_gate_queue" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("canonical_payload_path" in item for unit in test_set["test_units"] for item in unit["pass_conditions"]))
            self.assertTrue(any("response envelope" in item for unit in test_set["test_units"] for item in unit["required_evidence"]))
            self.assertFalse(any("error code -> retryable -> idempotent_replay mapping" in item for unit in test_set["test_units"] for item in unit["observation_points"]))
            self.assertIn("acceptance_traceability", bundle_markdown)
            self.assertIn("input_preconditions:", bundle_markdown)
            self.assertIn("required_evidence:", bundle_markdown)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

    def test_validate_input_rejects_missing_feat_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-INPUT",
                "title": "Input Validation",
                "goal": "验证输入缺失 feat_ref 时被拒绝。",
                "scope": ["校验 required files。", "校验 feat_ref 存在。", "校验 upstream lineage。"],
                "constraints": ["需要 EPIC 引用。", "需要 SRC 引用。", "需要 acceptance checks。"],
                "acceptance_checks": [
                    {"id": "AC-01", "scenario": "required files present", "given": "input dir", "when": "校验", "then": "全部文件存在"},
                    {"id": "AC-02", "scenario": "feat exists", "given": "feat_ref", "when": "查找", "then": "返回匹配 feature"},
                    {"id": "AC-03", "scenario": "handoff admits TESTSET", "given": "handoff", "when": "检查 derivable children", "then": "包含 TESTSET"},
                ],
                "source_refs": ["FEAT-SRC-001-INPUT", "EPIC-SRC-001", "SRC-001"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-to-testset-invalid")
            input_dir = self.make_feat_package(repo_root, "feat-to-testset-invalid", bundle)

            result = self.run_cmd("validate-input", "--input", str(input_dir), "--feat-ref", "FEAT-SRC-001-404")
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("Selected feat_ref not found" in error for error in payload["errors"]))

    def test_collaboration_profile_hardens_pending_visibility_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            feature = {
                "feat_ref": "FEAT-SRC-001-COLLAB",
                "title": "主链候选提交与交接流",
                "goal": "冻结 authoritative handoff、pending visibility 与 runtime re-entry routing 的协作边界。",
                "scope": [
                    "定义 candidate package、proposal、evidence 在什么触发场景下被提交。",
                    "定义提交后形成什么 authoritative handoff object。",
                    "定义提交完成后对上游和 gate 分别暴露什么业务结果。",
                ],
                "constraints": [
                    "Loop responsibility split must stay explicit.",
                    "Submission completion is visible without implying approval: The FEAT must make clear which authoritative handoff and pending-intake results become visible, while keeping approval and re-entry semantics outside this FEAT.",
                ],
                "dependencies": [
                    "candidate package 已就绪且准备进入主链 handoff。",
                    "下游 workflow 已接入 authoritative handoff submission 消费链。",
                ],
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "candidate submit-mainline 明确 loop 责任边界",
                        "given": "candidate package 已就绪",
                        "when": "执行 candidate submit-mainline",
                        "then": "execution、gate、human loop 各自拥有明确 transition",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "submission completion visibility stays pending-only",
                        "given": "candidate 提交完成",
                        "when": "读取 authoritative handoff object 与 pending visibility",
                        "then": "submission completion is visible without implying approval: The FEAT must make clear which authoritative handoff and pending-intake results become visible, while keeping approval and re-entry semantics outside this FEAT.",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "downstream inherits the same handoff model",
                        "given": "下游 workflow 消费 authoritative handoff submission",
                        "when": "校验 queue / handoff / gate 语义",
                        "then": "下游继承同一套协作规则而不重建并行 queue / handoff 模型",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-COLLAB", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            bundle = self.make_bundle_json(feature, run_id="feat-to-testset-collab")
            input_dir = self.make_feat_package(repo_root, "feat-to-testset-collab", bundle)

            result = self.run_cmd(
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-SRC-001-COLLAB",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-to-testset-collab-out",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            test_set = yaml.safe_load((artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))

            self.assertTrue(any("pending_state" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("gate_pending_ref" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("assigned_gate_queue" in ref for unit in test_set["test_units"] for ref in unit["supporting_refs"]))
            self.assertTrue(any("retryable / idempotent_replay field semantics" in item for unit in test_set["test_units"] for item in unit["observation_points"]))
            self.assertTrue(any("尚未冻结完整 error mapping table" in item for unit in test_set["test_units"] for item in unit["pass_conditions"]))
            collaboration_trace = {
                row["acceptance_ref"]: row for row in test_set["acceptance_traceability"]
            }
            self.assertIn("decision-driven revise/retry runtime routing", collaboration_trace["AC-02"]["then"])
            self.assertNotIn("approval and re-entry semantics outside this FEAT", collaboration_trace["AC-02"]["then"])

    def test_profile_specific_units_and_handoff_are_hardened(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            io_feature = {
                "feat_ref": "FEAT-SRC-001-IO",
                "title": "主链受治理 IO 落盘与读取流",
                "goal": "冻结主链受治理 IO 的正式写入、读取与失败边界。",
                "scope": [
                    "定义 handoff、decision、formal output、evidence 的正式读写动作。",
                    "定义业务调用点、正式 receipt / registry record 和 managed ref。",
                    "定义被拒绝读写时对业务方可见的失败表现。",
                ],
                "constraints": [
                    "正式写入必须受 Gateway / Policy / Registry 治理。",
                    "不得 fallback 到自由写入。",
                    "不得扩张成全仓文件治理。",
                ],
                "dependencies": [
                    "Gateway / Path Policy / Registry 已接入主链。",
                    "managed write/read preflight 可输出 verdict。",
                ],
                "non_goals": [
                    "不覆盖仓库级全局治理。",
                    "不重写 ADR-005 模块实现。",
                ],
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "正式写入返回 managed refs",
                        "given": "Gateway / Path Policy / Registry 已连通",
                        "when": "执行主链正式 write/read",
                        "then": "成功路径返回 receipt_ref、registry_record_ref、managed_artifact_ref",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "主链 IO 不能扩张为全局文件治理",
                        "given": "请求包含超出主链边界的目录动作",
                        "when": "执行 policy scope check",
                        "then": "超出范围的仓库级治理请求被拒绝",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "失败路径保持可追溯且不得 fallback",
                        "given": "preflight 或 registry / receipt build 可失败",
                        "when": "触发 policy_deny、registry_prerequisite_failed、receipt_pending",
                        "then": "失败路径被记录且不发生 free write fallback",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-IO", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            pilot_feature = {
                "feat_ref": "FEAT-SRC-001-PILOT",
                "title": "governed skill 接入与 pilot 验证流",
                "goal": "冻结 governed skill 的 onboarding、pilot、cutover 与 fallback 规则。",
                "scope": [
                    "定义哪些 governed skill 先接入以及 scope 外对象如何处理。",
                    "定义 pilot 主链如何选定、扩围和形成真实 evidence。",
                    "定义 cutover / fallback 如何判断，以及 adoption 成立需要交付哪些真实 evidence。",
                ],
                "constraints": [
                    "至少保留一条真实 pilot 主链。",
                    "evidence 不足时必须 fail closed。",
                    "不得扩张成仓库级全局治理。",
                ],
                "dependencies": [
                    "foundation FEAT 对应主链已可执行。",
                    "至少一个真实 pilot scope 已被选定。",
                ],
                "non_goals": [
                    "不要求一次性迁移所有 governed skill。",
                    "不替代 release orchestration。",
                ],
                "track": "adoption_e2e",
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "Onboarding scope and migration waves are explicit",
                        "given": "EPIC requires real governed skill landing",
                        "when": "The onboarding package is prepared",
                        "then": "onboarding scope, waves, cutover and fallback rules are machine-readable",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "At least one real pilot chain is required",
                        "given": "Foundation FEATs are implemented in isolation",
                        "when": "Adoption readiness is evaluated",
                        "then": "At least one producer -> consumer -> audit -> gate pilot chain is required",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "Adoption scope does not expand into repository-wide governance",
                        "given": "A team proposes folding all file-governance cleanup into this FEAT",
                        "when": "The proposal is checked against FEAT boundaries",
                        "then": "The FEAT rejects repository-wide governance expansion",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-PILOT", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }

            io_bundle = self.make_bundle_json(io_feature, run_id="feat-to-testset-io")
            io_input_dir = self.make_feat_package(repo_root, "feat-to-testset-io", io_bundle)
            io_result = self.run_cmd(
                "run",
                "--input",
                str(io_input_dir),
                "--feat-ref",
                "FEAT-SRC-001-IO",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-to-testset-io-out",
            )
            self.assertEqual(io_result.returncode, 0, io_result.stderr)
            io_artifacts_dir = Path(json.loads(io_result.stdout)["artifacts_dir"])
            io_handoff = json.loads((io_artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            io_access = io_handoff["required_environment_inputs"]["access"]
            self.assertTrue(any("credential" in item.lower() or "token" in item.lower() or "账号" in item for item in io_access))

            pilot_bundle = self.make_bundle_json(pilot_feature, run_id="feat-to-testset-pilot")
            pilot_input_dir = self.make_feat_package(repo_root, "feat-to-testset-pilot", pilot_bundle)
            pilot_result = self.run_cmd(
                "run",
                "--input",
                str(pilot_input_dir),
                "--feat-ref",
                "FEAT-SRC-001-PILOT",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-to-testset-pilot-out",
            )
            self.assertEqual(pilot_result.returncode, 0, pilot_result.stderr)
            pilot_artifacts_dir = Path(json.loads(pilot_result.stdout)["artifacts_dir"])
            pilot_handoff = json.loads((pilot_artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            pilot_test_set = yaml.safe_load((pilot_artifacts_dir / "test-set.yaml").read_text(encoding="utf-8"))
            pilot_access = pilot_handoff["required_environment_inputs"]["access"]
            self.assertTrue(any("credential" in item.lower() or "token" in item.lower() or "账号" in item for item in pilot_access))
            self.assertEqual(len(pilot_test_set["test_units"]), 5)
            self.assertIn(
                "fallback 结果必须记录到 receipt / wave state",
                [unit["title"] for unit in pilot_test_set["test_units"]],
            )
            self.assertIn(
                "adoption scope 不得扩张为仓库级全局治理改造",
                [unit["title"] for unit in pilot_test_set["test_units"]],
            )
            self.assertTrue(
                any(unit["trigger_action"] == "生成 onboarding matrix，并把 wave_id、compat_mode、cutover_guard_ref 写回 rollout state。"
                    for unit in pilot_test_set["test_units"])
            )
            fallback_unit = next(unit for unit in pilot_test_set["test_units"] if unit["title"] == "fallback 结果必须记录到 receipt / wave state")
            self.assertFalse(fallback_unit.get("acceptance_ref"))
            self.assertTrue(fallback_unit.get("derivation_basis"))
            self.assertFalse(any("file-governance cleanup" in item for item in fallback_unit["input_preconditions"]))
            pilot_trace = {
                row["acceptance_ref"]: row for row in pilot_test_set["acceptance_traceability"]
            }
            self.assertEqual(
                pilot_trace["AC-02"]["when"] if "AC-02" in pilot_trace else pilot_trace["FEAT-SRC-001-PILOT-AC-02"]["when"],
                "执行 pilot chain verifier 并评估 adoption readiness",
            )
            self.assertIn(
                "producer -> gate -> formal -> consumer -> audit",
                pilot_trace["AC-02"]["then"] if "AC-02" in pilot_trace else pilot_trace["FEAT-SRC-001-PILOT-AC-02"]["then"],
            )
            mapped_units = pilot_trace["AC-03"]["unit_refs"] if "AC-03" in pilot_trace else pilot_trace["FEAT-SRC-001-PILOT-AC-03"]["unit_refs"]
            self.assertEqual(len(mapped_units), 1)

    def test_gate_handoff_requires_machine_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            gate_feature = {
                "feat_ref": "FEAT-SRC-001-GATE",
                "title": "主链 gate 审核与裁决流",
                "goal": "冻结 gate decision 的单一路径与 decision object 语义。",
                "scope": [
                    "定义 approve / revise / retry / handoff / reject 的业务语义和输出物。",
                    "定义每种裁决的返回去向和对上游的业务结果。",
                    "定义 decision object 如何成为后续 formal 发布的唯一触发来源。",
                ],
                "constraints": [
                    "decision path 必须唯一。",
                    "decision object 不得并行分叉。",
                    "formal trigger 只来自 approve。",
                ],
                "dependencies": [
                    "candidate package 已形成 authoritative handoff submission。",
                    "formal publish control layer 可消费 approve decision object。",
                ],
                "acceptance_checks": [
                    {
                        "id": "AC-01",
                        "scenario": "Gate decision path is single and explicit",
                        "given": "candidate package awaiting approval",
                        "when": "handoff enters gate evaluation",
                        "then": "only one authoritative decision object is formed",
                    },
                    {
                        "id": "AC-02",
                        "scenario": "Candidate cannot bypass gate",
                        "given": "candidate exists but approval has not occurred",
                        "when": "a downstream consumer requests formal input",
                        "then": "candidate is not treated as formal source",
                    },
                    {
                        "id": "AC-03",
                        "scenario": "Formal publication is only triggered by the decision object",
                        "given": "approve decision object exists",
                        "when": "formal publication is requested",
                        "then": "only approve decision object can trigger formal publish",
                    },
                ],
                "source_refs": ["FEAT-SRC-001-GATE", "EPIC-SRC-001", "SRC-001", "ADR-012"],
            }
            gate_bundle = self.make_bundle_json(gate_feature, run_id="feat-to-testset-gate")
            gate_input_dir = self.make_feat_package(repo_root, "feat-to-testset-gate", gate_bundle)
            gate_result = self.run_cmd(
                "run",
                "--input",
                str(gate_input_dir),
                "--feat-ref",
                "FEAT-SRC-001-GATE",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-to-testset-gate-out",
            )
            self.assertEqual(gate_result.returncode, 0, gate_result.stderr)
            gate_artifacts_dir = Path(json.loads(gate_result.stdout)["artifacts_dir"])
            gate_handoff = json.loads((gate_artifacts_dir / "handoff-to-test-execution.json").read_text(encoding="utf-8"))
            gate_access = gate_handoff["required_environment_inputs"]["access"]
            self.assertTrue(any("service account" in item.lower() or "token" in item.lower() or "credential" in item.lower() for item in gate_access))


if __name__ == "__main__":
    unittest.main()
