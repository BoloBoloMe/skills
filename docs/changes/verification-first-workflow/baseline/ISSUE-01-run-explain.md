## 父级

- `../EXECUTION.md`

## 执行

- [ ] 已完成

## 要交付什么

`tests/run` 新增 `--explain`: 打印本次改动面会跑哪些套件与将执行的命令, 不运行 pytest, 退出码 0. 现有 `--fast` `--all` 与其他参数直通 pytest 的行为不变.

## 覆盖依据

- Product: `../SIM-TASK.md` 需求节 (模拟中充当已确认产品场景), 行为 1-4
- Technical: 无

## 相关决策

- 无

## 允许范围

同全局: `tests/run`

## 禁止范围

同全局

## 代码定位提示

- 入口: `tests/run` 的 `main()`; 复用已有 `changed_paths()` 与 `select_suites()`
- 阅读顺序: `main()` 的参数分支 → `select_suites()` 返回的 `(suites, saw_global)` → `PARALLEL` 与 `-m not e2e` 的拼接

## 验证契约

- 变更类型: 行为变更 (新增行为), 结构变更 (参数分支编排调整, 旧行为须保持)
- 对应范围: `tests/run` 参数处理与输出
- 验证要求/证据: 四条承诺行为各一条真实运行记录, 含命令与原始输出; 旧行为保持不变须用改动前后的同一命令对照

## 测试切片 (条件保留)

不新增自动化测试. 理由: 输出为一次性选择结果, 长期回归价值低; 四条行为可用真实命令逐条实跑. 现有测试照常运行.

## 验证入口

在 worktree 内依次制造四种改动面, 各跑一次, 记录退出码与原始输出:

1. 制造命中: 在 `workflow/use-sandbox-worktree/scripts/image-prep.py` 末尾加一行注释 → `uv run python tests/run --explain`
2. 不命中: 只改 `tests/run` 本身 → `uv run python tests/run --explain`
3. 兜底: 改 `pytest.ini` (加一行注释) → `uv run python tests/run --explain`
4. 干净: 全部提交后 → `uv run python tests/run --explain`

通过标准: 四项输出与需求文本逐条相符, 退出码均为 0, 且过程中无 pytest 执行痕迹 (无 pytest 汇总行).

## 交付证据

- 起点提交 102c1cc; worktree 与分支见 `../RUNLOG.md`
- 改动前: `uv run python tests/run --explain` 被当作 pytest 参数, `unrecognized arguments: --explain`, EXIT=4
- 四条需求行为各一条真实运行记录, 见 `../RUNLOG.md` 表格; 输出无 pytest 汇总行, 说明未真的跑测试
- 旧行为保持不变: `tests/run --version` 直通 pytest 输出 `pytest 9.2.0`
- 环境: Linux, pytest 9.2.0 (uv 解析)
- 未验证: 全量测试套件 (归合并节点), `tests/run` 无参数完整执行路径

## 风险提示

`--explain` 若落在「其他参数直通 pytest」分支, 会被当成 pytest 参数而报错; 参数判断顺序须把 `--explain` 置于直通分支之前.

## 停止条件

需要改变需求文本或扩大允许范围时停止.

## 适合 AFK 的原因

需求 4 条行为明确, 无产品/API 取舍.

## 验收标准

- [ ] 命中时打印受影响套件清单与命令, 不运行 pytest
- [ ] 不命中时打印现有提示, 退出码 0
- [ ] conftest/pytest.ini 级改动时打印兜底提示
- [ ] 干净工作树时提示工作树干净
- [ ] `--fast` 与 `--all` 行为不变

## Integration 特例 (条件保留)

无

## 被阻塞于

- 无
