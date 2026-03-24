# Acceptance Checklist

Use this checklist for manual acceptance of `ll-product-raw-to-src` before any
external gate or handoff materialization.

## Scope

- Skill under test: `ll-product-raw-to-src`
- Workflow key: `product.raw-to-src`
- Output boundary: candidate package only
- Out of scope:
  - `gate-decision.json`
  - `materialized-handoff.json`
  - `materialized-job.json`
  - final freeze into `ssot/src`

## Preconditions

- Run inside `E:\ai\LEE-Lite-skill-first`
- Use a clean temporary repo root with:
  - `ssot/src/`
  - `artifacts/raw-to-src/`
- Use fixtures from `tests/fixtures/raw-to-src/` unless a scenario requires a custom input

## Manual Acceptance Cases

### 1. Smoke Run: Raw Requirement

Command:

```bash
python skills/ll-product-raw-to-src/scripts/raw_to_src.py run --input tests/fixtures/raw-to-src/raw-requirement.md --repo-root <temp-repo> --run-id smoke-raw
```

Pass criteria:

- exit code is `0`
- result `status` is `freeze_ready`
- result `recommended_action` is `next_skill`
- `result-summary.json` sets `recommended_target_skill = product.src-to-epic`
- candidate package exists under `artifacts/raw-to-src/<run_id>/`

### 2. ADR Bridge Run

Command:

```bash
python skills/ll-product-raw-to-src/scripts/raw_to_src.py run --input tests/fixtures/raw-to-src/adr-bridge.yaml --repo-root <temp-repo> --run-id smoke-adr
```

Pass criteria:

- exit code is `0`
- `src-candidate.md` frontmatter contains `source_kind: governance_bridge_src`
- candidate body contains `## Bridge Context`

### 3. Reject Existing SSOT Input

Command:

```bash
python skills/ll-product-raw-to-src/scripts/raw_to_src.py validate-input --input tests/fixtures/raw-to-src/existing-ssot.md
```

Pass criteria:

- exit code is non-zero
- `issues` contains `input_already_ssot`
- normalized `input_type` remains a non-ADR type unless the source explicitly declares ADR semantics

### 4. Duplicate Title Block

Setup:

- create a frozen SRC in `<temp-repo>/ssot/src/` with the same title as the test input

Command:

```bash
python skills/ll-product-raw-to-src/scripts/raw_to_src.py run --input tests/fixtures/raw-to-src/raw-requirement.md --repo-root <temp-repo> --run-id duplicate-case
```

Pass criteria:

- result `status` is `blocked`
- result `recommended_action` is `blocked`
- `handoff-proposal.json` does not exist
- `job-proposal.json` exists
- `defect-list.json` contains `duplicate_title`

### 5. Semantic Retry Proposal

Setup:

- create a raw input whose problem statement drifts into `EPIC` or `FEAT`

Command:

```bash
python skills/ll-product-raw-to-src/scripts/raw_to_src.py run --input <semantic-retry-input> --repo-root <temp-repo> --run-id retry-case
```

Pass criteria:

- result `status` is `retry_proposed`
- result `recommended_action` is `retry`
- `run-state.json` has `current_state = retry_recommended`
- `job-proposal.json` has `job_type = retry`
- `job-proposal.json.retry_budget` matches the semantic retry budget

### 6. Dual-Agent Boundary

Commands:

```bash
python skills/ll-product-raw-to-src/scripts/raw_to_src.py executor-run --input tests/fixtures/raw-to-src/raw-requirement.md --repo-root <temp-repo> --run-id boundary-case
python skills/ll-product-raw-to-src/scripts/raw_to_src.py supervisor-review --artifacts-dir <temp-repo>/artifacts/raw-to-src/boundary-case --repo-root <temp-repo> --run-id boundary-case
```

Pass criteria:

- after `executor-run`, `execution-evidence.json` exists
- after `executor-run`, `supervision-evidence.json` does not exist
- after `executor-run`, `source-semantic-findings.json` does not exist
- after `supervisor-review`, all supervisor-owned artifacts exist

### 7. Output Package Validation

Commands:

```bash
python skills/ll-product-raw-to-src/scripts/raw_to_src.py validate-output --artifacts-dir <artifacts-dir>
python skills/ll-product-raw-to-src/scripts/raw_to_src.py validate-package-readiness --artifacts-dir <artifacts-dir>
python skills/ll-product-raw-to-src/scripts/raw_to_src.py freeze-guard --artifacts-dir <artifacts-dir>
```

Pass criteria:

- all commands return success on a valid package
- `freeze-guard` behaves exactly as the compatibility alias for `validate-package-readiness`

### 8. Unit Regression

Command:

```bash
python -m unittest tests/unit/test_lee_product_raw_to_src.py
```

Pass criteria:

- full suite passes

## Evidence to Review

- `package-manifest.json`
- `result-summary.json`
- `run-state.json`
- `patch-lineage.json`
- `source-semantic-findings.json`
- `acceptance-report.json`
- `retry-budget-report.json`
- `execution-evidence.json`
- `supervision-evidence.json`
- `proposed-next-actions.json`
- `job-proposal.json`
- `handoff-proposal.json` when action is not `blocked`

## Acceptance Decision Rule

Accept the skill only if:

- all required manual cases pass
- no new blocker defects are introduced
- the skill still stops at proposal emission and does not materialize external gate outputs
