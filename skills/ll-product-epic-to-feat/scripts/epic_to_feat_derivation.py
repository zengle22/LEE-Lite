#!/usr/bin/env python3
"""
Derivation helpers for the lite-native epic-to-feat runtime.
"""

from __future__ import annotations

import re
from typing import Any

from epic_to_feat_common import (
    ensure_list,
    extract_src_ref,
    normalize_semantic_lock,
    shorten_identifier,
    summarize_text,
    unique_strings,
)


def choose_src_ref(package: Any) -> str:
    resolved = str(package.manifest.get("resolved_src_ref") or "").strip().upper()
    if resolved:
        return resolved
    source_refs = ensure_list(package.epic_json.get("source_refs"))
    src_ref = extract_src_ref(source_refs, fallback=str(package.epic_json.get("src_root_id") or ""))
    if src_ref:
        # Convert verbose SRC-* format (e.g., SRC-SMART-PLAN-GENERATION-V2-MVP-20260331-R9)
        # to concise SRC-XXX format (e.g., SRC-002) by extracting sequence number from context
        verbose_match = re.match(r"SRC-([A-Z0-9-]+?)-(?:V\d+)?(?:-MVP)?(?:-\d{8})?(?:-R\d+)?$", src_ref)
        if verbose_match:
            # Extract sequence from run_id or use a mapping based on known patterns
            run_id = str(package.run_id or "").lower()
            # Check if run_id contains a sequence indicator like "src-freeze-N"
            seq_match = re.search(r"src-freeze-(\d+)", run_id)
            if seq_match:
                return f"SRC-{seq_match.group(1).zfill(3)}"
            # Fallback: use a hash-based short identifier for unknown patterns
            return f"SRC-{shorten_identifier(src_ref.replace('SRC-', ''), limit=12)}"
        return src_ref
    return f"SRC-{shorten_identifier(package.run_id, limit=32)}"


def choose_epic_ref(package: Any) -> str:
    resolved = str(package.manifest.get("resolved_epic_ref") or "").strip().upper()
    if resolved:
        return resolved
    existing = str(package.epic_json.get("epic_freeze_ref") or "").strip()
    if existing:
        src_ref = choose_src_ref(package)
        if src_ref and re.fullmatch(rf"EPIC-{re.escape(src_ref)}-\d+", existing.upper()):
            return existing
        return existing
    src_ref = choose_src_ref(package)
    if src_ref:
        return f"EPIC-{src_ref}-001"
    title = str(package.epic_json.get("title") or package.run_id)
    return f"EPIC-{shorten_identifier(title, limit=40)}"


def _generic_axis_name(axis: dict[str, Any]) -> str:
    return str(axis.get("name") or axis.get("product_surface") or axis.get("feat_axis") or "该 FEAT").strip()


def _generic_axis_surface(axis: dict[str, Any]) -> str:
    return str(axis.get("product_surface") or axis.get("business_deliverable") or _generic_axis_name(axis)).strip()


def _generic_axis_deliverable(axis: dict[str, Any]) -> str:
    return str(axis.get("business_deliverable") or axis.get("product_surface") or _generic_axis_name(axis)).strip()


def _generic_axis_completed_state(axis: dict[str, Any]) -> str:
    completed = str(axis.get("completed_state") or "").strip()
    if completed:
        return completed
    return f"{_generic_axis_name(axis)} 的业务完成态已对上下游清晰可见。"


def _generic_axis_scope_items(axis: dict[str, Any]) -> list[str]:
    items = [str(item).strip() for item in ensure_list(axis.get("scope")) if str(item).strip()]
    return items or [_generic_axis_surface(axis)]


def _generic_axis_capability_summary(axis: dict[str, Any]) -> str:
    capabilities = [str(item).strip() for item in ensure_list(axis.get("capability_axes")) if str(item).strip()]
    return "、".join(capabilities[:3])


def _generic_scope_fallback(axis: dict[str, Any]) -> list[str]:
    name = _generic_axis_name(axis)
    deliverable = _generic_axis_deliverable(axis)
    completed = _generic_axis_completed_state(axis)
    capabilities = _generic_axis_capability_summary(axis)
    bullets = _generic_axis_scope_items(axis)
    bullets.append(f"冻结 {name} 这一独立产品行为切片，并把它保持在产品层边界内。")
    if capabilities:
        bullets.append(f"该切片继承 {capabilities} 的统一约束，但不把 capability axis 直接下沉成实现任务。")
    bullets.append(f"对外交付 {deliverable}，供下游能力直接继承。")
    bullets.append(f"完成态：{completed}")
    return unique_strings(bullets)[:5]


def _generic_main_flow(axis: dict[str, Any]) -> list[str]:
    name = _generic_axis_name(axis)
    scope = _generic_axis_scope_items(axis)[0]
    surface = _generic_axis_surface(axis)
    deliverable = _generic_axis_deliverable(axis)
    completed = _generic_axis_completed_state(axis)
    return [
        f"用户或系统进入 {name} 对应的产品场景，并围绕 {surface} 启动该切片。",
        f"系统执行\"{scope}\"所要求的关键业务处理，并校验该切片成立所需的最小条件。",
        f"系统产出 {deliverable}，并把结果暴露为可被上下游观察的 authoritative 产品结果。",
        f"业务完成态收敛到：{completed}",
    ]


def _generic_acceptance_checks(feat_ref: str, axis: dict[str, Any]) -> list[dict[str, Any]]:
    name = _generic_axis_name(axis)
    scope = _generic_axis_scope_items(axis)[0]
    surface = _generic_axis_surface(axis)
    deliverable = _generic_axis_deliverable(axis)
    completed = _generic_axis_completed_state(axis)
    return [
        {
            "id": f"{feat_ref}-AC-01",
            "scenario": f"{name} happy path reaches the declared completed state",
            "given": f"{name} 对应的业务场景已经被触发",
            "when": f"用户或系统沿着 {surface} 完成该切片要求的关键步骤",
            "then": completed,
            "trace_hints": [feat_ref, name, surface, "completed_state"],
        },
        {
            "id": f"{feat_ref}-AC-02",
            "scenario": f"{name} keeps its declared product boundary",
            "given": "相邻 FEAT 或下游实现尝试把额外能力并入当前切片",
            "when": f"该 FEAT 的业务边界被审查",
            "then": f"该 FEAT 只覆盖\"{scope}\"及其直接完成结果，不吸收相邻产品切片、实现任务或测试执行细节。",
            "trace_hints": [feat_ref, name, "scope boundary", scope],
        },
        {
            "id": f"{feat_ref}-AC-03",
            "scenario": f"{name} hands downstream one authoritative product deliverable",
            "given": "下游 TECH 或 TESTSET 需要继承该 FEAT 的产品语义",
            "when": f"{name} 被作为 authoritative 输入消费",
            "then": f"下游必须围绕 {deliverable} 继承该 FEAT 的产品语义，而不是重新猜测完成条件、补写边界或改写验收口径。",
            "trace_hints": [feat_ref, name, deliverable, "downstream inheritance"],
        },
    ]


def _generic_business_sequence(axis: dict[str, Any]) -> str:
    name = _generic_axis_name(axis)
    deliverable = _generic_axis_deliverable(axis)
    return "\n".join(
        [
            "```text",
            f"[Trigger] -> [{name}] -> [{deliverable}] -> [Completed State Visible]",
            "```",
        ]
    )


def _generic_loop_gate_human_involvement(axis: dict[str, Any]) -> list[str]:
    name = _generic_axis_name(axis)
    deliverable = _generic_axis_deliverable(axis)
    return [
        f"Primary product actor 触发 {name} 的业务场景并提供必要输入。",
        f"System / runtime 负责把 {name} 收敛为 {deliverable} 并记录完成结果。",
        "Gate / human 只在边界冲突、风险升级或需要人工裁决时介入。",
    ]


def _generic_constraints(axis: dict[str, Any], package: Any) -> list[str]:
    name = _generic_axis_name(axis)
    deliverable = _generic_axis_deliverable(axis)
    completed = _generic_axis_completed_state(axis)
    selected = select_constraints(package, [name, _generic_axis_surface(axis), deliverable], fallback_count=2)
    specialized = [
        f"{name} 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。",
        f'{name} 的完成态必须与"{completed}"对齐，不能只输出中间态、占位态或内部处理结果。',
        f'{name} 下游继承 {name} 时必须保留 {deliverable} 这一 authoritative product deliverable，不能自行改写产品边界。',
    ]
    capabilities = _generic_axis_capability_summary(axis)
    if capabilities:
        specialized.append(f"{name} 必须继续受 {capabilities} 的统一约束约束，而不是在下游重新发明同题语义。")
    return unique_strings(selected + specialized)[:6]


def _generic_frozen_product_shape(axis: dict[str, Any]) -> list[str]:
    return [
        f"冻结 {_generic_axis_surface(axis)} 这一产品界面的核心结果形态。",
        f"冻结 {_generic_axis_deliverable(axis)} 作为下游 authoritative 输入的交付形态。",
    ]


def _generic_frozen_business_semantics(axis: dict[str, Any]) -> list[str]:
    return [
        f'{_generic_axis_name(axis)} 的完成态必须以{_generic_axis_completed_state(axis)}为准，而不是以中间占位状态替代。',
        f"下游继承 {_generic_axis_name(axis)} 时必须保留该切片的 scope 与 deliverable 边界。",
    ]


def _generic_open_technical_decisions(axis: dict[str, Any]) -> list[str]:
    name = _generic_axis_name(axis)
    return [
        f"{name} 的 supporting data / state schema",
        f"{name} 的 automation / service interface",
        f"{name} 的 observability / instrumentation surface",
    ]


def _generic_explicit_non_decisions(axis: dict[str, Any]) -> list[str]:
    name = _generic_axis_name(axis)
    return [
        f"不在本 FEAT 内直接决定 {name} 的技术实现细节、接口命名或存储结构。",
        "不在本 FEAT 内把相邻产品切片、下游 TECH 设计或测试执行方案合并进来。",
    ]


def _generic_input_objects(axis: dict[str, Any]) -> list[str]:
    return [
        f"{_generic_axis_name(axis)} trigger context",
        "authoritative user or business input",
        "inherited epic constraints and source refs",
    ]


def _generic_output_objects(axis: dict[str, Any]) -> list[str]:
    return [
        _generic_axis_deliverable(axis),
        "completed state marker",
        f"{_generic_axis_name(axis)} traceable result",
    ]


def _generic_required_deliverables(axis: dict[str, Any]) -> list[str]:
    return [
        _generic_axis_deliverable(axis),
        "authoritative product result",
        "downstream inheritance notes",
    ]


def _generic_role_split(axis: dict[str, Any]) -> list[str]:
    return [
        f"Primary product actor 负责触发 {_generic_axis_name(axis)} 的业务场景并提交必要输入。",
        f"Product / system owner 负责把 {_generic_axis_name(axis)} 收敛成稳定的产品结果。",
        "Downstream FEAT / TECH / TESTSET 只消费 authoritative 输出，不重写当前 FEAT 的产品语义。",
    ]


def _generic_handoff_points(axis: dict[str, Any]) -> list[str]:
    return [
        f"trigger context -> {_generic_axis_surface(axis)}",
        f"{_generic_axis_deliverable(axis)} -> downstream inheritance",
    ]


def _generic_interaction_timeline(axis: dict[str, Any]) -> list[str]:
    return [
        f"1. 触发 {_generic_axis_name(axis)} 对应场景",
        "2. 收集并校验成立该切片所需的最小信息",
        f"3. 产出 {_generic_axis_deliverable(axis)}",
        "4. 对外暴露可观察的 completed state",
    ]


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
    configured = str(axis.get("track") or "").strip()
    if configured:
        return configured
    return "adoption_e2e" if axis_key(axis) == "skill-adoption-e2e" else "foundation"


def _is_execution_runner_epic(package: Any) -> bool:
    lock = normalize_semantic_lock(package.epic_json.get("semantic_lock") or package.epic_frontmatter.get("semantic_lock"))
    return str((lock or {}).get("domain_type") or "").strip().lower() == "execution_runner_rule"


