## ADDED Requirements

### Skill Interface

impl-verify 是一个验收 Skill，接收冻结后的 FRZ Package 和 GSD 交付物，执行 5 步验证流程（step_1~step_5）。

- **Input**: `frz_package`（状态为 `frozen` 或 `revised` 的 FRZ Package）+ `gsd_delivery`（包含 git diff、commit 历史、工程资料目录）
- **Steps**: step_1 任务完成度检查 → step_2 工程资料检查 → step_3 范围合规检查 → step_4 代码变更溯源验证 → step_5 综合判定引擎
- **Output**: `VerificationReport`，包含 `final_verdict`（`pass`/`fail`/`conditional_pass`）及各子检查详细结果

> **GSD 交付物结构**: `gsd_delivery` 包含 `git_diff`（变更文件列表及 diff 内容）、`commits`（commit 消息列表）、`engineering_docs`（工程资料目录，含变更说明、决策记录、依赖变更清单、已知问题清单、回滚方案）。

> **Task 来源**: Task 列表来源于 IMPL YAML 的 `tasks` 字段，每项包含 `task_id`、`description`。

> **Scope 来源**: `allowed_scope` 和 `forbidden_scope` 均来源于 IMPL YAML。`allowed_scope` 包含 `directories`（允许修改的目录列表）和 `files`（允许修改的文件列表）。`forbidden_scope` 包含 `directories` 和 `files`（禁止修改的目录和文件列表）。

### Requirement: 任务完成度检查（step_1）
impl-verify SHALL 自动检查 GSD 交付物中所有 task 是否完成且仅修改了允许范围内的文件。

#### Scenario: 任务和范围均通过
- **WHEN** impl-verify 对 IMPL 的 `allowed_scope` 内且所有 task 已完成的 GSD 交付执行任务完成度检查（step_1）
- **THEN** 输出 `task_completion=pass`，`scope_compliance=pass`

#### Scenario: 任务未完成检测
- **WHEN** impl-verify 对某个 task 未提交的 GSD 交付执行任务完成度检查
- **THEN** 输出 `task_completion=fail`，`incomplete_tasks` 包含未完成的 task 引用

#### Scenario: 超出允许范围检测
- **WHEN** impl-verify 对 git diff 包含 `allowed_scope` 外文件修改的 GSD 交付执行文件范围检查
- **THEN** 输出 `scope_compliance=fail`，`out_of_scope_files` 包含越界文件

#### Scenario: 禁止范围违规检测
- **WHEN** impl-verify 对 git diff 包含 `forbidden_scope` 中文件的 GSD 交付执行文件范围检查
- **THEN** 输出 `scope_compliance=fail`，`forbidden_scope_violations` 包含被修改的禁止文件

> **注意**: 此处的 `scope_compliance` 指文件范围合规（file scope），与 step_3 功能范围合规（feature scope）区分。

#### Scenario: 任务完成度输出结构
- **WHEN** 检查任务完成度检查结果
- **THEN** 包含 `task_completion`、`scope_compliance`、`incomplete_tasks`、`out_of_scope_files`、`forbidden_scope_violations`

### Requirement: 工程资料检查（step_2）
impl-verify SHALL 自动检查 GSD 交付的工程资料是否齐全，验证变更说明、决策记录、依赖变更、已知问题、回滚方案。

#### Scenario: 工程资料完整
- **WHEN** impl-verify 对包含完整工程资料的 GSD 交付执行工程资料检查（step_2）
- **THEN** 输出 `engineering_docs=pass`，`missing_docs` 为空列表

#### Scenario: 缺少回滚方案
- **WHEN** impl-verify 对缺少回滚方案文档的 GSD 交付执行工程资料检查
- **THEN** 输出 `engineering_docs=fail`，`missing_docs` 包含 `rollback_strategy`

#### Scenario: 关键决策记录缺失
- **WHEN** impl-verify 对变更说明存在但关键决策记录缺失的 GSD 交付执行工程资料检查
- **THEN** 输出 `engineering_docs=partial`，`missing_docs` 包含 `key_decisions`

> **判定规则**: 必需文档（回滚方案）完全缺失 → `fail`；文档存在但内容不完整（如关键决策记录缺失但变更说明存在）→ `partial`。

