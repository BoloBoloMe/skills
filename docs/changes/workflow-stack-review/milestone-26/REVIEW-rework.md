# SWT-M26 返工复审 (REWORK-01 七项)

## 0 审核信息

| 项 | 值 |
| --- | --- |
| 任务标识 | SWT-M26-REVIEW-REWORK |
| 轴 | 返工复审 (只核 7 项是否修好 + 查回归, 不改代码) |
| 身份 | 未参与实现与本次修复 |
| 工作树 / 分支 | `/home/bolo/Workspace/refactor-skill-around-verification.worktrees/REVIEW-rew01` / `review/rew01` |
| 基点 | `6856e15` (返工已合并的集成提交) |
| 返工范围 | `git diff 7e23e1a...HEAD`; 提交 `6856e15 6453f60 2ed275d ea27c61 93945e0` |
| 返工单 | `issues/REWORK-01.md` |
| 实跑环境 | 容器内 (无 podman, 无出网), `PYTEST_XDIST_WORKER=gw0` 前缀, 不占 8090, 未碰真实 `~/.agents` (探针全用临时 `CODEMAP_RUNTIME_DIR` 与临时 `HOME`) |
| 我的临时证据 | `/tmp/rw01/` (`probe.py`, `probe2.py`, `d1*.py`, `h1*.py`, `codes.py`) |

逐项结论: **7 项全部已修好**, 其中第 2 项与第 4 项附带覆盖范围收窄 (见 2.2 / 2.4 与第 5 节).
回归发现 7 条 (P-1..P-7), 其中最严重一条是 P-1: A-1 新用例把"本机没有 podman"的前提硬编码成 `PATH=/usr/bin:/bin`, 在 podman 装在 `/usr/bin` 的宿主上会红.
未发现产品行为的功能性回归: 错误码集合 14 个与返工前逐一相同, `--json` 字段集合唯一变化是 `previous_url` 在缺地址形态变为可选 (返工单第 3 项明确授权).

## 1 我自己实跑的入口与结果

```
PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests -q   -> 78 passed in 18.69s (rc=0)
PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q                -> 943 tests collected
uv run python general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md -> OK
PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py  -> 1 passed
printf > workflow/codebase-map/scripts/_review_probe.py; ./tests/run --fast        -> 受影响套件: workflow/codebase-map/tests; 78 passed
  (untracked 探针文件用后立即删除, 工作树已复原干净)
```

78 passed 与 943 collected 都可复现, 与返工单自报一致 (940 基线 + 3 新增用例). 无 skipped, 无 failed, 无残留 `_serve-daemon` 进程. 我把三个断点的手工探针另写在 `/tmp/rw01/probe.py`: 自己起 CLI 子进程 + 自造 state.json, 不 import 测试 harness, 结果见下.

## 2 逐项结论

### 2.1 A-1 `podman_missing` 文案 — 已修好

- 代码依据: `scripts/codebase-map.py:95` message 为 `"本机没有 podman, 无法运行官方分析镜像."`, hint 保留 `先安装 podman 并确认 podman --version 可用, 再重试.`
- 我的实测 (真实 CLI 子进程, 不是函数返回值):
  `PATH=/usr/bin:/bin unshare -m -r /bin/sh -c 'mount -t tmpfs tmpfs /run && exec <python> <cli> build <dir> --json'`
  -> `{"success": false, "command": "build", "error": {"code": "podman_missing", "message": "本机没有 podman, ...", "hint": "..."}}`, 退出码 1.
- 新用例 `tests/test_cli_output_shape.py:64` 确实走 `subprocess.run` 起真实 CLI (`CLI_SCRIPT`), 断言 `error.code`、message 含"本机没有 podman"、退出码 1、hint 非空; 不是只测函数返回值.
- 副作用: 该用例的可移植性有缺陷, 见 P-1 / P-2.

### 2.2 A-2 换端口文案"旧地址已失效" — 已修好 (自动化只覆盖 JSON 形态)

