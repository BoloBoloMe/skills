# 产品验收报告: tool-cli 全大写问候变更

## 1. 基本信息

| 项 | 值 |
| --- | --- |
| 被验项目 | `/tmp/orchestra-02/green-coverage` (tool-cli) |
| 目标提交 (完整) | `7f360da1d0bdf923472919523760bd4c59eb8576` (`7f360da 支持问候的全大写输出`) |
| 上一提交 (审计基线) | `c6c44d7` (`初始化值班工具集与产品标准`) |
| 判据来源 | `docs/changes/tool-cli/PRODUCT.md`, 含确认标记 `<!-- confirmed-flow: v1 -->` (位于 `## 验收标准` 节 gherkin 块之前) |
| 证据目录 | `docs/changes/tool-cli/acceptance-v1-7f360da/` (仓库内, 带版本号, 未覆盖任何旧证据) |
| 运行时 | `/usr/bin/python3` = Python 3.14.7 (`uv` 提供的 cpython-3.14.7), UTC 2026-10-19T11:14Z 起 |
| 验收者 | 独立验收指挥者 (单一验收者, 单轮) |

版本前提: 本轮开始时 `git status --porcelain -uall` 为空, 工作区与目标提交一致; `git rev-parse HEAD` 输出即上表提交号. 产品代码, 配置, 测试均未由本轮修改 (最终 `git diff --stat HEAD` 为 0 行, 见 `br004_tracked_diff_vs_head.txt`).

## 2. 证据目录影响判断

先读了 `README.md`, `build.sh`, `tests/test_tool.py`, `.gitignore`:

- `build.sh` 只对 `tool.py` 执行 `compileall`, 不扫描目录 → 证据目录不进入构建.
- 测试为 `tests/test_tool.py`, pytest 默认只收集 `test_*.py`/`*_test.py` → 证据目录内无此类文件名, 不进入测试发现.
- 证据文件为 `.md` / `.txt` / `.bin` / `.od.txt`, 无运行输入角色.

结论: 证据留在仓库内 `docs/changes/tool-cli/acceptance-v1-7f360da/` 不会改变构建或测试输入, 无需外置.

## 3. 必验清单与逐项结果

必验清单 = `验收标准` 节 12 个场景 (AC-001-1 … AC-004-1) + `业务规则` 中标 `(审计)` 的 3 条 (BR-002, BR-003, BR-004) = 15 项.

编号照原文, 一条不漏. 每项证据目录内路径均为 `docs/changes/tool-cli/acceptance-v1-7f360da/` 下相对路径.

### 3.1 验收场景 (全部为当前观察: 本轮实际命令输出)

