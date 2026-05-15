---
name: ll-v2-frz-ingest
skill: ll-v2-frz-ingest
version: "1.0"
adr: ADR-056
category: freeze
chain: ll-v2
phase: governance
---

# ll-v2-frz-ingest

SSOT 编译与冻结工作流 — 接收 Complete Design Package，在编译零语义发明约束下执行完整性检查、编译 SSOT 链、对齐检查、漂移检测、生成验收测试用例、输出 FRZ Package 候选。

## Interface

- **Input**: `Complete Design Package` 目录路径
- **Output**: `FRZ Package` 候选（YAML）+ 编译日志
- **Steps**: step_1 完整性检查 → step_2 SSOT 链编译 → step_3 对齐检查 → step_4 漂移检测 → step_5 验收测试用例生成 → step_6 冻结输出

## Entry Point

```bash
python skills/ll-v2-frz-ingest/src/frz_ingest.py --input <design-package-dir> --output <frz-output-dir>
```
