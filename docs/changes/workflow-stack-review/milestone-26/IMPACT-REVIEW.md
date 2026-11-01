# SWT-M26 旧行为影响复查报告

- 任务标识: SWT-M26-IMPACT
- 审核者: 独立影响复查会话 (未参与实现, 只调查不改代码)
- 报告日期: 2026-11-01 (容器内时间)

## 1. 评审起点与目标提交

- 评审起点 (派工基点): `2bc146d` (m25 收尾, "doc: 更新路线图 milestone-25").
- 目标提交 (集成提交): `5c2311a` (Merge branch 'issue/06'), 即本报告所在分支 `review/impact` 的基点; 本报告提交前 HEAD 与 `5c2311a` 代码零差异, 只新增本报告文件.
- 核对方式: `git diff 2bc146d...HEAD` 与 `git log 2bc146d..HEAD --oneline` (31 个提交, 6 个 issue 合并 + 文档复审修正 + 路线图领取 + ac-draft workspace).
- 重要说明: 实际 diff 大于派工任务书描述的"codebase-map 新目录 + pytest.ini 一行 + README 一行 + SKILL.md 并入". 实际还含: 约 20 个既有 skill 文档的 writing-for-llm 复审修正 (提交 eb0f4c7/ccb63aa/1be98fb/2918ad8), `ROADMAP.json` milestone-26 状态 `待处理` -> `进行中` (提交 3a45dcd, drive-execution 领取动作), `workflow/to-spec/` 的 ac-draft.py `workspace` 子命令 + TEMPLATES.md 抽出 + 1 条测试 (提交 5e1d552). 这些全部纳入本次影响核对 (见第 2/3 节).

### blast-radius 判定

按 blast-radius skill 第 7 节以实际影响判定: 承载行为且被下游读的共享面只有 4 处, 且都是单行或闭合小面 (pytest.ini testpaths 一行, README 技能表一行, ROADMAP 状态字段, ac-draft.py 纯增量子命令), 每处都有实跑证明 (证据级别 4); 其余 diff 全部落在新建自包含目录 `workflow/codebase-map/` 内, 或是既有守卫测试已覆盖的文档文本. 判定为非"大或宽", 单路调查已够, 未做多模型同题调查. 依据: 第 2 节每条发现都标了证据级别 (1=直接断言, 3=走查失败路径, 4=实际跑过), 无降级使用.

## 2. 逐项发现 (结论: 未发现实现破坏, 0 项建议返工)

### 2.1 pytest.ini 顺序与 conftest 预载纪律 - 未破坏 (级别 4)

