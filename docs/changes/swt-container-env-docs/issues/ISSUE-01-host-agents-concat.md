## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已实现
## 要构建什么
使用者运行 sync-to-pi.py 后, 宿主 ~/.pi/agent/AGENTS.md 无询问地变为 仓库根 agent-prompts/PUBLIC.md 与 PI.md 的顺序拼接, 旧内容自动备份 .bak; 母本缺失时报错且目标文件不动; 容器侧母本被修改时拼接照常成功 (两环境互不同步); 仓库 pi/AGENTS.md 删除, 仓库根 agent-prompts/ 新建.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-001, AC-008
- Technical: `../TECHNICAL.md`, 模块接口 (sync-to-pi.py 拼接项), 测试接缝
## 相关决策
- `../DECISIONS.md`: D004, D015
## 允许范围
- `sync-to-pi.py`; 仓库根 `agent-prompts/` (新建 PUBLIC.md, PI.md); 删除 `pi/AGENTS.md`; 新增 `tests/test_sync_to_pi_compose.py`
## 禁止范围
- skill 侧 agent-prompts/ 任何内容 (容器侧归 ISSUE-02); ~/.pi/agent/ 下其他文件 (settings.json/models.json/keybindings.json); NG-001..NG-006; sync-to-pi 的其余同步项行为
## 代码定位提示
- `sync-to-pi.py`: main() 中 pi/AGENTS.md 单文件询问项 (约 448-455 行, 替换为无条件拼接调用), `_backup_and_atomic_write` (约 298-313 行, 复用)
- 母本内容 = 现 pi/AGENTS.md 拆分: 公共核 7 行 → PUBLIC.md, pi/herdr 行 → PI.md
- 阅读顺序: sync-to-pi.py main() → _backup_and_atomic_write → 现行 pi/AGENTS.md
## TDD 切片
- TS-001:
  接缝: TECHNICAL.md 测试接缝 接缝 3 (临时目录适配器).
  测试用例: TC-001.
  先写的失败测试: test_compose_host_agents_md_writes_concat_with_backup — compose_host_agents_md 尚不存在, 导入即失败.
  最小绿色实现范围: compose_host_agents_md(repo_root, pi_dir) 读取两份母本顺序拼接, 经 _backup_and_atomic_write 落盘.
  不得测试: main() 交互流程内部, 母本文件的具体文案内容.
  覆盖: AC-001.
- TS-002:
  接缝: 接缝 3.
  测试用例: TC-101.
  先写的失败测试: test_compose_is_idempotent — 对同一输入二次调用后断言目标文件与 .bak 字节, 现无实现无以断言.
  最小绿色实现范围: 同 TS-001 实现 (幂等为其自然属性, 测试先行固化).
  不得测试: 备份文件数量, 写盘顺序.
  覆盖: AC-001.
- TS-003:
  接缝: 接缝 3.
  测试用例: TC-102.
  先写的失败测试: test_compose_missing_master_errors_without_touching_target — 现实现会直接读文件抛裸异常而非人话报错.
  最小绿色实现范围: 缺母本时报出含缺失路径的错误且目标文件字节不变.
  不得测试: 报错文案逐字.
  覆盖: AC-001.
- TS-004:
  接缝: 接缝 3.
  测试用例: TC-008.
  先写的失败测试: test_compose_ignores_skill_master_drift — 构造 skill 侧 PUBLIC 与仓库根不同, 断言拼接结果只随仓库根; 现无此行为可断言.
  最小绿色实现范围: 确认实现不读取不校验 skill 侧母本 (无代码即测试即绿, 固化 BR-008).
  不得测试: skill 侧文件内容.
  覆盖: AC-008.
## 验证入口
- `uv run python -m unittest tests.test_sync_to_pi_compose -v` 全过
- 真实运行 `uv run python sync-to-pi.py`: 宿主 AGENTS.md 更新为拼接内容, .bak 产生, 无逐项询问
## 风险提示
- 宿主 AGENTS.md 被无条件重写: 已有 .bak 防护 (D004 用户已接受); 若宿主文件含手工修改会被覆盖, 属既定决策
- main() 移除询问项时勿动其他同步项的选择逻辑
## 停止条件
- 需要改变拼接顺序/母本划分或触碰 skill 侧母本时停止
## 适合 AFK 的原因
- 拼接公式/备份/报错行为均由 D004/D015 与 TECHNICAL 模块接口固定, 无待决产品点
## 验收标准
- [ ] AC-001 三场景与 AC-008 场景的可观察结果成立, 机检与快层测试全过
## 被阻塞于
- 无
