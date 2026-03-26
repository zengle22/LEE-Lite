#!/usr/bin/env python3
"""Runner-specific unit derivation helpers for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list
from feat_to_testset_units_common import unit_payload


def runner_ready_job_units(feature: dict[str, Any], layers: list[str], priority: str, refs: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "approve 结果只在允许时写入 ready execution job", priority, layers, [str(checks[0]["given"]), "approve decision 与 next skill target 可解析。"], str(checks[0]["when"]), ["ready execution job", "approve-to-job lineage", "queue publish verdict。"], ["approve 后形成唯一 ready execution job。", "approve-to-job lineage 可回链到 gate decision 与 target skill。"], ["approve 结果未产出 ready job。", "同一 approve 产出多条 ready queue item。"], ["ready execution job evidence", "approve-to-job lineage evidence", "ready queue receipt"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "非 approve 路径不得泄漏 ready queue item", priority, layers, [str(checks[1]["given"]), "存在 revise / retry / handoff / reject 等非 approve 决策。"], str(checks[1]["when"]), ["queue publish result", "blocked / denied verdict。"], ["非 approve 路径不会写入 artifacts/jobs/ready。", "blocked / denied verdict 可审计。"], ["revise / retry / reject 仍生成 ready queue item。", "缺少 blocked verdict。"], ["blocked publish evidence", "queue write denial trace"], refs + ensure_list(checks[1].get("trace_hints")) + ["non-approve path"]),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "ready execution job 必须保持单一 authoritative queue lineage", priority, layers, [str(checks[2]["given"]), "queue write receipt 与 lineage store 可观测。"], str(checks[2]["when"]), ["queue receipt", "lineage record", "target skill linkage。"], ["ready job 只保留一条 authoritative queue lineage。", "下游 runner 可直接用该 lineage 启动消费。"], ["ready job 缺少 lineage。", "queue receipt 与 lineage target 不一致。"], ["ready queue receipt", "lineage record", "target skill linkage evidence"], refs + ensure_list(checks[2].get("trace_hints")) + ["authoritative queue lineage"]),
    ]


def runner_operator_entry_units(feature: dict[str, Any], layers: list[str], priority: str, refs: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "runner skill 入口作为显式 Claude/Codex CLI 用户入口存在", priority, layers, [str(checks[0]["given"]), "operator surface inventory 已声明独立 runner skill entry。"], str(checks[0]["when"]), ["skill entry 名称", "CLI surface", "runner invocation receipt。"], ["存在独立 runner skill 入口。", "入口可通过 Claude/Codex CLI 直接调用，不隐藏在后台自动链中。"], ["runner 入口只存在于内部 runtime。", "CLI surface 不可见或命名漂移。"], ["runner invocation receipt", "runner skill entry trace", "operator surface evidence"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "start 与 resume 保留 authoritative runner context", priority, layers, [str(checks[1]["given"]), "runner start/resume request 与 runner context sample 可解析。"], str(checks[1]["when"]), ["runner_run_ref", "runner context ref", "bootstrap result。"], ["start / resume 都形成 authoritative runner context。", "resume 不丢失现有 run ownership 与 queue scope。"], ["resume 重建了新的并行 run context。", "runner context ref 无法回链。"], ["runner context bootstrap evidence", "runner_run_ref snapshot", "resume trace"], refs + ensure_list(checks[1].get("trace_hints")) + ["runner_run_ref", "runner context ref"]),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "runner 入口不退化为人工 relay 下游 skill", priority, layers, [str(checks[2]["given"]), "target skill / authoritative input 可从 runner context 解析。"], str(checks[2]["when"]), ["operator action", "invocation mode", "handoff / relay artifacts。"], ["runner 入口只启动或恢复 execution runner，不要求人工接力调用下一 skill。", "入口职责与 dispatch 职责分离。"], ["入口动作直接变成人工 relay 下游 skill。", "entry 与 dispatch 责任混层。"], ["invocation mode evidence", "responsibility boundary note"], refs + ensure_list(checks[2].get("trace_hints")) + ["manual relay forbidden"]),
    ]


def runner_control_surface_units(feature: dict[str, Any], layers: list[str], priority: str, refs: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "runner control surface 统一暴露 claim / run / complete / fail", priority, layers, [str(checks[0]["given"]), "runner CLI control surface 已发布。"], str(checks[0]["when"]), ["available control verbs", "command routing", "control action receipt。"], ["claim / run / complete / fail 具有统一入口与命名。", "控制动作产生 authoritative control action record。"], ["control verbs 分散在多个不一致入口。", "缺少 control action receipt。"], ["runner control action record", "command routing evidence", "control surface trace"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "runner control action 必须遵守 ownership 与状态机约束", priority, layers, [str(checks[1]["given"]), "job ownership fixture 与 invalid transition 样本可用。"], str(checks[1]["when"]), ["job ownership record", "transition verdict", "invalid transition denial。"], ["仅 job owner 能执行受限控制动作。", "非法状态跃迁必须 fail closed。"], ["非 owner 仍可 claim / complete。", "非法状态跃迁未被拒绝。"], ["job ownership evidence", "invalid transition evidence", "fail-closed verdict"], refs + ensure_list(checks[1].get("trace_hints")) + ["ownership strict mode"]),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "control plane 不越权改写 dispatch 或 outcome 边界", priority, layers, [str(checks[2]["given"]), "dispatch lineage 与 outcome record 可被读取。"], str(checks[2]["when"]), ["control action scope", "dispatch lineage", "outcome mutation boundary。"], ["control surface 只改变 runner lifecycle，不直接改写 dispatch 结果或 outcome 业务语义。", "control plane 与业务结果分层保持清晰。"], ["control action 直接重写 dispatch target。", "control plane 直接伪造 outcome。"], ["scope boundary evidence", "dispatch lineage trace", "outcome boundary note"], refs + ensure_list(checks[2].get("trace_hints")) + ["control plane boundary"]),
    ]


def runner_intake_units(feature: dict[str, Any], layers: list[str], priority: str, refs: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "ready queue intake 维持 single-owner claim 语义", priority, layers, [str(checks[0]["given"]), "ready execution job 已进入 artifacts/jobs/ready。"], str(checks[0]["when"]), ["claim receipt", "job owner", "running ownership record。"], ["同一 ready job 只被一个 runner 成功 claim。", "claim 后形成 running ownership record。"], ["同一 ready job 被多个 runner 同时 claim。", "claim 后未形成 ownership record。"], ["claim receipt", "running ownership record", "single-owner verdict"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "claim conflict 与 job_not_ready 路径必须 fail closed", priority, layers, [str(checks[1]["given"]), "存在 claim conflict 或 job_not_ready 场景。"], str(checks[1]["when"]), ["claim verdict", "denied reason", "queue state。"], ["claim conflict / job_not_ready 均返回 authoritative denied verdict。", "queue 状态不会被静默篡改。"], ["冲突场景仍成功 claim。", "失败场景没有 denied reason。"], ["claim denial evidence", "queue state snapshot", "failure verdict trace"], refs + ensure_list(checks[1].get("trace_hints")) + ["job_not_ready", "already_claimed"]),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "running ownership 必须对 dispatch 与 monitor 可见", priority, layers, [str(checks[2]["given"]), "running ownership record sample 可读取。"], str(checks[2]["when"]), ["ownership visibility", "dispatch precondition", "monitor snapshot。"], ["dispatch 与 observability 都能读取同一 running ownership record。", "ownership 不因 queue scan 重放而丢失。"], ["dispatch 看不到 current owner。", "monitor 与 dispatch 看到不同 ownership 真相。"], ["ownership visibility evidence", "dispatch precondition trace", "monitor snapshot"], refs + ensure_list(checks[2].get("trace_hints")) + ["running ownership visibility"]),
    ]


def runner_dispatch_units(feature: dict[str, Any], layers: list[str], priority: str, refs: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "claimed job 派发到声明的 target skill", priority, layers, [str(checks[0]["given"]), "claimed job 已带有 target skill ref。"], str(checks[0]["when"]), ["target skill ref", "invocation receipt", "execution attempt record。"], ["dispatch 只调用声明的 target skill。", "execution attempt record 可回链到 claimed job。"], ["dispatch 调用了错误 skill。", "缺少 execution attempt record。"], ["next-skill invocation evidence", "execution attempt record", "dispatch lineage trace"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "dispatch 保留 authoritative input lineage", priority, layers, [str(checks[1]["given"]), "authoritative input sample 与 claimed job input ref 可解析。"], str(checks[1]["when"]), ["input ref", "invocation payload", "lineage binding。"], ["dispatch 使用的输入与 claimed job authoritative input 一致。", "lineage binding 可回放。"], ["dispatch 输入经过人工重写或丢失。", "invocation payload 无法回链到 authoritative input。"], ["authoritative input evidence", "invocation payload snapshot", "lineage binding trace"], refs + ensure_list(checks[1].get("trace_hints")) + ["authoritative input lineage"]),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "dispatch 不退化为第三会话人工接力", priority, layers, [str(checks[2]["given"]), "runner 具备 skill invocation adapter。"], str(checks[2]["when"]), ["dispatch mode", "manual handoff requirement", "operator intervention。"], ["dispatch 由 runner 自动完成，不要求第三会话人工 relay。", "operator intervention 仅限治理例外，不是正常主链路径。"], ["正常 dispatch 仍依赖第三会话人工 relay。", "自动 dispatch 缺少明确控制边界。"], ["dispatch mode evidence", "operator intervention note"], refs + ensure_list(checks[2].get("trace_hints")) + ["manual relay forbidden"]),
    ]


def runner_feedback_units(feature: dict[str, Any], layers: list[str], priority: str, refs: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "done / failed / retry-reentry 形成单一 authoritative outcome", priority, layers, [str(checks[0]["given"]), "execution attempt fixture 可读取。"], str(checks[0]["when"]), ["execution outcome", "outcome status", "attempt linkage。"], ["每个 execution attempt 只写入一个 authoritative outcome。", "done / failed / retry-reentry 语义互斥。"], ["同一 attempt 产出多个 outcome。", "retry-reentry 与 done/failed 混层。"], ["execution outcome evidence", "attempt linkage trace", "status uniqueness evidence"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "failure evidence 与 retry-reentry directive 可追溯", priority, layers, [str(checks[1]["given"]), "failure evidence sample 与 retry directive 可解析。"], str(checks[1]["when"]), ["failure evidence", "retry directive", "attempt lineage。"], ["failure evidence 与 retry-reentry directive 绑定到同一 execution attempt。", "orchestration 可直接消费 retry directive。"], ["failure evidence 与 retry directive 不属于同一 attempt。", "retry directive 缺少 lineage。"], ["failure evidence binding", "retry-reentry directive evidence", "attempt lineage trace"], refs + ensure_list(checks[1].get("trace_hints")) + ["retry-reentry directive"]),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "feedback 结果保持 authoritative 并对 monitor 可见", priority, layers, [str(checks[2]["given"]), "outcome writer 与 monitor reader 可访问同一来源。"], str(checks[2]["when"]), ["outcome store", "monitor snapshot", "status propagation。"], ["monitor 读取到的结果与 authoritative outcome 一致。", "feedback 不通过侧写目录或临时日志推断。"], ["monitor 与 outcome store 看到不同状态。", "feedback 依赖目录猜测或非 authoritative 来源。"], ["outcome store evidence", "monitor snapshot", "status propagation trace"], refs + ensure_list(checks[2].get("trace_hints")) + ["authoritative outcome visibility"]),
    ]


def runner_observability_units(feature: dict[str, Any], layers: list[str], priority: str, refs: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "监控面覆盖 ready backlog / running / failed / waiting-human / deadletters", priority, layers, [str(checks[0]["given"]), "runner observability snapshot 可查询。"], str(checks[0]["when"]), ["status buckets", "snapshot payload", "missing state detection。"], ["监控面覆盖 ready backlog、running、failed、waiting-human、deadletters。", "状态缺失时返回明确 verdict。"], ["关键 runner 状态未显示。", "snapshot 只展示部分状态且无解释。"], ["runner observability snapshot", "status bucket evidence", "coverage verdict"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "monitor snapshot 可回链到 authoritative runner records", priority, layers, [str(checks[1]["given"]), "queue、ownership 与 outcome records 可读取。"], str(checks[1]["when"]), ["snapshot lineage", "queue source", "ownership/outcome source。"], ["每个 monitor bucket 都可回链到 queue、ownership 或 outcome source。", "snapshot 不依赖目录扫描猜测状态。"], ["monitor snapshot 无 lineage。", "状态来自临时目录或日志猜测。"], ["snapshot lineage trace", "queue/ownership/outcome evidence"], refs + ensure_list(checks[1].get("trace_hints")) + ["authoritative runner records"]),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "监控面保持只读，不承担控制或 dispatch 职责", priority, layers, [str(checks[2]["given"]), "runner status projector 与 control surface 都可访问。"], str(checks[2]["when"]), ["monitor action scope", "control side effect", "dispatch mutation。"], ["monitor surface 只做查询与展示。", "monitor 不直接 claim、dispatch 或重写 outcome。"], ["monitor surface 直接执行 lifecycle control。", "monitor 直接改写 dispatch / outcome。"], ["read-only evidence", "side-effect absence trace"], refs + ensure_list(checks[2].get("trace_hints")) + ["read-only monitor surface"]),
    ]
