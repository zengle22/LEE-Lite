# ADR-007：QA Test Execution 收敛为 Governed Skill 的标准方案

* 状态：Draft
* 日期：2026-03-23
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）skill-first QA 测试执行链（Web E2E / CLI）
* 相关 ADR：ADR-001、ADR-004、ADR-005、ADR-006

---

# 1. 背景

LL 当前已经在产品主链上逐步建立 governed skill、外置 gate、artifact registry、path policy、execution evidence 与 supervision evidence 的统一治理体系。

但 QA 测试执行链仍缺少一个正式冻结的架构定义，来回答下面几个问题：

* 测试执行到底是一个 runner，还是一个完整 governed skill；
* `TestSet`、具体测试用例、执行脚本、测试执行事实之间的边界如何划分；
* 上游需求、原型、流程、数据契约如何被安全地引入测试执行；
* Web E2E 与 CLI 测试是否共享同一套治理对象模型，还是各自发明一套；
* 哪些步骤必须脚本化，哪些步骤适合由 Agent 主导；
* 合规检查、结果判定、报告汇总、Bug 起草如何分层；
* 执行失败、测试失败、执行不可采信三者如何区分；
* 复跑时到底复用什么，重建什么，何时必须新建 revision。
* 当 coverage qualification 目标未达标时，究竟应该由 `TestSet` 继续膨胀，还是由 test execution runtime 负责自动扩展 runnable cases。

如果不把这条链路正式冻结为独立 ADR，后续实现会持续出现下列漂移：

* 有人把 test execution 理解为“只是跑脚本”；
* 有人把 test execution 理解为“从需求一直生成到报告的全链”；
* 有人把 `TestCasePack` 当中间缓存；
* 有人把 `TestCasePack` 当长期人工维护的主 SSOT；
* 有人把 `TestSet.test_units` 误当成最终 runnable case 清单；
* 有人把 coverage 未达标理解成必须手工回写更多 case 到 `TestSet`；
* 有人把脚本小修与语义性重写混成同一种 patch；
* 有人把 `invalid_run` 和 `failed` 当同义状态；
* 有人把环境说明文档当 `test_environment_ref` 的实际 contract。

这会直接导致：

* 输入输出契约不稳定；
* 证据链无法审计；
* 复跑与 repair 无法收口；
* 角色边界模糊；
* freeze 语义失效；
* 下游 CLI、lifecycle、report、bug bundle 都无法统一。

因此，需要一份独立、完整、只依赖本仓库治理体系的 ADR，正式定义 QA 测试执行 skill 的边界、对象模型、流程、冻结规则、状态规则与实现优先级。

---

# 2. 问题陈述

LL 需要解决的，不是“如何把一组测试脚本跑起来”，而是：

* 如何从一个策略级 `TestSet` 出发，沿显式 SSOT 引用安全地获取执行上下文；
* 如何把策略级测试定义稳定落成一次执行所依赖的具体 `TestCasePack`；
* 如何把用例翻译为可冻结、可追溯、可复跑的 `ScriptPack`；
* 如何通过内部 runner 执行并保留原始证据；
* 如何把执行是否合法与执行结果正确分开判断；
* 如何让结果、报告、Bug、证据、TSE 之间拥有稳定的引用关系；
* 如何在 freeze 之后只允许有限修改，而不是任意返工；
* 如何把复跑模式拆分成足够明确的几类，而不是笼统地说“再跑一次”。

如果这套定义不先冻结，后续 skill 实现将不可避免地出现以下结构性问题：

## 2.1 输入不确定

`test_environment_ref` 如果只是一个路径名或自然语言描述，而不是结构化环境契约，那么：

* Web 的 `base_url` 从哪里取；
* browser matrix 怎么定义；
* CLI 的 `command_entry`、stdin/stdout/stderr、exit code 规则怎么定义；
* `headless/headed`、viewport、trace、video、stdout/stderr、retry、parallelism 怎么继承；
* 账号、密钥、mock、外网访问权限怎么表达；
* readiness 通过标准是什么；

都会在不同实现里各自发明一套。

## 2.2 中间产物不确定

如果没有正式定义 `TestCasePack` 与 `ScriptPack` 的冻结边界，那么“冻结”就只是一个口头说法，无法支持：

