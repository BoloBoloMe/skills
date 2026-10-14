## 父级
- `../EXECUTION.md`
- 来源: 双轴评审发现 (Spec 轴 c4 / 基准点 0e50ddd)
## 执行
- [x] 已实现
## 要构建什么
补齐 TECHNICAL.md 已写明的接口契约: 拼装与渲染对缺失事实键按缺席文案渲染, 不抛异常.
现状: `env_docs.py` 的 identity/agents 渲染对 `repo_path` `mother_dir` `branch` `code_path` `container` `template_name` `template_version` `snapshot_digest` `default_models` 等直接下标取键, 缺键抛 KeyError; `mode` 只有 "非 whitelist/blacklist" 分支, 缺键仍抛. 目前只有 `lan_ip` 与 `deny` 走了缺席分支. 生产路径 `swt.py agent_env_facts` 恒供全键, 所以线上没爆, 但接口契约未满足.
目标: 缺键统一走缺席文案分支 —— `lan_ip` 缺或 None → "未确认"; 其余标量键缺 → "未登记"; `deny` 缺 → 空列表 (不逐条列出); `default_models` 缺 → 三个 agent 的模型均按缺席文案渲染. 生成节与四份小抄都不得因缺键抛异常.
## 覆盖依据
- Technical: `../TECHNICAL.md` "模块接口" 的 `stage_agent_prompts` 不变量 ("net_facts 缺键按缺席文案渲染, 不抛") 与 env_docs 不变量 ("缺席值占位 (\"未确认\"/\"未登记\")")
- Product: `../PRODUCT.md` AC-004 的 edge 场景 (缺席值占位)
## 相关决策
- `../DECISIONS.md`: D012 (四份小抄字段), D014 (network 快照声明不动)
## 允许范围
- `workflow/use-sandbox-worktree/scripts/env_docs.py` (缺席分支); `tests/test_env_docs.py` (补缺键测试)
## 禁止范围
- `swt.py` (生产侧恒供全键, 不改); 四份小抄与生成节的字段集合与文案语义 (D012/D009 已定, 只补缺键时的占位行为); 母本文件; 既有测试的断言口径
## 代码定位提示
- `env_docs.py`: `render_docs` 与各渲染函数 (`_identity`/`_network`/`_web_ports`/`_agents`), `render_generation_section`
- `tests/test_env_docs.py`: 现有 `make_facts` 夹具 (19 行) 与既有用例
- 对照 `../TECHNICAL.md` 的 env_docs 接口节: facts 字段清单与缺席规则
## TDD 切片
- TS-001:
  接缝: 接缝 1 (纯函数直接调用).
  测试用例: 当 facts 缺某个标量键时, render_docs 与 render_generation_section 都不抛异常, 且该字段渲染缺席文案 ("未登记"; lan_ip 为 "未确认").
  先写的失败测试: test_render_docs_tolerates_missing_scalar_keys — 现实现对缺键直接下标抛 KeyError.
  最小绿色实现范围: 各渲染函数改用带缺省值的取值 (缺 → "未登记"), 覆盖 repo_path/mother_dir/branch/code_path/container/template_name/template_version/snapshot_digest.
  不得测试: 缺席文案以外的具体字段顺序与格式.
  覆盖: AC-004 (缺席占位).
- TS-002:
  接缝: 接缝 1.
  测试用例: 当 facts 缺 deny 键时 network 文本仍含模式与快照声明且不抛; 当 facts 缺 default_models 键时 agents 文本不抛.
  先写的失败测试: test_render_docs_tolerates_missing_deny_and_default_models.
  最小绿色实现范围: deny 缺 → 空列表分支; default_models 缺 → 逐 agent 缺席文案.
  不得测试: nftables 语义, 模型名具体占位文案逐字.
  覆盖: AC-004.
## 验证入口
- `uv run python -m unittest tests.test_env_docs -v` 全过
- `uv run python -m unittest tests.test_swt_stage_env -v` 全过 (拼装侧不回归)
## 风险提示
- 只加缺席分支, 不要顺手改 D012 的字段集合或 D014 的声明文本
- 生产路径恒供全键, 本改动不改变任何现有 birth 产物字节 (既有测试断言 bytes 应原样通过, 若既有断言变了说明改错)
## 停止条件
- 需要改 TECHNICAL 的字段清单或 D009/D012 文案时停止
- 需要动 swt.py 才能满足时停止
## 适合 AFK 的原因
- 缺席规则已由 TECHNICAL 给定 ("未确认"/"未登记"), 无待决产品点
## 验收标准
- [ ] 缺键不再抛异常, 缺席文案按 TECHNICAL 规则渲染; 两个验证入口全过; 既有断言字节不变
## 被阻塞于
- 无
## Integration 特例
- 不适用 (单分支小改)
