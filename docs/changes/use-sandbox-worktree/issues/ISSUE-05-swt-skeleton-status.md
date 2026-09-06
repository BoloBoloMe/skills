# ISSUE-05 swt 骨架: CLI 协议底座 + status 子命令

## 父级

- `../roadmap/MILESTONE-12.md`
- `../EXECUTION-M12.md` (全局允许/禁止范围, CLI 契约, STATE/DECIDE/exit 协议 — 本 ISSUE 不重复)
- `../DECISIONS.md`: D025 (五子命令形态/废弃注册表索引), D027 (exit code+输出契约), D034 (文件锁), D026 (收据机制 — 本 ISSUE 只建机制, 首个承载者归 ISSUE-07)
- `../UNAUTHORIZED_DECISIONS.md`: U-002 (收据形态), U-003 (runtime/identity/锁/审计路径)

## 执行(Execution)

- [x] 已实现

## 要构建什么

`workflow/use-sandbox-worktree/scripts/swt.py` (uv run python, 单文件, stdlib only) 第一片:

1. argparse 五子命令骨架与共用 flag (`--repo`/`--records-root`); 本 ISSUE 只实现 `status`, 其余子命令存在即报 exit 2 `FAIL NOT-IMPLEMENTED <子命令>` (后续 ISSUE 逐个替换).
2. `--repo` 推导: 显式优先, 缺省 `git rev-parse --git-common-dir` → 主仓根 (worktree 内也正确); 非 git 目录 exit 2.
3. 输出协议实现: stdout 进度行 + 末行 `STATE {...}` (schema:1, 字段见 EXECUTION-M12 CLI 契约节); stderr 首行标签 FAIL/PARTIAL/ENV; exit 0/1/2/3/4.
4. runtime 状态文件: 读写 (临时文件+os.replace 原子写), 路径/identity 命名按 U-003; 缺文件 = 空状态.
5. 文件锁 (D034): 变更类子命令 (birth/resume/terminate/switch) 进入时 fcntl 非阻塞取 `<runtime>.lock`, 拿不到 exit 2 `FAIL LOCKED <持有者pid信息可得则含>`; status 不取锁.
6. 决策收据机制 (U-002): 生成 (decisions/<id>.json, 指纹字段按 D026 清单), 按 kind 匹配待决票, 指纹重算比对, 消费即删; 供后续 ISSUE 调用, 本 ISSUE 只测机制本身 (经一个内部最小 harness 或直接文件级断言, 不造假子命令).
7. `status` 子命令完整实现 (只读, 永不改状态, exit 0 含 "什么都没有"):
   - 母体: runtime + `git worktree list` 交叉; worktree-dirty 实测.
   - config: `git config --get-all` 比对 D008 模板 → swt-form true/false.
   - daemon: pgrep 按 srv/base-path 模式 (沿用 e2e-smoke `daemon_pids` 思路, 但 swt 的 base-path = 主仓所在目录, 以 runtime 记录为准; runtime 缺失时按 label 兜底), orphan 判定.
   - 容器: `podman ps -a --filter label=sandbox-worktree.repo=<主仓>` 全列 (D031 两层 label: 母体 id + 实例名 — 沿用 M03 三 label 并加 podman-id), 每容器 state/ssh-port (`podman port`)/retired (runtime)/dirty (ssh 可达才查, 不可达 reachable=false, dirty 不计数).
   - 镜像: 容器的 image-digest 与 records-root 内最新 build-id 镜像 digest 比对 → newer-available (D013); 无记录则 null.
   - 网络: net-firewall `show` → table-present; mode 取 runtime.

## 允许范围

- 新建 `swt.py`, `tests/test_swt_m12.py`; 本 ISSUE 文件
- /tmp 夹具仓; 测试用 `podman create` 带 label 的裸容器 (alpine 级, 不起 sshd) 作 status 探测对象
- 只读调用 slug.py / net-firewall.py (show) / image-prep 记录目录布局

## 禁止范围

- 不实现 birth/resume/terminate/switch 任何状态变更逻辑
- 不改 net-firewall.py / image-prep.py / e2e-smoke.py
- EXECUTION-M12 全局禁止范围全部适用
- status 禁止有任何写副作用 (含不创建 runtime 文件)

## TDD 切片

- TS-001 空仓 status: /tmp 夹具仓, 无任何 runtime/母体/容器 → exit 0, STATE 全空值 (mother.exists=false, daemon=null, containers=[], network=null), stdout 末行可解析 json.
- TS-002 --repo 推导: 主仓根/主仓 linked worktree 内 cwd 均解析到同一主仓; 非 git 目录 exit 2 FAIL.
- TS-003 母体与 config 探测: 手工建母体 worktree + 按 D008 模板写 config → status 报 mother.exists=true/config.swt-form=true; 改错一个值 → swt-form=false; 制造母体脏文件 → worktree-dirty=true.
- TS-004 容器探测: 裸容器带三 label (stopped/running 各一) → containers[] 名称/state 正确, ssh-port 不崩 (无端口映射则 null), 异仓 label 容器不出现.
- TS-005 锁: 变更类子命令持锁期间第二个变更类调用 exit 2 LOCKED (用 NOT-IMPLEMENTED 前的 birth 入口或 terminate 入口触发取锁路径即可, 取锁先于 NOT-IMPLEMENTED 判定); status 并发不受阻.
- TS-006 收据机制: 生成 → 文件存在且指纹字段齐; 同指纹匹配消费 → 删票; 指纹漂移 → 不匹配且票保留; 一次性 → 消费后二次使用失败.
- TS-007 输出协议: 人为触发各 exit 路径 (2=非 git 目录, 4=PATH 缺失 podman/git) 断言 stderr 首行标签与 exit code; STATE 永远只在 exit 0/1 的 stdout 末行.

## 验证入口

`uv run --with pytest pytest tests/test_swt_m12.py` 全绿.

## 停止条件

需要改 D025/D026/D027/D034 语义, 或扩大允许范围时停止上报.
