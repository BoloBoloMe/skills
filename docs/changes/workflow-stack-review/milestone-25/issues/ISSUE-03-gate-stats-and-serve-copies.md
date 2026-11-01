## 父级
- `../EXECUTION.md`

## 执行
- [x] 已完成
- [x] 派工前复核并记录 (写在本行下方): HEAD 提交号; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数; `workflow/codebase-map/` 当前存在哪些文件.
- HEAD 提交号: `22e25e0ebee2bc1ff42ba703cbc133f0edbafafc` (分支 issue/03, 与派工基点一致).
- 收集条数: 916 (EXECUTION 基线 865 + ISSUE-01/02/04 已增 51); 收工复跑 924, 增量 8 = 本 issue 新增用例数.
- `ls workflow/codebase-map`: `README.md, SKILL.md, agents, i18n, scripts, tests, tools`.

## 要交付什么
让 `build` 从"能出数据"变成"能判断该不该交付, 并把数据放到页面能取到的地方":

- 门禁判定 (在复制副本之前做): `edges = len(lenses.dependency.edges.dependencies)`; `level_kinds` = `type=File` 节点上 `level` 的取值种数; 通过条件 `edges > 0` 且 `level_kinds >= 3`. 不通过时仍把 cc.json 写进目标库 `.codebase-map/cc.json` 供复查, 但不复制副本, 输出 `gate_failed` 且 `gate.reason` 写明是边为 0 还是层号种数不足 (带实际数值).
- 统计 (门禁失败也必须完整输出): `scanned_files` (宿主侧按同一份排除集扫出的受支持源码文件数), `files_in_tree`, `zero_declaration:[{path, reason}]` (测试目录, build 目录, 自定义排除, 零声明四类原因), `unsupported_extensions:[{ext, count}]`, `cyclic_edges`, `upward_edges`, `excluded:{tests, build_dirs, custom, dot_codebase_map, tool_defaults}`. `tool_defaults` 单独一类, 表示"宿主扫描数进来了但被分析端自带规则过滤掉"的文件, 不与 `custom` 混.
- 副本分发: 通过门禁后复制到 `serve-root/<key>` (先写临时文件再 `os.replace`), 然后更新 `state.json.data_keys` (锁内). 副本必须与 `index.html` 同目录. `build` 不删除任何其它库的副本, 不做"只留最近一个".
- `build --json` 补齐 `gate`, `stats`, `serve_copy_path` 字段.
- 新测试树补本 issue 用例 (用 fixture 的 merge 产物与 fixture 目标树, 不需要 podman 与真实分析).

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-25/PRODUCT.md`, AC-005 (原件留在库里; 副本与 `index.html` 同目录; 键由清洗后库名与路径哈希组成; 同名不同库不互相覆盖; build 新库不动前面库的副本), AC-006 (依赖边为 0 与层号种数不足两条门禁场景; 未解析的语言只在输出里说明), AC-001 (统计摘要与分母口径场景里的统计部分); BR-010, BR-011, BR-012, BR-014 (覆盖侧), BR-022, BR-024, BR-025, BR-036 (不自动清理); G-005, G-006, NG-004, NG-006, NG-008.
- Technical: `docs/changes/workflow-stack-review/milestone-25/TECHNICAL.md`, 模块接口 (门禁, 统计, 产出, 幂等; `build --json` 的 `gate`/`stats` 字段), 非功能要求 (口径归因), 关键流程 (build 与运行中的服务), 安全策略 (目标库完整性).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-25/DECISIONS.md`: D001, D003, D005, D006, D019, F001.
- `docs/changes/workflow-stack-review/milestone-24/DECISIONS.md`: U001, U003, F003.
- `docs/changes/workflow-stack-review/milestone-13/DECISIONS.md`: D010, D017, D020, D023, D029.

## 允许范围
同全局, 增量: `codemap_analyze.py` 的门禁, 统计, 产出与副本三段, `state.json` 的 `data_keys` 写入, `build --json` 的对应字段, 本 issue 的测试.

## 禁止范围
- 不做服务启停, 不实现 `serve`/`stop` (ISSUE-04/ISSUE-05).
- 不改门禁阈值 (边 > 0, 文件层号种数 >= 3), 不因库小或语言少放宽; 不把统计差值硬凑成相等 (只做逐类归因).
- 不删除, 不移动, 不重命名 `serve-root` 里其它库的副本; 不清 `cache/`.
- 不把层号或违规标记拷进 metrics lens, 不改 merge 产物字段 (NG-006).
- 不在仓库内写 `.cc.json` 与私有路径, 测试 fixture 用临时目录, 证据放 `/tmp/m25-03/`.

