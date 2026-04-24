# Requirements — v2.2 双链执行闭环

> Scope: ADR-053 (需求轴统一入口) + ADR-054 (实施轴桥接)
> Requirements gated by: 无前置依赖（ADR 设计已完成）

---

## Milestone Requirements

### Category: 需求轴统一入口（ADR-053）

- [ ] **ENTRY-01**: 构建 `ll-qa-api-from-feat` Skill — 统一入口，编排 feat → api-test-plan → api-manifest → api-spec 子链，输出 acceptance traceability
- [ ] **ENTRY-02**: 构建 `ll-qa-e2e-from-proto` Skill — 统一入口，编排 prototype → e2e-plan → e2e-manifest → e2e-spec 子链，输出 acceptance traceability
- [ ] **ENTRY-03**: 补齐 acceptance traceability — 在 api-plan 和 e2e-plan 中增加显式 acceptance → capability/journey 追溯表
- [ ] **ENTRY-04**: 废弃 `ll-qa-feat-to-testset` — 停止维护，从 ll.contract.yaml 移除上游依赖

### Category: spec 桥接层（ADR-054 Phase 1）

- [ ] **BRIDGE-01**: SPEC_ADAPTER_COMPAT 格式规范 — spec 文件 → TESTSET unit 字段映射，含 `_source_coverage_id` 追溯和 `_api_extension` / `_e2e_extension` 扩展
- [ ] **BRIDGE-02**: `spec_adapter.py`（API spec）— 解析 `api-test-spec/*.md`，输出 SPEC_ADAPTER_COMPAT YAML，携带 `_source_coverage_id`
- [ ] **BRIDGE-03**: `spec_adapter.py`（E2E spec）— 解析 `e2e-journey-spec/*.md`，输出 SPEC_ADAPTER_COMPAT YAML，携带 `_source_coverage_id` + `_e2e_extension`
- [ ] **BRIDGE-04**: E2E spec `target_format` 字段规范 — 补充 ADR-047 E2E spec 格式，定义 `target_format`（css_selector/xpath/semantic/text）
- [ ] **BRIDGE-05**: `test_exec_runtime.py` 兼容性修改 — `_validate_testset_execution_boundary()` 增加 `SPEC_ADAPTER_COMPAT` 分支，向后兼容 TESTSET 路径
- [ ] **BRIDGE-06**: `StepResult` dataclass + 数据传递契约 — `execute_test_exec_skill()` 返回 `execution_refs` + `manifest_items`，显式传递给 `update_manifest()`
- [ ] **BRIDGE-07**: `test_orchestrator.py` 编排函数 — 线性编排 env → adapter → exec → manifest update，含乐观锁防竞态
- [ ] **BRIDGE-08**: `ll-qa-test-run` Skill — 用户入口 CLI，支持 `--app-url`/`--api-url`（分离架构）、`--resume`/`--resume-from`（重跑）、`--chain both`（双链）

### Category: 环境管理层（ADR-054 Phase 1）

- [ ] **ENV-01**: `environment_provision.py` — 从 feat.environment_assumptions + 用户参数生成 `ssot/environments/ENV-*.yaml`，支持 `--app-url`/`--api-url`/`--browser`
- [ ] **ENV-02**: `ssot/environments/` 目录结构 + `.gitkeep`

### Category: 实施轴补全（ADR-054 Phase 2）

- [ ] **EXEC-01**: `run_manifest_gen.py` — 每次执行生成唯一 `run-manifest.yaml`，绑定 git sha/frontend build/backend build/base_url/browser/accounts
- [ ] **EXEC-02**: `scenario_spec_compile.py`（简化版）— e2e spec → scenario spec，含 A/B 两层断言，C 层标记 `C_MISSING`
- [ ] **EXEC-03**: `state_machine_executor.py`（3-state 模型）— SETUP → EXECUTE → VERIFY → COLLECT → DONE，非 DONE 失败统一进入 COLLECT

### Category: 验收闭环（ADR-054 Phase 3）

- [ ] **GATE-01**: `independent_verifier.py` — 独立于 runner 的验证报告（verdict: pass/conditional_pass/fail），含置信度
- [ ] **GATE-02**: settlement 集成 — `ll-qa-settlement` 消费更新后的 manifest，产出 settlement report
- [ ] **GATE-03**: gate-evaluate 集成 — `ll-qa-gate-evaluate` 基于更新后的 manifest 产出 gate 结论

### Category: 集成测试

