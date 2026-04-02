---
name: ll-qa-impl-spec-test
description: Governed implementation-readiness testing skill for evaluating a frozen IMPL package plus linked FEAT/TECH/ARCH/API/UI/TESTSET authorities before implementation start, then emitting a structured verdict package and gate handoff refs.
---

# Impl Spec Test

This is the formal governed skill wrapper for ADR-036. It does not replace an external gate. It routes into the canonical workspace runtime at `python -m cli skill impl-spec-test`.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-036-IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线.MD`
- Primary object: `qa.impl-spec-test`
- Canonical runtime command: `python -m cli skill impl-spec-test --request <request.json> --response-out <response.json>`
- Canonical runtime carrier: `E:\ai\LEE-Lite-skill-first\cli\lib\impl_spec_test_runtime.py`
- Required working directory: repository root `E:\ai\LEE-Lite-skill-first`

## Runtime Boundary Baseline

- Classify this skill against `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This bundle is a governed `Skill` wrapper around one canonical runtime carrier. The request/response envelopes are artifacts and evidence carriers; the CLI implementation remains carrier, not skill authority.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept one structured `impl_spec_test_skill_request` envelope for `skill.impl-spec-test`.
2. Treat `IMPL` as the main tested object and linked FEAT / TECH / ARCH / API / UI / TESTSET refs as authority inputs, not background prose.
3. Support `quick_preflight` and `deep_spec_testing`, but force deep mode when ADR-036 triggers are present:
   - `migration_required`
   - canonical field / ownership / state-boundary sensitivity
   - cross-surface main chain plus post-chain augmentation
   - newly introduced `UI / API / state` surface
   - external gate candidate
4. Build the ADR-036 semantic review and required system views:
   - functional chain
   - user journey
   - state/data relationships
   - UI/API/state mapping
5. In deep mode, execute all 8 dimensions plus the Phase 2 deep-review surfaces:
   - logic risk inventory
   - UX risk inventory
   - UX improvement inventory
   - journey simulation
   - state invariant checks
   - cross-artifact trace
   - open questions
   - false-negative challenge
6. In deep mode, execute the counterexample families required by ADR-036.
7. If `review_profile` is present, use it only as deep-review steering for personas, focus areas, and counterexample families.
8. Detect cross-artifact conflicts, missing authority gaps, failure-path gaps, UX friction, and counterexample coverage gaps without inventing new business truth or design truth.
9. Emit a structured implementation-readiness verdict package plus an implementation-readiness gate subject.
10. Handoff the governed candidate to downstream gate review instead of self-approving implementation start.

## Workflow Boundary

- Input: one governed request envelope that references a frozen IMPL package and linked authority refs.
- Output: one governed response envelope for `skill.impl-spec-test`; `response.data` carries verdict fields, package refs, and handoff refs.
- Downstream handoff: mainline gate queue via the runtime-produced `handoff_ref`.
- Out of scope: replacing an external gate, running code-quality execution tests, or authoring new upstream truth.

## Non-Negotiable Rules

- Do not demote `qa.impl-spec-test` into a prose-only review summary.
- Do not bypass `python -m cli skill impl-spec-test` with hand-written response envelopes.
- Do not rewrite FEAT / TECH / ARCH / API / UI / TESTSET truth inside this workflow.
- Do not automatically dispatch coder work when the verdict is `pass_with_revisions` or `block`.
- Do not return `verdict = pass` when review coverage is insufficient in deep mode.
- Do not treat `review_coverage.status = partial` as a clean pass.
- Do not weaken ADR-036 hard rules around implementation executability, failure recovery, TESTSET coverage, or non-blocking UI conflicts.
- Do not require phase2 extended output refs for legacy baseline runs; validate them when present.
