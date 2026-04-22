# Plan 12-03 Summary: Gate Schema

**Status:** COMPLETED
**Files delivered:**
- `cli/lib/gate_schema.py` — `GateSchemaError`, `GateVerdict` enum, frozen `Gate` dataclass, `validate()`, `validate_file()`, CLI
- `ssot/schemas/qa/gate.yaml` — External YAML schema with 4-verdict enum + forbidden field list
- `tests/cli/lib/test_gate_schema.py` — 21 tests covering all 4 verdicts, forbidden fields, file I/O, defaults, frozen

**Key decisions:**
- 4-verdict enum: pass, conditional_pass, fail, provisional_pass
- Forbidden field: `hidden_verifier_failure`
- `skip` verdict explicitly rejected (not a valid verdict)

**Test results:** 21/21 passing
