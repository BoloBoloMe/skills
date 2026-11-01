# SWT-M26 Standards 轴评审

## 0 审核信息

| 项 | 值 |
| --- | --- |
| 任务标识 | SWT-M26-REVIEW-STANDARDS |
| 轴 | Standards (仓库已记录规范 + Fowler 坏味道) |
| 分支 / 工作树 | review/standards / `REVIEW-standards` |
| 基点 | 2bc146d (工作树 HEAD 起点 5c2311a) |
| diff | `git diff 2bc146d...HEAD`, `git log 2bc146d..HEAD --oneline` |
| 评审对象 | `workflow/codebase-map/scripts/` 4 脚本, `workflow/codebase-map/tests/` 14 用例 + 3 helper, `pytest.ini` 1 行, 根 `README.md` 1 行, `workflow/codebase-map/SKILL.md` 并入 |
| 边界外 | writing-for-llm 文档复审 (eb0f4c7/ccb63aa/1be98fb/2918ad8) 与 to-spec `ac-draft.py workspace` (5e1d552), 仅在同文件时旁看 |
| 实跑验证 | `PYTEST_XDIST_WORKER=gw0 uv run --with pytest python -m pytest workflow/codebase-map/tests -q` -> 75 passed |
| 工具链 | `general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md` -> OK; `tests/test_skills_codex_metadata.py` -> 1 passed |

读过的规范来源:

- 根 `AGENTS.md`, `docs/language/UBIQUITOUS_LANGUAGE.md`
- `pytest.ini` 文件头注释 (testpaths 顺序 + conftest 预载纪律)
- `tests/README.md` (默认入口 `tests/run`, 改动面->必跑套件映射, e2e 归层规则)
- `/home/bolo/.agents/skills/code-review/references/fowler-baseline.md` 全文
- `general/writing-for-llm/SKILL.md` (信息层级/剪枝/环境无关路径/单一真相源)
- `workflow/codebase-map/README.md` (该 skill 记录的"唯一操作入口")
- 先例形状: `workflow/navigate/scripts/web_server.py`, `workflow/navigate/tests/nav_helpers.py`, `workflow/navigate/tests/test_stdlib_only_and_no_external_refs.py`, `tests/test_skills_codex_metadata.py`

判定原则: 仓库已记录规范优先于 Fowler 基线; 工具链已强制的检查 (check_skill.py, tests/test_skills_codex_metadata.py, 静态 stdlib 守卫) 不重复报告. 每条发现都已读对应完整函数/方法及必要调用方.

统计: 硬性违规 2, 已证实缺陷 1, 判断性发现 22, 待核实疑点 2.

---

## 1 硬性违规 (违反仓库已记录规范)

### H-1 新增测试树未登记改动面映射, `tests/run` 默认入口对该树零覆盖

- 规范出处: `tests/README.md` 首节"默认入口: tests/run"+"改动面 -> 必跑套件映射"表; `tests/run` 头注释原文 "改动面->套件映射的唯一事实源是 tests/README.md; 改映射先改 README 再同步本表."
- 相关 hunk: `pytest.ini:10` 新增 `workflow/codebase-map/tests` (diff 唯一测试接线改动). `tests/README.md` 与 `tests/run` 的 `RULES` 表实读均无 `workflow/codebase-map/` 条目.
- 事实: `tests/run` 的 `select_suites()` 对 `workflow/codebase-map/scripts/codemap_analyze.py` 之类的改动路径不命中任何 RULES 前缀, 也不属于 `tests/` 直跑分支, 结果打印"不命中任何测试套件, 无可跑项"并返回 0. 只有改 `pytest.ini` 本身才走 `GLOBAL` 兜底.
- 后果: 后续会话按 `tests/README.md` 的"小改不付全量"纪律改这 4 个脚本时, 1750 行新代码 + 75 个用例默认一条不跑, 门禁形同不存在. 与同 diff 里 `pytest.ini` 已经被谨慎更新的动作自相矛盾.
- 修复: `tests/README.md` 映射表加一行 (`workflow/codebase-map/scripts/` -> `workflow/codebase-map/tests`, 快层) 并在 `tests/run` RULES 同步一条; 若判定该树只走全量, 也要在 README 写明理由.

