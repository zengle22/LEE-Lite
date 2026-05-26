# BUG REPORT & PARSER ROADMAP: Markdown 结构化字段提取缺陷

> 报告者: Claude Code (ai-marathon-root-v2 项目)
> 日期: 2026-05-26
> 关联报告: [BUG-REPORT-frz-cross-project.md](BUG-REPORT-frz-cross-project.md)
> 优先级: P0 — 导致所有标准 PRD 格式的 AC / 旅程 / Tech Stack 无法被提取

---

## 1. 执行摘要

`cli.lib.v2.parser._extract_structured_fields()` 是 FRZ 流程中将原始 Markdown 转换为结构化设计包的核心函数。经过在 `ai-marathon-root-v2` 项目（含 17 个 PRD、8 个 Tech Spec、6 个 API Doc）上的实测，发现该函数存在 **1 个致命正则 Bug + 2 个设计缺陷**，导致标准格式的 Acceptance Criteria、User Journey Map、Tech Stack 在文档内容完整存在的情况下被系统性遗漏。

---

## 2. Bug #1: AC 正则表达式不支持连字符（致命）

### 2.1 代码位置

`cli/lib/v2/parser.py` 第 174–184 行

```python
ac_pattern = re.compile(
    r'^\s*[-*]\s*\*\*(AC-[\w.]+)\*\*:\s*(.*?)(?=\n\s*[-*]\s*\*\*AC-|\n#{1,4}\s|\Z)',
    re.MULTILINE | re.DOTALL,
)
```

### 2.2 根因分析

`[\w.]+` 只匹配字母、数字、下划线和点，**不匹配连字符 `-`**。

项目中实际使用的 AC ID 格式：
```markdown
- **AC-M12-001.1**: Given 用户输入有效的8位邀请码，When 点击验证，Then ...
- **AC-M12-001.2**: Given 用户输入已使用或无效的邀请码，When 点击验证，Then ...
```

正则执行过程：
1. `AC-` 匹配成功
2. `[\w.]+` 匹配 `M12`（`M`、`1`、`2` 都是 `\w`）
3. 下一个字符是 `-`，不在 `[\w.]` 中，匹配停止
4. 此时期望 `\*\*`（闭合 `**`），但实际下一个是 `-001.1**:`
5. **匹配失败，整条 AC 被跳过**

### 2.3 影响范围

- 所有使用 `AC-{模块}-{序号}.{子序号}` 格式的 PRD 文档
- 实测 17 个 PRD 文件，**0 个 AC 被提取**
- 直接导致 `product_design.acceptance_criteria` 为空，FRZ completeness Q3 被 BLOCK

### 2.4 修复建议

将 `AC-[\w.]+` 改为支持连字符和常见分隔符：

```python
# 方案 A: 最小修复
r'^\s*[-*]\s*\*\*(AC-[\w.-]+)\*\*:\s*(.*?)(?=\n\s*[-*]\s*\*\*AC-|\n#{1,4}\s|\Z)'

# 方案 B: 更宽松的 AC ID 格式（推荐，支持中文项目常见的变体）
r'^\s*[-*]\s*\*\*(AC-[A-Za-z0-9._-]+)\*\*:\s*(.*?)(?=\n\s*[-*]\s*\*\*AC-|\n#{1,4}\s|\Z)'
```

---

## 3. Bug #2: `user_journey_map` 提取完全依赖文件名白名单

### 3.1 代码位置

`cli/lib/v2/parser.py` 第 186–191 行

```python
# --- user_journey_map extraction ---
# Trigger on filename hints or explicit journey headings
is_journey_file = "journey" in source_lower or "user_journey" in source_lower
is_story_file = "user_stories" in source_lower or "acceptance_criteria" in source_lower

if is_journey_file or is_story_file:
    # ... 提取逻辑 ...
```

### 3.2 根因分析

**整个 `user_journey_map` 提取被包裹在 `if` 条件中。** 如果文件名不含以下任一关键词，函数直接跳过，**文档内容完全不扫描**：
- `journey`
- `user_journey`
- `user_stories`
- `acceptance_criteria`

