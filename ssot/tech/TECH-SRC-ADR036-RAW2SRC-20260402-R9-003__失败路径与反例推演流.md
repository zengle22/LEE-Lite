---
id: "TECH-SRC-ADR036-RAW2SRC-20260402-R9-003"
ssot_type: TECH
title: 失败路径与反例推演流
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-003"
source_refs:
- "product.epic-to-feat::adr036-src2epic-20260402-r4"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-003"
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
- "product.src-to-epic::adr036-raw2src-20260402-r10"
candidate_artifact_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-003/tech-spec.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003"
arch_ref: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-003"
api_ref: "API-SRC-ADR036-RAW2SRC-20260402-R9-003"
candidate_package_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-003"
---

# TECH-SRC-ADR036-RAW2SRC-20260402-R9-003

## Overview

冻结 deep mode 下的失败路径推演、counterexample 覆盖和恢复动作校验。

## Design Focus

- Freeze a concrete TECH design for 失败路径与反例推演流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.

## Implementation Rules

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 失败路径与反例推演流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 失败路径与反例推演流 的完成态必须与“高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。”对齐，不能只输出中间态、占位态或内部处理结果。
- 失败路径与反例推演流 happy path reaches the declared completed state: 高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。
- 失败路径与反例推演流 keeps its declared product boundary: 该 FEAT 只覆盖“非法输入、部分失败、恢复动作、迁移兼容、counterexample family coverage。”及其直接完成结果，不吸收相邻产品切片、实现任务或测试执行细节。
- 失败路径与反例推演流 hands downstream one authoritative product deliverable: 下游必须围绕 counterexample coverage result 继承该 FEAT 的产品语义，而不是重新猜测完成条件、补写边界或改写验收口径。
- Revision constraint: Gate revise: round 1 | semantic_lock_preservation | Preserve implementation_readiness_rule semantic lock: keep qa.impl-spec-test as a pre-implementation gate only, keep IMPL as the main tested object, keep upstream...

## Non-Functional Requirements

- Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
- Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
- Keep the package freeze-ready by recording execution evidence and supervision evidence.
- Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.

## Implementation Carrier View

- Governed skill、handoff runtime、formal publication 相关写入都通过 ADR-005 提供的 Gateway / Path Policy / Registry 接入受治理 IO。
- Mainline handoff 与 formal writes 共享同一套 path / mode 约束，不允许局部目录策略绕过受治理写入。
- 全局文件治理、仓库级目录重构与非 governed skill 自由写入不进入本实现范围。

```text
[cli/commands/artifact/command.py]
              |
              v
[cli/lib/managed_gateway.py] --> [cli/lib/policy.py]
              |
              +--> [cli/lib/fs.py] --> [cli/lib/registry_store.py]
```

## State Model

- `write_requested` -> `path_validated` -> `gateway_committed` -> `registry_recorded` -> `consumable_ref_published`
- `path_validated(fail)` -> `write_rejected`，不得 silent fallback 到自由写入。

## Module Plan

- Handoff runtime adapter：负责把受治理对象写入/读取主链 runtime，并维持 traceability。
- Decision boundary adapter：负责把上游 FEAT 约束映射成 runtime 可执行边界，不把实现责任散落到业务 skill。
- Gateway integration adapter：把 handoff/materialization 写入重定向到 ADR-005 Gateway。
- Path governance guard：在写入前校验 path / mode / overwrite 规则，并拒绝自由写入 fallback。

## Implementation Strategy

- 先接通 runtime 到 ADR-005 Gateway / Path Policy / Registry 的调用路径，再禁止自由写入 fallback。
- 把 mainline handoff 与 formal publication 相关写入都切到同一条受治理 IO 链路，避免双轨写盘。
- 最后用真实 handoff write + formal write 两条样例验证 path / mode / registry 行为。

## Implementation Unit Mapping

