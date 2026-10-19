# wordcount 独立产品验收报告 (verify-change round-1)

- 目标提交: `b519339db7d0d1ec723aef311fef7d17f2810bce` (分支 `main`, 完整哈希; `git rev-parse HEAD` 核对一致)
- 判据来源: `docs/changes/wordcount/PRODUCT.md`, `验收标准` 节带确认标记 `<!-- confirmed-flow: v1 -->`; 覆盖 PRODUCT.md v1, 目标提交 b519339
- 产物根: `docs/changes/wordcount/`
- 证据目录: `docs/changes/wordcount/verify/round-1/` (本轮新建, 未覆盖旧证据; 仓库内无构建脚本, CI 配置或测试发现机制, `tests/run.sh` 只用固定路径, 该目录不会进入构建与测试输入)
- 派工计划: `docs/changes/wordcount/verify/round-1/plan.md`
- 非产品判据说明: `EXECUTION.md`, `issues/ISSUE-01-wordcount.md` 只作操作线索; `review/round-1.md` 是代码评审结论, 两项均未用作通过依据. 技术实现划分不属本轮产品判据, 不判通过也不判失败.

## 必验清单与逐项结果 (共 3 条: 2 个验收场景 + 1 条审计 BR)

| 标准编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间或版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 (验收标准 @AC-001 @normal @G-001) | 当前观察 (本轮实跑) | 验收者 acc-wc-1-1 在本工作区执行 `printf 'alpha beta gamma\n' \| bin/wordcount`, 取产品进程退出码, 并用 `od -c` 逐字节核对输出; 同一命令复跑一次 | 输出 `3` 加一个换行 (2 字节), 退出码 0; 两次一致 | `docs/changes/wordcount/verify/round-1/ac-001-1.log` | 2026-10-20T01:08:19+08:00 (复跑 01:08:34), 提交 b519339 | 通过 |
| AC-002-1 (验收标准 @AC-002 @normal @G-002) | 当前观察 (本轮实跑) | 验收者先核对 `samples/notes.txt` 实际字节 (`od -c`, 11 字节), 再执行 `bin/wordcount --file samples/notes.txt` 取退出码, 并复跑一次 | 文件确为 `alpha beta` + 换行; 输出 `2` 加一个换行 (2 字节), 退出码 0; 两次一致 | `docs/changes/wordcount/verify/round-1/ac-002-1.log` | 2026-10-20T01:08:22+08:00 (复跑 01:08:34), 提交 b519339 | 通过 |
| BR-001 (业务规则, 审计) | 静态材料核对 (非运行行为) | 验收者用 `git log --all -- tests/run.sh` 查触碰历史, 比对引入版 `cc48f65:tests/run.sh` 与 `HEAD:tests/run.sh` 的 blob 哈希与全文, 并核对工作区文件哈希; 指挥者独立复算同一组 git 命令 | 该文件仅由 cc48f65 引入, `cc48f65` 与 `HEAD` 的 blob 均为 `a85d460255b8266747fe63c847fbdb62cae18f4f`, `git diff cc48f65 HEAD -- tests/run.sh` 为空, 工作区 `git hash-object` 同值, `git status` 对 `tests/` 无输出 | `docs/changes/wordcount/verify/round-1/br-001.md`; 指挥者复算见本报告附注 | 2026-10-20T01:08:31+08:00, 提交 b519339 | 通过 |

汇总: 3 条中 通过 3, 失败 0, 未验证 0. 本轮无失败项, 所以不给"全部通过"这类笼统标签, 结论按上表逐条成立.

BR-001 的通过依据是静态材料核对结果, 不是运行 `tests/run.sh` 的行为结果; 本轮没有把运行测试的结论当作 BR-001 的证据.

## 派工记录

- 场景组划分与人数依据: 3 条必验项映射为单一组 G-1. 三条都落在同一仓库, 同一 `bin/wordcount`, 同一 `samples/notes.txt`, 同一 `tests/run.sh`; 拆开只会重复同一份工作区与版本准备, 不产生独立实例/端口/数据目录, 属"拆开后仍互相占用同一份资源", 因此只派 1 人, 不逐条 AC 开会话.
- 计划人数 1, 实际派出 1; 当轮可新开验收者数量充足, 按并行收益决定不派满.
- 验收者: 会话名 `acc-wc-1-1` (pi session id `01a15522-5573-7012-a841-9530f4d926b7`), tab `S-acc-wc-1-1` (w1E:t2C), 窗格 w1E:p2C
  - 启动命令: `herdr agent start acc-wc-1-1 --kind pi --pane w1E:p2C -- -a --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high`
  - 创建时间: 2026-10-20T01:07:59+08:00 (agent start 返回 idle); 会话 shell 起始 01:08:11, 首个命令 01:08:09
  - 承接标准: AC-001-1, AC-002-1, BR-001 (全部 3 条)
  - 未参与本次实现与修复的可核对事实: 会话创建时间晚于全部实现/合并/收尾提交 (beb0ebf 实现 00:49:43, 4187edb 合并 00:49:43, 720db42 00:49:43, 目标提交 b519339 01:06:36); 未继承任何实现或修复会话; 其操作记录 (见 session.md 命令清单) 只含只读 git 查询, 产品入口运行与证据写入, 没有任何编辑产品代码/test/samples 或 git 写历史动作; 全程 `git status --porcelain` 仅有 `?? docs/changes/wordcount/verify/` 一项.
