# milestone-05 实跑验收: 发现的问题

本文是 milestone-05 (同步到 pi 并在真实会话上实跑验收) 的产物. 它只记录问题, 不给最终方案: 每条问题的解决方案另行讨论. 读本文不需要会话日志之外的任何前提.

## 1. 这次验收怎么跑的

- milestone-05 的要求 (见 `roadmap/ROADMAP.json`): 用户跑 `uv run python sync-to-pi.py` 同步到 pi, 在一个真实会话上调用 `review-session` 跑一次, 检查能否定位并读完指定会话, 候选是否都指向真实存在的东西, 有没有提到 pi 里不存在的工具或机制, 触发条件是否有用, 花了多少 token.
- 实际执行: 用户没有同步到真实 agent 目录 (`~/.agents/skills/review-session/` 本次实测不存在), 而是让 agent 直接读仓库里的 `general/review-session/SKILL.md` 并照它执行. 同步这一步仍未验证.
- 用户指令: `读取 general/review-session/SKILL.md, 复盘当前容器内的 pi 会话.`
- skill 默认复盘"当前会话", 而当前会话当时只有这一条指令, 于是把复盘对象扩到本容器全部有内容的会话, 共 9 个, 加当前会话共 10 个.
- 开销: 本次实跑 (当前会话) 到写本文前 35 轮, 累计计费口径 input 约 8.0 万 token, output 约 3.4 万 token.
- 验收结论: 定位会话和读完全文可行; 每条候选都能追到具体时刻; 触发条件够用; 报出的候选里只有一处提到容器里不存在的工具 (jq, 见问题 5). 8 个候选里 6 个值得落 (本文第 3 节), 2 个本次不落 (第 4 节).

## 2. 证据在哪

会话日志目录:

```text
~/.pi/agent/sessions/--home-bolo-Workspace-review-old-sessions--/
```

