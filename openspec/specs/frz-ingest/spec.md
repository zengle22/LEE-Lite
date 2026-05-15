---
base_document: ssot/adr/ADR-056-LL-v2基于 FRZ 的多轴投影、冻结与实施验证架构.md
derived_from: _bmad-output/planning-artifacts/epics.md
patch_scope: "Epic 1 (FR1-FR6, NFR1-NFR7, AR1) — frz-ingest 实现规格"
priority_rule: "本 spec 与 epics.md 冲突时以本 spec 为准；本 spec 不得违背 brainstorming 关键决策"
---

## ADDED Requirements

### Requirement: 6 维度完整性检查
frz-ingest SHALL 在接收 Complete Design Package 时自动执行 6 维度完整性检查，验证 business_design、product_design、architecture_design、engineering_design 必填，ux_design 有条件必填（条件定义见 `docs/ai-infra/ITERATION-DOCUMENT-CHECKLIST.md`），test_design 可选。

#### Scenario: 完整 Design Package 通过检查
- **WHEN** frz-ingest 接收包含所有必填维度且 ux_design 满足条件必填规则的 Complete Design Package
- **THEN** 输出 `verdict=pass`，`missing_items` 为空列表，`warnings` 为空列表

#### Scenario: 缺少必填维度被拦截
- **WHEN** frz-ingest 接收缺少 `business_design` 维度的 Design Package
- **THEN** 输出 `verdict=blocked`，`missing_items` 包含 `business_design`，编译流程在 step_1 终止

#### Scenario: 条件必填维度未满足被拦截
- **WHEN** frz-ingest 接收 `ux_design` 触发条件必填但未提供内容的 Design Package
- **THEN** 输出 `verdict=blocked`，`missing_items` 包含 `ux_design`

#### Scenario: 可选维度缺失不阻塞
- **WHEN** frz-ingest 接收缺少 `test_design`（可选维度）的 Design Package
- **THEN** 输出 `verdict=pass` 或 `partial`，`missing_items` 不包含 `test_design`

#### Scenario: 输入文档格式异常
- **WHEN** frz-ingest 接收存在 YAML 格式错误、必填 frontmatter 字段缺失或文件编码异常的 Design Package
- **THEN** 输出 `verdict=blocked` 或 `partial`，`warnings` 包含具体格式异常项

### Requirement: SRC/EPIC/FEAT 需求链编译
frz-ingest SHALL 将 Design Package 的商业设计和用户旅程编译为 SRC 容器（含 EPIC/FEAT 章节），生成结构化 YAML 并支持段落级溯源。

#### Scenario: 商业设计维度编译为 SRC
- **WHEN** frz-ingest 编译通过完整性检查的商业设计维度（step_2_1）
- **THEN** 生成 SRC YAML，包含 `problem_domain`、`business_goal`、`target_users`、`triggering_scenarios`、`scope_boundaries`、`non_goals`、`global_constraints`，且每个字段包含段落级 `source_refs`

#### Scenario: 用户旅程编译为 EPIC 章节
- **WHEN** frz-ingest 编译包含用户旅程场景的 Design Package（step_2_2）
- **THEN** 在 SRC 中生成 `epics` 章节，每个 epic 包含 `epic_id`（格式 `EPIC-{src_id}-{序号}`）、`capability_name`、`user_value`、`business_closure`、`priority`、`included_scenarios`、`excluded_scenarios`

#### Scenario: 用户故事编译为 FEAT 章节
- **WHEN** frz-ingest 编译包含用户故事和 AC 的 Design Package
- **THEN** 每个 FEAT 包含 `feat_id`（格式 `FEAT-{src_id}-{epic序号}-{feat序号}`）、`title`、`user_value`、`trigger`、`main_flow`、`alternative_flows`、`state_changes`、`business_rules`、`exception_flows`、`acceptance_criteria`、`uat_scenarios`、`non_goals`

