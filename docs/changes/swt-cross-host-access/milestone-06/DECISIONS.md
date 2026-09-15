# MILESTONE-06 窗口直飞 (waypipe 远程直通) 固化 决策账本

盘问日期: 2026-09-14. 依据: [recon/03](../recon/03-waypipe.md) + [跨机GUI无感访问可行性调研报告](../../use-sandbox-worktree/跨机GUI无感访问可行性调研报告.md) (实测底座) + 反方攻击 (子代理 opposing-viewpoint, 6 条攻击, 5 条采纳并入 D001/D002/D006/D007/D008, 1 条驳回见 D001).

术语: **设备侧** = 人面前的机器 (B), **容器侧** = swt 容器 (宿主机 A 上). 与调研报告的 A/B 用法一致, 以本账本与 ROADMAP 为准.

## 决策

### D001 触发链路: 信箱 (b) 为主形, 手工命令 (a) 为底层零件, 常驻隧道 (c3) 仅作文档备选
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 容器内 AI 需要远程 headed 窗口时, 主链路 = 投信到信箱 (M01-M03 已建成) → 设备侧取信会话执行 `waypipe ssh ... <启动脚本>` 把窗口拉到设备屏. (a) 设备侧手工直发起保留为交付包里的底层零件命令模板, 不作默认形态. (c3) 设备侧预挂常驻 `-R` 隧道 + 容器内按需起 waypipe server **不固化**: 不进三态判定逻辑, 不进交付包默认内容, 仅以命令模板写进 SKILL.md 作高级备选. 理由: (1) (b) 已满足 "容器内 LLM 发起 + 零白名单改动" 的核心诉求, (c3) 的增量只剩省一次信箱往返和不依赖取信会话在线; (2) (c3) 新增设备侧常驻进程运维负担与隧道断后残留 socket 语义, 而取信会话是信箱本身的基础设施, 不为本功能单独存在 — 反方攻击称 "设备侧常驻 pi 会话比一条隧道更重" 不成立, 因为边际负担比较应算新增量, (c3) 是新增, (b) 是复用; (3) 反方指出的 "(b) 异步无反馈" 结构缺陷由 D007 的会话 socket 轮询堵上, 无需隧道. 排除依据同时记录: (c1) waypipe 原生反向不存在 (F001); (c2) 容器拨出常驻隧道违背白名单立场 (前序方向侦查已淘汰).
- 预计影响: SKILL.md 直飞章节; 交付包命令模板; M08 实施

### D002 音频形态: 同条 ssh -R unix socket 为主, 独立 ssh -R 为备, TCP 直连仅救场
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 音频主形态 = 与画面同条 ssh 反带 pulse unix socket: 设备侧 `waypipe ssh -R /tmp/swt/pulse-b.sock:/run/user/1000/pulse/native ... <启动脚本>` (waypipe 透传用户 `-R`, F004), 容器内启动脚本 `PULSE_SERVER=unix:/tmp/swt/pulse-b.sock`. 零白名单改动, 认证面 = B 侧同 uid unix 连接 (PipeWire 缺省放行), 显著小于 TCP 形态的 `auth-anonymous=1` (局域网任何人可用 B 声卡). **备胎排序** (反方攻击 5 采纳): 若同条 ssh 形态实测翻车 (尤其 B 侧 waypipe 为 Rust 版导致 `-R` 透传行为不符, F004), 第一备胎 = 另起一条独立 `ssh -R` 只带音频 (同安全级, 零白名单改动), TCP 直连仅作救场文档条目. 排序结论挂到 M07 必测点结果上 (recon 3.4 节 7 项: 端到端出声/PipeWire 认证/socket 权限属主/StreamLocalBindUnlink 行为/`-R` 与 waypipe 并存/跨版本兼容/延迟主观评价).
- 依赖事实: F003, F004
- 预计影响: 启动脚本模板 (音频 env 常量); 交付包 B 侧命令模板; M07 必测清单

