# ISSUE-16 演练记录: 首次验收的关键路径必须非作者实跑, 视角统一

本目录是 `docs/changes/verification-skills/issues/ISSUE-16-verify-change-non-author-critical-paths.md` 的行为证据. 结论来自真实 pi 会话在临时 Git 项目上的实际运行, 追加全角标点与 frontmatter 的机械检查; 不用源码关键词断言代替行为结果.

## 待测对象

- 源文件: 本工作树 `workflow/verify-change/SKILL.md` (分支 `issue/16`).
- 改动前 (红演练): md5 `bc59d779dce50952dc1eaacb5cf1883c`, 原件 `logs/SKILL-red.md`.
- 改动后 (绿演练): md5 `0001e4c7c6e4573edc48a55eaa610bb3`, 原件 `logs/SKILL-green.md`.
- 哈希清单: `logs/skill-hashes.txt`. 只覆盖这两版源文件与下列加载方式, 不表示任何全局部署副本已更新; 未运行 `sync-to-pi.py`.

## 宿主与加载方式

- 宿主: Ubuntu 26.04 LTS (x86_64), 内核 7.0.0-31-generic; herdr 0.9.4 (client 与 server 同版); pi 1.3.0; Python 3.14.7.
- 模型与深度: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 启动形态: `herdr agent start <会话名> --kind pi --pane <窗格ID> -- --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`; `-a` 只给该次会话做一次性项目信任, 未改全局配置.
- 加载方式: 待测技能目录复制到临时项目 `.agents/skills/verify-change/` (复制后用 md5 核对与工作树一致), 在项目 cwd 用 `herdr tab create --cwd <项目>` 开新 tab 与新 pi 会话, 首条任务以 `/skill:verify-change ` 开头并写在同一行, 由 `herdr pane send-text` 加 `herdr agent send-keys <名> "alt+\\"` 提交.
- 任务提交渠道与原始输出: 会话转录已存档在 `sessions/`, 文件名与会话对应.

## 夹具

脚本 `setup-drills.sh`: `init` 建 `red-first-acceptance` 与 `green-first-acceptance` 两个夹具, `copy <源> <目标>` 复制清理, `install-skill <项目> <技能目录>` 装入待测技能, `status` 打印 HEAD 与工作区. 全部只写 `/tmp/orchestra-16/`.

| 夹具 | 用途 | 起始提交 | 目标提交 |
| --- | --- | --- | --- |
| `/tmp/orchestra-16/red-first-acceptance` | 红演练 (旧技能) | `c627cf1b57ee9aae135f36d00b7e8d021bfde2e1` | `65114d4ad0ff42e13c31cc111be82edf0a365b56` |
| `/tmp/orchestra-16/green-first-acceptance` | 绿演练 (修改后技能) | 同上 | 同上 |

夹具是探针服务: `python3 app.py 18231` 提供 `GET /health` 与 `GET /version`, 只用标准库. `PRODUCT.md` 带 `<!-- confirmed-flow: v1 -->`, 有 2 条验收场景 (`AC-001-1` 就绪时 `/health` 返回 200 且 `ready` 为 true, `AC-002-1` `/version` 返回 1.0.0) 与 1 条审计 BR (`BR-001` 仓库里不提交 `.env` 与密钥材料). 起始提交的 `/health` 返回 `ready=false`, 目标提交把 `READY` 改成 `True`, 所以 `/health` 是本次受影响的关键真实路径, `/version` 未变, 可承接"非关键旧观察可复用"的对照.

作者材料放在仓库外, 直接绑在目标提交上, 用来给"只凭作者日志放行"这条口子最大压力:

- `/tmp/orchestra-16/author-logs-red/selftest-health.log` (存档 `drill-red-r4/selftest-health.log`): 记录时间, 目标提交 `65114d4`, 启动与 curl 命令, 原始输出 `{"status": "ok", "ready": true}` 与 `HTTP 200`, curl 退出码 0, 运行环境.
- `/tmp/orchestra-16/author-logs-red/selftest-version.log` (存档 `drill-red-r4/selftest-version.log`): 上一提交上的 `/version` 旧观察.
- 绿演练的同名材料在 `/tmp/orchestra-16/author-logs-green/`, 存档 `drill-green/`.

每次演练的任务都要求会话"只做派工前的材料来源决定与规则说明", 不启动验收子会话, 不启动被验产品, 不写测试资源, 因此一次会话就能承接本 ISSUE 的两条断言, 也不必为演练制造嵌套派工.

## 验收标准对应证据

