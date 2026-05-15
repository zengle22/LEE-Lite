---
name: ll-v2-impl-verify
skill: ll-v2-impl-verify
version: "1.0"
adr: ADR-056
category: verify
chain: ll-v2
phase: governance
---

# ll-v2-impl-verify

实施验证与双线路验收工作流 — 对 GSD 交付物执行完成度检查、工程资料检查、范围合规检查、溯源验证，输出验收报告与 recommendation、问题回流分类。

## Interface

- **Input**: `FRZ Package`（frozen 或 revised 状态）+ `GSD Delivery Package`
- **Output**: `VerificationReport`（含 final_verdict、findings、recommendation）
- **Steps**: step_1 任务完成度检查 → step_2 工程资料检查 → step_3 范围合规检查 → step_4 代码变更溯源验证 → step_5 综合判定引擎

## Entry Point

```bash
python skills/ll-v2-impl-verify/src/impl_verify.py --frz <frz-package-path> --gsd <gsd-delivery-dir>
```