* 最小修补；
* 可审计复跑；
* 失败定位；
* 版本比较；
* 证据一致性检查。

## 2.3 角色不确定

如果监督执行合法性的能力，与基于证据判定业务结果的能力写混，那么：

* 谁产出 `compliance_result` 不清楚；
* 谁产出 `case_results` 不清楚；
* 谁负责 `invalid_run` 不清楚；
* 谁负责 `passed/failed/blocked` 不清楚。

## 2.4 状态不确定

如果 `invalid_run` 与 `failed` 不做硬边界定义，那么：

* 测试没通过；
* 流程没跑完；
* 执行事实不可信；

三种情况会被混成同一种“失败”。

## 2.5 复跑不确定

如果只说“支持复跑”，但不区分复用 case、复用脚本、换环境、修脚本，就无法稳定设计：

* CLI 参数；
* lifecycle 状态；
* lineage；
* diff；
* flaky 分析。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **一个 QA test execution governed skill family + 各模态对应的宽/窄 skill 配对**

作为 QA 测试执行链的标准架构。

正式原则如下：

1. 对外暴露的是一个 QA test execution skill family，而不是只冻结单一 Web skill 名称。
2. 第一批正式 sibling skill 包括：
   * `skill.qa.test_exec_web_e2e`
   * `skill.qa.test_exec_cli`
3. 第一批对应的窄 runner skill 包括：
   * `skill.runner.test_e2e`
   * `skill.runner.test_cli`
4. 各 sibling skill 必须共享同一套对象模型、状态语义、freeze 规则、evidence 规则、review / gate 规则与 rerun lineage 规则。
5. 每个宽 skill 都负责从 `TestSet` 出发，到 `TSE / report / bugs / evidence` 为止的完整闭环，但只覆盖自身模态。
6. 每个窄 runner skill 只负责执行脚本与采集原始证据，不负责判定通过/失败。
7. QA test execution 采用冻结中间产物模型：
   * `ResolvedSSOTContext`
   * `TestCasePack`
   * `ScriptPack`
   * `TSE`
8. `test_environment_ref` 必须解析为结构化环境契约，而不是任意说明文档。
9. 模态由结构化环境契约与 runner 类型共同约束，不允许仅靠 skill 名称或自然语言推断。
10. 行为合规检查是强制门禁；结果判定必须基于证据；输出校验必须先自动完成，再按策略决定是否进入人类 gate。
11. freeze 后的修改必须受 allowed / forbidden mutation 规则约束；一旦触及语义层，必须新建 revision。
12. `invalid_run` 与 `failed` 必须严格分离。
13. 复跑必须至少区分：
   * `re_execute`
   * `re_bind_and_execute`
   * `full_regenerate`
14. `TestSet` 是策略级测试规格，不是最终 runnable case 清单；`TestCasePack`、`ScriptPack` 与 qualification 阶段的 case expansion 归属于 test execution runtime。
15. 在 `coverage_qualification` 模式下，runtime 必须以 coverage target 为目标生成或扩展 runnable cases，而不是要求上游 `TestSet` 预先枚举所有分支实例。

---

## 3.2 正式定义

### 3.2.1 宽 skill family 边界

`skill.qa.test_exec_web_e2e` 与 `skill.qa.test_exec_cli` 共享以下职责骨架：

* 接受 `TestSet` 与结构化测试环境；
* 解析显式 `ssot_refs`；
* 生成并冻结具体测试用例；
* 翻译并冻结执行脚本；
* 调用内部 runner；
* 收集 raw output 与 raw evidence；
* 执行行为合规检查；
* 基于证据完成结果判定；
* 组装 `TSE`、test report、bug bundle、evidence bundle；
* 完成末端输出校验与 freeze 准备。

它们都不是单纯的 runner wrapper，也不是长期维护 `TestCasePack` 主文档的编辑器。

模态分工固定为：

* `skill.qa.test_exec_web_e2e`
  * 面向浏览器 / Web UI 交互测试；
  * 典型脚本形态为 Playwright 或等价浏览器 runner 脚本；
  * 典型证据包括 screenshot、trace、video、console/network log。
