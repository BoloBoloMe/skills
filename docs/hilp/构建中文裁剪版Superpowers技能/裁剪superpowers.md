在结合 HILP 后，**Superpowers 进入 TDD 之前的“设计/审批类环节”大多应被 HILP 接管；“执行准备类环节”应保留**。

最合理的边界是：

```text
HILP：
需求事实 → 方案比较 → 人工裁决/审批 → 确定性实施蓝图 → 执行交接

Superpowers：
worktree → implementation plan → subagent/executing plan → TDD → code review → branch finish
```

## 应当取消或降级的 Superpowers 环节

### 1. `brainstorming` 作为独立入口：应取消

Superpowers 的 `brainstorming` 会做项目上下文探索、逐个澄清问题、提出 2–3 个方案、展示设计、要求用户批准、写 design doc，然后再进入
`writing-plans`。它还明确禁止在设计获批前写代码或调用实现 skill。([GitHub][1])

这些事情在 HILP 里已经被拆得更严格：

* 需求对齐与事实求证阶段
* 方案设计与审批阶段
* 必须人工裁决
* 人工批准授予
* 新事实推翻旧批准后的重审
* 带版本资产状态

所以保留 Superpowers `brainstorming` 会造成**双审批系统**：

```text
HILP 方案审批一次
Superpowers brainstorming design approval 再审批一次
```

这会让状态源混乱：到底哪个 design doc 是绑定性输入？哪个 approval 才算批准？在 HILP 架构下，答案应该只有一个：**HILP
的已批准设计资产和已批准蓝图**。

结论：
**不要在 HILP 后再跑 Superpowers brainstorming。**
它的有用内容应被 HILP 阶段吸收，而不是作为独立环节存在。

---

### 2. Superpowers 的 design doc：应由 HILP 资产替代