- 代码依据: `scripts/codemap_service.py:470-488`. 有 `previous_url` 时 note 为
  `"<启动 note> 换端口: 旧地址已失效 (原 URL <previous_url>), 现按端口 <N> 提供."`;
  本次也解析不出地址时 note 为 `"<启动 note> 换端口: 旧地址已失效, 现按端口 <N> 提供."`.
  两种形态都含连续短语"旧地址已失效".
- 两种输出形态都覆盖 (我实测, 见 `/tmp/rw01/probe.py` 输出):
  - `--json`: `"note": "... 换端口: 旧地址已失效 (原 URL http://203.0.113.77:46437/), 现按端口 57277 提供."`
  - 人类可读: `note: "状态记录显示服务未在运行, 按目标端口启动. 换端口: 旧地址已失效 (原 URL ...)"`, 因为 `cmc.human_summary` (`codemap_common.py:258`) 逐字段铺开同一份结果 dict.
- 不换端口时不出现: 实测 `serve` 不带 `--port` 走复用分支, note 为 `"已有存活实例 (探活三步全过), 直接复用, 不起新进程."`, 无 `port_changed`/`previous_url`; 用例 `test_tc_05_04:220/239`、`test_tc_04_04:157` 也各自断言.
- 缺口: 自动化断言只在 JSON dict 上 (`"旧地址已失效" in second["note"]`), 人类可读形态没有对应用例; 两形态靠 `human_summary` 的结构保证, 属"可实现层推测, 未观察" (归 P-7).

### 2.3 C-1 `last_url`/`previous_url` 用真实交付 URL — 已修好

- 写入条件 (读码确认, `codemap_service.py:441-451`):
  `host = resolved.get("url_host")`, `from_record = resolved.get("address_source") == cmc.ADDRESS_SOURCE_RECORD`;
  `last_url = f"http://{host}:{target_port}/"` 仅当 `host is not None and from_record`, 否则 `_loopback_url(target_port)`.
  即 `--address` 来源与缺地址来源都不把地址写进 state, 只有"已确认记录文件"来源才写, 且写的是交付 URL 而不是裸地址.
- 换端口取值顺序 (`:470-488`): 旧 `last_url` 是交付 URL (`_is_delivery_url`, `:94`, 判 host 非 `127.0.0.1`/`localhost`/None) -> 直接用; 否则 `host + 旧端口` 拼; 都没有 -> 省略 `previous_url`, 只留失效文案.
- 我的实测 (`/tmp/rw01/probe.py`, record 来源 = 临时 HOME 里 `lan-address` = `203.0.113.77`):
  - 首次 `serve`: `url = http://203.0.113.77:39111/`, `state.last_url = http://203.0.113.77:39111/` (与交付 URL 逐字相同).
  - `stop` 后 `serve --port 46437`: `port_changed = true`, `previous_url = http://203.0.113.77:39111/`, note 含失效文案.
  - `--address 198.51.100.9` 来源: 交付 `url = http://198.51.100.9:59967/`, 而 `state.last_url = http://127.0.0.1:59967/`, `198.51.100.9` 在 state.json 文本里 **不出现**; 换端口 `previous_url = http://198.51.100.9:59967/` (由本次解析地址 + 旧端口拼).
  - 缺地址来源: `address_missing` + candidates, `last_url` 保持回环留痕, 换端口 `previous_url` 省略、note 仍写失效.
  - 跨场景: 上次交付过局域网 URL、这次记录文件被删 -> `previous_url` 仍是旧交付 URL, 新 `last_url` 回退回环留痕 (符合"有旧交付地址就报它").
- state.json 无裸地址字段: 实测 state 键集合仍为 13 个 `version/port/last_port/last_url/pid/bind/started_at/stopped_at/command_path/serve_root/log_path/runtime_dir/data_keys`, 没有 address 类字段; `--address` 值不入盘也有既有用例 `test_delivery_output.py:164-165` 断言.
- 两条被改期望值的既有用例现在断言什么 (不是自己想当然的值, 而是分支语义 + 实测对照):
  - `test_serve_lifecycle.py:113 test_tc_04_03`: fixture 现在给空 HOME (无 `lan-address`), 走缺地址分支 -> 断言 `"previous_url" not in second`、note 含失效文案、`state.last_url == http://127.0.0.1:<新端口>/`. 旧断言 (`previous_url == 停机前回环 last_url`) 被换成分支语义, 不是换一个新回环值.
  - `test_delivery_output.py:201 test_tc_05_04`: record 来源 -> 断言 `state.last_url == first["url"]` (与真实交付输出对照)、`previous_url == url_before_stop` 且不含 `127.0.0.1`/`localhost`、note 含失效文案.
  - 新增 `test_delivery_output.py:243`: 独立对照 `previous_url == first["url"]`, 把期望锚在交付输出上, 不是锚在实现写出的 state 上. 综上不是"把回环换成另一个自己想当然的值".

