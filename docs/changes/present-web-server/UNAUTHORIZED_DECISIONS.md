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
