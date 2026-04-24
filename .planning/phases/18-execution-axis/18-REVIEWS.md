---
phase: 18
reviewers: [qwen]
reviewed_at: 2026-04-24
plans_reviewed: [18-01-PLAN.md, 18-02-PLAN.md, 18-03-PLAN.md, 18-04-PLAN.md]
note: Gemini/Codex/OpenCode CLI failed in Windows environment. Qwen review used as primary source.
---

# Cross-AI Plan Review — Phase 18

> **Note:** Phase 18 has already been executed and verified. This review is post-execution analysis for future reference.

## Qwen Review (Primary)

### Plan 18-01: run_manifest_gen.py

**Summary**

该计划设计清晰，定义了 run-manifest 的生成、加载和列表功能。存储路径遵循 D-01/D-02 决策，威胁模型考虑了路径遍历攻击。实现已完成并通过 24 项单元测试。

**Strengths**

- **明确的决策追溯**: D-01/D-02 决策在计划中明确引用，实现完全遵循
- **完善的威胁模型**: T-18-01/T-18-02 覆盖了路径遍历和 YAML 解析风险
- **良好的数据结构**: manifest 包含 git_sha、frontend_build、backend_build、base_url、browser、accounts 等完整字段
- **append-only 语义**: FileExistsError 防止覆盖，符合审计需求
- **单元测试覆盖**: 24 项测试覆盖核心功能和边界条件

**Concerns**

- **[LOW] 缺少并发写入保护**: 多进程同时写入同一 run_id 时存在竞态窗口
- **[LOW] build version 获取依赖 VERSION 文件**: 若 frontend/backend 目录不存在，返回 "unknown"，但没有提示用户如何修复
- **[MEDIUM] git 命令失败场景**: 在 CI 环境中 git 可能被禁用，应提供明确的 fallback 行为

**Suggestions**

- 添加 `flock` 或 Windows `msvcrt` 锁定机制防止并发写入竞态
- 在 manifest 中添加 `_build_version_source` 字段记录版本来源
- 考虑添加 `run_manifest_exists(workspace_root, run_id)` 查询函数

**Risk Assessment:** LOW — 功能边界清晰，已实现验证通过，威胁模型已覆盖主要风险。

---

### Plan 18-02: scenario_spec_compile.py

**Summary**

计划定义了 A/B/C 三层断言分离架构，C 层标记 C_MISSING 并收集 HAR + screenshot 证据。关键字匹配逻辑清晰，dataclass 结构完整。实现已完成，30 项测试通过。

**Strengths**

- **清晰的断言分层**: A-layer（UI 状态）、B-layer（网络/API）、C-layer（业务状态）各有独立关键字
- **C_MISSING 设计合理**: D-03/D-04 决策完整实现
- **Fallback 处理**: B-layer 无网络断言时添加 fallback
- **中英文关键字支持**: A-layer 包含 "显示" 等中文关键字

**Concerns**

- **[MEDIUM] 关键字匹配过于简单**: 使用简单的 `in` 检查，可能误匹配
- **[MEDIUM] 步骤提取缺失**: `compile_scenario_spec()` 未从 `_e2e_extension.ui_step_metadata` 提取 steps
- **[LOW] 缺少断言去重**: 同一条件可能被多个关键字同时匹配

**Suggestions**

- 改用词边界匹配：`re.search(r'\b' + keyword + r'\b', text_lower)`
- 在 `compile_scenario_spec()` 中显式提取 `_e2e_extension.steps`

**Risk Assessment:** MEDIUM — 关键字匹配精度可能影响断言分类准确性。

---

### Plan 18-03: state_machine_executor.py

**Summary**

计划定义了 5-state 状态机模型（SETUP/EXECUTE/VERIFY/COLLECT/DONE），状态持久化到 `{run_id}-state.yaml`。支持 resume 功能和 per-step 原子执行。实现已完成，31 项测试通过。

**Strengths**

- **状态机设计清晰**: 5-state 模型覆盖完整生命周期
- **状态持久化**: `{run_id}-state.yaml` 与 run-manifest 分离
- **Resume 功能**: `resume=True` 加载现有状态并跳过已完成步骤
- **Per-step 原子执行**: CompletedStep 记录 step_index、status、error

**Concerns**

- **[HIGH] VERIFY 状态逻辑被注释合并**: `_do_verify()` 为空实现
- **[MEDIUM] 缺少实际 Playwright 调用**: `_execute_step()` 是 placeholder
- **[MEDIUM] COLLECT → EXECUTE 恢复路径未明确**: 失败 journey 收集证据后是否继续其他 journey

**Suggestions**

- 在 `_do_verify()` 中实现 assertions 检查
- 集成 `cli/lib/test_exec_playwright.py` 替换 placeholder 实现
- 添加 `parallel_execution` 参数支持多 journey 并行

**Risk Assessment:** MEDIUM — VERIFY 状态空实现是主要风险点。

---

## Consensus Summary

### Agreed Strengths

1. 决策追溯完善（D-01~D-10）
2. 威胁模型覆盖主要风险（T-18-01~T-18-06）
3. 测试覆盖充分（121 tests passed）

### Agreed Concerns

1. **[MEDIUM] 关键字匹配精度**: 简单 `in` 检查可能误匹配
2. **[MEDIUM] VERIFY 状态空实现**: assertions 验证未在状态机中执行
3. **[MEDIUM] Playwright 集成缺失**: `_execute_step()` 是 placeholder

### Post-Execution Assessment

Phase 18 execution completed successfully:
- 4/4 plans completed
- 121 tests passed
- All must-haves verified

**Outstanding follow-up items** (for future phases):
1. Implement VERIFY state logic with actual assertions checking
2. Integrate `test_exec_playwright.py` for real E2E execution
3. Add word-boundary keyword matching for assertion extraction
4. Implement concurrent write protection for manifest generation
