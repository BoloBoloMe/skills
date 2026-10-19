# HANDOFF: ISSUE-08 benchmark-checklist 收益上限, 端到端, 基线与一次性实验边界

## 交付了什么

- `workflow/benchmark-checklist/SKILL.md` 增量三节, 都带完成标准:
  - "一次性实验的边界": 标非正式 TC, 只动独立实验脚本与临时数据, 按批准范围清理, 内部结果不冒充成品通过, 需给冻结目标加计数或需新正式接缝时停下报缺口或交回用例确认流程; 影响调查类脚本指向 `workflow/blast-radius/SKILL.md`, 不重复实现.
  - "收益上限与端到端": 用占比算上限 `r / (1 - r)` (10% 的段全删最多约 11%), 超限当测量错误线索查缓存/空操作/错误响应/计时区外计算, 微结果补测端到端并报占比, 分析器数字不进报告, 数字没动先查限制因素, 负载生成器饱和不当应用结果.
  - "基线与脚本固定前": 基线用于规划前审测量方法与适用条件; 待固定脚本必须有错误数与工作量输出并重跑; 需改冻结产品源码时只报缺口, 不认可固定.
- `description` 同步补上三项覆盖范围, 仍是单行人类摘要, `disable-model-invocation: true` 保留.
- 本目录证据: 红轮 2 份会话记录 5 份产物, 绿轮 3 份记录与全部原始输出, 6 份会话转录, 演练脚本与差异, 机械检查日志.

## 每个 AC 对应的证据

| AC | 证据文件 | 关键原始材料 |
| --- | --- | --- |
| AC-030-1 占比算上限, 不把局部加速说成整条路径收益 | `TS-001.md` | `green-ts001/docs/green1.md` 2.1-2.4; `green-ts001/docs/raw/task1-*` |
| AC-030-2 超上限当测量错误线索, 查缓存/空操作/错误 | `TS-001.md` | `green1.md` 3.1-3.3; `raw/task2-noop-recheck-21rounds.log` |
| AC-030-3 微结果补测端到端 (真实数据与并发) 并报占比 | `TS-001.md` | `green1.md` 4.1-4.6; `raw/task3-e2e-ab-c1-21rounds.log`, `raw/task3-e2e-proc.log` |
| AC-030-4 分析器数字不进报告, 限制因素单独给 | `TS-001.md` | `green1.md` 8.1-8.3; `raw/task4-profile.log` |
| AC-030-5 数字没动先查限制因素再判优化 | `TS-001.md` | `green1.md` 9.1-9.4; `raw/task5-flat-compare.log`, `raw/task5-flat-compare-fixed.log` |
| AC-030-6 生成器饱和不当应用结果, 换生成方式重测 | `TS-001.md` | `green1.md` 10.1-10.3; `raw/task6-loadgen-*.log` |
| AC-031-1 基线用于规划前先审测量方法与适用条件 | `TS-002.md` | `green-ts002/docs/green2.md` 1 节 |
| AC-031-2 固定脚本前补错误数与工作量并重跑 | `TS-002.md` | `green2.md` 2 节; `green-ts002/bench/team-entry.diff`, `team_entry_alternating_final.txt` |
| AC-031-3 需改产品源码时只报缺口, 不认可固定 | `TS-002.md` | `green2.md` 3 节 |
| AC-024-1 一次性实验标非正式 TC, 不改源码/测试/配置, 按批准范围清理 | `TS-003.md` | `green-ts003/docs/green3.md` 1, 6 节; `green-ts003/bench/oneoff_authz.py` |
| AC-024-2 内部结果不冒充成品通过 | `TS-003.md` | `green3.md` 2 节 |
| AC-024-3 需给冻结目标加计数时停止报缺口 | `TS-003.md` | `green3.md` 3 节 |
| AC-024-4 需新正式接缝时交回确认流程 | `TS-003.md` | `green3.md` 4 节 |

红轮 (v0 技能) 原始产物: `red-round/docs/task1.md` 到 `task5.md`, 会话转录 `red-round/sessions/bm-red.jsonl`, `bm-red2.jsonl`, bench 改动 `red-round/bench-diff/`.

## 跑过的命令与退出码

