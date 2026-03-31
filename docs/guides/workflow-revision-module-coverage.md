# Workflow Revision Module Coverage

This note records which LEE Lite governed skills must consume the shared revision module in `cli/lib/workflow_revision.py`, and which skills are intentionally excluded.

## Inclusion Rule

Apply the shared revision module when all of the following are true:

1. The skill regenerates a governed document or package.
2. External gate can return `revise` or `retry` back to that skill.
3. The rerun must preserve `revision-request.json`, `revision_context`, `revision_request_ref`, and `revision_summary` across bundle, manifest, and evidence artifacts.

## Included Skills

| Skill | Workflow key | Current status | Notes |
| --- | --- | --- | --- |
| `ll-product-raw-to-src` | `product.raw-to-src` | included | Uses the shared request/context layer, but keeps its own structural and semantic auto-fix loops plus retry budget logic. |
| `ll-product-src-to-epic` | `product.src-to-epic` | included | Rebuild-style revise flow. |
| `ll-product-epic-to-feat` | `product.epic-to-feat` | included | Rebuild-style revise flow. |
| `ll-dev-feat-to-ui` | `dev.feat-to-ui` | included | Rebuild-style revise flow. |
| `ll-dev-feat-to-tech` | `dev.feat-to-tech` | included | Rebuild-style revise flow. |
| `ll-qa-feat-to-testset` | `qa.feat-to-testset` | included | Rebuild-style revise flow. |
| `ll-dev-tech-to-impl` | `dev.tech-to-impl` | included | Rebuild-style revise flow. |

## Standard Operator Expectation

- First run: use the normal `run` or `executor-run` command.
- Gate revise or retry: rerun the same workflow with `--revision-request <path-to-revision-request.json>`.
- The runtime must materialize `revision-request.json` into the new artifacts directory and propagate a normalized `revision_context` into package JSON, manifests, and evidence.

## Excluded Skills

| Skill | Why excluded |
| --- | --- |
| `ll-project-init` | It is a scaffold materializer with repository side effects, not an external-gate-driven document regeneration chain. |
| `ll-gate-human-orchestrator` | It is the authoritative gate itself, not a downstream consumer of gate return jobs. |
| `ll-test-exec-cli` | It emits execution response envelopes rather than rerunnable authored document packages. |
| `ll-test-exec-web-e2e` | Same exclusion as `ll-test-exec-cli`. |
| `l3/ll-execution-loop-job-runner` | It consumes ready jobs and emits runner envelopes, not governed authored document bundles. |

## Special Case

`ll-product-raw-to-src` is not a pure rebuild-on-revise skill. It now shares the common `revision-request` and `revision_context` contract, but it still owns:

- `patchable` vs `blocking` classification
- minimal structural patching
- semantic patching
- retry-budget enforcement

That behavior must remain local to raw-to-src unless another skill explicitly adopts the same dual-loop repair model.
