---
created: '2026-04-22T16:00:00+08:00'
title: ADR-052 在v2.1没有进入scope的内容
area: planning
files:
  - ssot/src/SRC-009__adr-052-ssot-semantic-governance-upgrade.md
  - ssot/tech/TECH-009__adr-052-test-governance-technical-design.md
  - ssot/feat/FEAT-009-E__state-machine-execution-and-assertion-model.md
  - ssot/feat/FEAT-009-A__independent-verification-and-audit.md
  - ssot/feat/FEAT-009-S__skill-orchestration-dag-definition.md
---

## Problem

v2.1 milestone 仅覆盖 FEAT-009-D（测试需求轴治理 — 声明性资产分层与枚举冻结），ADR-052 定义的大量内容尚未排期到任何 milestone。这些内容分布在 TECH-009 的 Layer 2/3/4，对应 EPIC-009 下的 3 个未实施 FEAT：

### FEAT-009-E: 测试执行框架（状态机执行与三层断言模型）
- StateMachine 有限状态执行器：9 状态（Phase 1 简化 5 状态），逐节点执行产出结构化证据
- 三层断言模型：A:交互断言 / B:页面结果断言 / C:业务状态断言
- 8 类故障分类：ENV/DATA/SCRIPT/ORACLE/BYPASS/PRODUCT/FLAKY/TIMEOUT
- L0-L3 分层执行模型
- RunManifest 绑定执行时的世界快照（版本/环境/账号/数据）
- 6 条黄金路径（G1-G6）按产品核心价值主张排序
- 4 阶段实施计划（1a/1b/2/3/4）
- **实施轴模块**: environment-provision, run-manifest-gen, scenario-spec-compile, test-data-provision, l0-smoke-check, failure-classifier, settlement, gate-evaluation

### FEAT-009-A: 独立验证与审计
- Verifier 独立认证上下文：不同 API token、不同浏览器 context、不同账号、不同数据快照
- Verifier 一票否决 Gate 规则（FC-004）
- bypass-detector 违规检测：检测 AI 跳步、API 直调、误判行为
- Accident 标准化失败取证包：case_id / manifest / screenshots / traces / network_log / console_log / failure_classification
- failure-classifier 后处理路由：PRODUCT→回归用例、SCRIPT/ORACLE→Spec 更新、FLAKY→重跑确认

### FEAT-009-S: Skill 编排
- qa.test-plan Skill：将需求转化为可执行测试计划，编排 7 个需求轴编译模块
- qa.test-run Skill：在指定环境上跑测试并生成结果和报告，编排 12+ 个实施轴模块，支持 full / last_failed / report_only 模式
- DAG 解析器：模块依赖图、拓扑排序、并行执行
- 17+ 内部模块的接口契约（module_id / axis / input / output）

### Frozen Contracts 未验证部分
- FC-002: 需求轴/实施轴分离契约 — 声明性资产可重新编译，证据性资产只追加（架构性约束，无直接单元测试）

## Solution

需要在后续 milestone（建议 v2.2）中依次实施：
1. FEAT-009-E: 状态机执行 + 三层断言 + 故障分类（执行引擎核心）
2. FEAT-009-A: 独立验证 + 违规检测 + 事故包（可信性闭环）
3. FEAT-009-S: Skill 编排 DAG（用户入口）

每个 FEAT 需要独立的 IMPL 文档、Task Pack 和 TESTSET 映射，遵循 v2.1 已建立的声明性资产分层规则。
