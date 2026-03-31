#!/usr/bin/env python3
"""Unit derivation helpers for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_collaboration import collaboration_units as collaboration_units_impl
from feat_to_testset_common import ensure_list
from feat_to_testset_runner_units import (
    runner_control_surface_units,
    runner_dispatch_units,
    runner_feedback_units,
    runner_intake_units,
    runner_observability_units,
    runner_operator_entry_units,
    runner_ready_job_units,
)
from feat_to_testset_units_common import unit_payload


def _check_ref(checks: list[dict[str, Any]], feat_ref: str, index: int) -> str:
    if 0 <= index - 1 < len(checks):
        return str(checks[index - 1].get("id") or f"{feat_ref}-AC-{index:02d}")
    return f"{feat_ref}-AC-{index:02d}"


def _check_field(checks: list[dict[str, Any]], index: int, key: str, default: str) -> str:
    if 0 <= index - 1 < len(checks):
        return str(checks[index - 1].get(key) or default)
    return default


def default_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    units: list[dict[str, Any]] = []
    for index, check in enumerate(feature.get("acceptance_checks") or [], start=1):
        acceptance_ref = str(check.get("id") or f"{feat_ref}-AC-{index:02d}")
        units.append(
            unit_payload(
                feat_ref=feat_ref,
                index=index,
                acceptance_ref=acceptance_ref,
                title=str(check.get("scenario") or f"Acceptance check {index}"),
                priority=priority,
                layers=layers,
                input_preconditions=[
                    str(check.get("given") or "上游 FEAT 前置条件满足。"),
                    *ensure_list(feature.get("dependencies"))[:2],
                ],
                trigger_action=str(check.get("when") or "执行该 acceptance 对应的产品行为。"),
                observation_points=[
                    str(check.get("then") or ""),
                    "记录与主对象、handoff、gate subject 对应的可观察结果。",
                ],
                pass_conditions=[
                    str(check.get("then") or "Acceptance 结果成立。"),
                    "输出与 selected FEAT 保持单一边界，不引入并行真相。",
                ],
                fail_conditions=[
                    "缺少 acceptance 对应 evidence。",
                    "观测结果与 FEAT acceptance 或主对象边界不一致。",
                ],
                required_evidence=[
                    f"{acceptance_ref} 对应的执行结果证据",
                    "失败时的最小可审计上下文",
                ],
                supporting_refs=refs + ensure_list(check.get("trace_hints")),
            )
        )
    return units


def minimal_onboarding_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = list(feature.get("acceptance_checks") or [])
    return [
        unit_payload(feat_ref, 1, _check_ref(checks, feat_ref, 1), "最小建档必填字段校验通过后写下 profile_minimal_done 并立即放行首页", priority, layers, [_check_field(checks, 1, "given", "登录/注册已完成。"), "最小建档页已可提交。"], "提交包含 gender、birthdate、height、weight、running_level、recent_injury_status 的最小建档表单。", ["profile_minimal_done", "homepage entry allowed", "canonical minimal profile fields。"], ["必填字段全部通过后写下 profile_minimal_done。", "用户立即进入首页，且设备连接保持后置。"], ["必填字段通过但未写下 profile_minimal_done。", "提交成功后仍被阻塞在首页外。"], ["minimal profile submission evidence", "homepage entry decision evidence", "canonical field write evidence"], refs + ["profile_minimal_done", "birthdate", "running_level", "recent_injury_status", "homepage entry"]),
        unit_payload(feat_ref, 2, _check_ref(checks, feat_ref, 2), "必填字段缺失或非法时停留在单页最小建档并返回字段级错误", priority, layers, [_check_field(checks, 2, "given", "birthdate 或必填字段缺失/非法。")], "提交缺失或非法的最小建档表单。", ["field-level errors", "homepage entry blocked", "page stays on minimal onboarding。"], ["字段级错误可见，且 homepage entry 继续被阻止。", "不会跳过单页最小建档直接进入首页。"], ["缺失/非法字段仍可进入首页。", "错误只在日志出现而页面无可见反馈。"], ["validation failure evidence", "field-error snapshot", "homepage blocked verdict"], refs + ["field-level errors", "homepage blocked"]),
        unit_payload(feat_ref, 3, _check_ref(checks, feat_ref, 3), "birthdate 保持 canonical 年龄字段且设备连接仍为 deferred follow-up", priority, layers, ["最小建档提交成功。", "设备连接入口已配置为 follow-up path。"], "检查 canonical 字段写入与设备入口展示时机。", ["birthdate canonical write", "deferred device entry", "homepage visible state。"], ["birthdate 作为 canonical 年龄字段被写入。", "设备连接只在首页后作为 deferred follow-up entry 出现。"], ["使用非 canonical 年龄字段判断完成态。", "设备连接重新变成首进阻塞前置。"], ["canonical birthdate evidence", "deferred device entry evidence", "homepage-visible trace"], refs + ["birthdate", "deferred device entry"]),
    ]


def first_ai_advice_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = list(feature.get("acceptance_checks") or [])
    return [
        unit_payload(feat_ref, 1, _check_ref(checks, feat_ref, 1), "最小输入满足时释放首轮建议并补齐最低输出字段", priority, layers, [_check_field(checks, 1, "given", "minimal profile 已完成且风险输入齐全。")], "触发首页首轮建议生成。", ["training_advice_level", "first_week_action", "needs_more_info_prompt", "device_connect_prompt。"], ["首轮建议可见，且最低输出字段齐全。", "生成路径只依赖 minimal profile + risk gate 输入。"], ["首轮建议可见但最低输出字段不完整。", "要求扩展画像或设备数据才能出首轮建议。"], ["first advice payload evidence", "advice visibility evidence", "minimum-output snapshot"], refs + ["training_advice_level", "first_week_action", "needs_more_info_prompt", "device_connect_prompt"]),
        unit_payload(feat_ref, 2, _check_ref(checks, feat_ref, 2), "running_level 或 recent_injury_status 缺失时阻断正常建议分支并进入补充提示", priority, layers, [_check_field(checks, 2, "given", "risk gate 关键字段缺失。")], "在缺少 running_level 或 recent_injury_status 的情况下触发首轮建议。", ["risk gate verdict", "normal advice blocked", "completion prompt visible。"], ["正常 advice branch 被阻断，并显示补充提示。", "不会伪造 training_advice_level / first_week_action 作为正常建议。"], ["risk gate 缺字段仍放行正常建议。", "缺少补充提示或 fallback evidence。"], ["risk gate verdict evidence", "blocked normal-advice evidence", "completion prompt evidence"], refs + ["running_level", "recent_injury_status", "risk gate"]),
        unit_payload(feat_ref, 3, _check_ref(checks, feat_ref, 3), "扩展画像或设备数据缺失不阻塞首轮建议释放", priority, layers, ["扩展画像未完成或设备未连接。"], "在 minimal profile 完成后直接进入首页首轮建议路径。", ["advice visible state", "extended profile absent", "device data absent。"], ["不要求先补齐扩展画像或设备数据即可释放首轮建议。", "缺失额外数据时只影响 prompt/fallback，而不影响首轮建议主链。"], ["扩展画像或设备未完成导致首页无首轮建议。", "设备数据被错误当作首轮建议前置。"], ["non-blocking advice-release evidence", "prompt-mode evidence", "homepage advice trace"], refs + ["extended profile", "device data", "homepage advice"]),
    ]


def extended_profile_completion_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = list(feature.get("acceptance_checks") or [])
    return [
        unit_payload(feat_ref, 1, _check_ref(checks, feat_ref, 1), "首页任务卡展示扩展画像补全项并允许从首页发起渐进补全", priority, layers, [_check_field(checks, 1, "given", "homepage 已进入。")], "加载首页任务卡与扩展画像补全入口。", ["task cards", "in-progress task", "homepage remains usable。"], ["首页出现扩展画像任务卡与下一步补全项。", "补全入口位于首页，不重新回到首日 blocking onboarding。"], ["首页不出现任务卡或补全入口。", "补全入口把用户拉回首日阻塞链路。"], ["task-card rendering evidence", "homepage task snapshot", "entry-point trace"], refs + ["首页任务卡", "渐进补全"]),
        unit_payload(feat_ref, 2, _check_ref(checks, feat_ref, 2), "分步 patch 保存后刷新 completion percent 与 next task cards", priority, layers, [_check_field(checks, 2, "given", "存在可补全的扩展画像字段。")], "提交一次扩展画像 patch 保存。", ["saved patch ref", "profile completion percent", "next task cards。"], ["每次 patch 保存都能独立成功并刷新 completion percent。", "用户再次进入首页时能从新的任务卡状态继续补全。"], ["patch 保存成功但 completion percent 未更新。", "每次保存都要求重新提交整页完整画像。"], ["patch save evidence", "completion percent update evidence", "next-task-cards evidence"], refs + ["patch save", "completion percent", "next task cards"]),
        unit_payload(feat_ref, 3, _check_ref(checks, feat_ref, 3), "patch 保存失败时首页仍可用并保留 retry entry", priority, layers, [_check_field(checks, 3, "given", "patch save 过程发生失败。")], "触发 patch save failure。", ["homepage available", "retry entry", "failure message。"], ["保存失败不会撤销 homepage_entered。", "失败后保留 retry entry 并允许继续从首页发起补全。"], ["patch save 失败后首页不可用。", "失败后没有 retry entry 或恢复路径。"], ["retry-state evidence", "homepage preservation evidence", "patch failure evidence"], refs + ["retry entry", "homepage_entered"]),
    ]


def device_deferred_entry_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = list(feature.get("acceptance_checks") or [])
    return [
        unit_payload(feat_ref, 1, _check_ref(checks, feat_ref, 1), "设备连接入口只在首页后出现，并允许 skip", priority, layers, [_check_field(checks, 1, "given", "homepage 已进入。")], "进入首页并检查设备连接入口。", ["deferred device entry", "skip action", "homepage available。"], ["设备连接入口只在首页后显示。", "用户可 skip，且不影响首页继续可用。"], ["设备连接入口出现在首页前。", "skip 后首页或首轮建议不可用。"], ["deferred device entry evidence", "skip-path evidence", "homepage preservation evidence"], refs + ["deferred device entry", "device_skipped"]),
        unit_payload(feat_ref, 2, _check_ref(checks, feat_ref, 2), "设备授权或同步失败时维持 non-blocking，并保留首页与首轮建议可用", priority, layers, [_check_field(checks, 2, "given", "device auth 或 sync 失败。")], "触发 deferred device connection finalize failure。", ["device_failed_nonblocking", "homepage preserved", "first advice preserved。"], ["失败被记录为 non-blocking 结果。", "首页进入与首轮建议可用性保持不变。"], ["设备失败导致首页回退或首轮建议消失。", "失败结果没有留下 machine-readable 状态。"], ["non-blocking failure evidence", "homepage preserved evidence", "first-advice preserved evidence"], refs + ["device_failed_nonblocking", "homepage preserved", "first advice"]),
        unit_payload(feat_ref, 3, _check_ref(checks, feat_ref, 3), "设备连接成功仅增强体验，不得覆盖 canonical onboarding/profile 事实", priority, layers, [_check_field(checks, 3, "given", "设备连接成功并产生增强数据。")], "完成 deferred device connection 成功路径并检查后续写入。", ["enhancement ready", "canonical onboarding facts", "canonical profile facts。"], ["成功连接后只增强后续体验或建议精度。", "设备数据不会回写覆盖最小建档或 canonical 身体字段事实。"], ["设备成功连接后覆盖 canonical onboarding/profile 事实。", "增强数据被错误地当作主链前置条件。"], ["device-connected enhancement evidence", "canonical-boundary evidence", "non-overwrite trace"], refs + ["device_connected", "canonical facts", "enhancement"]),
    ]


def state_profile_boundary_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = list(feature.get("acceptance_checks") or [])
    return [
        unit_payload(feat_ref, 1, _check_ref(checks, feat_ref, 1), "primary_state 与 capability_flags 保持显式分离且不混写", priority, layers, [_check_field(checks, 1, "given", "onboarding 状态正在流转。")], "分别写入 primary_state 与 capability_flags，并读取统一结果。", ["primary_state", "capability_flags", "unified state read。"], ["primary_state 与 capability_flags 被单独持久化并保持语义分离。", "完成态判断不会被 capability_flags 伪造。"], ["primary_state 与 capability_flags 被混写或互相覆盖。", "能力开关被错误当作完成态真相源。"], ["primary_state write evidence", "capability_flags evidence", "unified state read evidence"], refs + ["primary_state", "capability_flags"]),
        unit_payload(feat_ref, 2, _check_ref(checks, feat_ref, 2), "身体字段跨对象冲突时 users / user_physical_profile / runner_profiles 保持单一事实源并触发 conflict_blocked", priority, layers, [_check_field(checks, 2, "given", "存在 users / user_physical_profile / runner_profiles 跨对象身体字段冲突。")], "触发跨边界冲突读取或写入。", ["users", "user_physical_profile", "runner_profiles", "conflict_blocked。"], ["users 只承载其边界内字段，user_physical_profile 保持身体字段唯一事实源。", "跨对象冲突时 unified-reader 或写入路径 fail closed 并返回 conflict_blocked。"], ["users / runner_profiles 覆盖 user_physical_profile 的 canonical 身体字段。", "冲突存在但系统继续放行完成态/资格判断。"], ["users boundary evidence", "canonical ownership evidence", "conflict_blocked evidence", "fail-closed verdict"], refs + ["users", "user_physical_profile", "runner_profiles", "conflict_blocked"]),
        unit_payload(feat_ref, 3, _check_ref(checks, feat_ref, 3), "统一读取层只依据 canonical_profile_boundary 做完成态与资格判断", priority, layers, [_check_field(checks, 3, "given", "存在完成态与资格判断请求。")], "通过 unified reader 读取 onboarding / profile 边界状态。", ["users", "canonical_profile_boundary", "eligibility verdict", "completion verdict。"], ["完成态与资格判断只依赖 canonical fields、users 边界内状态与 primary_state。", "派生值或 projection store 不能反向覆盖 canonical facts。"], ["eligibility / completion 读取旁路 canonical_profile_boundary。", "projection store 回写 canonical body facts。"], ["unified-reader judgment evidence", "users-boundary evidence", "canonical boundary evidence", "projection non-overwrite evidence"], refs + ["users", "canonical_profile_boundary", "completion verdict", "eligibility verdict"]),
    ]


def collaboration_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    return collaboration_units_impl(feature, layers, priority, refs)


def gate_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "authoritative handoff 进入单一路径的 gate 决策链", priority, layers, [str(checks[0]["given"]), "candidate package 已形成 authoritative handoff submission。"], "提交 handoff 并触发 gate evaluate。", ["只生成一个 authoritative decision object。", "decision path 不出现平行 shortcut。"], ["handoff -> decision 链唯一且可追溯。", "decision object 可被 formal publish 流消费。"], ["出现并行 decision path。", "缺少 authoritative decision object。"], ["gate decision response", "decision object evidence", "handoff submission trace"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[0]["id"]), "decision object 对 approve / revise / retry / handoff / reject 保持唯一业务语义", priority, layers, ["gate evaluator 能访问候选交接与审核上下文。"], "对同一候选输入分别验证 decision 结果分支。", ["不同 decision_type 的返回去向。", "回流或终止目标是否稳定。"], ["每个 decision_type 都映射到唯一业务去向。", "formal 发布触发不与 revise/retry/reject 混层。"], ["decision_type 语义不唯一。", "返回去向与主链职责混乱。"], ["decision branch evidence", "review summary", "routing trace"], refs),
        unit_payload(feat_ref, 3, str(checks[1]["id"]), "candidate 在 gate 前不得被当作 downstream formal source", priority, layers, [str(checks[1]["given"]), "candidate package 与 formal publication package 保持分层。"], str(checks[1]["when"]), ["下游消费路径", "candidate / formal package 边界。"], ["candidate 只能作为 gate 输入，不得成为 downstream formal source。", "formal object 仍需由 formal publish flow 生成。"], ["candidate 被 downstream 直接当作 formal source。", "object layering 被绕过。"], ["layer boundary evidence", "consumer rejection evidence"], refs + ensure_list(checks[1].get("trace_hints"))),
        unit_payload(feat_ref, 4, str(checks[2]["id"]), "decision object 缺失、冲突或 bypass 时必须 fail closed", priority, layers, [str(checks[2]["given"]), "存在 decision 缺失、冲突或旁路风险。"], str(checks[2]["when"]), ["decision path verdict", "fallback / reject result", "旁路检测。"], ["decision 缺失、冲突或 bypass 时必须 fail closed。", "不会静默 materialize 或 dispatch。"], ["decision 缺失仍推进 formal 或 dispatch。", "旁路行为未留下 verdict。"], ["fail-closed evidence", "decision conflict evidence", "bypass detection trace"], refs + ensure_list(checks[2].get("trace_hints")) + ["decision uniqueness", "fail closed"]),
    ]


def formal_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "formal publication 产出单一 canonical formal ref", priority, layers, [str(checks[0]["given"]), "approved decision object 已形成并允许 formalize。"], str(checks[0]["when"]), ["formal ref", "formal package", "lineage record。"], ["formal publication 只产出一条 canonical formal ref。", "lineage 可回链到 gate decision 与 candidate 来源。"], ["同一正式对象出现多条 formal ref。", "formal ref 缺少 lineage。"], ["formal publication evidence", "formal ref snapshot", "lineage record"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "downstream admission 只接受满足 lineage / layer 要求的 formal object", priority, layers, [str(checks[1]["given"]), "consumer admission 依赖 formal ref 与 lineage。"], str(checks[1]["when"]), ["admission verdict", "lineage verification result。"], ["只有满足 lineage / layer 约束的 formal object 能通过 admission。", "缺少 formal ref 或 lineage 时 fail closed。"], ["layer violation 仍被 admission。", "lineage 缺失未触发 fail closed。"], ["admission verdict", "lineage verification evidence"], refs + ensure_list(checks[1].get("trace_hints"))),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "candidate / intermediate artifact 不得被误当作 formal object", priority, layers, [str(checks[2]["given"]), "candidate、test output 或 freeze intermediate 仍可见。"], str(checks[2]["when"]), ["consumer input classification", "rejected non-formal object。"], ["非 formal object 不得通过 admission。", "对象分层边界保持单一 authoritative path。"], ["candidate 或中间物被当作 formal object 消费。", "层级边界被重写。"], ["classification evidence", "admission rejection evidence"], refs + ensure_list(checks[2].get("trace_hints"))),
        unit_payload(feat_ref, 4, None, "formal publication 失败时不得泄漏半正式对象", priority, layers, ["formalize 过程可能中断或前置条件不满足。"], "触发 formal publication 失败场景，并检查输出边界。", ["partial publication artifact", "registry state", "consumer visibility。"], ["formal publication 失败时不得留下可消费的半正式对象。", "consumer 只能看到明确失败 verdict。"], ["失败后仍暴露半正式对象。", "registry state 与 visibility 不一致。"], ["failed publication evidence", "registry state snapshot", "consumer visibility trace"], refs, derivation_basis=["no partial formal objects", "fail-closed formal publication"]),
    ]


def io_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "commit-governed / read-governed 只允许经 gateway 的 managed 路径", priority, layers, [str(checks[0]["given"]), "gateway / path policy / registry 已启用。"], str(checks[0]["when"]), ["gateway verdict", "receipt_ref / registry_record_ref / managed_artifact_ref。"], ["所有写读都经 gateway 并返回 managed refs。", "不出现自由写入或自由读取旁路。"], ["绕过 gateway 仍成功写读。", "managed refs 缺失。"], ["gateway verdict evidence", "receipt evidence", "registry record evidence"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "path policy 边界只覆盖 mainline governed IO，不扩张为仓库级总方案", priority, layers, [str(checks[1]["given"]), "scope boundary 已声明为 mainline governed IO。"], str(checks[1]["when"]), ["policy verdict scope", "被拒绝操作的边界说明。"], ["仅 mainline governed IO 被纳入受测边界。", "全局文件治理扩展请求被拒绝。"], ["测试边界覆盖仓库级全局治理。", "scope expansion 未被识别。"], ["boundary denial evidence", "policy scope note"], refs + ensure_list(checks[1].get("trace_hints"))),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "policy_deny 时不得 silent fallback 到自由写入", priority, layers, [str(checks[2]["given"]), "preflight 结果为 policy_deny。"], str(checks[2]["when"]), ["write result status", "是否存在自由写入旁路。"], ["policy_deny 返回可追溯 denied 结果。", "不存在 free write fallback。"], ["policy_deny 后仍发生自由写入。", "没有返回可审计 verdict。"], ["policy_deny evidence", "blocked fallback trace"], refs + ensure_list(checks[2].get("trace_hints")) + ["policy_deny"]),
        unit_payload(feat_ref, 4, str(checks[2]["id"]), "registry_prerequisite_failed 与 receipt_pending 都必须留下可追溯结果", priority, layers, ["registry bind 前置条件或 receipt build 可能失败。"], "分别触发 registry_prerequisite_failed 与 receipt_pending 场景。", ["partial success 标记", "失败结果 evidence", "重试/补偿上下文。"], ["registry_prerequisite_failed 与 receipt_pending 都可被追溯。", "主链不会因部分成功而静默丢失 managed refs 上下文。"], ["失败状态无 evidence。", "partial success 没有明确标记。"], ["registry_prerequisite_failed evidence", "receipt_pending evidence", "compensation trace"], refs + ["registry_prerequisite_failed", "receipt_pending"]),
    ]


def pilot_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "onboarding matrix 固化 skill、wave_id、compat_mode 与 cutover_guard_ref", priority, layers, [str(checks[0]["given"]), "rollout onboarding contract 可写回 wave state。"], "生成 onboarding matrix，并把 wave_id、compat_mode、cutover_guard_ref 写回 rollout state。", ["integration matrix", "wave_id", "compat_mode", "cutover_guard_ref。"], ["onboarding scope 与 migration waves 可追溯。", "cutover / fallback 规则以 machine-readable 形式存在。"], ["wave / compat_mode / cutover_guard_ref 缺失。", "迁移策略只能口头表达。"], ["onboarding matrix", "wave state evidence", "cutover directive"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "pilot chain verifier 验证 producer -> gate -> formal -> consumer -> audit", priority, layers, [str(checks[1]["given"]), "foundation 流程已提供 gate / formal / IO 基础能力。"], "执行真实 pilot chain verifier。", ["producer handoff", "gate decision", "formal publication", "consumer admission", "audit evidence。"], ["至少一条真实 pilot 主链完整跑通。", "五段链路都有可追溯 evidence。"], ["任一链路缺段仍被视为通过。", "仅组件内自测而无真实 pilot evidence。"], ["pilot evidence package", "end-to-end chain trace", "audit submission evidence"], refs + ensure_list(checks[1].get("trace_hints"))),
        unit_payload(feat_ref, 3, str(checks[1]["id"]), "pilot evidence 缺失时 rollout 必须 fail closed", priority, layers, ["pilot chain verifier 未产出完整 evidence。"], "尝试推进 wave 或 cutover。", ["rollout decision", "wave state", "denied / blocked verdict。"], ["evidence 不足时不能继续 rollout。", "wave 维持 fail closed 状态。"], ["evidence 缺失仍可推进 wave。", "rollout guard 被绕过。"], ["blocked rollout evidence", "wave state denial trace"], refs + ["fail closed", "pilot evidence package"]),
        unit_payload(feat_ref, 4, None, "fallback 结果必须记录到 receipt / wave state", priority, layers, ["fallback 或 rollback 场景已触发。", "receipt 与 wave state 都允许 authoritative writeback。"], "执行 fallback / rollback，并写回 receipt 与 wave state。", ["fallback result", "receipt / wave state writeback", "fallback reason code。"], ["fallback 结果被记录并可追溯。", "receipt 与 wave state 保持同一条 authoritative update trace。"], ["fallback 未记录到 receipt 或 wave state。", "fallback 结果无法回放或审计。"], ["fallback evidence", "wave state update", "receipt writeback trace"], refs + ensure_list(checks[2].get("trace_hints")), derivation_basis=["fallback writeback obligation", "wave state auditability", "cutover / rollback trace closure"]),
        unit_payload(feat_ref, 5, str(checks[2]["id"]), "adoption scope 不得扩张为仓库级全局治理改造", priority, layers, [str(checks[2]["given"]), "待评估方案包含超出 governed skill onboarding / pilot / cutover 的全局治理动作。"], "提交包含仓库级治理动作的 adoption 方案，并执行 FEAT boundary check。", ["scope boundary verdict", "rejected expansion note", "accepted onboarding scope。"], ["scope 仅限 governed skill onboarding / pilot / cutover。", "仓库级治理扩张请求被明确拒绝。"], ["把仓库级治理清理纳入该 FEAT。", "scope expansion 未留下明确 verdict。"], ["scope boundary verdict", "rejected expansion evidence", "boundary review note"], refs + ensure_list(checks[2].get("trace_hints")) + ["scope boundary"]),
    ]


def derive_test_units(
    feature: dict[str, Any],
    layers: list[str],
    profile: str,
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    if profile == "runner_ready_job":
        return runner_ready_job_units(feature, layers, priority, refs)
    if profile == "runner_operator_entry":
        return runner_operator_entry_units(feature, layers, priority, refs)
    if profile == "runner_control_surface":
        return runner_control_surface_units(feature, layers, priority, refs)
    if profile == "runner_intake":
        return runner_intake_units(feature, layers, priority, refs)
    if profile == "runner_dispatch":
        return runner_dispatch_units(feature, layers, priority, refs)
    if profile == "runner_feedback":
        return runner_feedback_units(feature, layers, priority, refs)
    if profile == "runner_observability":
        return runner_observability_units(feature, layers, priority, refs)
    if profile == "minimal_onboarding":
        return minimal_onboarding_units(feature, layers, priority, refs)
    if profile == "first_ai_advice":
        return first_ai_advice_units(feature, layers, priority, refs)
    if profile == "extended_profile_completion":
        return extended_profile_completion_units(feature, layers, priority, refs)
    if profile == "device_deferred_entry":
        return device_deferred_entry_units(feature, layers, priority, refs)
    if profile == "state_profile_boundary":
        return state_profile_boundary_units(feature, layers, priority, refs)
    if profile == "collaboration":
        return collaboration_units(feature, layers, priority, refs)
    if profile == "gate":
        return gate_units(feature, layers, priority, refs)
    if profile == "formal":
        return formal_units(feature, layers, priority, refs)
    if profile == "io":
        return io_units(feature, layers, priority, refs)
    if profile == "pilot":
        return pilot_units(feature, layers, priority, refs)
    return default_units(feature, layers, priority, refs)


def derive_acceptance_traceability(
    feature: dict[str, Any],
    units: list[dict[str, Any]],
    profile: str,
) -> list[dict[str, Any]]:
    mapping: list[dict[str, Any]] = []
    for check in feature.get("acceptance_checks") or []:
        acceptance_ref = str(check.get("id") or "")
        covered = [unit["unit_ref"] for unit in units if unit.get("acceptance_ref") == acceptance_ref]
        scenario = str(check.get("scenario") or "")
        given = str(check.get("given") or "")
        when = str(check.get("when") or "")
        then = str(check.get("then") or "")
        if profile == "pilot" and "At least one real pilot chain is required" in scenario:
            when = "执行 pilot chain verifier 并评估 adoption readiness"
            then = "至少一条 producer -> gate -> formal -> consumer -> audit 真实 pilot 主链必须被验证，不能只依赖组件内自测。"
        elif profile == "pilot" and "Adoption scope does not expand into repository-wide governance" in scenario:
            then = "onboarding scope 必须保持在 governed skill onboarding / pilot / cutover 范围内，并拒绝仓库级治理扩张。"
        elif profile == "collaboration" and "approval and re-entry semantics outside this FEAT" in then:
            then = "提交完成后只暴露 authoritative handoff 与 pending visibility；decision-driven revise/retry runtime routing 可以回流，但 gate decision issuance / approval 语义仍在本 FEAT 外。"
        elif profile == "runner_operator_entry" and "manual" in scenario.lower():
            then = "runner entry 只负责启动或恢复 execution runner，不得把正常主链 dispatch 退化为人工 relay。"
        elif profile == "runner_observability" and ("read-only" in scenario.lower() or "只读" in scenario):
            then = "monitor surface 只做 authoritative 状态读取与展示，不承担 claim、dispatch 或 outcome 改写职责。"
        mapping.append(
            {
                "acceptance_ref": acceptance_ref,
                "acceptance_scenario": scenario,
                "given": given,
                "when": when,
                "then": then,
                "unit_refs": covered,
                "coverage_status": "covered" if covered else "missing",
                "coverage_notes": "Acceptance is explicitly mapped to executable minimum coverage units." if covered else "Acceptance has not been mapped to a test unit.",
            }
        )
    return mapping
