# codebase-map v1 实施 Execution Spec

## 权威输入与决策引用

- Product Spec: `docs/changes/workflow-stack-review/milestone-25/PRODUCT.md`
- Technical Spec: `docs/changes/workflow-stack-review/milestone-25/TECHNICAL.md`
- 决策引用 (只读, 非意图来源): `docs/changes/workflow-stack-review/milestone-25/DECISIONS.md` 的 D001-D020, F001-F008; `docs/changes/workflow-stack-review/milestone-13/DECISIONS.md` 的 D001, D003, D005, D009, D010, D017, D020, D023, D024, D027, D030; `docs/changes/workflow-stack-review/milestone-24/DECISIONS.md` 的 U001, U002, U003, F001-F006; `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md` 的 D007, D011, D012.
- 决策背景 (只读, 只作事实来源): `docs/changes/workflow-stack-review/milestone-23/PROBE.md` 的 6.1-6.6 (运行配方, uid 映射, 合并替代, 零声明与分母, 门禁统计), 7 (前端行为与 `height=level` 实测), 9 (缺口).

## 评审起点

本节点已核实并作为派工基线 (每个 issue 派工前必须复核这三项, 结果写进该 issue 的 `执行` 节):

- HEAD (本节点收尾核实): `e5918a5` 之后为四份权威输入的提交 `075665abf5acdf76f4e69bc05d5b96759fae9ba3` 与本执行输入的提交; 派工一律以含本文件的提交为起点 (分支 `refactor-skill-around-verification`), 更早的 `731a3b423be82a3dde59bed5baa1878bbbf73084` 只是路线图提交. 派工时用 `git rev-parse HEAD` 复核, 不一致就停下问发起方.
- 收集基线: `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 实测 **865 条**, 连跑两次稳定 (分类: `workflow/navigate/tests` 37, `general/present/tests` 103, `tests` 725). 任务书里的 905 条在本容器复现不出, 已作废; `workflow/to-spec/tests` 另有 41 条, 不在 `testpaths` 里, 默认全量不计. 增强本树后复跑该命令, 逐条核对增量等于新增用例数.
- 被测 skill 目录不存在: 仓库内没有 `workflow/codebase-map/` (与 DECISIONS F007 一致), 全部从零新建; 现有资产只有文档决策与 m23 的外部证据.
- 权威输入 review_id: 第一版 `97520ca76be69817c1fccc12bf390376dba5a29b2f48ce129a0360b921d1c2b5` (v3), 用户最终采纳转正的版本为 `39f34602d5adb1d94ea98acbd9621a55ec37c3a39cad65cc77155eb98c6264a8` (v4, 48 场景), 两者都由 `ac-draft.py promote` 校验通过. review_id 绑定的是当时的 PRODUCT 暂存稿与验收草稿字节, 无法从最终三份文件复算; 故另登记本节点文件哈希作为可复算锚点: `PRODUCT.md` `103b42e481ec02f2605b3767784fff6e1f7e3faaff478a174d82f36e26324d69`, `TECHNICAL.md` `760af00f1e94fccad89545e4064b5252fc39677da5260b72eaf840645e2d7a2e`, `DECISIONS.md` `5b8d66716a2b3537e8031bc07b3c4c8a3f1a3a8689f131975051e7c4d5e4062c`.
- 两份机检结果 (本节点复跑): `uv run workflow/to-spec/check-ac.py docs/changes/workflow-stack-review/milestone-25/PRODUCT.md` -> `check-ac: 通过 - 48 个场景, 9 个 AC`, 退出码 0 (任务书写 45 场景, 实测 48, 以实测为准); `uv run python workflow/to-spec/check-tech.py docs/changes/workflow-stack-review/milestone-25/TECHNICAL.md` -> `check-tech: 通过 - 7 节`, 退出码 0. 注: `check-ac.py`/`ac-draft.py` 自带 PEP 723 依赖声明, `uv run` 会自动装 `gherkin-official`, 不需要手写 `--with` (已实测).

## 全局允许范围

以 TECHNICAL.md 模块划分末尾的目录边界为准 (`workflow/codebase-map/`, `pytest.ini`, `README.md`):

- 新建 `workflow/codebase-map/SKILL.md`: 三子命令用法与例子 (含 `serve --port` 与 `serve --address`), 地址来源与缺值出口, 交付消息必带的三类说明, 失败出口清单, 状态复原步骤, 数据副本清理入口与不自动删除说明, 前端与分析端版本说明.
- 新建 `workflow/codebase-map/agents/openai.yaml`: 内容固定为 `policy:\n  allow_implicit_invocation: false`.
- 新建 `workflow/codebase-map/scripts/codebase-map.py` (CLI 入口), `scripts/codemap_common.py` (共享常量与纯函数), `scripts/codemap_analyze.py` (初始化, 分析, 门禁, 统计, 产出), `scripts/codemap_service.py` (常驻服务与运行时状态).
- 新建 `workflow/codebase-map/tests/`: 行为回归, 不依赖 podman 与网络.
- 改 `pytest.ini`: 只在 `testpaths` 里 `tests` 之前追加 `workflow/codebase-map/tests`, 遵守文件内 conftest 预载顺序注释.
- 改 `README.md`: 工作流技能表加一行 `codebase-map`.
- 宿主运行时产物: `~/.agents/codebase-map/` (serve-root, cache, logs, state.json, lock), 不入仓库.
- 仓库外证据: `/tmp/m25-<NN>/` (本节点) 与 `/tmp/m26-<NN>/` (实施节点), 按 m25 D010 脱敏, 不入 git.
- 本目录产物: `docs/changes/workflow-stack-review/milestone-25/EXECUTION.md` 与 `issues/`; 执行时只允许填各 issue 的 `交付证据` 与 `执行` 两节.

## 全局禁止范围

- 不改 `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`; 不新增或改变决策内容; 不改 `docs/changes/workflow-stack-review/roadmap/ROADMAP.json` (状态流转归 `drive-execution`).
- 不改 `general/` 下任何文件, 不改 `workflow/` 下其它 skill 子目录, 不改仓库根 `tests/` 与 `workflow/to-spec/`.
- 不改 `docs/language/UBIQUITOUS_LANGUAGE.md` 与 `docs/adr/0026-codebase-map-host-resident-service.md`: m25 D011 要求的措辞同步已在本节点完成, 实施节点不再改动.
- 不改 `pytest.ini` 的既有三行 testpaths 顺序与 markers 段, 不动 `tests/conftest.py`.
- NG-001: 不做任何界面汉化, 不改官方前端产物.
- NG-002: 不做架构评审, 不出重构建议, 不进任何工作流.
- NG-003: 不做容器内运行支持, 不做容器内调宿主服务的接口, 不做没有 podman 时的 python 兜底分析器.
- NG-004: 不做按目录聚合, 不设文件数阈值.
- NG-005: 不自算层号, 环, 向上依赖.
- NG-006: 不把层号拷进官方指标, 不改官方默认 URL 参数, 不做 build 后处理.
- NG-007: 不引 nginx, 不做 HTML5 深链回退, 不做目录 listing.
- NG-008: 不提供 `--include-tests` 之类改变分析范围的开关, 只留 `--exclude <glob>`.
- NG-009: 不加认证, TLS, 多用户, 访问控制, 不做自动到期清理.
- NG-010 (BR-035): 仓库内不写任何 `.cc.json`, 前端产物 (`web.zip`/解包产物), 被分析库的完整路径.
- BR-033: 不新增第三方依赖, `scripts/` 下的脚本只 import python 标准库; 不建 venv.
- 不运行 `sync-to-pi.py`, 不修改真实 `~/.agents/skills/` 与 `~/.pi/`, 不声称安装效果或模型行为已验证.
- 不把 `--address` 或任何地址写进 `state.json` 与配置文件, 不回写 `~/.agents/sandbox-worktree/lan-address`.
- 不停止或接管其它 skill 的服务 (present 与 navigate 各有自己的运行时目录); 测试一律用隔离运行时目录 (`CODEMAP_RUNTIME_DIR`) 与独立端口 (`--port` 或 `CODEMAP_PORT`), 不占用 8090 做测试.
- 不用 stub podman, 本机 curl, 截图顶替"分析可用"与"用户设备可达"的证据.

## 完成定义

分两类, 不得互相顶替 (m25 D016).

### 容器内可复跑 (每个 issue 合并前必跑本 issue 受影响的条目)

1. `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests`; 通过标准 退出码 0 且无 failed. 该树不含 `tests/conftest.py`, 不跑 `podman volume ls`, 无网络动作. 前缀 `PYTEST_XDIST_WORKER=gw0` 是任务书指定写法; 只收集新树时它非必需, 但加上不改结果, 统一保留以免复制命令时漏掉逃逸.
   逃逸原因 (已实测): 仓库根 `tests/conftest.py` 的 `pytest_sessionstart` 无条件执行 `podman volume ls -q`, 本容器没有 podman, 整个会话 INTERNALERROR (`FileNotFoundError: 'podman'`). 设 `PYTEST_XDIST_WORKER=gw0` 让该探测跳过后可正常跑 (实测 `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py` -> 1 passed).
2. `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py`; 通过标准 1 passed (新增 skill 的 frontmatter 与 `agents/openai.yaml` 合规).
3. `uv run python general/writing-for-llm/check_skill.py workflow/codebase-map/SKILL.md`; 通过标准 输出 OK 且退出码 0.
4. 收集基线核对: `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q`; 通过标准 条数等于 865 加本树新增用例数, 差值逐条对得上, 记录在最后一轮 `交付证据`.

### 只能在宿主执行 (缺环境记未验证)

5. 真实库 build: 真实 Java 库由用户在实施时指定 (BR-026); 缺指定就记未验证, 不写死私有路径 (D010). 覆盖首次初始化 (拉镜像, 取官方前端), 三次 podman run, 门禁判定, 统计分母, 目标库只读.
6. 真实 3D 城市图与官方依赖视图渲染 (3D 图, 层号, 环, 向上依赖边), 以及局域网设备真实打开 (m25 D007: 用户设备真实请求才算通过, 宿主 curl 与截图只能作辅助).
7. 长期常驻: 隔真实时间并跨多次命令调用后仍复用同一实例.
8. 全量 `uv run python -m pytest` (含 `tests/` 与既有两树) 需要宿主有 podman, 容器内跑不了, 属环境缺口, **不得伪记通过**. 容器内只能跑上面 1-3 条, 以及带 `PYTEST_XDIST_WORKER=gw0` 的单文件回归.

### 每轮与集成

- 每轮合并后跑上面 1-3 条加本 issue 的新增用例. ISSUE-01 建立测试树后立即跑一次全树, 确认新树与 `pytest.ini` 接线自洽; ISSUE-04 与 ISSUE-05 共用 `codemap_service.py` 与 `state.json`, 两者完成时各跑一次全树, 便于把回归定位到单个 issue.
- 全部 issues 集成后再跑一次 1-3 条加收集基线核对; 宿主项由 ISSUE-07 汇总.

## 验证策略

- 变更类型 (按 `verification-contract` 选定, 逐 issue 声明):
  - ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04, ISSUE-05: 行为变更 (新增对外 CLI 与服务行为).
  - ISSUE-01 另含非行为改动 (`pytest.ini` 接线); ISSUE-06 为行为变更 (SKILL.md 是操作入口, 按 skill 规则改实际操作文档不属非行为改动) 加非行为改动 (`agents/openai.yaml` 与 README 行); ISSUE-07 纯核验.
- 自动化只加在长期存在且会被后续改动打坏的行为上: 键与清洗, 排除集与 glob 转换, 门禁与统计归因, 状态读写与三步探活, 单例与并发, 端口占用与显式换端口, 服务根越界, 地址缺口与交付一致性, CLI 输出形状与错误码, 两份静态守卫, 文档文本契约. 不为每个 AC 逐条造用例.
- 接缝与依赖类别按 TECHNICAL.md `接缝与依赖` 取用, 不新造:
  - 内部接缝 (分类: 内部): 测试直接 import `codemap_common` / `codemap_analyze` / `codemap_service` 并注入临时目录与假参数; `codebase-map.py` 带连字符不能当模块名, CLI 层一律 `subprocess` 调用.
  - 进程接缝 (分类: 真正外部): 只用本地 stub `podman` 脚本核对参数构造 (BR-017 的观察点) 与流程接线; stub 产物一律不得当作分析可用证据, 用例名与证据里必须写明是 stub.
  - 文件接缝 (分类: 本地可替换): `~/.agents/sandbox-worktree/lan-address` 用临时 `HOME` 替换 (不新增配置源, m14 D011); 被分析目标目录, 运行时目录 (`CODEMAP_RUNTIME_DIR`), `cache/frontend/` 的伪产物都可用临时目录.
  - 用户设备访问 (分类: 真正外部, 无法替身): 只有 ISSUE-07 的宿主证据能承接.
  - 网络接缝 (分类: 远程但自有): 容器内不触碰, 只在宿主 IS005 之后的 ISSUE-07 真实执行.
- 明确不自动化并写明理由的项:
  - 锁等待上限 30 秒, 端口就绪等待 10 秒, `stop` 等待 10 秒: TECHNICAL.md 已写明是实现选择可调整; 写用例会把时长常量变成测试博弈, 只按实现常量核对一次并在 ISSUE-04 交付证据记下实际值.
  - `serve`/`stop` 不做网络动作 (BR-027): 用 ISSUE-05 的人工核验 (容器内本就无出网, `serve` 仍成功且 `keys` 齐全; 加静态核对 `codemap_service.py` 不 import 网络模块与不调 podman) 承接, 不写"没发请求"这类不可靠断言.
  - `build` 的 `target_missing` 与 `podman_missing`: 容器内第一个前置检查就报 `container_not_supported`, 无法从真实入口到达后两条; 只在宿主构造 (目标不存在; `env PATH=/nonexistent /usr/bin/python3 ...`) 观察, 记入 ISSUE-07, 不在容器内造假.
- TC 编号口径: 覆盖某 AC 的主用例与 AC 同号 (`AC-005 -> TC-005`); 同一 AC 的其余用例与额外要求用 `TC-<issue 两位>-<两位序号>`. 本 spec 内全局唯一, 只给自动化用例分配编号; 纯宿主人工步骤不占 TC 号, 写进对应 issue 的 `验证入口` 与 ISSUE-07.
- 分析结果类验收 (真实库 build, 门禁统计, 分母, 真实 3D 渲染, 局域网设备打开, 长期常驻) 只能由宿主证据承接, 缺环境记未验证.

## 任务图

- 宽重构判定: 不适用 `workflow/to-execution/refactor-expand-contract.md`. 理由: 全部产物是从零新建的独立目录, 没有既有调用点需要兼容并存; 唯一被改的既有文件 (`pytest.ini`, `README.md`) 各一行, 每步都能保持绿色, 不需要共享 integration branch.
- ISSUE-01: `issues/ISSUE-01-shared-rules-and-cli-contract.md`; 覆盖: AC-007 (容器内拒绝), BR-011, BR-013, BR-015 (集合与转换), BR-021, BR-032, BR-033 (审计); 依赖: 无.
- ISSUE-02: `issues/ISSUE-02-first-init-and-analysis-output.md`; 覆盖: AC-001 (初始化字段与原件出现), AC-007 (digest 口径), BR-016, BR-017, BR-021 (初始化失败即停), BR-027 (build 侧), BR-028, BR-031; 依赖: ISSUE-01.
- ISSUE-03: `issues/ISSUE-03-gate-stats-and-serve-copies.md`; 覆盖: AC-005 (原件与副本与键), AC-006 (门禁), AC-001 (统计与分母), BR-010, BR-012, BR-014 (覆盖侧), BR-022, BR-024, BR-025, BR-036 (不做自动清理); 依赖: ISSUE-02.
- ISSUE-04: `issues/ISSUE-04-resident-service-and-state.md`; 覆盖: AC-003, AC-004, BR-001 至 BR-009, BR-013 (子命令落地), BR-029 (HTTP 面), BR-030, 非功能要求 (单例与并发/常驻性/状态真实性); 依赖: ISSUE-01.
- ISSUE-05: `issues/ISSUE-05-delivery-output-and-address.md`; 覆盖: AC-008, BR-004 (换端口报告), BR-019, BR-020, BR-023, BR-024 (交付侧), BR-027 (serve/stop 侧), BR-037, 非功能要求 (交付一致性); 依赖: ISSUE-03, ISSUE-04.
- ISSUE-06: `issues/ISSUE-06-skill-docs-and-metadata.md`; 覆盖: AC-009, BR-013 (文档形状), BR-018 (文档说明), BR-023, BR-036 (清理入口), BR-037 (原样转述); 依赖: ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04, ISSUE-05.
- ISSUE-07: `issues/ISSUE-07-host-acceptance-evidence.md`; 覆盖: AC-001, AC-002, AC-005, AC-006, AC-007 的宿主场景, AC-008 的真实地址, BR-005 (局域网设备), BR-009 (长期常驻), BR-026, BR-029 (真实开放范围), BR-033/BR-035 (审计人工核验), 非功能要求 (常驻性, 观察代价); 依赖: ISSUE-01 至 ISSUE-06.

并行机会: ISSUE-02 与 ISSUE-04 触不同模块但都要改 `scripts/codebase-map.py` 的子命令接线, 同一工作树内必须串行 (按编号顺序派工); ISSUE-05 依赖 03 与 04 两者; 其余全部串行.

## 覆盖矩阵

### AC

- AC-001 -> ISSUE-02 (初始化字段 + 目标库出现原件), ISSUE-03 (统计与分母, 同键覆盖), ISSUE-07 (真实库) -> 自动化: `workflow/codebase-map/tests` (TC-02-03 初始化字段, TC-03-04 分母对账); 宿主: ISSUE-07 真实 build 输出.
- AC-002 -> ISSUE-07 (真实 3D 与依赖视图与局域网设备) -> 无自动化, 用户设备真实打开 (m25 D007); 容器内不可替身.
- AC-003 -> ISSUE-04 -> TC-003 (存活复用) 加 TC-04-01..TC-04-05 加 TC-04-11; 局域网设备打开部分归 ISSUE-07.
- AC-004 -> ISSUE-04 -> TC-004 (状态字段) 加 TC-04-06..TC-04-10; 删运行时目录后真实 build 复原归 ISSUE-07.
- AC-005 -> ISSUE-03 -> TC-005 (原件 + 副本与 index.html 同目录 + 键命名) 加 TC-03-01, TC-03-02, TC-03-03; 根外软链 404 -> ISSUE-04 TC-04-09; 手工改坏副本重 build -> ISSUE-07.
- AC-006 -> ISSUE-03 (门禁判定与分母与零声明) 加 ISSUE-05 (交付消息三类说明) 加 ISSUE-07 (真实库门禁统计) -> TC-006 加 TC-03-04, TC-03-05 加 TC-05-04; BR-025 的扩展名维度归 ISSUE-03 TC-03-05 加 ISSUE-07.
- AC-007 -> ISSUE-01 (容器内拒绝) 加 ISSUE-02 (digest 口径与初始化失败即停) 加 ISSUE-07 (三条宿主场景与目标库只读) -> TC-007 加 TC-02-06; 宿主场景不占 TC 号, 记 ISSUE-07.
- AC-008 -> ISSUE-05 -> TC-008 加 TC-05-01, TC-05-02; 真实地址确认与设备打开归 ISSUE-07.
- AC-009 -> ISSUE-06 -> TC-009 加 TC-06-01; 官方英文原版与版本显示归 ISSUE-07.

### BR

- BR-001 -> ISSUE-04 -> TC-003 (单例, 首选 8090) 加 TC-04-01; 宿主实跑归 ISSUE-07.
- BR-002 -> ISSUE-04 -> TC-04-01 (并发只留一个 pid, 一真一假 reused).
- BR-003 -> ISSUE-04 -> TC-04-02 (8090 被占报错, 不顺延).
- BR-004 -> ISSUE-04 -> TC-04-03 (显式换端口与旧端口失效), TC-04-04 (换端口后不带 `--port` 沿用 last_port), TC-04-05 (存活实例时报 `instance_running`) 加 ISSUE-05 TC-05-04 (`port_changed`/`previous_url`).
- BR-005 -> ISSUE-04 -> TC-003 (bind 为 0.0.0.0) 加 ISSUE-07 (局域网设备打开).
- BR-006 -> ISSUE-04 -> TC-004 (state.json 字段齐全与唯一真值).
- BR-007 -> ISSUE-04 -> TC-04-06 (残留记录判死), TC-04-07 (pid 活但端口不通/端口是别人 -> state_mismatch).
- BR-008 -> ISSUE-04 -> TC-04-07.
- BR-009 -> ISSUE-04 -> TC-04-11 (短时真实等待后仍 200 且被复用) 加 ISSUE-07 (长期常驻).
- BR-010 -> ISSUE-03 -> TC-005 (原件权威, 副本是副本) 加 ISSUE-07 (改坏副本后重 build 以原件为准).
- BR-011 -> ISSUE-01 -> TC-01-01 (键清洗与哈希稳定) 加 ISSUE-03 TC-03-01, TC-03-02.
- BR-012 -> ISSUE-03 -> TC-005 (副本与 index.html 同目录, `keys[].key` 等于磁盘文件名).
- BR-013 -> ISSUE-01 (子命令形状) 加 ISSUE-04/ISSUE-05 (serve/stop 落地) 加 ISSUE-06 -> TC-009 (文档三子命令与调用式).
- BR-014 -> ISSUE-03 (同键覆盖) 加 ISSUE-04 (复用同实例) -> TC-03-01 加 TC-02-04 (同库重跑覆盖同一原件路径) 加 TC-003.
- BR-015 -> ISSUE-01 -> TC-01-03 (默认排除集, glob 转义, 同一份数据供两处) 加 ISSUE-03 TC-03-04 (工具默认过滤单列).
- BR-016 -> ISSUE-02 -> TC-02-06 (单架构 digest 阻断, 多架构只记录, 不信自报版本号) 加 ISSUE-07 (宿主真实 inspect).
- BR-017 -> ISSUE-02 -> TC-02-01 (stub 核对 `--userns=keep-id`, `--network=none`, `:ro`, `--rm`, 不提权/不挂 socket/不映射端口; 该用例是参数构造观察点, 不是分析可用证据) 加 ISSUE-07.
- BR-018 -> ISSUE-06 (文档写明按官方默认与依赖视图看层号) 加 ISSUE-07 (真实渲染).
- BR-019 -> ISSUE-05 -> TC-008 (局域网基址与完整 URL, 无 loopback/主机名/文件路径) 加 ISSUE-07.
- BR-020 -> ISSUE-05 -> TC-05-01 (缺地址报阻塞并给候选), TC-05-02 (`--address` 只作用于本次) 加 ISSUE-07.
- BR-021 -> ISSUE-01 (容器内与目标缺失) 加 ISSUE-02 (镜像/前端不可用即停) -> TC-007 加 TC-02-03; `podman_missing` 与"取不到官方前端"归 ISSUE-07 宿主构造.
- BR-022 -> ISSUE-03 -> TC-006 (边为 0 / 层号种数不足 -> 非 0 退出, 原件照写, 无副本, 分母与零声明照常输出) 加 ISSUE-07.
- BR-023 -> ISSUE-05 (`integrity_note` 字段) 加 ISSUE-06 (文档要求原样转述) -> TC-05-04 加 TC-06-01.
- BR-024 -> ISSUE-03 (分母统计) 加 ISSUE-05 (`denominator_note`) 加 ISSUE-06 -> TC-03-04 加 TC-05-04 加 TC-06-01.
- BR-025 -> ISSUE-03 -> TC-03-05 (扩展名维度只汇不支持的扩展名, 零声明与排除按类别计数) 加 ISSUE-07.
- BR-026 -> ISSUE-07 -> 人工核验: 用户指定的真实 Java 库 build 通过; 未指定就记未验证.
- BR-027 -> ISSUE-02 (build 做初始化并给固定字段) 加 ISSUE-05 (serve/stop 无网络动作, 人工核验) -> TC-02-03.
- BR-028 -> ISSUE-02 -> TC-02-03 (版本常量) 加 TC-02-07 (伪产物 sha256 不匹配即停, 不叠加旧产物) 加 ISSUE-07.
- BR-029 -> ISSUE-04 -> TC-04-09 (只读静态服务 serve_root, 越界与根外软链 404, 无写接口) 加 ISSUE-06 (文档写暴露范围纪律) 加 ISSUE-07.
- BR-030 -> ISSUE-04 (交集为空的两类文案, TC-04-10) 加 ISSUE-05 (`keys` 只取交集, 缺失与未登记两类提示, TC-05-03).
- BR-031 -> ISSUE-02 -> TC-02-05 (stub 跑完整 build 后目标库只多 `.codebase-map/cc.json`) 加 ISSUE-07 (真实库 git status).
- BR-032 -> ISSUE-01 -> TC-01-01.
- BR-033 (审计) -> ISSUE-01 承接 -> TC-01-05 (静态守卫: `scripts/*.py` 只 import 标准库) 加 人工核验: `git ls-files 'workflow/codebase-map/*'` 无依赖清单文件, 脚本 import 清单人工过一遍, 结论写进 ISSUE-01 交付证据.
- BR-034 (审计) -> ISSUE-06 承接 -> TC-06-02 (`tests/test_skills_codex_metadata.py` 通过) 加 人工核验: frontmatter 有 `disable-model-invocation: true`, `agents/openai.yaml` 内容逐字等于两行最小配置, 全仓库检索无其它 skill 调用 codebase-map.
- BR-035 (审计) -> ISSUE-07 -> 人工核验: `git ls-files` 里没有 `.cc.json`/`web.zip`/前端解包产物, 规格与 issue 里不出现被分析库完整路径; 通过标准 检索为空.
- BR-036 -> ISSUE-03 (不自动清理, TC-03-03) 加 ISSUE-06 (SKILL.md 写清理入口与不自动删除) -> TC-03-03 加 TC-06-01.
- BR-037 -> ISSUE-05 -> TC-05-04 (`delivery_notes` 三类说明是唯一来源, 字段语义不得丢) 加 ISSUE-06 TC-06-01 (文档要求原样转述).

### 非功能要求 (TECHNICAL.md 节锚)

- 单例与并发 -> ISSUE-04 -> TC-04-01 (并发后 pid 唯一, reused 一真一假, 同端口同 URL).
- 常驻性 -> ISSUE-04 -> TC-04-11 (短时) 加 ISSUE-07 (长期).
- 状态真实性 -> ISSUE-04 -> TC-04-06, TC-04-07 (伪造 state.json 三种死法).
- 交付一致性 -> ISSUE-05 -> TC-05-05 (`url` 端口 == `state.port` == 实际监听; `keys[].key` == 磁盘文件名).
- 口径归因 -> ISSUE-03 -> TC-03-04.
- 可诊断 -> ISSUE-01 -> TC-01-06 (每类失败有稳定错误码, 非 JSON 模式 stderr 说清下一步); 各 issue 复用该形状.
- 验证分工 -> 本文件 完成定义 与 验证策略 (无代码落点).
- 观察代价 -> ISSUE-07 -> 真实 build 只记录耗时, 不判定.

### 模块接口不变量与错误模式

- CLI 错误码集合 (`container_not_supported` ... `internal_error`) -> ISSUE-01 TC-01-06 固定形状, 各 issue 各自只新增自己用到的码.
- `build` 前置三条 (不在容器内/目标存在/podman 可用) -> ISSUE-01 (容器内那条) 加 ISSUE-07 (宿主两条).
- `build --json` 字段 (`gate`/`stats`/`initialization`/`duration_seconds`) -> ISSUE-02 (TC-02-03, TC-02-05) 加 ISSUE-03 (TC-006, TC-03-04, TC-03-05).
- `serve --json` 字段 (`url`/`base_url`/`keys`/`delivery_notes`/`address_source`/`address_missing`/`candidates`/`port_changed`/`previous_url`) -> ISSUE-05 (TC-008, TC-05-01..TC-05-05).
- `stop --json` 字段 (`stopped`/`pid`/`port`) -> ISSUE-04 (TC-04-08).
- 数据键不变式 (同目录恒同键, 不同 realpath 不同键, 键只含 `[A-Za-z0-9._-]`) -> ISSUE-01 TC-01-01.
- 运行时目录解析 (`CODEMAP_RUNTIME_DIR` 覆盖, 默认 `~/.agents/codebase-map`, 子目录 `serve-root`/`cache`/`logs`) -> ISSUE-01 TC-01-02 加 ISSUE-04 TC-004 (权限 0700/0600).
- 版本常量 (镜像 tag, 两个 digest, 前端版本与 sha256, 默认端口, bind) -> ISSUE-01 TC-01-04 加 ISSUE-02 TC-02-03.
- 分析三步与中间产物 (三条命令顺序, `cache/work/` 覆盖式复用) -> ISSUE-02 TC-02-02.
- 地址解析顺序与明确不采项 -> ISSUE-05 TC-05-01, TC-05-02.
- 锁等待 30 秒 / 就绪 10 秒 / stop 等待 10 秒 -> 不自动化 (理由见验证策略), 按实现常量核对并记入 ISSUE-04 交付证据.
- 单次调用只有一个进程改动运行时状态 (文件锁) -> ISSUE-04 TC-04-01 (并发只留一个 pid) 加 stop/build 全路径在锁内的代码核对.

### 安全策略 (TECHNICAL.md 节锚)

- 传输与访问 (无认证无 TLS, 绑 0.0.0.0, 只托管结构数据) -> ISSUE-04 TC-04-09 (只服务 serve_root, 无写接口) 加 ISSUE-06 TC-06-01 (文档写暴露范围纪律) 加 ISSUE-07 (真实开放范围).
- 分析隔离 (`:ro`, `--network=none`, `--userns=keep-id`, `--rm`, 不提权, 不挂 socket, 不映射端口) -> ISSUE-02 TC-02-01 加 ISSUE-07 (真实运行日志).
- 目标库完整性 (除 `.codebase-map/cc.json` 外不写目标库) -> ISSUE-02 TC-02-05 加 ISSUE-03 TC-005 加 ISSUE-07 (真实库 git status).
- 越界防护 (先规范化再判归属, 根外路径与根外软链 404) -> ISSUE-04 TC-04-09.
- 数据与隐私 (日志不含源码内容, 0600/0700, 仓库内不写完整路径) -> ISSUE-04 TC-004 加 ISSUE-07 (证据脱敏人工核验).
- 停止与清理 (只由显式 stop 停止, 不接管其它 skill 服务) -> ISSUE-04 TC-04-08 加 ISSUE-06 TC-06-01 加 ISSUE-07.

## 全局风险和停止条件

- 需要改变 PRODUCT.md / TECHNICAL.md / DECISIONS.md 时停止: 已定口径不得自行改, 尤其单架构 digest 阻断与多架构只记录 (m25 D013/D016), 端口默认取 `last_port` 与换端口报旧地址 (D018), 地址只走 `--address` 不落盘 (D017), 交集判据与两类文案 (D020).
- 需要扩大允许范围或触碰禁止范围时停止 (尤其: 为跑测试去改 `tests/conftest.py` 或加第三方依赖, 为省事改官方前端产物, 为通过门禁而改门禁阈值).
- Spec 与代码事实冲突或无法提供完成证据时停止, 并把冲突与缺证写给发起方, 不自行裁决.
- 环境缺口一律记未验证, 不补假: 本容器没有 podman (`podman volume ls` 直接 `FileNotFoundError`), 因此真实分析, 真实渲染, 局域网设备打开, 长期常驻, 全量 pytest 都只能在宿主执行.
- 宿主真实取证的目标库由用户指定 (BR-026, 一个真实 Java 库); 未指定就停在这一步并记未验证, 不猜路径, 不写进仓库.
- 局部风险: 新测试树与根 `tests/` 的 `conftest` 同名陷阱 (`pytest.ini` 注释已说明), 必须在 `workflow/codebase-map/tests/` 里用唯一定名 helper, 禁止 `from conftest import`; 违反会让其它树在预载时拿到错对象.
