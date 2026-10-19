# TS-002 证据: maintain 判据单一来源

接缝: maintain 的分类判据与参考文件之间的职责边界. 红态断言: 同一判据在 `SKILL.md` 与 `reference/drift-classification.md` 两处各写一份; 绿态断言: 判据只在一处, 另一处只留例子.

## 红态 (基点 `5c21b0b`)

- `raw/red-source-duplication.txt` 原样摘录两处:
  - `workflow/maintain-verification-skill/SKILL.md` 第 32-34 行: 文档漂移, 驱动缺口, 产品缺陷三条判据.
  - `workflow/maintain-verification-skill/reference/drift-classification.md` 第 9-11 行: 同一三类判据的表格 (类别 / 判据 / 处理), 第 13 行再给一次"先核对项目事实, 再判断产品"的顺序.
- 源哈希: `SKILL.md` `181a88a39beab1e093f744b2f8997390695b92a556a878e26ff61edeae26f38e`, 参考文件 `403187355afb1047b6e6067f841a0cc9d49240601ce91c155ef9d138544b2503` (`raw/red-source-sha256.txt`).
- 结论: 红态成立, 同一判据两处维护, 与评审 J1 的描述一致.

## 绿态 (本 ISSUE 改动后)

- 判据只保留在 `SKILL.md` 的 `## 分类漂移`: 第 32-34 行三条, 并在段首声明"判据以本节为准". `raw/green-criteria-location.txt` 记录了该 grep 结果.
- 参考文件删掉"三类判据"表与"判据顺序"行, 只留 `## 常见混淆` (5 条样例) 与 `## 证据底线`; 段首写明"本文件只放容易混淆的样例和证据底线. 三类判据与处理方式以 ../SKILL.md 的 `## 分类漂移` 为准, 这里不重复写". 对判据表与判据顺序的 grep 无命中 (rg 退出 1, 见同一文件).
- 差异证据: `diffs/drift-classification.patch` (删除判据表与顺序, 改写混淆样例为具体例子) 与 `diffs/maintain-skill.patch` (段首改为"判据以本节为准", 参考文件只指向样例).
- 行为回归: 绿态 maintain 会话仍能正确分类. 它把健康检查 `doctor` 不存在, 数据目录 `notes.txt`, `add --text` 参数错误归为文档漂移, 把缺退出码/末尾断言/取证目录/清理范围归为驱动缺口, 把 `export` 归为不修, 未把任何一条直接归为产品缺陷 (`raw/maint-green/maint-green-step1-pane.txt` 的分类表). 该会话读过一次参考文件, 只用来对照混淆样例 (`raw/green-criteria-usage.txt`).
- 结论: 绿态成立. 判据只剩一份, 参考文件只放例子与证据底线, 分类行为没有退化.

## 判定

AC-2 "判据只保留一份, 有 diff 证据" 满足: 红态两处摘录 + 哈希, 绿态单一位置 grep + 参考文件去除判据的 diff, 外加一次真实分类会话证明行为未退化.
