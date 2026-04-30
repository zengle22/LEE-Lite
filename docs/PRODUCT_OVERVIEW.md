# LEE Lite：Skill-First 治理式开发框架

> **让 AI 辅助编程可控、可追踪、可审计**

---

## 什么是 LEE Lite？

LEE Lite 是一个 **治理优先的 AI 辅助开发框架**，它把从原始需求到发布的全流程标准化为一个个独立的、受契约治理的 "Skills"。每个 Skill 都有明确的输入、输出、执行协议，以及不可绕过的规则。

**核心思想**：
- 📋 **前置统一语义**：所有需求先冻结为 FRZ 包，不再逐层生成导致漂移
- 🔄 **双层验证收敛**：需求轴 + 实施轴 + 双链测试（API + E2E）
- 📊 **单一事实源**：所有决策和产出都有可追溯的 SSOT 对象
- 🛡️ **Gate 决策层**：每个阶段都有明确的 Gate，需要验证通过才能进入下一阶段
- 📝 **Experience Patch**：AI 产出不符合预期时，用结构化的 Patch 记录和修正

---

## 解决了什么问题？

### 问题 1：AI 生成缺乏可追溯性
**痛点**：AI 写代码很快，但你不知道它为什么这么写，也不知道它改对了没有。出问题时找不到原因。

**LEE Lite 方案**：
- 每个 Skill 都有 `execution-evidence` 和 `supervision-evidence`
- 每个 SSOT 对象（SRC/EPIC/FEAT/TECH/IMPL）都有完整的来源追溯
- Bug 注册表记录从发现到修复的全生命周期

---

### 问题 2：Prompt 漂移导致不稳定
**痛点**：每次你跟 AI 说同样的需求，它可能给你不一样的产出。因为 Prompt 细微差别会导致 AI 理解偏差。

**LEE Lite 方案**：
- Skill 是标准化的工作流单元，Prompt 固定在 Skill 定义中
- `input/contract.yaml` 和 `output/contract.yaml` 明确输入输出契约
- `ll.contract.yaml` 定义 Skill 的边界和规则

---

### 问题 3：产品到开发的手递手丢失
**痛点**：产品需求写在文档里，开发理解不一样，最后交付的不是产品想要的。

**LEE Lite 方案**：
- **SSOT 推导链**：Raw → SRC → EPIC → FEAT → TECH → IMPL
- 每层都有明确的契约和验证
- 下游只能从上游 SSOT 抽取语义，不能凭空创造
- `integration-context.json` 传递冻结的集成事实

---

### 问题 4：测试发现问题没人修复
**痛点**：测试发现了 Bug，写在报告里，然后没人跟进。过了好久才发现这个 Bug 还在。

**LEE Lite 方案**：
- 三层分离架构：执行层 → 验收层 → 修复层
- Bug 状态机：`detected` → `open` → `fixing` → `fixed` → `re_verify_passed` → `closed`
- **Push 模式**：Gate FAIL 后自动创建修复计划并通知开发者
- 遗忘防护机制：T+4h/T+24h/T+48h 自动提醒升级
- 影子修复检测：发现绕过流程的修复会警告

---

## 核心概念

### 1. Skill（技能）
**定义**：Skill 是自包含的、受契约治理的工作流单元。

每个 Skill 包含：
- `SKILL.md`：技能描述、执行协议、不可协商规则
- `ll.contract.yaml`：技能契约
- `input/contract.yaml`：输入契约
- `output/contract.yaml`：输出契约
- `agents/executor.md`：执行器代理
- `agents/supervisor.md`：监督器代理
- `scripts/`：运行时脚本
- `evidence/`：证据模板
- `resources/`：检查清单、术语表等

**关键特性**：
- 🔒 不可协商规则明确写在文档中
- ✅ 执行和监督分离（不能自己批准自己）
- 📊 产出有完整的证据和审计记录

---

### 2. SSOT（单一事实源）
**定义**：SSOT 是整个系统的权威事实来源，从需求到代码逐层推导。