## 代码定位提示
- 主体在 `workflow/codebase-map/scripts/codemap_analyze.py` 的产出段; `data_keys` 写入借 `codemap_service.py` 的锁与原子写 (ISSUE-04 落地的函数先由本 issue 以最小实现引入, 之后 ISSUE-04 收口, 若顺序相反则以 04 的函数为准, 不写两份).
- 既有形状参照: `workflow/navigate/scripts/web_server.py` 的 `flock` 与原子写 (`os.replace`) 用法; 统计口径的实测样例见 `docs/changes/workflow-stack-review/milestone-23/PROBE.md` 6.4 (3312 -> 3014, src/test 457 -> 0, 零声明 4 个, 工具默认过滤单列).
- 测试 fixture: 一个最小 merge 产物 (含 `lenses.dependency.nodes` 的 `level` 与 `edges.dependencies` 的 `isCyclic`/`isPointingUpwards`) 与一棵最小目标树 (含 `src/`, `src/test/`, `target/`, `generated/`), 都放 `tmp_path`.

## 验证契约
- 变更类型: 行为变更.
- 对应范围: 门禁判定与退出码, 统计字段与归因, 副本分发与 `data_keys`, 幂等与不删他人副本.
- 验证要求/证据: 覆盖 AC-005 与 AC-006 的可观察结果, 逐条对应 BR-022/BR-024/BR-025/BR-036; 统计用"分量之和能对账"而不是"逐文件相等". 真实库的门禁统计与分母只能宿主执行, 由 ISSUE-07 承接.

