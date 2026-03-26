# TESTSET SSOT

本目录同时包含两类 `TESTSET` 文档：

1. 历史链路文档
   - `TESTSET-FEAT-SRC-001-*`
   - 这些文件对应旧的 `REL / DEVPLAN / TESTPLAN` 链路。
   - 它们已经在文件内标记为 `historical_only` / `superseded`。

2. 当前活跃链路文档
   - `TESTSET-SRC-ADR018-ENTRY-SURFACE-R1-*`
   - 这些文件对应 `ADR-018` 当前派生出来的 active runner testset 边界。
   - 其职责是冻结 `Execution Loop Job Runner` 的 operator-facing QA 对象，而不是保留旧 release/devplan lineage。

当前活跃的 runner testset 包括：

- `TESTSET-SRC-ADR018-ENTRY-SURFACE-R1-001`
  - 批准后 Ready Job 生成流 Test Set
- `TESTSET-SRC-ADR018-ENTRY-SURFACE-R1-002`
  - Runner 用户入口流 Test Set
- `TESTSET-SRC-ADR018-ENTRY-SURFACE-R1-003`
  - Runner 控制面流 Test Set
- `TESTSET-SRC-ADR018-ENTRY-SURFACE-R1-004`
  - Execution Runner 自动取件流 Test Set
- `TESTSET-SRC-ADR018-ENTRY-SURFACE-R1-005`
  - 下游 Skill 自动派发流 Test Set
- `TESTSET-SRC-ADR018-ENTRY-SURFACE-R1-006`
  - 执行结果回写与重试边界流 Test Set
- `TESTSET-SRC-ADR018-ENTRY-SURFACE-R1-007`
  - Runner 运行监控流 Test Set

这些 active 文档承接：

- `ADR-018`
- `EPIC-GATE-EXECUTION-RUNNER`
- `product.epic-to-feat::adr018-entry-surface-feat-r3`
- `qa.feat-to-testset`

后续如果继续补新的 runner testset 变体，应沿同一命名与对象边界收敛，而不是回退到旧的 release/devplan/testplan 写法。
