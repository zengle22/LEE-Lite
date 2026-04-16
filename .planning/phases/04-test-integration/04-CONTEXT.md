# Phase 4: 测试联动规则 - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning
**Source:** ADR-049 v2.1 + ADR-047 v1.4

<domain>
## Phase Boundary

实现 Patch → Test 同步机制，Patch-aware Harness 适配。

本阶段产出：
1. test_impact 强制验证（interaction/semantic 缺失时阻断）
2. Manifest 标记策略（新增 patch_affected 字段）
3. Patch context 注入到测试执行流
4. 冲突检测统一到 patch_schema.py
5. settle skill 强化 test_impact 验证

不涉及：AI Context 注入（Phase 5）、Hook 集成（Phase 6）、24h Blocking（Phase 7）。

**前提变更**：ADR-047 把 TESTSET 降级为兼容视图，真理源为 api-coverage-manifest / e2e-coverage-manifest + api-test-spec / e2e-journey-spec。ROADMAP/REQUIREMENTS 中 "TESTSET" 需重解释为 manifest + spec 层。

</domain>

<decisions>
## Implementation Decisions

### test_impact 表示法（来自评审决策）
- **D-01:** 保持 ADR-049 §5.3 boolean flags 设计（impacts_user_path, impacts_acceptance, impacts_existing_testcases, affected_routes, test_targets），不引入枚举
- **D-02:** REQUIREMENTS.md REQ-PATCH-04 中的 test_impact 枚举 (none, path_change, assertion_change, new_case_needed) 视为过时，将在 ROADMAP 修订时更新
- **D-03:** interaction/semantic Patch 入库时 AI 自动填充 test_impact 并标记 human-reviewed（ADR-049 §12.2）
- **D-04:** 结算时若 test_impact 为 null 且 change_class 为 interaction/semantic → 阻断结算，ERROR
- **D-05:** visual Patch 的 test_impact 保持可选（默认无测试影响）

### Manifest 标记策略（评审决策）
- **D-06:** 不动 lifecycle_status 状态机（ADR-047 §15 A.2 定义的正向转换）
- **D-07:** 新增 `patch_affected: boolean` + `patch_refs: [string]` 到 manifest item schema
- **D-08:** test_impact != none 时，设置相关 manifest item 的 `patch_affected: true` + 添加 patch_id 到 `patch_refs`
- **D-09:** 新增测试用例场景时，在 manifest 中新增 item，`lifecycle_status: drafted`

### Harness 适配
- **D-10:** patch context 注入合并到 `test_exec_artifacts.py` 作为 `resolve_patch_context()` 函数，与 `resolve_ssot_context()` 同层
- **D-11:** test_exec_runtime.py 中注入 patch context + 前置同步检查钩子
- **D-12:** 不新增独立文件，复用现有 test_exec_* 模块边界

### 冲突检测统一
- **D-13:** 统一到 `patch_schema.py` 中新增 `resolve_patch_conflicts()` 函数
- **D-14:** 消除三处重复：patch_capture_runtime.py:detect_conflicts()、settle_runtime.py:detect_settlement_conflicts()、新冲突逻辑

### 冲突解决规则（严格遵循 ADR-049 §10.3）
- **D-15:** SSOT 是基线，validated/pending Patch 在 scope 内覆盖 SSOT
- **D-16:** 多 Patch 冲突 → 最新 validated 为准（tie-breaking: patch_id 序列号大的优先）
- **D-17:** 不可调和冲突 → TEST_BLOCKED = `lifecycle_status: blocked`，跳过该 item，不阻断整个套件

### test_impact 强制执行级别
- **D-18:** visual → WARN，继续；interaction/semantic → 阻断；无关联 manifest → WARN + 审计记录

### 安全增强
- **D-19:** Patch 覆盖的 manifest item 必须保留原有 acceptance refs（只能新增/扩展，不能删除）
- **D-20:** resolve_patch_context() 返回严格类型 struct，不注入自由字符串到 subprocess env
- **D-21:** 新增 `reviewed_at` 时间戳到 Patch source，结算时验证 reviewed_at >= created_at
- **D-22:** TOCTOU 防护：Harness 构建 context 时计算 Patch 目录 hash，执行前校验无变更

