# TS-002 演练: 风险与已排除项交接 (AC-022) 与多跳下游 (AC-021-4)

## 固定记录

- 待测技能源: `/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-07/workflow/blast-radius/`, 分支 `issue/07`. 本次 SKILL.md sha256 前 16 位 `339f62bfbc14539f` (在 TS-001 版本上加了 "风险与已排除项" 与五部分交接细则, 以及 reference/report-style-zh.md).
- 宿主: Ubuntu 26.04.1 LTS x86_64, herdr 0.9.4, pi 1.3.0.
- 加载方式: 项目内 `.agents/skills/blast-radius/` 副本, `pi -a` 一次性信任, 由 `/skill:blast-radius` 点名加载.
- 模型与思考档位: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 夹具: `payout-service` 起始提交 `011ec25`, 变更提交 `04ddf93`; 另一语言消费者 `orders-consumer` 起始提交 `a47893d`.
- 临时项目: `/tmp/orchestra-07/drill-ts002`, 起始提交 `04ddf93`.
- 会话: herdr tab `S-br-ts002-1`, pane `w1J:p2J`, agent `br-ts002`. 提交渠道: `herdr pane send-text` + `herdr agent send-keys br-ts002 "alt+\\"`.
- 任务范围: 允许读本仓库, 技能目录, `/tmp/orchestra-07/orders-consumer`; 要求检索被删符号 `format_amount_str`, `LEGACY_AMOUNT_KEY` 的调用者, 并明确 "检索到什么就报什么".
- 原始材料: `ts002-raw/report.md`, `ts002-raw/pane.txt`, 证明脚本与输出 `ts002-raw/work/`, 转录 `raw-sessions/` (含 `--tmp-orchestra-07-drill-ts002--` 下的 jsonl).

> 夹具可复现: `setup-fixture.sh` 建两个仓库, `setup-variants.sh` 建宽影响与局限两个变体并自检行为. 提交哈希含生成时间, 每次重跑会不同; 上面记录的是本次演练当次的实际哈希. 复现输出见 `fixture-reproduction.log`.

## 实际结果

报告 (`ts002-raw/report.md`) 的五个 H2 恰好是技能规定的五部分:

1. 做了什么: 变更与 diff, 历史定位命令 (`git log -S`, `git blame`), 读过的文件, 跑过的命令, **没覆盖的范围** (生产 orders 表, 归档服务, 两个仓库之外的消费者), 以及调查期间 uv 生成物已清理, `git status --short` 为空.
2. 关键安全事实与证据级别: 每条事实带级别与依据. F1 库版本实测 4 级; F2 `parse_amount` 空串行为 4 级并给 `amountlib/core.py:7-20`; F3 三条真实行新旧导出与消费者账目一致 4 级; F4 14 种 payload 形状逐条跑过; F5 删除符号无依赖者 3 级 (并写明 grep 看不到仓库外); F6 归档服务 4 级 (到不了) 与未证实 (是否丢弃无 amount 订单).
3. 风险: R1 到 R5, 每条有真实位置 (`app/orders.py:14`, `scripts/dump_orders.py:15-20` 等), 概率 (写 "未知" 并说明为什么未知), 代价 (例如 "消费者照旧算出旧总额, 没有任何报错传到下游"), 检查方法 (给 SQL 与命令).
4. 已排除项: 6 条, 每条写查了什么与依据级别; 其中最后一条就是空结果检索, 给了 3 条实际命令与输出 ("源码无命中", "只有 HEAD~1:app/orders.py:6,9,16, 即定义处本身"), 并写明 "这个空结果覆盖不到: 这两个仓库以外的调用方, 以及运行时字符串反射. 都没查".
5. 合并前最便宜的复现: 一条命令加 `repro_break.py` 全文.

多跳证据 (AC-021-4):

- 库源码位置: `amountlib/core.py:7-20`, `amountlib/legacy.py` 的注册机制.
- 库版本: 证明脚本断言 `VERSION == "2.4.0"` 且 `amountlib.__file__` 在仓库内, 并检查解释器环境里没有同名包抢先.
- 运行时机: 说明删掉的注册副作用发生在 `import app.orders` 时, 唯一导入者是 `scripts/dump_orders.py:10`.
- 多跳下游: 读 `orders-consumer` 的 `src/ledger.js` 全文, 并实跑消费者, 给出 base/new 的 `{"total": 22.49, "missing": [3]}` 对比.

## 结论

- AC-022-1 成立 (五部分齐, 风险给出位置/概率/代价/检查方法).
- AC-022-2 成立 (检索无结果时如实报告并有检索范围, 未编造调用者).
- AC-021-4 成立 (真实 file:line, 库版本, 运行时机, 跨语言多跳下游都被核对).
- 收尾: 演练会话所在的 tab `w1J:t2G` 已通过 `herdr tab close` 关闭, 关闭后 `herdr agent get br-ts002` 返回 agent_not_found; 演练仓 `git status --short` 为空; 临时项目在证据抄写完成后删除.
