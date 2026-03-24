# Authoring Checklist

- Keep the workflow boundary at raw source normalization only.
- Accept only `adr`, `raw_requirement`, `business_opportunity`, and `business_opportunity_freeze`.
- Emit one SRC candidate package per run in `artifacts/raw-to-src/<run_id>`.
- Preserve same-topic fidelity and record explicit source refs.
- Add thin bridge fields whenever the input is ADR-like.
- Validate each generated intermediate state before continuing to the next step.
- Keep acceptance artifacts, retry-budget reports, and evidence alongside the candidate package.
- Never let executor logic replace supervisor review or external-gate decisions.