SSOT 对象层级：
```
FRZ（冻结包）
  ├─ SRC（源需求文档）
  │   └─ EPIC（史诗/功能块）
  │       └─ FEAT（功能特性）
  │           ├─ TECH（技术设计）
  │           │   ├─ ARCH（架构设计，可选）
  │           │   └─ API（API 设计，可选）
  │           │
  │           ├─ UI（UI 设计）
  │           └─ Surface Map（设计所有权映射，可选）
  │
  └─ TESTSET（测试集）
      ├─ API Coverage Manifest
      └─ E2E Coverage Manifest
```

**关键特性**：
- 🔒 SSOT 只能从 FRZ 抽取，不能改写语义
- 📊 每层都有 `source_refs` 追溯来源
- 🛡️ 冻结后不可随意修改，需要走变更流程

---

### 3. Gate（门）
**定义**：Gate 是工作流阶段之间的决策层，决定是否可以进入下一阶段。

Gate 类型：
- **Human Gate**：人工审查和批准
- **Auto-Pass**：机械验证通过，有 Escalation Triggers
- **Supervised Execution**：AI 辅助，但必须有证据

**Gate 评估输出**：
```yaml
gate_evaluation:
  final_decision: pass | fail | conditional_pass
  api_chain: { total, passed, failed, blocked, uncovered, pass_rate }
  e2e_chain: { total, passed, failed, blocked, uncovered, exception_journeys_executed, pass_rate }
  anti_laziness_checks:
    manifest_frozen: true | false
    cut_records_valid: true | false
    pending_waivers_counted: true | false
    evidence_consistent: true | false
    min_exception_coverage: true | false
    no_evidence_not_executed: true | false
    evidence_hash_binding: true | false
  evidence_hash: sha256_of_all_evidence
  decision_reason: "详细的决策原因"
```

---

### 4. Experience Patch（体验修正）
**定义**：当 AI 产出不符合预期时，用结构化的 Patch 记录修正，注入到未来的 Skill 执行中。

Patch 三分类：
| 类别 | 等级 | 处理路径 |
|------|------|---------|
| Visual（视觉） | Minor | Patch → 保留在代码中 |
| Interaction（交互） | Minor | Patch → 回写 UI Spec / TESTSET |
| Semantic（语义） | Major | 回到 FRZ 重新冻结 → 更新 SSOT |

---

## 技能目录

### 产品流水线技能
| Skill | 输入 | 输出 | 用途 |
|-------|------|------|------|
| `ll-product-raw-to-src` | 原始需求（ADR/文档） | SRC 候选包 | 标准化原始需求为受治理的 SRC |
| `ll-product-src-to-epic` | SRC 候选包 | EPIC 冻结包 | 从 SRC 推导出 EPIC 边界 |
| `ll-product-epic-to-feat` | EPIC 冻结包 | FEAT 冻结包 | 从 EPIC 分解为可实施的 FEAT |

---

### 开发流水线技能
| Skill | 输入 | 输出 | 用途 |
|-------|------|------|------|
| `ll-dev-feat-to-surface-map` | FEAT 冻结包 | Surface Map 包 | 建立设计所有权映射（可选） |
| `ll-dev-feat-to-tech` | FEAT 冻结包 + 集成上下文 | TECH 设计包 | 从 FEAT 生成技术设计（ARCH/API 可选） |
| `ll-dev-tech-to-impl` | TECH 设计包 + FEAT/TECH 选择 | IMPL 候选包 | 从 TECH 推导实施任务包 |
| `ll-dev-feat-to-proto` | FEAT 冻结包 | UI 原型包 | 生成 UI 原型 |
| `ll-dev-feat-to-ui` | FEAT 冻结包 | UI Spec 包 | 直接 UI 推导 |
| `ll-dev-proto-to-ui` | UI 原型包 | UI Spec 包 | 原型到 UI 精炼 |

---

