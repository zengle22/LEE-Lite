# TESTSET SSOT

本目录同时包含两类 `TESTSET` 文档：

1. 历史链路文档
   - `TESTSET-FEAT-SRC-001-*`
   - 这些文件对应旧的 `REL / DEVPLAN / TESTPLAN` 链路。
   - 它们已经在文件内标记为 `historical_only` / `superseded`。

2. 过渡期手工补录文档
   - `TESTSET-SRC-003-*`
   - 这些文件是 `ADR-018` 调整期手工补录后，再按正式 lineage-first 规则迁移得到的 runner testset 边界。
   - 它们保留了 runner QA 语义，但来源仍是过渡期补录，而不是一次完整的 skill + gate 正式物化。

当前手工补录的 runner testset 包括：

- `TESTSET-SRC-003-001`
  - 批准后 Ready Job 生成流 Test Set
- `TESTSET-SRC-003-002`
  - Runner 用户入口流 Test Set
- `TESTSET-SRC-003-003`
  - Runner 控制面流 Test Set
- `TESTSET-SRC-003-004`
  - Execution Runner 自动取件流 Test Set
- `TESTSET-SRC-003-005`
  - 下游 Skill 自动派发流 Test Set
- `TESTSET-SRC-003-006`
  - 执行结果回写与重试边界流 Test Set
- `TESTSET-SRC-003-007`
  - Runner 运行监控流 Test Set

这些过渡文档承接：

- `ADR-018`
- `EPIC-SRC-003-001` 风格的 runner EPIC lineage
- `product.epic-to-feat::adr018-entry-surface-feat-r3`
- `qa.feat-to-testset`

后续如果继续补新的 runner testset 变体，应优先通过 skill + gate 物化成 `TESTSET-SRC-<src>-<slot>`，不要再回退到 `TESTSET-SRC-ADR...` 或旧的 release/devplan/testplan 写法。
