#!/usr/bin/env python3
"""
Derivation helpers for the lite-native epic-to-feat runtime.
"""

from __future__ import annotations

from typing import Any

from epic_to_feat_common import (
    ensure_list,
    extract_src_ref,
    shorten_identifier,
    summarize_text,
    unique_strings,
)


def choose_src_ref(package: Any) -> str:
    source_refs = ensure_list(package.epic_json.get("source_refs"))
    src_ref = extract_src_ref(source_refs, fallback=str(package.epic_json.get("src_root_id") or ""))
    if src_ref:
        return src_ref
    return f"SRC-{shorten_identifier(package.run_id, limit=32)}"


def choose_epic_ref(package: Any) -> str:
    existing = str(package.epic_json.get("epic_freeze_ref") or "").strip()
    if existing:
        return existing
    title = str(package.epic_json.get("title") or package.run_id)
    return f"EPIC-{shorten_identifier(title, limit=40)}"


def axis_key(axis: dict[str, str]) -> str:
    raw = str(axis.get("id") or "").strip().lower()
    if raw:
        return raw
    name = str(axis.get("name") or "").strip()
    mapping = {
        "主链协作闭环能力": "collaboration-loop",
        "正式交接与物化能力": "handoff-formalization",
        "对象分层与准入能力": "object-layering",
        "主链文件 IO 与路径治理能力": "artifact-io-governance",
        "技能接入与跨 skill 闭环验证能力": "skill-adoption-e2e",
    }
    return mapping.get(name, shorten_identifier(name, limit=48).lower())


def epic_uses_adr005_foundation(package: Any, axes: list[dict[str, str]] | None = None) -> bool:
    refs = {item.upper() for item in ensure_list(package.epic_json.get("source_refs"))}
    active_axes = axes or derive_feat_axes(package)
    has_io_axis = any(axis_key(item) == "artifact-io-governance" for item in active_axes)
    return has_io_axis and ("ADR-005" in refs or {"ADR-001", "ADR-003", "ADR-006"}.issubset(refs))


def bundle_source_refs(package: Any, axes: list[dict[str, str]] | None = None) -> list[str]:
    refs = ensure_list(package.epic_json.get("source_refs"))
    return unique_strings(refs + (["ADR-005"] if epic_uses_adr005_foundation(package, axes) else []))


def prerequisite_foundations(package: Any, axes: list[dict[str, str]] | None = None) -> list[str]:
    if not epic_uses_adr005_foundation(package, axes):
        return []
    return [
        "ADR-005 作为主链文件 IO / 路径治理前置基础，要求在本 EPIC 启动前已交付或已可稳定复用。",
        "本 EPIC 只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力，不在本 EPIC 内重新实现这些模块。",
    ]


def feat_track(axis: dict[str, str]) -> str:
    return "adoption_e2e" if axis_key(axis) == "skill-adoption-e2e" else "foundation"


def feat_goal(axis: dict[str, str], package: Any) -> str:
    goals = {
        "collaboration-loop": "让 execution、gate、human 三类 loop 在同一条主链里形成稳定协作闭环，而不是由各 skill 分别拼接回流规则。",
        "handoff-formalization": "让 handoff、gate decision 与 formal materialization 形成单一路径的正式升级链，而不是让 candidate 与 formal 流转并存。",
        "object-layering": "让 candidate package、formal object 与 downstream consumption 形成稳定分层，防止业务 skill 混入裁决与准入职责。",
        "artifact-io-governance": "让主链中的 artifact IO、路径与目录边界稳定接入 ADR-005 已交付的治理基础，并且严格限制在 mainline handoff 和 formalization 语境内。" if epic_uses_adr005_foundation(package) else "让主链中的 artifact IO、路径与目录边界收敛为受治理能力，并且严格限制在 mainline handoff 和 formalization 语境内。",
        "skill-adoption-e2e": "让治理底座通过真实 governed skill onboarding、迁移切换和跨 skill E2E 闭环验证落到主链里，而不是停留在组件内自测或口头假设。",
    }
    key = axis_key(axis)
    if key in goals:
        return goals[key]
    business_goal = str(package.epic_json.get("business_goal") or "")
    return summarize_text(f"{axis.get('name')}承担 EPIC 目标中的一块独立能力面。{business_goal}", limit=220)