* `skill.qa.test_exec_cli`
  * 面向命令行 / 控制台 / shell 驱动测试；
  * 典型脚本形态为 shell、PowerShell、Python 或工具命令脚本；
  * 典型证据包括 stdout、stderr、exit code、output files、process log。

### 3.2.2 窄 runner skill family 边界

`skill.runner.test_e2e` 与 `skill.runner.test_cli` 共享以下职责骨架：

* 消费给定 `ScriptPack` 或脚本入口；
* 按环境契约执行 runner；
* 采集 stdout/stderr、logs 与模态相关的原始证据；
* 输出 `runner_output`、`runtime_errors`、`execution_status`。

它们明确不负责：

* 生成测试用例；
* 语义判定测试通过/失败；
* 解释业务期望；
* 修改上游脚本或结果。

### 3.2.3 模态继承规则

`web_e2e` 与 `cli` 两个 sibling skill 必须遵守：

* 共用 `TestSet / TestCasePack / ScriptPack / EvidenceBundle / TSE` 对象模型；
* 共用 `run_status / acceptance_status / invalid_run / failed` 状态边界；
* 共用 `full_regenerate / re_bind_and_execute / re_execute` 复跑模型；
* 共用 `Supervisor.compliance_checker / Supervisor.result_judge` 分层；
* 只允许在 `TestEnvironmentSpec`、`ScriptPack.binding` 与 `EvidenceBundle` 的模态字段上分化。

因此，CLI 支持应以 sibling skill 形式落地，而不是在 `skill.qa.test_exec_web_e2e` 内部用 if/else 偷渡。

### 3.2.4 监督角色与判定能力分层

LL 在 QA test execution 中维持二元角色：

* `Executor`
* `Supervisor`

但 `Supervisor` 下必须明确再分两个子能力：

1. `compliance_checker`
   * 负责执行行为合规、证据完整性、越权、tamper、unauthorized mock 等检查；
   * 负责产出 `compliance_result`；
   * 负责给出 `invalid_run` 判定依据。

2. `result_judge`
   * 负责基于 `TestCasePack.expected` 与执行证据判定 case 结果；
   * 负责产出 `case_results` 与 `results_summary`；
   * 负责给出 `passed / failed / blocked / invalid / not_executed`。

因此：

* `invalid_run` 由 `Supervisor.compliance_checker` 负责；
* `pass/fail/block/invalid/not_executed` 由 `Supervisor.result_judge` 负责；
* `Executor` 不得直接做结果判定。

---

# 4. 对象模型

## 4.1 TestSet

`TestSet` 是策略级测试 SSOT。

它定义：

* scope
* risk focus
* coverage strategy
* qualification coverage goal
* branch families / expansion hints
* allowed / forbidden test methods
* priority policy
* 显式 `ssot_refs`
* 最小策略单元 `test_units`

它不直接定义：

* 最终 runnable case 数；
* qualification 阶段为了 line coverage 展开的全部分支实例；
* 每个边界值；
* 每个定位器；
* 每条脚本实现。

正式规则是：

## **`TestSet` 定义“应该覆盖什么”与“为何覆盖”，不定义“最终要跑多少个 runnable execution cases”。**

## 4.2 TestEnvironmentSpec

`test_environment_ref` 必须解析到一个结构化环境契约对象，正式名为：

* `TestEnvironmentSpec`

它不是任意环境说明文档，不是 README，不是口头约定。

`TestEnvironmentSpec` 最少必须定义：

* `environment_id`
* `environment_name`
* `target_kind`
* `execution_modality`
* `runner_type`
* `runner_command`
* `runner_args_template`
* `working_directory`
* `locale`
* `timezone`
* `network_policy`
* `mock_policy`
* `auth_refs`
* `secret_refs`
* `artifact_capture_policy`
  * stdout
  * stderr
  * process_log
  * output_files
  * screenshot?
  * video?
  * trace?
  * console_log?
  * network_log?
* `timeout_policy`
* `retry_policy`
* `parallelism_policy`
* `readiness_checks`
* `readiness_pass_criteria`

按模态还必须满足：

* `target_kind = web_app` 或等价 Web 目标时：
  * `base_url`
  * `browser_matrix`
  * `head_mode`
  * `viewport`
