# Journey Structural Spec

- product_ref: PRD-001
- product_name: 跑步大师 / 无伤 PB AI 教练
- source_ref: E:\projects\ai-marathon-coach-v2\docs\prd\PRD-001-无伤PB-AI教练-MVP.md
- ui_shell_source_ref: skills/ll-dev-feat-to-proto/resources/ui-shell/default-ui-shell-spec.md
- note: Example draft aligned to the fixed running-coach shell candidate

## 1. Journey Main Chain

- `Setup Wizard` -> `Today Home` -> `Pre-run Decision` -> `Adjusted Training / Execute` -> `Post-run Feedback` -> `Today Home`
- Side entry: `Plan Review` can be entered from `Today Home` or `Pre-run Decision`, but it does not replace the main daily loop.
- `Today Home` is the anchor surface. Daily navigation should always be able to return to it.
- 首启建档：目标赛事、当前基线、训练背景、伤病史、每周可训练时间。
- 今日主屏：今天练什么、为什么这样练、当前风险是否抬头。
- 跑前检查：把睡眠、疲劳、疼痛、压力转成今日训练建议。
- 训练执行/调整：原计划执行、降级执行、替换训练、休息恢复四选一。
- 训练后反馈：完成情况、RPE、疲劳、疼痛、次日建议。
- 次日回流：把前一次反馈带回 `Today Home`，更新今日状态和推荐。

## 2. Page Map

- `Setup Wizard`: family=`setup_wizard`, container=`page`, goal=`完成最小可信建档并激活首个周期`
- `Today Home`: family=`today_home`, container=`page`, goal=`回答今天该怎么练以及为什么`
- `Pre-run Decision`: family=`pre_run_decision`, container=`page`, goal=`把当日状态转成唯一主建议`
- `Risk Detail`: family=`pre_run_decision`, container=`bottom_sheet`, goal=`展开疼痛、疲劳、负荷过快、恢复不足等风险原因`
- `Plan Review`: family=`plan_review`, container=`page`, goal=`查看周期结构、关键训练和赛前赛后上下文`
- `Post-run Feedback`: family=`post_run_feedback`, container=`bottom_sheet_or_page`, goal=`快速回收训练完成与体感反馈`
- `Warning / Sync Lag`: family=`today_home`, container=`inline_banner`, goal=`提示非阻断风险或同步延迟`

## 3. Decision Points

- 建档未完成前，不进入 `Today Home`，必须先拿到最小训练基线。
- 今日是否按原计划执行，先看疲劳、疼痛、睡眠、压力，再看 PB 目标。
- 一旦风险升高，`injury-first` 优先于 `PB-second`，不允许继续默认乐观路径。
- 当日建议只能有一个主结论：`原计划` / `降级` / `替换` / `休息`。
- 训练后反馈必须影响次日负荷，而不是只记录是否完成。
- 赛前减量和赛后恢复属于正常决策链，不视为异常路径。

## 4. CTA Hierarchy

- `Setup Wizard`: primary=`Activate cycle` | secondary=`Back`, `Skip`
- `Today Home`: primary=`Start pre-run check` | secondary=`View plan`, `Open risk detail`
- `Pre-run Decision`: primary=`Accept recommendation` | secondary=`Use easier option`, `Reset`
- Elevated risk: primary CTA downgrades to `Switch to easier session` or `Take recovery`, and must visually outrank the original workout path.
- `Plan Review`: primary=`Back to home` or `Pin this week` depending on context, but it must remain secondary to the daily decision loop.
- `Post-run Feedback`: primary=`Save review` | secondary=`Skip details`

## 5. Container Hints

- Use `page` for `Setup Wizard`, `Today Home`, full `Pre-run Decision`, full `Plan Review`, and expanded `Post-run Feedback`.
- Use `bottom_sheet` for risk reason detail, fatigue detail, alternative workout choices, and quick post-run capture.
- Use `inline_banner` for non-blocking warnings such as mild risk increase or sync lag.
- Use `modal` only for reset, override confirmation, or explicit blocking acknowledgement.
- Keep `Today Home` as the default return container for every daily path.

## 6. Error / Degraded / Retry Paths

- `blocked`: stop this run, route to recovery guidance, downgrade path, or coach review.
- `degraded`: continue with reduced volume, lower intensity, or substituted session; the shell must explain what changed and why.
- `retry`: allow re-submission of readiness inputs or missing fields without changing the core journey family.
- Persistent pain, poor recovery, or rapid load increase should trigger downgrade instead of optimistic continuation.
- `Warning / Sync Lag` stays non-blocking unless the missing data invalidates the readiness decision.
- Race taper and post-race recovery are expected branches, not defects.

## 7. Open Questions / Frozen Assumptions

- Frozen assumption: MVP is mobile-first and uses the fixed shell families `setup_wizard / today_home / pre_run_decision / plan_review / post_run_feedback`.
- Frozen assumption: P0 mainly depends on manual input rather than watch sync or automated biometrics.
- Frozen assumption: `injury-first` always outranks `PB-second`; elevated risk must downgrade the dominant CTA.
- Open question: `Post-run Feedback` should default to `bottom_sheet` or `page` for long-form race-day reviews.
- Open question: `Plan Review` needs a dedicated race context subsection for taper and post-race recovery, or whether that should stay feature-local.
