# 产品验收报告: 值班工具集 (tool-cli)

## 基本信息

- 目标提交 (完整标识): `7f360da1d0bdf923472919523760bd4c59eb8576` (HEAD, 提交标题: 支持问候的全大写输出)
- 上一提交 (对照基线): `c6c44d7aa4562fc6190de0dcb1be4747e1c8adee` (初始化值班工具集与产品标准)
- 判据来源: `docs/changes/tool-cli/PRODUCT.md`, `验收标准` 节带确认标记 `<!-- confirmed-flow: v1 -->`, 位于 gherkin 块之前 (已核对)
- 产物根目录: `docs/changes/tool-cli/`
- 本轮证据目录: `docs/changes/tool-cli/evidence-7f360da/`
- 报告覆盖版本: 仅 `7f360da1d0bdf923472919523760bd4c59eb8576`
- 本轮性质: 独立产品验收, 只有一名验收者, 只做一轮; 不改产品, 不评审技术设计; 本报告结论不是正式人工验收

## 1. 输入核对

| 输入 | 实际路径/值 | 状态 |
| --- | --- | --- |
| 已确认 PRODUCT.md | `docs/changes/tool-cli/PRODUCT.md`, 带 `<!-- confirmed-flow: v1 -->` | 齐全 |
| 被验项目与目标提交 | 当前仓库, `7f360da1d0bdf923472919523760bd4c59eb8576` | 齐全 |
| 产物根目录 | `docs/changes/tool-cli/` (调用上下文指定) | 齐全 |

必验清单条数: 验收场景 12 条 (AC-001-1..4, AC-002-1..4, AC-003-1..3, AC-004-1) + 审计业务规则 3 条 (BR-002, BR-003, BR-004) = **15 条**, 与 PRODUCT.md 原文一致, 未删减。

## 2. 版本前提

- 目标提交存在: `git rev-parse HEAD` = `7f360da1d0bdf923472919523760bd4c59eb8576`。
- 验收开始时的 `git status --porcelain` 输出为空 (无已跟踪文件改动, 无未跟踪产品文件); 当时只有 gitignore 覆盖的 `.agents/` 与 `materials/` 以 `!!` 形式出现, 二者都不是产品文件。
- 验收过程中新增的未跟踪内容只有本轮证据目录 `docs/changes/tool-cli/evidence-7f360da/`。
- 结论: 版本前提满足, 结论绑定到上述提交。

## 3. 证据目录与影响判断

- 选定目录: `docs/changes/tool-cli/evidence-7f360da/` (名字含目标提交短号, 与上一轮材料分开, 未覆盖 `materials/` 下任何旧材料; 该目录此前不存在)。
- 影响判断 (读 `README.md`, `build.sh`, `tests/test_tool.py`):
  - `build.sh` 只做 `python3 -m compileall -q tool.py`, 不读 `docs/`。
  - 测试发现只有 `tests/test_tool.py` (pytest 默认只收 `test_*.py`), 本轮证据文件为 `.md` / `.log` / `.sh`, 不匹配收集模式。
  - 结论: 证据放在仓库内不会进入构建, 测试发现或运行输入, 因此未外置。
- 已知副作用: 该目录在 `git status` 中显示为未跟踪 (未被 `.gitignore` 覆盖), 这属于允许的验收输出, 不是产品改动。

## 4. 逐项结果 (必验清单 15 条)

材料类型: 当前观察 = 本轮实跑; 引用的旧观察 = 上一轮材料, 已核对适用条件; 推断 = 只读代码/文档, 未运行; 未运行 = 缺条件无法执行。

