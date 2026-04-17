---
phase: 6
name: "PreToolUse Hook 集成（Patch 注入 + 自动登记）"
status: planned
created: 2026-04-17
goal: "在 AI 修改代码前自动注入相关 Patch context，在 AI 改代码后自动登记 Patch YAML。零手动步骤，仅用户确认分类。"
depends_on:
  - phase: 5
    artifact: patch-awareness.yaml schema + patch_aware_context.py
---

# Phase 6: PreToolUse Hook 集成

## Goal
在 AI 修改代码前自动注入相关 Patch context，在 AI 改代码后自动登记 Patch YAML。

## ADR-049 Alignment

| ADR-049 § | 要求 | Phase 6 实现方式 |
|-----------|------|-----------------|
| §3.4 | AI 必须能读取 Patch | CLAUDE.md 规则：Edit/Write 前自动读取 |
| §9.1 | 零手动登记 | PostToolUse 规则：改代码后自动扫描并填写 Patch YAML |
| §12.1 | 按文件匹配过滤 | 脚本扫描 `changed_files` 匹配当前编辑文件 |
| §12.2 | AI 自动生成 Patch 草案 | 脚本预填 + AI 补全 + 用户确认 |
| §10.1 | test_impact 强制声明 | Patch YAML 必填字段验证 |

## 核心设计：消费时注入

```
用户要求 AI 修改代码
    ↓
AI 执行 Edit / Write 操作
    ↓ (CLAUDE.md 规则触发)
自动执行: python scripts/find_related_patches.py --target-file {file}
    ↓
读取匹配到的 Patch YAML → 注入 AI 上下文
    ↓
AI 基于"SSOT + active Patch"生成代码
    ↓
代码写入完成
    ↓ (CLAUDE.md 规则触发)
自动执行: python scripts/auto_register_patch.py --changed-files {files}
    ↓
生成 Patch YAML 草案（预填 change_class, test_impact, backwrite_targets）
    ↓
AI 展示 Patch 草案，用户确认或调整
    ↓
用户确认 → Patch 入库
```

## Success Criteria
1. CLAUDE.md 新增规则：Edit/Write 前自动读取相关 Patch，改代码后自动登记
2. `scripts/find_related_patches.py` — 按目标文件匹配扫描 Patch 并输出 summary
3. `scripts/auto_register_patch.py` — 检测代码变更并预填 Patch YAML 草案
4. `ssot/experience-patches/` 目录结构 + 模板文件就位
5. 至少一个 Patch 的端到端演示：注入 → 改代码 → 自动登记 → 用户确认
