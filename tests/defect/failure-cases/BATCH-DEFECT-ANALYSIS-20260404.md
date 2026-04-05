# failure-cases 批量缺陷分析报告（2026-04-04）

## 1. 范围与结论

本次分析覆盖 `tests/defect/failure-cases` 下 6 个 failure case：

- `FC-20260402-074354-ADR036-C`
- `FC-20260402-115238-SRC-002-`
- `FC-20260402-171755-SRC001-P`
- `FC-20260403-053640-SRC002-F`
- `FC-20260403-081005-PROTO-SR`
- `FC-20260403-142839-EPIC-SRC`

先给结论：

1. 这批 defect 的主因不是单点实现 bug，而是 **语义锚点不稳、上游 freeze-ready 定义不足、运行前校验不完整、生成产物缺少忠实度约束**。
2. 6 个 case 中，`diagnosis_stub.root_cause_primary` 有 4 个直接指向 `definition_weakness`，说明主要问题在 **定义层/契约层**，不是单纯执行层。
3. `human_final_review` 才发现的 case 有 3 个，`impl_spec_testing` 深测后才发现的 case 有 2 个，说明 **前置 detector 不足，问题逃逸率高**。
4. 比 defect 本身更严重的一个元问题是：这批 failure package 的 **可复盘性很差**。当前仓库状态下，大量 `source_refs`、`evidence_refs`、`allowed_edit_scope` 已经失效，导致后续修复和复核成本被显著放大。

## 2. 批量画像

### 2.1 严重度与发现阶段

- 严重度：`blocker` 2 个，`high` 4 个。
- 发现阶段：
  - `human_final_review`: 3
  - `impl_spec_testing`: 2
  - `e2e_test_execution`: 1

### 2.2 根因标签分布

- `definition_weakness`: 4
- `detection_weakness`: 1
- `repair_fault`: 1

### 2.3 错误类型分布

- `detection_miss`: 3
- `structure_error`: 2
- `semantic_drift`: 1

这组分布很一致地指向一个判断：**当前体系更像是在“事后识别失败”，而不是在“前置阻断错误输入与错误投影”。**

## 3. 关键发现

### 3.1 语义主轴漂移：overlay 被误提升为 primary slice

涉及 case：

- `FC-20260402-074354-ADR036-C`
- `FC-20260403-142839-EPIC-SRC`

共性表现：

- UI 被当成默认 formal layer，而不是按 scope 判定 `not_applicable`。
- governance / handoff / gate / formal / IO 等 cross-cutting overlay，被误提升成 EPIC primary slices。
- 下游 FEAT / IMPL 会因此沿错误主轴继续展开，造成整条链路偏航。

本质问题：

- `semantic_lock.domain_type`、`primary_object`、`inheritance_rule` 的优先级不够硬。
- “主对象”和“继承约束”没有被明确拆成两个不同层级的判断。
- `not_applicable` 缺少稳定语义，在无 UI scope 时仍被系统按“缺失但应存在”处理。

这类问题危险在于：**一旦进入 release index 或 EPIC/FEAT 主链，后续所有下游都会继承错误结构。**

### 3.2 执行契约脆弱：schema 严苛但不健壮，错误一次只暴露一个

涉及 case：

- `FC-20260402-115238-SRC-002-`

该 case 不是单一故障，而是执行链韧性不足的集中暴露，至少包含：

- `api_version` 格式过窄
- `test_set_ref` / `test_set_refs` 命名不兼容
- 相对路径/绝对路径解析不稳定
- worktree / workspace root 语义不清
- Playwright / npm 依赖无 preflight
- simulation mode 与 coverage 产物契约不一致
- 错误串行暴露，导致 5+ 次 retry

这说明当前执行器更像“碰撞式排错”，不是“批量前置校验 + 一次性给出完整修复面”。

### 3.3 深测没有错，错的是上游 SSOT 还没准备好

涉及 case：

- `FC-20260402-171755-SRC001-P`
- `FC-20260403-053640-SRC002-F`

两个 suite 的结论高度一致：