- 代码依据: `pytest.ini` testpaths 现为 `workflow/navigate/tests`, `general/present/tests`, `workflow/codebase-map/tests`, `tests`; 根 `tests/` 仍在最后, 文件头预载顺序注释原样保留. 新树无 `conftest.py` (find 仅命中 codemap_helpers.py 文档字符串里的说明文字), 全树无 `from conftest import`/`import conftest` (grep 仅命中同一文档字符串).
- 代码依据: 共享工具按纪律用全仓库唯一命名 (`codemap_helpers.py`/`codemap_service_helpers.py`/`codemap_stub_helpers.py`, 文件头写明"刻意不叫 conftest"); 与 `nav_helpers.py` 无重名. 新树 14 个测试文件基名与既有三树逐一比对无冲突 (跨树重名会让 pytest 同名模块互相顶替).
- 代码依据: `codemap_helpers.py` 会把 `workflow/codebase-map/scripts/` 加进 sys.path; 该目录只有 `codebase-map.py` (带连字符, 不可 import) 与 `codemap_*.py` (全仓库唯一名), 不会遮蔽任何树要 import 的 stdlib 或既有模块名.
- 既有检查: EXECUTION 完成定义第 1 条与 ISSUE-06 验证入口都要求新树不带根 conftest 跑.
- 本轮实跑: `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 全量 940 collected 无错; 跨树混跑 `workflow/codebase-map/tests/test_data_key.py + tests/test_mailbox_core.py` (后者大量 `from conftest import`) 15 passed, 证明新树在前不改变 `sys.modules['conftest']` 归属; 四树按 testpaths 顺序各取一文件同会话 39 passed.

### 2.2 新测试树对既有两树的影响 - 无影响 (级别 4)

- 本轮实跑数字 (全部带 `PYTEST_XDIST_WORKER=gw0`):
  - 收集: `workflow/navigate/tests` 37, `general/present/tests` 103, `workflow/codebase-map/tests` 75, `tests` 725, 合计 940; m25 EXECUTION 基线 865 = 37+103+725, 既有两树与根树条数与基点逐树一致, 增量全部来自新树 75 条.
  - 运行: `pytest workflow/navigate/tests general/present/tests` -> 136 passed, 4 skipped, 2 subtests passed. 4 个 skip 全在 `general/present/tests/test_web_server_lifecycle.py` 的 `unittest.skipIf(IN_CONTAINER, ...)`, 该文件本轮 diff 未触碰, 属既有容器条件跳过, 与本变更无关.
  - 新树单独跑: 75 passed, 17.7s.
- 增量对账 (每 issue 交付证据声明的收集数与实测闭环): 865 (基点) -> 894 (ISSUE-01 +29, 其证据列出 TC-007 1/TC-01-01 8/TC-01-02 4/TC-01-03 5/TC-01-04 7/TC-01-05 1/TC-01-06 3, 合计 29) -> 907 (ISSUE-04 +13, 记录在 ISSUE-02 派工复核) -> 916 (ISSUE-02 +9) -> 924 (ISSUE-03 +8) -> 930 (ISSUE-05 +6) -> 940 (ISSUE-06 +10: TC-009 主用例 1 加参数面 1, TC-06-01 5, TC-06-02 3, 见 test_skill_docs.py 的 10 个用例名, 逐条对上). 每步增量都等于该 issue 新增用例数, 无对不上的缺口.
- `workflow/to-spec/tests` 不在 testpaths (42 条, 基点 41 + 本轮 1), 不进默认全量, 对收集基线无影响; 该树本身的回归核对见 3.9.

### 2.3 README.md 与 SKILL.md 改动对既有守卫测试的影响 - 无影响 (级别 4)

- 代码依据: README 技能表只改 codebase-map 一行的描述文字, 行格式与列数不变; `tests/` 全树 grep 无任何按 README 技能表或 README 链接做的守卫检查 (仅 `tests/test_swt_m12.py` 把 README.md 当临时文件内容写进 fixture 仓库, 与技能表无关). ISSUE-06 风险提示里担心的"按 README 链接做的检查"经查不存在.
- `sync-to-pi.py` 不解析 README (grep 无命中), 其测试 `tests/test_sync_to_pi_compose.py` 4 passed.
- 本轮实跑: `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py` -> 1 passed (该测试遍历 workflow/ 与 general/ 全部 SKILL.md, 本轮改过的约 20 个 SKILL.md 全部被它覆盖, frontmatter 与 openai.yaml 契约无回归). `general/writing-for-llm/check_skill.py` 逐一跑过 diff 内全部 SKILL.md, 全部 OK 退出码 0.
- 新树自带 `test_tc0602_readme_row_reflects_v1` 把 README 该行钉进文本契约 (在 75 passed 内), 后续漂移会被拦.

### 2.4 workflow/codebase-map/SKILL.md 并入 v1 后 m21 汉化链章节 - 完整 (级别 4)

- 代码依据: SKILL.md 末节 `## m21 汉化构建链 (保留)` 四个既有入口一个不少: `tools/build-zh.sh`, `tools/stage.py` (并注明 `frontend`/`data` 两个子入口), `i18n/`, `README.md` (该链操作手册, 逐条挂决策编号). 旧版末段"v1 就位前用 README 里的临时静态服务命令查看页面"改写为"细节见 README.md; v1 的常驻服务与交付走上面的三子命令", 指引仍可达.
- 代码依据: `git diff 2bc146d...HEAD -- workflow/codebase-map/README.md tools/ i18n/` 为空, m21 资产一字未动; m21 README.md 第 47 行临时静态服务命令仍在场, 第 6 行仍写明 v1 边界. SKILL.md 新引用的 `tools/stage.py frontend` 子命令在 stage.py argparse 里真实存在 (第 41 行).
- 版本口径节新增的"首次初始化会把 serve-root 前端整体换成官方英文 vis-2.9.1, 要汉化界面须初始化后用 `tools/stage.py frontend` 重新铺设"是与 m21 链共存的关键交接事实, ISSUE-06 交付证据声明为按会话指令补入的如实说明, 与 codemap_analyze.py 的整体替换逻辑一致 (ISSUE-02 证据).
- 本轮实跑: check_skill.py 对该文件 OK; 新树文本契约用例 (含错误码白名单断言: 文档出现的 15 个错误码 token 逐一在代码里) 全过.

