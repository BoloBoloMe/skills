# UNAUTHORIZED_DECISIONS.md — AFK 自主决定登记

MILESTONE-12 以 AFK 模式执行 (tdd-as-orchestra). 以下决定本应由用户拍板, 已在授权范围内自行决定, 逐条待用户追认. 每条含 问题/决策/理由/影响/风险 五项.

## U-001 M12 执行 spec 由代理派生

- 问题: tdd-as-orchestra 要求 EXECUTION.md 提供可执行 ISSUE, 但仓库 EXECUTION.md 只覆盖 MILESTONE-03 (ISSUE-01/02 已关闭), M12 无 ISSUE 拆分.
- 决策: 由本会话从 DECISIONS.md D025-D038 + design-caller 设计稿 (经反方修正) + D036 等价矩阵派生 `EXECUTION-M12.md` 与 `issues/ISSUE-05..11`, 再进入 TDD 循环.
- 理由: D025-D038 已拍完全部设计决策, 缺的是分解而非新决策; AFK 授权含 "自行决定本应由我拍板的事项"; 拆分属于编排者本职工作.
- 影响: M12 的 TDD 用例接缝由 spec 钉死, 不再逐条口头确认 (tdd skill 规定: 决策账本/Spec 已回答时不必再问).
- 风险: 派生理解可能与用户意图有偏差; 全部 spec 文字可审, 错误在 review 阶段与追认时暴露.

## U-002 决策收据机制的具体形态

- 问题: D026 定了收据原则 (一次性票据 + 指纹绑定), 未定存储位置, id 格式, DECIDE 行格式, 答案 flag 名称.
- 决策: 收据落 `<records-root>/runtime/<identity>/decisions/<decision-id>.json`, 消费即删; id = `d-<yyyymmdd-HHMMSS>-<seq>`; DECIDE 行格式 `DECIDE <id> <kind> <问题人话> 选项: <flag 形态>`; 答案 flag: 网络模式 `--mode/--allow/--deny`, 母体新建 `--new-mother`, 母体复用 `--reuse-mother`, 镜像 `--image <ref>`, resume 确认 `--confirm`, terminate/switch 强拆/强停 `--force`. 重跑时按 kind 匹配待决收据, 重算指纹比对, 不符则废票重新 DECIDE.
- 理由: design-caller §1.4/§2 示例已含大部分 flag 形态; resume 缺确认 flag (design 原文无 gate, D030 推翻后需补), `--confirm` 是最小补钉.
- 影响: swt CLI 契约与测试断言按此实现.
- 风险: flag 命名用户可能想改; 纯 interface 层, 改动成本低.

## U-003 runtime 状态位置与 identity 文件名

- 问题: design 提到 `~/.agents/sandbox-worktree/runtime/<identity>.json`, identity 未定义.
- 决策: swt 统一 `--records-root` flag (缺省 `~/.agents/sandbox-worktree`, 与 image-prep 一致); runtime 文件 = `<records-root>/runtime/<slug>-<sha1(project-id)[:8]>.json`, identity = 该文件名主体; project-id = 主仓绝对路径 (D024); slug 经 use-worktree slug.py 三参数形态取 dir 值 (M03 已验证契约); 审计登记 = 同目录 `audit.jsonl` 追加; 并发锁 = 同路径 `.lock` fcntl 非阻塞 (D034).
- 理由: 与 image-prep 记录根同屋 (D024); 文件名带 hash 防同 slug 碰撞 (D024 身份规则).
- 影响: 测试经 `--records-root /tmp/...` 隔离, 不碰真实记录根.
- 风险: 低; 路径规则一处实现.

## U-004 whitelist 模式下 daemon 地址自动并入 allow (接缝补钉, 重点追认)

