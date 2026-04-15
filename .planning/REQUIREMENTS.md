# Requirements: ADR-049 Experience Patch Layer Implementation

**Milestone:** v1.0-adr049
**Source:** ADR-049 v2.1 (frozen 2026-04-15)
**Defined:** 2026-04-16
**Core Value:** 为体验期高频碎改提供轻量中间治理层，防止 SSOT 漂移和测试链失真

---

## MVP Requirements (P0)

### REQ-PATCH-01: Patch Schema + 目录结构

**Source:** ADR-049 §7, §8, §10

- [ ] 定义 Patch YAML schema 文件（`ssot/schemas/qa/patch.yaml`）
  - 必填字段：id, feat_id, change_type (visual|interaction|semantic), description, affected_files, status, created_at
  - 选填字段：test_impact, backwrite_targets, ui_before, ui_after, semantic_rule_delta
- [ ] 创建目录结构规范
  - 位置：`.artifacts/{FEAT-ID}/experience-patches/`
  - 命名：`PATCH-{seq}.yaml`（如 `PATCH-001.yaml`）
- [ ] 创建 `patch_registry.json` 索引文件（每个 FEAT 一个）
  - 记录所有 Patch 的 id, status, change_type, created_at

### REQ-PATCH-02: Patch 登记 Skill

**Source:** ADR-049 §6, §9, §14

- [ ] 创建 `ll-experience-patch-register` 技能
  - 支持人工填写 Patch 信息（交互式 prompt）
  - 支持 AI 自动检测代码 diff → 建议 Patch
  - 输出合法 YAML 到 `.artifacts/{FEAT-ID}/experience-patches/`
  - 自动更新 `patch_registry.json`
- [ ] 双路径登记
  - Prompt-to-Patch：用户直接描述变更 → AI 生成 Patch YAML
  - Document-to-SRC：BMAD/Superpowers/OWC 产出文档 → 解析为 SRC + Patch（如涉及体验层）
- [ ] CLI 注册 `patch-register` 动作

### REQ-PATCH-03: 结算 Skill + 回写工具

**Source:** ADR-049 §11, §12

- [ ] 创建 `ll-experience-patch-settle` 技能
  - 批量读取 pending_backwrite 状态的 Patch
  - 按 change_type 分类回写目标：
    - visual → TECH 文档（不升级）
    - interaction → UI 文档
    - semantic → FEAT + 相关高层文档
  - 生成结算报告（resolved_patches.yaml）
  - 标记 Patch 为 `resolved`（不删除）
- [ ] 创建回写辅助脚本
  - 自动生成 SSOT artifact 变更草稿
  - 人工审核确认后再写入

## Phase 2 Requirements (P1)

### REQ-PATCH-04: 测试联动规则

**Source:** ADR-049 §13

- [ ] Patch schema 中 `test_impact` 字段必填
  - 枚举值：none, path_change, assertion_change, new_case_needed
- [ ] 当 test_impact != none 时，登记 Patch 后自动：
  - 标记相关 TESTSET 为 `needs_review`
  - 生成 TESTSET 更新建议草稿
- [ ] Patch-aware Harness 适配
  - 执行测试前检查是否有 active/resolved Patch
  - 合并 Patch 的 test_impact 信息到测试验证逻辑

### REQ-PATCH-05: AI Context 注入

**Source:** ADR-049 §14.2

- [ ] 创建 Patch context 文件生成器
  - 读取 `.artifacts/{FEAT-ID}/experience-patches/` 下所有 active/resolved Patch
  - 合并为 `patch-context.yaml`（AI 可读格式）
- [ ] AI 生成代码前自动注入 Patch context
  - 在 skill 的 executor.md 中添加 context injection 步骤
  - AI 读取 "SSOT + active Patches" 后再生成代码

### REQ-PATCH-06: Hook 集成

**Source:** ADR-049 §9

- [ ] 配置 PreToolUse hook（Edit 操作）
  - 检测体验期文件变更（前端组件、样式文件等）
  - 自动提示是否需要登记 Patch
  - 用户确认后自动生成 Patch YAML
- [ ] Hook 白名单机制
  - 非体验期文件不触发
  - 已关联 Patch 的文件不重复触发

### REQ-PATCH-07: 24h Blocking 机制

**Source:** ADR-049 §11.3

- [ ] 结算计时器
  - 从第一个 active Patch 创建开始计时
  - 24h 后未结算 → 标记 `BLOCKED` 状态
  - BLOCKED 状态下禁止新的 Patch 登记（critical 除外）
- [ ] 触发条件（任一满足即触发结算）：
  - 24h 超时
  - Patch 数量 > 10（同一 FEAT）
  - 用户手动触发 `/gsd-settle-patches`
- [ ] 审计告警
  - BLOCKED 状态记录到审计日志
  - 告警信息包含：FEAT ID, Patch 数量, 超时时间

## Non-Functional Requirements

| ID | Requirement | Target |
|----|------------|--------|
| NFR-01 | Patch 登记耗时 | < 30 秒/条（人工审核时间） |
| NFR-02 | Patch YAML 文件大小 | < 2KB/条 |
| NFR-03 | Schema 验证失败率 | 0%（所有 Patch 必须通过验证） |
| NFR-04 | 测试失真率 | 0%（有 test_impact 声明的 Patch 必须触发 TESTSET 更新） |

## Out of Scope

| Feature | Reason |
|---------|--------|
| Python 生产级 CLI 运行时 | 本轮只做 Prompt-first 技能，Python 运行时留给后续 |
| Patch 冲突检测 | 多 Patch 修改同一文件的冲突场景非本轮重点 |
| 自动回写 SSOT | 本轮只做草稿生成，人工审核确认后再写入 |
| E2E Patch 联动 | E2E 测试链的 Patch 适配留给后续扩展 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-PATCH-01 | Phase 1 | Pending |
| REQ-PATCH-02 | Phase 2 | Pending |
| REQ-PATCH-03 | Phase 3 | Pending |
| REQ-PATCH-04 | Phase 4 | Pending |
| REQ-PATCH-05 | Phase 5 | Pending |
| REQ-PATCH-06 | Phase 6 | Pending |
| REQ-PATCH-07 | Phase 7 | Pending |

**Coverage:**
- v1.0-adr049 requirements: 7 total + 4 NFRs
- Mapped to phases: 7
- Unmapped: 0

---
*Requirements defined: 2026-04-16*
