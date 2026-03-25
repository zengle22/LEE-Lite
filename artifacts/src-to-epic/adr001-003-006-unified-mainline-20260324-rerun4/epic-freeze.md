---
artifact_type: epic_freeze_package
workflow_key: product.src-to-epic
workflow_run_id: adr001-003-006-unified-mainline-20260324-rerun4
status: accepted
schema_version: 1.0.0
epic_freeze_ref: EPIC-ADR001-003-006-UNIFIED-MAINLINE-202-4-RERUN4
src_root_id: SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN4
downstream_workflow: product.epic-to-feat
source_refs:
- product.raw-to-src::adr001-003-006-unified-mainline-20260324-rerun4
- SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN4
- ADR-001
- ADR-003
- ADR-006
- ADR-005
rollout_required: true
---

# 主链正式交接与治理闭环统一能力

## Epic Intent

将《LL skill-first 主链文件化治理闭环》中的治理问题空间进一步收敛为“主链正式交接与治理闭环统一能力”这一 EPIC 级能力域，让下游可以围绕稳定的能力包拆分 FEAT，而不是继续复述 SRC 原则或沿治理对象逐项平移。

## Business Goal

本 EPIC 的核心不是分别建设 loop、handoff、formalization、IO 四块局部规则，而是形成一条可被多 skill 共享继承的主链受治理交接闭环。在这个统一上位能力下，下游再围绕 主链协作闭环能力、正式交接与物化能力、对象分层与准入能力、主链文件 IO 与路径治理能力、技能接入与跨 skill 闭环验证能力 形成稳定 FEAT，而不是继续复述 SRC 原则或各自实现等价规则。

## Scope

- 统一上位能力：形成一条可被多 skill 共享继承的主链受治理交接闭环。
- 主链协作闭环能力：定义 execution loop、gate loop、human loop 在 governed skill 主链中的协作责任、交接界面与回流边界，使不同 FEAT 不再各自重写等价 loop 规则。
- 正式交接与物化能力：统一 handoff、gate decision、formal materialization 的正式推进链路，使 candidate 到 formal 的升级路径可以被下游稳定继承。
- 对象分层与准入能力：固定 candidate package、formal object 与 downstream consumption 的层级规则、准入条件和引用约束，防止业务 skill 再次混入裁决职责。
- 主链文件 IO 与路径治理能力：定义主链如何接入 ADR-005 已提供的文件 IO / 路径治理能力，约束交接对象的 IO 入口、出口、物化落点与引用稳定性，只覆盖 handoff、formal materialization 与 governed skill IO，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。
- 技能接入与跨 skill 闭环验证能力：定义现有 governed skill 的 onboarding、迁移切换与跨 skill E2E 验证边界，使治理主链的成立不依赖口头假设、组件内自测或一次性全仓切换。

## Non-Goals

- 不在本 EPIC 中直接定义重型调度器、数据库、事件总线或平台化 runtime。
- 不在本 EPIC 中展开具体 schema 字段、CLI 命令、目录实现细节或代码实现方案。
- 不在本 EPIC 中直接完成下游需求分解。
- 本 EPIC 不要求一次性完成所有现有 governed skill 的全量迁移或全仓 cutover。
- 本 EPIC 不要求覆盖所有 producer/consumer 组合场景，只要求在下游 FEAT 中显式定义 onboarding 范围、迁移波次和至少一条真实跨 skill pilot 主链。
- 本 EPIC 不负责把 onboarding / migration_cutover 扩大为仓库级全局文件治理改造。
- 本 EPIC 不重新实现 ADR-005 的 Gateway / Path Policy / Registry 模块，只消费其已交付能力。

## Success Metrics

- 下游 FEAT 能完整覆盖 主链协作闭环能力、正式交接与物化能力、对象分层与准入能力、主链文件 IO 与路径治理能力、技能接入与跨 skill 闭环验证能力 这些主轴，且每个 FEAT 都对应独立可验收的能力面而不是原则复述。
- candidate 到 formal 的流转边界在下游 FEAT 层不再歧义，业务 skill、gate 与 materialization 职责不再混层。
- 至少一条 producer -> consumer -> audit -> gate pilot 主链可被真实验证，不再只停留在原则描述。
- 至少一组 candidate -> formal materialization 流程在真实 governed skill 链路中启用并保留证据。
- 当 rollout_required 为 true 时，至少一组 adoption / cutover / fallback 策略被验证。
- 下游 FEAT 必须产出可执行的 governed skill integration matrix、迁移波次规则与至少一条真实跨 skill pilot 闭环 evidence。
- 治理主链是否成立，不以组件内自测为唯一依据，而以真实 producer / consumer 接入后的 handoff / gate / E2E 证据为准。

## Decomposition Rules

- 按独立验收能力边界拆分 FEAT，不按实现顺序或单一任务切分。
- 每个下游 FEAT 都必须继承 src_root_id、epic_freeze_ref 和 authoritative source_refs。
- 保留 business skill、handoff runtime、external gate 的职责分层，不得在 FEAT 层重新混层。
- 优先将多个触发场景共享的主链能力放在同一 EPIC，下游再按场景或边界拆 FEAT。
- 四个 capability axes 是 primary decomposition axis，FEAT 应优先围绕这些能力轴拆分。
- required_feat_families / rollout families 是 mandatory cross-cutting overlays，必须叠加到对应 capability FEAT 上，而不是替代主轴。
- 建议 FEAT 轴映射：
  - 主链协作闭环能力 -> loop / handoff / gate 协作边界
  - 正式交接与物化能力 -> gate decision 与 formal materialization
  - 对象分层与准入能力 -> candidate / formal object 准入与层级规则
  - 主链文件 IO 与路径治理能力 -> 文件 IO / 路径 / 目录治理
  - 技能接入与跨 skill 闭环验证能力 -> skill onboarding / migration cutover / cross-skill E2E validation

