# tests-run-explain Execution Spec

## 权威输入与决策引用

- Product Spec: `../SIM-TASK.md` 的「需求」节充当本模拟的已确认场景来源 (模拟假定 PRODUCT.md 已确认, 未走 to-spec 流程)
- Technical Spec: 无 (模拟从 issue 拆分开始)
- 决策引用 (只读, 非意图来源): 无

## 评审起点

- 102c1cc (本次模拟基线提交)

## 全局允许范围

- `tests/run`

## 全局禁止范围

- 不改 `tests/README.md` 的改动面映射表
- 不改任何 `tests/` 下的 pytest 用例
- 不改 `--fast` `--all` 与其他参数直通 pytest 的行为

## 完成定义

- `uv run python tests/run --explain` 在四种改动面下各输出一次预期结果
- `uv run python tests/run --fast` 在选择逻辑被改动后仍能跑通受影响套件
- 全量套件归合并节点, 本模拟不跑

## 验证策略

- 变更类型: 行为变更 (新增命令行行为, 现有行为保持)
- 每项承诺行为各一条真实运行记录, 环境为本机 worktree

## 任务图

- ISSUE-01: `issues/ISSUE-01-run-explain.md`; 覆盖: 需求 4 条行为; 依赖: 无

## 覆盖矩阵

- 需求行为 1 (命中时打印套件与命令, 不运行) -> ISSUE-01 -> 验证入口
- 需求行为 2 (不命中时打印提示, 退出码 0) -> ISSUE-01 -> 验证入口
- 需求行为 3 (conftest/pytest.ini 级改动兜底) -> ISSUE-01 -> 验证入口
- 需求行为 4 (干净工作树提示) -> ISSUE-01 -> 验证入口

## 全局风险和停止条件

- 需要改变需求文本时停止.
- 需要改 `tests/README.md` 映射表时停止.
