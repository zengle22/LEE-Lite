---
id: IMPL-SRC-001-005-001
ssot_type: IMPL
title: governed skill integration matrix and onboarding scope definition
status: active
version: v1
schema_version: 0.1.0
parent_id: FEAT-SRC-001-005
source_refs:
  - FEAT-SRC-001-005
  - API-SRC-001-001
  - API-SRC-001-005
  - TECH-SRC-001-005
  - IMPL-SRC-001-005
  - TASK-FEAT-SRC-001-005-001
owner: dev-owner
tags:
  - ssot
  - onboarding
  - integration-matrix
  - revision
properties:
  feat_ref: FEAT-SRC-001-005
  tech_ref: TECH-SRC-001-005
  matrix_role: onboarding-and-readiness
  default_wave_id: wave-1-core-doc-chain
  default_compat_mode: mainline
---

# governed skill integration matrix and onboarding scope definition

## 1. Purpose

物化当前 governed skill onboarding matrix，明确：

- 哪些 skill 属于当前 adoption scope
- 每个 skill 在主链中的 integration role
- 当前 wave / compat mode / cutover guard 的默认要求
- 哪些 workflow 必须接入统一 `revision-request -> revision_context -> evidence lineage` 契约
- 哪些 workflow 明确排除在 revision module coverage 外

本文件是 `API-SRC-001-005.integration_matrix_ref` 的正式落点，不再依赖 superseded task 说明或非正式 guide。

## 2. Coverage Rule

- `included` workflow 必须支持显式 revision rerun 输入，并在 rerun artifacts 中物化 `revision-request.json`
- `included` workflow 必须把 `revision_request_ref` 写入 package bundle、manifest、execution evidence、supervision evidence
- `special_case` 允许共享 request/context contract，同时保留 skill 本地修复机制
- `excluded` workflow 不得伪装成 revision-module consumer

## 3. Matrix