#### Scenario: 编译零语义发明
- **WHEN** 任何编译字段的内容无法追溯到 Design Package 输入
- **THEN** frz-ingest 标记为 invented semantics 并中断编译

#### Scenario: 段落级溯源完整性
- **WHEN** 检查编译完成的 SRC 容器的 `source_refs`
- **THEN** 所有必填字段的 `source_refs` 非空，格式符合 `{path}#{section}.{paragraph}`

### Requirement: UI 交互设计编译
frz-ingest SHALL 将 UX 设计维度编译为 UI YAML 文件，输出结构化交互设计规格并与 FEAT 关联。

#### Scenario: UX 设计维度编译为 UI YAML
- **WHEN** frz-ingest 编译通过完整性检查且包含 UX 设计维度的 Design Package
- **THEN** 生成 UI YAML 文件，文件名格式 `UI-{src_id}-{slot}__{slug}.yaml`

#### Scenario: UI YAML 内容结构完整性
- **WHEN** 检查编译生成的 UI YAML 内容结构
- **THEN** 包含 `design_principles`（≥3 条，每条含 principle/description/example）、`interaction_flow`、`state_expression`、`design_tokens`、`copy_style`、`platform_strategy`、`error_state_ux`

#### Scenario: 微文案场景示例
- **WHEN** 检查编译生成的 UI YAML 的 `copy_style.examples`
- **THEN** 包含 ≥3 个微文案场景示例

#### Scenario: UI YAML 关联正确性
- **WHEN** 检查编译生成的 UI YAML 的 `feat_ref` 和 `src_ref`
- **THEN** 正确关联到输入的 FEAT 和 SRC

#### Scenario: 非 UI 驱动场景不生成 UI YAML
- **WHEN** frz-ingest 编译不包含 UX 设计维度的 Design Package
- **THEN** 不生成 UI YAML，或生成仅包含 `feat_ref`、`src_ref` 和空字段的占位 UI YAML

### Requirement: TECH/ARCH 架构设计编译
frz-ingest SHALL 将架构设计维度编译为 TECH YAML 和 ARCH YAML，输出结构化技术设计和架构设计规格。

#### Scenario: 架构设计维度编译为 TECH/ARCH
- **WHEN** frz-ingest 编译通过完整性检查且包含架构设计维度的 Design Package
- **THEN** 生成 TECH YAML 和 ARCH YAML，文件名格式 `TECH-{src_id}-{slot}__{slug}.yaml` 和 `ARCH-{src_id}-{slot}__{slug}.yaml`

#### Scenario: TECH YAML 内容完整性
- **WHEN** 检查编译生成的 TECH YAML
- **THEN** 包含 `tech_stack`（language、framework、database、ai_provider、key_libraries）、`sync_async`、`non_functional`（performance、security、concurrency、degradation）、`constraints`、`risks`

#### Scenario: ARCH YAML 内容完整性
- **WHEN** 检查编译生成的 ARCH YAML
- **THEN** 包含 `layering`（每层含 layer/responsibility/file_location）、`data_flow`（每步含 step/input/output/transformation）、`storage`（strategy、key_entities、jsonb_fields、normalization_notes）、`integration`（每项含 service/protocol/fallback）

#### Scenario: TECH/ARCH 关联正确性
- **WHEN** 检查编译生成的 TECH YAML 和 ARCH YAML 的 `feat_ref` 和 `src_ref`
- **THEN** 正确关联到输入的 FEAT 和 SRC

#### Scenario: 非功能需求溯源
- **WHEN** 检查 TECH YAML 中 `non_functional.performance` 的内容来源
- **THEN** 可追溯到 Design Package 架构设计维度的对应段落

### Requirement: API 契约编译
frz-ingest SHALL 将 API 设计维度编译为 API YAML 文件，输出结构化 API 契约并与 OpenAPI 兼容。

