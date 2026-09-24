# mailbox 独立与 pi 连接器 决策账本

> 盘问日期: 2026-09-23. 起因: `docs/changes/swt-mailbox-mesh/2026-09-21-three-way-field-report.md` 三方实操报告 + 用户提出的四项改造 (pi 扩展封装/session 身份与 IP 解耦/文件归位/扩展随 skill 加载). 全程经 grilling 多轮盘问 + 反方攻击 (opposing-viewpoint 子代理, gpt-5.6-luna, 全文 `/tmp/opposing-attack.md`, 攻击后裁决见 F005) 收敛.
> 本账本修订上游账本 `docs/changes/swt-mailbox-mesh/DECISIONS.md` 的 D001/D002 (部分), 并对应新 ADR `docs/adr/0015-mailbox-skill-standalone.md`.

## 决策

### D001 信箱独立为 mailbox skill
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 信箱从 `use-sandbox-worktree` skill 拆出, 成为独立 skill `mailbox` (仓库 `workflow/mailbox/` → 部署 `~/.agents/skills/mailbox/`). 搬迁内容: `scripts/swt-mailbox.py` 改名 `scripts/mailbox.py`; **LLM 中转面 (relay) 随信箱一起搬** (它与信箱同住单脚本/单进程/单 SQLite, 拆开是大手术, SKILL.md 说明二合一); `reference/mailbox.md` 搬入新 skill; 新建 SKILL.md. 测试不搬: 11 个 `test_swt_mailbox_*.py` 留在仓库根 `tests/` (用户决定: 测试与生产代码分离; sync 按目录名忽略 tests 不会同步到设备). 不留任何旧路径兼容/shim (用户确认旧容器已全部清空, 服务 `__identity__` 名可直改). agent-prompts 三母本与 swt SKILL.md 改指新 skill. 理由: 信箱已是通用 agent 基础设施 (设备/容器/host 平权), 不该绑在沙盒工作树 skill 里; 用户明示独立.
- 依赖事实: F001, F002
- 预计影响: workflow/mailbox/ (新建), workflow/use-sandbox-worktree/{SKILL.md,reference/mailbox.md,agent-prompts/} (mailbox.md 搬走, 其余改指), tests/ (改指新脚本路径); sync-to-pi.py 的改动见 D005
- 实际影响: 待实现后补记
- 需要调整: 无

### D002 客户端/服务端同收 mailbox skill, swt 只使用不实现
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: swt.py 删除自带的信箱客户端实现 (`probe_mailbox`/`identity_probe`/`_admin_post`/`register_container_session`/`revoke_container_session` 约 150 行及 MAILBOX_* 常量), 改为 subprocess 调用 mailbox.py 新增的机器子命令. 机器子命令契约 (新增, 供 swt 与测试消费): `discover` (探测本机信箱: 读状态文件 + `__identity__` 验活, 失活/缺席扫端口区间兜底, 输出 JSON `{port, admin_port, admin_token}` 或失败退出码) / `register-session <id>` (经 admin 口注册, 输出 JSON 三元组) / `revoke-session <id>` (经 admin 口注销). JSON 走 stdout, 人话走 stderr, exit code 稳定. swt.py 定位脚本: `Path(__file__).resolve().parents[2] / "mailbox/scripts/mailbox.py"` — 仓库 (`workflow/<skill>/scripts/`) 与部署 (`~/.agents/skills/<skill>/scripts/`) 同构, 零配置. 理由: 用户要求客户端/服务端都收纳到信箱 skill, swt 不重复建设; 反方攻击指出的契约风险 (稳定 JSON/exit code/路径策略) 以本条显式契约化解.
- 依赖事实: F002, F005
- 预计影响: workflow/mailbox/scripts/mailbox.py (新子命令), workflow/use-sandbox-worktree/scripts/swt.py (删改), tests/ (birth 接线测试改打新契约)
- 实际影响: 待实现后补记
- 需要调整: 无

