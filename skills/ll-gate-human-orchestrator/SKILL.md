---
name: ll-gate-human-orchestrator
description: Governed LL workflow skill for orchestrating human gate review over a gate_ready_package, producing authoritative brief, pending-human, decision, dispatch, and approve-auto-materialization outcomes through the mainline gate runtime.
---

# LL Gate Human Orchestrator

This skill is the governed gate workflow for turning one `gate_ready_package` into one authoritative gate decision package. It wraps the real `ll gate evaluate`, `ll gate dispatch`, and `ll gate materialize` runtime surface instead of inventing a parallel gate engine.

## Canonical Authority

- Governing ADRs: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-016-Gate Skill 作为第二会话 Human Gate Orchestrator 的实现基线.MD`, `ADR-015`, `ADR-001`
- Upstream runtime object: `gate_ready_package`
- Primary runtime command: `python skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator.py run --input <gate-ready-dir> --repo-root <repo-root>`
- Real execution surface: `ll gate evaluate`, `ll gate dispatch`, `ll gate materialize`

## Runtime Boundary Baseline

- Classify this gate workflow under `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This skill is the governed `Skill` and `Workflow` wrapper for human gate orchestration. The gate runtime commands are carriers; `Gate` remains the state-advance authority.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept only a governed `gate_ready_package` directory or the canonical `gate-ready-package.json` file.
2. Validate the package structure before issuing any gate decision.
3. Use the mainline gate runtime to build `gate-brief-record`, `gate-pending-human-decision`, and `gate-decision`.
4. Treat `approve` as approval plus immediate materialization on the default runtime path.
5. Always dispatch the authoritative decision after evaluation.
6. Record execution evidence and then require a supervisor pass before freeze.
7. Freeze only after `validate-package-readiness` returns success.

## Human Interaction Rule

- When using `claim-next`, `prepare-round`, or `show-pending`, do not stop at file paths or raw JSON.
- Always surface the approval context directly in the reply:
  - what object is under review
  - what decision is being requested
  - the main focus points
  - the allowed reply formats
- Default behavior: if the runtime returns `human_brief`, render the full markdown inline in the first reply for that pending item.
- Do not ask whether to paste the brief first; paste it by default unless the user explicitly asked for a shorter summary-only mode.
- Do not collapse to only `review_summary` or a short abstract unless the user explicitly asks for a shorter version.
- If the runtime returns `review_summary`, summarize the key fields in plain Chinese before asking for a decision.
- Default the human-facing brief to Chinese unless the user explicitly asks for another language.
- The user should not need to open artifact files just to understand the pending approval item.

## Workflow Boundary

- Input: one `gate_ready_package`
- Output: one `gate_decision_package`
- Out of scope: upstream candidate authoring, FEAT/TECH derivation, and replacing the underlying `ll gate ...` runtime

## Non-Negotiable Rules

- Do not bypass `ll gate evaluate` with handwritten decision files.
- Do not treat human decision actions as runtime states.
- Do not require a second skill for materialization after `approve`.
- Do not accept raw requirements or standalone markdown as gate input.
- Do not self-approve semantic validity without supervisor evidence.