#### Scenario: 工程资料质量警告
- **WHEN** impl-verify 对工程资料存在但质量不达标（如变更说明过于简略、决策记录缺少依据）的 GSD 交付执行工程资料检查
- **THEN** 输出 `doc_quality_warnings` 包含具体警告项（如 `change_description_too_brief`、`decision_missing_rationale`）

#### Scenario: 工程资料输出结构
- **WHEN** 检查工程资料检查结果
- **THEN** 包含 `engineering_docs`（`pass`/`fail`/`partial`）、`missing_docs`（每项含 `doc_type` 和 `severity`）、`doc_quality_warnings`

#### Scenario: 已知问题清单验证
- **WHEN** GSD 交付包含已知问题清单
- **THEN** impl-verify 验证每个已知问题包含 `description`、`impact`、`workaround`、`planned_fix_version`

### Requirement: 范围合规检查（step_3）
impl-verify SHALL 检测 GSD 交付中是否存在范围违规和未授权功能。

> **注意**: 此处的 `scope_compliance` 指功能范围合规（feature scope），与 step_1 文件范围合规区分。

#### Scenario: 范围完全合规
- **WHEN** impl-verify 对代码变更完全在 FEAT 定义范围内的 GSD 交付执行范围合规检查（step_3）
- **THEN** 输出 `scope_compliance=pass`，`unauthorized_features` 为空列表，`semantic_changes` 为空列表

#### Scenario: 未授权功能检测
- **WHEN** impl-verify 检测到代码引入了 FEAT 未定义的新的 API 端点
- **THEN** 输出 `scope_compliance=fail`，`unauthorized_features` 包含未授权 API 端点的描述和位置

#### Scenario: 语义变更半自动检测
- **WHEN** impl-verify 检测到代码修改了已有业务规则的行为语义
- **THEN** 输出 `semantic_changes` 包含变更项，标记为 `requires_review`，等待人工确认

#### Scenario: 未授权功能输出结构
- **WHEN** 范围合规检查发现未授权功能
- **THEN** 每个未授权功能包含 `location`、`description`、`suggested_action`（取值为 `remove` 或 `escalate_to_frz_revise`）

#### Scenario: 语义变更输出结构
- **WHEN** 范围合规检查发现语义变更
- **THEN** 每个语义变更包含 `original_semantic`、`changed_semantic`、`change_type`（取值为 `strengthen`、`weaken` 或 `alter`）、`confidence`（取值为 `auto_detected` 或 `manual_review_required`）

### Requirement: 代码变更溯源验证（step_4）
impl-verify SHALL 验证代码变更可以追溯回 SSOT 链的对应需求项，支持 full/partial/no_trace/exempt 四级标记。

#### Scenario: 完整溯源通过
- **WHEN** impl-verify 对 git diff 中每处变更都能在 IMPL 的 `allowed_scope` 和 FEAT 中找到对应需求的 GSD 交付执行溯源验证（step_4）
- **THEN** 所有变更块标记为 `trace_level=full`，输出 `traceability=pass`

#### Scenario: 部分溯源
- **WHEN** impl-verify 对某段代码变更能在 FEAT 中找到部分关联但无法精确对应到具体 AC 的 GSD 交付执行溯源验证
- **THEN** 该变更块标记为 `trace_level=partial`，输出 `traceability=conditional_pass`，`partial_traces` 包含变更位置和关联的模糊需求项

#### Scenario: 无溯源
- **WHEN** impl-verify 对某段代码变更在 SSOT 链中无直接对应需求的 GSD 交付执行溯源验证
- **THEN** 该变更块标记为 `trace_level=no_trace`，`no_trace_items` 包含变更位置

#### Scenario: 豁免规则
- **WHEN** 标记为 `trace_level=no_trace` 的变更块属于 IMPL 的 `allowed_scope` 中的基础设施/工具类文件且符合预定义豁免条件
- **THEN** 标记为 `trace_level=exempt`，不阻塞验收

> **豁免条件**: 包括 README 更新、CI 配置调整、依赖版本升级（无业务逻辑变更）、代码格式化等纯工程变更。

#### Scenario: 溯源验证输出结构
- **WHEN** 检查溯源验证结果
- **THEN** 包含 `traceability`、`full_traces`、`partial_traces`、`no_trace_items`、`exempt_items`