### D003 配置与运行时文件集中 ~/.agents/mailbox/
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 信箱 skill 的全部配置/运行时文件集中 `~/.agents/mailbox/`, 命名去 swt 前缀: `config.json` (原 `~/.agents/sandbox-worktree/mailbox.json`, 取信/投信凭证), `neighbors.json` (原同目录), `cli-state.json` (原 `mailbox-state.json`, 取信侧 pending_ack/seen_ids), `state.json` + `server.db` + serve 日志 (原 `~/.local/state/swt-mailbox/`, 整目录废弃). 旧路径首次运行自动迁移并提示 (仿 `_migrate_legacy_config` 先例). 测试注入 env 改 `MAILBOX_*` 前缀 (纯内部). **容器契约 env 保持不变**: `SWT_MAILBOX_URL`/`SWT_SESSION_ID`/`SWT_SESSION_SIGNING_KEY`/`SWT_SESSION_RESPONSE_KEY` 已烘进镜像与容器契约, 改名零收益高风险. swt 自有文件 (`lan-address`/`env.conf`/`runtime/`/`base/`) 留在 `~/.agents/sandbox-worktree/` 不动.
- 依赖事实: F002, F003
- 预计影响: mailbox.py (路径函数+迁移), swt.py (MAILBOX_STATE_PATH 删除, 经 discover 间接获得)
- 实际影响: 待实现后补记
- 需要调整: 无

### D004 pi 扩展合法化: 纯连接器, 禁止重实现 (修订 swt-mailbox-mesh D001)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 允许 pi 扩展作为 mailbox skill 的一部分存在, 约束: **扩展只是 pi 中优雅执行脚本的连接器, 禁止重新实现脚本已有能力, 需要相关能力时执行脚本**. 脚本 (mailbox.py) 仍是唯一跨 agent 实现, codex/kimi/裸终端裸用脚本不受损. 此决策部分推翻 swt-mailbox-mesh D001 的已排除候选 (a) "pi 扩展命令" — 当时排除的是扩展**承载信箱逻辑**取代脚本, 与本次连接器形态语义不同; 用户确认修订. 对应 ADR-0015, ADR-0014 备选方案节相关条目加修订指针.
- 依赖事实: F001, F004
- 预计影响: docs/changes/swt-mailbox-mesh/DECISIONS.md D001 注记, docs/adr/0014 注记
- 实际影响: 待实现后补记
- 需要调整: 无

### D005 扩展随 skill 加载: sync-to-pi.py 合并 settings.json
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 扩展源码放 `workflow/mailbox/pi-extension/` (index.ts 入口), 随 skill 同步到 `~/.agents/skills/mailbox/pi-extension/`, **禁止放 `pi/extensions/`**. sync-to-pi.py 新增一步: 把该绝对路径合并进 `~/.pi/agent/settings.json` 的 `extensions` 数组 (幂等去重, 写前 .bak 备份, 仿 models.json 合并逻辑). 副作用已接受: 容器内 pi 经 `~/.pi/agent` 复刻 + skill 只读挂载同路径拿到扩展, 命令面一致; 容器内生效需等 base 镜像重建 (settings.json 是构建期复刻的), 不阻塞.
- 依赖事实: F004
- 预计影响: sync-to-pi.py, workflow/mailbox/pi-extension/
- 实际影响: 待实现后补记
- 需要调整: 无

### D006 扩展命令面: /mail, /mail-listen, /mail-send
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 三个命令, 底层全部调脚本: `/mail` (总览: serve 验活/配置/邻居/待取数), `/mail-listen start|stop|status` (取信守护, 见 D007), `/mail-send` (投信, 缺参走交互补全, 带参直发). 不注册 LLM 工具: LLM 继续 bash 调脚本, 跨 agent 心智一致; 扩展只补脚本做不到的事 (守护/注入/交互/状态区).
- 依赖事实: F004
- 预计影响: workflow/mailbox/pi-extension/index.ts
- 实际影响: 待实现后补记
- 需要调整: 无

