# ADR-058：Complete Design Package 输入解析的 Tiered Semantic Extraction 架构

> **SSOT ID**: ADR-058
> **Title**: Complete Design Package 输入解析的 Tiered Semantic Extraction 架构
> **Status**: Draft
> **Version**: v1.0
> **Effective Date**: 2026-05-26
> **Scope**: frz-ingest 输入解析管道、parser 语义提取策略、LLM fallback 机制
> **Owner**: LL v2 架构 / frz-ingest
> **Governance Kind**: NEW
> **Audience**: AI 实施代理、parser 维护者、上游设计工具开发者
> **Depends On**: ADR-056 (FRZ 架构), ADR-057 (SSOT 文件管理规范)

---

## 1. 背景

### 1.1 一句话总结

> **将 frz-ingest 的输入解析从"纯规则引擎"升级为"三层语义提取管道"：显式结构化输入优先、规则引擎兜底、LLM 语义 fallback 作为最后防线。**

### 1.2 历史问题

ADR-056 §7.3 step_2 定义了 frz-ingest 的核心职责——将 Complete Design Package 编译为 SSOT 链。但 step_2 的前提是 parser 已成功将原始 Markdown 转换为结构化数据。

当前 parser（`cli/lib/v2/parser._extract_structured_fields()`）采用**纯规则匹配**策略：
- 文件名关键词白名单决定是否扫描某维度
- 正则表达式匹配特定 AC 格式（如 `**AC-XXX**: ...`）
- Markdown heading + 表格结构约束提取 tech_stack

这种策略在 ai-marathon-root-v2 项目（17 个 PRD、8 个 Tech Spec、6 个 API Doc）上实测后暴露了三类系统性缺陷：

1. **覆盖度不足**：AC ID 含连字符（`AC-M12-001.1`）时正则匹配失败；PRD 文件名不含 `journey` 关键词时用户旅程被完全跳过
2. **维护成本高**：每支持一个新项目格式就要新增/修改规则，规则之间产生冲突
3. **与上游工具耦合**：parser 假设上游设计工具（BMAD 等）输出固定格式，但实际上各工具输出风格差异巨大

ADR-056 §7.3 step_4_5 auto_repair 已意识到 parser 的脆弱性：

```yaml
parser_gap: "字段在 __raw__ 中但 Parser 未提取 → 放宽正则、降低 heading 级别、增加同义词映射"
```

但 "放宽正则" 是**战术级修复**，无法解决规则引擎的根本局限——规则的覆盖度永远追不上人类表达的多样性。

### 1.3 与现有 ADR 的关系

| ADR | 关系 |
|-----|------|
| ADR-056 (FRZ 架构) | 本 ADR 细化 ADR-056 §7.3 step_2 的输入解析实现，step_4_5 auto_repair 的 parser_gap 策略由本 ADR 正式替代 |
| ADR-057 (文件管理规范) | 本 ADR 的 Tier 1 显式输入 schema 继承 ADR-057 的 YAML 模板定义 |

---

## 2. 问题

### 2.1 规则引擎的根本局限

规则引擎的核心假设是：**上游工具的输出格式是可枚举的**。这个假设在现实中不成立：

| 上游工具 | 输出风格 | 与 parser 规则的兼容性 |
|---------|---------|----------------------|
| BMAD (v1) | `**AC-001.1**: Given...` | ✅ 匹配 |
| BMAD (v2) | `**AC-M12-001.1**: Given...` | ❌ 连字符导致失败 |
| 人工 PRD | `### 用户故事 P0` + US-XXX | ⚠️ 依赖文件名含 `user_stories` |
| Notion 导出 | `# 用户旅程` + 段落描述 | ❌ 无正则匹配目标 |
| 中文 Tech Spec | `| 模块 | 技术方案 | 版本 |` | ❌ 表头不在白名单 |

### 2.2 引入 LLM 的风险

