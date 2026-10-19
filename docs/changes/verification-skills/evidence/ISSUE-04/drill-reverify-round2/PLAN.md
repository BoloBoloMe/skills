# 独立验收复验派工计划 (round 2)

- 时间: 2026-10-19T22:30+08:00
- 新目标提交: `59069130494139f96994f144c1ba09d3b51876d6` (HEAD)
- 上一轮目标提交: `cd087542b4610c49ded0a1278fe8065726b62d9d`
- 基线提交: `8438934fc81b67ed518dc4ad2e2f7dbd83b0192a`
- 判据来源: `docs/changes/relay-board/PRODUCT.md` (验收标准 confirmed-flow v1, 业务规则 BR-001), 本轮未变
- 版本前提: HEAD 为新目标提交; 已跟踪源码/配置/测试无未提交改动; 未跟踪文件只有上一轮证据目录 (验收输出, 非产品文件); 端口 18101 空闲.
- 本轮证据目录: `docs/changes/relay-board/evidence/v2-5906913/` (另开一轮, 不覆盖 v1)

## 修复提交影响

`git diff cd08754 5906913` 只改 `app.py` (2 insertions, 1 deletion), 内容:

```diff
     def report(self) -> str:
-        return report_line(self.instance, "loading")
+        # report 的状态必须反映实例当前状态, 不能写成固定值.
+        return report_line(self.instance, self.state)
```

- 直接影响: `AC-003-1` (report 状态) 以及 G-003.
- 间接影响: `BR-001` 需按新提交重新核对依赖与 deps.txt; 修复提交只动 app.py, 无新增文件.
- `AC-001-1`, `AC-002-1`, `AC-004-1` 的代码路径未被这处改动触及; 但代码版本已变, 且四条场景共用同一实例, 本轮由验收者全部重跑, 不把上一轮通过结论当默认. 上一轮证据只作为旧材料参考, 不作为本轮通过依据.
- 关键路径 (AC-003 report) 必须有验收者本轮自己的实跑记录; 作者材料 `/tmp/orchestra-04/author-materials/green/` 只作引用参考, 不顶替本轮观察.

## 必验清单 (5 项, 与 v1 相同)

| 编号 | 类型 | 判据摘要 |
| --- | --- | --- |
| AC-001-1 | 场景 | 浏览器渲染 /status-page 并截图, 截图显示 instance=alpha, state=ready, version=relay-v1 |
| AC-002-1 | 场景 | `python3 app.py job --port 18101 --ms 2500` 输出 `job-done instance=alpha elapsed_ms=2500`, 退出码 0 |
| AC-003-1 | 场景 | `python3 app.py report --port 18101` 输出 `relay-report instance=alpha version=relay-v1 state=ready`, 退出码 0 |
| AC-004-1 | 场景 | `python3 app.py log --port 18101` 输出含 `instance=alpha` 与 `event=job-end`, 退出码 0 |
| BR-001 | 审计 (静态) | 本次变更不新增第三方依赖, deps.txt 与上一提交逐项一致 |

## 证据目录影响判断

- 目录 `docs/changes/relay-board/evidence/v2-5906913/` 只写 .md/.txt/.png/.log 等验收输出, 不写 .py 测试文件.
- 项目无 pytest.ini/tox.ini/setup.cfg/pyproject.toml/conftest.py; README 的 pytest 命令只发现 test_*.py, 不读取 docs/; 服务与测试不读 docs/.
- 结论: 写入该目录不进入构建, 测试发现或运行输入, 可留在仓库内; 新增证据是本轮相对起始提交的唯一预期变化.

## 换人与独立性

- 原验收者 `i04-a1-ac` 在修复阶段亲自改动 app.py 并提交 5906913 (有原生会话记录: 2026-10-19T22:27 的 `git add app.py && git commit`), 不再承担独立验收.
- 原验收者 `i04-a1-br` 会话已关闭; 按调用方安排新开非作者.
- 本轮两名验收者均为 22:27:25 (修复提交时间) 之后新开的会话, 不继承任何旧会话过程, 不读取实现或修复对话作为结论依据.
- 上一轮通过结论与作者材料只作参考材料, 不直接采信.

## 分组与人数

当轮计划 2 名, 均为新会话.

### 组 1: 运行场景 (承接 AC-001-1, AC-002-1, AC-003-1, AC-004-1)

- 验收者: `i04-a2-ac` (新会话).
- 资源: 唯一实例 alpha, 端口 18101, `runtime/alpha`, `runtime/shared`; google-chrome headless 截图.
- 共用准备: 本组自己启动实例一次并 health; 只有本组需要实例, 无跨组共用.
- 顺序: AC-002 的 job 完成后才能做 AC-004; 四条场景同一实例按序执行; 修复后的 AC-003 必须本轮实跑.
- 不拆理由: 四条场景争用同一实例/端口/数据目录; 禁止为并行加实例或扩端口; 单场景不值得单开会话.

### 组 2: 静态依赖审计 (承接 BR-001)

- 验收者: `i04-a2-br` (新会话).
- 资源: 只读 git 历史与工作区文件; 不占用实例, 端口与 runtime/.
- 范围: 修复提交 `5906913` 相对父提交 `cd08754` 的依赖材料; 同时核对基线 `8438934`..`5906913` 的累计变更, 确认整体未新增第三方依赖.
- 并行: 与组 1 完全隔离, 无共用准备, 可同时开工.

### 争用与先后

- 组 1 内 AC-002 (写 shared/events.log) 先于 AC-004 (只读同一日志), 执行者 `i04-a2-ac`, 依据 AC-004 的"假定耗时任务已经执行".
- 组 2 与组 1 无共用资源, 无先后约束.
- 不为制造并行新增实例, 端口或写入授权.

### 并行收益

- 组 2 无需任何共用准备, 与组 1 同时执行; 同时让 BR-001 由未参与修复的会话独立核对.
- 组 1 内部不可再分, 不再开第三个会话.

## 交付物

- 组 1: `evidence/v2-5906913/runtime-AC/REPORT.md` + 原始输出/截图.
- 组 2: `evidence/v2-5906913/audit-BR-001/REPORT.md` + 原始输出.
- 指挥者: 本计划 + `evidence/v2-5906913/VERIFY-REPORT.md` (汇总).