#### Scenario: API 设计维度编译为 API YAML
- **WHEN** frz-ingest 编译通过完整性检查且包含 API 设计维度的 Design Package
- **THEN** 生成 API YAML 文件，文件名格式 `API-{src_id}-{slot}__{slug}.yaml`

#### Scenario: API YAML 端点定义完整性
- **WHEN** 检查编译生成的 API YAML 的 `endpoints`
- **THEN** 每个端点包含 `path`、`method`、`purpose`、`consumer`、`provider`、`request_schema`（含 fields：name/type/required/description）、`response_schema`、`error_codes`、`compatibility`、`security_constraints`、`rate_limit`、`examples`

#### Scenario: API YAML 时序图完整性
- **WHEN** 检查编译生成的 API YAML 的 `sequence_diagrams`
- **THEN** 每个时序图包含 `scenario`、`diagram`（Mermaid/PlantUML 格式）、`timeout`、`retry_strategy`、`degradation_path`

#### Scenario: API YAML 版本策略
- **WHEN** 检查编译生成的 API YAML 的 `version_strategy`
- **THEN** 值为 Design Package 中定义的版本策略

#### Scenario: API YAML 关联正确性
- **WHEN** 检查编译生成的 API YAML 的 `feat_ref` 和 `src_ref`
- **THEN** 正确关联到输入的 FEAT 和 SRC

### Requirement: IMPL 实施包编译
frz-ingest SHALL 将工程实施维度编译为自包含的 IMPL YAML 文件，完整复制上游上下文使下游 GSD 执行者无需链式查找。

#### Scenario: IMPL YAML 自包含需求上下文
- **WHEN** frz-ingest 编译 IMPL 维度（step_2_6~2_9）
- **THEN** 生成 IMPL YAML，`requirement_context` 完整复制 FEAT 的所有字段，不丢失任何字段

#### Scenario: IMPL YAML 自包含技术上下文
- **WHEN** 检查编译生成的 IMPL YAML 的 `tech_context`
- **THEN** 完整复制 TECH 的 `tech_stack`、`sync_async`、`non_functional`、`constraints`、`risks`

#### Scenario: IMPL YAML 自包含架构上下文
- **WHEN** 检查编译生成的 IMPL YAML 的 `arch_context`
- **THEN** 完整复制 ARCH 的 `layering`、`data_flow`、`storage`、`integration`

#### Scenario: IMPL YAML 自包含 API 上下文
- **WHEN** 检查编译生成的 IMPL YAML 的 `api_context`
- **THEN** 完整复制 API 的 `version_strategy`、`endpoints`、`sequence_diagrams`

#### Scenario: IMPL YAML 允许范围定义
- **WHEN** 检查编译生成的 IMPL YAML 的 `allowed_scope`
- **THEN** 包含 `directories` 和 `files`

#### Scenario: IMPL YAML 测试指导
- **WHEN** 检查编译生成的 IMPL YAML 的 `test_guidance`
- **THEN** 包含 `boundary_conditions`、`ai_uncertainty_scenarios`、`test_layering`、`testability_notes`

#### Scenario: 冻结后 IMPL 不可变
- **WHEN** 冻结后的 IMPL YAML 的上游 FEAT/TECH/ARCH/API 发生变更
- **THEN** 已冻结 IMPL 内容保持不变

### Requirement: SSOT 链对齐检查
frz-ingest SHALL 在编译后验证 SSOT 链内部一致性，确保需求覆盖、轴间一致性、溯源完整性在冻结前被验证。

#### Scenario: 完整 SSOT 链对齐通过
- **WHEN** frz-ingest 对完整且内部一致的 mock SSOT 链执行对齐检查（step_3）
- **THEN** 输出 `verdict=pass`，`issues` 为空列表

