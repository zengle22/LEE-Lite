# Skill 方案：code-patrol（代码熵增巡检）v1.0-MVP

---
name: code-patrol
description: "定期对代码库进行自动化巡检，发现常见代码问题（风格漂移、架构腐化、安全漏洞、性能陷阱、重复代码等），生成结构化报告并推动修复，阻止代码熵增。"
argument-hint: "[--paths <dir1> [dir2...]] [--scope full|delta|staged|targeted] [--format markdown|json] [--max-files 500] [--max-file-size 1048576] [--since-days 7] [--output-dir .code-patrol] [--non-interactive] [--min-severity P0|P1|P2|P3] [--fix-mode report-only|suggest-fixes] [--baseline <path>] [--ruleset <path>] [--resume <patrol_id>] [--fail-on-p0p1]"
allowed-tools:
  - ReadFile
  - WriteFile
  - Shell
  - Grep
  - Glob
  - Task
---

## 1. 目的与范围

### 1.1 目的

`code-patrol` 是一个受治理的代码质量巡检 Skill，旨在：

1. **周期性扫描**代码库，捕获代码熵增的早期信号；
2. **结构化归类**发现的问题，按严重级别和影响范围分级；
3. **生成可执行报告**，为每次 Sprint 或迭代提供质量基线；
4. **输出修复证据**，供开发者和 Gate 决策消费，推动修复闭环。

> **治理约束**：本 Skill 仅产生 candidate、evidence 和 handoff proposal，不执行任何 Gate 审批/拒绝/block 操作，不直接修改源代码。所有修复动作须经人类或独立 Gate 确认。默认情况下，即使发现 P0/P1 问题，Skill 也返回退出码 0，由外部 Gate 独立决策是否阻断。（参见宪法 §4 Gate Ownership）

### 1.2 范围（v1.0-MVP）

- 支持对项目内任意目录或文件集合进行定向扫描；
- 默认覆盖：代码风格一致性、架构合规性、安全敏感模式、性能反模式、重复/死代码、文档与代码同步性；
- **v1.0 仅实现 L1（模式匹配）+ L3（统计聚合）引擎**，输出 Markdown/JSON 报告；
- 输出物包括：扫描报告、问题清单、修复建议、趋势对比（若存在历史数据）。

### 1.3 不适用场景

- **不替代编译器/静态分析工具**：如 ESLint、Pylint、SonarQube 等；`code-patrol` 是对这些工具结果的补充和聚合，而非替代。
- **不做运行时分析**：不执行性能剖析（Profiling）、不运行测试用例、不做内存泄漏检测。
- **不处理构建产物**：只扫描源代码和配置，不扫描 `node_modules/`、`venv/`、`.git/`、`__pycache__/`、`dist/` 等。
- **v1.0 不输出 SARIF**：SARIF 输出为 v1.1+ 规划特性。
- **v1.0 不执行自动修复**：仅生成报告与修复建议代码片段，不修改源代码。

---

## 2. 核心概念

### 2.1 代码熵增（Code Entropy）

指代码库在缺乏主动维护的情况下，因临时补丁、快速修复、人员更替等因素导致的结构性退化。表现为：

- 模块间耦合度上升、内聚度下降；
- 重复代码片段扩散；
- 命名规范漂移；
- 注释与实现不同步；
- 废弃 API / 死代码残留。

### 2.2 巡检维度（Patrol Dimensions）

| 维度 ID | 维度名称 | 检查内容 | 严重级别映射 | v1.0 引擎 |
|---------|---------|---------|-------------|----------|
| D01 | 风格一致性 | 命名规范、缩进、文件组织、导入顺序是否与项目约定一致 | P2-P3 | L1 + L3 |
| D02 | 架构合规性 | 是否违反分层/模块化设计？是否出现跨层调用、循环依赖？ | P0-P1 | L1 |
| D03 | 安全敏感模式 | 硬编码密钥、SQL 拼接、XSS 风险点、不安全的反序列化 | P0-P1 | L1 |
| D04 | 性能反模式 | N+1 查询、大数据量全量加载、同步阻塞 IO、内存泄漏模式 | P1-P2 | L1 |
| D05 | 重复与死代码 | 重复块（≥3 行，相似度≥80%）、未引用函数/变量、废弃装饰器 | P2-P3 | L3 |
| D06 | 文档同步性 | 函数 docstring 与参数签名不一致、README 示例过期、API 注释缺失 | P2-P3 | L1 |
| D07 | 依赖健康度 | 是否存在已弃用依赖、版本锁定冲突、许可证风险 | P1-P2 | L3 |
| D08 | 测试覆盖漂移 | 新增代码是否伴随测试？测试文件是否存在断言空洞？ | P1-P2 | L1 |

> **严重级别定义**：
> - **P0（阻塞）**：可能导致生产故障、安全漏洞、数据丢失，必须立即修复；
> - **P1（高风险）**：显著增加维护成本或引入隐蔽缺陷，应在当前迭代修复；
> - **P2（中风险）**：局部质量问题，可在后续迭代有计划地处理；
> - **P3（低风险）**：风格或美观问题，建议批量修复。