直接替换规则引擎为 LLM 提取也有问题：
- **成本**：每次 frz-ingest 都调用 LLM 解析全部文档，费用不可控
- **延迟**：LLM 调用增加编译时间
- **幻觉**：LLM 可能"发明"文档中不存在的字段
- **确定性**：规则引擎的结果是确定性的，LLM 结果有随机性

### 2.3 需要平衡的维度

```yaml
parser_requirements:
  robustness: "必须处理上游工具的各种输出风格"
  cost: "不能被 LLM 调用费用压垮"
  latency: "不能显著增加编译时间"
  determinism: "相同输入应产生相同输出（可重现）"
  no_hallucination: "不能提取文档中不存在的内容"
  maintainability: "新增项目格式不应要求改代码"
```

---

## 3. 决策

### 3.1 总体决策

采用 **Tiered Semantic Extraction Pipeline（三层语义提取管道）**：

```text
Complete Design Package (Markdown / YAML / 混合)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 1: 显式结构化输入 (Explicit Structured Input)       │
│ ─────────────────────────────────────────────────────  │
│ 如果文档 frontmatter 或并排 YAML 提供了结构化数据，      │
│ 直接读取，跳过所有解析。                                  │
│ 成本: 0    置信度: 100%    幻觉风险: 0                   │
└─────────────────────────────────────────────────────────┘
    │  未命中
    ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 2: 规则引擎 (Rule-Based Extraction)                 │
│ ─────────────────────────────────────────────────────  │
│ 修复后的正则匹配 + 内容启发式（不依赖文件名白名单）       │
│ 输出 confidence score，标记不确定的提取结果。            │
│ 成本: 低   置信度: 中-高   幻觉风险: 低                  │
└─────────────────────────────────────────────────────────┘
    │  提取为空 或 confidence < threshold
    ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 3: LLM 语义 fallback (Semantic Extraction)         │
│ ─────────────────────────────────────────────────────  │
│ 将原始 Markdown + 目标 schema 传给轻量级 LLM，           │
│ 让模型理解内容并输出结构化 JSON。                         │
│ 输出必须经过溯源校验才能生效。                           │
│ 成本: 中   置信度: 高     幻觉风险: 中（有校验）          │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Structured Design Package → 进入 ADR-056 §7.3 step_2 编译
```

### 3.2 关键设计原则

1. **显式优先于推断**：如果文档作者主动提供了结构化数据（Tier 1），绝不用规则或 LLM 覆盖
2. **规则为主，LLM 兜底**：Tier 2 处理 90%+ 的场景，Tier 3 只处理剩余 10%
3. **确定性优先**：Tier 3 的 LLM 输出必须经过**溯源校验**（traceback validation），确保提取内容能在原文中找到依据
4. **成本可控**：Tier 3 按**维度**触发，不是按文档触发；只调用缺失的维度，不重复解析已有数据

---

## 4. Tier 1: 显式结构化输入

### 4.1 Markdown Frontmatter Schema

文档作者可以在 Markdown frontmatter 中显式标注需要提取的字段：

```markdown
---
frz_schema:
  version: "1.0"
  source_tool: "bmad-v2"
  dimensions:
    product_design:
      fields:
        - user_journey_map
        - acceptance_criteria
      extraction_hint: "AC 在 ## 验收标准 章节，旅程在 ## 用户旅程 章节"
    architecture_design:
      fields:
        - tech_stack
        - api_contract
      extraction_hint: "技术选型在表格中，API 在代码块中"
---

# PRD-M12-Onboarding-Identity

## 产品愿景
...
```

当 parser 检测到 `frz_schema` frontmatter 时：
1. 扫描 `fields` 中列出的字段
2. 对于每个字段，优先使用 frontmatter 旁的 YAML 数据文件（见 §4.2）
3. 如果没有并排 YAML，使用 `extraction_hint` 指导 Tier 2 的解析（提高 confidence）
4. **不触发 Tier 3**（因为作者已显式声明了字段位置）