def feat_scope(axis: dict[str, str], package: Any | None = None) -> list[str]:
    scopes = {
        "collaboration-loop": [
            "定义 execution loop 应提交什么对象、在何时进入 gate loop，以及哪些状态允许回流到 revision / retry。",
            "定义 gate loop 与 human loop 的衔接界面，包括谁消费 proposal、谁返回 decision、谁触发后续推进。",
            "明确 loop 协作只覆盖推进责任、交接界面与回流条件，不定义 formal materialization 对象本身。",
            "显式约束下游不得再为 queue、handoff、gate 关系发明第二套等价规则。",
        ],
        "handoff-formalization": [
            "定义 handoff object、gate decision object、formal materialization object 在主链中的单向升级顺序。",
            "明确 candidate 只能作为 gate 消费对象，不能绕过 gate 直接成为 downstream formal input。",
            "明确本 FEAT 负责正式推进链路，不负责对象准入判定与读取资格细则。",
            "要求下游继承同一套 approve / revise / retry / handoff / reject 语义，不得并列批准语义。",
        ],
        "object-layering": [
            "定义 candidate package、formal object、downstream consumption object 的分层职责和允许的引用方向。",
            "定义什么对象有资格成为正式输入，以及哪些 consumer 只能读取 formal layer 而不能读取 candidate layer。",
            "明确本 FEAT 负责对象层级与准入，不负责 handoff 决策链和 IO/path 落盘策略。",
            "要求任何下游消费都必须沿 formal refs 与 lineage 进入，不能以路径猜测或旁路对象读取。",
        ],
        "artifact-io-governance": [
            "定义主链 handoff、formal materialization 与 governed skill IO 如何接入 ADR-005 提供的 artifact path、目录边界与写入模式治理能力。",
            "明确哪些 IO 是受治理主链 IO，哪些属于 ADR-005 之外的全局文件治理而必须留在本 FEAT 之外。",
            "要求所有正式主链写入都遵循统一的路径与覆盖边界，不允许以局部临时目录策略替代。",
            "明确本 FEAT 只定义主链接入与消费 ADR-005 的边界，不扩展为全仓库或全项目文件治理总方案。",
        ] if package is not None and epic_uses_adr005_foundation(package) else [
            "约束主链 handoff、formal materialization 与 governed skill IO 的 artifact path、目录边界与写入模式。",
            "明确哪些 IO 是受治理主链 IO，哪些属于全局文件治理而必须留在本 FEAT 之外。",
            "要求所有正式主链写入都遵循统一的路径与覆盖边界，不允许以局部临时目录策略替代。",
            "明确本 FEAT 只覆盖 mainline IO/path 边界，不扩展为全仓库或全项目文件治理总方案。",
        ],
        "skill-adoption-e2e": [
            "定义现有 governed skill 的 onboarding 边界、接入矩阵与分批纳入规则，明确哪些 producer、consumer、gate consumer 在 scope 内。",
            "定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界，但不要求一次性完成全量 skill 迁移。",
            "要求至少选择一条真实 producer -> consumer -> audit -> gate pilot 主链，形成跨 skill E2E 闭环 evidence。",
            "明确本 FEAT 只面向本主链治理能力涉及的 governed skill 接入与验证，不扩大为仓库级全局文件治理改造。",
        ],
    }
    key = axis_key(axis)
    if key in scopes:
        return scopes[key]
    return [
        str(axis.get("scope") or axis.get("feat_axis") or axis.get("name") or "").strip(),
        f"Derived axis: {axis.get('feat_axis') or axis.get('name')}",
    ]


