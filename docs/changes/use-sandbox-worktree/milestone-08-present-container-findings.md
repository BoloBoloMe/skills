# MILESTONE-08 容器内展示链 findings 与执行记录

状态: 实测完成. 依据: roadmap/MILESTONE-08.md, DECISIONS.md D021/D024, TECHNICAL.md, general/present/SKILL.md, general/present/scripts/web_server.py 现状.

## 执行环境与口径

- host: 本机 rootless podman (pasta 网络), 测试镜像 `swt-m08-present:test` = `localhost/swt-m03:latest` (M03 实际镜像, 2026-09-04 构建) + `apt-get install python3`.
- 容器: `podman run -d --name swt-m08-present -p 22 -p 53417 swt-m08-present:test` (两映射 host 侧均动态分配, `podman port` 发现: 22→36947/42953, 53417→34377/44885).
- 页面目录/增挂目录/web_server.py 均放容器内 agent 家目录, 路径 `~/.agents/skills/present/scripts/web_server.py` 代表 base 层 skill 库全量 COPY (D014/D023) 后的真实布局; 页面含合规 `__PRESENTATION_STATE__`.
- 服务经 ssh (agent, 真实用户路径, SSH_CONNECTION 存在) 启动; host 侧以 curl 代替浏览器验证可交付性 (127.0.0.1 与 LAN IP 192.168.31.252 双地址).

## 实测结果 (全部为实测值, 非推断)

### 1. 容器内 start + 端口映射交付: 通

- 容器内 `web_server.py start 53417 /home/agent/present-2026-09-05 --bind 0.0.0.0` → success JSON, bind 0.0.0.0, roots 落盘.
- host `curl http://127.0.0.1:44885/` → 200 顶层 listing; 抓 HTML 文件内容一致; `http://192.168.31.252:44885/` 同样 200 (host 浏览器可交付成立, 同网段可达面 = bind 0.0.0.0 的既定取舍, 与 ssh 远程模式同).
- `curl http://192.168.216.53:44885/` (tun0 地址) 也 200: 交付 URL 的 host 段选哪个 host 地址取决于用户从哪看, skill 容器分支交 host 侧会话选择, 与 `_detect_lan_host` 输出无关 (见 3).
- 容器端口直连 `192.168.216.53:53417` host 侧不可达 (符合预期: 只有映射端口可达).

### 2. 动态端口交付: 通, 且规则=映射在 create 时钉死容器端口

- `-p 53417` host 侧端口动态分配 (44885), create 后 `podman port` 发现; 与 F006 一致, URL 由 host 侧用发现值组装.
- 关键实测: 服务在容器内换端口重启到 53418 后, 原映射 (容器端口 53417) host 侧 000 不可达; 回到 53417 重启即恢复 200. 结论: **容器端口不是可随便重选的自由变量**, 容器分支必须规定 "复用创建时映射的同一容器端口", 不适用 host 模式 "port_in_use 换端口重试" 的自由度 (换端口 = 换 URL 失效, 恢复手段是容器重建加映射, 成本远高于 host 模式重试).

### 3. URL 输出字段在容器内不可直接交付

- ssh 会话内启动: `url: http://192.168.216.53:53417/` — 192.168.216.53 是 host 的 tun0 地址 (pasta 把 host 接口地址复制进容器, 容器自视地址与之相同, `hostname -I` 实测同值); host 段碰巧可用但**端口是容器端口**, 直接点击不可达 (实测 53417 直连失败).
- `podman exec` (root, 无 SSH_CONNECTION) 启动: `url: http://df42465d9d5a:53418/` — 回落 hostname, 完全不可用.
- 结论: 输出 JSON 的 url/hostname/lan_ip 在容器模式一律不直接交付; host 侧会话以 `podman port` 发现值 + host 地址重建 URL. web_server.py 本体不需要为容器改 URL 逻辑 (该字段在 host ssh 模式仍是权威).

### 4. add-dir (present ISSUE-02 考察点): 可用, 无需绕过

- 容器内 `add-dir /home/agent/present-extra` → success, roots 两目录; host 侧顶层 listing 立即变两文件并集, 增挂文件可取; 同目录重复 add-dir 幂等 (roots 不变).
- 控制面 namespace 守卫实测: 从容器内非 loopback 源 (容器自身 192.168.216.53:53417) POST add-dir → 无响应挂死 (守卫拒绝, curl 无输出), 只有容器内 CLI (loopback) 成功. 结论: MILESTONE-08 的担忧不成立, present ISSUE-02 产物在容器路径直接可用, host 侧不参与挂载.

