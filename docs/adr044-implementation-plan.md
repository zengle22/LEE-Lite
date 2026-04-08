# ADR-044 Implementation Plan（具体实施方案）

## Scope

本计划将 ADR-044 从“文档规则”落到仓库的可执行面（CLI + skills + gate dispatch + runner hold），并优先覆盖 ADR-043 phase-1 的四条主链派生技能：

* `ll-product-epic-to-feat`
* `ll-dev-feat-to-tech`
* `ll-dev-feat-to-proto`
* `ll-dev-proto-to-ui`

同时引入一个 L3 治理 skill（建议新增）：

* `skills/l3/ll-governance-spec-reconcile`（workflow key：`governance.spec-reconcile`）

## Goals

1. 每次执行都产出 `spec-findings.json`（允许空，但语义固定）。
2. 形成仓库级 `spec-backport-queue.json`（可见、可追溯、可延期但不可消失）。
3. dispatch 前必须产出 `spec-reconcile-report.json`，并把 `blocking_items` 变成硬门禁。
4. 将 ADR-044 的三段权威字段关系写入实现：
   - `spec-findings.proposed_ssot_targets` = proposal（不权威）
   - `backport-queue.target_ssot_paths` = plan（不等于已回写）
   - `reconcile-report.ssot_patch_refs` = audit evidence（唯一可审计）
5. 把 `local_assumption` 的“不得放行”规则落到 gate/dispatch hold（影响主流程/状态机/API/验收口径则不得 deferred 放行）。
6. 把 `scope_cut` 结构化字段（`scope_kind` + `affected_refs`）落到 schema + gate/dispatch hold。
7. 把“决策权限模型”落到 reconcile 输出（`decisions[].decided_by.role` 必填）。

## Non-Goals（Phase 1 不做）

* 不尝试自动完成 backport（不自动改 `ssot/` 文件内容）。
* 不引入复杂的多角色审批引擎（先用 `decided_by.role/ref` 做最小审计）。
* 不一次性覆盖所有 skills（先 pilot 再扩展）。

---

## Artifact Layout（落库位置）

### Per-run（随 run 走）

* `artifacts/<workflow>/<run_dir>/spec-findings.json`
* `artifacts/<workflow>/<run_dir>/spec-reconcile-report.json`
* `artifacts/<workflow>/<run_dir>/package-manifest.json` 增加：
  - `spec_findings_ref`
  - `spec_reconcile_report_ref`

### Repo-wide（仓库级队列）

* `artifacts/reports/governance/spec-backport/spec-backport-queue.json`

### Path 规范（P0 必须冻结）

* 所有 `*_ref` 字段默认使用 **repo 相对路径**（例如 `artifacts/...`、`ssot/...`），避免绝对路径导致跨环境不可复现。

---

## Phase 0（准备与冻结接口）

1. 冻结 ADR-044 的 schema 与硬规则（以 `ssot/adr/ADR-044-*.MD` 为准）。
2. 初始化仓库级 queue（空队列也必须存在）：
   - 创建 `artifacts/reports/governance/spec-backport/spec-backport-queue.json` 空骨架。
3. 固化 `impact_areas` 的使用约定（枚举以 ADR-044 附录 A 为准）。
4. 选定 pilot skill：推荐先从 `ll-dev-proto-to-ui` 开始。

**验收**：

* 能用一个空 findings 的 run，产出零项 reconcile report，且不被 dispatch 绕过。

---

## Phase 1（P0：先把闭环跑起来）

### 1) 新增 L3 治理 skill：`ll-governance-spec-reconcile`

**职责**：

* 读取 `spec-findings.json` + 可选 `spec-backport-queue.json`
* 生成 `spec-reconcile-report.json`
* 计算 `blocking_items`（按 ADR-044）
* 可选：`--allow-update` 时更新队列条目状态，并在队列项上回写 `reconcile_report_ref`

**输出关键点**：

* `decisions[].ssot_patch_refs` 是唯一审计证据（backported 必须非空）
* `decisions[].decided_by.role` 必填（对齐 ADR-044 3.8 权限模型）

### 2) CLI 集成：新增 `python -m cli.ll skill spec-reconcile`

参考现有 `failure-capture` 的 CLI 模式：

* 在 `cli/ll.py` 的 `skill` action 列表中加入 `spec-reconcile`
* 在 `cli/commands/skill/command.py` 增加 handler 分支
* 新增 `cli/lib/spec_reconcile_skill.py`（结构仿 `cli/lib/failure_capture_skill.py`）

### 3) Pilot：用 dispatch hold 强制 reconcile（模式 A，推荐 P0）

**选择模式 A 的理由**：

仓库现有 runner 已有稳定的 `auto-continue` vs `hold(waiting-human)` 推进模型；将 ADR-044 enforcement 放在 gate dispatch → downstream job emission，可避免 runner 自动推进时“没人做 reconcile”的结构性冲突。