### D003 启动脚本母本制: 模板在 skill 仓库, birth 生成实例, 只读挂载进容器
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 容器内固定路径 `/home/bolo/.local/bin/swt-headed-browser.sh`, 内容 = 音频 env (D002 常量) + `exec <chromium 精确路径> --no-sandbox --ozone-platform=wayland ...`. 交付链路套 agent-prompts 母本制先例: 模板放 use-sandbox-worktree skill 仓库 → birth 时 exec 解析 playwright chromium 精确字面路径 (F006) 生成实例脚本 → 落 `<records-root>/runtime/<identity>/swt-headed-browser.sh` 留档 (与 ssh 凭证/agent-prompts 留档同屋) → 只读单文件挂载进容器固定路径. 排除: 镜像内置 (脚本调参是高频经验性修改, 进镜像则每次调参触发 D017 级联重建; chromium 路径运行时 glob 有歧义); exec 写入 (两先例中选了挂载, 留档可追溯每容器用的哪版). 脚本路径稳定性只要求容器存续期内不变: B 侧命令在 birth/resume 交付包里, rm 重建后随新 birth 重生成, 口径自洽.
- 依赖事实: F006, F007
- 预计影响: use-sandbox-worktree skill 仓库新增脚本模板; swt.py birth 流程; M08 实施

### D004 base 层改动三项: SetEnv 合并单行 + 目录保障 + StreamLocalBindUnlink yes
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: base 镜像接受三项改动: (1) sshd_config 既有 `SetEnv PATH=...` 单行**合并**追加 `XDG_RUNTIME_DIR=/tmp/xdg-1000` (SetEnv 只认第一行, 追加第二行不生效, F003); (2) 容器启动路径保证 `/tmp/xdg-1000` (bolo:bolo 0700) 与 `/tmp/swt/` 目录存在 (同一处实现, entrypoint 或 swt-vnc 同类 helper); (3) sshd_config 加 `StreamLocalBindUnlink yes` — 不加则 ssh 不干净断开后残留死 socket, 音频 socket 与 waypipe `-R` socket 同路径重连直接失败 (F003). 级联成本已摆台并 accepted: (1)(2) 本就触发 D017 级联 (base→display→全部项目镜像重建), (3) 边际成本≈0, 搭车接受. 明确不加 entrypoint 残留 socket 清理逻辑 (双机制冗余, M07 实测暴露需要再补).
- 依赖事实: F003, F007
- 预计影响: base 镜像 Containerfile (sshd_config + entrypoint); D017 级联重建; tests/test_swt_m07.py 的 SetEnv 断言需更新

### D005 STATE 不动: 远程显示状态不落 STATE, 文件事实现查
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: STATE 单行 json 不加任何远程显示字段. 容器内文件/socket 事实是唯一事实源, host 需要时 exec 探测. 排除: (B) 探测快照 (resume/display-check 写 `remote-display: seen-*`) — 快照会过期, 会话中途建/断无法感知, 过期状态比没有状态更误导; (C) 出生声明 flag — 暂不需要, 日后可与 A 叠加. 实时判定只在容器内成立 (D007), 这是触发链路方向性决定的不是实现缺陷 (recon 5.3 论证).
- 预计影响: 无 (最小改动); SKILL.md 写明 "需要时现查" 的口径

### D006 B 端前提口径: 文档声明 + 交付包提示 + 设备侧执行前自动检查
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: B 端 (设备侧) 前提 = Linux Wayland 桌面会话 + waypipe 客户端, Atomic 系发行版 (Bazzite 等) 走 distrobox 安装. 三层落实: (1) SKILL.md 直飞章节开头一段前提声明; (2) 交付包远程直通命令模板旁附一行检查提示 (`waypipe --version` 不在场即提示安装路径); (3) 反方攻击 6 采纳 — 设备侧取信会话执行拉窗前自动 `command -v waypipe` 检查, 不在场时在**设备本地** herdr notification 告知用户安装, 不取下一封同类信, 不需要回程队列 (不违反 M01 D003 单向语义). swt.py 里不加探测逻辑.
- 预计影响: SKILL.md; 交付包模板; 设备侧取信扩展的 exec 执行器

