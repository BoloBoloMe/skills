# SWT-M26 Spec 轴评审

- 任务标识: SWT-M26-REVIEW-SPEC
- 评审对象: `git diff 2bc146d...HEAD` (实现产物 `workflow/codebase-map/scripts/` 四个脚本, `workflow/codebase-map/tests/` 14 个用例文件加 3 个 helper, `pytest.ini` 一行, `README.md` 一行, `workflow/codebase-map/SKILL.md` 的并入)
- 评审依据: m25 `PRODUCT.md` (AC-001..AC-009, BR-001..BR-037), `TECHNICAL.md`, `DECISIONS.md` (D001-D020, F001-F008), `EXECUTION.md`, `issues/ISSUE-01..06` 的验证契约/验证入口/交付证据, 以及 `verification-contract` skill.
- 不评范围 (按任务书边界): eb0f4c7/ccb63aa/1be98fb/2918ad8 的文档复审, 5e1d552 的 `to-spec ac-draft.py workspace` 子命令, ISSUE-07 的宿主取证 (未执行).
- 评审者身份: 未参与实现, 未改任何代码与规格.

## 复核方式 (我自己实跑的入口)

在容器内 (`/run/.containerenv` 在场, 无 podman, 无出网) 复跑, 结果与各 issue 交付证据一致:

- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests -q` -> `75 passed in 17.89s`, 退出码 0, 无 failed 无 skipped.
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` -> `940 tests collected` (= 865 基线 + 75, 与逐 issue 增量 29/13/9/8/6/10 相加一致).
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py` -> 1 passed.
- `uv run python general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md` -> OK, 退出码 0.
- 原始证据目录 `/tmp/m26-01..05` 在场, 抽查内容与 issue 交付证据的叙述逐条对上 (含 `/tmp/m26-04/manual_flow.txt` 的换端口输出, `/tmp/m26-05/evidence.md` 的两形态输出, `/tmp/m26-02/demo-run.txt` 的 stub argv).
- 宿主项 (真实 podman build, 真实 3D 渲染, 局域网设备打开, 长期常驻, 全量 pytest, `target_missing`/`podman_missing`/`image_unavailable`/`frontend_unavailable` 的宿主构造) 按容器事实一律视为未验证; 本次未把它们记为通过, 也未要求实现方造替身.

结论分四类外加疑点, 已证实与待核实分开写. 计数: 缺失/不完整 2, 范围蔓延 4, 实现方式有误 1, 证据与契约不符 5, 待核实疑点 4. 未发现会让主流程跑不起来的功能性缺陷; 最严重一条是换端口报出的"旧地址"是回环地址 (见 C-1).

## A 缺失或不完整 (spec 要求, 实现没做到或只做到一部分)

### A-1 `podman_missing` 的报错里没有 AC-007 指定的那句说法

- spec 原文: `PRODUCT.md` AC-007 场景大纲 "环境不足时报错停下不降级":
  - 情形表: `| 没有 podman | 本机没有 podman |`
  - 场景条款: "而且 报错里必须出现 <报错里必须出现的说法>"
- 实现: `workflow/codebase-map/scripts/codebase-map.py` 的 `_precheck_podman()` (行 90-100)
  ```python
  return cmc.error_result(
      "build",
      "podman_missing",
      "PATH 上找不到 podman, 无法运行官方分析镜像.",
      "先安装 podman 并确认 `podman --version` 可用, 再重试.",
  )
  ```
  message 与 hint 里都没有 "本机没有 podman".
- 对照组: 同一大纲的另两行是满足的 —— `target_missing` 的 message 含 "目标目录不存在或不是目录" (`_precheck_target`), `frontend_unavailable` 的 message 以 "取不到官方前端产物:" 开头 (`codemap_analyze.py` `download_frontend_zip`)。
- 为什么没被发现: 该场景只能在宿主构造。`EXECUTION.md` 验证策略明写 "`build` 的 `target_missing` 与 `podman_missing` ... 只在宿主构造 (目标不存在; `env PATH=/nonexistent /usr/bin/python3 ...`) 观察, 记入 ISSUE-07, 不在容器内造假", ISSUE-07 尚未执行, 所以容器内 75 条用例覆盖不到这句文案; 唯一碰到 `podman_missing` 的 `test_cli_output_shape.py` 只断言 `error.code` 非空与失败形状, 不断言文案。
- 影响: 按 AC-007 逐字判定会不及格; 修法是把 message 改成含 "本机没有 podman" 的说法 (例如 "本机没有 podman, 无法运行官方分析镜像")。

### A-2 `serve` 换端口的输出没有"写明旧地址已失效"

- spec 原文: `TECHNICAL.md` 常驻服务与状态 "换端口" 条: "换端口: 目标端口与 `last_port` 不同且成功启动时, 输出 `port_changed=true` 与 `previous_url` (由 `last_url` 或旧端口加当前地址拼出), **并写明旧地址已失效**." `PRODUCT.md` AC-003 (实例已停机时用显式端口换端口) 场景: "而且 输出明确报告旧地址已失效". `DECISIONS.md` D018: "换端口成功后必须报告旧地址已失效".
- 实现: `codemap_service.py` `_start_service` 行 441-452, 换端口时只往结果里塞 `port_changed` 与 `previous_url`, `note` 仍是启动文案 "状态记录显示服务未在运行, 按目标端口启动.", 全库检索 "失效" 只命中 `stop` 的 note (行 748) 与行 449 的注释, `serve` 路径没有任何"旧地址已失效"的措辞。
- 实测证据: `/tmp/m26-04/manual_flow.txt` 第 [7] 步 `serve --port 18472 --json` 输出
  ```json
  {"success": true, "port": 18472, ..., "note": "状态记录显示服务未在运行, 按目标端口启动.", "port_changed": true, "previous_url": "http://127.0.0.1:18471/"}
  ```
  只有字段, 没有那句话。
- 影响: AC-003 该场景的第三条要求落空。字段存在只能说"可从字段推断", 与 spec 明确要求的"写明"不同。修法: 换端口时把 note 改成含"旧地址 … 已失效"的文案 (TECHNICAL 已允许字段名调整, 文案属交付消息内容)。

## B 范围蔓延 (diff 里有, spec 没要求)

以下四条都不改变对外主契约, 且都在交付证据里留了记录, 但仍属 spec 未要求的新增, 列入以便发起方裁决是否需要收窄。

- B-1 未被使用的导出 `codemap_service.run_update_data_keys` (行 760-790)。`codemap_analyze.run_build` 的 `_update_data_keys` 直接复用 `cms._load_state`/`_atomic_write_state`, 生产与测试都没有调用者 (全仓 grep 只命中定义与模块 docstring "对外函数只有 run_serve / run_stop / run_update_data_keys")。spec 的 `codemap_service.py` 责任里没有这个入口, 它是一份多余的写状态 seam。
- B-2 `codemap_analyze.verify_frontend_zip(zip_path, expected_sha256=None)` (行 205-226) 的旁路参数从未被传过 (grep 两处调用 `verify_frontend_zip(tmp)`、`verify_frontend_zip(zip_path)` 都不传; 测试改用 `monkeypatch.setattr(cmc, "FRONTEND_ZIP_SHA256", ...)`)。spec 只允许"测试可放伪产物并预置 sha256 期望值", 没有要求在生产函数上开一个可覆盖期望值的参数。
- B-3 `stop` 增加 "记录的 pid 存活但不是本服务守护进程 -> `state_mismatch` 拒绝 SIGTERM" 分支 (`run_stop` 行 719-725, 读 `/proc/<pid>/cmdline` 的 `_is_our_daemon`)。spec 的 `stop` 流程只要求 "锁 -> 读 state -> 探活 -> SIGTERM -> 等 10 秒 -> 仍在则 `stop_failed`", 归属核对只见于 `serve` 的判定分支。实现方在 ISSUE-04 "实现取舍备注" 里主动请复核; 取向与 BR-008 (不静默接管) 一致, 风险低, 但确实是 spec 外的行为。
- B-4 `_dependency_lens` 同时接受两种边形状: `edges.dependencies` (TECHNICAL 定的 2.1 口径) 与 `edges` 直接是数组 (m23 实测 2.0 口径)。spec 只写前者。容错读取本身不改 merge 产物 (守 NG-006), 属 spec 外的宽容, 已在 ISSUE-03 交付证据声明。

## C 看似已实现但实现方式有误

### C-1 换端口报出的 `previous_url` 是回环地址, 不是用户手里的旧交付地址

- spec 原文:
  - `TECHNICAL.md` `state.json` 字段条: "`last_port`/`last_url` 与 `stopped_at` 让'已知停机'和'实例死掉的残留'可区分, **也是换端口时报告真实旧地址的依据** (m25 D018)"。
  - `DECISIONS.md` D018: "把 `pid` 置空并写 `stopped_at`, 保留 `port` 与 `last_url`, 于是 ... 换端口时能报出真实旧地址而不是假定旧端口是 8090"。
  - `PRODUCT.md` BR-019: "交付给用户的必须是局域网 URL (宿主已确认地址加实际端口), **不给 loopback 地址**, 不给文件路径"; AC-008: "而且 交付里没有回环地址, 主机名或文件路径"; BR-037: 交付消息的内容来自 `serve` 的"输出摘要"。
- 实现: `codemap_service.py` 行 431 每次启动把 `last_url` 写成 `_loopback_url(target_port)` = `http://127.0.0.1:<port>/`; 行 451 换端口时 `previous_url = old.get("last_url") or _loopback_url(old_last_port)`。因为 `last_url` 恒有值, 回退分支 ("旧端口加当前地址拼出") 永不触发, 于是 `previous_url` 永远是回环 URL。
- 实测证据: `/tmp/m26-04/manual_flow.txt` 第 [7] 步 `"previous_url": "http://127.0.0.1:18471/"`; 用例 `test_serve_lifecycle.py::test_tc_04_03` 与 `test_delivery_output.py::test_tc_05_04` 直接把 `state["last_url"]`/该回环值当期望值固定下来。
- 判断: 这不是任务书列出的三处已接受偏离, 而是 ISSUE-04 在"实现取舍备注"里挂起、留给 ISSUE-05 收口而没有收口的项 (ISSUE-05 的允许范围含"`codemap_service.py` 的输出组装", `_apply_delivery` 已经拿到解析后的地址与端口, 有条件把真实交付 URL 回写或据地址重算 `previous_url`, 但没做)。后果: 用户看到的"旧地址已失效"里给的是一个他从未用过的回环地址, 与 BR-019 的交付口径冲突, 也丢掉了 D018 要的"真实旧地址"。修法建议 (不改 spec 即可): `_apply_delivery` 组装 `url` 成功后把该 URL 写入 `state.last_url` (地址仍不入 state, `--address` 不入盘的纪律靠"只写组装后的 url 且下次 serve 按记录重算"把控), 或换端口时用 "旧端口 + 本次解析地址" 拼 `previous_url`。

