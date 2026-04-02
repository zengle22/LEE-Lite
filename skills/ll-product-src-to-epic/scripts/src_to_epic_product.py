from typing import Any

from src_to_epic_identity import (
    choose_src_root_id,
    is_review_projection_package,
    is_execution_runner_package,
    is_governance_bridge_package,
    is_implementation_readiness_package,
    uses_adr005_prerequisite,
    operator_surface_names,
)
from src_to_epic_common import shorten_identifier, ensure_list, unique_strings, summarize_text


def derive_epic_title(package: Any) -> str:
    if is_review_projection_package(package):
        return "Gate 审核投影视图与 SSOT 回写统一能力"
    if is_execution_runner_package(package):
        return "Gate 审批后自动推进 Execution Runner 统一能力"
    if is_implementation_readiness_package(package):
        return "IMPL 实施前文档压力测试与 Implementation Readiness 统一能力"
    if is_governance_bridge_package(package):
        return "主链正式交接与治理闭环统一能力"
    title = str(package.src_candidate.get("title") or package.run_id).strip()
    if "EPIC" in title.upper():
        return title
    return f"{title} 统一能力"


def choose_epic_freeze_ref(package: Any) -> str:
    src_root_id = choose_src_root_id(package)
    if src_root_id.upper().startswith("SRC-") and src_root_id[4:].isdigit():
        return f"EPIC-{src_root_id}-001"
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
    if is_review_projection_package(package):
        slice_names = "、".join(str(item.get("name") or "") for item in (product_behavior_slices or [])[:4])
        return (
            "本 EPIC 的核心不是扩张新的治理 runtime，而是把 Machine SSOT 在 gate 阶段翻译成稳定的人类审核视图。"
            f"下游 FEAT 需要围绕 {slice_names} 这些审核视图能力冻结产品界面、完成态和回写边界，"
            "并始终保持 Projection 只是 derived-only review artifact。"
        )
    if is_execution_runner_package(package):
        slice_names = "、".join(str(item.get("name") or "") for item in (product_behavior_slices or [])[:4])
        return (
            "本 EPIC 的核心不是把 approve 改写成 formal publication，而是把 gate 批准后的自动推进运行时冻结成连续产品行为。"
            f"下游 FEAT 需要围绕 {slice_names} 这些切片定义 approve 后的 ready job、runner 消费、next-skill dispatch 和 execution result 回写。"
        )
    if is_implementation_readiness_package(package):
        slice_names = "、".join(str(item.get("name") or "") for item in (product_behavior_slices or [])[:4])
        return (
            "本 EPIC 的核心不是新增第二层技术设计，也不是直接执行代码或测试，"
            "而是把 implementation start 前的文档压力测试冻结成连续产品能力。"
            f"下游 FEAT 需要围绕 {slice_names} 这些切片定义 intake、跨文档评审、失败路径推演和 readiness verdict。"
        )
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
    if is_review_projection_package(package):
        items = [
            problem_statement or "当前 Machine SSOT 结构对 AI 友好，但 gate 审核阶段的人类需要自己拼装产品主线、交付物和边界，审核成本高且容易漏判。",
            business_drivers[0] if business_drivers else "需要在不污染 SSOT 本体的前提下，为 gate 审核生成一份固定模板的人类友好 Projection。",
            "如果 Projection 不能稳定保留 authoritative snapshot、review focus 和 writeback 边界，人类就会把 narrative 误当成新的真相源。",
        ]
        return unique_strings([item for item in items if item])
    if is_execution_runner_package(package):
        items = [
            problem_statement or "dispatch 已能产出 materialized-job，但系统仍缺少正式 consumer 去自动消费 artifacts/jobs/ready 并推进到下一个 skill。",
            business_drivers[0] if business_drivers else "需要把 gate approve 与下一 skill 自动推进重新绑回同一条运行时链，而不是让 approve 停在 formal publication 或人工接力。",
            f"关键触发场景：{trigger_scenarios[0]}" if trigger_scenarios else "关键触发场景：当 gate approve 之后需要自动推进到下一个 governed skill 时。",
        ]
        return unique_strings([item for item in items if item])
    if is_implementation_readiness_package(package):
        items = [
            problem_statement or "当前 IMPL 在 implementation start 前仍缺独立的实施前文档压力测试能力，AI 容易在歧义输入下实现出另一套系统。",
            business_drivers[0] if business_drivers else "需要把 implementation readiness 从零散 review 提升成正式产品能力，让 gate、reviewer 和 implementation consumer 稳定消费。",
            f"关键触发场景：{trigger_scenarios[0]}" if trigger_scenarios else "关键触发场景：当 feature_impl_candidate_package 已生成并准备进入 implementation start 时。",
        ]
        return unique_strings([item for item in items if item])
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
    if is_review_projection_package(package):
        return (
            "该 EPIC 位于 gate 审核视图层，承接上游 Machine SSOT，对下定义一套稳定的人类审核 Projection 能力。"
            "它服务 reviewer 的快速理解与判断，但不改变 SSOT 作为唯一权威源的地位。"
        )
    if is_execution_runner_package(package):
        return (
            "该 EPIC 位于 gate 后自动推进运行时层，承接上游 bridge SRC，"
            "对下定义一条从 approve 后 ready job 生成、runner 自动取件、next-skill dispatch 到 execution result 回写的完整产品线。"
            f"它对外呈现的是 {slice_names} 这些可交付的自动推进产品流；{axis_names} 只作为这些产品流共享的 cross-cutting constraints 存在。"
        )
    if is_implementation_readiness_package(package):
        return (
            "该 EPIC 位于 implementation start 前的 readiness 产品能力层，承接上游 implementation-readiness SRC，"
            "对下定义一条从 IMPL intake、跨文档一致性评审、失败路径推演到 readiness verdict 与修复路由的完整产品线。"
            f"它对外呈现的是 {slice_names} 这些可交付的 readiness 产品流；{axis_names} 只作为这些产品流共享的 cross-cutting constraints 存在。"
        )
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
    if is_review_projection_package(package):
        actors.extend(
            [
                {"role": "gate reviewer", "responsibility": "消费 Human Review Projection，快速理解产品形态、主流程、交付物和边界，并给出审核判断。"},
                {"role": "SSOT owner", "responsibility": "维护 Machine SSOT 作为唯一权威源，并接收来自 Projection 的修订意见回写。"},
                {"role": "projection generator", "responsibility": "从最新 SSOT 稳定生成 Projection、Authoritative Snapshot、Review Focus 和风险提示。"},
                {"role": "downstream designer", "responsibility": "继续只继承 Machine SSOT，而不是直接继承 Projection。"},
            ]
        )
        return actors
    if is_execution_runner_package(package):
        actors.extend(
            [
                {"role": "gate / reviewer owner", "responsibility": "定义 approve 与非 approve 决策何时产生 ready execution job。"},
                {"role": "execution runner owner", "responsibility": "负责 ready queue 消费、claim 语义、dispatch 与结果回写。"},
                {"role": "downstream governed skill owner", "responsibility": "消费 authoritative runner invocation，而不是等待人工接力。"},
                {"role": "workflow / orchestration 设计者", "responsibility": "保持 gate approve、job queue、runner 和 next skill 之间的单一路径。"},
            ]
        )
        if operator_surface_names(package, "cli_control_surface"):
            actors.append({"role": "Claude/Codex CLI operator", "responsibility": "通过 runner skill 入口和 CLI control surface 启动、恢复、控制 execution loop。"})
        if operator_surface_names(package, "monitor_surface"):
            actors.append({"role": "workflow / orchestration operator", "responsibility": "通过 runner observability surface 观察 ready backlog、running、failed、deadletters 与 waiting-human 状态。"})
        return actors
    if is_implementation_readiness_package(package):
        actors.extend(
            [
                {"role": "implementation reviewer", "responsibility": "在 implementation start 前消费 readiness report 并判断是否允许继续。"},
                {"role": "AI coder / tester", "responsibility": "消费主测试对象、authority、修复目标和 verdict，而不是自行补出新的 truth。"},
                {"role": "workflow / orchestration 设计者", "responsibility": "保持 readiness 流程与 implementation start、external gate、downstream consumer 的职责边界。"},
                {"role": "upstream artifact owner", "responsibility": "根据 repair_target_artifact 接收修订任务并更新 FEAT / TECH / ARCH / API / UI / TESTSET / IMPL。"},
            ]
        )
        return actors
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
    if is_execution_runner_package(package):
        lines.extend(
            [
                "上游输入形态：关于 gate approve 后自动推进缺口的 bridge SRC，而不是 formal publication/admission 产品线定义。",
                "下游消费形态：ready job emission、runner intake、next-skill dispatch、execution result feedback 等自动推进 FEAT 切片。",
            ]
        )
        return lines
    if is_implementation_readiness_package(package):
        lines.extend(
            [
                "上游输入形态：关于 implementation start 前 readiness 压力测试的 bridge SRC，而不是具体代码实现或 TECH 方案本体。",
                "下游消费形态：IMPL intake、cross-artifact consistency、counterexample simulation、readiness verdict 与 repair routing 等 FEAT 切片。",
            ]
        )
        return lines
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
        if is_review_projection_package(package):
            slice_scope = [
                f"产品行为切片：{item['name']}，对审核人交付 {str(item.get('business_deliverable') or item.get('product_surface') or item['name']).rstrip('。.')}。"
                for item in (product_behavior_slices or [])[:6]
            ]
            axis_names = "、".join(axis["name"] for axis in capability_axes[:6])
            return (
                ["统一上位产品能力：在 gate 阶段生成 Human Review Projection，并保持 SSOT 仍是唯一权威源。"]
                + slice_scope
                + [f"Cross-cutting capability constraints：{axis_names}；这些能力轴只作为审核视图约束附着在上述产品行为切片上。"]
            )
        if is_execution_runner_package(package):
            slice_scope = [
                f"产品行为切片：{item['name']}，对业务方交付 {str(item.get('business_deliverable') or item.get('product_surface') or item['name']).rstrip('。.')}。"
                for item in (product_behavior_slices or [])[:8]
            ]
            axis_names = "、".join(axis["name"] for axis in capability_axes[:8])
            return (
                ["统一上位产品能力：形成一条 gate approve 后自动推进到下一 skill 的运行时产品线。"]
                + slice_scope
                + [f"Cross-cutting capability constraints：{axis_names}；这些能力轴只作为约束附着在上述产品行为切片上。"]
            )
        if is_implementation_readiness_package(package):
            slice_scope = [
                f"产品行为切片：{item['name']}，对业务方交付 {str(item.get('business_deliverable') or item.get('product_surface') or item['name']).rstrip('。.')}。"
                for item in (product_behavior_slices or [])[:6]
            ]
            axis_names = "、".join(axis["name"] for axis in capability_axes[:6])
            return (
                ["统一上位产品能力：形成一条 implementation start 前可被多方稳定消费的 readiness 产品线。"]
                + slice_scope
                + [f"Cross-cutting capability constraints：{axis_names}；这些能力轴只作为约束附着在上述产品行为切片上。"]
            )
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
    if is_review_projection_package(package):
        normalized.extend(
            [
                "本 EPIC 不把 Projection 变成新的真相源或新的下游继承输入。",
                "本 EPIC 不定义 handoff orchestration、formal publication、governed IO 或 skill onboarding runtime。",
                "本 EPIC 不要求把 SSOT 本体改写成同时面向 AI 和人类的混合文档。",
                "本 EPIC 不允许审核意见只停留在 Projection 上而不回写 Machine SSOT。",
            ]
        )
        return unique_strings(normalized)[:8]
    if is_execution_runner_package(package):
        normalized.extend(
            [
                "本 EPIC 不把 approve 重写成 formal publication、admission 或 publish-only 终态。",
                "本 EPIC 不要求第三会话人工接力作为正常自动推进路径。",
                "本 EPIC 不扩张成重型调度平台、事件总线或仓库级通用执行器设计。",
                "本 EPIC 不把 runner intake 替换成目录扫描、路径猜测或临时脚本调用。",
            ]
        )
        return unique_strings(normalized)[:8]
    if is_implementation_readiness_package(package):
        normalized.extend(
            [
                "本 EPIC 不新增第二层技术设计 truth，也不替代 FEAT / TECH / ARCH / API / UI / TESTSET / IMPL 的权威边界。",
                "本 EPIC 不直接执行代码、跑真实测试或替代 external gate 的最终审批职责。",
                "本 EPIC 不把 implementation readiness 降级为纯文档 lint 或格式检查器。",
            ]
        )
        return unique_strings(normalized)[:8]
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
    if is_review_projection_package(package):
        slice_names = "、".join(str(item["name"]) for item in (product_behavior_slices or [])[:4])
        return [
            f"下游 FEAT 能完整覆盖 {slice_names} 这些审核视图能力切片，且每个 FEAT 都对应独立可验收的产品完成态。",
            "gate 审核时，人类无需自行拼装主线就能理解产品摘要、主流程、关键交付物和 authoritative snapshot。",
            "Projection 始终被标记为 derived-only / non-authoritative / non-inheritable，下游继续只依赖 Machine SSOT。",
            "审核意见能稳定回写 SSOT，并在 SSOT 更新后重新生成 Projection，不产生第二真相源。",
        ]
    if is_execution_runner_package(package):
        slice_names = "、".join(str(item["name"]) for item in (product_behavior_slices or [])[:4])
        return [
            f"下游 FEAT 能完整覆盖 {slice_names} 这些自动推进产品切片，而不是把 approve 后流程改写成 formal publication / admission。",
            "至少一条 gate approve -> ready execution job -> runner claim -> next skill invocation 的真实链路可被验证。",
            "ready queue、runner ownership、next-skill dispatch 与 execution outcome 的职责边界不再依赖人工接力。",
            "失败、重试和回流仍保持 execution 语义，而不是在 approve 之后丢失运行时状态。",
        ]
    if is_implementation_readiness_package(package):
        slice_names = "、".join(str(item["name"]) for item in (product_behavior_slices or [])[:4])
        return [
            f"下游 FEAT 能完整覆盖 {slice_names} 这些 readiness 产品切片，而不是把能力塌缩成单一 review 步骤。",
            "至少一条 IMPL intake -> cross-artifact consistency review -> counterexample simulation -> readiness verdict -> repair routing 的链路可被验证。",
            "主测试对象、authority non-override、deep mode 触发、score-to-verdict 与 repair_target_artifact 在下游 FEAT 层不再歧义。",
            "implementation consumer 可在不回读 ADR 的前提下理解能否开工、哪里要修、以及修复责任落点。",
        ]
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
    ]
    trigger_scenarios = ensure_list(package.src_candidate.get("trigger_scenarios"))
    if len(trigger_scenarios) >= 2:
        rules.append("优先将多个触发场景共享的主链能力放在同一 EPIC，下游再按场景或边界拆 FEAT。")
    if is_review_projection_package(package):
        rules.append("FEAT 的 primary decomposition unit 是 Projection 生成、Snapshot 提取、Review Focus/Risk 提示和反馈回写这些审核视图切片。")
        rules.append("每个 FEAT 都必须显式回答它如何帮助 reviewer 在 gate 做判断，以及如何保持 Projection 不是新的真相源。")
        rules.append("禁止任何 FEAT 把能力扩张成 handoff orchestration、formal publication、governed IO 或 skill onboarding runtime。")
        rules.append("所有 Projection 修改意见都必须回写 Machine SSOT，再重新生成 Projection。")
        return unique_strings(rules)[:8]
    if is_execution_runner_package(package):
        rules.append("FEAT 的 primary decomposition unit 是 approve 后 ready job 生成、runner intake、next-skill dispatch 与 execution result feedback 这些自动推进切片。")
        rules.append("任何 FEAT 都不得把 approve 后链路重写成 formal publication、admission 或人工第三会话接力。")
        rules.append("下游 FEAT 必须保持 artifacts/jobs/ready、runner claim 和 next-skill invocation 之间的单一路径。")
        rules.append("失败、重试和回流必须保持 execution 语义，不得在 FEAT 层改写为 publish-only 状态。")
        return unique_strings(rules)[:8]
    if is_implementation_readiness_package(package):
        rules.append("FEAT 的 primary decomposition unit 是 IMPL intake、cross-artifact consistency review、counterexample simulation、readiness verdict / repair routing 这些产品行为切片。")
        rules.append("任何 FEAT 都不得把 implementation readiness 重写成第二层技术设计、代码实现计划或纯文档 lint。")
        rules.append("下游 FEAT 必须保持主测试对象优先级、authority non-override、deep mode 触发和 score-to-verdict 绑定的单一路径。")
        rules.append("repair_target_artifact 与 missing_information 必须留在产品级输出，而不是推迟到 TECH 层再补定义。")
        return unique_strings(rules)[:8]
    rules.append("保留 business skill、handoff runtime、external gate 的职责分层，不得在 FEAT 层重新混层。")
    if is_governance_bridge_package(package):
        rules.append("FEAT 的 primary decomposition unit 是产品行为切片；capability axes 只作为 cross-cutting constraints 保留，不直接等同于 FEAT。")
        rules.append("每个 FEAT 都必须冻结对业务方可见的产品界面、完成态和 authoritative deliverable，避免把产品定义下沉给 TECH。")
        rules.append("required_feat_families / rollout families 是 mandatory overlays，必须叠加到对应产品切片上，而不是替代主轴。")
        rules.append("涉及路径与目录治理的 FEAT 只能覆盖主链 handoff、formal materialization 与 governed skill IO 边界，不得外扩成全局文件治理。")
        if uses_adr005_prerequisite(package):
            rules.append("涉及主链文件 IO / 路径治理的 FEAT 只定义对 ADR-005 前置基础的接入与消费边界，不重新实现底层模块。")
    return unique_strings(rules)[:8]