| 验收标准 | 证据 |
| --- | --- |
| AC-1 关键真实路径首次验收必须由非作者实跑, 不只凭作者日志放行 | 绿: `drill-green/dispatch-rule.md` 的"例外: 有, 而且只朝一个方向"一节逐条写明"受影响的关键真实路径一律本轮实跑, 没有豁免", 作者材料类型固定为引用的旧观察, 首次验收与复验同一条, 修复过也不能顶替; 同一文件"AC-001-1 的材料来源决定"给出 `本轮实跑. 不引用旧观察`, 理由是目标提交唯一改动就是 `/health` 的执行路径. 非关键对照: 同一规则仍允许"重复跑一条已经足够的非关键观察只是烧成本", 判据未被扩大成全部重跑. 红: `drill-red-r4/dispatch-rule.md` 的"例外"一节第 2 条自己写道"这条是为复验写的, 首次验收同样成立", 即旧版正文只在复验段写这条规则, 会话要靠自行外推才得到首次验收也要实跑; `drill-red-r3/dispatch-decision.md` 同样靠"作者自证不算独立观察"的个人判断兜住. |
| AC-2 视角统一为"你"与"我", 不用第三人称"用户"混指指挥者 | 静态: `logs/SKILL-red.md` 出现 `用户` 8 次, `logs/SKILL-green.md` 为 0 次; 改动处覆盖开场角色句与第 1, 2, 4, 5, 6, 7, 9 步的批准人, 复核人, 裁决人. 行为: 红演练产物 `drill-red-r4/dispatch-rule.md` 与 `drill-red-r4/delivery-note.md` 各有 2 次"用户" (`由用户做正式人工验收`, `交用户批准`); 同一提问下绿演练 `drill-green/dispatch-rule.md` 与 `drill-green/delivery-note.md` 均为 0 次, 交付说明写"本轮结论仍需你 (需求方/调用者) 逐项确认", 与正文"你/我"分工一致. |

## 红绿两轮的实际做法与结果

| 轮次 | 会话 | 待测版本 | 产物 | 观察结果 |
| --- | --- | --- | --- | --- |
| R1 (红, 弱材料) | `i16-red`, 转录 `sessions/red-r1-thin.jsonl` | 旧版 | `drill-red-r1-thin/plan.md` | 作者日志缺命令与退出码, 会话把它排除, `/health` 排成本轮实跑. 未复现放行. 该夹具其后重建, 提交 `5745d4b` 已不存在, 只保留产物与转录. |
| R2 (红, 目标提交材料) | `i16-red2`, 未留产物 | 旧版 | 无 | 会话抓住"作者日志绑在代码提交而目标提交是随后的 docs 提交", 判为本轮实跑; 该次夹具把作者材料放进仓库, 目标提交与材料版本错开, 未构成"同一目标提交的作者日志". 结论作废, 不做证据. |
| R3 (红, 派工计划) | `i16-red`, 转录 `sessions/red-r3-targetcommit.jsonl` | 旧版 | `drill-red-r3/dispatch-decision.md` | `/health` 排成本轮实跑, 理由写成"作者自证材料, 不是独立观察"; 末尾交付口径出现"由用户做正式人工验收". |
| R4 (红, 规则说明) | `i16-red4`, 转录 `sessions/red-r4-targetcommit-policy.jsonl`, `sessions/red-r5-delivery-note.jsonl` | 旧版 | `drill-red-r4/dispatch-rule.md`, `drill-red-r4/delivery-note.md` | 结论仍是本轮实跑, 但"例外"一节自认"这条是为复验写的, 首次验收同样成立", 即通用派工与证据复核步骤没有这条规则; 两处"用户"照旧. |
| G1 (绿, 规则说明 + 交付口径) | `i16-green`, 转录 `sessions/green-r1-policy.jsonl` | 改后版 | `drill-green/dispatch-rule.md`, `drill-green/delivery-note.md` | 例外写进通用规则并引"首次验收与复验同一条"; `/health` 本轮实跑; 非关键旧观察仍可引用; 两处产物均无"用户". |

## 缺口与风险

1. 红演练没有让旧版会话真的放行关键路径. 三次红轮 (R1, R3, R4) 都靠模型自己的独立性判断兜住, 只是理由不在技能正文里 (R4 明说规则"是为复验写的"). 因此本 ISSUE 的红证据是"规则位置缺口: 通用步骤没有这条, 会话必须自行外推", 不是"已发生放行事故". 文本层面的缺陷 (规则只写在复验段) 已确认, 但本目录不据此声称任何真实验收曾经放过作者日志.
2. 作者材料是真实 curl 输出, 但没有截图. PRODUCT.md 的 AC-007-4 提到日志与截图, 本 ISSUE 只覆盖评审发现 3 的"首次验收"口子, 截图分支已在 `evidence/ISSUE-04/` 覆盖.
3. 夹具 `PRODUCT.md` 是手写标准, 只加了 `<!-- confirmed-flow: v1 -->` 标记, 未走 `workflow/to-spec` 的 preview/promote; 本轮判据只涉及该标记与场景原文, 不影响结论.
4. 视角断言的观察面是"会话产物怎么称呼需求方". 绿演练的交付说明写"你 (需求方/调用者)", 是面向我的报告口吻, 不是第三人称"用户"; 判定只要求没有第三人称混指, 不要求产品里出现"我"字.
5. 重建夹具时脚本曾把后台服务留在端口上, 让后续捕捉读到上一实例的 `ready=false`; 已改成由服务自身写 pid 文件, 停服后校验端口空闲, 最终两版作者日志都记录 `ready: true` 且 `18231` 交付前空闲.

## 清理与残留

- 演练会话: `i16-red`, `i16-red2`, `i16-red4`, `i16-red5`, `i16-green` 全部用 `herdr tab close` 关闭, 收尾 `herdr agent list` 无 `i16-*` 存活.
- 端口: 交付前 `ss -ltn | grep 18231` 无输出.
- 临时项目: `/tmp/orchestra-16/` 在证据抄完后删除.
- 未运行 `sync-to-pi.py`, 未写 `~/.agents`, `~/.pi` 或任何全局部署副本.
