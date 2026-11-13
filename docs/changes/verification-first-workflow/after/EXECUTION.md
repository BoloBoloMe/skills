# tests-run-explain Execution Spec (新说明书)

## 权威输入与决策引用

- Product Spec: `../SIM-TASK.md` 需求节 (模拟充当已确认场景)
- 决策引用: 无

## 完成定义

- 四条承诺行为各一条真实运行记录
- 全量套件归合并节点, 本模拟不跑

## 验证策略

- 变更类型: 行为变更 + 结构变更
- 每条承诺行为一条实跑记录; 结构变更给改动前后同一命令对照

## 任务图

- ISSUE-01: `after/ISSUE-01-run-explain.md`; 依赖: 无

## 全局禁止范围

- 不改 `tests/README.md` 映射表; 不改任何 pytest 用例; 不改 `--fast` `--all` 与直通行为

## 全局允许范围

- `tests/run`
