## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已实现
## 要构建什么
birth 拼装接线完成: 新 birth 容器的三份系统提示词 = PUBLIC+ENV+生成节+各自专属段 (空段跳过), 容器内无 ~/AGENTS.md; ~/docs/ 四份小抄 ro 挂载; birth 收尾挂载就位检查 (缺件 PARTIAL); 留档目录含全部拼装产物; m12 断言更新.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-002, AC-003, AC-005, AC-006, AC-009
- Technical: `../TECHNICAL.md`, 模块划分/模块接口 (swt.py 拼装模块, birth 验收段), 接缝与适配器, 关键流程, 测试接缝
## 相关决策
- `../DECISIONS.md`: D002, D006, D013, D018, D019
## 允许范围
- `workflow/use-sandbox-worktree/scripts/swt.py` (AGENT_PROMPT_MOUNTS, stage_agent_prompts, ensure_agent_prompt_parents, birth 命令构造与验收段); `tests/test_swt_stage_env.py` (新建); `tests/test_swt_m12.py` (母本断言改拼装断言, ro 写断言扩展 docs 目录)
## 禁止范围
- env_docs.py 与母本内容 (ISSUE-02 产物, 只消费); agent_config/ 模板初始化; apply_network/bake_host_info_env 语义; NG-001..NG-006
## 代码定位提示
- `swt.py`: AGENT_PROMPT_SOURCE_DIR/AGENT_PROMPT_MOUNTS (约 88-92 行), stage_agent_prompts (约 1140-1156 行), ensure_agent_prompt_parents (约 1527-1540 行), create 命令挂载构造 (约 2678-2682 行), birth 验收段 (agent-template install/check 之后, 标 born 前)
- 时序 (TECHNICAL.md 关键流程): stage 拼装 → create 挂载 → start → apply_network → bake_host_info_env → verify_env_mounts → born; resume 不重跑拼装
- m12 现断言: tests/test_swt_m12.py 约 881-900 行 (母本字节一致 + ro 写被拒 + 父目录属主)
- 阅读顺序: ISSUE-02 产物接口 → swt.py 上述四处 → test_swt_m12.py 断言块
## TDD 切片
- TS-001:
  接缝: TECHNICAL.md 测试接缝 接缝 1 (stage 单测, 留档目录直读).
  测试用例: TC-002/TC-112.
  先写的失败测试: test_stage_composes_three_prompts — 现 stage 逐字拷贝旧母本, 拼装公式断言失败.
  最小绿色实现范围: stage_agent_prompts 按 ISSUE-02 产物重写: 读五份母本, 拼三份 (空段跳过), 生成节经 env_docs 渲染, docs/ 四份落留档; TC-112 补两条接口不变量: 同输入重跑同字节 (幂等), 母本缺失报 SwtEnvError 含 sync-to-pi 指引且不动留档.
  不得测试: 母本文案语义 (ISSUE-02 已测), 留档目录外文件.
  覆盖: AC-002.
- TS-002:
  接缝: 接缝 1.
  测试用例: TC-003.
  先写的失败测试: test_no_home_agents_md_mount_entry — AGENT_PROMPT_MOUNTS 仍含 ~/AGENTS.md 项, 断言失败.
  最小绿色实现范围: 挂载表改为三文件 + docs 目录, 无 /home/bolo/AGENTS.md 项; create 命令构造同步.
  不得测试: podman 命令行逐字.
  覆盖: AC-003.
- TS-003:
  接缝: 接缝 1 (缺件两态构造留档目录).
  测试用例: TC-006/TC-109.
  先写的失败测试: test_verify_env_mounts_partial_on_missing — verify_env_mounts 尚不存在.
  最小绿色实现范围: verify_env_mounts(container) 对 3+4 文件验非空含生成标记, 缺件抛 SwtError(3, PARTIAL) 列缺件; birth 接线在标 born 前.
  不得测试: exec 子进程实现细节 (fake 容器读即可).
  覆盖: AC-006.
- TS-004:
  接缝: 接缝 1.
  测试用例: TC-103/TC-104.
  先写的失败测试: test_stage_skips_empty_agent_sections_and_generation_section_identical — 空段跳过与三份生成节同字节未固化.
  最小绿色实现范围: 拼装对 0 字节 CODEX/KIMI 跳过, 三份生成节同源同字节.
  不得测试: 专属段内容语义.
  覆盖: AC-002.
- TS-005:
  接缝: 接缝 2 (m12 真容器 exec).
  测试用例: TC-005/TC-108.
  先写的失败测试: m12 新增 docs 目录 ro 写被拒与拼装产物比对断言 — 旧母本字节断言先行改为新形态即失败.
  最小绿色实现范围: 更新 test_swt_m12.py: 容器内三份提示词 = 留档拼装产物, docs 四份与留档一致, ro 追加写被拒 (提示词 + identity.md).
  不得测试: 容器内其他路径.
  覆盖: AC-005, AC-009 (挂载随 create 固定, 无新 TC).
## 验证入口
- `uv run python -m unittest tests.test_swt_stage_env -v` 全过
- `uv run --no-project python -m unittest tests.test_swt_m12 -v` 真容器验收 (需 rootless podman, 按既有审批); 通过标准 = 该文件全部断言含新拼装/ro/检查项
- 真实 birth 一只新容器: 容器内三份提示词含 ENV 条目 0-29, ~/docs/ 四份, 无 ~/AGENTS.md
## 风险提示
- stage 在 create 前调用的顺序约束不单测 (由 birth 命令构造顺序保证, born 路径间接覆盖) — 改动 create 流程时人工复核
- 真容器验收环境缺失时按 EXECUTION.md 停止条件处理, 快层不得代替
- resume 路径不重跑拼装 (留档即真相), 改挂载表后旧容器挂载不变属预期
## 停止条件
- ISSUE-02 产物接口与 TECHNICAL 不符, 或需要动 agent_config/ 时停止
## 适合 AFK 的原因
- 拼装公式/挂载表/检查清单均由 D013/D018 与 TECHNICAL 接口固定, 无待决产品点
## 验收标准
- [ ] AC-002/003/005/006 各场景可观察结果成立, AC-009 性质保持; 快层与真容器验证入口全过
## 被阻塞于
- ISSUE-02
