# present-web-server 固化产物校验报告

校验方式: 只读交叉核对, 未修改任何被审文件. 校验对象: DECISIONS.md / PRODUCT.md / TECHNICAL.md / UBIQUITOUS_LANGUAGE.md / ADR 0005 / ADR 0006, 基线: browser_session.py / ADR 0003 / pytest.ini / sync-to-pi.py / general/present/pyproject.toml.

结论: 无阻断问题; 应修 1 项, 建议 5 项.

## 问题清单

### 应修

**P1. F005 事实来源路径错误**
- 位置: DECISIONS.md:204-207 (F005 "来源: 仓库根 `pyproject.toml`"); 牵连 D016 (DECISIONS.md:107 "对齐仓库 pyproject 零依赖现状").
- 问题: 仓库根不存在 `pyproject.toml` (`ls` 证实, 根目录仅 pytest.ini/sync-to-pi.py 等). 实际文件为 `general/present/pyproject.toml`, 其内容 (零 dependencies, `requires-python = ">=3.9"`) 与 F005 描述相符 — 即事实内容成立, 来源定位错误.
- 严重度: 应修. 事实账本承诺可溯源, 来源路径错误会破坏可验证性.

### 建议

**P2. AC-005 未关联任何 G 或 US**
- 位置: PRODUCT.md:55, "覆盖: BR-003, BR-005".
- 问题: 完备性约定要求每个 AC 关联至少一个 G 或 US; AC-005 (扁平并集/防遍历) 只挂 BR. 语义上可追溯至 G-001 (内容可访问), 但未显式声明.
- 严重度: 建议.

**P3. BR-002 无验收标准收口**
- 位置: PRODUCT.md:31 (BR-002); 仅 SC-002 (:42) 与 TC-006/TC-025 (TECHNICAL.md:93,124) 覆盖.
- 问题: 单例复用/bind 冲突是核心交互规则, AC-001..AC-008 无一引用 BR-002, 产品验收层缺锚点.
- 严重度: 建议.

**P4. 三条 TC 缺 Given 子句**
- 位置: TECHNICAL.md:109 (TC-019), :111 (TC-021), :120 (TC-024), 均只有 When/Then.
- 问题: 用例格式约定为 Given/When/Then 完整; TC-019/TC-021 的 Given (挂载目录已就绪/目标为目录) 与 TC-024 的 Given (SKILL.md 已更新) 被省略.
- 严重度: 建议.

**P5. TTL 环境变量未命名**
- 位置: DECISIONS.md:96 (D014 "TTL 值支持环境变量覆盖"), TECHNICAL.md:81/:127 (TC-028 "TTL 环境变量").
- 问题: 运行时目录注入变量已定名 `PI_PRESENT_WEB_RUNTIME_DIR` (D026), TTL 变量全文档无名, 两个注入点规格不对称, 实现与测试可能各自取名.
- 严重度: 建议.

**P6. 领域语言用词漂移**
- 位置: PRODUCT.md:30/:31 用 "根目录" — UBIQUITOUS_LANGUAGE.md:13 明确将 "根目录" 列为**挂载目录**的_避免_项; UL:27 定义的**内容面**在 DECISIONS/TECHNICAL 中未使用 (用 "内容访问"/"静态内容"); **常驻展示服务**在 DECISIONS/TECHNICAL 多以 "web 服务/常驻服务" 出现 (UL:8 避免 "web 服务器进程").
- 严重度: 建议. 语义无矛盾, 属术语纪律问题.

## 已核对无误项

### a. 交叉引用一致性 — 正确
- DECISIONS D001-D028, F001-F008 编号连续无缺; PRODUCT G-001..003/US-001..004/BR-001..008/SC-001..007/AC-001..008; TECHNICAL TG-001..004/NFR-001..004/TC-001..029, 全部存在.
- 全部 "覆盖: X" 引用 (7 条 SC, 8 条 AC, 4 条 TG, 29 条 TC, NFR-003→TC-015, NFR-004→TC-028) 逐条核对, 无悬空, 无指向不存在 ID.
- DECISIONS 内部互引核对: D006→D005, D007→D008, D009→D025/D005, D023→D002, D026→D014 及 TC-001..TC-029, D028→D004, 均正确.
- 决策引用分工: PRODUCT 引 D001-D015, TECHNICAL 引 D016-D028 + D005/D006/D011/D012, 并集覆盖全部 28 条, 无遗漏.
- D026 "28 条自动化 + 1 条人工" 与 TECHNICAL 实际 (TC-001..028 自动化 + TC-029 人工) 一致.