def _execution_runner_axis_defaults(axis_id: str) -> dict[str, Any]:
    return {
        "ready-job-emission": {
            "constraints": [
                "approve 必须稳定落成 ready execution job，而不是停在 formal publication。",
                "ready job 必须写入 artifacts/jobs/ready，并保留 authoritative refs 与目标 skill。",
                "revise / retry / reject / handoff 不得冒充 next-skill ready job。",
                "approve-to-job 关系必须可追溯。",
            ],
            "main_flow": [
                "gate 在 approve 后整理 next skill target、authoritative input 和 lineage。",
                "dispatch 生成 ready execution job 并写入 artifacts/jobs/ready。",
                "系统记录 approve-to-job 关系，供 runner 消费和审计。",
            ],
            "business_sequence": "```text\n[Approve Decision] -> [Ready Execution Job] -> [artifacts/jobs/ready]\n```",
            "loop_gate_human_involvement": ["Gate / reviewer 负责 approve。", "Execution runner 在 job 生成后才介入。"],
            "test_dimensions": ["approve happy path", "non-approve no-job path", "queue write traceability", "no formal-publication substitution"],
            "frozen_product_shape": ["冻结 approve 后的 ready execution job 结构。"],
            "open_technical_decisions": ["ready job schema", "queue index implementation"],
            "authoritative_output": "ready execution job",
            "input_objects": ["approve decision", "dispatch context", "next-skill target"],
            "output_objects": ["ready execution job", "ready queue record", "approve-to-job lineage"],
            "required_deliverables": ["ready execution job", "ready queue record", "approve-to-job lineage"],
            "role_responsibility_split": ["gate / reviewer 负责 approve。", "dispatch writer 负责 materialize ready job。"],
            "handoff_points": ["approve decision -> ready execution job", "ready execution job -> artifacts/jobs/ready"],
            "interaction_timeline": ["1. approve", "2. materialize ready job", "3. write queue record"],
            "dependencies": ["Boundary to runner intake FEAT: 本 FEAT 只负责 ready job emission，不负责 claim/running。"],
        },
        "runner-operator-entry": {
            "business_value": "让 Claude/Codex CLI 用户拥有一个稳定、显式、可审计的 runner 启动入口，而不是在 approve 后靠人工记忆下一步该执行什么命令。",
            "primary_actor": "Claude/Codex CLI operator",
            "secondary_actors": ["execution runner owner", "workflow / orchestration owner"],
            "user_story": "As a Claude/Codex CLI operator, I want one dedicated runner skill entry to start or resume Execution Loop Job Runner, so that自动推进链的启动不依赖隐式知识、临时脚本或人工接力。",
            "trigger": "当 operator 需要启动、恢复或显式进入 Execution Loop Job Runner 时。",
            "preconditions": ["approve 已能落成 ready execution job。", "runner skill entry 与其 authoritative inputs 已被冻结。"],
            "postconditions": ["operator 可以通过单一入口启动或恢复 runner。", "runner run 的入口责任边界可被审计。"],
            "constraints": [
                "Execution Loop Job Runner 必须以独立 skill 入口暴露给 Claude/Codex CLI 用户。",
                "入口必须显式声明 start / resume 语义，而不是隐式依赖后台自动进程。",
                "入口不得把 approve 后链路退化成手工逐个调用下游 skill。",
                "入口调用必须保留 authoritative run context 与 lineage。",
            ],
            "main_flow": [
                "operator 在 Claude/Codex CLI 中调用 Execution Loop Job Runner skill。",
                "skill 初始化或恢复 runner run context，并确认本次运行目标队列/作用域。",
                "runner 进入 ready queue 消费流程，后续交给 intake / dispatch / feedback FEAT 继续处理。",
            ],
            "business_rules": [
                "runner skill entry 是自动推进链的唯一人工起点。",
                "入口只负责启动或恢复 runner，不直接替代 ready job emission 或 next-skill dispatch。",
            ],
            "business_state_transitions": ["runner_entry_requested -> runner_context_initialized -> runner_ready_to_consume"],
            "business_sequence": "```text\n[Claude/Codex CLI Operator] -> [Runner Skill Entry] -> [Runner Context Initialized] -> [Ready Queue Consumption]\n```",
            "loop_gate_human_involvement": ["Claude/Codex CLI operator 负责显式启动或恢复 runner。", "runner owner 定义入口边界与运行前置条件。"],
            "test_dimensions": ["skill entry available", "start path", "resume path", "authoritative run context", "no manual downstream relay"],
            "frozen_product_shape": ["冻结独立 runner skill 入口及其 start/resume 产品边界。"],
            "open_technical_decisions": ["runner skill command surface", "run context bootstrap schema"],
            "authoritative_output": "runner skill entry invocation record",
            "input_objects": ["runner start request", "runner resume request", "authoritative run scope"],
            "output_objects": ["runner skill invocation record", "runner context initialization result", "runner start receipt"],
            "required_deliverables": ["runner skill entry definition", "runner invocation record", "runner start receipt"],
            "role_responsibility_split": ["Claude/Codex CLI operator 负责调用入口。", "runner skill 负责初始化或恢复运行上下文。"],
            "handoff_points": ["operator command -> runner skill entry", "runner skill entry -> runner intake flow"],
            "interaction_timeline": ["1. operator invokes runner skill", "2. runner context initializes", "3. hand off to ready queue intake"],
            "dependencies": ["Boundary to ready-job FEAT: 本 FEAT 不负责生成 ready execution job。", "Boundary to runner-control-surface FEAT: 入口启动后，后续控制语义由控制面 FEAT 承担。"],
            "product_surface": "Runner 用户入口流：Claude/Codex CLI 用户通过独立 runner skill 启动或恢复自动推进运行时",
            "completed_state": "用户已经可以通过独立 runner skill 显式启动或恢复 Execution Loop Job Runner，并形成可追踪的 invocation record。",
            "business_deliverable": "给 operator 使用的 runner skill entry 与启动回执。",
        },
        "runner-control-surface": {
            "business_value": "让 operator 能通过统一 CLI control surface 管理 runner 的 start、claim、run、complete、fail 等控制动作，而不是把运行控制散落在多个临时命令里。",
            "primary_actor": "Claude/Codex CLI operator",
            "secondary_actors": ["execution runner owner", "on-call / support operator"],
            "user_story": "As a Claude/Codex CLI operator, I want one stable CLI control surface for Execution Loop Job Runner, so that我可以启动、续跑、诊断和收口 runner，而不是记忆一组松散脚本。",
            "trigger": "当 operator 需要对 runner 执行启动、控制、收口或恢复动作时。",
            "preconditions": ["runner skill entry 已存在。", "runner control verbs 与权责边界已被冻结。"],
            "postconditions": ["operator 可以通过统一 CLI control surface 控制 runner。", "runner 控制动作的证据链可被审计。"],
            "constraints": [
                "runner control surface 必须提供统一的 CLI verbs，而不是分散在多个无治理脚本里。",
                "control surface 必须与 runner skill entry 对齐，不能绕开 authoritative run context。",
                "control verbs 不得直接替代 next-skill invocation 结果或篡改 execution outcome。",
                "控制动作必须产生可追踪的 command / state evidence。",
            ],
            "main_flow": [
                "operator 通过 runner CLI control surface 发起 start / claim / run / complete / fail / resume 等动作。",
                "runner 校验当前 run context 和 job ownership。",
                "系统记录控制动作与 resulting state，供观测和审计消费。",
            ],
            "business_rules": [
                "CLI control surface 是 runner 的唯一正式控制面。",
                "控制面只改变 runner control state，不重新定义 ready job、dispatch 或 feedback 业务语义。",
            ],
            "business_state_transitions": ["runner_control_requested -> runner_control_applied -> runner_control_recorded"],
            "business_sequence": "```text\n[Runner Skill Entry] -> [CLI Control Surface] -> [Runner Control Action] -> [Control Evidence]\n```",
            "loop_gate_human_involvement": ["Claude/Codex CLI operator 负责发起控制动作。", "runner owner 负责定义可用 verbs 与状态边界。"],
            "test_dimensions": ["control verbs available", "start/resume command path", "claim/run/complete/fail command recording", "ownership guard", "control evidence traceability"],
            "frozen_product_shape": ["冻结 runner CLI control surface 及其 command vocabulary。"],
            "open_technical_decisions": ["CLI command naming", "control evidence schema"],
            "authoritative_output": "runner control action record",
            "input_objects": ["runner command request", "run context", "job ownership context"],
            "output_objects": ["runner control action record", "runner state update", "control evidence"],
            "required_deliverables": ["runner CLI command set", "runner control action record", "control evidence"],
            "role_responsibility_split": ["operator 负责发起控制动作。", "runner control layer 负责校验并记录状态变化。"],
            "handoff_points": ["runner skill entry -> CLI control surface", "CLI control surface -> runner intake / running state"],
            "interaction_timeline": ["1. issue runner command", "2. validate run context", "3. record control outcome"],
            "dependencies": ["Boundary to runner-operator-entry FEAT: 本 FEAT 依赖独立 skill 入口存在。", "Boundary to runner-observability-surface FEAT: 控制结果需要被监控面读取，但监控面不拥有控制权。"],
            "product_surface": "Runner 控制面流：operator 通过统一 CLI verbs 控制 Execution Loop Job Runner 的运行动作",
            "completed_state": "runner 的启动、恢复、控制和收口动作都可以通过统一 CLI control surface 完成，并留下审计记录。",
            "business_deliverable": "给 operator 使用的 runner CLI control surface 与控制动作记录。",
        },
        "execution-runner-intake": {
            "constraints": [
                "Execution Loop Job Runner 必须自动消费 ready queue。",
                "claim 语义必须是 single-owner。",
                "runner intake 不得回退到人工接力或临时脚本触发。",
                "claim 和 running ownership 必须留下证据。",
            ],
            "main_flow": [
                "runner 扫描 artifacts/jobs/ready 中的 ready execution job。",
                "runner claim job 并记录 single-owner running ownership。",
                "claimed job 进入下一步自动 dispatch。",
            ],
            "business_sequence": "```text\n[artifacts/jobs/ready] -> [Runner Claim] -> [Running Ownership]\n```",
            "loop_gate_human_involvement": ["Execution runner 负责 claim/running。", "Human 不作为正常 intake 路径。"],
            "test_dimensions": ["queue scan", "single-owner claim", "running ownership visibility", "no manual relay"],
            "frozen_product_shape": ["冻结 ready -> claimed -> running 的 intake 状态链。"],
            "open_technical_decisions": ["claim lock implementation", "runner polling cadence"],
            "authoritative_output": "claimed execution job",
            "input_objects": ["ready execution job", "queue ownership context"],
            "output_objects": ["claimed execution job", "running ownership record", "claim evidence"],
            "required_deliverables": ["claimed execution job", "running ownership record", "claim evidence"],
            "role_responsibility_split": ["runner 负责 claim。", "gate 不负责 running ownership。"],
            "handoff_points": ["ready execution job -> runner claim", "runner claim -> running ownership"],
            "interaction_timeline": ["1. scan queue", "2. claim job", "3. record running ownership"],
            "dependencies": ["Boundary to ready-job FEAT: 只有 ready execution job 能进入本 FEAT。", "Boundary to dispatch FEAT: claim 成功后才允许调用 next skill。"],
        },
        "next-skill-dispatch": {
            "constraints": [
                "claimed execution job 必须调用声明的 next skill。",
                "dispatch 必须保留 authoritative input refs 和 target skill lineage。",
                "自动推进不得回退为人工第三会话接力。",
                "dispatch 失败必须回写 execution outcome。",
            ],
            "main_flow": [
                "runner 读取 claimed execution job 中的 target skill 和 authoritative input。",
                "runner 自动调用下一个 governed skill。",
                "系统记录 invocation / execution attempt 供反馈链消费。",
            ],
            "business_sequence": "```text\n[Claimed Job] -> [Runner Dispatch] -> [Next Skill Invocation]\n```",
            "loop_gate_human_involvement": ["Execution runner 负责派发。", "Downstream governed skill 接收 invocation。"],
            "test_dimensions": ["target skill routing", "authoritative input preservation", "automatic dispatch path", "dispatch failure capture"],
            "frozen_product_shape": ["冻结 claimed job 到 next skill invocation 的派发形态。"],
            "open_technical_decisions": ["invocation adapter", "dispatch retry policy"],
            "authoritative_output": "next-skill invocation record",
            "input_objects": ["claimed execution job", "authoritative input package", "target skill ref"],
            "output_objects": ["next-skill invocation", "execution attempt record", "dispatch lineage"],
            "required_deliverables": ["next-skill invocation", "execution attempt record", "dispatch lineage"],
            "role_responsibility_split": ["runner 负责自动派发。", "downstream skill 负责执行自身 workflow。"],
            "handoff_points": ["claimed execution job -> runner dispatch", "runner dispatch -> next governed skill"],
            "interaction_timeline": ["1. resolve target skill", "2. invoke downstream skill", "3. record execution attempt"],
            "dependencies": ["Boundary to feedback FEAT: 本 FEAT 只负责启动下一个 skill，不负责最终 done/failed/retry outcome。"],
        },
        "execution-result-feedback": {
            "constraints": [
                "done / failed / retry-reentry outcome 必须显式记录。",
                "失败证据必须和 execution attempt 绑定。",
                "retry 必须回到 execution semantics，不得改写成 publish-only 状态。",
                "approve 不是自动推进链的终态。",
            ],
            "main_flow": [
                "runner 收集下一个 skill 的 execution result。",
                "系统写出 done、failed 或 retry-reentry outcome。",
                "审计链和上游编排读取结果，决定继续推进或回流。",
            ],
            "business_sequence": "```text\n[Execution Attempt] -> [Outcome Recording] -> [Done | Failed | Retry/Reentry]\n```",
            "loop_gate_human_involvement": ["Execution runner 负责结果回写。", "Human 只在失败分析或策略判断时介入。"],
            "test_dimensions": ["done path", "failed path", "retry-reentry path", "failure evidence completeness"],
            "frozen_product_shape": ["冻结 execution outcome 与 retry-reentry directive 的结果形态。"],
            "open_technical_decisions": ["outcome schema", "failure evidence storage"],
            "authoritative_output": "execution outcome record",
            "input_objects": ["execution attempt record", "downstream skill result", "runner state"],
            "output_objects": ["execution outcome", "retry-reentry directive", "failure evidence"],
            "required_deliverables": ["execution outcome", "retry-reentry directive", "failure evidence"],
            "role_responsibility_split": ["runner 负责结果回写。", "编排方负责消费 done/failed/retry outcome。"],
            "handoff_points": ["next-skill result -> outcome record", "outcome record -> orchestration / audit"],
            "interaction_timeline": ["1. collect result", "2. record outcome", "3. expose retry or completion"],
            "dependencies": ["Boundary to dispatch FEAT: 本 FEAT 只负责 post-dispatch outcome，不重写 invocation 过程。"],
        },
        "runner-observability-surface": {
            "business_value": "让 operator 能持续观察 ready backlog、running、failed、deadletters 和 waiting-human 等 runner 状态，而不是在故障后依赖人工排查目录。",
            "primary_actor": "workflow / orchestration operator",
            "secondary_actors": ["Claude/Codex CLI operator", "execution runner owner", "audit owner"],
            "user_story": "As a workflow / orchestration operator, I want one runner observability surface, so that我可以看到 backlog、running、failed 和 waiting-human 状态，并在需要时决定恢复或介入。",
            "trigger": "当 operator 需要查看 runner 队列、执行状态、失败结果或待人工处理状态时。",
            "preconditions": ["runner 已有可观测的 queue / running / outcome 记录。", "监控面读取边界与状态词表已被冻结。"],
            "postconditions": ["operator 可以看到 runner backlog、running、failed、deadletters、waiting-human。", "状态观察结果可驱动恢复、诊断或人工介入。"],
            "constraints": [
                "runner observability surface 必须覆盖 ready backlog、running、failed、deadletters、waiting-human 等关键状态。",
                "监控面必须读取 authoritative runner state，而不是靠目录猜测或人工拼接。",
                "监控面只负责观察和提示，不直接改写 runner control state。",
                "观测结果必须能关联到 ready job、invocation 和 execution outcome lineage。",
            ],
            "main_flow": [
                "operator 打开 runner observability surface 查看 backlog、running、failed 和 waiting-human 状态。",
                "系统聚合 ready queue、claimed/running ownership、dispatch record 和 outcome evidence。",
                "operator 基于观测结果决定是否继续运行、恢复、重试或人工介入。",
            ],
            "business_rules": [
                "监控面是 runner 状态的唯一正式观察面。",
                "观测结果必须基于 authoritative runner records，而不是临时目录扫描。",
            ],
            "business_state_transitions": ["runner_state_collected -> observability_snapshot_published -> operator_decision_informed"],
            "business_sequence": "```text\n[Runner State Records] -> [Observability Surface] -> [Backlog / Running / Failed / Waiting-Human View] -> [Operator Decision]\n```",
            "loop_gate_human_involvement": ["workflow / orchestration operator 负责查看和解释监控结果。", "Human 只在 waiting-human 或失败诊断时进一步介入。"],
            "test_dimensions": ["ready backlog visibility", "running visibility", "failed visibility", "deadletters visibility", "waiting-human visibility", "lineage traceability"],
            "frozen_product_shape": ["冻结 runner observability surface 及其关键状态视图。"],
            "open_technical_decisions": ["observability query surface", "status aggregation model"],
            "authoritative_output": "runner observability snapshot",
            "input_objects": ["ready queue state", "running ownership record", "dispatch lineage", "execution outcome record"],
            "output_objects": ["runner observability snapshot", "backlog view", "failed/waiting-human view"],
            "required_deliverables": ["runner observability surface", "runner observability snapshot", "status aggregation evidence"],
            "role_responsibility_split": ["monitor surface 负责聚合并展示状态。", "operator 负责基于观测结果做运行决策。"],
            "handoff_points": ["runner state records -> observability surface", "observability surface -> operator recovery / escalation decision"],
            "interaction_timeline": ["1. collect runner states", "2. publish observability snapshot", "3. operator decides next action"],
            "dependencies": ["Boundary to intake / dispatch / feedback FEAT: 本 FEAT 消费这些 FEAT 的状态记录，但不重写它们的业务边界。"],
            "product_surface": "Runner 运行监控流：operator 观察 ready backlog、running、failed、deadletters 与 waiting-human 状态",
            "completed_state": "operator 已可通过统一监控面观察 runner 关键状态，并据此决定恢复、排障或人工介入。",
            "business_deliverable": "给 operator 使用的 runner observability surface 与状态快照。",
        },
        "skill-adoption-e2e": {
            "constraints": [
                "pilot 链必须证明 ready job、runner、next-skill dispatch 和 execution outcome 这条自动推进链真实可用。",
                "接入验证不得回退为人工第三会话接力。",
                "cutover / fallback 必须围绕 runner 自动推进结果定义。",
                "pilot evidence 必须绑定真实 approve -> runner -> next skill 链路。",
            ],
            "main_flow": [
                "rollout owner 选定要接入自动推进链的 producer、runner 和 downstream skill。",
                "pilot 波次运行真实 approve -> ready job -> runner -> next skill 链路。",
                "audit / gate 基于 execution outcome 和 pilot evidence 决定 cutover 或 fallback。",
            ],
            "business_sequence": "```text\n[Onboarding Directive] -> [Pilot Auto-Progression Chain] -> [Execution Evidence] -> [Cutover or Fallback]\n```",
            "loop_gate_human_involvement": ["Rollout owner 决定 wave。", "Audit / gate owner 基于 runner outcome 判断 cutover 或 fallback。"],
            "test_dimensions": ["pilot auto-progression path", "cutover decision", "fallback path", "pilot evidence completeness"],
            "frozen_product_shape": ["冻结 runner 自动推进 pilot 的 onboarding / cutover 结果形态。"],
            "open_technical_decisions": ["pilot automation surface", "rollout evidence schema"],
            "authoritative_output": "pilot evidence package",
            "dependencies": ["Boundary to execution-result-feedback FEAT: adoption 依赖真实 runner outcome，而不是 formal publication/admission。"],
        },
    }.get(axis_id, {})