### 4.2 并排 YAML 数据文件

允许 Markdown 文档与结构化数据文件并存：

```text
prds/
  ├── PRD-M01-Plan-Today-Card.md       # 人类可读文档
  ├── PRD-M01-Plan-Today-Card.yaml     # 机器可读结构化数据（可选）
  ├── PRD-M02-Checkin.md
  └── PRD-M02-Checkin.yaml             # 可选
```

YAML 文件内容示例：

```yaml
frz_schema:
  version: "1.0"
  source_file: "PRD-M01-Plan-Today-Card.md"
product_design:
  user_journey_map:
    - name: "查看今日计划"
      value: "用户打开 App 查看今日训练计划"
      steps: ["打开 App", "进入首页", "查看计划卡片"]
      priority: "P0"
  acceptance_criteria:
    - "AC-M01-001: Given 用户已登录，When 进入首页，Then 显示今日计划卡片"
```

**优先级规则**：
- 如果存在 `.yaml` 并排文件，直接使用，跳过 Tier 2/3
- 如果 frontmatter 中 `frz_schema.fields` 为空数组，表示**该维度已由作者确认不存在**，不触发任何提取

### 4.3 纯 YAML/JSON 输入模式

当 Complete Design Package 直接以 YAML/JSON 形式提供时（如 API 调用），parser 直接解析，不经过 Tier 2/3：

```yaml
complete_design_package:
  business_design:
    product_vision: "..."
    scope_declaration:
      in_scope: [...]
      out_of_scope: [...]
  product_design:
    user_journey_map: [...]
    acceptance_criteria: [...]
```

---

## 5. Tier 2: 规则引擎

### 5.1 核心修复（相对于当前实现）

#### 5.1.1 解除文件名强耦合

**当前实现**：`user_journey_map` 提取被包裹在 `if is_journey_file or is_story_file` 中，PRD 文件名不含关键词时完全跳过。

**修复后**：所有文件都扫描内容，通过**内容启发式**判断维度归属：

```python
# 旧逻辑（移除）
if "journey" in source_lower or "user_stories" in source_lower:
    # 提取旅程

# 新逻辑
has_journey_signal = bool(re.search(
    r'^#{2,4}\s*(?:用户旅程|User Journey|用户流程|User Flow|旅程|Journey|US-\d+)',
    raw, re.MULTILINE | re.IGNORECASE
))
# 始终提取，但标记 confidence
```

#### 5.1.2 AC 正则支持连字符和扩展 ID 格式

```python
# 旧正则
r'AC-[\w.]+'

# 新正则（支持模块前缀、连字符、下划线）
r'AC-[A-Za-z0-9._-]+'

# 同时支持无 AC- 前缀的 Given-When-Then 段落
# 作为 Tier 2 的 secondary pattern
```

#### 5.1.3 tech_stack 表头白名单扩展

```python
TECH_STACK_HEADERS = (
    # 原有
    "组件", "component", "技术", "technology", "选型", "stack", "name",
    # 新增
    "模块", "module", "服务", "service", "层", "layer",
    "依赖", "dependency", "框架", "framework",
    "库", "library", "工具", "tool", "平台", "platform",
    "语言", "language", "数据库", "database", "存储", "storage",
)
```

#### 5.1.4 支持非表格格式

在表格提取失败后，尝试从列表/段落提取：

```python
def _extract_tech_stack(body: str) -> list[dict]:
    # 1. 尝试表格
    tech_stack = _extract_tech_stack_from_table(body)
    # 2. 尝试列表（- 前端: React 18）
    if not tech_stack:
        tech_stack = _extract_tech_stack_from_list(body)
    # 3. 尝试段落
    if not tech_stack:
        tech_stack = _extract_tech_stack_from_paragraphs(body)
    return tech_stack
```

### 5.2 Confidence Score 机制

Tier 2 每个提取项输出 confidence score（0.0-1.0）：