## D 交付证据未覆盖契约声明, 或与验证契约不符

### D-1 ISSUE-06 声称的"错误码白名单断言防漂移"实际恒真 (空断言)

- 契约: ISSUE-06 验证入口 TC-06-01 的通过标准含"文档里出现的每个错误码与参数名都能在已实现代码里找到"; 交付证据写 "15 个全部在代码中, TC-06-01 用例里有白名单断言防漂移"。
- 实际: `tests/test_skill_docs.py` 行 142-149
  ```python
  unknown = tokens & { ...14 个错误码... } - KNOWN_ERROR_CODES
  assert not unknown, f"出现未知错误码样 token: {unknown}"
  ```
  `-` 的优先级高于 `&`, 表达式等价于 `tokens & ({...} - KNOWN_ERROR_CODES)`, 而左边集合是 `KNOWN_ERROR_CODES` 的子集, 差集恒为空, `unknown` 恒为空集, 断言永不失败。真正起作用的只有第 150-155 行的"关键错误码必须出现"子集断言。
- 分类: 检查虽然"通过"了, 但该断言没有验证任何东西, 不能作为"防漂移"的证据。低危 (信息层面), 但属证据与声明不符。

### D-2 ISSUE-06 未记录 BR-034 的第三条人工核验

- 契约: `EXECUTION.md` BR 覆盖矩阵 "BR-034 (审计) -> ISSUE-06 承接 -> TC-06-02 加 人工核验: frontmatter 有 `disable-model-invocation: true`, `agents/openai.yaml` 内容逐字等于两行最小配置, **全仓库检索无其它 skill 调用 codebase-map**"。
- 实际交付证据: ISSUE-06 记录了 frontmatter (TC-06-02 用例)、`agents/openai.yaml` 逐字核对、README diff、错误码与参数名核对, 但没有记录"全仓库检索无其它 skill 调用 codebase-map"这一步。
- 我复核该事实成立: `grep -rln "codebase-map"` 在 `workflow/`、`general/`、`tests/`、`pi/` 下除自身目录外只命中 `README.md` 的技能表行; 无 skill 调用它。
- 分类: 记录缺失 (不是检查未通过)。

