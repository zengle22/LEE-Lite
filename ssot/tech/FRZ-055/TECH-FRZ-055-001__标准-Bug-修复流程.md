---
id: "TECH-FRZ-055-001"
ssot_type: TECH
title: 标准 Bug 修复流程
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "frz-055-bug-lifecycle-20260507--feat-frz-055-001"
source_refs:
- "product.epic-to-feat::frz-055-bug-lifecycle-20260507"
- "FEAT-FRZ-055-001"
- "TECH-FRZ-055-001"
- "EPIC-FRZ-055-20260507"
- "FRZ-055"
- "SURFACE-MAP-FEAT-FRZ-055-001"
- "ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md"
- "ssot/frz/FRZ-055/frz.yaml"
- "SRC-FRZ-055-20260507"
- "ADR-055"
candidate_artifact_ref: "artifacts/feat-to-tech/frz-055-bug-lifecycle-20260507--feat-frz-055-001/tech-spec.md"
gate_decision_ref: "artifacts/active/gates/decisions/frz055-chain-manual-approval-20260507.json"
parent_id: "FEAT-FRZ-055-001"
arch_ref: "ARCH-FRZ-055-001"
api_ref: null
candidate_package_ref: "artifacts/feat-to-tech/frz-055-bug-lifecycle-20260507--feat-frz-055-001"
---

# TECH-FRZ-055-001

## Overview

建立从 test-run 失败发现到自动关闭的完整标准 Bug 修复流程，并与 GSD 执行阶段集成。

## Design Focus

- Freeze a concrete TECH design for 标准 Bug 修复流程, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.

## Implementation Rules

- 三层分离原则：执行层（test-run）仅记录，验收层（gate）仅决策，修复层（GSD）仅修复
- 按 feat 隔离：每个 feat 有独立的 bug registry，避免跨 feat 干扰
- 幂等性：多次运行 ll-bug-remediate 不应重复生成相同 phase
- test-run 失败用例应自动生成 detected 状态 bug 写入 registry: 应生成 detected 状态 bug 并写入对应 feat 的 bug registry。
- gate FAIL 应自动将 detected 提升为 open: bug status 应从 detected 变为 open，并生成 draft phase。
- ll-bug-remediate 应生成符合 GSD 规范的 bug fix phase: 应生成符合 GSD 规范的 {N}-bug-fix-{bug_id} phase。

## Non-Functional Requirements

- Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
- Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
- Keep the package freeze-ready by recording execution evidence and supervision evidence.

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

## State Machine

- states: prepared -> executing -> recorded
- guards: input validated before execution; evidence written before handoff
- field mapping: lifecycle_state tracks runtime progression and must not be owned by IMPL

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

## Algorithm Constraints

- decision rule: preserve FEAT acceptance and inherited constraints before selecting runtime shape
- determinism: design derivation must stay deterministic for the same FEAT and integration context
- compatibility anchor: Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- compatibility anchor: Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界。

## Input / Output Matrix and Side Effects

- select_FEAT-FRZ-055-001: inputs=feat_freeze_package, feat_ref; outputs=selected_feat snapshot; writes=none; side_effects=none; evidence=input validation; idempotency=repeatable
- derive_design: inputs=selected_feat, integration_context; outputs=TECH/ARCH/API blocks; writes=tech-design-bundle.*; side_effects=markdown/json materialization; evidence=execution-evidence; idempotency=run_id scoped
- handoff_downstream: inputs=frozen tech package; outputs=handoff-to-tech-impl.json; writes=handoff artifact; side_effects=downstream routing metadata; evidence=freeze gate + supervision

## Technical Glossary and Canonical Ownership

- bug registry entry: None
- gate decision: None
- GSD phase: None
- verify result: None
- closed notification: None
- FEAT-FRZ-055-001 owns product slice `标准 Bug 修复流程` and authoritative artifact `bug lifecycle closed loop record`.
- FEAT-FRZ-055-002 owns product slice `验证失败回退流程` and authoritative artifact `verification fallback record`.
- FEAT-FRZ-055-003 owns product slice `人工终止流程` and authoritative artifact `manual termination record`.
- FEAT-FRZ-055-004 owns product slice `Gate PASS 归档流程` and authoritative artifact `gate pass archive record`.

## Migration Constraints

- mode: extend
- mode: shadow
- mode: cutover
- mode: fallback
- legacy invariant: FEAT remains the product SSOT boundary; TECH must not collapse multiple FEAT slices back into one implementation blob.
- legacy invariant: Authoritative artifact, gate/admission dependencies, and prohibited inference rules must stay explicit across downstream derivation.

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

- Need Assessment: product.epic-to-feat::frz-055-bug-lifecycle-20260507, FEAT-FRZ-055-001, EPIC-FRZ-055-20260507, FRZ-055
- TECH Design: product.epic-to-feat::frz-055-bug-lifecycle-20260507, FEAT-FRZ-055-001, EPIC-FRZ-055-20260507, FRZ-055
- Cross-Artifact Consistency: product.epic-to-feat::frz-055-bug-lifecycle-20260507, FEAT-FRZ-055-001, EPIC-FRZ-055-20260507, FRZ-055
