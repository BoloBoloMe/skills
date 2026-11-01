## 父级
- `../EXECUTION.md`

## 执行
- [x] 已完成

## 要交付什么
把 present 收成一条交付流程, 并把本地浏览器那条路彻底删掉:

- 改写 `general/present/SKILL.md` 为唯一流程: 输出目录, 页面内容与样式要求, 交付前 `check_page.py` 自检, `start`/`status`/`add-dir`/`stop` 命令, 地址来源顺序与缺值出口 (自查 -> 经可用信箱向宿主会话索取 -> 问用户), 生命周期与 stop 影响说明, 失败出口. 保留原有页面规则: 文件名以当天日期 `YYYY-MM-DD-` 开头且不重复, 新版本另存不覆盖旧文件; 首次使用说明同网段可读全部挂载目录的风险一次, 并只挂愿意公开的展示目录.
- 删掉每页必须提供 `window.__PRESENTATION_STATE__` 的要求 (检查器本就不查它, 不动 `check_page.py`), 保留"页面可按需交互, 反馈与最终确认在 chat 完成".
- 把 `REMOTE.md` 的宿主/容器有效规则并入 SKILL.md 同一节 (不再按环境分叉), 然后删除 `REMOTE.md`.
- 删除 `general/present/scripts/browser_session.py`, `general/present/tests/test_browser_session.py`, `general/present/tests/test_browser_session_integration.py`.
- 改 `general/present/tests/test_skill_contract.py`: 去掉对 `browser_session.py` 与 `REMOTE.md` 的断言, 换成"只有一条流程"的文本契约 (单流程, 无状态对象强制, 自检失败不交付, 交付 `http://` 局域网 URL 而非文件路径, 含 `--lan-host`/`address_missing`/stop 影响).
- `README.md` 的 present 行改成统一局域网交付的描述.

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-15/PRODUCT.md`, AC-002; BR-013, BR-017, BR-018, BR-019, BR-014 (审计, 仓库侧).
- Technical: `docs/changes/workflow-stack-review/milestone-15/TECHNICAL.md`, 模块划分 (`SKILL.md` 改写 + `REMOTE.md` 删除, `browser_session.py` 删除, `tests/` 文本契约, `README.md`), 非功能要求 (页面自检).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D001, D002, D007, D008, D011, F001, F004.

## 允许范围
同全局, 增量: `general/present/SKILL.md`, 删除 `general/present/REMOTE.md`, 删除 `general/present/scripts/browser_session.py`, 删除 `general/present/tests/test_browser_session.py` 与 `general/present/tests/test_browser_session_integration.py`, `general/present/tests/test_skill_contract.py`, `README.md` 的 present 行.

## 禁止范围
- 不改 `general/present/scripts/check_page.py` 与 `general/present/tests/test_check_page.py` (F004: 它本就不检查状态对象, 改动等于虚改清单).
- 不改 `general/present/scripts/embed_mermaid.py`, `general/present/tests/test_embed_mermaid.py`, `general/present/examples/`, `general/present/pyproject.toml`, `general/present/uv.lock`, `general/present/agents/`.
- 不改 `web_server.py` 行为 (归 ISSUE-01/02); 不在文档里写死本机地址, 端口或"已验证安装效果".
- 不写 `stop` 之外的自停路径, 不把收工清理写成会执行 `stop`.

## 代码定位提示
- 现状: `general/present/SKILL.md` (61 行: 选择模式, 本地环境, 输出目录, 页面内容与样式, 本地展示流程 6 步), `general/present/REMOTE.md` (39 行: 挂载与交付, 容器分支, 服务生命周期).
- 文本契约: `general/present/tests/test_skill_contract.py` 7 条用例, 其中 `test_browser_helper_path_is_resolved_from_skill_directory`, `test_remote_ssh_mode_contract`, `test_self_check_is_mandatory_before_delivery` (读 REMOTE.md) 必须随删除改写; `test_mermaid_rendered_via_inlined_component`, `test_diagram_rules_block_known_failure_modes`, `test_rework_discipline_is_documented` 保留原意.
- `README.md` 行 23 是 present 表行.
- 删除面核对: `grep -rn "browser_session" general/present README.md` 应只剩 `general/access-web` 的 `browser_agent` 命中 (不同符号).

## 验证契约
- 变更类型: 行为变更 (调用会话的操作路径与交付方式改变, 按 verification-contract 改变实际操作的 skill/提示词不属非行为改动) 加结构变更 (删除脚本与两份测试, 文本契约位置移动).
- 对应范围: 文档与测试的删除/重写, 唯一入口 `general/present/SKILL.md`; `web_server.py` 行为不变.
- 验证要求/证据: 行为侧逐条核对 AC-002 三个场景 (无状态对象也能过自检并被挂上服务且交付局域网 URL; 自检失败时报告具体位置, 不给 URL 与文件路径, 目录不挂载; 宿主展示交付 `http://` 局域网 URL 而非文件路径). 结构侧留改前基线 (`uv run python -m pytest general/present/tests --collect-only -q` 143 条, 其中 63 条属待删文件; 改前全量跑一次留结果) 与改后同命令结果, 写明减少的用例数与保留原意; 改前改后都用 `check_skill.py` 检查同一份文档路径.