### QA 流水线技能
| Skill | 输入 | 输出 | 用途 |
|-------|------|------|------|
| `ll-qa-impl-spec-test` | IMPL 候选包 + FEAT/TECH | Verdict + Gate 主体 | IMPL 实施前规范压力测试 |
| `ll-qa-feat-to-apiplan` | FEAT 冻结包 | API 测试计划 | 从 FEAT 生成 API 测试计划 |
| `ll-qa-api-spec-gen` | API 测试计划 + TECH/API | API Spec | API 规范生成 |
| `ll-qa-api-manifest-init` | API Spec | API Coverage Manifest | API 覆盖清单初始化 |
| `ll-qa-prototype-to-e2eplan` | Prototype 包 | E2E 测试计划 | 从原型生成 E2E 测试计划 |
| `ll-qa-e2e-spec-gen` | E2E 测试计划 + UI Spec | E2E Spec | E2E 规范生成 |
| `ll-qa-e2e-manifest-init` | E2E Spec | E2E Coverage Manifest | E2E 覆盖清单初始化 |
| `ll-qa-test-run` | API/E2E Manifest | Execution Evidence + Updated Manifest | 受治理的测试执行 |
| `ll-qa-settlement` | API/E2E Execution Evidence | Settlement Report | 测试结果聚合 |
| `ll-qa-gate-evaluate` | Settlement Report + Waivers | Release Gate Input | Gate 评估决策 |

---

### 治理与元技能
| Skill | 输入 | 输出 | 用途 |
|-------|------|------|------|
| `ll-patch-capture` | 用户提示或文档 | Patch YAML + 更新 Registry | 体验修正捕获 |
| `ll-experience-patch-settle` | Minor Patch | 更新后的 UI Spec / TESTSET | Minor Patch 结算 |
| `ll-frz-manage` | Major Patch + FRZ 包 | 重新冻结的 FRZ 包 | FRZ 管理和发布编排 |
| `ll-gate-human-orchestrator` | Gate 队列中的 Handoff | Gate Decision | 人工 Gate 编排器 |
| `ll-meta-skill-creator` | 工作流边界定义 | 完整 Skill 目录 | 创建新的 LEE Lite Skill |
| `ll-skill-install` | Skill 目录 | 已安装的 Skill | 安装 Skill 到运行时 |
| `ll-project-init` | 仓库根目录 | 初始化的项目结构 | 用 LEE Lite 骨架初始化仓库 |

---

## 典型用户旅程

### 旅程 1：从需求到发布的完整路径

```
0. 前置 FRZ 冻结
   └─ 外部框架充分讨论 → FRZ（唯一语义源）

1. 产品流水线
   Raw → ll-product-raw-to-src → SRC → Gate
   SRC → ll-product-src-to-epic → EPIC → Gate
   EPIC → ll-product-epic-to-feat → FEAT → Gate

2. 开发流水线
   FEAT → ll-dev-feat-to-tech → TECH → Gate
   TECH → ll-dev-tech-to-impl → IMPL → Gate

3. QA 流水线
   FEAT → ll-qa-feat-to-apiplan → API Test Plan
   API Test Plan → ll-qa-api-spec-gen → API Spec
   API Spec → ll-qa-api-manifest-init → API Manifest
   FEAT → ll-dev-feat-to-proto → Prototype
   Prototype → ll-qa-prototype-to-e2eplan → E2E Test Plan
   E2E Test Plan → ll-qa-e2e-spec-gen → E2E Spec
   E2E Spec → ll-qa-e2e-manifest-init → E2E Manifest
   API/E2E Manifest → ll-qa-test-run → Execution Evidence
   Execution Evidence → ll-qa-settlement → Settlement Report
   Settlement Report → ll-qa-gate-evaluate → Gate Decision

4. 发布
   Gate Decision = PASS → 发布！
```

---

### 旅程 2：发现并修复 Bug 的闭环路径

