# AFK 自主决定记录 (present-web-server 实现)

格式: 问题/决策/理由/影响/风险. 全部待用户确认.

## U-001 自建 EXECUTION.md

- 问题: tdd-as-orchestra 要求权威输入含 EXECUTION.md (任务拆分为 ISSUE), 仓库中缺失; 用户 AFK 无法补充.
- 决策: 总指挥依据 TECHNICAL.md 的 6 个 Seam 与 TC-001..TC-028 权威清单机械拆分 ISSUE-01..ISSUE-09, 写入 `docs/changes/present-web-server/EXECUTION.md`.
- 理由: 拆分不产生新需求, 只对已确认决策做执行分组; 红线不含此项.
- 影响: 执行顺序按 Seam 依赖排列 (CLI 骨架 → 生命周期 → 内容 → 控制面 → TTL → SKILL.md).
- 风险: 分组粒度与用户意图有出入; 缓解: 每组可独立提交, 逐组可审查.

## U-002 测试执行方式

- 问题: present 项目 venv 无 pytest, 测试如何运行 TECHNICAL.md 未写死.
- 决策: 从仓库根执行 `uv run python -m pytest general/present/tests` (仓库根环境有 pytest, pytest.ini 已含该 testpath, 基线 64 passed).
- 理由: F003 已确认 pytest.ini 零配置接入, 仓库根是 pytest 的自然入口.
- 影响: 子代理提示词统一此命令.
- 风险: 无.

## U-003 执行者调度粒度

- 问题: tdd-as-orchestra 字面上每测试切片起一个全新执行者, 28 条用例成本过高.
- 决策: 每个 ISSUE 一个执行者 (串行), 执行者内部严格遵守逐 TC 先红后绿, 一次一个切片; 每个 ISSUE 完成后由审核者 review, 只采纳明确发现项再交还修复.
- 理由: 保持小任务/证据清楚/上下文干净的精神不变 — 单 ISSUE 内用例同构, 执行者上下文不超载; review 仍独立.
- 影响: 子代理调用次数从 ~28+ 降为 ~9+9.
- 风险: 单执行者上下文在长 ISSUE 中膨胀; 缓解: ISSUE 最大 6 条用例, 超大则拆.

## U-004 测试命令适配本机环境

- 问题: 本会话机器与上一会话不同 (/var/mnt/DATA/Workspace/skills 不存在, 仓库位于 /home/bolo/Workspace/skills; 仓库根无 pyproject, 系统 python 无 pytest), 原命令 `uv run python -m pytest` 报 No module named pytest.
- 决策: 测试命令改为 `~/.local/bin/uv run --with pytest python -m pytest general/present/tests -q` (uv 临时环境注入 pytest, 不改仓库文件).
- 理由: 保持 uv 管理约定 (~/docs/python-uv.md), 不新增根 pyproject/uv.lock (超出 D027 允许范围), 零仓库侵入.
- 影响: 所有子代理提示词统一此命令; web_server 相关用例为验收面.
- 风险: --with pytest 需 PyPI 缓存/网络; 已验证本机可用.

## U-005 browser_session 5 例失败认定为环境差异

- 问题: 全量测试中 test_browser_session.py 5 例失败, 根因是本机缺 playwright (旧机器已装), run_status/run_open 返回 access_web_unavailable.
- 决策: 认定为既有环境差异, 非本变更回归; 本变更基线与验收以 test_web_server*.py + test_skill_contract.py 为准; 不安装 playwright 及其浏览器二进制 (大体积外部下载, 触 AFK 红线 "需要外部资源").
- 理由: 失败全部位于 browser_session (本变更禁改文件), 与 web_server 零交集; web_server 子集 10 passed 全绿.
- 影响: 全量测试稳定呈 "69 passed, 5 failed (browser_session), 1 skipped"; 最终汇总列为环境阻塞项, 是否补装 playwright 由用户定.
- 风险: 若用户期望本机全绿, 需另行补环境; 不影响 present-web-server 交付判定.

## U-006 子代理模型重新选型

- 问题: handoff 指定的执行者 kimi-for-coding 与审核者 k3-256k 在本机子代理选型表中不存在 (旧机器配置).
- 决策: 执行者 = ai-work-zai/glm-5.3 (thinking xhigh); 审核者 = ai-work-zai/glm-5.3-flash (thinking high). 二者为不同模型, 满足对抗对不同模型要求.
- 理由: 执行者做真实子进程/并发/契约细节的 TDD 实现, 取 coding 基线档防返工; 审核者是大量读代码找缺陷, flash 的 review 画像分 (1.758) 高且价格 1/10, 弱点 (谨慎度) 由 thinking high 缓解.
- 影响: ISSUE-03..09 全部子代理调用沿用此配对; 旧机器的 opencode-go 额度耗尽结论不适用本机.
- 风险: 同家族模型对抗性弱于跨家族; 若审核发现率异常低, 中途换 ai-work-deepseek/deepseek-v4-flash-vision-exp 做交叉审核.

