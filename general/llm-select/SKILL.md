---
name: llm-select
description: 为子代理选择模型或 thinking 档位时使用, 也用于给模型补评分或重建评分表
---

# llm-select

为子代理选型的依据是每台设备自己的评分表: 候选模型各维能力相对基准模型的比率分, 由联网调研建立, 可按任务画像加权出总分. 不凭印象选型 — 印象分会过期, 且无法校对.

本 skill 平台无关: 不读任何 agent 平台的配置 (pi 的 settings.json/auth.json 等), 只依赖两份自有数据. 模型目录与总分的解释见 [bootstrap.md](bootstrap.md). 全部算分逻辑以 `score.py` 为唯一真相源 (改画像或算法只改它).

## 步骤

1. **渲染选型表**: 运行 `uv run python score.py` (本 skill 目录下). 输出每个候选模型的七维分, 七个画像总分, thinking 支持档与一行文字摘要.
   失败时按 stderr 中的原因分流: `no-table`/`no-catalog` 是数据文件缺失 (评分表或模型目录), 按其路径检查; `bad-scope` 表示 `--scope` 未匹配到模型; `bad-baseline` 是基准配置问题 — 基线不在此设备目录或成本无效, 修表治不了, 需先修模型目录 (见 [bootstrap.md](bootstrap.md) 模型目录节); `bad-json` 是数据文件损坏或评分非数值, 修复后重跑.
   完成标准: 拿到选型表, 或确认是环境问题并已向我报告.
2. **读表选定**:
   - 各维分是相对基准模型的比率: >1 强于基准, <1 弱; N/A 表示该维不适用, 算总分时权重归零重归一化; 表的排序按 general 画像总分, 未评分模型殿后, 仅供参考.
   - 按任务画像读对应列总分: coding/research/review/vision/long-doc/cheap-batch/general; vision 列只覆盖多模态非 N/A 的模型.
   - 跨过任务质量底线的候选中取成本最低者, 不取总分最高者; 若某模型标 [免费], 其价格维已按封顶分处理, 可视为最便宜.
   - 对抗对 (产出方/审查方) 两角色选不同模型: 同一模型的盲点相同, 审查会漏掉产出方的同类错误.
   - thinking 是成本旋钮, 档越深 token 与时间越贵: 任务简单或量大下调, 失败代价高上调; 只能从该模型 thinking 支持行里列出的档中选, 拿不准时选它支持的第二深档.
   - 文字摘要 (各维强弱/`部分评分`缺维/`弱依据`维) 用于脱离总分按质量底线自行判断, 是补充信息不是选型依据.
   完成标准: 选定 model 与 thinking, 且能说出依据了哪一列画像总分.
3. **处理未评分模型**: 表中 [未评分] 模型各维按基准 1 占位, 总分无区分度. 表格默认只列评分表里的模型; 用 `--scope` (glob, 空格或逗号分隔) 指定完整候选集, 可替换默认并纳入评分表外的候选, 它们会以 [未评分] 殿后. 当其中某个可能是更优候选时, 读 [bootstrap.md](bootstrap.md) 补评后重跑 score.py.

## 数据源

- 评分表 `~/.agents/llm-select/llm-scores.json`: 每台设备一份, 建立与维护流程见 [bootstrap.md](bootstrap.md).
- 模型目录 `~/.agents/llm-select/model-catalog.json`: 每台设备一份, 记录每个候选模型的 cost / reasoning / thinking 支持档 (平台无关 schema, 建立见 [bootstrap.md](bootstrap.md)); 价格维从这里派生, 不存于评分表.
- `score.py` 默认读以上两份; 也可用 `--scores`/`--catalog` 指定其他路径. 候选范围缺省 = 评分表的模型键; 用 `--scope` 指定完整候选集 (替换缺省).
- 选型时若要准确得到当前平台可用的模型列表, 由你自己从该平台的配置入口获取 (例如 pi 读 `settings.json` 的 `enabledModels` 或 `auth.json`), 传给 `--scope`, 不硬编码在 score.py 里.