项目中 PRD 文件名示例：
```
PRD-M01-Plan-Today-Card.md
PRD-M02-Checkin.md
PRD-M12-Onboarding-Identity.md
PRD-S01-S06-Domain-Data-Layer.md
```

这些文件名不含上述关键词，导致 PRD 中明确存在的用户旅程章节被完全忽略。

### 3.3 影响范围

- 所有按 `PRD-M{模块编号}-{模块名称}.md` 格式命名的 PRD
- 实测 17 个 PRD 文件，**0 个 journey 被提取**
- 直接导致 `product_design.user_journey_map` 为空，FRZ completeness Q2 被 BLOCK

### 3.4 修复建议

**方案 A（最小修复）**: 增加 PRD 文件名作为触发条件

```python
is_prd_file = "prd" in source_lower or "product" in source_lower or "feature" in source_lower
if is_journey_file or is_story_file or is_prd_file:
```

**方案 B（推荐）**: 改为内容驱动的启发式检测，解除文件名强耦合

```python
# 始终扫描内容，但通过启发式信号判断是否应该提取旅程
has_journey_signal = bool(re.search(
    r'^#{2,4}\s*(?:用户旅程|User Journey|用户流程|User Flow|旅程|Journey)',
    raw, re.MULTILINE | re.IGNORECASE
))
has_story_signal = bool(re.search(
    r'^#{2,4}\s*(?:用户故事|User Story|US-\d+)',
    raw, re.MULTILINE | re.IGNORECASE
))

if is_journey_file or is_story_file or has_journey_signal or has_story_signal:
    # ... 提取逻辑 ...
```

---

## 4. 设计缺陷 #1: `tech_stack` 提取的三重约束过于严格

### 4.1 代码位置

`cli/lib/v2/parser.py` 第 360–403 行

### 4.2 根因分析

`tech_stack` 提取需要同时满足以下三个条件之一：

**条件 1 — 文件名匹配:**
```python
is_tech_file = any(k in source_lower for k in [
    "implementation", "engineering", "tech_stack", "architecture",
    "decision_engine", "training_plan", "session_evaluation",
])
```

**条件 2 — Heading 匹配:**
```python
has_tech_heading = bool(re.search(
    r'^#{1,4}\s*(?:技术选型|Tech Stack|技术栈|技术架构|Technology)',
    raw, re.MULTILINE | re.IGNORECASE
))
```

**条件 3 — 表格格式匹配:**
```python
# 表头必须包含以下任一关键词
if not any(h in headers for h in ("组件", "component", "技术", "technology", "选型", "stack", "name")):
    continue
```

**问题:** 即使文件名和 heading 都匹配，如果表格表头不是 parser 预期的这几个中文/英文关键词（例如用 "Module"、"Service"、"Layer" 等），提取仍然为空。

### 4.3 影响范围

- Tech Spec 文档中技术栈以非表格形式描述（如列表、段落）时完全无法提取
- 表格表头使用非预期词汇时被跳过
- 实测中 `architecture_design` 的 `tech_stack` 为空，但文档中有完整的技术选型内容

### 4.4 修复建议

**方案 A**: 放宽表头匹配，增加常见变体

```python
TECH_STACK_HEADERS = (
    "组件", "component", "技术", "technology", "选型", "stack", "name",
    "模块", "module", "服务", "service", "层", "layer", "依赖", "dependency",
    "框架", "framework", "库", "library", "工具", "tool",
)
```

**方案 B（推荐）**: 支持非表格格式的 tech stack 提取

```python
# 在表格提取失败后，尝试从列表/段落中提取
tech_stack = _extract_tech_stack_from_table(body)
if not tech_stack:
    tech_stack = _extract_tech_stack_from_list(body)
if not tech_stack:
    tech_stack = _extract_tech_stack_from_paragraphs(body)
```

---

## 5. 系统性设计缺陷: 基于规则而非语义分析

### 5.1 问题描述

