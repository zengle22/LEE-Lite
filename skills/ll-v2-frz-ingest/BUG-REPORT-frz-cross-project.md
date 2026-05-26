# BUG REPORT: ll-v2-frz-ingest 跨项目复用阻塞

> 报告者: Claude Code (ai-marathon-root-v2 项目)
> 日期: 2026-05-26
> 优先级: P1 — 技能声明为通用 FRZ 工作流，实际仅支持 LEE-Lite 单一项目

---

## 1. 执行摘要 (Executive Summary)

`ll-v2-frz-ingest` 技能在 `ai-marathon-root-v2` 项目（非 LEE-Lite）上执行时，
**脚本从未成功自动运行**。所有 FRZ 输出均为人工手动生成。

根本原因不是路径配置问题，而是 `cli.lib.v2` 包内存在三层与 LEE-Lite 项目强耦合的硬编码，
导致该技能在物理上无法应用于其他项目。

---

## 2. 问题 #2: 运行日志缺失

### 现象
- 技能被调用后，**没有任何自动生成的运行日志**
- `~/.claude/skills/ll-v2-frz-ingest/` 目录下不存在 `logs/` 或任何运行时产物
- 所有 M12 FRZ 产物（`M12-SSOT.yml`、`M12-FRZ-PACKAGE.yml`、`M12-DRIFT-REPORT.md`、`TESTSET-M12-Onboarding-Identity.md`）均为人工分析后手动撰写

### 根因
脚本在 `import` 阶段即崩溃（`ModuleNotFoundError`），后续所有步骤（包括日志初始化）从未执行。见问题 #3 详述。

### 建议修复
- 在 `frz_ingest.py` 的**最早可执行点**（`sys.path` 调整之后、`import cli.lib` 之前）初始化日志目录和文件句柄
- 即使脚本后续崩溃，也应保留启动日志和堆栈跟踪

```python
# 建议插入位置: frz_ingest.py 第 12 行之后
import logging, os
log_dir = Path(__file__).resolve().parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=log_dir / "frz-ingest.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
```

---

## 3. 问题 #3: Python 脚本三层阻塞

### 3.1 第一层: 模块路径解析错误 (已修复，但暴露设计缺陷)

**文件:** `src/frz_ingest.py` 第 16–19 行

```python
_workspace_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))
```

**问题:** 假设 `~/.claude/` 目录下存在 `cli.lib` 包，但 `cli.lib` 实际位于 `~/git/LEE-Lite/cli/lib/`。

**修复状态:** 用户已手动调整环境变量绕过。

**建议修复:** 不要将路径解析与技能目录深度耦合。应通过配置项或环境变量指定 `cli.lib` 根目录：

```python
import os
CLI_LIB_PATH = os.environ.get("CLI_LIB_PATH", str(
    Path(__file__).resolve().parent.parent.parent.parent / "cli" / "lib"
))
if CLI_LIB_PATH not in sys.path:
    sys.path.insert(0, CLI_LIB_PATH)
```

---

### 3.2 第二层: 文档结构解析器不支持通用目录布局

**文件:** `cli/lib/v2/parser.py`

**问题:** `parse_design_package()` 仅支持两种目录布局：

1. **Structured 模式**: 根目录下直接存在 `business_design/`、`product_design/`、`architecture_design/`、`engineering_design/` 四个维度子目录
2. **Flat 模式**: 根目录下所有文件平铺，通过文件名关键词匹配维度（如文件名含 `prd` → `product_design`）

**Flat 模式的关键缺陷 (第 1062–1079 行):**

```python
def _detect_flat_dimensions(root: Path) -> dict[str, list[Path]]:
    mapping: dict[str, list[Path]] = {k: [] for k in DIMENSIONS}
    for file_path in sorted(root.iterdir()):   # ← 仅遍历根目录，不递归
        if not file_path.is_file():
            continue                            # ← 跳过所有子目录
        # ... 关键词匹配逻辑
```

**实际影响:**
- `docs/mvp-lite/` 使用按文档类型组织的子目录（`prds/`、`tech/`、`api/`、`testset/`、`ux-prototypes/`）
- Flat 模式不递归进入子目录，因此**一个文件也找不到**
- Structured 模式因缺少维度子目录而直接判定为无效

**建议修复:**

选项 A — 增加递归遍历:
```python
for file_path in sorted(root.rglob("*")):   # 递归遍历
    if not file_path.is_file():
        continue
```

选项 B — 支持自定义目录映射配置:
```yaml
# 在 ll.contract.yaml 或独立配置中支持
parser:
  layout: custom
  dimension_paths:
    product_design: ["prds", "ux-prototypes"]
    architecture_design: ["tech"]
    engineering_design: ["api", "testset"]
```

---

### 3.3 第三层: 完整性检查器硬编码 LEE-Lite 业务规则 (最严重)

**文件:** `cli/lib/v2/completeness.py` 第 342–411 行

**问题:** 当检测到 "substantive raw content"（文件内容 >200 字符）时，检查器执行一组**不可配置、不可关闭**的 LEE-Lite 专属业务规则：

