# 交接: present-web-server 实现 (ISSUE-01/02 已完成, 03-09 待执行)

日期: 2026-08-30
工作区: /var/mnt/DATA/Workspace/skills (skills 仓库, 只准改本仓库内容; 同步 pi agent 用 `uv run python sync-to-pi.py`, 是否执行由用户定)
模式: tdd-as-orchestra AFK — 总指挥只调度, 执行者串行 (kimi-for-coding), 审核者并行 (k3-256k, opencode-go 系额度已耗尽勿用)

## 任务本体

按 EXECUTION.md 逐 ISSUE 实现 present-web-server: `general/present/scripts/web_server.py` (start/status/stop/add-dir 常驻 web 服务) + SKILL.md 远程段 + TC-001..TC-028 测试. 每 ISSUE: 执行者逐 TC 先红后绿 → 审核者 review → 采纳明确发现项交还修复 → 勾选 EXECUTION.md → 本地提交 `feat: ISSUE-<NN>: <描述>`.

## 流程现状

- 设计/固化/校验: 全部完成 (见前一份 handoff 2026-08-30-present-web-server-impl.md 与 docs/changes/present-web-server/).
- ISSUE-01 ✅ CLI 骨架 (TC-001..004): commit 04d359d + 8847461 (审核建议修复). 审核无阻断.
- ISSUE-02 ✅ start/status 冷启动 (TC-005/007/008/009): commit f0159e9 + 63efbb8 (审核修复: S1 `_send_error` 未定义致 404 断连 [阻断, 已修], S2 复用路径改明确失败桩 [ISSUE-04 才实现真正复用], S3 port_in_use 误归类→子进程写 startup_error 文件区分, S4 server.json 原子写, S6 SIGKILL 兜底, T5 测试清理提前登记).
- 文档提交 c57e37a: 固化产物 + EXECUTION.md + UNAUTHORIZED_DECISIONS.md 入库.
- 当前测试: 74 passed, 1 skipped (`cd /var/mnt/DATA/Workspace/skills && uv run python -m pytest general/present/tests -q`).
- 进度: ISSUE 2/9, TC 8/28. web_server.py 约 700 行, 已有: CLI 骨架/运行时状态簇 (server.json/flock/权限)/后台化簇 (__serve__ re-exec/ping 就绪)/HTTP 最小闭环 (ping 端点/静态文件/containment)/host 探测 D011 全优先级.

## 关键约束与纪律

- 代码边界 D027: 只许 web_server.py + tests/test_web_server*.py + SKILL.md + test_skill_contract.py; 禁 browser_session.py/access-web/第三方依赖.
- 测试命令从仓库根: `uv run python -m pytest general/present/tests -q` (present 自身 venv 无 pytest).
- 执行者提示词模板沿用本会话 ISSUE-01/02 的结构 (现场事实/权威输入/范围内外/TDD 纪律/停止条件/输出契约/commit hash/pgrep 无残留证据).
- 审核者只报明确发现项, 总指挥只采纳阻断+建议级, 提示级默认不采纳 (先例: ISSUE-02 提示级 S5/S7/T1-T4 未采纳).
- AFK 自主决定立即落盘 UNAUTHORIZED_DECISIONS.md (已有 U-001 自建 EXECUTION/U-002 测试命令/U-003 调度粒度).
- 用户指示: 本次交接后停止; 下一会话继续 ISSUE-03 起.

## 已知伏笔 (后续 ISSUE 必须处理)