def feat_title(axis: dict[str, str], package: Any) -> str:
    explicit = str(axis.get("name") or "").strip()
    if explicit:
        return explicit
    titles = {
        "collaboration-loop": "主链候选提交与交接流",
        "handoff-formalization": "主链 gate 审核与裁决流",
        "object-layering": "formal 发布与下游准入流",
        "artifact-io-governance": "主链受治理 IO 落盘与读取流",
        "skill-adoption-e2e": "governed skill 接入与 pilot 验证流",
    }
    return titles.get(axis_key(axis), str(axis.get("name") or axis.get("feat_axis") or "Feature Slice").strip())


def feat_goal(axis: dict[str, str], package: Any) -> str:
    explicit = str(axis.get("goal") or "").strip()
    if explicit:
        return explicit
    goals = {
        "collaboration-loop": "把 governed skill 产出的 candidate package 以统一 authoritative handoff 形式提交进主链，并把候选交接正式送入 gate 消费链。",
        "handoff-formalization": "把 gate 对 candidate 的审核、裁决与 formalization trigger 语义冻结成单一业务流，让 approve / revise / retry / handoff / reject 都有明确业务结果。",
        "object-layering": "把 approved decision 之后的 formal 发布与 downstream 准入冻结成单一业务切片，确保下游只消费 authoritative formal output。",
        "artifact-io-governance": "把主链中必须落盘和必须受治理读取的业务动作冻结为受治理 IO 流，并让业务方拿到 authoritative receipt 与 managed ref。",
        "skill-adoption-e2e": "把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。",
    }
    key = axis_key(axis)
    if key in goals:
        return goals[key]
    business_goal = str(package.epic_json.get("business_goal") or "")
    return summarize_text(f"{axis.get('name')}承担 EPIC 目标中的一块独立能力面。{business_goal}", limit=220)


def feat_scope(axis: dict[str, str], package: Any | None = None) -> list[str]:
    explicit_scope = ensure_list(axis.get("scope"))
    key = axis_key(axis)
    scopes = {
        "collaboration-loop": [
            "定义 governed skill 在什么触发场景下提交 candidate package、proposal 和 evidence，以及提交后形成什么 authoritative handoff object。",
            "定义 handoff object 在 execution loop、gate loop、human loop 之间如何流转，以及哪些状态允许回流到 revise / retry。",
            "定义提交完成后哪些业务结果对上游可见，哪些业务结果必须等待 gate 返回 decision 才能继续推进。",
            "显式约束本 FEAT 只冻结候选提交与交接流，不直接定义 gate 裁决结果和 formal 发布结果。",
        ],
        "handoff-formalization": [
            "定义 gate 如何消费 candidate handoff、谁参与审核、以及 approve / revise / retry / handoff / reject 各自的业务语义与输出物。",
            "定义每一种裁决返回给谁、形成什么 authoritative decision object、以及哪些裁决会回流到 execution loop、哪些裁决会触发 formal 发布。",
            "明确本 FEAT 冻结的是审核与裁决流，以及 formal 发布 trigger 的业务语义，不直接负责 formal output 的下游读取准入和 IO 落盘策略。",
            "要求任何候选对象都必须先经过本 FEAT 的裁决流，不能直接跃迁为下游正式输入。",
        ],
        "object-layering": [
            "定义 approved decision 之后何时形成 formal object、何时生成 authoritative formal ref，以及这些对象如何成为 downstream 正式输入。",
            "定义 downstream consumer 在什么前置条件下可以读取 formal output，以及哪些 candidate / intermediate object 永远不能被正式消费。",
            "明确 lineage、formal refs、consumer admission 属于同一条 formal 发布与准入流，而不是零散的对象规则清单。",
            "要求任何下游消费都必须沿 formal refs 与 lineage 进入，不能以路径猜测、旁路文件或候选对象读取。",
        ],
        "artifact-io-governance": [
            "定义 candidate handoff、decision evidence、formal output 与 downstream consumption 中哪些业务动作必须经过受治理 IO 落盘。",
            "定义谁发起 governed write / read、在什么业务节点发生，以及哪些自由写入或目录猜测行为会被拒绝。",
            "要求所有正式主链落盘都遵循统一 path / mode / registry 边界，不允许以局部临时目录策略替代。",
            "明确本 FEAT 只冻结主链业务动作如何接入 ADR-005 已交付能力，不扩展为全仓库文件治理总方案。",
        ] if package is not None and epic_uses_adr005_foundation(package) else [
            "定义主链 handoff、formal materialization 与 governed skill IO 中哪些业务动作必须受治理落盘。",
            "明确哪些 IO 是受治理主链 IO，哪些属于全局文件治理而必须留在本 FEAT 之外。",
            "要求所有正式主链写入都遵循统一的路径与覆盖边界，不允许以局部临时目录策略替代。",
            "明确本 FEAT 只覆盖 mainline IO/path 业务边界，不扩展为全仓库或全项目文件治理总方案。",
        ],
        "skill-adoption-e2e": [
            "定义哪些 governed skill 先接入主链、哪些角色负责 producer / consumer / gate consumer 的 onboarding，以及 scope 外对象如何处理。",
            "定义 pilot 目标链路、migration wave、cutover rule、fallback rule 与 guarded rollout 边界，但不要求一次性全量迁移。",
            "要求至少选择一条真实 producer -> consumer -> audit -> gate pilot 主链，形成跨 skill E2E 闭环 evidence。",
            "明确本 FEAT 只面向本主链治理能力涉及的 governed skill 接入与验证，不扩大为仓库级全局文件治理改造。",
        ],
    }
    if explicit_scope:
        if len(explicit_scope) >= 3:
            return explicit_scope
        if key in scopes:
            return unique_strings(explicit_scope + scopes[key])[:5]
        return _generic_scope_fallback(axis)
    if key in scopes:
        return scopes[key]
    return _generic_scope_fallback(axis)


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
            "Do not redefine gate review vocabulary, reviewer responsibility, or candidate re-entry policy here.",
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


def feat_business_value(axis: dict[str, str], package: Any) -> str:
    explicit = str(axis.get("business_value") or "").strip()
    if explicit:
        return explicit
    values = {
        "collaboration-loop": "让上游 governed skill 的候选提交行为形成统一 authoritative handoff，避免不同 skill 以隐式上下文或特例脚本拼接交接流。",
        "handoff-formalization": "让 gate 审核与裁决结果成为可复用的统一业务语义，而不是把 approve / revise / retry 混在不同 skill 的局部逻辑里。",
        "object-layering": "让 formal output 与 downstream consumption 的关系变成稳定产品行为，而不是由 consumer 自己猜哪个对象可读。",
        "artifact-io-governance": "让主链业务动作的落盘和读取具备统一治理边界，保证 formal output、evidence 和 handoff 都可审计、可追踪。",
        "skill-adoption-e2e": "让主链能力通过真实接入和 pilot 验证落地，避免底座完成但真实 producer / consumer 链路仍然不可用。",
    }
    return values.get(axis_key(axis), str(package.epic_json.get("business_goal") or "该 FEAT 承担父 EPIC 的一条独立产品切片。"))


def feat_primary_actor(axis: dict[str, str]) -> str:
    explicit = str(axis.get("primary_actor") or "").strip()
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": "governed skill / execution loop",
        "handoff-formalization": "gate loop / reviewer",
        "object-layering": "formalization actor / downstream admission owner",
        "artifact-io-governance": "governed skill / runtime writer",
        "skill-adoption-e2e": "rollout owner / governed skill owner",
    }
    return mapping.get(axis_key(axis), "primary product actor")


def feat_secondary_actors(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("secondary_actors"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["gate loop", "human reviewer"],
        "handoff-formalization": ["execution loop", "formalization actor"],
        "object-layering": ["downstream consumer", "audit consumer"],
        "artifact-io-governance": ["registry / audit consumer", "downstream reader"],
        "skill-adoption-e2e": ["producer skill owner", "consumer skill owner", "audit / gate owner"],
    }
    return mapping.get(axis_key(axis), ["secondary product actor"])


def feat_user_story(axis: dict[str, str]) -> str:
    explicit = str(axis.get("user_story") or "").strip()
    if explicit:
        return explicit
    stories = {
        "collaboration-loop": "As a governed skill owner, I want candidate submission to always form an authoritative handoff object, so that gate 和后续 loop 不需要再靠隐式上下文理解上游状态。",
        "handoff-formalization": "As a gate / reviewer owner, I want every candidate to go through one explicit review-and-decision flow, so that approve、revise、retry、reject 的结果都可追踪、可回流、可验收。",
        "object-layering": "As a formalization / admission owner, I want approved decisions to become one explicit formal publication package that downstream consumers can consume only through admission, so that candidate 或中间对象不会被误当成正式输入。",
        "artifact-io-governance": "As a runtime / artifact owner, I want formal mainline writes and reads to use governed IO boundaries, so that audit 可以稳定回答对象写到了哪里、为什么可读。",
        "skill-adoption-e2e": "As a rollout owner, I want governed skills to onboard through explicit pilot and cutover rules, so that主链能力的成立可以通过真实链路验证而不是口头假设。",
    }
    return stories.get(axis_key(axis), "As a product actor, I want this FEAT to define a stable product slice, so that downstream design no longer has to infer the product shape.")


def feat_trigger(axis: dict[str, str]) -> str:
    explicit = str(axis.get("trigger") or "").strip()
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": "当 governed skill 产出 candidate package 并准备提交给主链时。",
        "handoff-formalization": "当 gate 开始审核候选对象并需要给出正式裁决时。",
        "object-layering": "当 candidate 已获批准并需要形成 formal output 供下游消费时。",
        "artifact-io-governance": "当 handoff、decision、formal output 或 evidence 需要正式读写时。",
        "skill-adoption-e2e": "当新的 governed skill 需要接入主链并参与真实 pilot 验证时。",
    }
    return mapping.get(axis_key(axis), "当该 FEAT 的核心业务场景被触发时。")


