# Roadmap

## Milestones

- **v2.2.1 Failure Case Resolution** — ✓ SHIPPED 2026-04-28
- [v2.2 双链执行闭环](.planning/milestones/v2.2-ROADMAP.md) ✓ SHIPPED 2026-04-24
- v2.1 双链双轴测试强化 ✓ SHIPPED 2026-04-23
- v2.0 ADR-050/051 SSOT 语义治理升级 ✓ SHIPPED 2026-04-22
- v1.1 ADR-049 体验修正层 ✓ SHIPPED 2026-04-21
- v1.0 ADR-047 双链测试 ✓ SHIPPED 2026-04-17

---

## v2.2.1: Failure Case Resolution — Phase Summary

| Phase | Name | Target Requirements | Estimated Plans | Status |
|-------|------|-------------------|----------------|--------|
| 20 | P0 缺陷紧急修复 | FIX-P0-01, FIX-P0-02 | 3 plans | **Complete** |
| 21 | PROTO 相关缺陷修复 | FIX-P1-01, FIX-P1-02 | 3 plans | **Complete** |
| 22 | TECH 和 IMPL 缺陷修复 | FIX-P1-03, FIX-P1-04, FIX-P1-05 | 3 plans | **Complete** |
| 23 | TESTSET 和治理技能修复 | FIX-P1-06, FIX-P1-07, FIX-P1-08 | 3 plans | **Complete** |
| 24 | impl-spec-test 增强和验证 | FIX-P1-09, ENH-P1-01~05 | 3-4 plans | **Complete** |

**Total:** 5 phases, ~12-15 plans

---

## v2.2.1 Phase Details

### Phase 20: P0 缺陷紧急修复

**Goal:** 修复两个P0级缺陷，解决最紧急的阻塞问题。

**Requirements:** FIX-P0-01, FIX-P0-02

**Success Criteria:**
1. SRC003 SSOT 多维度漂移问题解决 — API authority不重复、surface-map所有权正确、TECH/IMPL语义与仓库匹配、legacy src/不再违规增长
2. FEAT 分解按能力边界而非UI表面 — ll-product-epic-to-feat正确拆分，FEAT包含完整能力栈
3. 重新生成的SRC003/SRC004相关SSOT文档验证通过
4. 对应的failure-case文档可以关闭

**Planned Work:**
- 20-01: 分析和修复 SRC003 SSOT 多维度漂移
- 20-02: 分析和修复 ll-product-epic-to-feat 的 FEAT 分解逻辑
- 20-03: 验证修复并关闭相关 failure-cases

---

### Phase 21: PROTO 相关缺陷修复

**Goal:** 修复 ll-dev-feat-to-proto 的低保真问题和旅程闭环拆分问题。

**Requirements:** FIX-P1-01, FIX-P1-02

**Success Criteria:**
1. 菜单遮罩默认不遮挡主内容 — CSS隐藏状态正确
2. 页面内容不泛化占位 — 呈现真实的界面结构和信息密度
3. 旅程闭环不拆成孤立页面 — 保持连贯性，共享surface（wizard/hub+sheets）
4. 重新生成的SRC002/SRC004 PROTO验证高保真可用
5. 对应的failure-case文档可以关闭

**Planned Work:**
- 21-01: 修复 ll-dev-feat-to-proto 的菜单遮罩和页面泛化问题
- 21-02: 修复旅程闭环拆分问题，保持页面连贯性
- 21-03: 验证修复并关闭相关 failure-cases

---

### Phase 22: TECH 和 IMPL 缺陷修复

**Goal:** 修复 ll-dev-feat-to-tech 和 ll-dev-tech-to-impl 的系统性问题。

**Requirements:** FIX-P1-03, FIX-P1-04, FIX-P1-05

**Status:** Complete

**Success Criteria:**
1. ✅ ll-dev-feat-to-tech 主语不再漂移 — 正确聚焦工程基线，不串到ADR-005治理
2. ✅ TECH 模板不再过度共享 — 每份TECH按FEAT切片收敛，只包含本FEAT负责的工程对象
3. ✅ ll-dev-tech-to-impl 执行层不再漂移 — 触点不回到src/be/，不吸入.tmp/external/和ssot/testset/
4. ✅ 任务模型不再套用通用前后端模板 — 针对工程基线FEAT生成对象级任务清单

**Completed Work:**
- 22-01: 修复 ll-dev-feat-to-tech 的主语漂移和模板过度共享问题
- 22-02: 修复 ll-dev-tech-to-impl 的执行层系统性漂移问题
- 22-03: 验证修复并关闭相关 failure-cases

