# wordcount 独立验收报告 (第 1 轮, PRODUCT.md confirmed-flow v1)

## 摘要

- 目标提交: `5e20d11c94bfbab1ebd037ac95d9e1ccacfebdb4` (分支 `main`)
- 判据来源: `docs/changes/wordcount/PRODUCT.md`, `验收标准` 节带确认标记 `<!-- confirmed-flow: v1 -->`
- 必验项 3 条: AC-001-1, AC-002-1, BR-001
- 结果: 通过 3, 失败 0, 未验证 0
- 验收者: 本轮新开 2 个非作者子会话 (`v-g1-ac`, `v-g2-br001`)
- 证据目录: `docs/changes/wordcount/verify/round-1/`
- 结论仅代表本次自动验收核对, 仍需用户逐项确认与正式人工验收; 本报告不宣布正式交付, 不关闭用户验收.

## 一. 输入与版本前提 (第 1, 2 步)

| 项 | 实际情况 |
| --- | --- |
| 已确认 PRODUCT.md | `docs/changes/wordcount/PRODUCT.md`, gherkin 块之前有 `<!-- confirmed-flow: v1 -->` |
| 产物根目录 | `docs/changes/wordcount/` |
| 目标提交 | `5e20d11c94bfbab1ebd037ac95d9e1ccacfebdb4`, `git rev-parse HEAD` 与之一致 |
| 工作区一致性 | 验收开始时 `git status --porcelain` 为空; 验收期间新增的只有本证据目录, 已跟踪源码, 配置, 测试无改动, 也没有其他未跟踪产品文件 |
| 目标提交时间 | 2026-10-20T01:54:55+08:00; 最后一个实现/修复提交 `46ef5dc` 时间 2026-10-20T01:47:10+08:00 |

必验清单条数 = 验收场景 2 条 (AC-001-1, AC-002-1) + 标 `(审计)` 的业务规则 1 条 (BR-001) = 3 条, 与 PRODUCT.md 原文一一对应, 未做相关度筛选, 未增补.

## 二. 必验清单逐项结果 (第 7, 9 步)

| 标准编号 | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 时间或版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 (统计标准输入词数, `@G-001`) | 当前观察 (本轮实跑) | `printf 'alpha beta gamma\n' \| bin/wordcount` | stdout 原文 `3` (逐字节 `0000000   3  \n`), 退出码 `0`, stderr 为空 | `g1-ac.5e20d11.log` 第 39-42 行 (主跑), 45-49 行 (`od -c`), 52-55 行 (stderr 分离); 结论见 `g1-ac.5e20d11.md` | 2026-10-20T01:59:53+08:00, 提交 `5e20d11` | 通过 |
| AC-002-1 (统计文件词数, `@G-002`) | 当前观察 (本轮实跑) | `bin/wordcount --file samples/notes.txt` | 前提核对 `od -c samples/notes.txt` = `a l p h a   b e t a \n`; stdout 原文 `2` (逐字节 `0000000   2  \n`), 退出码 `0`, stderr 为空 | `g1-ac.5e20d11.log` 第 29-32 行 (前提), 63-66 行 (主跑), 69-73 行 (`od -c`), 76-79 行 (stderr 分离); 结论见 `g1-ac.5e20d11.md` | 2026-10-20T01:59:53+08:00, 提交 `5e20d11` | 通过 |
| BR-001 (既有测试 `tests/run.sh` 不得被改动, 审计) | 当前观察 - 静态材料核对 (非运行行为结果) | `git log --follow --stat -- tests/run.sh`; `git log --oneline --all -- tests/run.sh`; `git merge-base --is-ancestor 93fcc53 HEAD`; `git rev-parse 93fcc53:tests/run.sh` 与 `git rev-parse HEAD:tests/run.sh`; `git diff 93fcc53 HEAD -- tests/run.sh`; `git diff 93fcc53:tests/run.sh HEAD:tests/run.sh`; `git hash-object tests/run.sh`; `git diff HEAD -- tests/run.sh`; `git status --porcelain tests/run.sh`; `git ls-files -s tests/run.sh` | 文件只出现在 `93fcc53877c31263444cc169f76b0606f2e9895d` (scaffold, 新增 5 行), 全历史含所有分支仅此一条提交触及; 基准与目标提交 blob 均为 `a85d460255b8266747fe63c847fbdb62cae18f4f`; 两次 `git diff` 输出为空; 工作区 `git hash-object` 同为 `a85d4602...`, `git diff HEAD -- tests/run.sh` 与 `git status --porcelain tests/run.sh` 为空; 索引模式 `100755` 未变 | `g2-br001.5e20d11.log` 第 23-32 行 (历史), 34-50 行 (基准祖先性与区间变更), 52-66 行 (前后内容原文), 68-94 行 (blob 与 diff 比对); 结论见 `g2-br001.5e20d11.md` | 基准 `93fcc53` -> 目标 `5e20d11`, 检查时间 2026-10-20T01:59:41+08:00 | 通过 |

