# SSOT Map

Purpose: guide progressive disclosure across FRZ and SSOT objects.

Primary sources:

- `ssot/README.md`
- `ssot/adr/ADR-050-SSOT语义治理总纲.md`
- `ssot/adr/ADR-008-SSOT 主链、派生对象与文件标准统一基线.MD`

## Semantic Chain

```text
FRZ
  -> SRC
    -> EPIC
      -> FEAT
        -> SURFACE_MAP
        -> TECH
        -> API
        -> UI
        -> PROTOTYPE
        -> IMPL
        -> TESTSET or QA requirement-axis objects
          -> API/E2E manifests
            -> Evidence
              -> Gate
                -> Release fact
```

## Object Rules

| Object | Rule |
| --- | --- |
| FRZ | Frozen semantic source, stored as artifact and referenced by SSOT |
| SRC | Source projection from FRZ or governed raw-to-src bridge |
| EPIC | Scope grouping derived from SRC and FRZ truth |
| FEAT | Implementable feature scope derived from EPIC and FRZ truth |
| SURFACE_MAP | Ownership map before design assets |
| TECH/API/UI/PROTOTYPE | Design assets or derived implementation guidance |
| IMPL | Implementation candidate package, not code execution itself |
| TESTSET and QA objects | Coverage and verification authority, aligned to requirement and implementation axes |
| Evidence | Required support for decisions, gates, freezes, and release readiness |
| Gate | Promotion boundary |

## Change Routing

| Change type | Route |
| --- | --- |
| Visual detail | Minor patch, retain or local settle |
| Interaction behavior | Minor patch, backwrite UI/flow/TESTSET as applicable |
| Semantic behavior | Major patch, revise FRZ, re-extract or update SSOT |
| Runtime or implementation detail | Keep within IMPL, TECH, scripts, or evidence authority as appropriate |

## Load Next

For semantic governance, load ADR-050.

For concrete skill routing, load `ssot/governance/maps/SKILL-MAP.md`.

For patch classification, load ADR-049 and the patch skills.
