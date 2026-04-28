# Phase 21: PROTO 相关缺陷修复 - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

## Phase Boundary

修复 ll-dev-feat-to-proto 技能的两个关键缺陷：
1. FIX-P1-01: 低保真问题 - 菜单遮罩默认遮挡主内容、页面内容泛化占位、组件呈现不真实
2. FIX-P1-02: 旅程闭环拆分问题 - 6个 FEAT 不应拆成孤立页面，应保持旅程连贯性，共享 surface（wizard/hub + sheets）

## Implementation Decisions

### 缺陷分析

**FIX-P1-01: 低保真问题**

通过查看模板代码发现：
- SRC002 模板的 sheet 已经默认有 `hidden` 属性（index.html:60-61）
- CSS 中已定义 `.sheet[hidden] { display: none; }`
- 问题可能在于：某些场景下 hidden 属性被移除，或初始状态未正确设置

页面内容泛化问题：
- 需要检查模板中是否有占位文本（"Lorem ipsum"、"占位"、"TODO" 等）
- 需要确保模板使用真实的界面内容和信息密度

**FIX-P1-02: 旅程闭环拆分问题**

通过查看 feat_to_proto.py 发现：
- 代码已支持 journey_surface_inventory 和 journey_main_path（第478-492行）
- 问题可能在于：当多个 FEAT 属于同一旅程时，没有正确共享 surface
- 需要确保：旅程保持连贯性，使用 wizard/hub + sheets 模式而非独立页面

### 修复策略

1. **FIX-P1-01 修复步骤**：
   - 检查并确保所有 overlay（sheet、modal、drawer）默认隐藏
   - 清理模板中的占位文本，使用真实内容
   - 增强 placeholder lint 检查，降低允许的占位符数量

2. **FIX-P1-02 修复步骤**：
   - 改进 journey structural spec 生成逻辑，确保多 FEAT 旅程保持连贯
   - 确保 surface sharing 正确工作（wizard/hub + sheets 模式）
   - 验证 route map 和 reachability 在共享 surface 模式下正常

### 现有代码参考

- `skills/ll-dev-feat-to-proto/scripts/feat_to_proto.py` - 主要逻辑
- `skills/ll-dev-feat-to-proto/resources/templates/src002-journey-hifi/` - SRC002 模板
- `skills/ll-dev-feat-to-proto/resources/templates/generic-hifi/` - 通用模板

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 现有技能基础设施

- `skills/ll-dev-feat-to-proto/scripts/feat_to_proto.py` - 主技能脚本
- `skills/ll-dev-feat-to-proto/resources/templates/` - 模板目录

### 需求定义

- `.planning/REQUIREMENTS.md` - FIX-P1-01, FIX-P1-02
- `.planning/ROADMAP.md` - Phase 21 goal, success criteria

### 代码约定

- `.planning/codebase/CONVENTIONS.md` - 代码风格、类型标注、错误处理模式

## Existing Code Insights

### Reusable Assets

- `skills/ll-dev-feat-to-proto/scripts/feat_to_proto.py` - 已有的 journey surface 处理逻辑（第478-492行）
- `skills/ll-dev-feat-to-proto/resources/templates/src002-journey-hifi/prototype/` - SRC002 模板参考
- `_check_initial_view_integrity()` 函数（第568-584行）- 初始视图完整性检查

### Established Patterns

- frozen dataclass 用于 DTO
- CommandError + ensure() 预条件检查
- pytest fixture 测试模式

### Integration Points

- SRC002 模板的 sheet 默认 hidden 状态
- journey_surface_inventory 和 journey_main_path 处理
- route map 和 reachability 检查

## Specific Ideas

- "确保所有 overlay（sheet、modal、drawer）在 HTML 中默认有 hidden 属性"
- "清理模板中的占位文本，使用真实的应用内容"
- "改进多 FEAT 旅程的 surface 共享逻辑，保持 wizard/hub + sheets 模式"
- "降低 placeholder lint 的允许阈值，从 10 个减少到 3 个"

## Deferred Ideas

- 重构整个模板系统 - 当前阶段只修复缺陷，不做大型重构
- 添加新的模板类型 - 当前只修复现有模板的问题

---

*Phase: 21-proto-defect-fix*
*Context gathered: 2026-04-27*
