# Input Semantic Checklist

- `IMPL` is the main tested object and is explicitly identified.
- `FEAT` and `TECH` resolve to frozen upstream authorities.
- Optional `ARCH / API / UI / TESTSET` refs are treated as authorities when present.
- Requested mode does not weaken frozen deep-mode trigger rules.
- repo context is advisory only and does not override upstream truth.
- `repo_context` preserves touchable paths, observable paths, and migration notes when available.
- `risk_profile` stays on implementation-readiness strictness and does not reframe the workflow into another domain.
- `review_profile`, when provided, can steer persona simulation, counterexample families, and focus areas, but it cannot override authority or mode-selection rules.
- Deep mode requests provide enough authority context to build functional chain, user journey, state/data, and UI/API/state mapping views.
- Deep mode review is expected to exercise the six-stage path: semantic extraction, cross-artifact consistency, logic red-team, UX/journey review, supervisor challenge, and governed verdict packaging.
- The request should not weaken deep triggers for migration, canonical ownership, state boundaries, or newly introduced UI/API/state surfaces.
