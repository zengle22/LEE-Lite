# Phase 2: Patch 登记 Skill - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 02-patch-skill
**Areas discussed:** Skill structure, interaction flow, classification automation, Document-to-SRC path, skill naming

---

## Skill Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Follow ll-* governed pattern | SKILL.md + executor + supervisor + contracts | ✓ |
| Simpler Claude Code skill format | Just SKILL.md + executor | |

**User's choice:** Follow existing `ll-*` governed pattern
**Notes:** All 29 existing skills use this pattern; consistency matters for Phase 3+

## Interaction Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Step-by-step interactive Q&A | Ask user each field one by one | |
| Two-step: AI draft → user confirm table | AI pre-fills, user reviews table | |
| Three-step: AI draft → Supervisor → auto入库 (human only if needed) | AI → Supervisor Agent审核 → 默认全自动 | ✓ |

**User's choice:** Three-step with Supervisor Agent
**Notes:** User said "2和3用户参与过多了" — wants minimal human involvement. Supervisor Agent审核 first, escalate only when necessary.

## Classification Automation

| Option | Description | Selected |
|--------|-------------|----------|
| User picks each classification | Interactive selection for change_class etc | |
| AI pre-fills + user reviews table | AI fills everything, user confirms | |
| AI pre-fills + Supervisor审核 → auto unless flagged | Full automation, human only on escalation | ✓ |

**User's choice:** AI pre-fills all fields, Supervisor审核 auto-passes unless escalation conditions met
**Notes:** Escalation triggers: schema failure, low confidence, conflict detected, semantic patch, first patch for FEAT, contested test_impact

## Document-to-SRC Path

| Option | Description | Selected |
|--------|-------------|----------|
| Implement SRC generation in this skill | Full Document-to-SRC logic | |
| Delegate to existing ll-product-raw-to-src | Routing +关联 Patch only | ✓ |

**User's choice:** Delegate to `ll-product-raw-to-src`, this skill only handles routing and关联 Patch

## Skill Naming

| Option | Description | Selected |
|--------|-------------|----------|
| ll-experience-patch-register | Original name | |
| ll-patch-capture | Shorter, action-oriented | ✓ |
| ll-experience-patch-create | Accurate but long | |
| ll-prompt-to-patch | Matches ADR path name | |

**User's choice:** `ll-patch-capture`

---

## Claude's Discretion

- Executor prompt specific wording
- Supervisor checklist granularity
- Confidence threshold values for change_class
- Whether ll.lifecycle.yaml needed in this phase