```python
class ExtractionResult:
    field: str
    value: Any
    confidence: float        # 0.0-1.0
    matched_patterns: list   # 匹配到的模式 ID
    raw_evidence: str        # 原文片段（用于 Tier 3 校验）
```

**Confidence 计算规则**：

| 场景 | Confidence | 说明 |
|------|-----------|------|
| 多个独立模式都匹配到同一字段 | 0.9+ | 高度可信 |
| 单一模式匹配，但格式完全符合 | 0.7-0.9 | 可信 |
| 模式匹配但格式有偏差（如 AC ID 含未知字符） | 0.5-0.7 | 中等 |
| 启发式匹配（如 heading 匹配但内容格式不确定） | 0.3-0.5 | 低置信 |
| 无任何模式匹配 | 0.0 | 进入 Tier 3 |

**Tier 2 → Tier 3 的触发条件**：

```yaml
tier_2_to_3_trigger:
  conditions:
    - field_value_is_empty AND dimension_has_substantive_content
    - confidence < 0.5
    - completeness_Q1_Q5_blocked_due_to_field_missing
  scope: "按维度触发，不是按文档触发"
  example: "product_design.acceptance_criteria 为空但 product_design.__raw__ 有实质内容 → 只对该字段触发 Tier 3"
```

---

## 6. Tier 3: LLM 语义 Fallback

### 6.1 触发条件

Tier 3 仅在以下条件下触发：

```yaml
tier_3_trigger:
  must_all_be_true:
    - "Tier 2 对该维度的提取为空 或 confidence < 0.5"
    - "该维度的 __raw__ 内容长度 > 200（有实质内容可提取）"
  plus_any_of:
    - "completeness Q1-Q5 因该字段缺失而被 BLOCK"
    - "--semantic-extract 强制启用"
    - "环境变量 FRZ_TIER3_ALWAYS=1"
  exclusion:
    - "如果 frontmatter 中 frz_schema.fields 显式声明该维度为空，不触发"
    - "如果 --no-llm-fallback 参数被设置，不触发"
```

### 6.2 模型选择

```yaml
llm_config:
  primary_model: "anthropic/claude-haiku-4-5"
  rationale: "Haiku 90% Sonnet 能力，3x 成本节省，解析任务不需要深度推理"
  fallback_model: "anthropic/claude-sonnet-4-6"
  fallback_condition: "Haiku 返回格式错误 或 结果未通过溯源校验"
  max_tokens: 4000
  temperature: 0.0    # 解析任务要求确定性，零温度
```

### 6.3 Prompt 设计

```python
TIER3_SYSTEM_PROMPT = """你是一个文档解析助手。你的任务是从 Markdown 设计文档中提取结构化字段。

规则：
1. 只提取文档中**明确存在**的内容，不要推断、不要发明
2. 如果文档中某字段不存在，返回 null 或空数组，不要编造
3. 输出必须是合法的 JSON，符合提供的 schema
4. 对每个提取的字段，提供 "evidence" 字段，引用原文中的确切片段
5. 如果文档使用中文，输出也用中文；如果文档使用英文，输出也用英文
"""

def build_tier3_prompt(raw: str, target_fields: list[str], schema: dict) -> str:
    return f"""
请从以下 Markdown 文档中提取以下字段：{', '.join(target_fields)}

输出 schema：
{json.dumps(schema, indent=2, ensure_ascii=False)}

要求：
- 只提取文档中明确存在的内容
- 对每个字段提供 "evidence" 字段，引用原文中的确切片段（至少 10 个字符）
- 如果字段不存在，值为 null

文档内容：
---
{raw}
---
"""
```

### 6.4 溯源校验（Hallucination Guard）

Tier 3 的输出**必须经过校验**才能生效：

