# failure-cases 修复状态（2026-04-05）

## 已修复

### FC-20260402-115238-SRC-002-

- 状态：`resolved`
- 结论：`ll-test-exec-web-e2e` 的入口契约兼容和归一化已补齐，核心多次重试问题已修复。
- 关键修复：
  - `api_version` 兼容 `v1` / `1.0.0`
  - `test_set_ref` / `test_set_refs` 兼容归一
  - 通过 `run_normalized.py` 在 repo root 下执行
  - `validate_input.sh` 先归一化再校验
- 验证：
  - `python -m pytest tests/unit/test_ll_test_exec_web_e2e_normalization.py -q`
  - `python -m pytest tests/unit/test_web_skill_test_exec.py::TestWebExecSkillRuntime::test_web_skill_emits_candidate_and_handoff_with_real_testset -q`

### FC-20260403-081005-PROTO-SR

- 状态：`resolved`
- 结论：`dev.feat-to-proto` 的 fidelity 问题已修复，并补了专项 golden regression。
- 关键修复：
  - SRC-001 enum 域归一化
  - panel / entry / status 页面状态分支差异保留
  - technical payload 不再泄漏到 required UI scope
- 验证：
  - `python -m pytest skills/ll-dev-feat-to-proto/tests/test_feat_to_proto_workflow.py -q`

### FC-20260403-142839-EPIC-SRC

- 状态：`resolved`
- 结论：`src-to-epic` 已修复工程骨架型 SRC 主轴漂移问题。
- 关键修复：
  - 引入 engineering bootstrap baseline 识别
  - 主切片恢复为 repo/layout、api shell、miniapp shell、local env、migrations、health/readiness
  - revise context 回投到 reviewer 可见约束层
- 验证：
  - `python -m pytest tests/unit/test_lee_product_src_to_epic.py -q`

### FC-20260402-074354-ADR036-C

- 状态：`resolved`
- 结论：ADR-036 chain materialization 不再把 UI 当默认 formal layer 或默认 downstream leg。
- 关键修复：
  - 按 `downstream_workflows` 显式判断 UI applicability
  - 无 `feat-to-ui` workflow 时将 `ui` 标为 `not_applicable`
  - release index 不再默认输出 `ui_artifact_refs`
  - gate summary 不再暗示 `feat-to-ui` 是这条链路的正式下游腿
- 验证：
  - `python -m pytest tests/unit/test_materialize_adr036_ssot.py -q`

## 已关闭但未重建旧对象

### FC-20260402-171755-SRC001-P

- 状态：`closed`
- 结论：按用户决策关闭。机制层 guard 已收紧，但旧 case 指向的内容对象未在当前 workspace 中重建，因此本条不是“内容已复原后验证通过”的 resolved。
- 已完成：
  - `impl-spec-test` freeze guard 现在要求 `verdict=pass`
  - 同时要求 `implementation_readiness=ready`
  - 同时要求 `self_contained_readiness=sufficient` 和 review coverage sufficient
- 验证：
  - `python -m pytest tests/unit/test_impl_spec_guard_freeze.py tests/unit/test_ll_gate_human_orchestrator.py -q`

### FC-20260403-053640-SRC002-F

- 状态：`closed`
- 结论：按用户决策关闭。机制层 guard 已收紧，但旧 case 指向的内容对象未在当前 workspace 中重建，因此本条不是“内容已复原后验证通过”的 resolved。
- 已完成：
  - `impl-spec-test` freeze/readiness 前移
  - `gate-human-orchestrator` 明确要求 `machine_ssot_ref` 进入 `decision_basis_refs`
  - `projection_status=review_visible` 成为显式门槛
- 验证：
  - `python -m pytest tests/unit/test_impl_spec_guard_freeze.py tests/unit/test_gate_human_orchestrator_semantics.py tests/unit/test_ll_gate_human_orchestrator.py -q`

## 批次总览

- `resolved`: 4 / 6
- `closed`: 2 / 6
- `open`: 0 / 6

当前判断：

- 生成侧失败链路的核心问题已经完成主要修复，尤其是 `failure-capture`、`web-e2e` 和 `proto fidelity`。
- reviewer 漏拦截也已明显收紧。
- `SRC001/SRC002` 这两条按用户决策关闭，但关闭依据是“机制已收紧 + 原对象未重建”，不是内容侧逐项复验通过。