### D007 取信守护形态 (修订 swt-mailbox-mesh D002 的 pi 侧)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: pi 侧取信驱动从 "LLM 手动循环调脚本" 变为 **扩展守护代劳**: `/mail-listen start` 后, 扩展后台循环调取信脚本 (脚本阻塞到有信才退出) → 来信原文 (含处理指引与不可信输入声明) 经 `pi.sendUserMessage(deliverAs=followUp, triggerTurn=true)` 注入当前会话唤醒 LLM → 等 agent settled 再调脚本取下一封 (下次调用自动回执上一封, D003 回执时序 = 处理完之后得以保留). 守护在扩展后台跑, 不阻塞前台, 用户随时插话; agent 忙时来信排队等 settled. 脚本 exit 3 (缺凭证) → notify 用户并停守护. 手动前台取信脚本形态保留, 仍是非 pi agent (codex/kimi) 与裸终端的通用形态. 安全边界写明: 任何持合法 session 凭证者都能投信唤醒 LLM (远程唤醒/token 消耗面), 与 D002 时代相同, 靠注册凭证+HMAC 兜底, 不另加限流.
- 依赖事实: F004, F005
- 预计影响: pi-extension/index.ts, mailbox.py 取信输出不变
- 实际影响: 待实现后补记
- 需要调整: docs/changes/swt-mailbox-mesh/DECISIONS.md D002 注记

### D008 listen 状态持久化与多 listen 软提示
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: listen 开关状态落 `~/.agents/mailbox/listen.json`, 扩展 `session_start` 见标记即自动恢复守护, `session_shutdown` 清理. 多个 pi 会话同时 listen: start 时检测到其它 listen 标记 → 警告但不拦截 (软提示), 遵循 swt-mailbox-mesh D004 "不设唯一性强制, 散落自担" 的哲学.
- 依赖事实: F004
- 预计影响: pi-extension/index.ts, ~/.agents/mailbox/listen.json
- 实际影响: 待实现后补记
- 需要调整: 无

### D009 per-listener cli-state 修 pending_ack 竞态
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 取信脚本加 `--cli-state <路径>` (或 env 覆盖), 每个取信 listener 用独立状态文件 (pending_ack/seen_ids 各自一份); pi 扩展守护用自己的专属路径. 理由: 反方攻击实证 — cli-state 是每配置一份共享文件, 两个 listener 并发会互相覆盖 pending_ack, 出现 "A 替 B 回执, A 的信等租约超时重投" 的竞态. swt-mailbox-mesh D004 (不设唯一性强制) 保留, 本条只修状态文件归属.
- 依赖事实: F005
- 预计影响: mailbox.py cmd_fetch, pi-extension/index.ts
- 实际影响: 待实现后补记
- 需要调整: 无

### D010 session 身份与网络解耦 = 命名约束
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: session id 是设备绑定的固定逻辑身份 (host = `<hostname>-host`, 纯设备 = `<hostname>`, 容器 = `<容器名>-<8hex随机>`), 永不含网络地址, 换网不变. 本决策只是钉死命名约束, **无代码改动** (现状已满足); 明确不承诺换网自愈 (可达性是邻居管理的事, 见 D011 B 组). hostname 被改 = 产生新 session, 接受. 容器随机后缀保留 (防同名容器错投, 报告未推翻).
- 依赖事实: F001
- 预计影响: 无代码; 文档钉死
- 实际影响: 待实现后补记
- 需要调整: 无

