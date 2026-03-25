import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-dev-tech-to-impl" / "scripts" / "tech_to_impl.py"


class TechToImplWorkflowHarness(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def run_impl_flow(
        self,
        repo_root: Path,
        input_dir: Path,
        feat_ref: str,
        tech_ref: str,
    ) -> Path:
        result = self.run_cmd(
            "run",
            "--input",
            str(input_dir),
            "--feat-ref",
            feat_ref,
            "--tech-ref",
            tech_ref,
            "--repo-root",
            str(repo_root),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(json.loads(result.stdout)["artifacts_dir"])

    def make_tech_package(self, root: Path, run_id: str, bundle_json: dict[str, object]) -> Path:
        package_dir = root / "artifacts" / "feat-to-tech" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "artifact_type": "tech_design_package",
            "workflow_key": "dev.feat-to-tech",
            "workflow_run_id": run_id,
            "status": bundle_json["status"],
            "schema_version": bundle_json["schema_version"],
            "feat_ref": bundle_json["feat_ref"],
            "tech_ref": bundle_json["tech_ref"],
            "source_refs": bundle_json["source_refs"],
        }
        markdown = [
            "---",
            f"artifact_type: {frontmatter['artifact_type']}",
            f"workflow_key: {frontmatter['workflow_key']}",
            f"workflow_run_id: {frontmatter['workflow_run_id']}",
            f"status: {frontmatter['status']}",
            f"schema_version: {frontmatter['schema_version']}",
            f"feat_ref: {frontmatter['feat_ref']}",
            f"tech_ref: {frontmatter['tech_ref']}",
            "source_refs:",
            *[f"  - {item}" for item in frontmatter["source_refs"]],
            "---",
            "",
            f"# {bundle_json['title']}",
            "",
            "## Selected FEAT",
            "",
            f"- feat_ref: {bundle_json['feat_ref']}",
            f"- tech_ref: {bundle_json['tech_ref']}",
        ]
        (package_dir / "tech-design-bundle.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
        (package_dir / "tech-design-bundle.json").write_text(
            json.dumps(bundle_json, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (package_dir / "tech-spec.md").write_text("# TECH\n\ntech spec\n", encoding="utf-8")
        if bundle_json.get("arch_required"):
            (package_dir / "arch-design.md").write_text("# ARCH\n\narch\n", encoding="utf-8")
        if bundle_json.get("api_required"):
            (package_dir / "api-contract.md").write_text("# API\n\napi\n", encoding="utf-8")
        payloads = {
            "package-manifest.json": {"status": bundle_json["status"], "run_id": run_id},
            "tech-review-report.json": {"decision": "pass", "summary": "review ok"},
            "tech-acceptance-report.json": {"decision": "approve", "summary": "acceptance ok"},
            "tech-defect-list.json": [],
            "tech-freeze-gate.json": {"workflow_key": "dev.feat-to-tech", "freeze_ready": True, "decision": "pass"},
            "handoff-to-tech-impl.json": {
                "target_workflow": "workflow.dev.tech_to_impl",
                "feat_ref": bundle_json["feat_ref"],
                "tech_ref": bundle_json["tech_ref"],
                "arch_ref": bundle_json.get("arch_ref"),
                "api_ref": bundle_json.get("api_ref"),
            },
            "execution-evidence.json": {"run_id": run_id, "decision": "pass"},
            "supervision-evidence.json": {"run_id": run_id, "decision": "pass"},
        }
        for name, payload in payloads.items():
            (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return package_dir

    def make_bundle_json(
        self,
        feature: dict[str, object],
        run_id: str,
        *,
        arch_required: bool = False,
        api_required: bool = False,
    ) -> dict[str, object]:
        feat_ref = str(feature["feat_ref"])
        tech_ref = f"TECH-{feat_ref}"
        source_refs = [
            f"dev.feat-to-tech::{run_id}",
            feat_ref,
            tech_ref,
            "EPIC-SRC001",
            "SRC-001",
            "ADR-014",
        ]
        arch_ref = f"ARCH-{feat_ref.replace('FEAT-', '', 1)}" if arch_required else None
        api_ref = f"API-{feat_ref.replace('FEAT-', '', 1)}" if api_required else None
        return {
            "artifact_type": "tech_design_package",
            "workflow_key": "dev.feat-to-tech",
            "workflow_run_id": run_id,
            "title": f"{feature['title']} Technical Design Package",
            "status": "accepted",
            "schema_version": "1.0.0",
            "feat_ref": feat_ref,
            "tech_ref": tech_ref,
            "arch_ref": arch_ref,
            "api_ref": api_ref,
            "arch_required": arch_required,
            "api_required": api_required,
            "source_refs": source_refs,
            "selected_feat": feature,
            "tech_design": {
                "design_focus": list(feature["scope"])[:3],
                "implementation_rules": [
                    *list(feature["constraints"])[:2],
                    "Submission completion is visible without implying approval: The FEAT must make clear which authoritative handoff and pending-intake results become visible, while keeping approval and re-entry semantics outside this FEAT.",
                ],
                "state_model": [
                    "handoff_prepared -> handoff_submitted -> gate_pending_visible -> decision_returned",
                    "decision_returned(revise|retry) -> runtime_reentry_directive_written -> handoff_prepared",
                ],
                "implementation_unit_mapping": [
                    "`cli/lib/protocol.py` (`extend`): 定义 `HandoffEnvelope`、`PendingVisibilityRecord` 与 `DecisionReturnEnvelope`。",
                    "`cli/lib/mainline_runtime.py` (`new`): 管理 authoritative submission、pending visibility 与 decision-return intake。",
                    "`cli/commands/gate/command.py` (`extend`): 接入 submit-handoff / show-pending 路径。",
                ],
                "interface_contracts": [
                    "`HandoffEnvelope`: input=`producer_ref`, `proposal_ref`, `pending_state`; output=`handoff_ref`, `gate_pending_ref`, `trace_ref`; errors=`duplicate_submission`; idempotent=`yes by producer_ref + proposal_ref`; precondition=`payload ready`。"
                ],
                "main_sequence": [
                    "1. normalize candidate/proposal/evidence submission",
                    "2. persist authoritative handoff object and emit gate-pending visibility",
                    "3. consume structured decision object and route revise/retry via runtime",
                ],
                "integration_points": [
                    "调用方通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff。",
                    "旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility。",
                ],
                "exception_and_compensation": [
                    "authoritative handoff 已提交但 pending visibility build fail：标记 visibility_pending 并要求补写 receipt。",
                    "decision return consumed 但 re-entry directive write fail：返回 reentry_pending，等待 runtime repair。",
                ],
            },
            "design_consistency_check": {"passed": True, "checks": [], "issues": []},
        }
