# Requirements: ADR-050/051 SSOT 语义治理升级

**Defined:** 2026-04-18
**Core Value:** 确保 SSOT 不再逐层生成，而是从 FRZ 冻结包中分层语义抽取，执行层只能补全不能改写语义

## v2.0 Requirements

Requirements for v2.0 milestone — SSOT semantic governance upgrade.

### FRZ 冻结层

> **Workflow position:** 需求讨论阶段收敛后，作为 SSOT 体系的第一入口。
>
> **整体流程:** 自由格式文档(PRD/UX/Arch) → [ll-frz-manage 冻结模式] MSC 校验 → FRZ 冻结 → 注册 → [ll-frz-manage 抽取模式] 抽取 SRC

- [ ] **FRZ-01**: FRZ 包结构定义 (freeze.yaml) 包含 MSC 5维字段
  - **Skill/工具:** `cli/lib/frz_schema.py` (新) — 定义 FRZ 包结构、MSC 校验 schema
  - **调用方式:** `from cli.lib.frz_schema import FRZPackage, MSCValidator`
  - **Workflow:** 人工讨论产出 PRD/UX/Arch → 收敛为 FRZ 包 → MSC 5维校验通过 → frozen

- [ ] **FRZ-02**: MSC 验证器检查 FRZ 包是否满足最低语义完整性
  - **Skill 修改:** `ll-frz-manage` (新技能) — 冻结模式中集成
  - **调用方式:** `ll frz-manage validate --input <doc-dir>` — 输入自由格式文档，输出 FRZ 包 + MSC 报告
  - **Workflow:** 文档提交后自动运行，5维全部非空才放行

- [ ] **FRZ-03**: FRZ 注册表记录版本、状态、创建时间
  - **Skill 修改:** `ll-frz-manage` — 冻结模式中集成注册逻辑
  - **调用方式:** `ll frz-manage freeze --input <doc-dir> --id FRZ-xxx` — 冻结 + 注册一步完成
  - **Workflow:** MSC 验证通过后执行，写入 `ssot/registry/frz-registry.yaml`

- [ ] **FRZ-04**: CLI 命令 `frz validate` 验证 FRZ 包 MSC 合规性
  - **Skill 修改:** `ll-frz-manage` — 冻结模式 (FRZ-02 合并实现)
  - **调用方式:** `ll frz-manage validate --input <doc-dir>`
  - **Workflow:** 同上 FRZ-02

- [ ] **FRZ-05**: CLI 命令 `frz register` 注册已验证的 FRZ 包
  - **Skill 修改:** `ll-frz-manage` — 冻结模式 (FRZ-03 合并实现)
  - **调用方式:** `ll frz-manage freeze --input <doc-dir> --id FRZ-xxx`
  - **Workflow:** MSC 验证通过后执行，将 FRZ 包写入注册表，状态置为 frozen
  - **Major 变更:** `ll frz-manage freeze --input <doc-dir> --id FRZ-xxx --type revise --reason "..." --previous_frz FRZ-yyy`

- [ ] **FRZ-06**: CLI 命令 `frz list` 列出已注册 FRZ 包及状态
  - **Skill 修改:** `ll-frz-manage` — 查询模式
  - **调用方式:** `ll frz-manage list [--status frozen|blocked]`
  - **Workflow:** 查看 FRZ 注册表，选择要引用的 FRZ 包用于下游抽取

### 语义抽取链

> **Workflow position:** FRZ frozen 之后，SSOT 主链的生成全部改为从 FRZ 抽取。
>
> **整体流程:** FRZ(frozen) → [ll-frz-manage 抽取模式] SRC → [ll-product-src-to-epic] EPIC → [ll-product-epic-to-feat] FEAT → 进入 dev/QA 技能

