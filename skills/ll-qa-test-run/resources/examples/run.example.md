# ll-qa-test-run Example

## API Chain Execution

```bash
# Run API test chain for FEAT-SRC-003-001
python -m cli skill qa-test-run \
  --feat-ref FEAT-SRC-003-001 \
  --base-url http://localhost:8000 \
  --chain api \
  --coverage-mode smoke
```

Expected output:
```
Run completed: run_id=RUN-20260424-ABC12345
Executed: 15 test cases
Manifest updated: 15 items
```

## E2E Chain Execution

```bash
# Run E2E test chain for PROTOTYPE-001
python -m cli skill qa-test-run \
  --proto-ref PROTOTYPE-001 \
  --app-url http://localhost:3000 \
  --chain e2e \
  --coverage-mode smoke
```

## Both Chains Execution

```bash
# Run both API and E2E chains
python -m cli skill qa-test-run \
  --feat-ref FEAT-SRC-003-001 \
  --proto-ref PROTOTYPE-001 \
  --app-url http://localhost:3000 \
  --api-url http://localhost:8000 \
  --chain both \
  --coverage-mode smoke
```

## Resume from Failure

```bash
# Resume from last failed run
python -m cli skill qa-test-run \
  --feat-ref FEAT-SRC-003-001 \
  --resume \
  --coverage-mode smoke
```

## Output Artifacts

After execution, the following artifacts are created/updated:

1. **Environment file**: `ssot/environments/ENV-{id}.yaml`
2. **SPEC_ADAPTER_COMPAT file**: `ssot/tests/.spec-adapter/{id}.yaml`
3. **Updated manifest**: `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml`
4. **Candidate evidence**: `artifacts/active/qa/candidates/{slug}.json`