### 2.5 对其它 skill 与真实 ~/.agents 的耦合, scripts 依赖面 - 无越界 (级别 3, 关键处 4)

- 代码依据: `workflow/codebase-map/scripts/*.py` 全部 import 逐一过目, 只有 stdlib (hashlib/json/os/re/subprocess/pathlib/datetime/errno/fcntl/functools/http.client/mimetypes/signal/socket/sys/time/http.server/argparse/shutil) 加脚本同目录内部接缝 `codemap_common`/`codemap_analyze`/`codemap_service`; 无第三方依赖, 无依赖清单文件.
- 代码依据: 脚本对真实 home 的引用只有两处且都是规格内落点: 默认运行时目录 `~/.agents/codebase-map` (codemap_common.py:86, 可被 CODEMAP_RUNTIME_DIR 覆盖) 与地址文件 `~/.agents/sandbox-worktree` (codemap_common.py:116, m14 D011 默认值, serve 只读不回写). 不 import 任何其它 skill 的模块; 全仓库 md 检索除 README 技能表行外无其它 skill 调用 codebase-map (BR-034 审计点成立).
- 测试树 import 只有 stdlib 加 pytest; helpers 默认剥离 CODEMAP_RUNTIME_DIR 防串台, 用例全走临时运行时目录与高位端口, 不占 8090, 不触碰真实 `~/.agents/codebase-map/` 与 `~/.agents/sandbox-worktree/lan-address` (test_runtime_dir.py:21 对默认值的断言是纯函数断言, 前置已剥离 env, 不读真实盘).
- 既有检查: 新树 `test_stdlib_only.py` (BR-033 审计的自动化面) 在 75 passed 内.
- 本轮实跑: 75 passed 即含该守卫; `agents/openai.yaml` 逐字两行配置, 由 tests/test_skills_codex_metadata.py (1 passed) 与 TC-06-02 双重覆盖.

### 2.6 ISSUE-02/03/04/05/06 声明的越界调整 - 合理, 无掩盖失败 (级别 4)

逐处与 git diff 对过, 共四处既有测试调整, 全部在对应 issue 交付证据里声明过:

1. ISSUE-02 (提交 034c879) 改 ISSUE-01 的 `test_cli_output_shape.py` 两个 build 形状用例: 宿主分支改为注入 `PATH=/nonexistent` 让其在 `podman_missing` 快速失败. 理由成立: build 接上真实流水线后, 宿主上前置检查全过会走含网络的分析, 形状用例不应触发. 关键点: 形状断言逐字未动 (`--json` stdout 恰一行含 success/command/error; 非 JSON 多行摘要; stderr 下一步; 退出码 1), 仍是失败形状断言, 只是换了个更早的稳定失败码, 属加强可控性而非掩盖.
2. ISSUE-03 (提交 1ad6369) 把 `test_analyze_pipeline.py` 的 `assert_full_build_fields` 从"ISSUE-03 字段不得出现"翻转为"必带且门禁通过" (gate.passed 为真, edges>0, level_kinds>=3, serve_copy_path 以数据键结尾). 这是 ISSUE-02 阶段明写的临时守卫 (注释原文"ISSUE-03 的字段不得提前出现"), 翻转后断言严格变多, 不是放松.
3. 同提交把 TC-02-02 的 stub merge 产物内容断言从 `{"stub": ..., "run": 6}` 改为 `stub_run == 6` 加 `meta.projectName == "stub-merge"`. 被测行为 (第二次运行覆盖不追加, run 序号前进) 断言保留且加细; 改因是 stub 产物从退化 dict 升级为内置可过门禁的 fixture (带 lenses), 属 fixture 语义升级, 不是放宽被测行为.
4. ISSUE-04 (提交 ea516ab) 把 ISSUE-01 的 `test_serve_and_stop_not_registered_in_this_issue` (断言 serve/stop 是 argparse invalid choice) 改名为 `..._registered_since_issue_04` 的注册冒烟: stop 幂等成功 (success/stopped=false), serve 空目录在起服务前报 `no_data_keys` 退出码 1. 原断言在 ISSUE-04 注册子命令后必然失效, 替换用例仍按错误码与退出码断言真实行为, 且验证了"不静默成功"这条 ISSUE-01 原始意图.
- ISSUE-05 未改任何既有测试 (其交付证据与 diff 一致, 只加 test_delivery_output.py 6 例与 codemap_service_helpers.py 1 行).
- 本轮实跑: 全树 75 passed, 无 skip 无 xfail 兜底; 上述四个用例都在通过集合里, 且失败路径断言 (错误码/退出码) 逐条核对未被删除或弱化.

## 3. 已排除项与依据

1. 既有两棵测试树收集与运行被新树影响 - 已排除, 依据 2.2 (逐树计数与基点一致, 全量实跑绿).
2. conftest 预载顺序被新树破坏 - 已排除, 依据 2.1 (静态 + 混跑 + 四树同会话).
3. README/全部改动 SKILL.md 打破元数据守卫或 lint - 已排除, 依据 2.3 (1 passed + 逐文件 check_skill OK).
4. m21 汉化链入口丢失 - 已排除, 依据 2.4 (四入口在场, 资产 diff 为空).
5. scripts 引第三方依赖或耦合其它 skill/真实 home - 已排除, 依据 2.5 (import 清单 + 路径引用清单 + 守卫测试实跑).
6. 六处越界调整掩盖失败 - 已排除, 依据 2.6 (逐处 diff 比对, 断言只增不减).
7. ROADMAP.json 状态改动 (待处理 -> 进行中) 打破路线图校验 - 已排除: 该改动是 drive-execution 领取动作 (m25 EXECUTION 对 ROADMAP 的禁令明确把状态流转留给 drive-execution, 提交 3a45dcd 即该动作); `workflow/navigate/tests/test_roadmap_validation.py` 在本轮 navigate 全量 37 passed 内.
8. ac-draft.py 加 workspace 子命令破坏 to-spec 既有行为 - 已排除: diff 为纯增量 (新 workspace 函数 + argparse 分支, preview/promote 未动); `uv run ac-draft.py workspace` 实跑返回正确 JSON 退出码 0.
9. to-spec/tests 被本轮改坏 - 已排除 (关键核对): 该树不在 testpaths, 且在本容器用裸 `python -m pytest` 直跑时基点 `2bc146d` 就有 51 failed, HEAD 为 52 failed, 唯一差量恰为本轮新增的 workspace 用例自身. 失败根因是测试用 `sys.executable` 裸调 ac-draft.py, PEP 723 依赖 `gherkin-official` 不在沙箱 venv 里, `import gherkin` 失败, 属基点就存在的环境缺口 (基点 51 例失败清单与 HEAD 51 例逐条 diff 相同). 补依赖后实跑: 基点 41 passed + 37 subtests, HEAD 42 passed + 37 subtests, 零回归. 结论: 不是本轮破坏, 是既有环境限制 (见 4.3).
10. 文档复审修正 (约 20 个 skill 的 md) 影响任何守卫 - 已排除: 这些提交只动 md 文本与 to-spec/TEMPLATES.md 抽取; check_skill 逐文件 OK, 元数据守卫 1 passed, navigate/present 全量实跑绿.
11. 新树与既有树测试文件基名冲突 - 已排除, 依据 2.1 (逐基名比对无冲突).

