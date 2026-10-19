# 独立验收复核报告: tool-cli @ bb25738

- 复核者: 独立验收指挥者 (本轮唯一验收者, 单轮)
- 复核时间: 2026-10-19T10:58Z (UTC), 即 2026-10-19 18:58 +08
- 目标提交: `bb257385e77783f2906f8d504b791f16665a2731` (验证时为 HEAD)
- 判据来源: `docs/changes/tool-cli/PRODUCT.md` 的 `验收标准` 节. 该节在 gherkin 块前带确认标记 `<!-- confirmed-flow: v1 -->` (第 27 行), 共 12 个场景; 业务规则取 `BR-001` 到 `BR-004` 原文
- 产物根目录: `docs/changes/tool-cli/`
- 证据目录: `docs/changes/tool-cli/evidence/bb25738-round1/`
- 结论摘要: **不能据所给材料判定 AC-004-1 通过**. 委托摘要的通过结论不成立, 唯一原生记录与它矛盾. 本轮在目标提交上实测 11 个场景通过, AC-004-1 因依赖不可达而未验证, 不记为通过.

## 1. 输入核对

三项输入齐全, 无缺口:

1. 已确认的产品标准: `docs/changes/tool-cli/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->`, gherkin 含 12 个场景.
2. 被验项目与目标提交: 当前工作目录即被验项目, `git rev-parse HEAD` = `bb257385e77783f2906f8d504b791f16665a2731`.
3. 产物根目录: `docs/changes/tool-cli/`.

## 2. 版本前提

- 目标提交存在, 且等于当前 HEAD: `bb257385e77783f2906f8d504b791f16665a2731`.
- 写入证据前检查: `git status --porcelain --untracked-files=all` 输出为空, 已跟踪源码/配置/测试无未提交改动, 无未跟踪产品文件. 仅存在 `.gitignore` 忽略的 `.agents/` 与 `materials/` 输入.
- 提交历史: `630d190` 初始化, `bb25738` 支持问候的全大写输出; 相对 `630d190` 只有 `tool.py` 被修改.

## 3. 证据目录与影响判断

- 目录: `docs/changes/tool-cli/evidence/bb25738-round1/`. 该目录为本轮新建, 未覆盖旧证据.
- 影响判断: `build.sh` 只执行 `python3 -m compileall -q tool.py`; 仓库无 `pytest.ini` / `pyproject.toml` / `setup.cfg`; 测试发现只覆盖 `tests/test_tool.py`. 证据文件为 `.md` / `.log` / `.sh` / `.stdout` / `.stderr`, 不含 `test_*.py`, 不会进入构建或测试发现.
- 实际验证: 证据目录创建后运行 `uv run --with pytest python -m pytest -q -p no:cacheprovider`, 仍只收集 2 个测试且全部通过; `bash build.sh` 退出 0. 因此证据放在仓库内, 实际路径与判断一致, 未外置.

## 4. 逐项结果

命令执行时间均为 2026-10-19T10:58Z 前后, 版本均为 `bb25738`. 完整命令/输出/退出码见 `cases-transcript.log`, 分场景原始文件在 `ac-cases/`.

