# Test Environment 格式规范

> 本文档定义 `test_environment_ref` 指向的 environment YAML 文件的标准格式。
> 当前为**手动创建**阶段，后续由 `qa.environment-provision` 技能自动生成。

---

## 一、存储位置

```
ssot/environments/
├── ENV-FEAT-SRC-001-001.yaml
├── ENV-FEAT-SRC-003-001.yaml
└── ENV-<feat_id>.yaml
```

命名规则：`ENV-{feat_id}.yaml`，一个 FEAT 对应一个 environment。

---

## 二、完整字段定义

### 2.1 必需字段（所有 execution_modality）

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | string | 唯一标识 | `ENV-FEAT-SRC-001-001` |
| `ssot_type` | string | 固定值 | `"TESTENV"` |
| `execution_modality` | string | 执行模式 | `"web_e2e"` 或 `"cli"` |
| `feat_ref` | string | 关联的 FEAT | `FEAT-SRC-001-001` |

### 2.2 web_e2e 模式必需字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `base_url` | string | 被测目标 URL | `http://localhost:3000` |
| `browser` | string | 浏览器引擎 | `"chromium"`, `"firefox"`, `"webkit"` |

### 2.3 cli 模式必需字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `command_entry` | string | 入口命令 | `python -m cli.main` |
| 或 `runner_command` | string | Runner 命令 | `node dist/runner.js` |

### 2.4 可选字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `headless` | boolean | `true` | 无头模式（仅 web_e2e） |
| `viewport` | object | `{width: 1280, height: 720}` | 浏览器视口（仅 web_e2e） |
| `timeout` | number | `30000` | 单用例超时（毫秒） |
| `coverage_mode` | string | `"auto"` | `"auto"`, `"smoke"`, `"qualification"`, `"off"` |
| `coverage_enabled` | boolean | 由 coverage_mode 推导 | 是否启用覆盖率 |
| `coverage_include` | list[string] | 无 | 覆盖率包含路径 |
| `coverage_source` | list[string] | 无 | 覆盖率源码路径 |
| `coverage_branch` | boolean | `true` | 是否收集分支覆盖率 |
| `qualification_budget` | number | `1`（继承自 TESTSET） | qualification 扩展预算轮次 |
| `max_expansion_rounds` | number | `1`（继承自 TESTSET） | 最大用例扩展轮次 |
| `description` | string | 无 | 环境描述 |
| `created_at` | string | 无 | 创建时间 ISO 8601 |
| `created_by` | string | 无 | 创建者 |

---

## 三、代码校验规则

从 `test_exec_runtime.py` 和 `test_exec_execution.py` 推导出的校验规则：

### 3.1 execution_modality 校验（`_validate_environment`）

```python
# test-exec-web-e2e 要求：
execution_modality == "web_e2e"
base_url in environment        # 必须存在
browser in environment         # 必须存在

# test-exec-cli 要求：
execution_modality == "cli"
(command_entry or runner_command) in environment  # 至少一个
```

### 3.2 coverage_mode 处理（`_coverage_mode` + `_apply_testset_coverage_defaults`）

```
coverage_mode == "off"       → coverage_enabled = False
coverage_mode == "smoke"     → coverage_enabled = False（不收集）
coverage_mode == "qualification" → coverage_enabled = True（需 coverage_include 或 feature_owned_code_paths）
coverage_mode == "auto"      → 自动推导（默认）
```

### 3.3 运行时环境变量注入（`_execution_env`）

执行时，environment 的以下字段会注入到子进程环境变量：

```
LEE_BASE_URL        ← environment.base_url
LEE_BROWSER         ← environment.browser
LEE_EXECUTION_MODALITY ← environment.execution_modality
LEE_TEST_CASE_ID    ← case.case_id
LEE_TEST_CASE_TITLE ← case.title
LEE_TEST_PRIORITY   ← case.priority
LEE_TRIGGER_ACTION  ← case.trigger_action
```

---

## 四、模板

### 4.1 web_e2e 模板

```yaml
id: ENV-FEAT-SRC-XXX-YYY
ssot_type: TESTENV
execution_modality: web_e2e
feat_ref: FEAT-SRC-XXX-YYY
base_url: "http://localhost:3000"
browser: chromium
headless: true
viewport:
  width: 1280
  height: 720
timeout: 30000
coverage_mode: auto
coverage_branch: true
description: "本地开发环境 - {功能描述}"
created_at: "2026-04-21T00:00:00Z"
created_by: "your-name"
```

### 4.2 cli 模板

```yaml
id: ENV-FEAT-SRC-XXX-YYY
ssot_type: TESTENV
execution_modality: cli
feat_ref: FEAT-SRC-XXX-YYY
command_entry: "python -m cli.main"
coverage_mode: auto
coverage_branch: true
description: "CLI 执行环境 - {功能描述}"
created_at: "2026-04-21T00:00:00Z"
created_by: "your-name"
```

### 4.3 staging 环境模板

```yaml
id: ENV-FEAT-SRC-XXX-YYY
ssot_type: TESTENV
execution_modality: web_e2e
feat_ref: FEAT-SRC-XXX-YYY
base_url: "https://staging.example.com"
browser: chromium
headless: true
timeout: 60000
coverage_mode: smoke
description: "Staging 环境 - {功能描述}"
created_at: "2026-04-21T00:00:00Z"
created_by: "your-name"
```

---

## 五、与 TESTSET 的关系

```
FEAT
 ├──→ qa.feat-to-testset → TESTSET.yaml（定义"测什么"）
 └──→ 手动/未来技能 → ENV.yaml（定义"在哪测"）
        ↓
test_set_ref + test_environment_ref 一起传入 test-exec-* 技能
        ↓
execute_test_exec_skill()
```

| 来源 | 负责内容 | 关键字段 |
|------|----------|----------|
| **TESTSET** | 测试范围、test_units、coverage_scope | `test_units`, `feature_owned_code_paths` |
| **ENV** | 执行目标、浏览器、超时 | `base_url`, `browser`, `timeout` |

ENV 中的 `coverage_*` 字段如果未显式设置，会从 TESTSET 的 `feature_owned_code_paths` 和 `recommended_coverage_scope_name` 自动推导（由 `_apply_testset_coverage_defaults()` 完成）。

---

## 六、生命周期

```
[创建] 手动创建 ENV-{feat_id}.yaml（当前阶段）
  ↓
[使用] 执行时通过 test_environment_ref 传入
  ↓
[校验] _validate_environment() 校验必需字段
  ↓
[注入] 执行时将 base_url/browser 注入子进程环境变量
  ↓
[记录] environment._source_ref 写入 candidate artifact（可追溯）
  ↓
[未来] 由 qa.environment-provision 技能从 FEAT + TESTSET 自动生成
```

---

> 文档版本: 1.0
> 最后更新: 2026-04-21
> 状态: 手动创建阶段
