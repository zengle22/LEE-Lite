# Output Semantic Checklist

Review the `ui_spec_package` as an implementation-facing semantic contract.

- [required] Does the UI spec freeze page goals and task flow as implementation-facing contracts, not just prototype prose?
  Evidence: ui-spec-bundle.json, generated ui spec markdown, ui-flow-map.md
- [required] Are information hierarchy, layout regions, and shell framing explicit enough for implementation?
  Evidence: ui-semantic-source-ledger.json, journey-ux-ascii.md, ui-shell-spec.md
- [required] Does the UI spec make fields, actions, validation, and user feedback explicit?
  Evidence: generated ui spec markdown, ui-semantic-source-ledger.json
- [required] Are loading, success, degraded, and blocking state behaviors explicit at the UI contract layer?
  Evidence: generated ui spec markdown, ui-semantic-source-ledger.json
- [required] Does the spec freeze component/container contracts tied to shell and shared UI owner boundaries?
  Evidence: ui-shell-spec.md, ui-spec-bundle.json.ui_owner_ref, surface_map_ref
- [required] Are source traces and AI inferences disclosed clearly enough that reviewers can see what is authoritative versus inferred?
  Evidence: ui-semantic-source-ledger.json, ui-spec-review-report.json
- [aux] Does the review output show how the current UI owner changes relative to prototype input and owner baseline?
  Evidence: ui-spec-review-report.json, ui-flow-map.md