| skill_ref | workflow_key | integration_role | primary_input_artifact | primary_output_artifact | wave_id | compat_mode | cutover_guard_ref | revision_module_coverage | revision_mode | revision_entrypoints | status | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ll-product-raw-to-src` | `product.raw-to-src` | `producer` | `raw_requirement / adr / business_opportunity` | `src_candidate_package` | `wave-1-core-doc-chain` | `mainline` | `API-SRC-001-005::core-ready` | `special_case` | `local-auto-fix + shared-context` | `run`, `executor-run`, `supervisor-review` | `active` | 需要吸收 gate revise/retry return job，但仍保留 patchable/blocking、minimal patch 和 retry budget。 |
| `ll-product-src-to-epic` | `product.src-to-epic` | `consumer` | `src_candidate_package` | `epic_freeze_package` | `wave-1-core-doc-chain` | `mainline` | `API-SRC-001-005::core-ready` | `included` | `rebuild` | `run`, `executor-run`, `supervisor-review` | `active` | 属于整包重建型返修，必须统一 revision context 和 evidence lineage。 |
| `ll-product-epic-to-feat` | `product.epic-to-feat` | `consumer` | `epic_freeze_package` | `feat_freeze_package` | `wave-1-core-doc-chain` | `mainline` | `API-SRC-001-005::core-ready` | `included` | `rebuild` | `run`, `executor-run`, `supervisor-review` | `active` | 属于整包重建型返修，必须统一 revision context 和 evidence lineage。 |
| `ll-dev-feat-to-ui` | `dev.feat-to-ui` | `consumer` | `feat_freeze_package` | `ui_spec_package` | `wave-2-downstream-doc-chain` | `bridge` | `API-SRC-001-005::guarded-ui-optional` | `included` | `rebuild` | `run`, `executor-run`, `supervisor-review` | `active` | UI spec 是 governed authored package，若接收 gate return 必须统一 revision contract。 |
| `ll-dev-feat-to-tech` | `dev.feat-to-tech` | `consumer` | `feat_freeze_package` | `tech_design_package` | `wave-1-core-doc-chain` | `mainline` | `API-SRC-001-005::core-ready` | `included` | `rebuild` | `run`, `executor-run`, `supervisor-review` | `active` | TECH/ARCH/API bundle 是下游文档主链的一部分，返修必须统一上下文与证据。 |
| `ll-qa-feat-to-testset` | `qa.feat-to-testset` | `consumer` | `feat_freeze_package` | `test_set_candidate_package` | `wave-1-core-doc-chain` | `mainline` | `API-SRC-001-005::core-ready` | `included` | `rebuild` | `run`, `executor-run`, `supervisor-review` | `active` | TESTSET candidate 需要吸收 gate revise/retry，并保留统一 revision lineage。 |
| `ll-dev-tech-to-impl` | `dev.tech-to-impl` | `consumer` | `tech_design_package` | `feature_impl_candidate_package` | `wave-1-core-doc-chain` | `mainline` | `API-SRC-001-005::core-ready` | `included` | `rebuild` | `run`, `executor-run`, `supervisor-review` | `active` | implementation task package 属于 governed authored package，返修必须统一 contract。 |
| `ll-gate-human-orchestrator` | `governance.gate-human-orchestrator` | `gate_consumer` | `gate_ready_package` | `gate_decision_package` | `wave-0-control-plane` | `mainline` | `API-SRC-001-005::control-authority` | `excluded` | `not_applicable` | `n/a` | `active` | 这是 authoritative gate，本身不是 revise/retry return 的消费者。 |
| `ll-project-init` | `repo.project-init` | `excluded` | `project_init_request` | `project_init_package` | `wave-0-control-plane` | `excluded` | `API-SRC-001-005::not-doc-regeneration` | `excluded` | `not_applicable` | `n/a` | `active` | 这是 scaffold materializer，不是 external-gate-driven 文档重生成链。 |
| `ll-test-exec-cli` | `skill.test-exec-cli` | `excluded` | `test_exec_skill_request` | `test_exec_skill_response` | `wave-0-control-plane` | `excluded` | `API-SRC-001-005::execution-envelope` | `excluded` | `not_applicable` | `n/a` | `active` | 产出执行响应 envelope，不属于 authored package regeneration。 |
| `ll-test-exec-web-e2e` | `skill.test-exec-web-e2e` | `excluded` | `test_exec_skill_request` | `test_exec_skill_response` | `wave-0-control-plane` | `excluded` | `API-SRC-001-005::execution-envelope` | `excluded` | `not_applicable` | `n/a` | `active` | 同 CLI execution skill，产出执行响应 envelope，不是 revision-module consumer。 |
| `ll-execution-loop-job-runner` | `workflow.execution-loop-job-runner` | `control_surface` | `execution_runner_skill_request` | `execution_runner_skill_response` | `wave-0-control-plane` | `mainline` | `API-SRC-001-005::control-authority` | `excluded` | `not_applicable` | `n/a` | `active` | 负责消费 ready jobs 与推进 loop，不负责 governed authored package 重生成。 |

## 4. Required Fields For Onboarding Records

每个 included 或 special-case workflow 的 onboarding 记录至少要保留：

- `skill_ref`
- `workflow_key`
- `integration_role`
- `wave_id`
- `compat_mode`
- `cutover_guard_ref`
- `revision_module_coverage`
- `revision_mode`
- `revision_entrypoints`
- `rationale`

## 5. Required Semantics

- `revision_module_coverage = included` 表示采用共享 revision-request / revision_context contract
- `revision_module_coverage = special_case` 只允许用于 `product.raw-to-src`
- `revision_module_coverage = excluded` 只能用于 gate authority、execution envelope、runner control surface、scaffold materializer 这类非文档重生 workflow
- `revision_mode = rebuild` 表示吸收 `revision-request` 后整包重建再审
- `revision_mode = local-auto-fix + shared-context` 表示共享 request/context contract，但保留本地 auto-fix loop

## 6. Acceptance

- included workflow 必须覆盖当前 6 个整包重建型文档 workflow
- `product.raw-to-src` 必须作为 special case 单列，不得伪装成纯 rebuild workflow
- excluded workflow 必须覆盖 gate、project-init、execution envelope、runner control surface 四类边界
- 本 matrix 的 included/excluded 集合必须与 `API-SRC-001-001.revision_return_contract` 一致

## 7. Traceability

- parent FEAT: `FEAT-SRC-001-005`
- runtime baseline: `API-SRC-001-001`
- adoption contract: `API-SRC-001-005`
- implementation baseline: `IMPL-SRC-001-005`
- historical planning source: `TASK-FEAT-SRC-001-005-001`