### 材料类型补充说明 (第 8 步)

- 三条都是本轮亲手产生的当前观察, 没有引用旧观察. `review/round-4.md` 里"AC-001/AC-002 实跑通过"只有一句摘要, 没有可读取原件, 按第 8 步不算充分证据, 本轮未采用; 本轮所有结论都来自重新实跑 / 重新比对.
- BR-001 的基准点由 G2 验收者自行决定并留下理由: 该文件在全部历史 (含所有分支) 中只被 `93fcc53` 这一次提交写入过, 不存在第二版可选, 因此基准选择不依赖任何未确认的新规则. 决策过程见 `g2-br001.5e20d11.md` 的"基准提交"节, 命令见 log 第 23-50 行.
- 指挥者复核: 逐份读过两个验收者的结论 md 与原始 log, 并核对 G2 的关键结论与仓库现状一致 (本轮 `git rev-parse HEAD` = `5e20d11...`, `git hash-object tests/run.sh` = `a85d4602...`, `git log 93fcc53..HEAD -- tests/run.sh` 为空). 复核用的会话与产出原件见 `session-g1.5e20d11.log`, `session-g2.5e20d11.log`, `session-metadata.v1-5e20d11.log`.
- 摘要与原件没有冲突: 两个 md 的结论行 (`RESULT: ...`) 与各自 log 的实际输出一致, 也与指挥者看到的会话记录一致.

## 三. 派工记录 (第 4, 6 步)

### 分组与人数依据

- 计划文件: `plan.v1-5e20d11.md` (派工前写成, 未事后补记).
- 必验项只有 3 条, 按方法分成两组:
  - G1 运行行为: AC-001-1, AC-002-1. 两条场景都是"照 PRODUCT.md 命令跑一次比对输出", 同一个入口, 同一份准备, 拆开无收益, 因此合成一组交给 1 人.
  - G2 静态材料审计: BR-001. 断言对象是文件内容前后一致, 方法与 G1 不同 (历史与 blob 比对), 不需要跑产品.
- 共用准备: 无. 本仓库没有构建步骤, 没有服务启动, 没有 fixture 生成, 因此不存在"开多个会话要重复同一份准备"的成本.
- 写入争用: 无. 三件都是只读操作, 两组同时开工, 不需要先后顺序, 也不需要执行顺序记录.
- 可用非作者验收者 2 人, 计划 2 人 = 组数 2, 未按 AC 逐条开会话.
- 需要 benchmark-checklist / blast-radius 吗: 不需要. 没有性能结论类必验项, 也没有依赖未实证安全假设的判定, 派工单未安排这两项方法, 指挥者也未代为调用.
- 项目级验证配方: 没有. 派工单如实写明没有, 让验收者按 PRODUCT.md 与 README 已有入口操作.

### 验收者与未参与事实

| 会话 (herdr agent 名) | 窗格 | pi session ID | 创建时间 (会话首行 timestamp) | 承接标准 | 起止 |
| --- | --- | --- | --- | --- | --- |
| `v-g1-ac` | `w1E:p3R` (tab `w1E:t3R`) | `01a15551-4c3e-735d-b1c5-54a2a53a51a5` | 2026-10-20T01:59:13+08:00 | AC-001-1, AC-002-1 | 01:59:27 起, 01:59:57 结束 |
| `v-g2-br001` | `w1E:p3S` (tab `w1E:t3S`) | `01a15551-5fdf-773f-bdb4-a63fecab9ce9` | 2026-10-20T01:59:18+08:00 | BR-001 | 01:59:41 起, 01:59:41 结束 |

未参与本次实现与修复的可核对事实:

1. 两个会话的创建时间 (01:59:13 / 01:59:18) 都晚于目标提交时间 01:54:55 与最后一个实现/修复提交 01:47:10, 采集过程见 `session-metadata.v1-5e20d11.log`.
2. 两个会话都是本轮新开的 tab (`herdr tab create` 返回 `w1E:t3R` / `w1E:t3S`), 不是恢复实现会话, 启动命令为 `herdr agent start <名> --kind pi --pane <窗格> -- --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`, 启动响应里 `argv` 与之一致.
3. 会话记录里只有读, 只读 git 查询, PRODUCT.md 命令执行与写证据文件的动作, 没有任何实现或修复动作 (`session-g1.5e20d11.log`, `session-g2.5e20d11.log`); 两份 log 的收尾都留有 `git status --porcelain` / `git rev-parse HEAD` 的原始输出, 与起始状态一致.
4. 派工单只给了目标提交, 输入路径, 分到的标准, 证据目录与核对规则, 没有给实现对话, 设计理由或作者自证结论: `dispatch-g1.v1-5e20d11.md`, `dispatch-g2.v1-5e20d11.md`.

