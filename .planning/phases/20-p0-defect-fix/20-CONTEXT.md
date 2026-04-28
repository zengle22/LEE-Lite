# Phase 20: P0 缺陷紧急修复 - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

为 v2.2.1 构建轻量 SSOT 语义漂移扫描器，聚焦最明确的两个检测场景：
1. Overlay 词汇反客为主（governance/gate/handoff 等被提升为主要对象）
2. API authority 重复定义

扫描器采用 CLI 工具形式，CI 自动运行（非阻断，仅告警），不修改现有的 freeze-guard 或 gate 流程。不做 FEAT 分解、surface-map 所有权、TECH/IMPL 语义匹配等更复杂的检测（范围控制，保持简单稳定）。
</domain>

<decisions>
## Implementation Decisions

### 检测范围控制
- **D-20-01:** 初始仅实现 2 类检测。
  - 检测 1: Overlay 反客为主（EPIC/FEAT 的 primary object 包含 governance/gate/handoff/formal/registry/validation/audit/bypass/settlement 等词汇）
  - 检测 2: API authority 重复（多个 API-*.md 文件中声明相同的 endpoint/path）
- **D-20-02:** 暂不实现的检测。
  - FEAT 分解按能力边界 vs UI 表面
  - Surface-map 所有权漂移
  - TECH/IMPL 语义与仓库匹配
  - Legacy src/ 违规增长

### 实现架构
- **D-20-03:** 新建 `cli/lib/semantic_drift_scanner.py`。
  - 复用现有 `enum_guard.py` 和 `governance_validator.py` 的 CLI 模式
  - 纯库模块 + CLI 入口，独立可测试
  - 不依赖 LLM，纯规则/关键词匹配（稳定、可预测）
- **D-20-04:** 数据结构采用 frozen dataclass。
  - `ViolationType` enum: `OVERLAY_ELEVATION`, `API_DUPLICATE`
  - `Violation` dataclass: `type`, `file_path`, `detail`, `evidence`
  - `ScanResult` dataclass: `total_violations`, `blocker_count`, `warning_count`, `violations`

### 集成策略
- **D-20-05:** CI 集成方式为非阻断告警。
  - 在 CI 中新增独立 job 运行 `python -m cli.lib.semantic_drift_scanner --ssot-dir ./ssot --output json`
  - 仅报告，不阻断 pipeline（先观察效果再决定是否强化）
  - 输出同时支持 human-readable 和 JSON 两种格式
- **D-20-06:** 暂不集成到 freeze-guard。
  - 不修改现有的 gate 或 freeze 流程
  - 保持现有技能行为不变，降低风险

### 测试策略
- **D-20-07:** 单元测试覆盖检测逻辑。
  - Overlay 检测的正例/反例
  - API duplicate 检测的正例/反例
  - CLI 入口的 integration 测试
  - 参考 `test_enum_guard.py` 和 `test_governance_validator.py` 的模式

### 优先级
- **D-20-08:** 交付顺序：核心扫描逻辑 → CLI → 测试 → CI 集成。
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 现有治理验证基础设施
- `cli/lib/enum_guard.py` — CLI 模式、frozen dataclass、violation 输出模式
- `cli/lib/governance_validator.py` — 文件扫描、YAML 解析、验证模式
- `cli/lib/drift_detector.py` — 现有漂移检测的模式（锚点级，参考 API 设计）

### 现有 CLI 模式
- `cli/lib/enum_guard.py` 的 `main()` 函数 — `--object` / `--check` / `--list-types` 模式
- `cli/lib/governance_validator.py` 的 `validate_file()` 函数 — 文件加载、YAML 解析

### 需求定义
- `.planning/REQUIREMENTS.md` — FIX-P0-01, FIX-P0-02
- `.planning/ROADMAP.md` — Phase 20 goal、success criteria

### 代码约定
- `.planning/codebase/CONVENTIONS.md` — 代码风格、类型标注、错误处理模式
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli/lib/enum_guard.py` — frozen dataclass violation 模式、CLI 入口模式
- `cli/lib/governance_validator.py` — 文件扫描、YAML 加载、批量验证
- `cli/lib/errors.py` — CommandError + ensure() 预条件检查
- `cli/lib/fs.py` — 文件操作工具（ensure_parent, load_json, canonical_path）

### Established Patterns
- 技能脚本子命令架构：build_parser() → add_subparsers() → command_map 分发 → main()
- 错误处理：CommandError with status_code + ensure() 预条件检查
- 类型标注：from __future__ import annotations，所有函数签名带类型注解
- 不可变数据：@dataclass(frozen=True) 用于 DTO
- 测试风格：fixture-based 单元测试

### Integration Points
- CI 配置（待查找）— 集成点
- SSOT 目录结构 `ssot/` — 扫描目标：`ssot/epic/`, `ssot/feat/`, `ssot/api/`
</code_context>

<specifics>
## Specific Ideas

- "复用 enum_guard.py 和 governance_validator.py 的模式，不要重新发明 CLI 框架"
- "纯规则/关键词匹配，不使用 LLM — 保持简单、稳定、可预测"
- "先只做两个检测，验证效果后再考虑扩展"
- "CI 中先以非阻断方式运行，观察效果再决定是否强化"
</specifics>

<deferred>
## Deferred Ideas

- FEAT 分解按能力边界检测 — 需要更复杂的启发式，暂不实现
- Surface-map 所有权漂移检测 — 需要解析 surface-map 格式，暂不实现
- TECH/IMPL 语义匹配检测 — 需要与仓库代码做 cross-reference，暂不实现
- Freeze-guard 集成 — 现有流程稳定，暂不修改
</deferred>

---

*Phase: 20-p0-defect-fix*
*Context gathered: 2026-04-27*