### D011 可用性改造范围 (报告建议全清单处置)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 三方报告 30 条去重建议逐条处置如下 (字母组 = 账本自定义分组, 编号见盘问记录):
  - **做 — 投递可见性**: A1 send 回执分行打 `目标 session=` 与 `信件 id=`, 空 to 回打服务端实际解析出的目标; A2 post 应答带投递态 (`queued_local`/`forwarded`/`forwarded_partial`/`staged_pending`/`unknown_recipient`), CLI 按态打印, 不再一律 "已投递"; A4 转发异步化 (post 先收下再后台逐邻居转, 应答报路由判定, 消除 "CLI 超时但信已到" 的反义报错).
  - **做 — 邻居与滞留**: B1 admin 邻居 GET/DELETE/PATCH; B2 邻居加 name 标识按 name upsert (换址覆盖不累积); B4 pending_forwards 可查可控 (列出 id/to/目标邻居/最后错误/重试次数, 提供 retry/drop, 加上限+TTL 不无限涨); B5 文档写死 mesh 前提 "至少一个方向可达" + 反向隧道标准配方 + 隧道远端留标记文件 + 提醒 sshd ClientAliveInterval + 跨机换址联动清单 (防火墙白名单与邻居地址须同时改, 只改一半即不通); B8 邻居存储语义统一 (admin 加的进 DB 持久, 文件加的只作启动种子) 并文档化.
  - **做 — 启动与取信**: C1 组件读 state.json 先 `__identity__` 验活, 失活明报 "信箱不可达"; C2 取信连不上服务立即报 "信箱服务未启动" 再退避; C3 取信加 `--timeout`/`--count`, 待取数量可查; C5 status 报真实状态 (服务活否/端口/邻居数) 且认容器 env 凭证.
  - **做 — 安全小件**: D3 大信上限 1MB 拒收 (413) + 文档写明 "信箱只传控制消息, 传文件走 git".
  - **做 — 拉窗**: E1 pull-window 指令集动态绑定放宽 (poster session id 或容器名皆可命中, 限频键统一到容器标识); E2 拉窗 exec 信带 url 参数; E4 设备侧 chromium 模板强制 `--user-data-dir`, 音频 `-R` 标可选并给退化写法; E5 记录已验证 waypipe 版本组合 (容器 0.8.4 / host 自编译 minimal / 设备 0.11.0 混用实测出窗).
  - **做 — 日志**: F1 最小版 — serve 关键事件 (转发失败/邻居不可达/投递) 打带 UTC 时间戳日志行, 不建 JSON 日志体系.
  - **做 — 容器集成**: G1 birth 把宿主端口映射 (ssh/web/vnc) 写进容器 env 或只读文件; G2 birth 把宿主显示直通状态 (HOST_DISPLAY=ok/degraded/absent) 烘进容器 env; G3 信箱口加只读 sessions 列表端点 (session 签名认证, 只回 id+last_poll 不泄密钥; 纠正报告原方案 "走 admin 口" — 容器够不着硬绑回环的 admin 口).
  - **缓**: A5 物流查询 (与全内存有张力, 回执信先覆盖); B3 邻居健康检查自动暂停 (B1+B2 后手工已可行); B7 邻居配置热重载 (admin 改本就运行时生效); C4 systemd 保活 (只给文档样例不做安装); D1 跨实例签名链直投; D2 forward 端点验 from (与 D1 同批; post 侧的 from 验签已提前到 D013); D4 邻居密钥轮换; E3 拉起后校验回告 (防多窗只写进文档配方); F2 容器可达性诊断口 (原报告条未证伪); H1 一键配对 (已升级并入 D016 自组网); H2 隧道管理命令; H3 设备侧自动隧道包装; H4 死信队列 (B4 上限+TTL 先兜底); I1 代投标注 (信带 caused-by/reply-to 字段, 解决互相代投时回话寻址易混 — 属协议扩展, 下轮与 D1 跨实例签名链同批).
  - **拒**: A3 原版 "未知收件人默认拒绝" (违反 mesh 洪泛语义, 跨机投递时本机不认识收件人是常态; 改良版已被 D012 吸收); B6 邻居地址无认证自动学习 (伪造风险, 安全换便利不划算; 带认证的换址变体已进 D016); seen_ids 持久化 (容器 A9 推测项, 违 D008 全内存取向, 重启重复有取信侧去重兜底).
- 依赖事实: F001, F005
- 预计影响: mailbox.py (服务端+CLI), reference/ (mailbox.md/pull-window.md), swt.py birth (G1/G2), agent-prompts
- 实际影响: 待实现后补记
- 需要调整: 无

### D012 回执信: best-effort 三回执 + 信件 TTL
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 新增回执信机制, 吸收报告中 "投递失败主动通知发件方" "端到端回执对投信方可见" "信件 TTL" 三类诉求 (报告 3.4 yoga A1-A3/A7/A8, 3.5 容器 A13). 三种回执: **送达** (信进收件人本机队列) / **已读** (取信方 ack) / **失败** (TTL 超时丢弃). 信件加 TTL (默认 24h, serve env 可调), 任何节点持有/暂存超时即丢弃并回失败回执. 回执 = 带标记的 notify 信反向路由给原发件人, 回执不递归生成回执; 失败回执用确定性 id (`<原信id>.delivery-failed`, 多节点同时超时靠 seen-id 去重只投一封). **语义钉死 best-effort: 收到 = 确定发生, 缺席 = 未知** — 回执自身也走洪泛可能丢, serve 重启丢 pending 则失败回执发不出 (与 D008 丢信同窗). 已排除候选: 逐跳确认树版失败回执 (用户问成本后否决 — 需转发应答升级为送达确认+多路径聚合+回执路由+重启跟踪, 等于重写路由核心且违 D008).
- 依赖事实: F001, F005
- 预计影响: mailbox.py (TTL 字段/清扫/回执生成与路由), 取信脚本呈现
- 实际影响: 待实现后补记
- 需要调整: 无