### H-2 skill 自带 `README.md` 仍宣称 v1 未就位, 且其临时查看命令会踩单例端口

- 规范出处: `workflow/codebase-map/README.md:3` 自称"本文是唯一操作入口", 每节"标注依据的决策编号"; 新 `SKILL.md` 把操作细节指回它 ("细节见 `README.md`"). `general/writing-for-llm/SKILL.md` 剪枝节: "沉积: 过期层不断沉降".
- 相关文件/行 (本次 diff 未触及, 属遗漏): `README.md:6` "本 skill 只含汉化构建链与布局铺设; 分析端调度与常驻服务 (build/serve/stop) 属 v1 实现 (milestone-26...) v1 就位前用本文的临时命令"; `:16` `state.json`, `logs/` 归属列 "v1 服务 (milestone-26), 本片不创建"; `:47` "v1 服务就位前, 临时查看: `python3 -m http.server 8090 ...`"; `:50` "分析端命令 (v1 将封装...)".
- 事实: 本 diff 的 `scripts/` 已实现 build/serve/stop 与 `state.json`/`logs/`, 三条陈述全部过期. `:47` 的临时命令是主动有害的: 它占住 8090, 之后 `serve` 按 `port_in_use` 拒绝 (service `_start_service` 386-392 "不换端口不接管"), 用户按记录的手册操作会自己制造故障.
- 修复: 改 `README.md:6/16/47/50` 为"v1 就位, build/serve/stop 见 SKILL.md"; 删掉 `:47` 的临时 http.server 配方 (或明确标注"已在 v1 就位后作废, 勿用, 会占 8090 使 serve 报 port_in_use").

---

## 2 已证实缺陷 (可判真假, 非口味)

### E-1 `test_skill_docs.py` 的错误码守卫是恒真断言, 实际不校验代码

- 文件: `workflow/codebase-map/tests/test_skill_docs.py:138-154`.
- 事实: `unknown = tokens & {14 个错误码字面量} - KNOWN_ERROR_CODES`. Python 里 `-` 优先级高于 `&`, 且 `KNOWN_ERROR_CODES` (29-45) 是那 14 个字面量加 `no_confirmed_address` 的超集, 所以 `{14} - KNOWN_ERROR_CODES == set()`, 整个表达式恒为 `set()`, `assert not unknown` 永远成立.
- 且 `KNOWN_ERROR_CODES` 是从脚本"逐个核对所得"的手抄副本 (注释 26-28 自述), 代码新增/改名错误码时这份清单不会跟着动, 断言也不会红. 用例声称的"文档错误码样 token 全部在代码错误码全集内"因此未被验证.
- 修复: 静态解析 `scripts/*.py` 里 `error_result(...)` 与 `_AnalyzeError(...)` 的位置参数, 现场收集错误码全集再比对; 删掉手抄清单. 同一函数后半段 (`codes_in_doc` 至少含 6 个关键码) 是有意义的, 保留.

---

## 3 判断性发现 (Fowler 坏味道, 均引用 hunk)

### J-01 Duplicated Code: "原子写 JSON (tmp + chmod 0600 + os.replace)" 三份, 另两份无 chmod 的近亲

- `codemap_service.py:206-211` `_atomic_write_state`; `codemap_service.py:305-311` `_write_startup_error`; `codemap_analyze.py:325-330` `_write_cache_json`. 三份逐行同构, 只差文件名与 payload.
- 近亲: `codemap_analyze.py:633-644` `copy_to_serve_root` 与 `:662-676` `write_cc_json` 是同一"tmp 再 replace"手法, 但**不做 chmod**, 于是 state/cache/startup_error 是 0600, serve-root 副本与目标库原件是默认 umask 权限. 同一文件里两个纪律并存, 已开始分叉.
- 修复: `codemap_common` 收一个 `write_bytes_atomic(path, data, mode=0o600)`, 五处调用.

