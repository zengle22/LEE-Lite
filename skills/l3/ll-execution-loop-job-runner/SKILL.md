---
name: ll-execution-loop-job-runner
description: Governed execution-runner skill for starting or resuming the ready-job loop through the canonical workspace runtime without turning repo CLI carrier commands into skill authority.
---

# LL Execution Loop Job Runner

This is the canonical governed skill bundle for the Execution Loop Job Runner. It is the user-facing skill authority for Claude/Codex. It does not create a second runner. It routes into the canonical workspace carrier at `ll loop run-execution` and `ll loop resume-execution`.

## Canonical Authority

- Governing ADRs: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-018-Execution Loop Job Runner 作为自动推进运行时.MD`, `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-020-标准 Skill 实现、Adapter 安装与 CLI 边界基线.MD`
- FEAT: `E:\ai\LEE-Lite-skill-first\ssot\feat\FEAT-SRC-003-002__runner-用户入口流.md`
- Canonical runtime command: `python skills/l3/ll-execution-loop-job-runner/scripts/runner_operator_entry.py invoke --request <request.json> --response-out <response.json>`
- Real execution carrier: `python -m cli.ll loop run-execution --request <request.json> --response-out <response.json>`
- Real resume carrier: `python -m cli.ll loop resume-execution --request <request.json> --response-out <response.json>`

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept one `skill.execution-loop-job-runner` request envelope.
2. Require `payload.runner_scope_ref` and explicit `payload.entry_mode` of `start` or `resume`.
3. Route `start` to `ll loop run-execution` and `resume` to `ll loop resume-execution`.
4. Preserve the authoritative runner context, runner run ref, and entry receipt produced by the loop carrier.
5. Return a skill-scoped response envelope that points back to the delegated loop command and emitted runner artifacts.
6. Do not ask the operator to relay downstream skills manually.

## Workflow Boundary

- Input: one governed runner entry request
- Output: one governed runner entry response with runner context, receipt, and post-run snapshot refs
- Downstream handoff: execution runner queue consumption via the loop carrier
- Out of scope: direct job claim/run/fail verbs as user-facing skill authority, inventing a second runner implementation, and mutating queue state outside the canonical loop carrier

## Non-Negotiable Rules

- Do not replace the canonical skill with `ll skill execution-loop-job-runner`.
- Do not bypass the loop carrier with handwritten runner receipts or response files.
- Do not turn the skill into a manual dispatcher for downstream workflow skills.