### 2.4 D-1 恒真断言 — 已修好 (检查范围收窄到文档表格, 见 P-6)

- 代码依据: `tests/test_skill_docs.py:31 collect_code_error_codes` 用 ast 静态解析 `scripts/*.py` 的 `error_result(...)` 第 2 位置参与 `_AnalyzeError(...)` 第 1 位置参 (只收字符串字面量); `:61 doc_error_codes` 从文档表格首列提取反引号码; `:171` 主用例断言 `doc_codes - code_codes` 为空 + 关键 6 码子集; 手抄 `KNOWN_ERROR_CODES` 已删.
- 我的负向检验 (调同一套函数, 等价于文档漂移):
  - 假清单文本 `| zebra_wax |` -> `unknown = {'zebra_wax'}` (守卫会失败).
  - 真 SKILL.md 末尾追加 `| totally_fabricated_code |` -> `unknown = {'totally_fabricated_code'}`.
  - 现状实测: 代码侧收集 14 个码, 文档表格提取 14 个码, 双向差集都为空 (即既无未知码, 也无"代码有文档漏"的表格项).
  - 动态传递的两处 (返工单自称) 我点名核实: `codemap_analyze.py:810 exc.code`、`codemap_service.py:420 failure.get("code", ...)`; 其码值在别处以字面量出现 (前者来自 `_AnalyzeError` 字面量, 后者来自 `_write_startup_error("port_in_use"/"internal_error")`), 所以全集不缺.
- 新守卫会不会因文档漂移而失败: 会, 前提是漂移出现在**失败出口表格首列**; 正文里的编造码不再被抓 (P-6), collector 也不含 `no_confirmed_address` 这类不经 `error_result` 产生的码 (把它写进表格会假红).

### 2.5 H-1 测试映射登记 — 已修好

- 双向一致: `tests/README.md:51` 一行 (`workflow/codebase-map/scripts/` 或 `workflow/codebase-map/tests/` -> `workflow/codebase-map/tests/`, 快层) 与 `tests/run:35-36` 两条 RULES 一一对应, 顺序是"先 README 后 run", 与 README 头注释纪律一致.
- 选择函数实验 (我自己 exec `tests/run` 调 `select_suites`):
  `workflow/codebase-map/scripts/codemap_analyze.py` / `.../codebase-map.py` / `.../tests/test_serve_lifecycle.py` / `.../tests/codemap_service_helpers.py` / `.../scripts/codemap_common.py` -> 均 `['workflow/codebase-map/tests']`;
  `workflow/use-sandbox-worktree/scripts/swt.py`、`general/present/scripts/x.py` 命中各自原有套件, 未被新规则遮蔽; `pytest.ini`/`tests/conftest.py` 仍走 GLOBAL; 近名前缀 `workflow/codebase-map/scriptsX/foo.py` 不命中 (无过度匹配).
- 端到端: 在工作树放一个 untracked 脚本再 `./tests/run --fast`, 输出 `受影响套件: workflow/codebase-map/tests` 并 `78 passed`.
- 缺口: `workflow/codebase-map/SKILL.md` 与 `README.md` 的改动仍不命中任何套件 (其文档契约用例在 `test_skill_docs.py` 里), 属旧缺口, 返工单只要求登记 scripts/tests, 未扩 (P-5).

### 2.6 H-2 m21 手册过期陈述 — 已修好