### D007 三态选路: 脚本 preflight 管机械判定, SKILL.md 管编排, 投信后轮询会话 socket 判活
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 容器内 AI 要开 headed 浏览器时的三态规则. **判定拆分** (反方攻击 4 采纳一半): 机械判定写成代码, 编排写在文档. (1) 启动脚本 (D003) 加 preflight: `WAYLAND_DISPLAY` 在场**且对应 socket 可连**才启动 chromium — 覆盖宿主直通烘死的变量在宿主桌面注销后变死 socket 的翻车点; 不满足则以明确退出码退出, 不做选路. (2) SKILL.md 行为规则 (AI 读文档执行编排): preflight 失败 → 默认投信请设备侧拉起 (D001 主链路, 体验严格好于 noVNC, 信箱基础设施已建成) → **等 ack 后轮询容器内会话 socket `/tmp/waypipe-server-*.sock` 出现** (F005; 反方攻击 1 采纳 — ack 只证明信被取走, 不证明窗口拉起, 只盯投信环节有结构性静默黑洞: B 没装 waypipe/无桌面会话/命令失败时 AI 死等永不落兜底) → 超时未出现才落 `DISPLAY=:99` noVNC 兜底, 并在回复中告知用户落了兜底. 超时具体值留 M08 实施定. 判定依据均为文件/socket 事实, 不依赖运行期改写 env (env 烘配只在 podman create 时发生, resume 改不了).
- 依赖事实: F002, F005, F008
- 预计影响: 启动脚本模板 (preflight); SKILL.md 三态选路章节; M08 实施

### D008 exec 白名单首成员: 零参数拉窗指令, 幂等 + 限频
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 远程拉窗走信箱 exec 类型直批 (M01 D005 的白名单机制, 不问人). 首个白名单成员 = 结构化指令 "给某容器拉起 headed 浏览器", 受反方攻击 2 加严为三条硬约束: (1) **零参数** — 指令只带容器标识, 服务端对容器注册表校验合法; 原拟的 "可选 URL" 参数删除: 它是受容器控制的数据进入直批执行路径 (设备侧拼命令转义失误 = 注入借白名单还魂), 且功能冗余 (窗口起来后容器内 AI 经 playwright/CDP 自己导航, ADR 0001); (2) **幂等** — 同容器已有活跃 waypipe 会话时执行器直接返回不再拉起 (容器内会话 socket 可探测, F005); (3) **最小限频** — 防被提示注入操纵的容器循环投信窗口轰炸 (具体限额 M08 定). 直批不问人的理由修正: 不是 "容器是用户自己的 AI" (与沙箱立身前提矛盾 — 容器不可信, M01 F004 正是 M01 D005 白名单折中的存在理由), 而是: 白名单指令本身能力极窄 (只能拉起一个预定义命令, 无参数注入面), 幂等+限频封住滥用, 此时每次问人只剩形式, 会养成无脑同意习惯.
- 依赖事实: F005
- 预计影响: swt-base-server.py 指令集注册表 (M08 填); 设备侧 exec 执行器 (幂等+限频+preflight 检查 D006); SKILL.md 指令集章节

## 事实

### F001 waypipe 无反向模式, server 恒为拨出方
- 状态: 当前有效
- 来源: recon/03 §1.1/§1.2/§2.3 (man + 0.8.2 源码)
- 内容: 所有传输方式 (ssh/ncat/vsock) 下 waypipe server (应用侧) 主动 connect client (合成器侧) 的 socket, 不存在 client 拨向 server 的原生反向. ssh 模式每次随机 socket 名 (`<prefix>-client/server-<token>.sock`), 同设备多容器多会话源码层天然隔离. ssh 断线全清场 (两端 waypipe + 应用全退); 重连 (recon/--control) 仅 C 版 (0.8.x/0.9.x) 有, Rust 版 (0.10+) 已删.