### D-3 覆盖矩阵挂在 TC-003 名下的 "BR-001 首选端口 8090" 没有对应用例

- 契约: 覆盖矩阵 "BR-001 -> ISSUE-04 -> TC-003 (单例, 首选 8090) 加 TC-04-01"; BR-001 原文: "同一时刻只有一个实例, 占一个端口, **首选端口 8090**"。
- 实际: 全树所有 serve 用例都通过 `CodemapSrv.env()` 注入 `CODEMAP_PORT=<随机高位端口>` (测试隔离纪律要求, 正确), 因此没有任何用例在 `CODEMAP_PORT` 未设置时走到 `_preferred_port()` 的 8090 分支; 唯一与 8090 相关的断言是 `test_version_constants.py` 里 `DEFAULT_PORT == 8090` 的常量核对。
- 分类: 证据里声称的覆盖点不存在。实际行为 (`_preferred_port()` 未设 env 时返回常量) 由代码直读可确认正确, 但"首选 8090 生效"在自动化层没有观察点, 只能靠 ISSUE-07 宿主实跑。建议在证据里把这条改为"常量核对 + 归 ISSUE-07", 或补一条直接调 `_preferred_port()` 的小用例。

### D-4 TC-05-04 的断言对象与契约所指的对象不同源

- 契约: ISSUE-05 验证入口 TC-05-04: "`delivery_notes` 三类说明齐全且 `denominator_note` 里的文件数**等于最近一次 build 统计的依赖树文件数**"。
- 实际: `test_delivery_output.py::test_tc_05_04` 自己写一份伪副本 `write_cc_copy(srv.serve_root, KEY_DEMO, 4)` (4 个 File 节点), 再断言 note 里有 `demo-lib-ab12cd34.cc.json: 4`; 全程没有 build, 没有 build 的 `stats.files_in_tree` 参与。实现侧 `_delivery_notes` 也确实是从 serve-root 的副本现算 (`cma.files_in_tree_of`), 而不是取 build 的统计值。
- 分类: 用例通过的检查 (副本 File 节点数与 note 一致) 比契约要求的 (与 build 统计值一致) 弱; 由于副本是原件的逐字节拷贝, 两者数值在真实链路上应当相等, 但这条等价关系没有被任何证据观察到。建议证据里如实写明"以副本现算, 与 build 统计同口径函数", 或在 ISSUE-07 真实 build 后补一次对账。

### D-5 ISSUE-03 证据里的"全量 pytest 69 failed/100 errors"没有留下原始记录

- 契约: `verification-contract` 共用底线"记录证据"要求"记录对应要求, 入口操作与输入, 预期与实际结果, 未验证范围及**可复查的脱敏原始材料**"; `EXECUTION.md` 完成定义第 8 条要求全量 pytest 的环境缺口"不得伪记通过"。
- 实际: ISSUE-03 交付证据写 "全量 `uv run python -m pytest` 在容器内 69 failed/100 errors", 但 `/tmp/m26-03/` 只有 `pytest-codebase-map.txt` (59 passed) 与 `collect-only.txt`, 没有那次全量运行的输出。
- 分类: 结论本身诚实 (记成环境缺口不伪记通过), 但"69 failed/100 errors"这个具体数字无可复查材料, 按证据规则只能算未记录。

## E 待核实疑点 (需发起方裁决, 或需宿主证据才能定)

