# Skill 机制

[`writing-for-agents`](SKILL.md) 的 skill 专属分支: 当文档是 skill 时变化的部分 — frontmatter, 调用方式选择, 路由 skill. 其余写法都在 `SKILL.md` 的通用参考材料里.

## 调用方式

两种选择, 支付两种负载:

- **模型调用** skill 的 `description` 常驻上下文. agent 可以根据描述自动触发它, 其他 skill 也能调用它 (用固定格式: "调用 `另一个 skill 的名字` skill"), 模型调用 总是*包含* 用户可达, 因此我也能调用它; 将 description 写成触发器: 专注描写 agent 什么时候调用它, 而不介绍 skill 是什么. description 是 skill 的顶层 上下文指针, 被迫始终加载 — 用永久 上下文负载 换可发现性, 因此必须进行激进的剪枝. 内容全是 参考材料 的 模型调用 skill, 也是共享 参考材料 的一个家: 其他 skill 可以调用它, 多个 skill 需要的 参考材料 只放一处. 机制: 省略 `disable-model-invocation`, 写面向模型的 description, 携带触发 分支 (`SKILL.md` 的 指针 写法规则全部适用). description 内容里不能用冒号 `:`.

- **用户调用** skill 的 description 不会出现在上下文中. agent 不知道它的存在, 直到我亲自提名调用它, 或另一个 skill 写 "调用 `x` skill" — agent 就能用 `resolve_skill` 工具按名字查到并读取它. 零 上下文负载, 但花费 认知负载 — 必须有谁记得它存在并说出名字. 机制: 设 `disable-model-invocation: true`; `description` 变为面向人类: 一行摘要, 剥掉触发词清单.

和我确认 skill 的调用方式. 只会手动触发的, 做成 用户调用, 不付 上下文负载, 只有当 agent 必须自行抵达该 skill, 或其他 skill 必须抵达它时, 才考虑 模型调用.

两个 用户调用 skill 都需要的共享 参考材料, 可以 "住" 入其中一个, 另一个用 "调用 `x` skill" 提名它 — 名字本身就是足够的 指针. 若没有适合居住的 skill, 再推到 skill 系统外的普通文件: 任何 skill 都能指向的外部参考.

以上 "按名字抵达" 依赖本环境的 `resolve_skill` 扩展; 没有它的环境里, 用户调用 skill 只有我能抵达.

## 按 调用 拆分

拆分的 调用 切口 (顺序 切口在 `SKILL.md`): 当我有一个应该独立触发它的不同 引导词, 也就是我真会在 prompt 里用的触发词, 或其他 skill 必须抵达它时, 拆出一个 模型调用 skill. 我要为新的常驻 description 支付 上下文负载, 所以独立可达必须值得.

## 路由 skill

当 用户调用 skill 多到我记不住时, 堆积的 认知负载 由 **路由 skill** 治愈: 一个 用户调用 skill, 命名其他 skill 并说明何时取哪一个, 让我只记一个 skill 而不是许多个. 它说出名字, agent 就能抵达: 用户调用 skill 对 agent 不可发现, 但对提名可抵达.

## 脚本

需要保存, 复用或包含多步逻辑的自动化, 优先编写 Python 脚本, 不用 Bash/shell 实现同等逻辑. Python 脚本默认只用标准库. 必须使用第三方库时, 先说明充分理由并取得我的同意. 遵循项目声明的运行方式和版本约束, 不预设 `python`, `python3`, `py` 或解释器路径. 避免平台专用的 Python API, 命令和语法. 简短的一次性终端命令不属于这条规则的脚本.
