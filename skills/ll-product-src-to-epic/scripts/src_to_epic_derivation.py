#!/usr/bin/env python3
"""
Derivation helpers for the lite-native src-to-epic runtime.
"""

from __future__ import annotations

from typing import Any

from src_to_epic_common import ensure_list, guess_repo_root_from_input, shorten_identifier, summarize_text, unique_strings


ROLLOUT_KEYWORD_GROUPS = {
    "shared_runtime_or_governance_change": [
        "governance",
        "gateway",
        "registry",
        "audit",
        "external gate",
        "path policy",
        "formal materialization",
        "主链",
        "统一治理",
        "受管",
    ],
    "requires_existing_skill_migration": [
        "skill",
        "workflow",
        "consumer",
        "producer",
        "迁移",
        "接入",
        "rollout",
        "adoption",
        "onboarding",
    ],
    "effectiveness_depends_on_real_skill_integration": [
        "managed read",
        "formal reference",
        "handoff",
        "dispatch",
        "不得重新发明等价规则",
        "统一继承",
        "旁路",
        "consumer",
    ],
    "requires_cross_skill_e2e_validation": [
        "e2e",
        "cross-skill",
        "human gate",
        "repair",
        "follow-up",
        "dispatch",
        "handoff",
        "downstream",
        "上下游",
    ],
}


def choose_src_root_id(package: Any) -> str:
    existing = package.src_candidate.get("src_root_id")
    if existing:
        return str(existing)
    return f"SRC-{shorten_identifier(package.run_id, limit=64)}"


def is_governance_bridge_package(package: Any) -> bool:
    source_kind = str(package.src_candidate.get("source_kind") or "")
    title = str(package.src_candidate.get("title") or "")
    constraints_text = " ".join(ensure_list(package.src_candidate.get("key_constraints")))
    return source_kind == "governance_bridge_src" or any(
        marker in f"{title} {constraints_text}"
        for marker in ["gate", "handoff", "formal", "双会话双队列", "文件化"]
    )


def uses_adr005_prerequisite(package: Any) -> bool:
    refs = {item.upper() for item in ensure_list(package.src_candidate.get("source_refs"))}
    bridge = package.src_candidate.get("bridge_context") or {}
    bridge_text = " ".join(ensure_list(bridge.get("governance_objects")) + ensure_list(package.src_candidate.get("in_scope")))
    return is_governance_bridge_package(package) and (
        "ADR-005" in refs
        or ({"ADR-001", "ADR-003", "ADR-006"}.issubset(refs) and any(token in bridge_text for token in ["路径", "IO", "artifact", "目录"]))
    )


def prerequisite_foundations(package: Any) -> list[str]:
    if not uses_adr005_prerequisite(package):
        return []
    return [
        "ADR-005 作为主链文件 IO / 路径治理前置基础，要求在本 EPIC 启动前已交付或已可稳定复用。",
        "本 EPIC 只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力，不在本 EPIC 内重新实现这些模块。",
    ]


def epic_source_refs(package: Any, src_root_id: str, architecture_refs: list[str]) -> list[str]:
    base = [f"product.raw-to-src::{package.run_id}", src_root_id] + ensure_list(package.src_candidate.get("source_refs")) + architecture_refs
    return unique_strings(base + (["ADR-005"] if uses_adr005_prerequisite(package) else []))


def derive_capability_axes(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, str]]:
    if is_governance_bridge_package(package):
        axes = [
            {
                "id": "collaboration-loop",
                "name": "主链协作闭环能力",
                "scope": "定义 execution loop、gate loop、human loop 在 governed skill 主链中的协作责任、交接界面与回流边界，使不同 FEAT 不再各自重写等价 loop 规则。",
                "feat_axis": "主链候选交接提交流",
            },
            {
                "id": "handoff-formalization",
                "name": "正式交接与物化能力",
                "scope": "统一 handoff、gate decision、formal materialization 的正式推进链路，使 candidate 到 formal 的升级路径可以被下游稳定继承。",
                "feat_axis": "主链 gate 审核与裁决流",
            },
            {
                "id": "object-layering",
                "name": "对象分层与准入能力",
                "scope": "固定 candidate package、formal object 与 downstream consumption 的层级规则、准入条件和引用约束，防止业务 skill 再次混入裁决职责。",
                "feat_axis": "formal 物化与下游准入流",
            },
            {
                "id": "artifact-io-governance",
                "name": "主链文件 IO 与路径治理能力",
                "scope": "定义主链如何接入 ADR-005 已提供的文件 IO / 路径治理能力，约束交接对象的 IO 入口、出口、物化落点与引用稳定性，只覆盖 handoff、formal materialization 与 governed skill IO，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。" if uses_adr005_prerequisite(package) else "约束主链交接对象的 IO 入口、出口、物化落点与引用稳定性，只覆盖 handoff、formal materialization 与 governed skill IO，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。",
                "feat_axis": "主链受治理 IO 落盘流",
            },
        ]
        if rollout_requirement and rollout_requirement.get("required"):
            axes.append(
                {
                    "id": "skill-adoption-e2e",
                    "name": "技能接入与跨 skill 闭环验证能力",
                    "scope": "定义现有 governed skill 的 onboarding、迁移切换与跨 skill E2E 验证边界，使治理主链的成立不依赖口头假设、组件内自测或一次性全仓切换。",
                    "feat_axis": "governed skill 接入与 pilot 闭环流",
                }
            )
        return axes

    in_scope = ensure_list(package.src_candidate.get("in_scope"))
    title = str(package.src_candidate.get("title") or package.run_id)
    axes: list[dict[str, str]] = []
    for index, item in enumerate(in_scope[:4], start=1):
        axes.append(
            {
                "id": f"axis-{index}",
                "name": f"{title} 能力包 {index}",
                "scope": item,
                "feat_axis": item,
            }
        )
    if not axes:
        axes.append(
            {
                "id": "axis-1",
                "name": f"{title} 核心能力包",
                "scope": "围绕上游问题空间形成一个可继续拆分的能力边界。",
                "feat_axis": "核心能力拆分",
            }
        )
    return axes