### Requirement: 综合判定引擎（step_5）
impl-verify SHALL 基于各子检查的结果输出综合判定（pass/fail/conditional_pass），支持可配置的阈值。

#### Scenario: 全部通过
- **WHEN** 所有子检查结果均为 pass
- **THEN** 输出 `final_verdict=pass`，`verdict_reason="All checks passed"`

#### Scenario: 阻塞性失败
- **WHEN** 任务完成度=fail，其他检查为 pass
- **THEN** 输出 `final_verdict=fail`，`blocking_issues` 包含任务完成度失败的具体原因

#### Scenario: 条件通过（允许 partial trace）
- **WHEN** 溯源验证=conditional_pass（存在 partial_trace 但无 no_trace），其他检查为 pass，且配置允许 partial trace
- **THEN** 输出 `final_verdict=conditional_pass`，`conditions` 包含需要补充的文档项

#### Scenario: 条件通过但不允许 partial trace
- **WHEN** 溯源验证=conditional_pass，但配置不允许 partial trace
- **THEN** 输出 `final_verdict=fail`

#### Scenario: 综合判定输出结构
- **WHEN** 检查综合判定输出
- **THEN** 包含 `final_verdict`、`verdict_reason`、`blocking_issues`、`warnings`、`conditions`

#### Scenario: 阈值配置
- **WHEN** 检查验收阈值配置
- **THEN** 包含 `required_checks`（必须 pass 的检查列表）、`conditional_pass_threshold`（对象，包含 `allow_partial_trace`（boolean）、`allow_partial_engineering_docs`（boolean））、`fail_on_warning`（boolean）

### Requirement: 双线路收敛
线路 1（v1 test_execution）和线路 2（impl-verify）SHALL 并行验收后通过 AND gate 收敛，确认发布就绪。

#### Scenario: 双线路均通过
- **WHEN** 线路 1 返回 `verdict=pass`，线路 2 返回 `verdict=pass`
- **THEN** AND gate 输出 `convergence=pass`，`release_ready=true`

#### Scenario: 线路 2 失败
- **WHEN** 线路 1 返回 `verdict=pass`，线路 2 返回 `verdict=fail`
- **THEN** AND gate 输出 `convergence=fail`，`release_ready=false`，`blocking_line="line_2"`

#### Scenario: 线路 1 失败
- **WHEN** 线路 1 返回 `verdict=fail`，线路 2 返回 `verdict=pass`
- **THEN** AND gate 输出 `convergence=fail`，`release_ready=false`，`blocking_line="line_1"`

#### Scenario: 线路 2 条件通过
- **WHEN** 线路 1 返回 `verdict=pass`，线路 2 返回 `verdict=conditional_pass`
- **THEN** AND gate 输出 `convergence=conditional_pass`，`release_ready=false`

#### Scenario: 收敛输出结构
- **WHEN** 检查双线路收敛结果
- **THEN** 包含 `convergence`、`release_ready`、`blocking_line`、`line_1_verdict`、`line_2_verdict`、`line_1_issues`、`line_2_issues`、`conditions`

#### Scenario: 超时处理
- **WHEN** 线路 1 或线路 2 超时未返回结果且超过 `convergence_timeout`
- **THEN** 标记对应线路为 `timeout`，`convergence=fail`

### Requirement: 问题回流与分类
impl-verify 或双线路收敛发现的失败 SHALL 自动分流到 Bug Fix / Experience Patch / FRZ Revise 三类处理通道。

#### Scenario: Bug Fix 分类
- **WHEN** impl-verify 发现代码实现与 FEAT 的 acceptance_criteria 不符
- **THEN** 问题标记为 `type=bug_fix`，路由到 GSD 重新实施该 FEAT 的对应 task

#### Scenario: Experience Patch 分类
- **WHEN** impl-verify 发现交互细节或文案与 UI 规格不符但不影响核心功能
- **THEN** 问题标记为 `type=experience_patch`，路由到轻量级修复流程

#### Scenario: FRZ Revise 分类
- **WHEN** impl-verify 发现范围违规或语义变更表明原始需求需要调整
- **THEN** 问题标记为 `type=frz_revise`，路由到 FRZ Revise 流程

#### Scenario: Bug Fix 输出结构
- **WHEN** 问题被分类为 `bug_fix`
- **THEN** 包含 `linked_feat`、`linked_ac`、`fix_scope`、`retry_flow`

