---
id: TECH-SRC-001-002
ssot_type: TECH
title: 正式交接与物化技术设计
status: active
version: v4
schema_version: 0.1.0
parent_id: FEAT-SRC-001-002
derived_from_ids:
- id: FEAT-SRC-001-002
  version: v2
  required: true
source_refs:
- ARCH-SRC-001-001
- FEAT-SRC-001-002
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
  task_bundle_ref: ssot/tasks/SRC-001/FEAT-SRC-001-002
  design_analysis_ref: ssot/tech/SRC-001/T002/design-analysis.md
  implementation_scope_ref: ssot/tech/SRC-001/T002/implementation-scope.md
  decision_refs_ref: ssot/tech/SRC-001/T002/decision-refs.yaml
  review_result_ref: ssot/tech/SRC-001/T002/review-result.md
  risk_register_ref: ssot/tech/SRC-001/T002/risk-register.md
  tech_package_ref: ssot/tech/SRC-001/T002/tech-package.yaml
---

# 正式交接与物化技术设计

本技术设计服务于 `FEAT-SRC-001-002`，把该 FEAT 的 contract、runtime 组合与 validation hooks 收口为可实现边界。

## Architecture Decisions
- 只实现 `FEAT-SRC-001-002` 的能力面，不吞并相邻 FEAT。
- 所有实现都必须保留 source refs、evidence refs 与 release/test trace。
- 若涉及 guarded gate branch，只验证 guarded semantics，不擅自提升为 default-active。
- handoff、gate decision 与 formal materialization 默认承载为 `CLI command + file object materializer + loop/watcher consumer`，不预设前后端服务化架构。
- 跨模块 CLI/file-runtime contract 以 `API-SRC-001-001` 为准；本 TECH 只定义内部实现约束，不回写 API 契约。

## Technical Focus
- handoff and gate decision chain
- single formalization path
- business-skill separation

## Implementation Rules
- Required inputs: FEAT-SRC-001-002, EPIC-SRC-001-001, ARCH-SRC-001-001, REL-001, ADR-009
- Required outputs: contract baseline, runtime integration slices, validation hooks
- Preferred carriers: CLI commands, file-based materializers, gate loop consumers
- Forbidden shortcuts: 不得 path guessing，不得口头约定替代 contract，不得改写 acceptance 标准，不得把 formal materialization 先实现成默认唯一 HTTP/API 路径。
