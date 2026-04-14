# Roadmap: ADR-047 双链测试技能实施 + 骨架补全

**Created:** 2026-04-14
**Granularity:** Standard (4 phases, 3-5 plans each)
**Total Requirements:** 6

---

## Phase 1: QA Schema 定义

**Goal:** 建立统一的 QA 测试治理 schema（plan/manifest/spec/settlement 四层资产结构），作为所有 11 个技能的真理源。

**Requirements:** REQ-01

**Plans:** 2 plans

Plans:
- [ ] 01-01-PLAN.md — 定义 4 个 YAML schema 文件（plan/manifest/spec/settlement）
- [ ] 01-02-PLAN.md — Python dataclass 验证器 + 样例文件 + 单元测试

**Success Criteria:**
1. `ssot/schemas/qa/` 目录下有 4 个 schema 文件（plan.yaml, manifest.yaml, spec.yaml, settlement.yaml）
2. 每个 schema 包含 ADR-047 §4 定义的所有核心字段
3. 提供 Python dataclass 验证器（`cli/lib/qa_schemas.py`），能校验 YAML 文件是否符合 schema
4. 用一个手工编写的样例文件通过验证器测试

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
1. 6 个技能各有 4 个新文件（共 24 个文件）
2. 每个技能的 `validate_output.sh` 能调用 Phase 1 的 schema 验证器
3. 用 `tests/fixtures/` 下的样例输入能跑通每个技能的 dry-run
4. `validate_input.sh` 拒绝非法输入（文件不存在、schema 不匹配）

**UI hint:** no

---

## Phase 3: 结算/执行层技能 + 额外技能补全

**Goal:** 补全 ADR-047 的结算/执行层 3 个技能 + ll-skill-install + ll-dev-feat-to-tech。

**Requirements:** REQ-03

**Skills in scope:**
1. `ll-qa-settlement` — evidence + manifest → settlement report
2. `ll-qa-gate-evaluate` — settlement + waiver → release_gate_input.yaml
3. `ll-test-exec-cli` — spec → script → exec → evidence（半空→完整）
4. `ll-skill-install` — 技能安装/注册工具
5. `ll-dev-feat-to-tech` — feat → tech spec（补测试覆盖）

**Success Criteria:**
1. 5 个技能各有 4 个新文件（共 20 个文件）
2. `ll-test-exec-cli` 的 `scripts/run.sh` 能调用现有 Playwright 执行器
3. `ll-qa-gate-evaluate` 的输出符合 ADR-047 §9.4 的 gate_rules schema
4. 所有技能的 validate 脚本通过

**UI hint:** no

---

## Phase 4: API 链全流程试点

**Goal:** 选一个真实 feat，跑通完整的 API 测试链（plan → manifest → spec → exec → evidence → settlement → gate），验证双链治理设计可执行。

**Requirements:** REQ-04, REQ-05, REQ-06

**Pilot flow:**
```
选择一个真实 feat YAML
  → ll-qa-feat-to-apiplan（生成 api-test-plan + manifest 草稿）
  → ll-qa-api-manifest-init（冻结 manifest）
  → ll-qa-api-spec-gen（编译为 api-test-spec）
  → ll-test-exec-cli（执行测试，收集证据）
  → ll-qa-settlement（生成 settlement report）
  → ll-qa-gate-evaluate（生成 release_gate_input.yaml）
```

**Success Criteria:**
1. 整条链无手工干预（除 LLM 子代理调用外）自动跑通
2. 每个中间产物文件通过对应 schema 验证
3. `release_gate_input.yaml` 包含正确的 pass/fail/coverage 统计
4. 试点结果写入 `.planning/pilot-report.md`，记录所有问题和改进建议

**UI hint:** no

---

## Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-01: QA 统一 schema 定义 | Phase 1 | Planned |
| REQ-02: ADR-047 设计层 6 技能补全 | Phase 2 | Pending |
| REQ-03: 结算/执行层 3 技能 + 额外 2 技能补全 | Phase 3 | Pending |
| REQ-04: 试点跑通 API 链全流程 | Phase 4 | Pending |
| REQ-05: 所有中间产物通过 schema 验证 | Phase 4 | Pending |
| REQ-06: 产出 pilot 报告 + 改进建议 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0

---
*Roadmap defined: 2026-04-14*
*Last updated: 2026-04-14 after Phase 1 planning*
