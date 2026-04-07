import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-gate-human-orchestrator" / "scripts" / "gate_human_orchestrator.py"


class GateHumanOrchestratorTestSupport(unittest.TestCase):
    def run_cmd(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def make_gate_ready_package(self, root: Path, *, candidate_ref: str = "candidate.impl") -> Path:
        self.write_json(
            root / "artifacts" / "active" / "run-001" / "candidate.json",
            {
                "freeze_ready": True,
                "status": "freeze_ready",
                "product_summary": "Gate skill renders a reviewer-facing projection from Machine SSOT.",
                "roles": ["reviewer", "ssot owner"],
                "main_flow": ["render projection", "review constraints", "dispatch decision"],
                "deliverables": ["gate decision package"],
                "completed_state": "Projection ready for gate review.",
                "authoritative_output": "Machine SSOT remains authoritative.",
                "frozen_downstream_boundary": "Projection is not inheritable downstream.",
                "open_technical_decisions": ["Confirm reviewer wording."],
            },
        )
        self.write_json(
            root / "artifacts" / "registry" / "candidate-impl.json",
            {
                "artifact_ref": candidate_ref,
                "managed_artifact_ref": "artifacts/active/run-001/candidate.json",
                "status": "candidate",
                "trace": {"run_ref": "RUN-001"},
                "metadata": {},
                "lineage": [],
            },
        )
        self.write_json(root / "artifacts" / "active" / "run-001" / "acceptance.json", {"accepted": True})
        self.write_json(root / "artifacts" / "active" / "run-001" / "evidence.json", {"evidence": True})
        package_dir = root / "artifacts" / "active" / "gates" / "packages"
        self.write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": "RUN-001"},
                "payload": {
                    "candidate_ref": candidate_ref,
                    "machine_ssot_ref": candidate_ref,
                    "acceptance_ref": "artifacts/active/run-001/acceptance.json",
                    "evidence_bundle_ref": "artifacts/active/run-001/evidence.json",
                },
            },
        )
        return package_dir

    def make_raw_to_src_gate_ready_package(self, root: Path, *, run_id: str = "raw-src-run") -> Path:
        artifacts_dir = root / "artifacts" / "raw-to-src" / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / "src-candidate.md").write_text("# SRC Candidate\n\nApproved content.\n", encoding="utf-8")
        self.write_json(
            artifacts_dir / "src-candidate.json",
            {
                "artifact_type": "src_candidate",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": run_id,
                "title": "SRC Candidate",
                "status": "needs_review",
                "problem_statement": "Need a formal SRC artifact after approval.",
            },
        )
        self.write_json(
            artifacts_dir / "package-manifest.json",
            {
                "artifact_type": "src_candidate_package",
                "workflow_key": "product.raw-to-src",
                "workflow_run_id": run_id,
                "status": "freeze_ready",
            },
        )
        self.write_json(
            root / "artifacts" / "registry" / f"raw-to-src-{run_id}-src-candidate.json",
            {
                "artifact_ref": f"raw-to-src.{run_id}.src-candidate",
                "managed_artifact_ref": f"artifacts/raw-to-src/{run_id}/src-candidate.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "product.raw-to-src"},
                "metadata": {"layer": "formal"},
                "lineage": [],
            },
        )
        self.write_json(artifacts_dir / "acceptance-report.json", {"decision": "approve"})
        self.write_json(artifacts_dir / "result-summary.json", {"recommended_action": "next_skill"})
        self.write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})
        package_dir = artifacts_dir / "input"
        self.write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": run_id, "workflow_key": "product.raw-to-src"},
                "payload": {
                    "candidate_ref": f"raw-to-src.{run_id}.src-candidate",
                    "machine_ssot_ref": f"artifacts/raw-to-src/{run_id}/src-candidate.json",
                    "acceptance_ref": f"artifacts/raw-to-src/{run_id}/acceptance-report.json",
                    "evidence_bundle_ref": f"artifacts/raw-to-src/{run_id}/supervision-evidence.json",
                },
            },
        )
        return package_dir

    def make_feat_freeze_gate_ready_package(self, root: Path, *, run_id: str = "feat-freeze-run") -> Path:
        artifacts_dir = root / "artifacts" / "epic-to-feat" / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.write_json(
            artifacts_dir / "feat-freeze-bundle.json",
            {
                "artifact_type": "feat_freeze_package",
                "workflow_key": "product.epic-to-feat",
                "workflow_run_id": run_id,
                "title": "Execution Runner FEAT Bundle",
                "status": "accepted",
                "epic_freeze_ref": "EPIC-GATE-EXECUTION-RUNNER",
                "feat_refs": [
                    "FEAT-001",
                    "FEAT-002",
                    "FEAT-003",
                ],
                "downstream_workflows": [
                    "workflow.dev.feat_to_tech",
                    "workflow.qa.feat_to_testset",
                ],
                "bundle_intent": "Split the execution runner epic into user-visible FEAT slices so reviewer can approve user entry, control surface, and observability independently.",
                "bundle_shared_non_goals": [
                    "Do not collapse the FEAT bundle back into abstract runtime only wording.",
                    "Do not drift into TECH or implementation sequencing.",
                ],
                "epic_context": {
                    "business_goal": "Freeze approve -> ready job -> runner claim -> next skill invocation as a user-visible product line.",
                    "product_positioning": "This FEAT bundle sits between the approved EPIC and downstream TECH / TESTSET workflows.",
                    "actors_and_roles": [
                        {
                            "role": "Claude/Codex CLI operator",
                            "responsibility": "Start or resume the runner through the dedicated skill entry.",
                        },
                        {
                            "role": "workflow / orchestration operator",
                            "responsibility": "Observe backlog, running, failed, and waiting-human states.",
                        },
                    ],
                    "epic_success_criteria": [
                        "At least one approve -> ready job -> runner claim -> next skill invocation path is testable.",
                        "Runner entry, control surface, and observability stay explicit and user-facing.",
                    ],
                    "decomposition_rules": [
                        "Split by independently reviewable product behavior slices.",
                        "Do not rewrite approve into formal publication or publish-only state.",
                    ],
                },
                "features": [
                    {
                        "feat_ref": "FEAT-001",
                        "title": "Runner 用户入口流",
                        "goal": "Freeze a dedicated user-invokable runner skill entry.",
                        "track": "foundation",
                    },
                    {
                        "feat_ref": "FEAT-002",
                        "title": "Runner 控制面流",
                        "goal": "Freeze the CLI control surface for claim, run, complete, and fail.",
                        "track": "foundation",
                    },
                    {
                        "feat_ref": "FEAT-003",
                        "title": "Runner 运行监控流",
                        "goal": "Freeze the observability surface for backlog, running, failed, and waiting-human states.",
                        "track": "foundation",
                    },
                ],
                "source_refs": [
                    "ADR-018",
                    "EPIC-GATE-EXECUTION-RUNNER",
                ],
            },
        )
        self.write_json(artifacts_dir / "acceptance-report.json", {"decision": "approve"})
        self.write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})
        package_dir = artifacts_dir / "input"
        self.write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": run_id, "workflow_key": "product.epic-to-feat"},
                "payload": {
                    "candidate_ref": f"epic-to-feat.{run_id}.feat-freeze-bundle",
                    "machine_ssot_ref": f"artifacts/epic-to-feat/{run_id}/feat-freeze-bundle.json",
                    "acceptance_ref": f"artifacts/epic-to-feat/{run_id}/acceptance-report.json",
                    "evidence_bundle_ref": f"artifacts/epic-to-feat/{run_id}/supervision-evidence.json",
                },
            },
        )
        return package_dir

    def make_tech_design_gate_ready_package(self, root: Path, *, run_id: str = "tech-design-run") -> Path:
        artifacts_dir = root / "artifacts" / "feat-to-tech" / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.write_json(
            artifacts_dir / "tech-design-bundle.json",
            {
                "artifact_type": "tech_design_package",
                "workflow_key": "dev.feat-to-tech",
                "workflow_run_id": run_id,
                "title": "主链候选提交与交接流 Technical Design Package",
                "status": "accepted",
                "feat_ref": "FEAT-SRC-005-001",
                "tech_ref": "TECH-SRC-005-001",
                "surface_map_ref": "SURFACE-MAP-FEAT-SRC-005-001",
                "source_refs": ["FEAT-SRC-005-001", "EPIC-SRC-005-001", "SRC-005", "ADR-011"],
                "selected_feat": {
                    "feat_ref": "FEAT-SRC-005-001",
                    "title": "主链候选提交与交接流",
                    "goal": "冻结 governed skill 如何把 candidate package 提交为 authoritative handoff，并把候选交接正式送入 gate 消费链。",
                    "surface_map_ref": "SURFACE-MAP-FEAT-SRC-005-001",
                    "tech_owner_ref": "TECH-SRC-005-001",
                    "tech_action": "update",
                },
                "tech_design": {
                    "design_focus": [
                        "Freeze a concrete TECH design for 主链候选提交与交接流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready."
                    ],
                    "implementation_architecture": [
                        "Execution loop、gate loop、human review 通过文件化 handoff runtime 协作。",
                        "Runtime 在收到 gate decision object 后，只负责可见性回写与 revise/retry re-entry routing。",
                    ],
                    "module_plan": [
                        "Handoff runtime adapter：负责把受治理对象写入/读取主链 runtime，并维持 traceability。",
                        "Submission coordinator：定义 candidate/proposal/evidence 进入 authoritative handoff 的入口、receipt 与 pending visibility。",
                        "Decision return adapter：消费 gate decision object，并把 revise/retry 映射成 runtime re-entry directive。",
                    ],
                    "state_model": [
                        "`handoff_prepared` -> `handoff_submitted` -> `gate_pending_visible` -> `decision_returned`",
                        "`decision_returned(revise|retry)` -> `runtime_reentry_directive_written` -> `handoff_prepared`",
                    ],
                    "interface_contracts": [
                        "`HandoffEnvelope`: input=`producer_ref`, `proposal_ref`, `payload_ref`; output=`handoff_ref`, `gate_pending_ref`, `trace_ref`, `canonical_payload_path`。",
                        "`DecisionReturnEnvelope`: input=`handoff_ref`, `decision_ref`, `decision`; output=`boundary_handoff_record | reentry_directive`。",
                    ],
                    "implementation_strategy": [
                        "先冻结 authoritative handoff、pending visibility 和 decision return intake。",
                        "最后用至少一条真实 submit -> pending -> decision-return -> re-entry pilot 验证协作闭环成立。",
                    ],
                },
                "downstream_handoff": {
                    "target_workflow": "workflow.dev.tech_to_impl",
                },
            },
        )
        self.write_json(artifacts_dir / "acceptance-report.json", {"decision": "approve"})
        self.write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})
        package_dir = artifacts_dir / "input"
        self.write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": run_id, "workflow_key": "dev.feat-to-tech"},
                "payload": {
                    "candidate_ref": f"feat-to-tech.{run_id}.tech-design-bundle",
                    "machine_ssot_ref": f"artifacts/feat-to-tech/{run_id}/tech-design-bundle.json",
                    "acceptance_ref": f"artifacts/feat-to-tech/{run_id}/acceptance-report.json",
                    "evidence_bundle_ref": f"artifacts/feat-to-tech/{run_id}/supervision-evidence.json",
                },
            },
        )
        return package_dir

    def make_test_set_gate_ready_package(self, root: Path, *, run_id: str = "test-set-run") -> Path:
        artifacts_dir = root / "artifacts" / "feat-to-testset" / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.write_json(
            artifacts_dir / "test-set-bundle.json",
            {
                "artifact_type": "test_set_candidate_package",
                "workflow_key": "qa.feat-to-testset",
                "workflow_run_id": run_id,
                "title": "主链候选提交与交接流 TESTSET Candidate Package",
                "status": "approval_pending",
                "feat_ref": "FEAT-SRC-005-001",
                "test_set_ref": "TESTSET-SRC-005-001",
                "source_refs": ["FEAT-SRC-005-001", "EPIC-SRC-005-001", "SRC-005", "ADR-011"],
                "selected_feat": {
                    "feat_ref": "FEAT-SRC-005-001",
                    "title": "主链候选提交与交接流",
                    "goal": "冻结 governed skill 如何把 candidate package 提交为 authoritative handoff，并把候选交接正式送入 gate 消费链。",
                },
                "requirement_analysis": {
                    "coverage_scope": [
                        "定义 candidate package、proposal、evidence 在什么触发场景下被提交。",
                        "定义提交后形成什么 authoritative handoff object。",
                        "定义提交完成后对上游和 gate 分别暴露什么业务结果。",
                    ],
                    "coverage_exclusions": [
                        "Do not define candidate -> formal upgrade semantics, gate decision authority, or materialization outputs here.",
                        "Do not define object admission, formal-read eligibility, or path governance policy here.",
                    ],
                },
                "strategy_draft": {
                    "test_units": [
                        {
                            "unit_ref": "TS-SRC-005-001-U01",
                            "title": "candidate submit-mainline 明确 execution / gate / human loop 的责任边界",
                            "trigger_action": "执行 candidate package submit-mainline，并记录 execution loop、gate loop、human loop 的 transition ownership。",
                        },
                        {
                            "unit_ref": "TS-SRC-005-001-U04",
                            "title": "duplicate_submission 相同 payload 必须返回 idempotent replay 结果",
                            "trigger_action": "对同一 payload 重复执行 submit-mainline，并对比返回的 handoff_ref 与 replay 语义。",
                        },
                        {
                            "unit_ref": "TS-SRC-005-001-U09",
                            "title": "payload_ref 缺失或坏路径时 submit-mainline 必须 fail closed",
                            "trigger_action": "提交缺失 payload_ref 或坏路径的 candidate，并读取 submit-mainline 结果。",
                        },
                    ]
                },
                "test_set": {
                    "pass_criteria": [
                        "每条 acceptance check 都有至少一个可执行测试单元映射。",
                        "TESTSET 不越界覆盖相邻 FEAT 或新需求。",
                        "candidate package 在外置 approval 前保持 machine-readable traceability 与 gate subject identity。",
                    ],
                    "environment_assumptions": [
                        "需要可解析 selected FEAT 所依赖的集成环境与上游 artifact lineage。",
                        "需要保留 execution evidence 与 supervision evidence 所要求的最小审计链。",
                        "依赖服务或上游能力应以可观测、可判定的方式处于可用状态。",
                    ],
                },
                "downstream_target": "skill.qa.test_exec_cli",
            },
        )
        self.write_json(artifacts_dir / "acceptance-report.json", {"decision": "approve"})
        self.write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})
        package_dir = artifacts_dir / "input"
        self.write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": run_id, "workflow_key": "qa.feat-to-testset"},
                "payload": {
                    "candidate_ref": f"feat-to-testset.{run_id}.test-set-bundle",
                    "machine_ssot_ref": f"artifacts/feat-to-testset/{run_id}/test-set-bundle.json",
                    "acceptance_ref": f"artifacts/feat-to-testset/{run_id}/acceptance-report.json",
                    "evidence_bundle_ref": f"artifacts/feat-to-testset/{run_id}/supervision-evidence.json",
                },
            },
        )
        return package_dir

    def make_impl_gate_ready_package(self, root: Path, *, run_id: str = "impl-run") -> Path:
        artifacts_dir = root / "artifacts" / "tech-to-impl" / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.write_json(
            artifacts_dir / "impl-bundle.json",
            {
                "artifact_type": "feature_impl_candidate_package",
                "workflow_key": "dev.tech-to-impl",
                "workflow_run_id": run_id,
                "title": "主链候选提交与交接流 Implementation Task Package",
                "status": "execution_ready",
                "feat_ref": "FEAT-SRC-005-001",
                "tech_ref": "TECH-SRC-005-001",
                "impl_ref": "IMPL-SRC-005-001",
                "arch_ref": "ARCH-SRC-005-001",
                "api_ref": "API-SRC-005-001",
                "surface_map_ref": "SURFACE-MAP-FEAT-SRC-005-001",
                "resolved_design_refs": {
                    "surface_map_ref": "SURFACE-MAP-FEAT-SRC-005-001",
                    "prototype_ref": "PROTO-SRC-005-001",
                    "ui_ref": "UI-SRC-005-001",
                },
                "source_refs": ["FEAT-SRC-005-001", "TECH-SRC-005-001", "EPIC-SRC-005-001", "SRC-005", "ADR-011"],
                "selected_scope": {
                    "title": "主链候选提交与交接流",
                    "goal": "冻结 governed skill 如何把 candidate package 提交为 authoritative handoff，并把候选交接正式送入 gate 消费链。",
                    "scope": [
                        "定义 candidate package、proposal、evidence 在什么触发场景下被提交。",
                        "定义提交后形成什么 authoritative handoff object。",
                        "定义提交完成后对上游和 gate 分别暴露什么业务结果。",
                    ],
                    "constraints": [
                        "该 FEAT 只负责 loop 协作边界，不得把 formalization 细则混入 loop 责任定义。",
                        "Loop 协作语义必须显式说明哪类对象触发 gate、哪类 decision 允许回流、哪类状态允许继续推进。",
                    ],
                    "dependencies": [
                        "本 FEAT 不负责 formalization 语义、升级判定与物化结果。",
                        "对象是否具备正式消费资格由对象分层 FEAT 决定。",
                    ],
                },
                "workstream_assessment": {
                    "frontend_required": False,
                    "backend_required": True,
                    "migration_required": False,
                    "rationale": {
                        "frontend": ["No explicit UI/page/component implementation surface was detected."],
                        "backend": ["Detected runtime/service/contract surface: gate, io, runtime."],
                        "migration": ["No migration, cutover, rollback, or compat-mode surface was detected."],
                    },
                },
                "upstream_design_refs": {
                    "frozen_decisions": {
                        "state_model": [
                            "`handoff_prepared` -> `handoff_submitted` -> `gate_pending_visible` -> `decision_returned`",
                            "`decision_returned(revise|retry)` -> `runtime_reentry_directive_written` -> `handoff_prepared`",
                        ],
                        "main_sequence": [
                            "1. normalize candidate/proposal/evidence submission and producer state",
                            "2. persist authoritative handoff object and emit gate-pending visibility",
                            "3. route proposal into gate loop and escalate to human review when required",
                        ],
                        "implementation_unit_mapping": [
                            "cli/lib/protocol.py (extend): 定义 HandoffEnvelope、PendingVisibilityRecord、DecisionReturnEnvelope、ReentryDirective 结构。",
                            "cli/lib/mainline_runtime.py (new): 管理 authoritative submission、pending visibility、decision-return intake 与 boundary handoff record。",
                            "cli/lib/reentry.py (new): 只处理 revise / retry 的 runtime routing、directive 写回与 replay guard，不拥有 decision semantics。",
                            "cli/commands/gate/command.py (extend): 接入 submit-handoff / show-pending 路径，并把 returned decision 交给 cli/lib/mainline_runtime.py 消费。",
                        ],
                        "interface_contracts": [
                            "`HandoffEnvelope`: input=`producer_ref`, `proposal_ref`, `payload_ref`; output=`handoff_ref`, `gate_pending_ref`, `trace_ref`, `canonical_payload_path`。",
                            "`DecisionReturnEnvelope`: input=`handoff_ref`, `decision_ref`, `decision`; output=`boundary_handoff_record | reentry_directive`。",
                        ],
                    }
                },
                "implementation_steps": [
                    {
                        "title": "Freeze upstream refs and touch set",
                        "work": "Lock feat_ref, tech_ref, optional arch/api refs, and the concrete touch set before coding.",
                    },
                    {
                        "title": "Implement frozen runtime units",
                        "work": "Build authoritative submission, pending visibility, returned decision intake, and replay-safe re-entry routing.",
                    },
                    {
                        "title": "Integrate, evidence, and handoff",
                        "work": "Close the loop with evidence, smoke gate, and downstream feature delivery handoff.",
                    },
                ],
                "downstream_handoff": {
                    "target_template_id": "template.dev.feature_delivery_l2",
                    "primary_artifact_ref": "impl-bundle.json",
                    "phase_inputs": {
                        "implementation_task": ["impl-task.md"],
                        "backend": ["backend-workstream.md"],
                        "integration": ["integration-plan.md"],
                        "evidence": ["dev-evidence-plan.json", "smoke-gate-subject.json"],
                        "upstream_design": ["upstream-design-refs.json"],
                    },
                    "acceptance_refs": ["AC-001", "AC-002", "AC-003"],
                },
            },
        )
        self.write_json(artifacts_dir / "acceptance-report.json", {"decision": "approve"})
        self.write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})
        package_dir = artifacts_dir / "input"
        self.write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": run_id, "workflow_key": "dev.tech-to-impl"},
                "payload": {
                    "candidate_ref": f"tech-to-impl.{run_id}.impl-bundle",
                    "machine_ssot_ref": f"artifacts/tech-to-impl/{run_id}/impl-bundle.json",
                    "acceptance_ref": f"artifacts/tech-to-impl/{run_id}/acceptance-report.json",
                    "evidence_bundle_ref": f"artifacts/tech-to-impl/{run_id}/supervision-evidence.json",
                },
            },
        )
        return package_dir

    def make_runtime_pending_item(self, root: Path, *, key: str = "gate-job-001") -> None:
        handoff_ref = f"artifacts/active/gates/handoffs/{key}.json"
        pending_ref = f"artifacts/active/gates/pending/{key}.json"
        self.write_json(root / handoff_ref, {"trace": {"run_ref": "RUN-001"}, "producer_ref": "skill.test", "proposal_ref": key, "payload_ref": "artifacts/active/gates/packages/gate-ready-package.json", "pending_state": "gate_pending"})
        self.write_json(root / pending_ref, {"trace": {"run_ref": "RUN-001"}, "handoff_ref": handoff_ref, "producer_ref": "skill.test", "proposal_ref": key, "pending_state": "gate_pending"})
        index_path = root / "artifacts" / "active" / "gates" / "pending" / "index.json"
        index_payload = {"handoffs": {}}
        if index_path.exists():
            index_payload = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(index_payload.get("handoffs"), dict):
                index_payload["handoffs"] = {}
        index_payload["handoffs"][key] = {
            "handoff_ref": handoff_ref,
            "gate_pending_ref": pending_ref,
            "payload_digest": "digest",
            "trace_ref": "",
            "pending_state": "gate_pending",
            "assigned_gate_queue": "mainline.gate.pending",
        }
        self.write_json(index_path, index_payload)

    def make_legacy_runtime_pending_item(self, root: Path, *, key: str = "legacy-gate-job-001") -> Path:
        candidate_md = root / "artifacts" / "raw-to-src" / "run-legacy" / "src-candidate.md"
        candidate_md.parent.mkdir(parents=True, exist_ok=True)
        candidate_md.write_text("# Legacy candidate\n", encoding="utf-8")
        self.write_json(root / "artifacts" / "registry" / "formal-src-run-legacy.json", {"artifact_ref": "formal.src.run-legacy", "managed_artifact_ref": "artifacts/raw-to-src/run-legacy/src-candidate.md", "status": "materialized", "trace": {"run_ref": "RUN-LEGACY"}, "metadata": {}, "lineage": []})
        proposal_path = root / "artifacts" / "raw-to-src" / "run-legacy" / "handoff-proposal.json"
        self.write_json(proposal_path, {"supporting_artifact_refs": ["artifacts/raw-to-src/run-legacy/acceptance-report.json"], "evidence_bundle_refs": ["artifacts/raw-to-src/run-legacy/execution-evidence.json"]})
        self.write_json(root / "artifacts" / "raw-to-src" / "run-legacy" / "acceptance-report.json", {"decision": "approve"})
        self.write_json(root / "artifacts" / "raw-to-src" / "run-legacy" / "execution-evidence.json", {"ok": True})
        handoff_path = root / "artifacts" / "active" / "handoffs" / f"{key}.json"
        pending_path = root / "artifacts" / "active" / "gates" / "pending" / f"{key}.json"
        self.write_json(
            handoff_path,
            {
                "trace": {"run_ref": "RUN-LEGACY"},
                "producer_ref": "skill.test",
                "proposal_ref": str(proposal_path),
                "payload_ref": str(candidate_md),
                "trace_context_ref": str(root / "artifacts" / "raw-to-src" / "run-legacy" / "execution-evidence.json"),
                "state": "gate_pending",
                "gate_pending_ref": f"artifacts/active/gates/pending/{key}.json",
            },
        )
        self.write_json(pending_path, {"handoff_ref": f"artifacts/active/handoffs/{key}.json", "pending_state": "gate_pending", "assigned_gate_queue": "gate-queue-001"})
        self.write_json(root / "artifacts" / "active" / "gates" / "pending" / "_queue-index.json", {"next_index": 2})
        return pending_path