- 代码依据 `workflow/codebase-map/README.md`:
  `:3` 改为"v1 三子命令的唯一操作入口是 SKILL.md, 本文只保留汉化构建链与布局铺设手册";
  `:6` 改为"已由 v1 实现, 用法见 SKILL.md";
  `:16` 归属列改为"v1 服务 (milestone-26) 创建与维护";
  `:47` 临时 `python3 -m http.server 8090` 配方删除线 + **已作废, 勿用** + 明确的 `port_in_use` 后果说明;
  `:50` 节标题改为"v1 已封装为 build 子命令".
- 过期陈述改净: 全文 grep `就位/临时/唯一操作入口` 只剩 `:47` 那句"作废"说明本身与 `:28` 的"临时静态服务"(汉化冒烟步骤内部, 与 8090 无关, 不是过期陈述).
- 汉化链正文与决策标号保留: 文件仍 97 行; 决策/事实标号计数与 `7e23e1a` 版逐个相同 (D001/D003/D008/D010/D013/D014×2/D015/D016/D021×2/D022/D023×3/D024×2/D025×2/D027/D030×2/F001×2/F002/F011/F012/F014/U002/U003/U004), `tools/` 与 `i18n/` 未动.
- SKILL.md 侧口径对得上: `:108` "README.md: 该链的操作手册"、`:110` "细节见 README.md" 与新 README 的定位一致.

### 2.7 B-1/B-2 收窄 — 已修好

- `run_update_data_keys`: 全仓 grep (含 tests 与 docs) 只剩返工单/两份评审报告里作为历史叙述的提及, 代码零定义零调用; `codemap_service.py:8` docstring 已改为"对外函数只有 run_serve / run_stop".
- `expected_sha256`: 全仓 grep 只剩 docs 里的历史叙述; `codemap_analyze.py:205` 已是单参 `verify_frontend_zip(zip_path)`, `:208-210` docstring 改为"期望值恒用 FRONTEND_ZIP_SHA256 常量, 测试预置时 monkeypatch"; 两处调用 (`:241`、`:287`) 都不传参; 测试仍用 `monkeypatch.setattr(cmc, "FRONTEND_ZIP_SHA256", ...)` (`test_analyze_pipeline.py:67`, `test_gate_stats_and_copies.py:99`), 行为等价 (常量仍在调用时读取), 78 passed 佐证.
- 允许范围核对: diff 触及文件恰在返工单"允许范围"内 (`scripts/codebase-map.py`, `codemap_service.py`, `codemap_analyze.py`, `tests/`, `workflow/codebase-map/README.md`, 仓库根 `tests/README.md` 与 `tests/run`), 未动 PRODUCT/TECHNICAL/DECISIONS/EXECUTION、门禁、m21 `tools/`/`i18n/`.

## 3 回归检查 (与首轮评审不同的部分)

### 3.1 `--json` 字段语义与错误码集合

- 错误码集合未变: 我对 `7e23e1a` 与 `HEAD` 的 `scripts/*.py` 各跑同一 ast 收集器, 两侧都是 14 个, 差集为空.
- 成功结果字段: 除第 7 项外只有两处变化 —— `note` 文案 (第 2 项授权) 与 `previous_url` 现在可能缺席 (第 3 项"本次也解析不出地址时省略 `previous_url`"授权). 无字段改名, 无新增必带字段.
- 需注意的措辞落差: m25 `TECHNICAL.md:78` 仍写"输出 `port_changed=true` 与 `previous_url` ..., 并写明旧地址已失效", 没写"可以省略"; `SKILL.md` 也没记这条. 返工单授权了省略, 但 spec 文本比实现严, 见 Q-4.

### 3.2 state.json 多了一份局域网地址 (URL 形式)

- record 来源下 `last_url` 现在含已确认局域网地址 (`http://203.0.113.77:39111/`), 是返工单第 3 项正文明确要求的做法; D017 只约束 `--address` 值不落盘, 该值实测确实不入 state.
- 但 `_apply_delivery` (`:653-661`) 的 docstring 末句"地址与 `--address` 的值一律不落盘"容易被读成与事实相反 (实际落了 URL 里的地址); 建议改成"裸地址字段与 `--address` 的值不落盘" (P-4). 另外没有任何用例断言 record 地址**应当**出现在/不出现在 state 里, 现状靠读码.

### 3.3 为在容器里触发宿主前置链引入的环境依赖

