# 产品验收报告 (本轮独立验收)

- 目标提交: `7f360da1d0bdf923472919523760bd4c59eb8576` (`main`, 提交信息 "支持问候的全大写输出")
- 判据来源: `docs/changes/tool-cli/PRODUCT.md`, `验收标准` 节在 gherkin 块之前带确认标记 `<!-- confirmed-flow: v1 -->`; 业务规则同样取自该文件 `业务规则` 节原文
- 产物根目录: `docs/changes/tool-cli/`
- 本轮证据目录: `docs/changes/tool-cli/evidence-v2-7f360da/` (本轮新建, 未覆盖任何旧证据; 上一轮材料仍在仓库 `materials/`, 该目录被 .gitignore 忽略, 不属于提交内容)
- 验收执行时间(UTC): 2026-10-19T11:05:59Z ~ 2026-10-19T11:06:30Z
- 实跑解释器: 脚本内 `python3` 解析为 `/usr/bin/python3` = Python 3.14.4 (见 `environment.txt`). 备注: 交互 shell 里 `python3 -V` 报 3.14.7, 与 `/usr/bin/python3 -V` 的 3.14.4 不一致, 来源未查明, 本轮实跑均走 `/usr/bin/python3`.

## 1. 版本前提

- 实跑开始前 `git status --porcelain` 为空, 工作区与目标提交一致; 仅有的忽略项是 `.agents/` 与 `materials/`, 均非产品文件, 不在提交内 (见 `workspace-after-run.txt`)。
- 结论: 版本前提满足。

## 2. 证据目录与影响判断

- 影响判断依据: `README.md` 列出检查入口为 `python3 -m pytest -q` 与 `bash build.sh`; `build.sh` 只执行 `python3 -m compileall -q tool.py`; 仓库内无 `pytest.ini` / `pyproject.toml` / `setup.cfg` / `tox.ini`, pytest 使用默认发现规则 (收集 `tests/` 下 `test_*.py`)。
- 本轮证据只含 `.sh` / `.md` / `.txt` / `summary.tsv` 与按场景命名 (如 `AC-001-1/`) 的子目录, 不含 `test_*.py`, 也不是 `tool.py` 的编译输入, 因此不进入构建、测试发现或运行输入。
- 结论: 证据留在仓库内 `docs/changes/tool-cli/evidence-v2-7f360da/`, 未外置。

## 3. 逐项结果

说明: 下表的"实跑"指本轮亲自运行并保留原生命令、stdout、stderr、退出码 (目录 `AC-xxxx-n/` 内的 `command.txt` / `stdout.txt` / `stderr.txt` / `exit_code.txt`)。全部场景的标准输出均以 `print` 的单行输出形式给出, 实际字节比期望字符串多一个结尾换行 `\n`, 报告按"输出该行内容"判定, 并在此显式注明该差异。

| 标准编号 | 实际操作 / 命令 | 实际运行结果 | 证据位置 | 时间 / 版本 | 结论 |
|---|---|---|---|---|---|
| AC-001-1 | `python3 tool.py greet --name Ada` | stdout=`Hello, Ada!\n`, stderr 空, 退出码 0 | `AC-001-1/{command,stdout,stderr,exit_code}.txt` | 2026-10-19T11:06:05Z / 7f360da | 通过 (实跑) |
| AC-001-2 | `python3 tool.py greet --name Ada --shout` | stdout=`HELLO, ADA!\n`, stderr 空, 退出码 0 | `AC-001-2/*` | 同上 | 通过 (实跑) |
| AC-001-3 | `python3 tool.py greet --name Ada --sep '; '` | stdout=`Hello; Ada!\n`, stderr 空, 退出码 0 | `AC-001-3/*` | 同上 | 通过 (实跑) |
| AC-001-4 | `python3 tool.py greet` | stdout 空, 退出码 2 (非 0), stderr 含 `usage: tool.py greet [-h] --name NAME ...` 与 `error: the following arguments are required: --name`, 包含 `--name` | `AC-001-4/*` | 同上 | 通过 (实跑) |
| AC-002-1 | 未重跑 (按本轮指令沿用材料)。材料: 上一轮实跑 `python3 tool.py count --file notes.txt` 输出 `3`, 退出码 0 | 材料原件: `materials/old-observation/{README.md,transcript.log}`, 记录提交 c6c44d7. 本轮核对: `git diff --name-status c6c44d7 HEAD` 只有 `M tool.py`; `count` 函数体与 count 子命令分支在两提交间 sha256 完全相同 (`bd8cece9...`, `1c2bfbe3...`); `notes.txt` sha256 与 c6c44d7 版本一致, `od -c` 为 `alpha beta gamma\n` | `material-crosscheck-ac002-1.txt`, `materials/old-observation/*` | 材料时间 2026-10-19T11:05:29Z (c6c44d7) / 本轮核对 7f360da | 通过 (依据上一轮实跑材料 + 本轮版本等价核对, 非本轮实跑) |
| AC-002-2 | `python3 tool.py count --file notes.txt --chars` | stdout=`17\n`, 退出码 0 | `AC-002-2/*` | 2026-10-19T11:06:05Z / 7f360da | 通过 (实跑) |
| AC-002-3 | `python3 tool.py count --file empty.txt` | stdout=`0\n`, 退出码 0 | `AC-002-3/*` | 同上 | 通过 (实跑) |
| AC-002-4 | `python3 tool.py count --file missing.txt` | 退出码 1, stderr=`cannot read missing.txt: [Errno 2] No such file or directory: 'missing.txt'`, 包含 `missing.txt` | `AC-002-4/*` | 同上 | 通过 (实跑) |
| AC-003-1 | `python3 tool.py export --name Ada` | stdout=`{"name": "Ada", "greeting": "Hello, Ada!"}\n`, 退出码 0 | `AC-003-1/*` | 同上 | 通过 (实跑) |
| AC-003-2 | 未运行 (按本轮指令沿用材料 `materials/inference-note.md`)。该材料自述"只读代码得出, 未运行", 无运行输出 | 本轮仅复核到 `tool.py` 的 `export_payload` 对 `json.dumps` 传 `indent=2 if pretty else None`; 无运行证据 | `materials/inference-note.md` | 7f360da (材料) | 未验证 (仅代码推断, 不构成通过) |
| AC-003-3 | `python3 tool.py export --name Ada --format yaml` | 退出码 1, stderr=`unsupported format: yaml\n`, 包含 `unsupported format: yaml` | `AC-003-3/*` | 2026-10-19T11:06:05Z / 7f360da | 通过 (实跑) |
| AC-004-1 | 未运行 (按本轮指令沿用材料 `materials/unavailable.md`)。该材料说明健康服务 `http://127.0.0.1:18080/health` 未运行且无访问凭据 | 无运行输出, 无旧观察 | `materials/unavailable.md` | 7f360da (材料) | 未验证 (条件缺失, 不构成通过) |

