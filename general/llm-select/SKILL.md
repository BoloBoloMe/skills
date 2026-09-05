---
name: llm-select
description: 为子代理选择模型或 thinking 档位时使用, 也用于给模型补评分或重建评分表
---

# llm-select

为子代理选型的依据是每台设备自己的评分表: 候选模型各维能力相对基准模型的比率分, 由联网调研建立, 可按任务画像加权出总分. 不凭印象选型 — 印象分会过期, 且无法校对.

## 步骤

1. **渲染选型表**: 运行 `uv run python score.py` (本 skill 目录下). 输出每个候选模型的七维分, 七个画像总分, thinking 支持档与一行文字摘要.
   失败时按 stderr 中的原因分流: `no-scoped` 是环境/凭证问题 (检查 settings.json 的 enabledModels 与 provider 凭证), 建表治不了, 修好后重跑; 其余原因 (`no-table`/`bad-json`/`bad-baseline`) 读 [bootstrap.md](bootstrap.md) 建表或修表后重跑.
   完成标准: 拿到选型表, 或确认是环境问题并已向我报告.
2. **读表选定**:
   - 各维分是相对基准模型的比率: >1 强于基准, <1 弱; N/A 表示该维不适用, 算总分时权重归零重归一化; 表的排序按 general 画像总分, 未评分模型殿后, 仅供参考.
   - 按任务画像读对应列总分: coding/research/review/vision/long-doc/cheap-batch/general; vision 列只覆盖多模态非 N/A 的模型.
   - 在跨过任务质量底线的候选中取成本最低者, 而不是取总分最高者.
   - 对抗对 (产出方/审查方) 两个角色选不同模型: 同一模型的盲点相同, 审查会漏掉产出方的同类错误.
   - thinking 是成本旋钮, 档越深 token 与时间越贵: 任务简单或量大下调, 失败代价高上调; 只能从该模型 thinking 支持 行列出的档里选, 拿不准时选它支持的第二深档.
   完成标准: 选定 model 与 thinking, 且能说出依据了哪一列画像总分.
3. **处理未评分模型**: 表中 [未评分] 模型各维按基准 1 占位, 总分无区分度; 当其中某个可能是更优候选时, 读 [bootstrap.md](bootstrap.md) 补评后重跑 score.py.

## 数据源

- 评分表 `~/.agents/llm-select/llm-scores.json`: 每台设备一份, 建立与维护流程见 [bootstrap.md](bootstrap.md).
- 其余文件在 agent 目录下 (环境变量 PI_CODING_AGENT_DIR, 默认 `~/.pi/agent`):
- 模型目录, 价格, thinking 支持: `models-store.json`, `models.json` 中的同名 provider 覆盖前者.
- 候选范围 = settings.json 的 enabledModels (glob) 匹配到的模型 ∩ 有凭证的 provider (auth.json 有条目, 或 apiKey 字面量/`$ENV` 引用可用).

七个画像的权重与全部算分逻辑以 score.py 为唯一真相源, 改画像或改算法只改那里.
