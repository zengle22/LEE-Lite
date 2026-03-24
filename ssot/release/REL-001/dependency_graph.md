# REL-001 Dependency Graph

## FEAT Delivery Graph

```text
FEAT-SRC-001-002 -> FEAT-SRC-001-001
FEAT-SRC-001-001 -> FEAT-SRC-001-003
FEAT-SRC-001-001 -> FEAT-SRC-001-004
FEAT-SRC-001-002 -> FEAT-SRC-001-004
FEAT-SRC-001-003 -> FEAT-SRC-001-004
FEAT-SRC-001-001 -> FEAT-SRC-001-005
FEAT-SRC-001-002 -> FEAT-SRC-001-005
FEAT-SRC-001-003 -> FEAT-SRC-001-005
FEAT-SRC-001-004 -> FEAT-SRC-001-005
```

## Recommended Execution Spine

```text
FEAT-SRC-001-002
  -> FEAT-SRC-001-001
  -> FEAT-SRC-001-003
  -> FEAT-SRC-001-004
  -> FEAT-SRC-001-005
```

## Runtime Collaboration Notes

- `FEAT-SRC-001-001` 与 `FEAT-SRC-001-003` 在 FEAT 正文中存在运行态双向协作。
- RELEASE 级依赖图只保留 `delivery_depends_on`，因此这里不把该协作关系视为循环排期依赖。
- 结构化版本见 `feat_dependency_matrix.json`。

## TASK Density Summary

- `FEAT-SRC-001-001`: 2 TASK
- `FEAT-SRC-001-002`: 2 TASK
- `FEAT-SRC-001-003`: 2 TASK
- `FEAT-SRC-001-004`: 3 TASK
- `FEAT-SRC-001-005`: 4 TASK

## Validation Notes

- FEAT Bundle 非空。
- 所有 FEAT 当前均为 `frozen`。
- `delivery_depends_on` 图无循环，可被 downstream planning 拓扑化消费。
- `FEAT-SRC-001-005` 是最下游聚合能力面，适合作为 release scope 的尾部能力切片。