#### Scenario: FEAT 必填字段完整性
- **WHEN** frz-ingest 对某个 FEAT 的必填字段（feat_id、title、user_value、main_flow、acceptance_criteria）存在缺失的 SSOT 链执行对齐检查（step_3）
- **THEN** 输出 `verdict=fail`，`issues` 包含缺失字段的具体引用

#### Scenario: 轴间不一致检测
- **WHEN** frz-ingest 对 TECH 的 `tech_stack.language` 与 ARCH 的 `layering` 描述存在矛盾的 SSOT 链执行对齐检查
- **THEN** 输出 `verdict=fail`，`issues` 包含轴间不一致的具体描述

#### Scenario: 溯源断裂检测
- **WHEN** frz-ingest 对某个 IMPL 的 `feat_ref` 指向不存在的 FEAT 的 SSOT 链执行对齐检查
- **THEN** 输出 `verdict=fail`，`issues` 包含溯源断裂项

#### Scenario: 对齐检查问题输出结构
- **WHEN** 对齐检查发现 issues
- **THEN** 每个 issue 包含 `severity`、`location`、`description`、`suggested_fix`

### Requirement: 编译产物漂移检测
frz-ingest SHALL 检测编译产物相对原始 Design Package 的语义漂移，验证编译零语义发明和意图保真度。

#### Scenario: 无漂移通过
- **WHEN** frz-ingest 对编译产物忠实反映输入内容的 SSOT 链执行漂移检测（step_4）
- **THEN** 输出 `verdict=pass`，`drift_items` 为空列表

#### Scenario: 发明语义漂移检测
- **WHEN** frz-ingest 检测到 SRC 的 `business_goal` 包含 Design Package 中不存在的描述
- **THEN** 输出 `verdict=drift_found`，`drift_items` 包含类型 `invented_semantics`

#### Scenario: 范围漂移检测
- **WHEN** frz-ingest 检测到 FEAT 的 `scope_boundaries` 比 Design Package 的范围声明更宽
- **THEN** 输出 `verdict=drift_found`，`drift_items` 包含类型 `scope_drift`

#### Scenario: 技术漂移检测
- **WHEN** frz-ingest 检测到 TECH 的 `tech_stack` 选择了 Design Package 未指定的技术
- **THEN** 输出 `verdict=drift_found`，`drift_items` 包含类型 `tech_drift`

#### Scenario: 设计意图漂移检测
- **WHEN** frz-ingest 检测到 UI 的 `design_principles` 与 Design Package 的设计意图不符
- **THEN** 输出 `verdict=drift_found`，`drift_items` 包含类型 `design_intent_drift`

#### Scenario: 漂移项输出结构
- **WHEN** 漂移检测发现 drift_items
- **THEN** 每个 drift_item 包含 `drift_type`、`source_field`、`compiled_field`、`drift_description`、`severity`

### Requirement: 冻结机制与 FRZ Package 输出
frz-ingest SHALL 将验证通过的 SSOT 链冻结并输出 FRZ Package，使编译产物成为不可变的发布基线。

#### Scenario: 冻结成功
- **WHEN** frz-ingest 对通过所有检查的 SSOT 链执行冻结（step_6）
- **THEN** 生成 FRZ YAML 文件（`FRZ-{frz_ref}__{slug}.yaml`），`status` 从 `draft` 变为 `frozen`，`frozen_at` 写入当前时间戳，`format_version` 值为 `2.0`

#### Scenario: 冻结对象不可变
- **WHEN** 任何工具尝试修改 `frozen` 状态的 FRZ 或链内 SSOT 对象
- **THEN** 操作被拒绝，抛出 `FrozenObjectError`

#### Scenario: 幂等重试
- **WHEN** frz-ingest 从 step_3 重新执行（编译过程中 step_3 失败）
- **THEN** 结果与首次执行 step_3 一致，不重复生成已完成的 step_1 和 step_2 输出

