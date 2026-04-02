---
name: ll-skill-install
description: Install a canonical workflow skill into Codex or Claude Code as a workspace-bound adapter that points back to the canonical implementation in the current repository. Use when LL/LEE workflow skills should be packaged or refreshed for local agent runtimes instead of hand-copying folders and manually rewriting installed SKILL.md and agents/openai.yaml.
---

# LL Skill Install

Install canonical workflow skills into local runtime skill directories as workspace-bound adapters.

## Use This Skill For

- Installing a new local workflow skill into Codex or Claude Code.
- Reinstalling an existing installed skill after the canonical source changed.
- Converting a canonical governed skill into the adapter-style installed copy used by local runtimes.

## Install Workflow

1. Resolve the canonical source skill folder in the current workspace.
2. Confirm the canonical source is already the correct abstraction under `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`. The installer packages an existing `Skill` authority; it does not promote a `Command`, `Tool`, workflow residue, or repo CLI carrier into a skill.
3. Run `scripts/install_adapter.py` with the source path.
4. Set `--runtime codex` or `--runtime claude` unless `--dest-root` is being passed explicitly.
5. Use `--replace` when refreshing an existing installed copy.
6. Validate the installed result by checking the generated `SKILL.md` and `agents/openai.yaml`.

Default command pattern:

```powershell
python scripts/install_adapter.py --source <path-to-canonical-skill> --runtime codex --replace
```

Claude Code example:

```powershell
python scripts/install_adapter.py --source <path-to-canonical-skill> --runtime claude --replace
```

## Script Behavior

The installer script:

- copies the canonical skill into the selected runtime skills directory
- rewrites the installed `SKILL.md` into adapter-style wording
- rewrites `agents/openai.yaml` for adapter-style UI metadata
- preserves the copied governance pack, scripts, and contracts

## Guardrails

- Treat the workspace skill as the canonical source of truth.
- Treat `ADR-038` as the abstraction boundary baseline. Installation preserves authority and carrier boundaries; it does not reclassify runtime objects.
- Do not hand-edit the installed copy when the same change belongs in the canonical source.
- Use `--replace` only when you intend to refresh the installed copy.
- Prefer absolute paths for `--source`, `--dest-root`, and `--workspace-root`.

## Resources

- `scripts/install_adapter.py`: installs or refreshes a workspace-bound adapter copy in Codex or Claude Code skills.

## References

- `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`
- `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-020-标准 Skill 实现、Adapter 安装与 CLI 边界基线.MD`