- recovery 行为缺失
- state closure / invariant 不完整
- TESTSET 无法覆盖声明完成态
- UI authority / TESTSET authority 缺失或未 freeze-ready
- API 输出 / precondition 可观测性不足

这类 case 不能简单归因为 `qa.impl-spec-test` 太严格。更合理的判断是：

- **impl-spec-test 已经到了能发现“实现前文档不够可实施”的阶段**；
- 但流水线入口仍然允许这些不完整的 IMPL/UI/TESTSET/API 包进入深测，说明缺少 **readiness gate**。

换句话说，现在是把“本该在 freeze 前拦住的问题”，推迟到 “deep implementation-readiness review” 才暴露。

### 3.4 生成器已经不是 skeleton 问题，而是“看起来像对，实际上误导 review”

涉及 case：

- `FC-20260403-081005-PROTO-SR`

这里最关键的不是原型难看，而是原型 **失真**：

- frozen enum 漂移
- 状态切换只换标签，不换核心页面表意
- technical payload 被误展示成 required user-facing scope

这意味着 `dev.feat-to-proto` 当前风险不是“缺少信息”，而是“伪准确”。  
对于 freeze review 来说，伪准确比粗糙 skeleton 更危险，因为它会让 reviewer 误判边界已经稳定。

### 3.5 failure-capture 包自身存在完整性问题，已影响修复闭环

这是本轮最值得立即处理的元问题。

我对所有 case 的外部引用做了存在性检查，结果如下：

- `allowed_edit_scope`: 27 项中有 17 项当前不存在
- `evidence_refs`: 33 项中有 30 项当前不存在
- `source_refs`: 42 项中有 33 项当前不存在

分 case 看：

| Case | allowed_edit_scope 缺失 | evidence_refs 缺失 | source_refs 缺失 |
| --- | ---: | ---: | ---: |
| `FC-20260402-074354-ADR036-C` | 0 / 7 | 0 / 2 | 0 / 6 |
| `FC-20260402-115238-SRC-002-` | 4 / 4 | 1 / 2 | 3 / 5 |
| `FC-20260402-171755-SRC001-P` | 3 / 4 | 11 / 11 | 7 / 7 |
| `FC-20260403-053640-SRC002-F` | 3 / 4 | 7 / 7 | 8 / 8 |
| `FC-20260403-081005-PROTO-SR` | 5 / 6 | 9 / 9 | 7 / 8 |
| `FC-20260403-142839-EPIC-SRC` | 2 / 2 | 2 / 2 | 8 / 8 |

这意味着当前 failure-capture 体系存在三个结构性问题：

1. **案例不自包含**：大量证据只引用外部产物，没有快照进 case 目录。
2. **修复范围不可靠**：`repair_context` 经常指向不存在的目录、旧路径或函数限定字符串。
3. **复盘不可重现**：一旦临时 worktree 或 artifacts 清理掉，case 只剩摘要，失去修复依据。

如果不先修这个问题，后续 defect 分析会持续变成“看摘要猜现场”。

## 4. 分 case 诊断

| Failure ID | 主问题 | 根因判断 | 修复优先级 |
| --- | --- | --- | --- |
| `FC-20260402-074354-ADR036-C` | UI applicability 判定错误，scope 被默认扩张 | semantic applicability 规则不硬，UI 缺少 `not_applicable` 一等语义 | P0 |
| `FC-20260402-115238-SRC-002-` | 执行契约与运行环境韧性不足 | schema、path、workspace、dependency preflight 均不完整 | P0 |
| `FC-20260402-171755-SRC001-P` | IMPL 套件整体未达到 deep review readiness | 上游 SSOT completeness 不足，readiness gate 缺失 | P0 |
| `FC-20260403-053640-SRC002-F` | SRC002 套件仍旧整体不 freeze-ready | IMPL/UI/TESTSET/API 四类 authority 未同步到深测要求 | P0 |
| `FC-20260403-081005-PROTO-SR` | prototype 作为 review proxy 失真 | generator 没有绑定 frozen enums / state delta / field boundary | P1 |
| `FC-20260403-142839-EPIC-SRC` | 工程骨架型 SRC 被切成治理平台型 EPIC | primary object 与 overlay 识别层级混淆 | P0 |