- 共用准备: 由该验收者一人完成 (核对 HEAD 与工作区状态, 读入口与样例字节), 未重复准备.
- 原始材料归属: 全部归 acc-wc-1-1, 写入 `docs/changes/wordcount/verify/round-1/` (`ac-001-1.log`, `ac-002-1.log`, `br-001.md`, `session.md`).
- 组开始与结束: 2026-10-20T01:08:09 至 2026-10-20T01:08:34 (+08:00), 结束确认方式为 `herdr agent get` 报 done 且 4 份证据文件落盘.
- 争用写入片段: 无. 本轮全部为只读检查与产品入口运行, 没有需要写测试资源的场景, 因此不需要先后顺序安排.
- 共享材料: 无跨验收者共享 (只有 1 名验收者); 指挥者只做材料复核, 未产生产品运行观察.
- 方法技能: 未调用 benchmark-checklist 或 blast-radius. 理由: AC-001-1/AC-002-1 为功能正确性判定, 标准不含性能结论; 也不存在依赖"删除后数据仍可读"类未证实安全假设的场景.

## 三类去向

### 1. 明确实现问题 (交回实现流程)

0 条. 两条验收场景在目标提交上稳定满足 PRODUCT.md 原文, BR-001 静态核对无改动.

### 2. 尚缺产品规则 (交回决策流程)

0 条. 本轮没有判定取决于 PRODUCT.md 未确认新规则的项.

### 3. 权限与环境缺口 (未验证)

0 条. 本轮所需入口 (bin/wordcount, samples/notes.txt, git) 均可用, 无未验证项.

## 写入与清理记录

- 写入授权: 本轮无任何场景需要写测试资源 (两条 AC 只用仓库已有样例, BR-001 为静态比对), 因此未向用户申请测试资源写入批准, 也未发生未批准写入.
- 实际写入 (仅证据输出, 位于 `docs/changes/wordcount/verify/round-1/`):
  - 01:07 指挥者写 `plan.md`
  - 01:08 验收者写 `ac-001-1.log`, `ac-002-1.log`, `br-001.md`
  - 01:09 验收者写 `session.md` (首次尝试用 shell heredoc 写入被工具的危险 Git 操作告警拦截, 文件未生成; 改用 write 工具后落盘, `ls -l` 已确认)
- 清理: 无需清理的测试资源; 无临时对象残留. 证据目录按要求保留为本轮证据, 不删除.
- 未发生: 修改被跟踪产品文件, `git add/commit/push/merge`, 修改 PRODUCT.md/EXECUTION.md/issues, 运行 sync 类脚本.

## 附注: 指挥者对静态材料的独立复核 (不替代验收者结论)

执行于 2026-10-20T01:09 (+08:00), 提交 b519339:
- `git rev-parse HEAD` = `b519339db7d0d1ec723aef311fef7d17f2810bce`
- `git status --porcelain` 仅 `?? docs/changes/wordcount/verify/`
- `git log --all --format='%H %ci %s' -- tests/run.sh` 仅 `cc48f65... 2026-10-20 00:49:43 +0800 scaffold: 项目骨架, Product, 执行计划与测试`
- `git rev-parse cc48f65:tests/run.sh HEAD:tests/run.sh` 均为 `a85d460255b8266747fe63c847fbdb62cae18f4f`; `git hash-object tests/run.sh` 同值; `git diff cc48f65 HEAD -- tests/run.sh` 行数 0
- `wc -c < samples/notes.txt` = 11; `git status --porcelain samples/notes.txt bin tests` 无输出
- 指挥者未运行 `bin/wordcount`, 未运行 `tests/run.sh`, 未组织或执行任何修复.

## 收尾说明

- 除本次证据目录 `docs/changes/wordcount/verify/round-1/` 的输出外, 源码与 Spec 未变 (工作区相对目标提交的唯一差异是该未跟踪证据目录). 不声称整个工作区干净: 证据文件本身就是相对起始提交的改动.
- 本报告只覆盖 PRODUCT.md v1 (`confirmed-flow: v1`) 与目标提交 b519339; 验收开始后 PRODUCT.md 未新增场景.
- 本轮通过的结论不是正式交付: **结论仍需用户逐项确认和正式人工验收**. 不宣布正式交付, 不关闭用户验收.