当前 parser 的 `_extract_structured_fields()` 采用**纯规则匹配**策略：
- 文件名关键词白名单
- 正则模式匹配特定格式（如 `**AC-XXX**: ...`）
- Markdown heading + 表格结构约束

**这与用户的预期严重不符。** 用户认为 "PRD 里面有用户旅程和 AC，arch 文档中有技术栈"，parser 应该能**理解内容**并提取出来。但实际上 parser 只是在**匹配预定义的模式**。

### 5.2 具体表现

| 用户预期 | parser 实际行为 | 结果 |
|---------|----------------|------|
| "PRD 里有用户旅程章节" | 文件名不含 `journey`，跳过扫描 | ❌ 遗漏 |
| "AC 格式是标准 Given/When/Then" | 正则不支持连字符 | ❌ 遗漏 |
| "Tech Spec 有技术选型表格" | 表头词汇不在白名单 | ❌ 遗漏 |

### 5.3 改进方向（Roadmap）

#### 短期（P0，当前迭代）
1. 修复 AC 正则 Bug（加连字符支持）
2. 解除 `user_journey_map` 的文件名强耦合（增加内容启发式）
3. 放宽 `tech_stack` 表头匹配

#### 中期（P1，下一迭代）
4. **引入轻量级语义标记**: 不要求完整 NLP，但至少支持显式 YAML front matter 标注
   ```markdown
   ---
   frz_dimension: product_design
   frz_fields: [user_journey_map, acceptance_criteria]
   ---
   ```
5. **增加 fallback 宽松模式**: 当严格模式提取为空时，尝试宽松启发式
   - AC: 扫描所有 `**` 包裹的 `Given ... When ... Then ...` 段落
   - Journey: 扫描所有 `##` 级别的流程描述章节
   - Tech Stack: 扫描所有含技术关键词的表格

#### 长期（P2）
6. **引入 LLM 辅助提取**: 对 raw Markdown 内容调用轻量级模型（Haiku 级别），将非结构化文本转换为结构化 JSON，作为规则引擎的 fallback
   ```python
   if not extracted_fields:
       extracted_fields = llm_extract_structured(raw, target_schema)
   ```

---

## 6. 验证与测试建议

修复完成后，请使用以下测试用例验证：

### 测试用例 1: AC 连字符支持
```markdown
- **AC-M12-001.1**: Given X, When Y, Then Z
- **AC-API-042.3**: Given A, When B, Then C
```
**预期**: 提取 2 条 AC

### 测试用例 2: PRD 文件名触发旅程提取
```markdown
# PRD-M99-Test-Module.md
## 用户旅程
### 步骤 1: 登录
用户打开 App，输入手机号...
```
**预期**: 提取 `user_journey_map` 含 "登录" 步骤

### 测试用例 3: 非标准表头 Tech Stack
```markdown
## 技术选型
| 模块 | 技术方案 | 版本 |
|------|---------|------|
| 前端 | React | 18 |
```
**预期**: 提取 `tech_stack` 含 React 条目

### 测试用例 4: 端到端集成测试
使用 `ai-marathon-root-v2/docs/mvp-lite` 作为输入运行完整 FRZ 流程：
```bash
FRZ_CLI_LIB_PATH="/Users/zengle/git/LEE-Lite" \
python src/frz_ingest.py \
  --input /tmp/m12-frz-input \
  --output /tmp/test-output \
  --project-type generic
```
**预期**: completeness 检查通过（或仅报 warning，不 BLOCK）

---

## 7. 相关文件索引

- `cli/lib/v2/parser.py:171-184` — AC 提取正则
- `cli/lib/v2/parser.py:186-271` — `user_journey_map` 提取逻辑
- `cli/lib/v2/parser.py:360-403` — `tech_stack` 提取逻辑
- `cli/lib/v2/parser.py:317-344` — `target_users` 提取逻辑（参考实现，基于 heading 而非文件名）
- `cli/lib/v2/completeness.py:364-415` — Q1-Q4 质量门检查（被上述 Bug 触发 BLOCK）
