# Phase 8: FRZ→SRC 语义抽取链 - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

交付 `ll-frz-manage` 抽取模式 + 全 SSOT 链（SRC→EPIC→FEAT→TECH/UI/TEST/IMPL）从 FRZ 的分层语义抽取能力。包含漂移检测、投影不变性守卫、锚点注册。抽取产物走现有 gate 流程审核。不修改现有非抽取模式的 run 命令行为。

</domain>

<decisions>
## Implementation Decisions

### 抽取策略
- **D-01:** FRZ → SRC 采用规则模板投影（非 LLM、非语义匹配）。基于 FRZ MSC 5 维到目标字段的预定义映射规则，确定性输出。与 Phase 7 `frz_schema.py` + `MSCValidator` 的确定性模式一致。ADR-050 out of scope 明确排除 LLM 语义抽取。
- **D-02:** 抽取输出沿用现有 SSOT 包格式（JSON + YAML + metadata）。不新建专用格式。FRZ 溯源信息通过 metadata 字段追加，下游消费者无需修改。

### 投影不变性守卫
- **D-03:** 守卫采用抽取后验证（不预检）。抽取完成后比对输出与 FRZ `derived_allowed` 范围，超出则拒绝。与现有 `validate_output_package` 模式一致。
- **D-04:** `derived_allowed` 采用字段白名单方式。FRZ freeze.yaml 中的 `derived_allowed` 是字段名列表（如 `['tech_details', 'ui_layout']`），只有这些字段可被派生填充。检查时验证输出中没有新增非白名单字段。

### 漂移检测
- **D-05:** 漂移检测粒度为锚点级。以锚点 ID（JRN-xxx, ENT-xxx, SM-xxx, FC-xxx）为单位，检查每个锚点在抽取后的产物中是否仍然存在且语义一致。复用 `anchor_registry.py` 基础设施。不用字段级 diff（噪声大）或 MSC 维度级（太粗）。
- **D-06:** 漂移拦截策略为拦截 + 报告。返回 block verdict + 漂移详细报告，不写入下游。与现有 gate verdict 模式一致（approve/revise/reject/block）。不自动修正（需要人类判断是抽取错误还是 FRZ 本身问题）。

### 级联抽取
- **D-07:** 在现有技能脚本中各新增 `extract` 子命令。`src_to_epic.py` 加 `extract` 子命令接受 `--frz` 参数，`epic_to_feat.py` 同理。保持现有 `run` / `executor-run` 命令不变。
- **D-08:** 提供一键全链 + 可选分步两种模式。
  - 分步：`ll frz-manage extract --frz FRZ-xxx` → `ll src-to-epic extract --frz FRZ-xxx` → `ll epic-to-feat extract --frz FRZ-xxx` → 后续技能同理
  - 全链：`ll frz-manage extract --cascade --frz FRZ-xxx` 一键跑通完整 SSOT 链（FRZ→SRC→EPIC→FEAT→TECH/UI/TEST/IMPL）
  - 全链模式中，**每步抽取后走 gate 审核**再继续下一层
  - **范围覆盖整个 SSOT 链**：不仅 SRC→EPIC→FEAT，后续的 TECH、UI、TEST、IMPL 同样从 FRZ 对应文档做语义抽取
  - 如果 FRZ 中对应某层的内容信息缺失，**必须给出提示**（warning 级别，不阻断抽取）

### 锚点注册
- **D-09:** 锚点在抽取时立即注册（不等 gate 通过）。从 FRZ 抽取到产物时立即为每个 FRZ 锚点注册到 `AnchorRegistry`，`projection_path` 随层级变化（SRC/EPIC/FEAT/TECH/UI/TEST/IMPL）。实时可追溯。
- **D-10:** 锚点 ID 从 FRZ 继承。FRZ 中的锚点 ID（JRN-001, ENT-001 等）直接复用到所有下游产物。同一 `anchor_id` 在 `AnchorRegistry` 中有多条记录，通过 `projection_path` 区分层级。

### 测试策略
- **D-11:** 单元测试 + 集成测试两者结合。drift_detector、projection_guard 等纯逻辑函数用 fixture-based 单元测试。完整 FRZ→SSOT 链路用集成测试验证端到端。
- **D-12:** 漂移检测器测试覆盖 5 类核心场景：锚点缺失、锚点语义篡改、新增非 derived_allowed 字段、constraints 违反、known_unknowns 过期。每类至少 1 个测试。

### Gate 集成
- **D-13:** 复用现有 gate 逻辑。抽取产物走与现有 SRC/EPIC/FEAT 相同的 gate 流程（submit-handoff → evaluate → decide → materialize → dispatch）。不新增 gate 类型，只在 gate 校验中加 FRZ 锚点存在性检查。

