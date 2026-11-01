# present 统一局域网交付 Execution Spec

## 权威输入与决策引用
- Product Spec: `docs/changes/workflow-stack-review/milestone-15/PRODUCT.md`
- Technical Spec: `docs/changes/workflow-stack-review/milestone-15/TECHNICAL.md`
- 决策引用 (只读, 非意图来源): `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md` 的 D001, D002, D004, D005, D006, D007, D008, D009, D010, D011, D012 (D003 已被 D011 替代, 不引用), 事实 F001-F015; 已确认标准 `docs/changes/workflow-stack-review/ACCEPTANCE.md` 的 AC-15-01 至 AC-15-07.

## 评审起点
- 待填. 由 `drive-execution` 首次派工前填入完整提交号与核实依据.

## 全局允许范围
- 以 TECHNICAL.md 模块划分末尾的目录边界为准: `general/present/` 与 `README.md`.
- `general/present/SKILL.md` (改写为唯一交付流程), `general/present/REMOTE.md` (规则并入后删除).
- `general/present/scripts/web_server.py` (地址解析与 start/status 输出契约, 运行时记录与重建的交付一致性).
- 删除 `general/present/scripts/browser_session.py`, `general/present/tests/test_browser_session.py`, `general/present/tests/test_browser_session_integration.py`.
- `general/present/tests/test_web_server_lifecycle.py`, `general/present/tests/test_skill_contract.py`, `general/present/tests/test_web_server_cli.py` (新增/改写地址与文本契约用例).
- `README.md` 的 present 行.
- 本目录产物: `docs/changes/workflow-stack-review/milestone-15/EXECUTION.md` 与 `issues/`; 参与验证的原始输出放仓库外 `/tmp/m15-<NN>/`.

## 全局禁止范围
- 不改 `PRODUCT.md`, `TECHNICAL.md`, `milestone-14/DECISIONS.md`, `ACCEPTANCE.md`; 不新增或改变决策内容.
- 不改 `general/present/scripts/check_page.py`, `general/present/scripts/embed_mermaid.py`, `general/present/tests/test_check_page.py`, `general/present/tests/test_embed_mermaid.py`, `general/present/tests/test_web_server_content.py`, `general/present/tests/test_web_server_control_plane.py`, `general/present/tests/test_web_server_fixed_port.py`, `general/present/examples/`, `general/present/pyproject.toml`, `general/present/uv.lock`.
- 不改 `workflow/` 下任何文件 (含 `workflow/to-spec/tests/test_ac_draft.py`), 不改仓库根 `tests/`, 不改 `pytest.ini` 的 `testpaths` 顺序 (它靠顺序预载同名 conftest, 见文件内注释).
- NG-001/NG-004/NG-005: 不新增认证, TLS, 访问控制, 自动到期清理或状态回传接口; 不改 access-web 自身浏览器能力与 navigate 的展示服务; 不评估触发率/遵从率/节省幅度.
- NG-002: 不新增系统服务, 常驻监控器, 不承诺跨系统重启或容器销毁后的恢复.
- NG-003: 不做每目录 URL 前缀, 不新增 remove-dir 接口, 不改扁平并集与共享 stop 语义.
- 不修改真实已安装 skills (`~/.agents/skills/`, `~/.pi/`) 与全局配置, 不运行 `sync-to-pi.py`, 不声称安装效果或模型行为已验证.
- 不停止, 接管或探测正在运行的真实展示实例; 测试一律用独立运行时目录 (`PI_PRESENT_WEB_RUNTIME_DIR`) 与独立端口; 不在收工清理里执行 `stop`.
- 不改 `docs/changes/workflow-stack-review/roadmap/ROADMAP.json` (状态流转归 `drive-execution`).

