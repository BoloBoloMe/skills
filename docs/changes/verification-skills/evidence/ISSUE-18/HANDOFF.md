# HANDOFF: ISSUE-18 blast-radius 一次性实验边界与视角

## 交付了什么

- `workflow/blast-radius/SKILL.md`:
  - 新增第 5 节 "一次性实验的边界": 非正式 TC 标记, 批准范围, 产品源码/测试/项目配置 (含构建与运行配置) 保护, 按范围清理, 内部结果不顶替成品入口 (产品场景记未运行), 需改冻结目标加计数时停下报缺口, 需新正式接缝时停下交回既有用例确认流程; 带完成标准.
  - 第 4 节接上清理与授权边界, 并指向第 5 节. 原第 5-7 节顺延为 6-8.
  - 全篇改成 "你" 指执行 agent, "我" 指需求方; 被动句改主动 ("被写成这样", "能被人按...", "被下游共享" 三处); 超长句按一句一动作拆开.
- 本目录证据: 红绿两次真实会话的原始报告, 探针脚本, 原始输出, 会话转录, 视角/句长扫描器与红绿扫描结果, 关键词计数, 机械检查日志.
- 没有改 `reference/*.md`, 没有改 benchmark-checklist, 没有改 PRODUCT/TECHNICAL/DECISIONS.

## 每个 AC 对应的证据

| AC | 证据文件 | 关键原始材料 |
| --- | --- | --- |
| AC-024-1 实验标非正式 TC, 产品源码/测试/配置未改, 按批准范围清理 | `TS-001-oneoff-boundary.md` | `green/report.md` 附录 "非正式 TC 记录与清理"; `boundary-grep.txt`; 两仓 `git status` 为空 |
| AC-024-2 内部结果不冒充成品通过 | `TS-001-oneoff-boundary.md` | `green/report.md` "仍未运行的产品场景"; `green/session-br-green.jsonl` 拒绝写入的那一轮; `red/report.md` 事实 10 |
| AC-024-3 需给冻结目标加计数时停止报缺口 | `TS-001-oneoff-boundary.md` | `green/report.md` F7 与附录; `green/out/probe_unreachable.out` |
| AC-024-4 需新正式接缝时交回确认流程 | `TS-001-oneoff-boundary.md` | `green/report.md` 附录 (拒绝环境变量注入口); `green/out/probe_local_record.out`; 红轮部分跑红的说明 |
| 视角与长句已修正, 有扫描证据 | `TS-002-voice.md` | `red/scan-voice.txt` (36 条命中), `machine-checks.log` 第 3 节 (绿 0 条) |

## 跑过的命令与退出码

- `uv run python general/writing-for-llm/check_skill.py workflow/blast-radius/SKILL.md` -> `OK`, exit 0.
- 全角标点扫描 (正则见 `machine-checks.log`), 范围 `workflow/blast-radius/`, 本目录 `*.md`, `setup-fixture.sh` -> 无命中, rg exit 1.
- `uv run python evidence/ISSUE-18/scan-voice.py workflow/blast-radius/SKILL.md` -> exit 0, 0 条.
- 同一扫描器跑 `git show v2:.../SKILL.md` -> exit 1, 36 条 (视角 1, 被动 3, 长句 32).
- `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` -> `7 passed, 18 subtests passed`, exit 0.
- `uv run --with pytest python -m pytest -m "not e2e" -q` -> `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed` (275s), 6 条与开工基线相同, 都是 `general/present/tests/test_browser_session.py` 与 `tests/test_mailbox_admin.py::test_pending_cap_drops_oldest` 的 socket TimeoutError, 未新增失败.
- 明细与原始输出: `machine-checks.log`.

## 会话, 临时项目, 清理

- 待测源: 红 `git show v2:workflow/blast-radius/SKILL.md` (sha256 `59504b51...`), 绿 `workflow/blast-radius/SKILL.md` (sha256 `669de23c...`).
- 宿主: Ubuntu 26.04.1 LTS x86_64, 16 核, herdr 0.9.4, pi 1.3.0.
- 加载方式: 临时项目 `.agents/skills/blast-radius/` 的副本, `pi -a` 一次性项目信任, `/skill:blast-radius` 点名; 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high.
- 会话: 红 `br-red` (tab `w1E:t3V`, pane `w1E:p3V`), 绿 `br-green` (tab `w1E:t3Y`, pane `w1E:p3Y`). 提交渠道 `herdr pane send-text` + `herdr agent send-keys <名> "alt+\\"`.
- 临时项目: 红 `/tmp/orchestra-18/drill` 起始提交 `c342c22`; 绿 `/tmp/orchestra-18/drill-green` 起始提交 `5d83230`. 用 `setup-fixture.sh` 可重建.
- 清理: 两个 tab 已 `herdr tab close`, 之后 `herdr agent get` 均返回 `agent_not_found`; 两仓 `git status --short` 为空; `/tmp/orchestra-18` 在证据抄完后删除 (`rm -rf /tmp/orchestra-18`).

## 缺口, 风险, 未验证

- 红轮只在 AC-024-1 稳定跑红 (没有非正式 TC, 没有批准范围与清理记录). AC-024-2/3 在该模型上自行拒绝冒充与加计数, 没有跑红; AC-024-4 只部分跑红 (自建进程内 `_audit` 替身, 没交回确认流程). 如实记录, 不写成红轮通过.
- 场景 3/4 的触发条件是受控材料: 任务文案写明 "只能改 `src/svc` 加计数" 与 "只能给 `gateway.py` 加注入口". 真实项目里这两类边界不一定同时出现.
- 夹具的成品入口不可达是写死的 `raise`, 属构造条件, 不是真实部署故障; 因此 "产品场景未运行" 是被造出来的.
- 句长扫描按汉字计, 英文标识符不计入 25 字; 口径写在 `scan-voice.py` 顶部.
- 只在单一宿主与 pi 1.3.0 + herdr 0.9.4 上做过, 其他运行时的点名加载与行为未验证; 未运行 `sync-to-pi.py`, 未写任何全局部署副本, 结论不覆盖全局部署已生效.
- `workflow/blast-radius/reference/PROVENANCE.md` 的 H5/H6 属其他 ISSUE, 本 ISSUE 未动.

## 提交

- 实现与证据提交: `feat: ISSUE-18: blast-radius 承接一次性实验边界并统一视角`, 哈希见分支 `issue/18` 顶端 (`git log -1`).
