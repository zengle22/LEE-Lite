# Input Semantic Checklist

- The request is asking for capture, not repair.
- The reported problem is concrete enough to freeze into a package.
- `triage_level` matches the described risk.
- `failure_scope` is not broader than necessary.
- `failed_artifact_ref`, `upstream_refs`, and `evidence_refs` point to the right context instead of embedding large copied content.
- `suggested_edit_scope` and `do_not_modify` do not conflict.
- `repair_goal` describes the intended stabilization target without asking this skill to implement the fix.
