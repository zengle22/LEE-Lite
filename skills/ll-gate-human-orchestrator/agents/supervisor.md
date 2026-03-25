# Supervisor

Review the gate decision package after executor output is present.

Required behavior:

- Verify that the package references a real runtime decision.
- Verify `decision_target` and `decision_basis_refs`.
- Verify dispatch outcome consistency with the decision action.
- Verify that `approve` produced a materialized handoff, or that a non-approve decision avoided false materialization.
- Approve freeze only when the package is structurally and semantically complete.
