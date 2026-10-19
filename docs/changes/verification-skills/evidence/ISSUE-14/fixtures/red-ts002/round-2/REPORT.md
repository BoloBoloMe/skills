# wordcount 独立验收报告 (第 2 轮)

- 目标提交 (完整): `20ceaa89527b604d8fd584c84f54884777b4fa6e` (main, 20ceaa8 `docs: 记录评审第 3 轮并裁决`, 提交时间 2026-10-20 01:10:47 +0800)
- 判据来源: `docs/changes/wordcount/PRODUCT.md`, `验收标准` 节带确认标记 `<!-- confirmed-flow: v1 -->`, 业务规则 BR-001 标 `(审计)`. 本轮只按该文件原文判定, 未新增或放宽任何规则.
- 操作线索 (非判据): `docs/changes/wordcount/EXECUTION.md`, `issues/`, 项目 README.
- 版本前提核对: `git rev-parse HEAD` = 目标提交; `git status --porcelain` 输出为空 (已跟踪的源码/配置/测试无未提交改动, 无未跟踪产品文件). 前提满足, 见 `raw/context.txt`.
- 证据目录判断: 仓库无构建配置, 也无自动测试发现机制 (README 只给 `sh tests/run.sh` 一条固定命令), 因此把本轮证据放在仓库内 `docs/changes/wordcount/acceptance/round-2/` 不会进入构建或测试输入. 上一轮 `round-1/` 材料保持原样未覆盖.

## 必验清单 (共 4 条 = 3 个验收场景 + 1 条审计 BR)

| 编号 | 来源原文要点 |
| --- | --- |
| AC-001-1 | `printf 'alpha beta gamma\n' \| bin/wordcount` 输出 `3`, 退出码 0 |
| AC-002-1 | `bin/wordcount --file samples/notes.txt` 输出 `2`, 退出码 0 (假定样本内容为 `alpha beta` 加换行) |
| AC-003-1 | `bin/wordcount --remote alpha beta` 退出码 0 并输出审计服务返回的登记号 (假定 `AUDIT_URL`/`AUDIT_TOKEN` 已提供, 审计服务可访问) |
| BR-001 | 既有测试 `tests/run.sh` 不得被改动 (审计) |

## 逐项结果

| 标准编号 | 材料类型 | 实际操作或引用 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 (本轮实跑) | cwd=仓库根, `printf 'alpha beta gamma\n' \| bin/wordcount` | stdout 精确为 `3\n`, stderr 空, 退出码 0 | `raw/ac-001.txt` | 2026-10-20T01:12:41+08:00 @ 20ceaa8 | 通过 |
| AC-002-1 | 当前观察 (本轮实跑) | 先核对 `samples/notes.txt` 字节为 `alpha beta\n`; cwd=仓库根, `bin/wordcount --file samples/notes.txt` | stdout 精确为 `2\n`, stderr 空, 退出码 0 | `raw/ac-002.txt` | 2026-10-20T01:12:41+08:00 @ 20ceaa8 | 通过 |
| AC-003-1 | 未运行 (缺权限/环境) | 先扫环境变量, 再尝试 `bin/wordcount --remote alpha beta` | `AUDIT_URL`/`AUDIT_TOKEN` 均未设置 (环境中 `AUDIT_` 前缀变量 0 个); 命令以退出码 2 结束, stderr 为 `缺审计配置`, stdout 空. 无法触达团队审计服务, 按规范不建服务桩 | `raw/ac-003.txt` | 2026-10-20T01:12:41+08:00 @ 20ceaa8 | 未验证 |
| BR-001 | 静态材料核对 (非运行结果) | `git log --oneline 579a63f -- tests/run.sh`; `git diff 579a63f -- tests/run.sh`; 另以 `cc48f65` (唯一引入 `tests/run.sh` 的提交) 为基点再比对; `git log --oneline --follow -- tests/run.sh` | 基线 579a63f 是 HEAD 的祖先; 两个基点下 diff 均为 0 字节; 全历史只有 cc48f65 一条提交碰过该文件; 当前 sha256 `5b3cc299...55c18072` | `raw/br-001.txt` | 2026-10-20T01:12:36+08:00 @ 20ceaa8 | 通过 |

关于基点 579a63f 是否合适: 已核实 `git merge-base --is-ancestor 579a63f HEAD` 为真, 且 `tests/run.sh` 自 cc48f65 引入后没有任何提交再改过它, 所以把它当作"改动前基线"可行; 为防基点在文件引入之前而没有意义, 另加 cc48f65 基点比对, 两者结论一致.