### 交付优先级
- **D-14:** 按 ROADMAP 顺序：08-01 drift_detector → 08-02 frz-manage extract → 08-03 src-to-epic extract → 08-04 epic-to-feat extract。这是正确的依赖链顺序（drift_detector 被 extract 调用，extract 定义接口，级联修改依赖前两者）。

### Claude's Discretion
- 抽取规则的精确映射表定义（FRZ MSC 字段 → SRC/EPIC/FEAT/TECH/UI/TEST/IMPL 字段的具体映射关系）
- 全链 --cascade 的具体实现方式（顺序循环 vs 并行 gate 评估）
- 缺失内容提示的详细格式和严重级别划分

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### SSOT 语义治理总纲
- `ssot/adr/ADR-050-SSOT语义治理总纲.md` — 核心架构原则、FRZ 定义、抽取原则、投影不变性、变更分级
- `ssot/adr/ADR-051-TaskPack顺序执行循环模式.md` — Task Pack 结构、执行规则、与 ADR-018 集成

### FRZ 冻结层
- `cli/lib/frz_schema.py` — FRZPackage dataclass、MSCValidator、5 维校验 schema
- `cli/lib/frz_registry.py` — FRZ 注册表操作（get_frz, list_frz, register_frz）
- `skills/ll-frz-manage/scripts/frz_manage_runtime.py` — 现有 validate/freeze/list 实现，extract stub

### 锚点注册
- `cli/lib/anchor_registry.py` — AnchorRegistry 类、register/resolve/list_by_frz API、ANCHOR_ID_PATTERN

### 现有 SSOT 技能
- `skills/ll-product-src-to-epic/scripts/src_to_epic.py` — CLI 入口、子命令架构、现有 run/executor-run 实现
- `skills/ll-product-src-to-epic/scripts/src_to_epic_runtime.py` — 工作流核心逻辑
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat.py` — CLI 入口、子命令架构
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py` — 工作流核心逻辑

### 需求定义
- `.planning/REQUIREMENTS.md` — EXTR-01~05 需求定义、调用方式、workflow 位置

### ROADMAP
- `.planning/ROADMAP.md` — Phase 8 goal、4 个 plan、5 条 success criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli/lib/anchor_registry.py` — 已交付的锚点注册表，支持 register/resolve/list_by_frz/list_all，直接复用
- `cli/lib/frz_schema.py` — FRZPackage + MSCValidator，抽取时需读取 FRZ 的 MSC 5 维数据
- `cli/lib/frz_registry.py` — FRZ 注册表查询，extract 命令需通过它加载 FRZ 数据
- `cli/lib/errors.py` — CommandError + ensure() 模式，所有新代码统一使用
- `cli/lib/fs.py` — 文件操作工具（ensure_parent, load_json, canonical_path），统一使用
- `frz_manage_runtime.py` 现有架构 — validate/freeze/list 的 CLI 模式可参考实现 extract

### Established Patterns
- 技能脚本子命令架构：build_parser() → add_subparsers() → command_map 分发 → main()
- 错误处理：CommandError with status_code + ensure() 预条件检查
- 类型标注：from __future__ import annotations，所有函数签名带类型注解
- 不可变数据：@dataclass(frozen=True) 用于 DTO
- 测试风格：Phase 7 使用 fixture-based 单元测试，70 测试覆盖 validate/freeze/list
- Gate 模式：submit_handoff → evaluate → decide → materialize → dispatch

### Integration Points
- `frz_manage_runtime.py` 的 extract_frz() 函数（L349-362）当前是 stub，需要实现
- extract 子命令的 argparse 定义已在 build_parser() 中（L437-451），只需补实现
- src_to_epic.py 和 epic_to_feat.py 需要新增 extract 子命令
- 全链 --cascade 需要调用 gate skill（现有 `cli/commands/gate/command.py`）
- 漂移检测需要比对 FRZ 原始锚点和抽取产物中的锚点

</code_context>

<specifics>
## Specific Ideas

- "全链 --cascade 不是简单的脚本串联，而是每步抽取 → gate 审核 → 通过后下一步的完整流程"
- "SSOT 链包括 SRC→EPIC→FEAT→TECH/UI/TEST/IMPL，全部从 FRZ 抽取，不只是前三层"
- "FRZ 中如果缺少某层对应的内容信息，给 warning 提示但不阻断——让操作者知道哪些层的信息不完整"
- "保持与 Phase 7 相同的代码风格、错误处理模式、测试覆盖率"

</specifics>

<deferred>
## Deferred Ideas

- 复杂 DAG 调度器 + 并发执行 — ADR-051 明确不采纳，顺序 loop 足够
- 失败自动跳过 — ADR-051 明确失败必须暂停等待人工
- LLM 辅助语义抽取 — ADR-050 out of scope 明确排除
- FRZ 自动生成工具 — ADR-050 明确 FRZ 必须由人工讨论冻结

</deferred>

---

*Phase: 08-frz-src*
*Context gathered: 2026-04-18*
