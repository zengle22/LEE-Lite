# Project Structure Reference

This skill initializes the same LEE Lite skill-first repository skeleton used by the current workspace.

## Durable Directories

- `artifacts/`
- `cli/`
- `docs/`
- `examples/`
- `knowledge/`
- `legacy/`
- `scripts/`
- `skills/`
- `ssot/`
- `ssot/`
- `tests/`
- `tools/`

## Runtime Shells

- `/.lee/`
- `/.local/`
- `/.project/`
- `/.workflow/`
- `/.artifacts/`

## Managed Root Files

- `.editorconfig`
- `.env.example`
- `.gitignore`
- `.projectignore`
- `README.md`
- `agent.md`
- `Makefile`
- `.lee/config.yaml`
- `.lee/repos.yaml`
- `.project/dirs.yaml`
- `docs/repository-layout.md`

## Operating Rules

- Durable project truth lives in the durable directories.
- Runtime state stays in the runtime shells.
- Existing unmanaged files must not be overwritten.
- The initialization package must record every created, updated, and skipped path.
