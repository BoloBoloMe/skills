---
name: ponytail-gain
description: >
  以紧凑记分牌展示 ponytail 的实测影响: 更少代码, 更少成本, 更快速度,
  来自基准测试中位数. 一次性展示, 不是持久模式, 不是当前仓库的数据.
  触发: /ponytail-gain, "ponytail gain", "what does ponytail save",
  "show ponytail impact", "ponytail scoreboard".
---

# Ponytail Gain

调用时展示此记分牌. 一次性: 不要切换 mode, 不要写 flag 文件, 不要持久化任何东西.

数据为已发布的基准测试中位数 (5 个日常任务: email validator, debounce, CSV sum, countdown timer, rate limiter; 三个模型: Haiku, Sonnet, Opus). 这些是实测数据, 不是从当前仓库计算的. 来源: `benchmarks/` 和 README.

## Scoreboard

渲染纯 ASCII 条形图. 条形长度表示实测范围; 标签给出精确数字:

```
  ponytail gain                     benchmark median · 5 tasks · 3 models

  Lines of code   no-skill  ████████████████████  100%
                  ponytail  ██▌·················    6–20%   ▼ 80–94%
  Cost            no-skill  ████████████████████  100%
                  ponytail  █████▌··············   23–53%  ▼ 47–77%
  Speed           ponytail  ▸ 3–6× faster

  This repo:  /ponytail-debt  (shortcuts you deferred)
              /ponytail-audit (what's still cuttable)
```

## Honesty boundary

这些是基准测试中位数, 不是当前仓库. 永远不要输出当前仓库的节省数字 ("you saved X lines/tokens here"): 未构建的版本从未写过, 所以在实际仓库中没有真实的基准可以减. 唯一真实的当前仓库数字来自 `/ponytail-debt` (计数账本), 本卡片指向它而非凭空编造.

## Boundaries

一次性展示. 不修改任何东西, 不切换 mode. "stop ponytail" 或 "normal mode": 还原.