目录名 = `--` + 容器内工作目录去掉开头的 `/` 再把 `/`,`\`,`:` 换成 `-` + `--`. 文件名 = `时间戳_会话id.jsonl` (时间戳里的 `:` 和 `.` 换成 `-`). 文件每行一个 JSON; 首行 `type: "session"` 是会话头, 含 `id`, `timestamp`, `cwd`. 定位一次会话最可靠的键是 `cwd + 会话 id`, 时间戳辅助, 关键词只在候选缩小后检索.

本容器 9 个有内容的会话 (按开始时间):

| 开始 | 会话 id | 字节 | 用户消息 (不含 skill 调用) | 内容 |
| --- | --- | --- | --- | --- |
| 10-06 14:12 | 01a1118e | 479272 | 10 | 定义 review-session skill 的第一次 navigate 会话; 交付路线图页面给远程用户 |
| 10-06 14:42 | 01a111aa | 691256 | 2 | navigate 航行会话; 在 herdr 里开两个子会话做 milestone-01/02 调查 |
| 10-06 14:46 | 01a111ae | 1202423 | 1 | 子会话: milestone-01 会话日志读法调查 |
| 10-06 14:46 | 01a111ae | 867140 | 1 | 子会话: milestone-02 检查与护栏调查 |
| 10-06 15:53 | 01a111eb | 621638 | 8 | milestone-03 盘问与决策账本; 派两轮校验子代理 |
| 10-07 01:57 | 01a11414 | 101770 | 1 | 子会话: 对决策账本做对抗性分析 |
| 10-07 02:06 | 01a1141c | 628427 | 1 | 子会话: 第 1 轮校验 (抓出 8 处问题) |
| 10-07 02:23 | 01a1142c | 471134 | 1 | 子会话: 第 2 轮校验 (抓出 2 处记账问题) |
| 10-07 02:31 | 01a11433 | 363085 | 3 | milestone-04 落地 review-session skill 与 README |

(两个 14:46 的会话 id 前缀相同, 完整 id 见文件名; 字节数用于在清单里对号.)

查一个关键词落在哪一行: `rg -n '<关键词>' <会话文件>`, 再读该行. 按消息角色抽取的脚本见 `milestone-01/findings.md` 第 2.3 节.

## 3. 值得落的 6 个问题

### 问题 1: 在 herdr 里开子会话时, 一串假报错把 8 分钟和大量 token 耗在试错上

类别: 工具开销 / 导航.

背景: 这个会话 (01a111aa) 要开两个子会话, 分头做 milestone-01 和 milestone-02 调查. 做法是用 herdr 建窗格, `agent start` 起会话, 再把任务文字喂进去.

现象与证据:

- 14:44:52 `herdr agent prompt` 两次返回 `agent_prompt_stalled` ("agent prompt produced no observed working or blocked state within 5000 ms"). 任务文字其实已经送进窗格.
- 14:45:23-14:45:37 关掉两个 tab (w1:t3/t4), 重建 (w1:t5/t6), 并加上 `-- --model ai-work-openai/gpt-5.6-luna`.
- 14:46:33-14:46:40 又关掉重建一次 (w1:t7/t8), 这次把首条任务放在 `agent start` 的 `--` 之后, 结果两次都报 `timed out waiting for agent startup`, 但子会话其实已经开工.
- 14:47:31 `herdr agent wait research01` 报 `agent_not_found`: 启动时给的名字在等待时不认, 只能改用窗格编号 (如 `w1:p7`). 14:47:44 改窗格编号后进入长时间 `timed out waiting for agent status`, 反复到 15:06 左右.
- 该会话共 23 个错误, 绝大多数出自这一串.
- agent 在 14:43 已经读过 `use-herdr` 说明书, 仍未避开, 说明现有措辞没给出可直接执行的分支.
- 另外 `herdr agent read <name> --source recent-unwrapped` 在会话工作中会直接报 `agent_not_idle`.

影响: 每有一轮并行的子会话编排, 就重付一次这份试错成本. 本次约 8 分钟, 且会话上下文累计 token 被这些失败回合推高.

待讨论方向: 在 `general/use-herdr/SKILL.md` 收紧 stalled/timeout 段 (读 `agent get` 与 `pane read` 后再决定, 禁止重建, 用窗格编号等待, 带首条任务的启动超时属预期); 或改 herdr 命令本身的失败信号; 或两者都做.

### 问题 2: 容器里打不开 navigate 的路线图页面, 靠给宿主会话发信才纠正

类别: 信息获取.

背景: navigate 自带一个网页服务, 把 `ROADMAP.json` 渲染成页面给用户看. 用户通过 VPN 远程访问容器.

现象与证据 (会话 01a1118e):

- 14:30:42 用户要求内网地址.
- 14:31:44 agent 给 `http://192.168.65.165:39271/?roadmap=...`.
- 14:32:23 用户报 502 Bad Gateway. agent 判断是代理够不到容器网段, 另外起了一个 `/tmp` 里的转发进程把容器 8800 转到 39271, 14:33:14 改口给 `127.0.0.1:34337`.
- 14:35:08 用户说两个都不行, 要求让宿主侧 LLM 一起查. agent 用 mailbox 给宿主会话发信, 14:36:32 才拿到正确地址 `http://192.168.65.165:34337/?roadmap=...`.
- 14:37:00 用户又报页面拒绝, 原因是他手上那条 URL 被截断, 路径结尾只剩 `.../roa`, 服务只服务 `.json`.
- 14:40:47 用户确认页面可用.

根因:

- `workflow/navigate/scripts/web_server.py:43` 写死 `DEFAULT_PORT = 39271`, 且不支持指定 bind 或 fixed-port.
- 容器对外只有固定 8800 会被宿主映射 (present 的容器内分支按这条约定做, 见 `general/present/SKILL.md` 容器内分支与 `general/use-sandbox-worktree/SKILL.md` 的展示链一节), 宿主实际发布端口在容器环境变量 `SWT_HOST_WEB_PORT` (本容器为 34337). navigate 的页面服务不在这条链上.
- 容器里拿不到宿主已确认的局域网地址 (确认值在宿主侧 `records_root`, 容器内不可读), 只能问宿主会话.

