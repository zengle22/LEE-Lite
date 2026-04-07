# Output Semantic Checklist

Review the `prototype_package` as an experience-facing semantic slice.

- [required] Does the prototype freeze the intended journey slice and its owned surfaces rather than an arbitrary demo path?
  Evidence: prototype-bundle.json.pages, handoff-to-feat-downstreams.json.journey_surface_inventory
- [required] Are entry state, initial view, and exit / completion path explicit and reviewable?
  Evidence: prototype-initial-view-report.json, prototype-route-map.json
- [required] Are CTA hierarchy and container semantics explicit enough for reviewers to understand page intent?
  Evidence: journey-ux-ascii.md, ui-shell-spec.md, prototype-review-report.json
- [required] Does the prototype express primary states and feedback, not just a happy-path clickthrough?
  Evidence: prototype-fidelity-report.json, prototype-runtime-smoke.json, prototype-review-report.json
- [required] Are exception, retry, skip, or degraded paths frozen where the FEAT requires them?
  Evidence: prototype-placeholder-lint.json, prototype-journey-reachability-report.json, prototype-review-report.json
- [required] Does the prototype remain aligned to shell rules and shared owner binding instead of drifting into a FEAT-private layout?
  Evidence: ui-shell-spec.md, prototype-bundle.json.surface_map_ref, prototype-bundle.json.prototype_owner_ref
- [aux] Does the package clearly separate machine-complete prototype evidence from remaining review follow-up?
  Evidence: prototype-review-guide.md, prototype-review-report.json, prototype-freeze-gate.json