* `target_kind = cli_app` 或等价 CLI 目标时：
  * `command_entry`
  * `stdin_policy`
  * `stdout_policy`
  * `stderr_policy`
  * `exit_code_policy`

其中必须特别明确：

* 当前 run 属于 Web E2E 还是 CLI；
* 是否允许 mock；
* 是否允许外部网络访问；
* runner 命令的正式入口；
* stdout/stderr/output file 与 trace/video/screenshot 的采集级别；
* readiness 失败时是否允许进入执行。

## 4.3 ResolvedSSOTContext

`ResolvedSSOTContext` 是由 `TestSet.ssot_refs` 展开后形成的执行上下文冻结对象。

它至少包含：

* resolved refs 清单；
* artifact identity；
* 版本或快照信息；
* 去重后的 source list；
* traceability map；
* 解析时刻的 manifest。

正式约束：

* 只能沿 `TestSet.ssot_refs` 向上追溯；
* 不允许自由全局搜索；
* 不允许把未显式声明的旁支文档混入执行上下文。

## 4.4 TestCasePack

`TestCasePack` 是从 `TestSet + ResolvedSSOTContext` 派生出的具体测试用例包。

它是一次执行及其复跑的可冻结输入，不是顶层长期主 SSOT。

`TestCasePack` 可以来源于两种生成模式：

* `minimal_projection`
  * 只把 `TestSet.test_units` 投影为最小可执行集合；
  * 适用于 smoke / acceptance run。
* `qualification_expansion`
  * 在 `minimal_projection` 基础上，结合 `coverage_goal`、`feature_owned_code_paths`、`branch_families` 与 runtime feedback 自动扩展 runnable cases；
  * 适用于 coverage qualification run。

因此：

## **coverage qualification 时产生的额外 runnable cases 属于 `TestCasePack` 扩展结果，不属于 `TestSet` 主对象内容膨胀。**

最少字段应包括：

* `test_case_pack_id`
* `source_test_set_id`
* `source_context_ref`
* `revision`
* `generation_mode`
* `cases[]`

每条 case 最少应包含：

* `case_id`
* `title`
* `priority`
* `feature_point`
* `preconditions`
* `steps`
* `expected`
* `test_data`
* `boundary_checks`
* `allow_mock`
* `source_traceability`
* `derivation_basis`

其中：

* `derivation_basis = test_unit`
  * 表示该 case 直接来源于 `TestSet.test_units`
* `derivation_basis = qualification_expansion`
  * 表示该 case 为满足 qualification 覆盖目标，由 runtime 在策略边界内自动展开

## 4.5 ScriptPack

`ScriptPack` 是从 `TestCasePack` 翻译出的执行脚本包。

它可以承载：

* Web E2E 浏览器脚本；
* CLI 命令脚本；
* 以及与所选 runner 绑定的配置与入口信息。

它最少包含：

* `script_pack_id`
* `source_test_case_pack_id`
* `revision`
* `script_kind`
* `runner_type`
* `binding`
* `entrypoint`
* `runner_config`
* `script inventory`

## 4.6 EvidenceBundle

`EvidenceBundle` 是执行证据的一等产物。

它至少包含：

* raw logs
* raw stdout
* raw stderr
* process / command manifest
* output file refs
* raw screenshots?
* raw video?
* raw trace?
* evidence manifest
* checksum data

证据缺失可以直接触发 `invalid_run`。

### 4.6.1 按 case 优先级的最小证据要求

`EvidenceBundle` 不只是原始证据聚合，还必须满足按 case 优先级分层的 minimum evidence policy。

本 ADR 先冻结以下最小原则：

* `P0 / P1`
  * 至少保留：step/result log、断言结果、失败时错误上下文
  * Web 场景至少补充：关键截图、trace 或等价交互轨迹
  * CLI 场景至少补充：stdout/stderr、exit code、关键 output file 或等价命令执行轨迹
  * 缺失关键证据时，可直接触发 `invalid_run`
* `P2 / P3`
  * 至少保留：step/result log、断言结果、失败时错误上下文
  * Web 是否强制截图或 trace 由环境策略决定
  * CLI 是否强制保存 stdout/stderr 全量或 output files 由环境策略决定