影响: 6 分钟中断, 用户被卡住, 且要额外一次跨会话通信才恢复. 对"把路线图给远程用户看"这个高频动作, 每次都要重来.

待讨论方向: 让 navigate 的页面服务复用 present 容器内分支的端口语义; 或在 navigate 说明书里写清容器内交付 URL 必须用宿主映射端口; 或把宿主已确认的局域网地址与映射端口注入容器环境.

### 问题 3: 容器里没配 git 身份, 而全库规则强制收口提交, 所以每个新容器第一次提交必挂

类别: 自动检查.

背景: 全局规则要求 "任务改动收口后主动提交并推送". 提交时 git 需要作者名字和邮箱.

现象与证据 (会话 01a1118e, 14:40:53):

```text
git commit -q -m "doc: 绘制地图 ..." && git push ...
Author identity unknown
*** Please tell me who you are.
```

随后 agent 用 `git log -3 --format='%an <%ae>'` 翻出既有作者 `bolo <921402781@qq.com>`, 再 `git config --local user.name bolo` 与 `--local user.email ...`.

- 实测 `~/.gitconfig` 不存在, 全局身份为空.
- `--local` 写在 `.git/config`, 不进版本库, 换新容器或新克隆即丢.

影响: 每个新容器的第一次提交都要先失败一次, 再由 agent 现场考古既有作者再补配. 这是一条每次都会重复的固定损耗, 也容易让 agent 顺手编一个错的作者名.

待讨论方向: 在容器镜像层放全局身份 (镜像 `~/.gitconfig` 或 `git config --system`), 取值用本仓库既有作者; 落点属 use-sandbox-worktree 的镜像准备环节. 或者给提交加一道自动检查.

### 问题 4: 执行者写进决策账本的"事实"没查证, 被两个独立校验子代理抓出 6 到 8 处

类别: 编码规范 / 自动检查.

背景: 会话 01a111eb 里 agent 一边盘问一边把结论写进 `docs/changes/review-session-skill/milestone-03/DECISIONS.md`, 写完派了第 1 轮校验子代理 (会话 01a1141c, 模型 gpt-5.6-luna).

现象与证据 (agent 在 02:11:36 转述校验结果, 原文摘要):

1. F009 的措辞像在说 `general/review-session/SKILL.md` 现在已经存在, 与 D001 "新建" 冲突.
2. F002/D005 写 "仓库已有 `CONTRIBUTING.md` 等规范文档可沿用", 与本仓库实际没有 `CONTRIBUTING.md` 冲突.
3. F007 把 `空操作`,`上下文负载`,`指针` 归到 `docs/language/UBIQUITOUS_LANGUAGE.md`, 实际这些词在 `general/writing-for-llm/SKILL.md`.
4. D004 用 "pi 中不存在 `CLAUDE.md`" 当替换理由, 但 pi 实际支持 `CLAUDE.md` 上下文文件.
5. D002 把 `disable-model-invocation: true` 说成 "必须由用户在会话结束时调用".
6. D008 漏了目的地要求的 "建议动作必须指向真实存在的文件或机制".
7. D004 要求写死全局路径 `~/.pi/agent/AGENTS.md`, D012 又要求不钉死 pi 独有路径, 两条冲突.
8. 缺源版 `/retro` 到 pi 调用方式的映射.

第 2 轮校验 (会话 01a1142c, 模型 gpt-5.6-terra) 又抓出 2 处: 已被替代的旧决策仍标着 "必须遵守", 新决策里还写着 "照旧决策 X/Y 来". 用户本人在 02:22:22 也驳回了 2 条 (不写死路径; skill 也可以读取和分析 `CLAUDE.md`).

影响: 记账文档是后续会话的权威输入, 事实写错会把错传下去. 这一轮里 8 条中 6 条是"声称仓库/pi 里有什么"这类可机器核对的事实, 却全靠人工校验子代理发现, 代价是一整个子会话加一轮返工.

待讨论方向: 把 "文档里提到的仓库路径或文件名必须存在" 做成确定性检查 (仓库 `tests/` 下已有 `tests/pi/skill-anywhere.test.mjs` 这类针对文档的测试可参照); 判断题部分再另建规范文档 (本仓库当前没有 `CONTRIBUTING.md` 或 `CODING_STANDARDS.md`).