### 2.3 扫描模式

| 模式 | 枚举值 | 说明 | 触发时机 |
|------|--------|------|---------|
| `full` | `full` | 全量扫描整个代码库 | 每周/每迭代一次 |
| `delta` | `delta` | 仅扫描自上次扫描以来变更的文件 | 每次 PR/MR 时 |
| `staged` | `staged` | 扫描暂存区（git staged）文件 | 本地 pre-commit 前 |
| `targeted` | `targeted` | 扫描用户指定的路径或文件 | 按需 |

---

## 3. 执行流程

### 3.1 阶段 0：初始化与上下文收集

**输入解析**：

```
位置参数：无（全部使用命名参数）

命名参数：
  --paths <path> [path...]    扫描路径（默认当前目录）
  --scope full|delta|staged|targeted  扫描范围（默认 full）
  --format markdown|json      输出格式（默认 markdown）
  --max-files N               最大扫描文件数（默认 500）
  --max-file-size <bytes>     单文件大小上限（默认 1048576 = 1MB）
  --since-days N              仅扫描 N 天内修改过的文件（delta 模式）
  --output-dir <path>         输出目录（默认 .code-patrol）
  --baseline <path>           与上一次报告对比（可选）
  --ruleset <path>            自定义规则集 YAML（可选）
  --min-severity P0|P1|P2|P3  最小输出严重级别（默认 P3）
  --fix-mode report-only|suggest-fixes  修复模式（默认 report-only）
  --non-interactive           禁用交互提示，强制自动决策
  --resume <patrol_id>        恢复未完成的巡检（读取 patrol-state.json）
  --fail-on-p0p1              发现 P0/P1 时返回退出码 1（默认关闭）
```

**项目根目录判定**：

```
1. 若当前目录在 git 仓库中，项目根目录 = `git rev-parse --show-toplevel`
2. 否则，向上查找 pyproject.toml/package.json/go.mod/pom.xml 所在目录（最多向上 5 层）
3. 若仍无识别文件，项目根目录 = 当前工作目录
```

**环境探测**：

1. 检测项目类型（Python/Node/Go/Java 等），通过 `pyproject.toml`、`package.json`、`go.mod`、`pom.xml` 等；
   - **边界**：若未检测到任何已知配置文件，项目类型设为 `generic`，启用 language-agnostic 规则（如 D03 安全正则），输出 warning。
2. 读取项目已有的 lint/format 配置（如 `.eslintrc`、`.pre-commit-config.yaml`）；
3. 读取 `.gitignore` 和 `.projectignore` 以确定排除模式；
4. 收集 git 元数据（最近提交者、变更频率高的文件、近期重命名记录）；
   - **边界**：若当前目录不是 git 仓库或 git 命令不可用：
     - `staged` / `delta` 模式报错并提示改用 `full` 或 `targeted`，退出码 2；
     - issue 中 `author_git`/`commit_hash` 置为 `null`；
     - `full` / `targeted` 模式继续执行，跳过 git 元数据。

**输出目录初始化**：

```
patrol_id = {YYYYMMDD}-{HHMMSS}-{12位字母数字}
output_root = {output_dir}/{patrol_id}/
mkdir -p {output_root}/
```
- **边界**：若 mkdir 失败（磁盘满/权限不足），写入 stderr 错误详情，尝试回退到系统临时目录（如 `%TEMP%/code-patrol/{patrol_id}/`），并设置退出码为 2。
- **并发防碰撞**：patrol_id 使用 12 位随机字母数字（碰撞概率 < 1e-9），若目录已存在则重新生成 ID。

### 3.2 阶段 1：文件发现与过滤

**文件展开**：

```
1. 根据 --paths 和 --scope 展开文件列表
   - full：递归扫描 --paths 下所有文件
   - delta：执行 `git log --since="{since-days} days ago" --name-only --pretty=format: | sort -u` 获取变更文件
   - staged：执行 `git diff --cached --name-only` 获取暂存文件
   - targeted：仅扫描 --paths 显式指定的文件/目录
2. 应用排除规则：
   - 硬排除：node_modules/, venv/, .git/, __pycache__/, dist/, build/, .code-patrol/
   - 软排除：匹配 .gitignore 和 .projectignore 的条目
   - 大小排除：单文件 > max-file-size 的文本文件报警告并跳过
3. 文件数 > max-files → 行为分支：
   - 若 --non-interactive 或未检测到 TTY：自动按 git 最近修改时间排序取前 N（N=max-files），输出 warning
   - 若交互环境：提示用户确认或自动切换
4. 生成 manifest.json（见 5.4 Manifest Schema）
```

### 3.3 阶段 2：多维度扫描

**扫描引擎设计**：

