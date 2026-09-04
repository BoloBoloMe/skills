# ISSUE-02 容器接入: 容器为真实客户端的全验收闭环

## 父级

- `../EXECUTION.md`

## 执行(Execution)

- [ ] 已实现

## 要构建什么

把容器接入为真实客户端, 补齐全部 AC: 最简镜像 `workflow/use-sandbox-worktree/image/Containerfile` (契约见 TECHNICAL.md 架构节: node:24-bookworm-slim 基座 + git/openssh-server + `npm i -g @earendil-works/pi-coding-agent` + agent 用户 + 夹具临时公钥注入) → birth 容器段 (镜像检查/build, `podman create --name swt-<dir值> --label sandbox-worktree.{name,repo,branch} -p 22`, start, `podman port` 发现, BatchMode 连通断言) → 容器内 `git clone -b <dir值> git://<daemon地址>:<port>/<reponame>` → 容器内全部验收断言: 读面 (TC-003), 回流落地 (TC-004), 拒绝矩阵 (TC-005, 容器内执行), 脏树拒绝 (TC-006, 断言后还原) → cleanup 含容器 (D012 非交互形态: ssh 查容器 git 状态 — 未 commit 改动数/未 push commit 数; 脏则中止不删, 退出码 3; `--i-am-sure` 显式放行时把状态值/夹具路径/时间/依据记入产物与 checklist 的**脏放行登记**字段; 负向用例产生的未 push 本地提交由 smoke 断言后容器内 `git reset --hard` 复原, 保证干净 cleanup 可走通) → 全链重跑 (TC-007) → 产物文件 `../milestone-03-e2e-run.md` (逐阶段日志/结果事实/中间态声明含 daemon 监听地址实际值/checklist) → `pi --help` 演练记录 (NB-004, 待验证事实 1). 适合 AFK 的理由见末节.

## 覆盖依据

- Product: `../PRODUCT.md`, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006
- Technical: `../TECHNICAL.md`, TG-003, TG-004, NFR-001, NFR-002

## 相关决策

- `../DECISIONS.md`: D007, D008, D009; F001/F004/F006/F007 为预期值来源
- 边界声明: `../TECHNICAL.md` 关键流程节 (cleanup 实现 D012 非交互形态: 脏则阻塞, `--i-am-sure` 放行并登记)

## 允许范围

- `workflow/use-sandbox-worktree/scripts/e2e-smoke.py` (ISSUE-01 骨架上续写), `workflow/use-sandbox-worktree/image/Containerfile`, `tests/test_swt_m03.py` (同文件续写)
- /tmp 夹具目录 (含临时 ssh key)
- 产物文件 `../milestone-03-e2e-run.md`

## 禁止范围

- 容器内禁止出现真远端地址或凭据; 不复用用户既有 ssh key; 不加 VNC/登录墙组件; 不做 nft; 不删母体; cleanup 遇脏容器不得无条件删除 (须阻塞或 --i-am-sure 登记放行)

## 代码定位提示

- 容器/label/端口/克隆契约: `../TECHNICAL.md` 架构与组件/关键流程节
- 容器到达 daemon 地址与监听地址配对: `../TECHNICAL.md` 安全策略节与待验证事实 (兜底顺序已定)
- pi CLI 分发形态参考: 仓库 `pi/` 目录与 `sync-to-pi.py`; rootless podman 用法见用户 `~/docs/podman.md`
- checklist 内容来源: `../TECHNICAL.md` 依赖与风险节 + `../roadmap/MILESTONE-03.md` 编排器交付边界节

## TDD 切片

- TS-001:
  接缝: 编排器 CLI + 容器内 git 命令输出 (ssh BatchMode 执行).
  测试用例: TC-003.
  先写的失败测试: `tests/test_swt_m03.py::TestContainerLoop::test_container_clone_checks_out_mother_branch` — 容器内检出分支=母体分支, remote 仅 daemon URL, ls-remote 仅母体分支; 失败原因: 容器段未实现.
  最小绿色实现范围: Containerfile + 容器创建/label/端口/ssh/克隆/读面断言.
  不得测试: 内部实现; 不断言 HEAD 广告存在 (F007 已知泄露, 非目标).
  覆盖: TC-003, AC-001, AC-004, TG-003.
- TS-002:
  接缝: 母体目录文件内容 + 容器内 push 输出.
  测试用例: TC-004, TC-006.
  先写的失败测试: `test_container_push_lands_and_dirty_tree_rejected` — 容器内 ff push 落地母体文件; 母体脏树时容器 push 被拒, 断言后还原干净.
  最小绿色实现范围: 容器内 commit/push 编排 + 落地断言 + 脏树制造/断言/还原.
  不得测试: 不断言报错具体字符串 (只匹配 `[remote rejected]`).
  覆盖: TC-004, TC-006, AC-002.
