---
name: diagnosing-bugs
description: 未知根因失败诊断循环. 当我报告失败/报错/性能回退且根因未明时使用; 根因明确且适合测试先行时转 `tdd`.
---

# Diagnosing Bugs

面向 hard bug 的诊断纪律. 只有明确说明理由时才跳过阶段.

探索代码库时, 读取项目领域语言文件: 单上下文项目读取 `docs/language/UBIQUITOUS_LANGUAGE.md`; 多上下文项目先读取 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`, 再读取相关 `docs/language/contexts/*.md`. 同时检查你触碰区域的 ADR.

## 阶段 1: 建立反馈循环

**这是本 skill 的核心.** 如果你有一个紧反馈信号, 能针对这个 bug 变红, 你就能找到原因. 二分, 假设检验, 插桩都只是消费这个信号. 如果没有反馈循环, 盯代码没有意义.

在这里投入不成比例的精力. 要主动, 要有创意, 不要轻易放弃.

### 构造反馈循环的方法

大致按以下顺序尝试:

1. **失败测试**: 在能触达 bug 的 seam 上写测试, 可以是 unit, integration, e2e.
2. **Curl / HTTP 脚本**: 针对运行中的 dev server.
3. **CLI 调用**: 使用 fixture 输入, 将 stdout 与 known-good snapshot 做 diff.
4. **Headless browser 脚本**: Playwright / Puppeteer 驱动 UI, 断言 DOM/console/network.
5. **重放捕获 trace**: 保存真实 network request/payload/event log 到磁盘, 在隔离代码路径中重放.
6. **一次性 harness**: 启动系统最小子集, 例如一个 service 加 mocked deps, 用单个函数调用触发 bug 路径.
7. **Property / fuzz loop**: 如果 bug 是 sometimes wrong output, 跑 1000 个随机输入寻找失败模式.
8. **Bisection harness**: 如果 bug 出现在两个已知状态之间, 自动化 boot at state X, check, repeat, 使它能被 `git bisect run` 消费.
9. **Differential loop**: 同一输入跑 old-version vs new-version 或两个 config, 再 diff 输出.
10. **HITL bash 脚本**: 最后手段. 如果必须有人点击, 用 `scripts/hitl-loop.template.sh` 驱动人, 让循环仍然结构化. 捕获输出再反馈给 agent.

建立正确反馈循环后, bug 已经修好 90%.

### 收紧反馈循环

把反馈循环当产品. 有了一个循环后, 继续收紧:

- 能不能更快? 缓存 setup, 跳过无关 init, 缩小测试范围.
- 能不能信号更尖锐? 断言具体症状, 不只断言 did not crash.
- 能不能更确定? 固定时间, 固定 RNG seed, 隔离文件系统, 冻结网络.

30 秒且 flaky 的循环只比没有稍好. 2 秒确定性的循环才是调试超能力.

### 非确定性 bug

目标不是 clean repro, 而是更高复现率. 循环触发 100 次, 并行, 加 stress, 缩小 timing window, 注入 sleep. 50% flake 可以调试. 1% 不行. 继续提高复现率, 直到可调试.

### 如果确实无法建立反馈循环

停止并明确说明. 列出已尝试的方式. 向用户索取:

- 能复现的环境访问权限.
- 捕获资产, 例如 HAR file, log dump, core dump, 带时间戳的 screen recording.
- 添加临时生产 instrumentation 的许可.

没有反馈循环时, 不要继续假设.

### 完成标准: 一个紧且可变红的循环

阶段 1 完成条件: 你能给出一个已经至少运行过一次的命令, 例如脚本路径, 测试调用, curl, 并粘贴调用与输出. 该命令必须满足:

- [ ] **Red-capable**: 驱动真实 bug 路径, 断言用户的精确症状, 可以在这个 bug 上变红, 修复后变绿. 不能只是 runs without erroring.
- [ ] **Deterministic**: 每次运行结论相同. Flaky bug 需要按上文固定为高复现率.
- [ ] **Fast**: 秒级, 不是分钟级.
- [ ] **Agent-runnable**: 可无人值守运行. 人在回路只能通过 `scripts/hitl-loop.template.sh`.

如果你在这个命令存在前就开始读代码构建理论, 立刻停止. 直接跳到假设正是本 skill 防止的失败模式. 没有 red-capable command, 就没有阶段 2.

## 阶段 2: 复现 + 最小化

运行反馈循环. 观察它变红, 确认 bug 出现.

确认:

- [ ] 循环产出的失败模式就是用户描述的失败, 不是附近的另一个失败. 错 bug 等于错修复.
- [ ] 失败可多次复现. 非确定性 bug 要达到足够高复现率.
- [ ] 已捕获精确症状, 例如 error message, wrong output, slow timing, 以便后续验证修复确实覆盖它.

### 最小化

循环变红后, 将复现缩到仍会变红的最小场景. 一次只切掉一个输入, caller, config, data 或 step, 每次切完都重跑循环. 只保留对失败负重的元素.

原因: 最小复现缩小阶段 3 的假设空间, 并成为阶段 5 的干净回归测试.

完成条件: 每个剩余元素都是 load-bearing. 移除任一元素都会让循环变绿.

复现且最小化之前, 不要进入下一阶段.

## 阶段 3: 提出假设

先生成 **3-5 个排序后的假设**, 再测试其中任何一个. 单一假设会锚定第一个看似合理的想法.

每个假设必须可证伪: 写出它的预测.

格式: "如果 <X> 是原因, 那么 <改变 Y> 会让 bug 消失 / <改变 Z> 会让 bug 变严重."

如果说不出预测, 它只是感觉. 丢弃或打磨.

测试前先把排序列表给用户看. 用户常有领域知识, 能立刻重排, 例如 "我们刚发布了 #3 的变更", 或知道某些假设已经被排除. 这是低成本 checkpoint. 不阻塞: 如果用户 AFK, 按你的排序继续.

## 阶段 4: 插桩

每个 probe 必须对应阶段 3 的一个具体预测. 一次只改一个变量.

工具偏好:

1. **Debugger / REPL inspection**: 环境支持时优先. 一个断点胜过十条日志.
2. **Targeted logs**: 打在能区分假设的边界上.
3. 不要 log everything and grep.

每条 debug log 都使用唯一前缀, 例如 `[DEBUG-a4f2]`. 结束时用一次 grep 清理. 未打标日志会残留. 打标日志必须删除.

**性能分支**: 性能回退通常不该先写日志. 先建立 baseline measurement, 例如 timing harness, `performance.now()`, profiler, query plan, 然后二分. 先测量, 后修复.

## 阶段 5: 修复 + 回归测试

修复前先写回归测试, 但前提是存在正确 seam.

正确 seam 指测试能像调用点实际发生那样触发真实 bug pattern. 如果唯一 seam 太浅, 例如单 caller 测试覆盖不了需要多 caller 的 bug, 或 unit test 复制不了触发 bug 的调用链, 那里的回归测试只会给出假信心.

如果没有正确 seam, 这本身就是发现项. 记录它. 代码库架构正在阻止这个 bug 被锁定. 将它标记给下一阶段.

如果存在正确 seam:

1. 将最小复现变成该 seam 上的失败测试.
2. 确认它失败.
3. 应用修复.
4. 确认它通过.
5. 对原始未最小化场景重跑阶段 1 反馈循环.

## 阶段 6: 清理 + 事后分析

宣布完成前必须满足:

- [ ] 原始复现不再复现, 已重跑阶段 1 循环.
- [ ] 回归测试通过, 或已记录没有正确 seam.
- [ ] 所有 `[DEBUG-...]` instrumentation 已删除, 已 grep 前缀.
- [ ] 一次性原型已删除, 或移动到明确标记的 debug 位置.
- [ ] commit / PR message 说明最终正确的假设, 让下一个调试者学习.

然后追问: 什么本可阻止这个 bug? 如果答案涉及架构变化, 例如没有好测试 seam, caller 缠绕, 隐藏耦合, 将具体信息交给 `/improve-codebase-architecture` skill. 修复完成后再给该建议, 不要修复前给. 此时你知道的信息更多.
