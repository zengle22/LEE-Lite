---
id: TECH-SRC-001-004
ssot_type: TECH
title: 主链文件 IO 与路径治理技术设计
status: active
version: v4
schema_version: 0.1.0
parent_id: FEAT-SRC-001-004
derived_from_ids:
- id: FEAT-SRC-001-004
  version: v2
  required: true
source_refs:
- ARCH-SRC-001-001
- FEAT-SRC-001-004
- EPIC-SRC-001-001
- SRC-001
- REL-001
- ADR-005
- ADR-009
- API-SRC-001-001
owner: dev-architecture-owner
tags:
- tech
- ssot
workflow_key: template.dev.tech_design_l3
workflow_instance_id: manual-tech-design-l3-src-001-20260324-v2
properties:
  release_ref: REL-001
  src_root_id: src-root-src-001
  architecture_ref: ARCH-SRC-001-001
  runtime_carrier: cli-first file-runtime
  api_refs:
    - API-SRC-001-001
  task_bundle_ref: ssot/tasks/SRC-001/FEAT-SRC-001-004
  design_analysis_ref: ssot/tech/SRC-001/T004/design-analysis.md
  implementation_scope_ref: ssot/tech/SRC-001/T004/implementation-scope.md
  decision_refs_ref: ssot/tech/SRC-001/T004/decision-refs.yaml
  review_result_ref: ssot/tech/SRC-001/T004/review-result.md
  risk_register_ref: ssot/tech/SRC-001/T004/risk-register.md
  tech_package_ref: ssot/tech/SRC-001/T004/tech-package.yaml
---

# 主链文件 IO 与路径治理技术设计

本技术设计服务于 `FEAT-SRC-001-004`，把该 FEAT 的 contract、runtime 组合与 validation hooks 收口为可实现边界。

## Architecture Decisions
- 只实现 `FEAT-SRC-001-004` 的能力面，不吞并相邻 FEAT。
- 所有实现都必须保留 source refs、evidence refs 与 release/test trace。
- 若涉及 guarded gate branch，只验证 guarded semantics，不擅自提升为 default-active。
- Gateway、Policy 与 IO audit 默认承载为 `CLI command + runtime helper + file evidence consumer`，不先做常驻网关服务。
- 跨模块 CLI/file-runtime contract 以 `API-SRC-001-001` 为准；本 TECH 只定义内部实现约束，不回写 API 契约。

## Technical Focus
- mainline IO scope
- path class and mode verdict
- bypass detection and audit evidence

## Implementation Rules
- Required inputs: FEAT-SRC-001-004, EPIC-SRC-001-001, ARCH-SRC-001-001, REL-001, ADR-009
- Required outputs: contract baseline, runtime integration slices, validation hooks
- Preferred carriers: CLI operations, path/mode runtime helpers, watcher-safe audit consumers
- Forbidden shortcuts: 不得 path guessing，不得口头约定替代 contract，不得改写 acceptance 标准，不得新增独立服务化写入口绕开 Gateway CLI/runtime contract。
