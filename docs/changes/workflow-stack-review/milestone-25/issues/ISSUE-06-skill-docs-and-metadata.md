## 父级
- `../EXECUTION.md`

## 执行
- [x] 已完成
- [ ] 派工前复核并记录 (写在本行下方): HEAD 提交号; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数; `workflow/codebase-map/` 当前存在哪些文件.
- HEAD: `8abfee80d6a014d59a39a9d53e7b17ea15b91a89` (分支 issue/06, 与基点一致, 已含 ISSUE-01..05).
- 收集条数: 930.
- `ls workflow/codebase-map`: README.md, SKILL.md, agents, i18n, scripts, tests, tools (SKILL.md 与 m21 资产已存在, 见交付证据的差异说明).

## 要交付什么
让这个 skill 可被一个全新的调用会话照文档用起来, 不用猜:

- `workflow/codebase-map/SKILL.md`: frontmatter 为 `name: codebase-map`, 单行 `description`, `disable-model-invocation: true`. 正文至少覆盖:
  - 三个对外子命令各自的职责与调用式 `python3 <skill 目录>/scripts/codebase-map.py <build|serve|stop> ...` (宿主有 uv 时 `uv run python ...` 等价), 三者不合并, `stop` 没有"只停某一个库"的语义; `_serve-daemon` 是内部入口, 不写成对外子命令.
  - 用法与例子: `build <目标目录> [--exclude <glob>]... [--json]`, `serve [--port <N>] [--address <IP>] [--json]`, `stop [--json]`, 并说明 `--port` 只在没有存活实例时生效 (有实例要 `stop`), `--address` 只作用本次.
  - 地址来源与缺值出口: 已确认地址记录 `~/.agents/sandbox-worktree/lan-address`, 缺值时 `serve` 报阻塞并给候选, 用户确认后用 `serve --address <已确认地址>` 重新交付; 不猜地址, 不回写该文件.
  - 交付纪律: 交付局域网 URL 与每个数据键的完整 URL; 交付消息原样转述 `serve` 输出摘要里的三类说明 (层号/环/向上依赖在官方依赖视图看; 依赖抽取完整性未量化; 分母口径), 不改写数字与判断, 不说分层完全可信.
  - 失败出口清单: 每个错误码对应的下一步动作 (容器内不支持; 装 podman; 补网络; 处理端口占用; 先 build; 状态不一致交用户裁决).
  - 状态复原步骤: 删掉 `~/.agents/codebase-map/` 等于放弃当前实例, 复原 = 重新 `serve` (副本还在则原地复用) 或重新 `build`.
  - 数据副本清理入口: 手动删 `serve-root` 下对应 `.cc.json` 或整个目录重建; 工具不会自动删除任何库的副本, 也没有"只留最近一个"的清理.
  - 版本说明: 分析端 `codecharta/codecharta-analysis:2.3.0`, 版本以单架构清单 digest 核对 (多架构清单只记录); 前端为官方 `vis-2.9.1` 英文原版, v1 不做汉化.
  - 使用纪律: 无认证无 TLS, 只分析愿意公开的库, 不把仓库根或敏感目录当目标.
- `workflow/codebase-map/agents/openai.yaml`: 内容固定两行 `policy:` / `  allow_implicit_invocation: false`.
- `README.md`: 工作流技能表加一行 `codebase-map` (说明它做什么, 与既有行同样的措辞粒度).
- 新测试树补文本契约用例.

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-25/PRODUCT.md`, AC-009 (四个场景: 三子命令职责与调用式; 交付纪律三类说明; 清理数据副本入口与不自动删除; 第一版是官方英文原版); BR-013, BR-018, BR-019, BR-020, BR-023, BR-024, BR-028, BR-034 (审计), BR-036, BR-037; G-002, G-005, G-006, NG-001, NG-002, NG-009.
- Technical: `docs/changes/workflow-stack-review/milestone-25/TECHNICAL.md`, 模块划分 (`SKILL.md`, `agents/openai.yaml`, `README.md` 三行), 安全策略 (传输与访问, 停止与清理), 非功能要求 (可诊断的文档面向).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-25/DECISIONS.md`: D002, D004, D006, D011, D017, D018, F006.
- `docs/changes/workflow-stack-review/milestone-13/DECISIONS.md`: D001, D009, D010, D027.
- `docs/changes/workflow-stack-review/milestone-24/DECISIONS.md`: U003.

## 允许范围
同全局, 增量: `workflow/codebase-map/SKILL.md`, `workflow/codebase-map/agents/openai.yaml`, `README.md` 一行, 本 issue 的文本契约用例.