### 共用准备, 材料归属与共享

- 共用准备执行人: 无 (不需要).
- 原始材料归属: G1 -> `g1-ac.5e20d11.md` + `g1-ac.5e20d11.log`; G2 -> `g2-br001.5e20d11.md` + `g2-br001.5e20d11.log`; 会话记录与元数据 -> `session-*.log`.
- 两组之间没有共享材料, 因此不存在"交出方 / 接收方 / 适用性核对"链条. 指挥者只核对材料, 没有补跑任何产品命令.

## 四. 三类去向

### 明确实现问题 (交回实现流程)

无. 3 条必验项中没有在最终版本上稳定失败的项.

### 缺产品规则 (交回决策流程)

无. 没有哪条必验项的判定取决于 PRODUCT.md 尚未确认的新规则: BR-001 的"既有"基准在 git 历史里只有一个候选, 不需要新规则就能定性.

### 权限与环境缺口 (未验证)

无. 三条都在本轮实际完成, 没有缺权限, 缺依赖服务或环境不可达的情况.

## 五. 写入与清理记录 (第 5 步)

- 批准范围: 本轮不需要用户批准. 三条必验项都是只读 (读标准输入, 读 `samples/notes.txt`, 读 git 对象), 不创建测试资源, 不改产品文件, 不写数据库或服务.
- 派工单给验收者的写入范围: 只允许在 `docs/changes/wordcount/verify/round-1/` 内新增自己的结论与 log; 越界必须停下报告. 两位验收者都未提出越界要求.
- 实际写入: 只有本证据目录内的 11 个文件 (2 份派工单, 1 份计划, 2 份验收结论, 2 份验收原始 log, 2 份会话记录, 1 份会话元数据, 本报告).
- 补充说明: G1 的补充观察里跑了 `sh tests/cli_errors_test.sh`, 该脚本自身用 `mktemp` 在系统临时目录建文件并 `trap` 清理; 这是被执行的测试脚本的内部行为, 不是验收者为构造场景另建的资源, 也不改仓库内容 (该次运行的原始输出见 `g1-ac.5e20d11.log` 第 91-123 行).
- 清理结果: 无需清理的产品侧对象, 无残留测试资源.
- 残留: 本证据目录内的文件相对起始提交是未跟踪新增 (`git status --porcelain -uall` 已列在 `g2-br001.5e20d11.log` 第 119-124 行与本节说明), 按设计保留为验收输出, 不算未完成清理项.

## 六. 覆盖范围与非产品判据的注明 (第 7 步)

- 覆盖范围: PRODUCT.md confirmed-flow v1 的 2 条验收场景 + 1 条审计业务规则, 全部 3 条. 报告绑定提交 `5e20d11c94bfbab1ebd037ac95d9e1ccacfebdb4`. 验收期间 PRODUCT.md 与源码未变化, 因此不涉及"输入中途变化, 只覆盖旧版本"的情况.
- 非产品判据, 本轮不判通过也不判失败, 仅如实注明:
  - `EXECUTION.md` 任务图只列 ISSUE-01 (评审第 4 轮记为缺口 R4P-1) — 属执行计划材料, 不是产品判据.
  - 命令行参数用法错误行为 (未知选项 / 缺 `--file` 路径 / 多余参数 / 重复 `--file` / 空路径) 在 PRODUCT.md 里没有验收场景 (评审第 4 轮记为缺口 R4P-2). G1 顺手跑了 `sh tests/cli_errors_test.sh` (30 条全 ok), 这里只作补充观察记录, 不构成本轮任何必验项的结论.
  - `--file -` 读到标准输入 (评审第 4 轮记为缺口 R4S-1) — 没有任何已确认标准定义它, 本轮不定性.
  - 内部代码结构, awk 单点化这类技术事项 — 属既有评审与执行验证范围, 不属产品判据.
- 方法说明: 本轮没有调用 benchmark-checklist 或 blast-radius, 因为必验清单里没有需要性能结论或安全假设实证的项.

## 七. 收尾说明

- 除本次证据目录的输出外, 源码与 Spec 未变: `bin/wordcount`, `tests/run.sh`, `tests/cli_errors_test.sh`, `samples/notes.txt`, `PRODUCT.md`, `EXECUTION.md`, `.agents/` 均无改动 (本轮 `git status --porcelain -uall` 只列出本证据目录的新增文件); 未执行任何 `git add/commit/push/merge`.
- 本报告结论仍需用户逐项确认并走正式人工验收; 本轮结论不是正式验收结论, 也不代表交付已关闭.