- [ ] **EXTR-01**: FRZ → SRC 投影器从冻结包抽取需求语义
  - **Skill 修改:** `ll-frz-manage` — 新增抽取模式
    - **调用方式:** `ll frz-manage extract --frz <frz-id> --output <src-output-dir>`
    - **Workflow 位置:** FRZ frozen 后的第一步，输出 SRC 供下游路由
    - **内部逻辑:** 校验 FRZ frozen → 语义抽取 → 投影不变性守卫 → 锚点注册 → 漂移检测 → 输出 SRC
  - ~~`ll-product-raw-to-src`~~ — 不再修改，由 `ll-frz-manage` 抽取模式替代

- [ ] **EXTR-02**: SRC → EPIC → FEAT 级联投影引擎
  - **Skill 修改:** `ll-product-src-to-epic` — 改为从 FRZ 抽取 EPIC
    - **当前行为:** 从 SRC 生成 EPIC
    - **v2.0 行为:** 从 FRZ 冻结语义 + SRC 锚点抽取 EPIC，不改写 FRZ 语义
    - **调用方式:** `ll src-to-epic extract --src <src-dir> --frz <frz-id>`
    - **Workflow 位置:** SRC accepted 后触发，输出 EPIC
  - **Skill 修改:** `ll-product-epic-to-feat` — 改为从 FRZ 抽取 FEAT
    - **当前行为:** 从 EPIC 生成 FEAT
    - **v2.0 行为:** 从 FRZ 冻结语义 + EPIC 锚点抽取 FEAT
    - **调用方式:** `ll epic-to-feat extract --epic <epic-dir> --frz <frz-id>`
    - **Workflow 位置:** EPIC accepted 后触发，输出 FEAT

- [ ] **EXTR-03**: 锚点 ID 注册表记录投影不变性
  - **Skill/工具:** `cli/lib/anchor_registry.py` (新) — 锚点 ID 注册表
  - **调用方式:** `from cli.lib.anchor_registry import AnchorRegistry; registry.register(anchor_id="JRN-001", frz_ref="FRZ-xxx", projection_path="SRC/EPIC/FEAT")`
  - **Workflow:** 被 `ll-frz-manage` 抽取模式和 `ll-product-src-to-epic`/`ll-product-epic-to-feat` 内部调用

- [ ] **EXTR-04**: 语义漂移检测器比对抽取前后语义差异
  - **Skill/工具:** `cli/lib/drift_detector.py` (新) — 被 `ll-qa-impl-spec-test` 和抽取模式内部调用
  - **调用方式:** `from cli.lib.drift_detector import check_drift; result = check_drift(frz_ref, target_dir)`
  - **Workflow:** 抽取完成后自动运行，比对抽取结果与 FRZ 原始语义

- [ ] **EXTR-05**: 投影不变性守卫拒绝改写语义的抽取操作
  - **Skill 修改:** `ll-frz-manage` 抽取模式、`ll-product-src-to-epic`、`ll-product-epic-to-feat` 均集成
  - **调用方式:** 内置于抽取流程，抽取前校验 `derived_allowed` 范围
  - **Workflow:** 抽取操作的守卫步骤，任何超出 FRZ `derived_allowed` 范围的改写直接拒绝

### 执行语义稳定

> **Workflow position:** dev 技能执行阶段。语义守卫整合到 `ll-qa-impl-spec-test`，作为 dev 前最后一道全面检查。
>
> **整体流程:** FEAT accepted → [ll-qa-impl-spec-test] 全面检查(含语义稳定性) → 通过 → 进入 dev 技能

- [ ] **STAB-01**: 变更 vs 补全分类器 (clarification vs semantic change)
  - **Skill 修改:** `ll-qa-impl-spec-test` — 新增语义稳定性检查维度
  - **调用方式:** 在 impl-spec-test 的 8 维度中加第 9 维度 `semantic_stability`
  - **Workflow:** impl-spec-test deep mode 中自动触发，比对 FEAT/TECH/UI 与 FRZ 锚定语义

- [ ] **STAB-02**: 执行前语义守卫检查
  - **Skill 修改:** `ll-qa-impl-spec-test` — 语义稳定性维度中集成
  - **Workflow 位置:** impl-spec-test 执行时自动检查，不再需要 dev 技能单独加前置守卫

