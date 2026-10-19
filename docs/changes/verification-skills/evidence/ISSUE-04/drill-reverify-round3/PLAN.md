# 独立产品验收派工计划 (复验 round 3)

- 时间: 2026-10-19T22:37+08:00
- 新目标提交: `59069130494139f96994f144c1ba09d3b51876d6` (HEAD)
- 修复提交的父提交 (上一版本): `cd087542b4610c49ded0a1278fe8065726b62d9d`
- 基线提交: `8438934fc81b67ed518dc4ad2e2f7dbd83b0192a`
- 判据来源: `docs/changes/relay-board/PRODUCT.md` (验收标准 `confirmed-flow: v1`; 业务规则 BR-001)
- 本轮证据目录: `docs/changes/relay-board/evidence/v3-5906913/` (新开一轮, 不覆盖 v1/v2)
- 调用方选择: 不恢复原验收会话, 新开非作者验收者; 本轮可用非作者验收者 1 名
- 端口 18101 与 `runtime/` 只给本项目用

## 版本前提

| 检查 | 结果 |
| --- | --- |
| 目标提交存在且为 HEAD | `git rev-parse HEAD` = `59069130494139f96994f144c1ba09d3b51876d6` |
| 已跟踪源码/配置/测试无未提交改动 | `git diff` 与 `git diff --cached` 均为空 |
| 未跟踪文件 | 只有 `docs/changes/relay-board/evidence/` (历次验收输出, 非产品文件) |
| 判据未变 | `PRODUCT.md` 工作区 blob 与 `HEAD:docs/changes/relay-board/PRODUCT.md` 同为 `83cf9679...` |
| 端口 | 验收开始时 18101 无监听 |

## 修复提交影响

`git diff cd08754 5906913` 只改 `app.py` (2 insertions, 1 deletion):

```diff
     def report(self) -> str:
-        return report_line(self.instance, "loading")
+        # report 的状态必须反映实例当前状态, 不能写成固定值.
+        return report_line(self.instance, self.state)
```

- 直接影响: `AC-003-1` 与 G-003 (report 的状态字段).
- 影响 `BR-001`: 需按新提交重新核对依赖材料与 `deps.txt`; 修复提交未新增文件.
- `AC-001-1`, `AC-002-1`, `AC-004-1` 的代码路径未被该改动触及, 但本轮代码版本已变, 且四条场景共用同一实例, 由验收者全部重跑; 不把任何旧通过结论当默认.
- 上一轮证据 (`evidence/v1-cd08754/`, `evidence/v2-5906913/`) 与作者材料只作旧材料参考, 不作为本轮通过依据.

## 必验清单 (5 项)

| 编号 | 类型 | 判据摘要 |
| --- | --- | --- |
| AC-001-1 | 场景 | 浏览器渲染 `http://127.0.0.1:18101/status-page` 并截图; 截图显示 `instance=alpha`, `state=ready`, `version=relay-v1` |
| AC-002-1 | 场景 | `python3 app.py job --port 18101 --ms 2500` 输出 `job-done instance=alpha elapsed_ms=2500`, 退出码 0 |
| AC-003-1 | 场景 | `python3 app.py report --port 18101` 输出 `relay-report instance=alpha version=relay-v1 state=ready`, 退出码 0 |
| AC-004-1 | 场景 | `python3 app.py log --port 18101` 输出含 `instance=alpha` 与 `event=job-end`, 退出码 0 |
| BR-001 | 审计 (静态) | 本次变更不新增第三方依赖, `deps.txt` 与上一提交逐项一致 |

必验项总数 5 = 4 个验收场景 + 1 条审计 BR, 与 PRODUCT.md 原文一致, 无遗漏.

## 证据目录影响判断

- 只写 `.md/.txt/.png/.log` 验收输出, 不写 `.py`.
- 项目无 `pytest.ini/tox.ini/setup.cfg/pyproject.toml/conftest.py`; README 的 pytest 命令只发现 `test_*.py`; 服务与测试都不读 `docs/`.
- 结论: 写入 `docs/changes/relay-board/evidence/v3-5906913/` 不进入构建, 测试发现或运行输入, 可留在仓库内.
- 新增证据是本轮相对起始提交的唯一预期变化.

## 分组与人数

- 可隔离的组有 2 个: 组 A 运行场景 (AC-001..004), 组 B 静态依赖审计 (BR-001). 两组资源互不占用, 本可并行.
- 当轮可用非作者验收者 1 名, 按"组数与可用人数取较小者", 计划 1 人.
- 不派 2 人的理由: 没有第 2 名非作者; 也不让参与过实现或修复的会话顶替.
- 也不拆成逐条 AC 的多会话: 四条 AC 争用同一实例, 端口 18101 与 `runtime/`, 拆开只会重复准备并引入等待.
- 1 人依次完成组 A 与组 B; 组 B 只读 git 与文件, 不与组 A 争用, 放在组 A 收尾/清理后进行.

### 组 A: 运行场景 (承接 AC-001-1, AC-002-1, AC-003-1, AC-004-1)

- 资源: 唯一实例 alpha, 端口 18101, `runtime/alpha`, `runtime/shared`; headless Chrome 截图.
- 共用准备: 由该验收者启动实例一次并 health 确认; 四条场景共用这一次启动, 不重复启动.
- 顺序: AC-001 -> AC-002 (job) -> AC-003 -> AC-004 (log) -> 需要时复跑 AC-003.
- 写入/读取争用: AC-002 的 job 写 `runtime/shared/events.log` 的 `job-end`, AC-004 只读同一日志; 必须先 AC-002 后 AC-004, 依据 AC-004 场景的"假定耗时任务已经执行".
- 收尾: 停止实例, 确认端口无监听; 在证据目录留清理记录.

### 组 B: 静态依赖审计 (承接 BR-001)

- 资源: 只读 git 历史与工作区文件; 不占实例, 端口, `runtime/`.
- 范围: `5906913` 相对父提交 `cd08754` 的依赖材料; 同时核对 `8438934..5906913` 累计变更未新增第三方依赖.
- 结论性质: 静态材料核对结果, 不是运行行为结果.

## 材料归属与共享

- 原始材料归执行验收者, 由其本人下结论.
- 共用准备 (实例启动/health/停止) 只做一次, 由该验收者执行; 无跨组共享材料.
- 指挥者只读原件复核, 不运行产品入口, 不补跑, 不替验收者下单条结论.

## 交付物

- 组 A: `evidence/v3-5906913/runtime-AC/REPORT.md` + 原始命令输出, 截图, 退出码, 时间.
- 组 B: `evidence/v3-5906913/audit-BR-001/REPORT.md` + 原始 git/文件输出.
- 指挥者: 本计划 + `evidence/v3-5906913/VERIFY-REPORT.md` (汇总).
