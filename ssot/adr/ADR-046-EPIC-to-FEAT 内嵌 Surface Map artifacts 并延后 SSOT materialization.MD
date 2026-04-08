# ADR-046：EPIC-to-FEAT 内嵌 Surface Map artifacts 并延后 SSOT materialization

* 状态：Accepted
* 日期：2026-04-08
* 决策者：Le Zeng
* 适用范围：`ll-product-epic-to-feat`、`ll-dev-feat-to-surface-map`、`feat_freeze_package`、`surface_map_package`、`ssot/mapping`
* 相关 ADR：ADR-011、ADR-041、ADR-042、ADR-043

---

# 1. 背景

在 ADR-042 引入 `surface_map_package` 之后，仓库中出现了两类运行时不一致：

1) **`feat-to-surface-map` 在执行阶段直接写入 `ssot/mapping`**，导致还未经过 FEAT 的 gate 审核就“进入真相域”。  
2) **surface-map 作为独立下游 workflow**，需要用户显式调用，导致链路体验不稳定，也更容易出现“忘了跑 surface-map”的缺口。

同时，prototype 的 owner binding 需要有稳定可预测的 SSOT 路径（尤其是 Journey 级原型），不能被 FEAT 的细拆粒度牵着走。

# 2. 决策

## 2.1 `ll-dev-feat-to-surface-map` 只产出 artifacts，不直接 materialize 到 SSOT

`skills/ll-dev-feat-to-surface-map` 的 `run/build_package` 不再写入 `ssot/mapping`，仅在 artifacts 目录生成：

* `surface-map-bundle.json` / `surface-map-bundle.md`
* `surface-map-review-report.json`
* `surface-map-defect-list.json`
* `surface-map-freeze-gate.json`

并且 `formal_*_ref` 输出字段改为可选/空，避免脚本/测试对“执行阶段写 SSOT”产生隐式依赖。

## 2.2 `ll-product-epic-to-feat` 末尾自动物化 surface-map artifacts（不要求用户单独调用）

`skills/ll-product-epic-to-feat` 在 FEAT freeze artifacts 目录末尾自动生成 surface-map artifacts（复用 `ll-dev-feat-to-surface-map` 的建模与验证规则），使得下游 `feat-to-proto` / `feat-to-tech` 可以直接消费同目录中的 `surface-map-bundle.json`。

同时，会额外生成 ID-based 文件名（以 `surface_map_ref` 为主键）用于稳定引用与后续 materialization，例如：

* `surface-map-bundle__<surface_map_ref>.json`
* `surface-map-bundle__<surface_map_ref>.md`
* `surface-map-freeze-gate__<surface_map_ref>.json`

## 2.3 prototype owner binding 按 Journey 格式稳定化

surface-map 中 prototype 的 owner binding 采用 Journey 级稳定命名：

```text
PROTO-<SRC-XXX>-JOURNEY
```

其中 `SRC-XXX` 从 `feat_ref`（如 `FEAT-SRC-003-001`）推导，确保后续 prototype SSOT 路径稳定。

# 3. 后果

* `product.epic-to-feat` 的 handoff 仍保留 `design_gate_required`，但不再把 `workflow.dev.feat_to_surface_map` 作为必须的 target workflow。
* surface-map 的正式 SSOT materialization 由主线程在 gate 通过后统一执行（避免在 executor 阶段提前写入真相域）。
* 下游 workflow 如需 surface-map，只需从 FEAT freeze artifacts 目录读取，而不是依赖独立的 surface-map workflow 先行执行。

# 4. 迁移与兼容性

* 为兼容已有下游脚本，FEAT freeze artifacts 目录仍会保留固定文件名（`surface-map-bundle.json` 等），并同时补充 ID-based 命名。
* 旧的 `formal_surface_map_*_ref` 字段不再保证存在；调用方应改为以 artifacts 文件或 `surface_map_ref` 为主键解析。

