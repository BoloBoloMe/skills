# 建立与维护评分表

评分表的每个分都要有调研依据, 不凭印象打分: 没有依据的分数后续无法校对, 改分无从谈起. price 维不调研 — 它由 score.py 从模型目录的价格派生.

本 skill 平台无关, 两份数据都放在 `~/.agents/llm-select/` 下, 每台设备各一份: `llm-scores.json` (评分) 与 `model-catalog.json` (模型目录). 建立评分表前, 先确保有候选模型的目录数据 (含成本与 thinking 档), 否则价格维与选型无从算起.

## 评分语义

- 分数 = 相对基准模型的比率: 基准各维 = 1, 其余模型 >1 表示强于基准, <1 表示弱.
- 六个人工评分维: coding/knowledge/longctx/multimodal/stability/speed; price 派生, 不存于表中.
- null = N/A: 算画像总分时该维权重归零重归一化; vision 画像要求 multimodal 非 N/A, 否则该画像无总分 (选型表显示 —).
- multimodal 例外: 基准是纯文本模型时该维没有比率锚点, 改用绝对能力档 (1 = 可用, 1.5+ = 强).
- speed 缺权威数据源, 允许经验分, 但必须在 evidence 里标注依据弱.

## 模型目录 (model-catalog.json)

平台无关 schema: `models` 对象, 键为 provider/model 全限定名, 值为:
- `cost`: 单位成本对象, 含 `input`/`output` (价格维派生必需), 可含 `cacheRead`/`cacheWrite`.
- `reasoning`: 是否推理模型.
- `thinking`: 支持的 thinking 档列表 (最浅到最深), 供选型时挑档.

基准模型必须存在于目录且单位成本有效 (cost 有 input/output 且不全为零), 否则 score.py 报 `bad-baseline` 且修表治不了 — 先修目录.

## 建表

1. **定基准**: 从当前可用模型 (见 SKILL.md 数据源, 用 `--scope` 或平台可用列表确定) 中推荐基线模型 — 选稳定主流的中档模型, 让强模型 >1, 弱模型 <1 都有区分度; 先问我确认, 再继续.
   完成标准: 我已确认基线模型.
2. **并行调研**: 对其余每个模型各派一个子代理并行调研 (相对已确认基线打分), 任务中要求调用 `access-web` skill 联网查证, 厂商来源 (文档/定价页/模型卡) 优先于第三方测评; 返回六维比率分, 每维附一行依据.
3. **落盘**: 按 [scores-template.json](scores-template.json) 的结构写 `~/.agents/llm-select/llm-scores.json`: baseline 填已确认基线的 provider/model 全限定名, 基线条目各维 = 1; 每个条目带 updatedAt 与 note, 依据弱或需要说明的维把一行依据写进 evidence. 同时把候选模型写进 `model-catalog.json` (含 cost/thinking), 结构参考 [model-catalog-template.json](model-catalog-template.json). model 键永远用 provider/model 全限定名 — 同名模型可能存在于多个 provider; 基准必须在目录中.
   完成标准: 我已拿到可逐行审改的评分表 + 目录草稿.
4. **交审**: 给我文件路径, 每模型分数摘要, 以及依据弱的条目清单.
   完成标准: 我已拿到可逐行审改的评分表草稿.

## 维护

- 新增候选模型时, 先补 `model-catalog.json` 再补评分表条目; 评分表条目先填 1 占位, 选型表会标 [未评分] (若通过 `--scope` 纳入), 择机按上文流程补评.
- 改分是事件驱动的 (模型升级, 价格调整, 观察到分数与现实不符); 改分时同步更新 updatedAt 与 note/evidence, 否则依据会与分数脱节.
- 模型价格或 thinking 档变动时, 更新 `model-catalog.json` 而非评分表, 价格维自动重新派生.
