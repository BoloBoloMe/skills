# HANDOFF: ISSUE-07 blast-radius

## 交付了什么

- `workflow/blast-radius/SKILL.md`: 用户调用 skill (`disable-model-invocation: true`, 单行中文摘要). 七节: 读变更与自足历史定位, 找关键安全事实, 1 到 5 级证据并说明停在哪级, 可失败证明脚本, 风险与已排除项分开 (含检索空结果如实报范围), 大或宽变更的多模型同题调查 (含单路与能力缺口分支), 五部分交接与中文整理指针.
- `workflow/blast-radius/reference/multimodel.md`: 用 llm-select 选型 + use-herdr 开不同模型会话 + 逐条事实合并的具体步骤, 分歧保留规则, 缺口与单路说明.
- `workflow/blast-radius/reference/report-style-zh.md`: 中文交接整理规则 (短句/大白话, 事实-推断-未证实分开, 删冗但不删证据/风险强度/数量/边界).
- `workflow/blast-radius/reference/source-record.md`: 固定来源 (SHA `4382e68...`, 只读 raw 抓取 HTTP 200), 借用的上游位置与本技能位置对照, 按 F014 记录的借用范围, 没搬入的部分, 行为差异, 许可补齐归 ISSUE-13.
- `docs/changes/verification-skills/evidence/ISSUE-07/`: 三份演练记录, 各次会话原始报告与终端输出, 证明脚本与输出, 9 份会话转录 (jsonl), 夹具脚本与复现日志, 机械检查日志.

## 每个 AC 对应的证据

| AC | 证据文件 | 关键原始材料 |
| --- | --- | --- |
| AC-021-1 定位关键事实并标证据级别 | `TS-001-drill.md` (绿跑), `TS-002-drill.md`, `TS-003-drill.md` | `ts001-raw/green/report.md` 第 2 节; `ts002-raw/report.md` F1-F6 |
| AC-021-2 运行真实代码给出可失败证明 | `TS-001-drill.md` (绿跑) | `ts001-raw/green/work/proof_parse.py` 与 `proof_read.py`, `read-base.log`, `read-head.log` |
| AC-021-3 无法证明标未证实 | `TS-001-drill.md` (绿跑) | `ts001-raw/green/report.md` 事实 C |
| AC-021-4 深入库源码与多跳下游 | `TS-002-drill.md` | `ts002-raw/report.md` F1/F2/F5 与多跳小节的消费者实跑 |
| AC-022-1 五部分交接, 风险与已排除分开, 风险给位置/概率/代价/检查 | `TS-002-drill.md`, `TS-003-drill.md` | `ts002-raw/report.md` 五个 H2; `ts003-gap-raw/report.md` 五个 H2 |
| AC-022-2 搜索无结果如实报告 | `TS-002-drill.md` | `ts002-raw/report.md` 已排除项末条 (3 条检索命令 + 覆盖不到的边界) |
| AC-023-1 大/宽变更多模型同题并合并 | `TS-003-drill.md` 演练一 | `ts003-wide-raw/report.md`, `ts003-wide-raw/merge.md`, `ts003-wide-raw/work/router-a/report.md`, `.../router-b/report.md` |
| AC-023-2 小 diff 改共享格式按宽影响 | `TS-003-drill.md` 演练一 | 同上 (改动 2 文件各 1 行, 跨仓库线格式) |
| AC-023-3 局限且调用方选单路可完成 | `TS-003-drill.md` 演练二 | `ts003-local-raw/report.md` 第 6 节单路声明, `ts003-local-raw/work/scan_callers.py` |
| AC-023-4 只有一款模型时报告能力缺口 | `TS-003-drill.md` 演练三 | `ts003-gap-raw/report.md` 第 1 节能力缺口, 4 级事实未降级 |
| TC-107 自足历史定位与中文交接 | `TS-003-drill.md` 末节, 三份演练记录 | 各报告里的 git 命令与来源限制说明 |

## 跑过的命令与退出码

