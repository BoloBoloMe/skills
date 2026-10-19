# 独立产品验收报告: tool-cli @ 2028383

## 基本信息

- 目标提交: `2028383100c4d5c65789c3a56b13c44d6eba8da2` (HEAD, `feat: greet 支持全大写输出`, 2026-10-19 20:27:16 +0800)
- 上一提交 (审计基线): `adb566049dc92e4f47f3ed08880f88d2602a2249`
- 判据来源: `docs/changes/tool-cli/PRODUCT.md`; `验收标准` 节在 gherkin 块之前带 `<!-- confirmed-flow: v1 -->`; 判据取 5 个 gherkin 场景与 `业务规则` 中标 `(审计)` 的 BR-002 原文.
- 版本前提: 验收开始时 `git status --porcelain` 为空 (仅本证据目录为未跟踪项); `git rev-parse HEAD` 与目标提交一致.
- 证据目录: `docs/changes/tool-cli/verify-2028383-v1/` (仓库内; 见下文"证据目录影响判断")
- 验收者: 1 名, `S-verifier-1`, 会话 `01a15426-b0b5-7604-80c4-85011cab7cae`, 创建于 2026-10-19T12:33:04Z (20:33:04 +0800)
- 覆盖范围: 必验清单 6 项 (5 场景 + 1 审计 BR) 全覆盖; 技术材料 (`TECHNICAL.md`, pytest, build.sh, prepare.sh) 只作操作线索, 不判产品通过或失败.

## 逐项结果

| 标准编号 | 材料类型 | 实际操作 / 引用信息 | 实际结果 | 证据位置 | 时间 / 版本 | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 默认问候 | 当前观察 | `python3 tool.py greet --name Ada` | stdout 字节 `Hello, Ada!\n`, stderr 空, 退出码 0 | `AC-001-1.log` (含 hexdump) | 2026-10-19T20:33:23+08:00, 2028383 | 通过 |
| AC-001-2 全大写问候 | 当前观察 | `python3 tool.py greet --name Ada --shout` | stdout 字节 `HELLO, ADA!\n`, stderr 空, 退出码 0 | `AC-001-2.log` | 2026-10-19T20:33:23+08:00, 2028383 | 通过 |
| AC-002-1 统计词数 | 当前观察 | 先核对 `notes.txt` 为 17 字节 `alpha beta gamma\n` (符合场景前提), 再 `python3 tool.py count --file notes.txt` | stdout `3\n`, stderr 空, 退出码 0 | `AC-002-1.log`, `00-preconditions.log` | 2026-10-19T20:33:23+08:00, 2028383 | 通过 |
| AC-002-2 统计字符数 | 当前观察 | `python3 tool.py count --file notes.txt --chars` | stdout `17\n`, stderr 空, 退出码 0 | `AC-002-2.log` | 2026-10-19T20:33:23+08:00, 2028383 | 通过 |
| AC-003-1 JSON 导出 | 当前观察 | `python3 tool.py export --name Ada` | stdout 字节 `{"name": "Ada", "greeting": "Hello, Ada!"}\n`, stderr 空, 退出码 0 | `AC-003-1.log` (含 hexdump) | 2026-10-19T20:33:23+08:00, 2028383 | 通过 |
| BR-002 依赖与构建材料逐项一致 (审计) | 静态核对 (非运行行为) | `git diff adb5660..HEAD -- deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py`; 每文件 `git show adb5660:<file> \| sha256sum` 对比当前 `sha256sum`; `git diff --name-status adb5660..HEAD` | diff 无输出; 5 个文件 sha256 全部 SAME; 全量变更仅 `tool.py`, `tests/test_tool.py` | `BR-002.log` | 2026-10-19T20:33:28+08:00, adb5660→2028383 | 通过 |

### BR-002 明细 (静态材料核对, 不是运行行为结果)

| 文件 | adb5660 sha256 | 当前 sha256 | 结论 |
|---|---|---|---|
| deps.txt | f37d7a06…460d4806 | 同左 | SAME |
| deps.lock | 28cc4586…27da5f50 | 同左 | SAME |
| build.sh | ae45fcf9…4bfa05aad | 同左 | SAME |
| prepare.sh | d763bb6f…f96c2fac75e | 同左 | SAME |
| tools/build_manifest.py | 4c304ef6…4e41c4aee2 | 同左 | SAME |

完整哈希见 `BR-002.log`. `deps.txt` 内容 `python-stdlib`, `deps.lock` 声明只用标准库, 与"不新增第三方依赖"一致.

补充说明: `bash prepare.sh` 生成的 `dist/app.txt` 内容含 `greet-shout=yes`, 这是构建脚本在构建时读取当前 `tool.py` 的产物, 属预期; 构建材料本身 (build.sh, prepare.sh, build_manifest.py) 与基线逐项一致, 不构成 BR-002 违反.

## 非产品判据的观察 (不记通过, 也不记失败)

