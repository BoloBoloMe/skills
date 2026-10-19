你是独立产品验收者. 本轮只做验收, 不改产品, 不修复.

目标提交: c0505dee33c9c78ffaaf61f88e05e041a7e29402
项目 cwd: /tmp/orchestra-03/heavy/three-groups-2avail

## 第一步 核对版本前提
运行 `git rev-parse HEAD` 必须等于上面提交; `git status --porcelain --untracked-files=all` 只应出现本轮证据目录 docs/changes/tool-cli/evidence-c0505de-r1/ 下的文件. 不符就停下并报告前提不满足.

## 判据来源
只读 docs/changes/tool-cli/PRODUCT.md 的 `验收标准` 节和 `业务规则` 节. 场景编号, 步骤里的具体数据, 期望输出都是判据原文, 不得放宽. 不要用实现代码, 测试文件或我的说法去改判据. TECHNICAL.md 的 pytest/build 不是产品通过条件, 不必运行.

## 你承接的标准 (原文)

场景: AC-002-1 统计词数
  假定 值班同学已有文本文件 notes.txt, 内容为 `alpha beta gamma` 加一个换行
  当 值班同学运行 `python3 tool.py count --file notes.txt`
  那么 标准输出为 `3` 且退出码为 0

场景: AC-002-2 统计字符数
  假定 值班同学已有文本文件 notes.txt, 内容为 `alpha beta gamma` 加一个换行
  当 值班同学运行 `python3 tool.py count --file notes.txt --chars`
  那么 标准输出为 `17` 且退出码为 0

场景: AC-002-3 批量统计 250 个文件
  假定 值班同学已有 `data/count/docs/` 下 250 个文本文件, 以及 `data/count/expected.tsv` (每行是文件名与词数)
  当 值班同学对每个文件运行一次 `python3 tool.py count --file <该文件>`
  那么 250 条标准输出都与 `expected.tsv` 中对应词数一致且退出码都是 0

业务规则 (审计): BR-002 本变更不新增第三方依赖, 依赖清单, 锁文件和构建材料与上一提交逐项一致.

## 工作方式
- 每个场景都要本轮实际运行, 记录完整命令, 原始输出(不要转述), 退出码, 时间.
- AC-002-1/2: 先核对 notes.txt 的实际字节内容是否等于 `alpha beta gamma` 加一个换行 (给出 `od`/`xxd` 或等价证据), 再按原文命令运行并逐字节比对 stdout.
- AC-002-3: 必须真逐条运行 250 次, 不得抽样. 保留完整明细日志 (每行含序号, 文件名, 实际输出, expected.tsv 对应期望, 退出码, 是否一致), 给出通过数/失败数, 有失败列出具体差异.
- BR-002 属审计静态材料核对: 找到上一提交 (`git rev-parse HEAD^`), 逐项比对依赖清单/锁文件/构建材料 (至少 deps.txt, deps.lock, build.sh, 以及仓库里其他依赖或构建相关文件) 与上一提交是否逐项一致, 并核对本变更是否新增第三方依赖 (例如比对 tool.py 的 import 变化). 给出比对命令, 前后内容和可复核位置, 并明确标注这是静态材料核对结果, 不是运行行为结果.
- 不修改仓库任何被跟踪文件. 临时文件与日志只写在 docs/changes/tool-cli/evidence-c0505de-r1/verifier-b/.
- 不读实现代码来推断结果; 不启动替身服务, 不修改产品让它通过.
- data/greet/ 与 data/export/ 是另一名验收者的独占资源, 不要碰.

## 交付
1) verifier-b/RESULTS.md: 表格式逐条结果, 每行含 标准编号 | 实际命令 | 实际结果 | 是否符合判据 | 结论(通过/失败/未验证) | 证据文件路径 | 时间. 无法执行就写未验证并说明缺什么.
2) 原始材料原件留在 verifier-b/ (命令日志, 批量明细, 比对输出).
3) 回复我: 每条标准编号的结论 + 材料绝对路径. 不要只写 "全部通过" 而省略逐条结论.
