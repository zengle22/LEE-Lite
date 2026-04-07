---
artifact_type: surface_map_package
workflow_key: dev.feat-to-surface-map
workflow_run_id: manual-surface-map-<run-id>
status: drafted
schema_version: 1.0.0
feat_ref: FEAT-<REF>
surface_map_ref: SURFACE-MAP-FEAT-<REF>
source_refs:
  - FEAT-<REF>
  - EPIC-<REF>
  - SRC-<REF>
  - ADR-040
  - ADR-041
  - ADR-042
---

# Surface Map Package for <FEAT Title>

> 本文档不是新的设计事实源。
> 它的职责是把一个 `FEAT` 映射到已有 shared design assets，并明确这次是 `update` 还是 `create`。
> 后续 `TECH / PROTOTYPE / UI / IMPL` 只能沿本文档已经确认的 owner binding 继续推进。

## Package Semantics

- `artifact_type`: `surface_map_package`
- `workflow_key`: `dev.feat-to-surface-map`
- `authority_scope`: FEAT -> shared design assets ownership mapping
- `default_policy`: update existing shared asset first
- `create_policy`: only when a new long-lived boundary is introduced
- `consumed_by`:
  - `workflow.dev.feat_to_tech`
  - `workflow.dev.feat_to_proto`
  - `workflow.dev.proto_to_ui`
  - `workflow.dev.tech_to_impl`

## Selected FEAT

- feat_ref: `FEAT-<REF>`
- title: `<FEAT title>`
- goal: `<one sentence goal>`
- scope:
  - `<scope item 1>`
  - `<scope item 2>`
- constraints:
  - `<constraint 1>`
  - `<constraint 2>`
- acceptance_checks:
  - scenario: `<scenario name>`
    then: `<expected outcome>`
- source_refs:
  - `FEAT-<REF>`
  - `EPIC-<REF>`
  - `SRC-<REF>`

## Design Impact

- design_impact_required: `true`
- owner_binding_status: `bound | partially_bound | create_required | bypassed`
- bypass_rationale: `N/A`
- create_decision_rule:
  - 只有满足“新增长期责任边界”的 create 条件时，才允许新建 shared asset。
- gate_note:
  - `design_impact_required=true` 且本文档未冻结时，不得进入设计派生与 IMPL。

## Surface Map

### Architecture

- owner: `ARCH-<REF>` or `N/A`
- action: `update | create`
- create_signals:
  - `<required when action=create>`
  - `<required when action=create>`
- scope:
  - `<affected boundary or subsystem>`
  - `<affected state/data/runtime flow>`
- reason: `<why this owner is the correct architecture authority>`

### API

- owner: `API-<REF>` or `N/A`
- action: `update | create`
- create_signals:
  - `<required when action=create>`
  - `<required when action=create>`
- scope:
  - `<affected contract or endpoint family>`
  - `<affected command / query / response surface>`
- reason: `<why this owner is the correct API authority>`

### UI

- owner: `UI-<REF>` or `N/A`
- action: `update | create`
- create_signals:
  - `<required when action=create>`
  - `<required when action=create>`
- scope:
  - `<affected page / panel / shell / information architecture>`
  - `<affected interaction or rendering surface>`
- reason: `<why this owner is the correct UI authority>`

### Prototype

- owner: `PROTO-<REF>` or `N/A`
- action: `update | create`
- create_signals:
  - `<required when action=create>`
  - `<required when action=create>`
- scope:
  - `<affected main journey or state transition>`
  - `<affected skeleton flow or review-visible experience path>`
- reason: `<why this owner is the correct prototype authority>`

### TECH

- owner: `TECH-<REF>` or `N/A`
- action: `update | create`
- create_signals:
  - `<required when action=create>`
  - `<required when action=create>`
- scope:
  - `<affected implementation strategy or execution logic package>`
  - `<affected touch set / state machine / integration strategy>`
- reason: `<why this owner is the correct TECH authority>`

## Ownership Summary

- architecture:
  - `<ARCH-...> = update because ...`
- api:
  - `<API-...> = update because ...`
- ui:
  - `<UI-...> = update because ...`
- prototype:
  - `<PROTO-...> = update because ...`
- tech:
  - `<TECH-...> = create because ...`

## Create Justification

> 只有 `action=create` 的面需要填写本节。
> 建议至少满足以下判定信号中的 2 条：
>
> * 引入新的长期维护 owner
> * 形成新的独立主流程/主页面骨架
> * 形成新的服务域/契约族
> * 形成新的状态机 authority
> * 未来会被多个 FEAT 持续复用

### Architecture Create Justification

