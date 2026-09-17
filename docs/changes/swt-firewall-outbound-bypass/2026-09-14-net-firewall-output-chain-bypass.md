# Bug 反馈: net-firewall 缺 output 链, 白名单/黑名单对 "容器主动出站" 全部失效

- 日期: 2026-09-14
- 来源: cz_sdk 项目首次 sandbox 容器实跑 (whitelist 模式), 容器内 agent 自测发现
- 严重级: 安全 (fail-open, 白名单语义整体落空)
- 状态: 已修复 (2026-09-17 脚本级落地 + 同日冷审返工项, 见文末 修复记录)

## 现象

whitelist 模式容器 (allow = `172.22.8.94/32` + `119.147.156.0/24`), 容器内:

```text
curl https://www.baidu.com  →  HTTP 200, 实连公网 IP 183.2.172.177:443
```

未放行 IP 的出站连接畅通无阻. 同时 `nft list ruleset` (容器 netns) 显示 `table inet swt` 存在, input/forward 链条目齐全 — 规则 "在", 但不管用.

## 根因

`workflow/use-sandbox-worktree/scripts/net-firewall.py` 的 `build_ruleset()`:

```python
for chain_name in ("forward", "input"):
```

只生成 `forward` / `input` 两条链, **没有 `output` 链**. 容器进程主动发起的出站包在容器 netns 走 OUTPUT 钩子 → 无链 + `policy accept` → 直接放行; 回包在 INPUT 命中 `ct state established,related accept` → 整条连接建立. forward 链在该拓扑下无流量 (容器不做路由).

实际效果:

- whitelist: 只拦 "外部主动连容器" + IPv6; "容器主动出站" 全通, 等价无防火墙.
- blacklist: deny 条目同样只挂 input/forward, 容器主动连被保护服务 (数据库/redis) 一样穿透.
- SKILL.md/risks.md 宣称的 "其余容器流出全断" 自始未成立.

## 连带发现

1. **DNS 放行与真实解析器不匹配**: 规则只放行网关 `169.254.1.2:53` (DNS_PORTS 条目), 但 pasta 容器 `/etc/resolv.conf` 实际是 `169.254.1.1` (pasta DNS 代理) + host 侧公司 DNS `192.168.90.47/48`. 原规则下 DNS 之所以 "能用", 是因为出站根本没被过滤; 补上 output 链后 DNS 立刻全断, 须显式放行上述三个地址才恢复. 即: 原设计的 DNS 放行条目从未与真实解析器对齐过.
2. **m04 测试为何没抓住**: `tests/test_swt_m04.py` 的 NetFixture 是 podman bridge 专用网络 + 静态 IP (10.99.x.0/24), 不是生产的 pasta 拓扑; 阴性对照 `container_tcp(gateway, 9999)` 打的是 fixture 网关而非真实外部目的地, 其 TIMEOUT/REFUSED 观察值混入 bridge/pasta 自身行为, 与 nft 过滤无因果关系. "容器出站默认拒" 这一白名单核心承诺没有任何用例覆盖. (handoff 2026-09-11 记录的 `test_01_whitelist_default_deny` 环境性失败挂账, 与本发现吻合.)
3. **CDN IP 漂移 (运营性, 非本 bug)**: maven.aliyun.com 走 CDN, 实测解析轮换于至少 `119.147.156.0/24` 与 `183.61.236.0/24` 两段. IP 级白名单配 CDN 会时通时断, 换段需重新盘点.

## 已实施热修 (仅当前容器, stop 即失)

对容器 netns 手工补 output 链 (语义与 input 镜像 + DNS 修正), 规则序:

```text
chain output (hook output, policy accept):
  meta nfproto ipv6 drop
  DNS→169.254.1.2 (udp/tcp 53) accept
  169.254.1.1 accept                      # pasta DNS 代理
  192.168.90.47/48 (udp/tcp 53) accept    # 公司 DNS, 仅 53
  172.22.8.94/32 accept                   # 白名单条目
  119.147.156.0/24, 183.61.236.0/24 accept
  169.254.1.2 / 192.168.65.254 / 192.168.65.165 accept   # 网关/host 原自动放行面
  ct state established,related accept
  ip saddr <container-ip> drop            # 兜底默认拒 (loopback 不匹配此条, 不受影响)
```

验证矩阵 (容器内实测):

| 目标 | 期望 | 结果 |
| --- | --- | --- |
| https://www.baidu.com (未放行) | 拦 | 000 超时 |
| https://ai-work.changzhi.top (放行) | 通 | 401 (未带密钥的正常响应) |
| https://maven.aliyun.com (放行) | 通 | 404 (路径语义, 连接/TS 正常) |
| DNS 解析 | 通 | 正常 |
| git 桥 127.0.0.1:9418 / ssh | 通 | 正常 |
| mvn 编译冒烟 | 通 | 通过 |

## 建议的持久修复

1. `build_ruleset()` 补 `output` 链: whitelist 体与 input 同构 (saddr 过滤式规则可原样镜像); blacklist 体 = deny 条目 drop + established accept.
2. DNS 放行改为与容器实际 resolv.conf 对齐: 从 `podman exec <容器> cat /etc/resolv.conf` 推导 nameserver 集合放行 53, 而非只放行一个网关地址.
3. 测试补真出站阴性对照: 在 pasta 拓扑 (或至少对真实非放行公网 IP) 断言容器主动连接被拒; bridge 夹具的 gateway 探测不能作为 "默认拒" 依据.
4. SKILL.md/risks.md 相关措辞随修复核实修订 ("容器流出全断" 在修复前不成立; 网关自动放行的 DNS 依赖描述与 F015 一并核对).