| 层级 | 引擎 | 实现方式 | 覆盖维度 | v1.0 状态 |
|------|------|---------|---------|----------|
| L1 | 模式匹配引擎 | 基于 Grep/AST 的正则/树匹配 | D01 风格、D02 架构、D03 安全、D04 性能、D06 文档、D08 测试 | **已实现** |
| L2 | 语义分析引擎 | LLM Agent 做上下文感知分析 | D02 架构、D06 文档、D08 测试 | **[v1.1+]** |
| L3 | 统计聚合引擎 | Shell 命令 + 外部工具统计 | D01 风格、D05 重复、D07 依赖 | **已实现** |

**L1 模式匹配引擎（确定性扫描）**：

预定义规则库（`.code-patrol-config/ruleset.yaml`，见 4.1）。引擎执行逻辑：

```python
def run_l1(files, ruleset):
    issues = []
    for file in files:
        content = read(file)
        for rule in ruleset.rules:
            if rule.language != 'any' and file.lang != rule.language:
                continue
            for pattern in rule.patterns:
                matches = grep(content, pattern.value, multiline=pattern.multiline)
                for m in matches:
                    if any(re.search(ex, m.context) for ex in rule.exclude_patterns):
                        continue
                    issues.append(create_issue(file, m, rule, found_by='L1-pattern-matching'))
    return issues

def create_issue(file, match, rule, found_by):
    return {
        "id": f"{{patrol_id}}-{rule.id}-{{seq:04d}}",
        "rule_id": rule.id,
        "dimension": rule.dimension,
        "severity": rule.severity,
        "file": file.path,
        "line_start": match.line_start,
        "line_end": match.line_end,
        "column_start": match.column_start,
        "column_end": match.column_end,
        "message": rule.message,
        "evidence": match.context,
        "impact": rule.impact_template or infer_impact(rule.dimension, rule.severity),
        "fix_suggestion": rule.fix_template or None,
        "fix_snippet": rule.fix_snippet or None,
        "found_by": found_by,
        "confidence": 1.0 if found_by == 'L1-pattern-matching' else rule.confidence,
        "tags": rule.tags,
        "author_git": None,  # 阶段 3 填充
        "commit_hash": None  # 阶段 3 填充
    }
```

> **跨行正则**：Grep 调用需显式启用 multiline 模式（`-U` 或等效参数），或在规则中标注 `multiline: true`。

**L3 统计聚合引擎（确定性扫描）**：

```python
def run_l3(files, project_type):
    issues = []
    skipped_dimensions = []

    # D01 风格一致性（简单正则可覆盖的部分）
    for file in files:
        content = read(file)
        for match in re.finditer(r' +$', content, re.MULTILINE):
            line_number = content[:match.start()].count('\n') + 1
            issues.append(create_issue_from_l3(file, line_number, 'STYLE-001', 'trailing-whitespace'))

    # D05 重复代码
    try:
        scan_paths = ' '.join(files)
        jscpd_result = shell(f"jscpd --reporters json --output .tmp/jscpd.json --min-lines 3 --min-tokens 25 --threshold 80 {scan_paths}", timeout=300)
        duplicates = parse_jscpd_json('.tmp/jscpd.json')
        # 过滤仅保留用户指定范围内的重复块
        duplicates = [d for d in duplicates if all(f in files for f in d.files)]
        for dup in duplicates:
            issues.append(create_issue_from_l3(dup.files, dup.lines, 'DUP-001', 'duplicate-block'))
    except (ToolNotFound, Timeout):
        skipped_dimensions.append('D05')
        log_warning("jscpd 不可用或超时，D05 维度已跳过")

    # D05 死代码
    try:
        scan_paths = ' '.join(files)
        if project_type == 'python':
            vulture_result = shell(f"vulture --min-confidence 80 {scan_paths}", timeout=300)
            issues.extend(parse_vulture_output(vulture_result, files))
        elif project_type == 'typescript' or project_type == 'javascript':
            ts_prune_result = shell(f"ts-prune -p tsconfig.json", timeout=300)
            issues.extend(parse_ts_prune_output(ts_prune_result, files))
    except (ToolNotFound, Timeout):
        if 'D05' not in skipped_dimensions:
            skipped_dimensions.append('D05')
        log_warning("死代码检测工具不可用或超时")

    # D07 依赖健康度（按项目根目录运行，不限制文件范围）
    try:
        if project_type == 'python':
            audit_result = shell("pip-audit --format=json", timeout=300)
            issues.extend(parse_pip_audit_json(audit_result))
        elif project_type == 'node':
            audit_result = shell("npm audit --json", timeout=300)
            issues.extend(parse_npm_audit_json(audit_result))
    except (ToolNotFound, Timeout):
        skipped_dimensions.append('D07')
        log_warning("依赖审计工具不可用或超时，D07 维度已跳过")

    return issues, skipped_dimensions
```

> **工具输出解析示例**：
> - jscpd JSON：`duplications[].fragment` → evidence；`duplications[].files[].line` → line_start/line_end
> - vulture 文本：`file:line: unused function 'foo'` → 正则解析
> - pip-audit JSON：`dependencies[].vulns[].id` → rule_id；`summary` → message

