# 条件式等待

## 适用时机

测试或实现存在竞态、异步状态未稳定、任意 sleep、偶发失败或 CI 与本地表现不一致时使用。

## 输入契约

- HILP execution handoff asset_ref。
- 需要等待的真实条件。
- 超时上限、轮询间隔和失败诊断信息。
- 禁止越界项。

## 执行规则

等待真实条件，不等待猜测时间。waitFor 伪代码：

```text
waitFor(condition, description, timeoutMs):
  start = now
  loop:
    value = condition()  # 每次读取最新状态
    if value: return value
    if now - start > timeoutMs: throw "Timeout waiting for " + description
    sleep(pollInterval)
```

场景表：

| 场景 | 条件 |
|---|---|
| 事件 | 指定事件已出现。 |
| 状态 | 状态机进入目标状态。 |
| 数量 | 结果数量达到预期。 |
| 文件 | 文件存在或内容满足条件。 |
| 复杂条件 | 多个字段同时满足。 |

允许固定等待的条件：被测对象本身是节流、防抖或定时协议；必须先等待触发条件，再说明固定等待的时间来源。

常见错误：无超时、轮询过快、缓存旧状态、用 sleep 掩盖根因。

## 禁止事项

- 不得用随意 sleep 修 flaky。
- 不得无超时无限等待。
- 不得缓存旧状态后循环判断。
- 不得因等待失败扩大执行范围。

## 输出契约

输出等待真实条件、超时、轮询间隔、失败信息和验证命令。若问题来自设计或蓝图时序缺口，停止并回到 HILP 重审。

## 检查清单

- [ ] 等待的是真实条件。
- [ ] 有明确超时。
- [ ] 失败信息可诊断。
- [ ] 未使用任意 sleep。
- [ ] 验证命令已运行。
