---
name: ll-skill-install
description: Install a canonical workflow skill into Codex as a workspace-bound adapter that points back to the canonical implementation in the current repository. Use when Codex should package or update a local LL/LEE workflow skill for Codex runtime instead of hand-copying folders and manually rewriting installed SKILL.md and agents/openai.yaml.
---

# LL Skill Install

Install canonical workflow skills into `C:\Users\shado\.codex\skills` as workspace-bound adapters.

## Use This Skill For

- Installing a new local workflow skill into Codex.
- Reinstalling an existing installed skill after the canonical source changed.
- Converting a canonical governed skill into the adapter-style installed copy used by Codex.

## Install Workflow

1. Resolve the canonical source skill folder in the current workspace.
2. Run `scripts/install_adapter.py` with the source path.
3. Use `--replace` when refreshing an existing installed copy.
4. Validate the installed result by checking the generated `SKILL.md` and `agents/openai.yaml`.

Default command pattern:

```powershell
python scripts/install_adapter.py --source <path-to-canonical-skill> --replace
```

## Script Behavior

The installer script:

- copies the canonical skill into Codex's skills directory
- rewrites the installed `SKILL.md` into adapter-style wording
- rewrites `agents/openai.yaml` for adapter-style UI metadata
- preserves the copied governance pack, scripts, and contracts

## Guardrails

- Treat the workspace skill as the canonical source of truth.
- Do not hand-edit the installed copy when the same change belongs in the canonical source.
- Use `--replace` only when you intend to refresh the installed copy.
- Prefer absolute paths for `--source`, `--dest-root`, and `--workspace-root`.

## Resources

- `scripts/install_adapter.py`: installs or refreshes a workspace-bound adapter copy in Codex skills.