## 4. 未证实路径的缺口说明 (交发起方知悉/裁决, 不构成返工建议)

1. 文档复审提交的授权痕迹不在仓库: 提交 eb0f4c7/ccb63aa/1be98fb/2918ad8 的提交消息引用"复审报告", 但仓库内检索不到该报告文件 (docs/ 与 general/ 均无), 应为会话级材料. 我无法从仓库材料核实这些越出 m25 EXECUTION 允许范围 (它禁止实施节点改 workflow/ 下其它 skill 子目录) 的文档提交的授权来源. 行为面影响已全部排除 (第 3 节), 但授权链这条只能由发起方确认. 若发起方当时已批准, 本条自动关闭.
2. ISSUE-02 与 ISSUE-04 的派工顺序与 EXECUTION 任务图不符: spec 要求两者串行按编号派工 (都要改 codebase-map.py 子命令接线), 实际 issue/04 先于 issue/02 合并 (7f6fd4e 早于 22e25e0). 集成态自洽 (两份交付证据都在, 接线完整, 全树绿), 无行为影响, 但属流程偏差, 记录在案.
3. to-spec/tests 的环境缺口 (非本轮引入): 该树所有用例用 `sys.executable` 裸调 ac-draft.py/check-ac.py, 依赖 PEP 723 自动装包, 沙箱 venv 未播种 `gherkin-official`, 裸 pytest 必失败 51+ 例. 属镜像播种缺口, 建议宿主重建镜像时把 gherkin-official 纳入 venv, 或接受"该树只能带 `uv run --with gherkin-official` 跑"的现状.
4. 流程小疵 (不影响行为, 仅记录): ISSUE-01 与 ISSUE-06 的"派工前复核并记录"复选框未勾选但下方内容已填 (HEAD/收集数/目录清单齐全); ISSUE-06 交付证据如实记录了任务书说"新建"而实际 agents/openai.yaml 与 README 行已存在、按核对处理的偏差.
5. 宿主侧未验证项 (与 EXECUTION 完成定义 5-8 对应, 容器不可为, 不算本轮缺口): 真实库 build 与真实渲染, 局域网设备打开, 长期常驻, 以及含根 `tests/` 树的全量 pytest (需 podman). 本轮在容器内已覆盖: collect-only 940, 新树/两树全量, 代表性单文件与跨树混跑. ISSUE-07 宿主验收未开始, 不在本报告范围.

## 5. 合并前最便宜的复现 (blast-radius 第 8 节)

```bash
PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q | tail -1
# 期望: 940 tests collected (37+103+75+725)
PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/navigate/tests general/present/tests workflow/codebase-map/tests -q
# 期望: 211 passed, 4 skipped (skipped 为 present 树既有容器条件跳过)
PYTEST_XDIST_WORKER=gw0 uv run python -m pytest tests/test_skills_codex_metadata.py -q
# 期望: 1 passed
```

## 6. 总裁定

- 实现破坏: 0 项, 不建议返工.
- 缺口: 4 项 (第 4 节 1-4), 均不需改实现; 其中第 1 项 (授权痕迹) 请发起方裁决, 第 3 项 (gherkin 播种) 可选交宿主处理.
- 已排除: 11 项 (第 3 节).
- 未验证: 宿主侧 4 类 (第 4 节第 5 条), 归 ISSUE-07.
- 建议路线: 维持集成提交 `5c2311a` 现状, 进入 ISSUE-07 宿主验收.
