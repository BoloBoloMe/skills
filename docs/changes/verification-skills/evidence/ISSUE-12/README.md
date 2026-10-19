# ISSUE-12 证据索引

## 来源与环境

- 待测技能源: `workflow/maintain-verification-skill/`, 工作树 `issue/12`, 基点提交 `ec9d55f0e9cc61b8fa2f607320cf015483fbdee9`.
- 宿主: Ubuntu 26.04.1 LTS, Linux 7.0.0-31-generic x86_64.
- 运行时: pi 1.3.0, herdr 0.9.4.
- 模型与思考档: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 加载方式: 在临时项目 cwd 新建 herdr tab 与 pi 会话, 启动参数加 `-a` 做一次性项目信任, 首条提示词用 `/skill:maintain-verification-skill <任务>` 点名加载. 未改全局配置, 未运行 `sync-to-pi.py`.
- 会话提交渠道: `herdr pane send-text <pane> '<文本>'` 加 `herdr agent send-keys <名> "alt+\\"`, 与 `~/.agents/skills/use-herdr/PI.md` 一致.
- 夹具生成: `uv run python setup-drills.py` (本目录), 根目录默认 `/tmp/orchestra-12/`.
- 临时项目起始提交:
  - `/tmp/orchestra-12/drill-a`: `481957ed59536bd51919fb4176732e112965472c`
  - `/tmp/orchestra-12/drill-b`: `456c360da463ff96e653d62c4d952b4175dca6e3`
  - `/tmp/orchestra-12/drill-c`: `07687cd76af7375ea8bd3ccab6d6611d3002ea6d`

夹具是 notes-cli 小型命令行项目, 含 `app.py`, 项目本地旧配方 `.agents/skills/verify-notes/` 和不同范围的已确认 `docs/PRODUCT.md`. 旧配方故意包含文档漂移和驱动缺口; drill-a 的产品搜索故意包含已归档笔记.

## 演练一览

| 演练 | 目的 | 会话 | 结论 |
| --- | --- | --- | --- |
| drill-a 红态 | 技能不存在时提交同一任务 | `d12-red`, 子会话 `rerun-1` | `/skill:maintain-verification-skill` 未加载, 模型临时自拟流程; 删除了 Product 外的历史导出配方, 并把预期产品缺陷直接告诉复跑子会话. 作为失败基线. |
| drill-a 绿态 | 只按 Product 修订两条功能 | `d12-a`, 子会话 `verify-a1` | 只改新建/搜索两条与共用规则, 历史导出文件未动; 产品缺陷单列; 子会话首轮失败迭代(功能间未重置数据), 修配方后复跑; 清理残留且证据保留. |
| drill-b 绿态 | 改两条 + 新增一条, 健康检查漂移 | `d12-b`, 子会话 `drill-b-verifier` | 改新建/搜索, 新增导出配方, 归档配方未动; 健康检查 `--health` 漂移在配方范围修正后复跑; 三条功能与共用入口均跑过; 产品代码未改. |
| drill-c 缺 Product | 无已确认 Product 时停止 | `d12-c` | 报告输入缺口并停止, 配方零修改, 未用源码或旧配方替代产品范围. |
| drill-a 红态补充 | 技能不存在时无法修订的原始输出 | `d12-red` | `session-d12-red.ansi` 启动技能列表中没有待测技能; 会话内 `cat ~/.agents/skills/maintain-verification-skill/SKILL.md` 返回 NOT FOUND. |

## AC 对应

- AC-019-1: `drill-a-green/maintain-report.md` 第 1, 2, 3 节; `drill-a-green/recipe-diff.patch`; `drill-a-green/project-status.txt`; `drill-a-green/initial-snapshot/` 与 `final-recipe/`. 差异只有 `create-note.md`, `search-notes.md`, `SKILL.md`; `export-notes.md` 不在差异里. 报告明确未覆盖导出/归档, 没有声称整张地图或全项目已验证. 项目无 TECHNICAL.md/EXECUTION.md 也未阻塞.
- AC-019-2: `drill-c-no-product/maintain-report.md` 与 `drill-c-no-product/sessions/d12-c-main.jsonl`. 报告列出 PRODUCT.md 缺失, 停止, 配方文件哈希不变, 并明确看到源码与旧配方差异但未据此修订.
- AC-019-3: `drill-a-green/maintain-report.md` 第 4 节; `drill-a-green/recipe-evidence/2025-10-19-defect-archived-in-search.txt`; `drill-a-green/final-recipe/features/search-notes.md` 仍按 Product 要求排除归档项, 未放宽; `drill-a-green/sessions/verify-a1-subsession.jsonl` 中子会话按 Product 判失败.
- AC-020-1: 两条修改 + 一条新增 + 三个入口复跑见 `drill-b-green/maintain-report.md`, `drill-b-green/recipe-diff.patch`, `drill-b-green/recipe-evidence/{create-note,search-notes,export-notes,shared-rules}.log`, `drill-b-green/sessions/drill-b-verifier-subsession.jsonl`; 无 verify-change 层. 失败迭代与清理见 `drill-a-green/maintain-report.md` 第 5, 6 节, `drill-a-green/recipe-evidence/runner-20261019T175053-full-run.txt` (首轮 id 偏移) 与 `runner-rerun-20261019T175153-create.txt`, `runner-rerun-20261019T175154-search.txt` (修后复跑), 以及清理后的 `project-status.txt`. 该 AC 的失败迭代断言由 drill-a 承接, 修改加新增断言由 drill-b 承接, 两次真实执行合起来覆盖.
- AC-020-2: `drill-b-green/maintain-report.md` 第 "健康检查命令漂移" 节; `drill-b-green/recipe-diff.patch` 只含配方; `drill-b-green/project-status.txt` 显示 `app.py` 未改; `drill-b-green/recipe-evidence/shared-rules.log` 是修正后复跑. 没有把该失败归为产品缺陷.
- 结论边界: 三份维护报告均在"范围/清理与缺口"中写明只覆盖本次功能, 不代表整个项目或历史地图已验证.
- 机械检查: 本目录 `full-fast-suite.txt`, `baseline-master-failing-tests.txt`; 技能检查结果在 HANDOFF 记录.

## 材料说明

- `sessions/*.jsonl`: 对应 pi 会话的原始记录, 从 `~/.pi/agent/sessions/` 复制, 未改写.
- `session-*.ansi`: `herdr pane read --source recent-unwrapped --format ansi` 的原始终端快照, 未改写.
- `recipe-evidence/`: 维护会话或复跑子会话在临时项目中留下的原始运行日志与取证文件.
- `initial-snapshot/`: 临时项目起始提交的 `git archive HEAD` 解包.
- `final-recipe/`: 维护结束后的配方目录副本, 不含运行期 `evidence/`.
- `red/`: 技能不存在时的失败基线材料, 包括会话快照, 项目差异和两次报告.
- `setup-drills.py`: 只生成夹具和初始提交, 不替会话决定行为结果.

## 清理

- 所有演练 tab 已关闭: `d12-red`, `d12-a`, `d12-b`, `d12-c`; 子会话 `rerun-1`, `verify-a1`, `drill-b-verifier` 已由其创建者关闭.
- 临时项目 `/tmp/orchestra-12/drill-a`, `drill-b`, `drill-c` 在证据抄录完成后删除; 基线解包 `/tmp/orchestra-12/baseline-master` 一并删除.
- 未写入 `~/.agents`, `~/.pi` 或任何全局部署副本; 未运行同步脚本; 未自动提交临时项目.