Superpowers `brainstorming` 会把设计写入 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`，并要求用户 review 该 spec
后才进入 implementation plan。([GitHub][1])

在 HILP 中，这类文件应替换为：

```text
01-需求对齐与事实求证_...
02-方案设计与审批_...
03-实施蓝图_...
05-执行交接_...
```

原因是 HILP 的资产不仅是文档，还带有：

* `asset_ref`
* `version`
* `state`
* `approval_marker`
* `owner_skill`
* `last_event`
* `last_decision`
* 中文状态名
* 上下游引用链

Superpowers design doc 没有这些状态语义。它适合作为普通开发 spec，不适合作为 HILP 下的绑定性治理资产。

结论：
**Superpowers design doc 不再作为正式源文档。HILP 资产是唯一 source of truth。**

---

### 3. Superpowers 的“提出 2–3 个方案”：保留思想，取消环节

Superpowers `brainstorming` 要求提出 2–3 个方案、说明 trade-off、给出推荐方案。([GitHub][1])

这个能力仍然有价值，但应内化到 HILP 的“方案设计与审批阶段”。也就是说：

```text
保留：多方案比较、trade-off、推荐路径
取消：Superpowers brainstorming 作为单独 skill/阶段
```

HILP 更适合管理这种取舍，因为它能区分：

* 可以默认推进的建议裁决
* 必须人工裁决的阻断性取舍
* 可提交审批但尚未批准的方案
* 已批准方案
* 被新事实推翻的旧批准

Superpowers 的方案比较偏“设计协作”；HILP 的方案比较偏“治理状态机”。在结合场景中，后者应主导。

---

### 4. Superpowers 的用户审批 gate：应取消，改用 HILP approval

Superpowers `brainstorming` 要求用户 review spec 并批准后才能进入 implementation planning。([GitHub][1])

HILP 已经定义了更严格的批准语义：

```text
ready-for-approval ≠ approved
只有明确人工批准授予，才能进入 approved
只有 approved 资产可作为下游绑定输入
```

因此 Superpowers 的“looks good / approved?” gate 应替换为 HILP 的：

```text
Human Approval Granted
批准当前具体 asset_ref / version
```

结论：
**不能让 Superpowers 的轻量 approval 与 HILP 的正式 approval 并存。正式批准只认 HILP。**

---

## 应当保留的 Superpowers 环节

### 1. `using-git-worktrees`：应保留

这是执行隔离，不是方案治理。Superpowers 的 worktree skill 会创建隔离工作区、检查 worktree 目录是否被 git ignore、安装依赖、跑
baseline tests，确保开始实现前有干净基线。([GitHub][2])

HILP 不解决这个问题。HILP 只说“能不能进入执行”，不负责：

* 是否在 main/master 上误改
* worktree 是否被误提交
* baseline tests 是否已失败
* 依赖是否安装
* 当前工作区是否干净

结论：
**保留。它应该是 HILP 执行交接之后的第一个 Superpowers 环节。**

推荐顺序：

```text
HILP execution-handoff approved
→ create isolated worktree
→ install dependencies
→ run baseline tests
→ only then start implementation planning/execution
```

---

### 2. `writing-plans`：应保留，但改造成“蓝图转执行计划”

Superpowers `writing-plans` 的价值很大：它会把 spec 转成 bite-sized tasks，并要求每个任务写出精确文件路径、测试代码、命令、预期输出、最小实现和
commit 步骤；它还要求计划自检 spec coverage、placeholder、类型一致性。([GitHub][3])

但它不能再自由解释需求或重新设计架构。结合 HILP 后，它的输入应该不是普通 spec，而是：

```text
HILP 已批准设计资产
+ HILP 已批准实施蓝图
+ HILP 执行交接资产
```

它的职责从：

```text
把 requirements/spec 变成 implementation plan
```

降级为：

```text
把已批准、已确定的 HILP 蓝图机械拆成 TDD 任务
```

保留内容：

* 文件清单
* task decomposition
* 每步 2–5 分钟
* 写失败测试
* 跑测试确认失败
* 最小实现
* 跑测试确认通过
* commit
* plan self-review

删除/禁止内容：

* 新增方案选择
* 改写架构
* 补做未批准的设计判断
* 把 HILP 蓝图里的不确定项“自行解释清楚”
* 引入 HILP 未批准的文件范围或接口形态

结论：
**保留，但必须受 HILP execution handoff 约束。**

---

### 3. `subagent-driven-development`：应保留

Superpowers 的 subagent-driven development 会在已有 implementation plan 时，为每个独立 task 派 fresh subagent，并在每个
task 后做两阶段 review：先 spec compliance，再 code quality。([GitHub][4])

HILP 不替代这个。HILP 的执行交接只规定：

```text
执行什么
不能越界什么
引用哪些已批准资产
入口是否有阻断项
```

但它不规定：

* 每个 task 是否应该 fresh context
* task 之间如何 review
* 如何避免上下文污染
* 如何在实现中连续保持质量 gate

结论：
**保留，尤其适合 HILP 已经产出明确蓝图的大中型任务。**

但要加一个约束：

```text
subagent 的 prompt 不能只引用 Superpowers plan；
必须同时引用 HILP execution-handoff asset_ref 和禁止越界项。
```

---

### 4. `executing-plans`：有条件保留

Superpowers `executing-plans` 用于没有 subagent 或需要在独立 session 中执行计划的情况；它会先读取并审查 plan，发现 blocker
就停止，按任务执行验证，完成后进入 finishing branch。([GitHub][5])

结合 HILP 后，它是 `subagent-driven-development` 的 fallback：

```text
有 subagent + task 独立 → subagent-driven-development
无 subagent / task 紧耦合 / 当前平台不支持 → executing-plans
```

但同样不能重新规划。它只能执行 HILP 已交接的 plan。

结论：
**保留为 fallback，不作为默认首选。**

---

### 5. `test-driven-development`：必须保留

这是 Superpowers 的核心执行纪律。它要求任何
feature、bugfix、refactor、行为变更都先写失败测试；如果先写了生产代码，就删除并从测试重来。([GitHub][6])

HILP 不替代 TDD。HILP 能保证“现在可以写代码”，但不能保证“代码以正确方式写”。

两者边界非常清楚：

```text
HILP：是否允许进入实现？
TDD：实现时每一步是否可验证？
```

结论：
**必须保留。HILP 后的每个实现 task 都应进入 TDD。**

---

### 6. `requesting-code-review` / review gate：应保留

Superpowers 的 code review skill 要求在每个 subagent task 后、重大 feature 完成后、merge 前请求 review；review
会按严重性处理，Critical 阻断进展，Important 要先修。([GitHub][7])

HILP 的 review 是规划治理 review，不是代码质量 review。它关心：

* 是否有已批准资产
* 是否有阻断项
* 是否可以交接
* 是否新事实推翻旧资产

Superpowers code review 关心：

* 是否按 plan 实现
* 是否有 bug
* 测试是否充分
* 代码是否可维护
* 是否过度实现

结论：
**保留。它是执行层质量 gate，不与 HILP 重复。**

---

### 7. `finishing-a-development-branch`：应保留，但不能替代 HILP 归档

Superpowers finishing branch 会在实现完成且测试通过后，验证测试、给出 merge/PR/keep/discard/cleanup
等选项。([AgentSkills][8])

HILP 的 archive 是规划资产归档，不是 git 分支收尾。两者对象不同：

```text
Superpowers finishing：
代码分支、测试、merge/PR、worktree cleanup

