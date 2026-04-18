---
phase: 07
plan: 02
subsystem: CLI registry layer
tags: [registry, anchor, frz, yaml-persistence, unit-tests]
dependencies:
  requires: [cli.lib.errors, cli.lib.fs, cli.lib.frz_schema]
  provides: [anchor-registry, frz-registry]
  affects: [ssot/registry/]
tech-stack:
  added: [pyyaml]
  patterns: [YAML-backed registry, atomic write, frozen dataclass]
key-files:
  created:
    - path: cli/lib/anchor_registry.py
      purpose: AnchorRegistry class with register/resolve/list_by_frz/list_all/count
    - path: cli/lib/test_anchor_registry.py
      purpose: 15 unit tests for AnchorRegistry
    - path: cli/lib/frz_registry.py
      purpose: FRZ registry helpers (register_frz, list_frz, get_frz, update_frz_status)
    - path: cli/lib/test_frz_registry.py
      purpose: 14 unit tests for FRZ registry
    - path: ssot/registry/frz-registry.yaml
      purpose: Initial empty FRZ registry structure
decisions:
  - Used defensive _load() returning empty list for non-dict YAML (corruption handling)
  - Atomic write via tempfile + os.replace in frz_registry to prevent write-interruption corruption
metrics:
  duration: auto
  completed_date: "2026-04-18"
  tests_total: 29
  tests_passed: 29
  tests_failed: 0
---

# Phase 07 Plan 02: Anchor + FRZ Registry Summary

## One-liner

YAML-backed anchor ID registry and FRZ package registry with format validation, duplicate detection, atomic writes, and 29 passing unit tests.

## What was done

**Task 1 — Anchor Registry (`cli/lib/anchor_registry.py`)**
- Created `AnchorEntry` frozen dataclass with fields: `anchor_id`, `frz_ref`, `projection_path`, `metadata`, `registered_at`
- Implemented `ANCHOR_ID_PATTERN` regex: `^[A-Z]{2,5}-\d{3,}$`
- `AnchorRegistry` class with methods: `register`, `resolve`, `list_by_frz`, `list_all`, `count`
- Validates anchor ID format, projection path (SRC/EPIC/FEAT), detects duplicates
- YAML persistence to `ssot/registry/anchor_registry.yaml`
- 15 unit tests covering success, errors, edge cases, persistence, corruption handling

**Task 2 — FRZ Registry (`cli/lib/frz_registry.py` + `ssot/registry/frz-registry.yaml`)**
- Implemented `register_frz` with FRZ_ID_PATTERN validation (`^FRZ-\d{3,}$`)
- Atomic write via temp file + os.replace to prevent corruption on write interruption
- `list_frz` with optional status filtering
- `get_frz` for single record lookup
- `update_frz_status` with `REGISTRY_MISS` error on not found
- Revision chain tracking: `previous_frz_ref`, `revision_type`, `revision_reason`
- Created initial empty `ssot/registry/frz-registry.yaml`
- 14 unit tests covering all functions, duplicates, invalid formats, revision fields, status updates

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _load() crash on non-dict YAML in AnchorRegistry**
- **Found during:** Task 1 (test execution)
- **Issue:** `_load()` called `.get()` on the YAML result without checking if it was a dict. Corrupted YAML (e.g., plain text) caused `AttributeError: 'str' object has no attribute 'get'`
- **Fix:** Added `isinstance(data, dict)` check before `.get()`, returning empty list for non-dict data
- **Files modified:** `cli/lib/anchor_registry.py`
- **Commit:** `611f2e5`

**2. [Rule 2 - Missing] Added `isinstance(data, dict)` guard in frz_registry._load_registry()**
- **Found during:** Task 2 (preemptive, after discovering same pattern in Task 1)
- **Issue:** Same vulnerability existed in `_load_registry()` — would crash if YAML contained non-dict data
- **Fix:** Added `isinstance(data, dict)` guard before `.get()`
- **Files modified:** `cli/lib/frz_registry.py`
- **Commit:** `8cddb4f`

**3. [Rule 2 - Missing] Threat T-07-07 (path traversal) — not mitigated in code**
- **Found during:** Task 2 threat model review
- **Issue:** `package_ref` field is stored as-is without validation against workspace root
- **Decision:** Defer to Plan 07-04 (ll-frz-manage skill) which will handle path canonicalization at the CLI entry point. The registry layer stores what it receives; path validation belongs at the boundary layer.
- **Files affected:** `cli/lib/frz_registry.py`

## Commits

- `611f2e5`: feat(07-frz-02): create AnchorRegistry with register/resolve/list and unit tests
- `8cddb4f`: feat(07-frz-02): create FRZ registry with register/list/get/update_status

## Requirements Delivered

- **FRZ-03:** FRZ registry records version, status, created_at for each FRZ via `register_frz`/`list_frz`
- **EXTR-03:** Anchor ID registry supports register/resolve/list_by_frz with format validation

## Self-Check: PASSED

- FOUND: cli/lib/anchor_registry.py
- FOUND: cli/lib/frz_registry.py
- FOUND: cli/lib/test_anchor_registry.py
- FOUND: cli/lib/test_frz_registry.py
- FOUND: ssot/registry/frz-registry.yaml
- FOUND: commit 611f2e5
- FOUND: commit 8cddb4f
