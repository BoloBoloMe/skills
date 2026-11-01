# REWORK-03 发起方裁决的四条口径

## 父级
- `../../milestone-26/REVIEW-spec.md` (E-1, E-2, E-3, E-4)
- `../../milestone-25/{PRODUCT.md,TECHNICAL.md,DECISIONS.md}`

## 裁决来源
发起方 2026-11-01 明确答复"四小: 按你建议", 即采纳下列四条, E-2 明确放弃改锁只补文档.

## 执行
- [ ] 已完成
- [ ] 派工前复核: HEAD; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数.

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

## 停止条件
需要改锁实现或门禁阈值; 需要真实 podman/出网; 需要在 state.json 里加地址字段. 遇到停手并 mailbox request 上报.
