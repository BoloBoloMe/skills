# ISSUE-01 无容器 tracer: 母体拓扑 + 守护进程 + host 端回流闭环

## 父级

- `../EXECUTION.md`

## 执行(Execution)

- [x] 已实现

## 要构建什么

端到端可演示的无容器瘦闭环 (tracer bullet): 编排器 `workflow/use-sandbox-worktree/scripts/e2e-smoke.py` 骨架 (birth/smoke/cleanup 子命令, 阶段日志, `ASSERT-FAIL <名>`/`NOT-A-FIXTURE` + 退出码约定, 运行时 JSON 生命周期) + 完整 host 侧链路: `--repo` 夹具标识校验 (无标识退出码 2 零写操作) → 夹具主仓自建 (`srv/<reponame>/` 布局 + `.git/swt-m03-fixture` 标识) → 重入状态机 → slug 契约建/复用母体 (`dir=` 值 = 目录名 = 母体分支名) → `git-daemon-export-ok` → D008 config (写入语义: 标量键缺则写/符则跳/不符则中止; 多值 hideRefs 键空则按序 --add 三值/集合恰等则跳/否则中止不改写) → 逐键校验 (含 srv 根枚举仅一仓) → daemon 拉起 (监听地址探测顺序: pasta 网关接口地址优先, 0.0.0.0 兜底并记 checklist; 端口 = socket bind 0 预选空闲端口, 拉起后探测可连, 失败重选至多 3 次) → **host 侧客户端**经 daemon URL `clone -b <dir值>` → commit/push → 断言推送落地母体目录 → 拒绝矩阵 (新分支/tag/non-ff/删除全拒) → cleanup (停 daemon, 母体/ref 留存, 删 JSON) → 再 birth 走复用母体路径. 审计断言: hooks 零新增 (NB-001), daemon 命令行无 `--export-all` (NB-003). 适合 AFK: config 模板, 写入语义, 重入状态机, slug 契约, 拒绝矩阵预期值全部有权威来源.

## 覆盖依据

- Product: `../PRODUCT.md`, AC-001 (config/daemon 分支; 完整 AC-001 由 ISSUE-02 收口)
- Technical: `../TECHNICAL.md`, TG-001, TG-002

## 相关决策

- `../DECISIONS.md`: D007, D008, D010 (母体复用状态机); F007 为拒绝矩阵预期值来源
- `docs/adr/0008-mother-worktree-direct-receive-no-hooks.md`

## 允许范围

- 新建 `workflow/use-sandbox-worktree/scripts/e2e-smoke.py`, `tests/test_swt_m03.py`
- /tmp 夹具目录

## 禁止范围

- 不建容器/镜像 (ISSUE-02); 不改主仓 hooks; 不开 --export-all; 不触碰真实仓库; 不改其他 skills

## 代码定位提示

- 全部契约: `../TECHNICAL.md` (接口契约/数据模型与状态/关键流程/安全策略节)
- slug 契约: `uv run workflow/use-worktree/scripts/slug.py <project> main <分支名原文>`, 解析 stdout 的 `dir=` 行 (三参数形式无 `slug=` 行, 有 project=/source_slug=/target_slug=/dir=)
- 拒绝矩阵预期: `../milestone-02-worktree-topology-findings.md` §2.5
- 测试惯例: `tests/test_sync_to_pi.py` (unittest.TestCase); pytest.ini testpaths 已含 tests/

## TDD 切片

- TS-001:
  接缝: 编排器 CLI 退出码 + `git config --get-all` + 文件系统 + 进程表.
  测试用例: TC-001.
  先写的失败测试: `tests/test_swt_m03.py::TestHostLoop::test_birth_writes_mother_config_daemon` — 断言 birth 后母体/config/export-ok/daemon 全就位; 失败原因: 脚本尚不存在.
  最小绿色实现范围: 夹具自建 + 重入状态机 + 母体 + export-ok + config 写入与校验 + daemon 生命周期 + 运行时 JSON.
  不得测试: e2e-smoke.py 内部函数.
  覆盖: TC-001, TG-001, TG-002.
