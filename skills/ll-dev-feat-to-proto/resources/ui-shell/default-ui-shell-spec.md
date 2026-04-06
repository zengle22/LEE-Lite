# UI Shell Source

- ui_shell_source_id: UI-SHELL-RUNNING-COACH-001
- ui_shell_family: running-coach-mvp-shell
- ui_shell_version: 1.0.0
- shell_change_policy: governance-only

## App Shell

- The shell is organized around one daily coaching workspace, not a generic feature dashboard.
- Stable shell regions are `journey_rail`, `coach_mobile_shell`, and `authority_insight_rail`.
- Primary journey families stay fixed across prototype bundles: `setup_wizard`, `today_home`, `pre_run_decision`, `plan_review`, and `post_run_feedback`.
- The top shell header always reminds the user of the product promise: injury-first, PB-second, and today's decision over blind execution.
- Athlete identity, cycle context, and today's next recommended session live in the shell header rather than being redefined page by page.
- Local back behavior returns to the relevant shell family root, while leaving the active daily flow routes back to `today_home`.

## Container Rules

- Use `page` for setup wizard progression, today home, full pre-run decision, and plan detail views that require full-screen focus.
- Use `bottom_sheet` for scoped drill-ins such as risk reasons, fatigue details, swap-session options, and post-run quick capture.
- Use `modal` only for explicit overrides such as ignoring a blocked recommendation, resetting setup, or confirming plan regeneration.
- Use `inline_banner` for non-blocking readiness warnings, sync lag, or degraded-but-runnable recommendations.
- When risk level escalates from caution to stop, the shell upgrades from `inline_banner` to a full blocking `page` or explicit `modal`.

## CTA Placement

- Setup wizard uses one sticky bottom CTA rail with a dominant forward action and one clearly subordinate back or skip action.
- Today home keeps one dominant decision CTA above the fold: start pre-run check, follow today's recommendation, or review the adjusted session.
- Pre-run decision surfaces exactly one recommended action at a time: follow plan, downgrade, swap, or rest.
- Plan review and post-run feedback use anchored CTA docks so the user always knows how to commit today's decision or complete today's feedback.
- Danger or override actions stay visually separated from the recommended training path.

## State Expression

- `blocked` means stop the planned workout and route the runner to recovery, downgrade, or coach review with explicit reason chips.
- `degraded` means training can continue with reduced scope, lower intensity, or a substituted session; the shell must explain what changed and why.
- `ready` or `pass` means today's planned session can proceed with lightweight reassurance and minimal interruption.
- Loading, disabled, validation, and error states all preserve the same shell hierarchy: readiness banner first, decision card second, CTA dock last.
- Risk language must stay operational and actionable, never motivational-only.

## Common Structural Components

- coach header with athlete snapshot, current cycle, and today's training focus
- journey rail for setup, today, decision, plan, and review stages
- daily readiness banner with state tone and short explanation
- coach decision card with recommendation, why-now rationale, and risk chips
- weekly plan strip or next-session block
- risk detail container for pain, fatigue, or overload reasons
- fixed CTA dock anchored to the bottom of the active screen
- post-run quick feedback entry point that can open as `bottom_sheet`
- authority panel that exposes journey and shell references for downstream prototype and UI work

## Governance

- This document is the running coach MVP UI Shell Source authority, not a per-feature drafting surface.
- Feature runs may snapshot this source into `ui-shell-spec.md`, but must not silently redefine shell families, CTA placement rules, or risk-state behavior.
- Journey artifacts define flow semantics; this shell defines the cross-page frame, container family, and state expression rules that carry those semantics.
- Shell changes require explicit governance review rather than feature-local edits.