#### Scenario: FRZ Package 内容完整性
- **WHEN** 检查冻结后的 FRZ Package
- **THEN** `frozen_ssot_chain` 包含所有 SSOT 对象引用：`src_ref`、`tech_refs`、`arch_refs`、`api_refs`、`ui_refs`（可选）、`impl_refs`、`prototype_refs`（可选）；`acceptance_test_cases` 包含 `api_tests`、`e2e_tests`、`coverage_map`、`total_ac`、`covered_ac`；`completeness_check`、`alignment_check`、`drift_check` 结果均被记录

#### Scenario: FRZ Package 验收测试覆盖完整性
- **WHEN** frz-ingest 检查冻结前的 FRZ Package，发现某个 FEAT 的 `acceptance_criteria` 未被 `acceptance_test_cases` 覆盖
- **THEN** 输出 `verdict=fail`，`issues` 包含未覆盖 AC 的具体引用，冻结流程终止

#### Scenario: FRZ Revise 状态转换
- **WHEN** `frozen` 状态的 FRZ Package 需要修改
- **THEN** 必须通过 `frozen→revised` 状态转换，不能直接回到 `draft`

### Requirement: v1 测试集成与验收用例生成
frz-ingest SHALL 调用 v1 test_generation Skill 生成验收测试用例，实现 v1 测试能力在 v2 中无缝复用。

#### Scenario: 调用 v1 test_generation
- **WHEN** frz-ingest 执行 step_5 测试用例生成
- **THEN** 调用 v1 test_generation Skill 接口，`target_type` 参数固定为 `acceptance`

#### Scenario: 测试用例格式正确
- **WHEN** frz-ingest 接收 v1 test_generation 返回结果
- **THEN** 用例格式符合 v1 标准，包含 `test_id`、`description`、`steps`、`expected_result`、`linked_ac`

#### Scenario: 验收标准覆盖映射
- **WHEN** v1 test_generation 返回测试用例
- **THEN** `coverage_map` 显示每条 AC 至少被一条测试用例覆盖，或明确标记为 `uncovered`

#### Scenario: 测试生成失败降级
- **WHEN** v1 test_generation Skill 调用失败（网络错误、超时、返回格式异常）
- **THEN** 记录错误日志，`test_cases` 标记为 `generation_failed`，不阻塞后续冻结步骤

#### Scenario: 测试用例嵌入 FRZ Package
- **WHEN** 验收测试用例生成完成
- **THEN** 存储在 FRZ Package 的 `acceptance_test_cases` 字段中，与 SSOT 链一同冻结

## NonFunctional Requirements

### NFR1: 编译零语义发明
frz-ingest SHALL 确保编译产物中任何无法追溯到 Design Package 输入的内容均被标记为 invented semantics 并中断编译。

### NFR2: 段落级溯源
frz-ingest SHALL 为所有编译输出字段写入 `source_refs`，格式为 `{path}#{section}.{paragraph}`，冻结后不可修改。

### NFR3: 冻结状态机
frz-ingest SHALL 实现 FRZ 状态机：draft → frozen → revised。禁止 frozen → draft 的直接回退。

### NFR4: 幂等性
frz-ingest 编译 SHALL 是幂等操作，支持从失败步骤重试，不重复生成已完成步骤的输出。

### NFR5: v1 Skill 复用
frz-ingest 调用 v1 test_generation Skill 时，SHALL 保持 v1 接口契约不变，不做格式转换。

### NFR6: SSOT 格式版本管理
frz-ingest 输出的 v2 FRZ Package SHALL 包含 `format_version="2.0"`。major 版本不兼容，minor 版本向后兼容。

### NFR7: 不可协商规则
frz-ingest SHALL 不补全缺失需求、不静默修复冲突、不改变业务意图。

## Additional Requirements

### AR1: frz-ingest 骨架（Phase 1）
frz-ingest Phase 1 SHALL 实现：完整性检查 + v1 Skill 调用接口 + 冻结机制 + 漂移检测 + 段落级 source_refs + 完整异常处理。
