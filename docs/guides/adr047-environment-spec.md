# Test Environment 格式规范 (v2.2)

> 本文档定义 `test_environment_ref` 指向的 environment YAML 文件的标准格式。
> **当前状态**: 由 `environment_provision.py` 自动生成 (v2.2)。

---

## 一、存储位置

```
ssot/environments/
├── ENV-{feat_id}.yaml          ← environment_provision.py 生成
└── .gitkeep
```

命名规则：`ENV-{feat_id}.yaml`，一个 FEAT 对应一个 environment。

---

## 二、完整字段定义

### 2.1 必需字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | string | 唯一标识 | `ENV-FEAT-SRC-001-001` |
| `ssot_type` | string | 固定值 | `"TESTENV"` |
| `execution_modality` | string | 执行模式 | `"web_e2e"` 或 `"cli"` |
| `feat_ref` | string | 关联的 FEAT | `FEAT-SRC-001-001` |

### 2.2 web_e2e 模式必需字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `base_url` | string | 被测前端 URL | `http://localhost:3000` |
| `api_url` | string | API 服务 URL | `http://localhost:8000` |
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
| `description` | string | 无 | 环境描述 |
| `created_at` | string | ISO 8601 | 创建时间 |
| `created_by` | string | `"ll-qa-test-run"` | 创建者 |

---

## 三、代码校验规则

### 3.1 execution_modality 校验

```python
# ll-qa-test-run 要求:
execution_modality == "web_e2e" → base_url + api_url + browser 必需
execution_modality == "cli" → command_entry 或 runner_command 必需
```

### 3.2 运行时环境变量注入

执行时，environment 的以下字段会注入到子进程环境变量：

```
LEE_BASE_URL        ← environment.base_url
LEE_API_URL         ← environment.api_url
LEE_BROWSER         ← environment.browser
LEE_EXECUTION_MODALITY ← environment.execution_modality
LEE_TEST_CASE_ID    ← case.case_id
LEE_TEST_CASE_TITLE ← case.title
LEE_TEST_PRIORITY   ← case.priority
LEE_TRIGGER_ACTION  ← case.trigger_action
```

---

## 四、模板

### 4.1 web_e2e 模板 (v2.2)

```yaml
id: ENV-{feat_id}
ssot_type: TESTENV
execution_modality: web_e2e
feat_ref: {feat_id}
base_url: "http://localhost:3000"
api_url: "http://localhost:8000"
browser: chromium
headless: true
viewport:
  width: 1280
  height: 720
timeout: 30000
coverage_mode: auto
description: "本地开发环境"
created_at: "2026-04-24T00:00:00Z"
created_by: "ll-qa-test-run"
```

### 4.2 cli 模板

```yaml
id: ENV-{feat_id}
ssot_type: TESTENV
execution_modality: cli
feat_ref: {feat_id}
command_entry: "python -m cli.main"
coverage_mode: auto
description: "CLI 执行环境"
created_at: "2026-04-24T00:00:00Z"
created_by: "ll-qa-test-run"
```

### 4.3 staging 环境模板

```yaml
id: ENV-{feat_id}
ssot_type: TESTENV
execution_modality: web_e2e
feat_ref: {feat_id}
base_url: "https://staging.example.com"
api_url: "https://staging-api.example.com"
browser: chromium
headless: true
timeout: 60000
coverage_mode: smoke
description: "Staging 环境"
created_at: "2026-04-24T00:00:00Z"
created_by: "ll-qa-test-run"
```

---

## 五、v2.2 变更

### 5.1 新增字段

| 字段 | 说明 | 来源 |
|------|------|------|
| `api_url` | API 服务 URL | v2.2 新增（分离架构） |

### 5.2 生成方式变更

| 版本 | 生成方式 |
|------|----------|
| v2.1 | 手动创建 |
| **v2.2** | **environment_provision.py 自动生成** |

```python
# cli/lib/environment_provision.py
def generate_environment(
    feat_ref: str,
    base_url: str,
    api_url: str = None,
    browser: str = "chromium"
) -> EnvConfig:
    """从 FEAT + 用户参数生成 ENV YAML"""
    return EnvConfig(
        id=f"ENV-{feat_ref}",
        base_url=base_url,
        api_url=api_url,
        browser=browser,
        execution_modality="web_e2e"
    )
```

---

## 六、与实施轴的关系 (ADR-054)

```
environment_provision (v2.2)
        ↓
ll-qa-test-run
        ↓
test_orchestrator
        ↓
state_machine_executor
        ↓
independent_verifier → settlement → gate
```

---

## 七、生命周期

```
[生成] environment_provision.generate() (v2.2 自动)
  ↓
[使用] ll-qa-test-run 执行时引用
  ↓
[校验] test_orchestrator 校验必需字段
  ↓
[注入] 执行时将配置注入子进程环境变量
  ↓
[记录] environment._source_ref 写入 StepResult（可追溯）
```

---

> **文档版本**: v2.2
> **最后更新**: 2026-04-24
> **状态**: v2.2 自动生成
