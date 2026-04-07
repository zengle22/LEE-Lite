# Mapping Layer

本目录承载 `ADR-042` 引入的归属层模板与后续正式化对象。

## 目录定位

`surface_map_package` 不回答“要交付什么功能”，而回答：

* 这个 `FEAT` 影响哪些设计面
* 每个设计面归哪个已有 shared design asset 承接
* 本次是 `update` 还是 `create`
* 本次 delta 是什么

因此它位于：

```text
FEAT -> SURFACE-MAP -> shared design assets -> IMPL
```

而不是：

```text
FEAT -> UI / PROTOTYPE / TECH / API / ARCH
```

## 当前模板

* [SURFACE_MAP_PACKAGE_TEMPLATE.md](E:\ai\LEE-Lite-skill-first\ssot\mapping\SURFACE_MAP_PACKAGE_TEMPLATE.md)

## 使用规则

* `surface_map_package` 是从 `FEAT` 进入设计层的唯一正式入口。
* `design_impact_required=true` 时，没有 `surface_map_package` 不得进入：
  * `workflow.dev.feat_to_tech`
  * `workflow.dev.feat_to_proto`
  * `workflow.dev.proto_to_ui`
  * `workflow.dev.tech_to_impl`
* 默认 `update existing`，只有跨新长期边界时才允许 `create`。
* `owner` 是长期身份，不是本次 run 的临时名字。
* shared design asset 需要支持反向追踪：
  * `related_feats`
  * `last_updated_by`

## 命名建议

推荐用 `feat_ref` 作为主绑定键，并让 `surface_map_ref` 清楚表达这是一次面向设计层的归属包，例如：

* `surface-map-bundle.md`
* `surface-map-bundle.json`
* `SURFACE-MAP-FEAT-SRC-001-001`

若未来正式引入稳定对象 ID，可在不改变 `feat_ref` 主绑定规则的前提下补充新的 ID 规则。