- `uv run python general/writing-for-llm/check_skill.py workflow/benchmark-checklist/SKILL.md` -> `OK`, exit 0 (v1, v2, v3 与交付版各跑一次).
- 全角标点扫描 `rg -n "[\x{ff0c}\x{3002}\x{ff1b}\x{ff1a}\x{ff01}\x{ff1f}\x{3001}\x{ff08}\x{ff09}\x{3010}\x{3011}]" workflow/benchmark-checklist/` -> 无命中, rg exit 1.
- 全角标点扫描本目录 `*.md` -> 1 处命中, 在 `red-round/docs/task5.md` 第 68 行, 那是红轮会话自己写下的演练产物 (原文照录的原始材料), 不是本 ISSUE 撰写的正文; 按原始材料保留, 不改写. 我撰写的中文文档无命中.
- `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` -> `7 passed, 18 subtests passed`.
- `uv run --with pytest python -m pytest -m "not e2e" -q` -> `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed` (274s). 6 个失败在 `general/present/tests/test_browser_session.py` (5 个) 与 `tests/test_mailbox_admin.py::test_pending_cap_drops_oldest` (1 个), 都是 socket TimeoutError; `rg -l "benchmark-checklist" tests general` 无命中, 与本 ISSUE 新增路径无关, 属开工时既有环境失败, 与 ISSUE-07 记录的失败集合一致.
- 上游只读获取: `curl -sS -m 20 -o /tmp/pstack-bench-issue08.md -w "http=%{http_code}\n" <raw 地址>` -> HTTP 200, 5002 字节, `sha256=ba109e96c8f6c1c391baccf19e5d11e14370df7b3f2605e1572cd565a6c0fca0`.
- 明细见 `machine-checks.log`.

## 会话, 临时项目, 清理

- 宿主: Ubuntu 26.04.1 LTS, 16 核, herdr 0.9.4, pi 1.3.0; 会话模型 `cli/deepseek-v4.1-flash-expires-on-0910` thinking high, 启动参数 `-a` (一次性项目信任).
- 加载方式: 临时项目 `.agents/skills/benchmark-checklist/` 里的待测副本 + `/skill:benchmark-checklist <任务>`; 演练期间全机只有这一份同名技能目录.
- 会话名: `bm-red` (v0, 红轮任务 1-3 与 4-7), `bm-red2` (v0, 红轮上限算式), `bm-g1` (v1, AC-030), `bm-g2` (v2, AC-031), `bm-g3` (v3, AC-024).
- 提交渠道: `herdr pane send-text` + `herdr agent send-keys <名> "alt+\\"`; 状态与原始输出用 `herdr agent get` / `herdr agent read` 读取.
- 临时项目: `/tmp/orchestra-08/lab`, 提交 `a36278b` (v0) -> `2f89d4a` (v1) -> `86d5a0d` (v2) -> `28adf14` (v3).
- 清理: 五个演练会话所在 tab 全部关闭, 关闭后 `herdr agent list` 只剩编排者与其他执行者的会话; `/tmp/orchestra-08` 在证据抄完后删除 (`rm -rf /tmp/orchestra-08`); 逐轮复位材料用 `git restore .` 加删除未跟踪文件, 没有用 `git checkout -- <path>` 或 `git reset --hard`.

## 缺口, 风险, 未验证

- 红轮覆盖不完整: AC-030-1 的上限算式在红轮两次都只给直接占比 (10.2%), 不给 `r/(1-r)` (11.3%), 算跑红; AC-030-3 的红轮第一次任务缺并发测量. AC-030-2/4/5/6 与 AC-031 三条在该模型上红轮没有跑红 (该模型自行做了大部分核查), AC-024-4 只部分跑红 (红轮自建运行时注入口, 没交回确认流程), 如实记录, 不写成红轮通过.
- 演练数字全部来自 `time.sleep` 与 CPU 忙等模拟的受控材料, 只证明方法, 不代表真实产品性能; 删除整段归一化由 bench 内复刻路径实测 (产品冻结), 复刻件与真实入口校准差 <0.1%.
- 线程并发在 200/5000 行出现超过上限的 13.99%-17.10%, 根因是 GIL 争用放大, 会话已标为无法下结论并用独立进程重测; 这条是演练里真实的超限处理案例, 也说明并发模型不同会改变占比.
- v3 轮临时项目里残留了上一轮的 `docs/green2.md` (复位时漏删), 与 AC-024 场景无关.
- 只在单一宿主 (16 核) 与 pi 1.3.0 + herdr 0.9.4 上做过; 其他运行时的点名加载未验证. 未运行 `sync-to-pi.py`, 未写任何全局部署副本, 结论不覆盖全局部署已生效.
- 完整 MIT 许可文本与逐项差异记录按 ISSUE-13 统一补齐; 补齐前该副本不对外发布.

## 提交

- `6dbdd11` feat: ISSUE-08: benchmark-checklist 增加收益上限与端到端切片
- `590f9cd` feat: ISSUE-08: benchmark-checklist 增加基线与脚本固定前检查切片
- `2828254` feat: ISSUE-08: benchmark-checklist 增加一次性实验边界切片
- 证据与报告提交哈希见分支 `issue/08` 顶端与本文件所在的最后一次提交.