### 5. 复用挂载 (present ISSUE-04 考察点): 可用, 但受 UID 边界约束

- 同 bind (0.0.0.0) 同 UID 二次 start → `reused: true`, 走控制端点幂等挂载, 请求端口差异仅 warning (请求 53418, 服务保持 53417); bind 改 127.0.0.1 → `bind_conflict`, 拒绝复用.
- UID 边界实测: agent (ssh, 容器内 uid 1000) 已有实例时, `podman exec` 以 root (uid 0) 再 start → **不复用** (新实例 root@53418, `reused: false`): root 视角运行时目录是 `/tmp/pi-present-web-0`, 且读 agent 的 0600 server.json 会 EACCES. 同容器出现 agent@53417 与 root@53418 双实例并存, host 映射命中的是容器端口拥有者 (53417 = agent 实例). 结论: 容器分支应固定 "同一用户身份操作" (真实路径 = 一律 ssh 的 agent, 与 D021 委派配方一致), UID 混用是坑但真实路径不触发.

### 6. stop (缺失考察点): 可用, 且随容器灭自动兜底

- 容器内 `stop` → success; host 侧立即 000; 容器内 `status` → `alive: false`; 运行时目录仅剩 .lock 与 server.log (server.json 已删, 与 host 模式行为一致).
- **stop 缺失无影响成立 (实测)**: 服务存活状态下直接 `podman rm -f`, 容器内进程随 netns 消灭, host 映射端口立即释放 (000, `ss` 无监听残留), host 侧无任何 pi-present-web 残留 (host 的 /tmp/pi-present-web-1000 为 2026-09-03 起 host 侧历史产物, 与本测试无关, 未触碰). 结论: 终结容器不必先 stop; stop 只在容器存活期内有意义 (换目录重挂/换 bind).

### 7. 空闲 TTL 与 runtime 目录: 随容器生灭, 无跨容器承诺

- 运行时目录在容器层 `/tmp/pi-present-web-1000` (agent) 或 `-0` (root), `rm` 容器即消失; 容器重建从零开始, 无 host 侧状态. idle 24h 自退逻辑在容器内同样成立 (代码路径无平台分支, 未单独长测等待).

## 结论: MILESTONE-08 考察点逐项回答

- 容器内 `start <port> <root> --bind 0.0.0.0` + 端口映射交付 URL: 成立, 已实测打通.
- ISSUE-02 (add-dir) 影响: 无, 容器路径直接可用 (实测 4).
- ISSUE-04 (复用挂载) 影响: 无, 真实路径 (同 UID) 幂等复用可用 (实测 5).
- stop 缺失影响: 无, 随容器灭自动回收 (实测 6).
- 全部与预期一致, 无需为容器路径修改 web_server.py.

## 镜像/部署依赖 (交 MILESTONE-07 需求清单)

- python3: M03 最简镜像无 (`which python3` 实测为空), base 层需求清单须加 `python3` (web_server.py 纯标准库, 无第三方依赖).
- skill 库全量 COPY (D014/D023) 已覆盖 web_server.py 进容器路径, 无额外动作.
- ps/procps: 镜像内已有 (`/usr/bin/ps` 实测), stop 的 `ps -o args=` 校验可用, 无需加装.

## 回归

- present 自带测试套件 (web_server lifecycle/content/control_plane/cli + skill 契约): 44 passed (0 failed), 本次改动零代码, 全绿.
- tests/test_swt_m03.py: 15 passed + 3 subtests (9902f268 回归, 由并行 M04 会话触发).
- general/present/tests/test_browser_session.py 存在 5 个与本次无关的既有失败 (access-web 浏览器环境依赖), 改动前同样失败.

## 权威输入缺口与处置

1. MILESTONE-08.md 原文 "present / explain-diff / probe 等跟随" 未定义跟随形式. 处置: 按 "跟随 = present 行为变化的跟随" 落为 explain-diff 与 probe 各一句容器环境回退声明 (present 容器分支为权威, 跟随者零新行为), 未扩大范围.
2. 容器模式端口规则 (容器端口不可换) 为本次实测新知, MILESTONE-08.md 与 TECHNICAL.md 均无预设. 处置: 记录于本文件与 SKILL.md 容器分支, 未改两者原文.
3. 未触碰: 用户真实仓库 (全链路仅 /tmp 与一次性测试容器), roadmap/MILESTONE-08.md 状态 (保持进行中), present-web-server 本体范围外的需求 (登录墙等), 并行 M04 会话的进行中产物.