- TS-003:
  接缝: 容器内 push 拒绝输出.
  测试用例: TC-005.
  先写的失败测试: `test_container_oob_push_rejected` — 容器内四类越界 push 全拒.
  最小绿色实现范围: 容器内拒绝矩阵断言.
  不得测试: host 侧重验 (ISSUE-01 已做, 此处只走容器路径).
  覆盖: TC-005, AC-003.
- TS-004:
  接缝: 编排器 CLI + `podman ps -a`/`git worktree list`.
  测试用例: TC-007.
  先写的失败测试: `test_full_chain_cleanup_and_rerun` — cleanup 后容器/daemon 灭/母体留存/JSON 删, 再 birth+smoke 全过; 另: 脏容器 cleanup 默认中止 (退出码 3) 且不删, 传 --i-am-sure 才放行并登记.
  最小绿色实现范围: cleanup 容器段 + D012 非交互形态 (脏则阻塞 / --i-am-sure 登记放行) + 重跑.
  不得测试: 内部实现.
  覆盖: TC-007, AC-005, TG-004, NFR-002.
- TS-005:
  接缝: Containerfile 审计 + 容器内 `pi --help` + 产物文件内容.
  测试用例: NB-002/NB-004/AC-006.
  先写的失败测试: `test_image_minimal_pi_runs_report_complete` — Containerfile 无禁用组件; 容器内 pi --help 退出码 0 并记录; 产物文件含阶段日志/中间态声明/checklist 三节.
  最小绿色实现范围: Containerfile + pi 断言 + 产物生成.
  不得测试: 不校验日志文案措辞, 只校验章节与关键事实字段.
  覆盖: NB-002, NB-004, AC-006, NFR-001.

## 验证入口

`uv run pytest tests/test_swt_m03.py` 全部用例过 (含 ISSUE-01 回归); 全链手动: `birth --name demo` (从 stdout 取夹具路径 `<R>`) → `smoke --repo <R> --name demo` → `cleanup --repo <R> --name demo` → 再 `birth --repo <R> --name demo` (复用母体路径) + `smoke --repo <R> --name demo` 退出码全 0; 脏阻塞路径: 手工污染容器后 `cleanup --repo <R> --name demo` 退出码 3 且零删除, `cleanup --repo <R> --name demo --i-am-sure` 放行且产物含脏放行登记; `docs/changes/use-sandbox-worktree/milestone-03-e2e-run.md` 存在且三节齐全 (人工核验 checklist 可读).

## 风险提示

- sshd 用户/密钥配置与容器到 daemon 地址是首次实锤点, 按 TECHNICAL.md 兜底顺序退化并记产物, 不改编排接口.
- 镜像 build 需网络拉基础镜像, 失败原样透报.
- pi CLI 不可运行时先补镜像依赖; 超出 git/pi/sshd 底座的新依赖类别触发停止 (EXECUTION.md 全局停止条件).
- 脏树断言后母体必须还原, 否则 TC-007 假失败.

## 停止条件

需要改变任一 Spec/决策/issue 边界或扩大范围时停止; pi 依赖超界时停止上报.

## 适合 AFK 的原因

全部验收预期值有实测事实来源 (F001/F004/F006/F007); Containerfile 基座/依赖/用户/key 注入契约已在 TECHNICAL.md 架构节固化; 开放点 (容器到 daemon 地址/sshd 配置细节) 有已钉死的兜底顺序与记录路径, 属环境实锤而非待决取舍; 若兜底也失败, 停止条件已定义, 不会静默改决策.

## 验收标准

- [ ] 容器运行, label 三键齐全, ssh 免密可入, `podman port` 可发现 22 映射
- [ ] 容器内克隆检出母体分支, remote 仅 daemon URL, ls-remote 仅母体分支
- [ ] 容器内 ff push 落地母体目录; 脏树时拒; 四类越界 push 全拒
- [ ] cleanup 后容器/daemon 灭, 母体留存, 全链重跑全过
- [ ] 产物文件三节齐全, 中间态 (全通网络 + daemon 监听地址实际值) 显式声明, checklist 含脏放行登记字段
- [ ] `pi --help` 可运行有记录; Containerfile 无禁用组件
- [ ] ISSUE-01 全部用例回归通过

## 被阻塞于

- ISSUE-01
