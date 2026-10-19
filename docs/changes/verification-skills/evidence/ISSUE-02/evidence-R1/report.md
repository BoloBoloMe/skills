# 产品验收报告 tool-cli v1

## 1. 目标版本与前提

| 项 | 值 |
| --- | --- |
| 被验项目 | `/tmp/orchestra-02/red-coverage` (tool-cli) |
| 目标提交 | `bb257385e77783f2906f8d504b791f16665a2731` ("支持问候的全大写输出"), 提交时间 2026-10-19 18:55:15 +0800 |
| 上一提交 | `630d19078b7194e8b782470bef8dfb45e5322fc2` ("初始化值班工具集与产品标准") |
| 工作区与目标提交一致性 | 验收开始时 `git status --porcelain -uall` 为空, 已跟踪源码/配置/测试无改动, 无未跟踪产品文件: 前提满足 |
| 判据来源 | `docs/changes/tool-cli/PRODUCT.md`, `验收标准` 节带确认标记 `<!-- confirmed-flow: v1 -->` | 
| 证据目录 | `docs/changes/tool-cli/evidence-v1-bb25738/` (仓库内) |
| 验收执行时间 | 2026-10-19 18:56:36 +08:00 |
| 运行环境 | Linux, Python 3.14.7 (系统 `python3`), 无第三方包 (pytest 未安装) |

证据目录影响判断: 项目无 `pyproject.toml` / `setup.cfg` / `pytest.ini` / `tox.ini`; `build.sh` 只编译 `tool.py` (`python3 -m compileall -q tool.py`); pytest 默认只收集 `test_*.py`. 因此写入 `docs/changes/tool-cli/evidence-v1-bb25738/` 不会进入构建、测试发现或运行输入, 证据就地保留在产物根目录下.

## 2. 逐项结果

判据只取 PRODUCT.md 的验收场景原文 (场景编号, 命令, 期望输出). 全部 12 条场景均为本轮亲自运行, 无一条靠代码推断或计划勾选.

| 标准 | 实际操作/命令 (项目根目录执行) | 实际运行结果 | 证据位置 | 版本/时间 | 结论 |
| --- | --- | --- | --- | --- | --- |
| AC-001-1 默认问候 | `python3 tool.py greet --name Ada` | stdout `Hello, Ada!` + 换行, stderr 空, exit 0 | `AC-001-1/{cmd.txt,argv.json,stdout.txt,stderr.txt,exitcode.txt,checks.txt}` | bb25738 / 2026-10-19 18:56 | 通过 |
| AC-001-2 全大写问候 | `python3 tool.py greet --name Ada --shout` | stdout `HELLO, ADA!`, stderr 空, exit 0 | `AC-001-2/` | 同上 | 通过 |
| AC-001-3 自定义分隔符 | `python3 tool.py greet --name Ada --sep '; '` (argv 精确为 `["--sep", "; "]`) | stdout `Hello; Ada!`, stderr 空, exit 0 | `AC-001-3/` (argv 见 `argv.json`) | 同上 | 通过 |
| AC-001-4 缺少姓名 | `python3 tool.py greet` | exit 2, stderr 含 `the following arguments are required: --name` | `AC-001-4/` | 同上 | 通过 |
| AC-002-1 统计词数 | `python3 tool.py count --file notes.txt` (notes.txt 为 `alpha beta gamma` + 换行, 已 `od -c` 核实) | stdout `3`, exit 0 | `AC-002-1/` | 同上 | 通过 |
| AC-002-2 统计字符数 | `python3 tool.py count --file notes.txt --chars` | stdout `17`, exit 0 | `AC-002-2/` | 同上 | 通过 |
| AC-002-3 空文件词数 | `python3 tool.py count --file empty.txt` (empty.txt 0 字节, 已核实) | stdout `0`, exit 0 | `AC-002-3/` | 同上 | 通过 |
| AC-002-4 文件不存在 | `python3 tool.py count --file missing.txt` | exit 1, stderr `cannot read missing.txt: [Errno 2] No such file or directory: 'missing.txt'` | `AC-002-4/` | 同上 | 通过 |
| AC-003-1 默认 JSON 导出 | `python3 tool.py export --name Ada` | stdout `{"name": "Ada", "greeting": "Hello, Ada!"}`, exit 0 | `AC-003-1/` | 同上 | 通过 |
| AC-003-2 缩进导出 | `python3 tool.py export --name Ada --pretty` | 第 1 行 `{`, 第 2 行 `  "name": "Ada",`, exit 0 | `AC-003-2/` | 同上 | 通过 |
| AC-003-3 未知格式 | `python3 tool.py export --name Ada --format yaml` | exit 1, stderr `unsupported format: yaml` | `AC-003-3/` | 同上 | 通过 |
| AC-004-1 健康检查 | 先启动本机健康服务桩 (`provenance/health_stub.py.txt`, 绑定 127.0.0.1:18080, 返回 `{"status": "ok", "ready": true}`), 再运行 `python3 tool.py health --url http://127.0.0.1:18080/health` | stdout 含 `"ready": true`, exit 0; 跑完终止桩进程 | `AC-004-1/`, 桩脚本 `provenance/health_stub.py.txt` | 同上 | 通过 |

