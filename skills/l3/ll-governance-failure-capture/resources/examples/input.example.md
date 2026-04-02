```json
{
  "artifact_type": "failure_capture_request",
  "schema_version": "0.1.0",
  "status": "triaged",
  "skill_id": "dev.tech-to-impl",
  "sku": "impl_spec_builder",
  "run_id": "RUN-20260402-018",
  "artifact_id": "IMPL-SRC-023-004",
  "failure_scope": "artifact",
  "detected_stage": "human_final_review",
  "detected_by": "reviewer.le.zeng",
  "severity": "high",
  "triage_level": "P1",
  "symptom_summary": "implements relation is bound to the wrong FEAT object",
  "problem_description": "The generated IMPL points to FEAT-SRC-023-003 instead of FEAT-SRC-023-004, which would misroute downstream execution and test coverage.",
  "failed_artifact_ref": "artifacts/active/impl/IMPL-SRC-023-004.md",
  "upstream_refs": [
    "ssot/feat/FEAT-SRC-023-004.md",
    "ssot/tech/TECH-SRC-023-004.md"
  ],
  "evidence_refs": [
    "artifacts/reports/review/impl-review-20260402.json"
  ],
  "suggested_edit_scope": [
    "artifacts/active/impl/IMPL-SRC-023-004.md#traceability"
  ],
  "do_not_modify": [
    "artifacts/active/impl/IMPL-SRC-023-004.md#task-breakdown",
    "artifacts/active/impl/IMPL-SRC-023-004.md#acceptance"
  ],
  "repair_goal": "Correct the FEAT binding without changing unrelated implementation instructions."
}
```
