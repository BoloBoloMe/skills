# ISSUE-03 演练记录: 非作者委派与场景组派工

本目录是 `docs/changes/verification-skills/issues/ISSUE-03-verify-change-non-author-dispatch.md` 的行为证据. 全部结论来自真实 pi 会话在临时 Git 项目上的实际运行, 不是源码关键词断言.

## 待测对象

- 源文件: 本工作树 `workflow/verify-change/SKILL.md` (分支 `issue/03`).
- 改动前版本 (红演练用): md5 `5351807e2e6b18d8ee3bf2696fa391bd`, 原件 `logs/SKILL-v1.md`.
- 改动后版本 (绿演练用): md5 `9ac67b01f3e9a5d3714e3292dcba6277`, 原件 `logs/SKILL-v2.md`.
- 本目录的演练只覆盖该源文件的这一版行为, 不表示任何全局部署副本已更新. 未运行 `sync-to-pi.py`.

## 宿主与加载方式

- 宿主: Ubuntu 26.04 LTS (x86_64); herdr 0.9.4 (client 与 server 同版); pi 1.3.0; Python 3.14.7 (uv 管理).
- 模型与深度: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 启动命令形态: `herdr agent start <会话名> --kind pi --pane <窗格ID> -- --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`; `-a` 只给该次会话做一次性项目信任, 未改全局配置.
- 加载方式: 把待测目录复制到临时项目的 `.agents/skills/verify-change/`, 在项目 cwd 开新 pi 会话, 用 `/skill:verify-change <任务>` 点名加载. 每个会话启动画面与 `~/.pi/agent/sessions/` 记录都显示加载的是项目内这份文件.
- 验收者由指挥者在演练中自行新开: 它们同样加载项目内的 `.agents/skills/verify-change/`, 但只执行自己的任务书.

## 实现基线与目标提交

- 真实实现会话: `i03-author`, pi 会话 `01a1541e-e67c-7356-a787-00cc0ec9b429`, 启动 2026-10-19 20:24:33 CST, 在 `/tmp/orchestra-03/author` 完成 `tool.py` 与测试改动并提交 `04be7ddd9ca795eecbb4a5b2d5beba24617509ed`, 作者时间 20:26:12 CST. 会话原始记录见 `sessions/author/`, 画面记录见 `logs/i03-author.log`.
- 各夹具的产品标准不同, 所以目标提交是 `04be7dd` 的 cherry-pick. 已核对补丁逐字节相同:

```
cd /tmp/orchestra-03/green-blocked && git show --format= --no-color HEAD | sha256sum
cd /tmp/orchestra-03/author && git show --format= --no-color HEAD | sha256sum
# 两者都是 8d161fe9ed5eee1b2fc5fb5822bc42a8126216a761f85d1cbc8bfa4d1ab2b34f
```

- 因此"未参与实现"的可核对事实是: 各验收者会话启动时间 (20:33-20:53) 晚于实现提交时间 (20:26:12), 且不等于 `i03-author` 的会话 ID, 不继承其会话过程.

## 夹具

脚本: `setup-drills.sh` (基础夹具), `setup-heavy-drills.sh` (批量型三组夹具), `setup-micro-drill.sh` (微检查组夹具). 全部只写 `/tmp/orchestra-03/`, 产品标准经 `workflow/to-spec/ac-draft.py preview/promote` 真实转正并带 `<!-- confirmed-flow: v1 -->`, 转正后再跑 `check-ac.py` 通过.

