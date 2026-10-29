## 父级

- `../EXECUTION.md`

## 执行

- [x] 已完成

## 要交付什么

`tests/run` 新增 `--explain`: 打印本次改动面会跑哪些套件与将执行的命令, 不运行 pytest, 退出码 0. `--fast` `--all` 与其他参数直通 pytest 的行为不变.

## 覆盖依据

- Product: `../SIM-TASK.md` 需求节 (模拟中充当已确认产品场景), 行为 1-4

## 验证契约

- 变更类型: 行为变更, 结构变更 (参数分支编排调整, 旧行为须保持)
- 对应范围: `tests/run` 参数处理与输出
- 验证要求/证据: 四条承诺行为各一条真实运行记录, 含命令与原始输出; 结构变更须给改动前后的同一命令对照

## 验证入口

在 worktree 内依次制造四种改动面, 各跑一次, 记录退出码与原始输出:

1. 命中: 在 `workflow/use-sandbox-worktree/scripts/image-prep.py` 末尾加注释 → `uv run python tests/run --explain`
2. 不命中: 只改 `tests/run` 本身 → 同上
3. 兜底: 在 `pytest.ini` 末尾加注释 → 同上
4. 干净: 全部提交后 → 同上

通过标准: 四项输出与需求逐条相符, 退出码全为 0, 且输出中没有 pytest 汇总行 (未真的跑测试). 旧行为保持在改动后用 `uv run python tests/run --version` 对照.

## 交付证据

- 起点提交 9f1afaf; worktree 与分支见 `../RUNLOG-after.md`
- 结构变更对照: 改动前 `uv run python tests/run --explain` 被当作 pytest 参数, `unrecognized arguments: --explain`, EXIT=4; 改动后四条行为均 EXIT=0
- 行为逐条: 四条输出的原文见 `../RUNLOG-after.md`; 均无 pytest 汇总行
- 旧行为: `tests/run --version` 直通 pytest 输出 `pytest 9.2.0`
- 环境: Linux, pytest 9.2.0 (uv 解析)
- 未验证: 全量测试套件 (归合并节点), `tests/run` 无参数完整执行路径

## 验收标准

- [x] 命中时打印受影响套件清单与命令, 不运行 pytest
- [x] 不命中时打印现有提示, 退出码 0
- [x] conftest/pytest.ini 级改动时打印兜底提示
- [x] 干净工作树时提示工作树干净
- [x] `--fast` 与 `--all` 行为不变
