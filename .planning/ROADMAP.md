# Roadmap: ADR-049 Experience Patch Layer Implementation

**Created:** 2026-04-16
**Milestone:** v1.0-adr049
**Granularity:** Standard (7 phases, MVP-first)
**Total Requirements:** 7 + 4 NFRs

---

## Phase 1: Patch Schema + 目录结构

**Goal:** 定义 Patch YAML schema 和目录规范，为所有后续工作奠定基础。

**Requirements:** REQ-PATCH-01

**Plans:** 2 plans

Plans:
- [x] 01-01-PLAN.md — Patch YAML schema definition + directory structure with example
- [x] 01-02-PLAN.md — Python schema validator (TDD) with unit tests + CLI entry point

**Success Criteria:**
1. `ssot/schemas/qa/patch.yaml` 存在且包含所有必填/选填字段
2. `ssot/experience-patches/` 目录结构示例已创建（含 README 说明 + 示例 Patch）
3. Python schema 验证器（`cli/lib/patch_schema.py`）通过单元测试

**UI hint:** no

---

## Phase 2: Patch 登记 Skill

**Goal:** 创建 `ll-experience-patch-register` 技能，支持双路径登记（Prompt-to-Patch + Document-to-SRC）。

**Requirements:** REQ-PATCH-02
**Depends on:** Phase 1 (schema ready)

**Skill gets:**
- `scripts/run.sh` — Claude Code 子代理调用 wrapper
- `agents/executor.md` — LLM prompt 模板
- `validate_input.sh` — 输入验证
- `validate_output.sh` — 输出 schema 校验
- `ll.lifecycle.yaml` — 生命周期定义

**Success Criteria:**
1. 技能文件结构完整（run.sh + executor.md + validate + lifecycle）
2. Prompt-to-Patch 路径可工作：用户描述 → 生成合法 YAML
3. `patch_registry.json` 自动更新
4. CLI 已注册 `patch-register` 动作

**UI hint:** no

---

## Phase 3: 结算 Skill + 回写工具

**Goal:** 创建 `ll-experience-patch-settle` 技能，实现批量回写 SSOT。

**Requirements:** REQ-PATCH-03
**Depends on:** Phase 1 (schema), Phase 2 (patch registry)

**Skill gets:**
- `scripts/run.sh` — 批量结算 wrapper
- `agents/executor.md` — LLM prompt（回写草稿生成）
- `validate_input.sh` — 验证 pending_backwrite Patch 存在
- `validate_output.sh` — 验证结算报告完整性
- `ll.lifecycle.yaml` — 生命周期定义

**Success Criteria:**
1. 技能文件结构完整
2. 能按 change_type 分类回写（visual→TECH, interaction→UI, semantic→FEAT）
3. 生成 resolved_patches.yaml 结算报告
4. 回写草稿生成后需人工审核确认

**UI hint:** no

---

## Phase 4: 测试联动规则

**Goal:** 实现 Patch → TESTSET 同步机制，Patch-aware Harness 适配。

**Requirements:** REQ-PATCH-04
**Depends on:** Phase 1 (test_impact field in schema)

**Success Criteria:**
1. test_impact 字段在 Patch schema 中必填
2. test_impact != none 时自动标记 TESTSET 为 needs_review
3. Harness 执行前读取 active/resolved Patch 信息
4. 测试验证逻辑合并 Patch 的 test_impact

**UI hint:** no

---

## Phase 5: AI Context 注入

**Goal:** AI 生成代码前自动注入 Patch 上下文，防止覆盖已有优化。

**Requirements:** REQ-PATCH-05
**Depends on:** Phase 1 (schema), Phase 2 (patch registry)

**Success Criteria:**
1. Patch context 文件生成器可工作
2. 合并 active/resolved Patch 为 patch-context.yaml
3. Skill executor.md 中集成 context injection 步骤
4. AI 基于 "SSOT + Patches" 生成代码

**UI hint:** no

---

## Phase 6: Hook 集成

**Goal:** PreToolUse hook 自动触发 Patch 登记，减少人工操作。

**Requirements:** REQ-PATCH-06
**Depends on:** Phase 2 (patch register skill exists)

**Success Criteria:**
1. PreToolUse hook 配置完成（Edit 操作）
2. 检测体验期文件变更自动提示 Patch 登记
3. 用户确认后自动生成 Patch YAML
4. 白名单机制工作（非体验期文件不触发）

**UI hint:** no

---

## Phase 7: 24h Blocking 机制

**Goal:** 结算计时器 + 超时 blocking + 审计告警。

**Requirements:** REQ-PATCH-07
**Depends on:** Phase 3 (settlement skill)

**Success Criteria:**
1. 从第一个 active Patch 创建开始计时
2. 24h 后未结算 → 标记 BLOCKED 状态
3. BLOCKED 状态下禁止新 Patch 登记
4. 任一触发条件（24h / >10 patches / 手动）触发结算
5. 审计日志记录 BLOCKED 状态

**UI hint:** no

---

## Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-PATCH-01: Patch Schema + 目录结构 | Phase 1 | Planned (2 plans) |
| REQ-PATCH-02: Patch 登记 Skill | Phase 2 | Pending |
| REQ-PATCH-03: 结算 Skill + 回写工具 | Phase 3 | Pending |
| REQ-PATCH-04: 测试联动规则 | Phase 4 | Pending |
| REQ-PATCH-05: AI Context 注入 | Phase 5 | Pending |
| REQ-PATCH-06: Hook 集成 | Phase 6 | Pending |
| REQ-PATCH-07: 24h Blocking 机制 | Phase 7 | Pending |

**Coverage:**
- v1.0-adr049 requirements: 7 total + 4 NFRs
- Mapped to phases: 7
- Unmapped: 0

---
*Roadmap defined: 2026-04-16*
