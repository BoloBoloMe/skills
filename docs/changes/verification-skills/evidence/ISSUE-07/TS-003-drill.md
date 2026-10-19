# TS-003 演练: 影响范围判断与多模型同题调查 (AC-023), 含自足历史定位与中文交接 (TC-107)

## 固定记录

- 待测技能源: `/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-07/workflow/blast-radius/`, 分支 `issue/07`. 三次演练都用最终版, SKILL.md sha256 前 16 位 `59504b511e567aba` (加了多模型规则与 reference/multimodel.md).
- 宿主: Ubuntu 26.04.1 LTS x86_64, herdr 0.9.4, pi 1.3.0.
- 加载方式: 项目内 `.agents/skills/blast-radius/` 副本, `pi -a` 一次性信任, `/skill:blast-radius` 点名加载.
- 固定夹具: `payout-service` 提交链 `011ec25` (基线) -> `04ddf93` (删 amount_str 格式化符号) -> 本次变更; `orders-consumer` 起始 `a47893d`.

> 夹具可复现: `setup-fixture.sh` 建两个仓库, `setup-variants.sh` 建宽影响与局限两个变体并自检行为. 提交哈希含生成时间, 每次重跑会不同; 上面记录的是本次演练当次的实际哈希. 复现输出见 `fixture-reproduction.log`.

### 演练一: 宽影响, 多模型同题 (AC-023-1, AC-023-2)

- 临时项目: `/tmp/orchestra-07/drill-ts003-wide`, 起始提交 `e807b06` ("导出线格式改为 orders-export/2, 金额字段改名 amount_value", 2 文件各 1 行).
- 主会话: tab `S-br-wide-1`, pane `w1J:p2N`, agent `br-wide`, 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking high.
- 子会话 (由演练会话自己用 use-herdr 开, 用完自己关): A 路 `wide-a` `cli/gpt-6.1-sol` xhigh (tab `S-wide-a-1`); B 路 `wide-b` `cli/glm-5.3-flash` xhigh (tab `S-wide-b-1`).
- 操作: 首行 `/skill:blast-radius`, 任务给同一批关键事实 (线格式 vs 跨仓库消费者, 旧格式其他读者), 明确要求走多模型规则并单独出合并记录.
- 原始材料: `ts003-wide-raw/report.md` (交接), `ts003-wide-raw/merge.md` (合并记录), `ts003-wide-raw/work/router-a/report.md` 与 `.../router-b/report.md` (两路原文), `ts003-wide-raw/pane.txt`, 转录在 `raw-sessions/`.

结果:

- 判定: 变更只有 2 行, 但改的是跨仓库共享线格式, 会话按 "宽" 处理, 没有按 diff 行数当局限.
- 两路: 逐字相同的任务书 (`router-a/TASK.md`, `router-b/TASK.md`), 同 commit 副本, 各自跑证明, 互不读对方目录. 模型确实不同 (gpt-6.1-sol 与 glm-5.3-flash).
- 选型: 合并记录里给出 llm-select `score.py` 的依据 (能力分, 价格分) 与 thinking 档位理由.
- 合并: 逐条事实对齐 (F1-F8), 一致项保留最高级别并注明哪一路跑出; 分歧项 (F5 证据级别 2 vs 3, R1 概率措辞, stdout 读取方概率, README 解释) 全部保留双方说法与合并取法, 没有平均, 没有抹掉. 合并人还重跑了两路脚本核对.
- 交接: `ts003-wide-raw/report.md` 五部分齐 (做了什么 / 关键安全事实与证据级别 / 风险 / 已排除项 / 合并前最便宜的复现), 开头先给结论与建议.

### 演练二: 真局限 + 调用方选单路 (AC-023-3)

- 临时项目: `/tmp/orchestra-07/drill-ts003-local`, 起始提交 `2b905d2` ("内部数量上限从 99 收到 50", 只有 `app/clamp.py` 一行).
- 会话: tab `S-br-local-1`, pane `w1J:p2P`, agent `br-local`, 同一模型与档位.
- 任务里写明: 内部函数, 无共享格式, 调用方选择只做单路.
- 原始材料: `ts003-local-raw/report.md`, `ts003-local-raw/work/`, `ts003-local-raw/pane.txt`.

结果: 正常交付, 没有因为没做多模型而拒绝结论. 报告第 6 节 "单路声明与缺口" 写明单路, 保留已跑事实的 4 级, 并列出后续可加查的点; 同时查清 `clamp_qty` 零调用者 (`scan_callers.py` 文本 + AST, 退出码 0 表示零调用者, 有命中则非零退出).

### 演练三: 只有一款模型可用 (AC-023-4)

- 临时项目: `/tmp/orchestra-07/drill-ts003-gap`, 起始提交 `e807b06` (同一宽变更).
- 会话: tab `S-br-gap-1`, pane `w1J:p2Q`, agent `br-gap`, 同一模型与档位.
- 受控材料: 任务里写明 "本轮我只授权你使用当前这一款模型, 不得开其他模型会话". 这是调用方的授权限制, 不是真的缺模型 (本机实际可调用多款). 该点按 EXECUTION 测试策略的 "能力缺口可用明确标注的受控材料检验分支" 处理, 证据里如实标注为受控限制.
- 原始材料: `ts003-gap-raw/report.md`, `ts003-gap-raw/work/`, `ts003-gap-raw/pane.txt`.

结果: 报告第 1 节写 "能力缺口: 按要求只授权一款模型, 没有第二路同题调查. 下面 4 级事实是实跑证明的, 保留 4 级; 只是少了交叉核对这一层". 没有假装多路已完成, 也没有把已证明事实降级成未证实. 五部分交接照常齐全.

## 自足历史定位与中文交接 (TC-107)

- 历史定位在三次演练里都由会话自己用技能第 1 节的命令完成, 命令与输出留在各自报告: `git log --oneline`, `git show`, `git blame -L`, `git log --follow -p`, `git log --all -S"<符号>"`, `git remote -v`, `git ls-remote origin`, `git rev-parse origin/master`. 没有依赖工作树外未移植的说明文档.
- 取不到的材料都写了来源限制: remote 是本地路径, 提交消息无 PR 编号, 没有评审讨论; 三个报告都没有编造 PR 正文.
- 中文整理: 三份报告的正文是中文短句, 保留 `file:line`, 命令原文与原始输出, 事实/推断/未证实分开; 合并记录里对分歧措辞做了收敛, 但没有删掉任何一方的结论或证据级别.

## AC 对应

- AC-023-1 大或宽变更多模型同题调查并合并: 演练一.
- AC-023-2 小 diff 改共享格式按宽影响处理: 演练一 (2 行改动, 跨仓库线格式).
- AC-023-3 局限且调用方选单路可完成: 演练二.
- AC-023-4 只有一款模型时报告能力缺口: 演练三 (受控授权限制).
- TC-107 自足历史定位与中文交接: 三次演练的历史命令与报告文本.

## 收尾

- 演练一的两路子会话已由演练会话按 use-herdr 收尾规则关闭 (`agent list` 不再有 `wide-a` / `wide-b`); 四个演练 tab 由编排者关闭, 关闭后 `herdr agent get` 返回 agent_not_found.
- 四个演练仓库 `git status --short` 为空 (产品代码, 测试, 配置未改).
- 临时项目与 `/tmp/orchestra-07/out/` 在证据抄写完成后删除, 证据副本保留在本目录.
