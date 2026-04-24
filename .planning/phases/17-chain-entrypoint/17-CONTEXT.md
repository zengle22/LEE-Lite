# Phase 17: 双链统一入口 + spec 桥接跑通 - Context

**Gathered:** 2026-04-24
**Status:** Ready for planning

<domain>
## Phase Boundary

构建需求轴统一入口 Skill（ll-qa-api-from-feat, ll-qa-e2e-from-proto），废弃 TESTSET 策略层，补齐 SPEC_ADAPTER_COMPAT 桥接，打通 spec → 实施的完整路径，ll-qa-test-run 用户入口就绪。

Requirements: ENTRY-01~04, BRIDGE-01~08, ENV-01~02, TEST-01

**Domain type:** Skill orchestration + Bridge implementation (CLI modules) — NOT a UI/visual feature

</domain>

<spec_lock>
## Requirements (locked via SPEC.md)

**2 specs are locked.** See canonical refs below for full requirements.

Downstream agents MUST read ADR-053 and ADR-054 before planning or implementing. Requirements are not duplicated here.

**In scope (from ADR-053/054):**
- ll-qa-api-from-feat Skill（统一入口，编排 api 子链）
- ll-qa-e2e-from-proto Skill（统一入口，编排 e2e 子链）
- acceptance traceability（acceptance → capability/journey 追溯表）
- SPEC_ADAPTER_COMPAT 格式 + spec_adapter.py
- environment_provision.py（ENV 文件自动生成）
- test_orchestrator.py（含 StepResult + manifest 更新乐观锁）
- ll-qa-test-run Skill（用户入口，支持 --resume）
- test_exec_runtime.py 兼容性修改（SPEC_ADAPTER_COMPAT 分支）
- Phase 1 集成测试（API chain 端到端）

**Out of scope (from ADR-053/054):**
- ADR-048 Mission Compiler — 替代 SPEC_ADAPTER_COMPAT 的长期方案
- run_manifest_gen.py, scenario_spec_compile.py, state_machine_executor.py — Phase 18
- independent_verifier.py, settlement 集成, gate-evaluate 集成 — Phase 19

</spec_lock>

<decisions>
## Implementation Decisions

### Orchestrator mechanism (ENTRY-01/02)
- **D-01:** ll-qa-api-from-feat 和 ll-qa-e2e-from-proto 的 orchestrator 是 **AI agent**（`agents/orchestrator.md`），通过 **Skill tool `/ll-xxx` 调用**序列执行子 skill，**不是** CLI runtime 脚本
  - 子 skill 之间的调用链：Skill tool → `/ll-qa-feat-to-apiplan` → `/ll-qa-api-manifest-init` → `/ll-qa-api-spec-gen`
  - 每个子 skill 独立、可单独调用
  - error_handling: fail-fast at apiplan/manifest_init, continue on spec_gen failure

### StepResult dataclass (BRIDGE-06)
- **D-02:** `StepResult` dataclass 位于 `cli/lib/contracts.py`（新建共享 DTO 文件）
  - 这是 CLI 模块（test_orchestrator.py）内部 Step 3 → Step 4 的数据传递契约
  - 与 AI agent orchestrator **无关**
  - 字段：`run_id`, `execution_refs`, `candidate_path`, `case_results`, `manifest_items`, `execution_output_dir`

### Manifest concurrency (BRIDGE-07)
- **D-03:** manifest 更新使用 **timestamp + version 乐观锁**（Windows 兼容）
  - 不使用 fcntl.flock（POSIX only，Windows 上无效）
  - 每次更新比较 `_version` 字段，变更则重试

### --resume persistence (BRIDGE-08)
- **D-04:** --resume 使用 **run manifest per execution** 机制
  - **Phase 17 临时方案：** 直接读写 coverage manifest 的 `lifecycle_status` 字段（inline）
  - **Phase 18：** 迁移到 run_manifest_gen.py 生成的独立 run-manifest.yaml
  - 迁移路径清晰：Phase 17 产出物不变，只是读取位置从 manifest 变为 run-manifest

### Other locked points
- **D-05:** ll-qa-test-run Skill 是独立的 CLI skill，通过 `python -m cli skill qa-test-run` 调用
  - 不属于 ll-qa-api-from-feat/e2e-from-proto 统一入口
  - 支持 `--app-url` / `--api-url`（分离架构）、`--chain both`（双链）
- **D-06:** test_orchestrator.py 是 CLI 模块，不是 AI agent
  - 线性编排：Step 1 env → Step 2 adapter → Step 3 exec → Step 4 manifest update

