# Milestones

## v1.0 ADR-047 双链测试 (Shipped: 2026-04-17)

**Phases completed:** 4 phases, 8 plans, 24 tasks

**Key accomplishments:**

- ADR-049 governed ll-patch-capture skill skeleton with dual-path execution protocol, 6-state lifecycle, and input/output contracts
- Commit:
- Prompt-first runtime infrastructure for ll-qa-gate-evaluate skill: 3 shell scripts, lifecycle config, and evidence JSON schema
- Backward compatibility skill aggregating dual-chain plan/manifest/spec/settlement artifacts into legacy testset-compatible JSON view
- Registered 3 new QA skill actions in CLI handler, added gate output validator, and deprecated 2 legacy ADR-035 skills
- Patch schema guardrails with reviewed_at, test_impact enforcement, and ManifestItem patch tracking
- PatchContext dataclass + resolve_patch_context() + _check_patch_test_impact() gate, wired into test execution flow
- Patch-aware execution loop: per-item TEST_BLOCKED skip via _patch_blocked flag, TOCTOU re-verification with PATCH_CONTEXT_CHANGED gate, and manifest item marking with acceptance ref preservation

---