- [ ] **TEST-01**: API chain 端到端测试 — `qa.test-run --feat-ref FEAT-SRC-003-001 --app-url http://localhost:8000`，验证 manifest 更新 + settlement 可消费
- [ ] **TEST-02**: E2E chain 端到端测试 — `qa.test-run --proto-ref XXX --app-url http://localhost:3000 --api-url http://localhost:8000`，验证 playwright 执行
- [ ] **TEST-03**: `--resume` 重跑测试 — 失败后使用 `--resume` 重跑失败用例
- [ ] **TEST-04**: 单元测试套件 — `spec_adapter.py`、`environment_provision.py`、`StepResult` dataclass 单元测试

---

## Future Requirements（延期）

- [FR-01]: ADR-048 Mission Compiler — 替代 SPEC_ADAPTER_COMPAT 的长期方案，实现后废弃桥接层
- [FR-02]: 完整 9 节点 state_machine_executor — 区分 precondition failures (HALT) vs verification failures (COLLECT)
- [FR-03]: 独立 API 查询路径（Phase 3+ C 层验证）— 独立账号 + 独立会话
- [FR-04]: HAR 捕获 C 层验证（Phase 2 C 层）— 通过 HAR 拦截前端 API 响应验证业务状态
- [FR-05]: accident-package + failure-classifier — 标准化事故包 + 8 类失败分类
- [FR-06]: bypass-detector — 检测 AI/Playwright 绕过 UI 直调 API

---

## Out of Scope（明确排除）

- `render-testset-view` 废弃 — TESTSET 废弃后失去输入源
- `ll-qa-feat-to-testset` — 已在 ENTRY-04 废弃
- 复杂 DAG 调度 — ADR-050/051 明确采用顺序 loop
- 多 feat 共享 ENV 粒度管理（OQ-2）— 延期到 Phase 2 review

---

## Traceability

| REQ-ID | ADR-053 | ADR-054 | Phase |
|--------|---------|---------|-------|
| ENTRY-01 | §2.2 | — | Phase 17 |
| ENTRY-02 | §2.3 | — | Phase 17 |
| ENTRY-03 | §2.4 | — | Phase 17 |
| ENTRY-04 | §2.1 | — | Phase 17 |
| BRIDGE-01 | — | §2.2 | Phase 17 |
| BRIDGE-02 | — | §2.2.2 | Phase 17 |
| BRIDGE-03 | — | §2.2.3 | Phase 17 |
| BRIDGE-04 | — | §5.1 R-2 | Phase 17 |
| BRIDGE-05 | — | §2.4 | Phase 17 |
| BRIDGE-06 | — | §5.1 R-1 | Phase 17 |
| BRIDGE-07 | — | §2.5 | Phase 17 |
| BRIDGE-08 | — | §2.6 | Phase 17 |
| ENV-01 | — | §2.3 | Phase 17 |
| ENV-02 | — | §2.3.3 | Phase 17 |
| EXEC-01 | — | §3 Phase 2 | Phase 18 |
| EXEC-02 | — | §3 Phase 2 | Phase 18 |
| EXEC-03 | — | §3 Phase 2 | Phase 18 |
| GATE-01 | — | §3 Phase 3 | Phase 19 |
| GATE-02 | — | §3 Phase 3 | Phase 19 |
| GATE-03 | — | §3 Phase 3 | Phase 19 |
| TEST-01 | — | §6 Phase 1 | Phase 17 |
| TEST-02 | — | §6 Phase 2 | Phase 18 |
| TEST-03 | — | §6 Phase 2 | Phase 18 |
| TEST-04 | — | §6 Phase 3 | Phase 19 |

---

## Phase Mappings

| Phase | 目标 | Requirements |
|-------|------|-------------|
| Phase 17 | 双链统一入口 + spec 桥接跑通 | ENTRY-01~04, BRIDGE-01~08, ENV-01~02, TEST-01 |
| Phase 18 | 实施轴 P0 模块 | EXEC-01~03, TEST-02, TEST-03 |
| Phase 19 | 验收闭环 | GATE-01~03, TEST-04 |

*Phase numbering continues from v2.1 (ended at Phase 16)*

---

## v2.2 Coverage Summary

| Metric | Value |
|--------|-------|
| Total requirements | 24 |
| Phase 17 (需求轴统一入口 + spec 桥接) | 15 |
| Phase 18 (实施轴 P0 模块) | 5 |
| Phase 19 (验收闭环) | 4 |
| Mapped to phases | 24/24 (100%) |
| Unmapped | 0 |
