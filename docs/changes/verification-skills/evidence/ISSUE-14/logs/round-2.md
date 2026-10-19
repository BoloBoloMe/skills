# 评审第 2 轮结论

- 评审对象: `main` 上合并后的最终版本, HEAD 14338a9.
- 基准点: 3ca85f5 (合并前的 main 顶端).
- 两轴正文原样并列如下, 未改写技术结论, 未合并排序.

---

# Standards 轴评审 (基准 3ca85f5...HEAD, HEAD 14338a9)

规范来源: README.md (仅记录用法与测试入口 `sh tests/run.sh`). 仓库无 CODING_STANDARDS/CONTRIBUTING/AGENTS, 无 lint/formatter 配置. 工具链强制检查仅 tests/run.sh 一条, 其 `--file samples/notes.txt` 用例已覆盖本次改动, 故跳过.

## bin/wordcount — hunk `@@ -2,7 +2,7 @@` (第 5 行)

已记录规范违规: 无. README 只声明 "用 `--file` 读取单个文件", 新实现满足该条, 未触碰任何未记录的约定.

判断性发现:
- 可能是 Duplicated Code. 新增 `awk '{ n += NF } END { print n + 0 }' "$2"` 与默认分支第 15 行 `awk '{ n += NF } END { print n + 0 }'` 逐字相同. 已读完整文件 (17 行, 单个 `case` 块): 两处统计逻辑一致, 后续改计数规则要改两处. 修复: 提取 `count() { awk ... "$@"; }`, 两分支共用.
- 判断性 (非基线气味): 缺参处理不一致. `--remote` 分支对缺失配置显式 `echo ... >&2; exit 2`, 而 `--file` 无第二参数时在 `set -u` 下由 shell 直接抛 "parameter not set". 已读整文件确认这是唯一无自定义报错的分支. 仓库未记录错误处理规范, 因此只作建议.

## docs/changes/wordcount/issues/ISSUE-02-file-flag.md — hunk `@@ -17,4 +17,6 @@`

已记录规范违规: 无.

判断性发现:
- 判断性 (非基线气味): "执行" 段写法与兄弟文档 ISSUE-01 不一致: ISSUE-01 用 `- 状态: 已实现并合并, 见 ...`, 本文件删掉状态字段改为 `- [x] 已实现` 加两行细节. 属观察, 不建议因单次差异建规范.

## 汇总
硬性违规 0; 判断性发现 3 (基线气味 1, 其它 2).
发现总数: 3. 最严重: bin/wordcount 中新旧分支重复同一 awk 统计表达式 (可能是 Duplicated Code).

---

# Spec 轴评审 (base 3ca85f5, diff 3ca85f5...HEAD, 仅 bin/wordcount 的 --file 分支 + ISSUE-02 文档)

已核实: `sh tests/run.sh` -> ok/0; AC-002 `bin/wordcount --file samples/notes.txt` -> 2/0; AC-001 -> 3/0.
PRODUCT.md: "G-002: 从文件统计词数", AC-002-1 "那么 输出为 2, 退出码为 0".

## (a) 缺失 / 不完整

1. AC-003 无任务承接, 也无验收途径. EXECUTION.md 任务图只有 "ISSUE-01 ... 覆盖: AC-001, AC-002", 没有任何 ISSUE 覆盖 AC-003; tests/run.sh 亦无 `--remote` 断言, 而 BR-001 "既有测试 tests/run.sh 不得被改动". 归类: AC-003 主因是环境缺口 (缺 AUDIT_URL / AUDIT_TOKEN 与审计服务, 实测退出 2 打印 "缺审计配置"), 但任务图缺承接属流程缺口, 与上一轮 REPORT 的 "未验证" 状态一致.
2. spec 自身不一致, 导致 AC-003 无法判定: AC-003 标注 `@G-003`, 但 "目标" 只定义 G-001 / G-002, G-003 未定义; 业务规则也无 `--remote` 相关条目. 无目标即无判据.

## (b) 范围蔓延

无. diff 只把 `--file` 的 `echo 0` 换成 `awk '{ n += NF } END { print n + 0 }' "$2"`, 并补 ISSUE-02 文档勾选/合并提交/验证行; 未新增 flag, 未改 tests/run.sh (BR-001 满足), 未做目录递归 (NG-001 满足).

## (c) 已实现但方式有误

3. `--remote` 分支把 `words=2` 写死 (`curl ... -d "words=2"`), 与实际参数无关. AC-003 场景 `--remote alpha beta` 恰好两词, 于是"看似通过", 但任何其他输入仍报 2, 与 "登记一次调用" 并非同一语义. 属既有代码, 非本 diff 引入, 仅在 AC-003 被真正验收时会暴露.

备注 (不计发现): `--file` 缺第二参数或文件不存在时以 shell/awk 原样报错退出 2; spec 未规定错误处理, 故不作发现.

发现总数 3; 最严重: AC-003 无任务承接且无验收途径 (叠加 G-003 未定义, 该标准目前不可判定).

---

- Standards 轴发现总数 3, 最严重: bin/wordcount 中新旧分支重复同一 awk 统计表达式 (可能是 Duplicated Code); Spec 轴发现总数 3, 最严重: AC-003 无任务承接且无验收途径 (叠加 G-003 未定义, 该标准不可判定).
