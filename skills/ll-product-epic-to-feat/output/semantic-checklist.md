# Output Semantic Checklist

Review the `feat_freeze_package` against the upstream `epic_freeze_package`.

- [required] Does the FEAT freeze who acts, why the slice exists, and what completion means without collapsing into task or UI detail?
  Evidence: features[].identity_and_scenario, features[].goal, features[].business_value
- [required] Can a downstream reader recover the main business flow, collaboration sequence, and journey handoff from FEAT alone?
  Evidence: features[].business_flow, features[].collaboration_and_timeline
- [required] Are product rules, constraints, and prohibited inference boundaries explicit enough for downstream derivation?
  Evidence: features[].constraints, prohibited_inference_rules, boundary_matrix
- [required] Does the FEAT make authoritative inputs, produced outputs, and canonical artifact ownership explicit?
  Evidence: features[].consumes, features[].produces, features[].authoritative_artifact
- [required] Are exception paths, overlap boundaries, and non-responsibility edges explicit rather than left for downstream guesswork?
  Evidence: features[].acceptance_checks, features[].frozen_downstream_boundary, boundary_matrix
- [required] Would TECH and TESTSET consumers have enough FEAT-level acceptance truth to inherit without reopening EPIC?
  Evidence: features[].acceptance_and_testability, features[].acceptance_checks
- [aux] Are design impact routing hints and candidate design surfaces explicit when design derivation is required?
  Evidence: features[].design_impact_required, features[].candidate_design_surfaces, features[].design_surfaces
