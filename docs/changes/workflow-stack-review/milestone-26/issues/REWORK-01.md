# REWORK-01 评审发现项返工

## 父级
- `../../milestone-26/IMPACT-REVIEW.md`, `../../milestone-26/REVIEW-standards.md`, `../../milestone-26/REVIEW-spec.md`
- 实现与规格: `../../milestone-25/EXECUTION.md`, `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`, `issues/ISSUE-01..06`

## 执行
- [ ] 已完成
- [ ] 派工前复核: HEAD 提交号; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数; `workflow/codebase-map/` 现状.

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

## 停止条件
需要改 spec 或决策; 需要真实 podman/出网; 发现第 7 项删除的入口其实有调用者. 遇到就停手并 mailbox request 上报.