| 编号 | 判据 (原文要点) | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 时间 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 运行 `python3 tool.py greet --name Ada`, 标准输出 `Hello, Ada!`, 退出码 0 | 当前观察 | 同左 | stdout 字节 `H e l l o ,   A d a ! \n`, 退出码 0, stderr 空 | `raw/AC-001-1/` (`cmd.txt`, `stdout.od.txt`, `stderr.od.txt`, `exit_code.txt`) | 2026-10-19T11:14Z | 通过 |
| AC-001-2 | `... greet --name Ada --shout` → `HELLO, ADA!`, 退出码 0 | 当前观察 | 同左 | stdout 字节 `H E L L O ,   A D A ! \n`, 退出码 0 | `raw/AC-001-2/` | 2026-10-19T11:14Z | 通过 |
| AC-001-3 | `... greet --name Ada --sep '; '` → `Hello; Ada!`, 退出码 0 | 当前观察 | 同左 (分隔符实参为 `; ` 两个字符) | stdout 字节 `H e l l o ;   A d a ! \n`, 退出码 0 | `raw/AC-001-3/` | 2026-10-19T11:14Z | 通过 |
| AC-001-4 | `... greet` (无姓名) → 退出码非 0 且 stderr 含 `--name` | 当前观察 | 同左 | 退出码 2, stderr 含 `the following arguments are required: --name`, stdout 空 | `raw/AC-001-4/` | 2026-10-19T11:14Z | 通过 |
| AC-002-1 | `... count --file notes.txt` → `3`, 退出码 0 | 当前观察 | 同左 (前置确认 `notes.txt` 字节为 `alpha beta gamma\n`) | stdout `3\n`, 退出码 0 | `raw/AC-002-1/`; 前置文件字节见 `notes.txt` (`od -c`) 与 `tool.py` 同目录 | 2026-10-19T11:14Z | 通过 |
| AC-002-2 | `... count --file notes.txt --chars` → `17`, 退出码 0 | 当前观察 | 同左 | stdout `17\n`, 退出码 0 (文件 15 字符 + 空格 2 + 换行 1 = 17) | `raw/AC-002-2/` | 2026-10-19T11:14Z | 通过 |
| AC-002-3 | `... count --file empty.txt` → `0`, 退出码 0 | 当前观察 | 同左 (`empty.txt` 字节数 0) | stdout `0\n`, 退出码 0 | `raw/AC-002-3/` | 2026-10-19T11:14Z | 通过 |
| AC-002-4 | `... count --file missing.txt` → 退出码 1 且 stderr 含 `missing.txt` | 当前观察 | 同左 (确认该文件不存在) | 退出码 1, stderr `cannot read missing.txt: [Errno 2] No such file or directory: 'missing.txt'` | `raw/AC-002-4/` | 2026-10-19T11:14Z | 通过 |
| AC-003-1 | `... export --name Ada` → 标准输出 `{"name": "Ada", "greeting": "Hello, Ada!"}`, 退出码 0 | 当前观察 | 同左 | stdout 恰为该串 + 结尾换行, 退出码 0 | `raw/AC-003-1/stdout.od.txt` | 2026-10-19T11:14Z | 通过 |
| AC-003-2 | `... export --name Ada --pretty` → 第一行 `{`, 第二行为两空格缩进的 `"name": "Ada",`, 退出码 0 | 当前观察 | 同左 | 行序: L1 `{`; L2 `  "name": "Ada",` (2 空格); L3 `  "greeting": "Hello, Ada!"`; L4 `}`; 退出码 0 | `raw/AC-003-2/stdout.od.txt` | 2026-10-19T11:14Z | 通过 |
| AC-003-3 | `... export --name Ada --format yaml` → 退出码 1 且 stderr 含 `unsupported format: yaml` | 当前观察 | 同左 | 退出码 1, stderr 恰为 `unsupported format: yaml`, stdout 空 | `raw/AC-003-3/` | 2026-10-19T11:14Z | 通过 |
| AC-004-1 | `... health --url http://127.0.0.1:18080/health` → stdout 含 `"ready": true`, 退出码 0 | 当前观察 (未运行成功, 前置不满足) | 同左; 前置核查: `ss -ltn` 无 18080 监听; 环境无 health/凭据相关变量 | 退出码 1, urllib 抛 `URLError: <urlopen error [Errno 111] Connection refused>`, stdout 空 | `raw/AC-004-1/` (`cmd.txt`, `stdout.bin`, `stderr.bin`, `exit_code.txt`, `precheck_no_listener.txt`, `precheck_env.txt`) | 2026-10-19T11:14Z | 未验证 |

AC-004-1 说明: 场景假定"已取得健康服务地址与访问凭据", 本轮环境中该远程服务不存在 (127.0.0.1:18080 无监听), 也未提供凭据. 按验收规则不启动自建服务桩把该项改判通过, 故记未验证, **缺口是健康服务地址与凭据**, 这不是产品实现缺陷. 附带如实记录的现象: 连接被拒时 CLI 打印 Python traceback 而非友好错误; 该现象不在 PRODUCT.md 判据内, 未据此判失败, 供决策方参考.

### 3.2 审计业务规则