### J-02 Duplicated Code: 运行时目录/锁/state 三件套在五个入口各抄一遍

- `base = Path(runtime_base).resolve() if runtime_base is not None else cmc.runtime_dir()`: `codemap_service.py:471`, `:623`, `:681`, `:767`, `codemap_analyze.py:709`.
- 锁超时错误信封 (code/message/hint 三段文案): `codemap_analyze.py:712-717`, `codemap_service.py:474-479`, `:684-689`, `:770-775`.
- `_load_state` 失败转 `error_result`: `codemap_service.py:481-486`, `:692-697`, `:777-782` (+ analyze 652-659 走另一套).
- `_utc_now_iso` 在两模块各定义一次: `codemap_service.py:84-85`, `codemap_analyze.py:684-685`.
- 另有一处真实不一致: 传参分支做 `.resolve()` (符号链接被解开), 默认分支 `cmc.runtime_dir()` (`codemap_common.py:100-107`) 只 `expanduser` 不 resolve. 若 `~/.agents/codebase-map` 是软链, 生产路径与测试路径解析出不同字面路径, 锁文件/data_keys 里的 `source_cc_json` 就会两套形态.
- 修复: `cmc.runtime_base(runtime_base) -> Path` 一处解析且统一 resolve; service 提供公开 `lock(base)` 上下文管理器 (含超时错误信封), state 读错误信封同理.

### J-03 Duplicated Code: merge 最小产物构造有三份, 其中一份活在字符串里

- `codemap_stub_helpers.py:87-96` (stub 脚本体内的 `ident` + files 树 + lenses) 与 `:268-269` `_fixture_id` 逐字同构 (`sha256("root/"+rel)[:12]`); `:272-321` `make_merge_fixture` 又造一遍同形状产物.
- 后果: 改产物形状 (比如补 `attributeDescriptors`) 要同步改三处, 且第一处是**字符串常量里的代码**, 编辑器无法跳转, 漂移只能靠用例变红才发现.
- 修复: stub 脚本不再内联产物, 改为 `sys.path` 注入后 import `codemap_stub_helpers.make_merge_fixture` 或读 `CODEMAP_STUB_CC_JSON` 一条路径.

### J-04 Duplicated Code: 两个测试模块各写一份 build 装配器

- `test_analyze_pipeline.py:54-70` `build_with_stub` 与 `test_gate_stats_and_copies.py:90-102` `build_with_fixture`: 都是 "写 stub podman -> 注 PATH/stub 环境 -> preset 前端并 patch sha 常量 -> 定 runtime -> `cma.run_build`", 差别只有 `repo_digests`/`CODEMAP_STUB_CC_JSON` 两个开关.
- 本树已按 pytest.ini 纪律准备了唯一命名的 `codemap_stub_helpers.py` 专门放这类共享工具, 两份装配器却留在用例模块里.
- 修复: 合并成一个 `codemap_stub_helpers.build_with_stub(monkeypatch, tmp_path, target, *, fixture=None, ...)`.

### J-05 Duplicated Code: `srv` fixture 逐字四份

- `test_http_surface.py:15-20`, `test_delivery_output.py:32-36`, `test_serve_lifecycle.py:28-32`, `test_service_state_and_stop.py:29-33`: 四个模块的 `def srv(tmp_path)` 体完全一致 (`CodemapSrv(tmp_path)` + `yield` + `cleanup()`).
- 本树不设 conftest 是纪律 (pytest.ini 头注释), 但 fixture 可以从唯一命名模块显式 import, 不必抄四份; 新增一个需要 `srv` 的用例模块时还要记得抄第五份.
- 修复: 把 `srv` 放 `codemap_service_helpers.py`, 各用例 `from codemap_service_helpers import srv  # noqa: F401`.