### b. 内容一致性 — 正确
- 端口范围 49152-65534: D005/D009/D013-7/BR-001/TECHNICAL:51/TC-011/TC-024 全一致, 全仓无 65535.
- 重试上限 10 次 (start 由 LLM, 重建由脚本): D005/D009/BR-001/D013-7/TC-011/TC-024 一致.
- TTL 24h + env 可覆盖: D014/BR-007/AC-008/TG-003/NFR-004/TC-028 一致.
- 路径与权限: `pi-present-web-<uid>/`, server.json/server.log 0600, 目录 0700 (仅 TECHNICAL 数据模型补充, 不矛盾); AC-006 与 D002 一致.
- 错误码: TECHNICAL CLI 契约六码 (invalid_args/port_in_use/bind_conflict/instance_conflict/not_supported/internal_error) 与 D002/D006/D009/D025 及 TC-002/004/007/025/029 断言一一对应.
- 命令形状 `start <port> <root> --bind <addr>` 三参必填: D006/D013-1/BR-001/AC-001/TECHNICAL 一致.
- host 探测优先级 (SSH_CONNECTION 第 3 字段 > 默认路由接口 IP > 主机名): D011 与 F008 字段语义 (4 字段, 第 3 = 服务端 IP) 及 TC-027 (host=sip) 一致.
- D013 八条与 PRODUCT AC-001..008 逐条对齐; AC-001 增 "目录非法", AC-006 增 "uid 子目录/0600", 均为收紧非矛盾.
- TECHNICAL 接口契约与 D006 (四命令/复用告警/bind_conflict/挂载失败 success=false), D020 (POST /__control__/add-dir body 形状, ping 指纹 {service,pid}, stop 走 ps 校验+SIGTERM, 保留命名空间优先), D025 (run_* 返回 dict/main 薄适配器/单行 JSON/exit 0/1/_sanitize_error/port_in_use) 全部对齐.

### c. 完整性 — 正确 (例外见 P2/P4)
- DECISIONS 每条含状态/约束性/内容, 理由以 "理由/被拒绝的替代方案/已确认理由/用户明确拍板/对齐 X" 形式在文内, 非摘要.
- PRODUCT 固定章节 (背景/目标/非目标/用户故事/业务规则/关键场景/验收标准/成功指标/产品决策引用/待验证事实) 齐全.
- TC 均有所属 Seam, 公开接口与层级在 Seam 级声明, mock/fake 白名单节级声明, 预期值来源节级统一声明 ("已确认决策/规格字面量"), 每条含覆盖 ID; 每个 AC 至少一条 TC 覆盖 (AC-001..008 均有).
- 每个关键场景覆盖 ≥1 个 US/BR/AC (SC-001..007 全满足).

### d. 基线对齐 — 正确 (例外见 P1)
- browser_session.py 实测 313 行, run_open/run_state/run_status 返回 dict 不碰 stdout/exit, main() 薄适配器, 单行 JSON 含 success, exit 0/1, _sanitize_error 七模式 (token/api_key/secret/password/auth/credential/bearer), 路径校验 = 绝对路径+存在+resolve+relative_to containment — F001/D012/D022/D025 的"复用/对齐"声称全部属实.
- ADR 0003 内容为 "产物放系统临时目录, 不保证跨重启" — D010/D024/F006 的对齐声称属实.
- pytest.ini testpaths 含 `general/present/tests` (F003 属实); sync-to-pi.py `_SYNC_IGNORE` 含 tests/__pycache__/uv.lock, skills 目录整体 copytree 分发, scripts/ 下新脚本随同步无额外接线 (F004 属实); F002 (unittest.TestCase 惯例, test_skill_contract.py 文本断言先例) 属实; F007 (ADR 既有 0001-0004, docs/language 新建) 属实.

### e. 领域语言与 ADR — 正确 (例外见 P6)
- UL 七术语 (常驻展示服务/挂载目录/扁平并集/遮蔽/控制面/内容面/远程模式) 语义与 DECISIONS 对应决策一致, 示例对话与 D002/D006/D008/D020 行为一致.
- ADR 0005 与 D001 (无认证/TLS, 默认 0.0.0.0), D003 (完全替代+降级纯展示), D014 (24h 自退), D020 (控制面 loopback) 一致, 二阶后果封堵叙述与 D014 理由吻合.
- ADR 0006 与 D008 一致 (扁平并集/静默遮蔽/并集去重/拒绝每目录前缀方案及理由).

## 总结

产物整体质量高: 交叉引用零悬空, 关键数值 (端口/重试/TTL/权限/错误码) 全仓一致, 与 browser_session.py/ADR 0003/pytest.ini/sync-to-pi.py 基线的对齐声称经实测均属实. 唯一应修项是 F005 把 pyproject.toml 来源错标为仓库根 (实际在 general/present/), 属事实溯源错误而非设计错误. 其余五条为建议级: AC-005/BR-002 的追溯缺口, 三条 TC 缺 Given, TTL 变量未命名, 术语轻微漂移.
