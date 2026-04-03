# ADR-036 实施说明：`impl-spec-test` Runtime 误报修复与 Coverage 收敛

* 日期：2026-04-03
* 关联 ADR：ADR-036、ADR-037、ADR-039
* 适用范围：`cli/lib/impl_spec_test_*.py`、`skills/ll-qa-impl-spec-test`、`tests/unit/test_cli_skill_impl_spec_test.py`
* 性质：实施校准 / 变更说明

---

## 1. 结论

本次变更不修改 ADR-036 的目标、定位或 gate 语义。

它解决的是一个实现层问题：

## **`qa.impl-spec-test` 已进入 deep review 形态，但 runtime 的若干启发式过宽，导致把“已明确写清的语义”误判成风险或 coverage gap。**

因此本次调整的目标是：

1. 保留 ADR-036 的深审强度和阻断能力
2. 收紧误报来源
3. 让 verdict 更接近真实文档质量，而不是被 parser / matcher 噪音主导

---

## 2. 触发背景

在 `SRC001` 的 `IMPL-SRC-001-001` 到 `005` 上进行 Phase 2 deep rerun 时，出现了明显的“高召回但误报偏多”现象：

* `Out of Scope` 已写明，但 runtime 仍报告 “Non-goals are not explicit”
* `user_physical_profile` 已被显式声明为唯一事实源，runtime 仍报告 canonical ownership conflict
* UI 已明确写“non-blocking / deferred / 不能让用户误以为是前置条件”，runtime 仍报告 severe UI blocking conflict
* TESTSET 已观察 completion / terminal outcomes，但 runtime 仍报告 completion-test closure 缺失
* completion / invariant 检查把代码片段、自然语言 precondition、`done_when`、`execution_ready` 等噪音也当成 completion signal

这些问题如果不修，会带来两个后果：

1. 真风险与误报混在一起，修复成本被放大
2. `review_coverage.status` 会因为启发式噪音长期卡在 `insufficient`

---

## 3. 根因分析

### 3.1 Section parser 对 heading 归类顺序错误

`Out of Scope` 在实现中被先命中了 `scope` 的泛匹配规则，导致：

* `non_goals` 实际为空
* “non-goals are not explicit” 被持续触发

### 3.2 Ownership 抽取过宽

ownership 候选提取把以下内容一并算进“潜在 owner”：

* canonical owner
* projection 名称
* API 输入输出 token
* completion / error / field token
* precondition 文本

结果是：

* 只要一份文档里同时出现 `user_physical_profile`、`runner_profiles`、`birthdate`、`completion_verdict` 等 token，就可能被推成 ownership conflict

### 3.3 UI blocking / non-blocking 判断不识别否定句

原始逻辑只看 blocking 关键词，不识别：

* `不能让用户误以为 ... 是前置条件`
* `must not block`
* `not require`

所以“反阻塞表达”会被误判成“阻塞表达”。

### 3.4 Completion / TESTSET closure 仍偏字符串精确匹配

虽然 runtime 已有 semantic review，但某些 closure 仍然靠 token 直接命中：

* `completion_verdict`
* `homepage_preserved`
* `device_skipped`
* `completion_verdict_source`

如果 TESTSET 写法与 IMPL/API 的字面 token 不完全一致，就会被当成未闭环。

### 3.5 Completion signal 抽取噪音过多

原始 completion signal 集合混入了很多不应参与 invariant check 的内容：

* `execution_ready`
* `done_when`
* `mapping_status`
* `completeness_result`
* 代码片段整段文本
* 自然语言 precondition
* `mark_*` helper token
* `*_ref`
* `=true / =false` 派生表达

这会直接把 `logic-state-invariant-unclear` 推高。

### 3.6 Supervisor false-negative challenge 触发过于机械

只要：

* UI authority 存在
* UX findings 为空

就会自动触发 `supervisor-ux-clean-check`，即使 UI 维度本身已经有高 coverage、无 friction。

---

## 4. 变更内容

### 4.1 `impl_spec_test_semantics.py`

本次调整：

* 将 `non_goals` 的 section alias 匹配顺序前置，避免 `Out of Scope` 被 `scope` 吞掉
* 为 heading 归类增加“精确命中优先”逻辑
* 引入 negated-blocking 识别：
  * `must not`
  * `cannot`
  * `不能`
  * `不得`
  * `误以为`
  * `not require`
* 收紧 owner candidate 抽取：
  * 仅保留显式 canonical / sole-authority / resolved-owner 类句式
  * 过滤 field、state、error、completion、ref 等噪音 token
* 引入 terminal signal 筛选：
  * completion signal 只保留可观察终态或 completion verdict
  * 排除 `mark_*`、`*_ref`、`=true/false`、长自然语言、代码片段、多词短句、通用运行态噪音
* `build_system_views()` 中 API outputs 只保留 terminal/completion-relevant outputs

### 4.2 `impl_spec_test_review.py`

