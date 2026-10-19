# TS-001 演练: 关键安全事实调查与可失败证明 (AC-021)

## 固定记录

- 待测技能源: `/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-07/workflow/blast-radius/` 分支 `issue/07`.
  - 红跑与基线跑时该目录不存在 (技能源尚未创建).
  - 绿跑时 SKILL.md 的 sha256 前 16 位: `a0d09c481e1884a8`, 即只含证据级别与证明脚本规则的初版.
- 宿主: Ubuntu 26.04.1 LTS x86_64, herdr 0.9.4, pi 1.3.0.
- 加载方式: 项目内 `.agents/skills/blast-radius/` 副本, 会话启动参数 `pi -a` (一次性项目信任) 后由用户点名 `/skill:blast-radius` 加载. 未改全局配置, 未跑 sync-to-pi.py.
- 模型与思考档位: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 夹具:
  - `payout-service` 起始提交 `011ec25`, 变更提交 `04ddf93` (删除 app/orders.py 的 amount_str 格式化符号, 改用 parse_amount 回退).
  - `orders-consumer` 起始提交 `a47893d` (Node 消费者读导出的 JSON).
  - 夹具建立脚本: `setup-fixture.sh` (本目录).
- 临时项目: `/tmp/orchestra-07/drill-ts001-red`, `/tmp/orchestra-07/drill-ts001-green`, `/tmp/orchestra-07/drill-ts001-baseline`, 三者起始提交都是 `04ddf93`.
- 会话: herdr tab `S-br-red-1` (pane `w1J:p29`, agent `br-red`), `S-br-green-1` (pane `w1J:p2D`, agent `br-green`), `S-br-baseline-1` (pane `w1J:p2E`, agent `br-baseline`). 提交渠道: `herdr pane send-text` 写入任务文本, `herdr agent send-keys <名> "alt+\\"` 提交 (pi 的提交键).
- 原始材料:
  - 终端输出: `ts001-raw/red/pane.txt`, `ts001-raw/green/pane.txt`, `ts001-raw/baseline/pane.txt`
  - 会话报告: `ts001-raw/red/report.md`, `ts001-raw/green/report.md`, `ts001-raw/baseline/report.md`
  - 绿跑证明脚本与输出: `ts001-raw/green/work/` (proof_parse.py, proof_read.py, read-base.log, read-head.log 等)
  - 红跑证明脚本与输出: `ts001-raw/red/proof/`
  - 会话转录 (jsonl): `raw-sessions/`

> 夹具可复现: `setup-fixture.sh` 建两个仓库, `setup-variants.sh` 建宽影响与局限两个变体并自检行为. 提交哈希含生成时间, 每次重跑会不同; 上面记录的是本次演练当次的实际哈希. 复现输出见 `fixture-reproduction.log`.

## 红跑: 技能不存在

- 操作: 在 `/tmp/orchestra-07/drill-ts001-red` (无 `.agents/skills/blast-radius`) 开会话, 提交任务第一行是 `/skill:blast-radius`, 其余是同一份调查任务.
- 实际发生: 启动界面的技能列表 (`ts001-raw/red/pane.txt`) 里没有 blast-radius; 会话自己承认 "本机未安装 blast-radius 技能", 改为在文件系统里搜索同名技能, 最终按工作树里 ISSUE-07 规格文档执行, 并把检索到的 `docs/changes/.../ISSUE-07-blast-radius.md` 当依据.
- 结论: 技能未加载, 此次没有技能行为可审. 交接结构由会话自行组织: 证据级别用了自造的三档标签 (`已证实-本地` / `代码推断` / `未证实-需外部确认`), 没有按 1 到 5 级说明停在哪一级; 证明过程是临时命令, 未留下判断错就会失败的脚本 (`ts001-raw/red/report.md` 里搜不到 assert/非零退出断言). 这正是技能要固定下来的部分, 也说明红跑缺的是技能, 不是模型能力.

## 基线跑: 技能不存在, 但任务不带技能名

- 操作: 另开 `/tmp/orchestra-07/drill-ts001-baseline`, 任务文本不提任何技能名, 只给同样的事实与 "我要判断能不能合入".
- 结果 (`ts001-raw/baseline/report.md`): 结论与证据都写出来了, 但同样自造证据标签, 关键事实 A 只给 "已本地运行证实" 的转述, 没有可失败脚本原文; 五部分交接的名称不齐 (无 "已排除项" 与 "合并前最便宜的复现" 这两个独立小节).
- 结论: 无技能时模型仍能查出问题, 但证据级别口径, 可失败脚本, 五部分交接这三项靠运气. 这条作为绿跑的对照, 不冒充技能行为.

## 绿跑: 技能加载后

- 操作: `/tmp/orchestra-07/drill-ts001-green` 放入技能副本, 同一份任务文本首行 `/skill:blast-radius`, 报告写到仓库外 `/tmp/orchestra-07/out/green-ts001.md`.
- 结果 (`ts001-raw/green/report.md`):
  - 事实 A (parse_amount 空串行为): 标 "等级 4, 实际跑过", 给出 `amountlib/core.py:12-16` 位置, 脚本先断言 `amountlib.VERSION == "2.4.0"` 且 `amountlib.__file__` 在仓库内, 输出 `parse_amount('') -> None` 与 `OK: 版本与空串行为断言全部通过 / EXIT=0`, 并说明 "已到 4 级, 没有生产应用可跑, 所以不是 5 级".
  - 事实 B: 对 base 树 (`011ec25`) 与 head 树 (`04ddf93`) 各跑真实入口 `db/seed.py` + `scripts/dump_orders.py`, 输出 `IDENTICAL`.
  - 事实 C (归档服务): 标 "等级 1-2, 明确未证实", 写出缺口是 "缺生产凭据 ARCHIVE_TOKEN, 缺 orders_archive 表和数据, 缺生产网络可达性", 并实跑无 token 与假 token 两种失败.
  - 事实 D: 被删符号全仓检索无命中, 给出检索命令与范围.
  - 报告含五部分 (做了什么 / 关键事实与证据级别 / 风险 / 已排除项 / 合并前最便宜的复现) 与命令附录.
- 结论: AC-021-1, AC-021-2, AC-021-3 成立. AC-021-4 的 "多跳下游" 这一条在该次任务里被我给的范围限制挡住 (任务只允许读本仓库), 会话在风险 R2/R4 里如实标了 "未读消费者仓库, 未证实", 由 TS-002 演练用完整范围补上, 见 `TS-002-drill.md`.
- 收尾: 演练会话按 use-herdr 收尾规则关闭 (`herdr tab close w1J:t27`, `w1J:t2B`, `w1J:t2C`, 关闭后 `herdr agent get` 均返回 agent_not_found); 三个仓 `git status --short` 为空; 临时项目保留到证据抄完.

## AC 对应

- AC-021-1 定位关键安全事实并标注证据级别: 绿跑事实 A/B/C/D 与 "停在哪一级" 的说明.
- AC-021-2 运行真实代码给出可失败证明: 绿跑 `proof_parse.py` 先断言版本再断言行为, 判断错时 assert 失败并非零退出, 输出原文在 `ts001-raw/green/work/`.
- AC-021-3 无法证明时标未证实: 绿跑事实 C.
- AC-021-4 深入库源码与多跳下游: 库源码位置在绿跑已有; 多跳下游由 `TS-002-drill.md` 的完整范围演练承接.
