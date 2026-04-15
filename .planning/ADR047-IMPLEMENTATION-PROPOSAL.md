# ADR-047 双链测试技能实现方案

**日期:** 2026-04-14
**状态:** 已确认
**来源:** ADR-047 §11.1 技能层级 + §3.8 编译链设计 + CLI 协议分析

---

## 一、现状总结

### 11 个目标技能清单

| # | 技能 | ADR-047 层级 | 编译链步骤 | 当前状态 |
|---|------|-------------|-----------|---------|
| 1 | `ll-qa-feat-to-apiplan` | 设计层 | Step 1: feat → api-test-plan | 空壳 |
| 2 | `ll-qa-prototype-to-e2eplan` | 设计层 | Step 1: prototype → e2e-journey-plan | 空壳 |
| 3 | `ll-qa-api-manifest-init` | 设计层 | Step 1: plan → manifest 初始化 | 空壳 |
| 4 | `ll-qa-e2e-manifest-init` | 设计层 | Step 1: plan → manifest 初始化 | 空壳 |
| 5 | `ll-qa-api-spec-gen` | 设计层 | Step 2: manifest → spec | 空壳 |
| 6 | `ll-qa-e2e-spec-gen` | 设计层 | Step 2: manifest → spec | 空壳 |
| 7 | `ll-qa-settlement` | 结算层 | settlement report 生成 | 空壳 |
| 8 | `ll-qa-gate-evaluate` | 结算层 | release_gate_input.yaml 生成 | 空壳 |
| 9 | `ll-test-exec-cli` | 执行层 | spec → script → exec → evidence | 半空（有 lifecycle/contract，无 scripts）|
| 10 | `ll-skill-install` | 工具层 | 技能安装/注册 | 空壳 |
| 11 | `ll-dev-feat-to-tech` | 开发层 | feat → tech spec | 有 18 个 scripts 但 0 测试覆盖 |

### 缺失的 ADR-047 层
- **生成层**（`api-spec-to-tests` / `e2e-spec-to-tests`）— 连骨架都没有
- **兼容层**（`render-testset-view`）— 连骨架都没有

---

## 二、CLI 调用协议架构

