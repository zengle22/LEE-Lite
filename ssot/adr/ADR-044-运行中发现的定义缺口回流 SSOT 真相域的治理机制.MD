# ADR-044：运行中发现的定义缺口回流 SSOT 真相域的治理机制

* 状态：Draft
* 日期：2026-04-08
* 决策者：TBD
* 适用范围：`ssot/`（ADR-008 的主链与派生 SSOT）、`skills/`（governed workflows）、`cli/`（gate/runner/registry carrier）、`artifacts/`（trace/lineage/manifest/reports）
* 相关 ADR：ADR-008、ADR-015、ADR-016、ADR-018、ADR-038、ADR-039、ADR-042、ADR-043

---

# 1. 背景

本仓库已经建立了 SSOT 主链与派生对象模型（ADR-008），并在 `artifacts/` 中形成可审计的 trace/lineage/manifest 证据链。

但在真实执行中（product/dev/qa workflows、BMAD/辅助实现、脚本补洞、gate/validator 收敛），仍会持续发生：

1. SSOT 初次冻结并不总是完整（failure path、scope boundary、状态机分支、API 语义、验收口径等常缺口）。
2. 执行层为了推进，会在派生层补定义/做假设/裁范围。
3. 若缺乏回流机制，这些“事实上的真相”会永久散落在派生层与实现逻辑中，导致 SSOT 名义存在但事实不闭合。

仓库现有实现已明确：meta 层只用于 lineage/治理/审计，**不得替代 source 事实层**。因此本 ADR 要解决的是：

> **允许执行层临时补洞，但强制把长期定义回流到 SSOT 真相域，避免派生层取得事实定义权。**

---

# 2. 问题定义

需要治理的不是“执行中出现新增信息”，而是：

* 新增信息的分类是否结构化（禁止匿名规则）
* 新增信息是否被挂账并可见（禁止无痕消失）
* 新增信息是否被清算并回写（禁止长期真相滞留派生层）
* 哪些信息可延期、哪些必须阻断（避免 assumption 成逃逸口）
* 谁能定案（避免“谁顺手谁决定”）

---

# 3. 决策

## 3.1 SSOT 仍是唯一真相域，但真相域必须可回写

* SSOT 的权威边界仍由 `ssot/` 承载。
* “唯一真相”不等于“初版静态不动”，而是 **可追溯、可审计、可回写、可再派生**。

## 3.2 执行层允许临时补充，但禁止匿名沉淀长期定义

* 允许临时补充
* 禁止匿名补充（必须结构化记录）
* 禁止未清算地结束（必须有 reconcile 结论）
* 禁止长期定义只留在派生层

## 3.3 新增信息必须归类为四类之一

* `spec_gap`：SSOT 缺失了应有定义，影响未来同类实现/验收/测试
* `local_assumption`：局部假设，长期有效性未确认
* `scope_cut`：范围裁剪；必须结构化携带 `scope_kind` 与 `affected_refs`
* `execution_decision`：执行策略/工程顺序，不应成为长期真相

## 3.4 must_backport 判定标准

新增信息满足任一条件，则 `must_backport: true`：

1. 属于长期规则（未来复用）
2. 相邻/同类任务仍会用到
3. review/gate/test/验收依赖它才能下结论

### 3.4.1 默认判定清单（默认 `must_backport: true`）

以下内容默认 `must_backport: true`，除非在 reconcile 中显式豁免并写明理由：

* 状态机分支（含异常/补偿/回退/重试）
* API 字段语义 / 错误码 / 默认值 / 幂等与兼容性边界
* UI 主流程异常分支与兜底路径（取消/中断/失败/回退/返回）
* acceptance / testset 口径（成功/失败定义、边界条件、覆盖口径）
* 跨模块边界与 owner binding（surface map 归属、共享资产绑定、跨模块职责边界）

## 3.5 引入 `spec_reconcile` 收口步骤

在以下任一动作之前必须 reconcile：

* candidate → freeze-ready / formal materialization
* gate approve → downstream dispatch（进入 runner 自动推进）
* merge / release（形成发布事实证据链）

没有 reconcile 的产物，只能视为“实现推进了，但定义未闭环”。

## 3.6 三类工件边界与权威字段（必须写死）

同一 finding 的“建议/计划/证据”必须分离，并明确权威来源：

* `spec-findings.json.findings[].proposed_ssot_targets`：**proposal**（发现阶段建议，不承诺、不权威）
* `spec-backport-queue.json.items[].target_ssot_paths`：**plan**（待执行计划落点，不等于已回写）
* `spec-reconcile-report.json.decisions[].ssot_patch_refs`：**audit evidence**（已发生回写证据；是否回写只看它）

## 3.7 `local_assumption` 放行规则（防逃逸）

