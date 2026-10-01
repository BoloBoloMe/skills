# /list-sandbox (swt list 只读清单 + pi 扩展) 决策账本

## 决策

### D001 扩展落位: skill 内 pi-extension, 随 skill 分发
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: pi 扩展代码放 `workflow/use-sandbox-worktree/pi-extension/` (部署到 `~/.agents/skills/use-sandbox-worktree/pi-extension`), 仿 mailbox skill 先例. 理由: 扩展必须以相对路径锚定 skill 内 `scripts/swt.py`, 保证扩展与脚本同版本演进. 已排除: 仓库级 `pi/extensions/` (需硬编码部署路径, 脱离 skill 版本边界). settings.json 登记机制见 D012.
- 依赖事实: F002, F007
- 预计影响: 新文件 `workflow/use-sandbox-worktree/pi-extension/index.ts`; sync-to-pi.py (D012)
- 实际影响:
- 需要调整:

### D002 清理定义与 "还在使用" 语义
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 清理沙盒工作树 = 删掉容器 (即 terminate 语义); host 侧 git worktree 不要求清理 — 刻意保留, 防止清理操作误删尚未推送的 git-worktree 导致成果丢失 (用户陈述). "还在使用" = 容器存在于 podman (未被清理). 该定义与现行 terminate 行为一致 (terminate 后母体目录与 config 原样留存), 不新增清理机制; /list-sandbox 天然只列存在的容器, 已 terminate 的自然消失.
- 依赖事实: F001
- 预计影响: swt.py list 子命令枚举谓词; SKILL.md 术语节 (执行阶段补记)
- 实际影响:
- 需要调整:

### D003 列表范围与状态双轴
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: list 跨仓枚举本 host podman 全部带 `sandbox-worktree.repo` label 的容器 (键存在匹配, 不限仓). 每容器三组状态字段: `podman-state` (podman 状态字符串原样透传, 如 running/exited/created/paused, 可为 unknown, schema 非闭集, 未知值照传) / `lifecycle` (active/retired/unknown, 来自 runtime 记录) / `record-state` (matched/missing/corrupt). 拒绝把三者压成单一 "三态枚举": running/stopped 是 podman 运行轴, retired 是 swt 生命周期轴, 混轴丢信息 (retired 容器也可能被手工 podman start, 记录缺失时 retired 又不可知) — 反方审查论点 3, 采纳. 停止容器不交付不可达入口 (UD-11 语义), 只显示状态与 resume 提示; lifecycle=retired 标注 "仅可终结". 已排除: 只列 running (停止容器未被清理, 正属 "还在使用", 列出提醒收拾).
- 依赖事实: F001, F008
- 预计影响: swt.py list 输出 schema
- 实际影响:
- 需要调整:

### D004 组装归属: swt.py 新只读子命令, 扩展纯连接器
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 访问入口的发现/状态合并/端口现查/组装逻辑全部留在 swt.py 新增只读子命令 `list`; pi 扩展为纯连接器 (spawn `uv run python <skill>/scripts/swt.py list`), 只做容器选择与文本展示, 不实现任何 podman/runtime/组装业务 (mailbox 纯连接器先例). 已排除: (a) status 加跨仓 flag — status 契约是 "本主仓", 顶层 STATE 绑定主对, 跨仓模式撕裂 schema; (b) TS 扩展直跑 podman + 读 records root — 组装逻辑两种语言各一份, 漂移风险. 子命令新增按 D041 先例修订 use-sandbox-worktree 账本 D025 (display-check 已开过 "新增只读子命令不改状态" 的口子).
- 依赖事实: F002, F007, F009
- 预计影响: swt.py (list 子命令); `docs/changes/use-sandbox-worktree/DECISIONS.md` D025/D027 修订; ADR-0009 补充
- 实际影响:
- 需要调整:

### D005 LIST 输出协议
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: list 沿 D027 输出精神: stdout 进度行人话 + 末行 `LIST {...}` 单行 json; schema 带版本号, 只加字段不改名. 顶层字段: `schema` / `scope` (含所用 records-root 与完备性声明: podman 全量 × 本记录根) / `containers[]` / `warnings[]`. 退出码仅 0 成功 / 4 环境 (podman 缺失或整体不可用); 只读无 DECIDE 无 PARTIAL. 单容器 inspect/port 采集失败或枚举期间容器被删: 该条目记 `collection-errors`, 整体仍 exit 0 (只读快照的现实, 单项失败不拖垮全表). `LIST` 末行 + 0/4 是 D027 协议的又一显式例外 (先例: display-check 的 0/1/2 无 STATE; enroll-device-key 成功直返无 STATE 行 — 该例外当时未记账, 补记于 use-sandbox-worktree 账本 D057), 修订 D027 时与各先例并列记账 — 反方审查论点 6, 采纳.
- 依赖事实: F009
- 预计影响: swt.py list; `docs/changes/use-sandbox-worktree/DECISIONS.md` D027 修订
- 实际影响:
- 需要调整:

### D006 records-root 对齐与诚实完备性
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: list 支持 `--records-root` 覆盖, 与生命周期子命令对齐 (辅助子命令 enroll-device-key 无此参数, 不泛称 "其余子命令"); 缺省 `~/.agents/sandbox-worktree/`. 因容器 label 不携带 records-root/identity 信息且扫描只读单一记录根, 跨记录根创建的容器会被 podman 正确发现但记录不匹配 — 此时标注 "本记录根无记录", 不得称 "孤儿" 或宣称全 host 权威记录; record-state 区分 missing (无文件) 与 corrupt (文件在但不可解析). 反方审查论点 1, 采纳. v1 不做 roots 注册表或 birth 落 records-root label (延后, 需要时独立设计).
- 依赖事实: F008
- 预计影响: swt.py list schema 的 scope 字段
- 实际影响:
- 需要调整:

### D007 多网卡局域网候选地址 (swt-cross-host D010 的 list 语境修订)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: list 运行时枚举 host 全部非回环全局 IPv4, 接口名过滤复用现行 `TUNNEL_INTERFACE_PREFIXES` 全集 (tun/tap/wg/ppp/utun/ts/tailscale/docker/veth/br-/virbr/zt/podman), 不自造窄集 — 反方审查论点 4b: 自造窄集会让 VPN/Tailscale/Docker bridge 地址混入, 与 M14/F022 实测冲突. `records-root/lan-address` 已确认值排最前标 "已确认"; 其余每个真实网卡生成完整入口行 (一切含局域网地址的入口命令 — ssh 局域网入口/noVNC 局域网隧道/web 局域网 URL/herdr remote 局域网命令/窗口直飞模板 — 逐网卡代换地址), 整块标 "候选 (未确认可达)". 这是对 swt-cross-host-access M04 D010 ("有 IP 不等于可达, 只交付已确认值") 在 list 展示语境的显式修订 — 用户点名要多网卡多地址交付 (F010), 列表语境试错成本 = 点开失败且标签已明示; birth/resume 交付维持 D010 原样不动.
- 依赖事实: F004, F005, F010
- 预计影响: swt.py list 入口组装
- 实际影响:
- 需要调整:

### D008 访问入口条目范围与命名
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: list 展示的条目集命名 "访问入口" (access entries), 不叫 "交付包" — 交付包是 birth/resume 必须齐发的全量契约 (含风险声明与容器内路径契约), 同名不同集会让 F3 缺发语义歧义 — 反方审查论点 8, 采纳. 访问入口 = 交付包的入口子集: ssh 双入口 (本机/局域网, 含密码与私钥路径) / noVNC 本机 URL + 局域网隧道命令 / web 双 URL / herdr remote 双命令 / 窗口直飞模板 / host-display 三态. 清单在入口子集之外附带容器摘要元数据 (镜像与分支) 供识别, 不属入口本身 (交付包定义里无独立镜像项, 分支住在容器内路径契约中 — 反方审查论点 2 的集合口径修正). 风险声明与容器内路径契约不进 (birth 语境, 常驻列表是噪音). F3 精神沿用: 入口缺项 (如 lan 未确认/display absent/headed 脚本缺席) 打显式 reason 行, 不静默丢失.
- 依赖事实: F002, F005
- 预计影响: swt.py list; `docs/language/UBIQUITOUS_LANGUAGE.md` 访问入口词条
- 实际影响:
- 需要调整:

### D009 UI 组件与命令
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: pi 命令名 `/list-sandbox`: `ctx.ui.select` 列容器 (选项含容器名/状态/分支摘要) → `ctx.ui.custom()` 滚动文本组件展示选中容器的访问入口, 只给人看不进 LLM 上下文. 已排除: sendUserMessage 注入会话 (花 token 且污染会话); 自定义 entry 钉进会话记录 (本期不需要持久, 即开即看).
- 依赖事实: F006
- 预计影响: `workflow/use-sandbox-worktree/pi-extension/index.ts`
- 实际影响:
- 需要调整:

### D010 模式降级
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 按 ctx.mode/ctx.hasUI 分路: TUI → select+custom; RPC → notify 摘要; print/json → stderr 一行 "交互展示需 TUI/RPC 模式; 裸数据: uv run python <skill>/scripts/swt.py list" (notify 在 print/json 是 no-op, stderr 不污染 JSON 事件流) — 反方审查论点 5, 采纳. 非 host 环境 (容器内/设备侧 pi 无 podman): 命令仍注册, 探测失败按同路降级输出, 不崩不静默.
- 依赖事实: F006
- 预计影响: `workflow/use-sandbox-worktree/pi-extension/index.ts`
- 实际影响:
- 需要调整:

### D011 无记录容器的呈现与清理指引
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: record-state=missing/corrupt 的容器照列, 能组装的入口项照发, 缺项打显式 reason 行; 清理指引文案 = "无 runtime 记录, terminate 拒绝受理; 手工清理自行判断: podman rm <名>" — 与现行 terminate 行为一致 (runtime 缺失直接拒绝, 不自动拆除未登记资源). 已排除: 顺手扩 terminate 支持未登记强拆 — 新危险能力 (脏检查/podman-id 指纹绑定/审计都要重定义), 留独立评审, 本期不碰 — 反方审查论点 2, 采纳.
- 依赖事实: F003
- 预计影响: swt.py list reason 行组装
- 实际影响:
- 需要调整:

### D012 sync-to-pi.py 扩展登记泛化与集合对账
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `_merge_extensions` 从硬编码 mailbox 一家泛化为扫描 `~/.agents/skills/*/pi-extension` 逐个登记; 登记改集合对账语义: 新增当前存在的路径, 移除 sync 管理过且现已消失的路径 (管理标记需落地实现, 如登记清单 sidecar 文件), 用户手工加入的 extensions 项永不触碰. 反方审查论点 7: 只追加无清理会在扩展删除/改名后积累失效路径, 采纳.
- 依赖事实: F007
- 预计影响: sync-to-pi.py
- 实际影响:
- 需要调整:

### D013 范围边界
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 只枚举本 host 的 podman; 不经信箱 mesh 聚合其他设备/其他 host 的容器. 跨设备清单 out of scope, 未来需要时独立设计.
- 依赖事实: F001
- 预计影响: 无 (边界声明)
- 实际影响:
- 需要调整:

## 事实

### F001 podman label 契约
- 状态: 当前有效
- 来源: `workflow/use-sandbox-worktree/scripts/swt.py` (birth 打 label 与 podman_container_state 过滤代码)
- 内容: swt 容器带 label `sandbox-worktree.repo=<主仓>` 与 `sandbox-worktree.mother`; `podman ps -a --filter label=<key>` 键存在匹配可跨值枚举全部 swt 容器; 端口经 `podman port <名>` 活取.

### F002 交付行组装唯一事实源
- 状态: 当前有效
- 来源: `workflow/use-sandbox-worktree/scripts/swt.py`
- 内容: `print_delivery_lines` / `web_delivery_lines` / `headed_delivery_lines` 均在 swt.py; birth/resume/status 的交付文本都经它们产出. 局域网已确认值持久化于 `<records-root>/lan-address`.

### F003 terminate 现行拒绝无记录容器
- 状态: 当前有效
- 来源: swt.py terminate 路径
- 内容: runtime 记录缺失时 terminate 抛 PreconditionError "容器存在但 runtime 记录缺失, 不自动拆除未登记资源".