* `blocked`
  * 必须保留：阻塞原因、阻塞发生点、可证明未完成执行的证据
* `not_executed`
  * 必须保留：skip reason 或 not executed reason evidence

最终精确清单可在附属 `evidence-policy` 中继续细化，但本 ADR 先冻结“按优先级定义 minimum evidence”的原则。

### 4.6.2 模态证据等价原则

本 ADR 不要求 Web 与 CLI 使用同一类物理证据文件，但要求它们满足同等级的可审计性。

因此：

* screenshot / trace / video 可以视为 Web 的高价值交互证据；
* stdout / stderr / exit code / output files 可以视为 CLI 的高价值执行证据；
* 两类证据都必须能支撑 compliance 判断、result judgment 与 bug drafting。

## 4.7 TSE

`TSE` 是 `Test Set Execution` 主汇总对象。

它至少包含：

* `tse_id`
* `source_test_set_id`
* `test_case_pack_ref`
* `script_pack_ref`
* `environment_ref`
* `run_mode`
* `run_status`
* `acceptance_status`
* `case_results_ref`
* `report_ref`
* `bug_bundle_ref`
* `evidence_bundle_ref`
* `compliance_result_ref`
* `summary`

其中：

* `run_status` 只表示执行链路状态或执行结论态；
* `acceptance_status` 只表示该 run 是否已通过 `output_validation` / gate decision 并进入正式接受或拒绝结案状态。

---

# 5. 输入输出契约

## 5.1 对外输入

宽 skill 的正式输入为：

* `test_set_ref`
* `test_environment_ref`
* `test_case_pack_ref?`
* `script_pack_ref?`
* `execution_mode`
* `rerun_mode`
* `build_ref?`

约束如下：

1. `test_set_ref` 必须解析到策略级 `TestSet`。
2. `test_environment_ref` 必须解析到结构化 `TestEnvironmentSpec`。
3. `test_case_pack_ref` 只在复跑或局部恢复场景可选。
4. `script_pack_ref` 在 `re_execute` 中可作为执行输入；在 `re_bind_and_execute` 中可作为可选的 repair / diff 上下文输入。
5. `execution_mode` 至少支持：
   * `enforce`
   * `warn`
6. `rerun_mode` 至少支持：
   * `full_regenerate`
   * `re_bind_and_execute`
   * `re_execute`
7. `build_ref` 当前可作为 loose ref 输入，但后续实施应优先提升为结构化 build 契约对象，例如 `BuildSpec` 或 `TargetBuildRef`，而不应长期停留在弱引用状态。

## 5.2 复跑模式

### A. `full_regenerate`

从 `TestSet` 全量开始：

* 重建 `ResolvedSSOTContext`
* 重建 `TestCasePack`
* 重建 `ScriptPack`
* 重新执行

适用于：

* 上游需求或流程已变化；
* 用例语义需要调整；
* 不能信任旧的冻结中间产物。

### B. `re_bind_and_execute`

复用 `TestCasePack`，重建 `ScriptPack`，然后重新执行。

适用于：

* case 语义不变；
* 脚本需要修补；
* 环境不同导致绑定需要重做；
* 需要在同 case 下换 runner config。

### C. `re_execute`

复用 `TestCasePack + ScriptPack`，只重新执行。

适用于：

* flaky 复测；
* 环境偶发问题复测；
* 同脚本同 case 的重试；
* 同一脚本包切换等价环境做对比验证。

## 5.2.1 Qualification 扩展模式

当 `run_mode = coverage_qualification` 时，runtime 必须在上述复跑模式之外，再支持 coverage-driven execution expansion：

1. 先生成 `minimal_projection` 版本的 `TestCasePack`
2. 执行并采集 coverage
3. 读取 coverage summary
4. 基于 `feature_owned_code_paths`、`coverage_goal`、`branch_families` 与 `expansion_hints` 派生增量 runnable cases
5. 形成新的 expanded `TestCasePack` revision 并执行
6. 直到：
   * 达到 coverage target
   * 或达到 qualification budget / revision budget
   * 或进入人工审查所需的不可自动判定分支

runtime 必须保留每轮 expanded pack 与 coverage result 的 lineage，禁止把“自动扩展出来的 runnable cases”静默回写成新的 `TestSet` 主对象。

