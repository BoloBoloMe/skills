# agent-env-followups 决策账本

本账本记录一组 AI coding agent 环境改进的决策. 问题来源: [review-session-skill milestone-05 findings](../review-session-skill/milestone-05/findings.md) 里的 6 条实跑问题. 逐条方案经 2026-10-07 与用户盘问敲定 (pi 会话 `01a114ea-bf95-76c9-8677-6c0eb5907abf`), 并过了一轮独立反方攻击 (子代理会话 `01a11532-6b42-730f-85a5-b4dd1a864384`), 成立项已并入.

## 决策

### D001 use-herdr 按 writing-for-llm 重构为分层结构
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 按 [`general/writing-for-llm/SKILL.md`](../../../general/writing-for-llm/SKILL.md) 完全重构 `general/use-herdr/SKILL.md`, 正文压到 60-80 行, 只保留: 分派三支 (自己操作 / 学习安装排查 / 官网), 环境检查, 学习当前 CLI, 驱动 agent 全流程 (默认策略, start, 提交, 等待与 stalled 处理, 读取), 以及一张指针表. 其余按需查阅的参考材料披露到三个新文件: `layout.md` (布局与原语, ID 语义, 调用方上下文, 发现命令, agent 生命周期状态), `pane.md` (兄弟窗格几何与焦点, `pane run`/`wait-output`/`read` 的 source 语义, alternate screen 兜底, 清理已完成会话), `rules.md` (安全与协调规则). `PI.md` 保留并瘦身, `machine.md` 不动. 理由: 现有正文 208 行, 大部分是按需参考材料, 把真正要执行的流程埋住, 导致关键操作落在注意力低洼区被漏读 (本会话实测漏读 `PI.md`, 见 F003/F014); writing-for-llm 的判据是每个分支都要用的内联, 只有部分分支触及的披露到指针后面, 分支即最干净的披露测试.
- 依赖事实: F003, F014
- 预计影响: `general/use-herdr/SKILL.md`, 新建 `general/use-herdr/layout.md`/`pane.md`/`rules.md`, `general/use-herdr/PI.md`

### D002 use-herdr 行为文案四处修正
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 随 D001 一并改, 四点: (a) 驱动 agent 时首条任务不放 `herdr agent start` 的 `--` 之后 (`--` 是 agent 自身参数, 不是任务通道); 先 `start`, 再用提交方式送任务. (b) 任何 `agent_prompt_stalled` 或超时之后, 第一步是 `herdr agent get` + `herdr agent read`; 按观测结果分状态收尾: 任务已送达或 agent 仍在跑 → 继续等待, 不重建; agent 或窗格已消失 → 才允许重建或重开; `blocked` → 先看 UI 并问用户. 不写成"一律禁止重建", 因为那会把程序已死的情形也堵死. (c) `agent wait` 报 `agent_not_found` 时改用窗格 ID, 不重试同名. (d) `agent read` 报 `agent_not_idle` 表示 agent 正在干活, 不是错误, 改用 `pane read` 或等待. 理由: findings 记录该会话 23 个错误绝大多数出自这一串, agent 读过说明书仍踩; herdr 是第三方二进制, 改不了它的失败信号 (F002).
- 依赖事实: F002, F003
- 预计影响: `general/use-herdr/SKILL.md`

### D003 每个容器预留 6 个 web 端口 8800-8805
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 每个 sandbox 容器在 22/6080 之外预留 6 个容器内 web 端口 8800 到 8805. 宿主一律用 `0.0.0.0` 动态端口发布 (禁止回环), 各宿主端口经 birth 烘入容器环境变量 `SWT_HOST_WEB_PORT` (对应 8800) 与 `SWT_HOST_WEB_PORT_2` 到 `SWT_HOST_WEB_PORT_6`. STATE 登记全部映射. 交付包仍只列 8800 一条, 预留口不列. 理由: 容器对外只有一个 web 口 8800, 而 present 与 navigate 是两种不同的展示服务 (F005), 同时用必撞车; 宿主只发布 8800, 别的容器端口宿主看不见. 所以要多留; 又因端口映射建容器时定死, 加口必须重建容器, 一次多留几个比以后反复重建划算. 本条修订 M04 D001 "容器对外 web 端口固定为一个 8800" 的口径 (一个口 → 从 8800 起的一段口).
- 依赖事实: F005, F006, F008
- 预计影响: `workflow/use-sandbox-worktree/scripts/swt.py` (create 的 `-p` 列表, STATE 记录, 宿主信息 env), `workflow/use-sandbox-worktree/scripts/image-prep.py` 的 base `EXPOSE`, `workflow/use-sandbox-worktree/SKILL.md` 端口契约与展示链节, 对应测试
- 需要调整: M04 D001 待补记 (一个口改口径为一段口); `docs/changes/swt-cross-host-access/` 下引用单口 8800 的下游产物待检查