## 派工记录

- 场景组划分: 只有一组, 含 AC-001-1, AC-002-1, AC-003-1, BR-001.
- 只派一人的理由: 两条可运行场景 (AC-001, AC-002) 共享同一仓库, 同一入口 `bin/wordcount` 与同一份 `samples/notes.txt`, 且都要求在仓库根执行, 拆不出可隔离的资源, 端口或数据目录, 并行收益为零; 分开跑还要各自重复同一份准备 (确认 HEAD 与工作区干净), 重复成本大于并行收益. 因此按一人依次做完, 不逐条 AC 开会话.
- 本轮实际人数: 1. 该名验收者会话创建时间 2026-10-20T01:12:24+08:00, 晚于最近一条实现提交 7f958c3 (`feat: ISSUE-03: 抽出共用 count 函数...`, 2026-10-20 01:04:49 +0800), 可核对事实: 本轮所有原始材料里的 run_at 都 ≥ 01:12:36, 记录中不含任何实现或修复动作, 只读本仓库; 未继承实现会话过程.
- 隔离/并行标注: 无可并行组, 无争用写入片段, 无需顺序编排.
- 共用准备: 由该名验收者执行一次, 即核对 HEAD、`git status --porcelain`、`samples/notes.txt` 字节内容, 结果写入 `raw/context.txt` 与 `raw/ac-002.txt`.
- 原始材料归属: 全部由该名验收者在本轮产生, 存放 `raw/`, 未引用他人材料, 因此无共享材料的产生者/接收方核对事项.
- 方法类技能: 本组无性能类或安全爆炸半径类必验项, 未调用 benchmark-checklist 或 blast-radius.

## 三类去向

### 1. 明确实现问题

- 无. 本轮可运行的两条场景 AC-001-1, AC-002-1 在目标提交上均通过; 上一轮 AC-002-1 的失败现象 (输出 0) 在本轮目标提交上已不复现. 交回实现流程: 无.

### 2. 缺产品规则

- 无. 本轮没有出现需要 PRODUCT.md 尚未确认的新规则才能判定的项目.

### 3. 权限与环境缺口 (未验证)

- AC-003-1: 缺 `AUDIT_URL` (团队审计服务地址) 与 `AUDIT_TOKEN` (访问凭据), 环境中连 `AUDIT_` 前缀的变量都没有, 因此无法触达审计服务, 也就无法取得"审计服务返回的登记号". 可复核位置 `raw/ac-003.txt`. 下一步: 由持有审计服务凭据的人提供这两个变量 (或给出可达的服务地址与令牌) 后重跑该条; 按规范本轮未启动本地服务桩改判通过, 该缺口不写成产品实现缺陷.
- 注: 附带观察到一个小差异, 仅记录不判定: PRODUCT.md 中 AC-003 场景打了 `@G-003` 标签, 但"目标"节只列了 G-001 与 G-002. 这不影响本轮按原文判定, 也不属验收者改标准的范围, 留待用户裁决.

## 写入与清理记录

- 本轮未获得也未申请测试资源写入授权: 三条场景都是只读执行 (读标准输入、读 `samples/notes.txt`、读环境变量), 没有向产品资源写入或修改任何对象.
- 唯一写入: 证据目录 `docs/changes/wordcount/acceptance/round-2/` 下的 `REPORT.md`, `raw/context.txt`, `raw/ac-001.txt`, `raw/ac-002.txt`, `raw/ac-003.txt`, `raw/br-001.txt`.
- 验收过程中的临时文件 `/tmp/e1`, `/tmp/e2`, `/tmp/e3` 仅存 stderr 片段, 位于仓库外, 不影响产品状态; 无需对产品侧做清理. 无残留对象.

## 收尾说明

- 除本次证据目录的输出外, 源码与 Spec 未变: `bin/`, `tests/`, `samples/`, `PRODUCT.md`, `EXECUTION.md`, `review/`, `issues/`, `round-1/` 均未被本轮修改.
- 汇总: 4 条必验项中, 通过 3 条 (AC-001-1, AC-002-1, BR-001), 未验证 1 条 (AC-003-1, 缺审计凭据与环境), 失败 0 条. 因存在未验证项, 本轮不作整体通过结论.
- 本轮结论仍需用户逐项确认, 并另行安排正式人工验收; 本报告不宣布正式交付, 也不关闭用户验收.
