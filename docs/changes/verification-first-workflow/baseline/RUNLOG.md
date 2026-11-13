# baseline 运行记录 (旧说明书)

- 环境: Linux, python 由 uv 提供, pytest 9.2.0 (经 `uv run` 解析)
- 起点提交: 102c1cc
- worktree: `../skills-main-refactor-skill-around-verification.worktrees/sim-before`, 分支 `sim/before`
- 需求来源: `../SIM-TASK.md`

## 实际执行顺序

1. 需求文本即场景来源, 假定 PRODUCT.md 已确认, 从 issue 拆分开始 (未跑 to-spec, 见「偏差」).
2. 按 `workflow/to-execution/SKILL.md` 模板写 `EXECUTION.md` 与 `ISSUE-01-run-explain.md` (18 节全填).
3. 按 `workflow/verification-contract/SKILL.md` 判为行为变更 + 结构变更, 边改边实跑.
4. 改 `tests/run`, 逐条实跑取证.

## 改动前观察 (红态)

```
$ uv run python tests/run --explain
ERROR: usage: python -m pytest [options] ...
python -m pytest: error: unrecognized arguments: --explain
EXIT=4
```

## 改动后逐条证据

| 需求行为 | 命令与输入 | 实际输出 | 退出码 |
| --- | --- | --- | --- |
| 2 不命中 | 只改 `tests/run` 后 `--explain` | `[tests/run] 改动面 tests/run 不命中任何测试套件, 无可跑项; 需要全量用 tests/run --all` | 0 |
| 1 命中 | 在 `image-prep.py` 尾加注释后 `--explain` | `受影响套件: tests/test_swt_m07.py` + `$ ... pytest tests/test_swt_m07.py -q` | 0 |
| 3 兜底 | 在 `pytest.ini` 尾加注释后 `--explain` | `conftest/pytest.ini 级改动 → 快层全量兜底` + `受影响套件: -m not e2e` | 0 |
| 4 干净 | 提交后 `--explain` | `改动面 (工作树干净) 不命中任何测试套件, 无可跑项` | 0 |
| 旧行为 | `tests/run --version` (直通 pytest) | `pytest 9.2.0` | 0 |
| 新增组合 | 脏 `image-prep.py` + `--explain --fast` | 命令末尾带 `-m not e2e` | 0 |
| 新增组合 | `--explain --all` | `$ ... pytest -q` | 0 |

以上输出中均无 pytest 汇总行 (如 `passed`), 说明 `--explain` 未触发测试执行.

## 未验证范围

- 未跑全量测试套件 (按完成定义归合并节点).
- 未跑 `tests/run` 无参数与 `--fast` 的完整执行路径, 仅验证 `--fast` 的命令拼接.

## 偏差

基线的 `to-execution` 要求 PRODUCT.md 与 TECHNICAL.md 齐备, 本次以需求文本代替 PRODUCT.md, 跳过 `to-spec` 的 Gherkin 采纳流程 (该流程需用户在 chat 明确采纳, 无人值守下会阻塞).

## 产物测量

| 项 | 旧说明书 |
| --- | --- |
| issue 节数 | 18 |
| 其中填「无」「同全局」的节 | 5 |
| issue 字符数 | 1499 |
| EXECUTION.md 字符数 | 919 |
| 是否被推向 TDD | 否 (未调用 lazy-dev; issue 的 `测试切片` 节按条件保留写明不新增测试) |
| 证据是否来自真实运行 | 是 (含命令, 原始输出, 退出码) |
| 未验证范围是否写明 | 是 |
