---
name: ll-v2-frz-ingest
skill: ll-v2-frz-ingest
version: "2.0"
adr: ADR-056, ADR-058
category: freeze
chain: ll-v2
phase: governance
---

# ll-v2-frz-ingest

SSOT 编译与冻结工作流 — 接收 Complete Design Package，在编译零语义发明约束下执行完整性检查、编译 SSOT 链、对齐检查、漂移检测、生成验收测试用例、输出 FRZ Package 候选。

## Interface

- **Input**: `Complete Design Package` 目录路径
- **Output**: `FRZ Package` 候选（YAML）+ 编译日志
- **Mode**: 分步骤运行，支持 Agent 介入语义提取

## Entry Point

```bash
python skills/ll-v2-frz-ingest/src/frz_ingest.py --input <design-package-dir> --output <frz-output-dir> [--step <step>]
```

## Steps

### Step 1: Parse (Tier 2 规则提取)

```bash
python frz_ingest.py --input <dir> --output <dir> --step parse
```

Python 代码执行 Tier 2 规则提取（正则、heading 匹配、表格解析）。
输出：`.frz-tmp/design_package.json`

### Step 2: Gap Report (检测缺失字段)

```bash
python frz_ingest.py --input <dir> --output <dir> --step gap-report
```

扫描 design_package.json，检测 Tier 2 未能提取的字段。
输出：`.frz-tmp/gaps.json`

如果 `gaps.json` 中 `has_gaps: true`，进入 **Step 3（Agent 语义解析）**。
如果 `has_gaps: false`，直接跳到 **Step 4（Compile）**。

### Step 3: Agent Semantic Extraction (Tier 3)

**此步骤不由 Python 代码执行，由 Skill Agent 用自然语言处理。**

Agent 读取 `.frz-tmp/gaps.json`，对每个缺失字段：

1. 读取该字段对应的源文档（`source_files`）
2. 用自然语言理解文档内容，提取结构化字段
3. 将提取结果写回 `.frz-tmp/design_package.json`

Agent 指令模板：

```
以下字段在规则提取阶段未能成功提取，但源文档中有实质内容。
请阅读源文档，提取缺失字段的结构化数据。

维度: {dimension}
字段: {field}
描述: {description}
源文档: {source_files}

原始内容预览:
{raw_preview}

请将提取结果以 JSON 格式更新到 design_package.json 的 {dimension}.{field} 路径下。
只提取文档中明确存在的内容，不要推断、不要发明。
```

### Step 4: Compile (编译 SSOT 链)

```bash
python frz_ingest.py --input <dir> --output <dir> --step compile
```

读取（可能已被 Agent 修正的）design_package.json，执行：
- Completeness check (Q1-Q5)
- SSOT chain compilation
- Alignment check
- Drift detection
- Dimension quality gate
- Acceptance test generation
- FRZ Package freeze

### Full Mode (一步跑完)

```bash
python frz_ingest.py --input <dir> --output <dir> --step full
```

依次执行 Parse → Gap Report → Compile。如果检测到 gaps（`has_gaps: true`），立即报错终止，禁止继续编译。

## Architecture

```
Complete Design Package
    │
    ▼
Tier 2: Rule-Based Extraction (Python)
    │  正则、heading 匹配、表格解析
    ▼
design_package.json (Tier 2 结果)
    │
    ▼
Gap Detection (Python)
    │  检测缺失字段
    ▼
gaps.json
    │
    ▼
Tier 3: Agent Semantic Extraction (Skill Agent)
    │  自然语言理解、结构化提取
    ▼
design_package.json (已修正)
    │
    ▼
Compile Pipeline (Python)
    │  Completeness → Compile → Alignment → Drift → Quality → Freeze
    ▼
FRZ Package
```

## Key Design Principles

1. **Python 只做规则提取**：Tier 2 规则引擎处理标准格式（表格、列表、AC 正则）
2. **Agent 做语义理解**：Tier 3 语义提取由 Skill Agent 用自然语言处理，不嵌套 LLM API 调用
3. **分步骤运行**：Parse / Gap Report / Compile 可独立执行，Agent 在 Gap Report 后介入
4. **无 LLM API 依赖**：frz-ingest Python 代码不调用任何 LLM API，纯本地运行
5. **脚本错误强制传播**：任何 Python 脚本调用返回非零退出码时，skill 必须立即停止并报错，禁止手动继续运行。`full` 模式下若 `gaps.json` 存在且 `has_gaps: true`，同样必须报错终止，不得使用 Tier 2 不完整结果继续编译。

## CLI Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | required | Complete Design Package 目录 |
| `--output` | required | 输出目录 |
| `--step` | `full` | `parse` / `gap-report` / `compile` / `full` |
| `--src-id` | `SRC-001` | SRC 标识符 |
| `--slug` | auto | 文件命名 slug |
| `--project-type` | `generic` | 项目类型（generic, lee-lite） |
| `--rules-config` | - | 完整性规则 YAML 路径 |

## Files

| File | Purpose |
|------|---------|
| `src/frz_ingest.py` | CLI 入口，步骤编排 |
| `src/...` | 其他工具脚本 |
| `logs/frz-ingest.log` | 运行日志 |
