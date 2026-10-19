# ISSUE-12 HANDOFF

## 交付

- 新建 `workflow/maintain-verification-skill/SKILL.md`: 必需输入与缺 Product 停止, 按 Product 定范围, 三类漂移分类, 配方范围内修正, 新子会话复跑全部新改内容与入口, 失败迭代清理, 结论边界报告.
- 新建 `workflow/maintain-verification-skill/reference/drift-classification.md`: 三类判据, 健康检查漂移与产品回归的区分, 共享实例与证据底线.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-12/`: 4 次真实 pi 演练, 夹具生成脚本, 原始会话记录, 项目快照, 差异与运行日志.
- 未改既有技能, 未改 PRODUCT.md / TECHNICAL.md / DECISIONS.md / ISSUE 文件, 未勾选任何复选框, 未运行 `sync-to-pi.py`, 未写全局部署副本, 未自动提交临时项目.

## 每个 AC 的证据

| AC | 证据文件 | 说明 |
| --- | --- | --- |
| AC-019-1 | `evidence/ISSUE-12/drill-a-green/maintain-report.md`, `recipe-diff.patch`, `project-status.txt`, `initial-snapshot/`, `final-recipe/` | Product 只覆盖新建/搜索; 差异只有这两条和共用 `SKILL.md`; `export-notes.md` 未改; 无 TECHNICAL/EXECUTION 未阻塞; 报告声明不覆盖历史功能且不声称全项目已验证 |
| AC-019-2 | `evidence/ISSUE-12/drill-c-no-product/maintain-report.md`, `sessions/d12-c-main.jsonl` | 无 Product, 报告缺口并停止; 配方文件哈希不变; 明确看到源码与旧配方差异但未据此修订 |
| AC-019-3 | `evidence/ISSUE-12/drill-a-green/maintain-report.md` 第 4 节, `recipe-evidence/2025-10-19-defect-archived-in-search.txt`, `final-recipe/features/search-notes.md`, `sessions/verify-a1-subsession.jsonl` | 产品缺陷单列; 配方仍按 Product 要求排除归档项, 未放宽; 子会话按 Product 判搜索失败 |
| AC-020-1 | `evidence/ISSUE-12/drill-b-green/maintain-report.md`, `recipe-diff.patch`, `recipe-evidence/{create-note,search-notes,export-notes,shared-rules}.log`, `sessions/drill-b-verifier-subsession.jsonl`; 失败迭代与清理见 `drill-a-green/maintain-report.md` 第 5, 6 节, `recipe-evidence/runner-20261019T175053-full-run.txt`, `runner-rerun-20261019T175153-create.txt`, `runner-rerun-20261019T175154-search.txt`, `project-status.txt` | drill-b: 修改两条 + 新增导出一条, 子会话跑新建/搜索/导出和共用入口, 无 verify-change 层. drill-a: 子会话首轮因功能间未重置数据失败, 修配方后复跑, 清理 `data/` 后证据仍在 |
| AC-020-2 | `evidence/ISSUE-12/drill-b-green/maintain-report.md` 健康检查节, `recipe-diff.patch`, `project-status.txt`, `recipe-evidence/shared-rules.log` | 健康检查 `--health` 漂移只改配方并复跑; `app.py` 未改; 未归为产品缺陷 |
| 结论边界 | 三份维护报告的"本次范围/清理与缺口"节 | 均写明只覆盖本次范围, 不代表整张历史地图或全项目已验证 |

## 运行命令与结果

- `uv run python setup-drills.py`: 0; 生成 `/tmp/orchestra-12/drill-{a,b,c}` 初始提交.
- herdr 建 tab/启动会话/提交任务: 0; 会话名 `d12-red`, `d12-a`, `d12-b`, `d12-c`; 子会话 `rerun-1`, `verify-a1`, `drill-b-verifier`.
- 加载方式: cwd 为临时项目, `herdr agent start <名> --kind pi --pane <pane> -- --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`; 首条提示词 `/skill:maintain-verification-skill <任务>`, 用 `pane send-text` + `agent send-keys alt+\` 提交.
- `uv run python general/writing-for-llm/check_skill.py workflow/maintain-verification-skill/SKILL.md`: 0, 输出 OK.
- 全角标点扫描: `rg -n '[\x{ff0c}...]' workflow/maintain-verification-skill docs/changes/verification-skills/evidence/ISSUE-12` (排除原始会话/日志/夹具快照): 无命中, rg 退出 1.
- 英文残留人工审查: 保留 `PRODUCT.md`, `TECHNICAL.md`, `EXECUTION.md` (输入文件名), `Product` (产品要求术语), `use-herdr`, `verify-change`, `maintain-verification-skill` (技能名), `skill`, `agent`, `helper`, `PR` (交付动作与目标产物类型), frontmatter 字段名; 无解释性英文句子.
- `uv run --with pytest python -m pytest general/writing-for-llm/tests -q`: 0; 7 passed, 18 subtests passed.
- 全量快层 `uv run --with pytest python -m pytest -m "not e2e" -q`: 1; 6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed; 原始输出 `evidence/ISSUE-12/full-fast-suite.txt`.
- 同一失败集合的基线: 从 `ec9d55f` 用 `git archive` 解包到 `/tmp` 后跑 `general/present/tests/test_browser_session.py` 与 `tests/test_mailbox_admin.py`: 1; 6 failed, 71 passed, 与上条失败集合一致; 原始输出 `evidence/ISSUE-12/baseline-master-failing-tests.txt`.
- 未新增测试脚本或统一评测平台; `setup-drills.py` 只生成夹具.

## 会话与临时项目

- 起始源: `workflow/maintain-verification-skill/` @ `ec9d55f0e9cc61b8fa2f607320cf015483fbdee9`; 宿主 Ubuntu 26.04.1 LTS, Linux 7.0.0-31-generic x86_64; pi 1.3.0; herdr 0.9.4.
- `drill-a` 起始提交 `481957ed59536bd51919fb4176732e112965472c`: 红态 `d12-red` 与 `rerun-1`, 绿态 `d12-a` 与 `verify-a1`.
- `drill-b` 起始提交 `456c360da463ff96e653d62c4d952b4175dca6e3`: `d12-b` 与 `drill-b-verifier`.
- `drill-c` 起始提交 `07687cd76af7375ea8bd3ccab6d6611d3002ea6d`: `d12-c`.
- 所有 tab 已关闭; 临时项目与基线解包已删除; 原始材料已抄到 `evidence/ISSUE-12/`; 临时项目未提交, 未推送.

## 缺口与风险

- AC-020-1 的"两条修改 + 一条新增"与"一次失败迭代"分别由 drill-b 和 drill-a 承接, 没有在一次维护事件里同时发生; 两次都是真实执行, 证据见上表. 没有为了合并场景而伪造失败.
- drill-a 的失败迭代部分来自维护者自测和子会话首轮运行; 首轮日志保留在 `runner-20261019T175053-full-run.txt`, 修后复跑日志单独保留.
- drill-b 的健康检查漂移被维护者在派工前发现并修正, 子会话没有失败迭代; AC-020-2 的"配方范围内修正后重跑"仍由该次真实复跑证明.
- 夹具是 notes-cli 最小项目, 只验证单实例和本地数据目录; 未覆盖多实例共享, 端口争用, 权限不足等分支.
- 生成配方的 frontmatter 由维护会话写入, 未单独用 `check_skill.py` 验证; 通用技能自身的 frontmatter 已通过.
- 证据里的 `sessions/*.jsonl` 与 `*.ansi` 是原始会话快照, 含宿主路径和提示词原文, 作为审计材料保留.
- 未在真实产品项目上演练; 结论只覆盖临时夹具.

## 提交哈希

- 交付内容提交: `54c1f5c579d5a5d70094d8cb1ba073083cf21766` (`feat: ISSUE-12: 新增验证配方维护技能与真实演练证据`).
- 本 HANDOFF 的哈希回填写在随后一个 docs 提交里, 因为文件无法包含自身提交的哈希; 分支最终 HEAD 以 `git log -1` 为准.
- 分支 `issue/12`; 回填后工作区应干净.