- `cli/lib/policy.py` (`extend`): 定义 path / mode / overwrite 的 preflight verdict 规则。
- `cli/lib/fs.py` (`extend`): 实现 governed read/write 的底层文件访问与 receipt 落盘。
- `cli/lib/managed_gateway.py` (`new`): 编排 preflight、gateway commit、registry bind、receipt build。
- `cli/lib/registry_store.py` (`extend`): 记录 managed artifact ref、registry prerequisite 和 publish 状态。
- `cli/commands/artifact/command.py` (`extend`): 暴露 governed artifact commit / read 入口，依赖 `cli/lib/managed_gateway.py`。

## Interface Contracts

- `GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。
- `PolicyVerdict`: input=`logical_path`, `path_class`, `mode`, `caller_ref`; output=`allow`, `reason_code`, `resolved_path`, `mode_decision`; errors=`invalid_path_class`, `mode_forbidden`; idempotent=`yes`; precondition=`request normalized`。

## Main Sequence

- 1. normalize request
- 2. preflight policy check
- 3. registry prerequisite check
- 4. execute governed handler
- 5. build receipt and managed ref
- 6. persist staging / evidence / registry record
- 7. return result

```text
Runtime / Skill     -> Gateway Adapter : request governed write
Gateway Adapter     -> Path Policy     : validate path / mode
Path Policy         -> Gateway Adapter : allow or reject
Gateway Adapter     -> IO Gateway      : commit artifact when allowed
IO Gateway          -> Registry        : register managed ref
Registry            -> Runtime / Skill : publish consumable ref
Gateway Adapter     -> Runtime / Skill : return governed rejection when blocked
```

## Exception and Compensation

- policy pass 但 registry prerequisite fail：拒绝写入，返回 `registry_prerequisite_failed`，不得绕过 registry 直接落盘。
- write success 但 receipt build fail：保留 staged artifact，标记 `receipt_pending`，禁止发布 managed ref 给 consumer。
- staging retention fail：允许主写入成功，但必须追加 degraded evidence，并要求后续 cleanup job 补偿。

## Integration Points

- 调用方：runtime、formal publication 相关写入、governed skill 的正式写入都通过 `cli/commands/artifact/command.py` 进入 Gateway。
- 挂接点：file-handoff 写入发生在 policy preflight 之后、registry bind 之前；external gate 读取 formal refs 时只消费 managed artifact ref。
- 旧系统兼容：compat mode 仅允许受控 read fallback；正式 write 不允许 bypass Gateway。

## Minimal Code Skeleton

- Happy path:

```python
def governed_write(request: GatewayWriteRequest) -> GatewayWriteResult:
    normalized = normalize_write_request(request)
    verdict = preflight_policy_check(normalized)
    require(verdict.allow, verdict.reason_code)
    ensure_registry_prerequisite(normalized)
    artifact_ref = commit_via_gateway(normalized, verdict.resolved_path)
    receipt = build_write_receipt(artifact_ref, verdict)
    persist_gateway_evidence(receipt)
    return GatewayWriteResult(artifact_ref=artifact_ref, receipt_ref=receipt.receipt_ref)
```

- Failure path:

```python
def governed_write_with_compensation(request: GatewayWriteRequest) -> GatewayWriteResult:
    normalized = normalize_write_request(request)
    verdict = preflight_policy_check(normalized)
    if not verdict.allow:
        return GatewayWriteResult.reject(reason_code=verdict.reason_code)
    artifact_ref = commit_via_gateway(normalized, verdict.resolved_path)
    try:
        receipt = build_write_receipt(artifact_ref, verdict)
    except ReceiptBuildError:
        mark_receipt_pending(artifact_ref)
        return GatewayWriteResult.partial_success(artifact_ref=artifact_ref)
    return GatewayWriteResult(artifact_ref=artifact_ref, receipt_ref=receipt.receipt_ref)
```

## Traceability

- Need Assessment: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
- TECH Design: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
- Cross-Artifact Consistency: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
