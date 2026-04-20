---
name: ll-frz-manage
description: "ADR-050 governed skill for FRZ (Freeze Package) management: validate, freeze, list, and extract operations."
---

# LL FRZ Manage

This skill implements the ADR-050 FRZ lifecycle management interface. It accepts a directory containing source documents (PRD, UX, Architecture), runs MSC (Minimum Semantic Completeness) validation, and manages the FRZ registry for freezing and listing operations.

## Canonical Authority

- ADR: `ssot/adr/ADR-050-SSOT语义治理总纲.md`
- Upstream handoff: BMAD/Superpowers framework discussion output
- Downstream consumer: Phase 08 semantic extraction chain (FRZ -> SRC)

## Runtime Boundary Baseline

- Interpret this workflow using `ssot/adr/ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `FRZ Package Lifecycle Management`.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. **Accept input** — either a doc directory path (validate/freeze) or registry query parameters (list).
2. **Determine mode** — `validate`, `freeze` (new/revise), `list`, or `extract` based on subcommand.
3a. **validate mode**: `ll frz-manage validate --input <doc-dir>` — reads FRZ YAML from doc directory, runs MSC validation across all 5 dimensions, prints structured report with present/missing dimensions and PASS/FAIL status.
3b. **freeze mode**: `ll frz-manage freeze --input <doc-dir> --id FRZ-xxx` — validates MSC first (rejects if invalid), saves FRZ package to artifacts directory with input snapshot, registers to FRZ registry with status=frozen.
3b-r. **freeze --type revise**: `ll frz-manage freeze --type revise --input <doc-dir> --previous-frz FRZ-xxx --reason "..."` — same as freeze mode but records a revision chain linking to the previous FRZ, runs circular-reference prevention, and tags `revision_type=revise` in the registry. Used for Major patches that require FRZ re-freeze. After revise completes, the user must manually re-run the extraction chain (SRC → EPIC → FEAT).
3c. **list mode**: `ll frz-manage list [--status frozen|blocked]` — queries FRZ registry, displays formatted table of registered packages with ID, status, created_at, MSC validity.
3d. **extract mode**: `ll frz-manage extract --frz <frz-id> --output <dir>` — stub for Phase 8, prints "not implemented yet, use in Phase 8".
4. **Validate output** — confirm MSC report completeness, registry consistency, output format correctness.
5. **Return exit code** — 0 for success, non-zero for failure.

## Workflow Boundary

- Input: doc directory path containing FRZ YAML, FRZ ID (FRZ-xxx), optional status filter
- Output: MSC validation report, FRZ package artifacts, registry listing
- Out of scope: FRZ generation (BMAD/Superpowers), semantic extraction (Phase 8), Task Pack scheduling (Phase 10)

## Non-Negotiable Rules

- Do not bypass scripts/frz_manage_runtime.py — all CLI operations must flow through this runtime.
- Do not freeze without passing MSC validation first — freeze_frz explicitly calls MSCValidator.validate() before register_frz.
- Do not accept duplicate FRZ IDs — get_frz() uniqueness check before registration.
- All AI pre-filled fields must be marked as human-reviewed per ADR-050.
- FRZ IDs must match FRZ-xxx format (regex: ^FRZ-\d{3,}$).
- Use yaml.safe_load() only — no yaml.load() — for YAML deserialization (T-07-08 mitigation).
