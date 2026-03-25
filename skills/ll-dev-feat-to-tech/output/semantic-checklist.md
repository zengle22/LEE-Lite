# Output Semantic Checklist

Review the `tech_design_package` against the selected FEAT.

- Is `TECH` present and strong enough to seed downstream `tech-impl` work without re-deriving the FEAT?
- Does `TECH` include implementation architecture, state model, module plan, unit mapping, contracts, main sequence, exception strategy, integration points, and pseudocode rather than only boundary restatement?
- Do the runtime-view and flow diagrams appear as readable ASCII diagrams that explain how the implementation will actually work without repeating ARCH boundary rationale?
- When `API` is emitted, does it define command-level request schema, response schema, field semantics, enum/domain, invariants, canonical refs, errors, idempotency, and compatibility rules instead of abstract contract labels?
- Are `ARCH` and `API` emitted only when the need assessment justifies them, not as unconditional boilerplate?
- Does `ARCH` stay on placement/topology/responsibility split while `TECH` stays on implementation-ready design detail, instead of repeating the same architecture skeleton?
- Do the bundle-level `Optional ARCH` / `Optional API` sections stay as reference summaries instead of becoming shadow copies of the standalone `ARCH` / `API` artifacts?
- For collaboration FEATs, does `TECH` keep decision-driven runtime re-entry routing in scope without stealing formalization semantics or materialization ownership?
- Does the package avoid introducing new product scope, hidden dependencies, or task-level sequencing not present in the FEAT?
- Does the cross-artifact consistency check distinguish structural pass from semantic pass, keep blocking issues separate from minor open items, and prove that contracts, boundaries, and implementation design are mutually aligned?
