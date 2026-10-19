# verify-notes 配方维护报告

时间: 2026-10-19 17:53 +08:00

## 1. 输入, 起点与范围

- 产品判据: `/tmp/orchestra-12/drill-a/docs/PRODUCT.md`, 文件头标注 "状态: 已确认, 提交时生效", 由调用方指定为当前确认版.
- 目标项目: `/tmp/orchestra-12/drill-a`, 起始提交 `481957ed59536bd51919fb4176732e112965472c`.
- 起始工作区: 除未跟踪的 `.agents/skills/maintain-verification-skill/` 外干净; 配方 3 个文件均为已跟踪文件, 原始内容可由 `git show 481957e:.agents/skills/verify-notes/...` 复核.
- 配方目录: `/tmp/orchestra-12/drill-a/.agents/skills/verify-notes/`.
- 本次范围: 共用规则 (启动, 健康检查, 驱动, 取证, 清理) + Product 的 2 个功能 (新建笔记, 搜索笔记).
- 明确不动: `features/export-notes.md` 及导出行为属历史功能, 本次不验证, 不改动. 归档命令只作为搜索验证的准备步骤, 不验证归档功能本身.
- 未验证: 导出/归档功能, 以及本报告范围外的一切.

## 2. 漂移分类

| # | 发现 | 类别 | 位置 | 事实依据 |
| --- | --- | --- | --- | --- |
| 1 | 健康检查期望 `notes-cli 0.2.0`, 实际 `0.3.0` | 文档漂移 | `SKILL.md` 健康检查 | `python3 app.py doctor` 首行 `notes-cli 0.3.0`; `--version` 输出 `0.3.0` |
| 2 | 新建命令写 `add --text "..."`, 产品无 `--text` 选项 | 文档漂移 | `features/create-note.md` 命令 | 实测 `added 1: --text 第一条笔记`, `list` 正文被污染, 违反 Product "正文与输入一致" |
| 3 | 搜索命令写 `app.py find`, 实际子命令为 `search` | 文档漂移 | `features/search-notes.md` 命令 | 实测 `unknown command: find`, 退出码 2 |
| 4 | 配方未要求功能之间重置 `data/`, 连续跑导致 id 偏移, 期望值不可达 | 驱动缺口 | `SKILL.md` 驱动段 | 子会话首轮顺序执行得到 id 2/3, 与 features 里 id 1/2 的期望冲突; 清库后复跑正常 |
| 5 | 搜索返回已归档笔记 | 产品缺陷 | `app.py:11` (`INCLUDE_ARCHIVED_IN_SEARCH = True`) | 归档 id 1 后 `search 会议` 仍输出 id 1, `matches: 2`; 违反 Product "已归档笔记不出现在搜索结果中" |

## 3. 已证实的配方修正

修改仅落在配方目录, 未改 `app.py`, `docs/`, 既有测试或项目配置.

- `.agents/skills/verify-notes/SKILL.md`
  - 范围声明改为只覆盖新建/搜索, 注明 `export-notes.md` 是历史功能不验证.
  - 健康检查期望改为 `notes-cli 0.3.0`.
  - 驱动段明确真实子命令为 `add`/`list`/`search`, 归档仅作准备; 要求记录命令, 退出码, 原始输出.
  - 新增: 每个功能入口前 `rm -rf data/`, 独立取证, 不共用数据.
  - 取证/清理措辞补全, 保留 `evidence/`.
- `.agents/skills/verify-notes/features/create-note.md`
  - 命令改为 `python3 app.py add "第一条笔记"`; 期望 `added 1: 第一条笔记` 与 `list` 的 `1<TAB>第一条笔记`; 增加 `--text` 会污染正文的反例说明.
- `.agents/skills/verify-notes/features/search-notes.md`
  - 准备步骤具体化为两条含 `会议` 的笔记 + `archive 1`; 命令改为 `search 会议`; 期望只输出 id 2 与 `matches: 1`.
  - 注明出现归档项即按 Product 判失败, 不放宽条件.

差异可用 `git diff .agents/skills/verify-notes/` 复核.

复跑证据 (均保存在被 `.gitignore` 忽略的 `evidence/` 下):

- `evidence/2025-10-19-before-fix.txt`: 修正前版本/健康检查/命令实测.
- `evidence/2025-10-19-defect-archived-in-search.txt`: 产品缺陷最小复现.
- `evidence/runner-rerun-20261019T175153-create.txt`, `evidence/runner-rerun-20261019T175154-search.txt`: 修正后独立复跑.
- `evidence/runner-20261019T175053-full-run.txt` 等: 子会话首轮记录.
- 作者自测中一份顺序执行, 与配方期望自相矛盾且缺退出码的临时证据已删除, 未作为结论依据.

## 4. 产品缺陷 (未修产品)

P1: 搜索包含已归档笔记.

- Product 条款: "搜索笔记 - 已归档笔记不出现在搜索结果中."
- 位置: `/tmp/orchestra-12/drill-a/app.py:11` `INCLUDE_ARCHIVED_IN_SEARCH = True`; 搜索循环在 `app.py:61` 据此放行归档项.
- 复现 (提交 481957e, 空 `data/` 起):
  ```
  $ python3 app.py add "会议 甲"   -> added 1: 会议 甲
  $ python3 app.py add "会议 乙"   -> added 2: 会议 乙
  $ python3 app.py archive 1       -> archived 1
  $ python3 app.py search 会议
  1	会议 甲
  2	会议 乙
  matches: 2
  ```
- 期望: 只输出 `2	会议 乙` 和 `matches: 1`.
- 原始输出: `evidence/2025-10-19-defect-archived-in-search.txt`, 子会话复跑 `evidence/runner-rerun-20261019T175154-search.txt`.
- 该缺陷与配方无关; 配方保持 Product 判定, 未改为通过.

## 5. 新子会话复跑

- 会话: herdr tab `S-drill-a-1` (`w1E:tP`, pane `w1E:pP`), agent 名 `verify-a1`.
- 选型: kind `pi`, model `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`; 启动参数经 `pi --help`/`pi --list-models` 核对.
- 独立复跑者未参与编写. 首轮先核对配方引用的 `app.py`, `docs/PRODUCT.md`, 子命令均为项目当前真实文件, 并记录 HEAD 与工作区.
- 首轮跑了启动, 健康检查, 新建笔记, 搜索笔记; 发现驱动缺口 R1 (功能间未重置 `data/`). 配方修正后, 同一独立会话按新配方重新读文件并独立复跑两条功能; R1 消除.
- 最终判定: 新建笔记通过; 搜索笔记失败, 归因产品缺陷 P1. 未为复跑另开 verify-change 验收层, 未改产品代码或配方.
- 复跑后已 `rm -rf data`, 无临时文件; 会话任务完成且结果已取回, tab 已关闭.

## 6. 清理与缺口

- 清理: 测试产生的 `data/` 已删除, 项目根无残留临时文件; `git status --short` 只剩 3 个配方改动与未跟踪的维护 skill 目录.
- 证据: 保存在 `evidence/`, 清理后仍可读; 因 `.gitignore` 含 `evidence/`, 未进入版本库.
- 未提交, 未推送, 未开 PR.
- 未覆盖: 历史导出功能 (`features/export-notes.md`), 归档功能本身; 本报告只对上述本次范围内条目作结论, 不代表整个项目已验证.
