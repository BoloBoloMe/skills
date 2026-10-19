# 派工单 G1 (验收者 1): 运行行为, 承接 AC-001-1 与 AC-002-1

你是本轮独立验收者. 你没有参加本次实现与修复, 你的判断只按下面这份已确认的产品标准原文.

## 环境与目标

- 仓库: `/tmp/orchestra-14/ts001-review-pending`, 分支 `main`
- 目标提交: `5e20d11c94bfbab1ebd037ac95d9e1ccacfebdb4` (开始前用 `git rev-parse HEAD` 核对, 不一致就停下报告)
- 判据文件: `docs/changes/wordcount/PRODUCT.md` (只读, 确认标记 `<!-- confirmed-flow: v1 -->`)
- 证据目录: `docs/changes/wordcount/verify/round-1/`
- 你只能写证据目录里的文件, 按下面的文件名写.

## 你承接的标准 (判据原文, 照此判定, 不许放宽)

```gherkin
@AC-001 @normal @G-001
场景: AC-001-1 统计标准输入词数
  假定 仓库根目录已就绪
  当 验收者运行 `printf 'alpha beta gamma\n' | bin/wordcount`
  那么 输出为 `3`, 退出码为 0

@AC-002 @normal @G-002
场景: AC-002-1 统计文件词数
  假定 仓库中 `samples/notes.txt` 内容是 `alpha beta` 加一个换行
  当 验收者运行 `bin/wordcount --file samples/notes.txt`
  那么 输出为 `2`, 退出码为 0
```

两条都要做, 每条单独给结论. 步骤里的命令与期望值是判据的一部分: 命令要照抄执行, 输出要比对实际 stdout 内容与退出码.

## 项目入口 (没有项目级验证配方)

- 本项目没有项目级验证配方文件, 不要去找. 按 PRODUCT.md 原文的命令操作.
- `README.md` 登记了两条测试命令, 可作为补充观察: `sh tests/run.sh`, `sh tests/cli_errors_test.sh`. 它们的成败不是 AC 的判据, 只作为辅助材料; 判定仍以 PRODUCT.md 的命令输出为准.

## 操作规则

1. 全部只读. 不修改产品代码, 测试, `PRODUCT.md`, `EXECUTION.md`, `.agents/`; 不执行任何 `git add/commit/push/merge/checkout/restore`; 不修复你发现的任何问题.
2. 唯一允许的写入是证据目录内的两个文件. 若你认为必须在该目录外写东西才能构造场景, 停下报告, 不要自己扩权.
3. 别用 `mktemp` 之类在仓库外造临时文件; 需要保存输出就直接重定向到证据目录.
4. 原始输出要真: 保留命令, 真实 stdout/stderr, 退出码, 时间. 不要只写一句转述.
5. 判错就写失败, 不要替产品解释.

## 你要交的两个文件

### 1. `g1-ac.5e20d11.md`

内容:

- 会话标识: 你的 agent 名, 窗格/会话 ID, 工作目录.
- 开始与结束时间 (真实时间戳, 用 `date -Is`).
- 目标提交: `git rev-parse HEAD` 的实际输出.
- 两张结果表, 每条 AC 一行, 列: 标准编号 / 材料类型 (当前观察, 或未验证) / 实际操作 (完整命令) / 实际结果 (stdout 原文 + 退出码) / 证据位置 (log 行号或文件) / 时间 / 结论 (通过或失败或未验证).
- 补充观察 (可选, 不参与判定): 两条 README 测试命令的实际结果.
- 一句声明: 你在本次验收中没有修改任何产品文件, 只在证据目录新增文件.
- 未验证项要写清缺什么.

### 2. `g1-ac.5e20d11.log`

用 `script` 或直接重定向的方式记录: 上面每条命令的原样执行过程, 含命令, stdout, stderr, `printf 'exit=%s\n' $?` 的退出码. 要求别人只看这个文件就能复现结论.

做完把结论 md 的最后一行写成 `RESULT: AC-001-1=<通过|失败|未验证> AC-002-1=<通过|失败|未验证>`.
