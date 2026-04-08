# ADR-044 Spec Reconcile Operator Guide（运行手册）

本文档把 ADR-044 的 **spec-findings / backport-queue / reconcile-report** 三件套落到“怎么跑”的操作面，适用于：

* gate approve 后发现下游 job 被 hold（`waiting-human`）
* 需要补齐 `spec-reconcile-report.json` 才能继续 runner 自动推进

> 关键点：是否回写 SSOT 只看 `spec-reconcile-report.json.decisions[].ssot_patch_refs`（审计证据）。  
> `spec-findings.json.proposed_ssot_targets` 只是建议；`spec-backport-queue.json.items[].target_ssot_paths` 只是计划。

---

## 1) 你会看到什么现象

当下游派生被 ADR-044 门禁阻断时，会出现：

* job 文件落在 `artifacts/jobs/waiting-human/*.json`
* job payload 至少包含：
  * `status: waiting-human`
  * `hold_reason: spec_reconcile_required`
  * `required_preconditions: ["artifacts/<...>/spec-reconcile-report.json"]`

---

## 2) 先定位被 hold 的 job

用 CLI 看 waiting-human 队列：

```powershell
python -m cli.ll loop show-backlog --request <req.json> --response-out <resp.json>
```

或直接列目录：

```powershell
dir artifacts/jobs/waiting-human
```

打开 job JSON 后，找：

* `source_package_ref`（原始 package dir）
* `required_preconditions[0]`（通常就是 reconcile report 的路径）

---

## 3) 运行 spec-reconcile（生成 reconcile report）

### 3.1 最小 request（零 findings 也必须产出）

创建 `req.spec-reconcile.json`：

```json
{
  "api_version": "v1",
  "command": "skill.spec-reconcile",
  "request_id": "spec-reconcile-001",
  "workspace_root": "E:/ai/LEE-Lite-skill-first",
  "actor_ref": "operator",
  "trace": { "workflow_key": "governance.spec-reconcile", "run_ref": "spec-reconcile-001" },
  "payload": {
    "package_dir_ref": "artifacts/epic-to-feat/<run_id>",
    "queue_ref": "artifacts/reports/governance/spec-backport/spec-backport-queue.json",
    "allow_update": true,
    "decisions": []
  }
}
```

运行：

```powershell
python -m cli.ll skill spec-reconcile --request req.spec-reconcile.json --response-out resp.spec-reconcile.json --evidence-out evidence.spec-reconcile.json
```

输出：

* `artifacts/<package_dir_ref>/spec-reconcile-report.json`
* 可选：回写 `package-manifest.json.spec_reconcile_report_ref`
* 可选：把 must_backport 的 finding 入队到 `spec-backport-queue.json`（允许 queue 为空，但不能缺失）

### 3.2 decisions 的写法（必须满足 ADR-044 约束）

`decisions[]` 每个元素至少包含：

* `finding_id`
* `type`
* `outcome`（`backported|rejected|deferred|recorded`）
* `decided_by.role`（对应 ADR-044 权限模型）

常见 outcome 的硬约束：

* `backported` → `ssot_patch_refs` 必须非空
* `rejected` → `rationale` 必须非空
* `deferred` → `owner` + `next_checkpoint` 必须非空
* `recorded` → 只允许 `execution_decision`
* `scope_cut` → 必须有 `scope_kind` + `affected_refs`（且 affected_refs 非空）
* `local_assumption` 且 impact 命中关键域（core_user_flow/state_machine/api_contract/acceptance_testset）→ 不允许 `deferred` 放行

### 3.3 reconcile-as-apply（可选：自然语义 `ssot_updates` 自动回写 SSOT）

当你希望 reconcile 同时完成 “回写 SSOT + 产出审计证据 + 解除 hold”，可在 payload 中加入：

* `decided_by`（至少包含 `role`）
* `ssot_updates`（按 finding_id 分段的文本）
* `auto_release_holds: true`（可选：report 无 blocking 时自动释放等待该 report 的 hold jobs）

`ssot_updates` 的机械化解析要点：

* 每段必须显式引用 `finding_id`（例如 `GAP-104:`）
* `path: ssot/...` 可以省略：若能从 queue/findings 推断出唯一落点文件则自动选择；否则会拒绝并要求显式给 path
* 支持 `yaml-patch`：使用 ```yaml-patch 内容块会以 deep-merge 方式补丁 YAML（适合“补字段/改默认值”，无需整文件替换）

---

## 4) 解除 hold，恢复 runner 自动推进

当 reconcile report 已产出且 `blocking_items=[]`，就可以释放 hold job：

```powershell
python -m cli.ll gate release-hold --request <req.json> --response-out <resp.json>
```

或直接对 job 释放：

```powershell
python -m cli.ll job release-hold --request <req.json> --response-out <resp.json>
```

> `release-hold` 会校验 `required_preconditions` 指向的文件是否存在；当 `hold_reason=spec_reconcile_required` 时，会强制 `spec-reconcile-report.json` 存在且 `blocking_items=[]`，否则拒绝释放（避免“先放行、后补 reconcile”）。
