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
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            scenario = str(check.get("scenario") or "").strip()
            then = str(check.get("then") or "").strip()
            if scenario and then:
                rules.append(f"{scenario}: {then}")
    return unique_strings(rules)[:6]


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
    topics = ensure_list(feature.get("dependencies"))[:3]
    if len(topics) < 2:
        topics.extend(ensure_list(feature.get("scope"))[: 2 - len(topics)])
    return unique_strings(topics)[:3]


def responsibility_splits(feature: dict[str, Any]) -> list[str]:
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
            "`lee gate submit-handoff --producer-ref <producer_ref> --proposal-ref <proposal_ref> --payload-ref <payload_ref> --state <pending_state>` via `cli/commands/gate/command.py`",
            "`lee gate show-pending --handoff-ref <handoff_ref>` via `cli/commands/gate/command.py`",
        ]
    if axis == "formalization":
        return [
            "`lee gate decide --handoff-ref <handoff_ref> --proposal-ref <proposal_ref> --decision <approve|revise|retry|handoff|reject> --review-context <json>` via `cli/commands/gate/command.py`",
            "`lee registry publish-formal --candidate-ref <candidate_ref> --decision-ref <decision_ref> --target-kind <formal_kind>` via `cli/commands/registry/command.py`",
        ]
    if axis == "layering":
        return [
            "`lee registry resolve-formal-ref --requested-ref <object_ref>` via `cli/commands/registry/command.py`",
            "`lee registry validate-admission --consumer-ref <consumer_ref> --requested-ref <object_ref>` via `cli/commands/registry/command.py`",
        ]
    if axis == "io_governance":
        return [
            "`lee artifact commit-governed --logical-path <path> --path-class <class> --mode <read|write> --payload-ref <payload_ref>` via `cli/commands/artifact/command.py`",
            "`lee artifact read-governed --managed-ref <managed_ref>` via `cli/commands/artifact/command.py`",
        ]
    if axis == "adoption_e2e":
        return [
            "`lee rollout onboard-skill --skill-ref <skill_ref> --wave-id <wave_id> --compat-mode <mode>` via `cli/commands/rollout/command.py`",
            "`lee audit submit-pilot-evidence --pilot-chain-ref <chain_ref> --audit-ref <audit_ref>` via `cli/commands/audit/command.py`",
        ]
    return [
        "`lee gate submit-handoff --producer-ref <producer_ref> --proposal-ref <proposal_ref> --payload-ref <payload_ref> --state <pending_state>` via `cli/commands/gate/command.py`",
        "`lee gate show-pending --handoff-ref <handoff_ref>` via `cli/commands/gate/command.py`",
    ]


