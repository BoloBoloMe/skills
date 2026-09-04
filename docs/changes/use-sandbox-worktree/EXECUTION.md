# use-sandbox-worktree 瘦闭环 (MILESTONE-03) Execution Spec

## 权威输入

- Product Spec: `docs/changes/use-sandbox-worktree/PRODUCT.md`
- Technical Spec: `docs/changes/use-sandbox-worktree/TECHNICAL.md`
- Decisions: `docs/changes/use-sandbox-worktree/DECISIONS.md`

## 全局允许范围

- 新建 `workflow/use-sandbox-worktree/scripts/e2e-smoke.py`, `workflow/use-sandbox-worktree/image/Containerfile`, `tests/test_swt_m03.py`
- 只读调用 `workflow/use-worktree/scripts/slug.py` (契约见 TECHNICAL.md 架构节)
- /tmp 下的测试夹具与运行时产物
- 产物文件 `docs/changes/use-sandbox-worktree/milestone-03-e2e-run.md`

## 全局禁止范围

- 禁止修改其他 skills 的任何文件
- 禁止触碰用户真实仓库; 主仓 config 只写 /tmp 夹具仓
- 禁止新增 git hooks (BR-005/NB-001)
- 禁止实现 nft 网络控制/镜像推导/展示链/登录墙/五场景脚本稳定接口 (非目标)
- 禁止容器内引入真远端地址或凭据 (BR-001)
- 禁止对无 `.git/swt-m03-fixture` 夹具标识的仓库执行 birth (TC-008)
- cleanup 默认阻塞脏容器 (D012 非交互形态); 显式 `--i-am-sure` 放行时须登记脏放行字段

## 完成定义

- `e2e-smoke.py` 的 birth → smoke → cleanup → birth → smoke 全链退出码 0
- TC-001 至 TC-007 全部通过: `uv run pytest tests/test_swt_m03.py`
- 产物文件含逐阶段日志, 结果事实, 全通网络与 daemon 监听中间态声明, checklist (AC-006)
- NB-001/NB-002/NB-003 审计断言通过, NB-004 有演练记录

## 测试策略

- 全部用例端到端层级, 接缝 = 编排器 CLI 退出码/stderr + git/podman CLI 输出; 无单元层
- mock/fake 仅限 /tmp 文件系统夹具仓 (系统边界)
- 测试统一落 `tests/test_swt_m03.py` (unittest.TestCase 风格); 环境依赖缺失时失败并打印缺失项, 不静默 skip

## 任务图

- ISSUE-01: `issues/ISSUE-01-host-loop-tracer.md`; 覆盖: TC-001, TC-002, TC-008, NB-001, NB-003, TG-001, TG-002; 依赖: 无.
- ISSUE-02: `issues/ISSUE-02-container-client-loop.md`; 覆盖: AC-001 至 AC-006, TC-003, TC-004, TC-005, TC-006, TC-007, NB-002, NB-004, TG-003, TG-004, NFR-001, NFR-002; 依赖: ISSUE-01.

## 覆盖矩阵

- AC-001 -> ISSUE-02 -> TC-001/TC-002/TC-003 -> `e2e-smoke.py birth` 断言与容器读面断言. (config/daemon 部分 ISSUE-01 预建, 容器段补全); TC-008 -> ISSUE-01 -> 夹具标识断言.
- AC-002 -> ISSUE-02 -> TC-004/TC-006 -> `e2e-smoke.py smoke` 容器内回流/脏树断言.
- AC-003 -> ISSUE-02 -> TC-005 -> 容器内拒绝矩阵断言.
- AC-004 -> ISSUE-02 -> TC-003 -> 容器内 remote/ls-remote 断言.
- AC-005 -> ISSUE-02 -> TC-007 -> cleanup/再 birth 断言.
- AC-006 -> ISSUE-02 -> 产物文件断言 + 人工核验 checklist.
- TG-001 -> ISSUE-01 (编排器骨架); TG-002 -> ISSUE-01 (config/daemon/写面, host 客户端预验); TG-003 -> ISSUE-02; TG-004 -> ISSUE-02.
- NFR-001/NFR-002 -> ISSUE-02 -> 阶段日志断言/TC-007.
- NB-001 -> ISSUE-01 -> hooks 目录审计断言; NB-002 -> ISSUE-02 -> Containerfile 内容断言; NB-003 -> ISSUE-01 -> daemon 命令行审计断言; NB-004 -> ISSUE-02 -> `pi --help` 演练记录.

## 全局风险和停止条件

- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止 (如: hideRefs 行为与 F007 不符, 须回盘问).
- 需要扩大允许范围 (触碰真实仓库/其他 skills) 时停止.
- daemon 监听地址/端口发现不可行时按 TECHNICAL.md 兜底顺序退化并记 checklist, 不停止, 不改编排接口.
- pi CLI 容器内不可运行时先修镜像; 需引入超出 git/pi/sshd 底座的新依赖类别时停止上报.

## 拆分说明 (垂直切片)

两片皆为可独立演示的窄完整路径: ISSUE-01 打通 "夹具 → 母体 → config → daemon → host 客户端 clone/push/落地/拒绝矩阵 → cleanup → 重跑" 的无容器真闭环; ISSUE-02 把容器接入为真实客户端, 补齐全部 AC. 线性阻塞, 无共享分支/integration 特例.