### D004 navigate 在容器里的展示配方
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 8800 固定归 present; navigate 固定用 8801, 不做"从 8801 起挑第一个空口". 容器内用 socat 把 8801 桥接到 navigate 自带服务的实际端口 (端口从服务启动的 stdout 读), 桥随 navigate 服务生死: 服务停则清桥, 碰到残留死桥先清. 页面 URL 由容器自算, 但只在容器内非环回 IPv4 恰好一个且端口环境变量齐备时; 否则发 mailbox 问宿主取已确认的局域网地址. 端口变量注入失败保持软失败, 但交付包显式打一行 "web 端口未注入, 页面需走信箱协商". 不改 navigate 代码. 理由: M04 D010 要求用已确认的局域网地址, 不猜网卡, 自算必须加这条护栏才不违; "挑空口"有竞态 (两次探测同时看到空) 和残留桥占口两个问题, 固定口加生命周期就够.
- 依赖事实: F001, F005, F007, F008
- 预计影响: `workflow/navigate/SKILL.md` (加容器展示配方); `workflow/navigate/scripts/web_server.py` 不动

### D005 git 身份在 birth 时键级注入
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: birth 时在容器内用键级写入 `git config --global user.name bolo` 与 `user.email 921402781@qq.com`, 合并进现有 `~/.gitconfig`, 不覆盖整份文件; 写完读回验证. 不放镜像层 (要重建 base 且只对重建后新建的容器生效). 身份名取 `bolo` 而非 `luojingyan`, 与容器用户名一致, 也是容器内已形成的现状 (F010). 理由: 每个新容器第一次 commit 因无身份必失败, agent 再翻历史作者补配, 每次重付.
- 依赖事实: F010
- 预计影响: `workflow/use-sandbox-worktree/scripts/swt.py` (birth), 对应测试

### D006 不做账本事实的机械检查
- 状态: 当前有效
- 约束性: 可调整
- 内容: 决策账本里"某路径是否存在"这类可机器核对的错误, 继续靠审核或校验子代理发现, 不加自动测试. 理由: 用户判定, 反方攻击主张加窄范围机械检查 (只查仓库内路径存在性), 用户维持原判.
- 依赖事实: F012

### D007 jq 加进 base 镜像需求清单
- 状态: 当前有效
- 约束性: 可调整
- 内容: 只把 jq 加进 base 层需求清单, 消除容器内 `command not found`. 不为会话日志 JSONL 形状写文档, 也不做只读抽取脚本. 理由: 用户只选了装工具; 形状知识继续由使用者现场处理. jq 随下次 base 重建生效, base 更新会级联淘汰 display 与项目层 (F009), 不为它单独重建.
- 依赖事实: F009, F013
- 预计影响: `workflow/use-sandbox-worktree/scripts/image-prep.py` 的 base 需求清单与 apt 行

### D008 全局规则里的 `~/AGENTS.md` 指针不动
- 状态: 当前有效
- 约束性: 可调整
- 内容: `pi/AGENTS.md` 里"需要了解当前环境信息时, 可尝试读取 `~/AGENTS.md`"保持原样. 该行已声明文件可能不存在, 成本有界 (容器内一次注定失败的调用); 宿主机上可能有用途, 删了可惜. 理由: 用户判定暂缓.
- 依赖事实: F011

### D009 落地方式
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 本组改动落新目录 `docs/changes/agent-env-followups/` (本账本所在), 按逻辑单元实现并逐次提交推送, 不画 navigate 路线图. 理由: 决策已谈定, 再画一层路线图是重复劳动; 但决策必须落成账本, 否则后续会话不知为何这么定.
- 预计影响: 全部 D001-D008 的落点

## 事实

### F001 容器 IP 与宿主映射端口
- 状态: 当前有效
- 来源: 本容器命令实测 (`ip -4 addr`, `env`, `/etc/hosts`)
- 内容: pasta 下容器无独立 IP; 容器 `eno1` 的 192.168.65.165 即宿主局域网地址 (与 findings 里最终可用 URL 的主机一致); 宿主映射端口烘在 `SWT_HOST_WEB_PORT=34337` (与可用 URL 的端口一致).

### F002 herdr 是第三方静态二进制
- 状态: 当前有效
- 来源: `image-prep.py` base Containerfile (curl herdr releases v0.9.0); `herdr --version`
- 内容: 本仓库没有 herdr 源码, 改不了它的超时与错误信号, 只能改使用它的文档.