- `uv run python general/writing-for-llm/check_skill.py workflow/blast-radius/SKILL.md` -> `OK`, exit 0.
- 全角标点扫描 (translate-a-skill 给的 rg 正则, 覆盖 U+FF0C/U+3002/U+FF1B/U+FF1A/U+FF01/U+FF1F/U+3001/U+FF08/U+FF09/U+3010/U+3011; 实际命令写在 machine-checks.log): `workflow/blast-radius` 与 `evidence/ISSUE-07/*.md` 均无命中, rg exit 1 (= 无匹配).
- `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` -> `7 passed, 18 subtests passed`.
- `uv run --with pytest python -m pytest -m "not e2e" -q` -> `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed` (274s). 6 个失败都在 `general/present/tests/test_browser_session.py` 与 `tests/test_mailbox_admin.py::test_pending_cap_drops_oldest`, 均为 socket TimeoutError; `rg -l "blast-radius" tests general` 无命中, 与本 ISSUE 新增路径无关, 属开工时既有环境失败.
- 夹具自检: `bash setup-fixture.sh` 与 `bash setup-variants.sh` 全 PASS (含 "宽影响变体的消费者崩掉 exit 1"), 原文见 `fixture-reproduction.log`.
- 明细见 `machine-checks.log`.

## 会话, 临时项目, 清理

- 宿主: Ubuntu 26.04.1 LTS x86_64, herdr 0.9.4, pi 1.3.0; 会话模型 `cli/deepseek-v4.1-flash-expires-on-0910` thinking high, 加载方式 `pi -a` + `/skill:blast-radius`, 技能副本在临时项目 `.agents/skills/blast-radius/`.
- 会话名: `br-red`, `br-baseline`, `br-green`, `br-ts002`, `br-wide` (另开 `wide-a` = cli/gpt-6.1-sol xhigh, `wide-b` = cli/glm-5.3-flash xhigh), `br-local`, `br-gap`. 提交渠道 `herdr pane send-text` + `herdr agent send-keys <名> "alt+\\"`.
- 临时项目: `/tmp/orchestra-07/drill-ts001-red|green|baseline` (起始 `04ddf93`), `drill-ts002` (`04ddf93`), `drill-ts003-wide` 与 `drill-ts003-gap` (`e807b06`), `drill-ts003-local` (`2b905d2`); 夹具仓库 `payout-service` (`011ec25` -> `04ddf93`) 与 `orders-consumer` (`a47893d`).
- 清理: 子会话由演练会话自己关闭, 四个演练 tab 由编排者关闭, 关闭后 `herdr agent get` 均返回 agent_not_found; 所有演练仓 `git status --short` 为空; `/tmp/orchestra-07` 在证据抄完后删除, 重建方式是两个夹具脚本.

## 缺口, 风险, 未验证

- AC-023-4 用受控材料检验: 本机实际可调用多款模型, "只有一款可用" 通过调用方授权限制模拟, 记录里已标注为受控限制, 不是真实能力缺失.
- 演练只在本机单一宿主与 pi 1.3.0 + herdr 0.9.4 上做过; 其他运行时 (codex/claude 等) 的点名加载与多模型开法未验证.
- `raw-sessions/` 是演练会话的原始转录, 含本机临时路径; 脱敏只针对对外材料, 仓库内证据按原样保留.
- 许可: `reference/source-record.md` 记录了来源与 MIT 版权归属, 完整版权与许可文本 (含免责段) 按 ISSUE-13 统一补齐; 补齐前该副本不对外发布.
- 全量快层的 6 个失败项未修复 (超出本 ISSUE 范围, 且与新增路径无关).

## 提交

- 实现提交: `b57a7bf25d38c917cd0905e283d8eb37b5de9b5e` (`feat: ISSUE-07: 新增 blast-radius 技能与真实会话演练证据`).
- 本文件随其后的 `feat: ISSUE-07: HANDOFF 报告` 提交写入; 分支 `issue/07` 顶端哈希见执行者回复与 `git log -1`.
