# Phase 12: Schema 定义层 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 12-schema-layer
**Areas discussed:** 文件组织, 验证模式, 错误消息风格, CLI 入口

---

## 文件组织

| Option | Description | Selected |
|--------|-------------|----------|
| 各自独立文件 | testset_schema.py, environment_schema.py, gate_schema.py | ✓ |
| 合并到 qa_schemas.py | 已有文件但已 800+ 行 | |
| 新建 governance_schemas.py | 统一存放所有治理 schema | |

**User's choice:** 各自独立文件
**Notes:** 与 task_pack_schema.py、frz_schema.py 一致，职责单一

## 验证模式

| Option | Description | Selected |
|--------|-------------|----------|
| 仅 dataclass + 验证函数 | task_pack_schema.py 模式 | |
| dataclass + 外部 YAML schema | 两者互补，项目已有约定 | ✓ |
| 两者都加 | 过度冗余 | |

**User's choice:** dataclass + 外部 YAML schema
**Notes:** 外部 YAML 供人类阅读规范，dataclass 供代码校验

## 错误消息风格

| Option | Description | Selected |
|--------|-------------|----------|
| 简洁单行错误 | 已有 QaSchemaError 模式 | ✓ |
| 结构化错误 | 含字段路径+允许值+建议 | |
| 两者混合 | 简单用简洁，复杂用结构化 | |

**User's choice:** 简洁单行错误
**Notes:** 错误信息已包含字段名和允许值，保持现有消费方兼容

## CLI 入口

| Option | Description | Selected |
|--------|-------------|----------|
| 各自独立 __main__ | python -m cli.lib.testset_schema file.yaml | ✓ |
| 统一入口 | python -m cli.lib.governance_schemas --type testset file.yaml | |
| 两者都支持 | 独立 + 统一 | |

**User's choice:** 各自独立 __main__
**Notes:** 零学习成本，与现有 10 个 schema 入口一致

## Claude's Discretion

- 具体 dataclass 字段默认值设计
- YAML schema 文件的具体格式风格

## Deferred Ideas

- None — discussion stayed within phase scope
