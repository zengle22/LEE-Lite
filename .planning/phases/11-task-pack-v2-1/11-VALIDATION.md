---
phase: 11
slug: task-pack-v2-1
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-20
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` (existing) |
| **Quick run command** | `pytest cli/lib/test_task_pack_schema.py cli/lib/test_task_pack_resolver.py -q` |
| **Full suite command** | `pytest cli/lib/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest cli/lib/test_task_pack_schema.py cli/lib/test_task_pack_resolver.py -q`
- **After every plan wave:** Run `pytest cli/lib/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | PACK-01 | — | YAML schema validates valid task pack | unit | `pytest cli/lib/test_task_pack_schema.py::test_valid_pack` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | PACK-01 | — | Rejects pack missing task_id | unit | `pytest cli/lib/test_task_pack_schema.py::test_missing_task_id` | ❌ W0 | ⬜ pending |
| 11-01-03 | 01 | 1 | PACK-01 | — | Rejects pack missing required top-level fields | unit | `pytest cli/lib/test_task_pack_schema.py::test_missing_required_fields` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | PACK-02 | — | Topological sort returns valid execution order | unit | `pytest cli/lib/test_task_pack_resolver.py::test_linear_chain` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 1 | PACK-02 | — | Detects circular dependencies | unit | `pytest cli/lib/test_task_pack_resolver.py::test_cycle_detection` | ❌ W0 | ⬜ pending |
| 11-02-03 | 02 | 2 | PACK-02 | — | Handles diamond dependency graph | unit | `pytest cli/lib/test_task_pack_resolver.py::test_diamond_deps` | ❌ W0 | ⬜ pending |
| 11-03-01 | 03 | 2 | PACK-01 | — | Sample task pack validates + resolves end-to-end | integration | `pytest cli/lib/test_task_pack_resolver.py::test_sample_pack_e2e` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `cli/lib/test_task_pack_schema.py` — stubs for PACK-01
- [ ] `cli/lib/test_task_pack_resolver.py` — stubs for PACK-02
- [ ] pytest already configured in project

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Human-readable YAML schema review | PACK-01 | Schema readability is subjective | Review `ssot/schemas/qa/task_pack.yaml` against ADR-051 spec |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