### 问题 5: 读会话日志没有现成工具, 容器里连 jq 都没有

类别: 工具开销 / 信息获取.

背景: 两个子会话 (01a111ae) 的任务是查清 pi 会话日志怎么读, 日志是一行一个 JSON 的文件.

现象与证据 (会话 01a111aa 的父会话, 在等子会话时自己也在抽日志):

- 15:02:26 两次 `jq -r '...' "$F" | tail` 返回 `jq: command not found`. 任务简报本身写的是 "用 rg/jq 或同类现有命令", 把 jq 当既有工具.
- 15:02:34 改用 node 现写解析脚本, 两次报 `TypeError: c.map is not a function`, 原因是日志里 `message.content` 有时是字符串, 有时不存在, 不一定是有 block 的数组.
- 15:06:57 另一个 node 脚本报 `ReferenceError: file is not defined`.
- 实测容器内 `jq` 不存在, `node` 与 `python3` 存在.

影响: 每次复盘都要现场拼一次性解析脚本, 每次都在 `message.content` 的形状上踩一遍. 对 review-session 这个 skill, 这是它每次运行的入口动作.

待讨论方向: 镜像里装 jq; 或在文档里写清会话 JSONL 的形状要点 (含 `message.content` 可能是字符串或缺省); 或提供一个只读的抽取小工具.

### 问题 6: 全局规则里那行 `~/AGENTS.md` 指针指向不存在的文件

类别: 空操作 / 信息获取.

背景: 全局工作规则 (`/home/bolo/.pi/agent/AGENTS.md`, 源头是仓库 `pi/AGENTS.md`) 第 5 行写着 "需要了解当前环境信息时, 可尝试读取 `~/AGENTS.md`; 文件可能不存在, 不存在时继续处理."

现象与证据:

- 会话 01a111ae 在 14:47:08 执行 `read /home/bolo/AGENTS.md`, 返回 `ENOENT`.
- 会话 01a11414 在 01:58:05 再次执行同样的 read, 同样 `ENOENT`.
- 实测 `/home/bolo/AGENTS.md` 不存在.

影响: 规则自己声明了可能不存在, 所以它不改变 agent 的后续行为, 只制造一次注定失败的调用. 影响小, 但每次运行都付一次.

待讨论方向: 删掉这行; 或真的在容器里放一个 `~/AGENTS.md`; 或把这类环境事实挪到一个真实存在的文件里.

## 4. 本次不落的问题 (备回访)

- 仓库没有 CI, pre-commit 与 lint, 且 `tests/run` 的改动面映射与它自己声明的唯一事实源 `tests/README.md` 不一致 (会静默返回"无可跑项"后照样提交). 证据: `milestone-02/findings.md` 第 2.2 至 2.4 节, 以及会话 01a11433 在 02:3x 收口时的实测输出. 用户本次判定不落.
- `~/.pi/agent/settings.json` 里有两条不存在的模型 (`kimi-coding/k3-256k`, `kimi-coding/k3`) 和一条不存在的扩展路径, 每次启动打印 `Warning: No models match pattern ...`. 证据: 会话 01a111aa 14:45:15 的 `pi --list-models` 输出, 与 `milestone-02/findings.md` 第 1.2 节. 用户本次判定不落.

## 5. 待拍板的问题

1. 问题 1 落点选哪个: 只改 `use-herdr` 说明书, 还是同时改 herdr 的失败信号.
2. 问题 2 的端口语义: navigate 跟 present 对齐, 还是只在 navigate 说明书里写约定, 还是两件都做; 宿主已确认的局域网地址要不要注入容器.
3. 问题 3 的落点: 镜像层全局 git 身份, 还是提交前自动检查.
4. 问题 4 的机械检查范围: 只查"提到的路径是否存在", 还是也查术语归属; 以及要不要新建规范文档.
5. 问题 5 是否只装 jq, 还要不要顺带把会话日志形状写进文档.
6. 问题 6 选删规则还是补文件.
