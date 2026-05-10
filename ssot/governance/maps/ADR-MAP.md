# ADR Map

Purpose: select ADRs by governance question instead of loading all ADRs.

## Core Governance

| Need | Load |
| --- | --- |
| Runtime object classification | `ssot/adr/ADR-038-运行时核心抽象边界与对象分层基线.MD` |
| SSOT semantic governance | `ssot/adr/ADR-050-SSOT语义治理总纲.md` |
| Experience Patch layer | `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` |
| FRZ freeze layer | `ssot/adr/ADR-045-引入 FRZ 冻结层与全链 Pre-SSOT 集成方案.MD` |
| Dual-chain testing | `ssot/adr/ADR-047-测试体系重建 - 双链治理.md` |
| TaskPack execution loop | `ssot/adr/ADR-051-TaskPack顺序执行循环模式.md` |
| Bug reflow and execution integration | `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` |

## Product Chain

| Need | Load |
| --- | --- |
| Raw input to SRC | `ssot/adr/ADR-002-raw-to-src完整治理方案.MD`, `ssot/adr/ADR-019-raw-to-src 从 Thin Bridge 升级为 High-Fidelity SRC Normalizer.MD`, `ssot/adr/ADR-022-raw-to-src 从 Domain Projector 过渡为 Facet-Based Freeze Architecture.MD` |
| SRC to EPIC | `ssot/adr/ADR-010-src-to-epic Governed Workflow 具体实现冻结方案.MD` |
| EPIC to FEAT | `ssot/adr/ADR-011-EPIC-to-FEAT Lite-Native Skill 逆向 SSOT 基线.MD` |

## Development Chain

| Need | Load |
| --- | --- |
| FEAT to TECH | `ssot/adr/ADR-013-FEAT-to-TECH Lite-Native Skill 设计派生冻结基线.MD` |
| TECH to IMPL | `ssot/adr/ADR-014-TECH-to-IMPL Lite-Native Skill 实施候选冻结基线.MD`, `ssot/adr/ADR-034-IMPL 作为派生执行契约与自包含实施包收敛层.MD` |
| UI and prototype derivation | `ssot/adr/ADR-040-FEAT-to-UI 拆分为 Prototype Freeze 与 UI Spec 派生双阶段基线.MD`, `ssot/adr/ADR-042-FEAT 与 ARCH-UI-PROTOTYPE 解耦并引入 Surface Map 归属层基线.MD` |

## QA and Gate Chain

| Need | Load |
| --- | --- |
| Implementation spec testing | `ssot/adr/ADR-036-IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线.MD` |
| Test execution skill | `ssot/adr/ADR-007-QA Test Execution Governed Skill 标准方案.MD` |
| Testset and coverage | `ssot/adr/ADR-052-测试体系轴化-需求轴与实施轴.md`, `ssot/adr/ADR-053-QA需求轴统一入口与TESTSET废弃.md` |
| Gate runtime | `ssot/adr/ADR-006-External Gate 独立 Skill 化的 Decision 与 Materialization 层.MD`, `ssot/adr/ADR-009-Gate Runtime 采用 CLI-First File Runtime 承载.MD`, `ssot/adr/ADR-016-Gate Skill 作为第二会话 Human Gate Orchestrator 的实现基线.MD` |