## 关联

- `docs/changes/use-sandbox-worktree/DECISIONS.md` F015 (pasta 多实例串台注入错 netns) — 同为 whitelist fail-open 面, 已修; 本报告是另一独立面.
- 热修操作记录: 本会话经 `podman unshare nsenter --net=<SandboxKey> nft -f -` 注入, 与 ops.md 救场通道一致.

## 修复记录 (2026-09-17)

四项建议全部落地:

1. **output 链** (`scripts/net-firewall.py`): 过滤链扩为 forward/input/output 三链镜像同构 (`CHAINS` 常量); whitelist 体 = 网关 DNS + `--dns` 条目 (仅 53) + allow 条目 + established 回程 + saddr 兜底 drop, blacklist 体 = deny drop + established; 注入后校验升级为三链标记计数. conflict 守卫/merge 重放/remove 按源地址清理同步覆盖 output 链.
2. **DNS 对齐**: net-firewall.py apply 新增 `--dns <IP>` (whitelist 专属, 仅 udp/tcp 53, 去重去网关; blacklist 传入直接拒); swt.py 编排侧 birth/resume 经 `podman exec <容器> cat /etc/resolv.conf` 推导真实解析器自动传入 (解析函数 `parse_resolv_conf_nameservers`: 仅 IPv4/去重保序; 读不到 stderr 告警并退回网关单地址), 网络记录新增 `auto-dns`.
3. **真出站阴性对照** (`tests/test_swt_m04.py`): 新增 PastaFixture + PastaOutboundTestCase — pasta 直连拓扑 (生产同构, 注入点 = SandboxKey) 下 A/B 探针: 同一目的地 (host 监听经 map-guest-addr) 仅规则集有无放行条目之差, 断言 去条目后 TIMEOUT; 另覆盖容器内回环 (git 桥同形) 不受 saddr drop 误伤 + --dns 条目三链落位. 阳性对照在旧代码 (无 output 链) 下阴性断言必失败, 是本 bug 的专属探针. 镜像引用在 swt-m03 缺席时回落本机最新 sandbox-worktree base 层 (生产机可跑).
4. **文档**: SKILL.md whitelist 语义 (三链覆盖 + 解析器自动放行), risks.md 自动放行面拆解 (网关全端口 + 解析器 53), ops.md 手工救场须带 --dns 的提醒.

本机验证: bridge 夹具 14 项 + pasta 回归 5 项全过; pasta 拓扑手工冒烟 (放行 OPEN / 去条目 TIMEOUT / 非放行公网 IP TIMEOUT / 容器内回环 OPEN / getent 解析正常 / remove 三链 15 条) 与热修验证矩阵一致.

### 冷审返工 (2026-09-17, 审查方 gpt-5.6-luna/thinking high)

审查结论原为 "需返工": 2 阻塞 + 8 建议. 逐条核定后 2 阻塞 + 4 建议采纳修复, 其余不采纳或部分采纳:

1. **established 泄漏** (阻塞, 采纳): 原 output 链的 `ct state established,related accept` 放在兑底 drop 前, 容器先连已放行目标建连, 策略收紧去掉该条目后旧连接仍因 established 继续出站. 修复: output 链 established 改为方向限定 `ct direction reply` (只放 host 发起连接的出向应答), 容器主动连接属 original 方向, 收紧即断; 放行目的地的流量仍由 daddr 规则接纳. input/forward 保留双向 established (容器发起连接的应答与 host 发起连接的来包都是必需回程). 回归: pasta 拓扑持连接跨 re-apply 断言 FLOW-BLOCKED (test_05).
2. **apply 非原子** (阻塞, 采纳): 先单独删表再注入, 中间/失败态无表 = fail-open. 修复: 删表与建表合并为同一 nft 事务 (`nft -f` 整文件原子), 注入失败旧表原样保留.
3. **逐链校验** (建议, 采纳): 注入后校验从全局标记计数改为按链解析, 每链各自断言 IPv6 兑底; 测试侧 test_03 同步改逐链结构断言.
4. **merge 句柄守卫** (建议, 采纳): 发现缺 handle 无法安全重放的源地址规则时 APPLY-UNSAFE-MERGE 拒绝, 不静默丢弃.
5. **DNS 推导异常路径** (建议, 采纳): podman 缺失 (SwtEnvError) / exec 超时 (TimeoutExpired) 捕获告警退回网关; NetworkPlan 缺容器名时也告警不静默; 新增接缝 (network_plan_from_record 带出容器名) 与异常路径单测.
6. **pasta blacklist 出站对照** (建议, 采纳): 新增 test_04 (deny 条目出站 TIMEOUT + 回环/自身 IP 不误伤).
7. **计数断言按链全量结构化 / removed 计数脆弱** (部分不采纳): verify 侧与 test_03 已逐链; removed=3/9 保留 — 它钉住精确行为, 规则数合理变化本就该随测试更新.
8. **SKILL.md "流出全断" 措辞** (随修复 1 解决): output 链方向限定后, 策略收紧即断既有容器主动连接, 措辞成立, 不改.
