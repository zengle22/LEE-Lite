# Handoff Notes

- contract design 需要先定 finding schema，再定 consumer mapping contract；不要把 auditor 继续扩成投递总线。
- DEVPLAN 应把 IO Contract、auditor、consumer integration 分成三个连续切片。
- TESTPLAN 重点覆盖 unauthorized write、unmanaged read、path drift、repair targeting。
