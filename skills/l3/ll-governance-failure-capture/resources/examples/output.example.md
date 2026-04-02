```text
tests/defect/failure-cases/FC-20260402-103000-IMPL-SRC/
  capture_manifest.json
  failure_case.json
  diagnosis_stub.json
  repair_context.json
```

```json
{
  "artifact_type": "failure_capture_package",
  "schema_version": "0.1.0",
  "status": "captured",
  "workflow_key": "governance.failure-capture",
  "package_kind": "failure_case",
  "package_id": "FC-20260402-103000-IMPL-SRC",
  "triage_level": "P1",
  "skill_id": "dev.tech-to-impl",
  "sku": "impl_spec_builder",
  "run_id": "RUN-20260402-018",
  "artifact_id": "IMPL-SRC-023-004",
  "failure_scope": "artifact",
  "package_dir_ref": "tests/defect/failure-cases/FC-20260402-103000-IMPL-SRC",
  "request_ref": ".local/smoke/failure-capture/request.json",
  "source_refs": [
    ".local/smoke/failure-capture/request.json",
    "artifacts/active/impl/IMPL-SRC-023-004.md",
    "ssot/feat/FEAT-SRC-023-004.md",
    "ssot/tech/TECH-SRC-023-004.md"
  ],
  "evidence_refs": [
    "artifacts/reports/review/impl-review-20260402.json"
  ],
  "files": {
    "capture_manifest_ref": "tests/defect/failure-cases/FC-20260402-103000-IMPL-SRC/capture_manifest.json",
    "failure_case_ref": "tests/defect/failure-cases/FC-20260402-103000-IMPL-SRC/failure_case.json",
    "diagnosis_stub_ref": "tests/defect/failure-cases/FC-20260402-103000-IMPL-SRC/diagnosis_stub.json",
    "repair_context_ref": "tests/defect/failure-cases/FC-20260402-103000-IMPL-SRC/repair_context.json"
  }
}
```
