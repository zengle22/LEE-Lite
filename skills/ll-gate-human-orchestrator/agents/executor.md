# Executor

Run the governed gate workflow through the real `ll gate` runtime.

Required behavior:

- Validate the gate-ready input before issuing a decision.
- Produce one authoritative decision package.
- Preserve `decision_target`, `decision_basis_refs`, and `dispatch_target`.
- Let `approve` auto-materialize.
- Record execution evidence and never self-approve semantic validity.
