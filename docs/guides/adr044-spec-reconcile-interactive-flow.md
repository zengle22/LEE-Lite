# ADR-044 Spec Reconcile（交互式：自然语义/PRD → reconcile-as-apply）

本指南描述一种“**用户在 Codex/Claude Code 中交互式调用**”的落地方式：

* 用户输入自然语言或粘贴 PRD/评审结论
* LLM（交互态）负责解析与结构化
* 由 LLM 调用仓库 CLI：`python -m cli.ll skill spec-reconcile ...`
* 产出审计证据（patch receipt + reconcile report），并可选自动释放 hold jobs

> 说明：仓库内的 `skills/**/scripts/*.py` 是 deterministic runtime，不自带 LLM 推理能力。  
> 交互态“自然语义 → 结构化 patch”由 Codex/Claude Code 的 LLM 完成，然后再交给 CLI 落库与门禁校验。

---

## 1) 你需要准备的输入

必填：

* `package_dir_ref`：例如 `artifacts/feat-to-tech/run-73`
* `decided_by`：例如 `{"role":"ssot_owner","ref":"alice"}`
* 自然语义更新意图（或 PRD/评审结论）

推荐：

* `auto_release_holds: true`：当 report 无阻断时自动释放关联的 hold jobs。

---

## 2) `ssot_updates` 的结构化格式（LLM 输出给 CLI）

每个 finding 一段，最小块结构：

```text
GAP-104:
（自然语言说明...）
path: ssot/api_contract/API-011.yaml   # 可选
```yaml-patch
error_codes:
  E_FOO: "..."
```
```

规则：

* `finding_id` 必须显式出现（例如 `GAP-104:`）
* fenced content 必须存在
* `path: ssot/...` 可以省略：若能从 queue/findings 推断到唯一 SSOT 文件落点则自动选择；否则会拒绝并要求显式给 path
* 优先用 ```yaml-patch 做 deep-merge（补字段/改默认值），避免整文件替换

---

## 3) 生成 reconcile request 并执行

注意：`skill.spec-reconcile` 已启用 `ll.contract.yaml` 校验，且 `forbid_extra: true`，payload 不能带多余字段。

最小 request 示例：

```json
{
  "api_version": "v1",
  "command": "skill.spec-reconcile",
  "request_id": "spec-reconcile-001",
  "workspace_root": "E:/ai/LEE-Lite-skill-first",
  "actor_ref": "operator",
  "trace": { "workflow_key": "governance.spec-reconcile", "run_ref": "spec-reconcile-001" },
  "payload": {
    "package_dir_ref": "artifacts/feat-to-tech/run-73",
    "queue_ref": "artifacts/reports/governance/spec-backport/spec-backport-queue.json",
    "allow_update": true,
    "decided_by": { "role": "ssot_owner", "ref": "alice" },
    "decisions": [],
    "ssot_updates": "GAP-104:\\n```yaml-patch\\n...\\n```\\n",
    "auto_release_holds": true
  }
}
```

执行：

```powershell
python -m cli.ll skill spec-reconcile --request req.spec-reconcile.json --response-out resp.spec-reconcile.json --evidence-out evidence.spec-reconcile.json
```

---

## 4) 成功判据（与门禁一致）

* `artifacts/<package_dir_ref>/spec-reconcile-report.json.blocking_items=[]`
* 若发生回写：对应 `decisions[].ssot_patch_refs` 非空（指向 patch receipt）
* 若启用 `auto_release_holds`：相关 job 从 `artifacts/jobs/waiting-human` 自动进入 `artifacts/jobs/ready`

