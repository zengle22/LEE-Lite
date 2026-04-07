# Executor

1. Resolve one authoritative `feat_freeze_package` together with the selected `feat_ref`.
2. Determine whether the FEAT is design-impacting.
3. Produce a `surface_map_package` that binds each impacted design surface to an owner, action, scope, and reason.
4. Prefer `update` when an owner already exists. Use `create` only when the boundary is new and justified.
5. Materialize the governed output package and execution evidence.