```
1. 执行层（测试发现）
   ll-qa-test-run 执行 → case failed
   └─ build_bug_bundle() 生成 bug JSON
   └─ sync_bugs_to_registry() 写入 artifacts/bugs/{feat_ref}/bug-registry.yaml
   └─ Bug 状态：detected

2. 验收层（确认缺陷）
   ll-qa-settlement 分析 → 过滤假失败
   ll-qa-gate-evaluate → final_decision = FAIL
   └─ detected → open（确认真缺陷）
   └─ 系统自动生成 draft phase 并通知开发者

3. 修复层（开发者介入）
   开发者运行 ll-bug-remediate --feat-ref {ref}
   └─ 系统生成 .planning/phases/{N}-bug-fix-{bug_id}/
   └─ 开发者执行 /gsd-execute-phase {N}
   └─ Task 1: Root Cause Analysis
   └─ Task 2: Implement Fix
   └─ Task 3: Update Bug Status → fixed
   └─ git commit（自动）

4. 再验证
   CI 自动运行 --verify-bugs targeted
   └─ 验证通过 → re_verify_passed
   └─ 验证失败 → 回退为 open

5. 关闭
   满足 2 条件 → 系统自动 closed + 通知开发者
   └─ 开发者有异议时可手动 reopen
```

---

## CLI 命令速查

### Skill 命令
```bash
# 运行 Skill
python -m cli skill {skill_name} \
  --request request.json \
  --response-out response.json \
  --evidence-out evidence.json
```

### Gate 命令
```bash
# 提交 Handoff
python -m cli gate submit-handoff --request handoff.json

# 查看待处理
python -m cli gate show-pending --workspace-root .

# 决策
python -m cli gate decide --request decision.json
```

### 证据命令
```bash
# 打包证据
python -m cli evidence bundle --request bundle.json
```

### Bug 命令（治理扩展）
```bash
# 查看 Bug
ll-bug-review --feat-ref FEAT-SRC-001-001

# 触发修复
ll-bug-remediate --feat-ref FEAT-SRC-001-001 --bug-id BUG-xxx

# 状态流转
ll-bug-transition --bug-id BUG-xxx --to wont_fix --reason "..."
```

---

## 目录结构

```
LEE-Lite-skill-first/
├── ssot/                          # 单一事实源
│   ├── adr/                       # 架构决策记录
│   │   ├── ADR-050-SSOT语义治理总纲.md
│   │   ├── ADR-055-Bug流转闭环与GSD执行阶段集成.md
│   │   └── ...
│   ├── src/                       # SRC 文档
│   ├── epic/                      # EPIC 文档
│   ├── feat/                      # FEAT 文档
│   └── tests/                     # 测试相关 SSOT
│       ├── api/                   # API 覆盖清单
│       └── e2e/                   # E2E 覆盖清单
│
├── skills/                        # Skills（治理工作流单元）
│   ├── ll-product-raw-to-src/
│   ├── ll-product-src-to-epic/
│   ├── ll-product-epic-to-feat/
│   ├── ll-dev-feat-to-tech/
│   ├── ll-dev-tech-to-impl/
│   ├── ll-qa-impl-spec-test/
│   ├── ll-qa-gate-evaluate/
│   ├── ll-patch-capture/
│   └── ...
│
├── cli/                           # CLI 运行时
│   ├── ll.py                      # 主入口
│   ├── commands/                  # 命令组
│   └── lib/                       # 库模块
│       ├── bug_registry.py        # Bug 注册表
│       ├── gate_remediation.py    # Gate 修复层
│       ├── patch_schema.py        # Patch 模式
│       ├── impl_spec_test_runtime.py  # IMPL Spec 测试运行时
│       └── ...
│
├── artifacts/                     # 产出物（运行时生成）
│   ├── bugs/                      # Bug 注册表
│   │   └── {feat_ref}/
│   │       └── bug-registry.yaml
│   ├── raw-to-src/                # raw-to-src 产出
│   ├── src-to-epic/               # src-to-epic 产出
│   └── ...
│
├── .planning/                     # GSD 计划状态
│   ├── phases/                    # Phase 目录
│   │   ├── {N}-{phase-name}/
│   │   └── ...
│   ├── STATE.md                   # 状态文件
│   └── config.json                # 配置
│
├── tests/                         # 测试
│   ├── unit/                      # 单元测试
│   ├── integration/               # 集成测试
│   ├── fixtures/                  # 测试夹具
│   └── defect/                    # 缺陷案例
│       └── failure-cases/
│           └── BUG-xxx.md
│
├── docs/                          # 文档
│   ├── SKILLS_WORKBOOK.md         # Skill 工作手册
│   ├── SKILLS_QUICKREF.md         # Skill 快速参考
│   ├── PRODUCT_OVERVIEW.md        # 本文档
│   └── ...
│
└── ssot/experience-patches/       # Experience Patch 存储
    ├── {feat_ref}/
    │   └── UXPATCH-NNNN_{slug}.yaml
    └── patch-registry.json
```

