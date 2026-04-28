# Requirements — v2.2.1 Failure Case Resolution

> Scope: 修复 tests/defect/failure-cases/ 目录下记录的所有缺陷，同时系统性改进相关技能质量
> Requirements gated by: v2.2 已交付（无前置依赖）

---

## Milestone Requirements

### Category: P0 缺陷紧急修复

- [x] **FIX-P0-01**: 修复 SRC003 SSOT 多维度漂移 — API authority 重复、surface-map 所有权漂移、TECH/IMPL 语义与仓库不匹配、legacy src/ 违规增长
- [x] **FIX-P0-02**: 修复 FEAT 分解按 UI 表面而非能力边界的问题 — ll-product-epic-to-feat 应按能力边界拆分，FEAT 应包含完整能力栈（前端+后端）

### Category: PROTO 相关缺陷修复

- [x] **FIX-P1-01**: 修复 ll-dev-feat-to-proto 的低保真问题 — 菜单遮罩默认遮挡、页面内容泛化占位、组件呈现不真实
- [x] **FIX-P1-02**: 修复 ll-dev-feat-to-proto 的旅程闭环拆分问题 — 6个FEAT不应拆成孤立页面，应保持旅程连贯性，共享surface（wizard/hub+sheets）

### Category: TECH 和 IMPL 缺陷修复

- [x] **FIX-P1-03**: 修复 ll-dev-feat-to-tech 的主语漂移 — 从工程基线漂移到ADR-005治理IO/Gateway/Registry的问题
- [x] **FIX-P1-04**: 修复 ll-dev-feat-to-tech 的模板过度共享 — 每份TECH不应重复全工程骨架，应按FEAT切片收敛（只包含本FEAT负责的工程对象）
- [x] **FIX-P1-05**: 修复 ll-dev-tech-to-impl 的执行层系统性漂移 — 触点不应回到src/be/，不应吸入.tmp/external/和ssot/testset/，任务模型不应套用通用前后端模板

### Category: TESTSET 和治理技能修复

- [x] **FIX-P1-06**: 修复 ll-qa-feat-to-testset 的TESTSET套用gate模板问题 — 应针对工程基线对象建模，而非gate decision/formal publish
  - *Note: ll-qa-feat-to-testset was deprecated and removed in v2.2 per ADR-053*
- [x] **FIX-P1-07**: 修复 ll-governance-failure-capture 的位置错误 — 输出应到tests/defect/failure-cases/，而非artifacts/governance/
  - *Note: Already implemented correctly*
- [x] **FIX-P1-08**: 修复 ll-dev-proto-to-ui 的UI-spec输出结构问题 — 应合并为单一文档（ui-spec-bundle.md包含所有内容），而非分离ui-flow-map.md
  - *Note: Already implemented correctly*

### Category: impl-spec-test 增强

- [ ] **FIX-P1-09**: 修复 ll-qa-impl-spec-test 的中文解析问题 — 应能识别中文章节标题（如"### 5.5 完成状态定义"），正确提取excerpt

### Category: 技能质量增强

- [ ] **ENH-P1-01**: 增强 ll-dev-feat-to-tech 的 api_required 判定逻辑 — 基于能力边界而非关键词匹配（FEAT包含后端服务/API层即api_required=true）
- [ ] **ENH-P1-02**: 增强 ll-dev-feat-to-tech 的 ssot_type 声明 — 强制为TECH/ARCH/API输出添加ssot_type声明
- [ ] **ENH-P1-03**: 增强 ll-dev-feat-to-tech 的API设计质量 — 增加"前置条件与后置输出"章节，包含调用者上下文、幂等性、系统依赖前置状态、状态变更、UI表面映射、调用者后续处理流程、事件埋点输出
- [ ] **ENH-P1-04**: 增强 ll-dev-tech-to-impl 的 source_refs 生成 — 自动为IMPL文件生成完整source_refs，包含FEAT/TECH/ARCH/API的完整SSOT路径
- [ ] **ENH-P1-05**: 增强 ll-qa-feat-to-testset 的自动触发 — feat-to-tech完成后自动触发TESTSET生成，无需人工调用

---

## Out of Scope（明确排除）

| Item | Rationale |
|------|-----------|
| 新功能开发 | v2.2.1是Patch版本，仅包含bug修复和质量改进 |
| 架构重构 | 保持v2.2架构不变 |
| ADR-048 Mission Compiler | 继续延期到未来里程碑 |
| 复杂DAG调度 | ADR-050/051明确采用顺序loop |
| 多feat共享ENV粒度管理 | 继续延期 |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FIX-P0-01 | Phase 20 | Complete |
| FIX-P0-02 | Phase 20 | Complete |
| FIX-P1-01 | Phase 21 | Complete |
| FIX-P1-02 | Phase 21 | Complete |
| FIX-P1-03 | Phase 22 | Complete |
| FIX-P1-04 | Phase 22 | Complete |
| FIX-P1-05 | Phase 22 | Complete |
| FIX-P1-06 | Phase 23 | Complete |
| FIX-P1-07 | Phase 23 | Complete |
| FIX-P1-08 | Phase 23 | Complete |
| FIX-P1-09 | Phase 24 | Pending |
| ENH-P1-01 | Phase 24 | Pending |
| ENH-P1-02 | Phase 24 | Pending |
| ENH-P1-03 | Phase 24 | Pending |
| ENH-P1-04 | Phase 24 | Pending |
| ENH-P1-05 | Phase 24 | Pending |

---

## Phase Mappings

| Phase | 目标 | Requirements |
|-------|------|-------------|
| Phase 20 | P0 缺陷紧急修复 | FIX-P0-01, FIX-P0-02 |
| Phase 21 | PROTO 相关缺陷修复 | FIX-P1-01, FIX-P1-02 |
| Phase 22 | TECH 和 IMPL 缺陷修复 | FIX-P1-03, FIX-P1-04, FIX-P1-05 |
| Phase 23 | TESTSET 和治理技能修复 | FIX-P1-06, FIX-P1-07, FIX-P1-08 |
| Phase 24 | impl-spec-test 增强和验证 | FIX-P1-09, ENH-P1-01~05 |

*Phase numbering continues from v2.2 (ended at Phase 19)*

---

## v2.2.1 Coverage Summary

| Metric | Value |
|--------|-------|
| Total requirements | 16 |
| Phase 20 (P0 缺陷紧急修复) | 2 |
| Phase 21 (PROTO 相关缺陷修复) | 2 |
| Phase 22 (TECH 和 IMPL 缺陷修复) | 3 |
| Phase 23 (TESTSET 和治理技能修复) | 3 |
| Phase 24 (impl-spec-test 增强和验证) | 6 |
| Mapped to phases | 16/16 (100%) |
| Unmapped | 0 |

---

*Requirements defined: 2026-04-27*
*Last updated: 2026-04-28 after Phase 22-23 complete*