## 5.3 对外输出

宽 skill 必须输出：

* `test_case_pack_ref`
* `script_pack_ref`
* `tse_ref`
* `test_report_ref`
* `bug_bundle_ref`
* `evidence_bundle_ref`

建议输出：

* `compliance_result_ref`
* `case_results_ref`
* `results_summary_ref`
* `output_validation_ref`
* `execution_summary_ref`

---

# 6. Freeze、Revision 与最小修补规则

## 6.1 TestCasePack freeze 语义

`TestCasePack` freeze 后，允许的修改仅限：

* 补 metadata
* 补 traceability
* 修 schema 错误
* 修编号、排序、格式
* 修 manifest、checksum、artifact registration 信息

freeze 后，明确禁止：

* 修改 `steps` 的语义
* 修改 `expected`
* 修改 `priority`
* 改写 `test_data` 的业务意义
* 增删 case
* 变更 `allow_mock` 语义

## 6.2 ScriptPack freeze 语义

`ScriptPack` freeze 后，允许的修改仅限：

* 修导入路径
* 修 runner config 的非语义性错误
* 修语法错误
* 修 locator 的显式拼写错误
* 修入口文件或目录绑定错误
* 补 manifest、checksum、artifact registration 信息

freeze 后，明确禁止：

* 改变 case 与 script 的语义映射
* 通过修改断言来“消灭失败”
* 注入未授权 mock
* 通过放宽等待、跳过断言、吞异常来制造假通过
* 用脚本偷偷替换 `TestCasePack` 的预期语义

## 6.3 Revision 规则

一旦修改触及语义层，必须：

1. 新建 revision；
2. 重新做结构校验；
3. 重新 freeze；
4. 记录 lineage；
5. 重新生成受影响的下游产物。

语义层包括：

* `TestCasePack.steps`
* `TestCasePack.expected`
* `TestCasePack.priority`
* `TestCasePack.test_data` 的业务含义
* case 数量或 case 边界
* case 与 script 的业务语义映射
* assertion 语义
* mock 许可边界

## 6.4 最小修补原则

QA test execution 正式采用 Minimal Patch Principle：

* 先验证；
* 只修当前 defect scope；
* 修后立即重验；
* 不允许借修补之名顺带重写整个包。

这要求在 P0 脚本层预留 repair hook。

---

# 7. 正式执行流程

QA test execution 的正式流程冻结为 11 步：

1. `ssot_context_resolution`
2. `case_generation`
3. `test_case_pack_freeze`
4. `script_translation`
5. `script_pack_freeze`
6. `script_execution`
7. `behavior_compliance`
8. `result_judgment`
9. `tse_assembly`
10. `bug_drafting`
11. `output_validation_and_freeze`

## 7.1 `ssot_context_resolution`

目标：

* 从 `TestSet.ssot_refs` 解析需求、原型、流程、契约、数据规格；
* 形成 `ResolvedSSOTContext`。

输出：

* `resolved_ssot_context`

## 7.2 `case_generation`

目标：

* 从 `TestSet + ResolvedSSOTContext` 生成具体测试用例；
* 在 smoke / acceptance run 中生成最小投影；
* 在 qualification run 中允许继续扩展为满足 coverage target 的 runnable case pack。

输出：

* `test_case_pack_draft`

补充原则：

* `TestSet.test_units` 是最小策略单元，不是最终 case 数承诺；
* qualification 扩展不得突破 `TestSet` 已声明的 scope、risk focus、acceptance_traceability 与 forbidden methods；
* runtime 可以增加 runnable case 数，但不能借此引入新的产品需求、越界场景或额外业务语义。

## 7.3 `test_case_pack_freeze`

目标：

* 校验并冻结 `TestCasePack`。

输出：

* `test_case_pack`
* `test_case_pack.meta`

## 7.4 `script_translation`

目标：

* 将 `TestCasePack` 翻译为可执行脚本。

输出：

* `script_pack_draft`

## 7.5 `script_pack_freeze`

目标：

* 校验并冻结 `ScriptPack`。

输出：

* `script_pack`
* `script_binding`

## 7.6 `script_execution`

目标：

* 通过内部 runner skill 执行脚本并采集原始证据。

输出：