def derive_product_behavior_slices(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if is_governance_bridge_package(package):
        slices: list[dict[str, Any]] = [
            {
                "id": "collaboration-loop",
                "name": "主链候选提交与交接流",
                "track": "foundation",
                "goal": "冻结 governed skill 如何把 candidate package 提交为 authoritative handoff，并把候选交接正式送入 gate 消费链。",
                "scope": [
                    "定义 candidate package、proposal、evidence 在什么触发场景下被提交。",
                    "定义提交后形成什么 authoritative handoff object。",
                    "定义提交完成后对上游和 gate 分别暴露什么业务结果。",
                ],
                "product_surface": "候选提交流：governed skill 提交 candidate package 并形成 authoritative handoff submission",
                "completed_state": "上游 workflow 已明确看到一次正式提交完成，gate 已接管 handoff，待审批状态与回流边界都对上游可见。",
                "business_deliverable": "给 gate 使用的 authoritative handoff submission，以及给上游 workflow 可见的提交完成结果。",
                "capability_axes": ["主链协作闭环能力"],
                "overlay_families": [],
            },
            {
                "id": "handoff-formalization",
                "name": "主链 gate 审核与裁决流",
                "track": "foundation",
                "goal": "冻结 gate 如何审核 candidate、形成单一 decision object，并把结果明确返回 execution 或 formal 发布链。",
                "scope": [
                    "定义 approve / revise / retry / handoff / reject 的业务语义和输出物。",
                    "定义每种裁决的返回去向和对上游的业务结果。",
                    "定义 decision object 如何成为后续 formal 发布的唯一触发来源。",
                ],
                "product_surface": "审批裁决流：gate 审核 handoff 并输出 authoritative decision result",
                "completed_state": "一次 gate 审核已经结束，reviewer 给出单一 authoritative decision result，上游知道应回流、终止还是进入 formal 发布。",
                "business_deliverable": "给 execution 或 formal 发布链消费的 authoritative decision result，以及给 reviewer 可追溯的裁决结果。",
                "capability_axes": ["正式交接与物化能力", "主链协作闭环能力"],
                "overlay_families": [],
            },
            {
                "id": "object-layering",
                "name": "formal 发布与下游准入流",
                "track": "foundation",
                "goal": "冻结 approved decision 之后如何形成 formal output、formal ref 与 lineage，并让下游只通过正式准入链消费。",
                "scope": [
                    "定义 approved decision 之后的 formal 发布动作和 formal output 完成态。",
                    "定义 formal ref / lineage 如何成为 authoritative downstream input。",
                    "定义 consumer admission 边界，阻止 candidate 或旁路对象被正式消费。",
                ],
                "product_surface": "formal 发布与准入流：approved decision 发布成 formal package 并供 consumer 准入",
                "completed_state": "formal publication package 已形成且被 admission 链认可，下游 consumer 只会拿到 formal input，不会再把 candidate 当成正式结果。",
                "business_deliverable": "给 downstream consumer 正式消费的 formal publication package，以及可验证的 admission result。",
                "capability_axes": ["对象分层与准入能力", "正式交接与物化能力"],
                "overlay_families": [],
            },
            {
                "id": "artifact-io-governance",
                "name": "主链受治理 IO 落盘与读取流",
                "track": "foundation",
                "goal": "冻结主链业务动作在什么时候必须 governed write/read，以及这些正式读写会为业务方留下什么 authoritative receipt 和 managed ref。",
                "scope": [
                    "定义 handoff、decision、formal output、evidence 的正式读写动作。",
                    "定义业务调用点、正式 receipt / registry record 和 managed ref。",
                    "定义被拒绝读写时对业务方可见的失败表现。",
                ],
                "product_surface": "受治理落盘流：正式 write/read 生成 managed ref 与 authoritative receipt",
                "completed_state": "正式业务读写都留下 governed receipt / managed ref，调用方能知道对象写到哪里、为什么可读，失败不会静默旁路。",
                "business_deliverable": "给业务动作发起方返回的 governed write/read result，以及可审计的 managed ref / receipt。",
                "capability_axes": ["主链文件 IO 与路径治理能力"],
                "overlay_families": [],
            },
        ]
        if rollout_requirement and rollout_requirement.get("required"):
            slices.append(
                {
                    "id": "skill-adoption-e2e",
                    "name": "governed skill 接入与 pilot 验证流",
                    "track": "adoption_e2e",
                    "goal": "冻结 governed skill 的 onboarding、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。",
                    "scope": [
                        "定义哪些 governed skill 先接入以及 scope 外对象如何处理。",
                        "定义 pilot 主链如何选定、扩围和形成真实 evidence。",
                        "定义 cutover / fallback 如何判断，以及 adoption 成立需要交付哪些真实 evidence。",
                    ],
                    "product_surface": "接入验证流：governed skill 通过 pilot / cutover / fallback 接入主链",
                    "completed_state": "至少一条真实 pilot 链已完成验证，rollout owner 能看到 integration matrix、pilot evidence 和 cutover / fallback 决策结果。",
                    "business_deliverable": "给 rollout owner 使用的 onboarding / pilot / cutover package，以及真实链路 evidence。",
                    "capability_axes": ["技能接入与跨 skill 闭环验证能力"],
                    "overlay_families": ["skill_onboarding", "migration_cutover", "cross_skill_e2e_validation"],
                }
            )
        return slices
    axes = derive_capability_axes(package, rollout_requirement)
    derived: list[dict[str, Any]] = []
    for axis in axes:
        derived.append(
            {
                "id": str(axis.get("id") or ""),
                "name": str(axis.get("feat_axis") or axis.get("name") or ""),
                "track": "foundation",
                "goal": f"冻结 {axis.get('feat_axis') or axis.get('name')} 这一产品行为切片。",
                "scope": str(axis.get("scope") or axis.get("feat_axis") or axis.get("name") or ""),
                "product_surface": str(axis.get("feat_axis") or axis.get("name") or "产品切片"),
                "completed_state": "该切片对应的产品行为已形成可验收、可交接的业务结果。",
                "business_deliverable": str(axis.get("feat_axis") or axis.get("name") or "产品交付物"),
                "capability_axes": [str(axis.get("name") or axis.get("feat_axis") or "")],
                "overlay_families": [],
            }
        )
    return derived


def derive_epic_title(package: Any) -> str:
    if is_governance_bridge_package(package):
        return "主链正式交接与治理闭环统一能力"
    title = str(package.src_candidate.get("title") or package.run_id).strip()
    if "EPIC" in title.upper():
        return title
    return f"{title} 统一能力"


def choose_epic_freeze_ref(package: Any) -> str:
    base = derive_epic_title(package)
    slug = shorten_identifier(str(base), limit=44)
    if slug == "UNSPECIFIED":
        slug = shorten_identifier(package.run_id, limit=44)
    return f"EPIC-{slug}"


def derive_business_goal(
    package: Any,
    capability_axes: list[dict[str, str]],
    product_behavior_slices: list[dict[str, Any]] | None = None,
) -> str:
    if is_governance_bridge_package(package):
        slice_names = "、".join(str(item.get("name") or "") for item in (product_behavior_slices or [])[:5])
        return (
            "本 EPIC 的核心不是再按 loop、handoff、formalization、IO 这些治理轴分别建规则，"
            "而是把主链闭环冻结成一组连续的产品行为切片。"
            f"下游 FEAT 需要直接围绕 {slice_names} 这些切片定义产品界面、完成态和业务成品，"
            "而不是继续复述 SRC 原则或把产品定义下沉给 TECH。"
        )
    business_drivers = ensure_list(package.src_candidate.get("business_drivers"))
    problem_statement = str(package.src_candidate.get("problem_statement") or "")
    if business_drivers:
        return business_drivers[0]
    return summarize_text(problem_statement, limit=260)


def derive_business_value_problem(package: Any) -> list[str]:
    problem_statement = str(package.src_candidate.get("problem_statement") or "").strip()
    business_drivers = ensure_list(package.src_candidate.get("business_drivers"))
    trigger_scenarios = ensure_list(package.src_candidate.get("trigger_scenarios"))
    if is_governance_bridge_package(package):
        items = [
            "当前主链的 loop、handoff runtime、gate decision 与 formal publish 仍分散定义。若继续按局部规则理解，下游会把同一条主链拆成多个互不对齐的产品流程。",
            business_drivers[0] if business_drivers else "需要先冻结主链的统一产品行为，再让下游围绕可交付的 FEAT 切片继续设计，而不是继续各自补产品定义。",
            f"关键触发场景：{trigger_scenarios[0]}" if trigger_scenarios else "关键触发场景：当 governed skill 需要提交 candidate、接受 gate 裁决并形成 formal downstream input 时。",
        ]
        return unique_strings([item for item in items if item])
    items = []
    if problem_statement:
        items.append(summarize_text(problem_statement, limit=240))
    items.extend(business_drivers[:2])
    if trigger_scenarios:
        items.append(f"关键触发场景：{trigger_scenarios[0]}")
    return unique_strings(items)[:4]


def derive_product_positioning(
    package: Any,
    capability_axes: list[dict[str, str]],
    product_behavior_slices: list[dict[str, Any]] | None = None,
) -> str:
    slice_names = "、".join(str(item.get("name") or "") for item in (product_behavior_slices or [])[:5])
    axis_names = "、".join(axis["name"] for axis in capability_axes[:5])
    if is_governance_bridge_package(package):
        return (
            "该 EPIC 位于主链产品行为层，承接上游 bridge SRC，对下定义一条从候选提交、gate 审核裁决、formal 发布与准入、"
            "受治理 IO 到 governed skill 接入验证的完整产品线。"
            f"它对外呈现的是 {slice_names} 这些可交付的产品流；{axis_names} 只作为这些产品流共享的 cross-cutting constraints 存在。"
        )
    title = str(package.src_candidate.get("title") or package.run_id).strip()
    return f"该 EPIC 位于 `{title}` 的产品能力层，负责承接上游问题空间并为下游 FEAT 提供统一的能力边界与分解基线。"


def derive_actors_and_roles(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, str]]:
    target_users = ensure_list(package.src_candidate.get("target_users"))
    actors: list[dict[str, str]] = []
    if is_governance_bridge_package(package):
        actors.extend(
            [
                {"role": "workflow / orchestration 设计者", "responsibility": "定义主链的产品行为边界、交接角色和下游继承关系。"},
                {"role": "governed skill 作者", "responsibility": "让业务 skill 在统一主链里提交 candidate、消费 decision，并遵守统一交接规则。"},
                {"role": "gate / reviewer / human loop 设计者", "responsibility": "定义正式裁决、revision / retry / reject 参与点和审核责任。"},
                {"role": "downstream consumer / audit 消费方", "responsibility": "消费 formal output、evidence 和审计链，而不是依赖候选对象或路径猜测。"},
            ]
        )
        if rollout_requirement and rollout_requirement.get("required"):
            actors.append({"role": "skill onboarding / rollout owner", "responsibility": "定义接入矩阵、迁移波次、pilot 范围与 fallback 规则。"})
        return actors
    for user in target_users[:4]:
        actors.append({"role": user, "responsibility": "作为该 EPIC 的主要业务参与角色之一，消费或推动该能力块。"})
    if not actors:
        actors.append({"role": "product stakeholder", "responsibility": "负责在上游问题空间和下游 FEAT 之间对齐能力边界。"})
    return actors


