# milestone-26 执行报告 (容器侧, 未含宿主取证)

任务标识: SWT-M26. 分支 `refactor-skill-around-verification`, 集成提交 `8c4b738` (未推送, 本地领先 origin 20 个提交).
产物: `workflow/codebase-map/` 的 v1 (分析服务三子命令), 加 `pytest.ini` / 根 `README.md` 各一行, 加 `workflow/codebase-map/SKILL.md` 并入 v1 文档.

## 1 交付对象

`workflow/codebase-map/scripts/` 新增四个脚本:
- `codemap_common.py`: 数据键 (库名清洗 + realpath sha256 前 8 位), 运行时目录 (`CODEMAP_RUNTIME_DIR`, 默认 `~/.agents/codebase-map`), 默认排除集与 glob->`-e` 正则单一来源, 版本常量, 地址解析 (记录文件只读, 不采 SSH/主机名/回环).
- `codemap_analyze.py`: 首次初始化 (拉镜像 + 校验单架构 digest, 下官方 `vis-2.9.1` web.zip + sha256, 解包整体同步 serve-root), 三步 `podman run` (`--rm --network=none --userns=keep-id`, 源码 `:ro`), 门禁 (`edges>0` 且 `level_kinds>=3`), 统计归因 (五类排除 + 零声明), 原件写 `<target>/.codebase-map/cc.json`, 副本 `os.replace` 进 serve-root, `data_keys` 锁内更新.
- `codemap_service.py`: 运行时目录与 flock(30s), `state.json` 13 字段原子写 0600, 三步探活, 端口决策 (`--port` -> `last_port` -> 8090, 不顺延), 换端口报旧地址, 守护子进程, 只读静态服务 (越界与根外软链 404), `stop` (SIGTERM + 10s, 不 SIGKILL), 交付输出 (`url`/`keys` 交集/`delivery_notes` 三类说明/地址缺口与候选).
- `codebase-map.py`: `build`/`serve`/`stop` 三子命令, 两种输出形态, 退出码 0/1, 15 个稳定错误码.

`workflow/codebase-map/tests/`: 79 个用例, 不依赖 podman 与出网 (stub podman 只证明参数构造与接线).

## 2 逐项改动与落点提交

| 项 | 内容 | 落点 |
| --- | --- | --- |
| ISSUE-01 | 共享规则 + `build` 前置检查与错误信封 + 新测试树 + `pytest.ini` 接线 | `7f6fd4e` (分支提交 `ab4e272`, `4297636`) |
| ISSUE-04 | 常驻服务与运行时状态 (锁/state/探活/端口/stop/HTTP 面) | `72b04e8` |
| ISSUE-02 | 首次初始化与三步分析流水线 | `22e25e0` |
| ISSUE-03 | 门禁判定, 统计分母与副本分发 | `db3be1e` |
| ISSUE-05 | 地址解析与 serve 交付输出 | `8abfee8` |
| ISSUE-06 | `SKILL.md` 并入 v1 文档, README 行, 元数据核对 | `5c2311a` |
| REWORK-01 | 评审 7 项: `podman_missing` 文案, 换端口失效文案, 真实旧地址, 恒真断言, 测试映射, m21 手册过期陈述, 死代码收窄 | `6856e15` |
| REWORK-02 | 复审 6 项: A-1 用例 PATH 构造可移植性, docstring/映射/覆盖补强 | `8c4b738` |

## 3 验证结果 (容器内可复跑部分)

- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests` -> 79 passed, 退出码 0, 无 failed 无 skipped.
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` -> 944 条 (基线 865 + 79); 既有两树与根树条数与基点逐树一致.
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py` -> 1 passed.
- `uv run python general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md` -> OK.
- 既有两树混跑核对 (影响复查实跑): `workflow/navigate/tests general/present/tests` -> 136 passed, 4 skipped (既有容器条件跳过).

未验证 (环境缺口, 未用替身顶替): 真实库 build 与门禁统计, 真实初始化 (拉镜像/下 web.zip), 真实 3D 与依赖视图渲染, 局域网设备打开交付 URL, 长期常驻, 全量 `uv run python -m pytest` (根 `tests/` 需宿主 podman), `target_missing`/`podman_missing` 的宿主构造.

## 4 复核轨迹

- 旧行为影响复查: `IMPACT-REVIEW.md` (1 轮), 0 项建议返工; 逐树计数、conftest 预载纪律、m21 资产零改动、四处测试调整均核对为"只增不减".
- 双轴评审: `REVIEW-standards.md` (硬性违规 2, 已证实缺陷 1, 判断性 23), `REVIEW-spec.md` (缺失 2, 蔓延 4, 方式有误 1, 证据不符 5, 疑点 4). 采纳并修掉其中 7 项 (REWORK-01), 其余按"待发起方裁决"或"判断性发现"处理.
- 返工复审: `REVIEW-rework.md` (1 轮), 7 项全部确认修好, 新发现 7 条可移植性/覆盖问题, 其中 P-1 已修 (REWORK-02), P-2..P-7 同批处理.
- 未做: 独立核验 (`verify-change`). 原因: 该流程要求按已确认 `PRODUCT.md` 逐项实跑成品入口, 而本容器无 podman 无出网, 关键路径全部无法实跑, 报告只能以未验证收尾; 待宿主取证时一并做更有效.

## 5 缺口与待决

1. **ISSUE-07 宿主取证未执行**: 真实库 build/门禁/分母, 真实初始化, 3D 与依赖视图渲染, 局域网设备真实打开, 长期常驻, 目标库 `git status` (BR-031), 宿主构造的错误分支. 需要用户指定一个真实 Java 库 (BR-026), 在宿主上执行.
2. **评审待裁决四条** (未动, 需产品口径): E-1 `serve` 复用分支不再复查 `no_data_keys`; E-2 `build` 全程持锁 (超出 TECHNICAL 声明的锁覆盖范围, 期间 `serve`/`stop` 可能等 30s 后报 `internal_error`); E-3 交付消息缺"未解析扩展名"说明 (BR-025/D004); E-4 `build` 输出缺 AC-001 的三句"说明"句.
3. **返工复审疑点**: Q-1 宿主是否 `/usr/bin/podman` (已按最坏情况修好用例); Q-2 宿主是否允许非特权 user namespace (A-1 用例前置); Q-3 `last_url` 是否允许含已确认地址的 URL (现按返工单做法: 只写组装后的 URL, `--address` 值不入盘); Q-4 `previous_url` 可省略是否补进规格文档; Q-5 无 userns 环境是否允许该用例 skip.
4. **D-2/D-5 证据补记未做**: BR-034 第三条人工核验 (全仓检索无其它 skill 调用 codebase-map) 与全量 pytest 原始记录, 属记录缺失而非检查未通过.
5. **未推送**: 本地领先 origin 20 个提交, 等验收后再推.