> **v1.1+ L2 语义分析引擎规划**：详见附录 A《L2 语义分析引擎规格》。正文中仅保留核心约束：
> - 触发条件：L1 无法覆盖或需要上下文理解时
> - 降级策略：L2 失败后保留已完成结果，标记 `skipped_dimensions=["D02","D06","D08"]`，报告中显式告警

### 3.4 阶段 3：问题聚合与分级

**去重与合并**：

```
1. 相同文件、相同行范围、相同规则 ID → 去重保留一条
2. 跨层发现同一问题（如 L1 和 L3 都报告某函数无测试）→ 合并，severity 取最高
3. 关联问题分组（启发式规则）：
   - 同一文件 + 同一规则 ID + 同一作者 + 72h 时间窗口内 → 归为一组
   - 分组后输出 group_id，便于批量修复
```

**热点分析**：

```
1. 统计每个目录的问题密度（问题数/文件数）
2. 识别问题聚类：单一作者近期提交集中引入的问题 → 在报告中标注为热点
   - v1.0 仅做标注，不生成作者级通知（v1.2+ 规划）
```

**作者信息填充**：

```python
def enrich_git_metadata(issues, manifest):
    for issue in issues:
        file_entry = manifest.find(issue.file)
        if file_entry and file_entry.git_commit_hash:
            issue.commit_hash = file_entry.git_commit_hash
            issue.author_git = file_entry.git_author
        else:
            # 回退：按 issue 行号执行 git blame
            blame = shell(f"git blame -L {issue.line_start},{issue.line_start} {issue.file} --porcelain")
            issue.author_git = parse_git_author(blame)
            issue.commit_hash = parse_git_hash(blame)
```

**基线对比算法**：

```python
import hashlib

def compute_fingerprint(issue):
    # 按行提取内容，忽略行号，避免代码移动导致匹配失败
    lines = read(issue.file).splitlines()[issue.line_start-1:issue.line_end]
    normalized = '\n'.join(lines).strip()
    content_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    return f"{issue.rule_id}:{issue.file}:{content_hash}"

def compare_baseline(current_issues, baseline_issues):
    current_fps = {compute_fingerprint(i) for i in current_issues}
    baseline_fps = {compute_fingerprint(i) for i in baseline_issues}
    new_count = len(current_fps - baseline_fps)
    resolved_count = len(baseline_fps - current_fps)
    persistent_count = len(current_fps & baseline_fps)
    return new_count, resolved_count, persistent_count
```

### 3.5 阶段 4：报告生成

**质量分数计算**：

```
quality_score = max(0, 100 - sum(issue.weighted_penalty for issue in issues))

其中：
- P0 penalty = 20 × dimension_weight
- P1 penalty = 10 × dimension_weight
- P2 penalty = 4 × dimension_weight
- P3 penalty = 1 × dimension_weight

dimension_weights 见 4.1 规则集规范。

示例：某次扫描发现 D03(P0)×1 + D04(P1)×2，D03 权重 2.0，D04 权重 1.2
quality_score = 100 - (20×2.0 + 2×10×1.2) = 100 - (40 + 24) = 36
```

**报告结构**（Markdown 格式示例）：

```markdown
# 代码巡检报告 {patrol_id}

## 执行摘要
- 扫描范围：{paths}，共 {n} 个文件
- 发现问题：P0={n} P1={n} P2={n} P3={n}
- 质量分数：{quality_score}/100
- 与上次对比：新增 {n} / 修复 {n} / 遗留 {n}
- 建议修复优先级：立即处理 P0，本迭代处理 P1

## 热点地图
| 目录 | 问题密度 | 最严重级别 | 主要维度 |
|------|---------|-----------|---------|
| src/auth | 4.2 | P0 | D03 安全 |

## 详细问题清单
### P0 - 阻塞级
- [SEC-001] src/config.py:42 硬编码密钥...
  - 修复建议：使用 os.environ.get('API_KEY')

## 趋势数据（Markdown 表格）
| 日期 | P0 | P1 | P2 | P3 | 质量分数 |
|------|----|----|----|----|---------|
| ... | ... | ... | ... | ... | ... |
```

> **趋势图表**：v1.0 使用 Markdown 表格呈现趋势数据；v1.1+ 可引入图表库生成折线图（PNG/SVG）。默认展示最近 10 次巡检数据，可通过 `.code-patrol-config/config.yaml` 中 `trend_history: 10` 配置。

**机器可读格式**：

- JSON：包含完整结构化数据，供 CI 解析（见 5.2 Patrol Report Schema）。
- SARIF：v1.1+ 规划，届时将补充 OASIS SARIF v2.1 映射规范（ruleId→rule.id, level→severity, message→message, locations→file/line）。非标准字段（hotspots/trend/quality_score）将放入 `runs[0].properties.patrol` 中。

