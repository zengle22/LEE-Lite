# Experience Patches Directory

This directory stores experience patch YAML files for ADR-049 Experience Patch Layer.

## Directory Structure

```
ssot/experience-patches/
├── README.md
├── {FEAT-ID}/
│   ├── patch_registry.json
│   ├── UXPATCH-0001__{slug}.yaml
│   └── UXPATCH-0002__{slug}.yaml
└── ...
```

## Conventions

- **Location**: `ssot/experience-patches/{FEAT-ID}/` — one subdirectory per feature
- **Patch file naming**: `UXPATCH-{SEQ}__{slug}.yaml`
  - `SEQ`: 4-digit zero-padded sequence number (e.g., `0001`, `0002`)
  - `slug`: kebab-case short description (e.g., `button-color-fix`)
  - Example: `UXPATCH-0001__button-color-fix.yaml`
- **Registry file**: `patch_registry.json` per FEAT subdirectory — indexes all patches in that feature
- **ID format**: `UXPATCH-0001` (hyphen-separated, 4-digit zero-padded)

## Status Lifecycle

```
draft → active → validated → pending_backwrite → backwritten / retain_in_code / upgraded_to_src → archived
                                                        ↳ superseded / discarded (alternative paths)
```

## Schema

All patch YAML files must conform to `ssot/schemas/qa/patch.yaml`.
