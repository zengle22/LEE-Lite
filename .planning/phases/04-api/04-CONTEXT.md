# Phase 4: API 链全流程试点 - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning
**Source:** Discussion + ADR-047 + existing skill artifacts

<domain>
## Phase Boundary

选一个真实 feat，跑通完整的 API 测试链（plan → manifest → spec → exec → evidence → settlement → gate），
验证双链治理设计可执行。本阶段是端到端试点，不新增技能，而是串联 Phase 1-3 已建立的所有技能。

**试点流程：**
```
新建最小 feat YAML
  → ll-qa-feat-to-apiplan（生成 api-test-plan）
  → ll-qa-api-manifest-init（初始化 manifest）
  → ll-qa-api-spec-gen（编译为 api-test-spec）
  → （单步交互式执行测试 — 由 spec 直接驱动，不走 ll-test-exec-cli）
  → 执行后自动标记 manifest 状态 + 生成 evidence
  → ll-qa-settlement（生成 settlement report）
  → ll-qa-gate-evaluate（生成 release_gate_input.yaml）
```

**成功标准：**
1. 整条链无手工干预自动跑通
2. 每个中间产物通过对应 schema 验证
3. release_gate_input.yaml 包含正确的 pass/fail/coverage 统计
4. 产出 pilot 报告

</domain>

<decisions>
## Implementation Decisions

### 试点 feat 选择
- **D-01:** 新建一个最小可行 feat YAML 作为试点输入（不从现有 api-test-plan 中选）
- **D-02:** 最小 feat 应包含 2-3 个 API 对象、3-5 个 capabilities、覆盖 P0/P1 优先级

### 执行方式
- **D-03:** 采用单步交互式执行 — 一个 skill 调完后停下来检查结果，确认通过再调下一个
- **D-04:** 首次试点需要观察每个环节的输出，不追求全自动批量

### 证据生成
- **D-05:** 测试执行后自动在 manifest 对应 item 上标记 lifecycle_status（executed/passed/failed）和 evidence_status（complete/missing）
- **D-06:** evidence 作为独立文件存放在 `ssot/tests/.artifacts/evidence/` 目录下，按 coverage_id 命名

### 失败处理
- **D-07:** 链中任意环节失败（schema 不通过、skill 报错）时停止执行
- **D-08:** 记录失败原因到 pilot-report，不回退已完成的部分
- **D-09:** 已完成的中间产物保留，便于调试和排查

### Claude's Discretion
- 最小 feat YAML 的具体内容（API 对象、capabilities 选择）
- 测试执行时的具体断言验证方式
- pilot-report 的详细格式（只要包含失败记录和成功标准即可）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ADR / Architecture
- `ssot/adr/ADR-047-测试体系重建 - 双链治理.md` — 完整双链治理架构，§4 定义 schema 字段，§9.4 定义 gate rules，§10 定义 settlement 格式

### QA Schemas (Phase 1)
- `ssot/schemas/qa/plan.yaml` — plan schema 定义
- `ssot/schemas/qa/manifest.yaml` — manifest schema 定义
- `ssot/schemas/qa/spec.yaml` — spec schema 定义
- `ssot/schemas/qa/settlement.yaml` — settlement schema 定义
- `cli/lib/qa_schemas.py` — Python dataclass 验证器 + validate_file 入口 + validate_gate

### CLI Protocol
- `cli/commands/skill/command.py` — Skill command handler with _QA_SKILL_MAP（9 个 QA 动作）
- `cli/lib/qa_skill_runtime.py` — 共享 QA 技能运行时

### QA Skills (Phase 2-3)
- `skills/ll-qa-feat-to-apiplan/` — feat → api-test-plan
- `skills/ll-qa-api-manifest-init/` — plan → coverage manifest
- `skills/ll-qa-api-spec-gen/` — manifest → api-test-spec
- `skills/ll-qa-settlement/` — manifest → settlement report
- `skills/ll-qa-gate-evaluate/` — manifests + settlements → release_gate_input.yaml

### Phase 2-3 Context
- `.planning/phases/03-settlement-exec/01-CONTEXT.md` — Phase 3 的决策和技能边界
- `.planning/phases/01-qa-schema/01-CONTEXT.md` — Phase 1 的 schema 设计决策

### Phase 1 Artifacts (existing test plans for reference)
- `ssot/tests/api/FEAT-SRC-001-001/api-test-plan.md` — 参考现有 plan 格式
- `ssot/tests/templates/feat-to-api-test-plan.md` — 参考模板

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli/lib/qa_schemas.py` — 完整的 dataclass 定义 + validate_file() + validate_gate() + CLI 入口，可直接调用
- `cli/lib/qa_skill_runtime.py` — 共享运行时，支持 9 个 QA 技能动作
- `ssot/schemas/qa/` — 4 个 YAML schema 文件，每个包含字段定义和枚举值
- `skills/` — 9 个 QA 技能目录，每个有 scripts/run.sh + validate 脚本

### Established Patterns
- Prompt-first 模式：scripts/run.sh 调用 Claude Code 子代理 + agents/executor.md prompt
- validate_input.sh 检查输入文件存在性和 schema 匹配
- validate_output.sh 调用 qa_schemas.py 验证器
- ll.lifecycle.yaml 定义状态机（draft → validated → executed → frozen）

### Integration Points
- `cli/ll.py` — 主 CLI 入口，`ll skill <action>` 协议
- `cli/commands/skill/command.py` — _QA_SKILL_MAP 注册 9 个动作
- Phase 1 的 schema 验证器通过 `python -m cli.lib.qa_schemas` 调用

</code_context>

<specifics>
## Specific Ideas

- 最小 feat 应足够简单（2-3 API 对象、3-5 capabilities），但覆盖 P0 和 P1 优先级
- 试点流程每个中间产物都需要 schema 验证通过
- 首次试点不追求速度，重点是验证链路的正确性和可观测性
- pilot-report 应记录：每个环节的输入/输出文件路径、schema 验证结果、失败记录（如有）、改进建议
- settlement 的 statistics 需要自洽：executed = passed + failed + blocked
- gate evaluation 的 7 个 anti-laziness checks 全部为 deterministic 计算

</specifics>

<deferred>
## Deferred Ideas

- E2E 链全流程试点（v2 REQ-10）— 后续阶段
- Python 生产级 CLI 运行时（v2 REQ-20）— 后续阶段
- CI 接入 release gate（v2 REQ-21）— 后续阶段
- Phase 2 的 6 个设计层技能尚未执行，试点可能间接验证

</deferred>

---

*Phase: 04-api*
*Context gathered: 2026-04-14 via discussion*
