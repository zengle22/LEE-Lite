# Roadmap: v2.0 ADR-050/051 SSOT 语义治理升级

**Created:** 2026-04-18
**Milestone:** v2.0
**Granularity:** Standard (5 phases)
**Total Requirements:** 24 (21 active + 3 deferred to v2.1)

---

## Phase 7: FRZ 冻结层基础设施

**Goal:** 交付 FRZ 包结构定义、MSC 验证、注册表，以及 `ll-frz-manage` 新技能（冻结模式 + 查询模式）。

**Requirements:** FRZ-01, FRZ-02, FRZ-03, FRZ-04, FRZ-05, FRZ-06

**Plans:** 3 plans

- [x] 07-01-PLAN.md — FRZ 包结构定义 + MSC 5维 schema + 单元测试 (FRZ-01, FRZ-02)
- [x] 07-02-PLAN.md — 锚点 ID 注册表 + FRZ 注册表文件 + 版本追踪 (FRZ-03, EXTR-03)
- [x] 07-03-PLAN.md — ll-frz-manage 技能（冻结模式 validate + freeze + list）(FRZ-04, FRZ-05, FRZ-06)

**Success Criteria:**
1. `cli/lib/frz_schema.py` 定义 FRZPackage dataclass + MSCValidator，5维校验通过
2. 人工输入 PRD/UX/Arch 文档 → `ll frz-manage validate` 输出 MSC 报告
3. `ll frz-manage freeze --id FRZ-xxx` 将验证通过的 FRZ 写入注册表，状态 frozen
4. `ll frz-manage list` 列出所有已注册 FRZ 包及状态
5. `ssot/registry/frz-registry.yaml` 记录版本、状态、创建时间

**UI hint:** no

---

## Phase 8: FRZ→SRC 语义抽取链

**Goal:** 交付 `ll-frz-manage` 抽取模式 + SRC/EPIC/FEAT 级联抽取引擎 + 投影不变性守卫 + 漂移检测。

**Requirements:** EXTR-01, EXTR-02, EXTR-03, EXTR-04, EXTR-05

**Plans:**

- [x] 08-01 — `cli/lib/drift_detector.py`: 语义漂移检测器
- [x] 08-02 — `skills/ll-frz-manage` 抽取模式: FRZ → SRC 抽取 + 投影守卫 + 锚点注册 + 漂移检测
- [x] 08-03 — `skills/ll-product-src-to-epic`: 改为 FRZ 抽取 EPIC 模式
- [x] 08-04 — `skills/ll-product-epic-to-feat`: 改为 FRZ 抽取 FEAT 模式

**Success Criteria:**
1. `ll frz-manage extract --frz FRZ-xxx` 输出 SRC candidate，不超出 `derived_allowed` 范围
2. `ll src-to-epic extract --src <dir> --frz FRZ-xxx` 输出 EPIC，锚点 ID 已注册
3. `ll epic-to-feat extract --epic <dir> --frz FRZ-xxx` 输出 FEAT
4. 漂移检测器比对抽取结果与 FRZ 原始语义，漂移 >0 则拦截
5. 完整链路跑通: FRZ → SRC → EPIC → FEAT，所有锚点可追溯

**UI hint:** no

---

## Phase 9: 执行语义稳定 + impl-spec-test 增强

**Goal:** 在 `ll-qa-impl-spec-test` 中集成语义稳定性检查，交付静默覆盖防护。

**Requirements:** STAB-01, STAB-02, STAB-03, STAB-04

**Plans:**

- [x] 09-01 — `cli/lib/silent_override.py`: 静默覆盖检测器
- [x] 09-02 — `skills/ll-qa-impl-spec-test`: 加第9维度 `semantic_stability` (含 drift_detector 调用 + verdict 字段)
- [x] 09-03 — 所有 `ll-dev-*` 技能的 `validate_output.sh`: 加 `silent_override.py` 校验

**Success Criteria:**
1. `ll-qa-impl-spec-test` deep mode 包含 `semantic_stability` 维度，verdict 含 `semantic_drift` 字段
2. impl-spec-test 对漂移的 FEAT/TECH/UI 返回 `block` verdict
3. `ll-dev-feat-to-tech` 等技能的 `validate_output.sh` 检测静默改写 FRZ 语义的行为
4. 变更 vs 补全分类在 impl-spec-test 中正确工作 (clarification 放行，semantic_change 标记漂移)

**UI hint:** no

---

