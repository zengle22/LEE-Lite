# Phase 25: Bug 注册表与状态机 - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Bug 发现的原始观察能被持久化追踪（bug_registry.py），状态机支持完整流转和终止处理，与现有 test-run 执行链（test_orchestrator.py）集成。Phase 25 产出 3 个核心模块 + 1 个集成点，不含验收层逻辑（Phase 26）和验证/CLI（Phase 27）。

</domain>

<decisions>
## Implementation Decisions

### 状态机实现
- **D-01:** 在 bug_registry.py 中独立实现状态机，不复用 state_machine_executor.py
- **D-02:** 用 `BUG_STATE_TRANSITIONS` dict 定义流转矩阵，每个转换通过 `transition_bug_status()` 函数执行
- **D-03:** YAML 持久化复用 frz_registry.py 的原子写入模式（tempfile + os.replace）

### 与 test_orchestrator 集成
- **D-04:** test_orchestrator.py 的 `run_spec_test()` 新增 `on_complete=None` 回调参数，同步 bug 通过注入回调实现
- **D-05:** `sync_bugs_to_registry()` 作为回调函数提供，test_orchestrator 不直接 import bug_registry

### Bug ID 生成
- **D-06:** bug_id 格式为 `BUG-{case_id}-{md5_hash_6char}`，hash 基于 `case_id + run_id + timestamp`
- **D-07:** 同一 case 不同次失败产生不同 bug_id，通过 `resurrected_from` 字段关联历史记录

### 终止状态与清理
- **D-08:** not_reproducible N 阈值按测试层级：Unit=3, Integration=4, E2E=5
- **D-09:** gate PASS 后 detected bug 降级为 archived，连续 3 次未进入 gap_list 则流转 not_reproducible

### Severity 分级
- **D-10:** 系统自动初分 + 人工覆盖（`ll-bug-transition --severity`），初分规则按 ADR-055 §5.1

### Gap Type
- **D-11:** MVP 3 种 gap_type：code_defect / test_defect / env_issue，自动推断 + 人工覆盖
- **D-12:** 推断规则：flaky → env_issue，stack trace 在测试代码 → test_defect，默认 → code_defect

### Phase 生成（bug_phase_generator.py）
- **D-13:** 默认单 bug 单 phase，`--batch` 支持 mini-batch（max 2-3 同 feat 同模块 bug 聚合）
- **D-14:** 生成目录 `.planning/phases/{N}-bug-fix-{bug_id}/` 包含 CONTEXT.md + PLAN.md（6 个标准 tasks）+ DISCUSSION-LOG.md + SUMMARY.md
- **D-15:** 所有 bug-fix phase 标记 `autonomous: false`（MVP 人工确认）

### Claude's Discretion
- build_bug_bundle() 和 test_exec_reporting.py 的集成粒度由 planner 决定
- 乐观锁 version 字段的生成方式（UUID vs timestamp hash）由 planner 决定
- bug_phase_generator.py 生成的 PLAN.md 6 个 tasks 的具体内容模板由 planner 决定

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ADR (架构决策)
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` — 主设计文档，§2.1-§2.16 覆盖所有决策，§3 实现计划，§6 验收标准
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` §2.2 — 状态机完整流转矩阵（9 状态 + 终止状态）
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` §2.3 — bug-registry.yaml 完整 schema
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` §2.4 — GSD fix phase 生成机制 + mini-batch 策略
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` §2.5 — 修复 phase 6 个标准 tasks
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` §2.9 — 执行主体矩阵（LLM / 脚本 / 人类）
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` §2.8A — Handoff 契约（乐观锁 + 并发控制）
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` §5.1 — 开放问题展开（OQ-2~6 推荐方案）

### 现有模块（需读取以复用模式）
- `cli/lib/frz_registry.py` — YAML 原子写入模式（tempfile + os.replace），_load_registry / _save_registry 复用
- `cli/lib/test_orchestrator.py` — run_spec_test() 主流程，update_manifest() 乐观锁模式，_get_failed_coverage_ids()
- `cli/lib/test_exec_reporting.py` — build_bug_bundle() 现有实现（如存在），case_results 数据结构
- `cli/lib/state_machine_executor.py` — 参考其 _get_valid_transitions() 模式（不复用代码，只参考设计思路）

### 依赖 ADR
- `ssot/adr/ADR-054-实施轴桥接与执行闭环.md` — test_orchestrator 的上游设计
- `ssot/adr/ADR-053-需求轴统一入口.md` — case_id 命名规范

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frz_registry.py` 的 `_load_registry()` / `_save_registry()` + 原子写入 — bug_registry.py 直接复制此模式
- `test_orchestrator.py` 的 `update_manifest()` 乐观锁（version 字段 + UUID 生成）— bug-registry 乐观锁参考此实现
- `test_orchestrator.py` 的 `_get_failed_coverage_ids()` — 读取 manifest 获取失败 case，build_bug_bundle() 可复用此逻辑
- `registry_store.py` 的 CRUD 模式（save/load/list）— JSON 而非 YAML，但 API 设计可参考

### Established Patterns
- YAML 持久化：`yaml.safe_load()` + `yaml.dump()` + `tempfile.mkstemp()` + `os.replace()` — 所有 registry 统一模式
- 乐观锁：version 字段（UUID 或 timestamp hash），写入前比对，冲突抛异常
- StepResult 契约：所有 CLI 模块返回 `StepResult(ok, data, error)` — bug_registry 也应遵循
- 测试组织：`test_*.py` 与源文件同目录，pytest 标记 `@pytest.mark.unit`

### Integration Points
- `run_spec_test()` Step 3→4 之间（或 Step 4 之后）注入 `on_complete` 回调 → `sync_bugs_to_registry()`
- `cli/commands/skill/command.py` — CLI 入口，注册 `ll-qa-test-run` 命令并注入回调
- `artifacts/bugs/{feat_ref}/bug-registry.yaml` — 新建目录，当前不存在
- `tests/defect/failure-cases/` — 已有目录，bug_phase_generator 生成 BUG-{id}.md 到此处

</code_context>

<specifics>
## Specific Ideas

- 状态机实现参考 frz_registry.py 的代码结构（30 行左右实现 _load/_save），不要引入新抽象层
- on_complete 回调签名：`(workspace_root, feat_ref, proto_ref, run_id, case_results) -> None`
- bug_id hash 用 MD5 前 6 位即可（不需要密码学强度，只做碰撞分散）
- bug_phase_generator.py 的 PLAN.md 6 tasks 模板完全参照 ADR-055 §2.5 的 task 定义

</specifics>

<deferred>
## Deferred Ideas

- 通用 YamlRegistry 抽象层（选项 C 组合模式）— 当有 2+ 个 registry 消费者时再提取
- PR Check 层的 shadow fix 检测（ADR-055 §2.10 第二层）— Phase 27 再做
- 多 feat 并行冲突策略（ADR-055 §2.11）— MVP 假设单 feat，v2 再处理
- batch 聚合逻辑从 Execution 层迁移至 Gate 层（Winston 审计意见）— v2 优化

</deferred>

---

*Phase: 025-bug-registry-state-machine*
*Context gathered: 2026-04-29*