### 2.1 完整调用链路（6 层）

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 0: LLM (Claude Code CLI 子进程)                            │
│  读取 SKILL.md + agents/*.md，理解要做什么                          │
│  调用: python -m cli <group> <action> --request ...              │
└────────────────────────┬────────────────────────────────────────┘
                         │ subprocess 调用
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: CLI 入口 (cli/ll.py)                                     │
│  build_parser() → 路由到 handle_skill()                            │
│  参数: --request <request.json> --response-out <resp.json>         │
│                                                                    │
│  已注册 7 个 skill action:                                         │
│  impl-spec-test, test-exec-web-e2e, test-exec-cli,                │
│  gate-human-orchestrator, failure-capture, spec-reconcile,        │
│  tech-to-impl                                                      │
│                                                                    │
│  需新增: feat-to-apiplan, prototype-to-e2eplan,                    │
│           api-manifest-init, e2e-manifest-init,                    │
│           api-spec-gen, e2e-spec-gen,                              │
│           settlement, gate-evaluate                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: 协议层 (cli/lib/protocol.py)                              │
│  run_with_protocol() → load_context()                              │
│  - 读取 request.json，提取 payload + trace                          │
│  - 校验 API version、command 匹配                                   │
│  - 构建 CommandContext(request_path, response_path, ...)            │
│  - 调用 handler(ctx) → 返回 (status, message, data, ...)            │
│  - build_response() → write response.json + evidence.json           │
│                                                                    │
│  核心保证:                                                           │
│  - 输入必须是合法 JSON，包含 api_version/command/request_id/payload  │
│  - 输出必须包含 canonical_path（成功时）                              │
│  - 错误返回标准 status_code + exit_code                              │
│  - evidence 独立文件记录                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Skill Handler (cli/commands/skill/command.py)             │
│  _skill_handler(ctx) 根据 ctx.action 路由:                           │
│                                                                    │
│  impl-spec-test   → cli/lib/impl_spec_test_runtime.py             │
│  test-exec-web-e2e → cli/lib/test_exec_runtime.py                 │
│  test-exec-cli    → cli/lib/test_exec_runtime.py                  │
│  gate-human-orch  → cli/lib/gate_human_orchestrator_skill.py      │
│  spec-reconcile   → cli/lib/spec_reconcile_skill.py               │
│  failure-capture  → cli/lib/failure_capture_skill.py              │
│  tech-to-impl     → skills/ll-dev-tech-to-impl/scripts/*.py       │
│                                                                    │
│  需新增: QA 技能路由分支（每个 action 一个分支）                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: 业务逻辑层                                                 │
│  两种实现方式:                                                        │
│                                                                    │
│  A) Prompt-first（本轮）:                                            │
│     - sys.path.insert(skill scripts)                                │
│     - 调用 Claude Code 子进程做 LLM 推理                               │
│     - LLM 读取输入文件，按 ADR-047 规则生成输出文件                      │
│     - Python wrapper 收集 canonical_path + evidence                  │
│                                                                    │
│  B) Python 完整运行时（后续）:                                         │
│     - 纯 Python 实现业务逻辑                                          │
│     - 结构化解析/生成，不依赖 LLM                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5: 文件系统产物                                               │
│  .artifacts/<skill>/<run_id>/                                      │
│  ├── output_package/                                               │
│  │   └── <generated files> (YAML/JSON/Markdown)                    │
│  ├── execution_evidence.json                                       │
│  └── supervisor_review.json                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 以 `ll-product-src-to-epic` 为例的完整流程

```
Step 1: LLM 读取 SKILL.md
  → 理解：这是一个 SRC → EPIC 的转换技能
  → 读取 input/contract.yaml（输入契约）
  → 读取 agents/executor.md（执行 prompt）
  → 读取 agents/supervisor.md（监督 prompt）

Step 2: LLM 调用 CLI
  python -m cli skill src-to-epic \
    --request artifacts/requests/req-001.json \
    --response-out artifacts/responses/resp-001.json \
    --workspace-root /path/to/repo

Step 3: cli/ll.py 路由
  main() → build_parser() → skill group → handle_skill(args)

Step 4: protocol.py 加载上下文
  load_context(args)
    → 读取 artifacts/requests/req-001.json
    → 校验 {"command": "skill.src-to-epic", "api_version": "v1"}
    → 构建 CommandContext {
        request_path, response_path,
        workspace_root, group="skill", action="src-to-epic",
        payload={impl_ref, feat_ref, ...},
        trace={run_ref, ...}
       }

Step 5: _skill_handler(ctx) 路由
  → ctx.action == "src-to-epic"
  → sys.path.insert(0, "skills/ll-product-src-to-epic/scripts")
  → from src_to_epic_runtime import run_workflow
  → result = run_workflow(input_path, repo_root, ...)
  → 返回 ("OK", "governed skill candidate emitted",
          {canonical_path, handoff_ref, ...}, [], evidence_refs)

Step 6: protocol.py 写出响应
  build_response() → {
    "api_version": "v1",
    "command": "skill.src-to-epic",
    "result_status": "success",
    "status_code": "OK",
    "exit_code": 0,
    "data": {canonical_path, handoff_ref, ...},
    "evidence_refs": [...]
  }
  → 写入 artifacts/responses/resp-001.json
  → 如有 --evidence-out，同时写入 evidence.json
```

### 2.3 核心设计模式

**Request-Response 文件协议**

每个调用通过 JSON 文件传递，不是内存对象：
- `request.json` = 输入（包含 payload + trace）
- `response.json` = 输出（包含 status_code + data + evidence_refs）
- `evidence.json` = 证据（包含 response_ref + trace）

允许 LLM 子进程和父进程之间通过文件通信，不依赖共享内存。

**sys.path 动态插入**

```python
# cli/commands/skill/command.py 第 77-79 行
scripts_dir = resolve_skill_scripts_dir(ctx.workspace_root, "ll-dev-tech-to-impl")
sys.path.insert(0, str(scripts_dir.resolve()))
from tech_to_impl_runtime import run_workflow  # 从 skill 的 scripts/ 导入
```

每个 skill 的 `scripts/` 目录在运行时被动态加入 Python 路径。

**合约强制**

```python
enforce_ll_contract_payload(ctx.workspace_root, skill_dir_ref, payload)
```

在执行前校验 payload 是否符合 skill 的 `ll.contract.yaml` 定义。

### 2.4 Prompt-first + CLI 协议 = 正确路线

之前我把"Prompt-first"和"CLI 协议"对立起来了，这是概念混淆。两个维度是正交的：

```
                    │ 有 CLI 协议                    │ 无 CLI 协议
────────────────────┼────────────────────────────────┼──────────────────
Python 完整运行时   │ A. 完整生产级                   │ C. 混乱（危险）
                    │ 已有技能的路线                  │ LLM 直接读写文件
                    │                                 │ 没有约束
────────────────────┼────────────────────────────────┼──────────────────
Prompt-first        │ B. 我们要选的路线 ✅             │ D. 纯 prompt 乱飞
                    │ CLI 协议保证稳定性               │ 没有输入校验
                    │ LLM 做推理，CLI 做边界约束        │ 没有错误处理
```

**Prompt-first 指的是 Layer 4（业务逻辑层）让 LLM 做推理决策，而不是用 Python 硬编码业务规则。CLI 协议是 Layer 1-3 的边界约束，两者都要。**

CLI 协议提供的保证：
| CLI 协议做的事 | Prompt-first 做的事 |
|---|---|
| 输入格式校验（`enforce_ll_contract_payload`） | 推理如何从 feat 生成 api-test-plan |
| 输出必须有 `canonical_path` | 推理 output 应该长什么样 |
| evidence refs 收集 | 推理需要哪些证据 |
| 错误返回标准状态码 | 推理遇到不确定情况怎么处理 |
| trace 链路追踪 | 推理上游依赖关系 |

---

## 三、实现方案

### 3.1 每个技能需要的文件

```
skills/ll-qa-feat-to-apiplan/
├── SKILL.md              # 已有，需要修订
├── ll.contract.yaml      # 已有
├── scripts/
│   ├── run.sh            # 新建：CLI 协议入口 wrapper
│   └── qa_skill_runtime.py  # 新建：通用 QA skill 运行时（可复用）
├── agents/
│   ├── executor.md       # 新建：LLM prompt（业务推理）
│   └── supervisor.md     # 新建：LLM prompt（输出校验）
├── validate_input.sh     # 新建：检查 request.json 是否符合 contract
└── validate_output.sh    # 新建：检查 response.json + canonical_path
```

### 3.2 CLI 侧需要改动的文件

```
cli/ll.py                 # 新增 QA skill actions
cli/commands/skill/command.py  # 新增 QA 路由分支
cli/lib/qa_schemas.py     # Phase 1 产出：统一 schema 验证器
cli/lib/qa_skill_runtime.py  # 通用 QA skill 运行时（可被所有 QA skill 复用）
```

### 3.3 Phase 分解

| Phase | 目标 | 产出 |
|-------|------|------|
| **1: QA Schema 定义** | 统一 schema + Python 验证器 | `ssot/schemas/qa/*.yaml` + `cli/lib/qa_schemas.py` |
| **2: CLI 协议注册 + 骨架** | 11 个技能全部注册到 CLI + 基本文件结构 | `cli/ll.py` 新增 actions + 每个 skill 的 scripts/agents/validate |
| **3: 业务逻辑实现** | 每个技能的 agents/executor.md 填充 | LLM prompt 模板，能跑通 dry-run |
| **4: API 链全流程试点** | 真实 feat 跑通 plan→gate 全链 | 试点报告 + 改进建议 |

---

## 四、关键决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 业务逻辑实现方式 | Prompt-first（LLM 推理） | 快速试点，验证 ADR-047 设计 |
| 边界约束 | CLI 协议（不可妥协） | 保证输入校验、输出格式、错误处理、证据收集 |
| Schema 真理源 | `ssot/schemas/qa/` | 独立于代码，skills 和验证器都读取 |
| 试点链 | 先 API 链 | API 锚定 feat（已有实现），不依赖前端 |

---

## 五、试点路径

```
选择一个真实 feat YAML
  → ll-qa-feat-to-apiplan（生成 api-test-plan + manifest 草稿）
  → ll-qa-api-manifest-init（冻结 manifest）
  → ll-qa-api-spec-gen（编译为 api-test-spec）
  → ll-test-exec-cli（执行测试，收集证据）
  → ll-qa-settlement（生成 settlement report）
  → ll-qa-gate-evaluate（生成 release_gate_input.yaml）
```

每个步骤都走完整的 CLI 协议：request.json → CLI → response.json + evidence。