- [ ] **STAB-03**: 静默覆盖防护机制 (silent override prevention)
  - **Skill 修改:** 所有 `ll-dev-*` 技能的 `validate_output.sh` — 加输出校验
  - **调用方式:** `python cli/lib/silent_override.py check --output <output-dir> --baseline <feat-file>`
  - **Workflow:** 技能输出文件后自动校验

- [ ] **STAB-04**: 执行后语义一致性验证
  - **Skill 修改:** `ll-qa-impl-spec-test` — 语义稳定性维度中集成
  - **Workflow:** impl-spec-test  verdict 中加 `semantic_drift` 字段，漂移则 verdict 为 `block`

### 变更分级协同

> **Workflow position:** 执行过程中发现需要变更时，分级处理 → Minor 走 Patch → Major 回流 FRZ。
>
> **整体流程:** 变更发现 → [ll-patch-capture] 三分类 → visual/interaction → Minor Patch → semantic → [ll-frz-manage freeze --type revise] 回流

- [ ] **GRADE-01**: 三分类映射 (visual→Minor, interaction→Minor, semantic→Major)
  - **Skill 修改:** `ll-patch-capture` — 集成三分类
    - **当前行为:** Patch 捕获 + 双路径执行
    - **v2.0 行为:** 捕获时自动分类，visual/interaction → Minor patch，semantic → 触发 Major 回流
    - **Workflow 位置:** dev 技能执行过程中发现变更时

- [ ] **GRADE-02**: Minor 路径处理 (retain_in_code + backwrite UI/TESTSET)
  - **Skill 修改:** `ll-experience-patch-settle` — 处理 Minor 变更的 settle 逻辑
  - **调用方式:** `ll experience-patch-settle process --patch <patch-yaml> --type minor`
  - **Workflow:** Minor Patch 验证通过后，backwrite 到 UI Spec / Flow Spec

- [ ] **GRADE-03**: Major 路径处理 (回流 FRZ 重冻结)
  - **Skill 修改:** `ll-frz-manage` — 冻结模式加 `--type revise` 参数
    - **调用方式:** `ll frz-manage freeze --input <doc-dir> --id FRZ-xxx --type revise --reason "..." --previous_frz FRZ-yyy`
    - **Workflow:** semantic 变更触发，创建新 FRZ 修订 → 人工讨论 → 重新冻结 → 重新抽取
    - **注册表:** 记录 revision chain（parent_frz_ref, reason, status）

- [ ] **GRADE-04**: 与 ADR-049 Patch 层协同机制
  - **Skill 修改:** `ll-patch-aware-context` — 加语义变更检测
    - **当前行为:** 注入 Patch 上下文到编辑流程
    - **v2.0 行为:** 注入时检测当前 Patch 是 Minor 还是 Major 变更
    - **Workflow 位置:** 代码编辑前，Patch 上下文注入阶段

### Task Pack 顺序执行

> **Workflow position:** FEAT 已抽取、已验证，开始实施阶段。v2.0 仅交付结构，执行循环延期到 v2.1。
>
> **v2.0 scope:** Task Pack YAML schema + depends_on 解析。手动按顺序执行 task。
>
> **v2.1 scope (deferred):** 自动化 loop 执行器 + 双链验证集成 + 失败暂停。

- [ ] **PACK-01**: PACK YAML 结构定义 + schema 验证
  - **Skill/工具:** `ssot/schemas/qa/task_pack.yaml` (新 schema) + `cli/lib/task_pack_schema.py` (新)
  - **调用方式:** `from cli.lib.task_pack_schema import validate; validate(pack_yaml)`
  - **Workflow:** 创建 Task Pack 时验证结构合法性