| 夹具 | 目标提交 | 场景数 | 审计 BR | 说明 |
| --- | --- | --- | --- | --- |
| `/tmp/orchestra-03/red-delegation` | `93ba124b07ddc1c9cd845a9f7f4256fc6dee8294` | 5 | 1 | 红演练: 单条命令场景 |
| `/tmp/orchestra-03/red-plan` | `f98bbfebfd974fd68a9f8f3b3ec616fdda637b44` | 3 | 1 | 红演练: 3 个只读检查, 共用 `dist/app.txt` |
| `/tmp/orchestra-03/green-non-author` | `2028383100c4d5c65789c3a56b13c44d6eba8da2` | 5 | 1 | 绿: AC-004-1, 工作量小, 只用于委派 |
| `/tmp/orchestra-03/green-two-groups` | `ceda596ed3a3e96d4348a466a98c5d1c625921dd` | 3 | 1 | 绿: 2 组, 2 人可用 |
| `/tmp/orchestra-03/heavy/three-groups-3avail` | `c0505dee33c9c78ffaaf61f88e05e041a7e29402` | 8 | 1 | 绿: 3 组批量检查, 3 人可用 |
| `/tmp/orchestra-03/heavy/three-groups-2avail` | `c0505dee33c9c78ffaaf61f88e05e041a7e29402` | 8 | 1 | 绿: 同一夹具, 2 人可用 |
| `/tmp/orchestra-03/green-single-group` | `42c51b8a51c216d5689a1c918c319ae4474aafd6` | 2 | 1 | 绿: 单一不可分组, 3 人可用 |
| `/tmp/orchestra-03/micro2/micro-groups` | `5d3765e9b0d8228b8738a75ea69baef048402c45` | 3 | 0 | 绿: 3 个微检查共用 22 秒准备, 3 人可用 |
| `/tmp/orchestra-03/green-blocked` | `ce3fefedde8bd9059a9828b9642011242e302206` | 5 | 1 | 绿: 无可用非作者 (受控条件) |

演练结束后各夹具的 git 状态见 `logs/fixture-status.txt`: 已跟踪源码, 配置, 测试的 `git diff` 全部为空, 唯一新增是各轮证据目录 (未跟踪); `dist/`, `__pycache__/` 在 `.gitignore` 内. 演练没有修改被验项目的产品代码.

## 会话一览

指挥者与验收者都由 herdr 真实启动; 会话标识取自 `herdr agent list` 与 pi 会话文件首行.

| 角色 | 会话名 | pi 会话 ID | 启动 (CST) | 工作目录 |
| --- | --- | --- | --- | --- |
| 实现 | `i03-author` | `01a1541e-e67c-7356-a787-00cc0ec9b429` | 20:24:33 | `author` |
| 红指挥者 | `i03-r1` | `01a15421-859c-755b-b259-07455291386e` | 20:27:25 | `red-delegation` |
| 红指挥者 | `i03-r2` | `01a15424-2737-72c2-b9ea-72616ff782b4` | 20:30:17 | `red-plan` |
| 指挥者 | `i03-g1` | `01a15425-cf90-7653-8498-e055e6f313dc` | 20:32:06 | `green-non-author` |
| 验收者 | `verifier-1` | `01a15426-b0b5-7604-80c4-85011cab7cae` | 20:33:04 | `green-non-author` |
| 指挥者 | `i03-g2` | `01a15425-eabf-713f-bd99-4bc1912b1d2f` | 20:32:13 | `green-two-groups` |
| 验收者 | `acc-a` | `01a15426-d0df-7234-a311-e5f9f6f4c036` | 20:33:12 | `green-two-groups` |
| 验收者 | `acc-b` | `01a15426-df72-7379-b53a-dbb6f851f163` | 20:33:16 | `green-two-groups` |
| 指挥者 | `i03-h1b` | `01a15430-5dcb-71d3-98da-39f401dfb696` | 20:43:38 | `heavy/three-groups-2avail` |
| 验收者 | `verifier-a` | `01a15431-088b-707c-939b-1dc526e03f8e` | 20:44:22 | `heavy/three-groups-2avail` |
| 验收者 | `verifier-b` | `01a15431-1447-75a1-b68f-ebbc50315c92` | 20:44:25 | `heavy/three-groups-2avail` |
| 指挥者 | `i03-h2` | `01a1542d-db88-72d2-b355-77b9e765b7de` | 20:40:53 | `heavy/three-groups-3avail` |
| 验收者 | `rev-greet` | `01a15430-62d7-73c3-b832-c7e2d68978ce` | 20:43:39 | `heavy/three-groups-3avail` |
| 验收者 | `rev-count` | `01a15430-79e5-75dd-8713-ce3864c7b9a5` | 20:43:45 | `heavy/three-groups-3avail` |
| 验收者 | `rev-export` | `01a15430-79f0-74a3-8df1-291b7849ec69` | 20:43:45 | `heavy/three-groups-3avail` |
| 指挥者 | `i03-g4` | `01a15432-c5f0-7727-bb88-8498f5dfc506` | 20:46:16 | `green-single-group` |
| 验收者 | `acc-verify` | `01a15433-cd28-77f7-a744-2113227a15f1` | 20:47:23 | `green-single-group` |
| 指挥者 | `i03-g5b` | `01a15438-e21c-713b-b21b-c8256e923b49` | 20:52:56 | `micro2/micro-groups` |
| 验收者 | `acc-g5b-1` | `01a15439-77f0-71ac-8f2f-b3f474f424da` | 20:53:34 | `micro2/micro-groups` |
| 指挥者 | `i03-g6` | `01a15432-fcac-7395-8da8-25082cb980f8` | 20:46:30 | `green-blocked` |