#### Scenario: Experience Patch 输出结构
- **WHEN** 问题被分类为 `experience_patch`
- **THEN** 包含 `linked_ui`、`patch_scope`、`can_settle_locally`

#### Scenario: FRZ Revise 输出结构
- **WHEN** 问题被分类为 `frz_revise`
- **THEN** 包含 `linked_src`、`revise_scope`、`requires_frz_thaw`、`impact_assessment`

### Requirement: FRZ Revise 流程
冻结后的 FRZ Package SHALL 支持受控的需求修订流程，并自动判定 minor/major 版本。

> **FRZ 状态机**: FRZ Package 状态为 `draft` → `frozen` → `revised`。禁止 `frozen` 直接回退到 `draft`。

#### Scenario: Minor 版本修订
- **WHEN** 状态为 `frozen` 的 FRZ Package 收到视觉细节调整的 FRZ Revise 请求
- **THEN** 执行 minor 版本判定，`version` 更新为 `v1.1`，状态变为 `revised`，生成新的 FRZ Package 副本

#### Scenario: Major 版本修订
- **WHEN** 状态为 `frozen` 的 FRZ Package 收到业务规则修改的 FRZ Revise 请求
- **THEN** 执行 major 版本判定，`version` 更新为 `v2.0`，状态变为 `revised`，触发完整重新编译

#### Scenario: 版本判定决策树
- **WHEN** 执行 FRZ Revise 版本判定
- **THEN** 遵循：视觉细节/交互行为局部调整 → minor；语义行为/业务规则变更 → major；新增 FEAT（在原有 EPIC 内）且不影响已有 FEAT → minor；新增 EPIC/删除 FEAT → major

#### Scenario: 历史版本保留
- **WHEN** FRZ Package 状态变为 `revised`
- **THEN** `frozen` 版本的 FRZ Package 不可被删除或覆盖，`revision_history` 包含所有版本变更记录

#### Scenario: 修订后验收基准
- **WHEN** 下游 impl-verify 使用 `revised` 状态的 FRZ 进行验收
- **THEN** 使用最新版本的 FRZ 内容作为验收基准

#### Scenario: 禁止 frozen→draft 直接回退
- **WHEN** 尝试直接从 `frozen` 回退到 `draft`
- **THEN** 操作被拒绝，必须通过 `revised` 状态

### Requirement: v1/v2 向后兼容
v1 和 v2 的 SSOT 格式 SHALL 能够共存并支持混合链交互。

#### Scenario: v1 格式识别
- **WHEN** frz-ingest 或 impl-verify 读取无 `format_version` 字段的 SSOT 文件
- **THEN** 正确识别为 v1 格式（`format_version="0.x"`），按 v1 解析规则处理

#### Scenario: v2 格式识别
- **WHEN** frz-ingest 或 impl-verify 读取 `format_version="2.0"` 的 SSOT 文件
- **THEN** 正确识别为 v2 格式，按 v2 解析规则处理

#### Scenario: v1 FRZ 向后兼容验收
- **WHEN** impl-verify 对 v1 格式的 FRZ Package 执行验收
- **THEN** impl-verify 能够读取 v1 FRZ 内容并执行验证

#### Scenario: 混合链检测
- **WHEN** frz-ingest 编译或 impl-verify 验收检测到混合链（v1 SRC 引用 v2 TECH，或 v2 SRC 引用 v1 IMPL）
- **THEN** 输出 `warning=mixed_chain`，按 ADR-056 §8.2 的混合链规则处理

#### Scenario: v2 版本管理
- **WHEN** 检查 v2 FRZ Package 的 `format_version`
- **THEN** 值为 `"2.0"`，且版本管理遵循 major 不兼容、minor 向后兼容规则

#### Scenario: v1 测试生成接口不变
- **WHEN** v1 test_generation Skill 被 frz-ingest 调用
- **THEN** 调用参数和返回格式与 v1 标准完全一致，v2 不做任何格式转换或适配

#### Scenario: v1 测试执行接口不变
- **WHEN** v1 test_execution Skill 被线路 1 调用
- **THEN** 调用参数和返回格式与 v1 标准完全一致，线路 2 的 impl-verify 直接消费 v1 返回的 verdict 和证据