* 若 `local_assumption` 影响：核心用户流程闭环 / 状态机分支 / API 契约 / 验收口径  
  → **不得以 `deferred` 放行到 freeze/dispatch 前**，必须先升级为 `spec_gap` 或在本轮明确决策（backported/rejected）。
* 只有不影响主流程闭环的局部行为假设，才允许 `deferred` 进入下一轮（仍需挂牌，指定 owner+checkpoint）。

## 3.8 决策权限模型（谁能 backport / reject / defer）

* `spec_gap`：执行者可提出与补证据；reviewer 可阻断；**定案人：FEAT owner / SSOT owner**
* `local_assumption`：执行者可提出并临时使用（受 3.7 约束）；reviewer 可要求升级；**定案人：FEAT owner / SSOT owner**
* `scope_cut`：
  * 影响验收口径或版本边界：**定案人：product owner + SSOT owner**
  * 仅实施临时裁剪：**定案人：FEAT owner / SSOT owner**
* `execution_decision`：执行者可记录；reviewer 仅检查是否越权

---

# 4. 机制（落在仓库实现面）

本 ADR 引入三个可落地载体，并复用仓库既有的 trace/lineage/manifest 风格。

## 4.1 `spec-findings.json`（新增发现台账，允许为空）

* 位置：`artifacts/<workflow>/<run_dir>/spec-findings.json`
* manifest 增加：`spec_findings_ref`
* 空的语义固定：
  * 空 findings = 本轮无新增定义/假设/裁剪/决策需要挂账
  * 不代表没做 review
  * 不代表可以跳过 reconcile（可生成零项 reconcile report）

## 4.2 `spec-backport-queue.json`（回写队列，仓库级）

* 位置：`artifacts/reports/governance/spec-backport/spec-backport-queue.json`
* `spec_gap` 与未确认 `local_assumption` 必须入队
* Phase 0/1：`scope_cut` **不入队**（避免把“范围裁剪本身”误当作回写计划）；其回写与审计以 `spec-reconcile-report.json.decisions[].ssot_patch_refs` 为准
* 队列允许 deferred，但不得无痕消失

## 4.3 `spec-reconcile-report.json`（收口清算报告）

* 位置：`artifacts/<workflow>/<run_dir>/spec-reconcile-report.json`
* backported 必须给 `ssot_patch_refs` 非空（唯一审计证据）
* recorded 仅允许 `execution_decision`
* decision 必须包含 `decided_by.role`（对齐 3.8 权限模型）

## 4.4 用户旅程（落地用法）：调研 → reconcile → 自动回写 SSOT → 解除 hold

本仓库 Phase 0/1 的 reconcile 机制默认是“**治理门禁 + 审计报告**”，为了让流程可落地，本 ADR 同时定义一个可执行的“**reconcile-as-apply**”用户旅程：

> 当需要更新 SSOT 主链/派生链（`ssot/`）时，用户把“更新意图”作为自然语义输入交给 reconcile skill；skill 负责解析/结构化并执行回写，产出可审计的 patch receipt，并自动生成 `spec-reconcile-report.json` 以解除 hold。

### 4.4.1 触发场景

* runner/job 进入 `waiting-human` 且 `hold_reason=spec_reconcile_required`
* 或者在 freeze/materialize 前被门禁阻断（缺 reconcile 或 `blocking_items` 非空）

### 4.4.2 最小输入（自然语义 `ssot_updates`）

在 `skill.spec-reconcile` 的 request payload 中提供：

* `package_dir_ref`：被收口的上游包目录（如 `artifacts/feat-to-tech/run-73`）
* `decided_by.role/ref`：定案角色（对齐 3.8）
* `ssot_updates`：自然语义更新描述（建议在文本中显式引用 finding_id，并给出目标 `ssot/...` 路径与内容块）
* `auto_release_holds`（可选）：当 reconcile report 生成且 `blocking_items=[]` 时，自动释放引用该 report 的 `waiting-human` jobs（把人工步骤压到最少）