- [ ] **PACK-02**: depends_on 依赖解析 (拓扑排序)
  - **Skill/工具:** `cli/lib/task_pack_resolver.py` (新)
  - **调用方式:** `from cli.lib.task_pack_resolver import resolve_order; order = resolve_order(pack_yaml)`
  - **Workflow:** Task Pack 加载后，解析依赖得到可执行顺序

- [ ] **PACK-03**: 顺序循环执行器 (一次一个任务) — **DEFERRED to v2.1**
  - ~~`ll-execution-loop-job-runner`~~ — 延期
  - **v2.0 替代方案:** 手动按 resolved_order 逐个执行 task

- [ ] **PACK-04**: 失败暂停 + 等待人工干预 — **DEFERRED to v2.1**
  - 延期到 v2.1 与 PACK-03 一起实现

- [ ] **PACK-05**: 测试任务绑定到 API/E2E 双链 — **DEFERRED to v2.1**
  - 延期到 v2.1 与 PACK-03 一起实现

### ~~三轴管理~~ (AXIS-01~03)

> **说明:** 三轴管理是架构原则说明（需求强/实现弱/证据轻），不需要实施新技能或 CLI。已在 ADR-050 §7 定义。实际实施中：
> - 需求轴强治理 → 通过 FRZ/抽取/守卫 技能链实现
> - 实现轴轻量追踪 → Task Pack YAML 中的 status 字段
> - 证据轴绑定式链接 → QA 双链验证的 evidence 引用

## v2.1 Requirements (Deferred)

Requirements acknowledged but deferred to future release.

### QA 技能适配

- **QA-01**: 11 个 QA 技能提示词审计 (适配抽取模型)
- **QA-02**: 现有 SRC/FEAT 回填迁移

### FRZ 增强

- **FRZ-07**: FRZ 创建工具 (从 BMAD 等框架输出转换)
- **FRZ-08**: FRZ 差异对比工具 (diff between versions)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| FRZ 生成工具实现 | ADR-050 明确本轮仅定义治理规则，FRZ 仍通过 BMAD 等框架产出 |
| 复杂 DAG 调度器 | ADR-051 明确采用顺序 loop，不需要并发编排 |
| 三轴一律强管理 | ADR-050 §7 明确差异化强度 |
| AI 自动生成 FRZ | FRZ 必须由人工讨论冻结 |
| LLM 语义抽取 | 抽取基于规则/模式匹配，非 LLM 生成 |
| 失败自动跳过 | ADR-051 明确失败必须暂停等待人工 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FRZ-01 | Phase 1 | Pending |
| FRZ-02 | Phase 1 | Pending |
| FRZ-03 | Phase 1 | Pending |
| FRZ-04 | Phase 1 | Pending |
| FRZ-05 | Phase 1 | Pending |
| FRZ-06 | Phase 1 | Pending |
| EXTR-01 | Phase 2 | Pending |
| EXTR-02 | Phase 2 | Pending |
| EXTR-03 | Phase 2 | Pending |
| EXTR-04 | Phase 2 | Pending |
| EXTR-05 | Phase 2 | Pending |
| STAB-01 | Phase 3 | Pending |
| STAB-02 | Phase 3 | Pending |
| STAB-03 | Phase 3 | Pending |
| STAB-04 | Phase 3 | Pending |
| GRADE-01 | Phase 4 | Pending |
| GRADE-02 | Phase 4 | Pending |
| GRADE-03 | Phase 4 | Pending |
| GRADE-04 | Phase 4 | Pending |
| PACK-01 | Phase 5 | Pending |
| PACK-02 | Phase 5 | Pending |
| PACK-03 | Phase 5 | Deferred to v2.1 |
| PACK-04 | Phase 5 | Deferred to v2.1 |
| PACK-05 | Phase 5 | Deferred to v2.1 |

**Coverage:**
- v2.0 requirements: 24 total
- Active (v2.0 in scope): 21
- Deferred to v2.1: 3 (PACK-03, PACK-04, PACK-05)
- Mapped to phases: 21 active + 3 deferred
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-18*
*Last updated: 2026-04-18 after v2.0 milestone definition*