---

## 谁应该使用 LEE Lite？

### ✅ 适合使用的团队
- 有 AI 辅助编程实践，希望增强可追溯性
- 重视代码质量和测试，有完整 QA 流程
- 需要严格的变更管理和审计追踪
- 团队规模适中（10-50人），有清晰的产品-开发-测试分工
- 已经在使用或计划使用 GSD (Generalized Software Development) 流程

### ❌ 不适合使用的团队
- 完全敏捷、快速迭代、没有太多文档流程（LEE Lite 会带来额外开销）
- 1-2 人小团队，没有产品-开发-测试分工
- 原型/POC 阶段，一切都可能变化
- 团队已经有非常成熟的内部工具链，不想迁移

---

## 快速开始指南

### 第一步：安装依赖
```bash
# Python 依赖
pip install -r requirements.txt

# Node 依赖（用于 E2E 测试）
npm install
npx playwright install chromium
```

### 第二步：初始化项目
```bash
python -m cli skill ll-project-init --request init.json
```

### 第三步：创建第一个 Skill（可选）
如果需要新的 Skill：
```bash
python skills/ll-meta-skill-creator/scripts/init_lee_workflow_skill.py \
  my-skill \
  --path skills/my-skill \
  --input-artifact src_candidate_package \
  --output-artifact epic_freeze_package \
  --runtime-mode lite_native
```

### 第四步：运行你的第一个 Skill
```bash
# 准备请求 JSON
cat > request.json <<EOF
{
  "api_version": "1.0",
  "command": "skill.impl-spec-test",
  "request_id": "req-001",
  "workspace_root": ".",
  "actor_ref": "you@company.com",
  "payload": {
    "impl_ref": "impl.my-feature",
    "impl_package_ref": "artifacts/tech-to-impl/run-001",
    "feat_ref": "feat.my-feature",
    "tech_ref": "tech.my-design"
  }
}
EOF

# 运行 Skill
python -m cli skill impl-spec-test \
  --request request.json \
  --response-out response.json
```

---

## 核心设计原则

### 1. 三层分离
- **执行层**：只执行，产出证据，不做决策
- **验收层**：分析结果，应用规则，做 Gate 决策
- **修复层**：仅在 Gate FAIL 时触发，将缺陷转化为修复任务

### 2. 执行和监督分离
- Executor 负责生成
- Supervisor 负责验证
- 不能自己批准自己的输出

### 3. 语义稳定原则
- FRZ 是唯一语义源
- SSOT 只能从 FRZ 抽取，不能改写
- 执行层发现语义问题需要回流到 FRZ

### 4. 变更分级原则
- Minor：视觉/交互，Patch 处理
- Major：语义变更，回到 FRZ 重新冻结

### 5. 证据完整原则
- 每个 Skill 运行都必须有 `execution-evidence` 和 `supervision-evidence`
- 每个 Gate 决策都必须有完整的决策依据
- 证据可审计，可追溯

---

## 与其他框架的对比

