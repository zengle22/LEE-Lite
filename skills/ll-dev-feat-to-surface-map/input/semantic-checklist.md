# Input Semantic Checklist

- Is the selected FEAT frozen and accepted in the upstream `feat_freeze_package`?
- Does the selected FEAT already carry the minimum FEAT fields required by the upstream contract?
- If `design_impact_required=true`, are the downstream design surfaces explicit enough to route ownership?
- If `design_impact_required=false`, is there a clear bypass rationale instead of a silent design omission?
- Are any explicit owner refs stable enough to be treated as existing owners rather than speculative creates?