## 验证入口
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests`; 通过标准 退出码 0 且无 failed. 本 issue 新增用例:
  - TC-005 (AC-005 主用例): build (stub podman 加 fixture 产物) 后, 目标库出现 `.codebase-map/cc.json`; `serve-root` 里副本文件名等于 `keys[].key` 且与 `index.html` 同目录; 副本内容与原件一致; 键形如 `<清洗后库名>-<8 位十六进制>.cc.json`.
  - TC-006 (AC-006 主用例): 两种退化 fixture 各一次. 边为 0 时退出码非 0, `error.code == "gate_failed"`, `gate.reason` 含边为 0; 层号只有 0 与 1 两种时 `gate.reason` 含"2 种, 少于 3 种". 两次都要求: 目标库原件仍写出, `serve-root` 不出现该库副本, `stats` 与 `zero_declaration` 照常完整输出.
  - TC-03-01: 同库连跑两次, 键不变, 副本被覆盖且 `data_keys` 不出现重复条目, `built_at`/`bytes` 更新.
  - TC-03-02: 两个同名的不同路径目标各 build 一次, 得到两个不同键, 两份副本都在, 后者不覆盖前者.
  - TC-03-03: 已有 A, B 两份副本时 build 第三个库, A 与 B 的副本文件仍在且内容未变, `data_keys` 仍含它们 (BR-036 前半, 不自动清理).
  - TC-03-04: 统计归因, 用 fixture 目标树断言 `files_in_tree` + 五类 `excluded` + `zero_declaration` 各项之和等于磁盘侧文件总数 (实现须在代码里写明这条等式并由用例固定); `tool_defaults` 与 `custom` 分列且不相加串味.
  - TC-03-05: 扩展名维度只汇总分析端不支持的扩展名, 零声明文件与被排除规则命中的文件按类别给计数与清单, 不混进 `unsupported_extensions`.
- 未自动化的部分与理由: 真实库的门禁数值 (边 8820, 层号 8 种) 与真实分母只能宿主执行, 容器内 fixture 只能验判定逻辑, 由 ISSUE-07 承接.
- 通过标准 (整体): 上述每条成立; 门禁失败时 `stats` 与 `initialization` 仍完整 (不因失败省掉分母).

## 交付证据

### 机检结果 (容器内, 2026-11-01)

- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests`: 退出码 0, 59 passed, 无 failed, 无新增 skipped (原 51 条 + 本 issue 8 条). 原始输出 `/tmp/m26-03/pytest-codebase-map.txt`.
- 收集基线核对: `--collect-only -q` 实测 924 条 = 865 (EXECUTION 基线) + 51 (ISSUE-01/02/04) + 8 (本 issue 新增: TC-005 一条, TC-006 两条, TC-03-01..TC-03-05 五条), 增量与新增用例数逐条对上.
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py`: 1 passed.
- `uv run python general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md`: OK, 退出码 0.
- 全量 `uv run python -m pytest` 在容器内 69 failed/100 errors: EXECUTION 完成定义第 8 条写明的环境缺口 (`tests/` 树需宿主 podman), 不属本 issue 验证口径, 不伪记通过.

### 逐项交付与用例对应

- 门禁判定 (AC-006, m25 D001): `codemap_analyze.evaluate_gate`; `edges = len(lenses.dependency.edges.dependencies)`, `level_kinds` = files 树 type=File 节点在 dependency lens 上的 `level` 取值种数; 阈值 边>0 且 种数>=3 未动. TC-006 两条: 边为 0 时 `gate.reason` 含 "边为 0"/"0 条"; 层号只有 0 与 1 两种时含 "2 种, 少于 3 种"; 两次都原件照写, serve-root 无该库副本, state.json 未登记, stats 与 initialization 照常完整.
- 统计 (AC-001 统计场景, BR-024/BR-025, m25 D019): `codemap_analyze.compute_stats`; 统计等式写在函数头 (每份磁盘文件按固定次序归入且只归入一项), 由 TC-03-04 固定: 3+1+2+1+1+2+1 = 11 = 磁盘文件总数; `tool_defaults`(2) 与 `custom`(1) 分列不相加; `scanned_files`=5 且等于 files_in_tree + 零声明 + 工具默认过滤里受支持扩展名部分 (README.md 的 .md 不计入); TC-03-05: `unsupported_extensions` 只汇总 .md, 零声明与排除命中不混入.
- 副本分发 (AC-005, BR-010/BR-012/BR-036): `copy_to_serve_root` 先写 .tmp 再 `os.replace`, 副本与 index.html 同目录, 内容与原件逐字节一致 (TC-005); `data_keys` 在 run_build 持有的锁内 upsert, 复用 `codemap_service` 的 `_load_state`/`_atomic_write_state`, 不另写一份原子写; TC-03-01 同库重跑同键覆盖, `data_keys` 无重复条目, built_at/bytes 刷新; TC-03-02 同名不同路径两键互不覆盖; TC-03-03 build 第三库不动前两库副本与登记.
- `build --json`: 成功含 `gate`/`stats`/`serve_copy_path`; 门禁失败时 `error.code=gate_failed` 且 `gate`/`stats`/`initialization`/`cc_json_path`/`key` 照常输出, 不因失败省掉分母与零声明清单 (TC-006).

### 边界与偏差说明

- stub 边界: 全部用例用 stub podman + fixture merge 产物, 只证明流程接线与归因逻辑, 不等于分析可用; 真实库门禁数值 (边 8820, 层号 8 种) 与真实分母由 ISSUE-07 宿主承接.
- "退出码非 0": 容器内 CLI 首关 `container_not_supported`, 门禁不可从真实入口到达; run_build 返回 `success=false`, 退出码由 CLI `_emit` 的 success->0/1 映射承接 (TC-01-06 已固定该形状).
- test_analyze_pipeline.py 两处必要调整 (ISSUE-02 预留的临时守卫, ISSUE-03 交付后必翻转): `assert_full_build_fields` 由 "gate/stats/serve_copy_path 不得出现" 改为 "必带且门禁通过"; TC-02-02 的 merge 产物内容断言改为 stub_run 序号 (stub merge 产物默认改为内置可过门禁的 fixture, 原 `{"stub","run"}` 形状表达不了 lenses). 其余 TC-02 用例逻辑未动.
- 边列表形状兼容: TECHNICAL 定 2.1 形状 `edges.dependencies`; m23 PROBE 6.4 统计脚本实测 2.0 形状 edges 为纯数组; `_dependency_lens` 两种都读 (只读不改, NG-006), 真实形状由 ISSUE-07 核验.
- codebase-map.py 模块 docstring 里 "门禁...归 ISSUE-03, 本版 result 不含这些字段" 一行已过时; 该文件不在本 issue 允许增量内, 未改, 留给 ISSUE-06 文档收口.
- 未做项: serve/stop (ISSUE-04/05), 真实库门禁统计与分母 (ISSUE-07), SKILL.md 失败出口与清理入口措辞 (ISSUE-06).
## 风险提示
- 统计等式若先在实现里拍一个, 再让测试将就, 会变成自证; 先按 TECHNICAL 口径写出各分量含义, 再用 fixture 核对, 差值必须能逐类解释.
- `data_keys` 与副本复制都要在锁内, 否则并发 build 会写坏清单.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 需要放宽门禁阈值或删除其它库副本才能让流程通过时停止并上报.

## 验收标准
- [ ] 门禁两条退化场景都以 `gate_failed` 非 0 退出, 原件照写, 副本不出现.
- [ ] 门禁失败时分母与零声明清单仍完整输出.
- [ ] 通过门禁后副本与 `index.html` 同目录, 文件名等于键, 内容与原件一致.
- [ ] 统计五类排除与零声明能逐类归因, `tool_defaults` 单列.
- [ ] build 新库不动其它库副本, 不做任何自动清理.

## 被阻塞于
- `ISSUE-02-first-init-and-analysis-output.md`
