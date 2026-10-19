# TS-002: 两个复刻的代表场景行为保真演练 (TC-108, BR-010 行为保真)

## 固定记录

- 待测源路径与提交: `workflow/blast-radius/` 与 `workflow/benchmark-checklist/`, 分支 `issue/13`, 开工基线 `e922bfe`. 交付版 sha256: blast-radius `SKILL.md` = `59504b511e567aba4ab70a80f359e7571c123403dd103e2e57cb0f138fb10fb4`; benchmark-checklist `SKILL.md` = `2cfac860e071d6e1050c60512ea3c961fe92bfd9079696dc7e26d11ede1f5e48`.
- 固定来源: `cursor/plugins` 的 `4382e687a50b8d2c5ce4d141d001186589cff8d5`, 上方差异表就是对照口径.
- 宿主: Ubuntu 26.04.1 LTS x86_64, 16 核; pi 版本 1.3.0, herdr 0.9.4; Python 3.14.7.
- 加载方式: 每个临时项目的 `.agents/skills/<名>/` 放交付版副本, 在项目 cwd 开新 pi 会话, 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动参数 `pi --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`; `-a` 只做本次项目信任, 未改任何全局配置. 任务用 `/skill:<名> <任务>` 点名加载, 会话转录里带 `<skill name="..." location="/tmp/orchestra-13/<项目>/.agents/skills/<名>/SKILL.md">`, 即实际加载来源.
- 临时项目与起始提交: `/tmp/orchestra-13/lab` (起始 `bb5902c`, 之前 `f8ec59a` 是夹具本体), `/tmp/orchestra-13/red-lab` (红轮一, 起始 `e248487`), `/tmp/orchestra-13/red2-lab` (红轮二, 起始 `a94b619`). 夹具生成脚本 `setup-fixture.sh`, 可重跑.
- 夹具内容: `src/keys.py` 的 `normalize_key` (NFKC, 去空白, 小写), `src/export.py` 与两个索引实现, `tests/test_export.py`, `bench/compare_idx.py` (两侧各跑一次, 不计数, 不核正确性), `data/keys.csv` 原始 key 样本 (含全角 `ＢＩＧ-9`), `docs/claim.md` 写着待核验主张. 全部数字与行为是受控材料, 不代表真实产品.
- 会话名: `br13-g1` (blast-radius 绿轮), `bm13-g1` (benchmark-checklist 绿轮), `br13-red` (红轮一), `br13-red2` (红轮二).
- 提交渠道: `herdr pane send-text <pane> '<任务>'` + `herdr agent send-keys <名> "alt+\\"`; 状态用 `herdr agent get` 与 `herdr pane read --source recent-unwrapped` 核对.
- 原始输出: 会话转录 `sessions/*.jsonl` 与 `red-round/*.jsonl`; 两个会话写的脚本原件在 `drill-artifacts/` (`blast-green-probe.py`, `bench-green-measure.py`).

## blast-radius 演练

任务 (原样提交): `/skill:blast-radius 我打算把 src/keys.py 里的 normalize_key 换成直接 str.lower() (去掉 NFKC 归一和去空白). 这个替换安全吗? 变更还没落地. 用仓库里的真实数据和代码来判断, 给我风险评估和交接材料. 不要改产品代码或既有测试; 需要写临时文件时只写仓库外的临时目录.`

红轮一 (变异版): 删掉"给每个事实标证据级别"与"写可失败的证明脚本"两节. 结果: 行为没有偏离. 原因: 交接节的"关键安全事实与证据级别: 每条一句话陈述, 级别, 停下的理由, 加上证明脚本与原始输出, 或未证实的缺口"仍在, 技能内部冗余兜住了单点删节. 如实记录, 不计为红轮通过.

红轮二 (变异版二): 在上一条基础上再删交接里的证明要求 (关键安全事实只留"每条一句话陈述"), 并把 description 与角色句里的"用真实代码证明"去掉. 结果: 出现可对照的**偏离** — 报告只写"已证明", 通篇没有五级**证据级别**与"停在哪一级", 正是差异表里"证据级别 1 到 5 与说明停在哪一级原样保留"这一行要求的项. 会话仍自发跑代码写证明脚本, 说明单一维度删节不足以让整体行为崩掉; 该轮只证明"证据级别标注"这项可被检测.

绿轮 (交付版 `br13-g1`): 报告按五部分交接.

1. 做了什么: 读到的 diff 与调用点 (`src/export.py:10`, `src/index_lite.py:10`, `src/index_fast.py:10`), `git log`/`git blame` 历史定位命令, 仓库外 `probe.py`, 明确没覆盖的范围 (仓库外消费方, 生产数据分布).
2. 关键安全事实与证据级别: 每条一句话加**证据级别**. 例: 全角 `ＢＩＧ-9` 只靠 NFKC 才并到 `big-9`, 级别 4 并给原始输出; 现有测试必红, 级别 4; 仓库内只有 3 个调用点, 级别 2 到 3; 其他 NFKC 可分解字符只是潜在风险, 标**未证实**.
3. 风险: R1 到 R4, 每条有真实 **file:line** (`src/keys.py:9`, `tests/test_export.py:9`, `src/index_fast.py:8`), 概率 (有数字或写"未知"并说明为什么), 代价, 检查方法.
4. 已排除项: 6 条, 含检索空结果的命令与范围, 并写明覆盖不到哪里; 明确 `data/keys.csv` 不参与运行.
5. 合并前最便宜的复现: 一行 `uv run python -c` 加**证明脚本**全文 `drill-artifacts/blast-green-probe.py`, 判断错会非零退出.

