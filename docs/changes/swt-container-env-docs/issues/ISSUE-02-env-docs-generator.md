## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
skill 侧 agent-prompts/ 换为五份母本 (PUBLIC.md, ENV.md, PI.md, 空占位 CODEX.md/KIMI.md, 删旧三份 *_AGENTS.md), ENV.md 条目 0-29 按账本 D008 全文落定; 新建 scripts/env_docs.py 纯函数生成器 (生成节 + 四份小抄, 文本含 navigate 架桥配方); navigate/SKILL.md 删 "容器内展示配方" 节 (制图 step 4 保留); 全部配纯函数单测.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-004, AC-007
- Technical: `../TECHNICAL.md`, 模块接口 (env_docs.py, 母本文件组), 测试接缝
## 相关决策
- `../DECISIONS.md`: D001, D002, D006, D008, D009, D010, D012, D014, D016, D019
## 允许范围
- `workflow/use-sandbox-worktree/agent-prompts/` (五份母本, 删旧三份); `workflow/use-sandbox-worktree/scripts/env_docs.py` (新建); `workflow/navigate/SKILL.md` (删一节); `tests/test_env_docs.py` (新建)
## 禁止范围
- swt.py 接线与挂载 (ISSUE-03); sync-to-pi.py; agent_config/; 生成文档集合与字段增减 (D012 已定); ENV.md 条目语义 (D008 已定)
## 代码定位提示
- 母本拆分母本: 旧 `agent-prompts/pi_AGENTS.md` 的公共核 7 行 → PUBLIC.md; herdr 行 → PI.md; sandbox 段 6 行并账本 D008 条目 0-29 → ENV.md (重写为账本终版, 非原文拷贝)
- 生成节/小抄渲染输入 facts 字段清单见 TECHNICAL.md env_docs.py 接口 (container/repo_path/mother_dir/branch/code_path/mode/deny/lan_ip/template_name/template_version/snapshot_digest/default_models)
- navigate 待删节: `workflow/navigate/SKILL.md` 的 "## 容器内展示配方" (制图 step 4 在 "## 制图 Roadmap" 内, 保留)
- 阅读顺序: DECISIONS.md D008/D009/D012/D016 → TECHNICAL.md env_docs.py 接口 → 旧母本三份
## TDD 切片
- TS-001:
  接缝: TECHNICAL.md 测试接缝 接缝 1 (纯函数直接调用).
  测试用例: TC-004.
  先写的失败测试: test_render_docs_returns_four_fact_sheets — render_docs 尚不存在, 导入即失败.
  最小绿色实现范围: render_docs(facts) 返回恰四键, identity/network/web-ports/agents 各自字段齐备且与 facts 插值一致.
  不得测试: 文案逐字与账本比对 (语义正确性), 内部辅助函数.
  覆盖: AC-004.
- TS-002:
  接缝: 接缝 1.
  测试用例: TC-105.
  先写的失败测试: test_web_ports_unconfirmed_lan — 缺席占位行为未实现.
  最小绿色实现范围: lan_ip 为 None 时 web-ports.md 写 "未确认" 且变量指引仍在.
  不得测试: 其他缺席字段的文案.
  覆盖: AC-004.
- TS-003:
  接缝: 接缝 1.
  测试用例: TC-106.
  先写的失败测试: test_network_blacklist_lists_deny — blacklist 形态分支未实现.
  最小绿色实现范围: mode=blacklist 时 network.md 写 blacklist 与逐条 deny; mode 未知写 "未登记".
  不得测试: nftables 语义.
  覆盖: AC-004.
- TS-004:
  接缝: 接缝 1.
  测试用例: TC-107.
  先写的失败测试: test_no_dynamic_facts_in_output — 先行固化 BR-004 负向断言.
  最小绿色实现范围: 确认输出不含 allow 条目与宿主端口映射数值 (facts 中根本不提供这两类输入).
  不得测试: facts 结构之外的字段.
  覆盖: AC-004.
- TS-005:
  接缝: 接缝 1.
  测试用例: TC-007.
  先写的失败测试: test_web_ports_contains_bridge_recipe — 架桥配方文本未写.
  最小绿色实现范围: web-ports.md 含配方全要素 (8801 固定口归 navigate, 起服务读实际端口, 清残留死桥, 桥随服务同生死, URL 拼接, 缺席软失败走信箱, 不改 web_server.py).
  不得测试: socat 命令逐字与 navigate 原节比对.
  覆盖: AC-007.
- TS-006:
  接缝: 无代码接缝 (文件内容断言).
  测试用例: TC-110.
  先写的失败测试: test_navigate_skill_no_container_section — 删节未发生, 断言失败.
  最小绿色实现范围: navigate/SKILL.md 不含 "容器内展示配方" 节且 "## 制图 Roadmap" 的 step 4 仍在.
  不得测试: navigate SKILL.md 其余章节.
  覆盖: AC-007.
- TS-007:
  接缝: 接缝 1.
  测试用例: TC-111 对应的前置 (BR-003 审计的结构准备).
  先写的失败测试: test_generation_functions_are_pure — 固化 BR-003: 断言模块不 import subprocess/socket/requests 等且渲染函数输出与全局状态无关.
  最小绿色实现范围: 实现保持纯函数.
  不得测试: 渲染文本语义.
  覆盖: BR-003 (审计) 的结构侧, 人工审计见 EXECUTION.md 覆盖矩阵.
## 验证入口
- `uv run python -m unittest tests.test_env_docs -v` 全过
- `uv run python -c "from env_docs import render_docs, render_generation_section; ..."` 以样例 facts 打印四份小抄与生成节, 人工过目文案 (缺失测试/写作约定自检)
## 风险提示
- ENV.md 条目 0-29 是逐字规格 (D008), 漏条/改义 = 下游 ISSUE-03 拼装产物错; 完成后对照账本逐条核对
- 生成节指针措辞影响容器内 agent 触发率 (D009 定稿 4 行, 不得自行改写)
## 停止条件
- 账本 D008/D009/D012/D016 文本不足以支撑某条文案时停止 (回 deliberate)
## 适合 AFK 的原因
- 全部文案与字段由账本固定, facts 结构由 TECHNICAL 固定, 无待决产品点
## 验收标准
- [ ] AC-004 四场景与 AC-007 两场景的可观察结果成立; 五份母本就位且旧三份已删; 快层测试全过
## 被阻塞于
- 无
