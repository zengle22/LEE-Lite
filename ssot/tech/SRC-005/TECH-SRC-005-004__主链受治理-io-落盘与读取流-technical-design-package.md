---
id: TECH-SRC-005-004
ssot_type: TECH
tech_ref: TECH-SRC-005-004
feat_ref: FEAT-SRC-005-004
title: 主链受治理 IO 落盘与读取流 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: adr011-raw2src-fix-20260327-r1--feat-src-005-004
candidate_package_ref: artifacts/feat-to-tech/adr011-raw2src-fix-20260327-r1--feat-src-005-004
gate_decision_ref: artifacts/active/gates/decisions/feat-to-tech-adr011-raw2src-fix-20260327-r1--feat-src-005-004-tech-design-bundle-decision.json
frozen_at: '2026-03-29T14:26:55Z'
---

# 主链受治理 IO 落盘与读取流 Technical Design Package


## Selected FEAT

- feat_ref: `FEAT-SRC-005-004`
- title: 主链受治理 IO 落盘与读取流
- axis_id: artifact-io-governance
- resolved_axis: derived
- epic_freeze_ref: `EPIC-SRC-005-001`
- src_root_id: `SRC-005`
- goal: 冻结主链业务动作在什么时候必须 governed write/read，以及这些正式读写会为业务方留下什么 authoritative receipt 和 managed ref。
- authoritative_artifact: governed write-read receipt
- upstream_feat: FEAT-SRC-005-001, FEAT-SRC-005-002, FEAT-SRC-005-003
- downstream_feat: FEAT-SRC-005-005
- gate_decision_dependency_feat_refs: FEAT-SRC-005-002
- admission_dependency_feat_refs: FEAT-SRC-005-003

## Need Assessment

- arch_required: True
  - ARCH required by boundary/runtime placement.
  - Keyword hits: registry, 边界, boundary, path.
- api_required: True
  - API required by command-level contract surface.
  - Keyword hits: decision, handoff, proposal.

## TECH Design

- Design focus:
  - Freeze a concrete TECH design for 主链受治理 IO 落盘与读取流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Implementation rules:
  - Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
  - Downstream preservation rules：candidate -> formal、loop / gate / handoff 分层与 acceptance semantics 必须继续保持可校验、可追溯。
  - Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
  - ADR-005 是本 FEAT 的前置基础；本 FEAT 只定义主链如何消费其受治理 IO/path 能力，不重新实现底层模块。
  - Mainline IO boundary is explicit: The FEAT must define which IO belongs to mainline handoff / materialization and which IO is out of scope.
  - Path governance does not expand into global file governance: The FEAT must reject scope expansion beyond governed skill IO, handoff, and materialization boundaries.
  - Formal writes cannot fall back to free writes: The FEAT must preserve governed path / mode enforcement and block silent fallback to uncontrolled writes.
- Non-functional requirements:
  - Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
  - Keep the package freeze-ready by recording execution evidence and supervision evidence.
  - Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
  - Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.

### Implementation Carrier View
- Business skill、gate、consumer 分别围绕 candidate layer、formal layer、downstream consumption layer 协作，不共享隐式旁路对象。
- Admission checker 只根据 formal refs 与 lineage 放行 downstream 读取，不根据路径邻近关系或目录猜测放行。
- Layering policy 与 IO/path policy 分离：本 FEAT 只定义对象资格和引用方向，底层落盘仍消费外部治理基础。

```text
[cli/commands/registry/command.py]
              |
              v
[cli/lib/lineage.py] --> [cli/lib/admission.py] --> [Admission Verdict]
              |
              +--> [cli/lib/protocol.py]
```

### State Model
- `candidate_only`：仅允许 gate/runtime 消费，不允许 downstream 直接读取。
- `formal_authorized`：已具备 formal refs 与 lineage，可成为正式输入。
- `consumer_admitted`：consumer 通过 admission checker 后可读取 formal layer。

### Module Plan
- Handoff runtime adapter：负责把受治理对象写入/读取主链 runtime，并维持 traceability。
- Decision boundary adapter：负责把上游 FEAT 约束映射成 runtime 可执行边界，不把实现责任散落到业务 skill。
- Object lineage resolver：为 candidate/formal/downstream object 建立 lineage 与 authoritative refs。
- Admission checker：在 consumer 读取前验证 formal refs、lineage 与 layer eligibility。

### Implementation Strategy
- 先定义 candidate/formal/downstream 三层对象与 authoritative refs，再补 admission checker。
- 把 consumer read path 全部切到 formal refs 校验后，再清理路径猜测或旁路读取。
- 最后用至少一条真实 consumer consumption 验证 layer boundary 是否成立。

### Implementation Unit Mapping
- `cli/lib/protocol.py` (`extend`): 定义 `CandidateRef`、`FormalRef`、`AdmissionRequest`、`AdmissionVerdict` 结构。
- `cli/lib/lineage.py` (`new`): 维护 candidate/formal/downstream object 的 lineage 与 authoritative refs。
- `cli/lib/admission.py` (`new`): 基于 formal refs、lineage 与 layer eligibility 做准入判断。
- `cli/lib/registry_store.py` (`extend`): 提供 lineage 查询和 formal ref 解析能力。
- `cli/commands/registry/command.py` (`extend`): 暴露 resolve-formal-ref / validate-admission 操作，依赖 `cli/lib/lineage.py` 和 `cli/lib/admission.py`。