## 5. 改进方案

## 5.1 P0：先修 failure-capture 的可复盘性

这是所有后续修复的前提，建议先做。

### 目标

让每个 failure case 在脱离原始 worktree / artifacts 目录后，仍可独立复盘、独立修复、独立关闭。

### 建议动作

1. **强制 case 自包含**
   - 在 capture 时把最小必要证据复制到 case 目录内，而不是只留外链。
   - 至少落地：
     - 原始 request snapshot
     - 失败时的关键 response / summary snapshot
     - 被指认的 artifact 片段
     - repair 前后的定位片段

2. **校验 repair_context**
   - capture 生成前检查 `allowed_edit_scope` 是否存在。
   - 对函数级 edit scope 使用结构化字段，不要把 `path:function_name` 当普通路径字符串。
   - 对目录型 scope，要求给出实际存在的根目录或文件 glob。

3. **给每个 case 增加 reproducibility 指标**
   - `source_refs_resolved_ratio`
   - `evidence_refs_resolved_ratio`
   - `allowed_edit_scope_resolved_ratio`
   - 未达阈值时 case 状态应为 `captured_but_not_reproducible`，不能直接进入 repair。

4. **把临时 worktree 证据快照化**
   - 所有指向 `Temp`、`vibe-kanban worktrees`、临时 artifacts 的引用，capture 时必须同步入仓或同步进 case 包。

## 5.2 P0：建立前置 readiness gate，减少深测阶段才暴露的“上游未完成”

主要针对：

- `FC-20260402-171755-SRC001-P`
- `FC-20260403-053640-SRC002-F`

### 目标

不要让明显未 freeze-ready 的 IMPL/UI/TESTSET/API 进入 `impl_spec_testing`。

### 建议动作

1. 在 `qa.impl-spec-test` 前增加 `readiness-precheck`
   - recovery path 是否存在
   - completion / exit / rollback state 是否闭合
   - TESTSET 是否覆盖声明完成态
   - UI authority / TESTSET authority / API authority 是否齐备
   - implementation unit mapping snapshot 是否存在

2. 明确两类失败
   - `runtime_defect`: skill 本身执行或检测异常
   - `upstream_definition_not_ready`: 上游文档未达进入条件

3. 对第二类失败直接阻断下游深测
   - 不再继续跑完整 deep suite
   - 直接生成 readiness gap report，降低噪音

## 5.3 P0：加硬 semantic anchor，防止 scope 漂移

主要针对：

- `FC-20260402-074354-ADR036-C`
- `FC-20260403-142839-EPIC-SRC`

### 目标

把“主对象”和“继承约束”分层，禁止 overlay 反客为主。

### 建议动作

1. **semantic lock precedence 固化**
   - `domain_type`
   - `primary_object`
   - `one_sentence_truth`
   - `inheritance_rule`

   这四项应高于标题关键词、高频治理词、历史惯例推断。

2. **引入 layer applicability matrix**
   - 对 UI / API / TESTSET / PROTO / FORMAL 等层明确三态：
     - `required`
     - `optional`
     - `not_applicable`

3. **禁止默认下游腿自动展开**
   - 若 FEAT 没有 UI scope，链路不能默认补一条 feat-to-ui。
   - 若工程基线类 SRC 的 primary object 是 codebase baseline，EPIC 轴必须围绕 repo/layout、shell、env、migration、health/readiness、module boundary 展开。

4. **为 semantic drift 增加专门 detector**
   - 检查 EPIC/FEAT slice 名称是否与 `primary_object` 同域
   - 检查 overlay 词汇是否被提升为 capability axis
   - 检查 `not_applicable` 是否被误解释成 `missing_authority`

## 5.4 P1：修正执行契约与运行前校验

主要针对：

- `FC-20260402-115238-SRC-002-`

