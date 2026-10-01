# /list-sandbox 沙盒容器清单与访问入口 Product Spec

## 背景

用户在 host 上同时维护多个 sandbox-worktree (多仓多对并存), 容器一多, "哪些还在用, 入口是什么" 就得翻 birth 会话记录或手敲 podman 命令拼凑. 提出方是用户本人 (host 侧操作者), 受益者是日常在多对沙盒间切换的用户: 在 host pi 里一个命令看到全部在用容器, 选中即得该容器的访问入口, 不用记端口和路径. 顺带把 "清理" 的口径钉死: 删掉容器即清理, host 侧 git worktree 刻意不动, 防止误删未推送成果.

## 目标

- G-001: 用户在 host pi 执行 /list-sandbox 能看到本 host 全部还在使用的沙盒容器 (跨主仓), 各带状态标注, 选中其一即得访问入口.
- G-002: 访问入口同时含本机与局域网两套地址; 发现多个网卡时局域网地址逐网卡成组交付, 已确认值排最前.
- G-003: 停止容器不被隐藏也不交付不可达链接; 无记录容器得到诚实的 reason 行与手工清理指引.
- G-004: 无 UI 模式 (print/json/rpc) 与非 host 环境优雅降级, 不崩溃不污染输出流.
- G-005: 裸终端运行 swt.py list 可独立使用, 输出人话进度行 + 末行 LIST 单行 json.
- G-006: sync-to-pi.py 自动登记扩展路径, 旧扩展移除后登记不残留.

## 非目标

- NG-001: 不聚合其他设备/其他 host 的容器. (理由: 经信箱 mesh 的跨设备清单是独立设计, 本期边界只到本 host podman.)
- NG-002: 不扩展 terminate 受理无记录容器. (理由: 未登记强拆是新危险能力, 脏检查/指纹/审计都要重定义, 留独立评审.)
- NG-003: 不改 birth/resume 的交付语义. (理由: 已确认值单值机制 (swt-cross-host D010) 原样, 多网卡候选只发生在 list 展示语境.)
- NG-004: 不清理 host 侧 git worktree. (理由: 清理 = 删容器; worktree 保留以防误删未推送成果, 母体存删用户自决.)
- NG-005: 访问入口不含风险声明与容器内路径契约. (理由: 那是 birth 交付包的全量契约语境, 常驻列表只给入口子集.)

## 业务规则

- BR-001: 清理沙盒工作树 = 删除容器; 母体 worktree 不随之清理.
- BR-002: 还在使用 = 容器存在于 podman (不论 running/exited).
- BR-003: 非 running 容器不交付可达入口, 只给状态与恢复指引.
- BR-004: 入口缺项必须显式 reason 行, 不静默丢失.
- BR-005: 局域网入口中 lan-address 已确认值排最前标 已确认; 其余候选按网卡成组, 标 候选 (未确认可达).
- BR-006: 网卡枚举排除隧道/虚拟接口 (TUNNEL_INTERFACE_PREFIXES 全集: tun/tap/wg/ppp/utun/ts/tailscale/docker/veth/br-/virbr/zt/podman).
- BR-007: /list-sandbox 的展示内容不进入会话的 LLM 上下文. (审计)
- BR-008: sync-to-pi.py 的扩展登记永不触碰用户手工加入的 extensions 项.
- BR-009: swt.py list 为只读子命令: 不改 runtime 记录, 不动防火墙规则, 不持生命周期锁.
- BR-010: pi 扩展为纯连接器: podman/runtime 业务逻辑全部经子进程执行 swt.py list, 扩展不自行实现. (审计)

## 验收标准