### 3.6 阶段 5：修复建议与证据输出

**修复模式（v1.0）**：

| 模式 | 说明 | CLI 参数 |
|------|------|---------|
| `report-only` | 仅生成报告，不输出可执行修复片段（默认） | `--fix-mode report-only` |
| `suggest-fixes` | 在报告中附加每个问题的建议修复代码片段 | `--fix-mode suggest-fixes` |

> **v1.2 规划**：`auto-fix-safe` 模式（生成 patch 文件，不自动写入源代码）。详见附录 C《自动修复模式规格》。

**安全约束**：

- 禁止对安全相关代码（D03）和架构调整（D02）生成自动修复；
- 所有修复建议附带 `confidence` 字段（0.0-1.0），P3 建议 confidence ≥ 0.95；
- 修复建议输出到 `suggested-fixes.json`，不直接修改源代码。

**与门禁集成（示例）**：

```yaml
# GitHub Actions 集成示例：Skill 只输出 evidence，Gate 做决策
code-patrol-report:
  - name: Run Code Patrol
    run: code-patrol --scope delta --format json --output-dir .code-patrol
  - name: Upload Evidence
    uses: actions/upload-artifact@v4
    with:
      name: patrol-report
      path: .code-patrol/*/report.json
# Gate 决策由独立工作流或人工审查完成，不在 Skill 中执行 exit 1
```

### 3.7 阶段 6：中断与恢复

**状态持久化**：

```python
# 每完成一个阶段后写入
checkpoint_state = {
    "patrol_id": patrol_id,
    "status": "scanning | aggregating | reporting | completed | failed",
    "current_phase": "L3-statistical-aggregation",
    "completed_phases": ["init", "discovery", "L1-pattern-matching"],
    "pending_files": ["src/large_module.py"],
    "output_dir": output_root,
    "last_updated": "2026-05-13T12:00:00Z"
}
write(f"{output_root}/patrol-state.json", checkpoint_state)
```

**恢复触发**：

- `--resume <patrol_id>`：读取 `{output_dir}/{patrol_id}/patrol-state.json`
- 若 `status != completed`，从 `current_phase` 恢复，`pending_files` 参与当前阶段，`completed_phases` 跳过
- 若 patrol-state.json 损坏或不存在，报错退出码 2

**状态转换矩阵**：

| 当前状态 | 合法下一状态 | 触发条件 |
|---------|-------------|---------|
| scanning | aggregating | 完成 L1+L3 扫描 |
| scanning | failed | 扫描阶段超时或异常 |
| aggregating | reporting | 完成问题聚合与分级 |
| aggregating | failed | 聚合阶段异常 |
| reporting | completed | 报告写入成功 |
| reporting | failed | 报告生成异常 |

---

## 4. 规则集（Ruleset）规范

### 4.1 默认规则集结构

```yaml
ruleset_version: "1.0"
description: "默认代码巡检规则集（v1.0-MVP）"

# 排除模式（项目级）
global_excludes:
  - "**/migrations/**"
  - "**/generated/**"
  - "**/*.min.js"

# 规则定义
rules:
  - id: SEC-001
    dimension: D03
    severity: P0
    name: hardcoded-secret
    description: "检测硬编码的密码、密钥、Token"
    language: any
    patterns:
      - type: regex
        value: '(?i)(password|secret|token|api_key)\s*=\s*["\'][^"\']{8,}["\']'
        multiline: false
    exclude_patterns:
      - 'example|test|mock|dummy|placeholder'
    tags:
      - security
      - credentials
    message: "检测到可能的硬编码密钥，请使用环境变量或密钥管理服务"
    impact_template: "若代码泄露，生产环境密钥将暴露，可能导致未授权访问"
    evidence_required: true

  - id: ARCH-001
    dimension: D02
    severity: P1
    name: cross-layer-import
    description: "检测跨层调用（如 Presentation 层直接调用 DAO）"
    language: any
    patterns:
      - type: regex
        value: 'from\.\.dao|from\.\.repository'
        multiline: false
    tags:
      - architecture
    message: "检测到可能的跨层导入，请通过 Service 层间接调用"
    impact_template: "跨层调用破坏架构分层，导致模块耦合度上升，难以维护和测试"
    evidence_required: true

  - id: PERF-001
    dimension: D04
    severity: P1
    name: sync-io-in-async
    description: "异步函数中使用同步 IO"
    language: python
    patterns:
      - type: regex
        value: 'async def .*:\n.*open\('
        multiline: true
    tags:
      - performance
    message: "异步函数中使用了同步文件 IO，考虑使用 aiofiles"
    impact_template: "同步 IO 阻塞事件循环，降低并发吞吐，可能导致超时"
    evidence_required: true

  - id: DOC-001
    dimension: D06
    severity: P2
    name: docstring-param-mismatch
    description: "函数 docstring 参数与实际签名不一致"
    language: python
    patterns:
      - type: regex
        value: 'def .*\(.*\):\n\s+"""[^"]*:param'
        multiline: true
    tags:
      - documentation
    message: "请检查 docstring 参数列表是否与函数签名一致"
    impact_template: "文档与实现不同步，增加新开发者理解成本"
    evidence_required: true

  - id: TEST-001
    dimension: D08
    severity: P2
    name: empty-test-function
    description: "测试函数体中无断言"
    language: any
    patterns:
      - type: regex
        value: 'def test_.*\(\):\n\s+pass'
        multiline: true
    tags:
      - testing
    message: "测试函数缺少断言，请添加有效的测试逻辑"
    impact_template: "空测试产生虚假安全感，降低实际测试覆盖率"
    evidence_required: true

  - id: STYLE-001
    dimension: D01
    severity: P3
    name: trailing-whitespace
    description: "行尾存在多余空格"
    language: any
    patterns:
      - type: regex
        value: ' +$'
        multiline: false
    tags:
      - style
    message: "删除行尾多余空格"
    impact_template: "行尾空格增加 diff 噪音，部分编辑器会自动删除导致无关变更"
    evidence_required: true

# 维度权重（用于计算质量分数）
dimension_weights:
  D01: 0.8
  D02: 1.5
  D03: 2.0
  D04: 1.2
  D05: 1.0
  D06: 0.9
  D07: 1.1
  D08: 1.3
```

