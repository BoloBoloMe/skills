# 建立与维护评分表

评分表用数字比较模型能力和成本, `note` 则把比较结果写成选型结论. 每个能力分都要有调研依据, 否则后续无法校对; `price` 由 `score.py` 从目录价格派生, 不手填.

两份数据在本仓库的 `general/llm-select/` 维护: [llm-scores.json](llm-scores.json) (评分卡) 和 [model-catalog.json](model-catalog.json) (价格与模型目录). `score.py` 默认读取脚本同目录的数据, 不依赖当前工作目录或设备上的旧 `~/.agents/llm-select/`. 临时使用其他数据可传 `--scores`/`--catalog`, 不自动回退旧路径.

数据随整个 skill 由仓库同步到 `~/.agents/skills/llm-select/`, 沙箱通过已有 skills 只读挂载读取同一份副本, 无需另建评分数据挂载. 修改回到仓库进行, 不在同步后的真实 agent skill 目录维护. 建表时先取得候选模型的目录信息 (成本与 thinking 档), 才能判断价格和适用任务.

评分卡原样迁自设备数据 (2026-11-18); 2026-11-24 全表按 Artificial Analysis Intelligence Index v5.0.1 重锚, 基准仍为 `cli/glm-5.3-flash`, 六维依据统一取自 AA 模型页 (Max 档; coding 用 Terminal-Bench 4.0, 长上下文用 AA-LCR, 速度用每任务时间). gpt-6.2-astra/gpt-6.2-sol 已按 AA 数据评分; glm-5.4 无公开基准数据, 保持未评分.

## 评分语义

- 分数 = 相对基准模型的比率: 基准各维 = 1, 其余模型 >1 表示强于基准, <1 表示弱.
- 六个人工评分维: coding/knowledge/longctx/multimodal/stability/speed; price 派生, 不存于表中.
- null = N/A: 算画像总分时该维权重归零重归一化; vision 画像要求 multimodal 非 N/A, 否则该画像无总分 (选型表显示 —).
- multimodal 例外: 基准是纯文本模型时该维没有比率锚点, 改用绝对能力档 (1 = 可用, 1.5+ = 强).
- speed 缺权威数据源时允许经验分, 但须在 evidence 标注依据弱.

## 模型目录 (model-catalog.json)

平台无关 schema: `models` 对象, 键为 provider/model 全限定名, 值为:
- `cost`: 单位成本对象, 单位为 USD/1M tokens, 含 `input`/`output` (价格维派生必需), 可含 `cacheRead`/`cacheWrite`. 使用一致计费档的基础单价; 长上下文/缓存时长/批处理等额外计费规则另作说明, 价格分不代表实际账单.
- `reasoning`: 是否推理模型.
- `thinking`: 支持的 thinking 档列表 (最浅到最深), 供选型时挑档.

目录可在顶层 `sources`/`pricingNote` 保留来源和计费边界, 条目可用 `updatedAt` 记录核对日期. 这些说明不参与算分; 声明的档位仍须由当前平台核实是否可用.

基准模型必须存在于目录且单位成本有效 (cost 有 input/output 且不全为零), 否则 score.py 报 `bad-baseline` 且修表治不了 — 先修目录.

## note 的写法

`note` 是你根据评分和目录价格给我的定性结论, 不是证据栏. 每个已评分模型 (含基线) 用简短的话概括相对能力, 价格, 速度, 适合的任务; 有关键短板或不适合的任务时也点明. 例如 `优秀, 便宜, 中速. 适合复杂任务` 是表达形式, 具体判断须以当次数据为准. 能力强弱看相关单项分, 价格看目录中的 input/output 成本及相对基线的价格分, 速度看 speed 分; 任务建议须能由这些差异解释. 依据不足时保留不确定性, 别把弱证据写成肯定结论. 需要追溯的来源, 数值和弱依据留在 `evidence`, 不在 `note` 重抄评分或宣传语.

## 建表

1. **定基准**: 从当前平台实际可用的模型中推荐稳定主流的中档模型, 让强弱两侧有区分度; 先问我确认. 完成标准: 我已确认基线模型.
2. **调研**: 对其余每个模型各派一个子代理并行调研, 相对基线打分; 要求调用 `access-web` skill 查证, 厂商文档/定价页/模型卡优先于第三方测评. 完成标准: 每个候选都有六维分及逐维依据, 成本与 thinking 档已查明; 缺失或薄弱的依据已标出.
3. **落盘**: 按 [scores-template.json](scores-template.json) 写评分表, 按 [model-catalog-template.json](model-catalog-template.json) 写目录. 模型键及 baseline 用 `provider/model` 全限定名, 避免同名模型混淆; 基线必须在目录中且各可用维为 1, 纯文本模型的 multimodal 为 null. 每条评分带 `updatedAt` 和按上文写的 `note`; 依据弱或需要说明的维在 `evidence` 留一行依据. 完成标准: 两份草稿包含所有已调研模型, 每条 note 与分数和价格相符.
4. **交审**: 给我文件路径, 每模型分数摘要和依据弱的条目清单. 完成标准: 我能逐行审改两份草稿及每条定性结论.

## 维护

- 新增候选模型时只补 `model-catalog.json` (cost/thinking), 不要往评分表里填占位分: [未评分] 由"不在评分表"判定 (见 `score.py` 的 build_rows), 填任何数都会被当成已评分, 标记消失且总分混进无依据的伪值. 用 `--scope` 写完整名称纳入后, 该模型会以 [未评分] 殿后, 缺失的能力维显示 N/A, 由价格分算出的画像总分不能用于比较; 择机按上文流程补评后再写入评分表条目.
- 能力变化或发现分数与现实不符时改评分表, 同步更新 `updatedAt`, `note` 和受影响的 `evidence`, 保持结论与依据一致.
- 价格或 thinking 档变动时更新 `model-catalog.json`, 价格维自动派生; 若价格变动改变 `note` 的价格判断或任务建议, 同步更新评分表中的 `note` 和 `updatedAt`.