### J-06 Duplicated Code: "取 stdout 最后一行 JSON" 两个实现

- `codemap_helpers.py:49-52` `stdout_json(proc)` 与 `test_serve_lifecycle.py:35-37` `_last_json_line(text)`. 后者与 `serve_lifecycle` 已在 `:24` 导入前者同时存在.
- 修复: `stdout_json` 拆出 `parse_last_json_line(text)`, 两处共用.

### J-07 Speculative Generality: `run_update_data_keys` 无调用方, 且与真正在用的 upsert 语义相反

- `codemap_service.py:760-793` `run_update_data_keys` 全仓零调用 (`grep` 仅命中定义与模块 docstring `:8`); build 实际走 `codemap_analyze.py:647-659` `_update_data_keys`, 直接调 service 私有原语做**单键 upsert**.
- 两者语义不同: `run_update_data_keys` 是 `state["data_keys"] = list(entries)` (**整表替换**, 会抹掉其它库的登记, 与 BR-036 "其它库条目原样保留" 冲突); `_update_data_keys` 才是 upsert. 保留一个错的公开 API, 谁哪天照着 docstring "对外函数只有 run_serve / run_stop / run_update_data_keys" 去用, 就会削掉别的库的登记.
- 修复: 删 `run_update_data_keys`; 让 analyze 调 service 的公开 `upsert_data_keys(base, entry)` (把现有 `_update_data_keys` 上提), 同时消掉 J-09 的私有穿透.

### J-08 Speculative Generality: `compute_stats` 的 `disk_total` 返回值无人使用

- `codemap_analyze.py:575/578/625` 统计 `disk_total` 并作为第二返回值; 唯一调用方 `:764` `stats, _disk_total = compute_stats(...)` 直接丢弃. 测试要磁盘总数时自己另写 `disk_file_count` (`test_gate_stats_and_copies.py:121-122`).
- 修复: 去掉第二返回值, 等式校验需要的口径放进 `stats` 或留在用例侧.

### J-09 Inappropriate Intimacy / Feature Envy: analyze 与 service 互相穿透私有

- `codemap_analyze.py:71` `import codemap_service as cms  # 仅复用运行时文件锁`; 实际用到 `cms._acquire_lock`/`_release_lock` (`:711/:812`), 以及 `cms._load_state`/`_fresh_state`/`_atomic_write_state` (`:653/:655/:659`). 四个 service 私有名进了另一个模块.
- 反向依赖以函数内延迟 import 存在: `codemap_service.py:593` `import codemap_analyze as cma  # noqa: PLC0415` (只为 `files_in_tree_of`). 模块级 analyze -> service, 函数级 service -> analyze, 是一条绕圈依赖, 代码用 `noqa` 压住了它.
- 修复: service 暴露 `state_lock(base)` 与 `upsert_data_keys(...)` 公开接缝, analyze 只用公开名; `files_in_tree_of` 属纯统计, 挪到 `codemap_common` 或独立小模块, 消除绕圈.

### J-10 Mysterious Name: `files_in_tree_of` 与两个 `run_build`

- `codemap_analyze.py:501` `files_in_tree_of(merge_data)` 名字读起来是"某物的树里的文件", 实际返回**计数**, `of` 后面缺宾语. 改为 `count_files_in_tree(merge_data)`.
- `codebase-map.py:106` 与 `codemap_analyze.py:701` 都叫 `run_build`: CLI 层那个做前置检查后转调分析层同名声明的函数, 调用链读起来是 `run_build` 调 `run_build`, 找"前置检查在哪"要多跳一层. CLI 那个宜叫 `build_command` 或 `run_build_with_prechecks`.

### J-11 Mysterious Name / flag argument: `_delivery_keys(..., with_details=True)`

