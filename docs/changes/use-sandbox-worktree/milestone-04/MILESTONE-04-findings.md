# MILESTONE-04 执行记录与 findings: 网络访问控制双模式

日期: 2026-09-05
状态: 完成 (实现 + 验证, 全部无 root)
环境: rootless podman 5.7.0 (netavark, pasta), nftables 1.1.6, linux/amd64, uid 1000

权威输入: roadmap/MILESTONE-04.md; DECISIONS.md D011/D024; TECHNICAL.md 安全策略节; 2026-09-01-research.md §4.1. 原始调研报告 /tmp/report-podman-net-hardening.md 已易失 (不存在), 其结论以 §4.1 沉淀文本为准, 机制由本次全部重测.

## 0. 交付物

- `workflow/use-sandbox-worktree/scripts/net-firewall.py`: 同一脚本两个分支 (MILESTONE-04 原文), 子命令 apply/show/clear; apply 为表级全量替换.
- `tests/test_swt_m04.py`: 8 项端到端测试, 命令 `uv run --with pytest pytest tests/test_swt_m04.py`, 实测 8 passed (46.5s).
- 本文档.
- 未改动: e2e-smoke.py, test_swt_m03.py, M03 产物, roadmap 状态文件, 其他 skill, 真实用户仓库.

## 1. 机制事实 (本次全部实测)

### F-M04-01 注入通道: rootless netns + podman unshare nsenter, 无 root

- rootless 桥网络的 netns 持久路径: `$XDG_RUNTIME_DIR/containers/networks/rootless-netns/rootless-netns` (即 `/run/user/1000/...`), 由 pasta 进程持有 (`pgrep -af 'pasta --config-net'` 可见 `--netns` 参数, 可作发现手段).
- `podman unshare nsenter --net=<该路径> nft -f -` 注入成功, `nft list ruleset` 可读 netavark 表 (`table inet netavark`, FORWARD/INPUT 链 priority filter). 全程无 sudo/root.
- 容器流出必经该 netns 的 FORWARD 链 (podman1 → tun0 pasta); 流向网关 (aardvark DNS) 走 INPUT 链. 在此注入即对容器内任意 uid 生效 (netns 物理边界, 容器 root 无权触及; 承接调研 §4.1, 未重复实验).

### F-M04-02 netns 生命周期: 最后一个容器停则拆, 规则全失 → 重注入是唯一序

- `podman network create` 单独不产生 netns (`/run/user/1000/netns/` 为空, 无 pasta 进程); 第一个容器 start 后才建立.
- 该网络最后一个容器 `podman stop` → netns 连同自有表整体销毁; 再次 `start` → netns 重建, netavark 表由 netavark 重建, **自有表 `inet swt` 消失** (实测 `nft list tables` 仅剩 netavark).
- 与 D011 文本 "注入 nft 白名单规则 → ... → 最后 start 容器" 的出入: netns 在容器首启前不存在, "容器启动前注入" 字面上不可行. 实际落地 = **start 后立即注入, 先于任何 agent 工作负载** (镜像 CMD 仅 sshd, 无自动工作负载), 与调研 §4.1 "编排侧每次启动后重注入" 一致. D011 的排序精神 (规则未就绪工作负载不跑) 由此保全, 时序修订记入本条, 供 M10 编排实现遵循.
- 编排纪律: 每次容器 start 后必须重注入; 容器 stop 期间规则不存在不是缺陷而是该机制的固有形态.

### F-M04-03 静态 IP: `network create --subnet` + `run --ip` 跨 stop/start 保持

实测容器固定 `.5`, stop/start 后 `hostname -I` 仍为 `10.99.x.5` (调研 §4.1 的 DHCP 重分配弱点由此消除). 规则按容器源地址写, 静态 IP 是规则语义成立的前提.

### F-M04-04 容器 → host 通道 = pasta map-guest-addr 169.254.1.2

- 自定义桥网络的 pasta 以 `--no-map-gw --map-guest-addr 169.254.1.2` 运行: 容器访问 `169.254.1.2` 达 host **非 loopback 监听**的服务 (0.0.0.0 绑定实测可达, 127.0.0.1 绑定实测拒绝); 网关地址不映射 host (--no-map-gw).
- 复证 TECHNICAL M03 结论 (host loopback 对容器不可达). M03 的 git daemon 监听地址探测 ("pasta 网关接口地址优先, 0.0.0.0 兜底") 不变; M04 白名单模式下放行条目 = `169.254.1.2` (容器侧目的地址).
- 含义: 白名单放行 `169.254.1.2` 即放行容器到 host 全部非 loopback 监听服务 (IP 级, 见 F-M04-06 粒度说明), 与 M03 状态 quo 的暴露面一致, 未扩大.

### F-M04-05 规则形态: 自有表 `inet swt`, 源地址限定, policy accept + 显式收尾

