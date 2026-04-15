# Roadmap: ADR-047 双链测试技能实施 + 骨架补全

**Created:** 2026-04-14
**Granularity:** Standard (4 phases, 3-5 plans each)
**Total Requirements:** 6

---

## Phase 1: QA Schema 定义

**Goal:** 建立统一的 QA 测试治理 schema（plan/manifest/spec/settlement 四层资产结构），作为所有 11 个技能的真理源。

**Requirements:** REQ-01

**Plans:** 2 plans — ✅ 已完成

Plans:
- [x] 01-01 — 定义 4 个 YAML schema 文件（plan/manifest/spec/settlement）
- [x] 01-02 — Python dataclass 验证器 + 样例文件 + 单元测试

**Success Criteria:**
1. ✅ `ssot/schemas/qa/` 目录下有 4 个 schema 文件
2. ✅ 每个 schema 包含 ADR-047 §4 定义的所有核心字段
3. ✅ Python dataclass 验证器（`cli/lib/qa_schemas.py`），29 个单元测试通过
4. ✅ 4 个手工样例文件全部通过验证

**UI hint:** no

---

## Phase 2: ADR-047 设计层技能补全

**Goal:** 为 ADR-047 的 6 个设计层技能补上 Prompt-first 运行时（scripts/agents/validate）。

**Requirements:** REQ-02

**Skills in scope:**
1. `ll-qa-feat-to-apiplan` — feat → api-test-plan + manifest 草稿
2. `ll-qa-prototype-to-e2eplan` — prototype → e2e-journey-plan + manifest 草稿
3. `ll-qa-api-manifest-init` — plan → coverage manifest 初始化
4. `ll-qa-e2e-manifest-init` — plan → coverage manifest 初始化
5. `ll-qa-api-spec-gen` — manifest → api-test-spec 编译
6. `ll-qa-e2e-spec-gen` — manifest → e2e-journey-spec 编译

**Each skill gets:**
- `scripts/run.sh` — Claude Code CLI 子代理调用 wrapper
- `agents/executor.md` — LLM prompt 模板（输入/输出格式定义）
- `validate_input.sh` — 输入文件存在性与 schema 校验
- `validate_output.sh` — 输出文件 schema 校验

**Success Criteria:**
1. ✅ 6 个技能各有 6 个新文件（scripts/run.sh, validate_input.sh, validate_output.sh, evidence/*, ll.lifecycle.yaml）
2. ✅ 每个技能的 validate_output.sh 调用 Phase 1 的 qa_schemas 验证器
3. ✅ CLI 已注册 6 个新 action（feat-to-apiplan, prototype-to-e2eplan, api-manifest-init, e2e-manifest-init, api-spec-gen, e2e-spec-gen）
4. ✅ validate_input.sh 拒绝非法输入（文件不存在、schema 不匹配）
5. ✅ 共享运行时 cli/lib/qa_skill_runtime.py 支持所有 6 个技能

**UI hint:** no

---

## Phase 3: 结算层技能 + 兼容层

**Goal:** 补全结算层 2 个技能 + 兼容层 1 个技能；标记废弃 ADR-035 老 skill；注册 CLI 动作 + 扩展运行时映射 + 新增 gate 验证器。

**Requirements:** REQ-03

**Plans:** 4 plans

Plans:
- [x] 03-01 — ll-qa-settlement 基础设施（scripts/run.sh, validate_input.sh, validate_output.sh, evidence schema, ll.lifecycle.yaml）
- [x] 03-02 — ll-qa-gate-evaluate 基础设施（scripts 含 5 输入验证, evidence schema, ll.lifecycle.yaml）
- [x] 03-03 — render-testset-view 新技能（完整目录 13 文件，向后兼容聚合视图）
- [x] 03-04 — CLI 注册 + 运行时映射扩展 + gate 验证器 + 废弃技能标记

**Success Criteria:**
1. ✅ 3 个技能各有 scripts/validate/evidence 基础设施
2. ✅ `ll-qa-gate-evaluate` 的输出符合 ADR-047 §9.4 gate_rules
3. ✅ `render-testset-view` 能聚合 plan/manifest/spec 生成兼容视图
4. ✅ CLI _QA_SKILL_MAP 新增 3 个动作，qa_skill_runtime.py 映射扩展，qa_schemas.py 新增 gate 验证器
5. ✅ ll-test-exec-cli 和 ll-test-exec-web-e2e 有可见的 DEPRECATED 标记

---

## Phase 4: API 链全流程试点

**Goal:** 创建最小 feat YAML，跑通完整 API 测试链（plan → manifest → spec → simulated exec → evidence → settlement → gate），验证双链治理设计可执行，产出 pilot 报告。

**Requirements:** REQ-04, REQ-05, REQ-06

**Plans:** 1 plan

Plans:
- [x] 04-01 — 端到端试点：创建最小 feat → 设计链（plan/manifest/spec）→ 模拟执行 + 证据 → 结算 → gate 评估 → pilot 报告

**Success Criteria:**
1. ✅ 整条链无手工干预（除 LLM 子代理调用外）自动跑通
2. ✅ 每个中间产物文件通过对应 schema 验证
3. ✅ `release_gate_input.yaml` 包含正确的 pass/fail/coverage 统计
4. ✅ 试点结果写入 `.planning/pilot-report.md`，记录所有问题和改进建议

**UI hint:** no

---

## Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-01: QA 统一 schema 定义 | Phase 1 | ✅ Done |
| REQ-02: ADR-047 设计层 6 技能补全 | Phase 2 | ✅ Done |
| REQ-03: 结算/执行层 3 技能 + 额外 2 技能补全 | Phase 3 | ✅ Done |
| REQ-04: 试点跑通 API 链全流程 | Phase 4 | ✅ Done |
| REQ-05: 所有中间产物通过 schema 验证 | Phase 4 | ✅ Done |
| REQ-06: 产出 pilot 报告 + 改进建议 | Phase 4 | ✅ Done |

**Coverage:**
- v1 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0

---
*Roadmap defined: 2026-04-14*
*Last updated: 2026-04-14 after Phase 3 planning*
*Last updated: 2026-04-15 after Phase 4 planning*
*Last updated: 2026-04-15 all phases complete — 100%