---

### Phase 23: TESTSET 和治理技能修复

**Goal:** 修复 TESTSET、failure-capture、proto-to-ui 的问题。

**Requirements:** FIX-P1-06, FIX-P1-07, FIX-P1-08

**Status:** Complete - All requirements already implemented

**Key Discoveries:**
1. ✅ FIX-P1-06: ll-qa-feat-to-testset was deprecated and removed in v2.2 per ADR-053
2. ✅ FIX-P1-07: ll-governance-failure-capture already outputs to correct location
3. ✅ FIX-P1-08: ll-dev-proto-to-ui already outputs single ui-spec-bundle.md

**Success Criteria:**
1. ✅ TESTSET 不再套用gate模板 — 针对工程基线对象建模（repo layout、apps/api shell、local env等）
2. ✅ governance-failure-capture 输出到正确位置 — tests/defect/failure-cases/，而非artifacts/governance/
3. ✅ proto-to-ui 输出单一文档 — ui-spec-bundle.md包含所有内容，不分离ui-flow-map.md

**Completed Work:**
- All requirements verified to be already implemented - no additional changes needed

---

### Phase 24: impl-spec-test 增强和验证

**Goal:** 修复 impl-spec-test 的中文解析问题，增强多个技能的质量。

**Requirements:** FIX-P1-09, ENH-P1-01, ENH-P1-02, ENH-P1-03, ENH-P1-04, ENH-P1-05

**Success Criteria:**
1. impl-spec-test 能正确识别中文章节标题 — excerpt提取正常，错误报告内容完整
2. ll-dev-feat-to-tech 的api_required判定逻辑正确 — 基于能力边界而非关键词匹配
3. ll-dev-feat-to-tech 强制输出ssot_type声明 — TECH/ARCH/API都有正确的ssot_type
4. API设计包含完整的"前置条件与后置输出"章节
5. IMPL文件自动生成完整source_refs — 包含FEAT/TECH/ARCH/API的完整SSOT路径
6. feat-to-tech完成后自动触发TESTSET生成
7. 所有修复验证通过，所有failure-case文档可以关闭
8. 回归测试确保没有引入新问题

**Planned Work:**
- 24-01: 修复 impl-spec-test 的中文解析问题
- 24-02: 增强 ll-dev-feat-to-tech（api_required、ssot_type、API设计质量）
- 24-03: 增强 ll-dev-tech-to-impl（source_refs生成）和 ll-qa-feat-to-testset（自动触发）
- 24-04: 全面验证和回归测试，关闭所有 failure-cases

---

## Requirement Traceability (v2.2.1)

| Requirement | Phase | Status |
|-------------|-------|--------|
| FIX-P0-01 | 20 | Complete |
| FIX-P0-02 | 20 | Complete |
| FIX-P1-01 | 21 | Complete |
| FIX-P1-02 | 21 | Complete |
| FIX-P1-03 | 22 | Complete |
| FIX-P1-04 | 22 | Complete |
| FIX-P1-05 | 22 | Complete |
| FIX-P1-06 | 23 | Complete |
| FIX-P1-07 | 23 | Complete |
| FIX-P1-08 | 23 | Complete |
| FIX-P1-09 | 24 | Complete |
| ENH-P1-01 | 24 | Complete |
| ENH-P1-02 | 24 | Complete |
| ENH-P1-03 | 24 | Complete |
| ENH-P1-04 | 24 | Complete |
| ENH-P1-05 | 24 | Complete |

**Coverage:** 16/16 requirements mapped (100%)

---

## Phase Dependency Map

```
Phase 19 (v2.2 done)
     │
     ▼
Phase 20 ──> Phase 21 ──> Phase 22 ──> Phase 23 ──> Phase 24
(P0 fix)     (PROTO fix)   (TECH/IMPL)  (TESTSET/gov) (impl-spec/ENH)
     │            │            │             │               │
     └────────────┴────────────┴─────────────┴───────────────┘
                               │
                         All failure-cases closed
```

---

## Risk Notes

| Phase | Risk | Mitigation |
|-------|------|------------|
| 20 | P0修复可能影响现有SSOT | 备份现有SSOT，逐步验证修复 |
| 22 | TECH/IMPL修复范围较大 | 分步骤验证，先修复模板再修复执行层 |
| 24 | 多个技能增强可能引入回归 | 充分的单元测试和回归测试 |

---

*Last updated: 2026-04-28 — Phase 24 complete, v2.2.1 shipped*