- 依赖 1 (`P-1`, 已证实): `test_cli_output_shape.py:64` 用 `PATH=/usr/bin:/bin` 表达"没有 podman". 我实测: 同一个 PATH 前加一个假 `podman`, 报错码立刻变成 `image_unavailable` (因为我这里 `/usr/bin` 没有 podman, 用 `/tmp/rw01/fakebin/podman` 模拟). 宿主上 podman 常装在 `/usr/bin/podman`, 该用例会红或走真 build 分支. 用例 docstring 声称"宿主上同样可跑"这一条不成立.
- 依赖 2 (`P-2`, 已证实机制): 该用例靠 `unshare -m -r` + tmpfs 盖 `/run` 藏容器标记. 需要 `unshare` 在 PATH 里、内核允许非特权 user namespace、seccomp 不拦 `mount`. 本容器满足 (`unshare -m -r` 实测可用), 但 macOS、`kernel.unprivileged_userns_clone=0`、或禁 userns 的容器运行时下用例必然失败 (失败是响的: 断言 `obj is not None` 会红, 不会假通过).
- 依赖 3 (`P-3`, 分层): 该用例被归入快层 (`tests/run --fast` 会跑它), 而它自建 mount namespace; 与 `tests/README.md` 里"创建真实容器/镜像/netns/nft 即 e2e"的判据不冲突 (不是 netns), 但与"快层 = 无重外部资源"的精神有偏移.

### 3.4 用例是否被改弱

- 断言净增: 测试树 diff `+.*assert` 25 行, `-.*assert` 4 行 (2 条换端口期望值 + 1 条恒真表达式 + 1 条 docstring 附近的旧变量), 无 `skip`/`xfail` 新增, 无用例删除.
- 被改的两条都没有放松: 一条从"断言回环值"改为"断言字段缺席 + 失效文案 + 回环留痕", 一条从"断言回环值"改为"断言与控制台交付 URL 相同 + 不含回环 + 失效文案"; 另加一条独立用例.
- 78 passed / 943 collected 我复跑一致; 新增 3 条 (A-1、C-1、D-1 负向) 与返工单自报一致, 收集数 940+3=943 对得上.

## 4 已证实问题 (我复现或读码确认)

- P-1 (回归风险, 最严重): A-1 用例把"无 podman"硬编码为 `PATH=/usr/bin:/bin`; 宿主 `/usr/bin/podman` 常见, 用例会红或会真跑 build. 机制已实测 (假 podman -> `image_unavailable`). 建议改用临时目录 PATH 只放 `sh`/`mount` 的软链 (不带 podman), 而不是依赖系统 `/usr/bin:/bin` 的内容.
- P-2: 同一用例依赖 `unshare` + 非特权 userns, 适用范围窄; 建议在用例 docstring 写明前置, 或在无 userns 时 skip (skip 需发起方同意, 因为会改写"覆盖"口径).
- P-3: 该用例被归快层 (`tests/run --fast` 会跑), 内含 mount namespace 构造; 分层判据不违规但有偏移, 记录备案.
- P-4: `_apply_delivery` docstring 末句"地址与 `--address` 的值一律不落盘"与"record 来源把含地址的 URL 写进 `last_url`"并列时读起来矛盾; 纯措辞, 建议限定为"裸地址字段".
- P-5: H-1 映射只覆盖 `scripts/` 与 `tests/`, 改 `SKILL.md` / `README.md` 仍不选中任何套件, 而这两个文件被 `test_skill_docs.py` 的文本契约用例约束.
- P-6: D-1 守卫范围收窄为"失败出口表格首列": 正文里编造的错误码不再被抓 (旧表达式本意是扫全文 token); collector 也不收 `no_confirmed_address` 这类不经 `error_result` 产生的码, 若将来把它写进表格会假红.
- P-7: "旧地址已失效"只在 JSON 形态有断言; 人类可读形态无自动观察点 (只能靠 `human_summary` 结构推断, 我用探针手工确认过).