* `runner_output`
* `runtime_errors`
* `evidence_bundle_raw`
* `execution_status`

## 7.7 `behavior_compliance`

目标：

* 校验执行是否合法、证据是否齐全、是否存在作弊或越权。

输出：

* `compliance_result`

门禁：

* 强制门禁

## 7.8 `result_judgment`

目标：

* 基于 `expected` 与证据判定每个 case 的结果。

输出：

* `case_results`
* `results_summary`

## 7.9 `tse_assembly`

目标：

* 组装 `TSE` 主对象。

输出：

* `tse`

## 7.10 `bug_drafting`

目标：

* 为失败 case 起草 Bug 包。

执行条件：

* `fail_count > 0`

输出：

* `bug_bundle`

## 7.11 `output_validation_and_freeze`

目标：

* 对整套输出执行末端校验；
* 确认引用、统计、证据、报告、TSE、Bug、状态彼此一致；
* 判定本次 run 是否具备正式结案条件。

输出：

* `output_validation`
* `artifact_manifest`

---

# 8. Gate 与校验策略

## 8.1 行为合规检查是硬门禁

以下任一情况成立时，应进入 `invalid_run`：

* 关键证据缺失；
* 未授权 mock；
* Executor 越权判定；
* evidence tamper；
* runner 崩溃导致关键 case 无法证明；
* 执行中存在无法接受的静默跳过。

## 8.2 Output validation 的 gate 关系

`output_validation_and_freeze` 正式定义为：

* `auto validation + optional human review`

即：

1. 自动校验必须先执行；
2. 是否进入人类 gate 由 policy 决定；
3. 当 policy 要求人类 gate 时，自动校验通过只是进入 gate 的前提，不等于 run 已最终被接受。

因此：

* 它不是纯自动步骤；
* 也不是无条件必须人工；
* 它是“自动校验必选，人类复核可按策略启用”的组合节点。

建议默认策略：

* `prod` 或高风险域：启用 human review
* `dev/test/local` 或低风险域：可只保留自动校验

## 8.3 执行状态与最终接受状态分层

`run_status` 只表示执行链路状态，不表示最终是否已被治理体系接受结案。

因此：

* `completed`
* `completed_with_failures`
* `completed_with_warnings`
* `invalid_run`
* `failed`

都属于执行态或执行结论态。

最终接受状态必须由 `output_validation` 与 gate decision 单独表达，建议统一收敛到：

* `acceptance_status`

其最少应支持：

* `pending_validation`
* `validated`
* `pending_human_review`
* `accepted`
* `rejected`

自动校验通过不等于最终 `accepted`。

---

# 9. 状态模型

## 9.1 case 级状态

case 级状态固定为：

* `passed`
* `failed`
* `blocked`
* `invalid`
* `not_executed`

## 9.2 run 级状态

run 级状态固定为：

* `completed`
* `completed_with_failures`
* `completed_with_warnings`
* `invalid_run`
* `failed`

## 9.3 `invalid_run` 与 `failed` 的硬边界

### `invalid_run`

表示：

* 执行事实不可采信。

典型原因：

* 缺关键证据；
* 未授权 mock；
* 执行越权；
* 证据被篡改；
* runner 崩溃导致关键 case 无法证明；
* 执行完整性校验失败。

### `failed`

表示：

* 流程自身失败，未形成合格执行产物。

典型原因：

* 输入 contract 不通过；
* freeze 脚本崩溃；
* output validation 本身无法完成；
* artifact 注册失败；
* 必需 manifest 无法生成；
* 关键结构校验脚本自身失败。

因此：

* “测试没通过”不等于 `failed`；
* “执行不可采信”不等于 `failed`；
* 业务失败应主要体现在 case 级 `failed` 与 run 级 `completed_with_failures`。

---

# 10. 实现职责分配

## 10.1 必须优先脚本化的部分

以下能力必须优先采用脚本或确定性工具实现：

* `TestSet.ssot_refs` 解析与闭包展开
* `TestEnvironmentSpec` 结构校验
* `ResolvedSSOTContext` manifest 生成
* `TestCasePack` schema 校验
* qualification coverage target 评估
* coverage feedback loop
* expanded `TestCasePack` 生成与 lineage 记录
* `ScriptPack` schema 校验
* freeze、checksum、artifact manifest、registration
* runner CLI 调用
* 证据采集与 evidence manifest
* 行为合规硬规则检查
* 汇总统计与交叉校验
* output validation
* 结构层 repair hook