## U-007 add-dir 端点回写 server.json roots

- 问题: 审核发现 add-dir 只改服务进程内存挂载表, server.json roots 不更新 — 与 D005 "按原挂载清单重建" 矛盾, 且当前 run_status 报告的 roots 在 add-dir 后即失真 (规格自相矛盾, 非需求变更).
- 决策: 采纳审核建议 S1: /__control__/add-dir 端点在持锁 append 后原子回写 server.json 的 roots (0600), 数据模型 "写入方" 相应扩展为 "子进程启动时与挂载变更时; 重建时更新 port/pid/started_at".
- 理由: 消除规格内部矛盾, 使 status 与重建的 roots 权威来源一致; 改动面小 (端点内一次原子写), 不新增需求.
- 影响: ISSUE-03 修复轮实现; ISSUE-05 重建天然拿到完整挂载清单; TC-013 增补断言 (add-dir 后 server.json roots 含新目录).
- 风险: 服务进程写 server.json 与 CLI 侧读写的并发 — 由 roots_lock 串行化端点写, flock 串行化 CLI 入口, 交叉窗口为 CLI 读时端点写, 原子写保证读者见完整旧版或新版.

## U-008 挂载目录不可读时的 listing 语义

- 问题: ISSUE-06 并集 listing 重构后, 全部/部分挂载目录 listdir OSError 时返回 200 空/子集 listing, 而 ISSUE-02 单目录实现在同场景回 404; 规格静默区, 属未入账契约变化 (审核建议 S1).
- 决策: 顶层 listing = 可读挂载目录条目的并集 (部分不可读 → 子集, 200); 全部挂载目录不可读 → 404 (恢复单目录时代语义, 不泄露存在性). 子目录 listing 单点不可读 → 404 (维持原语义不变).
- 理由: 并集语义下部分失败降级为子集自然且不泄露; 全失败时 404 与 "不可访问不泄露存在性" 的安全基线一致, 也兼容重构前行为.
- 影响: ISSUE-06 修复轮实现; TC 增补两条断言 (全部 chmod 000 → 404; 部分不可读 → 子集 200).
- 风险: chmod 000 依赖测试运行者即属主 — 同 uid 下 listdir 仍可能成功 (root 或属主绕过). 测试须以非属主方式构造或声明 skip 条件; 无法确定性构造时以变异补红申报.

## U-009 控制面来源规则: loopback 或源 IP == bind 地址

- 问题: ISSUE-07 守卫按 "源非 loopback 一律拒" 一刀切, 导致 `--bind <具体 IP>` (AC-001 契约级输入) 时 CLI 自身就绪 ping/add-dir/探活 (源地址=本机 LAN IP) 被拒, start 端到端超时失败 — D020 字面与 AC-001 冲突 (审核阻断 B1).
- 决策: 守卫放行条件 = loopback 来源 或 client IP == 服务 bind 的地址; 其余拒绝 (403, 响应后关连接). bind 0.0.0.0/127.0.0.1 场景行为与原守卫完全一致 (TC-022 语义不变).
- 理由: D020 意图是控制面不对网段暴露; 远端无法以本机 bind IP 完成 TCP 握手, 放行 "源==bind" 不扩大暴露面; 保留具体 IP bind 可用性.
- 影响: ISSUE-07 修复轮实现 + 增补用例 (bind 具体 IP 的 start/status/add-dir 端到端).
- 风险: 多宿主机上本机进程经非 bind 接口自连仍被拒 — CLI 不会走此路径 (_ping_host 恒连 bind 地址), 无实际影响.

## U-010 /__control__/* 保留命名空间: loopback 下不回落静态

- 问题: loopback GET /__control__/<挂载内真实文件> 当前回落静态查找返回 200, 与 D020 "`/__control__/*` 为保留命名空间...同路径文件被静默遮蔽" 的字面冲突 (预存在行为, 审核提示 T3 请裁定).
- 决策: /__control__/* 全命名空间为控制面保留: loopback 下未知控制路径一律 404, 不回落静态查找; 非 loopback 一律 403 (U-009 规则下).
- 理由: "保留命名空间+静默遮蔽" 的字面兑现; 挂载目录内恰有 __control__/ 前缀文件的场景极罕见, 404 语义 (不存在) 符合不泄露原则.
- 影响: ISSUE-07 修复轮实现 + 用例 (挂载内放 __control__/shadow.txt, loopback GET → 404, LAN GET → 403).
- 风险: 极端场景用户真想经静态面提供 __control__/ 前缀文件将不可达 — 与决策取舍一致, 接受.