## 完成定义
- 测试入口: `uv run python -m pytest general/present/tests`; 通过标准 退出码 0 且无 failed. 拆分时基线: `--collect-only` 收 143 条 (其中 63 条属待删除的 browser_session 用例); ISSUE-03 删除后应为 80 条加本轮新增, 执行时如实记录收数变化与理由.
- skill 格式检查: `uv run python general/writing-for-llm/check_skill.py general/present/SKILL.md`; 通过标准 输出 OK 且退出码 0. `REMOTE.md` 删除后不再有第二份被检查的文档.
- 条件回归: 若改动触碰 `_Handler` 类属性 (`roots`/`roots_lock`/`runtime_dir`/`bind`) 或静态内容服务行为, 必须把 `uv run python -m pytest workflow/to-spec/tests/test_ac_draft.py` 纳入直接相关检查. 本轮按 TECHNICAL.md 接缝与依赖 只替换地址解析与 start/status 输出, 不触碰 `_Handler`, 故各 issue 写免跑理由; 实现中若不得不触碰, 该 issue 停下来上报并改为纳入该检查.
- 真实验证 (TECHNICAL.md 非功能要求): 宿主与容器两种环境各留一条真实局域网访问证据. 容器交付地址取已确认宿主局域网地址 `192.168.65.165` (birth 生成的 `~/docs/web-ports.md`) 加容器 8800 的宿主映射端口, 映射端口只从 `SWT_HOST_WEB_PORT` 读取; 本会话该环境变量缺失, 执行时按 BR-003 先自查, 仍缺经信箱向创建容器的宿主会话 (`01a18814-6e80-744f-a09f-346ba7b25522`) 索取; 宿主侧用同一已确认地址加 49152-65534 内的实际端口. 两处都要用户设备真实打开并与本次请求对上; 缺哪个环境记未验证, 不用本机 curl 或源码推断顶替.
- 每轮合并后跑本轮受影响的检查. 提前跑全量的节点: ISSUE-01 与 ISSUE-02 都动 `web_server.py` 与 CLI 输出契约 (共享底层), 因此 ISSUE-01 完成后先跑一次 `general/present/tests` 全量复跑, ISSUE-02 完成后再跑一次, 便于把回归定位到单个 issue; ISSUE-03 删测试文件后跑一次全量确认剩余套件自洽.
- 全部 issues 集成后跑一次完整检查: `uv run python -m pytest general/present/tests` 加 `check_skill.py general/present/SKILL.md`.
- 审计 BR-014/BR-015 按覆盖矩阵的人工核验执行, 结论记入 ISSUE-03 与 ISSUE-05 的交付证据.

## 验证策略
- 变更类型 (按 `verification-contract` 选定): ISSUE-01 与 ISSUE-02 行为变更; ISSUE-03 行为变更 (调用会话的操作路径与交付方式改变; 按 skill 规则, 改变实际操作的 skill/提示词不属非行为改动) 加结构变更 (删除脚本与配套测试, 文本契约位置移动); ISSUE-04 与 ISSUE-05 纯核验.
- 自动化只加在需要长期保护的行为上: 地址来源优先级与缺口 (ISSUE-01), 复用/重建后交付 URL 与记录、真实监听三者一致 (ISSUE-02), 单流程文本契约 (ISSUE-03). AC-005 与 AC-006 不新增用例, 复跑既有 `test_web_server_lifecycle.py`, `test_web_server_control_plane.py`, `test_web_server_content.py`; AC-007 是证据汇总, 不新增测试.
- TC 编号口径: 本 spec 里覆盖某 AC 的主用例与 AC 同号 (AC-001 -> TC-001 ... AC-002 -> TC-002 等), 本 spec 内编号唯一; 同一 AC 的额外用例用 `TC-<issue 两位>-<两位序号>`. `general/present/tests/` 中旧 present-web-server spec 遗留的 TC-001..TC-029 docstring 不属本编号空间, 执行时按文件与用例名定位, 不按数字检索.
- 未采用自动化测试的 TECHNICAL.md 不变量与理由:
  - "非默认 records-root 按无已确认地址处理" (模块接口 支持范围): 代码里没有第二条配置源可测, 用人工核对 start 在不传 `--lan-host` 且地址文件不存在时的输出 (`no_confirmed_address` 加 `candidates`, 服务仍在监听) 承接, 结论写进 ISSUE-01 交付证据.
  - "宿主 10 次 port_in_use 后停止尝试" (BR-001): 上限属调用会话纪律, 单条 CLI 只返回一次 `port_in_use`; 用复跑 CLI 加读 SKILL.md 文本核验, 写成循环测试只会测测试自身.
  - "24h 无请求不退出" (非功能要求 常驻性): 由既有 `test_idle_server_stays_available_until_stop` 承接 (注入已废弃的 `PI_PRESENT_WEB_TTL_SECONDS` 后等 1 秒), 不新增长等待用例.
- 两个环境的真实访问属 `user device access` 接缝 (TECHNICAL.md 分类: 真正外部, 无法替身), 只能由用户设备出证, 见 ISSUE-05.
- 每个 issue 的验证入口写明可复跑命令, 环境与通过标准; 实际结果填进 `交付证据`.

