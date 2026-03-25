# Historical SSOT Objects

The active governed mainline in this repository is:

- `FEAT`
- `TECH` with optional `ARCH` / `API`
- `IMPL`
- `TESTSET`

The older `RELEASE` / `DEVPLAN` / `TESTPLAN` objects under `ssot/release`, `ssot/devplan`, and `ssot/testplan` are kept only for historical traceability.

Rules:

- Do not use those historical objects as active upstream inputs for current governed workflow skills.
- Prefer the current chain frozen in `ADR-013` and `ADR-014`.
- If an old object must be cited for traceability, treat it as historical context only, not as an authoritative runtime contract.
