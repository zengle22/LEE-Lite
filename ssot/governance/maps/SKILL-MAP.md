# Skill Map

Purpose: route a task to the smallest canonical skill context. Canonical skill authority lives only under `skills/`.

Do not treat agent, Claude, or Cursor skill adapter surfaces as authority. Those are install or projection targets unless a registry entry explicitly says otherwise.

## Product Pipeline

| Task | Load |
| --- | --- |
| Raw requirement, ADR, or opportunity to SRC candidate | `skills/ll-product-raw-to-src/SKILL.md` |
| SRC candidate to EPIC freeze package | `skills/ll-product-src-to-epic/SKILL.md` |
| EPIC freeze package to FEAT freeze package | `skills/ll-product-epic-to-feat/SKILL.md` |

## Development Pipeline

| Task | Load |
| --- | --- |
| FEAT to surface ownership map | `skills/ll-dev-feat-to-surface-map/SKILL.md` |
| FEAT to prototype | `skills/ll-dev-feat-to-proto/SKILL.md` |
| Prototype to UI spec | `skills/ll-dev-proto-to-ui/SKILL.md` |
| FEAT to TECH design | `skills/ll-dev-feat-to-tech/SKILL.md` |
| TECH to IMPL package | `skills/ll-dev-tech-to-impl/SKILL.md` |

## QA Pipeline

| Task | Load |
| --- | --- |
| IMPL readiness review | `skills/ll-qa-impl-spec-test/SKILL.md` |
| FEAT to API plan | `skills/ll-qa-feat-to-apiplan/SKILL.md` |
| API plan to API spec | `skills/ll-qa-api-spec-gen/SKILL.md` |
| API spec to API manifest | `skills/ll-qa-api-manifest-init/SKILL.md` |
| Prototype to E2E plan | `skills/ll-qa-prototype-to-e2eplan/SKILL.md` |
| E2E plan to E2E spec | `skills/ll-qa-e2e-spec-gen/SKILL.md` |
| E2E spec to E2E manifest | `skills/ll-qa-e2e-manifest-init/SKILL.md` |
| Governed test run | `skills/ll-qa-test-run/SKILL.md` |
| Test settlement | `skills/ll-qa-settlement/SKILL.md` |
| Release gate input evaluation | `skills/ll-qa-gate-evaluate/SKILL.md` |
| Render testset human view | `skills/render-testset-view/SKILL.md` |

## Governance and Meta

| Task | Load |
| --- | --- |
| FRZ validate, freeze, list, extract | `skills/ll-frz-manage/SKILL.md` |
| Capture experience patch | `skills/ll-patch-capture/SKILL.md` |
| Settle minor experience patch | `skills/ll-experience-patch-settle/SKILL.md` |
| Human gate orchestration | `skills/ll-gate-human-orchestrator/SKILL.md` |
| Create or revise governed skill | `skills/ll-meta-skill-creator/SKILL.md` |
| Install canonical skill to adapter surface | `skills/ll-skill-install/SKILL.md` |
| Initialize LEE Lite project | `skills/ll-project-init/SKILL.md` |

## L3 and Experimental

| Task | Load |
| --- | --- |
| Execution loop job runner | `skills/l3/ll-execution-loop-job-runner/SKILL.md` |
| Governance failure capture | `skills/l3/ll-governance-failure-capture/SKILL.md` |
| Governance spec reconcile | `skills/l3/ll-governance-spec-reconcile/SKILL.md` |

## Execution Rule

After loading a selected `SKILL.md`, follow its Required Read Order. Do not load sibling skills unless the selected skill explicitly routes there or the user task spans that boundary.
