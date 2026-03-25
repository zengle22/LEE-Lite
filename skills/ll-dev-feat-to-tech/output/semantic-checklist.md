# Output Semantic Checklist

Review the `tech_design_package` against the selected FEAT.

- Is `TECH` present and strong enough to seed downstream `tech-impl` work without re-deriving the FEAT?
- Are `ARCH` and `API` emitted only when the need assessment justifies them, not as unconditional boilerplate?
- Do `ARCH`, `TECH`, and `API` stay within their own boundaries instead of repeating the same material?
- Does the package avoid introducing new product scope, hidden dependencies, or task-level sequencing not present in the FEAT?
- Does the cross-artifact consistency check prove that contracts, boundaries, and implementation design are mutually aligned?