- E-1 `serve` 复用分支跳过 `no_data_keys` 前置。spec: BR-030 "`serve` 以状态清单与磁盘副本的交集判断有没有数据: 交集为空就报错并区分..." 与 TECHNICAL "`serve` 前置: 状态清单与磁盘副本的交集非空 (否则 `no_data_keys` ...)"; 实现只在 `_start_service` 里调用 `_no_data_keys_error` (行 383), 复用分支 (`_serve_core` 行 527-547) 不复查。后果: 服务活着时副本被删, `serve` 仍成功返回, 只是 `keys` 为空并给 `notes` 提示。是否可接受取决于"前置"是否也约束复用分支; 现有用例 (TC-04-10) 只覆盖停服状态。
- E-2 `build` 全程持锁, 与 TECHNICAL 声明的锁覆盖范围不一致。TECHNICAL 文件锁条: "覆盖 serve 启动/复用, build 的**副本复制与 `data_keys` 更新**, stop 全过程", 非功能要求是"单次调用只有一个进程改动运行时状态 (文件锁)"; 实现 (`run_build` 行 711-713) 在进入初始化与三次 podman run 之前就取锁, 一直持有到结束。按 m23 量级 (单步约 26 秒) 一次 build 可能持锁数十秒到数分钟, 期间 `serve`/`stop` 会等 30 秒后报 `internal_error`。这既超出 spec 的覆盖声明, 也让"build 与服务互不干扰"这一使用预期变差。不是规格禁止的, 但值得裁决: 要么把锁收窄到写阶段, 要么在文档/规格里承认 build 期间 serve 会被挡住。
- E-3 交付消息里没有 BR-025/D004 要求的"未解析扩展名"说明。BR-025: "ccsh 没解析出依赖的语言只在命令输出与**交付消息**里说明"; D004: "未解析语言的说明放在 `build` 输出与交付消息里, 逐项写出本次没进依赖树的扩展名与原因"。实现里 `unsupported_extensions` 只出现在 `build --json`/build 摘要, `serve` 的 `delivery_notes` 只有三类说明 (level_hint/integrity_note/denominator_note), 没有扩展名维度。`EXECUTION.md` 把 BR-025 归给 ISSUE-03 与 ISSUE-07, 与 AC-006 场景里"输出与交付消息里"的措辞有张力; 是执行计划刻意的裁决还是漏项, 需发起方定。
- E-4 AC-001 的"说明"句在 build 输出里缺席。AC-001 (统计与分母场景) 要求 build 输出"说明测试目录与 build 目录默认不扫"、"说明零声明文件不进依赖树"、"把分析端自带的忽略规则单列为 `工具默认过滤` 一类"; 实际 build 输出只有 `stats.excluded.{tests,build_dirs,tool_defaults}` 计数与 `zero_declaration` 清单, 没有这三句说明; 三句白话说明只存在于 `serve` 的 `delivery_notes.denominator_note` 与 SKILL.md。若认为"字段结构即说明"则满足, 若按"输出说明…"的字面读则不满足。相关发现同 E-3 属同一类边界, 建议一起裁决。

## F 三处已接受偏离的守边界判断

- F-1 SKILL.md 并入 m21 既有文件而非新建: 守住意图。m21 章节 (`tools/build-zh.sh`, `tools/stage.py`, `i18n/`, `README.md`) 完整保留为独立一节, v1 三子命令成为主体; AC-009 的全部文本要件 (三子命令职责与调用式, 三者不合并与 stop 语义, 交付纪律三类说明, 清理入口与不自动删除, 复原步骤, 版本口径, 官方英文原版) 逐条在位, `check_skill.py` 通过, `_serve-daemon` 没有出现在文档里。新增的一句"首次初始化会把 serve-root 前端整体换成官方英文版, 要用汉化界面需之后用 `tools/stage.py frontend` 重新铺设"属 spec 外的如实交代, 我按实际代码核对了 `_ensure_frontend` + `sync_frontend_to_serve_root` 的行为, 与 m21 `stage.py` 只写 serve-root、不写 `cache/cache.json` 的事实吻合, 结论成立。唯一可议的是这句让 v1 文档承担了 m21 互操作说明 (轻微范围蔓延), 建议保留。
- F-2 两处用例改写: 守住意图。`test_cli_output_shape.py` 只是给两个形状用例加了不含 podman 的 `PATH`, 断言 (恰一行 JSON / 多行摘要 + stderr 下一步 + 退出码 1) 逐字未变, 失败出口从"流水线未接线"换成同为前置检查失败的 `podman_missing`, 不掩盖问题; `test_serve_and_stop_registered_since_issue_04` 把"本期未注册"的临时断言换成注册冒烟 (stop 幂等成功 + serve 空目录报 `no_data_keys`), 而"serve/stop 能注册且走前置检查"正是 ISSUE-04 自己契约里的交付物, 该断言没有删掉, 只是升级。
- F-3 ISSUE-03 把 ISSUE-02 的临时守卫翻转成必带字段: 守住意图。`assert_full_build_fields` 由"`gate`/`stats`/`serve_copy_path` 不得出现"改为"必带且门禁通过", 对应 ISSUE-03 的交付物; 同时 `TC-02-02` 的 merge 产物断言从 `{"stub","run"}` 改为 `stub_run` 序号, 原因是内置 stub 产物必须变成能表达 `lenses` 的合法形状 (否则门禁无法判定), 变更理由与影响面在证据里写清, 其余 TC-02 用例逻辑未动, 我逐条对过 diff。