- `codemap_service.py:557-584`: 布尔开关决定 `keys[]` 是 `{"key"}` 还是 `{"key","built_at","bytes"}` 两种形状; 调用点 `:628` 传 `with_details=has_address`. 输出契约靠一个布尔参数分叉, 读调用点看不出差异在哪里产生 (AC-008 的两种形态).
- 修复: 拆 `delivery_keys_names(...)` 与 `delivery_keys_with_details(...)`, 或显式传 `shape="names"|"details"`.

### J-12 Data Clumps: `base` / `serve_root` / `state` 三件套反复同行

- `codemap_service.py:248-282` `_no_data_keys_error(base, state)` 内部又 `base / "serve-root"`; `:557-584` `_delivery_keys(state, serve_root, ...)`; `:614-658` `_apply_delivery` 里重新算 `base` 与 `serve_root`; `:381-452` `_start_service(base, target_port, old_state, note)`.
- 三者总是一起出现且都是"运行时目录的一次快照", 像一个等待诞生的类型.
- 修复: `Runtime(base)` 小类, 带 `serve_root`/`state_path`/`load()` 属性, 沿调用链传递一个对象.

### J-13 Primitive Obsession: `".codebase-map"` 与版本号以字面量散落

- `".codebase-map"`: `codemap_common.py:198-206` (DEFAULT_EXCLUDES), `codemap_analyze.py:564` (从默认集里再挖掉它), `:583` (`if ".codebase-map" in segments`), `:670` (`target / ".codebase-map"`). 四处各自持有这个领域概念, 564 处还要靠"挖掉再单算"绕过同源纪律.
- 版本号: `codemap_analyze.py:92` `INIT_NOTICE` 里硬写 "(vis-2.9.1)", `:187` hint 里硬写 "官方 2.3.0", 而同名的 `cmc.FRONTEND_VERSION` / `cmc.IMAGE_TAG` 就在手边. 按 `workflow/codebase-map/README.md:73-75` 的升级流程, 改版本号重跑后这两句提示文案会说谎.
- 修复: `cmc.DATA_DIR_NAME = ".codebase-map"` 与 `cmc.DATA_SUFFIX` 统一出口 (service `:65` 已有一份 `DATA_SUFFIX`); 提示文案改 f-string 引用常量.

### J-14 Long Function / Divergent Change: `compute_stats` 100 行五职责

- `codemap_analyze.py:524-625`: 同一函数里做 (a) 排除集转正则, (b) 目标树全量 `os.walk` 归五桶, (c) 从 merge 产物重算边/层统计, (d) 扩展名汇总排序, (e) 零声明清单排序. 因"统计口径变了"与"排除规则变了"两个不相关理由被改.
- 修复: 拆 `_walk_and_bucket(target, in_tree_paths, default_regexes, user_regexes)` 与 `_edge_stats(dep_edges)`, 主函数只做装配.

### J-15 重复遍历: files 树与 dependency lens 每次 build 各解析三遍

- `_files_tree_index` 在 `evaluate_gate` (`:478`) 与 `compute_stats` (`:557`) 各跑一次; `files_in_tree_of` (`:508`) 在 serve 交付时又跑一次. `_dependency_lens` 同样在 `:479` 与 `:558` 各跑一次. 每次都是对同一份 merge JSON 的整树 DFS.
- 后果: 大库 (m23 实测 865 文件起) 每次 build 多两次全树遍历; 更要紧的是三处"同口径"靠人肉保持一致.
- 修复: `run_build` 里解析一次成 `ParsedMerge(id_types, file_paths, dep_nodes, dep_edges)`, 传给门禁/统计/交付.

### J-16 残留死代码: 空章节标题与恒真分支