def feat_non_goals(axis: dict[str, str], package: Any) -> list[str]:
    extras = {
        "collaboration-loop": [
            "Do not define candidate -> formal upgrade semantics, gate decision authority, or materialization outputs here.",
            "Do not define object admission, formal-read eligibility, or path governance policy here.",
        ],
        "handoff-formalization": [
            "Do not redefine execution / gate / human loop responsibility splits or re-entry conditions here.",
            "Do not define consumer admission, formal-ref eligibility, or path enforcement policy here.",
        ],
        "object-layering": [
            "Do not define the handoff -> gate decision -> formal materialization action chain here.",
            "Do not define governed artifact paths, write modes, or repository-level IO enforcement here.",
        ],
        "artifact-io-governance": [
            "Do not define object qualification, candidate/formal authority, or consumer admission semantics here.",
            "Do not re-implement ADR-005 Gateway / Path Policy / Registry modules or widen them into repository-wide governance here.",
        ] if epic_uses_adr005_foundation(package) else [
            "Do not define object qualification, candidate/formal authority, or consumer admission semantics here.",
            "Do not define gate decision semantics, approval authority, or formalization outcomes here.",
        ],
        "skill-adoption-e2e": [
            "Do not redefine ADR-005 prerequisite foundations or foundation FEAT contracts that already own IO/gate consumption boundaries.",
            "Do not require one-shot migration of every governed skill or exhaustive coverage of every producer/consumer combination.",
        ] if epic_uses_adr005_foundation(package) else [
            "Do not redefine Gateway / Policy / Registry / Audit / Gate technical contracts that already belong to foundation FEATs.",
            "Do not require one-shot migration of every governed skill or exhaustive coverage of every producer/consumer combination.",
        ],
    }
    return unique_strings(extras.get(axis_key(axis), []))[:4]


def bundle_shared_non_goals(package: Any) -> list[str]:
    inherited = ensure_list(package.epic_json.get("non_goals"))[:4]
    shared = [
        "Do not expand any FEAT into heavy scheduler, database, event-bus, or runtime platform design.",
        "Do not turn the FEAT bundle into schema, CLI, directory-layout, or code-implementation detail.",
        "Do not embed task-level implementation sequencing inside FEAT definitions.",
    ]
    return unique_strings(inherited + shared)[:7]


def select_constraints(package: Any, keywords: list[str], fallback_count: int = 2) -> list[str]:
    constraints = ensure_list(package.epic_json.get("constraints_and_dependencies"))
    selected: list[str] = []
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for item in constraints:
        lowered = item.lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            selected.append(item)
    if len(selected) < fallback_count:
        for item in constraints:
            if item not in selected:
                selected.append(item)
            if len(selected) >= fallback_count:
                break
    return selected


def feat_constraints(axis: dict[str, str], package: Any) -> list[str]:
    key = axis_key(axis)
    selected = {
        "collaboration-loop": select_constraints(package, ["双会话双队列", "execution loop", "human loop", "queue"], fallback_count=3),
        "handoff-formalization": select_constraints(package, ["handoff runtime", "external gate", "approve", "candidate", "formal object"], fallback_count=3),
        "object-layering": select_constraints(package, ["business skill", "formal object", "formal refs", "lineage", "consumer"], fallback_count=3),
        "artifact-io-governance": select_constraints(package, ["路径与目录治理", "governed skill io", "formal materialization", "handoff"], fallback_count=3),
        "skill-adoption-e2e": select_constraints(package, ["integration matrix", "onboarding", "migration", "cutover", "fallback", "producer -> consumer -> audit -> gate", "e2e"], fallback_count=3),
    }.get(key, select_constraints(package, [str(axis.get("name") or "")], fallback_count=3))

    specialized = {
        "collaboration-loop": [
            "Loop 协作语义必须显式说明哪类对象触发 gate、哪类 decision 允许回流、哪类状态允许继续推进。",
            "该 FEAT 只负责 loop 协作边界，不得把 formalization 细则混入 loop 责任定义。",
        ],
        "handoff-formalization": [
            "Candidate 不得绕过 gate 直接升级为 downstream formal input。",
            "Formal materialization 语义必须单一路径推进，不得出现并列正式化入口。",
        ],
        "object-layering": [
            "Consumer 准入必须沿 formal refs 与 lineage 判断，不得通过路径猜测获得读取资格。",
            "对象分层必须阻止业务 skill 在 candidate 层承担 gate 或 formal admission 职责。",
        ],
        "artifact-io-governance": ([
            "ADR-005 是本 FEAT 的前置基础；本 FEAT 只定义主链如何消费其受治理 IO/path 能力，不重新实现底层模块。",
            "主链 IO/path 规则只覆盖 handoff、formal materialization 与 governed skill IO，不得外扩成全局文件治理。",
            "任何正式主链写入都必须遵守受治理 path / mode 边界，不允许 silent fallback 到自由写入。",
        ] if epic_uses_adr005_foundation(package) else [
            "主链 IO/path 规则只覆盖 handoff、formal materialization 与 governed skill IO，不得外扩成全局文件治理。",
            "任何正式主链写入都必须遵守受治理 path / mode 边界，不允许 silent fallback 到自由写入。",
        ]),
        "skill-adoption-e2e": [
            "Onboarding / migration_cutover 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。",
            "真实闭环成立必须以 pilot E2E evidence 证明，不得把组件内自测当成唯一成立依据。",
        ],
    }.get(key, [])
    return unique_strings(selected + specialized)[:6]