本次调整：

* completion vs TESTSET、API errors vs TESTSET failure terms 统一改为 semantic-term overlap，而不是单纯 exact token overlap
* `network-failure` counterexample 只在真正存在 network/auth/session/provider/sync 类 failure evidence 时才视为 relevant
* `canonical-field-missing` 只在真正存在 canonical-owner 语义时才触发，不再把普通 body field 提升成 ownership 风险
* `risk-gate-fail` 只在 failure/recovery surfaces 内存在风险门槛证据时才 relevant
* “api outputs are not explicit enough ...” 只在 API outputs 确实缺失时再报告

### 4.3 `impl_spec_logic_redteam.py`

本次调整：

* completion / API / TESTSET closure 统一改为 semantic signature 匹配
* `state_invariant_check` 的支持证据面扩展到：
  * IMPL state model
  * IMPL main sequence
  * IMPL api contract
  * TECH state model
  * TECH main sequence
  * TECH api contract
  * bound API contract / api outputs
* invariant 支持判定从“精确相等”改为“supporting line 包含该 completion token”
* open questions 仅在 API preconditions / non-goals 确实缺失时触发

### 4.4 `impl_spec_journey_reviewer.py`

本次调整：

* `skip_device_user` 仅在 device 语义 relevant 时参与评分
* `invalid_input_user` 仅在 invalid / field / missing failure surface relevant 时参与评分
* 避免无关 persona gap 把 journey 维度拉低

### 4.5 `impl_spec_supervisor_review.py`

本次调整：

* `supervisor-ux-clean-check` 不再“只要 UI 存在且 UX finding 为空就触发”
* 现在要求 UI 维度 coverage 或分数不足时才触发 challenge

### 4.6 文档侧配合修复

除了 runtime 收紧，还对 `SRC001` 的文档做了一轮配合修复，尤其是：

* recovery path
* canonical ownership wording
* TESTSET terminal observation
* deferred / non-blocking UI wording
* migration precedence
* `IMPL-SRC-001-004` 明确补出 `experience_enhancement_ready` 状态与步骤

因此最终结论不是“runtime 放松了要求”，而是：

## **runtime 去掉了误报，同时文档也补足了真实缺口。**

---

## 5. 验证结果

### 5.1 Unit regression

执行：

```bash
python -m pytest E:\ai\LEE-Lite-skill-first\tests\unit\test_cli_skill_impl_spec_test.py -q
```

结果：

* `13 passed`

新增验证覆盖了：

* `Out of Scope` 不再被误归到 `scope`
* ownership 抽取只保留 canonical owner
* negated blocking UI 语言被识别为 non-blocking

### 5.2 Real workflow rerun

对 `SRC001` 的 `001-005` 重新运行 `qa.impl-spec-test` deep mode 后，最终结果为：

* `001`: `pass`
* `002`: `pass`
* `003`: `pass`
* `004`: `pass`
* `005`: `pass`

且全部满足：

* `implementation_readiness=ready`
* `review_coverage.status=sufficient`
* final response `validate-output` 通过

最终 suite 摘要在：

* `E:\projects\ai-marathon-coach-v2\artifacts\active\qa\impl-spec-tests\SRC001-phase2-final-suite-summary.md`

---

## 6. 不变项

本次没有改变以下 ADR-036 基线：

* `qa.impl-spec-test` 的主测试对象仍然是 `IMPL`
* `FEAT / TECH / ARCH / API / UI / TESTSET` 仍然只是 authority inputs
* skill 仍然不得建立新的 business truth 或 design truth
* deep review 仍然要看：
  * cross-artifact consistency
  * failure path
  * user journey
  * UI/API/state closure
  * counterexample coverage
* gate 语义仍然保留：
  * `pass`
  * `pass_with_revisions`
  * `block`

换句话说：

## **本次是“实现校准”，不是“治理降级”。**

---

## 7. 后续建议

### 7.1 把本次误报修复模式纳入 reviewer 回归集

建议后续补一组固定 regression fixture，覆盖：

* explicit projection wording
* negated blocking wording
* completion vs TESTSET semantic overlap
* canonical owner with projections present
* terminal outcome expressed in API/contract but not repeated in pure state lines

### 7.2 对 `SRC002+` 做一次批量复跑

本次 `SRC001` 已证明 runtime 校准有效。

下一步应对 `SRC002+` 批量复跑，判断还有没有：

* 同类误报
* 其他 domain-specific false positive family

### 7.3 若再出现误报，不要优先“放松规则”

后续的默认处理原则应固定为：

1. 先判断是文档真缺口还是 runtime 误判
2. 若是 runtime 误判，优先收紧抽取和匹配
3. 不以“降低 deep review 强度”换取通过率

---

## 8. 一句话摘要

ADR-036 的 deep review 方向是对的；本次做的不是改方向，而是把 `impl-spec-test` 从“高召回但误报偏多”校准到“仍然严格，但结果开始可信”。 