### F002 核心不对称: waypipe 的环境变量只喂给它自己拉起的子进程
- 状态: 当前有效
- 来源: recon/03 §1.3 (man ENVIRONMENT 节 + 源码) + §5.2/结论 7 (env 烘配只在 create 时发生)
- 内容: 设备侧发起的 `waypipe ssh` 会话中, `WAYLAND_DISPLAY=wayland-<rand>` 只设给 waypipe server 的子进程; 容器内 AI 在普通 shell 里自启的进程拿不到, 沿旧两态判定只能落 noVNC. 容器内跨进程判定远程会话只能靠文件/进程事实 (socket 存在性, pgrep), 不能靠 env — env 烘配只在 podman create 时发生.

### F003 sshd 三个配置事实
- 状态: 当前有效
- 来源: 调研报告坑 3 + recon/03 §3.2 (sshd_config(5))
- 内容: (1) SetEnv 只认第一行, 多变量必须合并单行 (`SetEnv XDG_RUNTIME_DIR=/tmp/xdg-1000 PATH=...`); (2) `StreamLocalBindUnlink` 缺省 no — 转发路径残留死 socket 时同路径重连失败; (3) `StreamLocalBindMask` 缺省 0177, 转发 socket 落 0600 仅属主 (会话用户 bolo), 容器内 socket 权限面收敛于工作用户; unix socket 反向转发无 PermitListen 类白名单 directive, sshd 缺省放行.

### F004 waypipe `-R` 透传的版本证据错位
- 状态: 当前有效
- 来源: recon/03 §1.2/§2.7
- 内容: "waypipe ssh 逐字透传用户 ssh 参数 (含 `-R`)" 的源码证据取自 0.8.2 C 版 (容器内版本), 但构造 ssh 命令的 wrapper 跑在设备侧, 设备侧版本用户自管, 可能是 0.10+ Rust 重写 (行为有删改, 官方未承诺跨版本线协议兼容). 音频同条 ssh 形态因此列为 M07 必测, 备胎见 D002. Debian 12 waypipe 0.8.2 默认压缩 none 不是 lz4, 固化 `-c lz4` 应写设备侧.

### F005 远程会话在场的容器内可探测标志
- 状态: 当前有效
- 来源: recon/03 §1.2/§1.4
- 内容: `waypipe ssh` 会话存活期间, 容器内 `/tmp/waypipe-server-<token>.sock` 必然存在 (sshd `-R` 建, ssh 掉线即消失), `pgrep -x waypipe` 同理. 这是投信后判定 "窗口真的拉起来了" 的文件事实依据 (D007/D008 幂等检查同用).

### F006 chromium 路径漂移与 glob 歧义
- 状态: 当前有效
- 来源: recon/03 §4
- 内容: playwright chromium 路径 `~/.cache/ms-playwright/chromium-<rev>/chrome-linux[64]/chrome`, rev 随 display 镜像构建变, 镜像升级后旧 rev 目录并存, 运行时 `chromium-*` glob 取哪个有歧义. birth 时 exec 解析精确字面路径烘进脚本最稳.

### F007 D017 级联: base 一动全镜像重建
- 状态: 当前有效
- 来源: use-sandbox-worktree/DECISIONS.md D017 + 三层镜像决策
- 内容: base 层改动触发 display 层与全部项目镜像级联重建 (谓词链: display 须基于当前 base, 项目层须基于当前 display). base/display 只在用户明说时重建. 本次 D004 的改动排入 Roadmap 目的地已声明的既定级联 (实施范围含 base/display 镜像重建).

### F008 信箱 ack 语义边界
- 状态: 当前有效
- 来源: M01 D003 + M03 ack 闭环
- 内容: 信箱队列纯单向 (容器投/设备取, 无回程), ack 只证明 "信被设备侧取走处理", 不证明请求的动作 (拉起窗口) 成功. 动作成败须另觅信号 (D007 用 F005 的文件事实).
