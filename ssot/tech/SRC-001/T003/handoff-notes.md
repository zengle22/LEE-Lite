# Handoff Notes

- contract design 应优先冻结 identity contract、registry record schema 和 formal reference schema。
- DEVPLAN 应把 registry binding 和 read guard 视为两个连续切片，中间不要再插入新的资格判断者。
- TESTPLAN 重点覆盖未注册拒绝、状态不合法拒绝和 lineage trace。