作废会话 (空任务重开, 中途消失的 `i03-h1`, 只查模型的辅助会话) 见 `incidents/host-incidents/README.md` 与 `SUMMARY.md`; 它们不作 AC 证据. 更早的微检查夹具重跑 (2 人) 见 `incidents/fixture-corrections/README.md`.

## 演练与验收标准对应

| 演练 | 夹具 | 技能版本 | 必验项 | 可用非作者 | 计划人数 | 实际验收者 | 支撑的断言 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `drill-R1-non-author-red/` | red-delegation | v1 | 6 | 3 | 未写计划 | 0 | AC-004 / AC-005 失败 (红) |
| `drill-R2-plan-red/` | red-plan | v1 | 4 | 3 | 未写计划 | 0 | AC-005 失败 (红) |
| `drill-G1-non-author/` | green-non-author | v2 | 6 | 3 | 1 | 1 | AC-004-1 |
| `drill-G2-two-groups/` | green-two-groups | v2 | 4 | 2 | 2 | 2 | AC-005-1 (2/2/2); AC-004-1 |
| `drill-G3-three-groups-3avail/` | heavy 3avail | v2 | 9 | 3 | 3 | 3 | AC-005-1 (3/3/3); AC-004-1 |
| `drill-G4-three-groups-2avail/` | heavy 2avail | v2 | 9 | 2 | 2 | 2 | AC-005-1 (3/2/2); AC-004-1 |
| `drill-G5-single-group/` | green-single-group | v2 | 3 | 3 | 1 | 1 | AC-005-2 |
| `drill-G6-micro-groups/` | micro2 | v2 | 3 | 3 | 1 | 1 | AC-005-3 |
| `drill-G7-blocked/` | green-blocked | v2 | 6 | 0 | 1 (无人可派) | 0 | AC-004-2 |

每个演练目录的 `NOTES.md` 记录该次的实际输入, 会话, 结果与限制; 目录内有会话自己写出的计划, 报告与原始材料. 每份 `PRODUCT.md` 是该夹具被验收的产品标准副本; `logs/author-commit.txt` 与 `logs/author-commit.patch` 是真实实现提交的完整信息与补丁.

## 机械复核