## 任务图
- 宽重构判定: 不适用 `workflow/to-execution/refactor-expand-contract.md`. 理由: 地址解析替换只落在 `web_server.py` 内部的一个解析入口与其 start/status 调用点, 输出字段契约变化由调用方文档同步说明; 删除 browser_session 的引用面已由 F001 与本次检索界定 (仅 SKILL.md, 两份测试, 一处文本契约), 没有跨模块的大批调用点需要兼容并存, 每个切片都能独立保持绿色, 不需共享 integration branch.
- ISSUE-01: `issues/ISSUE-01-address-resolution-delivery-url.md`; 覆盖: AC-001, BR-002, BR-003, BR-004, BR-019; 依赖: 无.
- ISSUE-02: `issues/ISSUE-02-port-record-and-rebuild-url.md`; 覆盖: AC-003, AC-004, BR-001, BR-005, BR-006, BR-007, BR-010; 依赖: ISSUE-01.
- ISSUE-03: `issues/ISSUE-03-single-delivery-flow-docs.md`; 覆盖: AC-002, BR-013, BR-017, BR-018, BR-014 (审计, 仓库侧); 依赖: ISSUE-01, ISSUE-02.
- ISSUE-04: `issues/ISSUE-04-security-and-lifetime-regression.md`; 覆盖: AC-005, AC-006, BR-008, BR-009, BR-011, BR-012, BR-015 (审计); 依赖: ISSUE-01, ISSUE-02, ISSUE-03.
- ISSUE-05: `issues/ISSUE-05-acceptance-evidence.md`; 覆盖: AC-007, BR-016 (审计), BR-014 (审计, 边界侧); 依赖: ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04.

并行机会: 无. 全部切片沿同一条 CLI 输出契约与同一份文档串行, 后一项的验证入口要用前一项的交付结果.