- run_start 复用路径当前是明确失败桩 ("复用挂载尚未实现 (ISSUE-04)"), ISSUE-04 须替换为真复用 (D006: add-dir 挂载 + 端口差异 warning + bind_conflict).
- `/__control__/*` loopback-only 限制未实现 (ISSUE-07, 当前 ping 指纹对 LAN 可见, 属排期内).
- status 遇死实例目前只报 alive=false, 重建逻辑在 ISSUE-05.
- 内容面只有基础 containment; 并集/listing/symlink/`../` 用例在 ISSUE-06.
- `import signal` 暂未用 (ISSUE-03 stop 用); `_Handler` 类属性当实例状态 (单实例下成立, 审核 T2 提示级未采纳).
- TC-022/023 无非 loopback 接口时 skip 不 fail; TC-029 人工不自动化.
- ISSUE-09 依赖 01-08 全部完成 (契约断言须对齐已实现行为).

## 风险

- 执行者曾越权提前提交 (ISSUE-01/02 均在 review 前 commit) — 提示词已要求完成后提交, 但顺序靠自觉; 后果可接受 (修复走后续 commit), 下一会话可在提示词中明示 "review 前不提交".
- 审核者模型选择: opencode-go 系 (glm-5.3 等) 5 小时额度已耗尽 (2026-08-30), 用 kimi-coding/k3-256k 做审核, 与执行者 kimi-for-coding 构成对抗对.
- 子代理上下文: ISSUE-06 有 6 条用例, 若执行者上下文超载可按 EXECUTION.md U-003 授权拆半.

## 必读推荐

1. `docs/changes/present-web-server/EXECUTION.md` — 必读. ISSUE-03..09 范围/用例/依赖/勾选状态的权威清单, 下一会话的直接工作单.
2. `docs/changes/present-web-server/TECHNICAL.md` — 必读. 接口契约与 TC 权威描述; DECISIONS.md 冲突时权威.
3. `docs/changes/present-web-server/UNAUTHORIZED_DECISIONS.md` — 必读. AFK 自主决定 3 条, 待用户确认; 下一会话新决定续写此文件.
4. `general/present/scripts/web_server.py` (约 700 行) — 必读. 现状代码, 后续 ISSUE 在其上生长; 重点看 S3 修复引入的 startup_error 文件机制与复用失败桩位置.
5. `general/present/tests/test_web_server_lifecycle.py` — 必读. 测试基类模式 (PI_PRESENT_WEB_RUNTIME_DIR 隔离/_server_pids 清理/_free_port), 后续测试文件复用.
6. `docs/changes/present-web-server/DECISIONS.md` — 必读. D001-D028 决策账本.
7. `~/.agents/skills/tdd-as-orchestra/SKILL.md` 与 `~/.agents/skills/tdd/SKILL.md` — 必读. 编排与 red-green 纪律.

## 路线图

1. ✅ 需求提出 + deliberate 盘问 (Q1-Q40) + 固化 (DECISIONS/PRODUCT/TECHNICAL/ADR 0005/0006/领域语言) + 子代理校验 P1-P6 修复.
2. ✅ 上一份 handoff → 本会话接收上下文.
3. ✅ AFK 补齐 EXECUTION.md (U-001), 基线确认.
4. ✅ ISSUE-01 CLI 骨架 (TC-001..004) + 审核 + 修复.
5. ✅ ISSUE-02 start/status 冷启动 (TC-005/007/008/009) + 审核 (1 阻断) + 修复.
6. ⏸️ **本会话在此停止** (用户指示: 下一次 git 提交完成后停下交接, commit c57e37a).
7. ⬜ 下一会话: ISSUE-03 stop/add-dir (TC-012..015/026) → ISSUE-04 复用/冲突/host (TC-006/025/027) → ISSUE-05 重建 (TC-010/011) → ISSUE-06 内容 (TC-016..021) → ISSUE-07 控制面 (TC-022/023) → ISSUE-08 TTL (TC-028) → ISSUE-09 SKILL.md 远程段 (TC-024).
8. ⬜ 全绿后: 用户确认 UNAUTHORIZED_DECISIONS.md 各条; 是否 `sync-to-pi.py` 同步由用户定.

进度评估: ISSUE 2/9, TC 8/28, 脚本骨架与最难的后台化/运行时状态已落地, 剩余为功能叠加, 无已知设计风险.
