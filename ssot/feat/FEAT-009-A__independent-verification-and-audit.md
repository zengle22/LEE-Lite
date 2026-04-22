---
id: FEAT-009-A
ssot_type: FEAT
feat_ref: FEAT-009-A
epic_ref: EPIC-009
title: 独立验证与审计 — Verifier/Bypass/Accident 标准化
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: SRC-009-adr052
candidate_package_ref: artifacts/raw-to-src/SRC-009-adr052
gate_decision_ref: ssot/gates/GATE-EPIC-FEAT-009.json
frozen_at: '2026-04-22T00:00:00+08:00'
---

# 独立验证与审计 — Verifier/Bypass/Accident 标准化

## Goal

定义独立验证层（verifier）和违规检测（bypass-detector），确保 AI 执行可审计，失败取证标准化。

## Scope

- 定义 Verifier 独立认证上下文：不同 API token、不同浏览器 context、不同账号、不同数据快照
- 定义 Verifier 一票否决 Gate 规则（FC-004）
- 定义 bypass-detector 违规检测：检测 AI 跳步、API 直调、误判行为
- 定义 Accident 标准化失败取证包：case_id / manifest / screenshots / traces / network_log / console_log / failure_classification
- 定义 failure-classifier 后处理路由：PRODUCT→回归用例、SCRIPT/ORACLE→Spec 更新、FLAKY→重跑确认

## Acceptance Criteria

- Verifier 有 verdict / confidence / c_layer_verdict / detail 定义
- Verifier 不与 runner 共享上下文（FC-007）
- verifier=fail 时 Gate 必须=fail，不可被 settlement 覆盖（FC-004）
- Accident 包含所有 required_fields
- 8 类故障分类均有后处理路由定义