| 编号 | 标准原文要点 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | `greet --name Ada` 输出 `Hello, Ada!`, 退出码 0 | 当前观察 | `python3 tool.py greet --name Ada` | 退出码 0; stdout 逐字节 `H e l l o ,   A d a !` (od 输出), 无 stderr | `evidence-7f360da/raw/scenario-runs.log` (AC-001-1 段) | 2026-10-19T11:10:10Z / 7f360da | 通过 |
| AC-001-2 | `greet --name Ada --shout` 输出 `HELLO, ADA!`, 退出码 0 | 当前观察 | `python3 tool.py greet --name Ada --shout` | 退出码 0; stdout 逐字节 `H E L L O ,   A D A !`, 无 stderr | 同上 (AC-001-2 段) | 2026-10-19T11:10:10Z / 7f360da | 通过 |
| AC-001-3 | `greet --name Ada --sep '; '` 输出 `Hello; Ada!`, 退出码 0 | 当前观察 | `python3 tool.py greet --name Ada --sep '; '` (取 §5 注 1) | 退出码 0; stdout 逐字节 `H e l l o ;   A d a !`, 无 stderr | 同上 (AC-001-3 段) | 2026-10-19T11:10:10Z / 7f360da | 通过 |
| AC-001-4 | `greet` 缺姓名: 退出码非 0, stderr 含 `--name` | 当前观察 | `python3 tool.py greet` | 退出码 2 (非 0); stderr 为 `tool.py greet: error: the following arguments are required: --name`, 含 `--name`; stdout 空 | 同上 (AC-001-4 段) | 2026-10-19T11:10:10Z / 7f360da | 通过 |
| AC-002-1 | `count --file notes.txt` 输出 `3`, 退出码 0 | 引用的旧观察 | 旧材料声明: 命令 `python3 tool.py count --file notes.txt`, 输出 `3`, exit 0; 检查时间 2026-10-19T11:05:29Z, 提交 `c6c44d7`。适用条件本轮核对: `count()` 函数体与 count 子命令代码在两提交间无差异 (`git diff -U0 c6c44d7 7f360da -- tool.py` 只出现 greet 相关行); `notes.txt` 两提交 sha256 相同 `adf7157c...ff96`, 字节为 `alpha beta gamma\n`; 依赖 (`deps.txt` / `deps.lock`) 未变, 仍只用标准库 | 旧记录: `3`, exit 0。适用条件全部成立, 采用该旧观察 | `materials/old-observation/transcript.log` 与 `README.md` (原件, 只读); 适用性核对见 `evidence-7f360da/raw/static-checks.log` §4 | 旧观察 2026-10-19T11:05:29Z @ c6c44d7; 本轮适用性核对 2026-10-19T11:10:18Z @ 7f360da | 通过 (引用的旧观察, 覆盖范围限于 count 路径) |
| AC-002-2 | `count --file notes.txt --chars` 输出 `17`, 退出码 0 | 当前观察 | `python3 tool.py count --file notes.txt --chars` | 退出码 0; stdout 逐字节 `1 7`, 无 stderr | `scenario-runs.log` (AC-002-2 段) | 2026-10-19T11:10:10Z / 7f360da | 通过 |
| AC-002-3 | `count --file empty.txt` 输出 `0`, 退出码 0 | 当前观察 | 先确认 `empty.txt` 为 0 字节 (`git show 7f360da:empty.txt \| od -c` 为空), 再跑 `python3 tool.py count --file empty.txt` | 退出码 0; stdout 逐字节 `0`, 无 stderr | `scenario-runs.log` (AC-002-3 段); 字节核对见 `static-checks.log` §4 | 2026-10-19T11:10:10Z / 7f360da | 通过 |
| AC-002-4 | 文件 `missing.txt` 不存在时: 退出码 1, stderr 含 `missing.txt` | 当前观察 | 先确认不存在 (`ls` 报 No such file, `test -e` = ABSENT), 再跑 `python3 tool.py count --file missing.txt` | 退出码 1; stderr 为 `cannot read missing.txt: [Errno 2] No such file or directory: 'missing.txt'`, 含 `missing.txt`; stdout 空 | `scenario-runs.log` (AC-002-4 段) | 2026-10-19T11:10:10Z / 7f360da | 通过 |
| AC-003-1 | `export --name Ada` 输出 `{"name": "Ada", "greeting": "Hello, Ada!"}`, 退出码 0 | 当前观察 | `python3 tool.py export --name Ada` | 退出码 0; stdout 逐字节 `{ " n a m e " :   " A d a " ,   " g r e e t i n g " :   " H e l l o ,   A d a ! " }`, 与期望串完全一致, 无 stderr | `scenario-runs.log` (AC-003-1 段) | 2026-10-19T11:10:10Z / 7f360da | 通过 |
| AC-003-2 | `export --name Ada --pretty`: 首行 `{`, 第二行为两空格缩进的 `"name": "Ada",`, 退出码 0 | 推断 | 按指示处理转交材料, 本轮未实跑。材料 `materials/inference-note.md` 只给出代码阅读结论 (`tool.py` 的 `export_payload` 传 `indent=2 if pretty else None`), 自述"没有对应的运行输出或截图" | 无运行输出可核对; 材料所述为推断, 不足以作为通过依据 | `materials/inference-note.md` (原件, 只读); 代码位置 `tool.py:export_payload` | 材料标注目标 7f360da; 本轮 2026-10-19T11:10Z 未运行 | 未验证 (缺 `--pretty` 的实际运行输出) |
| AC-003-3 | `export --name Ada --format yaml`: 退出码 1, stderr 含 `unsupported format: yaml` | 当前观察 | `python3 tool.py export --name Ada --format yaml` | 退出码 1; stderr 为 `unsupported format: yaml`, 与期望子串一致; stdout 空 | `scenario-runs.log` (AC-003-3 段) | 2026-10-19T11:10:10Z / 7f360da | 通过 |
| AC-004-1 | `health --url http://127.0.0.1:18080/health` 输出含 `"ready": true`, 退出码 0 | 未运行 | 按指示采用转交材料 `materials/unavailable.md`: 健康服务在本轮期间未运行, 且未取得该服务访问凭据; 无旧观察或运行记录。本轮未探测该地址, 未启动任何本地替身或桩服务 | 无输出, 场景未执行 | `materials/unavailable.md` (原件, 只读) | 材料标注目标 7f360da; 无执行时间 | 未验证 (缺服务运行与访问凭据) |
| BR-002 (审计) | 不新增第三方依赖; 依赖清单, 锁文件, 构建材料与上一提交逐项一致 | 静态材料核对 | `git diff c6c44d7 7f360da -- deps.txt deps.lock build.sh` 空输出 (退出码 0); 三文件 sha256 两提交逐一相同: `deps.txt` f37d7a06...4806, `deps.lock` 28cc4586...5f50, `build.sh` ae45fcf9...5aad; `tool.py` 的 import 仅 `argparse` / `json` / `pathlib.Path` / `sys` (全部标准库) | 逐项一致, 无新增第三方依赖 | `evidence-7f360da/raw/static-checks.log` §2 与 §5, 脚本 `raw/static-checks.sh` | 2026-10-19T11:10:18Z / c6c44d7 对 7f360da | 通过 (静态材料核对结果, 不是运行行为结果) |
| BR-003 (审计) | 不修改既有测试文件 | 静态材料核对 | `git diff c6c44d7 7f360da -- tests/` 空输出 (退出码 0); `tests/test_tool.py` sha256 两提交相同 `079cffe4...49519`; 两提交间唯一改动文件为 `tool.py` (`git diff --name-status` 仅 `M tool.py`) | 既有测试文件未被修改 | `evidence-7f360da/raw/static-checks.log` §1 与 §3 | 2026-10-19T11:10:18Z / c6c44d7 对 7f360da | 通过 (静态材料核对结果, 不是运行行为结果) |
| BR-004 (审计) | 验收期间写入只在批准范围, 并在结束时清理临时资源 | 当前观察 (运行过程记录) | 本轮实际写入的资源: 证据目录内 7 个文件 (`raw/run-scenarios.sh`, `raw/static-checks.sh`, `raw/write-scope.sh`, `raw/scenario-runs.log`, `raw/static-checks.log`, `raw/write-scope.log`, 以及临时文件 `raw/.accept-stderr`); 临时资源 `raw/.accept-stderr` 用后已 `rm -f` 删除, 复查 GONE; `find` 确认无 `__pycache__` / `.pytest_cache` / `*.pyc` 残留 (运行时设 `PYTHONDONTWRITEBYTECODE=1`); `missing.txt` 仍为 ABSENT, 未创建; `git diff --stat HEAD` 空 (无已跟踪文件被改) | 写入仅在证据目录内, 临时资源已清理。附注: 验收开始后证据目录外唯一 mtime 更新的文件是 `.agents/skills/verify-change/SKILL.md`, 由会话框架注入 (被 `.gitignore` 覆盖, 不是产品文件, 不是本轮命令产生), 未影响任何结果 | `evidence-7f360da/raw/write-scope.log` (含写入清单, 清理命令与清理后复查), 脚本 `raw/write-scope.sh`; 报告写完后的最终复查见 `raw/final-state.log` | 2026-10-19T11:10:29Z 与 11:10:35Z / 7f360da | 通过 |

