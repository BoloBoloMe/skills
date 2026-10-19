# 评审第 3 轮结论

- 评审对象: `main` 上合并后的最终版本, HEAD e6ecc25.
- 基准点: c22e43c (合并前的 main 顶端).
- 两轴正文原样并列如下, 未改写技术结论, 未合并排序.

---

# Standards 轴评审 round 3 (基准 c22e43c...HEAD, HEAD e6ecc25)

变更: 重构 7f958c3 (抽出 `count()`), 合并 8083970, 文档勾选 e6ecc25. 规范来源仍只有 README.md; 无 CODING_STANDARDS/AGENTS/lint 配置; 工具链强制检查仅 `sh tests/run.sh` (其 AC-001/AC-002 两条断言已覆盖本次重构的等价性, 跳过).

## bin/wordcount — hunk `@@ -1,8 +1,13 @@`

已记录规范违规: 无. README 的两种用法 (标准输入 / `--file`) 行为未变, 未触碰任何未记录约定.

判断性发现:
- 上一轮的 Duplicated Code 已消除: 统计表达式现在只有第 5 行一处, 两分支共用.
- 可能是 Mysterious Name (弱). 已读完整文件 (22 行): `count` 未揭示数的是什么, 而项目领域概念是 "词数" (README "统计词数"). 建议 `word_count` 更诚实; 纯命名, 无行为影响.
- 可能是 Middle Man (弱, 不建议改). 已读完整函数体: `count()` 只把 `"$@"` 原样转发给 `awk`, 自身无逻辑. 但它正是以转发换取两处去重, 这正是本次重构目标; 若再内联会退回重复. 保留即可.

遗留说明 (上轮已裁决不采纳, 仅复述一句): `--file` 缺参时仍由 `set -u` 抛 shell 原始报错, 与 `--remote` 分支的自定义报错不一致; 无记录规范约束, 只作提示.

## docs/changes/wordcount/issues/ISSUE-03-dedupe-count.md — hunk `@@ -17,5 +17,7 @@`

已记录规范违规: 无.

判断性发现:
- 判断性 (非基线气味, 已裁决不采纳): "执行" 段继续用 `- [x] 已实现` 而非 `- 状态: ...` 的兄弟文档写法; 一句提示, 不展开.

## 汇总
硬性违规 0; 判断性发现 2 (均为弱基线气味: Mysterious Name, Middle Man), 另有 1 条已裁决提示复述.
发现总数: 2. 最严重: `count` 命名未说明统计对象 (可能是 Mysterious Name), 仅建议, 不影响行为.

---

# Spec 轴评审 (第 3 轮, base c22e43c, HEAD e6ecc25)

diff: `git diff c22e43c...HEAD`; commits: 7f958c3 重构, 8083970 合并, e6ecc25 文档勾选.
规范源: PRODUCT.md (G-001/G-002, BR-001, AC-001..003, NG-001), EXECUTION.md, issues/ISSUE-03-dedupe-count.md.
实测: `sh tests/run.sh` -> ok/0; AC-001 -> 3/0; AC-002 `--file samples/notes.txt` -> 2/0. ISSUE-03 的 "不改变既有行为, 既有用例 AC-001 / AC-002 仍成立" 成立.

## (a) 缺失 / 不完整

1. ISSUE-03 未登记进任务图. ISSUE-03 自己写 "父级: `../EXECUTION.md`", 但 EXECUTION.md 的 "## 任务图" 至今只有一行 "ISSUE-01 ... 覆盖: AC-001, AC-002", ISSUE-02 与 ISSUE-03 都不在其中. 本轮重构在计划文档中无承接记录, 与上一轮 AC-003 无承接属同一类流程缺口 (AC-003 两条与 `words=2` 写死状态未变, 已由你记录待裁决, 此处不重复).

## (b) 范围蔓延

无. diff 仅新增 `count()` 并把 `--file` 与默认分支的两处 awk 换成 `count "$2"` / `count`, 未新增 flag, 未动 tests/run.sh (BR-001 满足), 未碰 `--remote` 分支 (AC-003 行为未变), 未做目录递归 (NG-001 满足).

## (c) 已实现但方式有误

无. 用 c22e43c 的旧版脚本与 HEAD 逐例对照, 结果完全一致: 默认/stdin 3, `--file` 正常 2, 空文件 0, 多行文件 5, `--file -` 走 stdin 得 3, `--file` 缺参退出 2, 文件不存在 awk 报错退出 2, `--remote` 缺配置退出 2 打印 "缺审计配置". 唯一差别是缺参报错行号由 5 变 10, PRODUCT.md 未规定错误信息与行号, 不作发现.

发现总数 1; 最严重: ISSUE-03 未写入 EXECUTION.md 任务图, 计划文档缺本轮任务的承接记录.

---

- Standards 轴发现总数 2, 最严重: `count` 命名未说明统计对象 (可能是 Mysterious Name, 仅建议, 不影响行为); Spec 轴发现总数 1, 最严重: ISSUE-03 未写入 EXECUTION.md 任务图, 计划文档缺本轮任务的承接记录.

## 裁决

- Standards 轴 `count` 命名弱建议 (可能是 Mysterious Name): 不采纳. 理由 = 弱判断性发现, 且同一报告已指出该转发函数保留即达到去重目标, 改名收益小于再走一轮实现循环的成本.
- Standards 轴 Middle Man: 不采纳. 该报告本身已说明保留 (以转发换取两处去重, 内联会退回重复).
- Spec 轴 ISSUE-03 未登记进 EXECUTION.md 任务图: 不采纳为本轮实现项. 理由 = EXECUTION.md 不在本轮授权修改范围内, 列为待用户裁决的缺口; ISSUE-02 同样未登记.
- 结论: 本轮无新的须重构发现项, 评审收敛.