### F004 现行隧道/虚拟接口过滤全集
- 状态: 当前有效
- 来源: swt.py `TUNNEL_INTERFACE_PREFIXES` (注释引 M14 发现 4; 反方审查引 F022)
- 内容: `tun, tap, wg, ppp, utun, ts, tailscale, docker, veth, br-, virbr, zt, podman` — 这些接口上的全局地址局域网够不着, 不得作局域网入口交付; VPN 在场时默认路由指向隧道, 跟默认路由必取错.

### F005 swt-cross-host-access M04 D010
- 状态: 当前有效
- 来源: `docs/changes/swt-cross-host-access/milestone-04/DECISIONS.md` D010
- 内容: 宿主可能多网卡/VPN, 有 IP 不等于用户设备可达; 局域网地址先用已确认值 (records-root/lan-address, birth 经 --lan-ip DECIDE 确认), 无法确定才问用户, 不把猜测地址当可用链接交付.

### F006 pi 扩展 UI 能力边界
- 状态: 当前有效
- 来源: pi 官方文档 `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/extensions.md`
- 内容: `ctx.ui.select/confirm/input` TUI 可用, RPC 模式经请求-响应协议也可用; `custom` 仅 TUI (RPC 返回 undefined); `notify` TUI+RPC 可用, print/json 模式全部 UI 方法为 no-op (`ctx.hasUI` 为 false); 命令经 `pi.registerCommand` 注册.

### F007 mailbox pi-extension 先例
- 状态: 当前有效
- 来源: `workflow/mailbox/pi-extension/index.ts`; sync-to-pi.py `_merge_extensions`
- 内容: 扩展纯连接器 (mailbox 账本 BR-007/D004), spawn skill 内脚本; 部署路径登记进 pi settings.json 的 extensions 数组; `_merge_extensions` 幂等追加, 现硬编码 mailbox 一家, 只追加不清理.

### F008 记录根关联缺口
- 状态: 当前有效
- 来源: swt.py `load_repo_runtimes`/`repo_runtime_files`; SKILL.md 环境前置节; 反方审查论点 1
- 内容: runtime 扫描只读调用方传入的单一 records_root; 容器 label 不含 records-root 或 runtime identity; `--records-root` 是 SKILL.md 公开契约 (生命周期与诊断子命令支持覆盖; 辅助子命令 enroll-device-key 除外, 见 use-sandbox-worktree 账本 D057). 跨记录根创建的容器会被 podman 发现但记录不匹配, 与 "记录真缺失" 不可区分.

### F009 swt 子命令与协议现状
- 状态: 当前有效
- 来源: `docs/changes/use-sandbox-worktree/DECISIONS.md` (D025/D026/D027/D041); ADR-0009
- 内容: D025 单 module 子命令形态 (决策时五子命令含 switch; switch 后被删除且当时未记账, 补记于 D056). 现行命令面: 生命周期四子命令 birth/resume/status/terminate + 诊断 display-check (D041, 退出码 0/1/2, 无 STATE 行) + 辅助 enroll-device-key (swt-cross-host-access M08 ISSUE-06/N4 所增, 成功直返无 STATE 行, 例外未记账, 补记于 D057); D027 规定生命周期全子命令 STATE 末行 + 0/1/2/3/4 退出码.

### F010 用户需求 (多网卡交付)
- 状态: 当前有效
- 来源: 用户陈述 (2026-10-01 盘问)
- 内容: /list-sandbox 交付须同时含本机与局域网访问地址; 发现多个网卡时, 局域网访问地址要多个.

### F011 反方审查已执行
- 状态: 当前有效
- 来源: herdr 子代理 (gpt-5.6-sol) 按 opposing-viewpoint skill 攻击, 2026-10-01
- 内容: 8 项论点 (records-root 关联缺口 / orphan-terminate 冲突 / 状态混轴 / 候选地址违反 D010+过滤集回退 / print-json 无 UI 输出 / D027 修订不足 / 登记无生命周期 / 命名偷换) 经评估全部成立 (程度不同), 逐项吸收进 D003/D005/D006/D007/D008/D010/D011/D012; 报告原文为容器临时文件 `/tmp/opposing-list-sandbox.md`, 不入库, 吸收结果以本账本各决策为准.