def feat_dependencies(axis: dict[str, str], package: Any | None = None) -> list[str]:
    dependencies = {
        "collaboration-loop": [
            "Boundary to 正式交接与物化能力: 本 FEAT 只负责协作责任、状态流转与回流条件，不负责 formalization 语义、升级判定与物化结果。",
            "Boundary to 对象分层与准入能力: 本 FEAT 可以要求对象交接，但对象是否具备正式消费资格由对象分层 FEAT 决定。",
        ],
        "handoff-formalization": [
            "Boundary to 主链协作闭环能力: 本 FEAT 消费 loop 协作产物，但不重写 execution / gate / human 的责任分工、状态流转与回流条件。",
            "Boundary to 对象分层与准入能力: 本 FEAT 定义 candidate 到 formal 的推进链，不定义 consumer admission 与读取资格。",
        ],
        "object-layering": [
            "Boundary to 正式交接与物化能力: 本 FEAT 定义哪些对象可以成为正式输入，而不是定义正式升级动作本身。",
            "Boundary to 主链文件 IO 与路径治理能力: 本 FEAT 定义对象资格与引用方向，path / mode 规则留给 IO 治理 FEAT。",
        ],
        "artifact-io-governance": [
            "Boundary to 对象分层与准入能力: 本 FEAT 定义对象落盘边界，不定义对象层级与消费资格本身。",
            "Boundary to 正式交接与物化能力: 本 FEAT 约束 formalization 的 IO/path 边界，但 formalization 决策语义仍属于正式交接 FEAT。",
            "Boundary to ADR-005 prerequisite foundation: 本 FEAT 只消费已交付的 Gateway / Path Policy / Registry 能力，不在此重写其模块边界。",
        ] if package is not None and epic_uses_adr005_foundation(package) else [
            "Boundary to 对象分层与准入能力: 本 FEAT 定义对象落盘边界，不定义对象层级与消费资格本身。",
            "Boundary to 正式交接与物化能力: 本 FEAT 约束 formalization 的 IO/path 边界，但 formalization 决策语义仍属于正式交接 FEAT。",
        ],
        "skill-adoption-e2e": [
            "Boundary to foundation FEATs: 本 FEAT 只负责接入、迁移与真实链路验证，不重写 foundation FEAT 与 ADR-005 前置基础的能力定义。",
            "Boundary to release/test planning: 本 FEAT 负责定义 adoption/E2E 能力边界和 pilot 目标，不替代后续 release orchestration 或 test reporting。",
        ] if package is not None and epic_uses_adr005_foundation(package) else [
            "Boundary to foundation FEATs: 本 FEAT 只负责接入、迁移与真实链路验证，不重写 Gateway / Policy / Registry / Audit / Gate 的能力定义。",
            "Boundary to release/test planning: 本 FEAT 负责定义 adoption/E2E 能力边界和 pilot 目标，不替代后续 release orchestration 或 test reporting。",
        ],
    }
    return dependencies.get(axis_key(axis), [])