HILP archive：
规划资产、批准链、执行交接引用、历史状态
```

结论：
**保留，但完成后应回写 HILP：执行结果、PR/commit、偏差、新事实。**

如果执行中发现蓝图错误或上游假设错误，不应该用 finishing branch 直接“收尾”，而应回到 HILP reapproval。

---

## 最终建议：HILP + Superpowers 的裁剪后流程

我建议组合成这个流程：

```text
1. HILP 初始分流
2. HILP 需求对齐与事实求证
3. HILP 方案设计与审批
4. HILP 实施蓝图
5. HILP 执行交接

6. Superpowers using-git-worktrees
7. Superpowers writing-plans
   - 输入只能是 HILP approved blueprint + execution handoff
   - 不允许重新设计
8. Superpowers subagent-driven-development
   或 executing-plans fallback
9. Superpowers test-driven-development
   - 每个 task 内部执行 Red-Green-Refactor
10. Superpowers requesting-code-review
    - 每 task / 每 batch / merge 前
11. Superpowers finishing-a-development-branch
12. HILP archive / reapproval
    - 无偏差：归档
    - 有新事实、偏差、回滚风险：重审
```

## 简化版判断表

| Superpowers 环节                   |       结合 HILP 后处理 | 原因                             |
|----------------------------------|------------------:|--------------------------------|
| `brainstorming`                  |            取消独立环节 | 与 HILP 需求、方案、审批重复              |
| `brainstorming` 的上下文探索           | 保留思想，放入 HILP 事实求证 | 仍需要事实基础                        |
| `brainstorming` 的 2–3 方案比较       | 保留思想，放入 HILP 方案设计 | HILP 更适合管理裁决和审批                |
| Superpowers design doc           |       替换为 HILP 资产 | HILP 有版本、状态、审批语义               |
| Superpowers spec approval        |                取消 | 只认 HILP Human Approval Granted |
| `using-git-worktrees`            |                保留 | 执行隔离，HILP 不处理                  |
| `writing-plans`                  |             保留但降级 | 只做已批准蓝图的任务拆解                   |
| `subagent-driven-development`    |                保留 | 防上下文污染，提供 task-level review    |
| `executing-plans`                |      保留为 fallback | 无 subagent 或紧耦合任务时使用           |
| `test-driven-development`        |              必须保留 | HILP 不替代代码验证纪律                 |
| `requesting-code-review`         |                保留 | 代码质量 gate，不是规划 gate            |
| `finishing-a-development-branch` |                保留 | git/PR/worktree 收尾             |
| Superpowers skill-writing TDD    |     只在改 skill 时保留 | 与业务开发流程无关                      |

## 关键原则

**HILP 接管“该不该做、做哪种方案、是否批准、是否能交接”。**

**Superpowers 保留“怎么安全地实现、怎么测试、怎么 review、怎么收尾”。**

所以，进入 TDD 前真正还需要的 Superpowers 前置环节只剩三个：

```text
worktree isolation
→ implementation plan from approved HILP blueprint
→ execution orchestration via subagent/executing-plans
```

其余设计和审批前置环节，应由 HILP 替代。

[1]: https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md?utm_source=chatgpt.com "superpowers/skills/brainstorming/SKILL.md at main · obra/superpowers · GitHub"

[2]: https://github.com/obra/superpowers/blob/main/skills/using-git-worktrees/SKILL.md?utm_source=chatgpt.com "superpowers/skills/using-git-worktrees/SKILL.md at main · obra/superpowers · GitHub"

[3]: https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md?utm_source=chatgpt.com "superpowers/skills/writing-plans/SKILL.md at main · obra/superpowers · GitHub"

[4]: https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md?utm_source=chatgpt.com "superpowers/skills/subagent-driven-development/SKILL.md at main · obra/superpowers · GitHub"

[5]: https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md?utm_source=chatgpt.com "superpowers/skills/executing-plans/SKILL.md at main · obra/superpowers · GitHub"

[6]: https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md?utm_source=chatgpt.com "superpowers/skills/test-driven-development/SKILL.md at main · obra/superpowers · GitHub"

[7]: https://github.com/obra/superpowers/blob/main/skills/requesting-code-review/SKILL.md?utm_source=chatgpt.com "superpowers/skills/requesting-code-review/SKILL.md at main · obra/superpowers · GitHub"

[8]: https://agentskills.so/skills/obra-superpowers-finishing-a-development-branch?utm_source=chatgpt.com "finishing-a-development-branch - Agent Skill by obra/superpowers"