- owner: `ARCH-<REF>`
- signals:
  - `<signal 1>`
  - `<signal 2>`
- justification: `<why update existing is no longer sufficient>`

### API Create Justification

- owner: `API-<REF>`
- signals:
  - `<signal 1>`
  - `<signal 2>`
- justification: `<why update existing is no longer sufficient>`

### UI / Prototype / TECH Create Justification

- owner: `<UI|PROTO|TECH-REF>`
- signals:
  - `<signal 1>`
  - `<signal 2>`
- justification: `<why update existing is no longer sufficient>`

## Downstream Handoff

- target_workflows:
  - `workflow.dev.feat_to_tech`
  - `workflow.dev.feat_to_proto`
  - `workflow.dev.proto_to_ui`
  - `workflow.dev.tech_to_impl`
- surface_map_ref: `SURFACE-MAP-FEAT-<REF>`
- feat_ref: `FEAT-<REF>`
- gate_expectations:
  - `TECH / PROTO / UI / IMPL` 必须显式回填 `surface_map_ref`
  - owner/action 必须与本文件一致
  - `IMPL` 不得在实施阶段重新发明 owner

## Reverse Traceability

### From FEAT to Shared Assets

- feat_ref: `FEAT-<REF>`
- related_owner_refs:
  - `ARCH-<REF>`
  - `API-<REF>`
  - `UI-<REF>`
  - `PROTO-<REF>`
  - `TECH-<REF>`

### Expected Reverse Metadata on Shared Assets

- related_feats:
  - `FEAT-<REF>`
- last_updated_by:
  - `FEAT-<REF>`
- open_deltas:
  - `<delta item still pending consolidation>`

## Freeze Checklist

- [ ] `design_impact_required` 已确认
- [ ] 每个受影响设计面都已给出 `owner`
- [ ] 每个设计面都已明确 `action=update|create`
- [ ] 每个设计面都已明确 `scope`
- [ ] 每个设计面都已写出 `reason`
- [ ] 所有 `create` 都已写出 justification
- [ ] `Downstream Handoff` 已明确目标 workflow
- [ ] 反向追踪字段已可由 shared asset 接收

## JSON Projection

```json
{
  "artifact_type": "surface_map_package",
  "workflow_key": "dev.feat-to-surface-map",
  "workflow_run_id": "manual-surface-map-<run-id>",
  "status": "drafted",
  "schema_version": "1.0.0",
  "feat_ref": "FEAT-<REF>",
  "surface_map_ref": "SURFACE-MAP-FEAT-<REF>",
  "selected_feat": {
    "feat_ref": "FEAT-<REF>",
    "title": "<FEAT title>",
    "goal": "<goal>",
    "scope": ["<scope 1>", "<scope 2>"],
    "constraints": ["<constraint 1>", "<constraint 2>"],
    "acceptance_checks": [{"scenario": "<scenario>", "then": "<outcome>"}],
    "source_refs": ["FEAT-<REF>", "EPIC-<REF>", "SRC-<REF>"]
  },
  "design_impact_required": true,
  "surface_map": {
    "design_surfaces": {
      "architecture": [{"owner": "ARCH-<REF>", "action": "update", "scope": ["<scope>"], "reason": "<reason>"}],
      "api": [{"owner": "API-<REF>", "action": "update", "scope": ["<scope>"], "reason": "<reason>"}],
      "ui": [{"owner": "UI-<REF>", "action": "update", "scope": ["<scope>"], "reason": "<reason>"}],
      "prototype": [{"owner": "PROTO-<REF>", "action": "update", "scope": ["<scope>"], "reason": "<reason>"}],
      "tech": [{"owner": "TECH-<REF>", "action": "create", "scope": ["<scope>"], "reason": "<reason>"}]
    },
    "ownership_summary": [
      "ARCH-<REF> update",
      "API-<REF> update",
      "UI-<REF> update",
      "PROTO-<REF> update",
      "TECH-<REF> create"
    ],
    "create_justification_summary": [
      "TECH-<REF> creates a new long-lived execution logic package."
    ],
    "owner_binding_status": "bound",
    "bypass_rationale": null
  },
  "source_refs": ["FEAT-<REF>", "EPIC-<REF>", "SRC-<REF>", "ADR-042"],
  "downstream_handoff": {
    "target_workflows": [
      "workflow.dev.feat_to_tech",
      "workflow.dev.feat_to_proto",
      "workflow.dev.proto_to_ui",
      "workflow.dev.tech_to_impl"
    ],
    "surface_map_ref": "SURFACE-MAP-FEAT-<REF>",
    "feat_ref": "FEAT-<REF>"
  }
}
```
