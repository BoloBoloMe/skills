# 产品验收报告 (独立验收, 单轮)

- 目标提交: `93ba124b07ddc1c9cd845a9f7f4256fc6dee8294` (HEAD, `feat: greet 支持全大写输出`)
- 上一提交 (对照基线): `c6a3745d7fc51055c0ff74b2ff75c22962973073` (`初始化工具集与产品标准`)
- 被验项目: `/tmp/orchestra-03/red-delegation` (tool-cli)
- 判据来源: `docs/changes/tool-cli/PRODUCT.md`, `验收标准` 节带确认标记 `<!-- confirmed-flow: v1 -->`; 另加 `业务规则` 节标 `(审计)` 的规则
- 产物根目录: `docs/changes/tool-cli/`
- 本轮证据目录: `docs/changes/tool-cli/evidence-93ba124-20261019/`
- 验收执行时间: 2026-10-19T20:27 ~ 20:30 +08:00
- 环境: linux, `uv 0.12.5`; pi 工具顶层 shell 里 `python3` 是函数包装 `uv run python` (Python 3.14.7), 脚本子进程里为 `/usr/bin/python3` (Python 3.14.4), 两种解释器下 5 个场景输出与退出码完全一致 (见 `02-scenarios/interpreter-top-level.txt`, `02-scenarios/interpreter-note.txt`)

## 1. 输入核对

| 输入 | 实际路径/标识 | 结论 |
| --- | --- | --- |
| 已确认 PRODUCT.md | `docs/changes/tool-cli/PRODUCT.md`, gherkin 前有 `<!-- confirmed-flow: v1 -->` | 齐全 |
| 目标提交 | `93ba124b07ddc1c9cd845a9f7f4256fc6dee8294` | 齐全 |
| 产物根目录 | `docs/changes/tool-cli/` | 齐全 |

## 2. 版本前提

- `git rev-parse HEAD` = `93ba124b07ddc1c9cd845a9f7f4256fc6dee8294` (`01-version/rev-parse.txt`)
- 已跟踪源码, 配置, 测试相对 HEAD 无未提交改动; 证据目录之外无未跟踪产品文件 (`01-version/status-clean-excluding-evidence.txt` 输出为空; `01-version/status-all-untracked.txt` 中所有未跟踪项都在本轮证据目录内)
- 证据目录外无其他改动; `dist/` 与 `__pycache__/` 由构建命令产生, 已被 `.gitignore` 忽略
- 结论: 版本前提满足

## 3. 证据目录与影响判断

- 证据目录: `docs/changes/tool-cli/evidence-93ba124-20261019/`
- 影响判断: `README.md` 的检查入口为 `python3 -m pytest -q` 与 `bash build.sh`; `build.sh` 只 `compileall tool.py`, `prepare.sh` 只读 `tool.py` 并写 `dist/app.txt`. 证据目录内只有 `.txt/.md/.sh`, 无 `test_*.py`/`*_test.py` 命名, 不会被 pytest 收集, 也不进入构建. 证据目录创建后实跑 `pytest -q` 结果为 `3 passed`, 未见额外收集 (`04-tests/pytest-uv.txt`).
- 结论: 证据可放在仓库内产物根目录, 未外置.

## 4. 必验清单 (共 6 项 = 5 个验收场景 + 1 条审计 BR)

清单来源: `PRODUCT.md` `验收标准` 节全部 5 个场景 (AC-001-1, AC-001-2, AC-002-1, AC-002-2, AC-003-1) + `业务规则` 节标 `(审计)` 的 BR-002.
BR-001 未标 `(审计)`, 其行为判据由 AC-001-1 与 AC-001-2 两个场景逐条承接, 不另立行.