- 会话摘要: `SUMMARY.md` 由 `summarize-sessions.py` 从 `sessions/` 原始 JSONL 统计, 列出每个会话的启动时间, bash 次数, 真正执行成品 (`python3 tool.py ...`) 的次数, 执行 `prepare.sh` 的次数, `herdr` 控制调用次数, 写文件次数, 执行样例与第一条用户输入.
- 指挥者不亲自操作成品: 9 个指挥会话的 `product_runs` 都是 0 (红演练的旧版指挥者是 2 和 3); 验收者的 `product_runs` 都大于 0. `product_runs` 排除 `herdr pane send-text` / `herdr agent prompt` 这类把命令文本转交验收者的转发调用, 但写任务书的 heredoc 可能仍被计入, 所以逐条核对见 `NOTES.md` 与 `SUMMARY.md` 的执行样例. 表中的 `git commit` 列同样是文本线索 (有一个指挥者的该列来自读取会话文件的 Python 单行命令), 不表示它提交过.
- 不逐条 AC 开会话: 绿演练的必验项与会话数为 4/2 (G2), 9/3 (G3), 9/2 (G4), 3/1 (G5), 3/1 (G6), 6/1 (G1); 计划里明确写了"不按 AC 逐条开".
- 自主启动不例行等批准: 各绿演练的计划写完后同一会话直接建 tab 并启动验收者, 没有再向用户提问; 会话记录里没有"等待批准/请确认"一类的段落 (可对 `sessions/*/*.jsonl` 与 `SUMMARY.md` 复核), `drill-G4-three-groups-2avail/dispatch-time.txt` 留了派工时间 `2026-10-19T20:44:49+08:00`.
- 未参与事实: 每份计划都写了验收者会话标识, 创建时间与实现提交时间的先后; 原始会话文件首行给出会话 ID 与启动时间, 可与 `SUMMARY.md` 对照.

## 机械检查命令与退出码

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` | 0 | `OK` |
| 全角标点扫描 (`rg` 扫 U+3001, U+3002, U+FF0C, U+FF1B, U+FF1A, U+FF01, U+FF1F, U+FF08, U+FF09) 覆盖 `workflow/verify-change/SKILL.md`, 三个 setup 脚本, 以及本目录我写的 `README.md` / `HANDOFF.md` / 各 `NOTES.md` / `incidents/*/README.md` / `summarize-sessions.py` | 1 (无命中) | 无输出 |
| 同一扫描对会话原始材料 (`drill-*/**`, `logs/`, `sessions/`) | 命中 | 保留会话与验收者自己写出的原文, 不做标点改写; 命中只出现在这些原始记录里 |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | 7 passed, 18 subtests passed |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | 6 failed, 659 passed, 2 skipped; 与 ISSUE-02 HANDOFF 记录的既有失败集合完全一致 (present 浏览器 5 条 + mailbox pending_cap 1 条), 本次未新增 |
| `bash setup-drills.sh <工作树> init` | 0 | 建立 9 个初始夹具, PRODUCT.md 经 `ac-draft.py preview/promote` 转正, `check-ac.py` 通过 |
| `bash setup-drills.sh <工作树> apply-author-change 04be7dd...` | 0 | 9 个夹具 cherry-pick 实现提交, 工作区干净 |
| `bash setup-heavy-drills.sh <工作树> 04be7dd...` | 0 | 建立 2 个批量型夹具, 工作区干净 |
| `bash setup-micro-drill.sh <工作树> 04be7dd...` | 0 | 建立微检查组夹具, `prepare.sh` 实测 22.24 秒 |
| `uv run python summarize-sessions.py` | 0 | 24 个会话写入 `SUMMARY.md` |

## 清理

- 全部演练会话与子会话已用 `herdr tab close` 关闭 (关闭前的完整列表见 `logs/agents-after-all.json` 与 `logs/tabs-after-all.json`).
- 临时项目 `/tmp/orchestra-03/` 已在证据抄完后删除 (`ls /tmp | grep -c orchestra-03` 为 0); 需要复跑时用三个 setup 脚本重建. 夹具的 git 状态快照保留在 `logs/fixture-status.txt`.
- 证据目录只保存验收输出与原始会话记录, 不含密钥或凭据. 未写入 `~/.agents`, `~/.pi`, 未运行同步.

## 限制

- 结论只覆盖本记录的组合: 上述源文件版本 + herdr 0.9.4 + pi 1.3.0 + 该模型与思考深度 + 项目 `.agents/skills/` 加载方式. 其他运行时或全局部署未验证.
- "没有可用非作者会话"是受控条件 (任务声明 + 会话清单), 不是真实配额系统耗尽.
- 并行执行顺序, 证据共享与复验属 ISSUE-04, 本目录不承诺.