### Claude's Discretion
- 具体的 orchestrator prompt 措辞和 error handling 细节
- SPEC_ADAPTER_COMPAT YAML 的具体字段命名（遵循 ADR-054 §2.2 映射规则即可）
- spec_adapter.py 的内部实现结构
- environment_provision.py 的具体实现

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core design specs
- `ssot/adr/ADR-053-QA需求轴统一入口与TESTSET废弃.md` — 需求轴统一入口设计（含 orchestrator state machine、acceptance traceability 规范）
- `ssot/adr/ADR-054-实施轴接入需求轴-双链桥接与执行闭环.md` — spec 桥接设计（含 SPEC_ADAPTER_COMPAT 格式、environment_provision、test_orchestrator、StepResult 契约）

### Skill structure (existing patterns to follow)
- `skills/ll-qa-feat-to-apiplan/SKILL.md` — 现有 skill 模板（SKILL.md + ll.contract.yaml + input/output/contract.yaml + agents/executor.md + agents/supervisor.md）
- `skills/ll-qa-feat-to-apiplan/agents/executor.md` — 子 skill executor prompt 格式
- `skills/ll-test-exec-cli/agents/executor.md` — CLI skill executor 格式参考

### CLI modules (to modify/create)
- `cli/lib/test_exec_runtime.py` §2.4 — SPEC_ADAPTER_COMPAT 分支修改位置
- `cli/commands/skill/command.py` §17-19 — action 路由，qa-test-run 需要加入
- `cli/lib/qa_skill_runtime.py` — skill runtime（参考，不是修改对象）

### Existing skills (do not modify their output contracts)
- `skills/ll-qa-feat-to-apiplan/` — 输出 api-test-plan.md（含 acceptance traceability 表）
- `skills/ll-qa-prototype-to-e2eplan/` — 输出 e2e-journey-plan.md（含 acceptance traceability 表）
- `skills/ll-qa-api-manifest-init/` — 输出 api-coverage-manifest.yaml
- `skills/ll-qa-e2e-manifest-init/` — 输出 e2e-coverage-manifest.yaml
- `skills/ll-qa-api-spec-gen/` — 输出 api-test-spec/*.md
- `skills/ll-qa-e2e-spec-gen/` — 输出 e2e-journey-spec/*.md

### Requirements
- `.planning/REQUIREMENTS.md` §需求轴统一入口（ENTRY-01~04）、§spec 桥接层（BRIDGE-01~08）、§环境管理层（ENV-01~02）、§集成测试（TEST-01）
- `.planning/ROADMAP.md` §Phase 17 — Phase goal and success criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `skills/ll-qa-feat-to-apiplan/` — 完整 skill 目录结构，可直接复用为 ll-qa-api-from-feat 的模板
- `skills/ll-qa-feat-to-apiplan/evidence/` — execution evidence schema（可参考）
- `cli/lib/test_exec_runtime.py:154` — `_validate_testset_execution_boundary()` 是 SPEC_ADAPTER_COMPAT 分支的修改位置

### Established Patterns
- Skill 目录结构：SKILL.md + ll.contract.yaml + input/contract.yaml + output/contract.yaml + agents/orchestrator.md（新增） + agents/supervisor.md（新增）+ evidence/
- CLI skill action 注册：`cli/commands/skill/command.py` 的 `_skill_handler()` 分支
- orchestrator agent prompt：遵循 ADR-053 §2.3.1 state machine 格式

### Integration Points
- ll-qa-test-run action 需要注册到 `cli/commands/skill/command.py` 第 19 行的 action 白名单
- spec_adapter.py 输出到 `ssot/tests/.spec-adapter/{id}.yaml`
- environment_provision.py 输出到 `ssot/environments/ENV-{id}.yaml`（新建目录）
- ll-qa-feat-to-testset 废弃：需要在 `cli/lib/enum_guard.py` 等处标记 deprecated

</code_context>

<specifics>
## Specific Ideas

- acceptance traceability 表必须在 api-plan/e2e-Plan 生成时同步产出，不接受后补
- --resume 在 Phase 17 使用 manifest inline 方案，Phase 18 平滑迁移到 run_manifest
- SPEC_ADAPTER_COMPAT 的 `_source_coverage_id` 必须从 spec 文件携带到 unit，确保 manifest 追溯链不断

</specifics>

<deferred>
## Deferred Ideas

**Phase 18：**
- run_manifest_gen.py（EXEC-01）— --resume 迁移目标
- scenario_spec_compile.py（EXEC-02）— e2e spec → scenario spec
- state_machine_executor.py（EXEC-03）— 3-state 模型

**Phase 19：**
- independent_verifier.py（GATE-01）
- ll-qa-settlement/GATE-02/GATE-03

**Future：**
- ADR-048 Mission Compiler — 废弃 SPEC_ADAPTER_COMPAT 桥接层
- 多 feat 共享 ENV 粒度管理（OQ-2）— Phase 2 review

</deferred>

---

*Phase: 17-chain-entrypoint*
*Context gathered: 2026-04-24*
