# m07-rw-06 / ISSUE-06 记录回填证据索引

- 任务标识: m07-rw-06; 回信地址: 01a21b35-1a38-779a-b0e7-7a28184df3ec
- 执行者: 本工单实施会话, pi session `01a21b69-dc6e-70bf-9817-c6b6e981bcaf` (取信守护 running=true)
- 现场: 工作树 `/home/bolo/Workspace/improve.worktrees/ISSUE-06`, 分支 `issue/06`, 开工基点 `1874ede3695a7727271ee4b2e921e913607b2725`
- 性质: 只改记录的文档轮. 未改产品文件, 未改归档证据. 环境见 `logs/environment.txt` (uv 0.13.1, Python 3.11.2, Linux x86_64)
- 提交: `676311a71ef2edf4c81c35077f395c06642da502` `feat: ISSUE-06: 回填非作者核对与实施前摘要并修正标点` (5 文件, 29 insertions, 19 deletions), 只落 `issue/06`, 未推送未合并. 见 `logs/commit.txt`, `logs/post-commit-verify.*`

## 1. 交付项与证据

| 交付项 | 内容 | 证据 |
| --- | --- | --- |
| (a) ISSUE-01 run4/run5 引用更正 | 交付证据节说明 text-mapping 表内 run4 标记与 run5 原件的实际对应 | `logs/run4-run5-compare.{cmd,stdout,exit}` |
| (b) ISSUE-02 回填非作者报告 | check1 路径/绑定/4 疑点/未验证项回填, 5 项验收标准勾选并注引用 | `logs/issue02-check1-binding.{cmd,stdout,exit}` |
| (c) ISSUE-03 回填核对 | run1 原件齐备与一致性核对, 5 项验收标准勾选并注引用 | `logs/issue03-run1-binding.{cmd,stdout,exit}` |
| (d) EXECUTION.md 实施前摘要行 | 取得时间 `2026-11-27 04:15:45 UTC`, 命令, 调度方, 231 文件 | `logs/environment.txt`; 仓库外原件 `pre-impl-snapshot/skills-manifest.sha256` (231 行) |
| (e) 标点半角修正 | ISSUE-01 3 处 U+2014, ISSUE-02 3 处 U+3001 | `logs/punct-before.{cmd,stdout,exit}`, `logs/punct-after.{cmd,stdout,exit}` |
| 引用路径逐一核对 | 允许范围 5 文件的反引号路径解析 | `logs/refs-before.stdout`, `logs/refs-after.{cmd,stdout,exit,unresolved.txt}` |
| 改动范围 | 仅 5 个允许文件; 无证据原件改动 | `logs/changes.patch`, `logs/status-at-commit.{cmd,stdout,exit}`, `logs/diff-check.{cmd,stdout}` |
| 归档树一致 | 工作树归档副本与主仓库归档树逐文件一致 (仅主仓库未跟踪 `run*/tmp` 缓存目录除外) | `logs/archive-copy-diff.{cmd,stdout,exit}` |

## 2. 关键事实

- run4/run5: 同名日志 252 个, 181 个逐字节一致, 71 个仅差运行路径/临时目录/时间戳/预览页文件名 (62 个 `.cmd`, 4 个 `trace-*.events.jsonl`, 5 个 stdout); `.exit` 与 `.stderr` 差异 0; `target-ac-*`/`base-tech-*`/`target-tech-*` 结论性输出一致; 两轮预览页仅 uuid 文件名不同. run5 另有 12 个最终绑定复跑日志.
- check1 绑定: 报告原件 `originals/SKILL.md`/`REVERIFY.md` 的 sha256 与 `git show b260081:...` 逐字节一致; 21 个 `### C` 场景, 43 条 `那么`/`而且` 预期; 核对顶端 `34ae059`, 起止 04:37:11Z/04:38:52Z, 早于集成提交 `1bc15f6` (04:57:27Z); 作业前后 git 状态文件均 0 字节.
- ISSUE-03 run1: `candidate.patch` 与 `git show --format= 70ae157 -- <3 文件>` 逐字节一致 (`cmp` 0); `local-check.md` 6 行; `check_skill.log` = `workflow/navigate/SKILL.md: OK`, `check_skill.exit` = 0.
- 标点: 改动前 6 处命中 (3 个 U+2014 在 ISSUE-01:62-64, 3 个 U+3001 在 ISSUE-02:64); 改动后 5 个允许文件全部 0 命中.
- 路径: 全部实际路径引用解析成功. `refs-at-commit-unresolved.txt` 的 64 个唯一未解析 token 均为提交 SHA, 分支名, 选项/JSON 键, 测试名, 命令名, 关键字文本, 通配计数或占位模式 (`run5/logs/<name>.{cmd,stdout,stderr,exit}`); `workflow/grilling` 为工单明确说明"仓库内无该目录"的否定引用, 非路径主张.

## 3. 未做 / 局限

- 未改产品条文, 未改归档证据, 未推送, 未合并.
- 非作者全局交叉核对与 README 复核仍属父级集成记录, 本工单只核对已有归档是否支撑各验收项, 不代填集成结论.
- ISSUE-02 验收标准第 3 项: check1 只判本切片 21 行, 其余 49 产品行与 2 工程行的语义承接不在本切片; 勾选依据是"计划表 70+3 行未被删减"与"分组盘问未减行", 该范围限制已写入工单引用.
- 提交绑定复跑: `logs/punct-at-commit.*` (TOTAL 0), `logs/refs-at-commit.*` (212 个 OK, 64 个唯一未解析 token 均为上列非路径项), 工作树与提交内同路径文件 sha256 一致 (`logs/post-commit-verify.*`), 提交前后工作树干净 (`logs/status-at-commit.*`).