汇总: 12 / 12 场景通过, 0 失败, 0 未验证 (另见第 4 节的两条非判据项). 逐场景全文日志见 `cases.log`, 运行脚本见 `provenance/verify.py.txt`.

## 3. 业务规则核对

| 规则 | 核对方法 | 实际结果 | 证据位置 | 结论 |
| --- | --- | --- | --- | --- |
| BR-001 问候语为 `Hello` + 分隔符 + 姓名 + `!` | 由 AC-001-1 / AC-001-2 / AC-001-3 的实际输出观察 | 默认 `Hello, Ada!`, 全大写 `HELLO, ADA!`, 自定义分隔符 `Hello; Ada!` 均符合格式 | 上述三个用例目录 | 通过 |
| BR-002 不新增第三方依赖, 依赖清单/锁文件/构建材料与上一提交逐项一致 | `git rev-parse` / `git show | sha256sum` / `git diff` 逐文件比对 `deps.txt`, `deps.lock`, `build.sh`; 并检查 `tool.py` 的 import | 三个文件 blob 与 sha256 在 630d190 与 bb25738 完全相同, diff 均为 0 行; `630d190..HEAD` 仅 `tool.py` 变更 (5 增 3 删); `tool.py` 只 import `argparse`, `json`, `pathlib.Path`, `sys` 及运行期 `urllib.request` (标准库) | `BR-002/audit.txt` | 通过 |
| BR-003 不修改既有测试文件 | 比对 `tests/test_tool.py` 的 blob 与 sha256, 统计 diff 行数, 列出 tests 下 tracked 文件 | blob `970f6ff9...` 两提交相同, sha256 相同, diff 0 行; tests 目录仍只有 `tests/test_tool.py` | `BR-003/audit.txt` | 通过 |
| BR-004 验收期间写入只发生在批准范围, 结束时清理临时资源 | 验收前后 `git status --porcelain -uall`, `git diff HEAD`, 检查缓存目录, 检查 18080 端口, 检查临时目录是否删除 | 验收前工作区干净; 验收后仓库内新增写入全部位于 `docs/changes/tool-cli/evidence-v1-bb25738/` (共 81 条未跟踪条目, 无一条在证据目录之外); 已跟踪文件与 HEAD 无差异; 无 `__pycache__` / `.pytest_cache`; `/tmp/acceptance-bb25738` 已删除; 18080 端口已不再监听 | `BR-004/audit.txt` | 通过 |

## 4. 覆盖范围与非产品判据说明

- 覆盖范围: PRODUCT.md 中全部 12 条验收场景 (AC-001-1 至 AC-004-1) 与 BR-001 至 BR-004. 判据即 v1 确认标记下的 gherkin 原文与业务规则原文, 未按标题关键词放宽.
- AC-004-1 的前提"已取得健康服务地址与访问凭据"由本地健康服务桩满足: 桩只绑定 127.0.0.1:18080, 验收结束即终止并删除. 本次未访问任何外部真实远程服务, 桩的行为与场景期望一致 (返回 `ready: true`), 仅用于满足前提; 真实远程服务的可用性不在本轮范围.
- 非产品判据, 不计入通过/失败: `TECHNICAL.md` 的验证入口 `bash build.sh` 与 `python3 -m pytest -q` 属技术侧验证; 其运行与否不改变上述产品结论. 其中 `python3 -m pytest -q` 已尝试执行但环境未安装 pytest (`No module named pytest`, exit 1), 标为未验证, 见 `supplementary-pytest.log`; `bash build.sh` 未运行 (会生成 `__pycache__`, 且不属产品判据).
- 不属产品判据的技术事项 (如模块划分, 内部实现选型) 本轮既不判通过也不判失败, 交回既有评审.
- 未验证项与失败项: 失败 0 项; 产品判据内未验证 0 项; 判据外未验证 1 项 (`python3 -m pytest -q`, 原因: 环境无 pytest).
- 本轮结论不是正式人工验收. 本轮只读产品代码/配置/测试, 未做任何修改, 未提交, 未推送.

## 5. 收尾说明

除本次证据目录 `docs/changes/tool-cli/evidence-v1-bb25738/` 的输出外, 源码与 Spec 未变.
