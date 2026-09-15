# Bug 反馈: net-firewall 缺 output 链, 白名单/黑名单对 "容器主动出站" 全部失效

- 日期: 2026-09-14
- 来源: cz_sdk 项目首次 sandbox 容器实跑 (whitelist 模式), 容器内 agent 自测发现
- 严重级: 安全 (fail-open, 白名单语义整体落空)
- 状态: 已热修单容器 (随容器存亡); 脚本级修复未做

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
