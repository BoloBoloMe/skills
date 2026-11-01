# REWORK-01 评审发现项返工

## 父级
- `../../milestone-26/IMPACT-REVIEW.md`, `../../milestone-26/REVIEW-standards.md`, `../../milestone-26/REVIEW-spec.md`
- 实现与规格: `../../milestone-25/EXECUTION.md`, `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`, `issues/ISSUE-01..06`

## 执行
- [x] 已完成
- [x] 派工前复核: HEAD 提交号; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数; `workflow/codebase-map/` 现状.
  - HEAD = `93945e0` (93945e0a6cf6dbe33631457fe996304cf1bb5384, 基点一致, 工作树干净).
  - collect = 940 tests collected (= 865 基线 + 75, 与 m26 评审复核一致).
  - `workflow/codebase-map/` 现状: `scripts/` 4 脚本 (codemap_common/codemap_analyze/codemap_service/codebase-map.py), `tests/` 14 用例文件 + 3 helper (75 用例), `SKILL.md` (v1 三子命令主体 + m21 汉化链保留节), `README.md` (m21 汉化链手册), `agents/`, `tools/`, `i18n/`.

## 要交付什么

采纳双轴评审里明确、且不需要改 spec 的发现, 共 7 项. 逐项照原文核对, 不扩大范围.

1. **A-1 `podman_missing` 文案** (`scripts/codebase-map.py` `_precheck_podman`): message 必须含 "本机没有 podman" 这句 (BR/AC-007 场景条款原文要求). 保留 hint 的下一步动作. 补一条自动化: 用不含 podman 的 `PATH` 起子进程跑真实 CLI, 断言 `error.code == "podman_missing"` 且 message 含该说法, 退出码 1 (该场景在容器内可通过 `PATH` 注入到达).
2. **A-2 换端口文案** (`scripts/codemap_service.py` 换端口分支): `port_changed` 为真时输出里必须写明"旧地址已失效" (TECHNICAL 换端口条与 D018 原文). 补用例断言这句话出现; 不带 `--port` 时两者都不出现.
3. **C-1 `last_url`/`previous_url` 不再用回环地址** (`scripts/codemap_service.py`, 交付层):
   - 地址来源是已确认记录文件 (`address_source == "record"`) 且 `url` 组装成功时, 把该交付 URL 写入 `state.last_url`; 地址来源是本次 `--address` 时**不**把含地址的 URL 写进 `state` (D017: 地址不落盘).
   - 换端口时 `previous_url` 取值顺序: `state.last_url` 是交付 URL 就用它; 否则用 "旧端口 + 本次解析到的地址" 拼; 本次也解析不出地址时省略 `previous_url`, 只保留"旧地址已失效"文案.
   - `state.json` 里仍不得出现裸地址字段 (`--address` 值不入 state).
   - 更新受影响的既有用例期望值 (现固定为回环 URL 的两条), 并补一条: record 来源下 last_url 是交付 URL 且 `previous_url` 不含 `127.0.0.1`/`localhost`.
4. **D-1 恒真断言** (`tests/test_skill_docs.py` 约 138-155 行): 现在的错误码白名单断言因运算符优先级恒真, 且清单是手抄副本. 改为静态解析 `scripts/*.py` 里错误码产生位置 (如 `error_result(...)` 与 `_AnalyzeError(...)` 的位置参数) 收集错误码全集, 再断言文档里出现的错误码样 token 都在这份现场集合内; 删掉手抄清单. 保留"关键错误码必须出现"子集断言. 用一条负向自测或用例内断言证明该检查现在会失败 (例如对一段含编造错误码的假文档文本调用同一检查函数时返回非空).
5. **H-1 测试映射登记** (`tests/README.md` 与 `tests/run`): 按 `tests/README.md` 的"改动面 -> 必跑套件"纪律, 给 `workflow/codebase-map/` 登记映射 (改 `scripts/` 或 `tests/` -> 跑 `workflow/codebase-map/tests`, 快层), 并同步 `tests/run` 的 `RULES` 表 (README 是唯一事实源, 先改 README 再改 run). 核对: 在临时仓库里改一个 `workflow/codebase-map/scripts/*.py` 路径后 `tests/run --dry-run` 或等价入口能选中该套件 (若脚本无 dry-run, 用它的选择函数做单元级核对并在证据里写清).
6. **H-2 m21 手册过期陈述** (`workflow/codebase-map/README.md`): 第 3 行自称唯一操作入口与第 6/16/47/50 行的"v1 未就位"表述已过期. 改为指向 SKILL.md 的 v1 用法, 并把第 47 行"临时用 `python3 -m http.server 8090` 查看"这条**明确标为作废** (它占住 8090 会让 `serve` 报 `port_in_use`); 保留汉化链正文与决策标号, 不改 tools/ 与 i18n/.
7. **B-1/B-2 收窄**: 删掉无调用者的 `codemap_service.run_update_data_keys` 与 `verify_frontend_zip` 的 `expected_sha256` 旁路参数 (测试改用 monkeypatch 常量, 已是现状); 同步删模块 docstring 里对它们的提及.