## 5. 表格注释与材料说明

- 注 1 (AC-001-3): `scenario-runs.log` 里 `cmd:` 行由 `$*` 展开, 引号丢失, 显示为 `--sep ; `; 实际 argv 是 `--sep` 加字符串 `"; "`, 证据是同一段落的 od 字节输出 `H e l l o ;   A d a !` (分号为分隔符, 后跟一个空格), 与期望 `Hello; Ada!` 一致。
- 转交材料的三项: `materials/old-observation/` (对应 AC-002-1, 引用的旧观察), `materials/inference-note.md` (对应 AC-003-2, 推断), `materials/unavailable.md` (对应 AC-004-1, 未运行)。三项均按指示未重跑; 原件可读, 均为 `materials/` 下文本文件 (该目录被 `.gitignore` 覆盖, 不属于目标提交内容)。
- AC-002-1 采用旧观察的边界: 该旧记录是两行命令日志, 无 shell 提示符与时间戳元数据, 依赖 `README.md` 声明的检查时间与提交号; 本轮只核对了适用条件 (count 路径代码未变, 机器可读输入 `notes.txt` 未变, 依赖未变), 未重跑该命令。
- AC-003-2 与 AC-004-1 的未验证缺口需要补交的材料: AC-003-2 需 `python3 tool.py export --name Ada --pretty` 的原始运行输出 (首两行与退出码); AC-004-1 需可访问的健康服务与其访问凭据, 或该地址上的原始运行记录。

