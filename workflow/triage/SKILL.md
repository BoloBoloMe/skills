---
name: triage
description: 单个 issue 的创建, 分流, 推进, 状态管理和 agent brief 流程.
disable-model-invocation: true
---

# 分流(Triage)

通过一个由分流(triage)角色组成的小型状态机,在项目议题跟踪器上推进议题.

在分流(triage)期间发布到议题跟踪器的每条评论或议题**必须**以下方免责声明开头:

```
> *这是 AI 在分流(triage)期间生成的.*
```

## 参考文档

- [AGENT-BRIEF.md](AGENT-BRIEF.md)--如何编写持久有效的智能体简报(agent brief)
- [OUT-OF-SCOPE.md](OUT-OF-SCOPE.md)--`.out-of-scope/` 知识库如何工作

## 启动前置读取

先读取目标项目的议题跟踪器约定和标签映射:

- `docs/agents/issue-tracker.md`
- `docs/agents/triage-labels.md`

如果不存在, 运行 `/setup-workspace`. 读取完成标准: 已知道 issue 文件位置, 状态字段规则, 评论追加位置, 标准角色到实际 label 的映射.

## 角色

两个**类别**角色:

- `bug`--有东西坏了
- `enhancement`--新功能或改进

五个**状态**角色:

- `needs-triage`--维护者需要评估
- `needs-info`--等待报告者提供更多信息
- `ready-for-agent`--规格已完整,已准备好交给 AFK agent
- `ready-for-human`--需要人类实现
- `wontfix`--不会处理

每个已分流(triage)的议题都应恰好携带一个类别角色和一个状态角色.如果状态角色冲突,请标记出来,并在做任何其他事情之前询问维护者.

这些是规范角色名称--议题跟踪器中实际使用的标签字符串可能不同.你应该已经获得了映射;如果没有,请运行 `/setup-workspace`.

状态转换:未标记的议题通常先进入 `needs-triage`;随后它会移动到 `needs-info`,`ready-for-agent`,`ready-for-human` 或 `wontfix`.一旦报告者回复,`needs-info` 会回到 `needs-triage`.维护者可以随时覆盖--对看起来异常的转换做出标记,并在继续前询问.

## 本地 Markdown adapter

当 issue tracker 是本地 Markdown 时, 抽象动作按以下方式落盘:

- 创建 issue: 在 `docs/changes/<feature-slug>/issues/<NN>-<slug>.md` 新建文件.
- 应用类别/状态角色: 在 issue 文件顶部附近维护独立纯 token 行, 如 `Type: bug` 和 `Status: ready-for-agent`. 如项目约定不用 `Type:`, 按 `docs/agents/triage-labels.md` 中的字段规则写入.
- 发布评论: 追加到文件底部 `## 评论(Comments)` 下. 兼容读取 `## Comments`, `## 评论`, `## 评论(Comments)`.
- 关闭 issue: 将 `Status:` 改为 `wontfix` 或目标 tracker 约定的关闭状态. 不删除文件.
- 查询 issue: 读取 `docs/changes/**/issues/*.md`, 按 `Status:` 和 `Type:` 分组. 缺少状态或类别的文件视为未标记.
- 记录报告者活动: 评论区出现非 AI triage 记录且时间晚于最近一次 `## 分流记录(Triage 记录)` 时, 视为需要重新评估.

完成标准: 每次状态变更都同时更新文件字段和必要评论, 最终回复列出变更文件路径.

## 调用

维护者调用 `/triage` 并用自然语言描述他们想要什么.解释该请求并执行.示例:

- "显示所有需要我关注的内容"
- "我们看看 #42"
- "将 #42 移动到 ready-for-agent"
- "有哪些已准备好让 agent 接手?"

## 展示需要关注的内容

查询议题跟踪器,并按从旧到新的顺序展示三个分组:

1. **未标记**--从未分流(triage).
2. **`needs-triage`**--评估进行中.
3. **自上次 triage 记录以来有报告者活动的 `needs-info`**--需要重新评估.

展示每个分组的数量,并为每个议题给出一行摘要.让维护者选择.

## 分流(Triage)特定议题

1. **收集上下文.** 阅读完整议题(正文,评论,标签,报告者,日期).解析任何先前的分流(triage)记录,兼容 `## Triage 记录`,`## 分流记录` 和 `## 分流记录(Triage 记录)`,避免重复询问已解决的问题.使用项目领域术语探索代码库,并遵守相关区域的 ADR.阅读 `.out-of-scope/*.md`,兼容其中的 `决策` / `Decision`,`为什么不在范围内` / `Reason`,`先前请求` / `Prior requests` 章节,并展示任何与此议题相似的先前拒绝.

2. **推荐.** 告诉维护者你建议的类别和状态,并说明理由,同时给出与该议题相关的简短代码库摘要.等待指示.

3. **复现(仅限 bug).** 在任何追问之前,先尝试复现:阅读报告者的步骤,跟踪相关代码,运行测试或命令.报告发生了什么--成功复现及代码路径,复现失败,或细节不足(强烈的 `needs-info` 信号).确认复现会形成强得多的智能体简报(agent brief).

4. **追问(如需).** 如果议题需要补充细节,请运行一次 `/grill-with-docs` 会话.

5. **应用结果:**
   - `ready-for-agent`--发布智能体简报(agent brief)评论([AGENT-BRIEF.md](AGENT-BRIEF.md)).标题使用 `## 智能体简报(Agent Brief)`.
   - `ready-for-human`--使用与智能体简报(agent brief)相同的结构,但补充 `**需要人类处理的原因:**`,说明为什么不能委派(判断取舍,外部访问,设计决策,手动测试).
   - `needs-info`--发布分流(triage)记录(见下方模板).
   - `wontfix`(bug)--礼貌解释,然后关闭.
   - `wontfix`(enhancement)--写入 `.out-of-scope/`,在评论中链接它,然后关闭([OUT-OF-SCOPE.md](OUT-OF-SCOPE.md)).
   - `needs-triage`--应用该角色.如有部分进展,可选择性评论.

## 快速状态覆盖

如果维护者说"将 #42 移动到 ready-for-agent",请信任他们并直接应用该角色.确认你将要做什么(角色变更,评论,关闭),然后执行.跳过追问.如果在没有追问会话的情况下移动到 `ready-for-agent`,请询问他们是否想编写智能体简报(agent brief).

## 补充信息(Needs-info)模板

```markdown
## 分流记录(Triage 记录)

**目前已确认的内容:**

- 要点 1
- 要点 2

**仍需 @reporter 提供的内容:**

- 问题 1
- 问题 2
```

将追问期间已解决的所有事项记录在"目前已确认的内容"下,这样工作不会丢失.问题必须具体且可操作,而不是"请提供更多信息".

## 恢复先前会话

如果议题上存在先前的分流(triage)记录,请阅读它们,检查报告者是否回答了任何未解决问题,并在继续前展示更新后的情况.兼容旧标题 `## Triage 记录`,`## 分流记录` 和新标题 `## 分流记录(Triage 记录)`.不要重复询问已解决的问题.