## 覆盖依据
- `../../milestone-26/REVIEW-spec.md` 的 A-1, A-2, C-1, D-1, B-1, B-2
- `../../milestone-26/REVIEW-standards.md` 的 E-1 (= 本 issue 第 4 项), H-1, H-2
- 规格 `../../milestone-25/TECHNICAL.md` (换端口条, state.json 字段条), `PRODUCT.md` (AC-003, AC-007, BR-019, BR-037), `DECISIONS.md` (D017, D018)
- 规范 `tests/README.md` (改动面映射唯一事实源)

## 允许范围
`workflow/codebase-map/scripts/codebase-map.py`, `scripts/codemap_service.py`, `scripts/codemap_analyze.py` (仅删旁路参数), `workflow/codebase-map/tests/`, `workflow/codebase-map/README.md` (第 6 项), 仓库根 `tests/README.md` 与 `tests/run` (第 5 项), `../../milestone-25/issues/ISSUE-03.md` 与 `ISSUE-06.md` 的 `## 交付证据` 节 (第 D-2/D-5 项补记录).

## 禁止范围
- 不改 PRODUCT/TECHNICAL/DECISIONS/EXECUTION, 不改门禁阈值, 不改 `--json` 字段语义, 不动 m21 的 `tools/` 与 `i18n/`.
- 不把裸地址写进 `state.json` 或任何文件; 不回写 `~/.agents/sandbox-worktree/lan-address`.
- 不为了通过而放宽任何断言; 删除调用者必须同时证明全仓无引用.
- 不处理评审里的 E-1..E-4 (serve 复用前置, build 持锁范围, 未解析扩展名说明, build 输出说明句): 这些待发起方裁决, 本轮不动.