## 验证入口
- `uv run python -m pytest general/present/tests` (本 issue 的文本契约主用例为 TC-002, 落在 `test_skill_contract.py`); 通过标准 退出码 0 且无 failed.
- `uv run python general/writing-for-llm/check_skill.py general/present/SKILL.md`; 通过标准 输出 OK 且退出码 0.
- `grep -rn "browser_session" general/present README.md`; 通过标准 无 present 相关命中 (access-web 的 `browser_agent` 命中不算).
- `test ! -e general/present/REMOTE.md` 与 `test ! -e general/present/scripts/browser_session.py`; 通过标准 均成立, 且 `test_skill_contract.py` 里不再有读 `REMOTE.md` 的断言.
- 人工按改写后的 SKILL.md 走一遍 (隔离实例, 临时 `PI_PRESENT_WEB_RUNTIME_DIR`): 生成页面 (用临时目录里的测试页, 自检失败页另造一份) -> 跑 `check_page.py` -> 成功页 `start` 后 `status` 探活; 失败页的报告具体位置且不挂载. 通过标准 文档里写的命令能照做, 输出与文档描述一致; 该自测只用 loopback, 不作交付证据.
- 条件回归: 本 issue 不触碰 `_Handler` 类属性与静态内容服务行为, 依据 `TECHNICAL.md` 接缝与依赖 的跨 skill 依赖条, `uv run python -m pytest workflow/to-spec/tests/test_ac_draft.py` 免跑; 若实现中必须改 `_Handler`, 停下写明并把该用例纳入检查.
- 通过标准 (整体): 上述命令全过; 文档逐条对得上 AC-002, BR-013, BR-017, BR-018, BR-019.

## 交付证据

## 交付证据

环境: 容器内 (本会话), Python 3.11.2 / pytest 9.1.1. 原始输出 `/tmp/m15-03/`.

### 改前/改后基线

- 改前 `uv run python -m pytest general/present/tests --collect-only -q` -> `143 tests collected`, 其中 `63` 条属待删的 `test_browser_session*.py` (`/tmp/m15-03/baseline-collect.txt`).
- 改前全量 `uv run python -m pytest general/present/tests -q` -> `5 failed, 137 passed, 1 skipped` (`/tmp/m15-03/baseline-testrun.txt`; 5 条失败均为本地 browse 环境缺失导致的 browser_session 用例失败).
- 改后 `uv run python -m pytest general/present/tests --collect-only -q` -> `103 tests collected` (80 条剩余 + 23 条本轮新增).
- 改后全量 `uv run python -m pytest general/present/tests -q` -> `99 passed, 4 skipped` (0 failed; 4 skip = 宿主分支 CLI 用例, 容器内不可复现).

### 删除与改写

删除: `general/present/REMOTE.md`, `general/present/scripts/browser_session.py`, `general/present/tests/test_browser_session.py` (63 条), `general/present/tests/test_browser_session_integration.py`.

改写: `general/present/SKILL.md` 重写成唯一流程 (输出目录 / 页面内容与样式 / 挂载到展示服务 含宿主与容器同一节 / 自检与交付 / 服务生命周期 / 失败出口 / 返工纪律). 保留原意: 日期前缀命名与新版本另存不覆盖 (``YYYY-MM-DD-``, "新版本不覆盖旧文件"), 图表规则与返工纪律原文; 新增: `--lan-host`, `address_missing.code=no_confirmed_address|container_env_missing`, 49152-65534 与最多 10 次, 容器锁 8800, 共享 `stop` 影响, 首次开放风险说明, 只挂愿意公开目录, `port` 永远是实际监听端口. 删除: SSH 变量选模式, 本地 Chromium 流程, `__PRESENTATION_STATE__` 强制要求, `ssh -L` 转发指引, 文件路径交付出口.

`general/present/tests/test_skill_contract.py` 改写:
- 删 `test_browser_helper_path_is_resolved_from_skill_directory` 与 `test_remote_ssh_mode_contract` (后者读 `REMOTE.md`).
- `test_self_check_is_mandatory_before_delivery` 不再读 `REMOTE.md`, 改断言唯一流程里的自检与失败出口句子.
- 新增 `test_single_delivery_flow_contract` (TC-002: 无 REMOTE.md/browser_session.py 引用, 无 `选择模式`, 无 `ssh -L`, 显式写不按 SSH 变量选分支/不开浏览器/交局域网 URL 不交文件路径与 loopback), `test_no_state_object_requirement` (D002), `test_address_resolution_contract_is_documented` (D011 地址来源与两级缺口出口), `test_port_and_lifetime_rules_are_documented` (BR-001/BR-009/BR-017/BR-018/BR-019 的文档承接).
- 保留 `test_user_invocation_frontmatter` (description 追加"局域网地址"), `test_mermaid_rendered_via_inlined_component`, `test_diagram_rules_block_known_failure_modes`, `test_rework_discipline_is_documented`.