**集成点**：

* 在 gate dispatch 为下游生成 job 时：
  - 缺 `spec-findings.json` 或缺 `spec-reconcile-report.json` → `waiting-human`
  - 或 `blocking_items` 非空 → `waiting-human`
  - 否则正常生成 `ready` job

**job 字段约定（建议固定）**：

* `status=waiting-human`
* `progression_mode=hold`
* `hold_reason=spec_reconcile_required`
* `required_preconditions` 至少包含 `spec_reconcile_report_ref`

**验收（P0）**：

* `spec_gap(must_backport=true)` 未 backported 或明确 deferred(owner+checkpoint) → reconcile 产 blocking_items → dispatch 必须 hold
* `local_assumption` 命中关键 impact_areas（core_user_flow/state_machine/api_contract/acceptance_testset）→ 不得 deferred 放行
* `scope_cut` 缺 `scope_kind/affected_refs` → blocking → dispatch hold
* 非 `execution_decision` 被 recorded → blocking → dispatch hold

---

## Automation / Runner Integration（P0：自动链路怎么停/怎么续）

本仓库已有稳定的 hold 机制（参见 `docs/guides/adr018-runner-operator-guide.md`）：

* `progression_mode=auto-continue` → `artifacts/jobs/ready/*.json`（runner 自动消费）
* `progression_mode=hold` → `artifacts/jobs/waiting-human/*.json`（等待 operator 释放）

ADR-044 的推荐集成方式是：dispatch 发现缺 reconcile 或存在 blocking 时进入 hold；reconcile 完成后由 operator 释放。

恢复路径：

1. 运行 reconcile（生成 `spec-reconcile-report.json`，并使 `blocking_items=[]`）
2. 使用 gate 或 job 入口释放 hold：
   - `python -m cli.ll gate release-hold --request req.json --response-out resp.json`
   - 或 `python -m cli.ll job release-hold --request req.json --response-out resp.json`

---

## Phase 2（扩展到 ADR-043 phase-1 四技能）

把 Phase 1 的接入模式复制到其余三条技能：

* `ll-product-epic-to-feat`
* `ll-dev-feat-to-tech`
* `ll-dev-feat-to-proto`

每条技能需要完成：

1. run 输出目录中落 `spec-findings.json`（允许空）
2. manifest 写入 `spec_findings_ref`
3. dispatch enforcement：缺 reconcile 或 blocking → hold

---

## Phase 3（工具化与质量门禁）

1. Queue 维护工具化（去重/合并，以 `finding_id` 为主键；输出健康度摘要）
2. must_backport 兜底推断（按 ADR-044 3.4.1 + impact_areas；豁免必须写 `rationale`）
3. 测试：
   - 单元测试：dispatch hold 判定、blocking_items 规则覆盖
   - 回归测试：至少一条 canary run 证明 hold/release 生效

---

## Operator Workflow（实际怎么跑）

1. 运行某个 workflow 产出 candidate（其产物目录必有 `spec-findings.json`）
2. 运行 reconcile（repo CLI carrier 形式）生成 `spec-reconcile-report.json`：

```powershell
python -m cli.ll skill spec-reconcile --request req.json --response-out resp.json --evidence-out evidence.json
```

最小 `req.json`（字段要求以 `cli/lib/protocol.py` 为准；command 必须是 `skill.spec-reconcile`）：

```json
{
  "api_version": "v1",
  "command": "skill.spec-reconcile",
  "request_id": "spec-reconcile-001",
  "workspace_root": "E:/ai/LEE-Lite-skill-first",
  "actor_ref": "operator",
  "trace": { "workflow_key": "governance.spec-reconcile", "run_ref": "spec-reconcile-001" },
  "payload": {
    "package_dir_ref": "artifacts/proto-to-ui/<run_dir>",
    "queue_ref": "artifacts/reports/governance/spec-backport/spec-backport-queue.json",
    "allow_update": true
  }
}
```

> reconcile 的 decision 必须携带 `decisions[].decided_by.role` 并符合 ADR-044 权限模型，否则视为无效 reconcile，不能解除 blocking。

3. 若 `blocking_items` 非空：
   - 选择：回写 SSOT（补 `ssot_patch_refs`）/ 否决（写 `rationale`）/ 延期（写 `owner+next_checkpoint`）
   - 重新 reconcile 直到 `blocking_items` 为空
4. 释放 hold，恢复 runner 自动推进（gate/job release-hold）

---

## Definition of Done（本计划完成的判据）

* ADR-043 phase-1 四技能：findings + reconcile + dispatch-hold 三件套全部落地。
* 队列存在且可追溯：任一 must_backport gap 不会只存在于 prose。
* reconcile 输出可审计：是否回写只看 `ssot_patch_refs`，不会出现三处各记各的口径漂移。