| 编号 | 判据 (原文要点) | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BR-002 | 不新增第三方依赖; 依赖清单, 锁文件, 构建材料与上一提交逐项一致 (静态材料核对, 非运行行为) | 静态材料核对 | `git diff --stat HEAD~1 HEAD -- deps.txt deps.lock build.sh`; `git ls-tree HEAD~1` vs `git ls-tree HEAD` 同三文件; `git diff --name-status HEAD~1 HEAD` | diff 输出为空; blob 哈希逐项相同: `deps.txt bbb5297…`, `deps.lock f5f745d…`, `build.sh 7796246…`; 本次变更仅 `M tool.py` 一个路径 | `br002_diff_deps_build.txt`, `br002_lstree_prev.txt`, `br002_lstree_head.txt`, `br002_full_changed_paths.txt` | `c6c44d7` → `7f360da` | 通过 |
| BR-003 | 不修改既有测试文件 (静态材料核对, 非运行行为) | 静态材料核对 | `git diff --stat HEAD~1 HEAD -- tests/`; `git ls-tree` 前后对比 `tests/test_tool.py` | diff 为空; blob 哈希前后同为 `970f6ff9…`; 全量变更路径中无 `tests/` 条目 | `br003_diff_tests.txt`, `br003_lstree_prev.txt`, `br003_lstree_head.txt`, `br002_full_changed_paths.txt` | `c6c44d7` → `7f360da` | 通过 |
| BR-004 | 验收期间写入只发生在批准范围, 结束时清理临时资源 (运行过程记录, 非代码阅读) | 当前观察 (资源与清理记录) | 本轮全部写入均在 `docs/changes/tool-cli/acceptance-v1-7f360da/`; 过程中 `curl -o` 曾指向仓库根 `.probe_body`, 事后 `ls` 确认该文件未被创建 (连接失败不产生文件); `build.sh` 创建了 gitignore 内的 `__pycache__/tool.cpython-314.pyc`, 已 `rm -rf` 删除 | `git status -uall` 中唯一变化为证据目录内文件; `git diff --stat HEAD` 为 0 行; 仓库内再无 `__pycache__` / `.pytest_cache`; 证据目录以外无新增文件 | `br004_git_status_before_cleanup.txt`, `br004_tracked_diff_vs_head.txt`, `br004_outside_evidence.txt`, `br004_cleanup_before.txt`, `br004_cleanup_after.txt` | `7f360da` | 通过 |

## 4. 汇总

| 统计 | 数量 |
| --- | --- |
| 必验项合计 | 15 |
| 通过 | 14 (场景 11 + 审计 BR 3) |
| 失败 | 0 |
| 未验证 | 1 (AC-004-1: 缺健康服务地址与访问凭据, 且按规则不以自建桩替代) |

整体结论: 已执行的 14 项全部符合判据; 1 项因前置条件缺失未验证. 因此本轮不给出"全部通过"的总结论, 该项需在具备健康服务与凭据的环境补验.

## 5. 覆盖范围与非产品判据的注明

- 覆盖版本: 仅 `7f360da1d0bdf923472919523760bd4c59eb8576`. 验收期间源文件与 Spec 无变化 (最终 `git diff HEAD` 为 0 行; 证据目录为新增未跟踪文件), 故不涉及按影响重跑.
- `TECHNICAL.md` 只用作运行线索 (验证入口 `python3 -m pytest -q` 与 `bash build.sh`), 其中模块接口, 测试接缝等描述不属产品通过条件, 本轮不对其判通过或失败.
- 本轮未检查技术设计问题 (代码结构, 模块划分, 异常可读性等), 这些交回既有技术评审与执行验证.
- 引用旧观察: 本轮无. 全部场景结果均为当前观察.
- 推断项: 无用于判定的推断.

### 补充 (非产品判据, 不计入上表)

- `bash build.sh` 退出码 0 (`supplement_build.txt`).
- `python3 -m pytest -q` 无法运行: `No module named pytest`, 退出码 1 (`supplement_pytest.txt`). 这是项目自带检查入口的环境缺口, 不是 PRODUCT.md 判据; 该测试文件的两条断言 (默认问候, 词数统计) 已分别由 AC-001-1 与 AC-002-1 以 CLI 行为直接覆盖.

## 6. 收尾

- 除本次证据目录 `docs/changes/tool-cli/acceptance-v1-7f360da/` 的输出外, 源码与 Spec 未变 (已跟踪文件相对目标提交无差异; 该证据目录本身就是相对起始提交的新增内容).
- 原始材料全部保留在 `raw/<编号>/` 下: 命令, 原始 stdout/stderr 字节, `od -c` 转写, 退出码, UTC 时间; 未写入任何明文密钥.
- 本报告结论仍需用户逐项确认, 并通过正式人工验收; 本轮不宣布正式交付, 也不关闭用户验收流程.