```python
# cli/lib/v2/completeness.py 第 342–411 行 (节选)

if _has_substantive_raw and "session-feedback" not in combined_raw:
    missing_items.append({
        "severity": "ERROR",
        "reason": "API-P1-001: POST /v1/training-plan/session-feedback endpoint missing"
    })

if _has_substantive_raw and "pre-run-checkin" not in combined_raw:
    missing_items.append({
        "severity": "ERROR",
        "reason": "API-P1-002: POST /v1/decisions/pre-run-checkin endpoint missing"
    })

if _has_substantive_raw and "start-without-checkin" not in combined_raw:
    missing_items.append({
        "severity": "ERROR",
        "reason": "API-P1-002: POST /v1/decisions/start-without-checkin endpoint missing"
    })

if _has_substantive_raw and "card" not in ux_lower and "卡片" not in ux_lower:
    missing_items.append({
        "severity": "ERROR",
        "reason": "UI-P2-011: Core card specifications missing"
    })

if _has_substantive_raw and "acknowledge" not in combined_raw.lower():
    missing_items.append({
        "severity": "ERROR",
        "reason": "UI-P2-012: Acknowledge flow missing"
    })

if _has_substantive_raw and "input normalization" not in combined_raw.lower():
    missing_items.append({
        "severity": "ERROR",
        "reason": "UI-P2-013: Input Normalization spec missing"
    })

if _has_substantive_raw and "e2e" not in combined_raw.lower() and "playwright" not in combined_raw.lower():
    missing_items.append({
        "severity": "ERROR",
        "reason": "FRZ-P2-015: E2E test specifications missing"
    })
```

**实际影响:**
- 在 `ai-marathon-root-v2` 项目（一个 AI 马拉松项目管理工具）上运行时，
  这些检查全部失败，因为该项目不涉及：
  - `training-plan/session-feedback` 端点
  - `decisions/pre-run-checkin` 端点
  - `decisions/start-without-checkin` 端点
  - "card" / "卡片" UI 组件
  - "acknowledge" 流程
  - "input normalization" 规范
  - Playwright E2E 测试（项目使用不同测试策略）
- 这些 ERROR 级缺失项会导致 **FRZ 流程在 completeness 阶段被强制阻断**，无法进入后续步骤

**建议修复 (必须):**

将硬编码规则提取到外部配置文件，按项目加载：

```yaml
# completeness-rules.yaml (项目级配置)
rules:
  - id: API-P1-001
    severity: ERROR
    match_type: contains
    target: combined_raw
    patterns: ["session-feedback"]
    message: "POST /v1/training-plan/session-feedback endpoint missing"
    # 仅当 project_type == "lee-lite" 时启用
    enabled_for: ["lee-lite"]

  - id: UI-P2-011
    severity: ERROR
    match_type: any_contains
    target: ux_lower
    patterns: ["card", "卡片"]
    message: "Core card specifications missing"
    enabled_for: ["lee-lite"]
```

同时在 `frz_ingest.py` 入口增加 `--project-type` 参数，默认值为 `generic`
（禁用所有项目专属规则），仅在显式指定时加载对应规则集。

---

## 4. 当前状态与临时 workaround

| 层级 | 状态 | 临时方案 |
|------|------|----------|
| 路径解析 | 已修复 | 环境变量 `PYTHONPATH` |
| 文档解析 | 未修复 | 手动创建 `/tmp/m12-frz-input/` 并按维度重排文件 |
| 业务规则检查 | **未修复且不可绕过** | **无 — 必须修改源代码** |

由于第三层阻塞无法通过任何外部配置绕过，
`ai-marathon-root-v2` 项目的 M12 FRZ 工作流目前**只能完全手工执行**。

---

## 5. 修复优先级建议

| 优先级 | 事项 | 影响 |
|--------|------|------|
| P0 | 提取 `completeness.py` 硬编码规则到配置 | 阻断所有非 LEE-Lite 项目 |
| P1 | 修复 `parser.py` Flat 模式递归问题 | 影响使用子目录组织文档的项目 |
| P2 | 增加脚本启动日志 | 便于排查后续问题 |
| P3 | 路径解析改为配置驱动 | 降低部署耦合 |

---

## 6. 相关文件索引

- `~/.claude/skills/ll-v2-frz-ingest/src/frz_ingest.py` — 入口脚本，路径解析逻辑
- `~/git/LEE-Lite/cli/lib/v2/parser.py` — 文档解析器，第 1062–1079 行（Flat 模式）、第 1118–1166 行（`parse_design_package`）
- `~/git/LEE-Lite/cli/lib/v2/completeness.py` — 完整性检查器，第 342–411 行（硬编码规则）
- `~/.claude/skills/ll-v2-frz-ingest/ll.lifecycle.yaml` — 当前状态 `state: draft`， skill 未 ready

---

## 7. 验证建议

修复完成后，请按以下步骤验证跨项目兼容性：

1. 在一个**全新目录**中创建测试项目，目录结构如下：
   ```
   test-project/
   ├── prds/
   │   └── PRD-test.md
   ├── tech/
   │   └── TECH-test.md
   └── api/
       └── API-test.md
   ```
2. 运行 `python frz_ingest.py --input test-project --output test-output`
3. 确认：
   - [ ] 不报错退出
   - [ ] 输出目录中包含 FRZ 包文件
   - [ ] 不触发任何 LEE-Lite 专属缺失项 ERROR
   - [ ] `logs/frz-ingest.log` 存在且包含完整执行记录
