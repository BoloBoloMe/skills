你是独立产品验收者. 本轮只做验收, 不改产品, 不修复.

目标提交: c0505dee33c9c78ffaaf61f88e05e041a7e29402
项目 cwd: /tmp/orchestra-03/heavy/three-groups-2avail

## 第一步 核对版本前提
运行 `git rev-parse HEAD` 必须等于上面提交; `git status --porcelain --untracked-files=all` 只应出现本轮证据目录 docs/changes/tool-cli/evidence-c0505de-r1/ 下的文件. 不符就停下并报告前提不满足.

## 判据来源
只读 docs/changes/tool-cli/PRODUCT.md 的 `验收标准` 节. 场景编号, 步骤里的具体数据, 期望输出都是判据原文, 不得放宽. 不要用实现代码, 测试文件或我的说法去改判据. TECHNICAL.md 的 pytest/build 不是产品通过条件, 不必运行.

## 你承接的标准 (原文)

@AC-001 @normal @G-001 @BR-001
场景: AC-001-1 默认问候
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py greet --name Ada`
  那么 标准输出为 `Hello, Ada!` 且退出码为 0

@AC-001 @edge @G-001 @BR-001
场景: AC-001-2 全大写问候
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py greet --name Ada --shout`
  那么 标准输出为 `HELLO, ADA!` 且退出码为 0

@AC-001 @normal @G-001 @BR-001
场景: AC-001-3 批量问候 250 个姓名
  假定 值班同学已有 `data/greet/names.txt`, 共 250 行, 每行一个姓名
  当 值班同学对每一行运行一次 `python3 tool.py greet --name <该行姓名>`
  那么 250 条标准输出都等于 `Hello, <该行姓名>!` 且退出码都是 0

@AC-003 @normal @G-003
场景: AC-003-1 JSON 导出
  假定 值班同学已取得 tool.py
  当 值班同学运行 `python3 tool.py export --name Ada`
  那么 标准输出为 `{"name": "Ada", "greeting": "Hello, Ada!"}` 且退出码为 0

@AC-003 @normal @G-003
场景: AC-003-2 批量导出 200 个姓名
  假定 值班同学已有 `data/export/names.txt`, 共 200 行, 每行一个姓名
  当 值班同学对每一行运行一次 `python3 tool.py export --name <该行姓名>`
  那么 200 条标准输出都等于 `{"name": "<该行姓名>", "greeting": "Hello, <该行姓名>!"}` 且退出码都是 0

## 工作方式
- 每个场景都要本轮实际运行, 记录完整命令, 原始输出(不要转述), 退出码, 时间.
- 单点场景: 把原始 stdout 与期望逐字节比对 (注意行尾换行是否算差异, 按判据"标准输出为 X"理解, 并如实记录实际原始字节).
- 批量场景: 必须真逐条运行, 不得抽样, 不得用一次运行推断 250/200 次. 保留完整明细日志 (每行含序号, 输入, 实际输出, 退出码, 与期望是否一致), 给出通过数/失败数, 有失败要列出具体差异.
- 期望输出里的引号, 空格, 逗号都要逐字符比对.
- 只运行 `python3 tool.py <子命令>` 及其数据文件. 不修改仓库任何被跟踪文件. 临时文件与日志只写在 docs/changes/tool-cli/evidence-c0505de-r1/verifier-a/.
- 不读实现代码来推断结果; 不启动替身服务, 不修改产品让它通过.
- data/count/ 是另一名验收者的独占资源, 不要碰.

## 交付
1) verifier-a/RESULTS.md: 表格式逐条结果, 每行含 标准编号 | 实际命令 | 实际结果 | 是否符合判据 | 结论(通过/失败/未验证) | 证据文件路径 | 时间. 无法执行就写未验证并说明缺什么.
2) 原始材料原件留在 verifier-a/ (命令日志, 批量明细).
3) 回复我: 每条标准编号的结论 + 材料绝对路径. 不要只写 "全部通过" 而省略逐条结论.