### F003 pi 的提交键是 `alt+\`
- 状态: 当前有效
- 来源: `general/use-herdr/PI.md`; 本会话实测
- 内容: herdr 驱动 pi 时, 提交键是 `alt+\`, 不是 enter. `herdr agent prompt` 默认发的 enter 只把文本留在输入框, 不提交. 正确两步: `herdr pane send-text <pane> '<文本>'` 然后 `herdr agent send-keys <短名> "alt+\\"`. 本会话用此法一次成功; 用 `agent prompt` 和 `send-keys enter` 均无法提交.

### F004 本容器无容器运行时
- 状态: 当前有效
- 来源: `which podman` / `which docker` 均空
- 内容: 端口发布, 镜像重建, 新建容器只能在宿主机做; 本容器内只能跑单元与快层测试. 涉及端口和镜像的改动本容器验收不了.

### F005 navigate 与 present 是两种不同服务
- 状态: 当前有效
- 来源: `workflow/navigate/scripts/web_server.py`; `workflow/navigate/web/index.html` (2107 行 SPA); `general/present/scripts/web_server.py`; 用户陈述
- 内容: navigate 自带 web 服务和 `/api/roadmap` 接口, 页面每几秒拉 `ROADMAP.json` 实时刷新; present 只发静态文件与目录 listing. 两者不是同一种服务; M04 D002 的"复用单实例"只覆盖 present 那族静态页, navigate 不在其内.

### F006 swt.py 已能读全端口表, 但命名键写死 8800
- 状态: 当前有效
- 来源: `workflow/use-sandbox-worktree/scripts/swt.py` (`parse_podman_ports`, `bake_host_info_env`, create 的 `-p`, 交付行)
- 内容: `parse_podman_ports` 已返回 `{容器端口: 宿主端口}` 全表; 但 web 端口的命名键 (`web-port`), 环境变量, 交付行, create 的 `-p` 都写死 8800, 加口需改这些位置.

### F007 宿主信息注入是软失败
- 状态: 当前有效
- 来源: `swt.py` 的 `bake_host_info_env` / `_rewrite_ssh_environment`
- 内容: 端口缺失时该条目被省略; 写入失败只告警, 不阻断 birth. 所以端口变量可能缺席, 依赖它的功能需要降级路径.

### F008 既有展示决策
- 状态: 当前有效
- 来源: `docs/changes/swt-cross-host-access/milestone-04/DECISIONS.md` (D001/D002/D010); `docs/adr/0012-container-web-direct-access.md`
- 内容: D001 定容器对外 web 端口固定为一个 8800, 直达局域网; D002 定 present 族静态展示页复用单实例, 不为每张页面另起服务; D010 要求使用已确认的局域网地址, 不猜网卡.

### F009 base 更新级联淘汰
- 状态: 当前有效
- 来源: `image-prep.py` 的 `resolve_display`; `use-sandbox-worktree/SKILL.md` 镜像管理节
- 内容: base 更新后旧 display 自然淘汰, display 更新后项目层淘汰; base 与 display 只在用户明说时重建, 无自动检测.

### F010 仓库历史有两个作者名
- 状态: 当前有效
- 来源: `git log --format='%an <%ae>'` 统计
- 内容: `luojingyan <921402781@qq.com>` 769 次 (宿主历史主作者); `bolo <921402781@qq.com>` 109 次 (全部是 agent 在容器内现场配的). 同邮箱.

### F011 容器刻意不注入 `~/AGENTS.md`
- 状态: 当前有效
- 来源: `image-prep.py` base Containerfile 注释 (D023); `docs/language/UBIQUITOUS_LANGUAGE.md` 完美复刻条
- 内容: 容器有意排除 `~/AGENTS.md` 与 `~/docs`, 容器内读它必 ENOENT; 宿主机上可能有.

### F012 账本事实错误已重复发生
- 状态: 当前有效
- 来源: findings.md 第 3 节问题 4; 会话 `01a1141c` (第 1 轮校验), `01a1142c` (第 2 轮校验)
- 内容: 两轮独立校验共抓 10 处错, 其中 6 处是"仓库/pi 里有什么"这类可机器核对的事实错误 (不存在的 `CONTRIBUTING.md`, 术语归属错文件, pi 支持 CLAUDE.md 的误判等).

### F013 会话日志形状与容器工具
- 状态: 当前有效
- 来源: findings.md 第 3 节问题 5; `milestone-01/findings.md`
- 内容: 会话日志在 `~/.pi/agent/sessions/<cwd 编码目录>/*.jsonl`, 一行一个 JSON; `message.content` 有字符串, 缺省, block 数组三种形态. 容器内有 node 与 python3, 无 jq.

### F014 use-herdr 现状规模
- 状态: 当前有效
- 来源: `general/use-herdr/` 目录
- 内容: `SKILL.md` 208 行; 已有两个 sibling 参考文件 `PI.md` (15 行) 与 `machine.md` (5 行).
