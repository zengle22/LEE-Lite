from __future__ import annotations

from copy import deepcopy
from typing import Any

from src_to_epic_identity import operator_surface_names

EXECUTION_RUNNER_BEHAVIOR_SLICES = [
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
]

EXECUTION_RUNNER_CORE_SLICES = [
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
            {"id": "runner-intake-AC-01", "scenario": "Execution outcomes are explicit", "given": "runner has finished or failed a next-skill invocation", "when": "the result is recorded", "then": "the product flow must emit explicit done, failed, or retry/reentry outcomes with evidence.", "trace_hints": ["done", "failed", "retry", "evidence"]},
            {"id": "runner-intake-AC-02", "scenario": "Retry returns to execution semantics", "given": "a downstream execution needs another attempt", "when": "the runner records the outcome", "then": "the result must return through retry / reentry semantics instead of being rewritten as publish-only status.", "trace_hints": ["retry", "reentry", "execution semantics"]},
            {"id": "runner-intake-AC-03", "scenario": "Approve is not treated as terminal", "given": "the overall product chain is reviewed", "when": "the flow after gate approval is inspected", "then": "the chain must continue through runner execution and result feedback rather than ending at approve itself.", "trace_hints": ["approve", "runner", "not terminal"]},
        ],
    },
]

EXECUTION_RUNNER_CORE_SLICES = [
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
            {"id": "runner-intake-AC-01", "scenario": "Execution outcomes are explicit", "given": "runner has finished or failed a next-skill invocation", "when": "the result is recorded", "then": "the product flow must emit explicit done, failed, or retry/reentry outcomes with evidence.", "trace_hints": ["done", "failed", "retry", "evidence"]},
            {"id": "runner-intake-AC-02", "scenario": "Retry returns to execution semantics", "given": "a downstream execution needs another attempt", "when": "the runner records the outcome", "then": "the result must return through retry / reentry semantics instead of being rewritten as publish-only status.", "trace_hints": ["retry", "reentry", "execution semantics"]},
            {"id": "runner-intake-AC-03", "scenario": "Approve is not treated as terminal", "given": "the overall product chain is reviewed", "when": "the flow after gate approval is inspected", "then": "the chain must continue through runner execution and result feedback rather than ending at approve itself.", "trace_hints": ["approve", "runner", "not terminal"]},
        ],
    },
]


def _execution_runner_entry_slice(package: Any) -> dict[str, Any]:
    skill_entries = operator_surface_names(package, "skill_entry")
    return {
        "id": "runner-operator-entry",
        "name": "Runner 用户入口流",
        "track": "foundation",
        "goal": "冻结一个用户可显式调用的 Execution Loop Job Runner 入口 skill，让 operator 能从 Claude/Codex CLI 启动或恢复自动推进。",
        "scope": [
            f"定义独立 skill 入口：{'、'.join(skill_entries)}。",
            "定义入口 skill 的最小输入、启动时机和与 ready queue 的绑定边界。",
            "定义 operator 通过入口 skill 触发 runner 的责任，而不是继续依赖人工接力或隐式后台。",
        ],
        "product_surface": "runner 用户入口流：用户通过独立 skill 入口启动或恢复 Execution Loop Job Runner",
        "completed_state": "operator 已经能通过独立 skill 入口显式启动或恢复 runner，而不是猜测后台是否存在自动消费器。",
        "business_deliverable": "给 Claude/Codex CLI operator 使用的 runner skill entry 与启动记录。",
        "capability_axes": ["Runner 用户入口能力"],
        "acceptance_checks": [
            {"id": "runner-operator-entry-AC-01", "scenario": "Runner exposes a named skill entry", "given": "an operator needs to start the execution loop", "when": "the runtime入口 is inspected", "then": "the product flow must expose a named runner skill entry instead of hiding start-up inside abstract background automation.", "trace_hints": ["skill entry", "operator", "start"]},
            {"id": "runner-operator-entry-AC-02", "scenario": "Entry remains user-invokable", "given": "a CLI-first workflow", "when": "the runner is started or resumed", "then": "the entry must stay invokable by Claude/Codex CLI rather than requiring direct file edits or out-of-band orchestration.", "trace_hints": ["CLI-first", "resume", "invoke"]},
        ],
    }


