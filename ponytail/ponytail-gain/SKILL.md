---
name: ponytail-gain
description: >
  当我说 "ponytail gain" 或 /ponytail-gain 时使用.
  展示基准测试中位数记分牌: 代码, 成本, 速度. 一次性展示.
---

# Ponytail Gain

调用时展示此记分牌. 一次性: 不要切换 mode, 不要写 flag 文件, 不要持久化任何东西.

数据为已发布的基准测试中位数 (5 个日常任务: email validator, debounce, CSV sum, countdown timer, rate limiter; 三个模型: Haiku, Sonnet, Opus). 这些是实测数据, 不是从当前仓库计算的. 来源: `benchmarks/` 和 README.

## Scoreboard

渲染纯 ASCII 条形图. 条形长度表示实测范围; 标签给出精确数字:

```
  ponytail 收益                    基准中位数 · 5 任务 · 3 模型

  代码行数      无 skill  ████████████████████  100%
                ponytail  ██▌·················    6–20%   ▼ 80–94%
  成本          无 skill  ████████████████████  100%
                ponytail  █████▌··············   23–53%  ▼ 47–77%
  速度          ponytail  ▸ 3–6× 更快

  本仓库:  /ponytail-debt  (你延迟的捷径)
           /ponytail-audit (还有什么可砍)
```

## Honesty boundary

不输出当前仓库的节省数字. 真实数字来自 `/ponytail-debt`.

## Boundaries

一次性展示. 不修改任何东西, 不切换 mode.
