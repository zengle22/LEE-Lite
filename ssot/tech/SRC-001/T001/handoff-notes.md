# Handoff Notes

- 下游 contract design 先固定 request / receipt schema，再细化 operation handler 接口。
- DEVPLAN 应把 Gateway runtime、policy integration、registry hook 视为分阶段实施，而不是单一大任务。
- TESTPLAN 重点覆盖 success / deny / failure / staging retention 四类路径。