def _execution_runner_control_slice(package: Any) -> dict[str, Any]:
    cli_controls = operator_surface_names(package, "cli_control_surface")
    return {
        "id": "runner-control-surface",
        "name": "Runner 控制面流",
        "track": "foundation",
        "goal": "冻结 runner 的 CLI 控制面，让启动、claim、run、complete、fail 等动作形成可设计、可审计的用户操作边界。",
        "scope": [
            f"定义 CLI control surface：{'、'.join(cli_controls)}。",
            "定义各控制命令与 runner lifecycle / job lifecycle 的映射关系。",
            "定义控制面输出的结构化状态，而不是把操作结果留成隐式终端副作用。",
        ],
        "product_surface": "runner CLI 控制流：用户通过 CLI 控制命令驱动 runner 和 job lifecycle",
        "completed_state": "operator 能通过一组固定 CLI 控制面驱动 runner，而不是临时拼接命令或目录操作。",
        "business_deliverable": "给 Claude/Codex CLI operator 使用的 runner control surface 与结构化执行状态。",
        "capability_axes": ["Runner 控制面能力"],
        "acceptance_checks": [
            {"id": "runner-control-surface-AC-01", "scenario": "CLI controls are explicit", "given": "an operator reviews the runner product surface", "when": "control actions are listed", "then": "start, claim, run, complete, fail or equivalent control commands must be explicit and stable.", "trace_hints": ["CLI control", "stable commands"]},
            {"id": "runner-control-surface-AC-02", "scenario": "Control results are structured", "given": "an operator triggers a runner command", "when": "the action completes", "then": "the control surface must emit structured execution state rather than relying on ambiguous ad hoc logs.", "trace_hints": ["structured state", "command result"]},
        ],
    }


def _execution_runner_monitor_slice(package: Any) -> dict[str, Any]:
    monitor_surfaces = operator_surface_names(package, "monitor_surface")
    return {
        "id": "runner-observability-surface",
        "name": "Runner 运行监控流",
        "track": "foundation",
        "goal": "冻结 runner 的观察面，让 ready backlog、running、failed、deadletters 与 waiting-human 成为用户可见的正式产品面。",
        "scope": [
            f"定义 monitor surface：{'、'.join(monitor_surfaces)}。",
            "定义 ready backlog、running jobs、failed jobs、deadletters、waiting-human jobs 的最小可见集合。",
            "定义监控面如何服务 operator 判断继续运行、恢复还是人工介入。",
        ],
        "product_surface": "runner 运行监控流：用户查看 execution loop backlog、运行态和失败态",
        "completed_state": "operator 能看到 execution loop 的核心状态分布，并据此判断是否继续推进、恢复或转人工。",
        "business_deliverable": "给 workflow / orchestration operator 使用的 runner observability surface 与运行态视图。",
        "capability_axes": ["Runner 监控与观察能力"],
        "acceptance_checks": [
            {"id": "runner-observability-surface-AC-01", "scenario": "Core queue states are visible", "given": "the runner is operating on execution jobs", "when": "an operator inspects the monitoring surface", "then": "ready backlog, running jobs, failed jobs, deadletters, and waiting-human jobs must be visible as formal runtime states.", "trace_hints": ["ready backlog", "running", "failed", "deadletters", "waiting-human"]},
            {"id": "runner-observability-surface-AC-02", "scenario": "Monitoring supports operator action", "given": "a failure or stuck state exists", "when": "the operator reads the monitoring surface", "then": "the product surface must support resume, retry, or handoff decisions instead of acting as a passive log dump.", "trace_hints": ["operator action", "resume", "retry", "handoff"]},
        ],
    }


def derive_execution_runner_behavior_slices(package: Any) -> list[dict[str, Any]]:
    slices = deepcopy(EXECUTION_RUNNER_BEHAVIOR_SLICES)
    skill_entries = operator_surface_names(package, "skill_entry")
    if skill_entries:
        slices.append(_execution_runner_entry_slice(package))
    cli_controls = operator_surface_names(package, "cli_control_surface")
    if cli_controls:
        slices.append(_execution_runner_control_slice(package))
    slices.extend(deepcopy(EXECUTION_RUNNER_CORE_SLICES))
    monitor_surfaces = operator_surface_names(package, "monitor_surface")
    if monitor_surfaces:
        slices.append(_execution_runner_monitor_slice(package))
    return slices
