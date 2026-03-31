# IMPL Execution Contracts

本目录承载基于 `ADR-014` 与 `ADR-034` 手工补建的 `IMPL` 正式对象与执行契约文档。

当前 `ll-dev-tech-to-impl` skill 尚未 ready，因此这些对象用于：

- 作为 `TECH -> IMPL` 阶段的人工冻结入口
- 固化每个 FEAT 的研发实施任务边界
- 为后续 `template.dev.feature_delivery_l2` 提供稳定 handoff 起点

这些 `IMPL` 文档的正式定位是：

- 本次执行输入的 canonical package / execution-time single entrypoint
- 基于上游 `ADR / SRC / EPIC / FEAT / ARCH / TECH / API / UI / TESTSET` 收敛得到的执行契约
- 供 coder / tester / downstream runtime 共享消费的统一任务入口

同时必须明确：

- `IMPL` 不是业务、设计或测试事实的 SSOT
- `IMPL` 不是第二层技术设计
- `IMPL` 不得改写上游 `ADR / ARCH / FEAT / TECH / API / UI / TESTSET` 决策
- `IMPL` 应收敛执行所需最小充分信息，而不是镜像上游全文
- 若 repo 现状与上游冻结对象冲突，不得默认以代码现状为准，必须显式做 discrepancy handling

当前目录下的 `IMPL` 文档应优先遵循以下阅读口径：

- 先看 frontmatter 里的 `package_semantics / authority_scope / selected_upstream_refs / freshness_status / repo_discrepancy_status`
- 先看 `Selected Upstream` / `Traceability`
- 再看 `Implementation Task`、`Integration Plan`、`Evidence Plan`
- 若文档中存在 `Required / Suggested`、`Normative / Informative` 或 provisional 标记，应以这些分层解释执行优先级
- 若 `IMPL` 与 `TESTSET` 冲突，以 `TESTSET` 为准；若与 `TECH / API / UI` 冲突，以上游冻结对象为准

新增或补建 `IMPL` 时，优先从以下模板起手：

- `ssot/impl/IMPL_CONTRACT_TEMPLATE.md`

与 `FEAT-SRC-001-005` 对应的 governed skill onboarding matrix 现行落点为：

- `ssot/impl/IMPL-SRC-001-005-001__governed-skill-integration-matrix-and-onboarding-scope-definition.md`
