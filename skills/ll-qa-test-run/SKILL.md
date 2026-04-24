---
name: ll-qa-test-run
description: User-facing CLI skill for executing QA test chains end-to-end. Orchestrates environment provision, spec adaptation, test execution, and manifest update.
version: "1.0"
adr: ADR-054
category: qa
chain: execution
phase: test-run
---

# LL QA Test Run

User-facing CLI skill for running QA test chains end-to-end.

## Input (CLI args)

- `--feat-ref`: feat identifier (API chain)
- `--proto-ref`: prototype identifier (E2E chain)
- `--app-url`: frontend application URL (E2E chain required, default http://localhost:3000)
- `--api-url`: backend API URL (separated architecture)
- `--chain`: execution chain type (`api` | `e2e` | `both`)
- `--coverage-mode`: `smoke` | `qualification`
- `--resume`: resume from last failed run
- `--resume-from <run_id>`: resume from specific run_id

## Output

- Updated `api-coverage-manifest.yaml` or `e2e-coverage-manifest.yaml`
- Execution evidence at `artifacts/active/qa/candidates/`

## Internal Flow

1. `provision_environment()` → ENV file
2. `spec_to_testset()` → SPEC_ADAPTER_COMPAT file
3. `execute_test_exec_skill()` → test execution
4. `update_manifest()` → manifest update with optimistic lock

## Options

- `--resume`: re-run only failed coverage items from last run
- `--chain both`: run both API and E2E chains simultaneously

## CLI Examples

```bash
# API chain
python -m cli skill qa-test-run \
  --feat-ref FEAT-SRC-003-001 \
  --base-url http://localhost:8000 \
  --chain api \
  --coverage-mode smoke

# E2E chain
python -m cli skill qa-test-run \
  --proto-ref PROTOTYPE-001 \
  --app-url http://localhost:3000 \
  --chain e2e \
  --coverage-mode smoke

# Both chains
python -m cli skill qa-test-run \
  --feat-ref FEAT-SRC-003-001 \
  --proto-ref PROTOTYPE-001 \
  --app-url http://localhost:3000 \
  --api-url http://localhost:8000 \
  --chain both \
  --coverage-mode smoke

# Resume from failure
python -m cli skill qa-test-run \
  --feat-ref FEAT-SRC-003-001 \
  --resume \
  --coverage-mode smoke
```
