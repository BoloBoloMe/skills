# ISSUE-09 证据索引

本目录是 ISSUE-09 在 `workflow/benchmark-checklist/SKILL.md` 上增量实现 "粗估与异常处理" (AC-028) 和 "结论与 PR 主数字" (AC-029) 的原始材料.

两份切片记录: `TS-001.md` (AC-028), `TS-002.md` (AC-029). 交付报告: `HANDOFF.md`. 机械检查日志: `machine-checks.log`.

## 环境

- 宿主: Ubuntu 26.04.1 LTS, 内核 7.0.0-31-generic, 16 核 (`nproc`).
- herdr 0.9.4 (protocol 22), pi 1.3.0.
- 演练模型: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 启动参数: `pi --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`; `-a` 只做本次项目信任, 未改任何全局配置.
- 加载方式: 把待测技能源目录复制到临时项目 `.agents/skills/benchmark-checklist/`, 在该项目 cwd 开新会话, 用 `/skill:benchmark-checklist <任务>` 点名加载. 会话转录里每条用户消息带 `<skill name="benchmark-checklist" location="/tmp/orchestra-09/lab/.agents/skills/benchmark-checklist/SKILL.md">` 前缀, 即实际加载来源.
- 来源核对: 演练期间 `find /home/bolo/.agents/skills /home/bolo/.pi -maxdepth 4 -type d -name benchmark-checklist` 无命中, `find /tmp/orchestra-09 -maxdepth 6 -type d -name benchmark-checklist` 只命中临时项目里那一份; 全局部署没有同名技能.

## 待测源与版本

待测源文件: `workflow/benchmark-checklist/SKILL.md`.

| 版本 | 仓库提交 | sha256 | 内容 |
| --- | --- | --- | --- |
| v0 | `1049cbb` (开工基线) | `63cc764b4ca6aaf4f44e9cb879ccf73dd292c2a547d7bc394a1069acaf770553` | ISSUE-08 合并后的文本, 无粗估例外, 无结论四要素, 无对外报告节 |
| v1 | `e977607` (交付版) | `2a194acce53faf9d8c92e18c14d3109aadb9492bd29f3fe18b986c54a19023fe` | 加 "粗估与选型"; "判定" 补齐四要素与第 4/7 问缺口; 新增 "对外报告" |

- 临时项目里 v1 的 `SKILL.md` sha256 与仓库交付版逐字节一致 (`2a194ac...`), 说明演练测的就是提交后的源文件.

## 临时项目

- 路径: `/tmp/orchestra-09/lab`, 练完抄完证据后已删除.
- 提交序列: `3c187b7` (初始材料 + 技能 v0) -> `043713c` (红轮记录, 含会话补计数后的 `bench/two_libs.py`) -> `a4c29c4` (技能 v1) -> `6f44e57` (绿轮 AC-028 记录) -> `6052846` (复位: 记录移出工作区, 保留历史), 绿轮 AC-029 记录只留在未跟踪文件里.
- 内容: `src/` 冻结产品源码 (`report_job.py` 报表导出流水线, `liteidx.py` / `fastidx.py` 两个候选索引库), `bench/` 授权的独立实验脚本 (`rough_once.py`, `alternating_compare.py`, `two_libs.py`), `docs/` 测量材料 (`measure-2000.log`, `measure-gap.log`).
- 数字性质: 全部耗时由 `time.sleep` 模拟, 只证明方法与判定流程, 不代表任何真实产品性能.
- 重建方式: 初始夹具全文在本目录 `red-round/fixtures/` (源文件名里 `/` 换成 `_`), 按 `lab_README.md` 的布局放回即可复现.

## 会话

| 会话名 | 技能版本 | 任务 | 原始转录 |
| --- | --- | --- | --- |
| `bm9-red` | v0 | 红轮: 单次粗估, 两种异常, 两库选型, 结论与 PR 草稿 | `red-round/sessions/bm9-red.jsonl` |
| `bm9-g1` | v1 | 绿轮 AC-028: 粗估声明, 两种异常与重测, 选型边界 | `green-ts001/sessions/bm9-g1.jsonl` |
| `bm9-g2` | v1 | 绿轮 AC-029: 完整材料结论, 缺口材料结论, PR 草稿 | `green-ts002/sessions/bm9-g2.jsonl` |

- 提交渠道: `herdr pane send-text <pane> '<任务>'` + `herdr agent send-keys <名> "alt+\\"`; 状态用 `herdr agent get <名>` 与 `herdr pane read --source recent-unwrapped` 核对.
- 收尾: 三个演练会话所在的 tab 全部关闭, 关闭后 `herdr agent list` 与 `herdr tab list` 里不再有 `bm9-*` 条目; 关闭动作没有触碰其他执行者的会话.

## 上游来源 (只读)

- 地址: `https://raw.githubusercontent.com/cursor/plugins/4382e687a50b8d2c5ce4d141d001186589cff8d5/pstack/skills/benchmark-checklist/SKILL.md` (固定 SHA, 与 ISSUE-06/08 记录同一份).
- 本 ISSUE 未重新下载源文; 借用范围按 DECISIONS F013/F014 记录的 "报告与例外" 段: 粗估可单次仍查第 4/7 问, 异常再查, 选型永远不算粗估, 结论四选一附单位/次数/极差/限制因素, PR 正文一个主数字带单位/前后对照/链接.
- 未借: 提交/发布/自动合并流程, 固定 PR 模板或文风, 统一显著性阈值.

## 借用范围与本 ISSUE 的 AC 对应

- 粗估单次例外与第 4/7 问, 异常继续检查: 覆盖 AC-028-1, AC-028-2.
- 选型永远不走粗估, 按完整对照两侧条件: 覆盖 AC-028-3.
- 结论四选一附单位/次数/极差/限制因素, 缺限制因素或单边未调优或第 4/7 问不可查则无法下结论: 覆盖 AC-029 与 AC-029-2.
- PR 正文一个主数字带单位/前后对照/链接, 完整证据不缩减, 不自动开 PR: 覆盖 AC-029-1.
- 许可: 完整 MIT 版权与许可文本按 ISSUE-13 统一补齐; 补齐前该副本不对外发布.
