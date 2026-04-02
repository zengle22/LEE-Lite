---
id: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-005"
ssot_type: ARCH
title: governed skill 接入与 pilot 验证流
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-005"
source_refs:
- "product.epic-to-feat::adr036-src2epic-20260402-r4"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-005"
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
- "product.src-to-epic::adr036-raw2src-20260402-r10"
candidate_artifact_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-005/arch-design.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005"
---

# ARCH-SRC-ADR036-RAW2SRC-20260402-R9-005

## Boundary Placement

- Boundary to foundation FEATs: 本 FEAT 只定义 onboarding/pilot/cutover 挂接边界，不重写 collaboration、gate decision/publication、IO foundation internals。
- Boundary to audit/gate consumption: 本 FEAT 组织 pilot evidence 与 cutover routing，不新建平行 decision 体系。
- Dedicated rollout placement is required so wave state、compat mode 与 fallback remain authoritative across skill adoption.

## System Topology

```text
[Producer Skill] --> [Mainline Runtime] --> [Gate / Formalization] --> [Consumer Skill] --> [Audit Evidence] --> [Cutover Decision]
                                                                                                              |
                                                                                                              +--> fallback --> [Producer Skill]
```

## Responsibility Split

- Rollout controller owns onboarding wave、compat mode 与 cutover/fallback routing.
- Pilot verifier owns end-to-end evidence completeness checks across producer / consumer / audit / gate.
- Foundation FEATs keep ownership of their technical semantics; onboarding does not rewrite them.

## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.

## Out of Scope

- Do not redefine Gateway / Policy / Registry / Audit / Gate technical contracts that already belong to foundation FEATs.
- Do not require one-shot migration of every governed skill or exhaustive coverage of every producer/consumer combination.
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- Onboarding / migration_cutover 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。
