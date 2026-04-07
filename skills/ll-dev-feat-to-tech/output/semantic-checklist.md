# Output Semantic Checklist

Review the `tech_design_package` against the selected FEAT.

- [required] Does TECH freeze implementation carriers, module responsibilities, and owner boundaries rather than only repeating FEAT scope?
  Evidence: tech_design.implementation_carrier_view, tech_design.module_plan, selected_feat
- [required] Are interface contracts, field semantics, and command/API meanings explicit enough for implementation and review?
  Evidence: tech_design.interface_contracts, api artifact, design_consistency_check
- [required] Does TECH explain the real state model and runtime flow, not just generic lifecycle text?
  Evidence: tech_design.state_model, tech_design.main_sequence, tech_design.io_matrix_and_side_effects
- [required] Are failure handling, retry / compensation, and degraded paths explicit for this FEAT slice?
  Evidence: tech_design.exception_and_compensation, tech_design.minimal_code_skeleton
- [required] Does TECH freeze concrete integration points and compatibility / migration constraints for the current system?
  Evidence: tech_design.integration_points, integration_context, tech_design.migration_constraints
- [required] Are canonical ownership, glossary terms, and algorithm / decision constraints explicit enough to block downstream reinterpretation?
  Evidence: tech_design.technical_glossary_and_canonical_ownership, tech_design.algorithm_constraints
- [aux] When ARCH or API is emitted, does it remain justified by need assessment and not duplicate TECH?
  Evidence: need_assessment, artifact_refs, design_consistency_check