## Phase 10: 变更分级协同

**Goal:** 集成三分类到 Patch 层，交付 Minor/Major 分流处理，Major 回流 FRZ。

**Requirements:** GRADE-01, GRADE-02, GRADE-03, GRADE-04

**Plans:** 4/4 plans complete

Plans:
- [x] 10-01-PLAN.md — `skills/ll-patch-capture`: 集成三分类 (visual→Minor, interaction→Minor, semantic→Major) + GradeLevel enum (GRADE-01)
- [x] 10-02-PLAN.md — `skills/ll-experience-patch-settle`: Minor settle 逻辑 (backwrite UI/TESTSET) (GRADE-02, GRADE-04)
- [x] 10-03-PLAN.md — `skills/ll-frz-manage`: 冻结模式加 `--type revise` 参数 (Major 回流) (GRADE-03)
- [x] 10-04-PLAN.md — `skills/ll-patch-aware-context`: 注入时检测 Minor/Major 变更 (GRADE-04)

**Success Criteria:**
1. `ll-patch-capture` 捕获变更时自动分类，visual/interaction → Minor patch
2. semantic 变更触发 Major 回流: `ll frz-manage freeze --type revise --previous-frz FRZ-xxx`
3. FRZ 注册表记录 revision chain（parent_frz_ref, reason, status）
4. Minor Patch 验证通过后 backwrite 到 UI Spec / Flow Spec
5. `ll-patch-aware-context` 注入时正确标记 Patch 类型

**UI hint:** no

---

## Phase 11: Task Pack 结构（执行循环延期到 v2.1）

**Goal:** 交付 Task Pack YAML schema + depends_on 解析。v2.0 手动按顺序执行 task。

**Requirements:** PACK-01, PACK-02, [PACK-03, PACK-04, PACK-05 deferred to v2.1]

**Plans:** 2 plans

- [ ] 11-01-PLAN.md — `ssot/schemas/qa/task_pack.yaml` + `cli/lib/task_pack_schema.py` + tests (PACK-01)
- [ ] 11-02-PLAN.md — `cli/lib/task_pack_resolver.py` + tests + sample Task Pack (PACK-02)

**Success Criteria:**
1. `task_pack.yaml` schema 定义 pack_id, feat_ref, tasks (task_id, type, depends_on, status, verifies)
2. `validate(pack_yaml)` 拒绝非法结构（缺少 task_id, depends_on 引用不存在等）
3. `resolve_order(pack_yaml)` 返回拓扑排序后的可执行顺序
4. 手工创建一个样例 Task Pack 并通过 schema 验证 + 依赖解析
5. PACK-03/04/05 明确标记 deferred，在 v2.1 Requirements 中追踪

**UI hint:** no

---

## Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FRZ-01 | Phase 7 | Satisfied |
| FRZ-02 | Phase 7 | Satisfied |
| FRZ-03 | Phase 7 | Satisfied |
| FRZ-04 | Phase 7 | Satisfied |
| FRZ-05 | Phase 7 | Satisfied |
| FRZ-06 | Phase 7 | Satisfied |
| EXTR-01 | Phase 8 | Pending |
| EXTR-02 | Phase 8 | Pending |
| EXTR-03 | Phase 7 | Satisfied |
| EXTR-04 | Phase 8 | Pending |
| EXTR-05 | Phase 8 | Pending |
| STAB-01 | Phase 9 | Pending |
| STAB-02 | Phase 9 | Pending |
| STAB-03 | Phase 9 | Pending |
| STAB-04 | Phase 9 | Pending |
| GRADE-01 | Phase 10 | Pending |
| GRADE-02 | Phase 10 | Pending |
| GRADE-03 | Phase 10 | Pending |
| GRADE-04 | Phase 10 | Pending |
| PACK-01 | Phase 11 | Pending |
| PACK-02 | Phase 11 | Pending |
| PACK-03 | Phase 11 | Deferred to v2.1 |
| PACK-04 | Phase 11 | Deferred to v2.1 |
| PACK-05 | Phase 11 | Deferred to v2.1 |

**Coverage:**
- v2.0 requirements: 24 total
- Active (v2.0 in scope): 21
- Deferred to v2.1: 3 (PACK-03, PACK-04, PACK-05)
- Mapped to phases: 21 active + 3 deferred
- Unmapped: 0 ✓

---
*Roadmap created: 2026-04-18*
*Last updated: 2026-04-20 after Phase 11 planning*