```python
def validate_tier3_output(raw: str, extracted: dict) -> tuple[bool, dict]:
    """校验 LLM 提取结果是否在原文中有依据。"""
    validated = {}
    for field, value in extracted.items():
        evidence = value.get("_evidence", "")
        if not evidence:
            continue  # 无 evidence = 未通过校验
        if evidence not in raw and _fuzzy_match(evidence, raw) < 0.8:
            logger.warning(f"Tier 3 hallucination detected: {field}")
            continue  # evidence 不在原文中，丢弃
        validated[field] = value
    return len(validated) > 0, validated
```

**校验规则**：
1. LLM 必须提供 `"_evidence"` 字段，引用原文中的确切片段
2. Evidence 片段必须在原文中存在（精确匹配或 fuzzy match ≥ 0.8）
3. 未通过校验的字段丢弃，不进入 completeness 检查
4. 如果校验后所有字段都丢弃，视为 Tier 3 失败，记录到日志

### 6.5 成本控制

```yaml
tier_3_cost_control:
  per_frz_budget:
    max_llm_calls: 5        # 单次 frz-ingest 最多 5 次 LLM 调用
    max_tokens_total: 20000  # 单次 frz-ingest 最多消耗 20k tokens
  per_call_budget:
    max_input_tokens: 8000   # 单次调用输入不超过 8k tokens
    max_output_tokens: 4000  # 单次调用输出不超过 4k tokens
  cost_tracking:
    log_to: "logs/frz-ingest.log"
    fields: [model, input_tokens, output_tokens, cost_usd, fields_extracted]
  circuit_breaker:
    if_cost_exceeds: "$0.10 per run"
    action: "降级为标记 warning，不 BLOCK，提示用户补充结构化输入"
```

---

## 7. 与 ADR-056 的衔接

### 7.1 输入解析在 frz-ingest 流程中的位置

```text
ADR-056 §7.3 step_1 (completeness_check)
    │ 检查维度是否存在（结构检查，不检查内容质量）
    ▼
ADR-058 Tier 1/2/3 (本 ADR) ← 新增明确阶段
    │ 将原始 Markdown 解析为结构化 Design Package
    ▼
ADR-056 §7.3 step_2 (compile)
    │ 映射 + 拆解 + 格式标准化
    ▼
...后续步骤不变
```

### 7.2 ADR-056 step_4_5 auto_repair 的更新

ADR-056 §7.3 step_4_5 的 auto_repair 策略更新为：

```yaml
auto_repair:
  strategies:
    # 旧策略（废弃）
    # parser_gap: "放宽正则、降低 heading 级别、增加同义词映射"

    # 新策略
    tier_1_prompt: "字段在 __raw__ 中但 Parser 未提取 → 检查是否有 frontmatter/YAML 显式输入"
    tier_2_repair: "Tier 2 confidence < 0.5 → 尝试 Tier 3 LLM fallback"
    tier_3_failure: "Tier 3 失败 → 生成 HUMAN-REVIEW 阻塞清单，提示用户补充结构化输入或修正文档格式"
```

### 7.3 completeness 判定更新

```yaml
completeness_verdict_update:
  blocked:
    condition_update: |
      新增：如果 Tier 3 因成本/幻觉校验失败而无法提取，
      且文档确有实质内容，completeness 不直接 BLOCK，
      而是降级为 "partial"，并附加 "parser_ambiguity_warning"，
      允许用户确认后继续（人类 Override）。
    rationale: "避免 parser 能力不足导致合理的 Design Package 被拒绝"
```

---

## 8. 拒绝方案

### 8.1 纯 LLM 提取（拒绝）

**方案**：废弃规则引擎，所有解析都走 LLM。

**拒绝理由**：
- 成本高：每次 frz-ingest 解析 10+ 篇文档，全部调 LLM 不可接受
- 延迟大：LLM 调用增加分钟级延迟
- 不必要的浪费：80%+ 的标准格式文档规则引擎可以正确处理

### 8.2 纯规则引擎修复（拒绝）

**方案**：继续扩展正则规则，增加更多文件名触发条件和同义词映射。