## Rollout and Adoption

- rollout_required: `true`
- trigger_score: `4`
- SRC 涉及共享治理底座或共用运行时能力，而不是单一业务功能。
- 功能真正生效依赖现有 skill / workflow 接入，而不是只完成底座建设。
- 效果判定依赖真实 producer / consumer 接入，不能只靠组件内自测证明。
- 需要跨 skill E2E 或 handoff/gate 闭环验证，才能证明治理主链真的成立。
- required_feat_tracks: `foundation, adoption_e2e`
- rollout / adoption / E2E 不另起第二个 EPIC，而是在当前主 EPIC 内显式保留，并在 epic-to-feat 阶段强制拆出独立 FEAT 族。
- foundation FEAT 与 adoption/E2E FEAT 必须共享同一组 source_refs 和治理约束，不得形成并行真相。
- default-active 与 guarded/provisional 切面必须分层表达，避免未冻结 slice 被误当成已默认启用能力。
- prerequisite foundation: ADR-005 作为主链文件 IO / 路径治理前置基础，要求在本 EPIC 启动前已交付或已可稳定复用。
- prerequisite foundation: 本 EPIC 只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力，不在本 EPIC 内重新实现这些模块。
- required_feat_families:
  - skill_onboarding: 建立现有 governed skill 的 integration matrix，明确 producer、consumer、gate consumer 与暂不接入对象。
  - migration_cutover: 定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界，而不是一次性全仓硬切。
  - cross_skill_e2e_validation: 至少选定一条真实 producer -> consumer -> audit -> gate 的 pilot 主链，并形成跨 skill E2E evidence。

## Constraints and Dependencies

### Epic-level constraints

- 本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- 主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界。
- 能力轴是 primary decomposition axis；rollout families 是 mandatory cross-cutting overlays，需叠加到对应 capability FEAT 上，不替代主轴。
- 主链文件 IO 与路径治理只覆盖交接对象的 IO 入口、出口、物化落点与引用稳定性，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。
- ADR-005 是主链文件 IO / 路径治理前置基础；本 EPIC 只消费其已交付能力，不重新实现 Gateway / Path Policy / Registry 模块。
- 当 rollout_required 为 true 时，foundation 与 adoption_e2e 必须同时落成，并至少保留一条真实 producer -> consumer -> audit -> gate pilot 主链。

### Authoritative inherited constraints

- 以下来源约束来自 authoritative SRC，downstream must preserve where applicable，但它们不重新定义本 EPIC 的 primary capability boundary。
- 双会话双队列闭环
- 文件化 handoff runtime
- external gate 独立裁决与物化
- business skill 只产出 candidate package、proposal、evidence
- execution loop、gate loop、human loop 通过结构化文件对象协作
- candidate package 与 formal object 强制分层
- 保持桥接型 SRC 的薄层语义，不把本候选扩写为实现设计或平台 API
- 下游需求链必须继承这套统一闭环，不得重新发明另一套 queue、handoff、gate、materialization 规则
- external gate 必须以 approve、revise、retry、handoff、reject 形成唯一决策，不得并列批准语义。
- candidate package 仅作为 gate 消费对象；经 gate 批准并物化后的 formal object 才能作为下游正式输入。
- Authoritative source refs: ADR-001, ADR-003, ADR-006
- Upstream package: E:\ai\LEE-Lite-skill-first\artifacts\raw-to-src\adr001-003-006-unified-mainline-20260324-rerun4

### Downstream preservation rules

- 下游 FEAT 不得改写 src_root_id、epic_freeze_ref 与 authoritative source_refs。
- 下游 FEAT 不得把 EPIC 重新打平为上游 QA test execution 对象清单；source-level object constraints 只能附着到实际受其约束的 FEAT。
- candidate -> formal、loop / gate / handoff 分层与 acceptance semantics 必须继续保持可校验、可追溯。

## Acceptance and Review

- Upstream acceptance: approve (Acceptance review passed.)
- Upstream semantic review: pass (No semantic issue detected.)
- Epic review: pass
- Epic acceptance: approve

## Downstream Handoff

- Next workflow: `product.epic-to-feat`
- epic_freeze_ref: `EPIC-ADR001-003-006-UNIFIED-MAINLINE-202-4-RERUN4`
- src_root_id: `SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN4`
- prerequisite foundation: ADR-005 作为主链文件 IO / 路径治理前置基础，要求在本 EPIC 启动前已交付或已可稳定复用。
- prerequisite foundation: 本 EPIC 只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力，不在本 EPIC 内重新实现这些模块。
- Required carry-over: source refs, decomposition rules, constraints, acceptance evidence

## Traceability

- Epic Intent: problem_statement, trigger_scenarios, business_drivers <- ADR-001, ADR-003, ADR-006, ADR-005
- Scope: in_scope, governance_change_summary, bridge_context.governance_objects <- SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN4, ADR-001, ADR-003, ADR-006, ADR-005
- Constraints and Dependencies: key_constraints, bridge_context.downstream_inheritance_requirements <- product.raw-to-src::adr001-003-006-unified-mainline-20260324-rerun4, ADR-001, ADR-003, ADR-006, ADR-005