## 禁止范围
- 不在文档里新增实现未提供的能力或开关 (`--include-tests`, `--no-aggregate`, 自定义指标参数等).
- 不写实现细节式教程 (代码结构, 函数名); 文档只讲用法, 交付纪律, 失败出口, 复原与清理.
- 不改 `docs/language/UBIQUITOUS_LANGUAGE.md` 与 ADR-0026 (m25 D011 已在本节点完成).
- 不把被分析库的完整路径或库名写进文档示例 (用 `demo`, `other` 这类中性名).
- 不加第二份 skill 文档 (例如另一个 `README.md` 或 `USAGE.md`), 唯一操作入口是 `SKILL.md`.

## 代码定位提示
- frontmatter 硬约束看 `general/writing-for-llm/check_skill.py` (name 与目录一致, description 单行, 可用 `disable-model-invocation`).
- 元数据契约与既有形状: `workflow/navigate/agents/openai.yaml` (两行最小配置), `workflow/navigate/SKILL.md` 的写法, 仓库测试 `tests/test_skills_codex_metadata.py` 的断言.
- README 表格位置: `README.md` 的技能表, 现有一行示例在 navigate 那行附近 (约 54 行).
- 文档要写的错误码清单来自已实现代码 (`codebase-map.py` 的错误码集合), 不照抄 TECHNICAL 之外的码.

## 验证契约
- 变更类型: 行为变更 (SKILL.md 是操作入口, 改它等于改实际操作方式, 按 skill 规则不属非行为改动) 加 非行为改动 (`agents/openai.yaml` 接线与 README 一行).
- 对应范围: 文档文本契约, 元数据两行配置, README 表格行.
- 验证要求/证据: 逐条验证 AC-009 四场景里能靠文本判定的三条 (第四条英文原版要靠宿主渲染, 归 ISSUE-07); 证据为 `check_skill.py` 输出, metadata 测试结果, 文本契约用例输出, 以及 `README.md` 的 diff.

## 验证入口
- `uv run python general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md`; 通过标准 输出 OK 且退出码 0.
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py`; 通过标准 1 passed (新增 skill 的 frontmatter 与 `agents/openai.yaml` 合规; 若该测试对其他 skill 也报错, 说明改坏了既有文件, 停下排查).
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests`; 通过标准 退出码 0 且无 failed. 本 issue 新增用例:
  - TC-009 (AC-009 主用例): 文档同时出现三个子命令的职责句 (build 只分析并产出; serve 起或复用并交付局域网 URL; stop 停整个服务), 出现"三者不合并"与"stop 没有只停某一个库的语义", 出现调用式 `python3 <skill 目录>/scripts/codebase-map.py`, 且不把 `_serve-daemon` 列成子命令.
  - TC-06-01 (交付纪律与清理与复原): 文档要求交付局域网 URL 加每个键的完整 URL, 要求交付消息带三类说明 (层号在依赖视图看 / 依赖抽取完整性未量化 / 分母口径), 要求原样转述不改写数字, 写明清理副本的入口并写明工具不会自动删除其它库副本, 写明删运行时目录的复原步骤, 写明版本口径 (镜像 tag 加单架构 digest 核对, 前端 `vis-2.9.1` 英文原版).
  - TC-06-02 (元数据): `SKILL.md` frontmatter 含 `disable-model-invocation: true` 且 `name` 等于目录名; `agents/openai.yaml` 内容逐字等于两行最小配置; `README.md` 技能表含指向 `workflow/codebase-map/SKILL.md` 的一行.
- 未自动化: AC-009 的"界面文案是官方英文原版, 页面版本显示 vis-2.9.1" 只能在宿主真实渲染时观察, 归 ISSUE-07; 文档侧只用 TC-06-01 断言写了版本口径.
- 通过标准 (整体): 三条命令全绿; 文档里出现的每个错误码与参数名都能在已实现代码里找到; 没有未实现的开关.

## 交付证据

