---
name: ll-qa-feat-to-testset
deprecated: true
superseded_by:
  - ll-qa-api-from-feat   # 双链 API 链，含 acceptance traceability
  - ll-qa-e2e-from-proto  # 双链 E2E 链，含 acceptance traceability
deprecation_reason: "执行层价值已被 ADR-047 双链完整覆盖，策略层价值迁移至双链产出"
removal_version: "2.2"
migration_guide: |
  - API 链：使用 /ll-qa-api-from-feat
  - E2E 链：使用 /ll-qa-e2e-from-proto
  - acceptance traceability：已在两个统一入口 skill 的产出物中补齐
---

> ⚠️ DEPRECATED: This skill is deprecated as of v2.1 and will be removed in v2.2.
> Use `/ll-qa-api-from-feat` for API test chain or `/ll-qa-e2e-from-proto` for E2E test chain.
>
> **Migration Guide:**
> - API 链：`/ll-qa-api-from-feat`（一次性跑完 api-plan → manifest → spec）
> - E2E 链：`/ll-qa-e2e-from-proto`（一次性跑完 e2e-plan → manifest → spec）
> - Acceptance traceability：已在统一入口 skill 的产出物中补齐

# LL QA FEAT to TESTSET (DEPRECATED)

This skill is deprecated. Use the unified entry skills instead.

## Migration

| Before | After |
|--------|-------|
| `/ll-qa-feat-to-testset` | `/ll-qa-api-from-feat` (API chain) or `/ll-qa-e2e-from-proto` (E2E chain) |

## Removed Capabilities

The following capabilities have been migrated to the unified entry skills:

- **API test chain**: Now available via `/ll-qa-api-from-feat`
- **E2E test chain**: Now available via `/ll-qa-e2e-from-proto`
- **Acceptance traceability**: Now included in the output of both unified entry skills

## Support

This skill remains functional for backward compatibility but will be removed in v2.2.
Please migrate to the unified entry skills immediately.
