## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
把"容器里代码放在哪个目录"的文档措辞改成与代码事实一致 (用户裁决: 改文档, 不改代码).

代码事实 (落笔前必须自己复核, 不要照抄本 issue):
- `scripts/swt.py` 的 `assert_container_clone` (约 2884 行) 用 `clone_dir = f"/home/bolo/Workspace/{branch}"`, 且同一个 `branch` 传给 `git clone -b`;
- `agent_env_facts` (约 1235 行) 的 `code_path` 用同一个公式;
- `birth()` 里的 `branch = resolve_mother_branch(repo, args.branch)` 原样返回分支名 (约 579 行), 所以分支名含 `/` 时容器内路径是嵌套目录;
- `tests/test_swt_m12.py` 的断言与之一致 (约 874/878/923 行用 `state["mother"]["branch"]`).

要改的文档 (只改这一处口径的措辞, 不动任何决策语义):
1. `docs/language/UBIQUITOUS_LANGUAGE.md` 的 "完美复刻" 条: 现在写 "代码固定 `~/Workspace/<母体目录名>` (规范化目录名, 非原始分支名)", 改成与代码事实一致的说法 (容器内代码目录 = `~/Workspace/<目标分支名>`, 分支名原样, 含 `/` 时为嵌套路径).
2. `docs/changes/swt-container-env-docs/DECISIONS.md` 的 D008 条目 2 (现写 "代码在 ~/Workspace/<母体目录名>, 是宿主母体分支的克隆"): 同一口径同步; 只动这一句, 不动条目其余内容与任何其他决策.
3. `workflow/use-sandbox-worktree/agent-prompts/ENV.md` 条目 2: 与上同步 (它是逐字采用 D008 的产物, 必须与账本一致).
4. 若 `docs/changes/swt-container-env-docs/issues/ISSUE-02-env-docs-generator.md` 或任何测试文件里也钉了同一措辞 (例如断言 ENV.md 内容), 一并同步.
## 覆盖依据
- 用户裁决 (2026-10-14): "代码目录那条改文档"
- `../../swt-container-env-docs/UNAUTHORIZED_DECISIONS.md` UD-013 第 1 条 (评审的硬性违规发现) 与 UD-016
## 相关决策
- `docs/changes/swt-container-env-docs/DECISIONS.md` D008 (只改条目 2 的措辞), D015 (两环境母本允许不一致, 与本改动无关)
## 允许范围
- `docs/language/UBIQUITOUS_LANGUAGE.md`; `docs/changes/swt-container-env-docs/DECISIONS.md` (仅 D008 条目 2 的措辞); `docs/changes/swt-container-env-docs/issues/ISSUE-02-env-docs-generator.md` (仅同一措辞); `workflow/use-sandbox-worktree/agent-prompts/ENV.md` (仅条目 2); `tests/test_env_docs.py` / `tests/test_swt_stage_env.py` (仅当它们钉死了旧措辞)
## 禁止范围
- 改代码 (`scripts/swt.py` 等一律不动); 改任何决策的语义/状态/约束性; 改 PRODUCT/TECHNICAL/EXECUTION; 改宿主侧母本 `agent-prompts/` (仓库根那份, 它与容器代码目录无关)
## 代码定位提示
- 旧措辞检索: `grep -rn "母体目录名" docs/ workflow/ tests/`
- 复核用: `scripts/swt.py` 的 `resolve_mother_branch` / `assert_container_clone` / `agent_env_facts`; `tests/test_swt_m12.py` 的相关断言
## TDD 切片
- 非代码特例, 无 TDD 切片. 验证 = 检索 + 内容断言 + 机检 (见验证入口).
## 验证入口
- `grep -rn "母体目录名" docs/ workflow/ tests/` 不再出现在这个口径上 (若别处仍有该词但语义不同, 逐条说明为什么保留)
- `grep -rn "Workspace/<目标分支名>\|Workspace/<branch>\|分支名原样" docs/ workflow/` 能看到新措辞
- `uv run python -m unittest tests.test_env_docs tests.test_swt_stage_env -v` 全过
- `cd docs/changes/swt-container-env-docs && uv run /home/bolo/.agents/skills/to-spec/check-ac.py PRODUCT.md` 与 `check-tech.py TECHNICAL.md` 退出码 0
- 账本 D008 条目 2 与 `ENV.md` 条目 2 逐字一致 (可用 diff 或逐字比对证明)
## 风险提示
- 这是 spec 级文档的措辞改动, 必须忠实于代码事实; 若复核发现代码事实与本 issue 的描述不符 (例如路径还有别的来源), 停下报告, 不要凭 issue 文字硬改
- 改 ENV.md 会改变容器提示词文本; 这是用户已批准的措辞对齐, 不是内容增删
## 停止条件
- 复核发现代码事实与"分支名原文"结论不符; 或发现需要改代码才能自洽时, 停下报告
## 适合 AFK 的原因
- 用户已选定方向, 只剩忠实落笔与核对
## 验收标准
- [ ] 三处 (领域词汇/账本条目 2/ENV.md 条目 2) 口径一致且与代码事实一致; 相关测试与机检全过; 无其他文档被误改
## 被阻塞于
- 无
