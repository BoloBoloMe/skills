## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

running 且记录匹配容器的完整访问入口组装: `lans[]` 枚举 (非回环全局 IPv4, 排除 TUNNEL_INTERFACE_PREFIXES 全集接口, lan-address 已确认值排最前 kind=confirmed, 其余 kind=candidate) 与 `access-entries[]` (一切含局域网地址的入口命令逐网卡代换: ssh 局域网入口/noVNC 局域网隧道/web 局域网 URL/herdr remote 局域网命令/直飞模板; 本机入口不受网卡影响) + host-display 三态 + 缺项 reason 行 (无已确认值/无 headed 脚本等). 适合 AFK: 组装规则全部在 AC-003/AC-002 场景与 M1 接口不变量中固定.

## 覆盖依据

- Product: `docs/changes/swt-list-sandbox/PRODUCT.md`, AC-002 (组装面), AC-003
- Technical: `docs/changes/swt-list-sandbox/TECHNICAL.md`, 模块接口 (M1 不变量/lans/access-entries), 测试接缝, 安全策略

## 相关决策

- `docs/changes/swt-list-sandbox/DECISIONS.md`: D007, D008, D011 (reason 纪律部分)

## 允许范围

- `swt.py` 内 list 实现的入口组装部分 + 模块级辅助 (网卡枚举/入口行拼装).
- 复用 `print_delivery_lines`/`web_delivery_lines`/`headed_delivery_lines` 的行内容逻辑 — 允许提取共享的行模板辅助函数供打印与 list 两用, 前提是不改变既有子命令输出文本.
- 扩展 `tests/test_swt_list.py`.

## 禁止范围

- 修改 birth/resume/status 的输出文本 (现有交付行逐字不变).
- 非 running / 无记录分支 (归 ISSUE-03).
- 改动 LIST schema 已定字段.

## 代码定位提示

- 入口行母本: `print_delivery_lines` (约 1660 行起) / `web_delivery_lines` (约 1560 行) / `headed_delivery_lines` (约 1571 行); lan 已确认值: `read_confirmed_lan_address` (约 609 行).
- 网卡枚举与过滤母本: `TUNNEL_INTERFACE_PREFIXES` 与 `lan_ip()` (约 584 行起) — list 需要返回全部而非首个, 写变体勿改原函数.
- host-display 与 headed-script 来源: runtime 容器记录字段 (`host-display`, `headed-script`), 参考 birth 记录更新处 (约 2467 行).

## TDD 切片

- TS-021:
  接缝: 接缝 B (podman fake-run), `tests/test_swt_list.py`.
  测试用例: TC-021.
  先写的失败测试: `test_running_container_full_entries` — fake running+matched 容器带三端口与 host-display=ok, 断言 access-entries 含 ssh 双入口 (密码与私钥路径字样), noVNC 本机 URL, web 双 URL, herdr remote 双命令, 直飞模板, host-display 行; 实现前 entries 为空, 失败.
  最小绿色实现范围: running+matched 路径的入口行拼装与字段挂接.
  不得测试: 行序以外的内部拼接细节.
  覆盖: AC-002 (组装面).
- TS-022:
  接缝: 同上.
  测试用例: TC-022.
  先写的失败测试: `test_lans_confirmed_first_candidates_per_nic` — fake `ip -o -4 addr` 返回 wlan0 192.168.1.10 / eth0 192.168.2.20 / tailscale0 100.64.0.5, lan-address 文件写 192.168.1.10; 断言 lans = [wlan0 confirmed] + [eth0 candidate], 无 100.64.0.5; 候选组入口行含 eth0 地址代换的 ssh/隧道/web/herdr/直飞全套; lan-address 缺席时全为 candidate 且无 confirmed.
  最小绿色实现范围: 网卡枚举变体 + 分组 + 逐网卡代换.
  不得测试: `ip` 命令调用次数.
  覆盖: AC-003.
- TS-023:
  接缝: 同上.
  测试用例: TC-023.
  先写的失败测试: `test_entries_reason_lines_and_no_secrets` — 无 headed-script 容器断言直飞 reason 行且其余入口照发; fake 私钥文件内容字符串不出现在 LIST 任何字段 (路径可以出现).
  最小绿色实现范围: reason 行纪律 + 输出不含密钥内容.
  不得测试: 未确认的脱敏规则.
  覆盖: AC-002 (缺项分支), 安全策略 (LIST 无秘密值).

## 验证入口

- `uv run --with pytest pytest -m "not e2e" -q tests/test_swt_list.py` 全绿 (含 ISSUE-01 用例不回归).

## 风险提示

- 行模板两用化 (打印与 list) 是本切片最大风险: 提取共享辅助时以既有输出文本逐字不变为红线, 既有交付断言套件 (`test_swt_m08_delivery` 等) 必须全绿.
- 直飞模板含 `$(id -u)` 设备侧展开语义, 代换的只是地址段, 其余逐字保留.

## 停止条件

- 需要改变任一 Spec/决策/issue 边界, 或共享辅助无法在不改既有输出的前提下提取时停止.

## 适合 AFK 的原因

组装规则全部由场景与不变量固定; 唯一的自由度 (行文案微调) 有既有交付断言做红线.

## 验收标准

- [ ] running+matched 容器 entries 全集 (TC-021).
- [ ] 多网卡候选/已确认排序与 VPN 排除 (TC-022).
- [ ] reason 行 + 无秘密值 (TC-023).
- [ ] 既有子命令输出零变化 (交付断言套件全绿).

## 被阻塞于

- ISSUE-01 (`issues/ISSUE-01-list-skeleton.md`)
