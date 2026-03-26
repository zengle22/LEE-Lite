#!/usr/bin/env python3
"""
Derivation helpers for the lite-native src-to-epic runtime.
"""

from __future__ import annotations

from typing import Any

from src_to_epic_common import (
    ensure_list,
    guess_repo_root_from_input,
    normalize_semantic_lock,
    shorten_identifier,
    summarize_text,
    unique_strings,
)


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


def semantic_lock(package: Any) -> dict[str, Any]:
    return normalize_semantic_lock(package.src_candidate.get("semantic_lock")) or {}


def is_review_projection_package(package: Any) -> bool:
    return str(semantic_lock(package).get("domain_type") or "").strip().lower() == "review_projection_rule"


def is_execution_runner_package(package: Any) -> bool:
    return str(semantic_lock(package).get("domain_type") or "").strip().lower() == "execution_runner_rule"


def is_governance_bridge_package(package: Any) -> bool:
    if is_review_projection_package(package) or is_execution_runner_package(package):
        return False
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
    if is_review_projection_package(package):
        return [
            {
                "id": "projection-generation",
                "name": "Gate Projection 生成能力",
                "scope": "在 gate 审核阶段，把机器优先 SSOT 渲染成人类友好的 Human Review Projection，并保持与 SSOT 的单向派生关系。",
                "feat_axis": "Human Review Projection 生成流",
            },
            {
                "id": "authoritative-snapshot",
                "name": "Authoritative Snapshot 摘要能力",
                "scope": "从 SSOT 提炼 completed state、authoritative output、frozen downstream boundary、open technical decisions，供人类快速校验权威约束。",
                "feat_axis": "Authoritative Snapshot 生成流",
            },
            {
                "id": "review-focus-risk",
                "name": "Review Focus 与风险提示能力",
                "scope": "从 SSOT 提取 review focus、risks、ambiguities，帮助审核人快速发现产品边界遗漏、歧义和责任下沉问题。",
                "feat_axis": "Review Focus 与风险提示流",
            },
            {
                "id": "feedback-writeback",
                "name": "Projection 批注回写能力",
                "scope": "把 gate 审核意见稳定回写到 Machine SSOT，并确保 Projection 只能重生成，不能变成新的真相源。",
                "feat_axis": "Projection 批注回写流",
            },
        ]
    if is_execution_runner_package(package):
        return [
            {
                "id": "ready-job-emission",
                "name": "批准后 Ready Job 生成能力",
                "scope": "把 gate approve 稳定映射成 ready execution job，而不是停在 formal publication 或人工接力。",
                "feat_axis": "approve 后 ready job 生成流",
            },
            {
                "id": "execution-runner-intake",
                "name": "Execution Runner 取件能力",
                "scope": "让 Execution Loop Job Runner 自动消费 artifacts/jobs/ready 中的 job，并形成唯一 claim / running 责任边界。",
                "feat_axis": "ready job 自动取件流",
            },
            {
                "id": "next-skill-dispatch",
                "name": "下游 Skill 自动派发能力",
                "scope": "把 claimed job 稳定推进到下一个 governed skill，并保留 authoritative refs、目标 skill 和输入边界。",
                "feat_axis": "next skill 自动派发流",
            },
            {
                "id": "execution-result-feedback",
                "name": "执行结果回写与重试边界能力",
                "scope": "把执行结果、重试回流与失败终止冻结成可审计的 runner 输出，而不是把 approve 当作终态。",
                "feat_axis": "执行结果回写流",
            },
        ]
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
    if is_review_projection_package(package):
        return [
            {
                "id": "projection-generation",
                "name": "Human Review Projection 生成流",
                "track": "foundation",
                "goal": "冻结 gate 审核阶段如何从 Machine SSOT 生成一份人类友好的 Projection，并保持 Projection 只是派生视图。",
                "scope": [
                    "定义 Projection 在什么 gate 触发点生成，以及输入只允许来自 Machine SSOT。",
                    "定义 Projection 必须包含的固定模板块，避免每次自由发挥。",
                    "定义 Projection 生成后如何标识 derived-only / non-authoritative / non-inheritable。",
                ],
                "product_surface": "Projection 生成流：从 Machine SSOT 派生一份 gate 审核可读视图",
                "completed_state": "审核人能看到一份由最新 SSOT 渲染的 Human Review Projection，且该视图明确不是新的真相源。",
                "business_deliverable": "给审核人使用的 Human Review Projection。",
                "capability_axes": ["Gate Projection 生成能力"],
                "overlay_families": [],
                "primary_actor": "projection generator",
                "secondary_actors": ["gate reviewer", "SSOT owner"],
                "user_story": "As a gate reviewer, I want a human-friendly Projection generated from the latest Machine SSOT, so that I can understand the product quickly without treating the view as a new source of truth.",
                "trigger": "当 Machine SSOT 进入 gate 审核阶段并需要给人类 reviewer 展示时。",
                "preconditions": ["Machine SSOT 已存在且处于可审核状态。", "gate 阶段已请求生成审核视图。"],
                "postconditions": ["Human Review Projection 已生成。", "Projection 被明确标记为 derived-only / non-authoritative / non-inheritable。"],
                "main_flow": [
                    "读取最新 Machine SSOT authoritative 内容。",
                    "按固定模板渲染产品摘要、角色摘要、主流程、关键交付物等审核视图块。",
                    "在 Projection 中显式标记其派生属性与非权威属性。",
                    "把 Projection 提供给 gate reviewer 使用。",
                ],
                "alternate_flows": ["当某些摘要块无法安全提取时，Projection 仍保留模板位置并显示 SSOT 字段不足提示。"],
                "exception_flows": ["若输入不是 freeze-ready 的 Machine SSOT，则拒绝生成 Projection。"],
                "business_rules": ["Projection 的输入只能是 Machine SSOT。", "Projection 只能重组和翻译 SSOT，不能新增 authoritative 定义。"],
                "business_state_transitions": ["ssot_ready -> projection_requested -> projection_rendered -> review_visible"],
                "input_objects": ["Machine SSOT", "gate review request"],
                "output_objects": ["Human Review Projection", "projection render record"],
                "required_deliverables": ["Human Review Projection", "projection render record"],
                "authoritative_output": "Human Review Projection（derived review artifact）",
                "constraints": [
                    "Projection 的输入只能来自 Machine SSOT。",
                    "Projection 必须显式标记 derived-only / non-authoritative / non-inheritable。",
                    "Projection 模板必须稳定，不能每次自由发挥。",
                    "Projection 不能成为下游继承输入。",
                ],
                "evidence_audit_trail": ["source ssot ref", "projection template version", "render timestamp"],
                "role_responsibility_split": ["projection generator 负责渲染。", "gate reviewer 负责阅读和判断。", "SSOT owner 负责维护权威源。"],
                "handoff_points": ["Machine SSOT -> Human Review Projection", "Human Review Projection -> gate reviewer"],
                "interaction_timeline": ["1. 读取 SSOT", "2. 渲染 Projection", "3. 标记派生属性", "4. reviewer 阅读审核"],
                "business_sequence": "```text\n[Machine SSOT] -> [Projection Renderer] -> [Human Review Projection] -> [Gate Reviewer]\n```",
                "loop_gate_human_involvement": ["Gate reviewer 在阅读 Projection 时介入。", "SSOT owner 不直接修改 Projection 本体。"],
                "observable_outcomes": ["reviewer 能看到结构化、易读的 Projection。", "Projection 明确声明自身不是新的真相源。"],
                "test_dimensions": ["happy path", "template completeness", "derived-only marker presence", "non-authoritative marker presence", "source traceability"],
                "frozen_product_shape": ["冻结 Projection 的固定模板块。", "冻结 Projection 的派生属性声明。"],
                "frozen_business_semantics": ["Projection 可读，不可继承。", "Projection 服务审核，不替代 SSOT。"],
                "open_technical_decisions": ["Projection renderer 的实现位置", "模板配置存储方式"],
                "explicit_non_decisions": ["不在本 FEAT 定义下游 TECH 输入。", "不在本 FEAT 修改 SSOT 权威结构。"],
                "acceptance_checks": [
                    {"id": "projection-generation-AC-01", "scenario": "Projection only derives from SSOT", "given": "a freeze-ready Machine SSOT", "when": "the Projection is generated", "then": "the FEAT must ensure the Projection is rendered only from Machine SSOT and keeps the SSOT ref visible.", "trace_hints": ["Machine SSOT", "Projection", "traceability"]},
                    {"id": "projection-generation-AC-02", "scenario": "Projection is not a new source of truth", "given": "a reviewer reads the Projection", "when": "the reviewer inspects the artifact", "then": "the FEAT must make derived-only / non-authoritative / non-inheritable markers explicit.", "trace_hints": ["derived-only", "non-authoritative", "non-inheritable"]},
                    {"id": "projection-generation-AC-03", "scenario": "Projection template is stable", "given": "multiple SSOT inputs of the same type", "when": "Projection rendering happens repeatedly", "then": "the FEAT must preserve a stable review template instead of free-form narrative output.", "trace_hints": ["stable template", "review projection"]},
                ],
            },
            {
                "id": "authoritative-snapshot",
                "name": "Authoritative Snapshot 生成流",
                "track": "foundation",
                "goal": "冻结 Projection 中的 Authoritative Snapshot 如何从 SSOT 稳定提取，使审核人不会只看 narrative 而忽略权威约束。",
                "scope": [
                    "定义 completed state、authoritative output、frozen downstream boundary、open technical decisions 的提取规则。",
                    "定义 Snapshot 在 Projection 中的固定位置和最小字段集合。",
                    "定义 Snapshot 只解释 SSOT 已有约束，不新增新的 authoritative 语义。",
                ],
                "product_surface": "Authoritative Snapshot 流：从 SSOT 提取审核必看的权威约束短摘要",
                "completed_state": "审核人能在 Projection 中快速看到 authoritative output、completed state 和 frozen boundary，不需要自己拼字段。",
                "business_deliverable": "给审核人快速校验的 Authoritative Snapshot。",
                "capability_axes": ["Authoritative Snapshot 摘要能力"],
                "overlay_families": [],
                "primary_actor": "projection generator",
                "secondary_actors": ["gate reviewer"],
                "user_story": "As a gate reviewer, I want a short Authoritative Snapshot inside the Projection, so that I can verify hard constraints without reading the whole SSOT field-by-field.",
                "trigger": "当 Projection 已生成并需要补齐权威约束短摘要时。",
                "preconditions": ["Machine SSOT 已定义 completed state、authoritative output 或相关边界字段。"],
                "postconditions": ["Projection 中包含固定位置的 Authoritative Snapshot。"],
                "main_flow": ["读取 SSOT 中的 authoritative fields。", "提取 completed state、authoritative output、frozen downstream boundary、open technical decisions。", "以短摘要形式写入 Projection 的 Authoritative Snapshot 区块。", "供 reviewer 快速校验。"],
                "business_sequence": "```text\n[Machine SSOT] -> [Snapshot Extractor] -> [Authoritative Snapshot] -> [Gate Reviewer]\n```",
                "loop_gate_human_involvement": ["Gate reviewer 通过 Snapshot 快速检查硬边界。"],
                "test_dimensions": ["field presence", "snapshot completeness", "authoritative traceability", "no new authority added"],
                "frozen_product_shape": ["冻结 Snapshot 必含字段集合。"],
                "frozen_business_semantics": ["Snapshot 解释 SSOT 约束，不新增权威语义。"],
                "open_technical_decisions": ["字段提取器的实现位置"],
                "authoritative_output": "Authoritative Snapshot",
                "constraints": [
                    "Snapshot 必须只提取 SSOT 已有 authoritative 字段。",
                    "Snapshot 必须包含 completed state、authoritative output、frozen boundary、open technical decisions。",
                    "Snapshot 不能新增新的权威定义。",
                    "Snapshot 必须保留到 SSOT 的追溯关系。",
                ],
                "acceptance_checks": [
                    {"id": "authoritative-snapshot-AC-01", "scenario": "Snapshot includes hard constraints", "given": "a Machine SSOT with authoritative fields", "when": "Authoritative Snapshot is rendered", "then": "the FEAT must surface completed state, authoritative output, frozen downstream boundary, and open technical decisions together.", "trace_hints": ["completed state", "authoritative output", "frozen downstream boundary"]},
                    {"id": "authoritative-snapshot-AC-02", "scenario": "Reviewer does not need to reconstruct hard constraints", "given": "a reviewer checks the Projection", "when": "the reviewer reads the Snapshot", "then": "the FEAT must make hard constraints visible without requiring the reviewer to stitch together multiple SSOT sections.", "trace_hints": ["reviewer", "snapshot"]},
                    {"id": "authoritative-snapshot-AC-03", "scenario": "Snapshot does not invent new authority", "given": "the Snapshot is compared against SSOT", "when": "authoritative meaning is checked", "then": "the FEAT must keep the Snapshot strictly as a projection of existing SSOT semantics.", "trace_hints": ["no new authority", "SSOT projection"]},
                ],
            },
            {
                "id": "review-focus-risk",
                "name": "Review Focus 与风险提示流",
                "track": "foundation",
                "goal": "冻结系统如何从 SSOT 自动整理 review focus、risks 与 ambiguities，让人类审核聚焦真正需要判断的问题。",
                "scope": [
                    "定义 Review Focus 至少覆盖产品形态、边界遗漏、回流路径、唯一 authoritative deliverable 等关键检查项。",
                    "定义 Risks / Ambiguities 如何识别术语歧义、边界重叠、异常流缺失和责任错置。",
                    "定义这些提示只能基于 SSOT 重组和强调，不能擅自新增权威定义。",
                ],
                "product_surface": "Review Focus 流：自动整理审核重点、风险与歧义点",
                "completed_state": "审核人拿到 Projection 时，已经能直接看到本轮该盯哪些问题、有哪些潜在歧义和边界风险。",
                "business_deliverable": "给审核人聚焦判断的 Review Focus / Risks / Ambiguities 摘要。",
                "capability_axes": ["Review Focus 与风险提示能力"],
                "overlay_families": [],
                "primary_actor": "projection generator",
                "secondary_actors": ["gate reviewer", "SSOT owner"],
                "user_story": "As a gate reviewer, I want the system to highlight review focus and likely risks, so that my attention goes to real product and boundary problems instead of field-by-field scanning.",
                "trigger": "当 Projection 已生成并需要补齐审核重点与风险提示时。",
                "preconditions": ["Machine SSOT 已包含范围、交付物、边界或异常流描述。"],
                "postconditions": ["Projection 中包含 Review Focus 与 Risks / Ambiguities。"],
                "main_flow": ["从 SSOT 提取产品形态、边界、交付物和异常流信号。", "整理 Review Focus 检查项。", "归纳 Risks / Ambiguities。", "把结果写入 Projection 对应区块。"],
                "business_sequence": "```text\n[Machine SSOT] -> [Focus/Risk Extractor] -> [Review Focus + Risks] -> [Gate Reviewer]\n```",
                "loop_gate_human_involvement": ["Gate reviewer 根据重点项与风险项做判断。"],
                "test_dimensions": ["focus coverage", "risk coverage", "ambiguity coverage", "no new authority added"],
                "frozen_product_shape": ["冻结 Review Focus 和 Risks / Ambiguities 的模板位置。"],
                "frozen_business_semantics": ["风险提示用于审核聚焦，不构成新的 authoritative 规则。"],
                "open_technical_decisions": ["歧义识别规则实现位置"],
                "authoritative_output": "Review Focus / Risks / Ambiguities 摘要",
                "constraints": [
                    "Review Focus 必须覆盖产品形态、边界完整性和唯一 authoritative deliverable。",
                    "Risks / Ambiguities 只能基于 SSOT 已有信息重组和强调。",
                    "风险提示不能升级成新的权威规则。",
                    "Focus/Risk 输出必须面向 reviewer 可直接判断。",
                ],
                "acceptance_checks": [
                    {"id": "review-focus-risk-AC-01", "scenario": "Review focus covers key judgment points", "given": "a reviewer is about to approve or reject the gate package", "when": "Review Focus is rendered", "then": "the FEAT must cover product shape, boundary completeness, authoritative deliverable uniqueness, and responsibility placement.", "trace_hints": ["product shape", "boundary", "authoritative deliverable"]},
                    {"id": "review-focus-risk-AC-02", "scenario": "Risks and ambiguities are surfaced", "given": "SSOT contains possible term overlap or missing exception paths", "when": "risk extraction runs", "then": "the FEAT must surface ambiguity and omission risks in a reviewer-facing format.", "trace_hints": ["ambiguity", "missing exception path", "risk"]},
                    {"id": "review-focus-risk-AC-03", "scenario": "Focus and risk output stays non-authoritative", "given": "the extracted hints are compared with SSOT", "when": "authoritative meaning is checked", "then": "the FEAT must not turn risk hints into a second source of truth.", "trace_hints": ["non-authoritative", "review hints"]},
                ],
            },
            {
                "id": "feedback-writeback",
                "name": "Projection 批注回写流",
                "track": "foundation",
                "goal": "冻结 gate 审核意见如何回写到 Machine SSOT，并要求回写后重新生成 Projection，而不是直接改 Projection 成新真相源。",
                "scope": [
                    "定义审核意见如何关联到 SSOT authoritative 字段或边界。",
                    "定义 Projection 上的修改建议何时必须落回 SSOT 才算完成。",
                    "定义 SSOT 更新后如何重新生成 Projection，并阻止下游直接继承 Projection。",
                ],
                "product_surface": "反馈回写流：审核意见回写 SSOT 并触发 Projection 重生成",
                "completed_state": "审核意见已经沉淀回 Machine SSOT，Projection 已基于最新 SSOT 重生成，下游继承仍只认 SSOT。",
                "business_deliverable": "可追踪的 SSOT 修订请求与重生成后的 Projection。",
                "capability_axes": ["Projection 批注回写能力"],
                "overlay_families": [],
                "primary_actor": "SSOT owner",
                "secondary_actors": ["gate reviewer", "projection generator"],
                "user_story": "As an SSOT owner, I want review comments to land back on Machine SSOT instead of stopping on the Projection, so that downstream still inherits one authoritative source.",
                "trigger": "当 reviewer 在 gate 上对 Projection 提出修订意见时。",
                "preconditions": ["Projection 已被 reviewer 审核。", "存在需要修订的审核意见。"],
                "postconditions": ["审核意见已回写 Machine SSOT。", "Projection 已基于最新 SSOT 重生成。"],
                "main_flow": ["reviewer 基于 Projection 提出修订意见。", "系统将意见关联到 Machine SSOT authoritative 字段或边界。", "SSOT owner 更新 Machine SSOT。", "Projection 基于最新 SSOT 重新生成。"],
                "business_sequence": "```text\n[Gate Reviewer Comment] -> [Writeback Mapping] -> [Machine SSOT Update] -> [Projection Regeneration]\n```",
                "loop_gate_human_involvement": ["Gate reviewer 提出意见。", "SSOT owner 完成 authoritative 回写。"],
                "test_dimensions": ["writeback traceability", "projection regeneration", "single source of truth preserved", "projection not directly editable"],
                "frozen_product_shape": ["冻结 writeback 必须回到 Machine SSOT 的规则。"],
                "frozen_business_semantics": ["Projection 上的意见不算完成，回写 SSOT 后才算完成。"],
                "open_technical_decisions": ["comment-to-SSOT mapping 实现方式"],
                "authoritative_output": "SSOT revision request + regenerated Projection",
                "constraints": [
                    "审核意见不能只停留在 Projection 上。",
                    "所有修订都必须回写 Machine SSOT。",
                    "Projection 必须在 SSOT 更新后重新生成。",
                    "下游继承仍只能指向 Machine SSOT。",
                ],
                "acceptance_checks": [
                    {"id": "feedback-writeback-AC-01", "scenario": "Comments do not terminate on Projection", "given": "a reviewer leaves a gate comment", "when": "the revision flow runs", "then": "the FEAT must require that comment to map back to Machine SSOT instead of treating Projection edits as completion.", "trace_hints": ["review comment", "writeback", "Machine SSOT"]},
                    {"id": "feedback-writeback-AC-02", "scenario": "Projection is regenerated after SSOT change", "given": "Machine SSOT has been revised", "when": "Projection is requested again", "then": "the FEAT must regenerate Projection from the updated SSOT rather than patching the old Projection in place.", "trace_hints": ["regeneration", "updated SSOT"]},
                    {"id": "feedback-writeback-AC-03", "scenario": "Downstream still inherits SSOT only", "given": "downstream workflows need authoritative input", "when": "they read the result of gate review", "then": "the FEAT must keep downstream inheritance pointed at Machine SSOT, not at Projection artifacts.", "trace_hints": ["downstream inheritance", "SSOT only"]},
                ],
            },
        ]
    if is_execution_runner_package(package):
        return [
            {
                "id": "ready-job-emission",
                "name": "批准后 Ready Job 生成流",
                "track": "foundation",
                "goal": "冻结 gate approve 如何生成 ready execution job，并把 approve 继续绑定到自动推进而不是 formal publication。",
                "scope": [
                    "定义 approve 后必须产出的 ready execution job 及其最小字段。",
                    "定义 ready job 的 authoritative refs、next skill target 和队列落点。",
                    "定义 revise / retry / reject / handoff 与 ready job 生成的边界，避免 approve 语义漂移。",
                ],
                "product_surface": "批准后 ready job 生成流：gate approve 生成可被 runner 自动消费的 ready execution job",
                "completed_state": "批准结果已经稳定物化为 ready execution job，并进入 artifacts/jobs/ready 等待 runner 消费。",
                "business_deliverable": "给 Execution Loop Job Runner 消费的 ready execution job，以及可追溯的 approve-to-job 关系。",
                "capability_axes": ["批准后 Ready Job 生成能力"],
                "acceptance_checks": [
                    {"id": "ready-job-emission-AC-01", "scenario": "Approve emits one ready job", "given": "gate has approved a governed handoff", "when": "dispatch finishes", "then": "exactly one authoritative ready execution job must be materialized for runner consumption.", "trace_hints": ["approve", "ready execution job", "artifacts/jobs/ready"]},
                    {"id": "ready-job-emission-AC-02", "scenario": "Approve is not rewritten as formal publication", "given": "a downstream reader inspects the product flow", "when": "the approve path is described", "then": "approve must continue into ready-job emission rather than being described as formal publication or admission.", "trace_hints": ["approve", "ready job", "not formal publication"]},
                    {"id": "ready-job-emission-AC-03", "scenario": "Non-approve decisions do not emit next-skill jobs", "given": "gate returns revise, retry, handoff, or reject", "when": "dispatch evaluates the decision", "then": "the product flow must keep those outcomes out of the next-skill ready queue.", "trace_hints": ["revise", "retry", "reject", "queue boundary"]},
                ],
            },
            {
                "id": "execution-runner-intake",
                "name": "Execution Runner 自动取件流",
                "track": "foundation",
                "goal": "冻结 Execution Loop Job Runner 如何从 ready queue 自动取件、claim job 并进入 running，而不是继续依赖第三会话人工接力。",
                "scope": [
                    "定义 runner 扫描、claim、running 和防重入边界。",
                    "定义 jobs/ready 到 runner ownership 的状态转移。",
                    "定义 runner 对 job lineage、claim 证据和并发责任的记录方式。",
                ],
                "product_surface": "runner 自动取件流：Execution Loop Job Runner claim ready job 并接管执行责任",
                "completed_state": "ready execution job 已被 runner claim，并进入可观察的 running ownership 状态。",
                "business_deliverable": "给编排方使用的 claimed execution job / running record，以及可追溯的 claim 证据。",
                "capability_axes": ["Execution Runner 取件能力"],
                "acceptance_checks": [
                    {"id": "runner-intake-AC-01", "scenario": "Ready queue is auto-consumed", "given": "artifacts/jobs/ready contains a valid next-skill job", "when": "Execution Loop Job Runner runs", "then": "the runner must claim the job and record running ownership without human relay.", "trace_hints": ["jobs/ready", "claim", "running"]},
                    {"id": "runner-intake-AC-02", "scenario": "Claim semantics are single-owner", "given": "multiple runner invocations inspect the same ready job", "when": "claim is attempted", "then": "only one runner ownership record may succeed.", "trace_hints": ["single owner", "claim", "ownership"]},
                    {"id": "runner-intake-AC-03", "scenario": "Ready queue remains the authoritative intake", "given": "a downstream flow needs to start next-skill execution", "when": "the start condition is resolved", "then": "the FEAT must use the ready queue and runner claim path instead of directory guessing or ad hoc invocation.", "trace_hints": ["ready queue", "runner intake", "no ad hoc invocation"]},
                ],
            },
            {
                "id": "next-skill-dispatch",
                "name": "下游 Skill 自动派发流",
                "track": "foundation",
                "goal": "冻结 claimed execution job 如何自动派发到下一个 governed skill，并保持 authoritative input / target skill / execution intent 一致。",
                "scope": [
                    "定义 next skill target、输入包引用和调用边界。",
                    "定义 runner 把 claimed job 交给下游 skill 时的 authoritative invocation 记录。",
                    "定义执行启动失败时如何回写 runner 结果而不是静默丢失。",
                ],
                "product_surface": "next skill 自动派发流：runner 基于 claimed job 调起下一个 governed skill",
                "completed_state": "claimed job 已被自动派发到目标 skill，并留下 authoritative invocation / execution attempt 记录。",
                "business_deliverable": "给下游 governed skill 使用的 authoritative invocation，以及给运行时使用的 execution attempt record。",
                "capability_axes": ["下游 Skill 自动派发能力"],
                "acceptance_checks": [
                    {"id": "next-skill-dispatch-AC-01", "scenario": "Claimed job invokes the declared next skill", "given": "runner owns a claimed execution job", "when": "dispatch starts", "then": "the invocation must target the declared next governed skill with the authoritative input package.", "trace_hints": ["claimed job", "next skill", "authoritative input"]},
                    {"id": "next-skill-dispatch-AC-02", "scenario": "Dispatch preserves lineage", "given": "a downstream skill is triggered by runner", "when": "audit inspects the invocation", "then": "the execution attempt must preserve upstream refs, job refs, and target-skill lineage.", "trace_hints": ["lineage", "job ref", "target skill"]},
                    {"id": "next-skill-dispatch-AC-03", "scenario": "Dispatch does not regress to human relay", "given": "the happy path is described", "when": "the next step after approve is reviewed", "then": "the FEAT must show automatic runner dispatch rather than requiring a third-session human handoff.", "trace_hints": ["automatic dispatch", "no human relay"]},
                ],
            },
            {
                "id": "execution-result-feedback",
                "name": "执行结果回写与重试边界流",
                "track": "foundation",
                "goal": "冻结 runner 执行后的 done / failed / retry-reentry 结果，让自动推进链在下一跳后仍可审计、可回流。",
                "scope": [
                    "定义 execution result、failure reason 和 retry / reentry directive 的 authoritative 结果。",
                    "定义 job 从 running 进入 done / failed / retry_return 的状态边界。",
                    "定义 runner 输出如何服务上游审计、下游继续推进和失败恢复。",
                ],
                "product_surface": "执行结果回写流：runner 把 next-skill execution 结果写回主链状态与后续动作",
                "completed_state": "执行结果已形成 authoritative outcome；成功、失败和重试回流都具有清晰的状态与证据。",
                "business_deliverable": "给编排方和审计链使用的 execution outcome、retry / reentry directive 与失败证据。",
                "capability_axes": ["执行结果回写与重试边界能力"],
                "acceptance_checks": [
                    {"id": "execution-feedback-AC-01", "scenario": "Execution outcomes are explicit", "given": "runner has finished or failed a next-skill invocation", "when": "the result is recorded", "then": "the product flow must emit explicit done, failed, or retry/reentry outcomes with evidence.", "trace_hints": ["done", "failed", "retry", "evidence"]},
                    {"id": "execution-feedback-AC-02", "scenario": "Retry returns to execution semantics", "given": "a downstream execution needs another attempt", "when": "the runner records the outcome", "then": "the result must return through retry / reentry semantics instead of being rewritten as publish-only status.", "trace_hints": ["retry", "reentry", "execution semantics"]},
                    {"id": "execution-feedback-AC-03", "scenario": "Approve is not treated as terminal", "given": "the overall product chain is reviewed", "when": "the flow after gate approval is inspected", "then": "the chain must continue through runner execution and result feedback rather than ending at approve itself.", "trace_hints": ["approve", "runner", "not terminal"]},
                ],
            },
        ]
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
    if is_review_projection_package(package):
        return "Gate 审核投影视图与 SSOT 回写统一能力"
    if is_execution_runner_package(package):
        return "Gate 审批后自动推进 Execution Runner 统一能力"
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
                for item in (product_behavior_slices or [])[:6]
            ]
            axis_names = "、".join(axis["name"] for axis in capability_axes[:6])
            return (
                ["统一上位产品能力：形成一条 gate approve 后自动推进到下一 skill 的运行时产品线。"]
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
    rules.append("保留 business skill、handoff runtime、external gate 的职责分层，不得在 FEAT 层重新混层。")
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
    if is_review_projection_package(package):
        lock = semantic_lock(package)
        epic_level_items = [
            "本 EPIC 直接负责 gate 审核阶段的人类友好 Projection，而不是引入新的运行时治理闭环。",
            "Projection 必须是 derived-only、non-authoritative、non-inheritable；冻结与下游继承仍只回到 Machine SSOT。",
            "Projection 必须固定包含产品摘要、主流程、关键交付物、Authoritative Snapshot、Review Focus、Risks / Ambiguities 等审核模板块。",
        ]
        inherited_items = unique_strings(
            ([f"Semantic lock truth: {lock.get('one_sentence_truth')}"] if lock.get("one_sentence_truth") else [])
            + ([f"Allowed capabilities: {', '.join(lock.get('allowed_capabilities', []))}"] if lock.get("allowed_capabilities") else [])
            + ([f"Forbidden capabilities: {', '.join(lock.get('forbidden_capabilities', []))}"] if lock.get("forbidden_capabilities") else [])
            + key_constraints
            + ([f"Authoritative source refs: {', '.join(source_refs)}"] if source_refs else [])
            + [f"Upstream package: {package.artifacts_dir}"]
        )
        downstream_items = [
            "下游 FEAT 不得改写 src_root_id、epic_freeze_ref、source_refs 与 semantic_lock。",
            "下游 FEAT 不得把 Projection 当成新的 SSOT，也不得允许 TECH / TESTSET 直接继承 Projection。",
            "任何审核意见必须沉淀回 Machine SSOT，再重新生成 Projection。",
        ]
        return [
            {"name": "Epic-level constraints", "items": unique_strings(epic_level_items)},
            {"name": "Authoritative inherited constraints", "items": inherited_items},
            {"name": "Downstream preservation rules", "items": unique_strings(downstream_items)},
        ]
    if is_execution_runner_package(package):
        lock = semantic_lock(package)
        epic_level_items = [
            "本 EPIC 直接负责 gate approve 后的自动推进运行时，不把 approve 停在 formal publication 或人工接力。",
            "自动推进主链固定为：approve -> ready execution job -> runner claim -> next skill dispatch -> execution outcome。",
            "artifacts/jobs/ready 是正式 ready queue；runner claim 是唯一 intake；next skill dispatch 必须保留 authoritative refs 和目标 skill 边界。",
        ]
        inherited_items = unique_strings(
            ([f"Semantic lock truth: {lock.get('one_sentence_truth')}"] if lock.get("one_sentence_truth") else [])
            + ([f"Allowed capabilities: {', '.join(lock.get('allowed_capabilities', []))}"] if lock.get("allowed_capabilities") else [])
            + ([f"Forbidden capabilities: {', '.join(lock.get('forbidden_capabilities', []))}"] if lock.get("forbidden_capabilities") else [])
            + key_constraints
            + ([f"Authoritative source refs: {', '.join(source_refs)}"] if source_refs else [])
            + [f"Upstream package: {package.artifacts_dir}"]
        )
        downstream_items = [
            "下游 FEAT 不得把 automatic progression 重新解释成 formal publication / admission-only 链。",
            "下游 FEAT 不得跳过 ready queue 和 runner claim 直接以人工接力或路径猜测触发下一个 skill。",
            "执行结果、重试和失败证据必须继续保持 execution 语义可追溯。",
        ]
        return [
            {"name": "Epic-level constraints", "items": unique_strings(epic_level_items)},
            {"name": "Authoritative inherited constraints", "items": inherited_items},
            {"name": "Downstream preservation rules", "items": unique_strings(downstream_items)},
        ]
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
    if is_review_projection_package(package):
        return []
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
    if is_review_projection_package(package):
        return {
            "score": 8,
            "reasons": ["semantic_lock=review_projection_rule", "fixed_review_slices=4"],
            "is_multi_feat_ready": True,
        }
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
    if is_review_projection_package(package):
        return {
            "required": False,
            "score": 0,
            "triggers": {name: False for name in ROLLOUT_KEYWORD_GROUPS},
            "rationale": ["该源只覆盖 gate 审核投影视图，不需要 adoption / rollout / cross-skill E2E 轨。"],
        }
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