### 目标

把 5+ 次 retry 压缩成 1 次失败 + 1 次修复。

### 建议动作

1. **输入契约兼容与规范化**
   - `api_version` 同时接受 `v1` 与 `1.0.0`，内部统一规范化。
   - `test_set_ref` / `test_set_refs` 做兼容读取，保留 deprecation warning。

2. **路径与 workspace 规范化**
   - 所有输入路径先解析成绝对路径。
   - 明确 repo root、workspace root、worktree root 的优先级和解析规则。
   - 错误信息中输出实际搜索路径。

3. **依赖 preflight**
   - npm / package.json / script / Playwright 安装状态全部在执行前一次性检查。

4. **批量报错，不串行报错**
   - 一次返回完整 validation error list。
   - 不要让用户修一个再撞下一个。

5. **simulation mode 契约补齐**
   - coverage 相关产物要么显式标记 `simulated=true`，要么在 contract 中声明 optional。

6. **同步修 repair_context 生成逻辑**
   - 当前 case 的 `allowed_edit_scope` 指向不存在路径，说明 capture 端未校验 repo 实际布局。

## 5.5 P1：提升 prototype 作为 review proxy 的忠实度

主要针对：

- `FC-20260403-081005-PROTO-SR`

### 目标

让 prototype 成为“高保真 review 代理”，而不是“看起来完整的误导界面”。

### 建议动作

1. **enum 绑定到 freeze 源**
   - 页面 mock data 只能从 frozen enum 域取值，禁止生成器自造近似值。

2. **增加 state delta threshold**
   - 如果状态切换没有导致核心 surface、主 CTA、关键信息区或错误/恢复文案发生可见变化，则视为无效状态分支。

3. **严格区分 field boundary**
   - `required user-visible fields`
   - `ui-visible optional fields`
   - `technical payload fields`

   三者必须明确分栏，且 technical payload 不得自动渲染成 required 输入。

4. **新增 generator regression cases**
   - 覆盖 enum 漂移
   - 覆盖 panel/entry/status 的状态差异
   - 覆盖 technical payload 泄漏

## 5.6 P2：建立缺陷回归与质量度量

建议把这 6 个 case 升级为 golden regression batch。

### 需要持续跟踪的指标

- human final review escape rate
- missing evidence ref rate
- missing allowed edit scope rate
- deep test blocked by upstream readiness rate
- semantic drift detection coverage
- average retry count before executable fix

### 回归策略

1. 每个 defect 至少保留一个最小可执行回归输入。
2. 每次修改相关 skill 后自动跑：
   - semantic classification regression
   - readiness precheck regression
   - failure-capture package integrity regression
   - prototype fidelity regression

## 6. 建议执行顺序

### 第一阶段：先修元问题（1-2 天）

1. 修 `governance.failure-capture` 的 package 完整性
2. 为 case 增加 reproducibility 校验
3. 修 `repair_context` 失效路径生成

### 第二阶段：堵语义漂移和 readiness 漏口（2-4 天）

1. 修 `raw-to-src` / `src-to-epic` 的 semantic anchor 优先级
2. 增加 UI/API/TESTSET applicability matrix
3. 在 `qa.impl-spec-test` 前加 readiness-precheck

### 第三阶段：修执行器与生成器（2-4 天）

1. 修 `ll-test-exec-web-e2e` 契约与 preflight
2. 修 `dev.feat-to-proto` 的 enum / state / field boundary
3. 把本批 6 个 defect 纳入 golden regression

## 7. 最终判断

这批 defect 给出的信号很明确：

- 不是某一个 skill 写坏了；
- 是整个链路在 **“定义是否足够硬、产物是否足够忠实、失败包是否足够可复盘”** 三个层面同时偏弱。

如果只按 case 逐个补洞，缺陷会继续重复出现。  
更有效的路线是：

1. 先把 failure-capture 做成可靠的修复入口；
2. 再把 semantic anchor 和 readiness gate 前移；
3. 最后用 regression 把这些 defect 固化成不会二次回归的测试资产。