`README.md` present 行改为"把内容生成自包含 HTML 页面, 经常驻 web 服务交付已确认的局域网地址.".

`general/present/scripts/check_page.py` 未改 (`git diff` 对它是空的), 符合 F004: 它本就不检查状态对象; 复跑 `test_check_page.py` 4 条通过, 证明自检器未被虚改.

### 检查命令与结果

- `uv run python -m pytest general/present/tests` -> `99 passed, 4 skipped`.
- `uv run python general/writing-for-llm/check_skill.py general/present/SKILL.md` -> `general/present/SKILL.md: OK`, exit 0.
- `grep -rn "browser_session" general/present README.md` -> 仅 `general/present/tests/test_skill_contract.py` 里两条**否定断言**命中 (断言该文件与措辞不存在); 无任何实现/文档/导入引用.
- `test ! -e general/present/REMOTE.md` 与 `test ! -e general/present/scripts/browser_session.py` -> 均成立.

### 人工按新文档走一遍 (隔离运行时目录, 容器分支注入测试地址; 仅 loopback 自测, 不作交付证据)

- 正常页 `/tmp/m15-03/report-a/2026-11-01-day1.html` (无状态对象, 无 mermaid): `check_page.py` -> `success: true, findings: []`.
- 失败页 `/tmp/m15-03/w/report-x/broken.html`: `check_page.py` -> `success: false`, `findings[0] = {code: mermaid_not_inlined, message: 页面有 1 个 mermaid 源码块, 但渲染库没有内联, hint: 运行 scripts/embed_mermaid.py}` (具体位置 + 修法).
- 只挂自检通过的 `report-a`: `start 50089 /tmp/m15-03/w/report-a --bind 0.0.0.0 --fixed-port` -> `success: true`, `roots` 只有 `report-a`; `curl http://127.0.0.1:50089/broken.html` -> `404` (失败页所在目录没被挂上); 顶层 listing 只有 `report-a` 的条目; `status` 的 `roots` 同样只有 `report-a`. 文档里写的命令能照做, 输出与文档描述一致 (`/tmp/m15-03/manual-walkthrough2.txt`).

### AC-002 对应

- 无状态对象也能过自检并被挂上服务且交付局域网 URL: 见上一条人工走查 + `test_no_state_object_requirement`.
- 自检失败时报告具体位置, 不给 URL 与文件路径, 目录不挂载: 见失败页输出 (具体 finding + hint) 与 `404`/`roots` 证据 + `test_self_check_is_mandatory_before_delivery`.
- 宿主展示交付 `http://` 局域网 URL 而非文件路径: `test_single_delivery_flow_contract` 固定文档措辞; 真实交付证据属 ISSUE-05.

### 未验证缺口

- 真实宿主场景的文档遵从 (agent 按新 SKILL.md 在宿主上实际交付) 未在本容器验证; 本 issue 只验证文档措辞契约与命令可照做.
- `stop` 之外的自停路径, 装机效果与模型行为一律未验证 (本 issue 未运行同步, 未改安装目录).
## 风险提示
- 取消状态对象时容易顺手改 `check_page.py`, 但 F004 明确它没查该对象, 那会制造无意义差异并牵动 `test_check_page.py`.
- SKILL.md 与 REMOTE.md 规则重叠, 合并时漏掉 stop 影响说明或端口重试上限就丢掉 BR-009 与 BR-001 的文档承接.
- `test_skill_contract.py` 全是文本断言, 改文档与改用例必须落在同一次提交, 否则中间态必红.
- 删两份测试后收数从 143 降到 80 加新增, 若收数不符要先查是否有别的文件引用了被删模块.

## 停止条件
需要改变 PRODUCT/TECHNICAL/决策, 需要改 `check_page.py` 或 `web_server.py` 才能让文档自洽, 或发现除本 issue 列出的文件外还有 present 相关引用被测覆盖时停止 (先把引用面报上来, 不擅自扩大删除范围).

## 验收标准
- [ ] `general/present/SKILL.md` 只有一条交付流程, 不出现按 SSH 变量选分支的规则, 不含 `__PRESENTATION_STATE__` 强制要求, 不给文件路径或 loopback 作交付.
- [ ] 文档含 `--lan-host`, `address_missing`, 49152-65534 与 10 次上限, 容器锁定 8800, stop 影响全部共用页面, 首次开放风险说明, 文件名日期前缀与新版本另存规则.
- [ ] `general/present/REMOTE.md` 已删除且无悬空引用.
- [ ] `browser_session.py` 与两份配套测试已删除, `test_skill_contract.py` 改为单流程契约且通过.
- [ ] `README.md` present 行描述统一局域网交付.
- [ ] `uv run python -m pytest general/present/tests` 退出码 0, `check_skill.py` 输出 OK.

## 被阻塞于
- ISSUE-01, ISSUE-02.
