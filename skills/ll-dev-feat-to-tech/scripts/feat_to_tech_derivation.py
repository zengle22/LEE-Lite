#!/usr/bin/env python3
"""
Derivation helpers for the lite-native feat-to-tech runtime.
"""

from __future__ import annotations

from typing import Any

from feat_to_tech_common import ensure_list, unique_strings


ARCH_KEYWORDS = [
    "架构",
    "architecture",
    "boundary",
    "边界",
    "module",
    "模块",
    "subsystem",
    "topology",
    "调用链",
    "io",
    "path",
    "registry",
    "external gate",
    "cross-skill",
]

STRONG_API_KEYWORDS = [
    "api",
    "接口",
    "contract",
    "schema",
    "request",
    "response",
    "webhook",
]

WEAK_API_KEYWORDS = [
    "event",
    "message",
    "proposal",
    "decision",
    "consumer",
    "provider",
    "handoff",
    "queue",
]

NEGATION_MARKERS = [
    "不",
    "无",
    "without",
    "no ",
    "not ",
    "do not",
]


def feature_text(feature: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ["title", "goal", "derived_axis"]:
        value = str(feature.get(key) or "").strip()
        if value:
            parts.append(value)
    for key in ["scope", "constraints", "dependencies", "outputs", "non_goals"]:
        parts.extend(ensure_list(feature.get(key)))
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            parts.extend(
                [
                    str(check.get("scenario") or ""),
                    str(check.get("given") or ""),
                    str(check.get("when") or ""),
                    str(check.get("then") or ""),
                ]
            )
    return "\n".join(parts).lower()


def feature_core_text(feature: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ["title", "goal", "derived_axis"]:
        value = str(feature.get(key) or "").strip()
        if value:
            parts.append(value)
    for key in ["scope", "constraints"]:
        parts.extend(ensure_list(feature.get(key)))
    return "\n".join(parts).lower()


def keyword_hits(feature: dict[str, Any], keywords: list[str]) -> list[str]:
    hits: list[str] = []
    segments: list[str] = []
    for key in ["title", "goal", "derived_axis"]:
        value = str(feature.get(key) or "").strip()
        if value:
            segments.append(value)
    for key in ["scope", "constraints", "dependencies", "outputs", "non_goals"]:
        segments.extend(ensure_list(feature.get(key)))
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            segments.extend(
                [
                    str(check.get("scenario") or ""),
                    str(check.get("given") or ""),
                    str(check.get("when") or ""),
                    str(check.get("then") or ""),
                ]
            )

    for segment in segments:
        lowered = segment.lower().strip()
        if not lowered:
            continue
        if any(marker in lowered for marker in NEGATION_MARKERS):
            continue
        for keyword in keywords:
            if keyword in lowered and keyword not in hits:
                hits.append(keyword)
    return hits


def build_refs(feature: dict[str, Any], package: Any) -> dict[str, str]:
    feat_ref = str(feature.get("feat_ref") or "").strip()
    feat_suffix = feat_ref.replace("FEAT-", "", 1) if feat_ref.startswith("FEAT-") else feat_ref
    return {
        "feat_ref": feat_ref,
        "tech_ref": f"TECH-{feat_ref}",
        "arch_ref": f"ARCH-{feat_suffix}" if feat_suffix else "",
        "api_ref": f"API-{feat_suffix}" if feat_suffix else "",
        "epic_ref": str(package.feat_json.get("epic_freeze_ref") or ""),
        "src_ref": str(package.feat_json.get("src_root_id") or ""),
    }


def explicit_axis(feature: dict[str, Any]) -> str:
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    mapping = {
        "collaboration-loop": "collaboration",
        "handoff-formalization": "formalization",
        "object-layering": "layering",
        "artifact-io-governance": "io_governance",
        "skill-adoption-e2e": "adoption_e2e",
    }
    if axis_id in mapping:
        return mapping[axis_id]
    title = str(feature.get("title") or "").strip().lower()
    if "候选提交" in title or "交接流" in title:
        return "collaboration"
    if "审核与裁决" in title or ("gate" in title and "裁决" in title):
        return "formalization"
    if "formal 发布" in title or "下游准入" in title:
        return "layering"
    if "受治理 io" in title or "落盘与读取" in title:
        return "io_governance"
    if "pilot 验证" in title or "接入与 pilot" in title:
        return "adoption_e2e"
    return ""


def selected_feat_snapshot(feature: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "feat_ref",
        "title",
        "goal",
        "axis_id",
        "track",
        "scope",
        "constraints",
        "dependencies",
        "upstream_feat",
        "downstream_feat",
        "consumes",
        "produces",
        "authoritative_artifact",
        "gate_decision_dependency_feat_refs",
        "gate_decision_dependency",
        "admission_dependency_feat_refs",
        "admission_dependency",
        "dependency_kinds",
        "identity_and_scenario",
        "business_flow",
        "product_objects_and_deliverables",
        "collaboration_and_timeline",
        "acceptance_and_testability",
        "frozen_downstream_boundary",
    ]
    snapshot: dict[str, Any] = {}
    for key in keys:
        if key in feature:
            snapshot[key] = feature.get(key)
    return snapshot


def assess_optional_artifacts(feature: dict[str, Any], package: Any) -> dict[str, Any]:
    axis = feature_axis(feature)
    arch_hits = keyword_hits(feature, ARCH_KEYWORDS)
    strong_api_hits = keyword_hits(feature, STRONG_API_KEYWORDS)
    weak_api_hits = keyword_hits(feature, WEAK_API_KEYWORDS)
    source_refs = ensure_list(feature.get("source_refs")) + ensure_list(package.feat_json.get("source_refs"))

    arch_reasons: list[str] = []
    api_reasons: list[str] = []

    if any(ref.startswith("ARCH-") for ref in source_refs):
        arch_reasons.append("Inherited source refs already point to an upstream architecture object.")
    if len(ensure_list(feature.get("dependencies"))) >= 2:
        arch_reasons.append("The FEAT exposes multiple boundary dependencies that need explicit architectural placement.")
    if len(arch_hits) >= 2:
        arch_reasons.append(f"Architecture-impacting language appears in the FEAT boundary: {', '.join(arch_hits[:4])}.")

    if strong_api_hits:
        api_reasons.append(f"Explicit API/contract language appears in the FEAT boundary: {', '.join(strong_api_hits[:4])}.")
    if any("contract" in item.lower() or "proposal" in item.lower() or "decision" in item.lower() for item in ensure_list(feature.get("outputs"))):
        api_reasons.append("The FEAT outputs already imply a boundary contract or exchange object.")
    if any("consumer" in item.lower() or "provider" in item.lower() for item in ensure_list(feature.get("dependencies"))):
        api_reasons.append("The FEAT depends on explicit consumer/provider coordination.")
    if axis in {"collaboration", "formalization"} and len(weak_api_hits) >= 3 and any(hit in weak_api_hits for hit in ["decision", "queue", "event", "message"]):
        api_reasons.append(f"Cross-loop exchange semantics require an explicit boundary contract: {', '.join(weak_api_hits[:4])}.")
    if axis in {"io_governance", "adoption_e2e"}:
        api_reasons.append("The FEAT defines CLI-facing governed commands and request/response contracts that must be frozen explicitly.")

    arch_required = bool(arch_reasons)
    api_required = bool(api_reasons)

    if not arch_required:
        arch_reasons.append("No architecture-impacting module placement or topology change was detected.")
    if not api_required:
        api_reasons.append("No explicit cross-boundary contract surface was detected.")

    return {
        "arch_required": arch_required,
        "api_required": api_required,
        "arch_rationale": arch_reasons,
        "api_rationale": api_reasons,
    }


def design_focus(feature: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("scope"))[:4]
    if len(items) < 3:
        items.extend(ensure_list(feature.get("constraints"))[: 3 - len(items)])
    return unique_strings(items)[:4]


def implementation_rules(feature: dict[str, Any]) -> list[str]:
    rules = ensure_list(feature.get("constraints"))[:4]
    source_refs = ensure_list(feature.get("source_refs"))
    if "ADR-007" in source_refs and feature_axis(feature) == "adoption_e2e":
        rules.extend(
            [
                "Authoritative inherited constraints：对外暴露一个宽 skill family：`skill.qa.test_exec_web_e2e` 与 `skill.qa.test_exec_cli`。",
                "Authoritative inherited constraints：内部保留一个窄 runner family：`skill.runner.test_e2e` 与 `skill.runner.test_cli`。",
            ]
        )
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            scenario = str(check.get("scenario") or "").strip()
            then = str(check.get("then") or "").strip()
            if scenario and then:
                rules.append(f"{scenario}: {then}")
    return unique_strings(rules)[:8]


def non_functional_requirements(feature: dict[str, Any], package: Any) -> list[str]:
    refs = ensure_list(feature.get("source_refs")) + ensure_list(package.feat_json.get("source_refs"))
    requirements = [
        "Preserve FEAT, EPIC, and SRC traceability across every emitted design object.",
        "Keep the package freeze-ready by recording execution evidence and supervision evidence.",
        "Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.",
    ]
    if any(ref.startswith("ADR-") for ref in refs):
        requirements.append("Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.")
    return unique_strings(requirements)


def architecture_topics(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "collaboration":
        return [
            "Boundary to gate decision / publication: 本 FEAT 负责 authoritative handoff submission、gate-pending visibility 与 decision-driven runtime re-entry routing，不负责 decision vocabulary、decision issuance 与 formal publication trigger semantics。",
            "Boundary to admission/layering: 本 FEAT 可以提交 candidate / proposal / evidence，但 formal admission、formal refs 与 downstream read eligibility 由对象分层 FEAT 决定。",
            "Dedicated runtime placement is required so submission receipt、pending visibility 和 re-entry routing 由同一 authoritative carrier 负责，而不是散落在 producer skill 或 gate worker 中。",
        ]
    if axis == "formalization":
        return [
            "Boundary to collaboration runtime: formalization FEAT 消费 authoritative handoff 与 proposal，不重新定义 submission receipt 或 pending visibility。",
            "Boundary to downstream publication/admission: 本 FEAT 负责 gate brief、pending human decision、authoritative decision object 与 dispatch trigger，不负责 formal publish / consumer admission policy 本身。",
            "Dedicated gate placement is required so brief、pending、decision、dispatch 使用同一 authoritative path，而不是散落在 gate worker 或 business skill 中。",
        ]
    if axis == "layering":
        return [
            "Boundary to collaboration/formalization: 本 FEAT 消费已有 candidate/formal objects，但不定义 handoff submission 或 materialization dispatch。",
            "Boundary to IO governance: 本 FEAT 冻结 authoritative refs 与 admission policy，不重写 path / mode / overwrite 规则。",
            "Dedicated lineage/admission placement is required so formal refs、layer policy 与 downstream eligibility stay authoritative.",
        ]
    if axis == "io_governance":
        return [
            "Boundary to object layering: 本 FEAT 冻结受治理 IO/path 边界，但不决定对象层级与 admission policy。",
            "Boundary to gate decision / publication: 本 FEAT 约束 write/read carrier 与 receipt/registry 行为，不定义 approve/reject 等 decision semantics。",
            "Dedicated gateway placement is required so policy、IO execution、registry bind 与 receipt publication use one governed carrier.",
        ]
    if axis == "adoption_e2e":
        return [
            "Boundary to foundation FEATs: 本 FEAT 只定义 onboarding/pilot/cutover 挂接边界，不重写 collaboration、gate decision/publication、IO foundation internals。",
            "Boundary to audit/gate consumption: 本 FEAT 组织 pilot evidence 与 cutover routing，不新建平行 decision 体系。",
            "Dedicated rollout placement is required so wave state、compat mode 与 fallback remain authoritative across skill adoption.",
        ]
    topics = ensure_list(feature.get("dependencies"))[:3]
    if len(topics) < 2:
        topics.extend(ensure_list(feature.get("scope"))[: 2 - len(topics)])
    return unique_strings(topics)[:3]


def responsibility_splits(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "collaboration":
        return [
            "Execution loop owns candidate/proposal/evidence preparation and authoritative submission initiation.",
            "Gate loop and human review own decision semantics; this FEAT only consumes returned decision objects as structured inputs for visibility and routing.",
            "Runtime owns gate-pending visibility and revise/retry re-entry routing after decision return, but does not own formal materialization or final approval semantics.",
        ]
    if axis == "formalization":
        return [
            "External gate owns gate brief build and approve / revise / retry / handoff / reject decision semantics, and emits the only authoritative decision object.",
            "Dispatch router owns execution / delegate / publication-trigger routing after decision issuance, but does not own formal publish itself or downstream admission policy.",
            "Business skills do not bypass gate by issuing decision objects or writing formal publication triggers directly.",
        ]
    if axis == "layering":
        return [
            "Lineage resolver owns candidate/formal/downstream object identity mapping and authoritative refs.",
            "Admission checker owns consumer allow/deny decisions based on formal refs and layer eligibility.",
            "Business skills and consumers do not infer eligibility from paths, filenames, or adjacency.",
        ]
    if axis == "io_governance":
        return [
            "Path policy owns allow/deny and mode decisions before any governed read/write executes.",
            "Gateway owns write/read orchestration, registry prerequisite checks, receipt generation, and managed ref publication.",
            "Callers do not bypass Gateway with direct filesystem writes once the operation is declared governed.",
        ]
    if axis == "adoption_e2e":
        return [
            "Rollout controller owns onboarding wave、compat mode 与 cutover/fallback routing.",
            "Pilot verifier owns end-to-end evidence completeness checks across producer / consumer / audit / gate.",
            "Foundation FEATs keep ownership of their technical semantics; onboarding does not rewrite them.",
        ]
    splits: list[str] = []
    for item in ensure_list(feature.get("constraints")) + ensure_list(feature.get("non_goals")):
        lowered = item.lower()
        if any(marker in lowered for marker in ["不", "只", "不得", "only", "must not", "do not", "not ", "leave", "留给"]):
            splits.append(item)
    if len(splits) < 2:
        splits.extend(ensure_list(feature.get("dependencies")))
    if len(splits) < 2:
        splits.extend(ensure_list(feature.get("scope")))
    return unique_strings(splits)[:3]


def api_surfaces(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "collaboration":
        return [
            "handoff submission contract",
            "gate pending visibility contract",
        ]
    if axis == "formalization":
        return [
            "gate decision contract",
            "formal publication contract",
        ]
    if axis == "layering":
        return [
            "formal ref resolution contract",
            "admission validation contract",
        ]
    if axis == "io_governance":
        return [
            "governed write contract",
            "governed read contract",
        ]
    if axis == "adoption_e2e":
        return [
            "skill onboarding contract",
            "pilot evidence submission contract",
        ]
    surfaces: list[str] = []
    text = feature_text(feature)
    if "handoff" in text:
        surfaces.append("handoff object contract")
    if "decision" in text or "gate" in text:
        surfaces.append("gate decision contract")
    if "proposal" in text:
        surfaces.append("proposal exchange contract")
    if "consumer" in text or "provider" in text:
        surfaces.append("consumer/provider boundary contract")
    if "event" in text or "message" in text or "queue" in text:
        surfaces.append("event or message contract")
    if not surfaces:
        surfaces.append("feature-specific boundary contract")
    return unique_strings(surfaces)[:4]


def api_cli_commands(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "collaboration":
        return [
            "`ll gate submit-handoff --request <gate_submit_handoff.request.json> --response-out <gate_submit_handoff.response.json>` via `cli/commands/gate/command.py`",
            "`ll gate show-pending --request <gate_show_pending.request.json> --response-out <gate_show_pending.response.json>` via `cli/commands/gate/command.py`",
        ]
    if axis == "formalization":
        return [
            "`ll gate evaluate --request <gate_evaluate.request.json> --response-out <gate_evaluate.response.json>` via `cli/commands/gate/command.py`",
            "`ll gate dispatch --request <gate_dispatch.request.json> --response-out <gate_dispatch.response.json>` via `cli/commands/gate/command.py`",
        ]
    if axis == "layering":
        return [
            "`ll registry resolve-formal-ref --request <registry_resolve_formal_ref.request.json> --response-out <registry_resolve_formal_ref.response.json>` via `cli/commands/registry/command.py`",
            "`ll registry validate-admission --request <registry_validate_admission.request.json> --response-out <registry_validate_admission.response.json>` via `cli/commands/registry/command.py`",
        ]
    if axis == "io_governance":
        return [
            "`ll artifact commit --request <artifact_commit.request.json> --response-out <artifact_commit.response.json>` via `cli/commands/artifact/command.py`",
            "`ll artifact read --request <artifact_read.request.json> --response-out <artifact_read.response.json>` via `cli/commands/artifact/command.py`",
        ]
    if axis == "adoption_e2e":
        return [
            "`ll rollout onboard-skill --request <rollout_onboard_skill.request.json> --response-out <rollout_onboard_skill.response.json>` via `cli/commands/rollout/command.py`",
            "`ll audit submit-pilot-evidence --request <audit_submit_pilot_evidence.request.json> --response-out <audit_submit_pilot_evidence.response.json>` via `cli/commands/audit/command.py`",
        ]
    return [
        "`ll gate submit-handoff --request <gate_submit_handoff.request.json> --response-out <gate_submit_handoff.response.json>` via `cli/commands/gate/command.py`",
        "`ll gate show-pending --request <gate_show_pending.request.json> --response-out <gate_show_pending.response.json>` via `cli/commands/gate/command.py`",
    ]


def api_command_specs(feature: dict[str, Any]) -> list[dict[str, Any]]:
    axis = feature_axis(feature)
    if axis == "collaboration":
        return [
            {
                "command": "ll gate submit-handoff",
                "surface": "`ll gate submit-handoff --request <gate_submit_handoff.request.json> --response-out <gate_submit_handoff.response.json>` via `cli/commands/gate/command.py`",
                "request_schema": [
                    "`producer_ref: string`",
                    "`proposal_ref: string`",
                    "`payload_ref: string`",
                    "`pending_state: enum<gate_pending|human_review_pending|reentry_pending|retry_pending>`",
                    "`trace_context_ref: string?`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`handoff_ref`, `queue_slot`, `gate_pending_ref`, `canonical_payload_path`, `pending_state`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                    "error fields=`code`, `message`, `retryable`, `idempotent_replay`",
                ],
                "field_semantics": [
                    "`pending_state` freezes only pending-visibility states; it must not encode final gate decisions.",
                    "`gate_pending_ref` is the canonical ref of the pending-intake record created by this submission.",
                    "`queue_slot` identifies the current gate queue slot responsible for the handoff.",
                    "`canonical_payload_path` must point to the normalized runtime-visible payload location used for traceability.",
                ],
                "enum_domain": [
                    "`pending_state ∈ {gate_pending, human_review_pending, reentry_pending, retry_pending}`",
                ],
                "invariants": [
                    "one accepted submission creates exactly one authoritative `handoff_ref`",
                    "the same idempotency key must not allocate a second queue slot",
                    "`gate_pending_ref` and `trace_ref` must be returned on every successful submission",
                ],
                "canonical_refs": [
                    "`handoff_ref`",
                    "`gate_pending_ref`",
                    "`trace_ref`",
                    "`canonical_payload_path`",
                ],
                "errors": [
                    "`missing_payload`",
                    "`invalid_state`",
                    "`duplicate_submission`",
                ],
                "idempotency": "`producer_ref + proposal_ref + payload_digest`",
                "preconditions": [
                    "`payload_ref` is already readable from the governed runtime carrier",
                    "`proposal_ref` resolves to the same submission intent as the payload",
                ],
            },
            {
                "command": "ll gate show-pending",
                "surface": "`ll gate show-pending --request <gate_show_pending.request.json> --response-out <gate_show_pending.response.json>` via `cli/commands/gate/command.py`",
                "request_schema": [
                    "`handoff_ref: string`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`handoff_ref`, `pending_state`, `assigned_gate_queue`, `gate_pending_ref`, `trace_ref`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                    "error fields=`code`, `message`, `retryable`",
                ],
                "field_semantics": [
                    "`assigned_gate_queue` is the queue currently responsible for the pending handoff, not a downstream execution queue.",
                    "`pending_state` must stay inside the frozen pending-state enum and must not leak approve/reject semantics.",
                ],
                "enum_domain": [
                    "`pending_state ∈ {gate_pending, human_review_pending, reentry_pending, retry_pending}`",
                ],
                "invariants": [
                    "the command returns the current pending-intake view for exactly one `handoff_ref`",
                    "successful lookups must echo the same `handoff_ref` and `gate_pending_ref` pair created during submission",
                ],
                "canonical_refs": [
                    "`handoff_ref`",
                    "`gate_pending_ref`",
                    "`trace_ref`",
                ],
                "errors": [
                    "`handoff_missing`",
                    "`pending_state_unavailable`",
                ],
                "idempotency": "`handoff_ref`",
                "preconditions": [
                    "`handoff_ref` has been submitted into the mainline runtime",
                ],
            },
        ]
    if axis == "formalization":
        return [
            {
                "command": "ll gate evaluate",
                "surface": "`ll gate evaluate --request <gate_evaluate.request.json> --response-out <gate_evaluate.response.json>` via `cli/commands/gate/command.py`",
                "request_schema": [
                    "`handoff_ref: string`",
                    "`proposal_ref: string`",
                    "`evidence_refs: string[]`",
                    "`brief_round: integer`",
                    "`priority_hint: enum<P0|P1|P2>?`",
                    "`merge_group_hint: string?`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`brief_record_ref`, `pending_human_decision_ref`, `decision_ref`, `decision`, `decision_target`, `decision_basis_refs`, `dispatch_target`, `trace_ref`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                ],
                "field_semantics": [
                    "`brief_record_ref` is the authoritative gate-brief record built from the handoff submission and evidence set.",
                    "`pending_human_decision_ref` identifies the uniquely claimed pending-human record consumed by the decision round.",
                    "`decision_ref` is the only authoritative gate result for downstream execution, delegation, or publication-trigger consumers.",
                    "`decision_basis_refs` must point back to the exact brief/evidence set used for this decision round.",
                ],
                "enum_domain": [
                    "`priority_hint ∈ {P0, P1, P2}`",
                    "`decision ∈ {approve, revise, retry, handoff, reject}`",
                ],
                "invariants": [
                    "one brief round yields at most one authoritative `brief_record_ref` and one active `pending_human_decision_ref`",
                    "one decision round yields at most one authoritative `decision_ref`",
                    "`decision_target` and `decision_basis_refs` must be present before the decision is accepted",
                ],
                "canonical_refs": [
                    "`brief_record_ref`",
                    "`pending_human_decision_ref`",
                    "`decision_ref`",
                    "`handoff_ref`",
                    "`trace_ref`",
                ],
                "errors": [
                    "`handoff_missing`",
                    "`invalid_state`",
                    "`decision_conflict`",
                    "`missing_basis_refs`",
                ],
                "idempotency": "`pending_human_decision_ref + decision_round`",
                "preconditions": [
                    "`handoff_ref` is already in gate-pending state",
                    "the pending human decision is active and uniquely claimed",
                ],
            },
            {
                "command": "ll gate dispatch",
                "surface": "`ll gate dispatch --request <gate_dispatch.request.json> --response-out <gate_dispatch.response.json>` via `cli/commands/gate/command.py`",
                "request_schema": [
                    "`decision_ref: string`",
                    "`dispatch_target: enum<execution_return|delegated_handler|formal_publication_trigger|reject_terminal>`",
                    "`decision_target: string`",
                    "`decision_basis_refs: string[]`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`dispatch_receipt_ref`, `dispatch_status`, `materialized_job_ref`, `materialized_handoff_ref`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                ],
                "field_semantics": [
                    "`dispatch_target` is derived from the authoritative decision object and is not an independently chosen runtime state.",
                    "`dispatch_receipt_ref` records the exact downstream handoff or execution return initiated by this command.",
                ],
                "enum_domain": [
                    "`dispatch_target ∈ {execution_return, delegated_handler, formal_publication_trigger, reject_terminal}`",
                ],
                "invariants": [
                    "dispatch must not succeed without an authoritative decision object",
                    "`formal_publication_trigger` may only be selected for `approve` or `handoff` decisions",
                ],
                "canonical_refs": [
                    "`decision_ref`",
                    "`dispatch_receipt_ref`",
                    "`materialized_job_ref`",
                    "`materialized_handoff_ref`",
                ],
                "errors": [
                    "`decision_not_dispatchable`",
                    "`dispatch_failed`",
                    "`unknown_dispatch_target`",
                ],
                "idempotency": "`decision_ref + dispatch_target`",
                "preconditions": [
                    "`decision_ref` resolves to one authoritative decision object",
                    "`decision_target` and `decision_basis_refs` are already present on the decision object",
                ],
            },
        ]
    if axis == "layering":
        return [
            {
                "command": "ll registry resolve-formal-ref",
                "surface": "`ll registry resolve-formal-ref --request <registry_resolve_formal_ref.request.json> --response-out <registry_resolve_formal_ref.response.json>` via `cli/commands/registry/command.py`",
                "request_schema": [
                    "`requested_ref: string`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`authoritative_ref`, `layer`, `lineage_ref`, `upstream_refs`, `downstream_refs`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                ],
                "field_semantics": [
                    "`authoritative_ref` must point to the formal-layer object when one exists.",
                    "`layer` is the authoritative object-layer classification consumed by admission logic.",
                ],
                "enum_domain": [
                    "`layer ∈ {candidate, formal, downstream}`",
                ],
                "invariants": [
                    "formal-layer resolution must not fall back to path guessing",
                ],
                "canonical_refs": [
                    "`authoritative_ref`",
                    "`lineage_ref`",
                ],
                "errors": [
                    "`unknown_ref`",
                    "`ambiguous_lineage`",
                ],
                "idempotency": "`requested_ref`",
                "preconditions": [
                    "`requested_ref` exists in registry or lineage storage",
                ],
            },
            {
                "command": "ll registry validate-admission",
                "surface": "`ll registry validate-admission --request <registry_validate_admission.request.json> --response-out <registry_validate_admission.response.json>` via `cli/commands/registry/command.py`",
                "request_schema": [
                    "`consumer_ref: string`",
                    "`requested_ref: string`",
                    "`lineage_ref: string?`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`allow`, `resolved_formal_ref`, `reason_code`, `evidence_ref`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                ],
                "field_semantics": [
                    "`allow=false` is still a successful admission verdict, not a transport error.",
                    "`resolved_formal_ref` must be present whenever `allow=true`.",
                ],
                "enum_domain": [
                    "`allow ∈ {true, false}`",
                ],
                "invariants": [
                    "consumers may only read formal-layer objects after an allow verdict",
                ],
                "canonical_refs": [
                    "`resolved_formal_ref`",
                    "`evidence_ref`",
                ],
                "errors": [
                    "`formal_ref_missing`",
                    "`lineage_missing`",
                    "`layer_violation`",
                ],
                "idempotency": "`consumer_ref + requested_ref`",
                "preconditions": [
                    "`requested_ref` resolves through lineage or registry",
                ],
            },
        ]
    if axis == "io_governance":
        return [
            {
                "command": "ll artifact commit",
                "surface": "`ll artifact commit --request <artifact_commit.request.json> --response-out <artifact_commit.response.json>` via `cli/commands/artifact/command.py`",
                "request_schema": [
                    "`logical_path: string`",
                    "`path_class: string`",
                    "`mode: enum<read|write>`",
                    "`payload_ref: string`",
                    "`overwrite: bool`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`managed_ref`, `registry_record_ref`, `write_receipt_ref`, `mode_decision`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                ],
                "field_semantics": [
                    "`mode_decision` is the normalized governed mode actually applied after policy evaluation.",
                    "`managed_ref` is the canonical downstream-consumable artifact reference.",
                ],
                "enum_domain": [
                    "`mode ∈ {read, write}`",
                ],
                "invariants": [
                    "a successful governed write must return both `managed_ref` and `write_receipt_ref`",
                ],
                "canonical_refs": [
                    "`managed_ref`",
                    "`registry_record_ref`",
                    "`write_receipt_ref`",
                ],
                "errors": [
                    "`policy_deny`",
                    "`registry_prerequisite_failed`",
                    "`write_failed`",
                ],
                "idempotency": "`logical_path + payload_digest + mode`",
                "preconditions": [
                    "request is normalized and payload is readable",
                ],
            },
            {
                "command": "ll artifact read",
                "surface": "`ll artifact read --request <artifact_read.request.json> --response-out <artifact_read.response.json>` via `cli/commands/artifact/command.py`",
                "request_schema": [
                    "`managed_ref: string`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`payload_ref`, `resolved_path`, `registry_record_ref`, `read_receipt_ref`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                ],
                "field_semantics": [
                    "`resolved_path` is the policy-approved physical path behind the managed ref.",
                ],
                "enum_domain": [],
                "invariants": [
                    "managed reads do not bypass registry-record resolution",
                ],
                "canonical_refs": [
                    "`managed_ref`",
                    "`registry_record_ref`",
                    "`read_receipt_ref`",
                ],
                "errors": [
                    "`managed_ref_missing`",
                    "`registry_record_missing`",
                    "`read_forbidden`",
                ],
                "idempotency": "`managed_ref`",
                "preconditions": [
                    "`managed_ref` is already registered",
                ],
            },
        ]
    if axis == "adoption_e2e":
        return [
            {
                "command": "ll rollout onboard-skill",
                "surface": "`ll rollout onboard-skill --request <rollout_onboard_skill.request.json> --response-out <rollout_onboard_skill.response.json>` via `cli/commands/rollout/command.py`",
                "request_schema": [
                    "`skill_ref: string`",
                    "`wave_id: string`",
                    "`scope: string`",
                    "`compat_mode: string`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`status`, `runtime_binding_ref`, `cutover_guard_ref`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                ],
                "field_semantics": [
                    "`compat_mode` freezes the transition mode used before full cutover.",
                ],
                "enum_domain": [],
                "invariants": [
                    "onboarding must keep a cutover guard ref for every accepted wave",
                ],
                "canonical_refs": [
                    "`runtime_binding_ref`",
                    "`cutover_guard_ref`",
                ],
                "errors": [
                    "`unknown_skill`",
                    "`scope_invalid`",
                    "`foundation_missing`",
                ],
                "idempotency": "`skill_ref + wave_id`",
                "preconditions": [
                    "foundation features are freeze-ready",
                ],
            },
            {
                "command": "ll audit submit-pilot-evidence",
                "surface": "`ll audit submit-pilot-evidence --request <audit_submit_pilot_evidence.request.json> --response-out <audit_submit_pilot_evidence.response.json>` via `cli/commands/audit/command.py`",
                "request_schema": [
                    "`pilot_chain_ref: string`",
                    "`producer_ref: string`",
                    "`consumer_ref: string`",
                    "`audit_ref: string`",
                    "`gate_ref: string`",
                ],
                "response_schema": [
                    "success envelope=`{ ok: true, command_ref, trace_ref, result }`",
                    "result fields=`evidence_status`, `cutover_recommendation`, `evidence_ref`",
                    "error envelope=`{ ok: false, command_ref, trace_ref, error }`",
                ],
                "field_semantics": [
                    "`cutover_recommendation` is a rollout recommendation, not a foundation design rewrite.",
                ],
                "enum_domain": [],
                "invariants": [
                    "pilot evidence must trace one complete producer -> consumer -> audit -> gate path",
                ],
                "canonical_refs": [
                    "`pilot_chain_ref`",
                    "`evidence_ref`",
                ],
                "errors": [
                    "`missing_chain_step`",
                    "`audit_not_traceable`",
                ],
                "idempotency": "`pilot_chain_ref`",
                "preconditions": [
                    "pilot chain has executed at least once",
                ],
            },
        ]
    return []


def api_request_response_contracts(feature: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for spec in api_command_specs(feature):
        rows.append(
            f"`{spec['command']}`: request schema={', '.join(spec['request_schema'])}; response schema={', '.join(spec['response_schema'])}."
        )
    return rows


def api_error_and_idempotency(feature: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for spec in api_command_specs(feature):
        rows.append(
            f"`{spec['command']}`: errors={', '.join(spec['errors'])}; idempotent key={spec['idempotency']}; precondition={'; '.join(spec['preconditions'])}."
        )
    return rows


def api_compatibility_rules(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    rules = [
        "新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。",
        "command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。",
    ]
    if axis == "collaboration":
        rules.append("提交与 pending 可见性命令不得偷带决策语义；`approve / revise / retry / handoff / reject` 只能留在 gate decision FEAT。")
    if axis == "formalization":
        rules.append("`ll gate evaluate` 与 `ll gate dispatch` 的 decision vocabulary / dispatch_target 必须共享同一份枚举与 target 语义，不允许把 human decision actions 漂成 runtime states。")
    if axis == "layering":
        rules.append("resolve/admission 命令必须始终返回 authoritative formal refs，不允许退化为路径猜测结果。")
    if axis == "io_governance":
        rules.append("governed IO 命令不得 silent fallback 到自由读写；兼容模式也必须显式返回 warning/code。")
    if axis == "adoption_e2e":
        rules.append("onboarding/cutover 命令必须保留 compat_mode 开关，并把 fallback 结果显式记录到 receipt。")
    return rules


def traceability_rows(feature: dict[str, Any], package: Any, refs: dict[str, str]) -> list[dict[str, Any]]:
    source_refs = unique_strings(
        [f"product.epic-to-feat::{package.run_id}", refs["feat_ref"], refs["epic_ref"], refs["src_ref"]]
        + ensure_list(feature.get("source_refs"))
    )
    return [
        {
            "design_section": "Need Assessment",
            "feat_fields": ["scope", "dependencies", "acceptance_checks"],
            "source_refs": source_refs[:4],
        },
        {
            "design_section": "TECH Design",
            "feat_fields": ["goal", "scope", "constraints"],
            "source_refs": source_refs[:4],
        },
        {
            "design_section": "Cross-Artifact Consistency",
            "feat_fields": ["dependencies", "outputs", "acceptance_checks"],
            "source_refs": source_refs[:4],
        },
    ]


def consistency_check(feature: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    axis = feature_axis(feature)
    checks: list[dict[str, Any]] = []
    issues: list[str] = []
    minor_open_items: list[str] = []

    structural_checks: list[bool] = []
    semantic_checks: list[bool] = []

    def add_check(category: str, name: str, passed: bool, detail: str, issue: str | None = None) -> None:
        checks.append(
            {
                "category": category,
                "name": name,
                "passed": passed,
                "detail": detail,
            }
        )
        if category == "structural":
            structural_checks.append(passed)
        else:
            semantic_checks.append(passed)
        if not passed and issue:
            issues.append(issue)

    add_check(
        "structural",
        "TECH mandatory",
        True,
        "TECH is always emitted for the selected FEAT.",
    )

    traceability_ok = bool(ensure_list(feature.get("source_refs")))
    add_check(
        "structural",
        "Traceability present",
        traceability_ok,
        "Selected FEAT carries authoritative source refs for downstream design derivation.",
        "Selected FEAT did not carry enough source refs to support traceability.",
    )

    if assessment["arch_required"]:
        arch_ok = len(architecture_topics(feature)) >= 2
        add_check(
            "structural",
            "ARCH coverage",
            arch_ok,
            "ARCH is required and carries system-boundary placement topics.",
            "ARCH was required but architecture topics could not be resolved clearly.",
        )
    else:
        add_check(
            "structural",
            "ARCH omission justified",
            True,
            "ARCH is omitted because the FEAT does not require boundary or topology redesign.",
        )

    if assessment["api_required"]:
        api_ok = len(api_command_specs(feature)) >= 1
        add_check(
            "structural",
            "API coverage",
            api_ok,
            "API is required and carries at least one command-level contract surface.",
            "API was required but no concrete command contract specs were derived.",
        )
    else:
        add_check(
            "structural",
            "API omission justified",
            True,
            "API is omitted because no explicit cross-boundary contract surface was detected.",
        )

    arch_tech_separation = True
    if assessment["arch_required"]:
        arch_tech_separation = architecture_diagram(feature) != tech_runtime_view(feature)
    add_check(
        "semantic",
        "ARCH / TECH separation",
        arch_tech_separation,
        "ARCH keeps boundary placement/topology while TECH keeps implementation carriers, contracts, and concrete execution design.",
        "ARCH and TECH still appear to share the same runtime topology instead of separating boundary placement from implementation design.",
    )

    api_contract_strength = True
    if assessment["api_required"]:
        specs = api_command_specs(feature)
        api_contract_strength = bool(specs) and all(
            spec.get("request_schema")
            and spec.get("response_schema")
            and spec.get("field_semantics")
            and spec.get("enum_domain") is not None
            and spec.get("invariants")
            and spec.get("canonical_refs")
            for spec in specs
        )
    add_check(
        "semantic",
        "API contract completeness",
        api_contract_strength,
        "API contracts carry schema, field semantics, enum/domain, invariants, and canonical refs that can seed validator or contract-test work.",
        "API is still too thin; command specs are missing schema, invariants, or canonical ref semantics.",
    )

    reentry_boundary_ok = True
    if axis == "collaboration":
        reentry_scope = collaboration_reentry_scope(feature)
        if reentry_scope == "ambiguous":
            reentry_boundary_ok = False
        elif reentry_scope == "routing":
            reentry_boundary_ok = (
                any("decision-driven runtime re-entry routing" in topic for topic in architecture_topics(feature))
                and any("Formal materialization" in item for item in implementation_architecture(feature))
            )
    add_check(
        "semantic",
        "Collaboration re-entry boundary",
        reentry_boundary_ok,
        "When collaboration FEATs mention revise/retry, TECH keeps decision-driven runtime routing in scope while leaving gate decision issuance and formal publication semantics out of scope.",
        "The FEAT carries ambiguous or unresolved revise/retry re-entry ownership, so the generated design cannot claim semantic consistency across runtime routing and downstream gate/publication boundaries.",
    )

    if assessment["api_required"]:
        minor_open_items.append(
            "Freeze a command-level error mapping table for `code -> retryable -> idempotent_replay` in a later API revision if validator-grade contract testing needs a closed semantics table."
        )
    if assessment["arch_required"] or assessment["api_required"]:
        minor_open_items.append(
            "Optional ARCH/API summaries are still embedded in the bundle for one-shot review; a later revision may collapse them to pure references to reduce duplication risk."
        )

    structural_passed = all(structural_checks) if structural_checks else True
    semantic_passed = all(semantic_checks) if semantic_checks else True
    return {
        "passed": structural_passed and semantic_passed,
        "structural_passed": structural_passed,
        "semantic_passed": semantic_passed,
        "checks": checks,
        "issues": issues,
        "minor_open_items": minor_open_items,
    }


def feature_axis(feature: dict[str, Any]) -> str:
    explicit = explicit_axis(feature)
    if explicit:
        return explicit
    title = str(feature.get("title") or "").strip().lower()
    core_text = feature_core_text(feature)
    full_text = feature_text(feature)

    # Prefer explicit FEAT title axes over secondary keywords that may appear
    # in boundary/dependency text from neighboring FEATs.
    if any(token in title for token in ["对象分层", "准入"]):
        return "layering"
    if any(token in title for token in ["正式交接", "物化"]):
        return "formalization"
    if any(token in title for token in ["主链协作闭环", "协作闭环"]):
        return "collaboration"
    if any(token in title for token in ["文件 io", "路径治理"]):
        return "io_governance"
    if any(token in title for token in ["技能接入", "跨 skill", "cross skill", "cross-skill"]):
        return "adoption_e2e"

    if any(token in core_text for token in ["candidate package", "formal object", "formal refs", "lineage", "candidate layer", "formal layer", "authoritative layer", "准入", "对象分层"]):
        return "layering"
    if any(token in core_text for token in ["materialization", "external gate", "approve", "reject", "formalization", "正式交接", "物化"]):
        return "formalization"
    if any(token in core_text for token in ["execution loop", "gate loop", "human loop", "双会话双队列", "queue", "协作闭环", "re-entry", "reentry"]):
        return "collaboration"
    if any(token in core_text for token in ["path", "registry", "gateway", "artifact io", "路径", "落盘", "写入模式"]):
        return "io_governance"
    if any(token in core_text for token in ["onboarding", "migration", "cutover", "pilot", "wave", "rollout"]):
        return "adoption_e2e"
    if any(token in full_text for token in ["candidate package", "formal object", "formal refs", "lineage"]):
        return "layering"
    return "collaboration"


def collaboration_reentry_scope(feature: dict[str, Any]) -> str:
    text = feature_text(feature)
    positive = any(token in text for token in ["回流条件", "re-entry", "reentry", "revise", "retry"])
    negative = any(
        token in text
        for token in [
            "re-entry semantics outside this feat",
            "keeping approval and re-entry semantics outside this feat",
            "回流语义留在",
            "回流语义不在本 feat",
        ]
    )
    structured_product_shape = isinstance(feature.get("identity_and_scenario"), dict) and isinstance(
        feature.get("collaboration_and_timeline"), dict
    )
    pending_visibility_frozen = any(
        token in text
        for token in [
            "gate pending",
            "pending-intake",
            "pending visibility",
            "authoritative handoff",
            "待审批状态",
            "交接正式送入 gate",
        ]
    )
    if positive and negative:
        if structured_product_shape and pending_visibility_frozen:
            return "routing"
        return "ambiguous"
    if negative:
        return "downstream"
    if positive:
        return "routing"
    return "none"


def implementation_architecture(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "Business skill 只产出 candidate package / proposal / evidence，由 handoff runtime 承接进入 external gate。",
            "External gate 先把 handoff 压缩成 `gate-brief-record` 与 `gate-pending-human-decision`，再由 reviewer 给出 approve / revise / retry / handoff / reject 决策。",
            "本 FEAT 只负责 decision issuance、trace persistence 与 downstream dispatch trigger；formal materialization / publish 由相邻 FEAT 消费 decision object 后继续完成。",
        ]
    if axis == "layering":
        return [
            "Business skill、gate、consumer 分别围绕 candidate layer、formal layer、downstream consumption layer 协作，不共享隐式旁路对象。",
            "Admission checker 只根据 formal refs 与 lineage 放行 downstream 读取，不根据路径邻近关系或目录猜测放行。",
            "Layering policy 与 IO/path policy 分离：本 FEAT 只定义对象资格和引用方向，底层落盘仍消费外部治理基础。",
        ]
    if axis == "io_governance":
        return [
            "Governed skill、handoff runtime、formal materialization 都通过 ADR-005 提供的 Gateway / Path Policy / Registry 接入受治理 IO。",
            "Mainline handoff 与 formal writes 共享同一套 path / mode 约束，不允许局部目录策略绕过受治理写入。",
            "全局文件治理、仓库级目录重构与非 governed skill 自由写入不进入本实现范围。",
        ]
    if axis == "adoption_e2e":
        return [
            "Foundation 能力先稳定，再把 governed skill 按 onboarding matrix 与 migration wave 接入主链。",
            "Pilot chain 必须覆盖 producer -> gate -> formal object -> consumer -> audit 的真实闭环，而不是组件内局部验证。",
            "Cutover controller 只负责切换与回退边界，不重写 foundation FEAT 或 ADR-005 的实现模块。",
        ]
    return [
        "Execution loop、gate loop、human review 通过文件化 handoff runtime 协作；authoritative handoff submission、pending visibility、decision-return intake 都以结构化对象驱动。",
        "Runtime 在收到 gate decision object 后，只负责可见性回写与 revise/retry re-entry routing；decision vocabulary 仍由 gate decision FEAT authoritative freeze。",
        "Formal publication、approve/handoff 的最终发布语义不在本 FEAT 内实现，本 FEAT 只保留对相邻 publication FEAT 的 authoritative boundary handoff。",
    ]


def implementation_modules(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    common = [
        "Handoff runtime adapter：负责把受治理对象写入/读取主链 runtime，并维持 traceability。",
        "Decision boundary adapter：负责把上游 FEAT 约束映射成 runtime 可执行边界，不把实现责任散落到业务 skill。",
    ]
    if axis == "formalization":
        return common + [
            "Gate brief builder：负责把 handoff submission 压缩成 `gate-brief-record` 与 `gate-pending-human-decision`。",
            "Gate decision processor：解析 approve / revise / retry / handoff / reject，并产出带 `decision_target` 与 `decision_basis_refs` 的唯一 authoritative decision object。",
            "Dispatch router：负责把 decision object 回交给 execution、delegated handler 或 formal publication trigger，而不是直接执行 formal publish。",
        ]
    if axis == "layering":
        return common + [
            "Object lineage resolver：为 candidate/formal/downstream object 建立 lineage 与 authoritative refs。",
            "Admission checker：在 consumer 读取前验证 formal refs、lineage 与 layer eligibility。",
        ]
    if axis == "io_governance":
        return common + [
            "Gateway integration adapter：把 handoff/materialization 写入重定向到 ADR-005 Gateway。",
            "Path governance guard：在写入前校验 path / mode / overwrite 规则，并拒绝自由写入 fallback。",
        ]
    if axis == "adoption_e2e":
        return common + [
            "Onboarding registry：记录 governed skill 接入矩阵、scope 与 migration wave。",
            "Pilot orchestration verifier：收集 producer -> consumer -> audit -> gate 的真实闭环证据并支撑 cutover/fallback。",
        ]
    return common + [
        "Submission coordinator：定义 candidate/proposal/evidence 进入 authoritative handoff 的入口、receipt 与 pending visibility。",
        "Decision return adapter：消费 gate decision object，并把 revise/retry 映射成 runtime re-entry directive，而不重写 decision semantics。",
    ]


def state_model(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "`candidate_prepared` -> `submitted_to_gate` -> `brief_prepared` -> `pending_human_decision` -> `decision_issued` -> `execution_returned|delegated|publication_triggered|rejected`",
            "`decision_issued(revise)` -> `returned_for_revision` -> `candidate_prepared`",
            "`decision_issued(retry)` -> `retry_pending` -> `submitted_to_gate`",
        ]
    if axis == "layering":
        return [
            "`candidate_only`：仅允许 gate/runtime 消费，不允许 downstream 直接读取。",
            "`formal_authorized`：已具备 formal refs 与 lineage，可成为正式输入。",
            "`consumer_admitted`：consumer 通过 admission checker 后可读取 formal layer。",
        ]
    if axis == "io_governance":
        return [
            "`write_requested` -> `path_validated` -> `gateway_committed` -> `registry_recorded` -> `consumable_ref_published`",
            "`path_validated(fail)` -> `write_rejected`，不得 silent fallback 到自由写入。",
        ]
    if axis == "adoption_e2e":
        return [
            "`skill_registered` -> `pilot_enabled` -> `cutover_guarded` -> `e2e_verified` -> `wave_accepted`",
            "`cutover_guarded(fail)` -> `fallback_triggered` -> `pilot_enabled`",
        ]
    return [
        "`handoff_prepared` -> `handoff_submitted` -> `gate_pending_visible` -> `decision_returned`",
        "`decision_returned(revise|retry)` -> `runtime_reentry_directive_written` -> `handoff_prepared`",
        "`decision_returned(approve|handoff|reject)` -> `boundary_handoff_recorded`，由 formalization / downstream runtime 消费后续推进",
    ]


def architecture_diagram(feature: dict[str, Any]) -> str:
    axis = feature_axis(feature)
    if axis == "formalization":
        return "\n".join([
            "```text",
            "[Business Skill]",
            "      |",
            "      v",
            "[Candidate Package] --> [Handoff Runtime] --> [External Gate] --> [Gate Brief Record]",
            "                                                              |",
            "                                                              +--> [Pending Human Decision] --> [Decision Object]",
            "                                                                                                  |",
            "                                                                                                  +--> revise/retry/reject --> [Execution / Runtime Return]",
            "                                                                                                  |",
            "                                                                                                  +--> approve/handoff --> [Dispatch Trigger]",
            "```",
        ])
    if axis == "layering":
        return "\n".join([
            "```text",
            "[Business Skill] --> [Candidate Layer] --> [Gate / Runtime] --> [Formal Layer] --> [Admission Checker] --> [Consumer Read]",
            "                                |",
            "                                +--> candidate-only objects",
            "                                      x blocked from direct consumer read",
            "```",
        ])
    if axis == "io_governance":
        return "\n".join([
            "```text",
            "[Governed Skill / Runtime]",
            "          |",
            "          v",
            "[Gateway Integration Adapter] --> [Path Policy] --> [Artifact IO Gateway] --> [Artifact Registry] --> [Managed Artifact Ref] --> [Gate / Consumer]",
            "```",
        ])
    if axis == "adoption_e2e":
        return "\n".join([
            "```text",
            "[Producer Skill] --> [Mainline Runtime] --> [Gate / Formalization] --> [Consumer Skill] --> [Audit Evidence] --> [Cutover Decision]",
            "                                                                                                              |",
            "                                                                                                              +--> fallback --> [Producer Skill]",
            "```",
        ])
    return "\n".join([
        "```text",
        "[Execution Loop] --> [Handoff Runtime] --> [Gate Loop] --> [Human Review]",
        "       ^                    |                     |",
        "       |                    +--> pending visibility --> [Producer / Upstream]",
        "       |                                          |",
        "       +---- revise/retry routing <---------------+",
        "                            decision object -----> [Handoff Runtime]",
        "```",
    ])


def tech_runtime_view(feature: dict[str, Any]) -> str:
    axis = feature_axis(feature)
    if axis == "formalization":
        return "\n".join([
            "```text",
            "[cli/commands/gate/command.py]",
            "              |",
            "              +--> [cli/lib/protocol.py]",
            "              |",
            "              +--> [cli/lib/registry_store.py]",
            "              |",
            "              +--> [Gate Brief Record / Pending Human Decision / Gate Decision]",
            "```",
        ])
    if axis == "layering":
        return "\n".join([
            "```text",
            "[cli/commands/registry/command.py]",
            "              |",
            "              v",
            "[cli/lib/lineage.py] --> [cli/lib/admission.py] --> [Admission Verdict]",
            "              |",
            "              +--> [cli/lib/protocol.py]",
            "```",
        ])
    if axis == "io_governance":
        return "\n".join([
            "```text",
            "[cli/commands/artifact/command.py]",
            "              |",
            "              v",
            "[cli/lib/managed_gateway.py] --> [cli/lib/policy.py]",
            "              |",
            "              +--> [cli/lib/fs.py] --> [cli/lib/registry_store.py]",
            "```",
        ])
    if axis == "adoption_e2e":
        return "\n".join([
            "```text",
            "[cli/commands/rollout/command.py]",
            "              |",
            "              v",
            "[cli/lib/rollout_state.py] --> [cli/lib/pilot_chain.py] --> [Pilot / Cutover Evidence]",
            "              |",
            "              +--> [cli/commands/audit/command.py]",
            "```",
        ])
    return "\n".join([
        "```text",
        "[cli/commands/gate/command.py]",
        "              |",
        "              v",
        "[cli/lib/mainline_runtime.py] --> [Gate Pending Receipt / Visibility]",
        "              |",
        "              +--> [cli/lib/protocol.py]",
        "              |",
        "              +--> [cli/lib/reentry.py] (revise/retry routing only)",
        "```",
    ])


def flow_diagram(feature: dict[str, Any]) -> str:
    axis = feature_axis(feature)
    if axis == "formalization":
        return "\n".join([
            "```text",
            "Business Skill -> Runtime         : submit candidate + proposal",
            "Runtime        -> External Gate   : enqueue handoff for decision",
            "External Gate  -> Runtime         : build gate brief + pending human decision",
            "Reviewer       -> External Gate   : approve / revise / retry / handoff / reject",
            "External Gate  -> Runtime         : persist decision object with target/basis",
            "Runtime        -> Execution Loop  : return structured decision on revise/retry/reject",
            "Runtime        -> Delegate/Publish Trigger : dispatch handoff or approve trigger",
            "```",
        ])
    if axis == "layering":
        return "\n".join([
            "```text",
            "Business Skill   -> Gate / Runtime    : write candidate package",
            "Gate / Runtime   -> Lineage Resolver  : resolve formal refs and lineage",
            "Lineage Resolver -> Gate / Runtime    : return formal object metadata",
            "Consumer         -> Admission Checker : request read",
            "Admission Checker-> Consumer          : allow only with formal refs",
            "```",
        ])
    if axis == "io_governance":
        return "\n".join([
            "```text",
            "Runtime / Skill     -> Gateway Adapter : request governed write",
            "Gateway Adapter     -> Path Policy     : validate path / mode",
            "Path Policy         -> Gateway Adapter : allow or reject",
            "Gateway Adapter     -> IO Gateway      : commit artifact when allowed",
            "IO Gateway          -> Registry        : register managed ref",
            "Registry            -> Runtime / Skill : publish consumable ref",
            "Gateway Adapter     -> Runtime / Skill : return governed rejection when blocked",
            "```",
        ])
    if axis == "adoption_e2e":
        return "\n".join([
            "```text",
            "Producer -> Runtime : emit governed object",
            "Runtime  -> Gate    : route through mainline gate",
            "Gate     -> Consumer: publish formal refs",
            "Consumer -> Audit   : produce audit evidence",
            "Audit    -> Gate    : confirm pilot readiness or fallback",
            "```",
        ])
    return "\n".join([
        "```text",
        "Execution Loop -> Runtime      : submit candidate / proposal / evidence",
        "Runtime        -> Gate Loop    : persist authoritative handoff and publish pending visibility",
        "Gate Loop      -> Human Review : escalate when required",
        "Human Review   -> Gate Loop    : return decision object",
        "Gate Loop      -> Runtime      : return decision object",
        "Runtime        -> Execution Loop: write revise/retry re-entry directive when applicable",
        "Runtime        -> Downstream   : expose boundary handoff record for approve/handoff/reject outcomes",
        "```",
    ])


def implementation_strategy(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "先固化 candidate -> brief -> pending human -> decision 的对象链与 decision vocabulary。",
            "实现 revise / retry / handoff 回流时，必须先打通 structured decision 回写，并确保 `decision_target` 与 `decision_basis_refs` 完整。",
            "最后把 approve decision 只作为 dispatch trigger 暴露给相邻 formal publication FEAT，不在本 FEAT 内直接 publish。",
        ]
    if axis == "layering":
        return [
            "先定义 candidate/formal/downstream 三层对象与 authoritative refs，再补 admission checker。",
            "把 consumer read path 全部切到 formal refs 校验后，再清理路径猜测或旁路读取。",
            "最后用至少一条真实 consumer consumption 验证 layer boundary 是否成立。",
        ]
    if axis == "io_governance":
        return [
            "先接通 runtime 到 ADR-005 Gateway / Path Policy / Registry 的调用路径，再禁止自由写入 fallback。",
            "把 mainline handoff 与 formal publication 相关写入都切到同一条受治理 IO 链路，避免双轨写盘。",
            "最后用真实 handoff write + formal write 两条样例验证 path / mode / registry 行为。",
        ]
    if axis == "adoption_e2e":
        return [
            "先冻结 onboarding matrix、pilot chain 和 cutover guard，再按 wave 接入 governed skill。",
            "先跑最小真实 producer -> consumer -> audit -> gate pilot，稳定后再扩大接入波次。",
            "每个 wave 都必须保留 fallback 条件与 rollback evidence，不能一次性全量切换。",
        ]
    return [
        "先冻结 authoritative handoff、pending visibility 和 decision return intake，再接入 human review escalation。",
        "把 revise / retry 收敛为 runtime-owned re-entry routing，不允许 business skill 或 gate worker 私下拼接回流路径。",
        "最后用至少一条真实 submit -> pending -> decision-return -> re-entry pilot 验证协作闭环成立，同时证明 gate decision issuance / formal publication 仍在本 FEAT 外。",
    ]


def implementation_unit_mapping(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "`cli/lib/protocol.py` (`extend`): 定义 `GateBriefRecord`、`GatePendingHumanDecision`、`GateDecision` 结构。",
            "`cli/lib/registry_store.py` (`extend`): 写入 brief/decision trace、`decision_target`、`decision_basis_refs` 与 dispatch receipt。",
            "`cli/commands/gate/command.py` (`extend`): 接入 `evaluate` / `dispatch` 语义，生成 brief record、decision object 与回交流水。",
        ]
    if axis == "layering":
        return [
            "`cli/lib/protocol.py` (`extend`): 定义 `CandidateRef`、`FormalRef`、`AdmissionRequest`、`AdmissionVerdict` 结构。",
            "`cli/lib/lineage.py` (`new`): 维护 candidate/formal/downstream object 的 lineage 与 authoritative refs。",
            "`cli/lib/admission.py` (`new`): 基于 formal refs、lineage 与 layer eligibility 做准入判断。",
            "`cli/lib/registry_store.py` (`extend`): 提供 lineage 查询和 formal ref 解析能力。",
            "`cli/commands/registry/command.py` (`extend`): 暴露 resolve-formal-ref / validate-admission 操作，依赖 `cli/lib/lineage.py` 和 `cli/lib/admission.py`。",
        ]
    if axis == "io_governance":
        return [
            "`cli/lib/policy.py` (`extend`): 定义 path / mode / overwrite 的 preflight verdict 规则。",
            "`cli/lib/fs.py` (`extend`): 实现 governed read/write 的底层文件访问与 receipt 落盘。",
            "`cli/lib/managed_gateway.py` (`new`): 编排 preflight、gateway commit、registry bind、receipt build。",
            "`cli/lib/registry_store.py` (`extend`): 记录 managed artifact ref、registry prerequisite 和 publish 状态。",
            "`cli/commands/artifact/command.py` (`extend`): 暴露 governed artifact commit / read 入口，依赖 `cli/lib/managed_gateway.py`。",
        ]
    if axis == "adoption_e2e":
        return [
            "`cli/lib/protocol.py` (`extend`): 定义 `OnboardingMatrix`、`CutoverDirective`、`PilotEvidenceRef` 结构。",
            "`cli/lib/rollout_state.py` (`new`): 保存 onboarding wave、cutover state 和 fallback marker。",
            "`cli/lib/pilot_chain.py` (`new`): 校验 producer -> consumer -> audit -> gate 的真实闭环证据。",
            "`cli/commands/rollout/command.py` (`extend`): 提供 onboarding wave、cutover、fallback 操作，依赖 `cli/lib/rollout_state.py`。",
            "`cli/commands/audit/command.py` (`extend`): 消费 pilot evidence 并把 findings 回交给 cutover decision。",
        ]
    return [
        "`cli/lib/protocol.py` (`extend`): 定义 `HandoffEnvelope`、`PendingVisibilityRecord`、`DecisionReturnEnvelope`、`ReentryDirective` 结构。",
        "`cli/lib/mainline_runtime.py` (`new`): 管理 authoritative submission、pending visibility、decision-return intake 与 boundary handoff record。",
        "`cli/lib/reentry.py` (`new`): 只处理 revise / retry 的 runtime routing、directive 写回与 replay guard，不拥有 decision semantics。",
        "`cli/commands/gate/command.py` (`extend`): 接入 submit-handoff / show-pending 路径，并把 returned decision 交给 `cli/lib/mainline_runtime.py` 消费。",
        "`cli/commands/audit/command.py` (`extend`): 作为 human review escalation 的旁路消费方，回写 structured review context 而非 formalization result。",
    ]


def interface_contracts(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "`GateBriefRecord`: input=`handoff_ref`, `proposal_ref`, `evidence_refs`; output=`brief_record_ref`, `pending_human_decision_ref`, `priority`, `merge_group`, `human_projection`; errors=`invalid_state`, `brief_build_failed`; idempotent=`yes by handoff_ref + brief_round`; precondition=`handoff 已进入 gate pending`。",
            "`GateDecision`: input=`brief_record_ref`, `pending_human_decision_ref`, `human_action`, `decision_target`, `decision_basis_refs`; output=`decision_ref`, `decision`, `decision_reason`, `decision_target`, `decision_basis_refs`, `dispatch_target`; errors=`invalid_state`, `unknown_target`, `missing_basis_refs`, `policy_reject`; idempotent=`yes by pending_human_decision_ref + decision_round`; precondition=`pending human decision is active and uniquely claimed`。",
        ]
    if axis == "layering":
        return [
            "`AdmissionRequest`: input=`consumer_ref`, `requested_ref`, `lineage_ref?`; output=`allow`, `resolved_formal_ref`, `layer`, `reason_code`; errors=`formal_ref_missing`, `lineage_missing`, `layer_violation`; idempotent=`yes by consumer_ref + requested_ref`; precondition=`requested object 已可解析到 registry / lineage`。",
            "`LineageResolveRequest`: input=`candidate_ref | formal_ref`; output=`authoritative_ref`, `layer`, `upstream_refs`, `downstream_refs`; errors=`unknown_ref`, `ambiguous_lineage`; idempotent=`yes`; precondition=`ref 存在于 registry/lineage store`。",
        ]
    if axis == "io_governance":
        return [
            "`GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。",
            "`PolicyVerdict`: input=`logical_path`, `path_class`, `mode`, `caller_ref`; output=`allow`, `reason_code`, `resolved_path`, `mode_decision`; errors=`invalid_path_class`, `mode_forbidden`; idempotent=`yes`; precondition=`request normalized`。",
        ]
    if axis == "adoption_e2e":
        return [
            "`OnboardingDirective`: input=`skill_ref`, `wave_id`, `scope`, `compat_mode`; output=`status`, `runtime_binding_ref`, `cutover_guard_ref`; errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent=`yes by skill_ref + wave_id`; precondition=`foundation features freeze-ready`。",
            "`PilotEvidenceSubmission`: input=`pilot_chain_ref`, `producer_ref`, `consumer_ref`, `audit_ref`, `gate_ref`; output=`evidence_status`, `cutover_recommendation`; errors=`missing_chain_step`, `audit_not_traceable`; idempotent=`yes by pilot_chain_ref`; precondition=`pilot chain 已完整执行一次`。",
        ]
    return [
        "`HandoffEnvelope`: input=`producer_ref`, `proposal_ref`, `payload_ref`, `pending_state`, `trace_context_ref`; output=`handoff_ref`, `gate_pending_ref`, `trace_ref`, `canonical_payload_path`; errors=`invalid_state`, `missing_payload`, `duplicate_submission`; idempotent=`yes by producer_ref + proposal_ref + payload_digest`; precondition=`payload 已写入 runtime 可读位置`。",
        "`DecisionReturnEnvelope` (consumed): input=`handoff_ref`, `decision_ref`, `decision`, `routing_hint`, `trace_ref`; output=`boundary_handoff_record | reentry_directive`; errors=`decision_conflict`, `handoff_missing`; idempotent=`yes by handoff_ref + decision_ref`; precondition=`decision object 已由 external gate authoritative emit`。",
    ]


def main_sequence(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "1. normalize handoff and proposal refs",
            "2. validate gate-pending state and build `gate-brief-record`",
            "3. persist `gate-pending-human-decision` and human-facing projection",
            "4. capture human decision action and persist authoritative decision object",
            "5. validate `decision_target` and `decision_basis_refs`",
            "6. dispatch structured result to execution, delegated handler, or formal publication trigger",
        ]
    if axis == "layering":
        return [
            "1. normalize requested ref and consumer identity",
            "2. resolve lineage and authoritative formal ref",
            "3. verify requested layer and consumer eligibility",
            "4. emit admission verdict and resolved formal ref",
            "5. record read evidence for audit / gate traceability",
        ]
    if axis == "io_governance":
        return [
            "1. normalize request",
            "2. preflight policy check",
            "3. registry prerequisite check",
            "4. execute governed handler",
            "5. build receipt and managed ref",
            "6. persist staging / evidence / registry record",
            "7. return result",
        ]
    if axis == "adoption_e2e":
        return [
            "1. resolve onboarding directive and targeted wave",
            "2. verify foundation readiness and compat mode",
            "3. bind selected skill to mainline runtime / gate hooks",
            "4. run pilot chain and capture producer -> consumer -> audit -> gate evidence",
            "5. evaluate cutover guard and emit fallback recommendation when needed",
            "6. persist wave status and rollout evidence",
        ]
    return [
        "1. normalize candidate/proposal/evidence submission and producer state",
        "2. persist authoritative handoff object and emit gate-pending visibility",
        "3. route proposal into gate loop and escalate to human review when required",
        "4. consume structured decision object when it returns to runtime",
        "5. if decision in {revise, retry}, write re-entry directive and replay guard",
        "6. if decision in {approve, handoff, reject}, persist boundary handoff record without materializing formal output here",
    ]


def exception_compensation(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "brief persisted 但 pending human decision 未建立：保留 `brief_record_ref`，阻止 decision issuance，并记录 `pending_build_failed`。",
            "decision capture 缺少 `decision_target` 或 `decision_basis_refs`：拒绝落 decision object，保留 active pending human decision，要求补充依据后重试。",
            "dispatch fail：保留 authoritative decision object，不伪造下游 publish 完成态，并记录 `dispatch_pending` 供后续 repair。",
        ]
    if axis == "layering":
        return [
            "lineage resolve fail：直接 deny admission，不允许退化为路径猜测。",
            "formal ref 存在但 layer mismatch：返回 `layer_violation`，consumer 不得继续读 candidate layer。",
            "admission evidence persist fail：允许 verdict 返回，但把 read 标记为 `audit_pending`，后续 gate 需感知缺失 evidence。",
        ]
    if axis == "io_governance":
        return [
            "policy pass 但 registry prerequisite fail：拒绝写入，返回 `registry_prerequisite_failed`，不得绕过 registry 直接落盘。",
            "write success 但 receipt build fail：保留 staged artifact，标记 `receipt_pending`，禁止发布 managed ref 给 consumer。",
            "staging retention fail：允许主写入成功，但必须追加 degraded evidence，并要求后续 cleanup job 补偿。",
        ]
    if axis == "adoption_e2e":
        return [
            "pilot chain 中任一步 evidence 缺失：cutover 直接 fail closed，维持 compat mode。",
            "cutover success 但 audit handoff fail：允许 partial success，但 wave 状态标记 `audit_pending`，禁止扩大 rollout。",
            "fallback trigger fail：保留 current wave 冻结，要求人工介入，不允许自动继续下一波次。",
        ]
    return [
        "authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。",
        "decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。",
        "boundary handoff record persist fail：不得偷跑 formalization；保持 decision visible but `downstream_handoff_pending`，等待 runtime repair。",
    ]


def integration_points(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "调用方：现有 governed skill 通过 handoff runtime 提交 candidate package，由 `cli/commands/gate/command.py` 负责 evaluate / dispatch。",
            "挂接点：file-handoff 发生在 candidate package 写入 runtime 之后；本 FEAT 只把 approve 决策交接为 formal publication trigger，不直接 materialize formal object。",
            "旧系统兼容：business skill 保持只产出 candidate/proposal/evidence，不新增直接 formal write 路径。",
        ]
    if axis == "layering":
        return [
            "调用方：downstream consumer 在正式读取前调用 admission checker；registry 负责提供 formal refs 与 lineage。",
            "挂接点：file-handoff 完成后先 resolve formal refs，再决定 consumer admission。",
            "旧系统兼容：现有路径猜测读取必须逐步迁移到 formal-ref based access，兼容模式只允许只读告警，不允许默认放行。",
        ]
    if axis == "io_governance":
        return [
            "调用方：runtime、formal materialization、governed skill 的正式写入都通过 `cli/commands/artifact/command.py` 进入 Gateway。",
            "挂接点：file-handoff 写入发生在 policy preflight 之后、registry bind 之前；external gate 读取 formal refs 时只消费 managed artifact ref。",
            "旧系统兼容：compat mode 仅允许受控 read fallback；正式 write 不允许 bypass Gateway。",
        ]
    if axis == "adoption_e2e":
        return [
            "调用方：现有 governed skill 的 onboarding/cutover 由 `cli/commands/rollout/command.py` 发起，audit findings 由 `cli/commands/audit/command.py` 消费。",
            "挂接点：compat mode 在 skill 接入 wave 前打开；file-handoff 和 gate/repair 路径必须进入 pilot evidence 链。",
            "旧系统兼容：先接入选定 pilot skill，再按 wave 扩大；未在 onboarding matrix 内的旧 skill 保持现状不切换。",
        ]
    return [
        "调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。",
        "挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。",
        "旧系统兼容：旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility，不允许自定义 revise/retry 回流规则。",
    ]


def minimal_code_skeleton(feature: dict[str, Any]) -> dict[str, str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return {
            "happy_path": "\n".join([
                "```python",
                "def evaluate_gate_decision(handoff_ref: str) -> GateDecision:",
                "    envelope = load_handoff_envelope(handoff_ref)",
                "    brief = build_gate_brief_record(envelope)",
                "    pending = persist_pending_human_decision(brief)",
                "    action = capture_human_action(pending)",
                "    decision = persist_gate_decision(",
                "        pending_ref=pending.ref,",
                "        human_action=action.kind,",
                "        decision_target=action.target,",
                "        decision_basis_refs=action.basis_refs,",
                "    )",
                "    dispatch_decision(decision)",
                "    return decision",
                "```",
            ]),
            "failure_path": "\n".join([
                "```python",
                "def evaluate_gate_decision_with_repair(handoff_ref: str) -> RepairOutcome:",
                "    envelope = load_handoff_envelope(handoff_ref)",
                "    brief = build_gate_brief_record(envelope)",
                "    pending = persist_pending_human_decision(brief)",
                "    action = capture_human_action(pending)",
                "    if not action.target or not action.basis_refs:",
                "        mark_pending_repair_required(pending.ref)",
                "        return request_basis_completion(pending.ref)",
                "    decision = persist_gate_decision(",
                "        pending_ref=pending.ref,",
                "        human_action=action.kind,",
                "        decision_target=action.target,",
                "        decision_basis_refs=action.basis_refs,",
                "    )",
                "    return dispatch_with_repair(decision)",
                "```",
            ]),
        }
    if axis == "layering":
        return {
            "happy_path": "\n".join([
                "```python",
                "def validate_admission(request: AdmissionRequest) -> AdmissionVerdict:",
                "    lineage = resolve_lineage(request.requested_ref)",
                "    formal_ref = require_formal_ref(lineage)",
                "    check_consumer_policy(request.consumer_ref, formal_ref)",
                "    record_read_evidence(request.consumer_ref, formal_ref)",
                "    return AdmissionVerdict.allow(formal_ref=formal_ref, lineage_ref=lineage.lineage_ref)",
                "```",
            ]),
            "failure_path": "\n".join([
                "```python",
                "def validate_admission_or_deny(request: AdmissionRequest) -> AdmissionVerdict:",
                "    lineage = resolve_lineage(request.requested_ref)",
                "    if lineage is None:",
                "        return AdmissionVerdict.deny(reason_code='lineage_missing')",
                "    if lineage.layer != 'formal':",
                "        return AdmissionVerdict.deny(reason_code='layer_violation')",
                "    return validate_admission(request)",
                "```",
            ]),
        }
    if axis == "io_governance":
        return {
            "happy_path": "\n".join([
                "```python",
                "def governed_write(request: GatewayWriteRequest) -> GatewayWriteResult:",
                "    normalized = normalize_write_request(request)",
                "    verdict = preflight_policy_check(normalized)",
                "    require(verdict.allow, verdict.reason_code)",
                "    ensure_registry_prerequisite(normalized)",
                "    artifact_ref = commit_via_gateway(normalized, verdict.resolved_path)",
                "    receipt = build_write_receipt(artifact_ref, verdict)",
                "    persist_gateway_evidence(receipt)",
                "    return GatewayWriteResult(artifact_ref=artifact_ref, receipt_ref=receipt.receipt_ref)",
                "```",
            ]),
            "failure_path": "\n".join([
                "```python",
                "def governed_write_with_compensation(request: GatewayWriteRequest) -> GatewayWriteResult:",
                "    normalized = normalize_write_request(request)",
                "    verdict = preflight_policy_check(normalized)",
                "    if not verdict.allow:",
                "        return GatewayWriteResult.reject(reason_code=verdict.reason_code)",
                "    artifact_ref = commit_via_gateway(normalized, verdict.resolved_path)",
                "    try:",
                "        receipt = build_write_receipt(artifact_ref, verdict)",
                "    except ReceiptBuildError:",
                "        mark_receipt_pending(artifact_ref)",
                "        return GatewayWriteResult.partial_success(artifact_ref=artifact_ref)",
                "    return GatewayWriteResult(artifact_ref=artifact_ref, receipt_ref=receipt.receipt_ref)",
                "```",
            ]),
        }
    if axis == "adoption_e2e":
        return {
            "happy_path": "\n".join([
                "```python",
                "def run_pilot_wave(directive: OnboardingDirective) -> PilotWaveResult:",
                "    binding = bind_skill_to_mainline(directive.skill_ref, directive.compat_mode)",
                "    evidence = execute_pilot_chain(binding, directive.scope)",
                "    verdict = evaluate_cutover_guard(evidence)",
                "    persist_wave_state(directive.wave_id, verdict, evidence)",
                "    return PilotWaveResult(binding_ref=binding.binding_ref, cutover_verdict=verdict)",
                "```",
            ]),
            "failure_path": "\n".join([
                "```python",
                "def run_pilot_wave_with_fallback(directive: OnboardingDirective) -> PilotWaveResult:",
                "    binding = bind_skill_to_mainline(directive.skill_ref, directive.compat_mode)",
                "    evidence = execute_pilot_chain(binding, directive.scope)",
                "    if not evidence.is_complete:",
                "        keep_compat_mode(binding.binding_ref)",
                "        return PilotWaveResult.fail(reason='pilot_evidence_incomplete')",
                "    return run_pilot_wave(directive)",
                "```",
            ]),
        }
    return {
        "happy_path": "\n".join([
            "```python",
            "def advance_mainline(handoff: HandoffEnvelope) -> RuntimeTransition:",
            "    slot = persist_handoff(handoff)",
            "    decision = request_gate_decision(slot.handoff_ref)",
            "    next_state = apply_runtime_transition(slot, decision)",
            "    record_transition_evidence(slot.handoff_ref, next_state)",
            "    return next_state",
            "```",
        ]),
        "failure_path": "\n".join([
            "```python",
            "def advance_mainline_with_reentry(handoff: HandoffEnvelope) -> RuntimeTransition:",
            "    slot = persist_handoff(handoff)",
            "    decision = request_gate_decision(slot.handoff_ref)",
            "    if decision.kind in {'revise', 'retry'}:",
            "        return write_reentry_command(slot.handoff_ref, decision)",
            "    return advance_mainline(handoff)",
            "```",
        ]),
    }
