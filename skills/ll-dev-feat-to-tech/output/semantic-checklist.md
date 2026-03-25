# Output Semantic Checklist

Review the `tech_design_package` against the selected FEAT.

- Is `TECH` present and strong enough to seed downstream `tech-impl` work without re-deriving the FEAT?
- Does `TECH` include implementation architecture, key flows, state model, module plan, and implementation strategy rather than only boundary restatement?
- Do the architecture and flow diagrams appear as readable ASCII diagrams that explain how the implementation will actually work?
- Does `TECH-IMPL` map implementation units to concrete repo paths, contract fields, main sequence, exception strategy, integration points, and pseudocode?
- When `API` is emitted, does it define concrete CLI command surfaces, request/response fields, errors, idempotency, and compatibility rules instead of abstract contract labels?
- Are `ARCH` and `API` emitted only when the need assessment justifies them, not as unconditional boilerplate?
- Do `ARCH`, `TECH`, and `API` stay within their own boundaries instead of repeating the same material?
- Does the package avoid introducing new product scope, hidden dependencies, or task-level sequencing not present in the FEAT?
- Does the cross-artifact consistency check prove that contracts, boundaries, and implementation design are mutually aligned?