- 问题: net-firewall whitelist 只放行 网关 DNS + --allow 条目; 容器到 host git daemon 的流量 (目的 = pasta 网关地址) 会被 drop, birth 的容器内 clone 必死. 权威输入未回答.
- 决策: birth/resume 在 whitelist 模式自动把 "容器可达的 daemon 地址 /32" 并入 allow 条目 (本机 daemon 落 0.0.0.0, 容器侧地址 = 网关地址), STATE/DECIDE 文案标注该自动条目; blacklist 模式无此动作.
- 理由: 容器唯一 git 通道是 daemon (BR-001 精神), 不放行则主链物理不通; 最小实现是 IP 级条目 (net-firewall 条目只收 IP/CIDR, 无端口语义).
- 影响: whitelist 对 "容器 → 网关 IP" 全端口放行 (不只 daemon 端口).
- 风险: 容器可经网关地址访问 host 任意监听端口 (sshd/其他服务), whitelist 对 host 方向的收敛失效 (internet 方向仍收敛). 端口级收窄需 net-firewall 条目支持端口谓词, 属接口再演进, 未做 — 若用户不接受, 替代 = daemon 绑专址 + 端口谓词扩展.

## U-005 switch --to 目标母体不存在的处理

- 问题: design-caller §1.4 说 "校验目标母体 ref 存在且工作区干净", 但其 §2.3 示例对无母体的 feat-search switch 成功 — 自相矛盾, D 账本未澄清.
- 决策: --to 收分支名原文, slug 化后: 对应母体 ref 已存在 → 校验 ref 与工作区干净, 脏则 exit 2; 不存在 → 允许, hideRefs 例外直接指向新 slug (授权域空换), 随后 birth 建母体. 两种情形 STATE 均标注 `target-mother-exists`.
- 理由: 否则 "换到一个全新方向" 死锁 (birth 被不变量 exit 2 指引去 switch, switch 又因 ref 不存在拒绝).
- 影响: switch 前置校验分两路; 测试各覆盖一条.
- 风险: 例外指向不存在 ref 期间容器侧无写面实体 (无可 push 对象), 无安全后果; 语义可能与用户预期不同.

## U-006 ssh key 与测试镜像

- 问题: swt 真实使用时容器 ssh 临时 key 落哪; 测试用什么镜像.
- 决策: key 对由 birth 生成, 私钥落 `<records-root>/runtime/<identity>/ssh/` (0600), terminate 时随 runtime 清除; 测试镜像复用 M03 最简镜像 `localhost/swt-m03:latest` (image/Containerfile, 测试首用即 build, 层缓存), birth 测试经 `--image` 直入跳过 match; match 集成路径另用 M07 式 scratch 伪镜像覆盖.
- 理由: key 是运行时产物, 与 runtime 状态同生死 (D012); M03 镜像契约 (sshd/agent 用户) 正是 swt 容器契约的最小满足.
- 影响: birth 不依赖 image-prep 真构建即可测主链; match DECIDE 路径独立测.
- 风险: 真镜像 (含 pi/skills) 与最简镜像差异要到 M10 演练才暴露, 知情接受 (M03 同判).

## U-007 测试文件归口与 git `!` 语法重验形态

- 问题: 测试落哪个文件; D008 "部署机重验 ! 语法" 在 swt 里什么形态.
- 决策: swt 测试统一落 `tests/test_swt_m12.py` (unittest.TestCase 风格, 沿用仓库先例); net-firewall 扩展 (D032) 用例增补进 `tests/test_swt_m04.py` 新 TestCase 类 (模块接口演进与其既有测试同屋). git `!` 重验 = birth 前置在 /tmp 一次性迷你仓行为级实测 hideRefs 否定例外, 失败 exit 4 (ENV); 每 birth 跑一次 (纯本地, 毫秒级), 不缓存.
- 理由: 仓库每里程碑一测试文件的惯例; 行为级重验按字面只能是实测.
- 影响: 测试发现命令 `uv run --with pytest pytest tests/test_swt_m12.py`.
- 风险: 低.

## U-008 net-firewall 扩展形态 (D032 落地)