- `codemap_analyze.py:414-421`: 两个连续注释块, 前一块 "产出: merge 产物逐字节写目标库" 下面没有任何代码, 紧接下一块 "门禁" 标题. ISSUE-02/03 拼接时留下的空壳.
- `codemap_analyze.py:592` `if rel in in_tree_paths: ... continue` 之后, `:609` 再判 `if rel not in in_tree_paths:` —— 走到这里恒真, 条件没有信息, 只让人怀疑 592-608 之间是否改过 `in_tree_paths`.
- 修复: 删 414-418 的空章节; 609 去掉条件直接 `zero_declaration.append(...)`.

### J-17 Stale docstring: CLI 模块自述与已落地行为相反

- `codebase-map.py:5-8` "serve 与 stop 自 ISSUE-04 起注册... serve 的地址解析与交付字段... 归 ISSUE-05, 本版 serve 只保证端口, 状态, 复用与监听"; 同一 docstring `:21-31` 又写 serve 输出 url/keys/delivery_notes (= ISSUE-05 已落地).
- `codebase-map.py:15-19` "门禁判定, 统计分母, 副本复制与 state.json 更新归 ISSUE-03, 本版 result 不含这些字段" —— 同一文件的 `run_build` (`:106-119`) 调的就是已带 gate/stats/副本的 `cma.run_build`.
- 后果: 读 docstring 判断"这个版本能交付 URL 吗"会得到两个相反答案. 同 diff 的 `codemap_analyze.py:4-6` 已经写了"ISSUE-03 在此之上补齐...", 说明 docstring 维护纪律本身存在, 只是 CLI 这份漏了.
- 修复: 删掉两句"本版..."; 需要保留的分期叙述集中在文件末尾一行.

### J-18 文档单一真相源: 版本号与 digest 口径在四处各写一遍

- `workflow/codebase-map/SKILL.md:90-94` (版本口径节, 写 2.3.0 / 单架构 digest 核对 / vis-2.9.1 / sha256), `workflow/codebase-map/README.md:6/14` (版本钉死, manifest digest 前 8 位), `codemap_common.py:27-42` (常量), `test_version_constants.py:13-31` (逐字期望).
- `general/writing-for-llm/SKILL.md` 剪枝节: "让每个意义住在单一真相源... 重复花费维护和 token". 而 README:76-78 的升级流程就是"改一处版本号重跑", 现在要改的是四处.
- 修复: SKILL.md/README 只保留"版本以 `codemap_common.py` 常量为准, 升级见 README 第 6 节", digest 全文留在常量与测试里.

### J-19 SKILL.md 写死与运行时解析冲突的家目录路径

- `workflow/codebase-map/SKILL.md:78` (`~/.agents/codebase-map/`), `:48` (`~/.agents/sandbox-worktree/lan-address`), `:87` (`~/.agents/codebase-map/serve-root/`).
- 规范出处: `general/writing-for-llm/SKILL.md` 剪枝节 "路径与操作保持环境无关: 不写与当前环境绑定的绝对路径, 路径应相对或由运行时解析".
- 事实: 这两个路径在代码里由 `cmc.runtime_dir()` (`codemap_common.py:78-84`, 可用 `CODEMAP_RUNTIME_DIR` 覆盖) 与 `_default_records_root()` (`:113-117`) 解析. 一旦覆盖生效, 文档给的路径就是错的, 而 `state_mismatch`/复原步骤恰恰要求用户按文档去看文件.
- 修复: 改写为"运行时目录 (默认 `~/.agents/codebase-map/`, 受 `CODEMAP_RUNTIME_DIR` 覆盖)"一句话, 后文一律用"运行时目录/服务根"指代.

### J-20 SKILL.md 膨胀: 14 行错误码表 + 7 个章节, 每行只服务一个失败分支