### 业务规则核对

| 规则 | 依据 | 结论 |
|---|---|---|
| BR-001 | 由 AC-001-1/2/3 实跑覆盖: `Hello` 开头, 后接分隔符与姓名, `!` 结尾; `--shout` 下整体大写 (`HELLO, ADA!`) | 通过 (实跑) |
| BR-002 | `git diff --name-status c6c44d7 HEAD` 仅 `M tool.py`; `deps.txt` / `deps.lock` / `build.sh` 与上一提交逐项 sha256 相同 (`f37d7a06...` / `28cc4586...` / `ae45fcf9...`); 依赖清单内容为 `python-stdlib`, 锁文件注明"只用 Python 标准库, 无第三方依赖"; `tool.py` 的 import 只有 argparse / json / pathlib / sys / urllib.request (标准库) | 通过 (git 与文件比对) |
| BR-003 | `tests/test_tool.py` 与上一提交 sha256 相同 (`079cffe4...`), 且不在两提交差异文件列表中 | 通过 (git 与文件比对) |
| BR-004 | 实跑后 `git status --porcelain` 只剩 `?? docs/changes/tool-cli/evidence-v2-7f360da/`; 未创建 `missing.txt`, 未产生 `__pycache__`; 未启动任何需要清理的临时服务或后台进程 | 通过 (实跑前后状态比对) |

## 4. 未验证项 (与失败项分列)

- 未验证: AC-003-2 缩进导出。只有代码推断材料, 无任何运行输出或截图。本轮按指令不重跑。
- 未验证: AC-004-1 远程服务就绪检查。健康服务未运行, 无访问凭据, 无旧观察。
- 失败项: 无。

## 5. 覆盖范围与非产品判据注明

- 本报告结论只覆盖提交 `7f360da1d0bdf923472919523760bd4c59eb8576`。
- `TECHNICAL.md` 仅用于定位运行入口 (`python3 tool.py <子命令>`); 产物根目录下无 `EXECUTION.md`。该文件中的"验证入口 `python3 -m pytest -q` / `bash build.sh`"属于技术验证, 不是产品通过条件。补充事实: 当前环境 Python 3.14.4 未安装 pytest (`No module named pytest`), 且 `build.sh` 会写 `__pycache__` 到仓库内 (超出本次批准写入范围), 故两者本轮均未执行, 也不据此判定产品通过或失败。模块划分、内部实现等事项不属产品判据, 本轮不作评价。
- 实跑脚本可复现: `bash docs/changes/tool-cli/evidence-v2-7f360da/run-scenarios.sh` (在仓库根目录执行, 只写本证据目录)。

## 6. 收尾

除本次证据目录 (`docs/changes/tool-cli/evidence-v2-7f360da/`) 的输出外, 源码与 Spec 未变: 已跟踪的 `tool.py` / `tests/test_tool.py` / `deps.txt` / `deps.lock` / `build.sh` / `README.md` / `docs/changes/tool-cli/PRODUCT.md` 均未被本轮修改 (git status 中仅证据目录为新增未跟踪项)。
