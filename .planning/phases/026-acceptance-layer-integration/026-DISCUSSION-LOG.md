# Phase 26: 验收层集成 - Discussion Log

## Discussion: 2026-04-29

**Participants:** You, Claude

---

## Gray Area 1: Draft Phase 存储策略

**Question:** Gate FAIL 后生成的 draft phase 应该存在哪里？
- **A:** 内存中，不持久化（每次 `ll-bug-remediate` 重新生成）
- **B:** 持久化到 `artifacts/bugs/{feat_ref}/draft-phase.yaml`
- **C:** 持久化到 `.planning/phases/026-draft-{bug_id}/` 但标记为 `draft=true`

**Discussion:** 用户同意推荐方案 A。

**Decision:** **A** — Draft phase 存储在内存中，不持久化。每次 `ll-bug-remediate` 重新生成。简单，MVP 范围最小。

---

## Gray Area 2: T+4h 提醒实现方式

**Question:** 如何实现 T+4h 提醒？
- **A:** 不实现（MVP 仅 gate FAIL 时终端通知一次）
- **B:** 用 `at` 命令或 cron 调度（但跨平台兼容问题）
- **C:** 下次运行任何 `ll-*` 命令时检查是否有过期 draft 并提醒

**Discussion:** 用户同意推荐方案 A + C。

**Decision:** **A + C** — MVP 仅 gate FAIL 时终端通知一次，同时下次运行任何 `ll-*` 命令时检查是否有未处理的 open bug 并提醒。T+4h 精确提醒延后到 v2。

---

## Gray Area 3: `ll-bug-remediate` 的交互流程

**Question:** 开发者运行 `ll-bug-remediate --feat-ref {ref}` 后应该看到什么？
- **A:** 列出所有 open bug，输入序号选择，逐个生成 phase
- **B:** 默认单 bug 单 phase，自动选择最老的 open bug
- **C:** 显示所有 open bug，默认全选（mini-batch），支持 `--exclude {id}` 排除

**Discussion:** 用户同意推荐方案 C。

**Decision:** **C** — 显示所有 open bug，默认全选（mini-batch，max 2-3），支持 `--exclude {id}` 排除。符合 ADR-055 §2.4 的 mini-batch 策略。

---

## Gray Area 4: Settlement 消费 bug 注册表的时机

**Question:** Settlement 应该什么时候读取 bug-registry？
- **A:** 每次运行都读取，用于 gap 分析（如"这个 gap 上次是 test_defect，这次是 code_defect"）
- **B:** 仅在 gate-evaluate 调用时读取，settlement 本身不读取
- **C:** 可选读取，通过 `--with-bug-registry` flag 控制

**Discussion:** 用户同意推荐方案 B。

**Decision:** **B** — 仅在 gate-evaluate 调用时读取 bug-registry，settlement 本身不读取。职责清晰，MVP 范围最小。

---

## Gray Area 5: Bug Associations 的契约格式

**Question:** `release_gate_input.yaml` 中的 `bug_associations` 应该是什么格式？
- **A:** `{case_id: bug_id}` 简单 mapping
- **B:** `{case_id: {bug_id, status, gap_type}}` 更丰富的信息
- **C:** `[{case_id, bug_id, status, gap_type}]` 数组格式

**Discussion:** 用户同意推荐方案 B。

**Decision:** **B** — `{case_id: {bug_id, status, gap_type}}` 嵌套对象格式。信息丰富，未来扩展性好，符合 ADR-055 §2.3 的完整信息原则。

---

## Other Discussion Points

**Discussion:** None. All gray areas resolved with user's agreement to recommended options.

---

## Summary

All 5 gray areas have been resolved:
1. ✅ Draft Phase 存储策略：内存中，不持久化（Option A）
2. ✅ T+4h 提醒：仅 gate FAIL 时终端通知 + 下次运行 `ll-*` 时检查（Option A + C）
3. ✅ `ll-bug-remediate` 交互：mini-batch 默认全选，支持 `--exclude`（Option C）
4. ✅ Settlement 消费 bug-registry：仅 gate-evaluate 读取（Option B）
5. ✅ Bug associations 契约：嵌套对象格式（Option B）

**Status:** Discussion complete! Ready for research and planning.

---

## Action Items

- [ ] Run `/gsd-research-phase 26` to gather codebase insights
- [ ] Run `/gsd-plan-phase 26` to create implementation plans

---

*Last updated: 2026-04-29*