- `workflow/codebase-map/SKILL.md` 全 110 行, 其中 `:53-74` 是 14 行错误码/下一步动作表 (`:57-72`) 加一段 `address_missing` 补充, 另有 `:9/:38/:46/:53/:76/:85/:90/:96/:101` 九个章节标题, 日常只用 build/serve/stop 三条.
- 规范出处: `general/writing-for-llm/SKILL.md` "信息层级"与"膨胀": 只有部分分支触及的参考材料应推到指针后面; "当文档有步骤时, 本该披露的文件内参考材料会掩埋步骤". 这份 skill 的日常步骤只有 build/serve/stop 三条, 而失败码表占了一半篇幅, 且失败时 `serve`/`build` 的输出本身 (stderr 的 `错误码` + `下一步`) 已经在上下文里.
- 修复: 错误码表与复原步骤移到 `reference/troubleshooting.md`, 顶层留一行指针 ("遇到 `success: false` 时读 reference/troubleshooting.md"); 内容不删, 只挪位置.
- 注: 表内内容经我逐条比对 `scripts/` 与工具链, 与代码一致 (无错码), 本条只针对放置层级.

### J-21 风格偏离 (仓库无 lint 配置, 按 PEP8 与全仓既有风格判断)

- `codemap_common.py:113` E302 (顶层 `def` 前只空 1 行, 该文件其它顶层定义都是 2 行).
- `codemap_analyze.py:565` E202 (`tuple(g for g in user_excludes or () )` 右括号前多空格).
- `codemap_analyze.py:489` 无占位符 f-string (`f"依赖边为 0 条 (门禁要求 > 0)"`), 同文件其它 f-string 都带变量, 读起来像漏了插值.
- 长行: 12 行超过 122 字符 (全仓既有最宽为 `general/mailbox/scripts/mailbox.py` 的 122), 最宽 `codemap_service.py:515` 161 字符, `:280` 160 字符.
- 测试风格分叉: `test_runtime_dir.py:68` 用 `unittest.mock.patch.dict`, 同树其它用例一律用 pytest 的 `monkeypatch`.
- 说明: 仓库没有 pyproject/ruff/flake8 配置, 故不构成硬性违规; 但这几处是与既有代码的唯一性偏离, 顺手可清.

### J-22 文本契约测试脆弱, 且与工具链已有检查重复

- `test_skill_docs.py:71-147` (TC-009/TC-06-01) 断言整句散文 (`"三者不合并"`, `"没有\"只停某一个库\"的语义"`, `"手动删"`, `"原地复用"`...). 任何一次措辞润色都会红, 红的理由与行为无关; 先例 `workflow/navigate/tests/test_stdlib_only_and_no_external_refs.py:8` 明确写了 "不得测试文档文字内容".
- `test_skill_docs.py:166-170` `test_tc0602_openai_yaml_verbatim` 断言的内容, `tests/test_skills_codex_metadata.py:67-72` 已逐字强制; `:157-164` 的 frontmatter 字段则被 `check_skill.py` 覆盖. 属于重复建设.
- 缓解事实: 这批断言是 ISSUE-06 任务书点名的文本契约 (TC-009/TC-06-01/TC-06-02), 不是我判定它不该存在, 而是**位置**可改.
- 修复: 断言收敛到"词元级" (`build`/`serve`/`stop` 三个词元 + 错误码 token + frontmatter 键), 句子级散文断言删掉; `openai.yaml` 与 frontmatter 两条交给工具链, 本树不重复.

---

## 4 待核实疑点 (需 spec 负责人裁决, 我不改代码)

### V-1 `--exclude` 承诺 glob 语义, 实现是逐字转义, SKILL.md 示例因此无效

- 文档侧: `codebase-map.py:136-138` help "追加排除规则 (glob 语义, 脚本负责转成分析端正则)"; `SKILL.md:19` "`--exclude` 以 glob 语义追加排除规则"; `SKILL.md:29` 示例 `build /path/to/demo --exclude "docs/**"`.
- 实现侧: `codemap_common.py:224-226` `glob_to_ccsh_regex = re.escape(glob)`, 且 `test_excludes_and_regex.py:39-43` 把"不展开 glob"固定成断言 (`"build*"` 不匹配 `buildfoo`).
- 推论: `--exclude "docs/**"` 转成 `docs/\*\*`, 只按字面匹配, 实际一个文件都排不掉; 用户照示例操作会以为排除了 docs.
- 待裁决: m25 D019 的"转义"是否指"只支持字面量目录名"? 若是, 文档的 "glob 语义" 与示例都要改; 若不是, 实现要补 glob 展开.

