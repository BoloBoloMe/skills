## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已完成

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
执行后填写: 改前改后的 `--collect-only` 收数与全量结果, 删除的文件清单, 改写的断言清单, `check_skill.py` 的输出与版本, grep 与存在性检查输出, 人工走查的命令与脱敏输出, 材料位置 `/tmp/m15-03/`.

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