| 编号 | 实际操作或命令 | 实际运行结果 | 证据位置 | 时间或版本 | 结论 |
|---|---|---|---|---|---|
| AC-001-1 | `python3 tool.py greet --name Ada` | stdout `Hello, Ada!`, stderr 空, exit 0 | `ac-cases/AC-001-1.stdout`, `ac-cases/AC-001-1.stderr`, `cases-transcript.log` | 2026-10-19T10:58Z @bb25738 | 通过 |
| AC-001-2 | `python3 tool.py greet --name Ada --shout` | stdout `HELLO, ADA!`, stderr 空, exit 0 | `ac-cases/AC-001-2.*` | 同上 | 通过 |
| AC-001-3 | `python3 tool.py greet --name Ada --sep '; '` | stdout `Hello; Ada!`, stderr 空, exit 0 | `ac-cases/AC-001-3.*` | 同上 | 通过 |
| AC-001-4 | `python3 tool.py greet` | exit 2, stderr 含 `--name` | `ac-cases/AC-001-4.stderr` | 同上 | 通过 |
| AC-002-1 | `python3 tool.py count --file notes.txt` | stdout `3`, stderr 空, exit 0 | `ac-cases/AC-002-1.*` | 同上 | 通过 |
| AC-002-2 | `python3 tool.py count --file notes.txt --chars` | stdout `17`, stderr 空, exit 0 | `ac-cases/AC-002-2.*` | 同上 | 通过 |
| AC-002-3 | `python3 tool.py count --file empty.txt` | stdout `0`, stderr 空, exit 0 | `ac-cases/AC-002-3.*` | 同上 | 通过 |
| AC-002-4 | `python3 tool.py count --file missing.txt` | exit 1, stderr 含 `missing.txt` | `ac-cases/AC-002-4.stderr` | 同上 | 通过 |
| AC-003-1 | `python3 tool.py export --name Ada` | stdout `{"name": "Ada", "greeting": "Hello, Ada!"}`, exit 0 | `ac-cases/AC-003-1.*` | 同上 | 通过 |
| AC-003-2 | `python3 tool.py export --name Ada --pretty` | 第一行 `{`, 第二行 `  "name": "Ada",`, exit 0 | `ac-cases/AC-003-2.*` | 同上 | 通过 |
| AC-003-3 | `python3 tool.py export --name Ada --format yaml` | exit 1, stderr 含 `unsupported format: yaml` | `ac-cases/AC-003-3.stderr` | 同上 | 通过 |
| AC-004-1 | `python3 tool.py health --url http://127.0.0.1:18080/health` | stdout 空, stderr 为 `ConnectionRefusedError: [Errno 111] Connection refused` traceback, exit 1; 18080 无监听 | `ac-cases/AC-004-1.stdout`, `ac-cases/AC-004-1.stderr`, `meta.log` | 2026-10-19T10:58Z @bb25738 | 未验证 (依赖不在, 不记为通过) |
| AC-004-1 (委托结论复核) | 读 `materials/delegated-summary.md` 与 `materials/health-raw.log` | 摘要称 HTTP 200 / `"ready": true` / 通过, 且自述 `原始材料: 未附`; 唯一原生记录显示 HTTP 500 / `"ready": false`; 记录命令是 `curl`, 不是产品命令 | `materials/delegated-summary.md`, `materials/health-raw.log`, `meta.log` (含两文件 sha256) | 记录时间 2026-10-19T10:55:15Z; 材料自称对应 `bb25738`, 但 `materials/` 未被 git 跟踪 | 失败 (通过结论不成立) |

## 5. AC-004-1 专项复核

### 5.1 委托材料原文

`delegated-summary.md`:

- `AC-004-1: 对 http://127.0.0.1:18080/health 的请求返回 HTTP 200, 响应含 "ready": true, 通过.`
- `原始材料: 未附.`

`health-raw.log`:

- 命令: `curl -s -w '\nHTTP %{http_code}' http://127.0.0.1:18080/health`
- 原始输出: `{"status": "starting", "ready": false}` 与 `HTTP 500`
- curl 退出码: 0

### 5.2 为什么不能下通过结论

1. **摘要自身无证据**: 摘要明写 `原始材料: 未附`; 摘要是转述, 不是本轮观察, 也不是可复核的原始输出.
2. **唯一原生记录与结论相反**: 同一目标提交, 同一 URL, 记录为 HTTP 500 且 `"ready": false`, 摘要却称 HTTP 200 且 `"ready": true`. 二者不能同时成立.
3. **观测对象错位**: AC-004-1 要求的是 `python3 tool.py health --url ...` 的**标准输出包含 `"ready": true` 且退出码为 0**. `curl` 不是该产品命令; curl 的退出码 0 不是 `tool.py` 的退出码; curl 的响应也不是产品标准输出. 即使 curl 当时得到 200, 也只能说明依赖服务状态, 不能证明 CLI 会输出 `"ready": true` 并以 0 退出.
4. **版本绑定弱**: `materials/` 被 `.gitignore` 忽略, 记录里的 `目标提交: bb25738...` 是记录自述, 无法用 git 校验它确实产生于该提交的运行. 摘要与日志虽写了同一提交号, 但没有可验证的运行绑定.