def build_acceptance_checks(feat_ref: str, epic_ref: str, axis: dict[str, str]) -> list[dict[str, Any]]:
    key = axis_key(axis)
    checks = {
        "collaboration-loop": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Loop responsibility split is explicit",
                "given": f"{epic_ref} requires execution, gate, and human loops to cooperate",
                "when": f"{feat_ref} is reviewed as a standalone capability",
                "then": "The FEAT must define which loop owns which transition, input object, and return path without overlapping formalization responsibilities.",
                "trace_hints": [feat_ref, "execution loop", "gate loop", "human loop", "responsibility split"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Loop re-entry conditions are bounded",
                "given": "A revise or retry decision occurs in the mainline",
                "when": "The decision is fed back to execution",
                "then": "The FEAT must make clear what objects are returned, who consumes them, and which loop state allows re-entry.",
                "trace_hints": [feat_ref, "revise", "retry", "re-entry", "handoff object"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Downstream flows do not redefine collaboration rules",
                "given": "A downstream workflow consumes this FEAT",
                "when": "It needs queue, gate, or human coordination semantics",
                "then": "It must inherit the same collaboration rules instead of inventing a parallel queue or handoff model.",
                "trace_hints": [feat_ref, "downstream inheritance", "queue", "handoff", "gate"],
            },
        ],
        "handoff-formalization": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Formal upgrade path is single and explicit",
                "given": f"{epic_ref} contains candidate outputs awaiting approval",
                "when": "The mainline moves from candidate to formal state",
                "then": "The FEAT must define one explicit handoff -> gate decision -> formal materialization chain without parallel shortcuts.",
                "trace_hints": [feat_ref, "handoff", "gate decision", "formal materialization", "single path"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Candidate cannot bypass gate",
                "given": "A candidate package exists but gate approval has not occurred",
                "when": "A downstream consumer requests formal input",
                "then": "The FEAT must prevent that candidate from being treated as a formal downstream source.",
                "trace_hints": [feat_ref, "candidate package", "gate approval", "formal input", "bypass forbidden"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Materialization stays separate from business skill logic",
                "given": "A business skill emits proposal and evidence objects",
                "when": "Formalization is evaluated",
                "then": "The FEAT must keep the formalization decision and materialization action outside the business skill body.",
                "trace_hints": [feat_ref, "business skill", "materialization separation", "external gate"],
            },
        ],
        "object-layering": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Candidate and formal layers cannot be confused",
                "given": f"{epic_ref} emits both candidate and formal-stage objects",
                "when": "A consumer resolves upstream inputs",
                "then": "The FEAT must make clear which layer is authoritative for downstream use and forbid layer ambiguity.",
                "trace_hints": [feat_ref, "candidate layer", "formal layer", "authoritative input"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Consumer admission is formal-ref based",
                "given": "A downstream reader needs to consume a governed object",
                "when": "It resolves eligibility",
                "then": "The FEAT must require formal refs and lineage-based admission rather than path guessing or adjacent file discovery.",
                "trace_hints": [feat_ref, "formal refs", "lineage", "consumer admission"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Business skill cannot silently inherit gate authority",
                "given": "A business skill emits a candidate package",
                "when": "That package is reviewed for downstream use",
                "then": "The FEAT must prevent the business skill from silently acting as gate, approver, or formal admission authority.",
                "trace_hints": [feat_ref, "business skill", "gate authority", "formal admission"],
            },
        ],
        "artifact-io-governance": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Mainline IO boundary is explicit",
                "given": f"{epic_ref} requires handoff and formalization artifacts to be written",
                "when": "A governed skill performs mainline IO",
                "then": "The FEAT must define which IO belongs to mainline handoff / materialization and which IO is out of scope.",
                "trace_hints": [feat_ref, "mainline IO", "handoff", "formalization", "scope boundary"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Path governance does not expand into global file governance",
                "given": "A downstream team proposes broader repository-wide directory rules",
                "when": "That proposal is compared to this FEAT",
                "then": "The FEAT must reject scope expansion beyond governed skill IO, handoff, and materialization boundaries.",
                "trace_hints": [feat_ref, "global file governance", "scope expansion forbidden", "path boundary"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Formal writes cannot fall back to free writes",
                "given": "A mainline write hits a path or mode restriction",
                "when": "The write is retried",
                "then": "The FEAT must preserve governed path / mode enforcement and block silent fallback to uncontrolled writes.",
                "trace_hints": [feat_ref, "path mode enforcement", "free write fallback", "formal write"],
            },
        ],
        "skill-adoption-e2e": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Onboarding scope and migration waves are explicit",
                "given": f"{epic_ref} requires real governed skill landing",
                "when": f"{feat_ref} is reviewed for downstream planning",
                "then": "The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.",
                "trace_hints": [feat_ref, "integration matrix", "migration wave", "cutover", "fallback"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "At least one real pilot chain is required",
                "given": "Foundation FEATs are implemented in isolation",
                "when": "Adoption readiness is evaluated",
                "then": "The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.",
                "trace_hints": [feat_ref, "producer -> consumer -> audit -> gate", "pilot chain", "E2E evidence"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Adoption scope does not expand into repository-wide governance",
                "given": "A team proposes folding all file-governance cleanup into this FEAT",
                "when": "The proposal is checked against FEAT boundaries",
                "then": "The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.",
                "trace_hints": [feat_ref, "governed skill onboarding", "scope control", "no global governance expansion"],
            },
        ],
    }.get(key, [])
    return checks


