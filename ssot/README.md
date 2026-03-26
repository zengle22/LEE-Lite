# SSOT Baseline

本目录的后续版本基线由 `ADR-008` 统一定义：

* 规范入口：`ssot/adr/ADR-008-SSOT 主链、派生对象与文件标准统一基线.MD`
* 生效范围：SSOT 对象模型、对象命名、最小字段、目录建议、历史兼容解释

## Canonical Object Model

正式主链：

```text
RAW -> SRC -> EPIC -> FEAT
```

FEAT 派生对象：

```text
FEAT
 ├─> ARCH?
 ├─> TECH
 ├─> API?
 ├─> IMPL
 ├─> TESTSET
 └─> UI?
```

发布事实对象：

```text
RELEASE_NOTE
```

## Canonical Rules

* `RAW` 不是 SSOT，只是输入池。
* `SRC`、`EPIC`、`FEAT` 是主链 SSOT。
* `TECH`、`IMPL`、`TESTSET` 是围绕 `FEAT` 的派生 SSOT。
* `API` 只要承载跨边界契约，就应作为正式 SSOT 对象存在。
* `UI` 是可选对象，不是每个 FEAT 必须具备。
* `RELEASE_NOTE` 是发布后的事实记录对象。

## Canonical Naming

除 `ADR-*` 与 `SRC-*` 外，当前 active SSOT 对象都应显式带上所属 `SRC` 编号，方便一眼看出它属于哪条 `SRC` 链。

推荐编号风格：

* `EPIC-SRC-001-001__...`
* `FEAT-SRC-001-001__...`
* `ARCH-SRC-001-001__...`
* `TECH-SRC-001-001__...`
* `API-SRC-001-001__...`
* `IMPL-SRC-001-001__...`
* `TESTSET-SRC-001-001__...`
* `UI-SRC-001-001__...`

解释：

* 第一段对象前缀表达对象类型。
* `SRC-001` 表达它属于哪条 `SRC` 主链。
* 末段三位序号表达该对象在该 `SRC` 链中的稳定槽位。
* `FEAT` 及其直接派生对象应优先共享同一个 `SRC` lineage 槽位；例如 `FEAT-SRC-001-004` 的直接派生对象应优先写作 `TECH-SRC-001-004`、`IMPL-SRC-001-004`、`TESTSET-SRC-001-004`。

## Deprecated As Canonical SSOT

以下对象不再作为未来标准主对象扩张：

* `TASK`
* `DEVPLAN`
* `TESTPLAN`

兼容解释：

* 历史 `TASK-*` 按历史 `IMPL` 理解。
* 历史 `DEVPLAN-*`、`TESTPLAN-*` 按编排视图理解。
* 历史 `REL-*` 或 `RELEASE` 若表达发布规划，可保留为历史对象；新的发布事实记录应优先采用 `RELEASE_NOTE`。

## Recommended Paths For Future Revisions

未来版本推荐目录：

* `ssot/src/`
* `ssot/epic/`
* `ssot/feat/`
* `ssot/tech/`
* `ssot/api/`
* `ssot/impl/`
* `ssot/testset/`
* `ssot/ui/`
* `ssot/release_note/`
* `ssot/adr/`

本说明不要求立刻迁移历史目录，只定义后续收敛方向。