### Claude's Discretion
- `patch_affected` 和 `patch_refs` 字段的具体 schema 定义格式
- resolve_patch_context() 的具体 struct 设计
- 冲突检测统一后旧函数的迁移策略（保留兼容 vs 直接替换）
- reviewed_at 的具体格式（ISO8601 vs Unix timestamp）

### Folded Todos
None

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ADR / Design
- `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` — ADR-049 全文
  - §10: 与测试体系的衔接（test_impact 强制声明、Harness 冲突解决规则）
  - §4.4: 分类与回写目标自动映射（含 test_impact 默认规则）
  - §8.5: 告警规则（test_impact=true 但未关联 TESTSET/TC 阻断结算）
  - §12.2: AI 自动填充规范
  - §12.5: Patch YAML 验证
- `ssot/adr/ADR-047-测试体系重建 - 双链治理.md` — 双链测试治理架构
  - §3.3: 双输入测试设计模型
  - §3.7: testset 去化策略（降级为兼容视图）
  - §3.3: 四层资产分离（plan/manifest/spec/settlement）
  - §6.4: 新执行流程（spec 驱动）
  - §15 A.1-A.2: Manifest 状态机（lifecycle_status 不可回退）
  - §19: 迁移连接点（执行入口改吃 spec）
- `.planning/ROADMAP.md` — Phase 4 goal + success criteria
- `.planning/REQUIREMENTS.md` — REQ-PATCH-04（test_impact 枚举定义已过时）

### Existing Patterns
- `cli/lib/patch_schema.py` — Patch schema 验证器 + PatchTestImpact dataclass
- `cli/lib/test_exec_runtime.py` — 测试执行运行时骨架
- `cli/lib/test_exec_artifacts.py` — SSOT context 解析（resolve_ssot_context 模式）
- `cli/lib/test_exec_execution.py` — 用例执行循环
- `cli/lib/test_exec_traceability.py` — 覆盖矩阵推导
- `skills/ll-experience-patch-settle/scripts/settle_runtime.py` — 结算运行时（含 test-impact-draft.yaml 生成）
- `skills/ll-patch-capture/scripts/patch_capture_runtime.py` — 登记运行时（含 detect_conflicts）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli/lib/patch_schema.py` — PatchTestImpact dataclass（boolean flags），PatchExperience dataclass，validate_patch 函数
- `cli/lib/test_exec_artifacts.py` — resolve_ssot_context() 函数，可参照新增 resolve_patch_context()
- `cli/lib/test_exec_runtime.py` — 测试执行入口，已有 ssot_type 验证边界检查
- `settle_runtime.py` — 已有 test-impact-draft.yaml 生成逻辑（lines 193-211）
- `patch_capture_runtime.py` — 已有 detect_conflicts() 函数（lines 55-83）

### Established Patterns
- cli/lib/ 存放共享验证器和工具函数（patch_schema.py 模式）
- skills/*/scripts/ 存放技能特定运行时
- dataclass + YAML read/write 是项目的标准数据模式

### Integration Points
- 读取 `ssot/experience-patches/` 下 validated/pending_backwrite Patch
- 按 feat_ref 查找对应 manifest
- 注入到 test_exec_runtime.py 的 spec 读取之后、generation 之前

</code_context>

<specifics>
## Specific Ideas

- 评审采用了 5 角色模式（Factual, Security, Senior Eng, Consistency, Redundancy）
- 用户决策：test_impact 保持 boolean flags；manifest 标记用新字段不动状态机
- 文件精简：从 2 新文件 + 2 改造 → 0 新文件 + 3 改造
- 冲突检测统一到 patch_schema.py，消除三处重复
</specifics>

<deferred>
## Deferred Ideas

- Phase 5: AI Context 注入（executor.md 中集成 context injection）
- Phase 6: PreToolUse hook 自动触发登记
- Phase 7: 24h Blocking 机制
- Patch 冲突自动检测 → 统一后由 settle skill 消费
</deferred>

---

*Phase: 04-test-integration*
*Context gathered: 2026-04-17, multi-role review completed*