## 10.2 更适合 Agent 的部分

以下能力由 Agent 主导：

* 功能点理解
* UI 路径或 CLI 命令路径理解
* 测试覆盖设计
* 边界值设计
* `TestCasePack` 语义生成
* `TestCasePack -> ScriptPack` 翻译
* 预期与实际的语义比对
* Bug 标题、现象、复现步骤与影响描述

---

# 11. P0 / P1 / P2 落地优先级

## 11.1 P0

P0 必须先补齐：

1. `resolve_ssot_context.py`
2. `validate_test_environment.py`
3. `validate_test_case_pack.py`
4. `freeze_test_case_pack.py`
5. `repair_test_case_pack.py`
6. `validate_script_pack.py`
7. `freeze_script_pack.py`
8. `repair_script_pack.py`
9. `run_test_runner.py`
10. `validate_compliance.py`
11. `validate_outputs.py`

## 11.2 P1

P1 重点补齐：

1. `agents/case-generator.md`
2. `agents/script-translator-web.md`
3. `agents/script-translator-cli.md`
4. `agents/compliance-checker.md`
5. `agents/result-judge.md`
6. `agents/bug-drafter.md`
7. `agents/tse-assembler.md`
8. `input/contract.yaml`
9. `output/contract.yaml`
10. `evidence/*.schema.json`
11. `ll.contract.yaml`
12. `ll.lifecycle.yaml`

## 11.3 P2

P2 后续补齐：

* 历史运行对比
* flaky case 标记
* bug dedup
* dashboard / observability 对接

---

# 12. 备选方案与拒绝理由

## 12.1 拆成 3 个对外独立 skill

不采纳。

原因：

* 同一条上游 SSOT 链会被多次切断；
* 调度复杂度变高；
* 失败定位更分散；
* freeze 与 lineage 更难统一。

## 12.2 只保留 runner skill

不采纳。

原因：

* 无法承载 `TestSet -> TestCasePack -> ScriptPack -> TSE` 的治理链；
* 无法明确角色隔离；
* 合规、判定、报告、Bug 都会退化成外部散落逻辑。

## 12.3 不冻结中间产物

不采纳。

原因：

* 无法支持最小修补；
* 无法支持稳定复跑；
* 无法形成可审计证据链；
* revision 无法落地。

---

# 13. 结果与影响

采用本 ADR 后，LL 在 QA test execution 上将获得：

* 稳定的输入输出契约；
* 明确的 `TestEnvironmentSpec`；
* 可审计的中间产物冻结链；
* 可执行的 repair 策略占位；
* 清晰的角色与子能力边界；
* 明确的 run / case 状态语义；
* 可实现的复跑模式与 lineage；
* 一个可同时承载 Web E2E 与 CLI sibling skill 的共用治理内核。

代价是：

* skill 架构更重；
* 需要更多 schema、脚本、evidence 与 validation 文件；
* 初期实现成本高于“直接跑脚本”。

但这是 QA 测试执行链进入 governed skill 体系所必需的复杂度，而不是可省略的装饰。

---

# 14. 后续行动

本 ADR 冻结架构与治理边界。

后续实施必须据此创建：

* `skill.qa.test_exec_web_e2e`
* `skill.qa.test_exec_cli`
* `skill.runner.test_e2e`
* `skill.runner.test_cli`
* `TestEnvironmentSpec` 契约
* `TestCasePack` / `ScriptPack` / `TSE` schema
* compliance、judgment、output validation、repair 的脚本与 evidence 模型

建议实施顺序：

1. 先落地 `skill.qa.test_exec_web_e2e` 与 `skill.runner.test_e2e`；
2. 再按同一对象模型补齐 `skill.qa.test_exec_cli` 与 `skill.runner.test_cli`；
3. 不允许 CLI 支持绕开本 ADR 另起一套对象模型、状态模型或 evidence 规则。

在这些契约与脚本补齐前，不应宣称 QA test execution skill family 已完成正式治理收敛。
