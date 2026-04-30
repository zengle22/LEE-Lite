# LEE Lite Skill 工作手册

> 最后更新: 2026-04-30
> 项目: LEE Lite - Skill-First Governed Development

---

## 目录

1. [系统架构概览](#1-系统架构概览)
2. [产品流水线技能](#2-产品流水线技能)
3. [开发流水线技能](#3-开发流水线技能)
4. [QA 流水线技能](#4-qa-流水线技能)
5. [治理与元技能](#5-治理与元技能)
6. [CLI 运行时](#6-cli-运行时)
7. [常见问题排查](#7-常见问题排查)

---

## 1. 系统架构概览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer (ll.py)                    │
│  artifact · registry · audit · gate · loop · job · skill    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐         ┌────▼────┐
   │ Skills  │          │  SSOT   │         │Artifacts│
   └─────────┘          └─────────┘         └─────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Experience Patch │
                    └───────────────────┘
```

### 1.2 SSOT 推导链

```
Raw Input → SRC → EPIC → FEAT → TECH → IMPL → Test Plan
                                                            ↓
                                                   Test Execution
                                                            ↓
                                                    Gate Review
                                                            ↓
                                                      Release
```

### 1.3 核心概念

| 概念 | 描述 |
|------|------|
| **Skill** | 自包含的、契约治理的工作流单元 |
| **SSOT Object** | 单一事实源对象（SRC/EPIC/FEAT/TECH/IMPL） |
| **Gate** | 工作流阶段之间的决策层 |
| **Experience Patch** | 记录 AI 输出偏差的结构化修正 |

### 1.4 Skill 目录结构

```
skills/{skill-name}/
├── SKILL.md                      # 技能描述与执行协议
├── ll.contract.yaml             # 契约定义
├── ll.lifecycle.yaml            # 生命周期定义
├── input/
│   ├── contract.yaml            # 输入契约
│   └── semantic-checklist.md    # 输入语义检查清单
├── output/
│   ├── contract.yaml            # 输出契约
│   ├── template.md              # 输出模板
│   └── semantic-checklist.md    # 输出语义检查清单
├── agents/
│   ├── executor.md              # 执行器代理
│   └── supervisor.md            # 监督器代理
├── evidence/
│   ├── execution-evidence.schema.json
│   ├── supervision-evidence.schema.json
│   └── report.template.md
├── scripts/
│   ├── {skill-name}.py          # 主运行时脚本
│   ├── validate_input.sh        # 输入验证脚本
│   ├── collect_evidence.sh      # 证据收集脚本
│   ├── freeze_guard.sh          # 冻结守卫脚本
│   └── validate_output.sh       # 输出验证脚本
├── resources/
│   ├── glossary.md              # 术语表
│   ├── checklists/              # 检查清单
│   ├── examples/                # 示例
│   └── upstream-workflow-analysis.md
└── agent.md                     # 代理分地图
```

---

## 2. 产品流水线技能

### 2.1 ll-product-raw-to-src

**功能**: 将原始需求标准化为受治理的 SRC 候选包

**工作流边界**:
- 工作流键: `product.raw-to-src`
- 输入: `adr`, `raw_requirement`, `business_opportunity`, `business_opportunity_freeze`
- 输出: `src_candidate_package`
- 上游: 原始源（非冻结 SSOT 对象）
- 下游: `ll-product-src-to-epic`

#### 输入契约 (`input/contract.yaml`)

```yaml
artifact_type: raw-input
schema_version: 1.0.0
accepted_input_types:
  - adr
  - raw_requirement
  - business_opportunity
  - business_opportunity_freeze
supported_file_types:
  - .md
  - .txt
  - .json
  - .yaml
  - .yml
required_fields:
  - artifact_type
  - input_type
  - title
  - body
  - source_refs
required_refs:
  - source_refs
forbidden_states:
  - frozen
  - active
  - deprecated
forbidden_markers:
  - gate-materialize
  - gate_materialize
```

#### 输出包内容

```
artifacts/raw-to-src/{run-id}/
├── package-manifest.json
├── src-candidate.md
├── src-candidate.json
├── structural-report.json
├── source-semantic-findings.json
├── acceptance-report.json
├── result-summary.json
├── proposed-next-actions.json
├── frz-package/
│   └── (pre-SSOT freeze package)
├── execution-evidence.json
└── supervision-evidence.json
```

#### 执行协议

1. **输入验证**: 运行 `scripts/validate_input.sh`
2. **执行器阶段**: `python scripts/raw_to_src.py executor-run --input <path>`
3. **监督器阶段**: `python scripts/raw_to_src.py supervisor-review --artifacts-dir <dir>`
4. **包验证**: `python scripts/raw_to_src.py validate-package-readiness --artifacts-dir <dir>`
5. **外部 Gate 移交**: 提交到 Gate 队列等待审批

#### 阶段映射（ADR-002 双循环）

```
1. input_validation
2. raw_input_intake
3. source_normalization
4. structural_acceptance_check
5. structural_fix_loop
6. structural_recheck
7. source_semantic_review
8. semantic_acceptance_review
9. semantic_fix_loop
10. semantic_recheck
11. freeze_readiness_assessment
12. frz_package_compilation
```

#### 关键脚本文件

| 文件 | 功能 |
|------|------|
| `scripts/raw_to_src.py` | 主运行时脚本 |
| `scripts/raw_to_src_executor_phase.py` | 执行器生成阶段 |
| `scripts/raw_to_src_supervisor_phase.py` | 监督器审核阶段 |
| `scripts/raw_to_src_revision.py` | 修订处理 |
| `scripts/raw_to_src_frz.py` | FRZ 包生成 |
| `scripts/raw_to_src_gate_integration.py` | Gate 集成 |

#### 不可协商规则

- ❌ 拒绝已携带 `ssot_type` 且状态为 `frozen/active/deprecated` 的输入
- ❌ 拒绝包含 `gate-materialize` 占位符的输入
- ✅ 每次运行精确生成一个 SRC 候选包
- ✅ 如果输入明显包含多个独立问题域，失败并请求拆分
- ✅ 对于 ADR 输入，生成带有显式桥接上下文的 `governance_bridge_src` 语义

#### 与人类交互点

- **外部 Gate**: 候选包必须通过外部 Gate 审批才能进入下一阶段
- **修订请求**: Gate 返回 `revise` 或 `retry` 时，使用 `--revision-request` 重新运行

---

### 2.2 ll-product-src-to-epic

**功能**: 将 SRC 候选包转换为 EPIC 冻结包

**工作流边界**:
- 工作流键: `product.src-to-epic`
- 输入: `src_candidate_package`（来自 `ll-product-raw-to-src`）
- 输出: `epic_freeze_package`
- 上游: `ll-product-raw-to-src`
- 下游: `ll-product-epic-to-feat`

#### 输入契约 (`input/contract.yaml`)

```yaml
artifact_type: src_candidate_package
schema_version: 1.0.0
authoritative_upstream_skill: ll-product-raw-to-src
accepted_statuses:
  - freeze_ready
required_runtime_artifacts:
  - package-manifest.json
  - src-candidate.md
  - src-candidate.json
  - structural-report.json
  - source-semantic-findings.json
  - acceptance-report.json
  - result-summary.json
  - proposed-next-actions.json
  - execution-evidence.json
  - supervision-evidence.json
required_candidate_frontmatter_fields:
  - artifact_type
  - workflow_key
  - workflow_run_id
  - title
  - status
  - source_kind
  - source_refs
required_candidate_sections:
  - Problem Statement
  - Target Users
  - Triggering Scenarios
  - Business Motivation
  - Key Constraints
  - Scope Boundaries
  - Source Traceability
required_refs:
  - workflow_run_id
  - source_refs
forbidden_statuses:
  - blocked
  - human_handoff_proposed
  - rejected
forbidden_inputs:
  - raw_requirement
  - adr
  - business_opportunity
  - direct_epic_freeze
```

#### 输出包内容

```
artifacts/src-to-epic/{run-id}/
├── package-manifest.json
├── epic-freeze.md
├── epic-freeze.json
├── epic-review-report.json
├── epic-acceptance-report.json
├── epic-defect-list.json
├── epic-freeze-gate.json
├── handoff-to-epic-to-feat.json
├── execution-evidence.json
└── supervision-evidence.json
```

#### 执行协议

1. **包验证**: 验证输入包结构完整
2. **执行器阶段**: `python scripts/src_to_epic.py executor-run --input <src-package-dir>`
3. **监督器阶段**: `python scripts/src_to_epic.py supervisor-review --artifacts-dir <epic-package-dir>`
4. **冻结检查**: `python scripts/src_to_epic.py freeze-guard --artifacts-dir <epic-package-dir>`
5. **下游移交**: 生成 `handoff-to-epic-to-feat.json`

#### 关键脚本文件

| 文件 | 功能 |
|------|------|
| `scripts/src_to_epic.py` | 主运行时脚本 |
| `scripts/src_to_epic_runtime.py` | 运行时集成 |
| `scripts/src_to_epic_extract.py` | SRC 上下文提取 |
| `scripts/src_to_epic_derivation.py` | EPIC 推导逻辑 |
| `scripts/src_to_epic_review_phase1.py` | 第一阶段审核 |
| `scripts/src_to_epic_gate_integration.py` | Gate 集成 |

#### 不可协商规则

- ❌ 不接受原始需求、ADR 文本或未冻结的 SRC 草稿
- ❌ 不绕过 `scripts/src_to_epic.py` 仅手工编写最终文件而无执行和监督证据
- ❌ 拒绝折叠为单个 FEAT 的输入；将此类情况路由到适当的下层流程
- ✅ 保留 `src_root_id`、权威 `source_refs` 和 ADR-025 验收语义
- ✅ 不让执行器自我批准自己的 EPIC 输出的语义有效性

---

### 2.3 ll-product-epic-to-feat

**功能**: 将 EPIC 冻结包分解为 FEAT 规范

**工作流边界**:
- 工作流键: `product.epic-to-feat`
- 输入: `epic_freeze_package`（来自 `ll-product-src-to-epic`）
- 输出: `feat_freeze_package`
- 上游: `ll-product-src-to-epic`
- 下游: `ll-dev-feat-to-tech`, `ll-dev-feat-to-proto`, `ll-dev-feat-to-ui`

#### 输入契约 (`input/contract.yaml`)

```yaml
artifact_type: epic_freeze_package
schema_version: 1.0.0
authoritative_upstream_skill: ll-product-src-to-epic
accepted_statuses:
  - accepted
  - frozen
required_runtime_artifacts:
  - package-manifest.json
  - epic-freeze.md
  - epic-freeze.json
  - epic-review-report.json
  - epic-acceptance-report.json
  - epic-defect-list.json
  - epic-freeze-gate.json
  - handoff-to-epic-to-feat.json
  - execution-evidence.json
  - supervision-evidence.json
required_candidate_frontmatter_fields:
  - artifact_type
  - workflow_key
  - workflow_run_id
  - status
  - epic_freeze_ref
  - src_root_id
  - source_refs
required_candidate_sections:
  - Epic Intent
  - Business Goal
  - Scope
  - Non-Goals
  - Decomposition Rules
  - Constraints and Dependencies
  - Downstream Handoff
  - Traceability
required_refs:
  - epic_freeze_ref
  - src_root_id
  - source_refs
forbidden_statuses:
  - revised
  - rejected
forbidden_inputs:
  - raw_requirement
  - adr
  - src_candidate_package
  - direct_feat_bundle
```

#### 输出包内容

```
artifacts/epic-to-feat/{run-id}/
├── package-manifest.json
├── feat-freeze-bundle.md
├── feat-freeze-bundle.json
├── integration-context.json
├── feat-review-report.json
├── feat-acceptance-report.json
├── feat-defect-list.json
├── feat-freeze-gate.json
├── handoff-to-feat-downstreams.json
├── execution-evidence.json
├── supervision-evidence.json
└── surface-map-bundle.json (if design_impact_required=true)
    └── surface-map-freeze-gate.json
```

#### 执行协议

1. **包验证**: 验证 EPIC 包结构
2. **执行器阶段**: `python scripts/epic_to_feat.py executor-run --input <epic-package-dir>`
3. **监督器阶段**: `python scripts/epic_to_feat.py supervisor-review --artifacts-dir <feat-package-dir>`
4. **冻结检查**: `python scripts/epic_to_feat.py freeze-guard --artifacts-dir <feat-package-dir>`
5. **下游移交**: 生成 `handoff-to-feat-downstreams.json`

#### 关键脚本文件

| 文件 | 功能 |
|------|------|
| `scripts/epic_to_feat.py` | 主运行时脚本 |
| `scripts/epic_to_feat_runtime.py` | 运行时集成 |
| `scripts/epic_to_feat_extract.py` | EPIC 上下文提取 |
| `scripts/epic_to_feat_review_phase1.py` | 第一阶段审核 |
| `scripts/epic_to_feat_gate_integration.py` | Gate 集成 |

#### 不可协商规则

- ❌ 不接受原始需求、SRC 候选包或非正式 EPIC markdown
- ❌ 不绕过 `scripts/epic_to_feat.py` 仅手工编写最终 FEAT 包而无执行和监督证据
- ✅ 每个发出的 FEAT 必须保持为独立可接受的能力切片，不是实现任务、屏幕待办事项列表或仅架构注释
- ✅ 保留 `epic_freeze_ref`、`src_root_id`、权威 `source_refs` 和 ADR-025 验收语义
- ✅ 下游就绪必须保持显式：FEAT 输出必须足够强大以启动 TECH 和 TESTSET 推导，无需重新推导父 EPIC
- ✅ 始终具体化 `integration-context.json` 作为 `ll-dev-feat-to-tech` 的下游种子；不要让 TECH 推导仅从 FEAT 散文中猜测集成事实

---

## 3. 开发流水线技能

### 3.1 ll-dev-feat-to-tech

**功能**: 将 FEAT 转换为 TECH 技术设计（ARCH/API 可选）

**工作流边界**:
- 工作流键: `dev.feat-to-tech`
- 输入: `feat_freeze_package` + `feat_ref` 选择器 + `integration_context`
- 输出: `tech_design_package`
- 上游: `ll-product-epic-to-feat`
- 下游: `ll-dev-tech-to-impl`

#### 输入契约 (`input/contract.yaml`)

```yaml
artifact_type: feat_freeze_package
schema_version: 1.0.0
authoritative_upstream_skill: ll-product-epic-to-feat
accepted_statuses:
  - accepted
  - frozen
required_runtime_artifacts:
  - package-manifest.json
  - feat-freeze-bundle.md
  - feat-freeze-bundle.json
  - integration-context.json
  - feat-review-report.json
  - feat-acceptance-report.json
  - feat-defect-list.json
  - feat-freeze-gate.json
  - handoff-to-feat-downstreams.json
  - execution-evidence.json
  - supervision-evidence.json
required_bundle_fields:
  - artifact_type
  - workflow_key
  - workflow_run_id
  - status
  - epic_freeze_ref
  - src_root_id
  - feat_refs
  - features
  - source_refs
required_feature_fields:
  - feat_ref
  - title
  - goal
  - scope
  - constraints
  - acceptance_checks
  - source_refs
required_optional_feature_fields:
  - design_impact_required
  - candidate_design_surfaces
  - surface_map_required_reason
required_selector_fields:
  - feat_ref
required_integration_context_fields:
  - workflow_inventory
  - module_boundaries
  - legacy_fields_states_interfaces
  - canonical_ownership
  - compatibility_constraints
  - migration_modes
  - legacy_invariants
  - gate_audit_evidence
  - source_refs
conditional_runtime_artifacts:
  when_design_impact_required_true:
    - surface-map-bundle.json
    - surface-map-freeze-gate.json
forbidden_statuses:
  - revised
  - rejected
forbidden_inputs:
  - raw_requirement
  - src_candidate_package
  - epic_freeze_package
  - direct_task_list
```

#### 输出包内容

```
artifacts/feat-to-tech/{run-id}/
├── package-manifest.json
├── tech-design-bundle.md
├── tech-design-bundle.json
├── tech-spec.md
├── arch-spec.md (条件)
├── api-spec.yaml (条件)
├── integration-context.json
├── tech-review-report.json
├── tech-acceptance-report.json
├── tech-defect-list.json
├── tech-freeze-gate.json
├── handoff-to-tech-impl.json
├── execution-evidence.json
└── supervision-evidence.json
```

#### 执行协议

1. **包验证**: 验证 FEAT 包结构和集成上下文
2. **执行器阶段**: `python scripts/feat_to_tech.py executor-run --input <feat-package-dir> --feat-ref <feat-ref>`
3. **监督器阶段**: `python scripts/feat_to_tech.py supervisor-review --artifacts-dir <tech-package-dir>`
4. **冻结检查**: `python scripts/feat_to_tech.py freeze-guard --artifacts-dir <tech-package-dir>`
5. **下游移交**: 生成 `handoff-to-tech-impl.json`

#### 关键脚本文件

| 文件 | 功能 |
|------|------|
| `scripts/feat_to_tech.py` | 主运行时脚本 |
| `scripts/feat_to_tech_package_builder.py` | 包构建器 |
| `scripts/feat_to_tech_input_support.py` | 输入支持 |
| `scripts/feat_to_tech_validation.py` | 验证逻辑 |
| `scripts/feat_to_tech_semantic_runtime.py` | 语义运行时 |
| `scripts/feat_to_tech_integration_context.py` | 集成上下文处理 |
| `scripts/feat_to_tech_gate_integration.py` | Gate 集成 |

#### 不可协商规则

- ❌ 不接受原始需求、SRC 候选包、EPIC 包或治理 `feat_freeze_package` 之外的独立 FEAT markdown
- ❌ 不将 `ARCH` 和 `API` 视为 `TECH` 的无条件同级；它们是由需求评估决定的条件子产物
- ❌ 不让 `ARCH`、`TECH` 和 `API` 重述相同材料
  - `ARCH` 拥有系统放置和边界
  - `TECH` 拥有实现设计
  - `API` 拥有外部契约
- ❌ 不在冻结前绕过最终跨产物一致性检查
- ❌ 不让执行器自我批准语义有效性
- ❌ 不冻结，除非 `integration_context_sufficient` 和 `stateful_design_present` 被显式记录
- ❌ 不让 `TECH` 省略内部状态机、关键算法、输入/输出副作用或下游实现必须继承的规范所有权事实

---

### 3.2 ll-dev-tech-to-impl

**功能**: 将 TECH 转换为 IMPL 实现候选包

**工作流边界**:
- 工作流键: `dev.tech-to-impl`
- 输入: `tech_design_package` + `feat_ref` + `tech_ref`
- 输出: `feature_impl_candidate_package`
- 上游: `ll-dev-feat-to-tech`
- 下游: `ll-qa-impl-spec-test`, Feature Delivery L2

#### 输入契约 (`input/contract.yaml`)

```yaml
artifact_type: tech_design_package
schema_version: 1.0.0
authoritative_upstream_skill: ll-dev-feat-to-tech
accepted_statuses:
  - accepted
  - frozen
required_runtime_artifacts:
  - package-manifest.json
  - tech-design-bundle.md
  - tech-design-bundle.json
  - tech-spec.md
  - integration-context.json
  - tech-review-report.json
  - tech-acceptance-report.json
  - tech-defect-list.json
  - tech-freeze-gate.json
  - handoff-to-tech-impl.json
  - execution-evidence.json
  - supervision-evidence.json
required_fields:
  - artifact_type
  - workflow_key
  - workflow_run_id
  - status
  - schema_version
  - feat_ref
  - tech_ref
  - selected_feat
  - need_assessment
  - integration_sufficiency_check
  - downstream_handoff
  - source_refs
required_selected_feat_fields:
  - feat_ref
  - title
  - goal
  - scope
  - constraints
required_selector_fields:
  - feat_ref
  - tech_ref
controlled_exceptions:
  provisional_inputs_allowed: true
  required_markers:
    - provisional_ref
    - impact_scope
    - follow_up_action
  rules:
    - provisional inputs must stay explicitly marked and must not be treated as final truth
    - repo context is execution context only and must not silently override upstream truth
    - upstream ref changes must trigger freshness review or re-derive before reuse
forbidden_statuses:
  - revised
  - rejected
forbidden_inputs:
  - raw_requirement
  - feat_freeze_package
  - direct_task_list
  - shadow_tech_doc
```

#### 输出包内容

```
artifacts/tech-to-impl/{run-id}/
├── package-manifest.json
├── impl-task.md
├── upstream-design-refs.json
├── integration-plan.md
├── dev-evidence-plan.json
├── smoke-gate-subject.json
├── frontend-workstream.md (条件)
├── backend-workstream.md (条件)
├── migration-cutover-plan.md (条件)
├── execution-evidence.json
└── supervision-evidence.json
```

#### 执行协议

1. **包验证**: 验证 TECH 包结构
2. **执行器阶段**: `python scripts/tech_to_impl.py executor-run --input <tech-package-dir> --feat-ref <feat-ref> --tech-ref <tech-ref>`
3. **监督器阶段**: `python scripts/tech_to_impl.py supervisor-review --artifacts-dir <impl-package-dir>`
4. **冻结检查**: `python scripts/tech_to_impl.py freeze-guard --artifacts-dir <impl-package-dir>`
5. **下游移交**: 生成带有 `template.dev.feature_delivery_l2` 目标的移交

#### 关键脚本文件

| 文件 | 功能 |
|------|------|
| `scripts/tech_to_impl.py` | 主运行时脚本 |
| `scripts/tech_to_impl_runtime.py` | 运行时集成 |
| `scripts/tech_to_impl_builder.py` | 包构建器 |
| `scripts/tech_to_impl_workstreams.py` | 工作流分析 |
| `scripts/tech_to_impl_package_documents.py` | 文档生成 |
| `scripts/tech_to_impl_validation.py` | 验证逻辑 |
| `scripts/tech_to_impl_review.py` | 审核逻辑 |
| `scripts/tech_to_impl_contract_projection.py` | 契约投影 |

#### 不可协商规则

- ❌ 不接受原始需求、FEAT markdown 或治理 `tech_design_package` 之外的未冻结 TECH 注释
- ❌ 不让 IMPL 成为第二个技术设计文档；TECH 保持设计真相源
- ❌ 不重新推导或重命名上游集成/状态/所有权/迁移/算法引用；保留它们为继承的权威
- ❌ 不机械地发出前端、后端和迁移工作流；适用性必须显式
- ❌ 不允许没有前端或后端执行表面的包通过就绪检查
- ❌ 不让执行器自我批准语义有效性或在没有监督证据的情况下标记执行就绪
- ❌ 不发送仅摘要的 IMPL 输出，省略具体的接触集、有序任务或嵌入的执行契约

---

### 3.3 其他开发技能

#### ll-dev-feat-to-proto

**功能**: 从 FEAT 生成 UI 原型

- 输入: `feat_freeze_package` + `feat_ref`
- 输出: `prototype_package`
- 关键脚本: `scripts/feat_to_ui.py`

#### ll-dev-feat-to-ui

**功能**: 直接 UI 推导，带有表面映射契约

- 输入: `feat_freeze_package` + `feat_ref` + `surface_map_ref`
- 输出: `ui_spec_package`
- 关键脚本: `scripts/feat_to_ui.py`

#### ll-dev-proto-to-ui

**功能**: 原型到 UI 的精炼

- 输入: `prototype_package`
- 输出: `ui_spec_package`
- 关键脚本: `scripts/feat_to_ui.py`

#### ll-dev-feat-to-surface-map

**功能**: 设计所有权层，建立共享设计上下文

- 输入: `feat_freeze_package` + `feat_ref`
- 输出: `surface_map_package`
- 关键脚本: `scripts/feat_to_surface_map.py`

---

## 4. QA 流水线技能

### 4.1 ll-qa-impl-spec-test

**功能**: IMPL 实施前规范压力测试

**工作流边界**:
- 工作流键: `qa.impl-spec-test`
- 输入: `impl_spec_test_skill_request` (引用 IMPL 包 + FEAT/TECH/ARCH/API/UI/TESTSET)
- 输出: `impl_spec_test_response` + `gate_subject`
- 上游: `ll-dev-tech-to-impl`
- 下游: Gate, Feature Delivery L2

#### 输入契约 (`input/contract.yaml`)

```yaml
artifact_type: impl_spec_test_skill_request
schema_version: 1.0.0
expected_command: skill.impl-spec-test
required_request_fields:
  - api_version
  - command
  - request_id
  - workspace_root
  - actor_ref
  - trace
  - payload
required_payload_fields:
  - impl_ref
  - impl_package_ref
  - feat_ref
  - tech_ref
optional_payload_fields:
  - surface_map_ref
  - prototype_ref
  - resolved_design_refs
  - arch_ref
  - api_ref
  - ui_ref
  - ui_refs
  - testset_ref
  - testset_refs
  - source_refs
  - repo_context
  - review_profile
  - execution_mode
  - risk_profile
  - proposal_ref
  - migration_required
  - state_boundary_sensitive
  - cross_surface_chain
  - introduces_new_surface
  - external_gate_candidate
  - false_negative_challenge
  - journey_personas
  - counterexample_families
  - review_focus
```

#### 输出内容

```
artifacts/impl-spec-test/{run-id}/
├── response.json
├── verdict.json
├── logic-risk-inventory.json
├── ux-risk-inventory.json
├── ux-improvement-inventory.json
├── journey-simulation.json
├── state-invariant-checks.json
├── cross-artifact-trace.json
├── open-questions.json
├── false-negative-challenge.json
├── phase2-review.json
├── gate-subject.json
├── execution-evidence.json
└── supervision-evidence.json
```

#### 执行协议

1. **请求验证**: 验证请求信封
2. **权威解析**: 解析 FEAT/TECH/ARCH/API/UI/TESTSET 引用
3. **模式检测**: 检查是否触发深度模式
   - `migration_required`
   - 规范字段/所有权/状态边界敏感
   - 跨表面主链 + 链后增强
   - 新引入的 `UI/API/state` 表面
   - 外部 Gate 候选
4. **快速预检或深度测试**:
   - **快速预检**: 基本完整性检查
   - **深度测试**: 完整的 8 维度测试 + Phase 2 深度审查
5. **执行器阶段**: CLI 运行时 `cli/lib/impl_spec_test_runtime.py`
6. **监督器阶段**: `cli/lib/impl_spec_supervisor_review.py`
7. **生成裁决**: 发出 `verdict = pass|pass_with_revisions|block`

#### 深度模式 8 维度

| 维度 | 描述 |
|------|------|
| 1. Logic Risk Inventory | 逻辑风险清单 |
| 2. UX Risk Inventory | UX 风险清单 |
| 3. UX Improvement Inventory | UX 改进清单 |
| 4. Journey Simulation | 用户旅程模拟 |
| 5. State Invariant Checks | 状态不变量检查 |
| 6. Cross-Artifact Trace | 跨产物可追溯性 |
| 7. Open Questions | 开放问题 |
| 8. False-Negative Challenge | 假阴性挑战 |

#### Phase 2 深度审查表面

- 逻辑红队 (`cli/lib/impl_spec_logic_redteam.py`)
- 旅程审查 (`cli/lib/impl_spec_journey_reviewer.py`)
- 语义分析 (`cli/lib/impl_spec_test_semantics.py`)
- 发现聚合 (`cli/lib/impl_spec_test_findings.py`)

#### 关键运行时文件

| 文件 | 功能 |
|------|------|
| `cli/lib/impl_spec_test_runtime.py` | 主运行时 |
| `cli/lib/impl_spec_test_review.py` | 审查逻辑 |
| `cli/lib/impl_spec_supervisor_review.py` | 监督器审查 |
| `cli/lib/impl_spec_phase2_review.py` | Phase 2 审查 |
| `cli/lib/impl_spec_journey_reviewer.py` | 旅程审查 |
| `cli/lib/impl_spec_logic_redteam.py` | 逻辑红队 |
| `cli/lib/impl_spec_test_semantics.py` | 语义分析 |
| `cli/lib/impl_spec_test_findings.py` | 发现聚合 |

#### 不可协商规则

- ❌ 不将 `qa.impl-spec-test` 降级为仅散文审查摘要
- ❌ 不绕过 `python -m cli skill impl-spec-test` 用手工编写的响应信封
- ❌ 不在此工作流内重写 FEAT/TECH/ARCH/API/UI/TESTSET 真相
- ❌ 当裁决为 `pass_with_revisions` 或 `block` 时不自动分派编码工作
- ❌ 当深度模式的审查覆盖不足时不返回 `verdict = pass`
- ❌ 不将 `review_coverage.status = partial` 视为干净通过
- ❌ 不削弱 ADR-036 关于实施可执行性、失败恢复、TESTSET 覆盖或非阻塞 UI 冲突的硬规则

---

### 4.2 ll-qa-gate-evaluate

**功能**: 发布 Gate 评估（ADR-047）

**工作流边界**:
- 工作流键: `qa.gate-evaluate`
- 输入: API 清单 + E2E 清单 + 结算报告 + 弃权记录
- 输出: `release_gate_input.yaml`
- 上游: `ll-qa-test-run` (API/E2E 执行)
- 下游: `ll-gate-human-orchestrator`, CI 流水线

#### 输入契约

```yaml
# 必需输入文件:
- ssot/tests/api/{feat_id}/api-coverage-manifest.yaml
- ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml
- ssot/tests/.artifacts/settlement/api-settlement-report.yaml
- ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml
- ssot/tests/.artifacts/settlement/waiver.yaml
```

#### 输出契约

```yaml
gate_evaluation:
  evaluated_at: {timestamp}
  feature_id: {feat_id}
  final_decision: pass|fail|conditional_pass
  api_chain:
    total: N
    passed: N
    failed: N
    blocked: N
    uncovered: N
    pass_rate: X.XX
    evidence_status: complete|partial|missing
  e2e_chain:
    total: N
    passed: N
    failed: N
    blocked: N
    uncovered: N
    pass_rate: X.XX
    exception_journeys_executed: N
    evidence_status: complete|partial|missing
  anti_laziness_checks:
    manifest_frozen: true|false
    cut_records_valid: true|false
    pending_waivers_counted: true|false
    evidence_consistent: true|false
    min_exception_coverage: true|false
    no_evidence_not_executed: true|false
    evidence_hash_binding: true|false
  evidence_hash: {sha256}
  decision_reason: {explanation}
```

#### 执行协议

1. **读取输入**: 加载 API/E2E 清单、结算报告、弃权记录
2. **计算 API 链指标**:
   - 总计、通过、失败、阻塞、未覆盖项数
   - 通过率 = 通过 / (执行 - 过时 - 批准弃权)
   - `lifecycle_status=passed` 必须有 `evidence_status=complete`
   - `waiver_status=pending` 项计为失败
3. **计算 E2E 链指标**:
   - 同上 + 验证最小异常旅程覆盖（必须 ≥1）
4. **应用 ADR-047 防偷懒检查** (7 项)
5. **生成 Gate 裁决**: `pass|fail|conditional_pass`
6. **计算证据哈希**: 所有证据文件内容的 SHA-256
7. **写入输出**: `ssot/tests/.artifacts/tests/settlement/release_gate_input.yaml`

#### ADR-047 防偷懒检查 (7 项)

| 检查 | 描述 |
|------|------|
| 1. Manifest Frozen | 清单项在执行前存在（未在执行后修改以添加通过） |
| 2. Cut Records Valid | 所有裁剪项有有效裁剪记录和批准人 |
| 3. Pending Waivers Counted | `waiver_status=pending` 项计为失败 |
| 4. Evidence Consistent | `lifecycle_status=passed` 要求 `evidence_status=complete` |
| 5. Min Exception Coverage | E2E 必须已执行 ≥1 异常旅程 |
| 6. No-Evidence-Not-Executed | 没有 `evidence_refs` 的项不计数为已执行 |
| 7. Evidence Hash Binding | 执行日志哈希存在且可验证 |

#### 关键文件

| 文件 | 功能 |
|------|------|
| `ssot/tests/gate/gate-evaluator.py` | Gate 评估器 |
| `skills/ll-qa-gate-evaluate/agents/executor.md` | 执行器代理 |
| `skills/ll-qa-gate-evaluate/agents/supervisor.md` | 监督器代理 |

#### 不可协商规则

- ❌ 不读取所有必需输入产物就生成 Gate 裁决
- ❌ 不将 `waiver_status=pending` 项计数为通过——必须计为失败
- ❌ 不将没有 `evidence_refs` 的项计数为已执行
- ❌ 不允许 `lifecycle_status=passed` 且 `evidence_status=missing/incomplete`——Gate 必须拒绝
- ❌ 异常旅程覆盖为零时不生成通过裁决
- ❌ 不跳过 7 项防偷懒检查中的任何一项
- ❌ `final_decision` 必须是 `pass`/`fail`/`conditional_pass` 之一

---

### 4.3 ll-qa-feat-to-apiplan / ll-qa-api-spec-gen / ll-qa-api-manifest-init

**API 测试流水线**:

```
FEAT → ll-qa-feat-to-apiplan → API Test Plan
     → ll-qa-api-spec-gen → API Spec
     → ll-qa-api-manifest-init → API Coverage Manifest
```

#### 输入/输出

| 技能 | 输入 | 输出 |
|------|------|------|
| `ll-qa-feat-to-apiplan` | `feat_freeze_package` + `feat_ref` | API 测试计划 |
| `ll-qa-api-spec-gen` | API 测试计划 + TECH/API | API 规范 |
| `ll-qa-api-manifest-init` | API 规范 | API 覆盖清单 (`api-coverage-manifest.yaml`) |

---

### 4.4 ll-qa-prototype-to-e2eplan / ll-qa-e2e-spec-gen / ll-qa-e2e-manifest-init

**E2E 测试流水线**:

```
Prototype → ll-qa-prototype-to-e2eplan → E2E Test Plan
         → ll-qa-e2e-spec-gen → E2E Spec
         → ll-qa-e2e-manifest-init → E2E Coverage Manifest
```

#### 输入/输出

| 技能 | 输入 | 输出 |
|------|------|------|
| `ll-qa-prototype-to-e2eplan` | `prototype_package` | E2E 测试计划 |
| `ll-qa-e2e-spec-gen` | E2E 测试计划 + UI 规范 | E2E 规范 |
| `ll-qa-e2e-manifest-init` | E2E 规范 | E2E 覆盖清单 (`e2e-coverage-manifest.yaml`) |

---

### 4.5 ll-qa-test-run

**功能**: 受治理的测试执行（API + E2E）

**工作流边界**:
- 工作流键: `qa.test-run`
- 输入: API/E2E 覆盖清单
- 输出: 执行证据 + 更新后的清单 + 结算报告
- 上游: 清单初始化
- 下游: `ll-qa-settlement`, `ll-qa-gate-evaluate`

#### 关键运行时文件

| 文件 | 功能 |
|------|------|
| `cli/lib/test_exec_playwright.py` | Playwright E2E 执行 |
| `cli/lib/test_exec_ui_resolution.py` | UI 解析 |
| `cli/lib/test_exec_ui_flow.py` | UI 流执行 |
| `cli/lib/test_exec_traceability.py` | 可追溯性 |
| `cli/lib/test_exec_artifacts.py` | 产物管理 |

---

### 4.6 ll-qa-settlement

**功能**: 测试结算与证据聚合

**工作流边界**:
- 输入: API/E2E 执行结果 + 清单
- 输出: `api-settlement-report.yaml` + `e2e-settlement-report.yaml`
- 下游: `ll-qa-gate-evaluate`

---

## 5. 治理与元技能

### 5.1 ll-patch-capture

**功能**: 体验修正捕获（ADR-049）

**工作流边界**:
- 工作流键: `governance.patch-capture`
- 输入: 用户提示文本 OR 文档路径
- 输出: Patch YAML + 更新的 `patch_registry.json`
- 下游: `ll-experience-patch-settle` (Minor), `ll-frz-manage --type revise` (Major)

#### 输入契约

```yaml
feat_id: string (e.g., "feat.training-plan")
input_type: enum[prompt, document]
input_value: string (prompt text OR file path)
```

#### 输出契约

```yaml
# ssot/experience-patches/{feat_id}/UXPATCH-{NNNN}__{slug}.yaml
patch_id: UXPATCH-NNNN
feat_id: feat.{slug}
change_class: visual|interaction|semantic|other
grade_level: Minor|Major
dimensions_detected: [string]
confidence: high|medium|low
needs_human_review: true|false
source:
  input_type: prompt|document
  ai_suggested_class: ...
  human_confirmed_class: ...
description: string
context: { ... }
created_at: timestamp
created_by: actor_ref
```

#### 三分类体系

| 顶级类 | 子类 | 等级 | 路由 |
|--------|------|------|------|
| `visual` | `ui_flow`, `copy_text`, `layout`, `navigation`, `data_display`, `accessibility` | Minor | `ll-experience-patch-settle` |
| `interaction` | `interaction` | Minor | `ll-experience-patch-settle` (回写到 UI 规范、流规范、TESTSET) |
| `semantic` | `semantic` | Major | `ll-frz-manage --type revise` (FRZ 重新冻结) |
| `other` | — | Minor (人类可升级) | `ll-experience-patch-settle` |

#### 执行协议

1. **输入接收**: 接收用户提示文本或文档路径
2. **路由检测**: 分类输入为 `prompt` 或 `document`
3. **三分类**: 运行 `scripts/patch_capture_runtime.py classify_change()`
   - 扫描所有指示器列表
   - 如果语义指示器匹配 → `GradeLevel.MAJOR`（语义占优）
   - 如果多个同级维度 → `confidence=medium`
   - 如果无指示器匹配 → 回退到文件模式分类 `_fallback_classify_by_paths()`
   - 低置信度情况设置 `needs_human_review=True`
4. **Prompt-to-Patch 路径**: 执行器生成 Patch YAML 草稿
5. **Document-to-SRC 路径**: 路由到 `ll-product-raw-to-src`
6. **监督器验证**: 运行模式验证，检查冲突
7. **自动通过或升级**:
   - **自动通过**: 高置信度且无冲突 → 注册 Patch，更新注册表
   - **升级**: 低置信度或冲突 → 呈现给人类确认
8. **验证输出**: 确认 YAML 验证通过，注册表更新

#### 关键文件

| 文件 | 功能 |
|------|------|
| `cli/lib/patch_schema.py` | Patch 模式定义与验证 |
| `cli/lib/patch_auto_register.py` | 自动注册逻辑 |
| `cli/lib/patch_context_injector.py` | Patch 上下文注入器 |
| `cli/lib/patch_awareness.py` | Patch 感知 |
| `skills/ll-patch-capture/scripts/patch_capture_runtime.py` | 捕获运行时 |
| `skills/ll-patch-capture/scripts/test_patch_capture_runtime.py` | 测试 |

#### 不可协商规则

- ❌ 不运行模式验证 (`cli/lib/patch_schema.py validate_file`) 就生成 Patch YAML
- ❌ 没有监督器验证通过就自动提交 Patch
- ❌ 不将 `source.human_confirmed_class` 写为 null——在自动通过模式必须匹配 `source.ai_suggested_class`
- ❌ 不绕过双路径路由——始终先将输入分类为提示或文档
- ❌ Document-to-SRC 路径委托给 `ll-product-raw-to-src`；此技能仅路由和关联
- ✅ 所有 AI 预填充字段必须按 ADR-049 标记为人类审核
- ✅ Patch ID 必须是从 `patch_registry.json` 最大序列号派生的顺序 `UXPATCH-NNNN` 格式
- ✅ 所有切换 `ChangeClass` 的消费者必须有显式 `other` 后备以优雅处理未知值（向后兼容要求）

#### ADR-049 Patch 上下文注入（修改代码前）

在修改任何代码前：

```bash
python cli/lib/patch_context_injector.py inject \
  --workspace-root . \
  --target-files {list-of-files}
```

读取输出——包含与目标文件相关的活跃 Patch 摘要，将 Patch 约束合并到代码更改中。

---

### 5.2 ll-experience-patch-settle

**功能**: Minor 体验修正的结算

**工作流边界**:
- 输入: Patch YAML (`grade_level=Minor`)
- 输出: 回写到 UI 规范、流规范、TESTSET
- 上游: `ll-patch-capture`
- 下游: 重新测试

---

### 5.3 ll-frz-manage

**功能**: 冻结管理与发布编排（Major 修正处理）

**工作流边界**:
- 工作流键: `governance.frz-manage`
- 输入: Patch YAML (`grade_level=Major`) 或 FRZ 包引用
- 输出: 重新冻结的 FRZ 包 + 传播通知
- 上游: `ll-patch-capture`
- 下游: 重新推导下游 SSOT 对象

#### 关键文件

| 文件 | 功能 |
|------|------|
| `cli/lib/frz_schema.py` | FRZ 模式 |
| `cli/lib/frz_registry.py` | FRZ 注册表 |
| `cli/lib/frz_extractor.py` | FRZ 提取器 |
| `skills/ll-frz-manage/scripts/frz_manage_runtime.py` | 管理运行时 |

---

### 5.4 ll-meta-skill-creator

**功能**: 创建新的 LEE Lite 工作流技能

**工作流边界**:
- 工作流键: `meta.skill-creator`
- 输入: 工作流边界定义
- 输出: 完整的技能目录结构
- 下游: `ll-skill-install`

#### 执行协议

1. **捕获工作流边界**:
   - 记录工作流键、输入产物类型、输出产物类型、权威上游引用、运行时模式、直接入口点、冻结期望
   - 首先对照 ADR-038 分类请求：主要抽象、次要抽象、权威、载体、不等边界
   - 仅当主要抽象确实是 `Skill` 或 `Workflow` 时才搭建治理工作流技能；如果请求主要是 `Command`、`Tool`、`Task`、`Gate` 或 `Artifact` 工作，将其重定向到适当的载体或 SSOT 对象而不是生成新技能包
   - 如果请求定义的工作流边界不足以编写输入和输出契约，则停止
2. **搭建治理技能**:
   - 运行 `python scripts/init_lee_workflow_skill.py <skill-name> --path <dir> --input-artifact <type> --output-artifact <type>`
   - 对于 LEE Lite 仓库，保持默认的 `--runtime-mode lite_native`；仅当用户显式想要与现有 `lee` 运行时互操作时才使用 `--runtime-mode legacy_lee`
   - 优先使用生成的布局而非临时文件创建，使每个工作流技能从相同的 LL 基线开始
3. **填充治理包，不仅仅是 `SKILL.md`**:
   - 保持生成的 `SKILL.md` 作为标准兼容外壳
   - 将工作流规则、契约、生命周期、证据模式和 Gate 放入 `ll.contract.yaml`、`ll.lifecycle.yaml`、`input/`、`output/`、`evidence/`、`agents/` 和工作流脚本
4. **分离执行与监督**:
   - 执行器内容属于 `agents/executor.md`、执行证据、草稿生成和结构验证
   - 监督器内容属于 `agents/supervisor.md`、语义审查、修订决策和冻结批准或拒绝
5. **在移交技能前验证**:
   - 运行 `python scripts/validate_lee_workflow_skill.py <path/to/generated-skill>`
   - 如果环境中有标准技能验证器，也运行它
6. **需要时安装**:
   - 使用 `ll-skill-install` 将规范技能安装到 Codex 或 Claude Code 作为工作区绑定适配器

#### 关键脚本

| 文件 | 功能 |
|------|------|
| `scripts/init_lee_workflow_skill.py` | 初始化技能脚手架 |
| `scripts/validate_lee_workflow_skill.py` | 验证技能结构 |
| `scripts/evaluate_skill.py` | 评估技能质量 |
| `scripts/install_profile.py` | 安装配置文件（兼容性包装器） |

#### 不可协商规则

- ❌ 保持技能外壳与标准技能兼容。不将 LL 治理字段移动到 YAML 前置元数据中
- ❌ 不使用工作流技能脚手架走私 `Command`、`Tool`、`Task`、`Gate` 或会话残余需求
- ✅ 要求输入和输出契约。工作流技能如果仅模板化输出则不完整
- ✅ 分离结构验证与语义验证。结构检查应可脚本化；语义检查应可审查且有证据
- ✅ 在 LEE Lite 中，除非用户显式请求遗留桥接，否则不将新生成的工作流指回 `lee run`
- ❌ 不让执行器对自己的输出发出最终语义通过
- ✅ 在任何冻结 Gate 通过前要求执行证据和监督证据

---

### 5.5 ll-gate-human-orchestrator

**功能**: 人工 Gate 编排器

**工作流边界**:
- 工作流键: `governance.gate-human-orchestrator`
- 输入: Gate 队列中的待处理移交
- 输出: Gate 决策（批准/拒绝/修订）
- 下游: 下一阶段工作流或修订循环

#### 关键文件

| 文件 | 功能 |
|------|------|
| `cli/lib/gate_human_orchestrator_skill.py` | 主运行时 |
| `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator.py` | 编排器逻辑 |
| `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_runtime.py` | 运行时 |
| `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_queue.py` | 队列管理 |
| `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_ui_brief.py` | UI 简报 |
| `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_projection.py` | 投影逻辑 |
| `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_interaction.py` | 交互逻辑 |
| `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_round_support.py` | 回合支持 |

---

### 5.6 ll-skill-install

**功能**: 安装技能到运行时

**工作流边界**:
- 输入: 技能目录
- 输出: 安装的技能适配器
- 关键脚本: `scripts/install_adapter.py`

---

### 5.7 ll-project-init

**功能**: 用 LEE Lite 骨架初始化仓库

**工作流边界**:
- 输入: 仓库根目录
- 输出: 初始化的项目结构
- 关键脚本: `scripts/workflow_runtime.py`

---

## 6. CLI 运行时

### 6.1 CLI 入口点 (`cli/ll.py`)

```bash
python -m cli <command-group> <action> [options]
```

### 6.2 命令组

| 命令组 | 动作 | 描述 |
|--------|------|------|
| `artifact` | `read`, `write`, `commit`, `promote`, `append-run-log` | SSOT 产物操作 |
| `registry` | `resolve-formal-ref`, `verify-eligibility`, `validate-admission`, `publish-formal`, `bind-record` | 注册表操作 |
| `audit` | `scan-workspace`, `emit-finding-bundle`, `submit-pilot-evidence` | 审计操作 |
| `gate` | `submit-handoff`, `show-pending`, `decide`, `create`, `verify`, `evaluate`, `materialize`, `dispatch`, `release-hold`, `close-run` | Gate 操作 |
| `loop` | `run-execution`, `resume-execution`, `show-status`, `show-backlog`, `recover-jobs` | 循环操作 |
| `job` | `claim`, `release-hold`, `run`, `renew-lease`, `complete`, `fail` | 任务操作 |
| `rollout` | `onboard-skill`, `cutover-wave`, `fallback-wave`, `assess-skill`, `validate-pilot`, `summarize-readiness` | 滚出操作 |
| `skill` | `impl-spec-test`, `test-exec-web-e2e`, `test-exec-cli`, `gate-human-orchestrator`, `failure-capture`, `spec-reconcile`, `qa-test-run` | 技能执行 |
| `validate` | `request`, `response` | 验证操作 |
| `evidence` | `bundle` | 证据操作 |

### 6.3 通用选项

| 选项 | 描述 |
|------|------|
| `--request <path>` | 请求 JSON 文件路径（必需） |
| `--response-out <path>` | 响应输出路径（必需） |
| `--evidence-out <path>` | 证据输出路径（可选） |
| `--workspace-root <path>` | 工作区根目录（可选） |
| `--strict` | 严格模式（可选） |

### 6.4 关键 CLI 库文件

| 文件 | 功能 |
|------|------|
| `cli/lib/protocol.py` | 协议定义 |
| `cli/lib/errors.py` | 错误定义 |
| `cli/lib/policy.py` | 策略定义 |
| `cli/lib/registry_store.py` | 注册表存储 |
| `cli/lib/anchor_registry.py` | 锚点注册表 |
| `cli/lib/job_state.py` | 任务状态 |
| `cli/lib/job_outcome.py` | 任务结果 |
| `cli/lib/execution_runner.py` | 执行运行器 |
| `cli/lib/runner_monitor.py` | 运行器监控 |
| `cli/lib/runner_entry.py` | 运行器入口 |
| `cli/lib/mainline_runtime.py` | 主线运行时 |
| `cli/lib/reentry.py` | 重入逻辑 |
| `cli/lib/admission.py` | 准入逻辑 |
| `cli/lib/lineage.py` | 谱系逻辑 |
| `cli/lib/managed_gateway.py` | 托管网关 |
| `cli/lib/rollout_state.py` | 滚出状态 |
| `cli/lib/pilot_chain.py` | 试点链 |
| `cli/lib/gate_schema.py` | Gate 模式 |
| `cli/lib/governance_validator.py` | 治理验证器 |
| `cli/lib/enum_guard.py` | 枚举守卫 |

### 6.5 示例：运行 impl-spec-test

```bash
# 1. 创建请求文件
cat > request.json <<EOF
{
  "api_version": "1.0.0",
  "command": "skill.impl-spec-test",
  "request_id": "req-123",
  "workspace_root": ".",
  "actor_ref": "dev@example.com",
  "trace": {},
  "payload": {
    "impl_ref": "impl.training-plan",
    "impl_package_ref": "artifacts/tech-to-impl/run-456",
    "feat_ref": "feat.training-plan",
    "tech_ref": "tech.training-plan-db",
    "execution_mode": "deep"
  }
}
EOF

# 2. 运行技能
python -m cli skill impl-spec-test \
  --request request.json \
  --response-out response.json \
  --evidence-out evidence.json

# 3. 查看响应
cat response.json
```

---

## 7. 常见问题排查

### 7.1 输入验证失败

**症状**: `scripts/validate_input.sh` 返回错误

**排查步骤**:
1. 检查输入文件是否存在且格式正确
2. 验证输入契约要求的所有字段都存在
3. 检查禁止的状态/标记不存在
4. 查看 `input/semantic-checklist.md` 确认所有检查项都满足

**常见修复**:
```bash
# 检查文件结构
ls -la {input-path}

# 验证 YAML/JSON 语法
python -c "import yaml; yaml.safe_load(open('file.yaml'))"
python -c "import json; json.load(open('file.json'))"
```

---

### 7.2 执行器阶段失败

**症状**: `executor-run` 命令抛出异常

**排查步骤**:
1. 检查执行日志中的错误消息
2. 验证输入包完整且所有必需产物存在
3. 检查引用的上游 SSOT 对象是否存在且状态正确
4. 查看 `agents/executor.md` 确认提示是否符合预期

**常见修复**:
```bash
# 重新运行带有调试日志
python scripts/{skill-name}.py executor-run --input {path} --debug

# 检查证据文件
cat {artifacts-dir}/execution-evidence.json
```

---

### 7.3 监督器阶段拒绝

**症状**: `supervisor-review` 返回 semantic_reject

**排查步骤**:
1. 查看 `supervision-evidence.json` 中的缺陷列表
2. 检查 `output/semantic-checklist.md` 哪些项未满足
3. 验证执行器输出与上游权威引用一致
4. 确认没有逻辑矛盾或遗漏的约束

**常见修复**:
```bash
# 使用修订请求重新运行
python scripts/{skill-name}.py run \
  --input {path} \
  --revision-request revision-request.json
```

---

### 7.4 冻结守卫失败

**症状**: `freeze-guard` 返回 not_ready

**排查步骤**:
1. 检查执行证据和监督证据都存在且有效
2. 验证所有必需的契约文件都存在
3. 确认语义检查都通过
4. 查看 `freeze-gate.json` 中的具体原因

**常见修复**:
```bash
# 检查包准备情况
python scripts/{skill-name}.py validate-package-readiness \
  --artifacts-dir {dir}
```

---

### 7.5 Gate 移交失败

**症状**: 外部 Gate 不接受移交包

**排查步骤**:
1. 检查包清单中的工作流键和运行 ID 正确
2. 验证所有必需的 Gate 产物存在
3. 确认 `source_refs` 谱系完整
4. 查看 `handoff-*.json` 中的下游目标是否正确

**常见修复**:
```bash
# 检查 Gate 队列
python -m cli gate show-pending --workspace-root .

# 重新提交移交
python -m cli gate submit-handoff \
  --request handoff-request.json \
  --response-out response.json
```

---

### 7.6 Patch 上下文注入问题

**症状**: 修改代码前未找到相关 Patch

**排查步骤**:
1. 确认目标文件路径正确
2. 检查 `patch_registry.json` 中的 Patch 是否活跃
3. 验证 Patch 的 `changed_files` 模式匹配目标文件
4. 查看注入器日志中的匹配细节

**常见修复**:
```bash
# 手动检查注册表
cat ssot/experience-patches/patch_registry.json

# 重新运行注入器，带详细模式
python cli/lib/patch_context_injector.py inject \
  --workspace-root . \
  --target-files {files} \
  --verbose
```

---

### 7.7 API/E2E 测试执行问题

**症状**: 测试未运行或证据丢失

**排查步骤**:
1. 检查清单文件是否存在且格式正确
2. 验证测试规范与清单匹配
3. 确认 Playwright 浏览器已安装
4. 查看执行日志中的错误

**常见修复**:
```bash
# 安装 Playwright 浏览器
npx playwright install chromium

# 验证清单
python -m cli validate request --request manifest.json
```

---

### 7.8 Gate 评估返回 fail

**症状**: `ll-qa-gate-evaluate` 返回 `final_decision: fail`

**排查步骤**:
1. 检查 7 项防偷懒检查是否都通过
2. 验证 API/E2E 通过率 ≥ 80%
3. 确认所有通过项都有完整证据
4. 检查 `waiver_status=pending` 项未被计为通过
5. 确认 E2E 有 ≥1 异常旅程执行

**常见修复**:
```bash
# 重新运行失败的测试
python -m cli skill qa-test-run --request rerun-request.json

# 生成结算报告
# 然后重新评估
```

---

### 7.9 技能安装问题

**症状**: `ll-skill-install` 失败

**排查步骤**:
1. 检查技能目录结构完整
2. 运行技能验证器
3. 确认运行时兼容性设置正确
4. 查看安装日志

**常见修复**:
```bash
# 验证技能结构
python skills/ll-meta-skill-creator/scripts/validate_lee_workflow_skill.py \
  {skill-path}

# 检查 ll.contract.yaml 存在
ls -la {skill-path}/ll.contract.yaml
```

---

## 附录 A: 关键 ADR 参考

| ADR | 标题 | 描述 |
|-----|------|------|
| ADR-002 | 双循环模型 | 结构 + 语义修复循环 |
| ADR-025 | 验收语义 | 验收证据要求 |
| ADR-036 | Impl Spec Test | IMPL 实施前规范压力测试 |
| ADR-038 | 运行时核心抽象边界 | 权威 vs 载体 |
| ADR-047 | 双链测试与防偷懒 | API + E2E 测试链 |
| ADR-049 | 体验修正层 | Experience Patch 系统 |
| ADR-050 | SSOT 语义治理总纲 | §6 变更分级 |

---

## 附录 B: 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 单一事实源 | SSOT (Single Source of Truth) | 规范对象（SRC/EPIC/FEAT/TECH/IMPL） |
| 技能 | Skill | 自包含的、契约治理的工作流单元 |
| 产物 | Artifact | 技能生成的文件包 |
| 证据 | Evidence | 执行和监督的审计记录 |
| Gate | Gate | 工作流阶段之间的决策层 |
| 冻结 | Freeze | SSOT 对象的不可变状态 |
| 移交 | Handoff | 阶段之间的受控传递 |
| 谱系 | Lineage | SSOT 对象之间的可追溯链接 |
| 体验修正 | Experience Patch | 记录 AI 输出偏差的结构化修正 |
| 执行器 | Executor | 生成草稿的代理角色 |
| 监督器 | Supervisor | 审核语义正确性的代理角色 |

---

## 附录 C: 快速参考卡

### 产品流水线

```
原始输入 → [ll-product-raw-to-src] → SRC
         → [ll-product-src-to-epic] → EPIC
         → [ll-product-epic-to-feat] → FEAT
```

### 开发流水线

```
FEAT → [ll-dev-feat-to-surface-map] → Surface Map (可选)
    → [ll-dev-feat-to-tech] → TECH (+ ARCH/API 可选)
    → [ll-dev-tech-to-impl] → IMPL
    → [ll-dev-feat-to-proto] → Prototype
    → [ll-dev-feat-to-ui] → UI Spec
```

### QA 流水线

```
FEAT → [ll-qa-feat-to-apiplan] → API Test Plan
    → [ll-qa-api-spec-gen] → API Spec
    → [ll-qa-api-manifest-init] → API Manifest
    → [ll-qa-test-run] → API Execution

Prototype → [ll-qa-prototype-to-e2eplan] → E2E Test Plan
         → [ll-qa-e2e-spec-gen] → E2E Spec
         → [ll-qa-e2e-manifest-init] → E2E Manifest
         → [ll-qa-test-run] → E2E Execution

IMPL → [ll-qa-impl-spec-test] → Verdict

API/E2E → [ll-qa-settlement] → Settlement Reports
        → [ll-qa-gate-evaluate] → Gate Decision
```

### 治理流水线

```
用户提示/文档 → [ll-patch-capture] → Patch
            → [ll-experience-patch-settle] (Minor)
            → [ll-frz-manage] (Major)

Gate 队列 → [ll-gate-human-orchestrator] → Decision

新技能需求 → [ll-meta-skill-creator] → Skill
          → [ll-skill-install] → Installed
```

---

**文档结束**