### D013 from 验签 + 服务端保留身份
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: post 校验 `letter.from == 签名 session id`, 伪造发件人 403 (反方攻击实证: 现签名只覆盖 session/ts/letter.id/body, from 未验; 一行级加固). 回执信由服务端生成, 不走 post 验签, 经内部注入进路由, from 用保留身份 `mailbox@<hostname>`.
- 依赖事实: F005
- 预计影响: mailbox.py post/内部注入
- 实际影响: 待实现后补记
- 需要调整: 无

### D014 投递态与回执的呈现降噪
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 回执信不唤醒发件侧 LLM: pi 扩展识别回执标记 → 不注入会话不 triggerTurn, 汇入 `/mail` 总览与 widget 状态; 裸脚本取信 (codex/kimi/终端) 打印紧凑单行 (`回执: 信件 <id> 已送达/已读/失败`). 普通信照常唤醒. post 投递态与 pending 查询的语义标注义务: 只承诺 "本 serve 进程存活期内的本地观察", 重启即清 — 写进 CLI 输出与文档 (反方攻击裁决).
- 依赖事实: F005
- 预计影响: pi-extension/index.ts, mailbox.py 取信输出, reference/mailbox.md
- 实际影响: 待实现后补记
- 需要调整: 无

### D015 执行分批 M1-M4
- 状态: 当前有效
- 约束性: 可调整
- 内容: 反方攻击裁决 "单版本塞不下", 拆四个 milestone 顺序落地: **M1 信箱独立** (拆 skill, 改名, `~/.agents/mailbox/` 集中+迁移, D002 机器契约, swt.py 切换, 测试改指); **M2 可用性** (D011 全部 "做" 项); **M3 回执信+TTL+from 验签** (D012/D013); **M4 pi 扩展** (D004-D009, D014 的扩展侧) + sync-to-pi.py settings 合并 (D005). 文档贯穿各 M.
- 依赖事实: F005
- 预计影响: 同各决策
- 实际影响: 待实现后补记
- 需要调整: 无

### D016 无感自组网: 舰队密钥方案 (M5)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 网络各节点自组网, 对用户全程无感. 设计: (1) **舰队密钥** = mesh 入群总钥匙, 0600 存 `~/.agents/mailbox/fleet.key`, 只经 ssh 分发; (2) 新设备入群唯一人工动作 = 在新设备上跑 `join-fleet <老设备>`, 主动 ssh 拉取舰队密钥 (新设备在 NAT 后也能用); (3) 自发现 = UDP 广播信标 (同网段), 听到新节点用舰队密钥 HMAC 互证, 通过才建邻居; (4) 舰队密钥只作入群认证, 建邻居时协商两两独立链路密钥 (单链路泄露不扩散); (5) 认证换址自愈: 节点地址变化用旧链路密钥签名宣告新地址, 邻居验签通过即更新 (B6 无认证学习仍拒, 本条是带认证变体); (6) 跨网段/VPN 信标够不着, 靠换址宣告愈合或手工告知地址, 完全无路由仍需反向隧道. 已排除候选: 邀请码配对 (被吸收 — 有舰队密钥后跨网段配对只是告知地址+互证, 不再搬运密钥); TOFU 人工确认 (用户要全程无感); 零确认全自动 (信任域=整网段, exec/唤醒面暴露, 拒); 自动反向隧道 (缓, 约 200 行另批); 舰队密钥轮换 (缓, 与邻居密钥轮换同批). 排期: 独立 milestone M5, 在 M2 之后 (邻居管理是地基).
- 依赖事实: F007
- 预计影响: mailbox.py (信标/握手/换址/join-fleet), reference/mailbox.md
- 实际影响: 待实现后补记
- 需要调整: 无

