# REWORK-03 发起方裁决的四条口径

## 父级
- `../../milestone-26/REVIEW-spec.md` (E-1, E-2, E-3, E-4)
- `../../milestone-25/{PRODUCT.md,TECHNICAL.md,DECISIONS.md}`

## 裁决来源
发起方 2026-11-01 明确答复"四小: 按你建议", 即采纳下列四条, E-2 明确放弃改锁只补文档.

## 执行
- [x] 已完成
- [x] 派工前复核: HEAD=436b842 (issue/rw03); `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数 = 79.

## 要交付什么

1. **E-1 serve 复用分支也复查 `no_data_keys`**: 当前只有启动路径报, 存活复用分支不查. 改为两条路径都按 `state.data_keys` 与 serve-root 实际 `.cc.json` 交集判定, 交集为空时报 `no_data_keys` (两类文案沿用: 都没 build 过 / 副本已删建议重新 build), 退出码非 0, 且**不改动正在运行的服务** (不 stop, 不重启). 补用例: 先正常起服务, 删光 serve-root 的副本, 再 `serve` -> 非 0 且 `error.code == "no_data_keys"`, 服务原进程仍在 (GET / 仍 200).
2. **E-2 build 持锁窗口写进文档**: 不改锁实现. 在 `workflow/codebase-map/SKILL.md` 加一节说明: `build` 全程持锁, 分析一个库期间 `serve`/`stop` 会等待, 超过 30 秒报 `internal_error`; 建议错开时间操作. 文案要与实现一致 (锁等待 30 秒).
3. **E-3 交付消息补"未解析扩展名"说明**: `build` 的 `unsupported_extensions` 要进交付消息.
   - `state.json` 的 `data_keys` 每项增加 `stats` 子对象, 至少含 `files_in_tree` 与 `unsupported_extensions` (与 build 时写进 `build --json` 的同源数据), 由 `build` 在锁内写入.
   - `serve --json` 的 `delivery_notes` 增加第 4 个字段 `unparsed_note`: 逐库列出"没进依赖树的扩展名与其数量"; 某库没有未解析扩展名时写明"没有未解析扩展名"; 记录里缺 `stats` (老数据) 时写明"该库缺少统计记录, 重新 build 可补".
   - 人类可读形态同样铺开该字段.
   - `SKILL.md` 的交付纪律由"三类说明"改为"四类说明", 并说明 `unparsed_note` 是第 4 类.
   - 补用例覆盖: 有未解析扩展名 / 无未解析扩展名 / 老数据缺 stats 三种.
4. **E-4 build 输出补 AC-001 的三句说明**: `build` 的人类可读输出与 `build --json` 都加这三句 (措辞与 SKILL.md 的分母口径一致): (a) 测试目录与 build 目录默认不扫; (b) 零声明文件不进依赖树; (c) 分析端自带的忽略规则单列为"工具默认过滤". JSON 放在 `stats.notes` (字符串数组, 固定三句), 人类可读输出逐行打印. 补用例断言三句在两种形态都出现.

## 允许范围
`workflow/codebase-map/scripts/{codemap_analyze.py,codemap_service.py}`, `workflow/codebase-map/tests/`, `workflow/codebase-map/SKILL.md`.

## 禁止范围
不改锁实现 (E-2 明确不改); 不改门禁阈值; 不改地址解析与 `--address` 不落盘纪律; 不把裸地址写进 state.json; 不改 m21 的 tools/ 与 i18n/; 不动 PRODUCT/TECHNICAL/DECISIONS 原文 (与原文的差异写进交付证据); 不放宽既有断言.

## 验证契约
- 变更类型: 行为变更 (E-1/E-3/E-4 的对外输出与错误出口) 加 非行为改动 (SKILL.md 文档).
- 验证要求/证据: 逐项命令与输出; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests` 全绿无 skip; 收集条数增量 = 新增用例数; `check_skill.py` OK; 证据目录 `/tmp/m26-rw03/`.

## 交付证据

复核与验证均在本工作树 (issue/rw03) 完成; 原始记录在 `/tmp/m26-rw03/` (collect-count.txt, pytest-full.txt, check_skill.txt, e1-e3-tests.txt, e4-e2-tests.txt).

### 总验证

- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests` : 85 passed, 0 failed, 0 skipped, 退出码 0.
- collect 条数: 79 -> 85, 增量 6 = 新增用例数 (E-1 一条, E-3 三条, E-4 一条, E-2 文档一条).
- `uv run python general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md` : OK.

### E-1 serve 复用分支复查 no_data_keys

- 做了什么: 存活复用分支在返回成功前同样调用 `_no_data_keys_error` 按 `state.data_keys` 与 serve-root 实际 `.cc.json` 交集判定, 交集为空报 `no_data_keys` 退出码非 0; 只报错返回, 不 stop 不重启不改写 state.json. 两类文案沿用启动路径同一函数.
- 落点: `workflow/codebase-map/scripts/codemap_service.py` 行 581-588 (复用分支复查), 行 399 (启动路径原有), `_no_data_keys_error` docstring (行 263-269) 写明两路径同口径.
- 用例: `tests/test_serve_lifecycle.py::test_e1_reuse_branch_rechecks_no_data_keys_and_keeps_service` (行 195): 起服务 -> 删光副本 -> 再 serve 断言非 0 且 `error.code == "no_data_keys"` 且文案含"副本已删", 守护 pid 不变, GET / 仍 200, state.json 逐字节未变.

### E-2 build 持锁窗口写进文档

- 做了什么: 不改锁实现; SKILL.md 加 "## build 持锁窗口" 节: build 全程持锁, 分析期间 serve/stop 会等锁, 超过 30 秒报 internal_error, 建议错开时间操作; 与实现一致 (`LOCK_WAIT_SECONDS = 30`, `run_build` 取锁到释放覆盖全程).
- 落点: `workflow/codebase-map/SKILL.md` 行 38-40.
- 用例: `tests/test_skill_docs.py::test_tc0601_build_lock_window_documented` (行 162).

### E-3 交付消息补未解析扩展名说明

- 做了什么:
  - build 在锁内给 `state.json.data_keys` 条目加 `stats` 子对象, 至少含 `files_in_tree` 与 `unsupported_extensions`, 与 `build --json` 的 stats 同源 (同一 `compute_stats` 产物取子集).
  - `serve --json` 的 `delivery_notes` 加第 4 字段 `unparsed_note`: 逐库列出没进依赖树的扩展名与数量 ("<键>: 没进依赖树的扩展名 .md x2"); 没有未解析扩展名写明"没有未解析扩展名"; 记录缺 stats (老数据) 写明"该库缺少统计记录, 重新 build 可补".
  - 人类可读形态同字段原样铺开 (human_summary 与 --json 共用同一结果 dict, 由用例直接断言).
  - SKILL.md 交付纪律"三类说明"改"四类说明", 写明 `unparsed_note` 是第 4 类.
- 落点: `scripts/codemap_analyze.py` 行 817-822 (data_keys.stats 锁内写入), 行 664-673 (`_update_data_keys` docstring); `scripts/codemap_service.py` 行 635-657 (`_unparsed_parts`), 行 659-687 (`_delivery_notes` 四类), 行 705-724 (`_apply_delivery` 接线); `SKILL.md` 行 45-49.
- 用例: `tests/test_delivery_output.py::test_tc_05_06_unparsed_note_lists_unsupported_extensions` (行 273, 有未解析扩展名 + 人类可读形态), `::test_tc_05_07_unparsed_note_states_none_when_no_unsupported` (行 300, 无未解析扩展名), `::test_tc_05_08_unparsed_note_missing_stats_legacy_data` (行 313, 老数据缺 stats); 另 `tests/test_gate_stats_and_copies.py` 行 172-174 (TC-005 内断言 data_keys.stats 与 build --json 同源).
- 与规格原文的差异 (对 TECHNICAL 的扩展, 按返工单口径备案): TECHNICAL "serve --json 字段" 节把 `delivery_notes` 定为三个字段 (level_hint/integrity_note/denominator_note), 本条按裁决扩为四个 (加 unparsed_note); TECHNICAL 的 data_keys 条目字段清单 (key/source_cc_json/built_at/bytes) 未列 stats 子对象, 本条按裁决加 stats (至少含 files_in_tree 与 unsupported_extensions). PRODUCT AC-005 场景文字仍是"三类说明", 未改 PRODUCT 原文, 差异即本条.

### E-4 build 输出补 AC-001 三句说明

- 做了什么: `compute_stats` 的 stats 加 `notes` 字符串数组, 固定三句 (措辞与 SKILL.md 分母口径及 serve denominator_note 同一措辞): "测试与 build 目录默认不扫." / "零声明文件不进依赖树." / "分析端自带忽略规则单列为工具默认过滤."; `build --json` 与门禁失败路径的 stats 都带 (门禁失败 stats 照常完整输出); 人类可读输出逐行打印 (每句一行 "说明: " 前缀).
- 落点: `scripts/codemap_analyze.py` 行 529-537 (STATS_NOTES 常量), 行 640 (stats.notes); 人类可读逐行在 `scripts/codemap_common.py` 行 276-283 (human_summary 的 stats.notes 分支).
- 用例: `tests/test_gate_stats_and_copies.py::test_e4_build_notes_three_denominator_sentences_in_both_forms` (行 422) 断言三句在两种形态都出现且逐行; `assert_stats_complete` (行 113-119) 扩入 notes, 随 TC-005/TC-006 系列覆盖成功与门禁失败两路径.
- 与规格原文的差异: TECHNICAL "build --json 字段" 节的 stats 字段清单未列 notes, 本条按裁决加 `stats.notes` (固定三句); 这是裁决新增, 非原文已有. 另外, 逐行打印必须发生在输出编码层, 故改了 `codemap_common.py` 的 `human_summary` (带 stats 键守卫, serve/stop 结果无 stats 键不受影响) - 这是超出返工单"允许范围"文件清单的一处 (清单只列 codemap_analyze.py/codemap_service.py), 非停止条件清单项, 特此备案.

### 既有断言的更新 (非放宽)

- `tests/test_delivery_output.py::test_tc_05_04` 的 `set(notes)` 断言由三个字段扩为四个 (加 unparsed_note), 并加老数据形态的第 4 类文案断言; `test_tc008` 的交付说明齐全断言同步加 unparsed_note.
- `tests/test_gate_stats_and_copies.py::assert_stats_complete` 的 stats 字段集扩入 notes (E-4 规定新增字段).
- `tests/test_skill_docs.py::test_tc0601_delivery_discipline` 加四类说明断言 (原有三短语断言保留).
- 均为按裁决新增字段的扩展, 未删除或放松任何既有断言, 未加 skip/xfail.

## 停止条件
需要改锁实现或门禁阈值; 需要真实 podman/出网; 需要在 state.json 里加地址字段. 遇到停手并 mailbox request 上报.
