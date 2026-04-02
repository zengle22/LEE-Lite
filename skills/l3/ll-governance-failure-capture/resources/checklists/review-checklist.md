# Review Checklist

- `P0` / `P1` packages land under `tests/defect/failure-cases/`; `P2` packages land under `tests/defect/issue-log/`.
- The package contains the four required files for its kind.
- `capture_manifest.json` lists canonical refs for every generated file.
- `diagnosis_stub.json` contains only initial classification.
- `repair_context.json` clearly states what may change and what must stay untouched.
- The package references the failure context instead of duplicating large source content.
- No file in the package claims the problem has already been fixed.
