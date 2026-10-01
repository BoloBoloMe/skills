## 父级

- `../EXECUTION.md`

## 执行

- [ ] 已实现

## 要构建什么

swt.py 新增只读子命令 `list [--records-root <PATH>]`: 跨仓枚举本 host 全部带 `sandbox-worktree.repo` label 的容器 (键存在匹配, 不限仓), 逐容器 inspect + port 现查, 合并 runtime 记录得出 lifecycle 与 record-state, 输出 stdout 人话进度行 + 末行 `LIST {...}` 单行 json (schema v1 核心字段), 退出码仅 0/4. 裸终端可直接使用并机器可读. 适合 AFK: 全部行为由 fake-run 测试钉住, 无产品决策残留.

## 覆盖依据

- Product: `docs/changes/swt-list-sandbox/PRODUCT.md`, AC-001 (数据面), AC-007
- Technical: `docs/changes/swt-list-sandbox/TECHNICAL.md`, 模块接口 (M1), 测试接缝, 非功能要求

## 相关决策

- `docs/changes/swt-list-sandbox/DECISIONS.md`: D002, D003, D004, D005, D006

## 允许范围

- `workflow/use-sandbox-worktree/scripts/swt.py`: parse_args 注册 list 子命令 (`--records-root`, 缺省与生命周期子命令同值), 新增 list 实现函数与必要的模块级辅助 (枚举/合并/LIST 组装/打印).
- 复用现有公共函数 (`run`, `podman_json`, `load_repo_runtimes` 同族的 records 扫描, `parse_podman_ports` 等) 不改其签名.
- 新增 `tests/test_swt_list.py`.

## 禁止范围

- 修改其余子命令的行为/输出/退出码.
- 改动共享公共函数签名.
- `access-entries`/`lans` 的入口组装 (归 ISSUE-02/03); 本切片条目可输出空 `access-entries` 与空 `lans`.

## 代码定位提示

- 入口: `swt.py` `parse_args` (约 2994 行起) 与 `main` 分发 (约 4435 行起), 仿 display-check 的注册形状.
- 枚举参考: `podman_container_state` (label 过滤/inspect/port 合并的既有形状, 约 690 行起); records 扫描参考 `repo_runtime_files`/`load_repo_runtimes` (约 231 行起) — 注意它们以 repo 为参, list 需要跨仓变体 (扫描全部 `<records-root>/runtime/*.json`).
- 输出协议参考: `print_state` (末行 STATE 形状, 约 505 行); 退出码与 stderr 标签参考 `require_command`/ENV 路径.
- 测试参考: `tests/test_swt_m08_headed.py` 的 fake-run 注入形状; `tests/README.md` 的快层/e2e 归层规则.

## TDD 切片

- TS-001:
  接缝: 接缝 B (podman 执行器 fake-run), `tests/test_swt_list.py`.
  测试用例: TC-001.
  先写的失败测试: `test_list_three_containers_two_repos` — fake ps/inspect/port 返回两仓三容器 (running/exited 各态), 断言末行 LIST 解析后 containers 含三个条目且 name/repo/branch/podman-state 正确; 实现前无 list 子命令, 失败.
  最小绿色实现范围: 子命令注册 + label 键存在枚举 + 逐容器 inspect/port + LIST 末行输出 (核心字段).
  不得测试: 内部函数调用次数 (子进程计数归 TC-004 专测), 私有辅助函数.
  覆盖: AC-001 (数据面), AC-007a.
- TS-002:
  接缝: 同上.
  测试用例: TC-002.
  先写的失败测试: `test_list_empty_no_containers` — fake ps 返回空, 断言 exit 0 且 LIST containers 为空, 人话行含 无在用沙盒容器.
  最小绿色实现范围: 空清单路径.
  不得测试: 同 TS-001.
  覆盖: AC-001 (空清单分支).
- TS-003:
  接缝: 同上.
  测试用例: TC-003.
  先写的失败测试: `test_list_record_state_and_lifecycle` — 构造 runtime 记录 matched/missing/corrupt 三容器与 retired 标记, 断言 record-state 与 lifecycle 字段; 记录文件不存在/损坏的区分在实现前不可能通过.
  最小绿色实现范围: 跨仓 records 扫描 + name 匹配 + corrupt 区分 (解析失败按 corrupt, 不抛).
  不得测试: 内部解析辅助.
  覆盖: AC-001 (标注面).
- TS-004:
  接缝: 同上.
  测试用例: TC-004.
  先写的失败测试: `test_list_subprocess_budget` — fake-run 计数断言 N 容器时 podman 子进程调用 ≤ 2+N.
  最小绿色实现范围: 聚合 ps 一次 + 逐容器 inspect/port 各一次, 不做多余轮询.
  不得测试: 未确认用例 (如并行度).
  覆盖: 非功能要求.
- TS-005:
  接缝: 同上.
  测试用例: TC-005.
  先写的失败测试: `test_list_readonly_and_collection_errors_and_env` — 三断言: 执行前后 fake runtime 文件内容与 nft 调用集不变 (只读, AC-007b); 某容器 inspect 失败时该条目含 collection-errors 且 exit 0 (AC-007c); podman 缺失时 exit 4 且 stderr 首行 ENV 标签 (AC-007d).
  最小绿色实现范围: 只读纪律 (不写任何文件/不发 nft 写命令), 单容器失败容错, ENV 出口.
  不得测试: nft 真实规则集.
  覆盖: AC-007b/c/d.

## 验证入口

- `uv run --with pytest pytest -m "not e2e" -q tests/test_swt_list.py` 全绿.
- 手动冒烟 (可选): 容器内无 podman 环境 `uv run python workflow/use-sandbox-worktree/scripts/swt.py list` 应 exit 4 + ENV 行.

## 风险提示

- `load_repo_runtimes` 族以 repo 为参: 跨仓扫描需新写遍历 `<records-root>/runtime/*.json` 的变体, 勿改旧函数签名 (停上级已定, 复用优先).
- podman label 键存在过滤 (`--filter label=sandbox-worktree.repo`) 在 fake 中要按真实 podman 语义建模 (任意值均命中).
- LIST 行必须单行 (json 序列化禁多行), 人话行禁含 `LIST ` 前缀字样.

## 停止条件

- 需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
- 发现共享函数必须改签名才能复用时停止.

## 适合 AFK 的原因

行为全部由 fake-run 断言钉住; 无产品/API/架构决策残留; 退出码与 schema 已在 TECHNICAL.md M1 接口固定.

## 验收标准

- [ ] `uv run python scripts/swt.py list` 在 fake/真机输出末行 `LIST {...}` 且 schema 字段齐 (TC-001/003).
- [ ] 空清单 exit 0 + 提示 (TC-002).
- [ ] 子进程 ≤ 2+N (TC-004).
- [ ] 只读 / 单容器失败 exit 0 / podman 缺失 exit 4+ENV (TC-005).
- [ ] 未改动其余子命令行为 (`tests/run --fast` 快层既有套件全绿).

## 被阻塞于

- 无