def api_request_response_contracts(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "collaboration":
        return [
            "`lee gate submit-handoff`: request fields=`producer_ref`, `proposal_ref`, `payload_ref`, `pending_state`, `trace_context_ref`; response fields=`handoff_ref`, `queue_slot`, `gate_pending_ref`, `trace_ref`.",
            "`lee gate show-pending`: request fields=`handoff_ref`; response fields=`handoff_ref`, `pending_state`, `assigned_gate_queue`, `trace_ref`.",
        ]
    if axis == "formalization":
        return [
            "`lee gate decide`: request fields=`handoff_ref`, `proposal_ref`, `decision`, `decision_reason`, `review_context_ref`; response fields=`decision_ref`, `decision`, `reentry_allowed`, `materialization_required`, `evidence_ref`.",
            "`lee registry publish-formal`: request fields=`candidate_ref`, `decision_ref`, `target_kind`, `publish_mode`; response fields=`formal_ref`, `lineage_ref`, `publish_status`, `receipt_ref`.",
        ]
    if axis == "layering":
        return [
            "`lee registry resolve-formal-ref`: request fields=`requested_ref`; response fields=`authoritative_ref`, `layer`, `lineage_ref`, `upstream_refs`, `downstream_refs`.",
            "`lee registry validate-admission`: request fields=`consumer_ref`, `requested_ref`, `lineage_ref?`; response fields=`allow`, `resolved_formal_ref`, `reason_code`, `evidence_ref`.",
        ]
    if axis == "io_governance":
        return [
            "`lee artifact commit-governed`: request fields=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; response fields=`managed_ref`, `registry_record_ref`, `write_receipt_ref`, `mode_decision`.",
            "`lee artifact read-governed`: request fields=`managed_ref`; response fields=`payload_ref`, `resolved_path`, `registry_record_ref`, `read_receipt_ref`.",
        ]
    if axis == "adoption_e2e":
        return [
            "`lee rollout onboard-skill`: request fields=`skill_ref`, `wave_id`, `scope`, `compat_mode`; response fields=`status`, `runtime_binding_ref`, `cutover_guard_ref`.",
            "`lee audit submit-pilot-evidence`: request fields=`pilot_chain_ref`, `producer_ref`, `consumer_ref`, `audit_ref`, `gate_ref`; response fields=`evidence_status`, `cutover_recommendation`, `evidence_ref`.",
        ]
    return [
        "`lee gate submit-handoff`: request fields=`producer_ref`, `proposal_ref`, `payload_ref`, `pending_state`, `trace_context_ref`; response fields=`handoff_ref`, `queue_slot`, `gate_pending_ref`, `trace_ref`.",
        "`lee gate show-pending`: request fields=`handoff_ref`; response fields=`handoff_ref`, `pending_state`, `assigned_gate_queue`, `trace_ref`.",
    ]


def api_error_and_idempotency(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "collaboration":
        return [
            "`lee gate submit-handoff`: errors=`missing_payload`, `invalid_state`, `duplicate_submission`; idempotent key=`producer_ref + payload_digest`; precondition=`payload 已写入 runtime 可读位置`.",
            "`lee gate show-pending`: errors=`handoff_missing`, `pending_state_unavailable`; idempotent key=`handoff_ref`; precondition=`handoff 已提交到 gate pending`.",
        ]
    if axis == "formalization":
        return [
            "`lee gate decide`: errors=`handoff_missing`, `invalid_state`, `decision_conflict`; idempotent key=`handoff_ref + decision_round`; precondition=`handoff 已进入 gate pending`.",
            "`lee registry publish-formal`: errors=`decision_not_approvable`, `registry_bind_failed`, `publish_failed`; idempotent key=`candidate_ref + decision_ref`; precondition=`decision in {approve, handoff}`.",
        ]
    if axis == "layering":
        return [
            "`lee registry resolve-formal-ref`: errors=`unknown_ref`, `ambiguous_lineage`; idempotent key=`requested_ref`; precondition=`ref 已存在于 registry/lineage store`.",
            "`lee registry validate-admission`: errors=`formal_ref_missing`, `lineage_missing`, `layer_violation`; idempotent key=`consumer_ref + requested_ref`; precondition=`requested object 可解析`.",
        ]
    if axis == "io_governance":
        return [
            "`lee artifact commit-governed`: errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent key=`logical_path + payload_digest + mode`; precondition=`request normalized and payload readable`.",
            "`lee artifact read-governed`: errors=`managed_ref_missing`, `registry_record_missing`, `read_forbidden`; idempotent key=`managed_ref`; precondition=`managed_ref 已登记`.",
        ]
    if axis == "adoption_e2e":
        return [
            "`lee rollout onboard-skill`: errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent key=`skill_ref + wave_id`; precondition=`foundation features freeze-ready`.",
            "`lee audit submit-pilot-evidence`: errors=`missing_chain_step`, `audit_not_traceable`; idempotent key=`pilot_chain_ref`; precondition=`pilot chain 已执行一次`.",
        ]
    return [
        "`lee gate submit-handoff`: errors=`missing_payload`, `invalid_state`, `duplicate_submission`; idempotent key=`producer_ref + payload_digest`; precondition=`payload 已写入 runtime 可读位置`.",
        "`lee gate show-pending`: errors=`handoff_missing`, `pending_state_unavailable`; idempotent key=`handoff_ref`; precondition=`handoff 已提交到 gate pending`.",
    ]


def api_compatibility_rules(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    rules = [
        "新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。",
        "command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。",
    ]
    if axis == "collaboration":
        rules.append("提交与 pending 可见性命令不得偷带决策语义；`approve / revise / retry / handoff / reject` 只能留在 formalization FEAT。")
    if axis == "formalization":
        rules.append("`lee gate decide` 与 `lee registry publish-formal` 的 decision vocabulary 必须共享同一份枚举，不允许命名漂移。")
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
    checks: list[dict[str, Any]] = []
    issues: list[str] = []

    checks.append(
        {
            "name": "TECH mandatory",
            "passed": True,
            "detail": "TECH is always emitted for the selected FEAT.",
        }
    )

    if assessment["arch_required"]:
        passed = len(architecture_topics(feature)) >= 2
        checks.append(
            {
                "name": "ARCH coverage",
                "passed": passed,
                "detail": "ARCH is required and carries system-boundary topics.",
            }
        )
        if not passed:
            issues.append("ARCH was required but architecture topics could not be resolved clearly.")
    else:
        checks.append(
            {
                "name": "ARCH omission justified",
                "passed": True,
                "detail": "ARCH is omitted because the FEAT does not require boundary or topology redesign.",
            }
        )

    if assessment["api_required"]:
        passed = len(api_surfaces(feature)) >= 1
        checks.append(
            {
                "name": "API coverage",
                "passed": passed,
                "detail": "API is required and carries at least one contract surface.",
            }
        )
        if not passed:
            issues.append("API was required but no contract surfaces were derived.")
    else:
        checks.append(
            {
                "name": "API omission justified",
                "passed": True,
                "detail": "API is omitted because no explicit cross-boundary contract surface was detected.",
            }
        )

    return {
        "passed": not issues,
        "checks": checks,
        "issues": issues,
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


def implementation_architecture(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "Business skill 只产出 candidate package / proposal / evidence，由 handoff runtime 承接进入 external gate。",
            "External gate 负责 approve / revise / retry / handoff / reject 决策，并把 decision 与 formal materialization 串成单一路径。",
            "Formal object 物化后才允许进入 downstream consumer；candidate layer 永远不直接成为正式输入。",
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
        "Execution loop、gate loop、human review 通过文件化 handoff runtime 协作，所有推进都以结构化对象驱动。",
        "Gate 只消费 handoff/proposal 并返回结构化 decision；回流路径必须回到 runtime，而不是由 skill 私下拼接。",
        "Formal materialization 不在本 FEAT 内实现，只保留与正式交接 FEAT 对接的边界。",
    ]


def implementation_modules(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    common = [
        "Handoff runtime adapter：负责把受治理对象写入/读取主链 runtime，并维持 traceability。",
        "Decision boundary adapter：负责把上游 FEAT 约束映射成 runtime 可执行边界，不把实现责任散落到业务 skill。",
    ]
    if axis == "formalization":
        return common + [
            "Gate decision processor：解析 approve / revise / retry / handoff / reject，并驱动唯一升级链。",
            "Formal materialization worker：把 candidate 升级成 formal object，并写出 downstream 可消费引用。",
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
        "Loop coordinator：定义 execution / gate / human 三类 loop 的责任切换点。",
        "Re-entry controller：约束 revise / retry 回流时的允许状态、消费对象和下一跳。",
    ]


def state_model(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "`candidate_prepared` -> `submitted_to_gate` -> `decision_issued` -> `formal_materialized` -> `downstream_consumable`",
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
        "`handoff_prepared` -> `gate_pending` -> `decision_returned` -> `advanced_or_reentered`",
        "`decision_returned(revise/retry)` -> `runtime_reentry` -> `handoff_prepared`",
    ]


def architecture_diagram(feature: dict[str, Any]) -> str:
    axis = feature_axis(feature)
    if axis == "formalization":
        return "\n".join([
            "```text",
            "[Business Skill]",
            "      |",
            "      v",
            "[Candidate Package] --> [Handoff Runtime] --> [External Gate] --> [Decision Object]",
            "                                                              |",
            "                                                              +--> revise/retry --> [Handoff Runtime]",
            "                                                              |",
            "                                                              +--> approve/handoff --> [Formal Materialization] --> [Formal Object] --> [Downstream Consumer]",
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
        "       |                    |                     +--> decision --> [Handoff Runtime]",
        "       +---- advance/re-enter <------------------+",
        "```",
    ])


def flow_diagram(feature: dict[str, Any]) -> str:
    axis = feature_axis(feature)
    if axis == "formalization":
        return "\n".join([
            "```text",
            "Business Skill -> Runtime         : submit candidate + proposal",
            "Runtime        -> External Gate   : enqueue handoff for decision",
            "External Gate  -> Runtime         : approve / revise / retry / handoff / reject",
            "Runtime        -> Materializer    : materialize formal object on approve/handoff",
            "Materializer   -> Consumer        : publish formal refs",
            "Runtime        -> Business Skill  : return structured decision on revise/retry",
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
        "Execution Loop -> Runtime      : submit handoff object",
        "Runtime        -> Gate Loop    : enqueue proposal",
        "Gate Loop      -> Human Review : escalate when required",
        "Human Review   -> Gate Loop    : return decision",
        "Gate Loop      -> Runtime      : approve / revise / retry / handoff / reject",
        "Runtime        -> Execution Loop: advance or re-enter",
        "```",
    ])


def implementation_strategy(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "先固化 candidate -> gate -> formal 的对象链与 decision vocabulary，再接入真正的 materialization writer。",
            "实现 revise / retry 回流时，必须先打通 structured decision 回写，再允许下游消费 formal refs。",
            "最后用一条真实 candidate-to-formal pilot 验证 formal object、decision 和 evidence 三者闭环。",
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
            "把 mainline handoff 与 formalization 写入都切到同一条受治理 IO 链路，避免双轨写盘。",
            "最后用真实 handoff write + formal write 两条样例验证 path / mode / registry 行为。",
        ]
    if axis == "adoption_e2e":
        return [
            "先冻结 onboarding matrix、pilot chain 和 cutover guard，再按 wave 接入 governed skill。",
            "先跑最小真实 producer -> consumer -> audit -> gate pilot，稳定后再扩大接入波次。",
            "每个 wave 都必须保留 fallback 条件与 rollback evidence，不能一次性全量切换。",
        ]
    return [
        "先定义 loop ownership、handoff object 和 decision return path，再接入 human review escalation。",
        "实现 revise / retry 回流时，必须通过 runtime 统一回写，不允许 business skill 自行拼接回路。",
        "最后用至少一条真实 handoff -> gate -> re-entry pilot 验证协作闭环成立。",
    ]


def implementation_unit_mapping(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "`cli/lib/protocol.py` (`extend`): 定义 `HandoffEnvelope`、`GateDecision`、`FormalMaterializationReceipt` 结构。",
            "`cli/lib/formalization.py` (`new`): 实现 candidate -> formal 的物化编排与结果回写。",
            "`cli/lib/registry_store.py` (`extend`): 写入 formal refs、lineage 与 downstream 可消费引用。",
            "`cli/commands/gate/command.py` (`extend`): 接入 gate decision vocabulary 并驱动 materialization dispatch。",
            "`cli/commands/registry/command.py` (`extend`): 提供 formal object publish / resolve 能力，依赖 `cli/lib/formalization.py`。",
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
        "`cli/lib/protocol.py` (`extend`): 定义 `HandoffEnvelope`、`ProposalEnvelope`、`GateDecision`、`ReentryCommand` 结构。",
        "`cli/lib/mainline_runtime.py` (`new`): 管理 execution/gate/human loop 之间的 handoff 与状态推进。",
        "`cli/lib/reentry.py` (`new`): 处理 revise / retry 的回流判断、对象回写和下一跳选择。",
        "`cli/commands/gate/command.py` (`extend`): 接入 gate decision consume / return 路径，依赖 `cli/lib/mainline_runtime.py`。",
        "`cli/commands/audit/command.py` (`extend`): 作为 human review / audit escalation 的消费方，回写 structured decision。",
    ]


def interface_contracts(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "`GateDecision`: input=`HandoffEnvelope` + `proposal_ref`; output=`decision`, `decision_reason`, `reentry_allowed`, `materialization_required`; errors=`invalid_state`, `unknown_candidate`, `policy_reject`; idempotent=`yes by handoff_ref + decision_round`; precondition=`candidate package 已注册且 gate pending`。",
            "`FormalMaterializationRequest`: input=`candidate_ref`, `decision_ref`, `target_formal_kind`; output=`formal_ref`, `lineage_ref`, `evidence_ref`; errors=`decision_not_approvable`, `registry_bind_failed`, `publish_failed`; idempotent=`yes by candidate_ref + decision_ref`; precondition=`decision in {approve, handoff}`。",
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
        "`HandoffEnvelope`: input=`producer_ref`, `proposal_ref`, `payload_ref`, `state`; output=`handoff_ref`, `queue_slot`, `trace_ref`; errors=`invalid_state`, `missing_payload`; idempotent=`yes by producer_ref + payload_digest`; precondition=`payload 已写入 runtime 可读位置`。",
        "`GateDecision`: input=`handoff_ref`, `proposal_ref`, `review_context`; output=`decision`, `next_loop`, `reentry_ref?`; errors=`handoff_missing`, `decision_conflict`; idempotent=`yes by handoff_ref + decision_round`; precondition=`handoff 已进入 gate pending`。",
    ]


def main_sequence(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "1. normalize handoff and proposal refs",
            "2. validate gate-pending state and decision vocabulary",
            "3. persist gate decision and decision evidence",
            "4. if approve/handoff then dispatch formal materialization",
            "5. bind formal refs into registry / lineage store",
            "6. publish downstream-consumable ref and completion receipt",
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
        "1. normalize handoff object and producer state",
        "2. enqueue handoff into runtime / queue slot",
        "3. route proposal into gate loop and escalate to human review when required",
        "4. return structured decision to runtime",
        "5. decide advance vs revise/retry re-entry",
        "6. persist transition evidence and next-loop directive",
    ]


def exception_compensation(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "decision persisted 但 materialization fail：保留 decision evidence，状态回到 `materialization_pending`，禁止伪造 formal refs。",
            "materialization success 但 downstream publish fail：允许 partial success，formal object 保持已物化，但必须记录 `publish_pending` 并阻止 consumer admission。",
            "registry bind fail：回滚 formal publish 指针，保留 candidate 不变，要求人工或 gate repair 后重试。",
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
        "gate decision 持久化失败：不允许推进下一 loop，当前 handoff 保持 pending。",
        "runtime re-entry write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。",
        "human review timeout：按明确规则降级到 `handoff` 或 `retry_pending`，并记录超时 evidence。",
    ]


def integration_points(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return [
            "调用方：现有 governed skill 通过 handoff runtime 提交 candidate package，由 `cli/commands/gate/command.py` 消费 decision。",
            "挂接点：file-handoff 发生在 candidate package 写入 runtime 之后，formal materialization 在 external gate approve/handoff 之后。",
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
        "调用方：producer skill 通过 runtime 写入 handoff object；gate loop 和 human review 在 `cli/commands/gate/command.py` / `cli/commands/audit/command.py` 挂接。",
        "挂接点：file-handoff 发生在 producer 写入 runtime 之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 decision。",
        "旧系统兼容：旧 skill 若未接入统一 re-entry controller，只能以 compat mode 只读消费，不允许自定义回流规则。",
    ]


def minimal_code_skeleton(feature: dict[str, Any]) -> dict[str, str]:
    axis = feature_axis(feature)
    if axis == "formalization":
        return {
            "happy_path": "\n".join([
                "```python",
                "def execute_formalization(handoff_ref: str) -> FormalMaterializationReceipt:",
                "    envelope = load_handoff_envelope(handoff_ref)",
                "    decision = gate_decide(envelope)",
                "    assert decision.kind in {'approve', 'handoff'}",
                "    formal_ref = materialize_formal_object(envelope.candidate_ref, decision)",
                "    bind_lineage(formal_ref, envelope.candidate_ref, decision.decision_ref)",
                "    publish_downstream_ref(formal_ref)",
                "    return build_receipt(formal_ref, decision.decision_ref)",
                "```",
            ]),
            "failure_path": "\n".join([
                "```python",
                "def execute_formalization_with_repair(handoff_ref: str) -> RepairOutcome:",
                "    envelope = load_handoff_envelope(handoff_ref)",
                "    decision = gate_decide(envelope)",
                "    if decision.kind in {'revise', 'retry'}:",
                "        return persist_reentry(envelope, decision)",
                "    try:",
                "        formal_ref = materialize_formal_object(envelope.candidate_ref, decision)",
                "        bind_lineage(formal_ref, envelope.candidate_ref, decision.decision_ref)",
                "    except RegistryBindError:",
                "        mark_materialization_pending(envelope.handoff_ref, decision.decision_ref)",
                "        return request_gate_repair(envelope.handoff_ref)",
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
