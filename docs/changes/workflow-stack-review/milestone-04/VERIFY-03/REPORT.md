# Milestone-04 第三轮独立核验证据报告

目标提交: `fa45a87fdde22e5ba3bfa1e474da395250010349`
分支: `verify/m04-r3`
判据: `docs/changes/workflow-stack-review/milestone-04/PRODUCT.md`, `confirmed-flow: v1`, 仅核验 AC-010, AC-015, BR-003.

## 核验者与范围

三项由同一位非作者验收者独立核验, pi session `01a19327-c644-76eb-aaea-aa0690c22416`, 会话创建时间 `2026-10-31T18:10:19Z` (session 文件名时间). 没有另开子会话: 三项分别是有限文档逐句核对, 按指定命令运行同一套测试, 以及一次限定范围的文本审计, 没有并行收益; 同一验收者连续取证也避免共享服务状态造成干扰. 未参与该里程碑实现或前两轮核验, 本报告只记录本轮观察, 不作正式验收结论.

VERIFY-01 与 VERIFY-02 是历史记录, 本轮不改它们. 本报告只补验两轮遗留的三项, 不替代也不重写历史结论.

## 结果摘要

| 项目 | 本轮结论 | 材料类型 | 证据 |
|---|---|---|---|
| AC-010 | 失败 | 静态核对 | 下文逐句核对; 三处正向保留约定和 LOGIC 第 5 步替换均存在, 但 `workflow/demo/SKILL.md:31` 对持久化演示用本地文件写了“用后即焚”, 与该场景要求三处没有用完即删义务不符. |
| AC-015 | 通过 | 当前观察 | `uv run python -m pytest workflow/navigate/tests` 退出码 0, `30 passed in 8.04s`; 服务运行前后均确认 `alive:false`. |
| BR-003 | 通过 | 静态核对 | 活跃范围的全部 `prototype` 命中均属于规格允许例外: 明确测试负向用例, JS 内建成员, vendored Mermaid 第三方库. 除例外外没有残留. |

## AC-010: 静态核对

逐句按 PRODUCT.md 的 AC-010 核对 `workflow/demo/SKILL.md`, `workflow/demo/UI.md`, `workflow/demo/LOGIC.md`:

1. 保留与不主动删除: SKILL.md:28 明写演示材料及变体分支可留着回看且代理不主动删除; UI.md:84-85 分别对 A/B 变体分支和 C 演示文件作同样约定; LOGIC.md:62 明写演示材料与变体分支可留回看且代理不主动删除. 这一断言符合.
2. 仓库主人点名清理: SKILL.md:28, UI.md:84-85, LOGIC.md:62 都写明需要清理时由仓库主人点名删除对象. 但“没有用完即删义务”这一并列断言不符合: SKILL.md:31 的通用规则 3 对“若问题涉及持久化”的演示材料明确写“用本地文件, 取醒目名字, 用后即焚”. 该句要求用后删除, 与 AC-010 不设用完即删义务的要求冲突. 因此不能把此条笼统判为通过. 三份文件均未查到合并主干前清理的义务.
3. LOGIC 第 5 步: LOGIC.md:62 的“需要清理时由仓库主人点名删除对象”已取代 PRODUCT 所指的原句“原型文件在合并主干前由人类清理”; 不再要求合并主干前清理. 这一断言符合.

证据边界: 这是对目标提交工作树中文件的静态核对, 没有推断实际使用行为. 本项失败原因归为明确实现问题: SKILL.md:31 的文字与 AC-010 直接矛盾; 本轮不修改产品文件.

## AC-015: 测试运行

在执行 pytest 前运行 `uv run python workflow/navigate/scripts/web_server.py stop`, 随后运行 `status`, 返回 `alive:false`. 执行命令为 `uv run python -m pytest workflow/navigate/tests`, pytest 收集 30 项并全部通过, 汇总 `30 passed in 8.04s`, 进程退出码 0. 收工再次 stop, status 返回 `alive:false`. 前后服务停止确认均通过. 本轮没有启动展示服务, 没有占用 39271 或自建临时端口.

测试期间 pytest 按自身机制使用其临时目录; 本轮没有手动删除任何 pytest 临时目录, 仅做授权范围内的 pytest 执行.

## BR-003: 限定范围审计

仅检查 `workflow/`, `README.md`, `general/`, 使用不区分大小写的全文搜索 `rg -n -i 'prototype' workflow README.md general`. 按规格排除 `docs/changes/` 既有文件和 `docs/adr/0024-demo-poc-milestone-types.md`; 没有把它们纳入命中判定.

审计命中及例外逐项如下:

- `workflow/navigate/tests/test_roadmap_validation.py:3,192,193,197,201`: TC-003 用例及说明, 故意输入旧类型并检查拒绝/合法值中不含旧类型, 属于规格允许的负向测试.
- `workflow/navigate/tests/visual/render_checks.py:176,196,254`: `CanvasRenderingContext2D.prototype` 是 JavaScript 内建对象成员, 用来临时替换画布文字绘制函数以进行视觉检查, 不是旧里程碑类型名.
- `general/present/vendor/mermaid.min.js`: vendored Mermaid 第三方压缩库内使用的 prototype 成员, 属第三方库标识符例外. 全部匹配行号与每行匹配数见证据文件 `BR-003-exceptions.txt`.

除上述例外外, 该限定活跃范围没有 `prototype` 命中, 因而按既定审计口径通过. 原始全命中行保存在 `prototype-audit.txt`.

## 缺口及分类

- 明确实现问题: AC-010 因 `workflow/demo/SKILL.md:31` 的“用后即焚”表述失败.
- 尚缺产品规则: 无. 判据来自已确认 PRODUCT.md.
- 权限或环境缺口: 无. 指定测试和限定静态审计均已完成.

## 操作与证据记录

证据目录: `/tmp/m9-04-verify-r3/`.

- `2026-10-31T18:11:02Z`: 执行 `mkdir -p /tmp/m9-04-verify-r3`, 成功; 操作记录见 `actions.log`.
- 同一时间执行 BR-003 搜索并将原始结果写入 `prototype-audit.txt`; 命中 73 行. 分类和逐行位置在 `BR-003-exceptions.txt`.
- pytest 前运行服务 `stop` 和 `status`, 后运行 `stop` 和 `status`; 命令输出分别在 `pre-stop.txt`, `pre-status.txt`, `post-stop.txt`, `post-status.txt`. 前后 status 均为 `alive:false`. 未启动服务, 未占端口.
- pytest 原始输出在 `pytest.txt`; 命令退出码及运行记录在 `actions.log`.
- 本轮没有删除文件, 没有其他被本轮占用的端口或手动清理的临时目录.
- 本报告是目标仓库中唯一新增文件; 仓库原有文件未改.