def feat_preconditions(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("preconditions"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["governed skill 已形成 candidate package、proposal 与 evidence。", "主链 runtime 已可接收 handoff object。"] ,
        "handoff-formalization": ["authoritative handoff object 已进入 gate pending 状态。", "reviewer / gate loop 可消费 proposal 与 evidence。"],
        "object-layering": ["gate 已给出允许 formal 发布的 decision。", "formal refs / lineage 可被 authoritative store 记录。"],
        "artifact-io-governance": ["ADR-005 已作为前置基础可用。", "调用方已完成对象分类并声明 write/read 意图。"],
        "skill-adoption-e2e": ["foundation FEAT 已 freeze-ready。", "已有明确的 skill onboarding 范围和 pilot 目标链路。"],
    }
    return mapping.get(axis_key(axis), ["父 EPIC 对应的前置业务条件已经成立。"])


def feat_postconditions(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("postconditions"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["主链形成 authoritative handoff object。", "提交完成后 gate 接管消费，待审批状态与交接责任边界清晰且可追踪。"] ,
        "handoff-formalization": ["每次 gate 裁决都会形成 authoritative decision object。", "revise / retry / reject / handoff 的返回去向明确。"],
        "object-layering": ["formal output 与 formal refs 成为下游 authoritative input。", "candidate 与 intermediate object 被阻止作为正式输入。"],
        "artifact-io-governance": ["正式主链读写留下 governed receipt / record。", "未通过治理边界的读写不会被静默放行。"],
        "skill-adoption-e2e": ["至少一条 pilot 链形成可审计 evidence。", "接入、cutover、fallback 边界被显式记录。"],
    }
    return mapping.get(axis_key(axis), ["该 FEAT 定义的业务结果已对下游可见。"])


def feat_main_flow(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("main_flow"))
    key = axis_key(axis)
    flows = {
        "collaboration-loop": [
            "execution loop 收到业务完成信号后整理 candidate package、proposal、evidence。",
            "governed skill 把候选对象提交为 authoritative handoff object。",
            "runtime 把 handoff 路由到 gate loop，并记录下一跳责任。",
            "提交完成后，上游只看到 handoff 已建立并等待裁决；是否回流由后续 decision flow 决定。",
        ],
        "handoff-formalization": [
            "gate loop 消费 authoritative handoff object 并组织审核上下文。",
            "reviewer / gate 给出 approve / revise / retry / handoff / reject 中的一种裁决。",
            "系统生成 authoritative decision object，并把结果返回给 execution loop、指定处理者或 formal 发布流。",
            "被拒绝或需修订的对象不会进入 formal downstream input。",
        ],
        "object-layering": [
            "formalization actor 在获批后生成 formal object 与 formal refs。",
            "lineage 绑定 candidate、decision、formal output 之间的 authoritative 关系。",
            "downstream consumer 通过 formal refs 请求正式输入。",
            "只有通过准入检查的 consumer 才能读取 formal output。",
        ],
        "artifact-io-governance": [
            "业务动作声明要写入或读取的主链对象及其用途。",
            "主链调用 governed IO 边界完成 path / mode / registry 校验。",
            "受治理写入生成 authoritative receipt、registry record 与可追踪 ref。",
            "下游读取必须通过同一套 governed read 边界取得正式对象。",
        ],
        "skill-adoption-e2e": [
            "rollout owner 确认本波次要接入的 producer、consumer 与 gate consumer。",
            "被选 skill 先以 pilot 模式接入主链并运行真实业务闭环。",
            "audit / gate 消费 pilot evidence，决定继续 cutover、保持 guarded 还是触发 fallback。",
            "通过的波次进入下一轮扩大接入范围。",
        ],
    }
    fallback = flows.get(key, _generic_main_flow(axis))
    if explicit:
        if len(explicit) >= 3:
            return explicit
        return unique_strings(explicit + fallback)[:5]
    return fallback


def feat_alternate_flows(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("alternate_flows"))
    if explicit:
        return explicit
    flows = {
        "collaboration-loop": ["candidate 在提交前发现缺失 evidence，则保留在 execution loop，不进入 gate。"],
        "handoff-formalization": ["当 reviewer 需要补充上下文时，可返回 revise 或 handoff 到指定处理者而不直接 approve。"],
        "object-layering": ["当 formal output 已生成但 consumer 尚未满足准入条件时，可先记录 authoritative output，再阻止消费。"],
        "artifact-io-governance": ["当同一对象重复提交时，可按 idempotent write 语义返回已有 managed ref。"],
        "skill-adoption-e2e": ["当 pilot 范围不足以证明闭环时，可扩大 pilot actor 范围后再次验证，而不是直接全量切换。"],
    }
    return flows.get(axis_key(axis), [])


def feat_exception_flows(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("exception_flows"))
    if explicit:
        return explicit
    flows = {
        "collaboration-loop": ["handoff 对象不完整或状态非法时，必须拒绝进入 gate，并返回可追踪错误。"] ,
        "handoff-formalization": ["reject 会终止正式推进；revise / retry 会带着 decision object 回流到 execution loop。"],
        "object-layering": ["若 lineage 不完整或 formal refs 缺失，则 downstream admission 必须拒绝并留下审计记录。"],
        "artifact-io-governance": ["若 path / mode 校验失败，则写入被拒绝，不能 silent fallback 到自由写入。"],
        "skill-adoption-e2e": ["若 pilot evidence 不能证明 producer -> consumer -> audit -> gate 闭环成立，则 cutover 不得继续推进。"],
    }
    return flows.get(axis_key(axis), [])


def feat_business_rules(axis: dict[str, str], package: Any) -> list[str]:
    explicit = ensure_list(axis.get("business_rules"))
    if explicit:
        return explicit
    rules = {
        "collaboration-loop": [
            "candidate 提交后必须形成 authoritative handoff object，不能只靠目录约定或隐式上下文表示\"已提交\"。",
            "进入 gate 前后的责任主体必须显式可辨认。",
        ],
        "handoff-formalization": [
            "approve / revise / retry / handoff / reject 是唯一合法裁决词表。",
            "candidate package 只能作为 gate 消费对象，不能直接成为 formal downstream input。",
        ],
        "object-layering": [
            "formal output 才是 downstream authoritative input。",
            "consumer 不得通过路径邻近、旁路文件或 candidate 对象取得正式读取资格。",
        ],
        "artifact-io-governance": [
            "所有正式主链写入必须经过受治理 IO 边界。",
            "本 FEAT 只定义主链业务动作如何消费 ADR-005 能力，不重新实现 ADR-005 模块。",
        ] if epic_uses_adr005_foundation(package) else [
            "所有正式主链写入必须经过统一治理边界。",
            "本 FEAT 不扩展为全仓文件治理总方案。",
        ],
        "skill-adoption-e2e": [
            "skill onboarding、cutover、fallback 必须有明确 business owner 和波次边界。",
            "真实 pilot evidence 是 adoption 成立的必要条件，不是附属材料。",
        ],
    }
    return rules.get(axis_key(axis), [])


def feat_business_state_transitions(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("business_state_transitions"))
    if explicit:
        return explicit
    transitions = {
        "collaboration-loop": ["candidate_prepared -> handoff_submitted -> gate_pending"],
        "handoff-formalization": ["gate_pending -> under_review -> decision_issued -> approved|revised|retried|rejected|handed_off"],
        "object-layering": ["decision_approved -> formal_materialized -> formal_ref_published -> consumer_admitted"],
        "artifact-io-governance": ["write_requested -> governed_validated -> receipt_recorded -> managed_ref_available"],
        "skill-adoption-e2e": ["skill_selected -> pilot_enabled -> cutover_guarded -> wave_accepted|fallback_triggered"],
    }
    return transitions.get(axis_key(axis), [])


def feat_input_objects(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("input_objects"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["candidate package", "proposal", "evidence bundle"],
        "handoff-formalization": ["authoritative handoff object", "proposal ref", "review context"],
        "object-layering": ["approved decision object", "candidate lineage", "formalization intent"],
        "artifact-io-governance": ["handoff write request", "decision evidence write request", "formal output write/read request"],
        "skill-adoption-e2e": ["skill onboarding matrix entry", "pilot target chain", "cutover directive"],
    }
    return mapping.get(axis_key(axis), _generic_input_objects(axis))


def feat_output_objects(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("output_objects"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["authoritative handoff object", "handoff trace ref", "submission accepted marker"],
        "handoff-formalization": ["decision object", "review outcome", "re-entry directive or formal publication trigger"],
        "object-layering": ["formal object", "formal ref", "admission verdict", "lineage record"],
        "artifact-io-governance": ["managed artifact ref", "registry record", "write/read receipt"],
        "skill-adoption-e2e": ["integration matrix", "pilot evidence", "cutover or fallback decision"],
    }
    return mapping.get(axis_key(axis), _generic_output_objects(axis))


def feat_required_deliverables(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("required_deliverables"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["authoritative handoff submission", "handoff trace ref / submission receipt", "gate pending visibility result"],
        "handoff-formalization": ["authoritative decision result", "review outcome record", "formal publication trigger or delegation result"],
        "object-layering": ["formal publication package", "formal ref / lineage package", "admission verdict"],
        "artifact-io-governance": ["governed write/read receipt", "registry record / managed ref", "rejected write/read result"],
        "skill-adoption-e2e": ["onboarding matrix", "pilot chain 定义", "pilot evidence 要求", "cutover / fallback 规则"],
    }
    return mapping.get(axis_key(axis), _generic_required_deliverables(axis))


def feat_authoritative_output(axis: dict[str, str]) -> str:
    explicit = str(axis.get("authoritative_output") or "").strip()
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": "authoritative handoff object",
        "handoff-formalization": "authoritative decision object",
        "object-layering": "formal publication package (formal object + formal ref)",
        "artifact-io-governance": "managed artifact ref + registry record",
        "skill-adoption-e2e": "pilot evidence + cutover decision",
    }
    return mapping.get(axis_key(axis), "authoritative FEAT output")


def feat_evidence_audit_trail(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("evidence_audit_trail"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["提交时间、提交者、handoff ref、下一跳责任人"],
        "handoff-formalization": ["review context、decision reason、decision round、返回去向"],
        "object-layering": ["formalization receipt、lineage record、admission evidence"],
        "artifact-io-governance": ["write/read receipt、registry record、policy verdict"],
        "skill-adoption-e2e": ["pilot evidence、cutover record、fallback record、audit finding"],
    }
    return mapping.get(axis_key(axis), [])


def feat_role_responsibility_split(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("role_responsibility_split"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["execution loop 负责提交 candidate 与补充 evidence。", "gate loop 负责接收 handoff 并决定是否进入审核。", "human loop 只在需要人工参与时介入。"],
        "handoff-formalization": ["gate / reviewer 负责做出裁决。", "execution loop 只消费 revise / retry / reject 等结果，不自行批准。", "formalization actor 只消费 decision object 作为 formal 发布 trigger。"],
        "object-layering": ["formalization actor 负责生成 formal output 与 formal refs。", "downstream consumer 负责按准入规则请求正式读取。", "admission owner 负责阻止 candidate / intermediate object 被误消费。"],
        "artifact-io-governance": ["业务动作发起方负责声明读写意图。", "governed IO 边界负责校验和记录。", "registry / audit 消费方负责提供 authoritative readback。"],
        "skill-adoption-e2e": ["rollout owner 负责 wave 和 pilot 范围。", "skill owner 负责接入和回退执行。", "audit / gate owner 负责判断 pilot 是否成立。"],
    }
    return mapping.get(axis_key(axis), _generic_role_split(axis))


def feat_handoff_points(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("handoff_points"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["candidate package -> authoritative handoff object", "authoritative handoff object -> gate pending state"],
        "handoff-formalization": ["handoff object -> reviewer context", "decision object -> execution loop / delegated handler / formal publication flow"],
        "object-layering": ["approved decision -> formal output", "formal ref -> downstream admission request"],
        "artifact-io-governance": ["business write request -> governed receipt", "managed artifact ref -> downstream read"],
        "skill-adoption-e2e": ["onboarding directive -> pilot activation", "pilot evidence -> cutover / fallback decision"],
    }
    return mapping.get(axis_key(axis), _generic_handoff_points(axis))


def feat_interaction_timeline(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("interaction_timeline"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["1. execution loop 整理 candidate", "2. governed skill 提交 authoritative handoff", "3. runtime 路由到 gate loop", "4. 上游看到提交完成并等待裁决"],
        "handoff-formalization": ["1. gate 接收 handoff", "2. reviewer 审核 proposal/evidence", "3. 生成 decision object", "4. decision 返回 execution、delegated handler 或 formal 发布流"],
        "object-layering": ["1. approved decision 触发 formal 发布", "2. formalization actor 写出 formal refs / lineage", "3. consumer 请求 admission", "4. 通过后消费 authoritative input"],
        "artifact-io-governance": ["1. 声明读写意图", "2. governed IO 校验", "3. 生成 receipt / record", "4. 返回 managed ref 或拒绝结果"],
        "skill-adoption-e2e": ["1. 选定 pilot wave", "2. 接入 producer / consumer", "3. 收集 audit / gate evidence", "4. 决定 cutover 或 fallback"],
    }
    return mapping.get(axis_key(axis), _generic_interaction_timeline(axis))


def feat_business_sequence(axis: dict[str, str]) -> str:
    explicit = str(axis.get("business_sequence") or "").strip()
    if explicit:
        return explicit
    diagrams = {
        "collaboration-loop": "\n".join([
            "```text",
            "[Governed Skill] -> [Execution Loop] -> [Authoritative Handoff] -> [Gate Loop]",
            "                                            |",
            "                                            +-> [Gate Pending / Awaiting Decision]",
            "```",
        ]),
        "handoff-formalization": "\n".join([
            "```text",
            "[Handoff Object] -> [Gate / Reviewer] -> [Decision Object]",
            "                                   |",
            "                                   +-> revise / retry / reject -> [Execution Loop]",
            "                                   +-> handoff -> [Delegated Handler]",
            "                                   +-> approve -> [Formal Publication Flow]",
            "```",
        ]),
        "object-layering": "\n".join([
            "```text",
            "[Approved Decision] -> [Formal Publication] -> [Formal Ref / Lineage] -> [Admission Check] -> [Consumer]",
            "```",
        ]),
        "artifact-io-governance": "\n".join([
            "```text",
            "[Business Action] -> [Governed Write / Read] -> [Receipt / Registry Record] -> [Managed Ref]",
            "```",
        ]),
        "skill-adoption-e2e": "\n".join([
            "```text",
            "[Onboarding Directive] -> [Pilot Chain] -> [Audit / Gate Evidence] -> [Cutover or Fallback]",
            "```",
        ]),
    }
    return diagrams.get(axis_key(axis), _generic_business_sequence(axis))


def feat_observable_outcomes(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("observable_outcomes"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["上游可以观察到 authoritative handoff 已建立。", "gate 可以观察到 handoff 已进入 pending intake。"],
        "handoff-formalization": ["每次审核都有 decision object。", "approve / reject / revise / retry / handoff 的结果可被外部观察。"],
        "object-layering": ["formal ref 可被解析。", "candidate 对象不能再被当成正式输入。"],
        "artifact-io-governance": ["正式写入会生成 receipt / registry record。", "被拒绝的读写不会 silent fallback。"],
        "skill-adoption-e2e": ["pilot evidence 可追踪。", "cutover / fallback 边界可被外部观察。"],
    }
    return mapping.get(axis_key(axis), [])


def feat_test_dimensions(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("test_dimensions"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": [
            "happy path",
            "incomplete evidence rejection",
            "gate pending visibility",
            "bypass prevention",
            "audit traceability",
        ],
        "handoff-formalization": [
            "happy path",
            "reject path",
            "revise/retry path",
            "handoff delegation path",
            "bypass prevention",
            "audit traceability",
        ],
        "object-layering": [
            "happy path",
            "admission reject path",
            "lineage missing path",
            "bypass prevention",
            "audit traceability",
        ],
        "artifact-io-governance": [
            "happy path",
            "policy reject path",
            "idempotent repeat write",
            "bypass prevention",
            "audit traceability",
        ],
        "skill-adoption-e2e": [
            "happy path",
            "pilot reject path",
            "cutover path",
            "fallback path",
            "scope control",
            "audit traceability",
        ],
    }
    return mapping.get(
        axis_key(axis),
        [
            "happy path",
            "reject path",
            "bypass prevention",
            "audit traceability",
        ],
    )


def feat_frozen_product_shape(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("frozen_product_shape"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["冻结 authoritative handoff 的形成条件。", "冻结候选提交完成后对上游与 gate 可见的产品结果。"],
        "handoff-formalization": ["冻结 decision vocabulary 及其输出物。", "冻结裁决回流与继续推进的业务结果。"],
        "object-layering": ["冻结 formal publication package 与 consumer admission 的 authoritative 关系。", "冻结 candidate 不可直接消费这一产品形态。"],
        "artifact-io-governance": ["冻结哪些业务动作必须 governed write/read。", "冻结主链正式落盘与读取的 authoritative 边界。"],
        "skill-adoption-e2e": ["冻结 onboarding wave / pilot / cutover / fallback 的产品形态。", "冻结真实 pilot evidence 的存在要求。"],
    }
    return mapping.get(axis_key(axis), _generic_frozen_product_shape(axis))


def feat_frozen_business_semantics(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("frozen_business_semantics"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["提交 candidate 不等于获得批准。", "进入 gate 前后由不同角色负责。"],
        "handoff-formalization": ["approve / revise / retry / handoff / reject 是互斥且完备的裁决结果。", "裁决结果必须形成 authoritative decision object。"],
        "object-layering": ["formal output 才能作为 downstream 正式输入。", "consumer admission 依赖 formal refs / lineage，而不是路径猜测。"],
        "artifact-io-governance": ["正式主链读写必须遵循 governed IO 边界。", "未通过治理的写入不算正式输出。"],
        "skill-adoption-e2e": ["pilot 成功是 cutover 的前置业务语义。", "fallback 是正式定义的业务结果，不是临时补救动作。"],
    }
    return mapping.get(axis_key(axis), _generic_frozen_business_semantics(axis))


def feat_open_technical_decisions(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("open_technical_decisions"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["handoff object 的 schema 字段", "runtime 模块划分", "具体 CLI surface"],
        "handoff-formalization": ["decision object schema", "gate implementation 位置", "formalization runtime 调度方式"],
        "object-layering": ["formal refs 存储结构", "lineage 持久化方案", "admission checker 实现位置"],
        "artifact-io-governance": ["Gateway / Path Policy / Registry 的具体调用接口", "receipt schema", "路径物理目录布局"],
        "skill-adoption-e2e": ["onboarding CLI / config surface", "pilot evidence schema", "rollout automation 方式"],
    }
    return mapping.get(axis_key(axis), _generic_open_technical_decisions(axis))


def feat_explicit_non_decisions(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("explicit_non_decisions"))
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": ["不在本 FEAT 决定 formal output 的物理落盘方式。", "不在本 FEAT 决定实现态模块和命令名。"],
        "handoff-formalization": ["不在本 FEAT 决定 consumer admission 实现。", "不在本 FEAT 决定 registry / path 物理实现。"],
        "object-layering": ["不在本 FEAT 决定 gate 裁决流程本身。", "不在本 FEAT 决定落盘路径和 CLI 命令。"],
        "artifact-io-governance": ["不在本 FEAT 重新实现 ADR-005 模块。", "不在本 FEAT 决定对象层级和 gate 裁决语义。"],
        "skill-adoption-e2e": ["不在本 FEAT 重写 foundation FEAT 的能力定义。", "不在本 FEAT 直接做 release / task 排期。"],
    }
    return mapping.get(axis_key(axis), _generic_explicit_non_decisions(axis))


def feat_product_interface(axis: dict[str, str]) -> str:
    explicit = str(axis.get("product_surface") or "").strip()
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": "候选提交流：把 candidate package 提交为 authoritative handoff submission",
        "handoff-formalization": "审批裁决流：gate 审核 handoff 并输出 authoritative decision result",
        "object-layering": "formal 发布与准入流：approved decision 发布成 formal package 并供 consumer 准入",
        "artifact-io-governance": "受治理落盘流：正式 write/read 生成 managed ref 与 authoritative receipt",
        "skill-adoption-e2e": "接入验证流：governed skill 通过 pilot / cutover / fallback 接入主链",
    }
    return mapping.get(axis_key(axis), "产品行为切片界面")


def feat_completed_state(axis: dict[str, str]) -> str:
    explicit = str(axis.get("completed_state") or "").strip()
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": "上游 workflow 已完成一次正式候选提交，并明确看到 handoff 已建立、gate 已接管，但尚未获得批准结果。",
        "handoff-formalization": "一次完整的 gate 审核已结束，业务方拿到单一 authoritative decision result，并知道应回流、终止还是进入 formal 发布。",
        "object-layering": "formal publication package 已形成且被 admission 链认可，下游 consumer 只会拿到 formal input，不会再看到 candidate 冒充正式结果。",
        "artifact-io-governance": "正式业务读写都留下 governed receipt / managed ref，调用方能回答对象写到哪里、为什么可读，失败也不会静默旁路。",
        "skill-adoption-e2e": "至少一条真实 pilot 链完成验证，rollout owner 能看到 integration matrix、pilot evidence 和 cutover / fallback 决策结果。",
    }
    return mapping.get(axis_key(axis), "该 FEAT 的业务完成态已对上下游可见。")


def feat_business_deliverable(axis: dict[str, str]) -> str:
    explicit = str(axis.get("business_deliverable") or "").strip()
    if explicit:
        return explicit
    mapping = {
        "collaboration-loop": "给 gate 使用的 authoritative handoff submission，以及给上游 workflow 可见的提交完成结果",
        "handoff-formalization": "给 execution 或 formal 发布链消费的 authoritative decision result，以及给 reviewer 可追溯的裁决结果",
        "object-layering": "给 downstream consumer 正式消费的 formal publication package，以及可验证的 admission result",
        "artifact-io-governance": "给业务动作发起方返回的 governed write/read result，以及可审计的 managed ref / receipt",
        "skill-adoption-e2e": "给 rollout owner 使用的 onboarding / pilot / cutover package，以及真实链路 evidence",
    }
    return mapping.get(axis_key(axis), "该 FEAT 的业务交付物")


def feat_governance_intermediates(axis: dict[str, str]) -> list[str]:
    mapping = {
        "collaboration-loop": ["candidate package", "proposal", "evidence bundle"],
        "handoff-formalization": ["review context", "proposal ref"],
        "object-layering": ["lineage record", "admission verdict"],
        "artifact-io-governance": ["policy verdict", "write/read receipt"],
        "skill-adoption-e2e": ["pilot evidence", "audit finding"],
    }
    return mapping.get(axis_key(axis), [])


def feat_loop_gate_human_involvement(axis: dict[str, str]) -> list[str]:
    explicit = ensure_list(axis.get("loop_gate_human_involvement"))
    key = axis_key(axis)
    mapping = {
        "collaboration-loop": [
            "Execution loop 在 candidate 整理和提交时介入。",
            "Gate loop 在 authoritative handoff 建立后接管消费。",
            "Human loop 仅在 gate 要求人工审查或 revise / retry 升级时介入。",
        ],
        "handoff-formalization": [
            "Gate loop 组织审核上下文并持有裁决 authority。",
            "Human reviewer 在需要人工判断 approve / revise / reject 时介入。",
            "Execution loop 只在收到 revise / retry / reject 后重新介入。",
        ],
        "object-layering": [
            "Gate 只提供 approved decision，不直接承担 downstream admission。",
            "Formalization actor 在 approved decision 到达后介入并发布 formal output。",
            "Human / audit 只在 lineage 缺失或 admission 异常时作为审计介入点出现。",
        ],
        "artifact-io-governance": [
            "业务动作发起方在正式 write/read 时介入并声明意图。",
            "Gate / human 不拥有 IO 执行权，但其 decision 会决定哪些对象进入正式读写。",
            "Audit consumer 在 receipt / registry record 生成后介入做 authoritative readback。",
        ],
        "skill-adoption-e2e": [
            "Rollout owner 在 wave、pilot、cutover 判断时介入。",
            "Gate / audit owner 在 pilot evidence 审核和 cutover 决策时介入。",
            "Human involvement 点集中在 pilot 放量、fallback 触发和 scope 调整。",
        ],
    }
    fallback = mapping.get(key, _generic_loop_gate_human_involvement(axis))
    if explicit:
        if len(explicit) >= 1:
            return explicit
        return unique_strings(explicit + fallback)[:3]
    return fallback


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
    explicit = ensure_list(axis.get("constraints"))
    key = axis_key(axis)
    selected = {
        "collaboration-loop": select_constraints(package, ["双会话双队列", "execution loop", "human loop", "queue"], fallback_count=3),
        "handoff-formalization": select_constraints(package, ["handoff runtime", "external gate", "approve", "candidate", "formal object"], fallback_count=3),
        "object-layering": select_constraints(package, ["business skill", "formal object", "formal refs", "lineage", "consumer"], fallback_count=3),
        "artifact-io-governance": select_constraints(package, ["路径与目录治理", "governed skill io", "formal materialization", "handoff"], fallback_count=3),
        "skill-adoption-e2e": select_constraints(package, ["integration matrix", "onboarding", "migration", "cutover", "fallback", "producer -> consumer -> audit -> gate", "e2e"], fallback_count=3),
    }.get(key)

    specialized = {
        "collaboration-loop": [
            "Loop 协作语义必须显式说明哪类对象触发 gate、哪类 decision 允许回流、哪类状态允许继续推进。",
            "该 FEAT 只负责 loop 协作边界，不得把 formalization 细则混入 loop 责任定义。",
        ],
        "handoff-formalization": [
            "Candidate 不得绕过 gate 直接升级为 downstream formal input。",
            "Formal 发布只能由 authoritative decision object 触发，不得出现并列正式化入口。",
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
    fallback = unique_strings((selected or _generic_constraints(axis, package)) + specialized)[:6]
    if explicit:
        if len(explicit) >= 4:
            return explicit
        return unique_strings(explicit + fallback)[:6]
    return fallback


def feat_dependencies(axis: dict[str, str], package: Any | None = None) -> list[str]:
    dependencies = {
        "collaboration-loop": [
            "Boundary to 正式交接与物化能力: 本 FEAT 只负责协作责任、状态流转与回流条件，不负责 formalization 语义、升级判定与物化结果。",
            "Boundary to 对象分层与准入能力: 本 FEAT 可以要求对象交接，但对象是否具备正式消费资格由对象分层 FEAT 决定。",
        ],
        "handoff-formalization": [
            "Boundary to 主链协作闭环能力: 本 FEAT 消费 loop 协作产物，但不重写 execution / gate / human 的责任分工、状态流转与回流条件。",
            "Boundary to 对象分层与准入能力: 本 FEAT 定义 candidate 到 decision 以及 decision 到 formal 发布 trigger 的推进链，不定义 consumer admission 与读取资格。",
        ],
        "object-layering": [
            "Boundary to 正式交接与物化能力: 本 FEAT 从 approved decision 之后开始，定义 formal publication package 和 downstream admission，而不是定义 gate 审核动作本身。",
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


def _engineering_baseline_acceptance_checks(feat_ref: str, slice_id: str) -> list[dict[str, Any]]:
    """Generate engineering baseline-specific acceptance checks with file/path/command level detail.

    These checks are concrete and verifiable at the file/object/command level,
    not generic product contract templates.
    """
    # Map slice IDs to specific acceptance check sets
    slice_checks = {
        "repo-layout-baseline": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Repository skeleton generator creates all baseline directories",
                "given": "The repo skeleton generator is executed for a new project",
                "when": "Directory structure validation is performed",
                "then": "All baseline directories must exist: apps/, services/, packages/, contracts/, scripts/, docs/ with proper README.md in each",
                "trace_hints": [feat_ref, "skeleton generator", "directory validator", "baseline dirs"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Documentation hierarchy is established",
                "given": "The skeleton generator completes",
                "when": "Documentation structure is reviewed",
                "then": "docs/adr/, docs/superpowers/specs/, docs/superpowers/decisions/ directories exist with index files",
                "trace_hints": [feat_ref, "adr directory", "specs directory", "documentation hierarchy"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Skeleton generator compliance is verifiable",
                "given": "A reviewer runs the skeleton generator",
                "when": "Output is compared against expected layout spec",
                "then": "No deviation from the baseline layout spec; any customization must be in allowed override zones only",
                "trace_hints": [feat_ref, "layout spec", "compliance check", "override zones"],
            },
        ],
        "api-shell-runnable": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Health endpoints are accessible and return correct structure",
                "given": "The API server is started locally",
                "when": "GET /healthz and GET /readyz are called",
                "then": "Both endpoints return 200 with {status: 'ok'} structure; /readyz includes dependency checks",
                "trace_hints": [feat_ref, "/healthz", "/readyz", "health endpoint", "probe response"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Layered architecture boundary is enforced in code structure",
                "given": "The API codebase is reviewed",
                "when": "Import statements and directory boundaries are inspected",
                "then": "No circular imports between layers; handlers -> services -> repositories direction is enforced; Go module boundary is explicit in go.mod",
                "trace_hints": [feat_ref, "layered architecture", "import boundary", "go.mod"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "API server is runnable as a standalone process",
                "given": "Dependencies are installed",
                "when": "The server start command is executed (e.g., go run ./cmd/server or npm start)",
                "then": "Server starts successfully and binds to configured port without errors",
                "trace_hints": [feat_ref, "server startup", "port binding", "runnable entrypoint"],
            },
        ],
        "miniapp-shell-runnable": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Miniapp compiles and previews without errors",
                "given": "Miniapp project dependencies are installed",
                "when": "Build/preview command is executed (e.g., npm run dev, uniapp build)",
                "then": "Build completes without errors; preview server starts and serves the miniapp shell",
                "trace_hints": [feat_ref, "miniapp build", "preview server", "compilation"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "API integration layer is scaffolded",
                "given": "The miniapp shell is created",
                "when": "API client code structure is reviewed",
                "then": "API client module exists with configurable base URL, request/response interceptors, and error handling skeleton",
                "trace_hints": [feat_ref, "API client", "interceptors", "error handling"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Navigation structure is defined",
                "given": "The miniapp shell pages are created",
                "when": "Page routing configuration is inspected",
                "then": "pages.json (or equivalent) defines all baseline pages with proper navigation paths and tab bar configuration if applicable",
                "trace_hints": [feat_ref, "pages.json", "navigation", "tab bar", "routing"],
            },
        ],
        "local-env-baseline": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Docker Compose file defines all required services",
                "given": "docker-compose.local.yml exists",
                "when": "docker compose -f docker-compose.local.yml config is validated",
                "then": "Services defined: postgres (with volume), redis (optional), and app service with correct networking and volume mounts",
                "trace_hints": [feat_ref, "docker-compose.local.yml", "postgres service", "volume mounts"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Environment variables are documented and configurable",
                "given": ".env.example or .env.template exists",
                "when": "Environment file is reviewed",
                "then": "All required env vars documented: DATABASE_URL, REDIS_URL, PORT, API keys placeholders; .env file is in .gitignore",
                "trace_hints": [feat_ref, ".env.example", "DATABASE_URL", "environment variables"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Postgres connectivity is verifiable",
                "given": "docker compose up is executed",
                "when": "Application attempts database connection",
                "then": "Connection succeeds; health check passes; database is accessible from app container",
                "trace_hints": [feat_ref, "postgres connectivity", "health check", "container networking"],
            },
        ],
        "db-migrations-discipline": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Empty database can be migrated from scratch",
                "given": "Fresh empty PostgreSQL database is created",
                "when": "Migration command is run (e.g., goose up, golang-migrate up, alembic upgrade head)",
                "then": "All migrations execute successfully; schema matches the expected initial schema; no manual SQL required",
                "trace_hints": [feat_ref, "empty database", "migration command", "initial schema"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Initial schema is version-controlled",
                "given": "Migration files are inspected",
                "when": "Schema structure is reviewed",
                "then": "Core tables exist with proper constraints, indexes, and foreign keys; migration files are sequential and reversible (up/down)",
                "trace_hints": [feat_ref, "initial schema", "migration files", "reversible migrations"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Migration discipline is enforced",
                "given": "A developer needs to change schema",
                "when": "Schema change process is reviewed",
                "then": "All schema changes go through migration files; no direct DDL in application code; migration rollback is tested",
                "trace_hints": [feat_ref, "migration discipline", "schema changes", "rollback tested"],
            },
        ],
        "healthz-readyz-contract": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Liveness probe endpoint is implemented correctly",
                "given": "Application is running",
                "when": "GET /healthz is called",
                "then": "Returns 200 OK with minimal latency; response includes timestamp and version; endpoint does not check external dependencies",
                "trace_hints": [feat_ref, "/healthz", "liveness probe", "version info"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Readiness probe validates all critical dependencies",
                "given": "Application is running with dependencies",
                "when": "GET /readyz is called",
                "then": "Returns 200 only when database, redis, and other critical deps are reachable; returns 503 when any critical dep is unavailable",
                "trace_hints": [feat_ref, "/readyz", "readiness probe", "dependency check", "503 response"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Traffic scheduling integration is documented",
                "given": "Kubernetes or load balancer configuration exists",
                "when": "Probe configuration is reviewed",
                "then": "Liveness probe: periodSeconds 10-30, initialDelaySeconds 5; Readiness probe: periodSeconds 5-10, failureThreshold 3; traffic only routes to ready pods",
                "trace_hints": [feat_ref, "traffic scheduling", "probe config", "kubernetes"],
            },
        ],
    }

    # Return slice-specific checks or fall back to generic engineering checks
    return slice_checks.get(slice_id, [
        {
            "id": f"{feat_ref}-AC-01",
            "scenario": "Engineering baseline deliverable is concrete and verifiable",
            "given": "The engineering baseline FEAT is implemented",
            "when": "Deliverables are inspected",
            "then": "Concrete artifacts exist: files, directories, runnable commands, configuration files with specific content",
            "trace_hints": [feat_ref, "engineering baseline", "concrete artifacts"],
        },
        {
            "id": f"{feat_ref}-AC-02",
            "scenario": "Engineering boundary is enforced",
            "given": "Downstream implementation needs engineering guidance",
            "when": "Boundary is reviewed",
            "then": "FEAT defines file/path/command level artifacts, not abstract product contracts",
            "trace_hints": [feat_ref, "engineering boundary", "file level artifacts"],
        },
        {
            "id": f"{feat_ref}-AC-03",
            "scenario": "Downstream can inherit without guessing",
            "given": "TECH/IMPL downstream consumes this FEAT",
            "when": "Inheritance is evaluated",
            "then": "No gap-filling required; all engineering artifacts are explicit and authoritative",
            "trace_hints": [feat_ref, "downstream inheritance", "no gap filling"],
        },
    ])


def build_acceptance_checks(feat_ref: str, epic_ref: str, axis: dict[str, str]) -> list[dict[str, Any]]:
    explicit = axis.get("acceptance_checks")
    key = axis_key(axis)
    # Check if this is an engineering baseline slice
    slice_id = axis.get("id", "")
    is_engineering_baseline = slice_id.startswith("engineering-baseline-") or "engineering" in slice_id.lower() or "baseline" in slice_id.lower()

    # For engineering baseline slices, use specialized concrete checks
    if is_engineering_baseline:
        engineering_checks = _engineering_baseline_acceptance_checks(feat_ref, slice_id)
        if isinstance(explicit, list) and explicit:
            if len(explicit) >= 3:
                return explicit
            return explicit + engineering_checks[: max(0, 3 - len(explicit))]
        return engineering_checks

    # For non-engineering slices, use the existing axis-based checks
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
                "scenario": "Submission completion is visible without implying approval",
                "given": "A candidate package has been submitted into the mainline",
                "when": "Upstream and gate inspect the result of the submission",
                "then": "The FEAT must make clear which authoritative handoff and pending-intake results become visible, while keeping approval and re-entry semantics outside this FEAT.",
                "trace_hints": [feat_ref, "handoff object", "gate pending", "submission completed", "not yet approved"],
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
                "scenario": "Gate decision path is single and explicit",
                "given": f"{epic_ref} contains candidate outputs awaiting approval",
                "when": "The mainline moves from candidate handoff into gate review",
                "then": "The FEAT must define one explicit handoff -> gate decision chain and one authoritative decision object without parallel shortcuts.",
                "trace_hints": [feat_ref, "handoff", "gate decision", "decision object", "single path"],
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
                "scenario": "Formal publication is only triggered by the decision object",
                "given": "A business skill emits proposal and evidence objects",
                "when": "Formal publication eligibility is evaluated",
                "then": "The FEAT must make the decision object the only business-level trigger for formal publication and keep approval authority outside the business skill body.",
                "trace_hints": [feat_ref, "business skill", "decision object", "formal publication trigger", "external gate"],
            },
        ],
        "object-layering": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Approved decision leads to one explicit formal publication path",
                "given": f"{epic_ref} emits approved decisions that need downstream consumption",
                "when": "The product moves from approved decision to downstream use",
                "then": "The FEAT must define one explicit approved decision -> formal publication -> admission chain without bypassing formal refs or lineage.",
                "trace_hints": [feat_ref, "approved decision", "formal publication", "formal ref", "lineage"],
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
                "scenario": "Candidate and intermediate objects cannot pose as formal deliverables",
                "given": "A candidate package or intermediate object still exists after decision approval",
                "when": "A downstream consumer resolves formal input",
                "then": "The FEAT must prevent candidate or intermediate objects from being treated as the formal publication package.",
                "trace_hints": [feat_ref, "candidate", "intermediate object", "formal publication package"],
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
        "runner-operator-entry": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Runner skill entry is explicit",
                "given": f"{epic_ref} requires an operator-visible way to start automatic progression",
                "when": f"{feat_ref} is reviewed as a standalone capability",
                "then": "The FEAT must define one dedicated runner skill entry for Claude/Codex CLI instead of relying on implicit background behavior or manual downstream relays.",
                "trace_hints": [feat_ref, "runner skill entry", "Claude/Codex CLI", "start", "resume"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Runner entry preserves authoritative context",
                "given": "An operator starts or resumes the runner",
                "when": "The runner accepts the request",
                "then": "The FEAT must require authoritative run context and lineage rather than free-form command arguments or guesswork.",
                "trace_hints": [feat_ref, "authoritative context", "lineage", "resume"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Runner entry is not a manual relay surface",
                "given": "A reviewer inspects post-approve progression",
                "when": "The operator entry is described",
                "then": "The FEAT must keep the operator entry limited to launching or resuming runner semantics, not manual invocation of downstream skills one by one.",
                "trace_hints": [feat_ref, "manual relay forbidden", "runner launch", "downstream skill"],
            },
        ],
        "runner-control-surface": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Runner control verbs are unified",
                "given": f"{epic_ref} needs a usable operator control surface",
                "when": f"{feat_ref} is reviewed for product completeness",
                "then": "The FEAT must define one unified runner CLI control surface instead of scattering control verbs across ad-hoc scripts or undocumented commands.",
                "trace_hints": [feat_ref, "runner CLI", "control verbs", "unified surface"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Control actions preserve ownership and context",
                "given": "A runner command is issued",
                "when": "That command changes runner state",
                "then": "The FEAT must require authoritative run context and ownership guards before recording the control action result.",
                "trace_hints": [feat_ref, "ownership", "run context", "control action record"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Control surface does not replace execution semantics",
                "given": "A reviewer compares control commands with dispatch and outcome flows",
                "when": "Responsibilities are checked",
                "then": "The FEAT must keep control actions separate from ready-job emission, next-skill invocation, and execution outcome ownership.",
                "trace_hints": [feat_ref, "control surface", "dispatch boundary", "outcome boundary"],
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
        "runner-observability-surface": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Runner observability covers critical states",
                "given": f"{epic_ref} requires operators to monitor automatic progression",
                "when": f"{feat_ref} is reviewed as a product surface",
                "then": "The FEAT must make ready backlog, running, failed, deadletters, and waiting-human states visible from one authoritative monitoring surface.",
                "trace_hints": [feat_ref, "backlog", "running", "failed", "waiting-human"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Observability reads authoritative runner records",
                "given": "An operator inspects a monitored item",
                "when": "Lineage and details are resolved",
                "then": "The FEAT must trace the view back to authoritative runner records rather than directory scans or inferred status.",
                "trace_hints": [feat_ref, "authoritative records", "lineage", "no directory scan"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Observability informs but does not control",
                "given": "Monitoring surfaces and control surfaces coexist",
                "when": "Responsibilities are compared",
                "then": "The FEAT must keep observability limited to status visibility and operator decision support, without silently taking over control semantics.",
                "trace_hints": [feat_ref, "observability boundary", "control separation", "decision support"],
            },
        ],
    }.get(key, _generic_acceptance_checks(feat_ref, axis))
    if isinstance(explicit, list) and explicit:
        if len(explicit) >= 3:
            return explicit
        return explicit + checks[: max(0, 3 - len(explicit))]
    return checks


def derive_feat_axes(package: Any) -> list[dict[str, str]]:
    rollout_required = bool((package.epic_json.get("rollout_requirement") or {}).get("required"))
    required_tracks = ensure_list((package.epic_json.get("rollout_plan") or {}).get("required_feat_tracks"))
    execution_runner_epic = _is_execution_runner_epic(package)
    product_behavior_slices = package.epic_json.get("product_behavior_slices")
    if isinstance(product_behavior_slices, list) and product_behavior_slices:
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(product_behavior_slices, start=1):
            if not isinstance(item, dict):
                continue
            normalized_item = dict(item)

            # Get capability_axes first to determine primary capability for feat_axis
            capability_axes = ensure_list(item.get("capability_axes"))
            primary_capability = capability_axes[0] if capability_axes else None

            normalized_item.update(
                {
                    "id": str(item.get("id") or f"slice-{index}").strip(),
                    "name": str(item.get("name") or f"Feature Slice {index}").strip(),
                    "scope": ensure_list(item.get("scope")) or [str(item.get("scope") or item.get("name") or "").strip()],
                    "feat_axis": str(primary_capability or item.get("name") or item.get("product_surface") or f"Feature Slice {index}").strip(),
                    "goal": str(item.get("goal") or "").strip(),
                    "track": str(item.get("track") or ("adoption_e2e" if str(item.get("id") or "") == "skill-adoption-e2e" else "foundation")).strip(),
                    "product_surface": str(item.get("product_surface") or "").strip(),
                    "completed_state": str(item.get("completed_state") or "").strip(),
                    "business_deliverable": str(item.get("business_deliverable") or "").strip(),
                    "capability_axes": capability_axes,
                    "overlay_families": ensure_list(item.get("overlay_families")),
                }
            )
            if execution_runner_epic:
                normalized_item.update(_execution_runner_axis_defaults(normalized_item["id"]))
            normalized.append(normalized_item)
        if rollout_required and "adoption_e2e" in required_tracks and not any(axis_key(item) == "skill-adoption-e2e" for item in normalized):
            appended = {
                "id": "skill-adoption-e2e",
                "name": "governed skill 接入与 pilot 验证流",
                "scope": [
                    "定义 governed skill 的接入、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。",
                    "定义至少一条 producer -> consumer -> audit -> gate pilot 主链如何覆盖真实协作。",
                    "定义 adoption 成立时业务方拿到的 evidence、integration matrix 与 cutover decision。",
                ],
                "feat_axis": "governed skill 接入与验证产品界面",
                "goal": "把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。",
                "track": "adoption_e2e",
                "product_surface": "governed skill 接入与验证产品界面",
                "completed_state": "至少一条真实 pilot 链完成验证，cutover / fallback 决策可被观察。",
                "business_deliverable": "可执行的 onboarding / pilot / cutover package",
                "capability_axes": ["技能接入与跨 skill 闭环验证能力"],
                "overlay_families": ["skill_onboarding", "migration_cutover", "cross_skill_e2e_validation"],
            }
            if execution_runner_epic:
                appended.update(_execution_runner_axis_defaults("skill-adoption-e2e"))
            normalized.append(appended)
        if normalized:
            return normalized[:8]
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
        {"feat_section": "Identity and Scenario", "epic_fields": ["title", "business_goal", "scope"], "source_refs": [epic_ref] + source_refs[:3]},
        {"feat_section": "Business Flow", "epic_fields": ["scope", "product_behavior_slices", "decomposition_rules"], "source_refs": [epic_ref, str(axis.get("name") or axis.get("id") or "")]},
        {"feat_section": "Deliverables and Freeze Boundary", "epic_fields": ["constraints_and_dependencies", "non_goals", "rollout_plan"], "source_refs": [epic_ref] + source_refs[:3]},
        {"feat_section": "Acceptance and Testability", "epic_fields": ["acceptance_and_review", "decomposition_rules", "rollout_requirement"], "source_refs": [epic_ref, feat_ref]},
    ]


def feat_candidate_design_surfaces(axis: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            str(axis.get("id") or ""),
            str(axis.get("name") or ""),
            str(axis.get("scope") or ""),
            str(axis.get("feat_axis") or ""),
            str(axis.get("product_surface") or ""),
            str(axis.get("business_deliverable") or ""),
        ]
    ).lower()

    surfaces = ["architecture", "tech"]
    api_markers = ("api", "contract", "service", "interface", "endpoint", "queue", "job", "runner")
    ui_markers = ("ui", "page", "screen", "dialog", "drawer", "modal", "sheet", "form", "journey", "prototype", "shell", "conversation", "miniapp", "web", "mobile", "onboarding")

    if any(marker in text for marker in api_markers):
        surfaces.append("api")
    if any(marker in text for marker in ui_markers) or bool(axis.get("ui_required")) or bool(axis.get("requires_ui")):
        surfaces.extend(["prototype", "ui"])

    return unique_strings(surfaces)


def feat_design_impact_required(axis: dict[str, Any]) -> bool:
    explicit = axis.get("design_impact_required")
    if isinstance(explicit, bool):
        return explicit
    return True


def _normalize_surface_entries(raw_value: Any) -> list[dict[str, Any]]:
    entries = raw_value if isinstance(raw_value, list) else ensure_list(raw_value)
    normalized: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        normalized.append(
            {
                "owner": str(entry.get("owner") or "").strip(),
                "action": str(entry.get("action") or "").strip(),
                "scope": ensure_list(entry.get("scope")),
                "reason": str(entry.get("reason") or "").strip(),
                "create_signals": ensure_list(entry.get("create_signals")),
            }
        )
    return normalized


def _create_signals_for(surface_name: str, axis_id: str) -> list[str]:
    surface_defaults = {
        "architecture": ["new long-lived owner", "new subsystem boundary"],
        "api": ["new service or contract family", "future multi-feat reuse"],
        "ui": ["new independent UI shell or panel family", "future multi-feat reuse"],
        "prototype": ["new independent main flow skeleton", "future multi-feat reuse"],
        "tech": ["new reusable implementation strategy package", "future multi-feat reuse"],
    }
    execution_runner_overrides = {
        "architecture": ["new long-lived owner", "new subsystem boundary"],
        "api": ["new service or contract family", "future multi-feat reuse"],
        "ui": ["new independent UI shell or panel family", "future multi-feat reuse"],
        "prototype": ["new independent main flow skeleton", "future multi-feat reuse"],
        "tech": ["new reusable implementation strategy package", "future multi-feat reuse"],
    }
    if _is_execution_runner_epic_axis(axis_id):
        return execution_runner_overrides.get(surface_name, surface_defaults.get(surface_name, ["new long-lived owner", "future multi-feat reuse"]))
    return surface_defaults.get(surface_name, ["new long-lived owner", "future multi-feat reuse"])


def _is_execution_runner_epic_axis(axis_id: str) -> bool:
    return axis_id in {
        "ready-job-emission",
        "runner-operator-entry",
        "runner-control-surface",
        "execution-runner-intake",
        "next-skill-dispatch",
        "execution-result-feedback",
        "runner-observability-surface",
        "skill-adoption-e2e",
    }


def _execution_runner_design_surfaces(src_ref: str, feat_ref: str, axis_id: str) -> dict[str, list[dict[str, Any]]]:
    tech_owner = feat_ref.replace("FEAT-", "TECH-", 1)
    mapping: dict[str, dict[str, list[dict[str, Any]]]] = {
        "ready-job-emission": {
            "architecture": [
                {
                    "owner": "ARCH-EXECUTION-RUNNER-CORE",
                    "action": "create",
                    "scope": ["approve_to_ready_job_transition", "ready_job_authority_boundary"],
                    "reason": "SRC-003 首次定义 execution runner 的 approve-to-ready-job 主边界。",
                }
            ],
            "api": [
                {
                    "owner": "API-EXECUTION-RUNNER",
                    "action": "create",
                    "scope": ["ready_job_emission_contract"],
                    "reason": "需要新增 ready execution job 的出件契约与 authoritative refs。",
                }
            ],
            "tech": [
                {
                    "owner": tech_owner,
                    "action": "create",
                    "scope": ["ready_job_generation_rules", "approve_dispatch_persistence"],
                    "reason": "需要单独冻结 approve 后 ready job 生成规则与落盘策略。",
                }
            ],
        },
        "runner-operator-entry": {
            "architecture": [
                {
                    "owner": "ARCH-EXECUTION-RUNNER-CORE",
                    "action": "update",
                    "scope": ["runner_operator_entry_boundary"],
                    "reason": "runner 用户入口流属于 execution runner 主架构的操作入口扩展。",
                }
            ],
            "api": [
                {
                    "owner": "API-EXECUTION-RUNNER",
                    "action": "update",
                    "scope": ["runner_entry_invocation_contract"],
                    "reason": "runner 用户入口需要沿用并扩展 execution runner 调用契约。",
                }
            ],
            "ui": [
                {
                    "owner": "UI-RUNNER-OPERATOR-SHELL",
                    "action": "create",
                    "scope": ["runner_entry_panel", "entry_cta_cluster"],
                    "reason": "需要新增 runner 操作入口可视壳层，供后续控制面和监控面复用。",
                }
            ],
            "prototype": [
                {
                    "owner": "PROTO-RUNNER-OPERATOR-MAIN",
                    "action": "create",
                    "scope": ["runner_entry_flow"],
                    "reason": "需要定义 runner 用户入口主流程原型，作为 UI 壳层的体验骨架。",
                }
            ],
            "tech": [
                {
                    "owner": tech_owner,
                    "action": "update",
                    "scope": ["runner_entry_strategy", "operator_prompt_resolution"],
                    "reason": f"已有 {tech_owner} 需按 ADR042 继续承接 runner 用户入口实现策略。",
                }
            ],
        },
        "runner-control-surface": {
            "architecture": [
                {
                    "owner": "ARCH-EXECUTION-RUNNER-CORE",
                    "action": "update",
                    "scope": ["runner_control_surface_boundary"],
                    "reason": "runner 控制面流属于 execution runner 主架构的控制面扩展。",
                }
            ],
            "api": [
                {
                    "owner": "API-EXECUTION-RUNNER",
                    "action": "update",
                    "scope": ["runner_control_commands", "runner_status_projection"],
                    "reason": "控制面需要复用并扩展 runner 控制命令与状态投影契约。",
                }
            ],
            "ui": [
                {
                    "owner": "UI-RUNNER-OPERATOR-SHELL",
                    "action": "update",
                    "scope": ["runner_control_panel", "decision_controls"],
                    "reason": "控制面是既有 runner operator shell 上的增量面板。",
                }
            ],
            "prototype": [
                {
                    "owner": "PROTO-RUNNER-OPERATOR-MAIN",
                    "action": "update",
                    "scope": ["runner_control_flow"],
                    "reason": "控制面流程是在已有 runner operator 主流程上的扩展。",
                }
            ],
            "tech": [
                {
                    "owner": tech_owner,
                    "action": "create",
                    "scope": ["control_surface_state_machine", "manual_override_rules"],
                    "reason": "控制面需要独立实现策略包来约束状态切换与人工干预。",
                }
            ],
        },
        "execution-runner-intake": {
            "architecture": [
                {
                    "owner": "ARCH-EXECUTION-RUNNER-CORE",
                    "action": "update",
                    "scope": ["runner_intake_loop"],
                    "reason": "自动取件流是 execution runner 核心循环的一部分。",
                }
            ],
            "api": [
                {
                    "owner": "API-EXECUTION-RUNNER",
                    "action": "update",
                    "scope": ["ready_job_intake_contract"],
                    "reason": "自动取件需要复用 ready job intake 读写契约。",
                }
            ],
            "tech": [
                {
                    "owner": tech_owner,
                    "action": "create",
                    "scope": ["intake_polling_rules", "queue_claiming_strategy"],
                    "reason": "自动取件需要单独冻结轮询、claim 与去重策略。",
                }
            ],
        },
        "next-skill-dispatch": {
            "architecture": [
                {
                    "owner": "ARCH-EXECUTION-RUNNER-CORE",
                    "action": "update",
                    "scope": ["downstream_dispatch_boundary"],
                    "reason": "自动派发流是 execution runner 的下游派发边界扩展。",
                }
            ],
            "api": [
                {
                    "owner": "API-EXECUTION-RUNNER",
                    "action": "update",
                    "scope": ["skill_dispatch_contract"],
                    "reason": "下游 skill 自动派发需要扩展 dispatch 契约与 next skill binding。",
                }
            ],
            "tech": [
                {
                    "owner": tech_owner,
                    "action": "create",
                    "scope": ["dispatch_routing_rules", "skill_resolution_strategy"],
                    "reason": "自动派发需要单独的路由与 skill 解析实现策略。",
                }
            ],
        },
        "execution-result-feedback": {
            "architecture": [
                {
                    "owner": "ARCH-EXECUTION-RUNNER-CORE",
                    "action": "update",
                    "scope": ["feedback_and_retry_boundary"],
                    "reason": "执行结果回写与重试边界属于 execution runner 核心闭环的一部分。",
                }
            ],
            "api": [
                {
                    "owner": "API-EXECUTION-RUNNER",
                    "action": "update",
                    "scope": ["execution_feedback_contract", "retry_state_contract"],
                    "reason": "结果回写与重试需要扩展执行反馈与 retry 契约。",
                }
            ],
            "tech": [
                {
                    "owner": tech_owner,
                    "action": "update",
                    "scope": ["result_writeback_rules", "retry_boundary_strategy"],
                    "reason": f"已有 {tech_owner} 需按 ADR042 继续承接回写与重试边界实现策略。",
                }
            ],
        },
        "runner-observability-surface": {
            "architecture": [
                {
                    "owner": "ARCH-EXECUTION-RUNNER-CORE",
                    "action": "update",
                    "scope": ["runner_observability_boundary"],
                    "reason": "运行监控流属于 execution runner 主架构的观测面扩展。",
                }
            ],
            "api": [
                {
                    "owner": "API-EXECUTION-RUNNER",
                    "action": "update",
                    "scope": ["runner_metrics_projection", "runner_incident_queries"],
                    "reason": "运行监控需要扩展 runner 指标投影与事件查询契约。",
                }
            ],
            "ui": [
                {
                    "owner": "UI-RUNNER-OPERATOR-SHELL",
                    "action": "update",
                    "scope": ["runner_monitoring_panel", "incident_overview_card"],
                    "reason": "运行监控是既有 runner operator shell 上的观测面增量。",
                }
            ],
            "prototype": [
                {
                    "owner": "PROTO-RUNNER-OPERATOR-MAIN",
                    "action": "update",
                    "scope": ["runner_monitoring_flow"],
                    "reason": "运行监控流程是在已有 runner operator 主流程上的扩展。",
                }
            ],
            "tech": [
                {
                    "owner": tech_owner,
                    "action": "create",
                    "scope": ["monitoring_snapshot_rules", "incident_summary_strategy"],
                    "reason": "运行监控需要独立实现策略来汇总 runner 状态与异常视图。",
                }
            ],
        },
        "skill-adoption-e2e": {
            "architecture": [
                {
                    "owner": "ARCH-EXECUTION-RUNNER-CORE",
                    "action": "update",
                    "scope": ["governed_skill_integration_boundary"],
                    "reason": "governed skill 接入与 pilot 验证流属于 execution runner 的集成边界扩展。",
                }
            ],
            "api": [
                {
                    "owner": "API-EXECUTION-RUNNER",
                    "action": "update",
                    "scope": ["governed_skill_binding_contract", "pilot_validation_contract"],
                    "reason": "接入 governed skill 需要扩展 skill binding 与 pilot 验证契约。",
                }
            ],
            "tech": [
                {
                    "owner": tech_owner,
                    "action": "create",
                    "scope": ["governed_skill_registry_strategy", "pilot_validation_rules"],
                    "reason": "governed skill 接入需要独立实现策略来处理 registry 绑定与 pilot 校验。",
                }
            ],
        },
    }
    result = mapping.get(axis_id, {})
    for entries in result.values():
        for entry in entries:
            if entry["action"] == "create" and not entry.get("create_signals"):
                entry["create_signals"] = _create_signals_for(
                    next(key for key, value in result.items() if entry in value),
                    axis_id,
                )
    return result


def feat_design_surfaces(package: Any, feat_ref: str, axis: dict[str, Any], candidate_design_surfaces: list[str]) -> dict[str, list[dict[str, Any]]]:
    explicit = axis.get("design_surfaces")
    if isinstance(explicit, dict) and explicit:
        normalized = {
            key: _normalize_surface_entries(explicit.get(key))
            for key in ("architecture", "api", "ui", "prototype", "tech")
            if explicit.get(key) is not None
        }
    elif _is_execution_runner_epic(package):
        normalized = _execution_runner_design_surfaces(choose_src_ref(package), feat_ref, axis_key(axis))
    else:
        src_ref = choose_src_ref(package)
        owner_defaults = {
            "architecture": f"ARCH-{src_ref}-CORE",
            "api": f"API-{src_ref}",
            "ui": f"UI-{src_ref}-MAIN",
            "prototype": f"PROTO-{src_ref}-MAIN",
            "tech": feat_ref.replace("FEAT-", "TECH-", 1),
        }
        normalized = {}
        for surface_name in candidate_design_surfaces:
            normalized[surface_name] = [
                {
                    "owner": owner_defaults.get(surface_name, feat_ref.replace("FEAT-", f"{surface_name.upper()}-", 1)),
                    "action": "create",
                    "scope": feat_scope(axis, package)[:2] or [feat_title(axis, package)],
                    "reason": f"{feat_title(axis, package)} 需要显式承接 {surface_name} 设计归属。",
                    "create_signals": _create_signals_for(surface_name, axis_key(axis)),
                }
            ]
    for surface_name, entries in normalized.items():
        for entry in entries:
            if entry.get("action") == "create" and not ensure_list(entry.get("create_signals")):
                entry["create_signals"] = _create_signals_for(surface_name, axis_key(axis))
    return normalized


def build_feat_record(package: Any, axis: dict[str, str], index: int) -> dict[str, Any]:
    src_ref = choose_src_ref(package)
    epic_ref = choose_epic_ref(package)
    feat_ref = f"FEAT-{src_ref}-{index:03d}"
    source_refs = unique_strings([epic_ref, src_ref] + bundle_source_refs(package))
    title = feat_title(axis, package)
    goal = feat_goal(axis, package)
    scope = feat_scope(axis, package)
    dependencies = feat_dependencies(axis, package)
    non_goals = feat_non_goals(axis, package)
    constraints = feat_constraints(axis, package)
    acceptance_checks = build_acceptance_checks(feat_ref, epic_ref, axis)
    candidate_design_surfaces = feat_candidate_design_surfaces(axis)
    design_impact_required = feat_design_impact_required(axis)
    design_surfaces = feat_design_surfaces(package, feat_ref, axis, candidate_design_surfaces) if design_impact_required else {}
    ui_required = "ui" in candidate_design_surfaces or "prototype" in candidate_design_surfaces
    return {
        "feat_ref": feat_ref,
        "title": title,
        "axis_id": axis_key(axis),
        "slice_id": str(axis.get("id") or axis_key(axis)),
        "track": feat_track(axis),
        "derived_axis": axis.get("feat_axis"),
        "cross_cutting_capability_axes": ensure_list(axis.get("capability_axes")),
        "overlay_families": ensure_list(axis.get("overlay_families")),
        "epic_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "source_refs": source_refs,
        "goal": goal,
        "business_value": feat_business_value(axis, package),
        "scope": scope,
        "inputs": [
            f"Authoritative EPIC package {epic_ref}",
            f"src_root_id {package.epic_json.get('src_root_id')}",
            "Inherited scope, constraints, rollout requirements, and acceptance semantics",
        ],
        "processing": [
            "Translate the parent EPIC product behavior slice into one independently acceptable FEAT with a dedicated product interface, completed state, and boundary statement.",
            "Preserve parent-child traceability while separating this FEAT's concern from adjacent FEATs and rollout overlays.",
            "Emit FEAT-specific business flow, deliverable, constraints, and acceptance checks that can seed downstream TECH and TESTSET derivation.",
        ],
        "outputs": [
            f"Frozen FEAT product slice for {feat_ref}",
            "FEAT-specific acceptance checks for downstream TECH and TESTSET derivation",
            "Traceable handoff metadata for downstream governed TECH and TESTSET workflows",
        ],
        "dependencies": dependencies,
        "non_goals": non_goals,
        "constraints": constraints,
        "acceptance_checks": acceptance_checks,
        "design_impact_required": design_impact_required,
        "candidate_design_surfaces": candidate_design_surfaces,
        "surface_map_required_reason": "ADR042 requires a surface-map freeze before downstream design derivation." if design_impact_required else "No shared design asset impact was declared for this FEAT.",
        "design_surfaces": design_surfaces,
        "ui_required": ui_required,
        "identity_and_scenario": {
            "product_interface": feat_product_interface(axis),
            "completed_state": feat_completed_state(axis),
            "primary_actor": feat_primary_actor(axis),
            "secondary_actors": feat_secondary_actors(axis),
            "user_story": feat_user_story(axis),
            "trigger": feat_trigger(axis),
            "preconditions": feat_preconditions(axis),
            "postconditions": feat_postconditions(axis),
        },
        "business_flow": {
            "main_flow": feat_main_flow(axis),
            "alternate_flows": feat_alternate_flows(axis),
            "exception_flows": feat_exception_flows(axis),
            "business_rules": feat_business_rules(axis, package),
            "business_state_transitions": feat_business_state_transitions(axis),
        },
        "product_objects_and_deliverables": {
            "input_objects": feat_input_objects(axis),
            "output_objects": feat_output_objects(axis),
            "required_deliverables": feat_required_deliverables(axis),
            "authoritative_output": feat_authoritative_output(axis),
            "business_deliverable": feat_business_deliverable(axis),
            "governance_intermediates": feat_governance_intermediates(axis),
            "evidence_audit_trail": feat_evidence_audit_trail(axis),
        },
        "collaboration_and_timeline": {
            "role_responsibility_split": feat_role_responsibility_split(axis),
            "handoff_points": feat_handoff_points(axis),
            "interaction_timeline": feat_interaction_timeline(axis),
            "business_sequence": feat_business_sequence(axis),
            "loop_gate_human_involvement": feat_loop_gate_human_involvement(axis),
        },
        "acceptance_and_testability": {
            "acceptance_criteria": [check["then"] for check in acceptance_checks],
            "observable_outcomes": feat_observable_outcomes(axis),
            "test_dimensions": feat_test_dimensions(axis),
            "out_of_scope": non_goals,
        },
        "frozen_downstream_boundary": {
            "frozen_product_shape": feat_frozen_product_shape(axis),
            "frozen_business_semantics": feat_frozen_business_semantics(axis),
            "open_technical_decisions": feat_open_technical_decisions(axis),
            "explicit_non_decisions": feat_explicit_non_decisions(axis),
        },
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


def _feat_relations_for(axis_id: str) -> dict[str, Any]:
    mapping = {
        "ready-job-emission": {
            "upstream_axis_ids": [],
            "downstream_axis_ids": ["runner-operator-entry"],
            "gate_decision_axis_ids": [],
            "admission_dependency_axis_ids": [],
            "consumes": ["approve decision", "dispatch context", "next-skill target"],
            "produces": ["ready execution job", "approve-to-job lineage", "ready queue record"],
            "authoritative_artifact": "ready execution job",
            "gate_decision_dependency": "owned by this FEAT; it binds approve semantics to ready-job emission instead of formal publication",
            "admission_dependency": "none; downstream progression starts from runner intake, not admission",
        },
        "runner-operator-entry": {
            "upstream_axis_ids": ["ready-job-emission"],
            "downstream_axis_ids": ["runner-control-surface"],
            "gate_decision_axis_ids": ["ready-job-emission"],
            "admission_dependency_axis_ids": [],
            "consumes": ["ready execution job", "runner start request", "authoritative run scope"],
            "produces": ["runner skill invocation record", "runner context initialization result", "runner start receipt"],
            "authoritative_artifact": "runner skill entry invocation record",
            "gate_decision_dependency": "depends on approve-driven ready-job emission because the runner entry exists to launch or resume consumption of authoritative ready jobs",
            "admission_dependency": "none; runner entry belongs to execution semantics rather than formal publication or admission",
        },
        "runner-control-surface": {
            "upstream_axis_ids": ["runner-operator-entry"],
            "downstream_axis_ids": ["execution-runner-intake"],
            "gate_decision_axis_ids": ["ready-job-emission"],
            "admission_dependency_axis_ids": [],
            "consumes": ["runner skill invocation record", "runner command request", "run context"],
            "produces": ["runner control action record", "runner state update", "control evidence"],
            "authoritative_artifact": "runner control action record",
            "gate_decision_dependency": "control surface exists to operate approve-derived runner progression; it may not replace or bypass ready-job emission",
            "admission_dependency": "none; runner control actions remain inside execution semantics",
        },
        "execution-runner-intake": {
            "upstream_axis_ids": ["runner-control-surface"],
            "downstream_axis_ids": ["next-skill-dispatch", "runner-observability-surface"],
            "gate_decision_axis_ids": ["ready-job-emission"],
            "admission_dependency_axis_ids": [],
            "consumes": ["ready execution job", "ready queue ownership context"],
            "produces": ["claimed execution job", "running ownership record", "claim evidence"],
            "authoritative_artifact": "claimed execution job",
            "gate_decision_dependency": "requires the ready-job FEAT to emit authoritative jobs into artifacts/jobs/ready before claim can begin",
            "admission_dependency": "none; runner intake must not be replaced by formal publication or admission",
        },
        "next-skill-dispatch": {
            "upstream_axis_ids": ["execution-runner-intake"],
            "downstream_axis_ids": ["execution-result-feedback", "runner-observability-surface"],
            "gate_decision_axis_ids": ["ready-job-emission"],
            "admission_dependency_axis_ids": [],
            "consumes": ["claimed execution job", "authoritative input package", "target skill ref"],
            "produces": ["next-skill invocation", "execution attempt record", "dispatch lineage"],
            "authoritative_artifact": "next-skill invocation record",
            "gate_decision_dependency": "approve-derived jobs claimed by runner are the only source for automatic next-skill dispatch",
            "admission_dependency": "none; dispatch must stay in execution semantics rather than formal publication",
        },
        "execution-result-feedback": {
            "upstream_axis_ids": ["next-skill-dispatch"],
            "downstream_axis_ids": ["runner-observability-surface"],
            "gate_decision_axis_ids": ["ready-job-emission"],
            "admission_dependency_axis_ids": [],
            "consumes": ["execution attempt record", "downstream skill result", "runner state"],
            "produces": ["execution outcome", "retry-reentry directive", "failure evidence"],
            "authoritative_artifact": "execution outcome record",
            "gate_decision_dependency": "approve starts the automatic progression chain, but this FEAT owns the post-dispatch done/failed/retry outcomes",
            "admission_dependency": "none; post-dispatch results remain execution outcomes, not admission results",
        },
        "runner-observability-surface": {
            "upstream_axis_ids": ["execution-runner-intake", "next-skill-dispatch", "execution-result-feedback"],
            "downstream_axis_ids": [],
            "gate_decision_axis_ids": ["ready-job-emission"],
            "admission_dependency_axis_ids": [],
            "consumes": ["claimed execution job", "running ownership record", "dispatch lineage", "execution outcome record"],
            "produces": ["runner observability snapshot", "backlog view", "failed/waiting-human view"],
            "authoritative_artifact": "runner observability snapshot",
            "gate_decision_dependency": "observability exists to show the state of approve-derived runner progression after ready-job emission",
            "admission_dependency": "none; observability reads execution state rather than formal publication or admission state",
        },
        "collaboration-loop": {
            "upstream_axis_ids": [],
            "downstream_axis_ids": ["handoff-formalization"],
            "gate_decision_axis_ids": ["handoff-formalization"],
            "admission_dependency_axis_ids": ["object-layering"],
            "consumes": ["candidate package", "proposal", "evidence"],
            "produces": ["authoritative handoff submission", "handoff trace ref", "gate pending visibility result"],
            "authoritative_artifact": "authoritative handoff submission",
            "gate_decision_dependency": "depends on FEAT handoff-formalization to turn gate-pending handoff into approve / revise / retry / handoff / reject business results",
            "admission_dependency": "formal admission is out of scope until FEAT object-layering publishes a formal package",
        },
        "handoff-formalization": {
            "upstream_axis_ids": ["collaboration-loop"],
            "downstream_axis_ids": ["object-layering"],
            "gate_decision_axis_ids": [],
            "admission_dependency_axis_ids": ["object-layering"],
            "consumes": ["authoritative handoff submission", "proposal", "evidence"],
            "produces": ["authoritative decision object", "delegation directive", "formal publication trigger"],
            "authoritative_artifact": "authoritative decision object",
            "gate_decision_dependency": "owned by this FEAT; it is the only slice that defines approve / revise / retry / handoff / reject vocabulary",
            "admission_dependency": "approve decisions emitted here are the only business-level prerequisite for downstream formal publication and admission",
        },
        "object-layering": {
            "upstream_axis_ids": ["handoff-formalization"],
            "downstream_axis_ids": ["artifact-io-governance", "skill-adoption-e2e"],
            "gate_decision_axis_ids": ["handoff-formalization"],
            "admission_dependency_axis_ids": [],
            "consumes": ["authoritative decision object", "approval lineage context"],
            "produces": ["formal publication package", "formal object", "formal ref-lineage package", "admission verdict"],
            "authoritative_artifact": "formal publication package",
            "gate_decision_dependency": "requires an approve decision object from FEAT handoff-formalization before formal publication can begin",
            "admission_dependency": "owned by this FEAT; downstream consumers must resolve formal refs and lineage through admission before use",
        },
        "artifact-io-governance": {
            "upstream_axis_ids": ["collaboration-loop", "handoff-formalization", "object-layering"],
            "downstream_axis_ids": ["skill-adoption-e2e"],
            "gate_decision_axis_ids": ["handoff-formalization"],
            "admission_dependency_axis_ids": ["object-layering"],
            "consumes": ["authoritative handoff submission", "authoritative decision object", "formal publication package", "write-read intent"],
            "produces": ["governed write-read receipt", "registry record-managed ref", "rejected write-read result"],
            "authoritative_artifact": "governed write-read receipt",
            "gate_decision_dependency": "consumes decision-owned artifacts but must not redefine gate decision vocabulary or approval authority",
            "admission_dependency": "managed refs and governed reads emitted here must still honor downstream admission and formal-ref rules",
        },
        "skill-adoption-e2e": {
            "upstream_axis_ids": ["collaboration-loop", "handoff-formalization", "object-layering", "artifact-io-governance"],
            "downstream_axis_ids": [],
            "gate_decision_axis_ids": ["handoff-formalization"],
            "admission_dependency_axis_ids": ["object-layering"],
            "consumes": ["authoritative handoff submission", "authoritative decision object", "formal publication package", "governed write-read result", "integration scope"],
            "produces": ["integration matrix", "pilot evidence package", "cutover fallback decision"],
            "authoritative_artifact": "pilot evidence package",
            "gate_decision_dependency": "depends on the foundation gate decision flow being usable in a real pilot chain",
            "admission_dependency": "depends on formal publication and admission behavior from FEAT object-layering before cutover can be trusted",
        },
    }
    return mapping.get(
        axis_id,
        {
            "upstream_axis_ids": [],
            "downstream_axis_ids": [],
            "gate_decision_axis_ids": [],
            "admission_dependency_axis_ids": [],
            "consumes": [],
            "produces": [],
            "authoritative_artifact": "",
            "gate_decision_dependency": "none",
            "admission_dependency": "none",
        },
    )


def apply_feature_relationships(feats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axis_to_ref = {str(feat.get("axis_id") or ""): str(feat.get("feat_ref") or "") for feat in feats}
    execution_runner_bundle = "ready-job-emission" in axis_to_ref and "execution-result-feedback" in axis_to_ref
    for feat in feats:
        relations = _feat_relations_for(str(feat.get("axis_id") or ""))
        if execution_runner_bundle and str(feat.get("axis_id") or "") == "skill-adoption-e2e":
            relations = {
                "upstream_axis_ids": [
                    "ready-job-emission",
                    "runner-operator-entry",
                    "runner-control-surface",
                    "execution-runner-intake",
                    "next-skill-dispatch",
                    "execution-result-feedback",
                    "runner-observability-surface",
                ],
                "downstream_axis_ids": [],
                "gate_decision_axis_ids": ["ready-job-emission"],
                "admission_dependency_axis_ids": [],
                "consumes": [
                    "ready execution job",
                    "runner skill entry invocation record",
                    "runner control action record",
                    "claimed execution job",
                    "next-skill invocation record",
                    "execution outcome record",
                    "runner observability snapshot",
                    "integration scope",
                ],
                "produces": ["integration matrix", "pilot evidence package", "cutover fallback decision"],
                "authoritative_artifact": "pilot evidence package",
                "gate_decision_dependency": "depends on approve-driven ready-job emission being usable in a real pilot chain",
                "admission_dependency": "none; rollout validation depends on runner outcomes rather than formal publication or admission",
            }
        upstream_feat_refs = [axis_to_ref[item] for item in relations["upstream_axis_ids"] if axis_to_ref.get(item)]
        downstream_feat_refs = [axis_to_ref[item] for item in relations["downstream_axis_ids"] if axis_to_ref.get(item)]
        feat["upstream_feat"] = upstream_feat_refs
        feat["downstream_feat"] = downstream_feat_refs
        feat["consumes"] = relations["consumes"]
        feat["produces"] = relations["produces"]
        feat["authoritative_artifact"] = relations["authoritative_artifact"] or feat["product_objects_and_deliverables"]["authoritative_output"]
        feat["gate_decision_dependency"] = relations["gate_decision_dependency"]
        feat["admission_dependency"] = relations["admission_dependency"]
        feat["gate_decision_dependency_feat_refs"] = [axis_to_ref[item] for item in relations["gate_decision_axis_ids"] if axis_to_ref.get(item)]
        feat["admission_dependency_feat_refs"] = [axis_to_ref[item] for item in relations["admission_dependency_axis_ids"] if axis_to_ref.get(item)]
        feat["dependency_kinds"] = {
            "upstream_feat": "product_flow_predecessor",
            "downstream_feat": "product_flow_successor",
            "gate_decision_dependency_feat_refs": "gate_decision_source",
            "admission_dependency_feat_refs": "admission_or_publication_source",
        }
    return feats


def canonical_glossary(feats: list[dict[str, Any]]) -> list[dict[str, str]]:
    axis_to_ref = {str(feat.get("axis_id") or ""): str(feat.get("feat_ref") or "") for feat in feats}
    if "ready-job-emission" in axis_to_ref:
        return [
            {
                "term": "ready execution job",
                "canonical_meaning": "Authoritative job emitted after approve and written into artifacts/jobs/ready for automatic runner consumption.",
                "owned_by_feat": axis_to_ref.get("ready-job-emission", ""),
                "must_not_be_confused_with": "formal publication package",
            },
            {
                "term": "runner skill entry",
                "canonical_meaning": "Dedicated Execution Loop Job Runner skill surface used by Claude/Codex CLI operators to start or resume the automatic progression runtime.",
                "owned_by_feat": axis_to_ref.get("runner-operator-entry", ""),
                "must_not_be_confused_with": "manual downstream skill relay",
            },
            {
                "term": "runner CLI control surface",
                "canonical_meaning": "Authoritative CLI command surface used to control runner start, resume, claim, run, complete, and fail behavior within the governed execution loop.",
                "owned_by_feat": axis_to_ref.get("runner-control-surface", ""),
                "must_not_be_confused_with": "ad-hoc scripts",
            },
            {
                "term": "runner claim",
                "canonical_meaning": "Single-owner intake step where Execution Loop Job Runner claims a ready job and records running ownership.",
                "owned_by_feat": axis_to_ref.get("execution-runner-intake", ""),
                "must_not_be_confused_with": "manual relay",
            },
            {
                "term": "next-skill invocation",
                "canonical_meaning": "Authoritative dispatch record showing which governed skill was invoked from a claimed execution job.",
                "owned_by_feat": axis_to_ref.get("next-skill-dispatch", ""),
                "must_not_be_confused_with": "directory scan trigger",
            },
            {
                "term": "execution outcome",
                "canonical_meaning": "Authoritative done, failed, or retry-reentry result emitted after runner dispatch completes.",
                "owned_by_feat": axis_to_ref.get("execution-result-feedback", ""),
                "must_not_be_confused_with": "approve terminal state",
            },
            {
                "term": "runner observability surface",
                "canonical_meaning": "Authoritative monitoring view for ready backlog, running, failed, deadletters, and waiting-human states across runner progression.",
                "owned_by_feat": axis_to_ref.get("runner-observability-surface", ""),
                "must_not_be_confused_with": "directory scan dashboard",
            },
        ]
    return [
        {
            "term": "candidate",
            "canonical_meaning": "Pre-decision governed package emitted before any authoritative gate decision exists.",
            "owned_by_feat": axis_to_ref.get("collaboration-loop", ""),
            "must_not_be_confused_with": "formal object",
        },
        {
            "term": "handoff submission",
            "canonical_meaning": "Authoritative submission that puts the candidate into the gate-consumable pending state.",
            "owned_by_feat": axis_to_ref.get("collaboration-loop", ""),
            "must_not_be_confused_with": "decision object",
        },
        {
            "term": "decision object",
            "canonical_meaning": "Authoritative gate result carrying approve / revise / retry / handoff / reject semantics.",
            "owned_by_feat": axis_to_ref.get("handoff-formalization", ""),
            "must_not_be_confused_with": "handoff submission",
        },
        {
            "term": "formal object",
            "canonical_meaning": "Published formal output produced only after an approve decision enables formal publication.",
            "owned_by_feat": axis_to_ref.get("object-layering", ""),
            "must_not_be_confused_with": "candidate",
        },
        {
            "term": "formal ref",
            "canonical_meaning": "Authoritative downstream reference that points to a formal object eligible for admission.",
            "owned_by_feat": axis_to_ref.get("object-layering", ""),
            "must_not_be_confused_with": "managed ref",
        },
        {
            "term": "lineage",
            "canonical_meaning": "Authoritative relation linking candidate, decision object, and formal publication package.",
            "owned_by_feat": axis_to_ref.get("object-layering", ""),
            "must_not_be_confused_with": "receipt",
        },
        {
            "term": "managed ref",
            "canonical_meaning": "Governed IO reference produced by the receipt/registry path for managed reads and writes.",
            "owned_by_feat": axis_to_ref.get("artifact-io-governance", ""),
            "must_not_be_confused_with": "formal ref",
        },
        {
            "term": "receipt",
            "canonical_meaning": "Authoritative governed IO result recording what write/read happened and under which governance boundary.",
            "owned_by_feat": axis_to_ref.get("artifact-io-governance", ""),
            "must_not_be_confused_with": "lineage",
        },
        {
            "term": "admission",
            "canonical_meaning": "Eligibility check that allows a downstream consumer to use a formal object through formal refs and lineage.",
            "owned_by_feat": axis_to_ref.get("object-layering", ""),
            "must_not_be_confused_with": "path guessing",
        },
    ]


def prohibited_inference_rules() -> list[dict[str, Any]]:
    return [
        {
            "id": "no-formal-publication-substitution",
            "applies_to": ["TECH", "TESTSET", "consumer"],
            "rule": "Downstream work must not rewrite approve-driven automatic progression as formal publication, admission, or publish-only completion.",
            "protected_fields": ["business_sequence", "authoritative_artifact", "acceptance_criteria"],
        },
        {
            "id": "no-tech-product-shape-redefinition",
            "applies_to": ["TECH"],
            "rule": "TECH must not redefine product_interface, completed_state, business_deliverable, or authoritative_output that are already frozen by FEAT.",
            "protected_fields": ["product_interface", "completed_state", "business_deliverable", "authoritative_output"],
        },
        {
            "id": "no-testset-alternate-formal-input",
            "applies_to": ["TESTSET"],
            "rule": "TESTSET must not invent alternate formal inputs or bypass authoritative_output when deriving formal-consumption tests.",
            "protected_fields": ["authoritative_output", "required_deliverables", "acceptance_criteria"],
        },
        {
            "id": "no-task-candidate-as-formal-deliverable",
            "applies_to": ["TASK"],
            "rule": "TASK must not treat candidate package, proposal, evidence, or intermediate objects as formal deliverables.",
            "protected_fields": ["required_deliverables", "authoritative_output", "completed_state"],
        },
        {
            "id": "no-consumer-path-guessing",
            "applies_to": ["TECH", "TESTSET", "TASK", "consumer"],
            "rule": "Downstream consumers must not replace admission, formal refs, or managed refs with path guessing, adjacent file discovery, or free-form directory scans.",
            "protected_fields": ["consumes", "authoritative_artifact", "admission_dependency"],
        },
    ]


def derive_bundle_intent(package: Any, feats: list[dict[str, Any]]) -> str:
    epic_ref = choose_epic_ref(package)
    axis_titles = "、".join(feat["title"] for feat in feats)
    rollout_required = bool((package.epic_json.get("rollout_requirement") or {}).get("required"))
    if rollout_required:
        return (
            f"Decompose {epic_ref} into {len(feats)} complementary product-behavior FEAT slices so that foundation capability constraints and adoption/E2E landing work "
            f"are both explicit. The bundle keeps {axis_titles} as independently acceptable FEATs, because the parent EPIC now requires both "
            "product-ready behavior slices and real governed-skill landing. Fewer FEATs would collapse foundation and adoption concerns together, "
            "while more FEATs would prematurely drift into TASK or implementation detail."
        )
    return (
        f"Decompose {epic_ref} into {len(feats)} complementary product-behavior FEAT slices so that each slice owns a distinct product surface, completed state, and authoritative deliverable. "
        f"The bundle keeps {axis_titles} as independently acceptable FEATs while capability axes remain cross-cutting constraints; fewer FEATs would merge "
        "incompatible acceptance semantics, while more FEATs would prematurely split into task or implementation detail."
    )