def derive_upstream_downstream(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[str]:
    lines = [
        f"Upstream：承接 `product.raw-to-src::{package.run_id}` 冻结后的 SRC 包，而不是原始需求或单个 ADR 原文。",
        "Downstream：产出一个可继续拆分为多个 FEAT 的单一主 EPIC，并交接给 `product.epic-to-feat`。",
    ]
    if is_governance_bridge_package(package):
        lines.extend(
            [
                "上游输入形态：统一继承源中的问题陈述、业务动因、治理对象和硬约束。",
                "下游消费形态：主链候选提交、gate 裁决、formal 物化、准入、IO 落盘与 governed skill 接入验证等产品级 FEAT 切片。",
            ]
        )
    if rollout_requirement and rollout_requirement.get("required"):
        lines.append("Rollout 约束：仍保持单一主 EPIC，但要求下游同时覆盖 foundation 与 adoption_e2e 两类 FEAT track。")
    return lines


def derive_scope(
    package: Any,
    capability_axes: list[dict[str, str]],
    product_behavior_slices: list[dict[str, Any]] | None = None,
) -> list[str]:
    if capability_axes:
        if is_governance_bridge_package(package):
            slice_scope = [
                f"产品行为切片：{item['name']}，对业务方交付 {str(item.get('business_deliverable') or item.get('product_surface') or item['name']).rstrip('。.') }。"
                for item in (product_behavior_slices or [])[:6]
            ]
            axis_names = "、".join(axis["name"] for axis in capability_axes[:6])
            return (
                ["统一上位产品能力：形成一条可被多 skill 共享继承的主链受治理交接闭环。"]
                + slice_scope
                + [f"Cross-cutting capability constraints：{axis_names}；这些能力轴只作为约束附着在上述产品行为切片上。"] 
            )
        return [f"{axis['name']}：{axis['scope']}" for axis in capability_axes[:6]]
    in_scope = ensure_list(package.src_candidate.get("in_scope"))
    governance_summary = ensure_list(package.src_candidate.get("governance_change_summary"))
    scope = list(in_scope) if in_scope else governance_summary[:4]
    return unique_strings([item for item in scope if item])[:8]


def derive_non_goals(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[str]:
    out_of_scope = ensure_list(package.src_candidate.get("out_of_scope"))
    bridge_non_goals = ensure_list((package.src_candidate.get("bridge_context") or {}).get("non_goals"))
    normalized: list[str] = []
    for item in unique_strings(out_of_scope + bridge_non_goals):
        if "ADR-005" in item and any(token in item for token in ("Gateway", "Path Policy", "Registry")):
            continue
        text = item.replace("本 SRC", "本 EPIC").replace("在本 SRC 中", "在本 EPIC 中")
        if text.startswith("不在本 EPIC 中") or text.startswith("本 EPIC 不负责") or text.startswith("不"):
            normalized.append(text)
        else:
            normalized.append(f"本 EPIC 不负责{text}")
    if rollout_requirement and rollout_requirement.get("required"):
        normalized.extend(
            [
                "本 EPIC 不要求一次性完成所有现有 governed skill 的全量迁移或全仓 cutover。",
                "本 EPIC 不要求覆盖所有 producer/consumer 组合场景，只要求在下游 FEAT 中显式定义 onboarding 范围、迁移波次和至少一条真实跨 skill pilot 主链。",
                "本 EPIC 不负责把 onboarding / migration_cutover 扩大为仓库级全局文件治理改造。",
            ]
        )
    if uses_adr005_prerequisite(package):
        normalized.append("本 EPIC 不重新实现 ADR-005 的 Gateway / Path Policy / Registry 模块，只消费其已交付能力。")
    return unique_strings(normalized)[:8]


def derive_success_metrics(package: Any, capability_axes: list[dict[str, str]], product_behavior_slices: list[dict[str, Any]] | None = None) -> list[str]:
    if is_governance_bridge_package(package):
        slice_names = "、".join(str(item["name"]) for item in (product_behavior_slices or [])[:5])
        return [
            f"下游 FEAT 能完整覆盖 {slice_names} 这些产品行为切片，且每个 FEAT 都对应独立可验收的产品完成态，而不是原则复述。",
            "candidate 提交、gate 裁决、formal 发布、下游准入与受治理 IO 的产品边界在下游 FEAT 层不再歧义，业务 skill、gate 与 formal publish 职责不再混层。",
            "至少一条 producer -> consumer -> audit -> gate pilot 主链可被真实验证，不再只停留在原则描述。",
            "至少一组 approved decision -> formal publish -> downstream admission 流程在真实 governed skill 链路中启用并保留证据。",
            "当 rollout_required 为 true 时，至少一组 adoption / cutover / fallback 策略被验证。",
            "下游 FEAT 必须产出可执行的 governed skill integration matrix、迁移波次规则与至少一条真实跨 skill pilot 闭环 evidence。",
            "治理主链是否成立，不以组件内自测为唯一依据，而以真实 producer / consumer 接入后的 handoff / gate / E2E 证据为准。",
        ]
    bridge_context = package.src_candidate.get("bridge_context") or {}
    acceptance_impact = ensure_list(bridge_context.get("acceptance_impact"))
    metrics = [f"下游验收指标：{item}" for item in acceptance_impact[:3]]
    if not metrics:
        metrics = [
            "下游 FEAT 拆分时无需重新回读原始问题空间即可理解 EPIC 边界。",
            "EPIC 追溯链能同时指向 raw-to-src 运行批次和上游源引用。",
            "EPIC scope 能拆成多个独立验收 FEAT，而不是单一实现任务。",
        ]
    return metrics


def derive_decomposition_rules(package: Any, capability_axes: list[dict[str, str]], product_behavior_slices: list[dict[str, Any]] | None = None) -> list[str]:
    rules = [
        "按独立验收的产品行为切片拆分 FEAT，不按实现顺序、能力轴名称或单一任务切分。",
        "每个下游 FEAT 都必须继承 src_root_id、epic_freeze_ref 和 authoritative source_refs。",
        "保留 business skill、handoff runtime、external gate 的职责分层，不得在 FEAT 层重新混层。",
    ]
    trigger_scenarios = ensure_list(package.src_candidate.get("trigger_scenarios"))
    if len(trigger_scenarios) >= 2:
        rules.append("优先将多个触发场景共享的主链能力放在同一 EPIC，下游再按场景或边界拆 FEAT。")
    if is_governance_bridge_package(package):
        rules.append("FEAT 的 primary decomposition unit 是产品行为切片；capability axes 只作为 cross-cutting constraints 保留，不直接等同于 FEAT。")
        rules.append("每个 FEAT 都必须冻结对业务方可见的产品界面、完成态和 authoritative deliverable，避免把产品定义下沉给 TECH。")
        rules.append("required_feat_families / rollout families 是 mandatory overlays，必须叠加到对应产品切片上，而不是替代主轴。")
        rules.append("涉及路径与目录治理的 FEAT 只能覆盖主链 handoff、formal materialization 与 governed skill IO 边界，不得外扩成全局文件治理。")
        if uses_adr005_prerequisite(package):
            rules.append("涉及主链文件 IO / 路径治理的 FEAT 只定义对 ADR-005 前置基础的接入与消费边界，不重新实现底层模块。")
    return unique_strings(rules)[:8]


def derive_constraint_groups(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    key_constraints = ensure_list(package.src_candidate.get("key_constraints"))
    source_refs = ensure_list(package.src_candidate.get("source_refs"))
    if is_governance_bridge_package(package):
        inherited_labels = {"QA test execution skill", "TestEnvironmentSpec", "TestCasePack 冻结", "ScriptPack 冻结", "合规与判定分层"}
        filtered_constraints = [item for item in key_constraints if item not in inherited_labels]
        epic_level_items = [
            "本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。",
            "主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。",
            "FEAT 的 primary decomposition unit 是产品行为切片；rollout families 是 mandatory cross-cutting overlays，需叠加到对应产品切片上，不替代主轴。",
            "主链文件 IO 与路径治理只覆盖交接对象的 IO 入口、出口、物化落点与引用稳定性，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。",
        ]
        if uses_adr005_prerequisite(package):
            epic_level_items.append("ADR-005 是主链文件 IO / 路径治理前置基础；本 EPIC 只消费其已交付能力，不重新实现 Gateway / Path Policy / Registry 模块。")
        if rollout_requirement and rollout_requirement.get("required"):
            epic_level_items.append("当 rollout_required 为 true 时，foundation 与 adoption_e2e 必须同时落成，并至少保留一条真实 producer -> consumer -> audit -> gate pilot 主链。")
        inherited_intro = "以下来源约束来自 authoritative SRC，downstream must preserve where applicable，但它们不重新定义本 EPIC 的 primary capability boundary。"
        inherited_items = unique_strings([inherited_intro] + filtered_constraints + ([f"Authoritative source refs: {', '.join(source_refs)}"] if source_refs else []) + [f"Upstream package: {package.artifacts_dir}"])
        downstream_items = [
            "下游 FEAT 不得改写 src_root_id、epic_freeze_ref 与 authoritative source_refs。",
            "下游 FEAT 不得把 EPIC 重新打平为上游 QA test execution 对象清单；source-level object constraints 只能附着到实际受其约束的 FEAT。",
            "candidate -> formal、loop / gate / handoff 分层与 acceptance semantics 必须继续保持可校验、可追溯。",
        ]
        return [
            {"name": "Epic-level constraints", "items": unique_strings(epic_level_items)},
            {"name": "Authoritative inherited constraints", "items": inherited_items},
            {"name": "Downstream preservation rules", "items": unique_strings(downstream_items)},
        ]
    structure_items: list[str] = []
    layering_items: list[str] = []
    formalization_items: list[str] = []
    remaining_items: list[str] = []
    for item in key_constraints:
        if any(token in item for token in ["双会话双队列", "execution loop", "gate loop", "human loop"]):
            structure_items.append(item)
        elif any(token in item for token in ["approve", "revise", "retry", "handoff", "reject", "materialization", "物化"]):
            formalization_items.append(item)
        elif any(token in item for token in ["candidate", "formal", "分层", "proposal", "evidence", "裁决"]):
            layering_items.append(item)
        elif "handoff runtime" in item:
            structure_items.append(item)
        else:
            remaining_items.append(item)
    if is_governance_bridge_package(package):
        layering_items.append("路径与目录治理仅限主链 handoff、formal materialization 与 governed skill IO 边界，不得扩展为全局文件治理。")
    groups = [
        {"name": "主链结构约束", "items": unique_strings(structure_items)},
        {"name": "职责分层约束", "items": unique_strings(layering_items)},
        {"name": "Formalization 约束", "items": unique_strings(formalization_items)},
        {
            "name": "来源与依赖约束",
            "items": unique_strings(
                remaining_items
                + ([f"Authoritative source refs: {', '.join(source_refs)}"] if source_refs else [])
                + [f"Upstream package: {package.artifacts_dir}"]
            ),
        },
    ]
    return [group for group in groups if group["items"]]


def flatten_constraint_groups(groups: list[dict[str, Any]]) -> list[str]:
    flattened: list[str] = []
    for group in groups:
        for item in group["items"]:
            flattened.append(f"{group['name']}：{item}")
    return flattened[:14]


def derive_validation_findings(
    package: Any,
    constraint_groups: list[dict[str, Any]],
    decomposition_rules: list[str],
    success_metrics: list[str],
) -> list[dict[str, Any]]:
    if not is_governance_bridge_package(package):
        return []
    findings: list[dict[str, Any]] = []
    group_map = {group["name"]: group["items"] for group in constraint_groups}
    required_groups = {"Epic-level constraints", "Authoritative inherited constraints", "Downstream preservation rules"}
    if not required_groups.issubset(group_map):
        findings.append({"severity": "P1", "title": "Constraint layers are not separated", "detail": "Governance EPIC must separate epic-level constraints, inherited source constraints, and downstream preservation rules."})
    epic_items = " ".join(group_map.get("Epic-level constraints", []))
    inherited_items = " ".join(group_map.get("Authoritative inherited constraints", []))
    source_level_markers = ["TestEnvironmentSpec", "TestCasePack", "ScriptPack", "skill.qa.test_exec_web_e2e", "skill.runner.test_e2e", "invalid_run", "acceptance_status"]
    source_text = " ".join(ensure_list(package.src_candidate.get("key_constraints")) + ensure_list(package.src_candidate.get("source_refs")))
    qa_source_detected = any(marker in source_text for marker in source_level_markers)
    if any(marker in epic_items for marker in source_level_markers):
        findings.append({"severity": "P1", "title": "Epic-level constraints still carry source object detail", "detail": "EPIC-level constraints must stay at capability-boundary level instead of repeating QA execution object rules."})
    if qa_source_detected and not any(marker in inherited_items for marker in source_level_markers):
        findings.append({"severity": "P1", "title": "Inherited source constraints are too thin", "detail": "Authoritative inherited constraints should preserve the source-level object rules where applicable."})
    if (
        not any("产品行为切片" in rule for rule in decomposition_rules)
        or not any("cross-cutting constraints" in rule for rule in decomposition_rules)
        or not any("mandatory overlays" in rule or "mandatory cross-cutting overlays" in rule for rule in decomposition_rules)
    ):
        findings.append({"severity": "P1", "title": "FEAT decomposition axis is still ambiguous", "detail": "The EPIC must explicitly define product behavior slices as primary, capability axes as cross-cutting constraints, and rollout families as mandatory overlays."})
    metrics_text = " ".join(success_metrics)
    for token, title, detail in [
        ("producer -> consumer -> audit -> gate", "Missing pilot-chain completion signal", "Success metrics should require at least one real producer -> consumer -> audit -> gate pilot chain."),
        ("formal publish", "Missing materialization completion signal", "Success metrics should require at least one real approved decision -> formal publish -> admission path."),
        ("adoption / cutover / fallback", "Missing rollout verification signal", "Success metrics should define rollout verification for adoption / cutover / fallback."),
    ]:
        if token not in metrics_text:
            findings.append({"severity": "P1", "title": title, "detail": detail})
    return findings


def derive_traceability(package: Any, src_root_id: str) -> list[dict[str, Any]]:
    source_refs = unique_strings(ensure_list(package.src_candidate.get("source_refs")) + (["ADR-005"] if uses_adr005_prerequisite(package) else []))
    return [
        {
            "epic_section": "Epic Intent",
            "input_fields": ["problem_statement", "trigger_scenarios", "business_drivers"],
            "source_refs": source_refs,
        },
        {
            "epic_section": "Business Value and Problem",
            "input_fields": ["problem_statement", "business_drivers", "trigger_scenarios"],
            "source_refs": source_refs,
        },
        {
            "epic_section": "Actors and Roles",
            "input_fields": ["target_users", "trigger_scenarios", "bridge_context.downstream_inheritance_requirements"],
            "source_refs": [src_root_id] + source_refs,
        },
        {
            "epic_section": "Capability Scope",
            "input_fields": ["in_scope", "governance_change_summary", "bridge_context.governance_objects"],
            "source_refs": [src_root_id] + source_refs,
        },
        {
            "epic_section": "Constraints and Dependencies",
            "input_fields": ["key_constraints", "bridge_context.downstream_inheritance_requirements"],
            "source_refs": [f"product.raw-to-src::{package.run_id}"] + source_refs,
        },
        {
            "epic_section": "Epic Success Criteria",
            "input_fields": ["business_drivers", "bridge_context.acceptance_impact", "trigger_scenarios"],
            "source_refs": [f"product.raw-to-src::{package.run_id}"] + source_refs,
        },
    ]


def derive_optional_architecture_refs(package: Any, src_root_id: str) -> list[str]:
    repo_root = guess_repo_root_from_input(package.artifacts_dir)
    architecture_dir = repo_root / "ssot" / "architecture"
    if not architecture_dir.exists():
        return []
    refs: list[str] = []
    for path in architecture_dir.glob(f"ARCH-{src_root_id}-*.md"):
        stem = path.stem
        if "__" in stem:
            refs.append(stem.split("__", 1)[0])
        else:
            refs.append(stem)
    return unique_strings(refs)


def multi_feat_score(package: Any) -> dict[str, Any]:
    scope_count = len(ensure_list(package.src_candidate.get("in_scope")))
    scenario_count = len(ensure_list(package.src_candidate.get("trigger_scenarios")))
    governance_object_count = len(ensure_list((package.src_candidate.get("bridge_context") or {}).get("governance_objects")))
    expected_downstream = ensure_list((package.src_candidate.get("bridge_context") or {}).get("expected_downstream_objects"))
    score = scope_count + scenario_count + governance_object_count + len(expected_downstream)
    reasons = [
        f"in_scope={scope_count}",
        f"trigger_scenarios={scenario_count}",
        f"governance_objects={governance_object_count}",
        f"expected_downstream_objects={len(expected_downstream)}",
    ]
    return {
        "score": score,
        "reasons": reasons,
        "is_multi_feat_ready": score >= 6 or (scope_count >= 2 and scenario_count >= 2),
    }


def _package_text_blob(package: Any) -> str:
    bridge = package.src_candidate.get("bridge_context") or {}
    fields = [
        package.src_candidate.get("title"),
        package.src_candidate.get("problem_statement"),
        *ensure_list(package.src_candidate.get("business_drivers")),
        *ensure_list(package.src_candidate.get("key_constraints")),
        *ensure_list(package.src_candidate.get("in_scope")),
        *ensure_list(package.src_candidate.get("governance_change_summary")),
        *ensure_list(package.src_candidate.get("trigger_scenarios")),
        *ensure_list(bridge.get("governance_objects")),
        *ensure_list(bridge.get("current_failure_modes")),
        *ensure_list(bridge.get("downstream_inheritance_requirements")),
        *ensure_list(bridge.get("acceptance_impact")),
    ]
    return " ".join(str(item).lower() for item in fields if item)


def assess_rollout_requirement(package: Any) -> dict[str, Any]:
    text_blob = _package_text_blob(package)
    governance_bridge = is_governance_bridge_package(package)
    triggers = {
        name: governance_bridge or any(keyword in text_blob for keyword in keywords)
        for name, keywords in ROLLOUT_KEYWORD_GROUPS.items()
    }
    score = sum(1 for status in triggers.values() if status)
    required = score >= 2 and (triggers["shared_runtime_or_governance_change"] or governance_bridge)
    rationale = []
    if triggers["shared_runtime_or_governance_change"]:
        rationale.append("SRC 涉及共享治理底座或共用运行时能力，而不是单一业务功能。")
    if triggers["requires_existing_skill_migration"]:
        rationale.append("功能真正生效依赖现有 skill / workflow 接入，而不是只完成底座建设。")
    if triggers["effectiveness_depends_on_real_skill_integration"]:
        rationale.append("效果判定依赖真实 producer / consumer 接入，不能只靠组件内自测证明。")
    if triggers["requires_cross_skill_e2e_validation"]:
        rationale.append("需要跨 skill E2E 或 handoff/gate 闭环验证，才能证明治理主链真的成立。")
    return {
        "required": required,
        "score": score,
        "triggers": triggers,
        "rationale": rationale,
    }


def derive_rollout_plan(package: Any, rollout_requirement: dict[str, Any]) -> dict[str, Any]:
    if not rollout_requirement.get("required"):
        return {
            "required_feat_tracks": ["foundation"],
            "required_feat_families": [],
            "planning_notes": ["当前 SRC 不需要单独的 adoption / rollout / E2E FEAT 族。"],
        }
    return {
        "required_feat_tracks": ["foundation", "adoption_e2e"],
        "required_feat_families": [
            {
                "family": "skill_onboarding",
                "goal": "建立现有 governed skill 的 integration matrix，明确 producer、consumer、gate consumer 与暂不接入对象。",
            },
            {
                "family": "migration_cutover",
                "goal": "定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界，而不是一次性全仓硬切。",
            },
            {
                "family": "cross_skill_e2e_validation",
                "goal": "至少选定一条真实 producer -> consumer -> audit -> gate 的 pilot 主链，并形成跨 skill E2E evidence。",
            },
        ],
        "planning_notes": [
            "rollout / adoption / E2E 不另起第二个 EPIC，而是在当前主 EPIC 内显式保留，并在 epic-to-feat 阶段强制拆出独立 FEAT 族。",
            "foundation FEAT 与 adoption/E2E FEAT 必须共享同一组 source_refs 和治理约束，不得形成并行真相。",
            "default-active 与 guarded/provisional 切面必须分层表达，避免未冻结 slice 被误当成已默认启用能力。",
        ],
    }