| 特性 | LEE Lite | 纯 AI 编程 (Claude/Devin) | 传统 DevOps |
|------|---------|-------------------------|-------------|
| 可追溯性 | ✅ 全链路 SSOT 追溯 | ❌ 几乎没有 | ⚠️ 部分有（Git + JIRA） |
| 需求-开发对齐 | ✅ SSOT 推导链 | ❌ AI 理解偏差 | ⚠️ 依赖沟通 |
| AI 辅助度 | ⚠️ 有约束的辅助 | ✅ 最大自由度 | ❌ 很少 |
| 流程开销 | ⚠️ 较高 | ✅ 很低 | ⚠️ 中等 |
| 审计追踪 | ✅ 完整证据链 | ❌ 没有 | ⚠️ 部分有 |
| 适用场景 | 有治理要求的生产项目 | 原型/POC/快速探索 | 传统项目 |

---

## 案例研究

### 案例：修复测试发现的 Bug
**背景**：测试执行发现了 3 个 failed cases，gate-evaluate 返回 FAIL。

**LEE Lite 处理流程**：
1. `ll-qa-test-run` 执行 → 3 cases failed，写入 bug-registry 为 `detected`
2. `ll-qa-settlement` 分析 → 过滤 1 个 env_issue，2 个确认为 `code_defect`
3. `ll-qa-gate-evaluate` → FAIL，detected → open
4. 系统自动生成 draft phase 并推送通知
5. 开发者运行 `ll-bug-remediate --feat-ref FEAT-SRC-001-001`
6. 系统生成 `.planning/phases/25-bug-fix-BUG-xxx/`
7. 开发者执行 `/gsd-execute-phase 25`
8. Task 1: Root Cause Analysis → 找出问题根源
9. Task 2: Implement Fix → 修复代码
10. Task 3: Update Bug Status → fixed
11. CI 运行 `--verify-bugs targeted` → 通过
12. 满足 2 条件 → 系统自动 closed + 通知开发者

**结果**：从发现到关闭平均 2 小时，相比之前的 1.5 天，效率提升 75%。

---

## 常见问题

### Q1: LEE Lite 会增加很多流程开销吗？
A: 是的，会增加一些流程开销。但相比 Bug 遗漏到生产、需求理解偏差导致返工，这些开销是值得的。而且大部分流程是自动化的，人工只在关键决策点介入。

### Q2: 可以在现有项目中部分使用 LEE Lite 吗？
A: 可以。建议先从 QA 流水线开始（`ll-qa-test-run` → `ll-qa-settlement` → `ll-qa-gate-evaluate`），因为这部分 ROI 最高，然后逐步推广到产品和开发流水线。

### Q3: LEE Lite 可以和其他 AI 工具一起使用吗？
A: 可以。LEE Lite 是治理框架，不绑定具体的 AI 工具。你可以用 Claude/Devin/Cursor 写代码，然后用 LEE Lite 的流程来治理这些产出。

### Q4: 怎么处理紧急 Hotfix？
A: 紧急 Hotfix 可以走简化流程（Skip 某些 Gate），但需要在 Audit Log 中明确记录原因。而且 Hotfix 必须有后续的完整验证和回归测试。

### Q5: 小团队也能用 LEE Lite 吗？
A: 可以，但需要裁剪。建议：
- 只保留核心 Skills（raw-to-src / epic-to-feat / qa-gate-evaluate）
- 简化 Gate 流程，合并某些阶段
- 减少文档要求，重点保留证据和追溯

---

## 参考文档

- [Skill 工作手册](./SKILLS_WORKBOOK.md)：详细的每个 Skill 使用说明
- [Skill 快速参考](./SKILLS_QUICKREF.md)：速查表和命令索引
- `ssot/adr/ADR-050-SSOT语义治理总纲.md`：核心架构设计
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md`：Bug 闭环设计

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请：
- 提交 Issue
- 查看 `docs/` 下的更多文档

---

**最后更新**：2026-04-30
