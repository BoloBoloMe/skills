## 父级
- ../EXECUTION.md (返工轮; SPEC/STANDARDS 记录类发现 F2/F3/F5/F6, H2/H3)

## 执行
- [x] 已完成

## 要交付什么
(a) ISSUE-01 工单 text-mapping 引用 run4 与声明的 run5 依据不一致, 以实际为准更正; (b) ISSUE-02 工单交付证据回填非作者核对结论: check1 报告 21 场景/43 预期/无阻塞/4 疑点, 已归档 docs/changes/to-spec-grilling-and-chinese-ids/evidence/m07-1bc15f612c10aa6e68e33587a01cd2de1ede2fe4/issue-02/check1/, 并勾选已有证据支撑的验收标准项 (注明引用); (c) ISSUE-03 工单同类核查后回填/勾选; (d) EXECUTION.md 执行记录补一行实施前摘要取得时间与命令: 2026-11-27 04:15:45 UTC, find ~/.agents/skills -type f | sort | xargs sha256sum (调度方取得, 231 文件); (e) 标点半角修正: ISSUE-01 约 62-64 行破折号, ISSUE-02 约 64 行顿号 (以 STANDARDS 报告 H2/H3 引用为准).

## 允许范围
- issues/ISSUE-01-tospec-flow-and-cli.md, issues/ISSUE-02-verify-change-method-flow.md, issues/ISSUE-03-navigate-readme-alignment.md, EXECUTION.md, 本工单文件.

## 禁止范围
- 不动产品文件, 不改证据内容本身.

## 验证契约
- 变更类型: 记录修正. 全部引用路径真实存在 (逐一核对), 证据写 /home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-06/run1/.

## 验收标准
- [x] 回填与勾选均有归档证据支撑, 引用路径可访问. (`/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-06/run1/INDEX.md`; 回填引用 `../evidence/m07-1bc15f612c10aa6e68e33587a01cd2de1ede2fe4/{issue-02/check1,issue-03/run1}/`; 路径与标点核对见 `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-06/run1/logs/refs-{before,after}.*`, `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-06/run1/logs/punct-{before,after}.*`)

## 执行结果 (m07-rw-06)
- 改动: (a) ISSUE-01 run4/run5 引用更正; (b) ISSUE-02 回填非作者报告与 4 疑点, 勾选 5 项; (c) ISSUE-03 回填 run1 核对, 勾选 5 项; (d) EXECUTION.md 实施前摘要行; (e) 标点半角修正 (ISSUE-01 3 处 U+2014, ISSUE-02 3 处 U+3001). 未改产品文件与归档证据.
- 证据: `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-06/run1/` (`INDEX.md`, `logs/run4-run5-compare.*`, `logs/issue02-check1-binding.*`, `logs/issue03-run1-binding.*`, `logs/punct-{before,after}.*`, `logs/refs-{before,after}.*`, `logs/diff-check.*`).
- 未完成项: 无验收标准未勾; 非作者全局交叉核对与 README 复核仍属父级集成记录, 本工单未代填.
