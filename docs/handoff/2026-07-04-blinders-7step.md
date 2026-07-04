# 交接: blinders 改造 — 从 15 步 per-issue 到 7 步全局

日期: 2026-07-04

## 路线图

**真实意图**: 将 AFK 工作流从"父会话一次读取全流程"改为逐步披露 (blinders). 父会话只知当前步骤, 不掌握全局. 多次迭代后收敛到: 7 个全局共享步骤文件, 跨多个 issue 串行执行.

**里程碑**:

1. 盘问确认: `_next.md` 语义更正为 `_current.md` — 文件内容是"当前应立即执行的步骤", 不是"下一步".
2. 落地 blinders 初版: SKILL.md 极简入口, 19 step-gen-guide 模板, to-issues 生成 per-issue 步骤文件.
3. write-a-skill 审核 + prompt 重构: 4 个 prompt 合并为 2 个 (WORKER.md, REVIEWER.md), 去掉所有 `<...>` 占位符. 父会话不读 prompt, 通过 task 参数把路径注入子代理.
4. 步骤合并: 19→16 (合并 02/03/04 入预检), 再 16→15 (合并 01+02). `_current.md` 增加 `done` sentinel.
5. 发现 per-issue 步骤文件架构问题: 15×N 文件, 其中 14×N 是重复模板. 写审核报告 `docs/review/per-issue-step-files.md`.
6. 对抗性分析, 否决方案 A (模板+变量), B (父会话 copy), C (维持). 明确约束: 两个父会话隔离 (to-issues ≠ run-afk-workflow), skill 不提供步骤模板, 步骤文件在父会话工作目录生成.
7. **决议**: 7 步全局共享, `_current.md` 格式 `ISSUE-KEY:NN`. 详见审核报告.

**距离目的地**: 审核报告 (方案) 已定, 当前 skill 文件仍是旧架构 (per-issue 15 步). 下一步: 按审核报告方案改代码.

## 当前状态

### 已修改的文件 (已落地)

| 文件 | 状态 |
|------|------|
| `workflow/run-afk-workflow/SKILL.md` | 极简入口, 92 行. `_current.md` 路由 + 子代理接口 + 硬边界. 执行循环含 `done` sentinel. |
| `workflow/run-afk-workflow/prompts/WORKER.md` | 新建. 18 行静态角色定义. |
| `workflow/run-afk-workflow/prompts/REVIEWER.md` | 新建. 17 行静态角色定义. |
| `workflow/run-afk-workflow/prompts/WORKER-IMPLEMENT.md` | 已删除 |
| `workflow/run-afk-workflow/prompts/WORKER-FIX.md` | 已删除 |
| `workflow/run-afk-workflow/prompts/REVIEWER-CORRECTNESS.md` | 已删除 |
| `workflow/run-afk-workflow/prompts/REVIEWER-DECISION-BOUNDARY.md` | 已删除 |
| `workflow/to-issues/references/step-gen-guide.md` | 仍为 per-issue 15 步模板 (待替换) |
| `workflow/to-issues/SKILL.md` | 步骤 6a 引用 step-gen-guide (待更新) |
| `docs/changes/blinders/DECISIONS.md` | 已更新 D002/D005/D009/D010 等 |
| `docs/changes/blinders/CONTRACT.md` | 已同步 |
| `docs/changes/blinders/PRD.md` | 已同步 |

### 核心设计原则 (已确立)

- prompt: 静态, 父会话不读. 路径由父会话 task 注入.
- `_current.md`: 三态 — `step-NN.md` / `done` / 不存在.
- 盲视: 父会话一次只持当前步骤 + `_current.md`. 不读其他步骤文件.
- 两个父会话隔离: to-issues 父会话 ≠ run-afk-workflow 父会话.
- skill 本身不提供步骤模板文件.

## 必读推荐

1. **`docs/review/per-issue-step-files.md`** — 审核报告. 包含 per-issue 文件爆炸问题分析、否决的 A/B/C 方案、最终决议方案 (7 步全局, `ISSUE-KEY:NN`). **下一步改进计划的目标架构.**

2. **`docs/changes/blinders/DECISIONS.md`** — 决策账本. D001-D010, 其中 D002 (`_current.md`), D005 (step-gen-guide 位置), D010 (步骤粒度) 需要随新方案更新.

3. **`docs/changes/blinders/CONTRACT.md`** — 行为边界、允许/禁止范围、验证入口. 仍需更新: 步数从 15→7, 步骤文件从 per-issue 到全局.

4. **`workflow/run-afk-workflow/SKILL.md`** — 当前已落地的 SKILL.md. 执行循环和子代理接口已到位, 但步骤文件位置描述仍指向 per-issue 目录.

5. **`workflow/run-afk-workflow/prompts/WORKER.md`** 和 **`REVIEWER.md`** — 新 prompt 模型样例. 审核报告中步骤文件的路径模型应与此一致 (静态 + 约定推断, 不 baked-in).

6. **`workflow/to-issues/references/step-gen-guide.md`** — 当前仍是 per-issue 15 步模板. 新方案下此文件需重构或删除.