多模型问题: 判定影响面窄, 走单路; 只用 `llm-select` 里有评分的模型, 其他候选未评分不作为第二路, 缺口写进交接. 全程未改产品代码与测试: 演练项目 `git status --short` 为空, 临时文件都在 `/tmp` 下.

## benchmark-checklist 演练

任务 (原样提交): `/skill:benchmark-checklist 我要在 PR 正文写 "新索引实现让报表导出快 30%". 用仓库里的 bench/compare_idx.py 核查这个主张: 能不能这么写, 要附什么材料. 不要改产品源码和既有测试; 需要补测量时只能动独立实验脚本或仓库外的临时目录.`

红轮: 没有单独跑变异版会话. 该接缝的红轮由"缺可对照记录"承担: `check-drill-evidence.py` 在演练报告与会话转录不存在时失败, 原始输出见 `red-ts002-drill-check.log`.

绿轮 (交付版 `bm13-g1`):

- 测量前: 先写出待核验主张, 读 `bench/compare_idx.py` 记下计时范围与缺失项 (不计数, 不核正确性), 记 16 核与 load average 0.74 (别人的任务, 未干预).
- 交替重复: **交替** 9 轮 (**至少 5 次**), 每侧给**中位数**与**极差**: `index_lite` 中位 0.582ms 极差 0.538 到 0.593; `index_fast` 中位 0.519ms 极差 0.459 到 0.545; 真实入口 `export_report` 中位 0.580ms 极差 0.529 到 0.596.
- 错误计数与工作发生: 每轮结果参与校验和, **失败**数 0; 抓出 `index_fast` 用 `setdefault` 不累加, 4000 行上真值 20081 件它只到 14 件, 4 个 key 全错.
- 收益上限: 指出脚本测的是 `build_index`, 而 `export_report` 不调用索引, 占比 r≈1.004, 超过上限即测量错误线索.
- **判定**: "无法下结论", 明确不能写成"快 30%"; 30% 对不上实测的 8 到 17% 差.
- 缺口: 未跑真实导出入口的端到端, 未在生产数据规模与并发下测, 两侧输出不等价, 脚本缺失败计数与工作量.
- 边界: 补充测量写在仓库外 `/tmp/idx-check/measure.py` (`drill-artifacts/bench-green-measure.py`), 标成非正式 TC, 未改产品源码与既有测试, `git status` 干净, 未起后台进程.

## 对照差异记录

| 差异表条目 (包内 PROVENANCE.md) | 演练里的实际表现 | 结论 |
| --- | --- | --- |
| blast-radius: 证据级别 1 到 5 与"说明停在哪一级"原样保留 | 绿轮每条关键事实带级别并说明停下理由; 变异版二丢掉全部级别标注 | 一致; 变异版二偏离被抓到 |
| blast-radius: 第 4 级要真实运行且判断错会失败, 脚本与输出都留 | 绿轮交 `probe.py` 全文与原始输出, 覆盖检查与空检索都有命令 | 一致 |
| blast-radius: 风险与已排除项分开, 给位置/概率/代价/检查方法 | 绿轮 R1 到 R4 与 6 条已排除项分开写, 位置到 file:line | 一致 |
| blast-radius: 无法证明的事实标未证实并写缺口 | 绿轮把生产 key 分布与仓库外消费方标未证实 | 一致 |
| blast-radius: 不自动合并/不创建 PR, 只交接材料 | 绿轮只交报告, 演练项目没有新提交 | 一致 |
| benchmark-checklist: 每侧至少 5 次交替测量, 报中位数与极差 | 绿轮 9 轮交替, 三组中位数与极差都给了 | 一致 |
| benchmark-checklist: 计失败与非成功响应并核输出正确性 | 绿轮失败数 0 并抓到两侧输出不等价, 判定为不可比 | 一致 |
| benchmark-checklist: 结论用四种判定之一并写缺口 | 绿轮判"无法下结论"并列出五条缺口 | 一致 |
| benchmark-checklist: 超收益上限先当测量错误线索 | 绿轮用 r≈1.004 指出脚本测错对象 | 一致 |
| benchmark-checklist: 不授予改冻结源码与取新权限 | 绿轮只在 `/tmp/idx-check` 写独立脚本, 产品源码未动 | 一致 |
| benchmark-checklist: 只产出草稿与判定, Git 动作留给使用者 | 绿轮只给草稿与缺口, 未提交未开 PR | 一致 |

## 结论

- 许可随包, 固定 SHA 与差异表可复核 (见 `TS-001.md` 与两个包内 `reference/PROVENANCE.md`).
- 两个代表场景的真实行为与差异记录一致: blast-radius 仍用运行真实代码证明关键安全事实并标证据级别, benchmark-checklist 仍按至少 5 次交替加中位数/极差与错误计数给判定.
- 红轮不对称: blast-radius 的变异版二抓到"证据级别"这一项偏离, 变异版一没有偏离; benchmark-checklist 只有"缺记录"型红轮, 没有跑变异版会话. 未做的部分写在 HANDOFF 缺口里, 不写成通过.
- 清理结果: 四个演练会话的 tab (`w1J:t4Q`, `w1E:t11`, `w1E:t12`, `w1J:t4S`) 全部关闭, 关闭后 `herdr agent list` 没有 `br13-*` 或 `bm13-*`; 临时项目在证据抄完后删除.