```gherkin
# language: zh-CN
功能: /list-sandbox 沙盒容器清单与访问入口

@AC-001 @normal @G-001 @BR-002
场景: 跨仓全列
假定 host 的 podman 中有两个主仓的三个容器 swt-feature-a 与 swt-hotfix-b 与 swt-legacy-c
而且 swt-feature-a 处于 running 且生命周期为 active
而且 swt-hotfix-b 处于 exited 且生命周期为 active
而且 swt-legacy-c 处于 exited 且生命周期为 retired
当 用户在 host pi 执行 /list-sandbox
那么 选择列表同时呈现三个容器
而且 每个条目带 podman 运行状态与生命周期标注

@AC-001 @edge @G-001
场景: 空清单
假定 host 的 podman 中没有任何带 sandbox-worktree.repo label 的容器
当 用户在 host pi 执行 /list-sandbox
那么 用户收到 无在用沙盒容器 的提示
而且 pi 不报错

@AC-001 @normal @G-001 @BR-001
场景: 清理后消失
假定 容器 swt-feature-a 已被 terminate 且容器已删除
而且 其母体工作树目录仍存在于 host
当 用户在 host pi 执行 /list-sandbox
那么 选择列表不含 swt-feature-a
而且 母体工作树目录仍存在

@AC-002 @normal @G-001
场景: 选中看访问入口
假定 容器 swt-feature-a 处于 running 且本记录根的 runtime 记录匹配
当 用户在选择列表选中 swt-feature-a
那么 用户看到访问入口: ssh 双入口含密码与私钥路径, noVNC 本机 URL 与局域网隧道命令, web 双 URL, herdr remote 双命令, 窗口直飞模板, host-display 三态

@AC-002 @edge @G-001 @BR-004
场景: 入口缺项打原因
假定 容器 swt-feature-a 的镜像未解析出 headed 启动脚本
当 用户在选择列表选中 swt-feature-a
那么 窗口直飞位置呈现一条说明缺席的 reason 行
而且 其余入口照常呈现

@AC-003 @normal @G-002 @BR-005
场景: 单网卡已确认
假定 host 的 lan-address 已确认值为 192.168.1.10
而且 host 仅有一块物理网卡 wlan0 持有 192.168.1.10
当 用户在选择列表选中 running 容器
那么 局域网入口仅一组且标注 已确认

@AC-003 @normal @G-002 @BR-005
场景: 双网卡候选
假定 host 的 lan-address 已确认值为 192.168.1.10
而且 host 另有网卡 eth0 持有 192.168.2.20
当 用户在选择列表选中 running 容器
那么 已确认组排在最前
而且 eth0 候选组含 ssh 入口与 noVNC 隧道命令与 web URL 与 herdr remote 命令与直飞模板的完整入口行且标注 候选 (未确认可达)

@AC-003 @edge @G-002 @BR-006
场景: VPN 接口排除
假定 host 存在接口 tailscale0 持有地址 100.64.0.5
当 用户在选择列表选中 running 容器
那么 局域网入口的任何组都不含 100.64.0.5

@AC-003 @edge @G-002 @BR-005
场景: 无已确认值
假定 host 的 lan-address 文件不存在
而且 host 有网卡 eth0 持有 192.168.2.20
当 用户在选择列表选中 running 容器
那么 全部局域网入口为候选组
而且 不存在已确认组

@AC-004 @normal @G-003 @BR-003
场景: 停止容器不给可达入口
假定 容器 swt-hotfix-b 处于 exited 且本记录根的 runtime 记录匹配
当 用户在选择列表选中 swt-hotfix-b
那么 不出现 ssh 入口与任何 URL
而且 用户看到 resume 命令提示 uv run python scripts/swt.py resume --name swt-hotfix-b

@AC-004 @normal @G-003
场景: retired 标注
假定 容器 swt-legacy-c 的生命周期为 retired
当 用户在 host pi 执行 /list-sandbox
那么 选择列表中该容器标注 仅可终结

@AC-005 @normal @G-003 @BR-004
场景: 记录缺失
假定 容器 swt-orphan-x 带 sandbox-worktree.repo label 而本记录根无其 runtime 记录
当 用户在选择列表选中 swt-orphan-x
那么 条目标注 本记录根无记录
而且 缺失的入口项以 reason 行呈现
而且 清理指引为 podman rm swt-orphan-x
而且 不出现 terminate 指引

@AC-005 @edge @G-003 @BR-004
场景: 记录损坏
假定 容器 swt-orphan-x 的 runtime 记录文件存在但不可解析
当 用户在选择列表选中 swt-orphan-x
那么 条目标注 记录不可解析
而且 缺失的入口项同样以 reason 行呈现

@AC-006 @edge @G-004
场景: print 模式降级
假定 pi 以 print 模式运行
当 用户提交 /list-sandbox
那么 stdout 不出现交互界面
而且 stderr 呈现一行提示且含裸数据命令 uv run python <skill>/scripts/swt.py list

@AC-006 @failure @G-004
场景: 无 podman 环境
假定 pi 运行于无 podman 的容器内
当 用户执行 /list-sandbox
那么 用户收到 本环境无 podman, 仅 host pi 可用 的提示
而且 pi 不崩溃

@AC-006 @edge @G-004
场景: rpc 模式降级
假定 pi 以 rpc 模式运行
当 用户调用 /list-sandbox
那么 用户收到一条 notify 摘要

@AC-007 @normal @G-005
场景: 裸命令输出
假定 host 有容器 swt-feature-a 在运行
当 agent 在终端执行 uv run python scripts/swt.py list
那么 stdout 呈现人话进度行
而且 末行呈现 LIST 单行 json 且含 scope 与全部容器条目

@AC-007 @normal @G-005 @BR-009
场景: 裸命令只读
假定 host 有容器 swt-feature-a 与其 runtime 记录及防火墙规则
当 agent 在终端执行 uv run python scripts/swt.py list
那么 runtime 记录文件内容与执行前一致
而且 nftables 规则集与执行前一致

@AC-007 @edge @G-005
场景: 单容器采集失败
假定 podman ps 返回容器 swt-gone-y 且其 inspect 失败
当 agent 在终端执行 uv run python scripts/swt.py list
那么 swt-gone-y 条目含 collection-errors
而且 命令退出码为 0

@AC-007 @failure @G-005
场景: podman 整体不可用
假定 host 无 podman 命令
当 agent 在终端执行 uv run python scripts/swt.py list
那么 命令退出码为 4
而且 stderr 首行为 ENV 标签行

@AC-008 @normal @G-006
场景: 登记新增
假定 部署目录 ~/.agents/skills/use-sandbox-worktree/pi-extension 存在
当 agent 完成 sync-to-pi.py 的同步
那么 pi settings.json 的 extensions 数组含该扩展路径

@AC-008 @normal @G-006
场景: 登记回收
假定 pi settings.json 登记着一个 sync 管理过且现已消失的扩展路径
当 agent 再次运行 sync-to-pi.py
那么 该登记项被移除

@AC-008 @normal @G-006 @BR-008
场景: 手工项保留
假定 用户手工在 pi settings.json 的 extensions 数组加入 /my/manual/ext
当 agent 运行 sync-to-pi.py
那么 /my/manual/ext 原样保留
```

## 决策引用

- docs/changes/swt-list-sandbox/DECISIONS.md: D001, D002, D003, D004, D005, D006, D007, D008, D009, D010, D011, D012, D013
