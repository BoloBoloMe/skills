---
name: llm-select
description: 为子代理选择模型或 thinking 档位时使用
disable-model-invocation: true
---

# llm-select

用本机评分表为子代理选模型和 thinking 档位. 画像总分是按任务侧重汇总的参考值, 不是可用性或质量保证; 算分以 `score.py` 为准.

## 步骤

1. **定候选**: 明确任务需要的能力和失败代价. 从当前平台核实可调用的 `provider/model` 名称和权限, 不输出凭证; 无法核实时说明限制, 不把评分表名单当成可用名单.
2. **跑表**: 在本 skill 目录运行 `uv run python score.py --scope 'provider/model1 provider/model2'`. `--scope` 替换默认名单; 不传时只列评分表中的模型. 通配符只匹配已评分模型, 未评分模型须写完整名称. 报错按提示中的路径和原因处理; 缺数据时不猜分数, 建表见 [bootstrap.md](bootstrap.md).
3. **选模型**: 读贴近任务的画像列 (coding/research/review/vision/long-doc/cheap-batch/general), 先看相关单项分是否达到任务底线, 再在合格模型中选成本较低者. >1 强于基准, <1 弱于基准; N/A 通常从总分中剔除, 不代表达标; vision 的多模态 N/A 则无总分. `部分评分`/`弱依据` 须核实关键维度; `[未评分]` 的画像总分不能比较, 需要时先按 [bootstrap.md](bootstrap.md) 补评. 表按 general 总分排序, 不是推荐顺序.
   价格分用 `0.75 * input + 0.25 * output` 估算, 不是实际账单; 输出/缓存用量特殊时查目录原价. `[免费]` 的价格分已封顶, 价格 N/A 不等于免费. 产出方和审查方尽量选不同模型, 但不能为此放弃质量底线.
4. **选 thinking 并交代依据**: 只从目录确认支持的档里选: 简单/批量任务选浅档, 失败代价高选深档; 拿不准时选第二深档 (仅一档则选该档). 表中的 `off` 可能是目录缺项的回退值, 须核实支持情况. 报出模型, thinking, 画像, 质量底线和价格依据; 无合格候选就说明缺什么, 不猜.