| 项目 | 材料类型 | 操作 | 实际结果 | 证据 | 说明 |
|---|---|---|---|---|---|
| pytest | 未运行 | `python3 -m pytest -q` | `No module named pytest`, 退出码 1 | `tech-hints.log` | 环境缺 pytest. 测试是否通过不属本轮产品判据, 记为技术线索不可用 |
| 构建检查 | 当前观察 | `bash prepare.sh` | `built dist/app.txt`, 退出码 0 | `tech-hints.log` | 生成被 gitignore 的 `dist/app.txt` |
| 编译检查 | 当前观察 | `bash build.sh` | 无输出, 退出码 0 | `tech-hints.log` | 不属产品判据 |
| 测试文件改动 | 静态核对 | 基线到目标提交的 diff | 新增 `tests/test_tool.py::test_shout_greeting_is_uppercase` | `BR-002.log` 的 `--name-status` | 属技术事项, 本轮不判产品通过或失败 |

## 派工记录

- 场景组划分: G1 问候 (`AC-001-1`, `AC-001-2`, `AC-003-1`; 导出复用问候逻辑), G2 统计 (`AC-002-1`, `AC-002-2`), G3 审计 (`BR-002`).
- 当轮可用非作者验收者: 2 名; 计划与实际人数: **1 名**.
- 只派一人的依据:
  1. 重复准备成本大于并行收益: 每个新会话都要重读同一份 PRODUCT.md, 重复确认同一工作区, 并按 README 各跑一次 `bash prepare.sh` 生成同一份 `dist/app.txt`; 实际工作量只有 6 条秒级命令, 新会话启动与重复准备的成本高于并行省下的时间.
  2. 拆开后仍占用同一份资源: 同一入口 `tool.py`, 同一工作区, 同一份构建产物与 `notes.txt`, 不构成真正隔离.
  3. 不逐条 AC 开会话, 不为用满名额制造重复劳动.
- 验收者明细:

| 会话 | 会话标识 | 创建时间 | 承接标准 | 未参与本次实现与修复的可核对事实 |
|---|---|---|---|---|
| S-verifier-1 | pi 会话 `01a15426-b0b5-7604-80c4-85011cab7cae`, pane `w1J:p30`, tab `w1J:t3Y` | 2026-10-19T12:33:04Z (20:33:04 +0800) | AC-001-1, AC-001-2, AC-002-1, AC-002-2, AC-003-1, BR-002 | 会话创建时间晚于实现提交 (20:27:16 +0800); 不是实现者会话 (`/tmp/orchestra-03/author`), 未继承其过程; 会话记录只有 read/bash/write (write 目标仅本证据目录), 无 edit, 无 `git commit` |

- 派完核对: 会话记录显示它读了 PRODUCT.md 与 TECHNICAL.md, 按分到的 6 项逐条执行, 产出 `AC-*.log`, `BR-002.log`, `00-preconditions.log`, `tech-hints.log`, `RESULT.md`; 作范围超出分派事项.

### 证据目录影响判断

- `build.sh` 只编译 `tool.py`; `prepare.sh` → `tools/build_manifest.py` 只读 `tool.py` 并写 `dist/app.txt`, 都不扫描 `docs/`.
- pytest 无配置文件, 默认只收集 `test_*.py` / `*_test.py`; 本目录只放 `.md` 与 `.log`, 无 Python 文件.
- 结论: 目录留在仓库内, 不进入构建, 测试发现或运行输入.

## 材料复核

- 6 项材料全部有可读取原件, 存于本目录; `RESULT.md` 是验收者自写摘要, 结论以其 `*.log` 原件为准.
- 逐项把 `*.log` 的原始 stdout, stderr, 退出码与验收者会话记录 (`~/.pi/agent/sessions/--tmp-orchestra-03-green-non-author--/2026-10-19T12-33-04-182Z_01a15426-b0b5-7604-80c4-85011cab7cae.jsonl`) 中的工具调用与返回逐条对照, 一致.
- 发现并已澄清的一处表面差异: 验收者批量跑场景时终端回显 `stdout=[]`, 但该行来自脚本里的固定字符串 `stdout=[$(cat /dev/null)]`, 是回显写法错误, 不是空输出. 真实 stdout 由重定向写入临时文件后 hexdump 进日志 (`AC-*.log` 的 `stdout_hexdump` 段), 且随后 `cat` 日志复核有内容, 两者不冲突. 结论不依赖该回显行.
- 未发现无原件的摘要结论, 未发现摘要与原件冲突的通过项.

## 未验证项与失败项

- 产品判据失败: 0 项.
- 产品判据未验证: 0 项.
- 非产品判据未运行: `python3 -m pytest -q` (环境无 pytest). 已按技术线索记录, 不影响本报告的通过结论, 也不作为产品判据的通过依据.

## 收尾

- 除本次证据目录的输出外, 源码与 Spec 未变: `git status --porcelain` 仅本证据目录为未跟踪项, 已跟踪文件无改动. 另由技术线索命令产生了被 gitignore 的 `dist/` 与 `__pycache__/` (未跟踪且被忽略), 一并注明.
- 本报告基于 2028383 版本; 结论仍需用户逐项确认并走正式人工验收. 本报告不宣布正式交付, 也不关闭用户验收.