> **D05 重复代码**和**D07 依赖健康度**的具体规则由 L3 引擎通过外部工具（jscpd、pip-audit 等）产生，不通过 YAML 规则集定义。

### 4.2 自定义规则集加载

- 项目根目录下 `.code-patrol-config/ruleset.yaml` 自动加载；
- `--ruleset` 参数显式指定；
- 自定义规则与默认规则合并，同名规则自定义优先；
- **错误处理**：ruleset YAML 解析失败 → 输出 stderr 错误详情，退出码 2；baseline 格式不匹配 → 跳过对比并输出 warning。

---

## 5. 数据结构

### 5.1 Issue Schema（单条问题）

```json
{
  "id": "{patrol_id}-{rule_id}-{seq:04d}",
  "rule_id": "SEC-001",
  "dimension": "D03",
  "severity": "P0",
  "file": "src/config.py",
  "line_start": 42,
  "line_end": 45,
  "column_start": 8,
  "column_end": 32,
  "message": "检测到可能的硬编码密钥",
  "evidence": "API_KEY = 'sk-live-abc123xyz'",
  "impact": "若代码泄露，生产环境密钥将暴露，可能导致未授权访问",
  "fix_suggestion": "使用 os.environ.get('API_KEY') 替代硬编码",
  "fix_snippet": "API_KEY = os.environ.get('API_KEY')",
  "found_by": "L1-pattern-matching",
  "confidence": 0.95,
  "tags": ["security", "credentials"],
  "author_git": "alice@example.com",
  "commit_hash": "a1b2c3d4"
}
```

> **字段填充规则**：
> - `author_git` / `commit_hash`：由阶段 3 从 manifest.git_author / manifest.git_commit_hash 填充；若 manifest 无数据，则按 issue 行号执行 `git blame` 提取；非 git 环境填充 `null`。
> - `found_by`：严格使用引擎官方标识：`L1-pattern-matching`、`L2-semantic-analysis`（v1.1+）、`L3-statistical-aggregation`。
> - `confidence`：L1 规则匹配为 1.0（确定）；L3 工具输出按其置信度；L2（v1.1+）由 LLM 自评。
> - `impact`：优先取规则集 `impact_template`；若规则集未定义，由引擎根据 dimension 和 severity 推断默认值；仍无则填充 `null`。

### 5.2 Patrol Report Schema

```json
{
  "patrol_id": "20260513-120000-a1b2c3d4e5f6",
  "started_at": "2026-05-13T12:00:00Z",
  "completed_at": "2026-05-13T12:05:00Z",
  "config": {
    "paths": ["src/"],
    "scope": "full",
    "format": "markdown",
    "max_files": 500,
    "max_file_size": 1048576,
    "min_severity": "P3",
    "fix_mode": "report-only",
    "since_days": null,
    "ruleset": null,
    "baseline": null,
    "non_interactive": false,
    "resume": null,
    "fail_on_p0p1": false
  },
  "summary": {
    "total_files_scanned": 234,
    "total_issues": 45,
    "severity_breakdown": { "P0": 2, "P1": 8, "P2": 20, "P3": 15 },
    "dimension_breakdown": { "D01": 5, "D02": 3, "D03": 2, "D04": 8, "D05": 10, "D06": 4, "D07": 6, "D08": 7 },
    "skipped_dimensions": [],
    "quality_score": 36
  },
  "hotspots": [
    { "directory": "src/auth", "issue_density": 4.2, "max_severity": "P0" }
  ],
  "issues": [],
  "baseline_comparison": {
    "previous_patrol_id": "20260506-120000-c3d4e5f6a7b8",
    "new_issues": 12,
    "resolved_issues": 8,
    "persistent_issues": 25
  },
  "trend": {
    "history_length": 10,
    "direction": "improving",
    "quality_score": 36
  }
}
```