### D017 PRODUCT 验收场景集已逐条确认
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 用户逐条采纳 37 条验收场景 (AC-001..AC-037, 含校验后增补的 AC-036 待取数量与 AC-037 关键事件日志), 同步确认目标 G-001..G-010, 非目标 NG-001..NG-009, 业务规则 BR-001..BR-009 (含自组网增量 G-010/NG-009/BR-009 与场景 AC-031..AC-035 与 AC-036/AC-037). 场景全文以 `docs/changes/mailbox-standalone/PRODUCT.md` 验收标准节为权威载体.
- 预计影响: docs/changes/mailbox-standalone/PRODUCT.md
- 实际影响: 待实现后补记
- 需要调整: 无

## 事实

### F001 三方实操报告与根因归纳
- 状态: 当前有效
- 来源: `docs/changes/swt-mailbox-mesh/2026-09-21-three-way-field-report.md` (2026-09-21 同一次实操, office 主机/容器/换网笔记本三方各自汇报)
- 内容: 五个根因 (按影响): 1 投递结果不可见 (回执把信件 id 当 session id 打/未知收件人静默转邻居仍报已投递/滞留队列不可见/CLI 超时语义与实际相反); 2 邻居表只能加不能改 (无 GET/DELETE/upsert, 换址累积废条目拖慢每次投递); 3 mesh 无健康检查与自愈 (换网静默失联, 需人工反向隧道); 4 启动/存活状态无可信广播 (state.json 残留不验活, 取信对服务未起静默重试); 5 权限与自省缺位 (跨实例投信借 shared_key 明文走信, 容器查不了 session 列表与宿主端口). 报告含 P0-P4 建议与 yoga/容器两份完整清单 (约 80 条), 本账本 D011 是去重后的处置.

### F002 现行实现事实 (改造前)
- 状态: 当前有效
- 来源: 读 `workflow/use-sandbox-worktree/scripts/swt-mailbox.py` (1551 行), `swt.py`, `reference/mailbox.md`
- 内容: 单文件纯 stdlib: serve (信箱面 38417-38426 区间首空闲 + admin 38416 硬绑回环 + LLM 中转 38427-38436) + 缺省取信 (阻塞长轮询) + send/config/status CLI. 信件全内存 (queue/leases/seen_ids/pending_forwards), SQLite (`~/.local/state/swt-mailbox/server.db`) 只存 sessions/whitelist/neighbors/relay keys. 状态文件 `~/.local/state/swt-mailbox/state.json`. 配置 `~/.agents/sandbox-worktree/mailbox.json`, 邻居表 `neighbors.json`, 取信状态 `mailbox-state.json`. swt.py 自带信箱客户端 (`probe_mailbox`/`_admin_post`/`register_container_session`/`revoke_container_session`, birth 注册 `<容器名>-<8hex>` session 烘 env, terminate 注销). post 同步逐邻居转发 (各 5s 超时), CLI 客户端 10s 超时. session id 已设备绑定 (host=`<hostname>-host`), 无 IP 成分.

### F003 本机环境事实
- 状态: 当前有效
- 来源: 读 `~/.agents/sandbox-worktree/`, `~/.local/state/swt-mailbox/`, `~/.pi/agent/settings.json`
- 内容: `~/.agents/sandbox-worktree/` 现有 base/ cz_sdk-master/ display/ env.conf lan-address mailbox-state.json mailbox.json neighbors.json runtime/. `~/.local/state/swt-mailbox/` 有 server.db + serve.log + receive.log (serve 当前未跑, 无 state.json). neighbors.json 仍挂着报告中的死地址 `192.168.131.194:38417` (yoga 旧地址). settings.json 无 `extensions` 键, `packages: []`.