不属于问题但已核实: E-1..E-4 四项确实按返工单"不动"处理 —— 复用分支 (`codemap_service.py:563-588`, 无 `_no_data_keys_error` 调用; 该检查只在 `:396` 启动路径) 仍不复查 `no_data_keys`; `run_build` 仍全程持锁 (`codemap_analyze.py:711`); `unsupported_extensions` 仍只出现在 build 的 stats (`codemap_analyze.py:612-621`), 不在 `delivery_notes`; build 输出仍无 AC-001 的三句说明.

## 5 剩余缺口 (含需发起方裁决项)

1. **E-1..E-4 (REVIEW-spec.md 的待裁决四条) 未处理**: serve 复用分支跳过 `no_data_keys`; build 持锁范围超出 TECHNICAL 声明; 交付消息缺"未解析扩展名"说明 (BR-025/D004); build 输出缺 AC-001 的"说明"句. 返工单明确"待发起方裁决, 本轮不动", 现状与首轮一致.
2. **D-2/D-5 补记录未做**: 返工单允许范围内含 ISSUE-03/ISSUE-06 的交付证据补记录, 但 7 项不含, 未做 (`BR-034 第三条人工核验`、全量 pytest 原始记录).
3. **A-2 缺人类可读形态的自动断言** (P-7).
4. **D-1 检查范围收窄** (P-6): 正文漂移不抓; `no_confirmed_address` 等非 `error_result` 码不在全集.
5. **H-1 未覆盖 skill 文档改动** (P-5).
6. **`previous_url` 可省略未写进 spec 面文档** (Q-4): TECHNICAL:78 措辞仍是无条件输出, SKILL.md 未提; 本轮禁改 spec, 需发起方决定是否补一句.
7. **record 来源的 last_url 落地址的判断只靠读码, 无断言** (P-4 附带): 若发起方认为 state.json 连 URL 里的地址也不该有, 则第 3 项的读法要改, 属裁决项而非缺陷.

## 6 待核实疑点 (需对方信息或裁决)

- Q-1: 宿主 `/usr/bin` 或 `/bin` 里是否有 podman (决定 P-1 是否在宿主上实际触发). 我无法在容器内核实宿主安装位置.
- Q-2: 宿主内核是否允许非特权 user namespace (决定 P-2 在宿主与 CI 的表现).
- Q-3: 返工单"禁止范围"里"不把裸地址写进 state.json"与第 3 项正文"把交付 URL 写进 last_url"的读法: 我按"具体条文优先于总括禁止"判为合规 (URL 不是裸地址字段, `--address` 值实测不入盘). 若发起方按更严读法, C-1 的修法要换 (例如只在 `previous_url` 现场拼, 不写 last_url).
- Q-4: `previous_url` 在缺地址形态省略是否需要同步进 SKILL.md / TECHNICAL (本轮禁改 spec, 未改).
- Q-5: A-1 用例在无 userns 环境是否允许 skip (会改变"覆盖"口径, 需裁决).

## 7 处置建议 (按优先级)

1. 改 A-1 用例的 PATH 构造 (临时目录只放 `sh`/`mount`), 消掉"宿主有 podman 就红"的陷阱 (P-1); 顺带在 docstring 写明 unshare/userns 前置 (P-2/P-3).
2. `_apply_delivery` docstring 措辞收紧为"裸地址字段" (P-4); 视 Q-3 裁决决定是否保留 last_url 落 URL 的做法.
3. 补一条人类可读形态的换端口断言 (P-7); 给 D-1 守卫补正文 token 检查或明确写"只查表格" (P-6).
4. `tests/README.md`/`tests/run` 视需要把 `workflow/codebase-map/SKILL.md` 映射到该套件 (P-5).
5. E-1..E-4 与 Q-3/Q-4 由发起方裁决后再决定是否另开返工.

## 8 结论

返工单 7 项: **A-1 / A-2 / C-1 / D-1 / H-1 / H-2 / B-1+B-2 全部已修好**, 首轮最严重的 C-1 (换端口报回环地址) 已按 D018/BR-019 收口, 错误码集合与既有断言无削弱, 78 passed 与 943 collected 可复现.
新增问题集中在"为在容器内到达宿主分支而写的用例可移植性" (P-1/P-2/P-3) 与三处覆盖范围收窄 (P-5/P-6/P-7), 均不影响产品行为; 最严重一条是 P-1.
