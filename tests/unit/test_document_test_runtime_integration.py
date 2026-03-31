import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "raw-to-src"
RAW_SCRIPT = ROOT / "skills" / "ll-product-raw-to-src" / "scripts" / "raw_to_src.py"
SRC_SCRIPT = ROOT / "skills" / "ll-product-src-to-epic" / "scripts" / "src_to_epic.py"
EPIC_SCRIPT = ROOT / "skills" / "ll-product-epic-to-feat" / "scripts" / "epic_to_feat.py"


def run_cmd(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_src_package(root: Path, run_id: str) -> Path:
    package_dir = root / "artifacts" / "raw-to-src" / run_id
    package_dir.mkdir(parents=True, exist_ok=True)
    candidate = {
        "artifact_type": "src_candidate_package",
        "workflow_key": "product.raw-to-src",
        "workflow_run_id": run_id,
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
    markdown = [
        "---",
        "artifact_type: src_candidate",
        "workflow_key: product.raw-to-src",
        f"workflow_run_id: {run_id}",
        f"title: {candidate['title']}",
        "status: freeze_ready",
        f"source_kind: {candidate['source_kind']}",
        "source_refs:",
        "  - SRC-100",
        "  - REQ-UX-100",
        "---",
        "",
        f"# {candidate['title']}",
        "",
        "## Problem Statement",
        "",
        candidate["problem_statement"],
        "",
    ]
    (package_dir / "src-candidate.md").write_text("\n".join(markdown), encoding="utf-8")
    write_json(package_dir / "src-candidate.json", candidate)
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
        write_json(package_dir / name, payload)
    return package_dir


def make_epic_package(root: Path, run_id: str) -> Path:
    package_dir = root / "artifacts" / "src-to-epic" / run_id
    package_dir.mkdir(parents=True, exist_ok=True)
    epic = {
        "artifact_type": "epic_freeze_package",
        "workflow_key": "product.src-to-epic",
        "workflow_run_id": run_id,
        "title": "Managed Artifact IO Governance Foundation",
        "status": "accepted",
        "schema_version": "1.0.0",
        "epic_freeze_ref": "EPIC-SRC-001-001",
        "src_root_id": "SRC-001",
        "source_refs": ["product.src-to-epic::src001", "EPIC-SRC-001-001", "SRC-001", "ADR-005"],
        "business_goal": "把受治理的 artifact IO 主链收敛成统一底座，并能通过真实 skill 接入验证闭环成立。",
        "business_value_problem": [
            "多个 governed skill 仍在自由读写文件。",
            "consumer 仍可能通过目录扫描消费上下游产物。",
        ],
        "product_positioning": "该 EPIC 位于主链治理产品层。",
        "actors_and_roles": [
            {"role": "workflow 设计者", "responsibility": "定义主链能力边界和下游 FEAT 分解方式。"},
            {"role": "governed skill 作者", "responsibility": "让业务 skill 通过统一主链提交与消费治理对象。"},
        ],
        "scope": ["统一 execution、gate、human loop 的交接与回流。", "统一 handoff、gate decision、formal materialization。"],
        "upstream_and_downstream": ["Upstream：承接 freeze-ready 的 SRC 包。", "Downstream：拆成多个可独立验收的 FEAT。"],
        "epic_success_criteria": ["下游 FEAT 可以独立描述主链业务流和交付物。"],
        "non_goals": ["不直接下沉到 TASK 或代码实现。"],
        "decomposition_rules": ["按独立验收的产品行为切片拆分 FEAT，不按实现顺序切分。"],
        "product_behavior_slices": [
            {
                "id": "collaboration-loop",
                "name": "主链候选提交与交接流",
                "track": "foundation",
                "goal": "冻结 governed skill 如何提交 authoritative handoff。",
                "scope": ["定义 candidate package 的提交流程。", "定义提交后形成的 authoritative handoff object。"],
                "product_surface": "候选提交与交接产品界面",
                "completed_state": "authoritative handoff object 已建立并进入 gate 消费链。",
                "business_deliverable": "可被 gate 正式消费的 authoritative handoff submission",
                "capability_axes": ["主链协作闭环能力"],
            },
            {
                "id": "gate-decision-loop",
                "name": "主链 Gate 决策与回流流",
                "track": "foundation",
                "goal": "冻结 gate 如何做出 approve/revise/retry 决策并回流到执行链。",
                "scope": ["定义 gate decision object 的结构。", "定义 revise/return job 的派发流程。"],
                "product_surface": "Gate 决策与回流产品界面",
                "completed_state": "gate decision object 已建立并能触发下游 return job 派发。",
                "business_deliverable": "可被 execution 消费的 gate decision 与 return job",
                "capability_axes": ["主链 Gate 决策能力"],
            },
        ],
        "constraints_and_dependencies": ["所有正式写入必须经由 Gateway。", "Path Policy 是唯一政策源。"],
        "capability_axes": [
            {"id": "collaboration-loop", "name": "主链协作闭环能力", "scope": "统一协作 loop 边界。", "feat_axis": "loop collaboration"},
            {"id": "gate-decision-loop", "name": "主链 Gate 决策能力", "scope": "统一 Gate 决策与回流边界。", "feat_axis": "gate decision"},
        ],
        "rollout_requirement": {"required": False},
        "rollout_plan": {"required_feat_tracks": ["foundation"], "required_feat_families": []},
    }
    markdown = [
        "---",
        "artifact_type: epic_freeze_package",
        "workflow_key: product.src-to-epic",
        f"workflow_run_id: {run_id}",
        f"title: {epic['title']}",
        "status: accepted",
        "epic_freeze_ref: EPIC-SRC-001-001",
        "src_root_id: SRC-001",
        "---",
        "",
        f"# {epic['title']}",
        "",
        "## Epic Intent",
        "",
        epic["business_goal"],
        "",
    ]
    (package_dir / "epic-freeze.md").write_text("\n".join(markdown), encoding="utf-8")
    write_json(package_dir / "epic-freeze.json", epic)
    payloads = {
        "package-manifest.json": {"status": epic["status"], "run_id": run_id},
        "epic-review-report.json": {"decision": "pass", "summary": "review ok"},
        "epic-acceptance-report.json": {"decision": "approve", "summary": "acceptance ok"},
        "epic-defect-list.json": [],
        "epic-freeze-gate.json": {"workflow_key": "product.src-to-epic", "freeze_ready": True, "decision": "pass"},
        "handoff-to-epic-to-feat.json": {"to_skill": "product.epic-to-feat"},
        "execution-evidence.json": {"run_id": run_id, "decision": "pass"},
        "supervision-evidence.json": {"run_id": run_id, "decision": "pass"},
    }
    for name, payload in payloads.items():
        write_json(package_dir / name, payload)
    return package_dir


def make_revision_request(path: Path, payload: dict) -> Path:
    write_json(path, payload)
    return path


class DocumentTestRuntimeIntegrationTests(unittest.TestCase):
    def test_raw_to_src_materializes_document_test_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "ssot" / "src").mkdir(parents=True, exist_ok=True)
            result = run_cmd(
                RAW_SCRIPT,
                "run",
                "--input",
                str(FIXTURES / "raw-requirement.md"),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "doc-test-raw",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            report = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))

            self.assertIn(report["test_outcome"], {"blocking_defect_found", "no_blocking_defect_found"})
            self.assertEqual(report["recommended_actor"], report["sections"]["fixability"]["recommended_actor"])
            self.assertIn("downstream_readiness", report["sections"])
            self.assertEqual(manifest["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))
            self.assertEqual(supervision["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))
            self.assertEqual(supervision["document_test_outcome"], report["test_outcome"])

            validate = run_cmd(RAW_SCRIPT, "validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_src_to_epic_materializes_document_test_report_and_gate_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = make_src_package(repo_root, "src-doc-test")
            result = run_cmd(
                SRC_SCRIPT,
                "run",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "epic-doc-test",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            report = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            gate = json.loads((artifacts_dir / "epic-freeze-gate.json").read_text(encoding="utf-8"))
            evidence = (artifacts_dir / "evidence-report.md").read_text(encoding="utf-8")

            self.assertEqual(report["sections"]["downstream_readiness"]["downstream_target"], "product.epic-to-feat")
            self.assertEqual(manifest["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))
            self.assertEqual(supervision["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))
            self.assertEqual(supervision["document_test_outcome"], report["test_outcome"])
            self.assertTrue(gate["checks"]["document_test_report_present"])
            self.assertTrue(gate["checks"]["document_test_non_blocking"])
            self.assertIn("## Document Test", evidence)

            validate = run_cmd(SRC_SCRIPT, "validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_src_to_epic_validation_rejects_malformed_or_blocking_document_test_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = make_src_package(repo_root, "src-doc-invalid")
            result = run_cmd(
                SRC_SCRIPT,
                "run",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "epic-doc-invalid",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifacts_dir = Path(json.loads(result.stdout)["artifacts_dir"])
            report_path = artifacts_dir / "document-test-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))

            malformed = dict(report)
            malformed.pop("sections")
            write_json(report_path, malformed)
            validate = run_cmd(SRC_SCRIPT, "validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("sections", validate.stdout)

            write_json(report_path, report)
            report["test_outcome"] = "blocking_defect_found"
            write_json(report_path, report)
            readiness = run_cmd(SRC_SCRIPT, "validate-package-readiness", "--artifacts-dir", str(artifacts_dir))
            self.assertNotEqual(readiness.returncode, 0)
            self.assertIn("document_test_non_blocking", readiness.stdout)

    def test_src_to_epic_revision_rerun_materializes_document_test_revision_trace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = make_src_package(repo_root, "src-doc-revise")
            first = run_cmd(SRC_SCRIPT, "run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-doc-revise")
            self.assertEqual(first.returncode, 0, first.stderr)
            artifacts_dir = Path(json.loads(first.stdout)["artifacts_dir"])
            revision_path = make_revision_request(
                repo_root / "revision-request.json",
                {
                    "workflow_key": "product.src-to-epic",
                    "run_id": "epic-doc-revise",
                    "source_run_id": "src-doc-revise",
                    "decision_type": "revise",
                    "decision_reason": "把 revise 上下文显式落盘到 EPIC 约束层。",
                    "decision_target": "epic_freeze_package",
                    "basis_refs": ["epic-review-report.json"],
                    "revision_round": 2,
                    "source_gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                    "source_return_job_ref": "artifacts/jobs/waiting-human/src-to-epic-return.json",
                    "authoritative_input_ref": "artifacts/raw-to-src/src-doc-revise",
                    "candidate_ref": "src-to-epic.epic-doc-revise.epic-freeze",
                    "original_input_path": str(input_dir),
                },
            )
            rerun = run_cmd(
                SRC_SCRIPT,
                "run",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "epic-doc-revise",
                "--allow-update",
                "--revision-request",
                str(revision_path),
            )
            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            report = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["revision_request_ref"], str(artifacts_dir / "revision-request.json"))
            self.assertTrue(report["sections"]["semantic_drift"]["revision_context_present"])

    def test_epic_to_feat_revision_rerun_materializes_document_test_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = make_epic_package(repo_root, "epic-doc-revise-input")
            first = run_cmd(EPIC_SCRIPT, "run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "feat-doc-revise")
            self.assertTrue(first.stdout.strip(), first.stderr)
            artifacts_dir = Path(json.loads(first.stdout)["artifacts_dir"])
            revision_path = make_revision_request(
                repo_root / "revision-request.json",
                {
                    "workflow_key": "product.epic-to-feat",
                    "run_id": "feat-doc-revise",
                    "source_run_id": "epic-doc-revise-input",
                    "decision_type": "revise",
                    "decision_reason": "保留下游 FEAT 边界，并把 revise 上下文显式写入 bundle / evidence / gate。",
                    "decision_target": "epic-to-feat.feat-doc-revise.feat-freeze-bundle",
                    "basis_refs": ["feat-review-report.json"],
                    "revision_round": 1,
                    "source_gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                    "source_return_job_ref": "artifacts/jobs/waiting-human/epic-to-feat-return.json",
                    "authoritative_input_ref": "artifacts/src-to-epic/epic-doc-revise-input",
                    "candidate_ref": "epic-to-feat.feat-doc-revise.feat-freeze-bundle",
                    "original_input_path": str(input_dir),
                },
            )
            rerun = run_cmd(
                EPIC_SCRIPT,
                "run",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "feat-doc-revise",
                "--allow-update",
                "--revision-request",
                str(revision_path),
            )
            self.assertTrue(rerun.stdout.strip(), rerun.stderr)
            report = json.loads((artifacts_dir / "document-test-report.json").read_text(encoding="utf-8"))
            manifest = json.loads((artifacts_dir / "package-manifest.json").read_text(encoding="utf-8"))
            supervision = json.loads((artifacts_dir / "supervision-evidence.json").read_text(encoding="utf-8"))
            gate = json.loads((artifacts_dir / "feat-freeze-gate.json").read_text(encoding="utf-8"))
            evidence = (artifacts_dir / "evidence-report.md").read_text(encoding="utf-8")

            self.assertEqual(report["revision_request_ref"], str(artifacts_dir / "revision-request.json"))
            self.assertTrue(report["sections"]["semantic_drift"]["revision_context_present"])
            self.assertTrue(report["sections"]["downstream_readiness"]["downstream_target"])
            self.assertEqual(manifest["document_test_report_ref"], str(artifacts_dir / "document-test-report.json"))
            self.assertEqual(supervision["document_test_outcome"], report["test_outcome"])
            self.assertTrue(gate["checks"]["document_test_report_present"])
            self.assertTrue(gate["checks"]["document_test_non_blocking"])
            self.assertIn("## Document Test", evidence)

            validate = run_cmd(EPIC_SCRIPT, "validate-output", "--artifacts-dir", str(artifacts_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)


if __name__ == "__main__":
    unittest.main()