- TS-002:
  接缝: 编排器 CLI 退出码与 stderr.
  测试用例: TC-002.
  先写的失败测试: `test_birth_aborts_on_config_mismatch` — 预写错误键, birth 退出码 1, stderr 含 `ASSERT-FAIL config`, 错误键未被覆盖, 无 daemon.
  最小绿色实现范围: config 写入语义的 "不符即中止" 分支.
  不得测试: 内部实现.
  覆盖: TC-002.
- TS-003:
  接缝: host 客户端经 daemon URL 的 clone/push 输出 + 母体目录文件内容.
  测试用例: TG-002 host 端预验 (TC-004/TC-005 的容器内正式版归 ISSUE-02, 本切片不独占其覆盖).
  先写的失败测试: `test_host_client_push_lands_and_oob_rejected` — host 客户端 push 落地母体文件变化; 四类越界 push 全拒; 失败原因: smoke 断言未实现.
  最小绿色实现范围: smoke 的 host 客户端断言 (clone -b/push 落地/拒绝矩阵).
  不得测试: 不断言拒绝信息具体字符串 (只匹配 `[remote rejected]` 前缀).
  覆盖: TG-002.
- TS-004:
  接缝: 文件系统与进程审计.
  测试用例: NB-001/NB-003.
  先写的失败测试: `test_no_hooks_no_export_all` — 主仓 hooks 目录无新增, daemon 命令行无 --export-all.
  最小绿色实现范围: 两条审计断言.
  不得测试: 内部实现.
  覆盖: NB-001, NB-003.
- TS-006:
  接缝: 编排器 CLI 退出码与 stderr + 目标目录文件系统.
  测试用例: TC-008.
  先写的失败测试: `test_birth_refuses_non_fixture_repo` — 无标识目录作 --repo, 退出码 2, stderr 首行 NOT-A-FIXTURE, 目标零写操作; 失败原因: 标识校验未实现.
  最小绿色实现范围: 夹具标识校验 + 拒绝路径.
  不得测试: 内部实现.
  覆盖: TC-008.
- TS-005:
  接缝: 编排器 CLI 重入.
  测试用例: TG-004 的 host 端预验 (TC-007 全链版归 ISSUE-02).
  先写的失败测试: `test_cleanup_and_rebirth_reuses_mother` — cleanup 后 daemon 灭/JSON 删/母体留存, 再 birth 走复用路径退出码 0.
  最小绿色实现范围: cleanup 幂等 + 复用母体路径.
  不得测试: 内部实现.
  覆盖: TG-004 (部分).

## 验证入口

`uv run pytest tests/test_swt_m03.py` 本切片用例全过; 手动: `uv run workflow/use-sandbox-worktree/scripts/e2e-smoke.py birth --name demo` (缺省自建夹具, 从 stdout 取路径 `<R>`) 退出码 0, `smoke --repo <R> --name demo` 断言全过, `cleanup --repo <R> --name demo` 退出码 0, 再 `birth --repo <R> --name demo` 走复用母体路径退出码 0.

## 风险提示

- daemon 监听地址与容器可达配对是待实锤项: 按 TECHNICAL.md 兜底顺序退化并记 checklist, 不改接口.
- 端口预选有 TOCTOU 竞态 (重选 ≤3 次兜底); cleanup 必须回收 daemon 进程 (含 JSON 缺失时的 pgrep 兜底发现), 测试重复跑不留僵尸.

## 停止条件

需要改变任一 Spec/决策/issue 边界或扩大范围时停止; hideRefs 行为与 F007 不符时停止 (回盘问).

## 适合 AFK 的原因

config 模板/写入语义/重入状态机/slug 契约/拒绝矩阵预期/审计项全部有权威来源; 监听地址与端口发现有明确兜底与记录路径, 无待决取舍.

## 验收标准

- [ ] birth 后母体/config/export-ok/daemon 就位, config 与 D008 模板逐项一致, srv 根枚举仅一仓
- [ ] config 错一键 (含多值键集合不符) 时 birth 中止, 原值未被覆盖, 无 daemon
- [ ] 无夹具标识的 --repo 被拒 (退出码 2) 且零写操作
- [ ] host 客户端 clone -b 检出母体分支, push 落地母体目录, 四类越界 push 全拒
- [ ] hooks 零新增, daemon 无 --export-all
- [ ] cleanup 幂等 (含 JSON 缺失时按 label/pgrep 兜底发现回收), 母体留存, 再 birth 走复用路径全过

## 被阻塞于

- 无
