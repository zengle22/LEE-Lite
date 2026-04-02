# Authoring Checklist

- Use this skill only after a real problem has been detected.
- Supply the failing artifact ref and at least one upstream ref.
- Set `triage_level` before capture.
- Keep `failure_scope` as small as possible. Default to `artifact`.
- Fill `suggested_edit_scope` and `do_not_modify` when preparing later repair.
- Keep `repair_goal` concrete and local.
- Do not ask this workflow to write the repair patch.