### 5.3 Patrol State Schema（用于恢复）

```json
{
  "patrol_id": "20260513-120000-a1b2c3d4e5f6",
  "status": "scanning",
  "current_phase": "L3-statistical-aggregation",
  "completed_phases": ["init", "discovery", "L1-pattern-matching"],
  "pending_files": ["src/large_module.py"],
  "output_dir": ".code-patrol/20260513-120000-a1b2c3d4e5f6/",
  "last_updated": "2026-05-13T12:03:00Z"
}
```

> 状态枚举：`scanning | aggregating | reporting | completed | failed`
> 状态转换矩阵见 3.7 阶段 6。

### 5.4 Manifest Schema（扫描文件清单）

```json
{
  "patrol_id": "20260513-120000-a1b2c3d4e5f6",
  "generated_at": "2026-05-13T12:01:00Z",
  "files": [
    {
      "path": "src/config.py",
      "language": "python",
      "size_bytes": 2048,
      "last_modified": "2026-05-13T10:00:00Z",
      "git_commit_hash": "a1b2c3d4",
      "git_author": "alice@example.com"
    }
  ],
  "excluded_count": 45,
  "excluded_reasons": { "hard_exclude": 30, "soft_exclude": 10, "size_exclude": 5 }
}
```

---

## 6. 性能与资源约束

### 6.1 文件数限制

- 默认 max-files = 500；
- 超过 500 时，优先扫描最近修改的文件（由 git log 排序）；
- 全量扫描 > 2000 文件时，建议分片并行（按目录分片）。

### 6.2 Token 预算（L2 v1.1+）

- L2 语义分析按文件计费；
- 单文件预算 ≤ 4000 tokens（输入+输出）；
- 总预算超过阈值时，仅对热点文件启用 L2，其余用 L1+L3；
- **热点判定**：使用阶段 0 收集的 git 变更频率 + 阶段 2 L1 预扫描的 P0/P1 问题数综合排序；
- 详细预算控制与超限时调度策略见附录 A。

### 6.3 超时策略

| 阶段 | 超时 | 失败行为 |
|------|------|---------|
| 阶段 0 初始化 | 30s | 退出码 2，输出错误详情 |
| 阶段 1 文件发现 | 2 min | 返回已发现的部分文件列表，告警 |
| L1 模式匹配 | 5 min | 跳过剩余文件，记录 timeout |
| L3 统计聚合 | 5 min | 跳过未完成的工具，记录 timeout，标记 skipped_dimensions |
| L2 LLM 分析（v1.1+）| 10 min/批次 | 重试 1 次，仍失败则标记 skipped_dimensions=["D02","D06","D08"]，保留已完成结果 |
| 阶段 3 聚合 | 2 min | 使用简化聚合（跳过关联分组）|
| 阶段 4 报告生成 | 2 min | 使用简化模板 |
| 阶段 5 修复建议 | 1 min | 跳过修复建议生成 |

---

## 7. 与项目治理体系的集成

### 7.1 SSOT 对齐

- 项目架构约定应来源于 `ssot/governance/` 下的 ADR 文档；
- `code-patrol` 在执行时，应通过 `ssot/governance/maps/` 中的路由映射定位最小相关架构约束，遵循宪法 **Progressive Disclosure** 原则（Batch 1-2 渐进加载）；
- 若发现代码与冻结的架构约定冲突，应生成架构评审请求（Architecture Review Request），**不套用 Patch Reflow**（Patch Reflow 仅适用于 UI/UX 体验变更，参见宪法 §6）。

### 7.2 证据与审计

- 每次扫描的所有原始输出（manifest、各引擎结果、LLM 调用记录 v1.1+）写入 `{output_root}/raw/`；
- 扫描结果作为 **Supervision Evidence** 存入项目证据目录；
- **可选**：最终报告可经过独立 Verifier 确认（检查 P0 证据是否充分），Verifier 规格：
  - 输入：report.json + raw/ 目录
  - 输出：verdict.json `{ "passed": true/false, "reason": "..." }`
  - 触发：由外部流程调用，非 Skill 内部强制阻塞

---

## 8. 反模式与预防机制

| 反模式 | 预防机制 |
|--------|---------|
| 误报风暴（大量 P3 淹没 P0） | 默认输出按严重级别过滤，P3 折叠；提供 `--min-severity` 参数 |
| 规则漂移（自定义规则与默认冲突） | 规则合并时显式记录 override 关系；版本化 ruleset |
| 扫描盲区（新文件类型无规则） | 未知扩展名报警告，提示用户补充规则或加入排除列表 |
| 修复回退（自动修复引入新问题） | v1.0 不执行自动修复；v1.2 仅生成 patch 文件，须经 Gate 审批 |
| 基线污染（历史问题计入新扫描） | 基线对比仅统计新增/修复；遗留问题单独标记 |
| L2 降级静默丢失维度 | 降级后显式写入 skipped_dimensions，报告中告警 |
| CI 交互阻塞 | `--non-interactive` 参数 + TTY 检测，无交互时自动降级 |