### F004 pi 扩展机制事实
- 状态: 当前有效
- 来源: pi 官方文档 docs/extensions.md (0.87.0)
- 内容: settings.json 支持 `"extensions": [绝对路径文件或目录]` 加载自动发现目录之外的扩展. 扩展经 jiti 加载 TypeScript 免编译. 工厂函数禁止起后台资源, 后台循环应在 `session_start` 启动并在 `session_shutdown` 清理. 注入会话: `pi.sendUserMessage(content, {deliverAs: "followUp"|"steer"|..., triggerTurn: true})` — followUp = 等 agent 完成当前工具调用后交付, triggerTurn = idle 时立即触发一轮 LLM. 状态展示: `ctx.ui.setStatus`/`setWidget`/`notify`. 容器内 pi 的 settings.json 是 base 镜像构建期从 host 复刻的.

### F005 反方攻击裁决 (2026-09-23)
- 状态: 当前有效
- 来源: opposing-viewpoint 子代理 (pi + gpt-5.6-luna high), 全文 `/tmp/opposing-attack.md`
- 内容: 反方六条攻击的裁决: 成立并吸收七点 —(1) post 签名不覆盖 from, 发件人可伪造 → D013; (2) 回执在洪泛+全内存下无强语义 → D012 降级 best-effort 并钉死措辞; (3) 投递态/pending 查询与 D008 重启语义冲突 → D014 语义标注义务; (4) cli-state 共享文件 pending_ack 竞态 (实证: A/B 两 listener 互相覆盖回执) → D009; (5) pi listener 改变 D002 取信 owner → D007 显式修订 D002 并写明安全边界; (6) 单版本工作量不现实 → D015 分批; (7) 机器子命令契约与路径策略 → D002 显式契约. 舍弃: "拆 skill 方向错误" (用户明示要拆, 攻击只成立为工作量) ; "维持 D002 不要后台 listener" (用户已明示要守护注入形态).

### F006 旧容器已清空
- 状态: 当前有效
- 来源: 用户陈述 (盘问 Q18)
- 内容: 不存在运行中的旧容器, 本次改名/换路径不需要任何兼容 shim 或过渡期双写.

### F007 用户网络拓扑
- 状态: 当前有效
- 来源: 报告第 1 节实测 + 用户陈述
- 内容: office 在 192.168.65.x (有线) / 192.168.107.x (无线); yoga 在 192.168.31.x (家网) + VPN 192.168.216.x. 设备分属不同网段, UDP 广播/组播不出网段, 同网段自发现只覆盖部分场景; 跨网段换址后可能双向无路由 (yoga 换网实测 curl 超时), 此时任何协议层自愈都无效, 只能反向隧道.

### D018 status 补邻居数输出 (补 D006/D011-C5 缺口)
- 状态: 当前有效 (用户 2026-09-23 批准)
- 约束性: 必须遵守
- 内容: cmd_status 在验活成功且本机可达 admin 面 (state.json 提供端口与 token) 时输出邻居数; 容器 env 凭证场景无 admin 面则输出未知, 不报错. pi 扩展 /mail 转呈 status 输出, 自动获得该项. 理由: D006/D011-C5 明文含邻居数, ISSUE-05/07 因范围锁死未实现, 用户裁决补齐.
- 实际影响: ISSUE-11 实现

### D019 拉窗文档单源化 (消双写)
- 状态: 当前有效 (用户 2026-09-23 批准)
- 约束性: 必须遵守
- 内容: 拉窗设备侧模板 (chromium --user-data-dir 强制, 音频 -R 可选与退化写法, waypipe 版本组合) 以 mailbox skill 的 reference/pull-window.md 为唯一权威源; swt skill 的 reference/pull-window.md 保留其独有内容 (三态选路/容器侧编排/STATE 代换), 重叠段落改为指向 mailbox skill 文档, agent-prompts 既有路径引用不失效.
- 实际影响: ISSUE-12 实现

### D020 fleet.key 引导生成
- 状态: 当前有效 (用户 2026-09-23 批准)
- 约束性: 必须遵守
- 内容: serve 启动时若 fleet.key 文件缺席且 MAILBOX_FLEET_KEY env 未设, 自动生成随机密钥落盘 0600 (父目录 0700) 并打 UTC 日志行; 已有文件或 env 则照旧. 语义不变: 自生成密钥 = 自成单节点舰队, 与异钥舰队握手仍然被拒 (NG-009 无零确认入群). BR-009 只约束分发经 ssh, 本地生成不违.
- 实际影响: ISSUE-13 实现