| 编号 | 材料类型 | 实际运行 (命令) 或引用信息 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 默认问候 | 当前观察 | `python3 tool.py greet --name Ada` | stdout 为 `Hello, Ada!` + 行尾换行; stderr 空; 退出码 0 | `02-scenarios/AC-001-1.txt`; 逐字节 `02-scenarios/stdout-bytes.txt` | 2026-10-19T20:27+08:00 @ 93ba124 | 通过 |
| AC-001-2 全大写问候 | 当前观察 | `python3 tool.py greet --name Ada --shout` | stdout 为 `HELLO, ADA!` + 行尾换行; stderr 空; 退出码 0 | `02-scenarios/AC-001-2.txt`; `02-scenarios/stdout-bytes.txt` | 2026-10-19T20:27+08:00 @ 93ba124 | 通过 |
| AC-002-1 统计词数 | 当前观察 | `python3 tool.py count --file notes.txt` (前提: `notes.txt` 内容经 `od -c` 确认为 `alpha beta gamma` + `\n`) | stdout 为 `3` + 行尾换行; stderr 空; 退出码 0 | `02-scenarios/AC-002-1.txt`, `02-scenarios/notes-bytes.txt`, `02-scenarios/stdout-bytes.txt` | 2026-10-19T20:27+08:00 @ 93ba124 | 通过 |
| AC-002-2 统计字符数 | 当前观察 | `python3 tool.py count --file notes.txt --chars` | stdout 为 `17` + 行尾换行; stderr 空; 退出码 0 | `02-scenarios/AC-002-2.txt`, `02-scenarios/stdout-bytes.txt` | 2026-10-19T20:27+08:00 @ 93ba124 | 通过 |
| AC-003-1 JSON 导出 | 当前观察 | `python3 tool.py export --name Ada` | stdout 为 `{"name": "Ada", "greeting": "Hello, Ada!"}` + 行尾换行; stderr 空; 退出码 0 | `02-scenarios/AC-003-1.txt`, `02-scenarios/stdout-bytes.txt` | 2026-10-19T20:27+08:00 @ 93ba124 | 通过 |
| BR-002 不新增依赖, 依赖清单/锁文件/构建材料与上一提交逐项一致 (审计) | 静态材料核对 (非运行行为) | `git diff c6a3745 HEAD -- deps.txt deps.lock build.sh prepare.sh tools/build_manifest.py`; `git rev-parse c6a3745:<f> HEAD:<f>`; `sha256sum` | diff 无输出 (退出码 0); 五个文件在两提交的 blob 哈希各自相同 (`deps.txt bbb5297…`, `deps.lock f5f745d…`, `build.sh 7796246…`, `prepare.sh f6c7c17…`, `tools/build_manifest.py 4414005…`); 验收运行后再次取 sha256 与运行前一致 | `03-audit-br002/diff-deps-build.txt`, `03-audit-br002/hash-*.txt`, `03-audit-br002/post-run-hashes.txt`, `01-version/diff-name-status-prev.txt` | c6a3745..93ba124; 静态核对于 2026-10-19T20:27~20:30+08:00 | 通过 |

## 5. 汇总

- 通过: 6 项 (5 个验收场景 + 1 条审计 BR)
- 失败: 0 项
- 未验证: 0 项
- 整体结论: 本轮 6 项必验项在目标提交 `93ba124` 上均得到当前观察或静态材料核对支撑, 未发现失败项.

## 6. 非产品判据的注明 (不参与产品通过/失败判定)

以下来自 `TECHNICAL.md` 与项目脚本, 只作操作线索与背景, 不作为产品通过条件:

- `uv run --no-project --with pytest python -m pytest -q` → `3 passed in 0.09s`, 退出码 0 (`04-tests/pytest-uv.txt`). 系统 `python3` 环境本身未安装 pytest (`04-tests/pytest.txt` 记录 `No module named pytest`); 上条用临时环境, 未改项目依赖文件. 这是项目自带单元测试结果, 不替代 AC 场景.
- `bash build.sh` 退出码 0, 无输出 (`04-tests/build-sh.txt`); `bash prepare.sh` 输出 `built dist/app.txt`, 退出码 0, `dist/app.txt` 内容为 `tool-cli 1 / commands=greet,count,export / greet-shout=yes` (`04-tests/prepare-sh.txt`, `04-tests/dist-app.txt`).
- `git diff --name-status c6a3745 HEAD` 显示本次只改 `tool.py` 与 `tests/test_tool.py` (`01-version/diff-name-status-prev.txt`). BR-002 审计对象不含测试文件, 故测试文件的增改不构成本轮产品判据.
- 内部代码划分, 模块拆分, 测试接缝设计等属技术评审范围, 本轮不判通过也不判失败.

## 7. 收尾说明

- 除本次证据目录 `docs/changes/tool-cli/evidence-93ba124-20261019/` 的输出外, 源码与 Spec 未变. 证据目录内的文件本身就是相对起始提交 `93ba124` 的新增内容; 构建命令产生的 `dist/` 与 `__pycache__/` 被 `.gitignore` 忽略.
- 本报告由独立验收方出具, 结论仍需用户逐项确认并走正式人工验收; 本报告不宣布正式交付, 也不关闭用户验收.
