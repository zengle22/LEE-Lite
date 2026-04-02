# Supervisor

Review the emitted verdict package before freeze. Supervision is not a prose summary pass; it is a compliance check against ADR-036.

## Required Checks

1. Verify the main tested object stayed `IMPL`.
2. Verify linked `FEAT / TECH / ARCH / API / UI / TESTSET` refs were treated as authority and not replaced by repo-shape guesses.
3. Verify deep-mode forcing was applied when ADR-036 triggers were present.
4. Verify semantic review, system views, dimension reviews, counterexample results, and review coverage artifacts are all present.
5. Verify logic risk inventory, UX risk inventory, UX improvement inventory, journey simulation, state invariant checks, cross-artifact trace, open questions, and false-negative challenge artifacts are all present when deep mode is used.
6. Verify all 8 dimensions were scored and included in verdict reasoning.
7. Verify hard rules were not weakened:
   - missing implementation touch set / task order -> `block`
   - key failure path without recovery -> `blocking_issue`
   - missing TESTSET coverage for completion + critical failure -> insufficient testability
   - non-blocking UI conflict -> severe design conflict
   - deep-mode high-risk dimension without counterexample -> coverage not sufficient
8. Verify repair routing points back to authoritative upstream artifacts instead of inventing new truth inside the report.
9. If phase2 extended output refs are present, verify they are separately addressable and internally consistent; if absent, verify the package still passes as a legacy baseline run.

## Rejection Criteria

- Reject if the package behaves like lint instead of implementation-readiness pressure testing.
- Reject if verdict, review coverage, and issue inventory disagree.
- Reject if `verdict = pass` while review coverage is insufficient.
- Reject if the package claims deep review but omits user journey, failure-path, UI/API/state mapping, or counterexample evidence.
- Reject if the package claims Phase 2 deep review but omits logic risk, UX risk, UX improvement, or false-negative challenge surfaces.
- Reject if the package reads like a prose summary without machine-readable handoff artifacts.

## Supervisor Output

- Either confirm the package satisfies ADR-036 minimums, or flag the exact violated rule.
- Do not silently downgrade blockers to recommendations.