## G 已核对通过 (不复述细节, 供发起方确认覆盖面)

- `codemap_common`: 键命名与清洗 (空格/非法字符逐个换 `-`、折叠、去首尾、空回 `repo`、realpath sha256 前 8 位), 运行时目录 (`CODEMAP_RUNTIME_DIR` 覆盖 + 0700), 默认排除集七项与 glob→`-e` 正则转义单一来源, 六个版本常量的值, 地址解析顺序与不采项, 与 BR-011/BR-032/BR-015/BR-019/BR-020/D005/D011/D017/D019 一致。
- `codemap_analyze`: 三步 ccsh 参数逐字符合 TECHNICAL; `podman run` 固定参数 (`--rm --network=none --userns=keep-id`, `:/proj:ro`, `cache/work:/out`) 符合 BR-017; 单架构 digest 阻断、多架构只记录进 `cache/cache.json` 符合 D013/D016; 前端 sha256 校验与整体替换不叠加符合 BR-028/m13 D030; 原件逐字节写 `<target>/.codebase-map/cc.json` 且不改字段; 门禁 `edges>0 且 level_kinds>=3` 与失败出口 (`gate_failed` + 原件照写 + 不复制副本 + stats/初始化照常) 符合 BR-022/D001; 统计五类归因与 `zero_declaration` 等式可对账, `tool_defaults` 单列符合 BR-024/BR-025/D019; 副本 `os.replace` 且与 `index.html` 同目录、不动其它库副本符合 BR-010/BR-012/BR-036。
- `codemap_service`: 13 个 state 字段与 0600/0700 权限、原子写、flock 30 秒、三步探活、`state_mismatch` 两种死法、`port_in_use` 不顺延、`instance_running`、`last_port` 沿用、stop 幂等与留痕、`ThreadingHTTPServer` 只读 + `resolve()`+`relative_to` 越界 404 + 无 listing + 无写接口, 均与 BR-001..BR-009/BR-029/BR-030/TECHNICAL 一致; `stop` 不自动 SIGKILL。
- `codebase-map.py`: 三子命令注册、前置检查顺序 (`container_not_supported` → `target_missing` → `podman_missing`)、`--json` 单行与人类可读两形态、退出码 0/1 (`argparse` 2)、`serve --address` 只作用本次。
- 交付面: `url`/`base_url`/`keys[].url` 形状、缺地址时 `BLOCKED` 首行 + 退出码 0 + 不给 url + 候选全 IPv4 非回环、`keys` 为交集且缺失/未登记两类提示、`--address` 不落盘不回写、`delivery_notes` 三句、交付一致性 (端口三方一致), 与 AC-002/AC-008/BR-019/BR-030/BR-037 一致。
- 工程纪律: `scripts/*.py` 仅标准库加同目录模块 (静态守卫 + 我人工过一遍 import 清单); `pytest.ini` 只在 `tests` 之前插入一行; `README.md` 只改一行; 仓库内无 `.cc.json`/`web.zip`/前端解包产物; 测试全部用隔离运行时目录与高位端口, 未占用 8090, 复跑后无残留 `_serve-daemon`。
- 宿主未验证项在 ISSUE-01..06 的交付证据里都记成了未验证 (真实 build/初始化、真实渲染、局域网设备、长期常驻、全量 pytest、`target_missing`/`podman_missing`/`image_unavailable`/`frontend_unavailable` 宿主构造), 没有用 stub 或截图顶替, 符合 m25 D016 的验证分工。

## 处置建议 (按优先级)

1. C-1 换端口 `previous_url` 上报回环地址: 在交付层收口, 并把两条用例的期望值改成"真实交付 URL"。
2. A-1 `podman_missing` 文案补齐 "本机没有 podman"; A-2 换端口输出补"旧地址已失效"措辞。
3. D-1 修 `test_skill_docs.py` 的空断言; D-2/D-3/D-4/D-5 在证据里补记录或改口径。
4. E-1..E-4 由发起方裁决是否算漏项; B-1..B-4 决定保留还是收窄。

未发现需要修改 spec 或改代码才能判断的阻塞项, 因此没有停机上报。