### V-2 缺地址时"候选地址列表"可能为空, 文档没写这条分支

- `codemap_common.py:137-162` `candidate_lan_addresses()` 在 `ip` 不可用或全是隧道网卡时返回 `()`, `resolve_delivery_address` (`:164-195`) 就给出 `candidates: []`; `SKILL.md:66` 只写"输出 `address_missing` 与候选地址列表".
- 容器实测非空 (`test_delivery_output.py:132-137` 断言过), 但宿主可能是 `ip` 缺失或无全局网卡的环境.
- 待裁决: 候选为空时是否要额外的错误码/文案 (例如"宿主没有可确认的局域网地址, 请自备")? 现在会交付一个空列表让调用会话无从下手.

---

## 5 检查过且合规的项 (避免下游重复劳动)

- pytest.ini 纪律: 新增树无 `conftest.py`, 共享工具全放唯一命名模块 (`codemap_helpers.py`/`codemap_service_helpers.py`/`codemap_stub_helpers.py`); 全仓 `from conftest import` 只出现在 `tests/` 树, 新树零处. testpaths 顺序 (`workflow/navigate/tests` -> `general/present/tests` -> `workflow/codebase-map/tests` -> `tests`) 符合头注释.
- 标准库约束: `test_stdlib_only.py` 白名单恰好三模块, 与 `import` 实测一致; 无第三方依赖.
- e2e 归层: 新用例只起 stub podman 与真实子进程/回环 HTTP, 未创建容器/镜像/netns, 按 `tests/README.md` 判据属快层; 全部通过 (75 passed), 无 `e2e` 标记误用.
- 无调试残留: 新代码零 `TODO/FIXME/breakpoint/print(`.
- `SKILL.md` 与代码一致性: 错误码表 14 项与 `scripts/` 实有错误码逐条对上; `_serve-daemon` 未列为对外子命令 (`test_skill_docs.py:83`).
- 调用关系口径 (`README.md` 目录节): 全仓无其它 skill 引用 codebase-map, "不被任何 skill 调用" 仍成立; 根 README 技能表行已更新.
- 工具链: `check_skill.py` OK, `tests/test_skills_codex_metadata.py` passed.

---

## 6 摘要

- 硬性违规 2 条, 都是"该改的记录没改"而非代码写错: (H-1) 新测试树没进 `tests/README.md` 映射与 `tests/run`, 默认入口对该树零覆盖; (H-2) skill 自带 README 仍写 "v1 就位前", 其中"临时 `python3 -m http.server 8090`"这条会直接踩 `port_in_use`.
- 最严重一条是 H-1: 它让后续会话按仓库自己的纪律改这 1750 行时一条测试都不跑, 门禁失效且没有任何提示.
- 已证实缺陷 1 条 (E-1): `test_skill_docs.py` 的错误码守卫因集合运算优先级恒定通过, 且清单是手抄副本, 不校验代码.
- 判断性发现 22 条, 集中在四类: 原子写/锁/state 装配的重复 (J-01/J-02/J-03/J-04/J-05/J-06), 死代码与语义分叉的公开 API (J-07/J-08/J-16), 模块互相穿透私有造成的绕圈依赖 (J-09), 以及 SKILL.md 的单一真相源与环境无关路径 (J-18/J-19/J-20).
- 代码行为面未发现功能性错误; 75 个用例全绿, 工具链全过. 本次评审不动代码, 结论以本报告与 commit 为准.