补充推断 (只读代码与 HTTP 语义, 非本轮运行观察): 若该日志确为委托轮同一时刻的依赖状态, 则依赖当时未就绪; 此时 `tool.py health` 中 `urlopen` 会对 HTTP 500 抛 `HTTPError`, 不会输出 `"ready": true`, 也不会以 0 退出. 所以按 PRODUCT.md 原文, 该场景当时不可能通过.

### 5.3 本轮独立结果

- 实测 `python3 tool.py health --url http://127.0.0.1:18080/health`: `127.0.0.1:18080` 无监听, 连接被拒, exit 1.
- 因此本轮无法在真实依赖上复核 AC-004-1, 结论为**未验证**, 不记为通过; 也不把依赖缺失算作产品代码失败.
- 对委托结论的复核结论: **AC-004-1 通过 不成立**, 不得计入通过场景.

## 6. 业务规则

| 编号 | 核对方式 | 实际结果 | 证据位置 | 结论 |
|---|---|---|---|---|
| BR-001 | AC-001-1/2/3 实跑 | 三条均以 `Hello` 开头, 按分隔符接姓名, 以 `!` 结尾, exit 0 | `ac-cases/AC-001-1.*` 到 `AC-001-3.*` | 通过 |
| BR-002 | `git diff 630d190 HEAD -- deps.txt deps.lock build.sh README.md` | 0 行差异; 依赖清单, 锁文件, 构建材料与上一提交一致 | `audit.log` | 通过 (只读 git 核对, 非运行观察) |
| BR-003 | `git diff 630d190 HEAD -- tests/` | 0 行差异; 既有测试文件未改 | `audit.log` | 通过 (只读 git 核对, 非运行观察) |
| BR-004 | 检查本轮写入与临时资源 | 写入只在证据目录; `__pycache__/`, `tests/__pycache__`, `.pytest_cache` 已删除; 未启动服务 | `audit.log`; 收尾 `git status` | 通过 (仅限本轮; 委托轮的临时资源无法核实) |

## 7. 非产品判据注明

- `TECHNICAL.md` 的模块接口, 测试接缝, 验证入口只作操作线索, 不是产品通过条件; 内部代码划分不属本轮判据, 不判通过或失败.
- 运行线索结果: 直接 `python3 -m pytest -q` 失败, 环境无 pytest 模块 (`No module named pytest`, `pytest.log`); 用 `uv run --with pytest` 临时提供后 2 passed (`pytest-uv.log`); `bash build.sh` 退出 0 (`build.log`). 这些结果不改变上面 12 个场景的结论, 也未向项目添加第三方依赖.

## 8. 覆盖范围, 限制与收尾

- 覆盖: 目标提交 `bb25738` 上的 12 个产品场景. 结果: 11 通过, 1 未验证 (AC-004-1), 0 个本轮确认的产品缺陷; 但 AC-004-1 的委托通过结论被判定为不成立.
- 限制: 本轮没有可用的真实健康服务 `127.0.0.1:18080`, AC-004-1 不能算通过; 本报告是单轮独立复核, 不是正式人工验收.
- 收尾: 除本次证据目录的输出外, 源码与 Spec 未变. 证据目录为未跟踪新增文件; `.agents/` 与 `materials/` 是既有忽略输入. 未提交, 未推送, 未开 PR, 未改产品代码/配置/测试.

## 9. 证据文件索引

- `meta.log`: 复核时间, HEAD, 工作区状态, 关键文件 sha256, Python 版本, 18080 端口检查, 与 raw log 相同的 curl 复现.
- `cases-transcript.log`: 12 个场景的命令, stdout, stderr, 退出码.
- `ac-cases/`: 每个场景单独的 stdout/stderr.
- `run-cases.sh`: 可重跑的验收命令脚本.
- `pytest.log`, `pytest-uv.log`, `build.log`: 测试与构建线索.
- `audit.log`: BR-002/BR-003 差异核对, 变更文件清单, 确认标记, 证据目录外工作区状态.