- 问题: D032 给了两个方向 ("按容器源地址删规则" 或 "锁内全量重渲染"), 未定 interface.
- 决策: 两端都做最小形态: (1) 新子命令 `remove --container-ip <IP>` 按源地址删该容器规则行, 表内不再有任何 swt 规则时删整表, 幂等; (2) `apply` 增 `--merge` flag: 见异己 saddr 不拒 (无 --merge 时 APPLY-CONFLICT 原行为不变), 其规则行原文保留并入新表 — swt 在锁内编排调用. resume 共享表场景禁止 clear+apply (D032 明文).
- 理由: 单做 remove 解决不了 "第二个容器 birth 时 apply 被 APPLY-CONFLICT 拒"; 单做 merge 解决不了 "terminate 一个容器不能删整表".
- 影响: net-firewall 接口演进, 既有 M04 测试保持绿, 新用例增补.
- 风险: --merge 的规则行原文保留依赖 nft 文本解析, 行格式漂移会破坏; 由测试钉住.

## U-009 子代理选型

- 问题: 执行者/审核者模型与 thinking 档.
- 决策: 执行者 = `ai-work-openai/gpt-5.6-luna` thinking=high (coding 画像 1.000, stability 1.0 — 长 AFK 实现循环把 stability≥0.8 设为质量底线, glm-5.3-flash coding 总分更高但 stability 0.49 出局); 审核者 = `ai-work-zai/glm-5.3-flash` thinking=high (review 画像 1.019, 价格维 3.79 最便宜; 与执行者不同模型, 对抗对不同盲点).
- 理由: llm-select score.py 2026-09 渲染表, 过质量底线取最便宜.
- 影响: herdr 子会话启动参数.
- 风险: glm 稳定性低 → 审核者中断时 resume 或降级重派.

## U-010 daemon 粒度: 主仓级共享 (ISSUE-08 复核补钉)

- 问题: ISSUE-08 任务书写 "kill 该容器 daemon" 假设每容器专属 daemon; 实现与 birth 实际为主仓级单 daemon 复用 (TS-206 已钉).
- 决策: 确认主仓级共享 daemon 形态; terminate 仅在最后容器终结时收 daemon.
- 理由: 母体模型下 base-path=主仓, 多容器共享同一母体 (D009/D031) 时一个 daemon 即可服务全部; 按容器拆 daemon 会引入端口与发现复杂度, 无收益.
- 影响: D008 "每容器专属守护进程" 字面在该点被实践修订 (每主仓每个活动母体域一个).
- 风险: 低; 威胁模型不变 (daemon 无认证, 单授权域).

## U-011 决策收据 id 加微秒 (ISSUE-08 复核补钉)

- 问题: U-002 字面 id = `d-<yyyymmdd-HHMMSS>-<seq>`, 同秒多收据撞 id.
- 决策: id 时间戳改为 `d-<yyyymmdd-HHMMSS>-<微秒>`.
- 理由: 实测同秒冲突致收据互覆.
- 影响: 纯格式, 无语义变化.
- 风险: 无.

## U-012 ISSUE-08 两项偏差追认

- terminate 执行顺序实现为 nft remove → rm → (最后容器) 收 daemon, 与任务书字面序不同 — 先断网再删方向更安全, 接受.
- birth/status 为支持多容器 nft 断言夹带的改动 (own_netns 兄弟规则复制/runtime network.netns 字段/status stage 回读) 接受为必要使能改动.

## U-013 ISSUE-09 三项偏差追认

- switch 执行序实现为 nft remove 先于 podman stop (spec 字面为停容器先行) — 先断网方向更安全, 接受 (同 U-012 逻辑).
- 目标校验 (ref 存在性与工作区干净) 提为 switch 前置, 脏/异常 exit 2 (未动资源); ISSUE-09 步骤 3 "停容器后校验, 脏 exit 3" 与 U-005/D027 自相矛盾 (exit 2 要求未动资源), 实现取前置 exit 2 一侧, 自洽.
- 新增前置: 目标 ref 存在但无对应母体 worktree → exit 2 (半状态母体不接收授权域换绑).