def derive_feat_axes(package: Any) -> list[dict[str, str]]:
    rollout_required = bool((package.epic_json.get("rollout_requirement") or {}).get("required"))
    required_tracks = ensure_list((package.epic_json.get("rollout_plan") or {}).get("required_feat_tracks"))
    axes = package.epic_json.get("capability_axes")
    if isinstance(axes, list) and axes:
        normalized: list[dict[str, str]] = []
        for index, axis in enumerate(axes, start=1):
            if not isinstance(axis, dict):
                continue
            axis_id = str(axis.get("id") or "").strip()
            name = str(axis.get("name") or axis.get("id") or f"Feature Slice {index}").strip()
            scope = str(axis.get("scope") or axis.get("feat_axis") or name).strip()
            feat_axis = str(axis.get("feat_axis") or name).strip()
            normalized.append({"id": axis_id, "name": name, "scope": scope, "feat_axis": feat_axis})
        if rollout_required and "adoption_e2e" in required_tracks and not any(axis_key(item) == "skill-adoption-e2e" for item in normalized):
            normalized.append(
                {
                    "id": "skill-adoption-e2e",
                    "name": "技能接入与跨 skill 闭环验证能力",
                    "scope": "定义现有 governed skill 的 onboarding、迁移切换与跨 skill E2E 验证边界，使治理主链的成立不依赖口头假设、组件内自测或一次性全仓切换。",
                    "feat_axis": "skill onboarding / migration cutover / cross-skill E2E validation",
                }
            )
        if normalized:
            return normalized[:8]

    scope_items = ensure_list(package.epic_json.get("scope"))
    if scope_items:
        normalized = []
        for index, item in enumerate(scope_items, start=1):
            title = item.split("：", 1)[0].strip(" -") or f"Feature Slice {index}"
            normalized.append({"id": "", "name": title, "scope": item, "feat_axis": item})
        return normalized[:8]

    title = str(package.epic_json.get("title") or package.run_id).strip()
    return [{"id": "", "name": f"{title} Core Capability", "scope": "Preserve the EPIC as one decomposable FEAT boundary.", "feat_axis": title}]


def derive_traceability(package: Any, feat_ref: str, axis: dict[str, str]) -> list[dict[str, Any]]:
    source_refs = bundle_source_refs(package)
    epic_ref = choose_epic_ref(package)
    return [
        {"feat_section": "Goal", "epic_fields": ["title", "business_goal"], "source_refs": [epic_ref] + source_refs[:3]},
        {"feat_section": "Scope", "epic_fields": ["scope", "capability_axes", "decomposition_rules"], "source_refs": [epic_ref, axis["name"]]},
        {"feat_section": "Constraints", "epic_fields": ["constraints_and_dependencies", "non_goals", "rollout_plan"], "source_refs": [epic_ref] + source_refs[:3]},
        {"feat_section": "Acceptance Checks", "epic_fields": ["acceptance_and_review", "decomposition_rules", "rollout_requirement"], "source_refs": [epic_ref, feat_ref]},
    ]