> 说明：为了让解析/结构化可机械化落地，`ssot_updates` 推荐以“自然语言说明 +（可省略的）目标文件 + 内容块”的形式提供；skill 会把它结构化为写文件操作并生成 patch receipt。后续可以升级为纯自然语言到结构化 patch 的 LLM 解析器，但不得破坏 3.6 的权威字段关系。
>
> 机械化解析规则（已实现）：
>
> 1. **finding_id 必须显式出现**；否则无法挂接审计证据。
> 2. `path: ssot/...` **可省略**：若该 finding 在 `spec-backport-queue.target_ssot_paths` 或 `spec-findings.proposed_ssot_targets` 中只解析出 **唯一** `ssot/...` 文件路径，则自动选择；否则拒绝并要求显式给 path。
> 3. 支持 `yaml-patch`：当内容块使用 ```yaml-patch 时，会对目标 YAML 做 deep-merge patch（适合“补字段/改默认值”，避免整文件替换）。

### 4.4.3 输出与审计证据

reconcile-as-apply 成功后，必须满足：

* `ssot/` 目标文件已被写入/更新（真相回流完成）
* `spec-reconcile-report.json.decisions[].ssot_patch_refs` 填入 **patch receipt**（唯一可审计证据）
* `spec-reconcile-report.json.blocking_items=[]`（解除 hold 的必要条件）

### 4.4.4 解除 hold（继续自动推进）

当 report 已产出且 `blocking_items=[]`：

* `python -m cli.ll gate release-hold ...` 或 `python -m cli.ll job release-hold ...`

release 动作将校验 `required_preconditions` 指向的 reconcile report 存在且无 blocking。

---

# 5. 附录 A：JSON Schema（建议基线）

> 说明：schema 的目标是先冻结“最小可执行闭环”。后续可以增量扩展字段，但不得破坏 3.6 的权威字段关系。

## A.1 `spec-findings.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "lee-lite/spec-findings.schema.json",
  "title": "SpecFindings",
  "type": "object",
  "required": ["artifact_type", "schema_version", "status", "trace", "findings"],
  "additionalProperties": false,
  "properties": {
    "artifact_type": { "const": "spec_findings" },
    "schema_version": { "type": "string", "minLength": 1 },
    "status": { "enum": ["open", "closed"] },
    "trace": {
      "type": "object",
      "required": ["workflow_key", "run_ref"],
      "additionalProperties": true,
      "properties": {
        "workflow_key": { "type": "string", "minLength": 1 },
        "run_ref": { "type": "string", "minLength": 1 }
      }
    },
    "lineage": {
      "type": "array",
      "items": { "type": "string", "minLength": 1 },
      "default": []
    },
    "findings": {
      "type": "array",
      "items": { "$ref": "#/$defs/finding" },
      "default": []
    }
  },
  "$defs": {
    "impact_area": {
      "enum": [
        "core_user_flow",
        "state_machine",
        "api_contract",
        "api_semantics",
        "ui_main_flow",
        "ui_failure_path",
        "acceptance_testset",
        "cross_module_boundary",
        "owner_binding"
      ]
    },
    "finding": {
      "type": "object",
      "required": ["finding_id", "type", "title", "description", "affects_future_work", "must_backport", "status"],
      "additionalProperties": false,
      "properties": {
        "finding_id": { "type": "string", "minLength": 6 },
        "type": { "enum": ["spec_gap", "local_assumption", "scope_cut", "execution_decision"] },
        "title": { "type": "string", "minLength": 1 },
        "description": { "type": "string", "minLength": 1 },
        "affects_future_work": { "enum": ["yes", "possible", "no"] },
        "severity": { "enum": ["low", "medium", "high"], "default": "medium" },
        "impact_areas": {
          "type": "array",
          "items": { "$ref": "#/$defs/impact_area" },
          "default": []
        },
        "must_backport": { "type": "boolean" },
        "proposed_ssot_targets": {
          "description": "proposal 字段（不权威）。计划落点以 backport-queue 为准；审计落点以 reconcile ssot_patch_refs 为准。",
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "default": []
        },
        "scope_kind": { "enum": ["formal", "temporary"] },
        "affected_refs": {
          "description": "scope_cut 必填：受影响 SSOT/acceptance/testset/ui flow 引用列表。",
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "default": []
        },
        "status": { "enum": ["open", "recorded", "superseded", "closed"] },
        "superseded_by": { "type": "string", "default": "" }
      },
      "allOf": [
        {
          "if": { "properties": { "type": { "const": "scope_cut" } } },
          "then": { "required": ["scope_kind", "affected_refs"], "properties": { "affected_refs": { "minItems": 1 } } }
        },
        {
          "if": { "properties": { "status": { "const": "superseded" } } },
          "then": { "required": ["superseded_by"] }
        }
      ]
    }
  }
}
```

## A.2 `spec-backport-queue.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "lee-lite/spec-backport-queue.schema.json",
  "title": "SpecBackportQueue",
  "type": "object",
  "required": ["artifact_type", "schema_version", "status", "items"],
  "additionalProperties": false,
  "properties": {
    "artifact_type": { "const": "spec_backport_queue" },
    "schema_version": { "type": "string", "minLength": 1 },
    "status": { "enum": ["active", "archived"] },
    "items": {
      "type": "array",
      "items": { "$ref": "#/$defs/item" },
      "default": []
    }
  },
  "$defs": {
    "item": {
      "type": "object",
      "required": ["finding_id", "source_artifact_ref", "trace", "lineage", "priority", "status"],
      "additionalProperties": false,
      "properties": {
        "finding_id": { "type": "string", "minLength": 1 },
        "source_artifact_ref": { "type": "string", "minLength": 1 },
        "trace": {
          "type": "object",
          "required": ["workflow_key", "run_ref"],
          "additionalProperties": true,
          "properties": {
            "workflow_key": { "type": "string", "minLength": 1 },
            "run_ref": { "type": "string", "minLength": 1 }
          }
        },
        "lineage": { "type": "array", "items": { "type": "string", "minLength": 1 }, "minItems": 1 },
        "target_ssot_paths": {
          "description": "plan 字段（不等于证据）。是否回写以 reconcile ssot_patch_refs 为准。",
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "default": []
        },
        "reconcile_report_ref": { "type": "string", "default": "" },
        "owner": { "type": "string", "default": "" },
        "priority": { "enum": ["low", "medium", "high"] },
        "status": { "enum": ["pending", "in_progress", "backported", "rejected", "deferred"] },
        "notes": { "type": "string", "default": "" }
      }
    }
  }
}
```

## A.3 `spec-reconcile-report.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "lee-lite/spec-reconcile-report.schema.json",
  "title": "SpecReconcileReport",
  "type": "object",
  "required": ["artifact_type", "schema_version", "status", "trace", "input_spec_findings_ref", "decisions", "summary"],
  "additionalProperties": false,
  "properties": {
    "artifact_type": { "const": "spec_reconcile_report" },
    "schema_version": { "type": "string", "minLength": 1 },
    "status": { "enum": ["produced"] },
    "trace": {
      "type": "object",
      "required": ["workflow_key", "run_ref"],
      "additionalProperties": true,
      "properties": {
        "workflow_key": { "type": "string", "minLength": 1 },
        "run_ref": { "type": "string", "minLength": 1 }
      }
    },
    "input_spec_findings_ref": { "type": "string", "minLength": 1 },
    "input_queue_ref": { "type": "string", "default": "" },
    "decisions": { "type": "array", "items": { "$ref": "#/$defs/decision" }, "default": [] },
    "summary": {
      "type": "object",
      "required": ["total", "backported", "rejected", "deferred", "recorded"],
      "additionalProperties": false,
      "properties": {
        "total": { "type": "integer", "minimum": 0 },
        "backported": { "type": "integer", "minimum": 0 },
        "rejected": { "type": "integer", "minimum": 0 },
        "deferred": { "type": "integer", "minimum": 0 },
        "recorded": { "type": "integer", "minimum": 0 }
      }
    },
    "blocking_items": { "type": "array", "items": { "type": "string", "minLength": 1 }, "default": [] }
  },
  "$defs": {
    "decision": {
      "type": "object",
      "required": ["finding_id", "type", "outcome", "decided_by"],
      "additionalProperties": false,
      "properties": {
        "finding_id": { "type": "string", "minLength": 1 },
        "type": { "enum": ["spec_gap", "local_assumption", "scope_cut", "execution_decision"] },
        "outcome": { "enum": ["backported", "rejected", "deferred", "recorded"] },
        "decided_by": {
          "type": "object",
          "required": ["role"],
          "additionalProperties": true,
          "properties": { "role": { "type": "string", "minLength": 1 }, "ref": { "type": "string", "default": "" } }
        },
        "scope_kind": { "enum": ["formal", "temporary"] },
        "affected_refs": { "type": "array", "items": { "type": "string", "minLength": 1 }, "default": [] },
        "ssot_patch_refs": {
          "description": "audit evidence（唯一可审计回写证据）。",
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "default": []
        },
        "owner": { "type": "string", "default": "" },
        "rationale": { "type": "string", "default": "" },
        "next_checkpoint": { "type": "string", "default": "" }
      },
      "allOf": [
        { "if": { "properties": { "outcome": { "const": "backported" } } }, "then": { "properties": { "ssot_patch_refs": { "minItems": 1 } } } },
        { "if": { "properties": { "outcome": { "const": "rejected" } } }, "then": { "properties": { "rationale": { "minLength": 1 } } } },
        {
          "if": { "properties": { "outcome": { "const": "deferred" } } },
          "then": { "properties": { "owner": { "minLength": 1 }, "next_checkpoint": { "minLength": 1 } } }
        },
        { "if": { "properties": { "outcome": { "const": "recorded" } } }, "then": { "properties": { "type": { "const": "execution_decision" } } } },
        { "if": { "properties": { "type": { "const": "scope_cut" } } }, "then": { "required": ["scope_kind", "affected_refs"], "properties": { "affected_refs": { "minItems": 1 } } } }
      ]
    }
  }
}
```

---

# 6. 一句话结论

> 执行层可以发现缺口、允许临时补洞，但不能长期持有真相。  
> 新增定义必须分类挂牌，并在收口时清算回流到 SSOT 真相域。

