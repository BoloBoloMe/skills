# HANDOFF ISSUE-11: workflow/create-verification-skill

## 交付物

- 新建技能源码 `workflow/create-verification-skill/SKILL.md`, 用户调用 (`disable-model-invocation: true`), 给已确认 Product 的项目生成本地验证配方: 输入门槛, 本次范围, 生成物形态, 改动边界, 交付前由未参与编写的新会话按 `/skill:verify-<应用名>` 实跑, 交付报告字段.
- 演练证据目录 `docs/changes/verification-skills/evidence/ISSUE-11/`:
  - `README.md` 演练总表 (宿主版本, 源版本指纹, 14 个会话, 临时项目).
  - `TC-016.md`, `TC-017.md`, `TC-018.md`, `TC-104.md` 按用例写证据与结论.
  - `generated/` 六份生成产物原文 (含红的失败产物), `raw/` 会话转录与终端快照, `raw/verifier-evidence/` 两个实跑会话的取证文件, `skill-versions/` v2 与 v3 源码快照.

没有改 `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`, 既有技能, `README.md` 索引 (本 ISSUE 允许范围里没有索引行), 没有写任何全局部署副本, 没有运行 `sync-to-pi.py`, 没有勾选任何复选框.

## 验收标准逐条对应

| 验收标准 | 证据 |
| --- | --- |
| 只凭已确认 Product 和项目事实生成相关范围配方; 缺 Product 时停止 | `TC-016.md`; 原始: `raw/TS-001-green-v2-transcript-i11-gen4.txt`, `raw/TS-001-draft-product-transcript-i11-gen6.txt`; 产物: `generated/TS-001-p1-verify-fixture-SKILL.md` |
| 新子会话跑过全部新改入口, 未实跑项如实保留 | `TC-017.md`; 原始: `raw/TS-002-017-verifier-transcript-i11-ver1.txt`, `raw/ver1-report.md`, `raw/TS-002-017-green-transcript-i11-gen5.txt`, 取证 `raw/verifier-evidence/ver1-p2-20261019-180308/` |
| 项目技能按真实加载入口使用当前文件, 来源可核对; 加载缺口不掩盖 | `TC-017.md` 最后一节, `TC-104.md`; 原始: ver1 转录首条展开块, `raw/TC-104-ver2-startup-diagnostics.txt`, `raw/TC-104-ver2-collision-notloaded-pane.txt` |
| 生成物只落在项目本地验证目录, 构建失败不修产品 | `TC-018.md`; 原始: `raw/TS-003-green-transcript-i11-gen7b.txt`, `raw/TS-003-green-verifier-transcript-i11-ver4.txt`, 取证 `raw/verifier-evidence/ver4-p3-20261019-182528/` |

## 跑过的命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/create-verification-skill/SKILL.md` | 0 | `SKILL.md: OK`, name 与目录一致, 单行 description, 有 `disable-model-invocation: true` |
| `rg -n "[\x{ff0c}\x{3002}...]" workflow/create-verification-skill/` (translate-a-skill 的扫描式) | 1 | 无命中, 即无全角标点. 新增的中文 md 同样无命中 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | 7 passed, 18 subtests passed |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | 6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed |
| 同上, 在 base 提交 `ec9d55f` 的 `git archive` 副本里只跑两个失败文件 | 1 | 同样 6 个失败 (`general/present/tests/test_browser_session.py` 5 条, `tests/test_mailbox_admin.py::test_pending_cap_drops_oldest`), 与工作树一致, 本变更没有新增失败 |

说明: 开工时没有记录基线, 上表最后一行是补做的对照, 用 base 提交的归档副本跑同样 6 条, 失败集合一致.

## 会话与临时项目

- 14 个会话名, tab, 起始提交, 加载版本见 `README.md` 的清单表.
- 临时项目 `/tmp/orchestra-11/{p1-dual,p2-gaps,p3-buildfail,p4-draft}`, 各自独立 Git 仓库, p1 起点 786baa1, p2 起点 4057bb5 (冲突演练前另加 5c0dd32), p3 起点 5d1df07 (复跑前 2b41b8f), p4 起点 44ba7bc.
- 演练用宿主: pi 1.3.0, herdr 0.9.4, 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high, 启动带 `-a`.

## 缺口, 风险与未验证项

1. 演练宿主只覆盖 pi 1.3.0 的一个模型和一个本机环境. 结论只对这个组合成立, 不能外推到其他运行时或全局部署副本.
2. 技能派工那一步靠"操作者开新会话"落地: 演练里生成者只输出派工单, 由操作者按 use-herdr 开会话执行. 生成者自己能否直接开子会话, 本机演练没有覆盖 (会话内没有 herdr 派工权限假设).
3. TC-104 的同名冲突与未加载只在 pi 的项目级发现机制下演练过; 其他运行时的同名规则未验证.
4. 演练暴露并已修的配方质量缺口: 生成的 frontmatter 若 `description` 含未引号冒号会被宿主整份丢弃. 修法只在 v3 复跑里验证过一遍 (p3 项目), 其他项目的生成物没有全部重跑.
5. p2 的第三功能 (历史导入) 真实上游数据始终没有, 实跑用的是同格式临时文件, 该条判据在演练里是"未验证", 不是通过.
6. 网页入口的产品本身没有提交表单, 浏览器内提交这条判据在演练里未验证; 这属于夹具产品的缺口, 不属技能行为.
7. 清理结果: 14 个演练 tab 已逐个关闭 (`herdr tab close`, 收尾后 `herdr agent list` 里没有 i11-* 会话); 无残留 `notes.web` / `ledger-cli` 进程 (`pgrep -af` 只命中自己的命令行); 临时端口全部释放后 `ss -ltnp` 里只剩与本演练无关的 8317 与 8080; `/tmp/orchestra-11` (四个夹具项目), `/tmp/i11-base` (base 归档副本), `/tmp/verify-fixture-*` (实跑取证与临时数据, 已先拷进本目录) 均已删除. 删除后证据目录仍在, 结论不依赖临时项目的存活.

## 提交

本分支 `issue/11`, 提交信息 `feat: ISSUE-11: 新增 create-verification-skill 技能与演练证据`. 提交哈希见同分支的下一个回填提交 (本文件先于提交写好, 无法包含自身哈希).