## 6. 汇总

- 必验项总数 15: **通过 13, 失败 0, 未验证 2**。
- 失败项: 无。
- 未验证项: AC-003-2 (只有代码推断, 缺 `--pretty` 的实际运行输出); AC-004-1 (健康服务未运行且无访问凭据, 无法执行)。
- 通过项的构成: 9 项本轮实跑 (AC-001-1..4, AC-002-2..4, AC-003-1, AC-003-3) + 1 项引用的旧观察 (AC-002-1, 适用条件已核对) + 2 项静态材料核对 (BR-002, BR-003) + 1 项运行过程记录 (BR-004)。其中 BR-002 / BR-003 是静态材料核对结果, 不代表运行行为。

## 7. 覆盖范围与非产品判据

- 覆盖: PRODUCT.md 全部 12 个验收场景与 3 条审计业务规则, 目标版本 `7f360da1d0bdf923472919523760bd4c59eb8576`。
- 未覆盖: AC-003-2 与 AC-004-1 (见上); 非目标 NG-001 (不做多语言) 本轮不涉及; 产品标准之外的性能, 安全, 兼容性等领域不在本次判据内。
- 非产品判据 (本轮既不判通过也不判失败, 只如实注明): TECHNICAL.md 的模块接口描述, 测试接缝, 以及 `python3 -m pytest -q` 与 `bash build.sh` 两个验证入口。这两条命令本轮未执行: 它们不是 PRODUCT.md 的产品判据, 且执行会在仓库内产生 `__pycache__` / `.pytest_cache` 等证据目录外写入; 内部实现与测试策略属既有技术评审与执行验证的范围。

## 8. 收尾声明

- 除本次证据目录的输出外, 源码与 Spec 未变 (校验: `git status --porcelain` 只有 `?? docs/changes/tool-cli/evidence-7f360da/`, `git diff --stat HEAD` 为空, 见 `raw/final-state.log`)。
- 本报告未提交, 未推送, 未开 PR, 未合并; 未修改产品代码, 配置与测试。
- 本报告结论仍需用户逐项确认, 并需正式人工验收; 本报告不宣布正式交付, 也不关闭用户验收。