## 覆盖矩阵
- AC-001 -> ISSUE-01 -> TC-001 (显式地址优先, 端口为实际监听端口) 加 TC-01-01 (已确认记录), TC-01-02 (无确认缺口, SSH/localhost/文件路径不入交付), TC-01-03 (容器用宿主地址加映射端口), TC-01-04 (容器缺映射报缺口), TC-01-05 (loopback 只给 localhost 加 `loopback_bind`) -> `uv run python -m pytest general/present/tests`.
- AC-002 -> ISSUE-03 -> TC-002 (单流程文本契约: 无状态对象强制, 自检失败不交付, 交付 http:// 局域网 URL) 加人工按改写后的 SKILL.md 走一遍自检与失败出口 -> `uv run python -m pytest general/present/tests` 与 `check_skill.py general/present/SKILL.md`.
- AC-003 -> ISSUE-02 -> TC-003 (复用存活实例: 交付端口为实例实际端口, 挂载清单含两目录) 加复跑既有 `test_web_server_lifecycle.py` 的复用与 bind_conflict 用例, 复跑 `test_web_server_content.py` 的并集/遮蔽用例 (不新增用例).
- AC-004 -> ISSUE-02 -> TC-004 (宿主重建换口后 `status.port` = 记录 `port` = 实际监听, `url` 用该端口且可请求) 加 TC-02-01 (容器记录 `port` 为 8800, 交付 URL 用映射端口, 记录不出现映射端口) 加复跑既有重建/锁端口/权限用例.
- AC-005 -> ISSUE-04 -> 复跑 `test_web_server_lifecycle.py` 的 `test_idle_server_stays_available_until_stop` 与 stop 用例, 加隔离实例上真实 `stop` 后两页均非 200 的人工记录.
- AC-006 -> ISSUE-04 -> 复跑 `test_web_server_content.py` 与 `test_web_server_control_plane.py` (含越界与 `../`), 加同网段真实请求与用户设备确认 (与 AC-007 共用取证, 不重复执行).
- AC-007 -> ISSUE-05 -> 证据汇总: 两环境真实局域网访问 (用户设备打开加对得上的 `server.log` 请求行), 测试与格式检查的命令/版本/结果, 缺环境记未验证.
- BR-001 -> ISSUE-02 (端口真值与锁定实例) 加 ISSUE-03 (文档写 49152-65534, 10 次上限, 容器锁定 8800) -> 复跑 `test_web_server_fixed_port.py` 与 `test_web_server_lifecycle.py` 的 port_in_use 用例; 10 次上限按文档核对 (理由见验证策略).
- BR-002 -> ISSUE-01 -> TC-001, TC-01-01, TC-01-02.
- BR-003 -> ISSUE-01 -> TC-01-03, TC-01-04; 真实映射端口取证在 ISSUE-05.
- BR-004 -> ISSUE-01 -> TC-01-02, TC-01-04, TC-01-05 (无文件路径/loopback/猜测值).
- BR-005 -> ISSUE-02 -> TC-003 加复跑 bind_conflict 与同目录幂等用例.
- BR-006 -> ISSUE-02 -> TC-004 加 TC-02-01 加复跑 TC-026 权限用例.
- BR-007 -> ISSUE-02 -> TC-004 加复跑残留记录重建与锁定实例只试原端口用例.
- BR-008 -> ISSUE-04 -> 复跑闲置存活与 stop 用例 (不恢复自退语义).
- BR-009 -> ISSUE-03 (文档写 stop 影响全部共用页面) 加 ISSUE-04 (真实 stop 观察) .
- BR-010 -> ISSUE-02 -> 复跑 `test_web_server_content.py` 的扁平并集/同名遮蔽/顶层 listing 用例 (不新增).
- BR-011 -> ISSUE-04 -> 复跑 `test_web_server_control_plane.py` 远程 403 与本机 ping 200 用例, 加同网段真实请求.
- BR-012 -> ISSUE-04 -> 复跑 `test_web_server_content.py` 的 `../` 与越界 symlink 用例, 加一次本机 LAN IP 越界请求的真实输出.
- BR-013 -> ISSUE-03 -> TC-002 (文档不再要求状态对象) 加复跑 `test_check_page.py` 证明自检器未被虚改.
- BR-014 (审计) -> ISSUE-03 (仓库侧删除与文档不新增通道) 加 ISSUE-05 (边界核验) -> 人工核验: `git status --short` 与 `git diff --stat` 只落允许范围, 全程无 `sync-to-pi.py` 调用, `ls ~/.agents/skills/present` 与改前一致; 证据里不写安装效果或模型行为结论.
- BR-015 (审计) -> ISSUE-04 (隔离核验) 加 ISSUE-05 (汇总复核) -> 人工核验: 测试全程使用临时 `PI_PRESENT_WEB_RUNTIME_DIR` 与独立端口; 真实展示实例进程与记录在验证前后不变 (`pgrep -af web_server.py`, 记录文件 mtime); navigate 的实例与记录未被触碰.
- BR-016 (审计) -> ISSUE-05 -> 人工核验: 宿主与容器各一条用户设备真实访问证据, 逐条写明环境, URL, 访问时间, 页面与对得上的请求行; 缺环境记未验证.
- BR-017 -> ISSUE-03 (文档写首次风险说明与只挂展示目录) 加 ISSUE-04 (核对实际挂载目录只是展示目录, 不含仓库根或敏感目录).
- BR-018 -> ISSUE-03 (保留文件名以当天日期开头, 不重复, 新版本另存不覆盖) -> 人工核对文档句与实际生成页文件名.
- BR-019 -> ISSUE-01 (start 仍要求 `--bind`, 交付默认 0.0.0.0 场景) 加 ISSUE-03 (文档写默认监听 0.0.0.0 与 `--bind` 必填).
- 非功能要求 常驻性 -> ISSUE-04 -> 复跑 `test_idle_server_stays_available_until_stop`, 交付证据里注明 `PI_PRESENT_WEB_TTL_SECONDS` 已不被实现读取, 该用例是防旧自退行为复活的保护.
- 非功能要求 记录与交付一致 -> ISSUE-02 -> TC-004 与 TC-02-01, 两条一致性分开验证 (宿主记录端口即交付端口; 容器记录 8800 而交付用映射端口).
- 非功能要求 两环境真实证据 -> ISSUE-05 -> 见 AC-007.
- 非功能要求 页面自检 -> ISSUE-03 -> TC-002 加人工 `check_page.py` 复跑 (含 1 处失败时不给 URL 与文件路径).
- 安全策略 管理面/越界/隔离 -> ISSUE-04 -> 复跑控制面与内容面用例加真实请求.
- 模块接口不变量 (stdout 单行 JSON, 退出码 0/1) -> ISSUE-01, ISSUE-02 -> 新增用例一律解析 stdout 单行 JSON 并核对退出码, 复跑 `test_web_server_cli.py`.
- 模块接口不变量 (记录字段六项与 0600/0700 权限) -> ISSUE-02 -> TC-02-01 加复跑 TC-026.
- 模块接口 地址解析错误模式 (解析失败不是启动失败) -> ISSUE-01 -> TC-01-02, TC-01-04, TC-01-05 (服务照常监听, 只给缺口).
- 模块接口 支持范围 (非默认 records-root 不扫别处) -> ISSUE-01 -> 人工核对, 理由见验证策略.
- 条件依赖 (跨 skill `_Handler` 用例) -> ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04, ISSUE-05 -> 各 issue 验证入口写免跑理由; 若触碰 `_Handler` 则改为纳入直接相关检查.

## 全局风险和停止条件
- 需要改变 PRODUCT.md / TECHNICAL.md / DECISIONS.md / ACCEPTANCE.md 时停止. 已定的地址口径: `--lan-host` 只作用于宿主分支; 容器分支固定用 `SWT_HOST_LAN_IP` 加 `SWT_HOST_WEB_PORT`, 不被 `--lan-host` 覆盖 (TECHNICAL.md 地址解析 按 D011 写明); 实现若需要别的口径先停下上报, 不自行改口径.
- 需要扩大允许范围或触碰禁止范围时停止 (尤其: 为跑测试去改 `test_web_server_content.py` / `test_web_server_control_plane.py` / `test_web_server_fixed_port.py`, 或为省事改 `check_page.py`).
- Spec 与代码事实冲突或无法提供完成证据时停止.
- 环境缺值时停止取证并记未验证: 本会话 `SWT_HOST_LAN_IP` 与 `SWT_HOST_WEB_PORT` 都不在环境变量里 (已确认地址 `192.168.65.165` 来自 birth 生成的 `~/docs/web-ports.md`); 映射端口只能经自查后向宿主会话索取, 不得用猜测端口或容器 8800 拼交付 URL.

## 执行者报告: 推送缺口与一条越界引用 (待协调方处理)

### 1. `m15-present` 分支推不进 origin

- 命令: `git push origin m15-present` -> 被桥拒绝 `! [remote rejected] m15-present -> m15-present (deny updating a hidden ref)`.
- 原因: 桥按对下沉 `receive.hideRefs`, 只放行本对母体分支 `refs/heads/refactor-skill-around-verification` (`workflow/use-sandbox-worktree/scripts/swt.py` 的 `receive.hideRefs` 配置), 其它分支名一律拒. 母体分支当前 `731a3b4` 与 `m15-present` 的基点 `a5a8ecf` 不是快进关系, 所以也不能靠改推目标绕过.
- 现状: 5 个逻辑提交 (ISSUE-01..05) 只在容器内本地分支 `m15-present` 上, 尚未到宿主母体.
- 可选出路 (需协调方决定, 执行者未擅自扩大范围): (a) 协调方在母体工作树内 `git merge --no-ff m15-present` 后快进推母体分支 (与 drive-execution 的"合并本轮"一致); (b) 宿主侧把 `refs/heads/m15-present` 加入桥允许范围后重推.

### 2. 一处越界引用 (未修, 交协调方)

- `workflow/use-sandbox-worktree/scripts/env_docs.py` 的 `_web_ports` 生成文案含 "(与 present 的 REMOTE.md 对齐)". 本节点删了 `general/present/REMOTE.md`, 该句变成悬空引用; 生成物 `~/docs/web-ports.md` 会继续提到一个不存在的文件.
- 未修理由 (初次报告时): `workflow/` 在本轮全局禁止范围内, 且 D011 明确"容器自查顺序沿用环境文档及 milestone-18 规则, 不改其生成器". 交由协调方按 milestone-18 或其后续节点处理.
- 后续: 协调方来信授权只改这一处措辞, 已于提交 `4e2abb5` 改为 "与 present 的地址规则一致, 见 docs/changes/workflow-stack-review/milestone-14/DECISIONS.md 的 D011"; 生成器行为未改, 无测试断言该字符串. 该文件在容器内 `uv run python -m pytest tests/test_env_docs.py` 会因 `tests/conftest.py` 的 `pytest_sessionstart` 调 `podman volume ls` 而 INTERNALERROR (容器无 podman, 与本次改动无关, 改动前后一致), 故用 `uv run python -m unittest tests.test_env_docs` 跑同一文件, 11 passed.