- 自建表不碰 netavark 表 (不动它的链与策略, netavark 升级/重建不受影响).
- 两链: forward + input, `type filter hook <chain> priority filter + 10; policy accept;` (排在 netavark 之后评估; accept 不终结, drop 才终结, 与 netavark 链共存无冲突).
- 所有规则以 `ip saddr <容器IP>` 限定作用面 → 同 netns 其他网络/容器流量不受影响 (D010 多容器共存的守卫另见 F-M04-07).
- **白名单链序**: IPv6 drop → 网关 DNS (tcp/udp 53) accept → 逐条 allow accept → `ct state established,related` accept → `ip saddr <容器IP> drop`. ct established 必须在 catch-all drop 之前: host 发起连接 (如 ssh 发布端口) 的回程包源地址是容器 IP, 无此条会被默认拒断掉 ssh (链路推演得出, 未单独实测 ssh 全链, 见 §4 局限).
- **黑名单链序**: IPv6 drop → 逐条 deny drop → ct established accept (deny 在前, 防已建连接对新增 deny 项继续存活).
- **两模式共通**: `meta nfproto ipv6 drop` (调研 §4.1 兜底; rootless netns 本无 v6 全局路由, 此为显式保险).

### F-M04-06 双模式行为实测矩阵

白名单 (allow=[169.254.1.2], 容器 10.99.x.5, host 0.0.0.0:PORT 监听):

| 目的 | 结果 |
| --- | --- |
| 169.254.1.2:PORT (放行, daemon 通道) | 通 |
| 网关 10.99.x.1:53 (DNS) | 通 |
| 网关:9999 (非放行 IP 非监听) | TIMEOUT (默认拒) |
| 1.1.1.1:443 | TIMEOUT (默认拒) |
| host LAN IP:80 | TIMEOUT (默认拒) |
| DNS 解析 (getent github.com) | 正常 |

黑名单 (deny=[169.254.1.2]): 该 IP 全端口 TIMEOUT; 网关 DNS 通; 网关非监听端口 REFUSED (默认放行, 穿透到栈); 出网通.

断言口径: 被滤 = TIMEOUT (rc 124), 未监听 = REFUSED (rc 1), 两者区分, 防 "恰好没服务" 假阴性.

### F-M04-07 多容器守卫 (D010 衍生)

netns 为用户级共享, 同 netns 多个 swt 容器并存时, 表按单一容器源地址过滤, `apply` 的表级全量替换会清掉异己容器规则 (对它 fail-open). 脚本 apply 前检查现存表内 `ip saddr`, 发现非本容器的源地址即拒 (`APPLY-CONFLICT`, 退出码 1), 不猜不覆盖. 同容器 IP 重注入 (restart 场景) 不受影响. 多容器各自规则的真表结构 (表 per 容器或单表多段) 归 M10/M11 编排设计, 本切片只负责不造成静默 fail-open.

### F-M04-08 颗粒度与域名语义

- nft 规则为 IP/CIDR 级, 端口无关: 放行某 IP 即全端口可达. git daemon 场景暴露 = 该地址全部非 loopback 监听 (见 F-M04-04), 接受; 如需端口级收紧须盘点条目升级为 IP+端口对, 归 M10 盘点格式拍板, 本切片不擅自加.
- 调研 §4.1 "盘点所需域名/IP" 中的域名: nft 无域名语义 (调研实证规则形如 `ip daddr <IP>`), 域名条目须在盘点确认环节解析为具体 IP 后进入清单, 脚本对非 IP/CIDR 条目拒绝 (退出码 2 `INVALID-ENTRY`). 解析时机与失效重盘点 (站点换 IP) 属 M10 流程, 本切片不猜.

## 2. 与权威输入的偏差登记

1. **D011 时序** (F-M04-02): "容器 start 前注入" 不可行 (netns 尚不存在), 改为 start 后即时注入且先于工作负载. 不需要回盘问: 调研 §4.1 已明文 "启动后重注入", D011 排序的精神 (fail-closed) 保全, 差异是纯机制事实.
2. 其余 (双模式, 创建时静态确认, 运行期不切换, 桥 netns 注入, 静态 IP, IPv6 兜底) 均按原文落地, 无偏差.

## 3. 验证记录

- 命令: `uv run --with pytest pytest tests/test_swt_m04.py -x -q` → `8 passed in 46.51s`.
- 覆盖: 白名单默认拒 + 放行/DNS/解析 (test_01); stop/start 规则全失 + 静态 IP 保持 + 重注入恢复 (test_02); 黑名单默认放行 + 拒项 (test_03); clear 幂等 (test_04); 异己容器 saddr 冲突拒绝 (test_05); 域名条目拒收 / 模式与清单旗标错配拒收 / netns 不可达报错 (守卫 3 项).
- 手工探针 (写码前机制摸底, 同一 netns): 白名单放行通/其余断/DNS 通, restart 后表灭, 黑名单拒项断/默认放行通, 与测试矩阵一致.
- test_swt_m03.py 未重跑 (M03 代码零改动); 测试脚本互不依赖.
- 运行期不切换的实现口径: apply 是表级全量替换, 不存在增量放行通道; 换模式/换清单 = clear + 全量重建, 模式选择的用户确认环节在 M10 编排层 (host llm 创建容器前询问), 脚本层不交互.

## 4. 局限与移交

- ssh 发布端口回程经 ct established 保全为链路推演, 未跑通全链 ssh 实验 (M03 已覆盖 ssh 通道, M04 只新增 FORWARD/INPUT 过滤; 风险 = 若推演有误 ssh 断连, 症状即时可见, 非静默). M10 接线后 e2e 复验.
- 黑名单模式的出网依赖 host 出网; 测试中出网断言仅手工探针做过, 自动化测试用确定性目标 (网关/169.254.1.2) 避免外网依赖.
- 阻塞: 无. 未动用任何 root/外部权限; 权威输入未覆盖的点 (ct established 位置, 多容器守卫, IP 级颗粒度) 均由机制事实推导并登记如上, 无猜测性设计.