## 验证契约
- 变更类型: 行为变更 (A-1/A-2/C-1 的对外输出与文案) 加 非行为改动 (D-1/H-1/H-2/B-1/B-2 的测试与文档).
- 验证要求/证据: 逐项给命令与输出; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests` 全绿; 收集条数增量 = 新增用例数; `tests/README.md` 与 `tests/run` 的改动双向一致 (同一映射).
- 证据目录 `/tmp/m26-rw01/`.

## 交付证据

环境: 容器内 (无 podman, 无出网), `PYTEST_XDIST_WORKER=gw0` 前缀, `CODEMAP_RUNTIME_DIR` 与临时 HOME 隔离, 不占 8090, 未碰真实 `~/.agents/codebase-map` 与 `~/.agents/sandbox-worktree/lan-address`. 原始记录 `/tmp/m26-rw01/`.

**逐项证据**

1. **A-1 `podman_missing` 文案** — 已做.
   - 做了什么: message 改为含 "本机没有 podman" 的说法, hint 下一步动作保留.
   - 落点: `scripts/codebase-map.py:95` (`_precheck_podman`).
   - 自动化: 新增 `tests/test_cli_output_shape.py:64` `test_podman_missing_message_names_no_podman` — 不含 podman 的 `PATH` (`/usr/bin:/bin`) 起真实 CLI 子进程, 断言 `error.code == "podman_missing"`、message 含 "本机没有 podman"、退出码 1、hint 非空.
   - 可达性说明: 容器内 `/run/.containerenv` 在场, 直跑 CLI 第一关是 `container_not_supported`; 用例用 `unshare -m -r` + tmpfs 盖 `/run` 在子进程里藏掉容器标记 (环境级构造, 不改产物不用替身数据), 让宿主分支前置链 (container -> target -> podman) 可达 podman 关, 即返工单括号注 "PATH 注入到达" 的实现方式. 手工复验同命令链: `PATH=/usr/bin:/bin unshare -m -r /bin/sh -c 'mount -t tmpfs tmpfs /run && exec ... build ... --json'` -> `{"error":{"code":"podman_missing","message":"本机没有 podman, ..."}}`, 退出码 1 (`/tmp/m26-rw01/a1-manual-podman-missing.json`). 宿主真实构造仍归 ISSUE-07 未验证, 不伪记.
2. **A-2 换端口文案** — 已做.
   - 做了什么: 换端口时 `note` 追加 "换端口: 旧地址已失效 ..." (有 `previous_url` 时附原 URL 括号), 两种形态都含连续短语 "旧地址已失效"; 不带 `--port`/沿用 `last_port` 时不出现 (分支未触发).
   - 落点: `scripts/codemap_service.py:471-487` (`_start_service` 换端口分支).
   - 用例: `tests/test_delivery_output.py::test_tc_05_04` (record 来源, 断言 `"旧地址已失效" in changed["note"]`) 与 `tests/test_serve_lifecycle.py::test_tc_04_03` (缺地址形态, 同断言); 两者同时断言不带 `--port` 时 `port_changed`/`previous_url` 不出现.
3. **C-1 `last_url`/`previous_url` 不再用回环地址** — 已做.
   - 做了什么: (a) 地址来源为 confirmed_record 且 url 组装成功时, 启动路径把交付 URL 写入 `state.last_url`; 来源为本次 `--address` 或缺地址时写回环留痕, `--address` 值不入 state (D017); (b) 换端口 `previous_url` 取值顺序: 旧 `last_url` 是交付 URL -> 用它; 否则旧端口 + 本次解析地址拼; 本次解析不出 -> 省略字段只留失效文案; (c) state.json 无裸地址字段. 实现方式: 地址解析 (纯只读不持锁) 提前到 `run_serve` 判定分支之前, 传 `resolved` 供启动路径锁内写留痕与拼 `previous_url`; 交付输出层 `_apply_delivery` 改收已解析结果, 不再自行解析.
   - 落点: `scripts/codemap_service.py:94` (`_is_delivery_url`), `:394/445-458` (`_start_service` 签名与 last_url 留痕), `:471-487` (previous_url 三选一), `:496` (`_serve_core` 透传), `:653/699` (`_apply_delivery`/`run_serve`), 模块 docstring `:20-27` 同步改口径.
   - 既有用例期望值更新 (原固定回环 URL 的两条): `test_serve_lifecycle.py:113` `test_tc_04_03` (缺地址形态: `previous_url` 省略 + `last_url` 保持回环留痕), `test_delivery_output.py:201` `test_tc_05_04` (record 形态: `previous_url` == 交付 URL, 不含回环).
   - 新增: `tests/test_delivery_output.py:243` `test_port_change_reports_record_delivery_url_as_previous` — record 来源下 `state.last_url` == 交付 URL 且 `previous_url` 不含 `127.0.0.1`/`localhost`, note 含失效文案.
   - 辅助: `tests/codemap_service_helpers.py:31/34` 新增 `CONFIRMED_ADDR` 常量与 `use_temp_home` (自 `test_delivery_output.py` 上移共用); `test_serve_lifecycle.py`/`test_service_state_and_stop.py` 的 `srv` fixture 默认空 HOME 隔离 (无 lan-address, 不受宿主记录影响), 需要 record 形态的用例单独覆盖.
4. **D-1 恒真断言** — 已做.
   - 做了什么: 删手抄 `KNOWN_ERROR_CODES` 清单与恒真表达式; 新增 `collect_code_error_codes()` 用 ast 静态解析 `scripts/*.py` 里 `error_result(...)` 第 2 位置参与 `_AnalyzeError(...)` 第 1 位置参的字符串字面量收集全集 (实测 14 个, 两处动态传递的错误码均已在别处以字面量出现); 新增 `doc_error_codes()` 从 SKILL.md 失败出口清单表格首列提取文档错误码; 主用例改为断言文档码 ⊆ 代码全集 + 关键六码子集断言保留.
   - 落点: `tests/test_skill_docs.py:31` (`collect_code_error_codes`), `:61` (`doc_error_codes`), `:171` (主用例改写).
   - 负向自测: `tests/test_skill_docs.py:190` `test_error_code_guard_would_fail_on_fabricated_code` — 对含编造码的假清单文本调同一套函数断言 unknown 非空. 另做实弹负向演示: 临时往 SKILL.md 清单塞 `| totally_fabricated_code |`, `pytest test_tc0601_every_error_code_token_exists_in_code` -> 失败 `AssertionError: 文档里的错误码不在代码错误码全集内: {'totally_fabricated_code'}` (退出码 1, `/tmp/m26-rw01/d1-negative.txt`), 还原后该文件 11 passed.
5. **H-1 测试映射登记** — 已做.
   - 做了什么: 按 "README 是唯一事实源" 顺序, 先在 `tests/README.md` 映射表加行, 再同步 `tests/run` 的 `RULES` 表 (改 `scripts/` 或 `tests/` -> 跑 `workflow/codebase-map/tests`, 快层).
   - 落点: `tests/README.md:51`; `tests/run:35-36`.
   - 核对: `tests/run` 无 dry-run, 用其选择函数做单元级核对 (`/tmp/m26-rw01/h1-select-suites.txt`): 改 `workflow/codebase-map/scripts/codemap_analyze.py`/`codebase-map.py`/`tests/test_serve_lifecycle.py`/`tests/codemap_service_helpers.py` 均 -> `['workflow/codebase-map/tests']`; 对照组 `scripts/swt.py` 不命中 (既有行为不变). 端到端: 临时 git 仓库 (`/tmp/m26-rw01/tmp-repo`) 已跟踪脚本改动后 `tests/run --fast` 输出 "受影响套件: workflow/codebase-map/tests" (`/tmp/m26-rw01/h1-e2e-testsrun.txt`). 双向一致: README 行与 RULES 行均为 scripts/ 与 tests/ 两个前缀 -> `workflow/codebase-map/tests` 快层.
6. **H-2 m21 手册过期陈述** — 已做.
   - 做了什么: 第 3 行改为 "v1 三子命令的唯一操作入口是 SKILL.md, 本文只保留汉化构建链手册"; 第 6 行改为 "build/serve/stop 已由 v1 实现, 用法见 SKILL.md"; 第 16 行归属列改 "v1 服务 (milestone-26) 创建与维护"; 第 47 行临时 `http.server 8090` 配方明确标 **作废勿用** (占住 8090 会让 serve 报 `port_in_use`); 第 50 行节标题改 "v1 已封装为 build 子命令". 汉化链正文与决策标号保留, 未改 `tools/` 与 `i18n/`.
   - 落点: `workflow/codebase-map/README.md:3/6/16/47/50`.
7. **B-1/B-2 收窄** — 已做.
   - 做了什么: 删无调用者的 `codemap_service.run_update_data_keys` 整个函数及其章节注释, 模块 docstring 第 8 行同步改为 "对外函数只有 run_serve / run_stop"; 删 `verify_frontend_zip` 的 `expected_sha256` 旁路参数, docstring 同步改为 "期望值恒用 FRONTEND_ZIP_SHA256 常量, 测试预置期望时 monkeypatch 该常量".
   - 无调用者证明 (删除前 grep 全仓, 排除 docs 与 pyc): `run_update_data_keys` 仅命中定义与 codemap_service.py docstring; `verify_frontend_zip` 仅命中定义与 codemap_analyze.py:241/:287 两处不传参调用; `tests/` 下零命中.
   - 落点: `scripts/codemap_service.py:8` (docstring), 函数已删; `scripts/codemap_analyze.py:205` (`verify_frontend_zip` 单参签名).

**总验证** (命令与结果, 原始输出在 `/tmp/m26-rw01/`)

- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests` -> `78 passed in 18.59s`, 退出码 0, 无 failed, 无新增 skipped (`pytest-codebase-map.txt`).
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` -> `943 tests collected` = 940 基线 + 3 新增 (A-1 一条, C-1 一条, D-1 负向一条) (`collect-only.txt`).
- `uv run python general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md` -> `OK`, 退出码 0 (`check-skill.txt`).
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py` -> `1 passed` (`codex-metadata.txt`).
- 第 5 项双向一致核对与端到端输出见上 (`h1-select-suites.txt`, `h1-e2e-testsrun.txt`).
- 基线三行与 D-1 负向演示见 `baseline.txt`, `d1-negative.txt`.

**未验证项** (保持 m25 D016 分工, 未用替身顶替): 宿主真实构造的 `podman_missing`/`target_missing` 场景 (本项 A-1 用例是环境级构造, 宿主实跑仍归 ISSUE-07); 真实 podman build/镜像/前端下载链路上的 `frontend_hash_mismatch` 等宿主分支; 局域网设备打开交付 URL; 长期常驻.

**范围外未动** (按返工单): 评审 E-1..E-4 待发起方裁决; PRODUCT/TECHNICAL/DECISIONS/EXECUTION 未改; 门禁阈值未改; m21 `tools/` 与 `i18n/` 未动; D-2/D-5 补记录不在 7 项内未做; ISSUE-03/ISSUE-06 的交付证据节未触碰.

## 停止条件
需要改 spec 或决策; 需要真实 podman/出网; 发现第 7 项删除的入口其实有调用者. 遇到就停手并 mailbox request 上报.
