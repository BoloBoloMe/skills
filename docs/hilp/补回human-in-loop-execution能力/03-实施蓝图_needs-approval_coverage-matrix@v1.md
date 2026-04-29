asset_id: hilp-execution-capability-restoration-coverage-matrix
artifact_name: stage-4-5/coverage-matrix
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: human-in-loop-planning
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批

# 覆盖矩阵：补回 human-in-loop-execution 执行能力

## 所属主蓝图

- `stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`

## 覆盖矩阵

| 设计决策 / 能力承诺 | 改动切片 | 子蓝图 | 验证项 | 风险检查点 |
|---|---|---|---|---|
| 保留 HILP 执行边界，不恢复被裁剪入口 | entry-routing | `blueprint-slice-entry-routing@v1` | grep 禁止入口词；检查 SKILL.md 和 README | 不新增 brainstorming、using-superpowers、using-git-worktrees 独立入口 |
| inline fallback 必须先审计划、逐项执行、失败停止 | entry-routing | `blueprint-slice-entry-routing@v1` | grep 验证失败、阻断、任务状态 | 验证失败不得声明完成 |
| TDD 补回强制门和反误用规则 | hard-disciplines | `blueprint-slice-hard-disciplines@v1` | grep 删除并从测试重来、常见借口、RED-GREEN-REFACTOR | 不允许测试后补伪装成 TDD |
| 完成前验证补回证据门 | hard-disciplines | `blueprint-slice-hard-disciplines@v1` | grep 退出码、新鲜验证、输出摘要 | 不允许未验证声明完成 |
| 系统化调试补回根因和反猜测机制 | hard-disciplines | `blueprint-slice-hard-disciplines@v1` | grep 根因、假设、三次失败 | 不允许猜测修复和堆叠改动 |
| 测试反模式补回 mock 与测试专用方法约束 | hard-disciplines | `blueprint-slice-hard-disciplines@v1` | grep mock、测试专用、集成测试 | 不允许测试 mock 行为 |
| 根因追踪补回从症状到源头的追踪链 | hard-disciplines | `blueprint-slice-hard-disciplines@v1` | grep 最早触发点、调用者、参数来源 | 不允许只修深层症状点 |
| 防御式验证补回多层检查 | hard-disciplines | `blueprint-slice-hard-disciplines@v1` | grep 入口边界、业务逻辑、环境守卫 | 不允许单点验证被绕过 |
| 条件式等待补回真实条件等待模式 | hard-disciplines | `blueprint-slice-hard-disciplines@v1` | grep waitFor、真实条件、超时 | 不允许随意 sleep 修 flaky |
| 执行计划补回文件结构、任务粒度、No placeholders、自检 | planning-orchestration | `blueprint-slice-planning-orchestration@v1` | grep No placeholders、占位符、文件职责 | 计划不得要求执行者补设计判断 |
| subagent 编排补回状态处理和审查循环 | planning-orchestration | `blueprint-slice-planning-orchestration@v1` | grep DONE_WITH_CONCERNS、NEEDS_CONTEXT、BLOCKED、规格审查 | 不跳过两阶段审查 |
| 并行 agent 补回独立域与集成检查 | planning-orchestration | `blueprint-slice-planning-orchestration@v1` | grep 同一文件、共享状态、集成验证 | 不并行编辑同一文件集 |
| 实现 prompt 补回提问、升级、自查、报告格式 | planning-orchestration | `blueprint-slice-planning-orchestration@v1` | grep 提问、升级、DONE、BLOCKED | subagent 不静默猜测 |
| 规格审查 prompt 补回不信任报告与 file:line | planning-orchestration | `blueprint-slice-planning-orchestration@v1` | grep 不信任实现报告、file:line | 审查不只看报告 |
| 质量审查 prompt 补回严重性校准 | planning-orchestration | `blueprint-slice-planning-orchestration@v1` | grep Critical、Important、Minor | 不把风格问题标为 Critical |
| 代码审查补回 SHA 范围、反馈处理和 YAGNI | review-finishing | `blueprint-slice-review-finishing@v1` | grep BASE_SHA、HEAD_SHA、外部反馈、YAGNI | 蓝图外建议不直接实现 |
| 最终审查 prompt 补回生产就绪检查 | review-finishing | `blueprint-slice-review-finishing@v1` | grep Ready to merge、file:line、生产 | 审查结论必须有 diff 证据 |
| 分支收尾补回四选项、确认删除、验证失败阻断 | review-finishing | `blueprint-slice-review-finishing@v1` | grep 本地合并、创建 PR、保留分支、丢弃、确认 | 不自动删除用户工作 |
| 技能编写补回文档 TDD、压力场景、description 规则 | meta-skill | `blueprint-slice-meta-skill@v1` | grep 文档 TDD、压力场景、RED、GREEN、REFACTOR | 不允许无压力场景改技能 |

## 全局验证命令

```bash
# 结构检查：所有 reference 保留固定六段。
for f in human-in-loop-execution/references/*.md human-in-loop-execution/references/prompt-templates/*.md; do
  grep -q "## 适用时机" "$f" && \
  grep -q "## 输入契约" "$f" && \
  grep -q "## 执行规则" "$f" && \
  grep -q "## 禁止事项" "$f" && \
  grep -q "## 输出契约" "$f" && \
  grep -q "## 检查清单" "$f" || exit 1
done

# 禁止路径检查：本次执行不得修改 superpowers 目录。
git diff --name-only -- superpowers | grep . && exit 1 || true

# 入口边界检查：不得恢复被裁剪入口。
grep -R "name: brainstorming\|name: using-superpowers\|name: using-git-worktrees" human-in-loop-execution && exit 1 || true

# 高风险能力关键词检查。
grep -n "删除并从测试重来" human-in-loop-execution/references/test-driven-development.md
grep -n "退出码" human-in-loop-execution/references/verification-before-completion.md
grep -n "三次\|3 次" human-in-loop-execution/references/systematic-debugging.md
grep -n "DONE_WITH_CONCERNS\|NEEDS_CONTEXT\|BLOCKED" human-in-loop-execution/references/subagent-driven-development.md
grep -n "BASE_SHA\|HEAD_SHA" human-in-loop-execution/references/code-review.md
grep -n "本地合并\|创建 PR\|保留分支\|丢弃" human-in-loop-execution/references/finishing-branch.md
grep -n "文档 TDD\|压力场景" human-in-loop-execution/references/writing-skills.md
```

## 确定性检查

- 每个已批准设计承诺均映射到一个切片。
- 每个切片均有文件范围、验证项和风险检查点。
- 未确定项：无。
- 模糊表达：无。
- 需要执行者自行裁量的规划判断：无。
