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
        integration_context = _default_integration_context(bundle_json)
        bundle_json = {
            **bundle_json,
            "integration_context": integration_context,
            "need_assessment": bundle_json.get("need_assessment") or _default_need_assessment(bundle_json),
            "integration_sufficiency_check": bundle_json.get("integration_sufficiency_check") or _default_integration_sufficiency_check(),
            "downstream_handoff": bundle_json.get("downstream_handoff") or _default_downstream_handoff(bundle_json),
        }
        frontmatter = {
            "artifact_type": "tech_design_package",
            "workflow_key": "dev.feat-to-tech",
            "workflow_run_id": run_id,
            "status": bundle_json["status"],
            "schema_version": bundle_json["schema_version"],
            "feat_ref": bundle_json["feat_ref"],
            "tech_ref": bundle_json["tech_ref"],
            "surface_map_ref": bundle_json.get("surface_map_ref"),
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
            f"surface_map_ref: {frontmatter['surface_map_ref'] or ''}",
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
        (package_dir / "integration-context.json").write_text(
            json.dumps(integration_context, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
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
                "integration_context_ref": "integration-context.json",
                "canonical_owner_refs": ["tech-design-bundle.json#/tech_design/technical_glossary_and_canonical_ownership"],
                "state_machine_ref": "tech-design-bundle.json#/tech_design/state_machine",
                "nfr_constraints_ref": "tech-design-bundle.json#/tech_design/non_functional_requirements",
                "migration_constraints_ref": "tech-design-bundle.json#/tech_design/migration_constraints",
                "algorithm_constraint_refs": ["tech-design-bundle.json#/tech_design/algorithm_constraints"],
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
        tech_ref = f"TECH-{feat_ref.replace('FEAT-', '', 1)}"
        source_refs = [
            f"dev.feat-to-tech::{run_id}",
            feat_ref,
            tech_ref,
            "EPIC-SRC-001-001",
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
            "surface_map_ref": f"SURFACE-MAP-{feat_ref.replace('FEAT-', '', 1)}",
            "arch_ref": arch_ref,
            "api_ref": api_ref,
            "arch_required": arch_required,
            "api_required": api_required,
            "source_refs": source_refs,
            "selected_feat": feature,
            "need_assessment": _default_need_assessment({"arch_required": arch_required, "api_required": api_required}),
            "integration_sufficiency_check": _default_integration_sufficiency_check(),
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
                "non_functional_requirements": [
                    "Maintain stable handoff lineage.",
                    "Preserve execution-ready evidence semantics.",
                ],
                "state_machine": [
                    "handoff_prepared -> handoff_submitted -> gate_pending_visible -> decision_returned",
                ],
                "algorithm_constraints": [
                    "Decision routing stays deterministic for identical input refs.",
                ],
                "io_matrix_and_side_effects": [
                    "submit handoff -> authoritative handoff + gate pending visibility",
                ],
                "technical_glossary_and_canonical_ownership": [
                    "authoritative handoff: runtime-owned canonical submission object",
                ],
                "migration_constraints": [
                    "compat mode may observe but may not redefine authoritative handoff semantics",
                ],
            },
            "design_consistency_check": {"passed": True, "checks": [], "issues": []},
            "downstream_handoff": _default_downstream_handoff(
                {
                    "feat_ref": feat_ref,
                    "tech_ref": tech_ref,
                    "arch_ref": arch_ref,
                    "api_ref": api_ref,
                }
            ),
        }


def _default_integration_context(bundle_json: dict[str, object]) -> dict[str, object]:
    feat_ref = str(bundle_json.get("feat_ref") or "FEAT-UNKNOWN").strip()
    tech_ref = str(bundle_json.get("tech_ref") or "TECH-UNKNOWN").strip()
    source_refs = bundle_json.get("source_refs") or [feat_ref, tech_ref, "EPIC-SRC-001-001", "SRC-001"]
    return {
        "artifact_type": "integration_context",
        "schema_version": "1.0.0",
        "context_ref": "integration-context.json",
        "workflow_inventory": [
            f"workflow.dev.feat_to_tech produced {tech_ref}",
            "workflow.dev.tech_to_impl consumes frozen TECH outputs",
        ],
        "module_boundaries": [
            "ll-dev-tech-to-impl owns implementation planning artifacts.",
            "Upstream ll-dev-feat-to-tech remains canonical for design truth.",
        ],
        "legacy_fields_states_interfaces": [
            "TECH bundle refs, review artifacts, and freeze gate remain required inputs.",
        ],
        "canonical_ownership": [
            "TECH package owns design truth.",
            "IMPL package owns execution planning only.",
        ],
        "compatibility_constraints": [
            "IMPL must not re-derive state machine, algorithm, or canonical owner semantics.",
        ],
        "migration_modes": [
            "extend",
        ],
        "legacy_invariants": [
            "Approved TECH freeze gate is required before implementation planning.",
        ],
        "gate_audit_evidence": [
            "Execution evidence and supervision evidence must remain present.",
        ],
        "source_refs": list(source_refs),
    }


def _default_need_assessment(bundle_json: dict[str, object]) -> dict[str, object]:
    arch_required = bool(bundle_json.get("arch_required"))
    api_required = bool(bundle_json.get("api_required"))
    return {
        "arch_required": arch_required,
        "api_required": api_required,
        "integration_context_sufficient": True,
        "stateful_design_present": True,
        "arch_rationale": ["ARCH artifact required by test fixture." if arch_required else "ARCH artifact not required by test fixture."],
        "api_rationale": ["API artifact required by test fixture." if api_required else "API artifact not required by test fixture."],
        "integration_context_rationale": ["Fixture integration context is sufficient for input validation."],
        "stateful_design_rationale": ["Fixture TECH package includes explicit stateful design fields."],
    }


def _default_integration_sufficiency_check() -> dict[str, object]:
    return {
        "passed": True,
        "checks": [{"name": "fixture_context", "passed": True, "detail": "test fixture provides integration context"}],
        "issues": [],
        "summary": "integration_context sufficient",
    }


def _default_downstream_handoff(bundle_json: dict[str, object]) -> dict[str, object]:
    return {
        "handoff_id": f"handoff-{bundle_json.get('tech_ref', 'tech')}-to-tech-impl",
        "from_skill": "ll-dev-feat-to-tech",
        "source_run_id": str(bundle_json.get("workflow_run_id") or "fixture-run"),
        "target_workflow": "workflow.dev.tech_to_impl",
        "feat_ref": str(bundle_json.get("feat_ref") or ""),
        "tech_ref": str(bundle_json.get("tech_ref") or ""),
        "arch_ref": bundle_json.get("arch_ref"),
        "api_ref": bundle_json.get("api_ref"),
        "primary_artifact_ref": "tech-design-bundle.md",
        "supporting_artifact_refs": ["tech-design-bundle.json", "tech-spec.md", "integration-context.json"],
        "integration_context_ref": "integration-context.json",
        "canonical_owner_refs": ["tech-design-bundle.json#/tech_design/technical_glossary_and_canonical_ownership"],
        "state_machine_ref": "tech-design-bundle.json#/tech_design/state_machine",
        "nfr_constraints_ref": "tech-design-bundle.json#/tech_design/non_functional_requirements",
        "migration_constraints_ref": "tech-design-bundle.json#/tech_design/migration_constraints",
        "algorithm_constraint_refs": ["tech-design-bundle.json#/tech_design/algorithm_constraints"],
    }