- `uv run python general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md` -> `workflow/codebase-map/SKILL.md: OK`, 退出码 0.
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py` -> `1 passed`, 退出码 0.
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests` -> `75 passed`, 退出码 0, 无 failed 无 skipped (基线 65 + 本 issue 新增 10).
- 收集基线核对: 派工前 930 -> 改后 940, 增量 10 = 本 issue 新增用例 10 条 (test_skill_docs.py: TC-009 主用例 1 加参数面 1, TC-06-01 5, TC-06-02 3), 逐条对上.
- README diff: 技能表 codebase-map 一行改为 "代码库结构与依赖可视化: 分析+常驻服务 (build/serve/stop 三子命令), 只由用户手动调用.", 其余正文未动.
- agents/openai.yaml: 已存在且逐字等于 `policy:\n  allow_implicit_invocation: false\n`, 核对未改 (任务书说新建, 实际已存在).
- 错误码逐条核对 (文档出现 -> 代码位置): `container_not_supported`/`target_missing`/`podman_missing` -> codebase-map.py 前置检查; `image_unavailable`/`image_digest_mismatch`/`frontend_unavailable`/`frontend_hash_mismatch`/`gate_failed` -> codemap_analyze.py (_AnalyzeError); `no_data_keys`/`port_in_use`/`instance_running`/`state_mismatch`/`stop_failed`/`internal_error` -> codemap_service.py; `no_confirmed_address` -> codemap_common.py resolve_delivery_address (address_missing.code); 15 个全部在代码中, TC-06-01 用例里有白名单断言防漂移.
- 参数名逐条核对: `build`/`serve`/`stop`/`--exclude`/`--json`/`--port`/`--address` -> codebase-map.py argparse; `delivery_notes`/`address_missing`/`candidates`/`last_port` -> codemap_service.py; `no_confirmed_address` -> codemap_common.py; `stats` -> codemap_analyze.py build --json 组装; `8090` -> codemap_common.DEFAULT_PORT; `serve-root`/`cache` -> codemap_common.RUNTIME_SUBDIRS 与 `cache/frontend/` (codemap_analyze.py); `~/.agents/codebase-map/` -> runtime_dir 默认; `~/.agents/sandbox-worktree/lan-address` -> confirmed_lan_address_path; `state.json`/`web.zip`/`.codebase-map/cc.json`/`.cc.json` -> 四个脚本各自出现; 默认排除集七项 -> codemap_common.DEFAULT_EXCLUDES; `tools/stage.py frontend` -> m21 tools/stage.py 子命令; `2.3.0`/`vis-2.9.1` -> codemap_common.IMAGE_TAG/FRONTEND_VERSION; `podman --version` -> podman_missing 的 hint 原文.
- 与任务书原写的差异及理由: (1) SKILL.md 是并入而非新建: m21 汉化链入口与文件 (tools/, i18n/, README.md) 已存在且属已交付成果, 删除会破坏 ISSUE-06 基点前已合并的内容, 故 v1 三子命令写成主体, m21 部分压缩为保留一节; (2) agents/openai.yaml 与 README codebase-map 行已存在, 按核对处理而非新建; (3) 按本会话指令补入 "首次初始化会用官方英文 vis-2.9.1 整体替换 serve-root 前端, 汉化界面需初始化后用 tools/stage.py frontend 重新铺设" 的如实说明 (版本口径节).
- 未做项: AC-009 第四场景 (界面文案官方英文原版, 页面版本显示 vis-2.9.1) 只能宿主真实渲染观察, 归 ISSUE-07; 容器无 podman 无出网, 未真跑 build/serve; 全量 pytest 容器内受 conftest podman 探测限制, 以 collect-only 核对基线 (与 EXECUTION 完成定义口径一致); 未触碰真实 `~/.agents/codebase-map/` 与 `~/.agents/sandbox-worktree/lan-address`.

## 风险提示
- README 表格行与 `check_skill.py` 之外的仓库测试 (例如按 README 链接做的检查) 可能因为少一行或多一行报错; 改完先跑一次 `tests/test_skills_codex_metadata.py` 再加一次全树收集核对.
- 文档写错错误码或参数名, 会让调用会话按错的下一步动作操作; 以代码为准写, 不照抄规格里的示意.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 需要在文档里承诺实现未提供的能力时停止并上报.

## 验收标准
- [ ] `check_skill.py` 通过, frontmatter 三项合规.
- [ ] `agents/openai.yaml` 内容逐字为两行最小配置.
- [ ] 文档写明三子命令职责, 调用式, 不合并与 stop 语义.
- [ ] 文档写明交付三类说明与原样转述, 清理入口与不自动删除, 复原步骤, 版本口径.
- [ ] README 技能表新增一行且链接可解析.

## 被阻塞于
- `ISSUE-01-shared-rules-and-cli-contract.md`
- `ISSUE-02-first-init-and-analysis-output.md`
- `ISSUE-03-gate-stats-and-serve-copies.md`
- `ISSUE-04-resident-service-and-state.md`
- `ISSUE-05-delivery-output-and-address.md`