---

## 9. 输出目录结构

```
.code-patrol-config/              ← canonical 配置（应纳入版本控制）
├── ruleset.yaml                  # 项目级规则集
├── config.yaml                   # 项目级配置（排除模式、默认参数）
└── schedule.yaml                 # 调度配置（可选）

.code-patrol/                     ← 运行时产物（不纳入版本控制）
└── 20260513-120000-a1b2c3d4e5f6/  # 单次巡检产物
    ├── manifest.json             # 扫描文件清单
    ├── patrol-state.json         # 执行状态（支持恢复）
    ├── raw/
    │   ├── L1-results.json       # 模式匹配原始结果
    │   ├── L3-results.json       # 统计聚合原始结果
    │   └── L2-results/           # LLM 分析原始结果（v1.1+，见附录 A）
    ├── report.json               # 机器可读完整报告
    ├── report.md                 # 人类可读报告
    ├── hotspots.json             # 热点分析
    ├── baseline-diff.json        # 与基线对比（如提供基线）
    └── suggested-fixes.json      # 修复建议（suggest-fixes 模式）
```

---

## 10. 退出码定义

| 退出码 | 含义 | 场景 |
|--------|------|------|
| 0 | 成功完成 | 扫描正常结束（默认，无论是否存在 P0/P1） |
| 1 | 成功完成，发现 P0/P1 问题 | 仅当启用 `--fail-on-p0p1` 时返回 |
| 2 | 系统错误 | 参数无效、ruleset 解析失败、mkdir 失败、认证失败、git 缺失时 delta/staged 被使用等 |
| 3 | 部分维度被跳过 | 扫描完成，但部分维度因超时或引擎失败被跳过（skipped_dimensions 非空）|

---

## 11. 命令示例

```bash
# 全量扫描，输出 Markdown
code-patrol --paths src/ tests/ --scope full --format markdown

# 增量扫描，与基线对比
code-patrol --paths src/ --scope delta --since-days 7 --baseline .code-patrol/20260506-120000-c3d4e5f6a7b8/report.json

# 仅报告 P0/P1，JSON 格式供 CI 解析
code-patrol --paths src/ --min-severity P1 --format json --non-interactive

# 对暂存文件快速扫描
code-patrol --scope staged --max-files 50

# 使用自定义规则集
code-patrol --paths src/ --ruleset .code-patrol-config/my-rules.yaml

# 恢复未完成的巡检
code-patrol --resume 20260513-120000-a1b2c3d4e5f6

# 启用 suggest-fixes 模式
code-patrol --paths src/ --fix-mode suggest-fixes

# CI 中启用 P0/P1 失败码（由外部 Gate 决定是否阻断）
code-patrol --paths src/ --non-interactive --fail-on-p0p1
```

---

## 12. 验收标准（AC）

| # | 验收标准 | 验证方式 |
|---|---------|---------|
| AC-01 | 给定包含硬编码密钥的 Python 文件，code-patrol 应在 30 秒内产出至少 1 条 P0 issue（rule_id=SEC-001） | pytest 端到端测试 |
| AC-02 | 给定空目录，code-patrol 应产出空报告（summary.total_issues=0）且退出码为 0 | pytest 端到端测试 |
| AC-03 | 给定 600 个文件的目录（max-files=500），--non-interactive 模式下应自动取最近修改的 500 个文件，不阻塞 | pytest 模拟测试 |
| AC-04 | 给定损坏的 ruleset YAML，code-patrol 应以退出码 2 报错并输出明确错误信息 | pytest 异常测试 |
| AC-05 | 给定非 git 目录，code-patrol 应完成扫描（scope=full），author_git 字段为 null，不崩溃 | pytest 边界测试 |
| AC-06 | 两次扫描同一文件且内容不变（仅移动行号），基线对比应判定为 persistent，而非 new | pytest 指纹测试 |
| AC-07 | 给定未安装 jscpd 的环境，code-patrol 应完成扫描，skipped_dimensions 包含 D05，退出码为 3 | pytest 降级测试 |

---

## 13. 后续演进路线

| 版本 | 特性 |
|------|------|
| v1.0 (MVP) | L1+L3 引擎、Markdown/JSON 报告、基线对比、热点地图（文本）、修复建议 |
| v1.1 | 引入 L2 LLM 语义分析、SARIF 输出、趋势折线图（PNG/SVG） |
| v1.2 | auto-fix-safe 模式（生成 patch 文件，不自动写入）、作者级反馈通知 |
| v2.0 | 跨仓库趋势聚合、与 SonarQube/Snyk 结果融合、质量门禁集成 |

---

*方案版本：v1.0-MVP*
*编写日期：2026-05-13*
*治理状态：评审中*
