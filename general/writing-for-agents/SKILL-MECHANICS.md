# Skill 机制

[`writing-for-agents`](SKILL.md) 的 skill 专属分支: 文档是 skill 时, 写法有哪些不同 — frontmatter, 调用方式选择, 路由 skill. 其余写法见 `SKILL.md` 的通用参考材料.

## 调用方式

两种选择, 各付一种负载:

- **模型调用** skill 的 `description` 常驻上下文. agent 能据描述自动触发它, 其他 skill 也能调用它 (固定格式: "调用 `另一个 skill 的名字` skill"); *模型调用* 天然*包含* *用户可达*, 我也能随时点名. description 要写成触发器: 只写 agent 什么时候该调用它, 不介绍 skill 是什么. 它是 skill 的顶层 *上下文指针*, 被迫始终加载 — 用常驻 *上下文负载* 换可发现性, 所以必须激进剪枝. 内容全是 *参考材料* 的 *模型调用* skill 还有个附带用途: 安置共享 *参考材料*, 其他 skill 调用它即可共用, 多处需要的东西只存一份. 机制: 省略 `disable-model-invocation`, 写面向模型的 description, 带上触发 *分支* (`SKILL.md` 的 *指针* 写法规则全部适用). description 内容里不能用冒号 `:`.

- **用户调用** skill 的 description 不进上下文. agent 不知道它存在, 直到我亲自提名, 或另一个 skill 写 "调用 `x` skill" — agent 根据名字到 skill 目录下找到它. 零 *上下文负载*, 但消耗 *认知负载*: 得有人记得它存在, 并说得出名字. 机制: 设 `disable-model-invocation: true`; `description` 转为面向人类: 一行摘要, 剥掉触发词.

调用方式先和我确认. 只会手动触发的, 做成 *用户调用*, 不付 *上下文负载*; 只有当 agent 必须自行抵达, 或其他 skill 必须抵达它时, 才考虑 *模型调用*.

两个 *用户调用* skill 共享的 *参考材料*, 可以住进其中一个, 另一个用 "调用 `x` skill" 提名它 — 名字本身就是足够的 *指针*. 若没有适合居住的 skill, 再放到 skill 系统外的普通文件, 作任何 skill 都能指向的外部参考.

*按名字抵达* 依赖环境里的路径 *指针* (本环境是 `AGENTS.md` 中指向 `~/.agents/skills/` 的一行), 且要求 skill 目录名与 frontmatter `name` 一致; 没有指针的环境里, *用户调用* skill 只有我能抵达.

## 命名

skill 的名字本身就是一个 *引导词*: 它在我的 prompt 和其他 skill 的 "调用 `x` skill" 里作为 token 反复出现, 每次都触及同一组行为. 命名优先用预训练已有的概念词/术语 (`tdd`, `probe`, `handoff`): 它们免费招募模型先验, 一个 token 锚定一整片行为; 自造词招募不到先验, 还得另花 token 下定义. 没有贴切的现成词, 就退而动词短语 (`explore-repo`, `write-a-skill`), 让名字读起来像命令, 提名即指令.
硬约束由机制导出: 小写 kebab-case; 目录名必须与 frontmatter `name` 一致, 否则 *按名字抵达* 断裂; 名字必须是我真会在 prompt 里说出的词 — 我不会说的名字, 触发器永远不会被扣动.

## 按 *调用* 拆分

拆分的 *调用* 切口 (*顺序* 切口在 `SKILL.md`): 当我有一个真会在 prompt 里用的独立触发词, 或其他 skill 必须抵达它时, 拆出一个 *模型调用* skill. 新的常驻 description 要我付 *上下文负载*, 独立可达必须值这个价.

## 路由 skill

*用户调用* skill 多到我记不住时, 堆积的 *认知负载* 靠 **路由 skill** 化解: 一个 *用户调用* skill, 列出其他 skill 的名字和各自何时取用, 让我只记一个, 不必记许多个. 它说出名字, agent 就能抵达 — *用户调用* skill 对 agent 不可发现, 但被提名即可达.

## 脚本

需要保存, 复用或含多步逻辑的自动化, 优先写 Python 脚本, 不用 Bash/shell 实现同等逻辑. 默认只用标准库; 必须用第三方库时, 先说明充分理由并取得我同意. 遵循项目声明的运行方式和版本约束, 不预设 `python`, `python3`, `py` 或解释器路径. 避免平台专用的 Python API, 命令和语法. 简短的一次性终端命令不算这里说的脚本.
