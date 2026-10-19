# HANDOFF: ISSUE-16

## 状态

完成. 分支 `issue/16`, 工作树 `/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-16`.

## 交付了什么

只改一个文件: `workflow/verify-change/SKILL.md`.

1. 关键路径规则进通用步骤 (对应评审发现 3 与 STANDARDS H4 的判据缺口):
   - 第 4 步 (分组与派工计划) 的材料来源段落改成先分"本轮实跑 / 引用旧观察 / 未验证"; 受影响的关键真实路径一律排给验收者本轮自己走一遍成品入口, 首次验收与复验同一条, 作者留下的通过日志, 截图, 自测说明只当对照材料. 非关键旧观察仍按条件复用, "已足够的观察重复跑"的成本理由只留在非关键路径上.
   - 第 4 步完成标准加一条: 受影响的关键真实路径都排成本轮实跑.
   - 第 8 步 (复核材料与证据类型) 加一段: 作者在实现或修复期间留下的通过材料归入引用的旧观察, 受影响的关键真实路径即使有作者通过材料也只取本轮实跑记录, 冲突按摘要与原件冲突处理.
   - 复验第 4 条从重复陈述改成指针, 指向第 4 步与第 8 步, 保持单一真相源.
2. 视角统一: 正文里指需求方的第三人称"用户" 8 处改为第一/第二视角 (批准, 复核, 裁决, 交付说明), 开场角色句改为"你是独立验收指挥者". 现在正文 `用户` 出现 0 次, 也不改 PRODUCT/TECHNICAL 等其他文件.

未新增 reference 文件, 未改其他技能, 未动 Spec/决策, 未运行 `sync-to-pi.py`.

## 每个 AC 对应的证据

证据目录 `docs/changes/verification-skills/evidence/ISSUE-16/`, 索引见其中 `README.md`.

- AC-1 (关键真实路径首次验收必须非作者实跑):
  - 绿: `drill-green/dispatch-rule.md` 的"例外: 有, 而且只朝一个方向"与"AC-001-1 的材料来源决定" (结论为"本轮实跑. 不引用旧观察", 并写明首次验收与复验同一条, 作者材料类型固定, 冲突处理方向).
  - 红: `drill-red-r4/dispatch-rule.md` 的例外第 2 条自认"这条是为复验写的, 首次验收同样成立", 即旧正文只在复验段有这条规则; `drill-red-r3/dispatch-decision.md` 也靠会话自己的独立性判断兜住, 不是正文要求.
  - 非关键对照: 绿版同一规则仍允许非关键旧观察按条件引用, 判据未被扩大.
- AC-2 (视角统一为"你"与"我"):
  - 静态: `logs/skill-hashes.txt` 记录两版 md5; `logs/SKILL-red.md` 出现"用户" 8 次, `logs/SKILL-green.md` 0 次.
  - 行为: 红演练产物 `drill-red-r4/dispatch-rule.md` 与 `drill-red-r4/delivery-note.md` 各有 2 次"用户"; 绿演练 `drill-green/dispatch-rule.md` 与 `drill-green/delivery-note.md` 均 0 次, 交付说明写"本轮结论仍需你 (需求方/调用者) 逐项确认, 本轮写入范围由你批准".

## 跑过的命令与退出码

- `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` -> 退出 0, 输出 `workflow/verify-change/SKILL.md: OK` (改动前与改动后各一次).
- 全角标点扫描 `rg -n "[\x{ff0c}\x{3002}\x{ff1b}\x{ff1a}\x{ff01}\x{ff1f}\x{3001}\x{ff08}\x{ff09}\x{3010}\x{3011}]" workflow/verify-change/SKILL.md docs/changes/verification-skills/evidence/ISSUE-16/README.md .../setup-drills.sh` -> 无命中 (退出 1); 演练产物与两版 SKILL 副本同样无命中. 会话转录里出现的全角标点是模型的思考原文, 属原始材料, 不是本仓库文档.
- `rg -n "用户" workflow/verify-change/SKILL.md` -> 无命中 (退出 1).
- `uv run --with pytest python -m pytest -m "not e2e" -q` -> `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 274.56s`, 6 条失败与 `evidence/BASELINE.md` 的既有失败集合逐条一致, 原始输出 `logs/pytest-not-e2e.log`.
- 英文残留: 两版 SKILL 的英文只有命令, 路径, 字段名与被调用的技能名 (`PRODUCT.md`, `gherkin`, `benchmark-checklist`, `blast-radius`, `herdr` 等), 均属保留类型; 新增中文正文没有引入新英文术语.

## 会话与临时项目

- 夹具: `/tmp/orchestra-16/red-first-acceptance` 与 `/tmp/orchestra-16/green-first-acceptance`, 起始提交 `c627cf1b57ee9aae135f36d00b7e8d021bfde2e1`, 目标提交 `65114d4ad0ff42e13c31cc111be82edf0a365b56`; 作者日志 `/tmp/orchestra-16/author-logs-red/`, `/tmp/orchestra-16/author-logs-green/`.
- 会话 (全部已用 `herdr tab close` 关闭, 收尾 `herdr agent list` 无 `i16-*`):
  - `i16-red` (R1, R3), `i16-red2` (R2, 作废), `i16-red4` + 续问 (R4, R5), `i16-green` (G1).
  - 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动加 `-a`; 加载方式 `herdr tab create --cwd <项目>` 后 `/skill:verify-change <任务>` 单行点名.
- 转录: `sessions/red-r1-thin.jsonl`, `sessions/red-r3-targetcommit.jsonl`, `sessions/red-r4-targetcommit-policy.jsonl`, `sessions/red-r5-delivery-note.jsonl`, `sessions/green-r1-policy.jsonl`.
- 收尾: `ss -ltn | grep 18231` 无输出; `/tmp/orchestra-16/` 在证据抄完后删除.

## 缺口, 风险与未验证项

1. 红演练没有让旧版会话真的放行关键路径. 三次红轮都靠模型自己的独立性判断兜住, 红证据是"规则位置缺口: 通用派工与证据复核步骤没有这条, 会话必须自行外推" (R4 明说规则"是为复验写的"), 不是已发生的放行事故. 不据此声称任何真实项目验收曾用作者日志放行.
2. 作者材料是真实 curl 输出, 没有截图; 截图分支已由 `evidence/ISSUE-04/` 覆盖, 本 ISSUE 不重复.
3. 夹具 `PRODUCT.md` 是手写标准, 只加了 `<!-- confirmed-flow: v1 -->` 标记, 未走 `workflow/to-spec` 的 preview/promote; 本轮判据只用到该标记与场景原文.
4. 演练中夹具脚本曾把后台服务留在端口上, 让后续捕捉读到上一实例的 `ready=false`; 已改成服务自身写 pid 文件并在停服后校验端口空闲, 最终两版作者日志均为 `ready: true`, 交付前端口空闲. 这一段排查只影响夹具, 不影响待测技能.
5. 视角断言的行为观察面是"会话产物怎么称呼需求方"; 绿演练写成"你 (需求方/调用者)"是面向我的报告口吻, 判定只要求没有第三人称"用户"混指, 不要求产物里出现"我"字.

## 提交

- 内容与证据提交: `917ae12b` (`feat: ISSUE-16: 关键路径首次验收必须非作者实跑, 视角统一`). 本行由随后的 `docs: ISSUE-16: 补记提交哈希` 提交写入.
- 工作区: 提交后 `git status` 干净 (证据目录随提交入库, 未跟踪的临时项目都在 `/tmp`).
