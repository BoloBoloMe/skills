# 维护报告: verify-notes

日期: 2026-10-19
目标项目: /tmp/orchestra-12/drill-b
起始提交: 456c360 (`fixture: 初始项目与旧配方`)
起始工作区: 仅未跟踪 `.agents/skills/maintain-verification-skill/`, 产品代码无改动.
配方目录: /tmp/orchestra-12/drill-b/.agents/skills/verify-notes
产品判据: /tmp/orchestra-12/drill-b/docs/PRODUCT.md, 文件标注"状态: 已确认", 由调用方指定.
配方原始副本: /tmp/orchestra-12/drill-b-orig/verify-notes (供复核).
旧命令实际表现: /tmp/orchestra-12/drill-b-orig/pre-fix-commands.log

## 本次范围

按 PRODUCT.md 核对 3 个功能:

- 新建笔记
- 搜索笔记
- 导出笔记

共用规则: 启动, 健康检查, 驱动, 取证, 清理.

明确不动: `features/archive-notes.md` (归档属于历史功能, 不在本次产品范围). 该文件 sha256 修改前后均为 `1ed3885c...`, 未改动也未验证. 搜索准备中调用 `archive` 只为造出已归档数据, 不作为归档功能的验收.

## 已证实修正

### 1. 健康检查命令漂移 (文档漂移)

- 位置: `SKILL.md` 的"健康检查".
- 原写法: `python3 app.py --health`, 期望输出 version 与 data_path.
- 实际: `unknown command: --health`, 退出码 2. 当前健康检查子命令是 `doctor`.
- 修正: 改为 `python3 app.py doctor`, 写明期望的三行输出和退出码 0.
- 证据: pre-fix-commands.log; 复跑 shared-rules.log.

### 2. 新建笔记命令参数漂移 (文档漂移)

- 位置: `features/create-note.md`.
- 原写法: `python3 app.py add --text "第一条笔记"`.
- 实际: `add` 没有 `--text` 选项, 该参数被当成正文, 存成 `--text 第一条笔记`, 与 PRODUCT.md "正文与输入一致" 不符.
- 修正: 改为 `python3 app.py add "第一条笔记"`, 补期望输出与 list 首行校验.
- 证据: pre-fix-commands.log; 复跑 create-note.log.

### 3. 搜索子命令与期望输出漂移 (文档漂移)

- 位置: `features/search-notes.md`.
- 原写法: `python3 app.py find 会议`, 只验证"输出只含未归档的匹配项".
- 实际: `unknown command: find`, 退出码 2; 真实子命令是 `search`. 且 `search` 末尾会输出 `matches: N`, 原期望没提.
- 修正: 改为 `search 会议`, 写明命中行, 排除已归档编号, 以及 `matches: 1` 汇总行.
- 证据: pre-fix-commands.log; 复跑 search-notes.log.

### 4. 导出笔记入口缺失 (驱动缺口)

- 位置: `SKILL.md` 功能入口列表; 无 `features/export-notes.md`.
- 实际: PRODUCT.md 要求导出笔记, 但配方没有任何入口, 后来者无法按配方到达 `export` 并观察结果.
- 修正: 新增 `features/export-notes.md` (准备, 命令, 期望输出, 行数一致校验); 入口列表加入导出笔记. 同时把 `SKILL.md` 过时的来源描述 ("旧配方, 覆盖多个历史功能") 改为当前三个功能, 并补充驱动约定 (`add` 无 `--text`, 搜索是 `search`, 每步先清 `data/`) 与取证文件名约定.
- 证据: 复跑 export-notes.log.

## 产品缺陷

无.

已按 PRODUCT.md 核对: 新建后正文与输入一致; 搜索返回正文含关键词的笔记且排除已归档; 导出文件存在, 行数与 list 行数一致. 三者实际行为均满足要求.

一个不构成缺陷的事实差异: 已归档笔记在 `list` 行尾带 ` [archived]`, 在导出文件中不带该后缀. PRODUCT.md 只要求导出行数与 list 行数一致, 未要求后缀, 故不列为产品缺陷, 也未据此改配方判定条件.

## 新子会话复跑

- 会话: herdr tab `S-drill-b-verify`, agent `drill-b-verifier`.
- 配置: pi, 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动参数 `--model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high --approve`.
- 独立性: 新会话, 未参与配方编写; 只读配方并执行, 未改配方或产品代码 (只写 evidence).
- 加载来源核对: 子会话记录项目 HEAD 456c360, 配方文件 sha256 与当前工作区一致:
  - SKILL.md `ac11b495...`
  - create-note.md `62e31fa0...`
  - search-notes.md `bb6adb08...`
  - export-notes.md `a3192400...`
  - app.py `e595dca7...`, 路径 `/tmp/orchestra-12/drill-b/app.py`, 与配方指向一致.
- 复跑覆盖: 启动, `doctor` 健康检查, 新建笔记, 搜索笔记, 导出笔记; 共用准备与清理合并执行.
- 结果: 三项功能全部通过, 共用规则通过. 每功能从删除 `data/` 开始.
- 取证 (保留, 已被 .gitignore 忽略):
  - `.agents/skills/verify-notes/evidence/shared-rules.log`
  - `evidence/create-note.log`
  - `evidence/search-notes.log`
  - `evidence/export-notes.log`
  - `evidence/export.tsv`
- 复跑未出现失败迭代; 子会话额外核查了"归档后导出仍含该笔记", 行数仍与 list 一致.

## 清理与缺口

- 已删除项目根 `data/`; 已删除 `/tmp/verify-notes-export.tsv` 与附加核查用的 `/tmp/verify-notes-export-archived.tsv`; 清理后 `data/` 不存在.
- 保留了 evidence 供复核; 配方原始副本与旧命令日志保留在 `/tmp/orchestra-12/drill-b-orig/`.
- 创建的 herdr tab 已关闭, 未动其他会话或实例.
- 未验证: 归档功能本身 (历史功能, 不在产品范围); PRODUCT.md 之外的行为.
- 缺 TECHNICAL.md / EXECUTION.md, 启动, 版本, 子命令, 数据位置均从 app.py, PRODUCT.md 和实际运行读取, 未因此阻塞.
- 未提交, 未推送, 未开 PR. 配方改动仍在工作区, 等待调用方处理.
- 结论只覆盖上述 3 个功能与共用规则; 不代表整个项目或历史地图健康.