### Interface Contracts
- `AdmissionRequest`: input=`consumer_ref`, `requested_ref`, `lineage_ref?`; output=`allow`, `resolved_formal_ref`, `layer`, `reason_code`; errors=`formal_ref_missing`, `lineage_missing`, `layer_violation`; idempotent=`yes by consumer_ref + requested_ref`; precondition=`requested object 已可解析到 registry / lineage`。
- `LineageResolveRequest`: input=`candidate_ref | formal_ref`; output=`authoritative_ref`, `layer`, `upstream_refs`, `downstream_refs`; errors=`unknown_ref`, `ambiguous_lineage`; idempotent=`yes`; precondition=`ref 存在于 registry/lineage store`。

### Main Sequence
- 1. normalize requested ref and consumer identity
- 2. resolve lineage and authoritative formal ref
- 3. verify requested layer and consumer eligibility
- 4. emit admission verdict and resolved formal ref
- 5. record read evidence for audit / gate traceability

```text
Business Skill   -> Gate / Runtime    : write candidate package
Gate / Runtime   -> Lineage Resolver  : resolve formal refs and lineage
Lineage Resolver -> Gate / Runtime    : return formal object metadata
Consumer         -> Admission Checker : request read
Admission Checker-> Consumer          : allow only with formal refs
```

### Exception and Compensation
- lineage resolve fail：直接 deny admission，不允许退化为路径猜测。
- formal ref 存在但 layer mismatch：返回 `layer_violation`，consumer 不得继续读 candidate layer。
- admission evidence persist fail：允许 verdict 返回，但把 read 标记为 `audit_pending`，后续 gate 需感知缺失 evidence。

### Integration Points
- 调用方：downstream consumer 在正式读取前调用 admission checker；registry 负责提供 formal refs 与 lineage。
- 挂接点：file-handoff 完成后先 resolve formal refs，再决定 consumer admission。
- 旧系统兼容：现有路径猜测读取必须逐步迁移到 formal-ref based access，兼容模式只允许只读告警，不允许默认放行。

### Minimal Code Skeleton
- Happy path:
```python
def validate_admission(request: AdmissionRequest) -> AdmissionVerdict:
    lineage = resolve_lineage(request.requested_ref)
    formal_ref = require_formal_ref(lineage)
    check_consumer_policy(request.consumer_ref, formal_ref)
    record_read_evidence(request.consumer_ref, formal_ref)
    return AdmissionVerdict.allow(formal_ref=formal_ref, lineage_ref=lineage.lineage_ref)
```

- Failure path:
```python
def validate_admission_or_deny(request: AdmissionRequest) -> AdmissionVerdict:
    lineage = resolve_lineage(request.requested_ref)
    if lineage is None:
        return AdmissionVerdict.deny(reason_code='lineage_missing')
    if lineage.layer != 'formal':
        return AdmissionVerdict.deny(reason_code='layer_violation')
    return validate_admission(request)
```

## Optional ARCH

- arch_ref: `ARCH-SRC-005-004`
- summary_topics:
  - Boundary to collaboration/formalization: 本 FEAT 消费已有 candidate/formal objects，但不定义 handoff submission 或 materialization dispatch。
  - Boundary to IO governance: 本 FEAT 冻结 authoritative refs 与 admission policy，不重写 path / mode / overwrite 规则。
  - Dedicated lineage/admission placement is required so formal refs、layer policy 与 downstream eligibility stay authoritative.
- see: `arch-design.md`

## Optional API

- api_ref: `API-SRC-005-004`
- contract_surfaces:
  - formal ref resolution contract
  - admission validation contract
- command_refs:
  - `ll registry resolve-formal-ref`
  - `ll registry validate-admission`
- response_envelope:
  - success: `{ ok: true, command_ref, trace_ref, result }`
  - error: `{ ok: false, command_ref, trace_ref, error }`
- see: `api-contract.md`

## Cross-Artifact Consistency

- passed: True
- structural_passed: True
- semantic_passed: True
- checks:
  - [structural] TECH mandatory: True (TECH is always emitted for the selected FEAT.)
  - [structural] Traceability present: True (Selected FEAT carries authoritative source refs for downstream design derivation.)
  - [structural] ARCH coverage: True (ARCH coverage matches the selected FEAT boundary needs.)
  - [structural] API coverage: True (API coverage includes concrete command-level contracts.)
  - [semantic] ARCH / TECH separation: True (ARCH keeps boundary placement while TECH keeps implementation carriers.)
  - [semantic] API contract completeness: True (API contracts carry schema, semantics, invariants, and canonical refs.)
- issues:
  - None
- minor_open_items:
  - Freeze a command-level error mapping table for `code -> retryable -> idempotent_replay` in a later API revision if validator-grade contract testing needs a closed semantics table.
  - Optional ARCH/API summaries are still embedded in the bundle for one-shot review; a later revision may collapse them to pure references to reduce duplication risk.

## Downstream Handoff

- target_workflow: workflow.dev.tech_to_impl
- tech_ref: `TECH-SRC-005-004`
- arch_ref: `ARCH-SRC-005-004`
- api_ref: `API-SRC-005-004`

## Traceability

- Need Assessment: scope, dependencies, acceptance_checks <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-004, EPIC-SRC-005-001, SRC-005
- TECH Design: goal, scope, constraints <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-004, EPIC-SRC-005-001, SRC-005
- Cross-Artifact Consistency: dependencies, outputs, acceptance_checks <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-004, EPIC-SRC-005-001, SRC-005