def build_feat_record(package: Any, axis: dict[str, str], index: int) -> dict[str, Any]:
    src_ref = choose_src_ref(package)
    epic_ref = choose_epic_ref(package)
    feat_ref = f"FEAT-{src_ref}-{index:03d}"
    source_refs = unique_strings([epic_ref, src_ref] + bundle_source_refs(package))
    return {
        "feat_ref": feat_ref,
        "title": axis["name"],
        "axis_id": axis_key(axis),
        "track": feat_track(axis),
        "derived_axis": axis.get("feat_axis"),
        "epic_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "source_refs": source_refs,
        "goal": feat_goal(axis, package),
        "scope": feat_scope(axis, package),
        "inputs": [
            f"Authoritative EPIC package {epic_ref}",
            f"src_root_id {package.epic_json.get('src_root_id')}",
            "Inherited scope, constraints, rollout requirements, and acceptance semantics",
        ],
        "processing": [
            "Translate the parent EPIC capability boundary into one independently acceptable FEAT slice with dedicated responsibility and boundary statements.",
            "Preserve parent-child traceability while separating this FEAT's concern from adjacent FEATs and rollout overlays.",
            "Emit FEAT-specific constraints and acceptance checks that can seed downstream delivery-prep and plan flows.",
        ],
        "outputs": [
            f"Frozen FEAT definition for {feat_ref}",
            "FEAT-specific acceptance checks for downstream TECH, TASK, and TESTSET derivation",
            "Traceable handoff metadata for delivery-prep and plan workflows",
        ],
        "dependencies": feat_dependencies(axis, package),
        "non_goals": feat_non_goals(axis, package),
        "constraints": feat_constraints(axis, package),
        "acceptance_checks": build_acceptance_checks(feat_ref, epic_ref, axis),
        "traceability": derive_traceability(package, feat_ref, axis),
    }


def feat_count_assessment(feats: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "feat_count": len(feats),
        "is_valid": len(feats) >= 2,
        "reason": "At least two FEAT slices were derived." if len(feats) >= 2 else "The EPIC decomposed into fewer than two FEATs.",
    }


def build_boundary_matrix(feats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for feat in feats:
        matrix.append(
            {
                "feat_ref": feat["feat_ref"],
                "title": feat["title"],
                "responsible_for": feat["scope"][:2],
                "not_responsible_for": feat["non_goals"][:2],
                "boundary_dependencies": feat["dependencies"],
                "acceptance_focus": [check["scenario"] for check in feat["acceptance_checks"][:3]],
            }
        )
    return matrix


def derive_bundle_intent(package: Any, feats: list[dict[str, Any]]) -> str:
    epic_ref = choose_epic_ref(package)
    axis_titles = "、".join(feat["title"] for feat in feats)
    rollout_required = bool((package.epic_json.get("rollout_requirement") or {}).get("required"))
    if rollout_required:
        return (
            f"Decompose {epic_ref} into {len(feats)} complementary FEAT slices so that foundation capability axes and adoption/E2E landing work "
            f"are both explicit. The bundle keeps {axis_titles} as independently acceptable FEATs, because the parent EPIC now requires both "
            "capability construction and real governed-skill landing. Fewer FEATs would collapse foundation and adoption concerns together, "
            "while more FEATs would prematurely drift into TASK or implementation detail."
        )
    return (
        f"Decompose {epic_ref} into {len(feats)} complementary FEAT slices so that each capability axis owns a distinct acceptance surface and can "
        f"be inherited downstream without overlap. The bundle keeps {axis_titles} as independently acceptable FEATs; fewer FEATs would merge "
        "incompatible acceptance semantics, while more FEATs would prematurely split into task or implementation detail."
    )