**拒绝理由**：
- 这是当前路径，已被证明有架构级缺陷
- 规则集无限膨胀，维护成本指数增长
- 永远无法覆盖人类表达的全部多样性

### 8.3 要求上游输出标准 YAML（拒绝）

**方案**：强制要求 BMAD 等上游工具输出标准 YAML，不接受 Markdown。

**拒绝理由**：
- 不现实：设计阶段人类需要 Markdown 的可读性
- 与 LL 的定位冲突：ADR-056 定义 LL 是"项目级粘合层"，不应强制上游工具改变输出格式
- 增加上游工具的接入成本，降低 adoption

---

## 9. 实现路线图

### Phase 1: 短期（当前迭代）

1. **Tier 1 骨架**：支持 frontmatter `frz_schema` 读取
2. **Tier 2 修复**：
   - 解除文件名强耦合
   - AC 正则支持连字符
   - tech_stack 表头白名单扩展
   - 增加非表格格式提取
3. **Confidence Score 机制**：为 Tier 2 输出添加 confidence

### Phase 2: 中期（下一迭代）

4. **Tier 3 骨架**：LLM fallback 实现（Haiku 模型、prompt 模板、溯源校验）
5. **并排 YAML 支持**：自动检测 `.md` 旁的 `.yaml` 文件
6. **成本监控**：Tier 3 调用次数、token 消耗、费用日志

### Phase 3: 长期

7. **Prompt Caching 优化**：缓存系统 prompt，降低重复调用成本
8. **模型选择动态化**：根据字段复杂度自动选择 Haiku/Sonnet
9. **校验层增强**：引入语义相似度模型替代简单的 fuzzy match

---

## 10. Consequences

### 10.1 正向影响

1. **鲁棒性大幅提升**：不再因 AC ID 含连字符或 PRD 文件名不标准而 BLOCK
2. **上游工具解耦**：BMAD、Notion、人工 PRD 等各种来源都能被正确处理
3. **成本可控**：Tier 3 只处理 10% 的困难场景，不是全量
4. **渐进增强**：Phase 1 的 Tier 2 修复就能解决 80% 的当前问题
5. **人类 Override**：parser 不确定性时不硬 BLOCK，允许人类确认后继续

### 10.2 代价

1. **架构复杂度增加**：parser 从单一函数变为三层管道
2. **LLM 引入不确定性**：Tier 3 的结果有随机性，需要溯源校验
3. **调试成本**：三层之间的 fallback 逻辑增加了问题定位难度
4. **Token 成本**：Tier 3 虽然控制严格，但仍有增量成本

### 10.3 兼容性说明

本 ADR **不改变** ADR-056 的核心架构（编译=映射+拆解、冻结、验收双线路），只改变输入解析的实现方式。frz-ingest 的外部接口（输入、输出、CLI 参数）保持不变，新增参数为可选（`--semantic-extract`, `--no-llm-fallback`）。

---

## 11. Final Decision Summary

本 ADR 决定：

1. 废弃 ADR-056 §7.3 step_4_5 的 `parser_gap: "放宽正则"` 策略，升级为三层语义提取管道
2. **Tier 1**：显式结构化输入（frontmatter `frz_schema` + 并排 YAML），零成本、零幻觉
3. **Tier 2**：修复后的规则引擎（解除文件名耦合、扩展匹配、输出 confidence score）
4. **Tier 3**：LLM 语义 fallback（Haiku 模型、按维度触发、0.0 temperature、必须经过溯源校验）
5. **成本控制**：单次 frz-ingest 最多 5 次 LLM 调用、20k tokens，超出时降级为 warning
6. **completeness 宽容化**：parser 不确定性时不硬 BLOCK，允许人类 Override 后继续
7. 外部接口不变，新增可选参数 `--semantic-extract` 和 `--no-llm-fallback`
8. 分三期实现：Phase 1 Tier 1+2，Phase 2 Tier 3，Phase 3 优化

---

*文档版本：v1.0*
*创建日期：2026-05-26*
